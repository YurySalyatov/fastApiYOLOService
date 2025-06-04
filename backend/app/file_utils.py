import cv2
import torch
from typing import List, Tuple
from ultralytics import YOLO
import numpy as np
from shapely.geometry import box
import shapely

from app.config import settings


DEFAULT_COLORS = [
    (255, 0, 0),  # Red
    (0, 255, 0),  # Green
    (0, 0, 255),  # Blue
    (255, 255, 0),  # Yellow
    (128, 0, 128)  # Purple
]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

cashed_model = {}


def get_colors(cnt):
    if cnt <= len(DEFAULT_COLORS):
        return DEFAULT_COLORS[:cnt]

    res = DEFAULT_COLORS[:]
    for i in range(cnt - len(DEFAULT_COLORS)):
        pred_color = res[i]
        add = 113
        if i % 3 == 0:
            color = ((pred_color[0] + add) % 255, pred_color[1], pred_color[2])
        elif i % 3 == 0:
            color = (pred_color[0], (pred_color[1] + add) % 255, pred_color[2])
        else:
            color = (pred_color[0], pred_color[1], (pred_color[2] + add) % 255)
        res.append(color)
    return res


def process_frame(model, frame):
    """Process a single frame and return detection results
    :param frame: one frame to predict
    :return: result of prediction
    """
    results = model.predict(frame, verbose=False)
    return results[0]


def draw_detections(frame, detections, confidence, classes, colors=DEFAULT_COLORS):
    """Draw bounding boxes and labels on the frame
    :param frame: one frame to work with
    :param detections: list of boxes and labels witch was detected
    :return: frame with labeled objects, if they were detected
    """
    res = {}
    for box in detections.boxes:
        class_id = int(box.cls)
        label = classes[class_id]
        conf = float(box.conf)
        if conf < confidence:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        color = colors[class_id]

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Create text label with confidence
        text = f"{label} {conf:.2f}"
        if label in res:
            res[label].append([x1, y1, x2, y2])
        else:
            res[label] = [[x1, y1, x2, y2]]
        # Calculate text position
        (text_width, text_height), _ = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
        )

        # Handle text position for top-edge cases
        text_y = y1 - 10 if y1 - 10 > text_height else y1 + 20

        # Draw text background
        cv2.rectangle(
            frame,
            (x1, text_y - text_height - 2),
            (x1 + text_width, text_y + 2),
            color,
            -1
        )

        # Put text
        cv2.putText(
            frame,
            text,
            (x1, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (30, 30, 30),  # Dark gray text
            2
        )
    return frame, res


def load_model(model_name: str):
    if model_name not in cashed_model:
        model_path = settings.MODELS_FOLDER / f"{model_name}.pt"
        if not model_path.exists():
            raise ValueError(f"Model {model_name} not found")
        model = YOLO(model_path)
        model.to(device)
        cashed_model[model_name] = model
        return model
    return cashed_model[model_name]


def process_image(model, classes, colors, input_path: str,
                  output_path: str, confidence=0.5):
    frame = cv2.imread(input_path)
    results = process_frame(model, frame)
    frame, _ = draw_detections(frame, results, confidence, classes, colors)
    cv2.imwrite(output_path, frame)
    cv2.destroyAllWindows()


def return_process_image(model, classes, colors, frame, confidence=0.5):
    frame = cv2.imread(frame)
    results = process_frame(model, frame)
    frame, sort_results = draw_detections(frame, results, confidence, classes, colors)
    return frame, sort_results


def process_video(model, classes, colors, input_path: str,
                  output_path: str,
                  confidence=0.5,
                  show_live: bool = False):
    """
    Process video file and save annotated results
    :param input_path: input video file path
    :param output_path: output video file path
    :param show_live: show real-time processing window
    """
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError("Error opening video file")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out = cv2.VideoWriter(output_path,
                          cv2.VideoWriter_fourcc(*'mp4v'),
                          fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = process_frame(model, frame)
        frame, _ = draw_detections(frame, results, confidence, classes, colors)

        out.write(frame)

    cap.release()
    out.release()
    cv2.destroyAllWindows()


def predict(self, img_path, iou=0.4):
    return self.model.predict(source=img_path, imgsz=640, iou=iou)


def normalize_colors(user_colors: List[Tuple[int, int, int]], num_classes: int) -> List[Tuple[int, int, int]]:
    if not user_colors:
        return DEFAULT_COLORS[:num_classes]

    colors = user_colors.copy()
    while len(colors) < num_classes:
        colors.extend(DEFAULT_COLORS)

    return colors[:num_classes]


def proces_camera(contents, classes, colors, model, confidence):
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    processed_img, boxes = return_process_image(model, classes, colors, img, confidence=confidence)

    _, buffer = cv2.imencode('.jpg', processed_img)
    return buffer, boxes


def union_area(list_rectangles):
    rectangles = [box(x1, y1, x2, y2) for (x1, y1, x2, y2) in list_rectangles]
    union = shapely.unary_union(rectangles)
    return union.area
