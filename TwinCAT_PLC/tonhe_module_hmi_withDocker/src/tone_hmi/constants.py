"""
constants.py
────────────
Application-wide constants for the TONHE Module HMI.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _get_root_dir() -> Path:
    # PyInstaller onefile/onedir: _MEIPASS is the extraction directory
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    # cx_Freeze and PyInstaller onedir: exe sits at the bundle root
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    # Running from source: tonhe_module_hmi/src/tone_hmi/constants.py → tonhe_module_hmi/
    return Path(__file__).resolve().parent.parent.parent


# ── Filesystem paths ──────────────────────────────────────────────────────────
ROOT_DIR: Path = _get_root_dir()
RESOURCES_DIR: Path = ROOT_DIR / "resources"
STYLES_DIR: Path = RESOURCES_DIR / "styles"
ICONS_DIR: Path = RESOURCES_DIR / "icons"

# Sibling plc_ads_project provides the ADS backend services.
ADS_BACKEND_DIR: Path = ROOT_DIR.parent / "plc_ads_project"

# ── Application metadata ──────────────────────────────────────────────────────
APP_NAME: str = "TONHE Module HMI"
APP_VERSION: str = "1.0.0"
ORG_NAME: str = "TwinCAT Tools"
APP_ID: str = "com.twincattools.tonhemodulehmi"

# ── Window sizing ─────────────────────────────────────────────────────────────
# Minimum: fits a 1366×768 14-inch laptop (HD) with room for the OS taskbar.
# Max-cap:  clamp the 90 %-of-screen size on large external monitors.
WINDOW_MIN_WIDTH: int = 960
WINDOW_MIN_HEIGHT: int = 600
WINDOW_DEFAULT_WIDTH: int = 1920   # upper cap – full-HD monitor
WINDOW_DEFAULT_HEIGHT: int = 1060  # ~1080 minus taskbar

# ── Polling ───────────────────────────────────────────────────────────────────
POLL_INTERVAL_MS: int = 300       # fast poll so V/I displays feel live
CONNECTION_TIMEOUT_S: int = 5

# ── Status colours (stylesheet fragments) ─────────────────────────────────────
STATUS_CONNECTED: str = "#27ae60"
STATUS_DISCONNECTED: str = "#e74c3c"
STATUS_CONNECTING: str = "#f39c12"

# ── Module state colours ──────────────────────────────────────────────────────
STATE_OFF_COLOR: str = "#7f8c8d"
STATE_ON_COLOR: str = "#27ae60"
STATE_FAULT_COLOR: str = "#e74c3c"
STATE_UNKNOWN_COLOR: str = "#f39c12"

# ── Log table columns ─────────────────────────────────────────────────────────
LOG_COL_TIME: int = 0
LOG_COL_LEVEL: int = 1
LOG_COL_MODULE: int = 2
LOG_COL_MSG: int = 3
LOG_COLUMNS: list[str] = ["Time", "Level", "Module", "Message"]
LOG_MAX_ROWS: int = 500

# ── QSettings keys ────────────────────────────────────────────────────────────
SETTING_THEME: str = "appearance/theme"
SETTING_CONFIG_PATH: str = "plc/config_path"
SETTING_WINDOW_GEOMETRY: str = "window/geometry"
SETTING_WINDOW_STATE: str = "window/state"
SETTING_SPLITTER_STATE: str = "window/splitter"
SETTING_VIEW_PAGE: str = "window/view_page"
SETTING_LOG_VISIBLE: str = "window/log_visible"

# ── ToneModule-specific PLC variable names ────────────────────────────────────
# These are the ADS symbol paths used throughout the controllers.
# All status variables live in MAIN.stStatus (populated by FB_Tonhe30kW_Module).
# All command / setpoint variables live in MAIN.stSettings.
# CAN-layer diagnostics are read from MAIN.fbComm.
# FB internals (retry counters) are read from MAIN.fbModule.

# Status readbacks (MAIN.stStatus)
VAR_MODULE_STATUS   = "MAIN.stStatus.nModuleState"
VAR_MODULE_VOLTAGE  = "MAIN.stStatus.rActualVoltage"
VAR_MODULE_CURRENT  = "MAIN.stStatus.rActualCurrent"
VAR_MODULE_FAULTS   = "MAIN.stStatus.wFaultBits"
VAR_PFC_FAULTS      = "MAIN.stStatus.nPfcFaultBits"
VAR_MODULE_FAULT    = "MAIN.stStatus.bModuleFault"
VAR_ACK_RECEIVED    = "MAIN.stStatus.bAckReceived"
VAR_PHASE_A         = "MAIN.stStatus.rPhaseVoltageA"
VAR_PHASE_B         = "MAIN.stStatus.rPhaseVoltageB"
VAR_PHASE_C         = "MAIN.stStatus.rPhaseVoltageC"
VAR_TEMPERATURE     = "MAIN.stStatus.nTemperature"
VAR_STATUS_BITS     = "MAIN.stStatus.wStatusBits"
VAR_EXT_FAULTS      = "MAIN.stStatus.wExtFaultWarningBits"
VAR_MODULE_RUNNING  = "MAIN.stStatus.bModuleRunning"
VAR_STATUS_TEXT     = "MAIN.stStatus.sStatusText"
VAR_CONTROL_STATE   = "MAIN.stStatus.eControlState"
VAR_RAMP_CURR_VOLT  = "MAIN.stStatus.rRampCurrentVoltage"
VAR_RAMP_COMPLETE   = "MAIN.stStatus.bRampComplete"

# CAN communication diagnostics (MAIN.fbComm)
VAR_STATUS_RECEIVED = "MAIN.fbComm.bStatusReceived"
VAR_RX_FRAME_COUNT  = "MAIN.fbComm.nRxFrameCount"
VAR_LAST_COB_ID     = "MAIN.fbComm.nLastRxCobId"

# Control commands — rising-edge triggered (MAIN.stSettings)
VAR_START           = "MAIN.stSettings.bEnableModule"
VAR_STOP            = "MAIN.stSettings.bDisableModule"
VAR_CLEAR_FAULT     = "MAIN.stSettings.bClearFault"
VAR_UPDATE_VI       = "MAIN.stSettings.bUpdateSetpoint"

# Setpoints (MAIN.stSettings)
VAR_TARGET_VOLTAGE  = "MAIN.stSettings.rTargetVoltage"
VAR_TARGET_CURRENT  = "MAIN.stSettings.rTargetCurrent"
VAR_MAX_VOLTAGE     = "MAIN.stSettings.rMaxVoltage"
VAR_MAX_CURRENT     = "MAIN.stSettings.rMaxCurrent"
VAR_MODULE_ADDRESS  = "MAIN.stSettings.nModuleAddress"
VAR_MASTER_ADDRESS  = "MAIN.stSettings.nMasterAddress"

# Voltage ramp / soft-start (MAIN.stSettings)
VAR_ENABLE_RAMP     = "MAIN.stSettings.bEnableRamp"
VAR_RAMP_STEP       = "MAIN.stSettings.rRampVoltageStep"
VAR_RAMP_TIME_S     = "MAIN.stSettings.rRampStepTime_s"   # Step time in seconds (REAL)
VAR_HEARTBEAT       = "MAIN.stSettings.bEnableHeartbeat"

# FB_Tonhe30kW_Module internals — diagnostic read-only (MAIN.fbModule)
VAR_RETRY_COUNT     = "MAIN.fbModule.nRetryCount"
VAR_MAX_RETRIES     = "MAIN.fbModule.nMaxRetries"

# ── Graph panel ───────────────────────────────────────────────────────────────
GRAPH_MAX_POINTS: int = 1200      # 6 min of history at 300 ms/sample
