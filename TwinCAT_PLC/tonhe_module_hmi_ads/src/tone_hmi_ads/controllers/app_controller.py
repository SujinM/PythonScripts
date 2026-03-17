"""
app_controller.py
──────────────────
Top-level orchestrator for the TONHE Module HMI – ADS Notification Edition.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QObject, QSettings, pyqtSlot
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox

from tone_hmi_ads.app_context import AppContext
from tone_hmi_ads.constants import APP_NAME, ORG_NAME, SETTING_CONFIG_PATH, SETTING_THEME
from tone_hmi_ads.utils.style_manager import StyleManager
from tone_hmi_ads.controllers.connection_controller import ConnectionController
from tone_hmi_ads.controllers.module_controller import ModuleController

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tone_hmi_ads.views.main_window import MainWindow

log = logging.getLogger(__name__)


class AppController(QObject):
    def __init__(self, window: "MainWindow", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._window = window
        self._ctx = AppContext()

        self._conn_ctrl = ConnectionController(
            panel=window.connection_panel,
            ctx=self._ctx,
            parent=self,
        )
        self._mod_ctrl = ModuleController(
            status_panel=window.module_status_panel,
            control_panel=window.module_control_panel,
            setpoint_panel=window.setpoint_panel,
            phase_panel=window.phase_info_panel,
            fault_panel=window.fault_panel,
            ctx=self._ctx,
            graph_panel=window.graph_panel,
            parent=self,
        )

        # Cross-controller wiring
        # ConnectionController passes the NotificationBridge to ModuleController
        self._conn_ctrl.connected.connect(self._mod_ctrl.on_connected)
        self._conn_ctrl.disconnected.connect(self._mod_ctrl.on_disconnected)

        # Status bar wiring
        self._conn_ctrl.connected.connect(
            lambda _: window.set_status("Connected to PLC – ADS notifications active", success=True)
        )
        self._conn_ctrl.disconnected.connect(
            lambda: window.set_status("Disconnected")
        )
        self._conn_ctrl.connect_failed.connect(
            lambda msg: window.set_status(f"Connection failed: {msg}", error=True)
        )
        self._mod_ctrl.status_message.connect(window.set_status)
        self._mod_ctrl.error_occurred.connect(
            lambda msg: window.set_status(msg, error=True)
        )

        # Main window actions
        window.open_config_requested.connect(self._on_open_config)
        window.theme_changed.connect(self._on_theme_changed)
        window.about_requested.connect(self._on_about)

        self._try_restore_config()

    # ── Slots ─────────────────────────────────────────────────────────────────

    @pyqtSlot()
    def _on_open_config(self) -> None:
        settings = QSettings(ORG_NAME, APP_NAME)
        last_dir = settings.value(SETTING_CONFIG_PATH, "")
        path, _ = QFileDialog.getOpenFileName(
            self._window,
            "Open ToneModule Config",
            last_dir,
            "XML Files (*.xml);;All Files (*)",
        )
        if path:
            self._load_config(path)

    @pyqtSlot(str)
    def _on_theme_changed(self, theme: str) -> None:
        StyleManager.apply(QApplication.instance(), theme)

    @pyqtSlot()
    def _on_about(self) -> None:
        from tone_hmi_ads.views.about_dialog import AboutDialog
        AboutDialog(self._window).exec()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load_config(self, path: str) -> None:
        try:
            self._ctx.load(path)
            if self._ctx.config:
                self._window.connection_panel.populate_from_config(self._ctx.config)
            settings = QSettings(ORG_NAME, APP_NAME)
            settings.setValue(SETTING_CONFIG_PATH, path)
            self._window.set_status(f"Config loaded: {path}", success=True)
            log.info("Config loaded from %s", path)
        except Exception as exc:
            log.exception("Failed to load config")
            QMessageBox.critical(
                self._window,
                "Config Error",
                f"Could not load configuration:\n{exc}",
            )
            self._window.set_status(f"Config error: {exc}", error=True)

    def _try_restore_config(self) -> None:
        settings = QSettings(ORG_NAME, APP_NAME)
        path = settings.value(SETTING_CONFIG_PATH, "")

        if path:
            try:
                self._load_config(path)
                return
            except Exception:
                log.warning("Saved config path failed, falling back to default: %s", path)

        default_config = (
            Path(__file__).resolve()
            .parent   # controllers/
            .parent   # tone_hmi_ads/
            .parent   # src/
            .parent   # tonhe_module_hmi_ads/
            / "config"
            / "tone_config.xml"
        )
        if default_config.exists():
            try:
                self._load_config(str(default_config))
                settings.setValue(SETTING_CONFIG_PATH, str(default_config))
            except Exception:
                log.warning("Default config also failed to load: %s", default_config)

    def teardown(self) -> None:
        self._mod_ctrl.teardown()
        self._ctx.teardown()
