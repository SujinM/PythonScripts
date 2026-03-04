"""
constants.py
------------
Application-wide constants: paths, window geometry, table column indices,
polling frequency, and other magic numbers.

Import pattern::

    from plc_gui.constants import APP_NAME, POLL_INTERVAL_MS
"""

from __future__ import annotations

import sys
from pathlib import Path


def _get_root_dir() -> Path:
    """
    Get the application root directory.
    
    When running as a frozen executable (cx_Freeze), the root is the
    directory containing the .exe. When running from source, it's
    the plc_gui_project/ directory.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable - resources are relative to exe
        return Path(sys.executable).parent
    else:
        # Running in development - resources are relative to this file
        # plc_gui_project/src/plc_gui/constants.py -> plc_gui_project/
        return Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Filesystem paths
# ---------------------------------------------------------------------------
ROOT_DIR: Path = _get_root_dir()
SRC_DIR: Path = ROOT_DIR / "src"
RESOURCES_DIR: Path = ROOT_DIR / "resources"
STYLES_DIR: Path = RESOURCES_DIR / "styles"
ICONS_DIR: Path = RESOURCES_DIR / "icons"

# Sibling plc_ads_project that provides the backend services (dev only)
ADS_BACKEND_DIR: Path = ROOT_DIR.parent / "plc_ads_project"

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------
APP_NAME: str = "TwinCAT 3 PLC Monitor"
APP_VERSION: str = "1.0.0"
ORG_NAME: str = "TwinCAT Tools"
APP_ID: str = "com.twincattools.plcmonitor"

# ---------------------------------------------------------------------------
# Main window sizing
# ---------------------------------------------------------------------------
WINDOW_MIN_WIDTH: int = 1100
WINDOW_MIN_HEIGHT: int = 700
WINDOW_DEFAULT_WIDTH: int = 1280
WINDOW_DEFAULT_HEIGHT: int = 800

# ---------------------------------------------------------------------------
# Polling / timing
# ---------------------------------------------------------------------------
POLL_INTERVAL_MS: int = 500           # milliseconds between background read_all passes
CONNECTION_TIMEOUT_S: int = 5         # seconds before a connect attempt is declared failed
WORKER_POOL_MAX_THREADS: int = 4

# ---------------------------------------------------------------------------
# Variable table columns
# ---------------------------------------------------------------------------
VAR_COL_NAME: int = 0
VAR_COL_TYPE: int = 1
VAR_COL_VALUE: int = 2
VAR_COL_UPDATED: int = 3
VAR_COLUMNS: list[str] = ["Variable Name", "Type", "Value", "Last Updated"]

# ---------------------------------------------------------------------------
# Log table columns
# ---------------------------------------------------------------------------
LOG_COL_TIME: int = 0
LOG_COL_LEVEL: int = 1
LOG_COL_MODULE: int = 2
LOG_COL_MSG: int = 3
LOG_COLUMNS: list[str] = ["Time", "Level", "Module", "Message"]
LOG_MAX_ROWS: int = 500           # rows kept before the oldest are dropped

# ---------------------------------------------------------------------------
# Status colours (used as Qt stylesheet snippets)
# ---------------------------------------------------------------------------
STATUS_CONNECTED: str = "#27ae60"       # green
STATUS_DISCONNECTED: str = "#e74c3c"    # red
STATUS_CONNECTING: str = "#f39c12"      # amber

# ---------------------------------------------------------------------------
# QSettings keys
# ---------------------------------------------------------------------------
SETTING_THEME: str = "appearance/theme"
SETTING_CONFIG_PATH: str = "plc/config_path"
SETTING_POLL_ENABLED: str = "plc/poll_enabled"
SETTING_WINDOW_GEOMETRY: str = "window/geometry"
SETTING_WINDOW_STATE: str = "window/state"
SETTING_SPLITTER_STATE: str = "window/splitter_state"
