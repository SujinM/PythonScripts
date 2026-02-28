"""
Logging configuration for fingerprint sensor application.
"""
import logging
import os
from pathlib import Path
from typing import Optional

# Default log file path
DEFAULT_LOG_FILE = os.path.expanduser("~/.fingerprint_log.txt")

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console: bool = False
) -> None:
    """
    Set up logging configuration.
    
    Args:
        log_file: Path to log file (uses default if None)
        level: Logging level
        console: Whether to also log to console
    """
    log_path = log_file or DEFAULT_LOG_FILE
    
    # Ensure log directory exists
    log_dir = os.path.dirname(log_path)
    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    handlers = [logging.FileHandler(log_path)]
    
    if console:
        handlers.append(logging.StreamHandler())
    
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=handlers
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Initialize default logging
setup_logging()
