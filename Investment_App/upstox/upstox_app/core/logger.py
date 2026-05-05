"""
Centralized logging configuration.

Provides a factory function that returns named loggers with a consistent
format.  The log level is sourced from the LOG_LEVEL environment variable
(default: INFO).

Usage:
    from upstox_app.core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Service started.")
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Return a configured logger for the given module name.

    If the logger already has handlers it is returned as-is, so calling
    get_logger multiple times for the same name is safe.

    Args:
        name:  Logger name — use ``__name__`` for per-module loggers.
        level: Optional log-level override (e.g. "DEBUG").
               Falls back to the LOG_LEVEL environment variable, then INFO.

    Returns:
        A fully configured :class:`logging.Logger` instance.
    """
    import os

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when the logger is retrieved repeatedly
    if logger.handlers:
        return logger

    # Resolve log level: explicit arg > env var > INFO
    resolved_level_str = level or os.getenv("LOG_LEVEL", "INFO")
    resolved_level = getattr(logging, resolved_level_str.upper(), logging.INFO)

    logger.setLevel(resolved_level)
    logger.propagate = False  # Don't bubble up to the root logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(resolved_level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)

    return logger
