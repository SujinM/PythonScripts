"""
app/core/logger.py
──────────────────
Structured logging factory used across the application.

Logs go to both:
  • stdout (always)
  • logs/app.log — rotating file, 5 MB per file, 5 backups kept
    (path is configured via LOG_FILE in .env; set LOG_FILE=off to disable)
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import get_settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_file_handler: RotatingFileHandler | None = None


def _get_file_handler() -> RotatingFileHandler | None:
    """Create the shared rotating file handler once; return None if disabled."""
    global _file_handler
    if _file_handler is not None:
        return _file_handler

    log_path = get_settings().log_file
    if not log_path or log_path.lower() == "off":
        return None

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    _file_handler = RotatingFileHandler(
        path,
        maxBytes=5 * 1024 * 1024,  # 5 MB per file
        backupCount=5,
        encoding="utf-8",
    )
    _file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    return _file_handler


def get_logger(name: str) -> logging.Logger:
    settings = get_settings()
    logger = logging.getLogger(name)

    if not logger.handlers:
        # Console handler
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
        logger.addHandler(console)

        # File handler (skipped if LOG_FILE=off)
        fh = _get_file_handler()
        if fh:
            logger.addHandler(fh)

        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        logger.propagate = False

    return logger
