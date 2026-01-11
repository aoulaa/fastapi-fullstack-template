import logging
import os

from app.core import logger


def test_log_directory_creation():
    # Helper to check if logs dir was created
    log_dir = logger.LOG_DIR
    assert os.path.exists(log_dir)
    assert os.path.isdir(log_dir)


def test_logger_file():
    log_file = logger.LOG_FILE_PATH
    # Maybe check if file exists, or if logger has handlers
    logger_instance = logging.getLogger("")
    handlers = [h for h in logger_instance.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
    assert len(handlers) > 0
    assert handlers[0].baseFilename == log_file
