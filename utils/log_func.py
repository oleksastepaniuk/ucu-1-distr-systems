import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
import sys


def init_logger(
    logger_name: str,
    log_dir: str,
    log_level=logging.INFO,
    max_bytes=1048576,
    backup_count=3,
) -> logging.Logger:
    log_path = Path.cwd() / log_dir
    log_file = os.path.join(log_dir, f"{logger_name}.log")
    log_path.mkdir(exist_ok=True, parents=True)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # File Handler
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Stream Handler
    handler_stream = logging.StreamHandler(sys.stdout)
    handler_stream.setFormatter(formatter)
    logger.addHandler(handler_stream)

    return logger
