"""
module_control_panel.py
────────────────────────
Control panel with Start / Stop / Clear Fault buttons and module address
configuration.  All button clicks are forwarded as Qt signals; the
ModuleController handles the actual ADS write.
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont, QIntValidator
from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
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
    clear_fault_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Module Control", parent)

        # ── Buttons ───────────────────────────────────────────────────────────
        self._btn_start = QPushButton("▶  START")
        self._btn_start.setObjectName("btnStart")
        self._btn_start.setFixedHeight(44)
        self._btn_start.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self._btn_start.setToolTip("Send C_M_24 Start command (0xAA) to the module")

        self._btn_stop = QPushButton("■  STOP")
        self._btn_stop.setObjectName("btnStop")
        self._btn_stop.setFixedHeight(44)
        self._btn_stop.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self._btn_stop.setToolTip("Send C_M_24 Stop command (0x55) to the module")

        self._btn_clear = QPushButton("⚑  CLEAR FAULT")
        self._btn_clear.setObjectName("btnClearFault")
        self._btn_clear.setFixedHeight(36)
        self._btn_clear.setToolTip("Clear fault flags and reset PLC state machine")

        # ── Module address fields (informational, could later allow editing) ──
        self._module_addr_label = QLabel("0x01")
        self._module_addr_label.setFont(QFont("Consolas", 11))
        self._master_addr_label = QLabel("0xA0")
        self._master_addr_label.setFont(QFont("Consolas", 11))
        self._retry_label = QLabel("0 / 10")
        self._retry_label.setFont(QFont("Consolas", 11))

        # ── Signal wiring ─────────────────────────────────────────────────────
        self._btn_start.clicked.connect(self.start_requested)
        self._btn_stop.clicked.connect(self.stop_requested)
        self._btn_clear.clicked.connect(self.clear_fault_requested)

        self._build_layout()
        self.set_disconnected()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addWidget(self._btn_start)
        btn_row.addWidget(self._btn_stop)

        form = QFormLayout()
        form.setSpacing(6)
        form.addRow("Module Address:", self._module_addr_label)
        form.addRow("Master Address:", self._master_addr_label)
        form.addRow("Retries:", self._retry_label)

        vbox = QVBoxLayout(self)
        vbox.setSpacing(10)
        vbox.addLayout(btn_row)
        vbox.addWidget(self._btn_clear)
        vbox.addWidget(self._make_separator())
        vbox.addLayout(form)
        vbox.addStretch()

    @staticmethod
    def _make_separator():
        from PyQt6.QtWidgets import QFrame
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    # ── Public API ────────────────────────────────────────────────────────────

    def set_disconnected(self) -> None:
        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(False)
        self._btn_clear.setEnabled(False)

    def set_connected(self) -> None:
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(True)
        self._btn_clear.setEnabled(True)

    def update_addresses(self, module_addr: int | None, master_addr: int | None) -> None:
        if module_addr is not None:
            self._module_addr_label.setText(f"0x{module_addr:02X} ({module_addr})")
        if master_addr is not None:
            self._master_addr_label.setText(f"0x{master_addr:02X} ({master_addr})")

    def update_retries(self, count: int | None, max_count: int | None) -> None:
        c = count if count is not None else "–"
        m = max_count if max_count is not None else "–"
        self._retry_label.setText(f"{c} / {m}")
