"""
app_controller.py
-----------------
:class:`AppController` is the top-level orchestrator instantiated once by
:class:`~plc_gui.views.main_window.MainWindow`.

Responsibilities
~~~~~~~~~~~~~~~~
* Listen to the main-window menu/toolbar for **Open Config** and **theme
  switching**.
* Coordinate :class:`~plc_gui.controllers.connection_controller.ConnectionController`
  and :class:`~plc_gui.controllers.variable_controller.VariableController`.
* Forward status-bar messages and error notifications to the main window.
* Persist / restore the last-used config path via :class:`QSettings`.
* Call :meth:`~plc_gui.app_context.AppContext.teardown` on application exit.
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, QSettings, pyqtSlot
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox

from plc_gui.app_context import AppContext
from plc_gui.constants import APP_NAME, ORG_NAME, SETTING_CONFIG_PATH, SETTING_THEME
from plc_gui.utils.style_manager import StyleManager
from plc_gui.controllers.connection_controller import ConnectionController
from plc_gui.controllers.variable_controller import VariableController

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from plc_gui.views.main_window import MainWindow


class AppController(QObject):
    """
    Top-level application controller.

    Args:
        window: The application's :class:`~plc_gui.views.main_window.MainWindow`.
        parent: Optional Qt parent.
    """

    def __init__(self, window: "MainWindow", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._window = window
        self._ctx = AppContext()

        # Sub-controllers.
        self._conn_ctrl = ConnectionController(
            panel=window.connection_panel,
            ctx=self._ctx,
            parent=self,
        )
        self._var_ctrl = VariableController(
            panel=window.variable_panel,
            ctx=self._ctx,
            parent=self,
        )

        # Cross-controller wiring.
        self._conn_ctrl.connected.connect(self._var_ctrl.on_connected)
        self._conn_ctrl.disconnected.connect(self._var_ctrl.on_disconnected)

        # Status-bar wiring.
        self._conn_ctrl.connected.connect(
            lambda: window.set_status("Connected", success=True)
        )
        self._conn_ctrl.disconnected.connect(
            lambda: window.set_status("Disconnected")
        )
        self._conn_ctrl.connect_failed.connect(
            lambda msg: window.set_status(f"Connection failed: {msg}", error=True)
        )
        self._var_ctrl.status_message.connect(window.set_status)
        self._var_ctrl.error_occurred.connect(
            lambda msg: window.set_status(msg, error=True)
        )

        # Main window actions.
        window.open_config_requested.connect(self._on_open_config)
        window.theme_changed.connect(self._on_theme_changed)
        window.about_requested.connect(self._on_about)

        # Try to auto-load the last used config.
        self._try_restore_config()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _on_open_config(self) -> None:
        settings = QSettings(ORG_NAME, APP_NAME)
        last_dir = settings.value(SETTING_CONFIG_PATH, "")

        file_path, _ = QFileDialog.getOpenFileName(
            self._window,
            "Open PLC Configuration",
            last_dir,
            "XML Files (*.xml);;All Files (*)",
        )
        if not file_path:
            return
        self._load_config(file_path)

    @pyqtSlot(str)
    def _on_theme_changed(self, theme: str) -> None:
        StyleManager.apply(QApplication.instance(), theme)

    @pyqtSlot()
    def _on_about(self) -> None:
        from plc_gui.views.about_dialog import AboutDialog
        AboutDialog(self._window).exec()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_config(self, path: str) -> None:
        """Load the XML config at *path* and update the UI."""
        try:
            self._ctx.load(path)
            self._window.set_status(f"Loaded config: {path}")
            self._window.connection_panel.populate_from_config(self._ctx.config)
            settings = QSettings(ORG_NAME, APP_NAME)
            settings.setValue(SETTING_CONFIG_PATH, path)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(
                self._window,
                "Config Error",
                f"Failed to load configuration file:\n\n{exc}",
            )
            self._window.set_status("Config load failed", error=True)

    def _try_restore_config(self) -> None:
        """Silently attempt to reload the last used config."""
        settings = QSettings(ORG_NAME, APP_NAME)
        last_path = settings.value(SETTING_CONFIG_PATH, "")
        if last_path:
            try:
                self._ctx.load(last_path)
                self._window.connection_panel.populate_from_config(self._ctx.config)
                self._window.set_status(f"Config restored: {last_path}")
            except Exception:
                pass   # silently ignore – user can open manually

    def teardown(self) -> None:
        """Gracefully shut down on application close."""
        self._var_ctrl._stop_poll_worker()   # noqa: SLF001
        self._ctx.teardown()
