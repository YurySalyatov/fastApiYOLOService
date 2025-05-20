import cv2
import torch
import yaml
from pathlib import Path
from typing import List, Tuple
from config import settings
from ultralytics import YOLO

DEFAULT_COLORS = [
    (255, 0, 0),  # Red
    (0, 255, 0),  # Green
    (0, 0, 255),  # Blue
    (255, 255, 0),  # Yellow
    (128, 0, 128)  # Purple
]


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
    for box in detections.boxes:
        class_id = int(box.cls)
        label = classes[class_id]
        conf = float(box.conf)

        if conf < confidence:  # Confidence threshold
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        color = colors[class_id]

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Create text label with confidence
        text = f"{label} {conf:.2f}"

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
    return frame


def load_model(model_name: str):
    if model_name == settings.DEFAULT_MODEL:
        return YOLO('yolo12s.yaml').load('yolo12s.pt')

    model_path = settings.MODELS_FOLDER / f"{model_name}.pt"
    if not model_path.exists():
        raise ValueError(f"Model {model_name} not found")

    return YOLO(model_path)


def process_image(model, classes, colors, input_path: str,
                  output_path: str, confidence=0.5):
    frame = cv2.imread(input_path)
    results = process_frame(model, frame)
    frame = draw_detections(frame, results, confidence, classes, colors)
    cv2.imwrite(output_path, frame)
    cv2.destroyAllWindows()


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
        frame = draw_detections(frame, results, confidence, classes, colors)

        if show_live:
            cv2.imshow('Video Processing', frame)
            if cv2.waitKey(1) == ord('q'):
                break

        out.write(frame)

    cap.release()
    out.release()
    cv2.destroyAllWindows()


def predict(self, img_path, iou=0.4):
    return self.model.predict(source=img_path, imgsz=640, iou=iou)


def real_time_processing(model, classes, colors, camera_id: int = 0):
    """
    Process live video stream from webcam
    :param camera_id: webcam device ID (default 0)
    """
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        raise ValueError("Error connecting to camera")

    print("Real-time processing started. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = process_frame(model, frame)
        frame = draw_detections(frame, results, classes, colors)

        cv2.imshow('Live Detection', frame)
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def normalize_colors(user_colors: List[Tuple[int, int, int]], num_classes: int) -> List[Tuple[int, int, int]]:
    if not user_colors:
        return DEFAULT_COLORS[:num_classes]

    colors = user_colors.copy()
    while len(colors) < num_classes:
        colors.extend(DEFAULT_COLORS)

    return colors[:num_classes]
