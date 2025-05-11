from pathlib import Path


class Settings:
    REDIS_URL = "redis://redis:6379/0"
    BASE_DIR = Path(__file__).parent.parent
    UPLOAD_FOLDER = BASE_DIR / "shared_volume/uploads"
    PROCESSED_FOLDER = BASE_DIR / "shared_volume/processed"
    MODELS_FOLDER = BASE_DIR / "shared_volume/models"
    MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB
    DEFAULT_MODEL = "yolo12s"


settings = Settings()