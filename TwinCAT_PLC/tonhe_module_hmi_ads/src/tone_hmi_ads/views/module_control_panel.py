"""
module_control_panel.py
────────────────────────
Control panel with Start / Stop / Clear Fault buttons and module address
configuration.  All button clicks are forwarded as Qt signals; the
ModuleController handles the actual ADS write.
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ModuleControlPanel(QGroupBox):
    """Command panel for the TONHE charging module.

    Signals:
        start_requested:       User pressed Start.
        stop_requested:        User pressed Stop.
        clear_fault_requested: User pressed Clear Fault.
    """

    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    _BTN_FONT   = QFont("Segoe UI", 9, QFont.Weight.Bold)
    _INFO_FONT  = QFont("Consolas", 10)
    _LABEL_FONT = QFont("Segoe UI", 8)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Module Control", parent)

        # ── Primary action buttons ─────────────────────────────────────────
        self._btn_start = QPushButton("▶   START")
        self._btn_start.setObjectName("btnStart")
        self._btn_start.setFixedSize(116, 38)
        self._btn_start.setFont(self._BTN_FONT)
        self._btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_start.setToolTip("Send Start command (0xAA) to the module")
        self._btn_start.setStyleSheet(
            "QPushButton#btnStart {"
            "  background: #2e7d32; color: #ffffff;"
            "  border: none; border-radius: 6px;"
            "}"
            "QPushButton#btnStart:hover  { background: #388e3c; }"
            "QPushButton#btnStart:pressed { background: #1b5e20; }"
            "QPushButton#btnStart:disabled { background: #555; color: #888; }"
        )

        self._btn_stop = QPushButton("■   STOP")
        self._btn_stop.setObjectName("btnStop")
        self._btn_stop.setFixedSize(116, 38)
        self._btn_stop.setFont(self._BTN_FONT)
        self._btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_stop.setToolTip("Send Stop command (0x55) to the module")
        self._btn_stop.setStyleSheet(
            "QPushButton#btnStop {"
            "  background: #c62828; color: #ffffff;"
            "  border: none; border-radius: 6px;"
            "}"
            "QPushButton#btnStop:hover  { background: #d32f2f; }"
            "QPushButton#btnStop:pressed { background: #b71c1c; }"
            "QPushButton#btnStop:disabled { background: #555; color: #888; }"
        )

        # ── Clear Fault button removed — now lives in ModuleStatusPanel flags row ──

        # ── Info value labels ──────────────────────────────────────────────
        self._module_addr_label = self._make_value_label("0x01")
        self._master_addr_label = self._make_value_label("0xA0")
        self._retry_label       = self._make_value_label("0 / 10")

        # ── Signal wiring ─────────────────────────────────────────────────
        self._btn_start.clicked.connect(self.start_requested)
        self._btn_stop.clicked.connect(self.stop_requested)

        self._build_layout()
        self.set_disconnected()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _make_value_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(self._INFO_FONT)
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        lbl.setStyleSheet("padding-left: 8px; padding-right: 4px;")
        lbl.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        return lbl

    @staticmethod
    def _make_key_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 8))
        lbl.setStyleSheet("color: #9e9e9e; padding-left: 8px; padding-right: 4px;")
        return lbl

    @staticmethod
    def _make_divider() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet("color: #3a3a3a;")
        return line

    # ── Layout ────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        # Primary buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addWidget(self._btn_start)
        btn_row.addWidget(self._btn_stop)
        btn_row.addStretch()

        # Info grid: key | value | <stretch>
        info = QGridLayout()
        info.setSpacing(4)
        info.setContentsMargins(0, 0, 0, 0)
        info.setColumnStretch(2, 1)  # col 2 absorbs leftover space

        rows = [
            ("Module Addr", self._module_addr_label),
            ("Master Addr", self._master_addr_label),
            ("Retries",     self._retry_label),
        ]
        for r, (key, val) in enumerate(rows):
            key_lbl = self._make_key_label(key)
            info.addWidget(key_lbl, r, 0)
            info.addWidget(val,     r, 1)

        vbox = QVBoxLayout(self)
        vbox.setSpacing(8)
        vbox.setContentsMargins(10, 8, 10, 10)
        vbox.addLayout(btn_row)
        vbox.addWidget(self._make_divider())
        vbox.addLayout(info)
        vbox.addStretch()

    # ── Public API ────────────────────────────────────────────────────────

    def set_disconnected(self) -> None:
        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(False)

    def set_connected(self) -> None:
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)

    def update_running_state(self, running: bool) -> None:
        """Disable Start while module is running; disable Stop while idle."""
        self._btn_start.setEnabled(not running)
        self._btn_stop.setEnabled(running)

    def update_addresses(self, module_addr: int | None, master_addr: int | None) -> None:
        if module_addr is not None:
            self._module_addr_label.setText(f"0x{module_addr:02X} ({module_addr})")
        if master_addr is not None:
            self._master_addr_label.setText(f"0x{master_addr:02X} ({master_addr})")

    def update_retries(self, count: int | None, max_count: int | None) -> None:
        c = count if count is not None else "–"
        m = max_count if max_count is not None else "–"
        self._retry_label.setText(f"{c} / {m}")
