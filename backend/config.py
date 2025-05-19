from pathlib import Path


class Settings:
    REDIS_URL = "redis://redis:6379/0"
    ROOT = Path(__file__).parent.parent
    BASE_DIR = Path('/app/' + str(ROOT))
    UPLOAD_FOLDER = BASE_DIR / "shared_volume/uploads"
    PROCESSED_FOLDER = BASE_DIR / "shared_volume/processed"
    MODELS_FOLDER = BASE_DIR / "shared_volume/models"
    # MODELS_FOLDER = Path("/app/" + str(MODELS_FOLDER))
    DEFAULT_COLORS = []
    DEFAULT_CUSTOM_WEIGHTS = None
    MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB
    DEFAULT_MODEL = "yolo12s"


settings = Settings()