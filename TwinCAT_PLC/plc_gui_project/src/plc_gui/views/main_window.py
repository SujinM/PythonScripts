"""
main_window.py
--------------
:class:`MainWindow` is the application's top-level
:class:`~PyQt6.QtWidgets.QMainWindow`.

Layout
~~~~~~
::

    ┌─────────────────────────────────────────────────┐
    │  Menu bar (File | View | Help)                  │
    │  Tool bar (Open Config | Theme toggle)          │
    ├──────────────┬──────────────────────────────────┤
    │  Connection  │  Variable Panel                  │
    │  Panel       │  (table + toolbar)               │
    │  (left)      │                                  │
    ├──────────────┴──────────────────────────────────┤
    │  Log Panel (resizable splitter pane)            │
    ├─────────────────────────────────────────────────┤
    │  Status bar                                     │
    └─────────────────────────────────────────────────┘

The main window owns its child panels and exposes them as public attributes so
:class:`~plc_gui.controllers.app_controller.AppController` can wire them up.

It also emits signals for actions that belong to the controller layer:
* :attr:`open_config_requested`
* :attr:`theme_changed`
* :attr:`about_requested`
"""

from __future__ import annotations

from PyQt6.QtCore import QByteArray, QSettings, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from plc_gui.constants import (
    APP_NAME, APP_VERSION, ORG_NAME,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    SETTING_WINDOW_GEOMETRY, SETTING_WINDOW_STATE, SETTING_SPLITTER_STATE,
    STATUS_CONNECTED, STATUS_DISCONNECTED, STATUS_CONNECTING,
)
from plc_gui.views.connection_panel import ConnectionPanel
from plc_gui.views.variable_panel import VariablePanel
from plc_gui.views.log_panel import LogPanel


