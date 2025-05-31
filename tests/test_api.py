# import pytest
# import httpx
# import uuid
# import os
# from pathlib import Path
# from fastapi import status
# import json
# import asyncio
#
# BASE_URL = "http://localhost:8000"
# TEST_DIR = Path(__file__).parent / "test_dir"
# TIMEOUT = 30  # Увеличенный таймаут для обработки видео
#
#
# @pytest.fixture(scope="module")
# def test_image():
#     return TEST_DIR / "fire_example.png"
#
#
# @pytest.fixture(scope="module")
# def test_video():
#     return TEST_DIR / "fire-smoke.mp4"
#
#
# @pytest.fixture(scope="module")
# def test_frames_dir():
#     return TEST_DIR / "frames"
#
#
# @pytest.mark.asyncio
# async def test_upload_image(test_image):
#     async with httpx.AsyncClient() as client:
#         with open(test_image, "rb") as f:
#             files = {"file": (test_image.name, f, "image/png")}
#             data = {
#                 "confidence": "0.5",
#                 "model_name": "yolo12s",
#                 "colors": json.dumps([])
#             }
#             response = await client.post(
#                 f"{BASE_URL}/upload/file",
#                 data=data,
#                 files=files,
#                 timeout=TIMEOUT
#             )
#         assert response.status_code == status.HTTP_200_OK
#         task_id = response.json()["task_id"]
#         assert uuid.UUID(task_id, version=4) is not None
#
#         # Проверяем статус задачи
#         status_url = f"{BASE_URL}/api/tasks/{task_id}"
#         for _ in range(10):  # Ожидаем завершения обработки
#             status_resp = await client.get(status_url)
#             if status_resp.json()["status"] == "SUCCESS":
#                 break
#             await asyncio.sleep(1)
#
#         assert status_resp.json()["status"] == "SUCCESS"
#         assert "processed_" in status_resp.json()["result"]
#
#
# @pytest.mark.asyncio
# async def test_upload_video(test_video):
#     async with httpx.AsyncClient() as client:
#         with open(test_video, "rb") as f:
#             files = {"file": (test_video.name, f, "video/mp4")}
#             data = {
#                 "confidence": "0.5",
#                 "model_name": "yolo12s",
#                 "colors": json.dumps([])
#             }
#             response = await client.post(
#                 f"{BASE_URL}/upload/file",
#                 data=data,
#                 files=files,
#                 timeout=TIMEOUT * 2  # Увеличенный таймаут для видео
#             )
#         assert response.status_code == status.HTTP_200_OK
#         task_id = response.json()["task_id"]
#
#         # Проверяем статус задачи
#         status_url = f"{BASE_URL}/api/tasks/{task_id}"
#         success = False
#         for _ in range(30):  # Дольше ждем обработку видео
#             status_resp = await client.get(status_url)
#             if status_resp.json()["status"] == "SUCCESS":
#                 success = True
#                 break
#             await asyncio.sleep(2)
#
#         assert success, "Video processing timed out"
#         assert "processed_" in status_resp.json()["result"]
#
#
# @pytest.mark.asyncio
# async def test_get_models():
#     async with httpx.AsyncClient() as client:
#         response = await client.get(f"{BASE_URL}/api/models")
#         assert response.status_code == status.HTTP_200_OK
#         models = response.json()
#         assert isinstance(models, list)
#         if len(models) > 0:
#             model = models[0]
#             assert "name" in model
#             assert "classes" in model
#             assert "colors" in model
#
#
# @pytest.mark.asyncio
# async def test_process_frame(test_image):
#     async with httpx.AsyncClient() as client:
#         with open(test_image, "rb") as f:
#             files = {"frame": (test_image.name, f, "image/png")}
#             data = {
#                 "confidence": "0.5",
#                 "model_name": "yolo12s",
#                 "colors": json.dumps([])
#             }
#             response = await client.post(
#                 f"{BASE_URL}/camera_upload/process_frame/",
#                 data=data,
#                 files=files,
#                 timeout=TIMEOUT
#             )
#         assert response.status_code == status.HTTP_200_OK
#         result = response.json()
#         assert "processed_frame" in result
#         assert "timestamp" in result
#         assert isinstance(result["timestamp"], int)
#
#
# @pytest.mark.asyncio
# async def test_frames_processing(test_frames_dir):
#     """Тестируем обработку потока кадров и генерацию логов"""
#     log_file = "shared_volume/logs/fire-smoke_logs.txt"
#     if os.path.exists(log_file):
#         os.remove(log_file)  # Очищаем предыдущие логи
#
#     async with httpx.AsyncClient() as client:
#         for frame_path in test_frames_dir.iterdir():
#             if frame_path.is_file() and frame_path.suffix in [".jpg", ".png"]:
#                 with open(frame_path, "rb") as f:
#                     files = {"frame": (frame_path.name, f, "image/jpeg")}
#                     data = {
#                         "confidence": "0.5",
#                         "model_name": "fire-smoke",  # Используем специальный детектор
#                         "colors": json.dumps([])
#                     }
#                     response = await client.post(
#                         f"{BASE_URL}/camera_upload/process_frame/",
#                         data=data,
#                         files=files,
#                         timeout=TIMEOUT
#                     )
#                 assert response.status_code == status.HTTP_200_OK
#
#         # Проверяем наличие логов
#         await asyncio.sleep(2)  # Даем время на запись логов
#         assert os.path.exists(log_file), "Log file not created"
#         with open(log_file, "r") as f:
#             log_content = f.read()
#             assert "Detector 1" in log_content
#             assert "fire" in log_content or "smoke" in log_content