"""
main_window.py
──────────────
Application shell for the TONHE Module HMI.

Layout
──────
┌───────────────────────────────────────────────────────────────────┐
│  Menu bar  (File | View | Help)                                   │
│  Tool bar  (Open Config | Theme | 📊 Graph | 🔍 Details | Log)   │
├──────────────┬────────────────────────────────────────────────────┤
│  Connection  │  Module Status panel   │  Control + Setpoints      │
│  Panel       ├────────────────────────────────────────────────────┤
│              │  ┌── View switcher bar (Graph / Details) ─────────┐│
│              │  │  STACKED WIDGET                                ││
│              │  │   Page 0 – Graph:   full GraphPanel            ││
│              │  │   Page 1 – Details: phase info | fault panel   ││
│              │  └────────────────────────────────────────────────┘│
├──────────────┴────────────────────────────────────────────────────┤
│  Log Panel  (collapsible via toolbar toggle)                      │
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
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
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
    SETTING_VIEW_PAGE, SETTING_LOG_VISIBLE,
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

        # Adaptive initial size: 90 % of the available screen area,
        # clamped between the minimum and the full-HD upper cap.
        # Works correctly on a 14-inch laptop (1366×768 / 1920×1080)
        # as well as on a large external monitor.
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            w = max(min(int(avail.width()  * 0.90), WINDOW_DEFAULT_WIDTH),  WINDOW_MIN_WIDTH)
            h = max(min(int(avail.height() * 0.90), WINDOW_DEFAULT_HEIGHT), WINDOW_MIN_HEIGHT)
        else:
            w, h = WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT
        self.resize(w, h)

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

        tb.addSeparator()

        # View-switch actions (checkable so they show as pressed)
        self._act_graph = QAction("📊  Graph", self)
        self._act_graph.setCheckable(True)
        self._act_graph.setChecked(True)
        self._act_graph.setToolTip("Show full-screen graph view")
        self._act_graph.triggered.connect(lambda: self._switch_view(0))
        tb.addAction(self._act_graph)

        self._act_details = QAction("🔍  Details", self)
        self._act_details.setCheckable(True)
        self._act_details.setToolTip("Show phase info & fault details")
        self._act_details.triggered.connect(lambda: self._switch_view(1))
        tb.addAction(self._act_details)

        tb.addSeparator()

        self._act_log = QAction("📋  Log", self)
        self._act_log.setCheckable(True)
        self._act_log.setChecked(True)
        self._act_log.setToolTip("Show / hide the event log panel")
        self._act_log.triggered.connect(self._toggle_log)
        tb.addAction(self._act_log)

    def _build_central_widget(self) -> None:
        # ── Top strip: module status + control/setpoints (always visible) ─────
        top_strip = QHBoxLayout()
        top_strip.setSpacing(8)
        top_strip.addWidget(self.module_status_panel, stretch=3)

        ctrl_vbox = QVBoxLayout()
        ctrl_vbox.setSpacing(4)
        ctrl_vbox.setContentsMargins(0, 0, 0, 0)
        ctrl_vbox.addWidget(self.module_control_panel)
        ctrl_vbox.addWidget(self.setpoint_panel)
        ctrl_vbox.addStretch()
        ctrl_widget = QWidget()
        ctrl_widget.setLayout(ctrl_vbox)
        top_strip.addWidget(ctrl_widget, stretch=2)

        top_strip_widget = QWidget()
        top_strip_widget.setLayout(top_strip)
        top_strip_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        # ── View-switcher tab bar ─────────────────────────────────────────────
        tab_bar = QHBoxLayout()
        tab_bar.setContentsMargins(0, 4, 0, 0)
        tab_bar.setSpacing(2)

        self._btn_graph_tab = QPushButton("📊  Graph")
        self._btn_graph_tab.setObjectName("tabBtnGraph")
        self._btn_graph_tab.setCheckable(True)
        self._btn_graph_tab.setChecked(True)
        self._btn_graph_tab.setMinimumHeight(32)
        self._btn_graph_tab.clicked.connect(lambda: self._switch_view(0))

        self._btn_details_tab = QPushButton("🔍  Details")
        self._btn_details_tab.setObjectName("tabBtnDetails")
        self._btn_details_tab.setCheckable(True)
        self._btn_details_tab.setMinimumHeight(32)
        self._btn_details_tab.clicked.connect(lambda: self._switch_view(1))

        tab_bar.addWidget(self._btn_graph_tab)
        tab_bar.addWidget(self._btn_details_tab)
        tab_bar.addStretch()

        tab_bar_widget = QWidget()
        tab_bar_widget.setLayout(tab_bar)

        # ── Stacked widget – page 0: Graph, page 1: Details ───────────────────
        self._view_stack = QStackedWidget()

        # Page 0 – Graph (full space)
        self._view_stack.addWidget(self.graph_panel)

        # Page 1 – Details (phase info + fault panel side by side)
        details_page = QWidget()
        details_layout = QHBoxLayout(details_page)
        details_layout.setSpacing(8)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.addWidget(self.phase_info_panel, stretch=1)
        details_layout.addWidget(self.fault_panel, stretch=2)
        self._view_stack.addWidget(details_page)

        # ── Right pane: top strip + tab bar + stacked view ────────────────────
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        right_layout.setSpacing(4)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(top_strip_widget)
        right_layout.addWidget(tab_bar_widget)
        right_layout.addWidget(self._view_stack, stretch=1)

        # ── Horizontal splitter: connection panel | right pane ────────────────
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.addWidget(self.connection_panel)
        top_splitter.addWidget(right_pane)
        top_splitter.setStretchFactor(0, 0)
        top_splitter.setStretchFactor(1, 1)
        top_splitter.setSizes([250, 1050])

        # ── Vertical splitter: content area | log panel ───────────────────────
        self._main_splitter = QSplitter(Qt.Orientation.Vertical)
        self._main_splitter.setObjectName("mainSplitter")
        self._main_splitter.addWidget(top_splitter)
        self._main_splitter.addWidget(self.log_panel)
        self._main_splitter.setStretchFactor(0, 4)
        self._main_splitter.setStretchFactor(1, 1)
        self._main_splitter.setSizes([640, 160])

        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.setSpacing(0)
        vbox.addWidget(self._main_splitter)
        self.setCentralWidget(container)

    # ── View switching ────────────────────────────────────────────────────────

    def _switch_view(self, page: int) -> None:
        """Switch the stacked widget between Graph (0) and Details (1)."""
        self._view_stack.setCurrentIndex(page)
        self._btn_graph_tab.setChecked(page == 0)
        self._btn_details_tab.setChecked(page == 1)
        self._act_graph.setChecked(page == 0)
        self._act_details.setChecked(page == 1)

    def _toggle_log(self, checked: bool) -> None:
        """Show/hide the log panel without destroying its contents."""
        self.log_panel.setVisible(checked)

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
        # Restore last active view page
        page = int(s.value(SETTING_VIEW_PAGE, 0))
        self._switch_view(page)
        # Restore log visibility
        log_visible = s.value(SETTING_LOG_VISIBLE, True)
        visible = log_visible if isinstance(log_visible, bool) else log_visible == "true"
        self._act_log.setChecked(visible)
        self.log_panel.setVisible(visible)

    def closeEvent(self, event: QCloseEvent) -> None:
        s = QSettings(ORG_NAME, APP_NAME)
        s.setValue(SETTING_WINDOW_GEOMETRY, self.saveGeometry())
        s.setValue(SETTING_WINDOW_STATE, self.saveState())
        s.setValue(SETTING_SPLITTER_STATE, self._main_splitter.saveState())
        s.setValue(SETTING_VIEW_PAGE, self._view_stack.currentIndex())
        s.setValue(SETTING_LOG_VISIBLE, self.log_panel.isVisible())
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
