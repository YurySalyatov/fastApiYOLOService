import os
from pathlib import Path
from app.file_utils import union_area
from app.config import settings


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


MAX_TIME_DELTA = 72000


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
        last_detected[key] = time
    for key in last_detected.keys():
        if key not in dict and time - last_detected[key] > MAX_TIME_DELTA:
            message += f'{key} to many times not clear: {time - last_detected[key]},'
    message = message[:-1]
    message += f'. Detection at {time}\n'
    storage['last_detected'] = last_detected
    return True, message


def trash_disappear(boxes_names_frames, id, time, storage):
    prev_detected = storage.get('prev_detected', {})
    message = f"Detector {id}. Detect trash: "
    add = False
    for key in prev_detected.keys():
        if prev_detected[key] == 0:
            message += f'{key} was successfully cleared,'
            add = True
    if not add:
        return False, None
    message = message[:-1]
    message += f'. Detection at {time}\n'
    return True, message


def phone_detection(boxes_names_frames, id, time, storage):
    prev_detected = storage.get('prev_detected', 0)
    detected_phones = 0
    for box in boxes_names_frames:
        detected_phones = max(detected_phones, len(box.get('cellphone - v1 2024-06-24 2-21pm')))
    if detected_phones == 0 or prev_detected == detected_phones:
        return False, None
    storage['prev_detected'] = detected_phones
    return True, (f"Detector {id}. Detect phones {detected_phones}. "
                  f"Detection at {time}\n")


def dangerous_detection(boxes_names_frames, id, time, storage):
    prev_detected = storage.get('prev_detected', {})
    dict = {}
    for box in boxes_names_frames:
        for key in box:
            dict[key] = max(dict.get(key, 0), len(box[key]))
    if len(dict) == 0:
        return False, None
    message = f"Detector {id}. Detect dangerous things: "
    for key in dict.keys():
        prev_detected[key] = dict[key]
        message += f'{key} {dict[key]},'
    message = message[:-1]
    message += f'. Detection at {time}\n'
    storage['prev_detected'] = prev_detected
    return True, message


def couriers_detection(boxes_names_frames, id, time, storage):
    prev_detected = storage.get('prev_detected', {})
    prev_couriers = prev_detected.get('hunan-couriers', 0)
    prev_robot = prev_detected.get('robot-couriers', 0)
    couriers = 0
    robots = 0
    for box in boxes_names_frames:
        couriers = max(len(box.get('human-courier', [])), couriers)
        robots = max(len(box.get('robot-courier', [])), robots)
    if couriers == 0 and robots == 0:
        prev_detected['hunan-couriers'] = 0
        prev_detected['robot-couriers'] = 0
        storage['prev_detected'] = prev_detected
        return False, None
    if prev_couriers >= couriers and prev_robot >= robots:
        return False, None
    message = f"Detector {id}."
    if couriers > prev_couriers:
        message += f" Detected more human couriers: {couriers}."
    if robots > prev_robot:
        message += f"Detected more robot couriers: {robots}"
    message += f" Detection at {time}"
    prev_detected['human-courier'] = couriers
    prev_detected['robot-courier'] = robots
    storage['prev_detected'] = prev_detected
    return True, message


# def package_detection(boxes_names_frames, id, time, storage):
#


default_logs = Destination(settings.LOGS_FOLDER / "default.log")
default_detector = AnyDetector(0, [], "default", default_logs)

fire_smoke_logs = Destination(settings.LOGS_FOLDER / "fire-smoke.log")
fire_smoke_detector = AnyDetector(1, [fire_appear, smoke_appear, fire_smoke_disappear],
                                  "fire detector",
                                  fire_smoke_logs)

trash_logs = Destination(settings.LOGS_FOLDER / "trash.log")
trash_detector = AnyDetector(2, [trash_detection, long_trash_detection, trash_disappear], 'trash detector', trash_logs)

phone_logs = Destination(settings.LOGS_FOLDER / "phone.log")
phone_detector = AnyDetector(3, [phone_detection], 'phone detector', phone_logs)

dangerous_logs = Destination(settings.LOGS_FOLDER / "dangerous.log")
dangerous_detector = AnyDetector(4, [dangerous_detection], 'dangerous detector', dangerous_logs)

couriers_logs = Destination(settings.LOGS_FOLDER / "couriers.log")
couriers_detector = AnyDetector(5, [couriers_detection], 'couriers detector', couriers_logs)

all_detectors = {'fire-smoke': fire_smoke_detector,
                 'trash': trash_detector,
                 'phone': phone_detector,
                 'mask-stick-knife': dangerous_detector,
                 'couriers': couriers_detector}


def get_detector(model_name):
    if model_name in all_detectors:
        return all_detectors[model_name]
    return default_detector
