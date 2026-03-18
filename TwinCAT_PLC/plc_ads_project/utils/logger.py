''' Centralized logging configuration for the PLC ADS project.

    Usage::

    from utils.logger import setup_logger, get_logger, set_correlation_id

    # Call once at application startup (e.g. in main.py)
    setup_logger(log_level=logging.DEBUG, log_file="logs/plc_ads.log")

    # In every module that needs logging
    log = get_logger(__name__)
    log.info("PLC connection established")

    # Optional: override log level via environment variable LOG_LEVEL=WARNING
    # Optional: use JSON output via use_json=True for log aggregators
    # Optional: tag concurrent operations with a correlation ID (for async / multi-request apps)
        - Useful when multiple PLC connections run concurrently
        - set_correlation_id("plc-session-1")
'''

from __future__ import annotations

import contextvars
import json
import logging
import logging.handlers
import os
import sys
import threading
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

# Thread-safety lock for setup_logger.
_setup_lock = threading.Lock()

# Correlation ID context variable (per-thread / per-async-task).
_correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="-")


def set_correlation_id(value: str) -> None:
    """Set a correlation ID that will appear in every subsequent log record."""
    _correlation_id.set(value)


def _enable_windows_ansi() -> None:
    """Enable ANSI escape codes on Windows 10+ consoles."""
    import ctypes
    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    # STD_ERROR_HANDLE = -12, ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    handle = kernel32.GetStdHandle(-12)
    mode = ctypes.c_ulong()
    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)

class _CorrelationFilter(logging.Filter):
    """Injects the current correlation ID into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.correlation_id = _correlation_id.get()  # type: ignore[attr-defined]
        return True


class _ColourisedFormatter(logging.Formatter):
    """Custom formatter that adds ANSI colour codes to console log messages."""

    def __init__(self, fmt: str, datefmt: Optional[str] = None, use_colour: bool = True) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt)
        self._use_colour = use_colour

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        formatted = super().format(record)
        if self._use_colour:
            colour = _COLOURS.get(record.levelno, _RESET)
            return f"{colour}{formatted}{_RESET}"
        return formatted


class _JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON for log aggregators."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        payload: dict = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "file": f"{record.filename}:{record.lineno}",
            "correlation_id": getattr(record, "correlation_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)
    
def setup_logger(
    log_level: int = logging.DEBUG,
    log_file: str = "logs/plc_ads.log",
    *,
    enable_console: bool = True,
    enable_file: bool = True,
    use_json: bool = False,
) -> logging.Logger:
    """Configure the root logger for the PLC ADS project.

    The ``LOG_LEVEL`` environment variable (e.g. ``WARNING``) overrides
    *log_level* when set.

    Args:
        log_level:       Minimum severity level for both handlers.
        log_file:        Path to the rotating log file.  The parent directory
                         is created automatically if it does not exist.
        enable_console:  When *True*, attach a stderr console handler.
        enable_file:     When *True*, attach a rotating file handler.
        use_json:        When *True*, emit JSON lines instead of plain text
                         (useful for log aggregators such as Loki / Splunk).
    Returns:
        The configured root logger for this project.
    """
    # Allow environment variable to override the programmatic log level.
    _env = os.getenv("LOG_LEVEL", "").upper()
    if _env and hasattr(logging, _env):
        log_level = getattr(logging, _env)

    with _setup_lock:
        logger = logging.getLogger(_ROOT_LOGGER_NAME)

        # Guard against re-initialisation (e.g. during unit tests).
        if logger.handlers:
            return logger

        logger.setLevel(log_level)

        _fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | [%(correlation_id)s] | %(message)s"
        _datefmt = "%Y-%m-%d %H:%M:%S"
        _filter = _CorrelationFilter()

        # -----------------------------------------------------------------------
        # Console handler
        # -----------------------------------------------------------------------
        if enable_console:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(log_level)
            console_handler.addFilter(_filter)

            if use_json:
                console_handler.setFormatter(_JsonFormatter(datefmt=_datefmt))
            else:
                # Enable ANSI colours when stderr is a real TTY.
                use_colour = hasattr(sys.stderr, "isatty") and sys.stderr.isatty()
                if use_colour and sys.platform == "win32":
                    try:
                        _enable_windows_ansi()
                    except Exception:
                        use_colour = False
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
            file_handler.addFilter(_filter)
            file_handler.setFormatter(
                _JsonFormatter(datefmt=_datefmt) if use_json
                else logging.Formatter(fmt=_fmt, datefmt=_datefmt)
            )
            logger.addHandler(file_handler)

        logger.propagate = False
        logger.info("Logger initialised. level=%s file=%s json=%s", log_level, log_file, use_json)
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
    if name.startswith(_ROOT_LOGGER_NAME):
        child_name = name
    else:
        child_name = f"{_ROOT_LOGGER_NAME}.{name}"
    return logging.getLogger(child_name)