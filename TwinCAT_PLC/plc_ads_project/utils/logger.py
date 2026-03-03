"""
logger.py
---------
Centralized logging configuration for the PLC ADS project.

Provides:
    - Rotating file handler to avoid unbounded log file growth.
    - Colourised console handler for rapid development feedback.
    - A thin ``get_logger`` factory so every module receives a child logger
      that inherits the root configuration automatically.

Usage::

    from utils.logger import setup_logger, get_logger

    # Call once at application startup (e.g. in main.py)
    setup_logger(log_level=logging.DEBUG, log_file="logs/plc_ads.log")

    # In every module that needs logging
    log = get_logger(__name__)
    log.info("PLC connection established")
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from typing import Optional


# ---------------------------------------------------------------------------
# ANSI colour codes for console output
# ---------------------------------------------------------------------------
_RESET = "\033[0m"
_COLOURS: dict[int, str] = {
    logging.DEBUG:    "\033[36m",   # Cyan
    logging.INFO:     "\033[32m",   # Green
    logging.WARNING:  "\033[33m",   # Yellow
    logging.ERROR:    "\033[31m",   # Red
    logging.CRITICAL: "\033[35m",   # Magenta
}

# Root logger name used throughout the project.
_ROOT_LOGGER_NAME = "plc_ads"

# Maximum size of a single log file (10 MB).
_MAX_LOG_BYTES = 10 * 1024 * 1024

# Number of rotated backup files to keep.
_BACKUP_COUNT = 5


class _ColourisedFormatter(logging.Formatter):
    """
    A :class:`logging.Formatter` subclass that prepends ANSI colour codes to
    each log record based on severity.  Falls back to plain text when the
    output stream does not support colour (e.g. redirected to a file).
    """

    def __init__(self, fmt: str, datefmt: Optional[str] = None, use_colour: bool = True) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt)
        self._use_colour = use_colour

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        formatted = super().format(record)
        if self._use_colour:
            colour = _COLOURS.get(record.levelno, _RESET)
            return f"{colour}{formatted}{_RESET}"
        return formatted


def setup_logger(
    log_level: int = logging.DEBUG,
    log_file: str = "logs/plc_ads.log",
    *,
    enable_console: bool = True,
    enable_file: bool = True,
) -> logging.Logger:
    """
    Configure the project-wide root logger.

    This function is **idempotent** – calling it multiple times does not
    add duplicate handlers.  It should be invoked once during application
    startup before any other module attempts to obtain a logger.

    Args:
        log_level:       Minimum severity level for both handlers.
        log_file:        Path to the rotating log file.  The parent directory
                         is created automatically if it does not exist.
        enable_console:  When *True*, attach a stderr console handler.
        enable_file:     When *True*, attach a rotating file handler.

    Returns:
        The configured root logger for this project.
    """
    logger = logging.getLogger(_ROOT_LOGGER_NAME)

    # Guard against re-initialisation (e.g. during unit tests).
    if logger.handlers:
        return logger

    logger.setLevel(log_level)

    _fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    _datefmt = "%Y-%m-%d %H:%M:%S"

    # -----------------------------------------------------------------------
    # Console handler
    # -----------------------------------------------------------------------
    if enable_console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(log_level)

        # Detect colour support: enabled when stderr is a real TTY and we are
        # not on Windows without ANSI support.
        use_colour = hasattr(sys.stderr, "isatty") and sys.stderr.isatty()
        console_handler.setFormatter(
            _ColourisedFormatter(fmt=_fmt, datefmt=_datefmt, use_colour=use_colour)
        )
        logger.addHandler(console_handler)

    # -----------------------------------------------------------------------
    # Rotating file handler
    # -----------------------------------------------------------------------
    if enable_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=_MAX_LOG_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(
            logging.Formatter(fmt=_fmt, datefmt=_datefmt)
        )
        logger.addHandler(file_handler)

    logger.propagate = False
    logger.info("Logger initialised. level=%s file=%s", logging.getLevelName(log_level), log_file)
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger under the project root namespace.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A :class:`logging.Logger` instance named ``plc_ads.<name>``.

    Example::

        log = get_logger(__name__)
        log.debug("Detailed diagnostic message")
    """
    # Strip the package prefix if ``name`` already starts with the root name
    # to avoid double-prefixing (e.g. ``plc_ads.plc_ads.core.ads_client``).
    if name.startswith(_ROOT_LOGGER_NAME):
        child_name = name
    else:
        child_name = f"{_ROOT_LOGGER_NAME}.{name}"
    return logging.getLogger(child_name)
