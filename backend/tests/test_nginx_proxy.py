# test_nginx_proxy.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import os
from PIL import Image
from io import BytesIO
# from main import app
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# @pytest.fixture(scope="module")
# def client():
#     with TestClient(base_url="https://localhost:8000", app=app) as client:
#         yield client


@pytest.mark.anyio
def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# # Фикстура для асинхронного клиента
# @pytest_asyncio.fixture(scope="module")
# async def client():
#     async with httpx.AsyncClient(base_url="http://nginx", timeout=1000000) as client:
#         yield client
#
#
# # Тест: Статические файлы фронтенда
# @pytest.mark.asyncio
# async def test_frontend_serving(client):
#     response = await client.get("/")
#     assert response.status_code == 200
#     # assert "text/html" in response.headers["content-type"]
#
#
# # Тест: Проксирование API запросов
# @pytest.mark.asyncio
# async def test_api_proxy(client):
#     response = await client.get("/api/models")
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
#
#
# # Тест: Доступ к обработанным файлам
# @pytest.mark.asyncio
# async def test_processed_files_access(client):
#     # Создаем тестовый файл
#     test_file = "/app/shared_volume/processed/test.jpg"
#     Image.new("RGB", (100, 100)).save(test_file)
#
#     response = await client.get("/processed/test.jpg")
#     assert response.status_code == 200
#     assert "image/jpeg" in response.headers["content-type"]
#     os.remove(test_file)
#
#
# # Тест: Большие файлы (превышение лимита)
# @pytest.mark.asyncio
# async def test_large_file_upload(client):
#     large_file = b"a" * (101 * 1024 * 1024)  # 101MB
#     files = {"file": ("large_file.bin", large_file)}
#     response = await client.post("/upload/file/", files=files, data={
#         "confidence": "0.5",
#         "model_name": "default",
#         "colors": "[]"
#     })
#     assert response.status_code == 413  # Payload Too Large
