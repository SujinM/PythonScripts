"""
Logging utility for the WhatsApp Notification System.

Provides a centralized, configurable logger that outputs to console and
optionally to a rotating log file. All modules obtain their logger
through get_logger() to ensure consistent formatting.
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional


_loggers: dict[str, logging.Logger] = {}


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 5 * 1024 * 1024,   # 5 MB
    backup_count: int = 3,
) -> None:
    """
    Configure the root logger once at application start.

    Args:
        level:        Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file:     Optional path to the rotating log file.
        max_bytes:    Maximum size of a single log file before rotation.
        backup_count: Number of backup log files to keep.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid adding duplicate handlers when setup_logging is called multiple times
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Console handler — always active
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)
    root_logger.addHandler(console_handler)

    # File handler — active only when a path is supplied
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(numeric_level)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger, reusing cached instances.

    Args:
        name: Logger name — conventionally use __name__ of the calling module.

    Returns:
        logging.Logger instance.
    """
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    return _loggers[name]
