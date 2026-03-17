"""
constants.py
────────────
Application-wide constants for the TONHE Module HMI – ADS Notification Edition.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _get_root_dir() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    # Running from source: tonhe_module_hmi_ads/src/tone_hmi_ads/constants.py
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
APP_VERSION: str = "2.0.0"
ORG_NAME: str = "TwinCAT Tools"
APP_ID: str = "com.twincattools.tonhemodulehmi.ads"

# ── Window sizing ─────────────────────────────────────────────────────────────
WINDOW_MIN_WIDTH: int = 960
WINDOW_MIN_HEIGHT: int = 600
WINDOW_DEFAULT_WIDTH: int = 1920
WINDOW_DEFAULT_HEIGHT: int = 1060

# ── ADS Notification channel limit ───────────────────────────────────────────
# The ADS router allows at most 500 notification handles (0–499) per connection.
# When the number of subscribed variables reaches this cap, a new ADS channel
# (ConnectionManager + ADSClient + NotificationManager) is opened automatically.
NOTIFICATION_CHANNEL_LIMIT: int = 499

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

# ── Graph ─────────────────────────────────────────────────────────────────────
GRAPH_MAX_POINTS: int = 3600   # 1 h of 1-second samples

# ── QSettings keys ────────────────────────────────────────────────────────────
SETTING_THEME: str = "appearance/theme"
SETTING_CONFIG_PATH: str = "plc/config_path"
SETTING_WINDOW_GEOMETRY: str = "window/geometry"
SETTING_WINDOW_STATE: str = "window/state"
SETTING_SPLITTER_STATE: str = "window/splitter"
SETTING_VIEW_PAGE: str = "window/view_page"
SETTING_LOG_VISIBLE: str = "window/log_visible"

# ── ToneModule-specific PLC variable names ────────────────────────────────────
# Status (read-only from PLC)
VAR_MODULE_STATUS: str   = "MAIN.stStatus.nModuleState"
VAR_MODULE_VOLTAGE: str  = "MAIN.stStatus.rActualVoltage"
VAR_MODULE_CURRENT: str  = "MAIN.stStatus.rActualCurrent"
VAR_MODULE_FAULTS: str   = "MAIN.stStatus.wFaultBits"
VAR_PFC_FAULTS: str      = "MAIN.stStatus.nPfcFaultBits"
VAR_STATUS_BITS: str     = "MAIN.stStatus.wStatusBits"
VAR_EXT_FAULTS: str      = "MAIN.stStatus.wExtFaultWarningBits"
VAR_PHASE_A: str         = "MAIN.stStatus.rPhaseVoltageA"
VAR_PHASE_B: str         = "MAIN.stStatus.rPhaseVoltageB"
VAR_PHASE_C: str         = "MAIN.stStatus.rPhaseVoltageC"
VAR_TEMPERATURE: str     = "MAIN.stStatus.nTemperature"
VAR_MODULE_RUNNING: str  = "MAIN.stStatus.bModuleRunning"
VAR_MODULE_FAULT: str    = "MAIN.stStatus.bModuleFault"
VAR_ACK_RECEIVED: str    = "MAIN.stStatus.bAckReceived"
VAR_STATUS_TEXT: str     = "MAIN.stStatus.sStatusText"
VAR_RAMP_CURR_VOLT: str  = "MAIN.stStatus.rRampCurrentVoltage"
VAR_RAMP_COMPLETE: str   = "MAIN.stStatus.bRampComplete"

# Settings (read/write from HMI)
VAR_START: str           = "MAIN.stSettings.bEnableModule"
VAR_STOP: str            = "MAIN.stSettings.bDisableModule"
VAR_CLEAR_FAULT: str     = "MAIN.stSettings.bClearFault"
VAR_UPDATE_VI: str       = "MAIN.stSettings.bUpdateSetpoint"
VAR_TARGET_VOLTAGE: str  = "MAIN.stSettings.rTargetVoltage"
VAR_TARGET_CURRENT: str  = "MAIN.stSettings.rTargetCurrent"
VAR_MAX_VOLTAGE: str     = "MAIN.stSettings.rMaxVoltage"
VAR_MAX_CURRENT: str     = "MAIN.stSettings.rMaxCurrent"
VAR_MODULE_ADDRESS: str  = "MAIN.stSettings.nModuleAddress"
VAR_MASTER_ADDRESS: str  = "MAIN.stSettings.nMasterAddress"
VAR_ENABLE_RAMP: str     = "MAIN.stSettings.bEnableRamp"
VAR_RAMP_STEP: str       = "MAIN.stSettings.rRampVoltageStep"
VAR_RAMP_TIME_S: str     = "MAIN.stSettings.rRampStepTime_s"
VAR_HEARTBEAT: str       = "MAIN.stSettings.bEnableHeartbeat"

# Comm diagnostics (read-only)
VAR_STATUS_RECEIVED: str = "MAIN.fbComm.bStatusReceived"
VAR_RX_FRAME_COUNT: str  = "MAIN.fbComm.nRxFrameCount"
VAR_LAST_COB_ID: str     = "MAIN.fbComm.nLastRxCobId"

# Module FB diagnostics (read-only)
VAR_RETRY_COUNT: str     = "MAIN.fbModule.nRetryCount"
VAR_MAX_RETRIES: str     = "MAIN.fbModule.nMaxRetries"

# ── All read-only / notification variables (subscribed via ADS notifications) ─
# These are the variables whose changes are pushed by the PLC.
# Write-only command variables (bEnableModule, bDisableModule, etc.) are NOT
# subscribed – they are written by the HMI and do not generate useful notifications.
NOTIFICATION_VARIABLES: tuple[str, ...] = (
    VAR_MODULE_STATUS,
    VAR_MODULE_VOLTAGE,
    VAR_MODULE_CURRENT,
    VAR_MODULE_FAULTS,
    VAR_PFC_FAULTS,
    VAR_STATUS_BITS,
    VAR_EXT_FAULTS,
    VAR_PHASE_A,
    VAR_PHASE_B,
    VAR_PHASE_C,
    VAR_TEMPERATURE,
    VAR_MODULE_RUNNING,
    VAR_MODULE_FAULT,
    VAR_ACK_RECEIVED,
    VAR_STATUS_TEXT,
    VAR_RAMP_CURR_VOLT,
    VAR_RAMP_COMPLETE,
    VAR_STATUS_RECEIVED,
    VAR_RX_FRAME_COUNT,
    VAR_LAST_COB_ID,
    VAR_RETRY_COUNT,
    VAR_MAX_RETRIES,
    # Setpoint readback variables
    VAR_TARGET_VOLTAGE,
    VAR_TARGET_CURRENT,
    VAR_ENABLE_RAMP,
    VAR_RAMP_STEP,
    VAR_RAMP_TIME_S,
    VAR_MODULE_ADDRESS,
    VAR_MASTER_ADDRESS,
)
