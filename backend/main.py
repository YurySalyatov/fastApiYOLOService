import uuid
import time
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.responses import RedirectResponse
from celery import Celery
from apscheduler.schedulers.background import BackgroundScheduler
from config import settings
from file_utils import load_model, get_colors, return_process_image
import json
from ultralytics import YOLO
import base64
from tasks import process_ws_frame, process_image_task, process_video_task, detect_list_of_frames
import asyncio
from anydetector import get_detector

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
celery = Celery(__name__, broker=settings.REDIS_URL, backend=settings.REDIS_URL)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600
)
# Инициализация папок
Path(settings.UPLOAD_FOLDER).mkdir(exist_ok=True, parents=True)
Path(settings.PROCESSED_FOLDER).mkdir(exist_ok=True, parents=True)
Path(settings.MODELS_FOLDER).mkdir(exist_ok=True, parents=True)


@app.get("/", include_in_schema=False)
async def redirect():
    return RedirectResponse("/health")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/upload/file/")
async def upload_file(
        file: UploadFile = File(...),
        confidence: str = Form(0.5),
        model_name: str = Form(settings.DEFAULT_MODEL),
        colors: str = Form(settings.DEFAULT_COLORS),
        custom_weights: UploadFile = File(settings.DEFAULT_CUSTOM_WEIGHTS)
):
    # Сохранение файла
    if colors is None:
        colors = []
    else:
        colors = json.loads(colors)
    confidence = float(confidence)
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in [".jpg", ".jpeg", ".png", ".mp4"]:
        raise HTTPException(400, "Unsupported file format")

    file_id = f"{uuid.uuid4()}{file_ext}"
    file_path = settings.UPLOAD_FOLDER / file_id

    with open(file_path, "wb") as buffer:
        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(413, "File too large")
        buffer.write(content)

    # Обработка задачи
    if file_ext == '.mp4':
        task = process_video_task.si(str(file_path), confidence, model_name, colors)
    else:
        task = process_image_task.si(str(file_path), confidence, model_name, colors)
    result = task.delay()
    print("task_id:", result.id)
    return JSONResponse({"task_id": result.id})


@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = celery.AsyncResult(task_id)
    # print(task.status, task.result if task.ready() else None)
    return JSONResponse({"status": task.status, "result": task.result if task.ready() else None})


@app.on_event("startup")
async def startup_event():
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_files, 'interval', minutes=30)
    scheduler.start()


def cleanup_files():
    now = time.time()
    for folder in [settings.UPLOAD_FOLDER, settings.PROCESSED_FOLDER]:
        for file_path in folder.glob('*'):
            if file_path.is_file() and (now - file_path.stat().st_mtime) > 3600:
                file_path.unlink()


@app.get("/api/models")
def get_available_models():
    models = []
    models_dir = settings.MODELS_FOLDER
    for pt_file in models_dir.glob("*.pt"):
        model_name = pt_file.stem
        model = YOLO(pt_file)
        classes = model.names
        colors = get_colors(len(classes))
        models.append({
            'name': model_name,
            'classes': classes,
            'colors': colors
        })

    return JSONResponse(models)


MAX_CAPACITY = 10
last_frames = []


@app.post("/camera_upload/process_frame/")
async def process_live_frame(
        frame: UploadFile = File(...),
        confidence: float = Form(...),
        model_name: str = Form(...),
        colors: str = Form(...)
):
    try:
        print("here")
        contents = await frame.read()
        print("here1")
        model = load_model(model_name)
        print("here2")
        detector = get_detector(model_name)
        print("here3")
        classes = model.names
        print("here4")
        buffer, boxes = return_process_image(model, classes, colors, contents, confidence)
        print("here5")
        last_frames.append(boxes)
        if len(last_frames) >= MAX_CAPACITY:
            task = detect_list_of_frames.si(detector, last_frames[:])
            result = task.delay()
            last_frames.clear()
        encoded_frame = base64.b64encode(buffer).decode('utf-8')
        return JSONResponse({
            "processed_frame": encoded_frame,
            "timestamp": int(time.time() * 1000)
        })

    except Exception as e:
        raise HTTPException(500, f"Frame processing error: {str(e)}")


# WebSocket-эндпоинт для потоковой обработки
@app.websocket("/api/ws/video_feed")
async def video_feed_websocket(websocket: WebSocket):
    await websocket.accept()
    init_data = await websocket.receive_json()
    model_name = init_data['model_name']
    confidence = init_data['confidence']
    colors = init_data['colors']
    try:
        while True:
            frame_data = await websocket.receive_bytes()

            task = process_ws_frame.delay(
                frame_data,
                model_name,
                confidence,
                colors
            )

            while not task.ready():
                await asyncio.sleep(0.001)

            result = task.result
            await websocket.send_bytes(result)
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
