import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.getenv("LOG_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs"))

try:
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)
    LOG_FILE_PATH = os.path.join(LOG_DIR, "app.log")
    HAS_FILE_LOGGING = True
except Exception as e:
    print(f"Warning: Could not initialize file logging: {e}. Falling back to console logging.")
    HAS_FILE_LOGGING = False

LOGGING_LEVEL = logging.INFO
LOGGING_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(level=LOGGING_LEVEL, format=LOGGING_FORMAT)

if HAS_FILE_LOGGING:
    try:
        file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=10485760, backupCount=5)
        file_handler.setLevel(LOGGING_LEVEL)
        file_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
        logging.getLogger("").addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Failed to add file handler: {e}")
