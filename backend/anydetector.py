from file_utils import union_area
import os
from pathlib import Path


class Destination:
    def __init__(self, file_path):
        self.file_path = file_path
        if os.path.exists(file_path):
            os.remove(file_path)
        os.makedirs(Path(self.file_path).parent, exist_ok=True)

    def send_message(self, message):
        with open(self.file_path, "a") as f:
            f.write(message)


class AnyDetector:
    def __init__(self, detector_id, conds, detector_name, destination: Destination):
        self.conds = conds
        self.id = detector_id
        self.detector_name = detector_name
        self.destination = destination
        self.storage = {}

    def detect_frames(self, boxes_names_frames, time):
        for i, cond in enumerate(self.conds):
            res, message = cond(boxes_names_frames, self.id, time)
            if res:
                self.call_massage(message)

    def call_massage(self, message):
        self.destination.send_message(message)


def default_detection(boxes_names_frames, id, time, storage):
    return True, f"Detector {id} is default detector"


def fire_appear(boxes_names_frames, id, time, storage):
    prev_fires = storage.get('fires', 0)
    next_fires = []
    for i in range(len(boxes_names_frames)):
        if len(boxes_names_frames[i].get('Fire', [])) > len(next_fires):
            next_fires = boxes_names_frames[i].get('Fire', [])
    if len(next_fires) <= prev_fires:
        return False, None
    square = union_area(next_fires)
    message = (f"Detector {id}. Detect more fires: was {prev_fires} fires, became {len(next_fires)}. "
               f"Square of fire:{square} "
               f"Detection at {time}\n")
    storage['fires'] = len(next_fires)
    return True, message


def smoke_appear(boxes_names_frames, id, time, storage):
    prev_fires = storage.get('smoke', 0)
    next_smokes = []
    for i in range(len(boxes_names_frames)):
        if len(boxes_names_frames[i].get('Smoke', [])) > len(next_smokes):
            next_smokes = boxes_names_frames[i].get('Smoke', [])
    if len(next_smokes) <= prev_fires:
        return False, None
    square = union_area(next_smokes)
    message = (f"Detector {id}. Detect more smokes: was {prev_fires} smokes, became {len(next_smokes)}. "
               f"Square of smoke:{square} "
               f"Detection at {time}\n")
    storage['smoke'] = len(next_smokes)
    return True, message


def fire_smoke_disappear(boxes_names_frames, id, time, storage):
    smokes = storage['smoke']
    fires = storage['fires']
    if smokes == 0 and fires == 0:
        return False, None
    nxt_smokes = 0
    nxt_fires = 0
    for i in range(len(boxes_names_frames)):
        nxt_fires = max(nxt_fires, len(boxes_names_frames[i].get('Fire', [])))
        nxt_smokes = max(nxt_smokes, len(boxes_names_frames[i].get('Smoke', [])))
    if nxt_smokes > 0 or nxt_fires > 0:
        return False, None
    storage['smoke'] = nxt_smokes
    storage['fires'] = nxt_fires
    return True, (f"Detector {id}. Detect no fires and smoke. "
                  f"Detection at {time}\n")


def trash_detection(boxes_names_frames, id, time, storage):
    prev_detected = storage.get('prev_detected', {})
    dict = {}
    for box in boxes_names_frames:
        for key in box:
            dict[key] = max(dict.get(key, 0), len(box[key]))
    if len(dict) == 0:
        return False, None
    message = f"Detector {id}. Detect trash: "
    for key in dict.keys():
        prev_detected[key] = dict[key]
        message += f'{key} {dict[key]},'
    message = message[:-1]
    message += f'. Detection at {time}\n'
    storage['prev_detected'] = prev_detected
    return True, message


def long_trash_detection(boxes_names_frames, id, time, storage):
    last_detected = storage.get('last_detected', {})
    dict = {}
    for box in boxes_names_frames:
        for key in box:
            dict[key] = max(dict.get(key, 0), len(box[key]))
    if len(dict) == 0:
        return False, None
    message = f"Detector {id}. Detect trash: "
    for key in dict.keys():
        if last_detected[key] != dict[key]:
            last_detected[key] = time
        message += f'{key} {dict[key]},'
    message = message[:-1]
    message += f'. Detection at {time}\n'
    storage['last_detected'] = last_detected
    return True, message


default_logs = Destination("shared_volume/logs/default_logs.txt")
default_detector = AnyDetector(0, [], "default", default_logs)

fire_smoke_logs = Destination("shared_volume/logs/fire-smoke_logs.txt")
fire_smoke_detector = AnyDetector(1, [fire_appear, smoke_appear, fire_smoke_disappear],
                                  "fire detector",
                                  fire_smoke_logs)

trash_logs = Destination("shared_volume/logs/trash_logs.txt")
trash_detector = AnyDetector(2, [trash_detection], 'trash detector', trash_logs)
all_detectors = {'fire-smoke': fire_smoke_detector}


def get_detector(model_name):
    if model_name in all_detectors:
        return all_detectors[model_name]
    return default_detector
