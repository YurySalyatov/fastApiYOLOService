import uuid
import time
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from celery import Celery
from apscheduler.schedulers.background import BackgroundScheduler
import json
from ultralytics import YOLO
import base64
import asyncio
import cv2
import numpy as np

from app.config import settings, logger
from app.tasks import process_image_task, process_video_task, process_camera_frames
from app.file_utils import load_model, get_colors, return_process_image

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
celery = Celery(__name__,
                broker=settings.REDIS_URL,
                backend=settings.REDIS_URL,
                )

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
Path(settings.LOGS_FOLDER).mkdir(exist_ok=True, parents=True)


@app.on_event("startup")
async def startup_event():
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_files, 'interval', minutes=1)
    scheduler.start()
    logger.info("Application started")


def cleanup_files():
    now = time.time()
    for folder in [settings.UPLOAD_FOLDER, settings.PROCESSED_FOLDER]:
        for file_path in folder.glob('*'):
            if file_path.is_file() and (now - file_path.stat().st_mtime) > settings.MAX_TIME_FILES_LIVE:
                file_path.unlink()


@app.get("/", include_in_schema=False)
async def redirect():
    return RedirectResponse("/health/")


@app.get("/health/")
async def health_check():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Frame processing error: {str(exc)}",
                "traceback": traceback.format_exc()
            }
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


@app.post("/upload/file/")
async def upload_file(
        file: UploadFile = File(...),
        confidence: str = Form(0.5),
        model_name: str = Form(settings.DEFAULT_MODEL),
        colors: str = Form(settings.DEFAULT_COLORS),
        custom_weights: UploadFile = File(settings.DEFAULT_CUSTOM_WEIGHTS)
):
    logger.info("Used upload/file/ to detect one file")
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


@app.get("/api/tasks/{task_id}/")
async def get_task_status(task_id: str):
    task = celery.AsyncResult(task_id)
    # print(task.status, task.result if task.ready() else None)
    logger.info(f"Used /api/tasks/{task_id}")
    return JSONResponse({"status": task.status, "result": task.result if task.ready() else None})


@app.get("/api/models/")
def get_available_models():
    models = []
    print(settings.ROOT)
    logger.info("Used /api/models/")
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
last_camera_frames = []


@app.post("/camera_upload/process_frame/")
async def process_live_frame(
        frame: UploadFile = File(...),
        confidence: str = Form(...),
        model_name: str = Form(...),
        colors: str = Form(...)
):
    try:
        colors = json.loads(colors)
        confidence = float(confidence)
        file_ext = Path(frame.filename).suffix.lower()
        logger.info("Used /camera_upload/process_frame/ to detect one file")

        file_id = f"{uuid.uuid4()}{file_ext}"
        file_path = settings.UPLOAD_FOLDER / file_id

        with open(file_path, "wb") as buffer:
            content = await frame.read()
            if len(content) > settings.MAX_FILE_SIZE:
                raise HTTPException(413, "File too large")
            buffer.write(content)
        model = load_model(model_name)
        classes = model.names
        buffer, boxes = return_process_image(model, classes, colors, file_path, confidence)
        last_camera_frames.append(boxes)
        if len(last_camera_frames) >= MAX_CAPACITY:
            task = process_camera_frames.si(model_name, last_camera_frames[:])
            task.delay()
            last_camera_frames.clear()
            logger.info("Process 10 frames in /camera_upload/process_frame/")
        encoded_frame = base64.b64encode(buffer).decode('utf-8')
        return JSONResponse({
            "processed_frame": encoded_frame,
            "timestamp": int(time.time() * 1000)
        })

    except Exception as e:
        print(e)
        raise HTTPException(500, f"Frame processing error: {str(e)}")


last_ws_frames = []


@app.websocket("/api/ws/video_feed/")
async def video_feed_websocket(websocket: WebSocket):
    await websocket.accept()
    init_data = await websocket.receive_json()
    model_name = init_data['model_name']
    confidence = init_data['confidence']
    colors = init_data['colors']
    colors = json.loads(colors)
    logger.info(
        f"Used /api/ws/video_feed/ to detect one file model: {model_name}, confidence: {confidence}, colors: {colors}")
    try:
        while True:
            frame_data = await websocket.receive_bytes()
            logger.info("Receive one frame on websocket")
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            file_id = f"{uuid.uuid4()}.jpg"
            file_path = settings.UPLOAD_FOLDER / file_id
            cv2.imwrite(file_path, frame)
            model = load_model(model_name)
            classes = model.names
            logger.info("Before process")
            processed, boxex = return_process_image(
                model,
                classes,
                colors,
                file_path,
                confidence
            )
            logger.info("Return processed from websocket")
            # Конвертация в bytes
            _, buffer = cv2.imencode('.jpg', processed)
            last_ws_frames.append(boxex)
            if len(last_ws_frames) >= MAX_CAPACITY:
                task = process_camera_frames.si(model_name, last_ws_frames[:])
                task.delay()
                last_ws_frames.clear()
                logger.info("Process 10 frames in /api/ws/video_feed/")
            await websocket.send_bytes(buffer.tobytes())
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
