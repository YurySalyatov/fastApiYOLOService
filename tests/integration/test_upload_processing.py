# test_upload_processing.py
import pytest
import httpx
import asyncio
from PIL import Image
from io import BytesIO


# Генерация тестового изображения
def generate_test_image():
    img = Image.new("RGB", (800, 600), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_image_upload_processing():
    async with httpx.AsyncClient(base_url="http://backend:8000") as client:
        # Загрузка изображения
        test_image = generate_test_image()
        files = {"file": ("test.jpg", test_image)}
        data = {
            "confidence": "0.5",
            "model_name": "default",
            "colors": "[]"
        }

        response = await client.post("/upload/file/", files=files, data=data)
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        # Проверка статуса задачи
        for _ in range(10):  # Ожидание обработки
            await asyncio.sleep(1)
            response = await client.get(f"/api/tasks/{task_id}")
            status = response.json()["status"]
            if status == "SUCCESS":
                break

        assert response.json()["status"] == "SUCCESS"
        assert "processed_url" in response.json()["result"]


@pytest.mark.asyncio
async def test_camera_upload_processing():
    async with httpx.AsyncClient(base_url="http://nginx") as client:
        test_frame = generate_test_image()
        files = {"frame": ("frame.jpg", test_frame)}
        data = {
            "confidence": "0.5",
            "model_name": "default",
            "colors": "[]"
        }

        response = await client.post("/camera_upload/process_frame/", files=files, data=data)
        assert response.status_code == 200
        assert "processed_frame" in response.json()
