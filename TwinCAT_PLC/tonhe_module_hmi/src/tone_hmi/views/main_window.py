"""
main_window.py
──────────────
Application shell for the TONHE Module HMI.

Layout
──────
┌───────────────────────────────────────────────────────────────────┐
│  Menu bar  (File | View | Help)                                   │
│  Tool bar  (Open Config | Connect | Theme toggle)                 │
├──────────────┬────────────────────────────────────────────────────┤
│  Connection  │  ┌──── Module Status ────┬──── Control ─────────┐  │
│  Panel       │  │ State LED             │ START / STOP / CLEAR │  │
│              │  │ Voltage card          │                      │  │
│              │  │ Current card          │ Addresses / retries  │  │
│              │  │ Status text           ├──── Setpoints ───────┤  │
│              │  │ Flag pills            │ Target V / I         │  │
│              │  └───────────────────────┴──────────────────────┘  │
│              │  ┌── Phase Info ──────────┬── Fault / Diag ──────┐  │
│              │  │ Va, Vb, Vc, Temp       │ Fault decode         │  │
│              │  └────────────────────────┴──────────────────────┘  │
├──────────────┴────────────────────────────────────────────────────┤
│  Log Panel                                                        │
├───────────────────────────────────────────────────────────────────┤
│  Status bar                                                       │
└───────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

from PyQt6.QtCore import QByteArray, QSettings, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from tone_hmi.constants import (
    APP_NAME, APP_VERSION, ORG_NAME,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    STATUS_CONNECTED, STATUS_DISCONNECTED,
    SETTING_WINDOW_GEOMETRY, SETTING_WINDOW_STATE, SETTING_SPLITTER_STATE,
)
from tone_hmi.views.connection_panel import ConnectionPanel
from tone_hmi.views.module_status_panel import ModuleStatusPanel
from tone_hmi.views.module_control_panel import ModuleControlPanel
from tone_hmi.views.setpoint_panel import SetpointPanel
from tone_hmi.views.phase_info_panel import PhaseInfoPanel
from tone_hmi.views.fault_panel import FaultPanel
from tone_hmi.views.graph_panel import GraphPanel
from tone_hmi.views.log_panel import LogPanel


class MainWindow(QMainWindow):
    """Top-level application window.

    Signals:
        open_config_requested: User chose File → Open Config.
        theme_changed:         User switched theme; carries theme name.
        about_requested:       User chose Help → About.
    """

    open_config_requested = pyqtSignal()
    theme_changed = pyqtSignal(str)
    about_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)

        # ── Child panels (public so controllers can reach them) ───────────────
        self.connection_panel = ConnectionPanel(self)
        self.module_status_panel = ModuleStatusPanel(self)
        self.module_control_panel = ModuleControlPanel(self)
        self.setpoint_panel = SetpointPanel(self)
        self.phase_info_panel = PhaseInfoPanel(self)
        self.fault_panel = FaultPanel(self)
        self.graph_panel = GraphPanel(self)
        self.log_panel = LogPanel(parent=self)

        self._build_menubar()
        self._build_toolbar()
        self._build_central_widget()
        self._build_statusbar()
        self._restore_geometry()

        self._app_controller = None   # set later via install_controller()

    # ── Build helpers ─────────────────────────────────────────────────────────

    def _build_menubar(self) -> None:
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("&File")
        act_open = QAction("&Open Config…", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.setStatusTip("Load a tone_config.xml file")
        act_open.triggered.connect(self.open_config_requested)
        file_menu.addAction(act_open)
        file_menu.addSeparator()
        act_quit = QAction("E&xit", self)
        act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        act_quit.triggered.connect(QApplication.quit)
        file_menu.addAction(act_quit)

        # View
        view_menu = mb.addMenu("&View")
        act_dark = QAction("🌙 Dark theme", self)
        act_dark.triggered.connect(lambda: self.theme_changed.emit("dark"))
        view_menu.addAction(act_dark)
        act_light = QAction("☀ Light theme", self)
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
        act_open.setToolTip("Load tone_config.xml  (Ctrl+O)")
        act_open.triggered.connect(self.open_config_requested)
        tb.addAction(act_open)

        tb.addSeparator()

        act_dark = QAction("🌙 Dark", self)
        act_dark.triggered.connect(lambda: self.theme_changed.emit("dark"))
        tb.addAction(act_dark)

        act_light = QAction("☀ Light", self)
        act_light.triggered.connect(lambda: self.theme_changed.emit("light"))
        tb.addAction(act_light)

    def _build_central_widget(self) -> None:
        # ── Top-right: module status + control (horizontal) ───────────────────
        top_right_top = QHBoxLayout()
        top_right_top.setSpacing(8)
        top_right_top.addWidget(self.module_status_panel, stretch=3)

        ctrl_vbox = QVBoxLayout()
        ctrl_vbox.setSpacing(8)
        ctrl_vbox.addWidget(self.module_control_panel)
        ctrl_vbox.addWidget(self.setpoint_panel)
        ctrl_widget = QWidget()
        ctrl_widget.setLayout(ctrl_vbox)
        top_right_top.addWidget(ctrl_widget, stretch=2)

        # ── Bottom row: phase info + fault panel ──────────────────────────────
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)
        bottom_row.addWidget(self.phase_info_panel, stretch=1)
        bottom_row.addWidget(self.fault_panel, stretch=2)

        # ── Combine top & bottom into right pane ──────────────────────────────
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        right_layout.setSpacing(8)
        right_layout.addLayout(top_right_top, stretch=3)
        right_layout.addLayout(bottom_row, stretch=2)

        # ── Horizontal splitter: connection panel | right pane ────────────────
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.addWidget(self.connection_panel)
        top_splitter.addWidget(right_pane)
        top_splitter.setStretchFactor(0, 0)
        top_splitter.setStretchFactor(1, 1)
        top_splitter.setSizes([250, 1050])

        # ── Vertical splitter: main area | log panel ──────────────────────────
        self._main_splitter = QSplitter(Qt.Orientation.Vertical)
        self._main_splitter.setObjectName("mainSplitter")
        self._main_splitter.addWidget(top_splitter)
        self._main_splitter.addWidget(self.graph_panel)
        self._main_splitter.addWidget(self.log_panel)
        self._main_splitter.setStretchFactor(0, 3)
        self._main_splitter.setStretchFactor(1, 2)
        self._main_splitter.setStretchFactor(2, 1)
        self._main_splitter.setSizes([480, 280, 160])

        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.setSpacing(0)
        vbox.addWidget(self._main_splitter)
        self.setCentralWidget(container)

    def _build_statusbar(self) -> None:
        self._statusbar = QStatusBar(self)
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("Ready – open a config file to begin")

    # ── Geometry persistence ──────────────────────────────────────────────────

    def _restore_geometry(self) -> None:
        s = QSettings(ORG_NAME, APP_NAME)
        geom = s.value(SETTING_WINDOW_GEOMETRY, QByteArray())
        state = s.value(SETTING_WINDOW_STATE, QByteArray())
        spl = s.value(SETTING_SPLITTER_STATE, QByteArray())
        if not geom.isEmpty():
            self.restoreGeometry(geom)
        if not state.isEmpty():
            self.restoreState(state)
        if not spl.isEmpty():
            self._main_splitter.restoreState(spl)

    def closeEvent(self, event: QCloseEvent) -> None:
        s = QSettings(ORG_NAME, APP_NAME)
        s.setValue(SETTING_WINDOW_GEOMETRY, self.saveGeometry())
        s.setValue(SETTING_WINDOW_STATE, self.saveState())
        s.setValue(SETTING_SPLITTER_STATE, self._main_splitter.saveState())
        if self._app_controller:
            self._app_controller.teardown()
        super().closeEvent(event)

    # ── Controller wiring (avoids circular import) ────────────────────────────

    def install_controller(self) -> None:
        from tone_hmi.controllers.app_controller import AppController
        self._app_controller = AppController(self)

    # ── Status bar helpers ────────────────────────────────────────────────────

    def set_status(self, message: str, *, success: bool = False, error: bool = False) -> None:
        style = ""
        if success:
            style = f"color: {STATUS_CONNECTED};"
        elif error:
            style = f"color: {STATUS_DISCONNECTED};"
        self._statusbar.setStyleSheet(style)
        self._statusbar.showMessage(message)
