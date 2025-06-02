# test_upload_processing.py
import pytest
import pytest_asyncio
import httpx
import asyncio
from PIL import Image
from io import BytesIO
import time
import json

# Генерация тестового изображения
def generate_test_image():
    img = Image.new("RGB", (800, 600), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_image_upload_processing(test_app):
    # Загрузка изображения
    test_image = generate_test_image()
    files = {
        "file": ("test_image.jpg", test_image, "image/jpeg")
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
    # Генерация тестового изображения
    print("Generating test image...")
    test_frame = generate_test_image()
    print("Test image generated")

    # Подготовка данных
    print("Preparing request data...")
    files = {
        "frame": ("test_image.jpg", test_frame, "image/jpeg")
    }
    colors = [(255, 0, 0), (0, 255, 0)]
    data = {
        "confidence": "0.5",
        "model_name": "fire-smoke",
        "colors": json.dumps(colors)
    }
    print(f"Request data: {data}")

    # Отправка запроса
    print("Sending POST request to /camera_upload/process_frame/")
    response = test_app.post("/camera_upload/process_frame/", files=files, data=data)
    print(f"Status code: {response.status_code}")

    # Вывод ответа
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))

    # Проверки и вывод их результатов
    now = int(time.time() * 1000)
    print(f"Current timestamp (ms): {now}")

    print("Running assertions:")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("✓ Status code 200 OK")

    json_data = response.json()
    assert "processed_frame" in json_data, "processed_frame not in response"
    print("✓ processed_frame found in response")

    assert "timestamp" in json_data, "timestamp not in response"
    print(f"✓ timestamp found: {json_data['timestamp']}")

    assert now > json_data[
        "timestamp"], f"Current time {now} should be greater than response timestamp {json_data['timestamp']}"
    print("✓ Current time > response timestamp")

    assert json_data[
               "timestamp"] + 2000 > now, f"Response timestamp {json_data['timestamp']} + 2000 should be greater than current time {now}"
    print("✓ Response timestamp + 2000 > current time")

    print("✓ All assertions passed!")
