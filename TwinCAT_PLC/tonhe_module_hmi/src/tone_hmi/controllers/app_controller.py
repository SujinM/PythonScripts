"""
app_controller.py
──────────────────
Top-level orchestrator instantiated by MainWindow.install_controller().

Coordinates:
  • AppContext (config loading)
  • ConnectionController
  • ModuleController
  • Theme / About / Open config actions
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import QObject, QSettings, pyqtSlot
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox

from tone_hmi.app_context import AppContext
from tone_hmi.constants import APP_NAME, ORG_NAME, SETTING_CONFIG_PATH, SETTING_THEME
from tone_hmi.utils.style_manager import StyleManager
from tone_hmi.controllers.connection_controller import ConnectionController
from tone_hmi.controllers.module_controller import ModuleController

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tone_hmi.views.main_window import MainWindow

log = logging.getLogger(__name__)


class AppController(QObject):
    def __init__(self, window: "MainWindow", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._window = window
        self._ctx = AppContext()

        # Sub-controllers
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
        self._conn_ctrl.connected.connect(self._mod_ctrl.on_connected)
        self._conn_ctrl.disconnected.connect(self._mod_ctrl.on_disconnected)

        # Status-bar wiring
        self._conn_ctrl.connected.connect(
            lambda: window.set_status("Connected to PLC", success=True)
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
        from tone_hmi.views.about_dialog import AboutDialog
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
            except Exception:
                pass

    def teardown(self) -> None:
        self._mod_ctrl.teardown()
        self._ctx.teardown()
