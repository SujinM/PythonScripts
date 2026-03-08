"""
setpoint_panel.py
──────────────────
Panel for reading and writing voltage / current setpoints and ramp settings.

The operator can type a new voltage (in V) or current (in A), configure the
soft-start voltage ramp, then press Apply to write the encoded values to the
PLC and pulse bUpdateSetpoint.
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SetpointPanel(QGroupBox):
    """Voltage / Current setpoint editor with ramp configuration.

    Signals:
        apply_requested: Emitted when the operator clicks Apply;
                         carries (voltage_raw, current_raw, enable_ramp,
                                  ramp_step_raw, ramp_time_ms).
                         voltage_raw  : int  — 0.1 V/bit
                         current_raw  : int  — 0.01 A/bit
                         enable_ramp  : bool — enable soft-start ramp
                         ramp_step_raw: int  — ramp step in 0.1 V/bit units
                         ramp_time_ms : int  — step interval in milliseconds
    """

    apply_requested = pyqtSignal(int, int, bool, int, int)

    # Limits from TONHE V1.3 spec (realistic maximums)
    _VOLT_MIN = 0.0
    _VOLT_MAX = 1000.0    # 1000 V
    _CURR_MIN = 0.0
    _CURR_MAX = 200.0     # 200 A
    _RAMP_STEP_MIN = 0.0
    _RAMP_STEP_MAX = 200.0    # 200 V per step max
    _RAMP_TIME_MIN = 100      # 100 ms minimum step time
    _RAMP_TIME_MAX = 60000    # 60 s maximum step time

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Setpoints && Ramp", parent)

        # ── Live readback labels ──────────────────────────────────────────────
        self._volt_live = QLabel("–––  V")
        self._curr_live = QLabel("–––  A")

        # ── Setpoint editors ──────────────────────────────────────────────────
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

        # ── Ramp controls ─────────────────────────────────────────────────────
        self._ramp_chk = QCheckBox("Enable soft-start ramp")
        self._ramp_chk.setToolTip(
            "When enabled, voltage is stepped up gradually from 0 to setpoint on START"
        )

        self._ramp_step_edit = QLineEdit()
        self._ramp_step_edit.setPlaceholderText("e.g.  10.0")
        self._ramp_step_edit.setValidator(
            QDoubleValidator(self._RAMP_STEP_MIN, self._RAMP_STEP_MAX, 1, self._ramp_step_edit)
        )
        self._ramp_step_edit.setMaximumWidth(120)
        self._ramp_step_edit.setToolTip("Voltage increase per ramp step (V)")

        self._ramp_time_edit = QLineEdit()
        self._ramp_time_edit.setPlaceholderText("e.g.  1000")
        self._ramp_time_edit.setValidator(
            QIntValidator(self._RAMP_TIME_MIN, self._RAMP_TIME_MAX, self._ramp_time_edit)
        )
        self._ramp_time_edit.setMaximumWidth(120)
        self._ramp_time_edit.setToolTip("Time between each ramp step (milliseconds)")

        # Ramp live readback
        self._ramp_voltage_live = QLabel("–––  V")
        self._ramp_voltage_live.setToolTip("Current ramp voltage during soft-start")

        # ── Apply button ──────────────────────────────────────────────────────
        self._btn_apply = QPushButton("⬆  Apply")
        self._btn_apply.setObjectName("btnApplySetpoint")
        self._btn_apply.setFixedHeight(28)
        self._btn_apply.setToolTip(
            "Write voltage/current setpoints and ramp settings, then pulse bUpdateSetpoint"
        )
        self._btn_apply.setEnabled(False)

        self._btn_apply.clicked.connect(self._on_apply)
        self._volt_edit.returnPressed.connect(self._on_apply)
        self._curr_edit.returnPressed.connect(self._on_apply)

        self._build_layout()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setColumnStretch(3, 1)

        # Row 0: Voltage setpoint
        grid.addWidget(QLabel("Voltage:"),      0, 0)
        grid.addWidget(self._volt_edit,         0, 1)
        grid.addWidget(QLabel("V"),             0, 2)
        grid.addWidget(self._volt_live,         0, 3)

        # Row 1: Current setpoint
        grid.addWidget(QLabel("Current:"),      1, 0)
        grid.addWidget(self._curr_edit,         1, 1)
        grid.addWidget(QLabel("A"),             1, 2)
        grid.addWidget(self._curr_live,         1, 3)

        # Separator row (spacer label)
        sep = QLabel("── Ramp ─────────────────")
        sep.setStyleSheet("color: gray; font-size: 9pt;")
        grid.addWidget(sep, 2, 0, 1, 4)

        # Row 3: Enable ramp checkbox + live ramp voltage
        grid.addWidget(self._ramp_chk,          3, 0, 1, 2)
        grid.addWidget(QLabel("Now:"),          3, 2)
        grid.addWidget(self._ramp_voltage_live, 3, 3)

        # Row 4: Ramp step size
        grid.addWidget(QLabel("Step size:"),    4, 0)
        grid.addWidget(self._ramp_step_edit,    4, 1)
        grid.addWidget(QLabel("V / step"),      4, 2)

        # Row 5: Ramp step time
        grid.addWidget(QLabel("Step time:"),    5, 0)
        grid.addWidget(self._ramp_time_edit,    5, 1)
        grid.addWidget(QLabel("ms"),            5, 2)

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

    def update_live_ramp_voltage(self, v_raw: int | None) -> None:
        """Show current ramp voltage progress (raw 0.1 V/bit)."""
        if v_raw is not None:
            self._ramp_voltage_live.setText(f"{v_raw / 10:.1f}  V")
        else:
            self._ramp_voltage_live.setText("–––  V")

    def populate_setpoints(self, voltage_raw: int | None, current_raw: int | None) -> None:
        """Pre-fill the V/I editor fields with the current PLC setpoints."""
        if voltage_raw is not None:
            self._volt_edit.setText(f"{voltage_raw / 10:.1f}")
        if current_raw is not None:
            self._curr_edit.setText(f"{current_raw / 100:.2f}")

    def populate_ramp_settings(
        self,
        enable_ramp: bool | None,
        ramp_step_raw: int | None,
        ramp_time_ms: int | None,
    ) -> None:
        """Pre-fill ramp fields with the current PLC ramp configuration."""
        if enable_ramp is not None:
            self._ramp_chk.setChecked(bool(enable_ramp))
        if ramp_step_raw is not None:
            self._ramp_step_edit.setText(f"{ramp_step_raw / 10:.1f}")
        if ramp_time_ms is not None:
            self._ramp_time_edit.setText(str(int(ramp_time_ms)))

    # ── Slot ──────────────────────────────────────────────────────────────────

    def _on_apply(self) -> None:
        try:
            v_f = float(self._volt_edit.text().replace(",", "."))
            a_f = float(self._curr_edit.text().replace(",", "."))
        except ValueError:
            return
        v_raw = max(0, round(v_f * 10))      # 0.1 V/bit
        a_raw = max(0, round(a_f * 100))     # 0.01 A/bit

        enable_ramp = self._ramp_chk.isChecked()

        try:
            step_f = float(self._ramp_step_edit.text().replace(",", "."))
            ramp_step_raw = max(0, round(step_f * 10))   # 0.1 V/bit
        except ValueError:
            ramp_step_raw = 100  # default 10 V

        try:
            ramp_time_ms = int(self._ramp_time_edit.text())
            ramp_time_ms = max(self._RAMP_TIME_MIN, min(self._RAMP_TIME_MAX, ramp_time_ms))
        except ValueError:
            ramp_time_ms = 1000  # default 1 s

        self.apply_requested.emit(v_raw, a_raw, enable_ramp, ramp_step_raw, ramp_time_ms)
