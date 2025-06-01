# test_websocket.py
import pytest
import websockets
import json
import asyncio
import base64
from test_upload_processing import generate_test_image


@pytest.mark.asyncio
async def test_video_feed_websocket():
    async with websockets.connect("ws://backend:8000/api/ws/video_feed") as ws:
        # Инициализация
        await ws.send(json.dumps({
            "model_name": "default",
            "confidence": 0.5,
            "colors": []
        }))

        # Отправка тестового кадра
        test_frame = generate_test_image()
        await ws.send(test_frame)

        # Получение обработанного кадра
        processed = await asyncio.wait_for(ws.recv(), timeout=10.0)
        assert len(processed) > 0

        # Проверка валидности изображения
        try:
            base64.b64decode(processed)
        except Exception:
            pytest.fail("Invalid base64 image received")