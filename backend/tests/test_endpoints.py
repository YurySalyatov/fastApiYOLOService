# test_upload_processing.py
import pytest
import pytest_asyncio
import httpx
import asyncio
from PIL import Image
from io import BytesIO
import time
import json
import websockets
import base64

from app.config import settings


# Генерация тестового изображения
def generate_test_image():
    img = Image.new("RGB", (800, 600), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_image_upload_processing(test_app):
    # Загрузка изображения
    file_path = settings.TEST_FOLDER / "fire_example.jpeg"
    with open(file_path, "rb") as f:
        file_content = f.read()

    files = {
        "file": ("test_image.jpg", file_content, "image/jpeg")
    }
    colors = [(255, 0, 0), (0, 255, 0)]
    data = {
        "confidence": "0.5",
        "model_name": "fire-smoke",
        "colors": json.dumps(colors)
    }
    response = test_app.post("/upload/file/", files=files, data=data)
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    # Проверка статуса задачи
    for _ in range(10):  # Ожидание обработки
        time.sleep(1)
        response = test_app.get(f"/api/tasks/{task_id}")
        status = response.json()["status"]
        if status == "SUCCESS":
            break

    assert response.json()["status"] == "SUCCESS"
    assert "processed_" in response.json()["result"]


def test_camera_upload_processing(test_app):
    frames_folder = settings.TEST_FOLDER / "frames"
    frames = frames_folder.glob("*.jpg")

    colors = [(255, 0, 0), (0, 255, 0)]
    data = {
        "confidence": "0.5",
        "model_name": "fire-smoke",
        "colors": json.dumps(colors)
    }
    for frame_file in frames:
        with open(frame_file, "rb") as f:
            frame_content = f.read()
        files = {
            "frame": ("test_image.jpg", frame_content, "image/jpeg")
        }
        response = test_app.post("/camera_upload/process_frame/", files=files, data=data)

        now = int(time.time() * 1000)
        # print(response.json())
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        json_data = response.json()
        assert "processed_frame" in json_data, "processed_frame not in response"
        assert "timestamp" in json_data, "timestamp not in response"
        assert now > json_data[
            "timestamp"], f"Current time {now} should be greater than response timestamp {json_data['timestamp']}"
        try:
            base64.b64decode(json_data['processed_frame'])
        except Exception:
            pytest.fail("Invalid base64 image received")
    time.sleep(2)

    log_file = settings.LOGS_FOLDER / "fire-smoke.log"
    assert log_file.exists(), f"Log file {log_file} does not exist"
    assert log_file.stat().st_size > 0, "Log file is empty"

    # Проверяем содержимое лог-файла
    with open(log_file, "r") as f:
        lines = f.readlines()

    assert len(lines) > 0, "Log file has no content"

    # Проверяем формат каждой строки
    for i, line in enumerate(lines):
        assert line.startswith("Detector 1."), \
            f"Line {i + 1} does not start with 'Detector 1.': {line.strip()}"


def test_available_models(test_app):
    response = test_app.get("/api/models")
    models = response.json()
    models_path = settings.MODELS_FOLDER
    for model_path in models_path.glob("*.pt"):
        model_name = model_path.stem
        dont_exist = True
        for model in models:
            if model['name'] == model_name:
                dont_exist = False
        assert not dont_exist, f"Expecting found {model_name} model, but not found"


def test_video_feed_websocket():
    with websockets.connect("ws://backend:8000/api/ws/video_feed") as ws:
        frames_folder = settings.TEST_FOLDER / "frames"
        frames = frames_folder.glob("*.jpg")
        colors = [(255, 0, 0), (0, 0, 255)]
        ws.send(json.dumps({
            "model_name": "fire-smoke",
            "confidence": 0.5,
            "colors": json.dumps(colors)
        }))
        for frame_file in frames:
            with open(frame_file, "rb") as f:
                frame_content = f.read()

            ws.send(frame_content)

            processed = ws.recv()
            assert len(processed) > 0

            try:
                base64.b64decode(processed)
            except Exception:
                pytest.fail("Invalid base64 image received")
