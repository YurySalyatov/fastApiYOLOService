from pathlib import Path
import logging


class Settings:
    REDIS_URL = "redis://redis:6379/0"
    ROOT = Path(__file__).parent.parent.parent.parent.parent
    # print(ROOT)
    BASE_DIR = Path('/app/' + str(ROOT))
    UPLOAD_FOLDER = BASE_DIR / "shared_volume/uploads"
    PROCESSED_FOLDER = BASE_DIR / "shared_volume/processed"
    MODELS_FOLDER = BASE_DIR / "shared_volume/models"
    LOGS_FOLDER = BASE_DIR / "shared_volume/logs"
    TEST_FOLDER = BASE_DIR / "test_dir"
    DEFAULT_COLORS = []
    DEFAULT_CUSTOM_WEIGHTS = None
    MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB
    DEFAULT_MODEL = "yolo12s"
    # change to false in prod
    DEBUG = False
    MAX_TIME_FILES_LIVE = 360



settings = Settings()

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
settings.LOGS_FOLDER.mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler(settings.LOGS_FOLDER / "app.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
