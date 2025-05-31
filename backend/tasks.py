import time

import cv2
import numpy as np
from celery import Celery
from file_utils import return_process_image, load_model
from config import settings
from file_utils import process_image, process_video
from pathlib import Path
from anydetector import AnyDetector

celery = Celery(__name__, broker=settings.REDIS_URL)


@celery.task(name="process_image_task")
def process_image_task(input_path, confidence, model_name, colors):
    output_path = settings.PROCESSED_FOLDER / f"processed_{Path(input_path).name}"
    model = load_model(model_name)
    classes = model.names
    process_image(model, classes, colors, input_path, output_path, confidence)
    return f"processed_{Path(input_path).name}"


@celery.task(name="process_video_task")
def process_video_task(input_path, confidence, model_name, colors):
    output_path = settings.PROCESSED_FOLDER / f"processed_{Path(input_path).name}"
    model = load_model(model_name)
    classes = model.names
    process_video(model, classes, colors, input_path, output_path, confidence)
    return str(output_path)


@celery.task(name="process_ws_frame", serializer='pickle')
def process_ws_frame(frame_data, model_name, confidence, colors):
    nparr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    model = load_model(model_name)
    processed = return_process_image(
        model,
        model.names,
        colors,
        frame,
        confidence
    )

    # Конвертация в bytes
    _, buffer = cv2.imencode('.jpg', processed)
    return buffer.tobytes()


@celery.task(name="process_ws_frame", serializer='pickle')
def detect_list_of_frames(detector: AnyDetector, list_of_frames):
    detector.detect_frames(list_of_frames, time.time())
