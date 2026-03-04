"""
module_status_panel.py
───────────────────────
Large status panel showing:
  • Module state (OFF / ON / FAULT) with a colour indicator
  • Output voltage and current with big digit display
  • CAN node state and acknowledgment flags
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from tone_hmi.constants import (
    STATE_FAULT_COLOR,
    STATE_OFF_COLOR,
    STATE_ON_COLOR,
    STATE_UNKNOWN_COLOR,
)

_BIG_FONT = QFont("Consolas", 32, QFont.Weight.Bold)
_MED_FONT = QFont("Segoe UI", 14, QFont.Weight.Bold)
_SMALL_FONT = QFont("Segoe UI", 10)


def _make_separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


class _MetricCard(QGroupBox):
    """A small card with a large value display and unit label."""

    def __init__(self, title: str, unit: str, parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
        self._value_label = QLabel("–––")
        self._value_label.setFont(_BIG_FONT)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value_label.setObjectName("metricValue")

        self._unit_label = QLabel(unit)
        self._unit_label.setFont(_SMALL_FONT)
        self._unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._unit_label.setObjectName("metricUnit")

        vbox = QVBoxLayout(self)
        vbox.addWidget(self._value_label)
        vbox.addWidget(self._unit_label)

    def set_value(self, value: float | None, fmt: str = ".1f") -> None:
        if value is None:
            self._value_label.setText("–––")
        else:
            self._value_label.setText(f"{value:{fmt}}")

    def set_color(self, color: str) -> None:
        self._value_label.setStyleSheet(f"color: {color};")


class ModuleStatusPanel(QGroupBox):
    """Main status display for the TONHE charging module.

    Displays:
        - State badge (OFF / ON / FAULT)
        - Output voltage (large)
        - Output current (large)
        - Status text from PLC
        - Boolean flags: Module Running, Status Received, Ack Received, Fault
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Module Status", parent)

        # ── State badge ───────────────────────────────────────────────────────
        self._state_led = QLabel("●")
        self._state_led.setFont(QFont("Segoe UI", 22))
        self._state_led.setFixedWidth(36)
        self._state_label = QLabel("UNKNOWN")
        self._state_label.setFont(_MED_FONT)
        self._state_label.setObjectName("stateBadge")

        # ── Metric cards ──────────────────────────────────────────────────────
        self._voltage_card = _MetricCard("Output Voltage", "V")
        self._current_card = _MetricCard("Output Current", "A")

        # ── Status text ───────────────────────────────────────────────────────
        self._status_text = QLabel("–")
        self._status_text.setWordWrap(True)
        self._status_text.setObjectName("statusText")
        self._status_text.setFont(QFont("Segoe UI", 9))

        # ── Boolean flag indicators ───────────────────────────────────────────
        self._flag_running = _FlagIndicator("Running")
        self._flag_status_rx = _FlagIndicator("Status RX")
        self._flag_ack_rx = _FlagIndicator("ACK RX")
        self._flag_fault = _FlagIndicator("Fault", fault=True)

        self._build_layout()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        # State row
        state_row = QHBoxLayout()
        state_row.addWidget(self._state_led)
        state_row.addWidget(self._state_label)
        state_row.addStretch()

        # Flags row
        flags_row = QHBoxLayout()
        flags_row.setSpacing(8)
        for flag in (self._flag_running, self._flag_status_rx,
                     self._flag_ack_rx, self._flag_fault):
            flags_row.addWidget(flag)
        flags_row.addStretch()

        # Metric cards
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(12)
        metrics_row.addWidget(self._voltage_card)
        metrics_row.addWidget(self._current_card)

        # Status text box
        status_group = QGroupBox("PLC Status Message")
        sl = QVBoxLayout(status_group)
        sl.addWidget(self._status_text)

        # Final layout
        vbox = QVBoxLayout(self)
        vbox.setSpacing(10)
        vbox.addLayout(state_row)
        vbox.addWidget(_make_separator())
        vbox.addLayout(metrics_row)
        vbox.addWidget(_make_separator())
        vbox.addLayout(flags_row)
        vbox.addWidget(status_group)

    # ── Public update API (called by ModuleController) ────────────────────────

    def update_module_status(self, status_byte: int | None) -> None:
        """Set LED + badge from the M_C_1 nModuleStatus byte."""
        if status_byte is None:
            self._apply_state(STATE_UNKNOWN_COLOR, "UNKNOWN")
            return
        if status_byte == 0x01:
            self._apply_state(STATE_ON_COLOR, "ON")
        elif status_byte == 0x11:
            self._apply_state(STATE_FAULT_COLOR, "FAULT")
        else:
            self._apply_state(STATE_OFF_COLOR, "OFF")

    def update_voltage(self, v: float | None) -> None:
        self._voltage_card.set_value(v, ".1f")
        if v is not None:
            color = "#27ae60" if v > 1.0 else "#7f8c8d"
            self._voltage_card.set_color(color)

    def update_current(self, a: float | None) -> None:
        self._current_card.set_value(a, ".2f")
        if a is not None:
            color = "#2980b9" if a > 0.1 else "#7f8c8d"
            self._current_card.set_color(color)

    def update_status_text(self, text: str | None) -> None:
        self._status_text.setText(text or "–")

    def update_flags(
        self,
        running: bool,
        status_received: bool,
        ack_received: bool,
        fault: bool,
    ) -> None:
        self._flag_running.set_active(running)
        self._flag_status_rx.set_active(status_received)
        self._flag_ack_rx.set_active(ack_received)
        self._flag_fault.set_active(fault)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _apply_state(self, color: str, text: str) -> None:
        self._state_led.setStyleSheet(f"color: {color}; font-size: 24px;")
        self._state_label.setText(text)
        self._state_label.setStyleSheet(f"color: {color}; font-weight: bold;")


class _FlagIndicator(QWidget):
    """Small pill-shaped boolean indicator."""

    _ON_STYLE = "background: #27ae60; color: white; border-radius: 4px; padding: 2px 8px;"
    _OFF_STYLE = "background: #2c3e50; color: #7f8c8d; border-radius: 4px; padding: 2px 8px;"
    _FAULT_ON_STYLE = "background: #e74c3c; color: white; border-radius: 4px; padding: 2px 8px;"

    def __init__(self, label: str, fault: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._fault = fault
        self._label = QLabel(label)
        self._label.setFont(QFont("Segoe UI", 8))
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        self.set_active(False)

    def set_active(self, active: bool) -> None:
        if active:
            self._label.setStyleSheet(
                self._FAULT_ON_STYLE if self._fault else self._ON_STYLE
            )
        else:
            self._label.setStyleSheet(self._OFF_STYLE)
