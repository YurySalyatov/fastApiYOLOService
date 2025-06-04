import time
from celery import Celery
from pathlib import Path

from app.file_utils import return_process_image, load_model
from app.config import settings
from app.file_utils import process_image, process_video
from app.anydetector import get_detector

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


@celery.task(name="process_camera_frames")
def process_camera_frames(detector_name, list_of_frames):
    detector = get_detector(detector_name)
    detector.detect_frames(list_of_frames, time.time())
