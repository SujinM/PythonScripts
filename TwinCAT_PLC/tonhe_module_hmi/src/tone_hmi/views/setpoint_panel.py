"""
setpoint_panel.py
──────────────────
Panel for reading and writing voltage / current setpoints.

The operator can type a new voltage (in V) or current (in A), then press
Apply to write the encoded integer values to the PLC and pulse bUpdateVI.
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SetpointPanel(QGroupBox):
    """Voltage / Current setpoint editor.

    Signals:
        apply_requested: Emitted when the operator clicks Apply;
                         carries (voltage_raw: int, current_raw: int).
                         voltage_raw is in 0.1 V/bit, current_raw in 0.01 A/bit.
    """

    apply_requested = pyqtSignal(int, int)   # (voltage_raw, current_raw)

    # Limits from TONHE V1.3 spec (realistic maximums)
    _VOLT_MIN = 0.0
    _VOLT_MAX = 1000.0    # 1000 V
    _CURR_MIN = 0.0
    _CURR_MAX = 200.0     # 200 A

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Setpoints", parent)

        # ── Live readback labels ──────────────────────────────────────────────
        self._volt_live = QLabel("–––  V")
        self._curr_live = QLabel("–––  A")

        # ── Write editors ─────────────────────────────────────────────────────
        self._volt_edit = QLineEdit()
        self._volt_edit.setPlaceholderText("e.g.  500.0")
        self._volt_edit.setValidator(
            QDoubleValidator(self._VOLT_MIN, self._VOLT_MAX, 1, self._volt_edit)
        )
        self._volt_edit.setMaximumWidth(120)

        self._curr_edit = QLineEdit()
        self._curr_edit.setPlaceholderText("e.g.  41.00")
        self._curr_edit.setValidator(
            QDoubleValidator(self._CURR_MIN, self._CURR_MAX, 2, self._curr_edit)
        )
        self._curr_edit.setMaximumWidth(120)

        self._btn_apply = QPushButton("⬆  Apply")
        self._btn_apply.setObjectName("btnApplySetpoint")
        self._btn_apply.setFixedHeight(28)
        self._btn_apply.setToolTip(
            "Write new voltage/current setpoints and pulse bUpdateVI"
        )
        self._btn_apply.setEnabled(False)

        self._btn_apply.clicked.connect(self._on_apply)
        self._volt_edit.returnPressed.connect(self._on_apply)
        self._curr_edit.returnPressed.connect(self._on_apply)

        self._build_layout()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        # Two-row grid: label | input | unit | live readback
        # This halves the vertical height compared to 4 separate form rows.
        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setColumnStretch(3, 1)   # live-value column takes remaining space

        grid.addWidget(QLabel("Voltage:"), 0, 0)
        grid.addWidget(self._volt_edit, 0, 1)
        grid.addWidget(QLabel("V"), 0, 2)
        grid.addWidget(self._volt_live, 0, 3)

        grid.addWidget(QLabel("Current:"), 1, 0)
        grid.addWidget(self._curr_edit, 1, 1)
        grid.addWidget(QLabel("A"), 1, 2)
        grid.addWidget(self._curr_live, 1, 3)

        vbox = QVBoxLayout(self)
        vbox.setSpacing(4)
        vbox.setContentsMargins(8, 6, 8, 6)
        vbox.addLayout(grid)
        vbox.addWidget(self._btn_apply)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_connected(self) -> None:
        self._btn_apply.setEnabled(True)

    def set_disconnected(self) -> None:
        self._btn_apply.setEnabled(False)

    def update_live_voltage(self, v: float | None) -> None:
        self._volt_live.setText(f"{v:.1f}  V" if v is not None else "–––  V")

    def update_live_current(self, a: float | None) -> None:
        self._curr_live.setText(f"{a:.2f}  A" if a is not None else "–––  A")

    def populate_setpoints(self, voltage_raw: int | None, current_raw: int | None) -> None:
        """Pre-fill the editor fields with the current PLC setpoints."""
        if voltage_raw is not None:
            self._volt_edit.setText(f"{voltage_raw / 10:.1f}")
        if current_raw is not None:
            self._curr_edit.setText(f"{current_raw / 100:.2f}")

    # ── Slot ──────────────────────────────────────────────────────────────────

    def _on_apply(self) -> None:
        try:
            v_f = float(self._volt_edit.text().replace(",", "."))
            a_f = float(self._curr_edit.text().replace(",", "."))
        except ValueError:
            return
        v_raw = max(0, round(v_f * 10))      # 0.1 V/bit
        a_raw = max(0, round(a_f * 100))     # 0.01 A/bit
        self.apply_requested.emit(v_raw, a_raw)
