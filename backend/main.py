import uuid
import time
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.responses import RedirectResponse
from celery import Celery
from apscheduler.schedulers.background import BackgroundScheduler
from config import settings
from file_utils import process_image, process_video, load_model, get_colors
import yaml
import json
from ultralytics import YOLO

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
    return RedirectResponse("/docs")


@app.post("/upload/")
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
    print(task.status, task.result if task.ready() else None)
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


@celery.task(name="process_image_task")
def process_image_task(input_path, confidence, model_name, colors):
    output_path = settings.PROCESSED_FOLDER / f"processed_{Path(input_path).name}"
    model = load_model(model_name)
    classes = model.names
    process_image(model, classes, colors, input_path, output_path, confidence)
    return str(output_path)


@celery.task(name="process_video_task")
def process_video_task(input_path, confidence, model_name, colors):
    output_path = settings.PROCESSED_FOLDER / f"processed_{Path(input_path).name}"
    model = load_model(model_name)
    classes = model.names
    process_video(model, classes, colors, input_path, output_path, confidence)
    return str(output_path)


@app.get("/api/models")
def get_available_models():
    model_default = YOLO('yolo12s.pt')
    models = [{'name': 'default yolo12s',
               'classes': model_default.names,
               'colors': get_colors(len(model_default.names))}]
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