class MainWindow(QMainWindow):
    """
    Application shell: menu bar, toolbars, central splitter, status bar.

    Signals:
        open_config_requested: User requested to open a config file.
        theme_changed:         User switched theme; carries the new theme name.
        about_requested:       User opened the About dialog.
    """

    open_config_requested = pyqtSignal()
    theme_changed = pyqtSignal(str)
    about_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)

        # Child panels (public so controllers can access them)
        self.connection_panel = ConnectionPanel(self)
        self.variable_panel = VariablePanel(self)
        self.log_panel = LogPanel(parent=self)

        self._build_menubar()
        self._build_toolbar()
        self._build_central_widget()
        self._build_statusbar()
        self._restore_geometry()

        # Deferred controller wiring to break circular import.
        self._app_controller = None

    # ------------------------------------------------------------------
    # Build helpers
    # ------------------------------------------------------------------

    def _build_menubar(self) -> None:
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("&File")

        act_open = QAction("&Open Config…", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.setStatusTip("Load a PLC configuration XML file")
        act_open.triggered.connect(self.open_config_requested)
        file_menu.addAction(act_open)

        file_menu.addSeparator()

        act_quit = QAction("E&xit", self)
        act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        act_quit.triggered.connect(QApplication.quit)
        file_menu.addAction(act_quit)

        # View
        view_menu = mb.addMenu("&View")

        act_dark = QAction("Dark theme", self)
        act_dark.triggered.connect(lambda: self.theme_changed.emit("dark"))
        view_menu.addAction(act_dark)

        act_light = QAction("Light theme", self)
        act_light.triggered.connect(lambda: self.theme_changed.emit("light"))
        view_menu.addAction(act_light)

        # Help
        help_menu = mb.addMenu("&Help")

        act_about = QAction("&About…", self)
        act_about.triggered.connect(self.about_requested)
        help_menu.addAction(act_about)

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main Toolbar", self)
        tb.setObjectName("mainToolbar")
        tb.setMovable(False)
        self.addToolBar(tb)

        act_open = QAction("⚙  Open Config", self)
        act_open.setToolTip("Load a PLC configuration XML file  (Ctrl+O)")
        act_open.triggered.connect(self.open_config_requested)
        tb.addAction(act_open)

        tb.addSeparator()

        act_dark = QAction("🌙 Dark", self)
        act_dark.setToolTip("Switch to dark theme")
        act_dark.triggered.connect(lambda: self.theme_changed.emit("dark"))
        tb.addAction(act_dark)

        act_light = QAction("☀ Light", self)
        act_light.setToolTip("Switch to light theme")
        act_light.triggered.connect(lambda: self.theme_changed.emit("light"))
        tb.addAction(act_light)

    def _build_central_widget(self) -> None:
        # Horizontal splitter: connection panel (left) | variable panel (right)
        top_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        top_splitter.addWidget(self.connection_panel)
        top_splitter.addWidget(self.variable_panel)
        top_splitter.setStretchFactor(0, 0)   # connection panel fixed width
        top_splitter.setStretchFactor(1, 1)   # variable panel takes all extra space
        top_splitter.setSizes([280, 820])

        # Vertical splitter: top area | log panel
        self._main_splitter = QSplitter(Qt.Orientation.Vertical, self)
        self._main_splitter.setObjectName("mainSplitter")
        self._main_splitter.addWidget(top_splitter)
        self._main_splitter.addWidget(self.log_panel)
        self._main_splitter.setStretchFactor(0, 3)
        self._main_splitter.setStretchFactor(1, 1)
        self._main_splitter.setSizes([530, 170])

        container = QWidget(self)
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(4, 4, 4, 4)
        vbox.addWidget(self._main_splitter)
        self.setCentralWidget(container)

    def _build_statusbar(self) -> None:
        self._statusbar = QStatusBar(self)
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("Ready")

    # ------------------------------------------------------------------
    # Geometry persistence
    # ------------------------------------------------------------------

    def _restore_geometry(self) -> None:
        settings = QSettings(ORG_NAME, APP_NAME)
        geom: QByteArray = settings.value(SETTING_WINDOW_GEOMETRY, QByteArray())
        state: QByteArray = settings.value(SETTING_WINDOW_STATE, QByteArray())
        splitter_state: QByteArray = settings.value(SETTING_SPLITTER_STATE, QByteArray())
        if not geom.isEmpty():
            self.restoreGeometry(geom)
        if not state.isEmpty():
            self.restoreState(state)
        if not splitter_state.isEmpty():
            self._main_splitter.restoreState(splitter_state)

    def _save_geometry(self) -> None:
        settings = QSettings(ORG_NAME, APP_NAME)
        settings.setValue(SETTING_WINDOW_GEOMETRY, self.saveGeometry())
        settings.setValue(SETTING_WINDOW_STATE, self.saveState())
        settings.setValue(SETTING_SPLITTER_STATE, self._main_splitter.saveState())

    # ------------------------------------------------------------------
    # Public API (called by controllers)
    # ------------------------------------------------------------------

    def set_status(
        self,
        message: str,
        *,
        success: bool = False,
        error: bool = False,
        timeout_ms: int = 8000,
    ) -> None:
        """
        Update the status bar message with optional colour coding.

        Args:
            message:    Text to display.
            success:    If ``True`` the text is tinted green.
            error:      If ``True`` the text is tinted red.
            timeout_ms: How long to show the message (0 = permanent).
        """
        colour = ""
        if success:
            colour = f"color: {STATUS_CONNECTED};"
        elif error:
            colour = f"color: {STATUS_DISCONNECTED};"
        self._statusbar.setStyleSheet(colour)
        if timeout_ms > 0:
            self._statusbar.showMessage(message, timeout_ms)
        else:
            self._statusbar.showMessage(message)

    def install_controller(self) -> None:
        """
        Create and attach the :class:`~plc_gui.controllers.app_controller.AppController`.

        Called from ``app.py`` after the window is shown so the ADS backend
        import does not delay the first frame.
        """
        from plc_gui.controllers.app_controller import AppController
        self._app_controller = AppController(self, parent=self)

    # ------------------------------------------------------------------
    # Qt overrides
    # ------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self._save_geometry()
        if self._app_controller is not None:
            self._app_controller.teardown()
        super().closeEvent(event)
