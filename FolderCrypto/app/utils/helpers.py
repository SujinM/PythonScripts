"""Helper utilities."""

import os
import sys
from pathlib import Path
from typing import Optional


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Formatted size string.
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def validate_path(path: str, must_exist: bool = False) -> Path:
    """Validate and convert path string to Path object.

    Args:
        path: Path string.
        must_exist: Whether path must exist.

    Returns:
        Path object.

    Raises:
        ValueError: If path is invalid.
    """
    if not path:
        raise ValueError("Path cannot be empty")

    path_obj = Path(path).resolve()

    if must_exist and not path_obj.exists():
        raise ValueError(f"Path does not exist: {path}")

    return path_obj


def clear_screen() -> None:
    """Clear terminal screen."""
    os.system("cls" if sys.platform == "win32" else "clear")


def confirm_action(message: str, default: bool = False) -> bool:
    """Prompt user for confirmation.

    Args:
        message: Confirmation message.
        default: Default value if user presses Enter.

    Returns:
        True if user confirms, False otherwise.
    """
    default_str = "Y/n" if default else "y/N"
    response = input(f"{message} [{default_str}]: ").strip().lower()

    if not response:
        return default

    return response in ["y", "yes"]


def get_folder_size(path: Path) -> int:
    """Calculate total size of a folder.

    Args:
        path: Folder path.

    Returns:
        Total size in bytes.
    """
    total_size = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total_size += item.stat().st_size
            except (OSError, PermissionError):
                pass
    return total_size


def create_backup_name(original_path: Path) -> Path:
    """Create a backup filename that doesn't conflict.

    Args:
        original_path: Original path.

    Returns:
        Backup path that doesn't exist.
    """
    counter = 1
    while True:
        backup_path = original_path.parent / f"{original_path.name}.backup{counter}"
        if not backup_path.exists():
            return backup_path
        counter += 1
