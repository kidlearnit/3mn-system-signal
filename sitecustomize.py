import logging
import os
from logging.handlers import RotatingFileHandler


def _init_file_logging() -> None:
    service = os.getenv("SERVICE_NAME", "app").lower()
    log_dir = "/code/logs"
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        # Fallback to current dir if /code/logs not writable
        log_dir = "./logs"
        os.makedirs(log_dir, exist_ok=True)

    logfile = os.path.join(log_dir, f"{service}.log")

    # Create handlers
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    file_handler = RotatingFileHandler(logfile, maxBytes=5 * 1024 * 1024, backupCount=5)
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    root = logging.getLogger()
    # Avoid duplicating handlers on reload
    existing = {type(h) for h in root.handlers}
    if RotatingFileHandler not in existing:
        root.addHandler(file_handler)
    if logging.StreamHandler not in existing:
        root.addHandler(stream_handler)
    # Default level
    if root.level == logging.NOTSET:
        root.setLevel(logging.INFO)


try:
    _init_file_logging()
except Exception:
    # Never break app startup due to logging init
    pass


