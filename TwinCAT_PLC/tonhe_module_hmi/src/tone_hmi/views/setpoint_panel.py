"""
setpoint_panel.py
──────────────────
Panel for reading and writing voltage / current setpoints and ramp settings.

The operator can type a new voltage (in V) or current (in A), configure the
soft-start voltage ramp, then press Apply to write the encoded values to the
PLC and pulse bUpdateSetpoint.
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QDoubleValidator, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
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
                         carries (voltage_v, current_a, enable_ramp,
                                  ramp_step_v, ramp_time_s).
                         voltage_v    : float — voltage setpoint in Volts
                         current_a    : float — current setpoint in Amps
                         enable_ramp  : bool  — enable soft-start ramp
                         ramp_step_v  : float — ramp step size in Volts
                         ramp_time_s  : float — step interval in seconds
    """

    apply_requested = pyqtSignal(float, float, bool, float, float)
    update_vi_requested = pyqtSignal()

    # Limits from TONHE V1.3 spec (realistic maximums)
    _VOLT_MIN = 0.0
    _VOLT_MAX = 1000.0
    _CURR_MIN = 0.0
    _CURR_MAX = 200.0
    _RAMP_STEP_MIN = 0.0
    _RAMP_STEP_MAX = 200.0
    _RAMP_TIME_MIN = 0.1
    _RAMP_TIME_MAX = 60.0

    _EDIT_W   = 110
    _EDIT_H   = 26
    _UNIT_SS  = "color: #9e9e9e; font-size: 8pt;"
    _KEY_SS   = "color: #9e9e9e; font-size: 8pt;"
    _LIVE_SS  = "color: #64b5f6; font-family: Consolas; font-size: 9pt;"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Setpoints && Ramp", parent)

        # ── Live readback labels ──────────────────────────────────────────
        self._volt_live = self._make_live_label("–––  V")
        self._curr_live = self._make_live_label("–––  A")

        # ── Setpoint editors ─────────────────────────────────────────────
        self._volt_edit = self._make_edit(
            "500.0",
            QDoubleValidator(self._VOLT_MIN, self._VOLT_MAX, 1),
        )
        self._curr_edit = self._make_edit(
            "41.00",
            QDoubleValidator(self._CURR_MIN, self._CURR_MAX, 2),
        )

        # ── Ramp controls ─────────────────────────────────────────────────
        self._ramp_chk = QCheckBox("Enable soft-start ramp")
        self._ramp_chk.setFont(QFont("Segoe UI", 8))
        self._ramp_chk.setToolTip(
            "When enabled, voltage is stepped up gradually from 0 to setpoint on START"
        )

        self._ramp_step_edit = self._make_edit(
            "10.0",
            QDoubleValidator(self._RAMP_STEP_MIN, self._RAMP_STEP_MAX, 1),
            tooltip="Voltage increase per ramp step (V)",
        )
        self._ramp_time_edit = self._make_edit(
            "1.0",
            QDoubleValidator(self._RAMP_TIME_MIN, self._RAMP_TIME_MAX, 2),
            tooltip="Time between each ramp step (s)",
        )
        self._ramp_voltage_live = self._make_live_label("–––  V")
        self._ramp_voltage_live.setToolTip("Current ramp voltage during soft-start")

        # ── Write Setpoints button ────────────────────────────────────────
        self._btn_apply = QPushButton("⬆   Write Setpoints")
        self._btn_apply.setObjectName("btnApplySetpoint")
        self._btn_apply.setFixedSize(170, 34)
        self._btn_apply.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_apply.setToolTip(
            "Write voltage/current setpoints and ramp settings to PLC memory (stSettings)"
        )
        self._btn_apply.setEnabled(False)
        self._btn_apply.setStyleSheet(
            "QPushButton#btnApplySetpoint {"
            "  background: #1565c0; color: #ffffff;"
            "  border: none; border-radius: 6px;"
            "}"
            "QPushButton#btnApplySetpoint:hover  { background: #1976d2; }"
            "QPushButton#btnApplySetpoint:pressed { background: #0d47a1; }"
            "QPushButton#btnApplySetpoint:disabled { background: #555; color: #888; }"
        )

        # ── Send bUpdateSetpoint button ───────────────────────────────────
        self._btn_update_vi = QPushButton("↻   Send Update Signal")
        self._btn_update_vi.setObjectName("btnUpdateVI")
        self._btn_update_vi.setFixedSize(170, 34)
        self._btn_update_vi.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._btn_update_vi.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_update_vi.setToolTip(
            "Pulse bUpdateSetpoint = TRUE so the PLC applies the written V/I setpoints"
        )
        self._btn_update_vi.setEnabled(False)
        self._btn_update_vi.setStyleSheet(
            "QPushButton#btnUpdateVI {"
            "  background: #2e7d32; color: #ffffff;"
            "  border: none; border-radius: 6px;"
            "}"
            "QPushButton#btnUpdateVI:hover  { background: #388e3c; }"
            "QPushButton#btnUpdateVI:pressed { background: #1b5e20; }"
            "QPushButton#btnUpdateVI:disabled { background: #555; color: #888; }"
        )

        self._btn_apply.clicked.connect(self._on_apply)
        self._btn_update_vi.clicked.connect(self._on_update_vi)
        self._volt_edit.returnPressed.connect(self._on_apply)
        self._curr_edit.returnPressed.connect(self._on_apply)

        self._build_layout()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _make_edit(self, placeholder: str, validator, tooltip: str = "") -> QLineEdit:
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setValidator(validator)
        edit.setFixedSize(self._EDIT_W, self._EDIT_H)
        edit.setFont(QFont("Consolas", 9))
        if tooltip:
            edit.setToolTip(tooltip)
        return edit

    def _make_live_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(self._LIVE_SS + "padding-left: 8px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return lbl

    @staticmethod
    def _make_section_header(title: str) -> QLabel:
        lbl = QLabel(title.upper())
        lbl.setStyleSheet(
            "color: #78909c; font-size: 7pt; font-weight: bold; letter-spacing: 1px;"
        )
        return lbl

    @staticmethod
    def _make_divider() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet("color: #3a3a3a;")
        return line

    def _make_key(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(self._KEY_SS + "padding-left: 8px;")
        return lbl

    def _make_unit(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(self._UNIT_SS)
        return lbl

    # ── Layout ────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        # ── Setpoints sub-grid ─────────────────────────────────────────────
        sp_grid = QGridLayout()
        sp_grid.setSpacing(5)
        sp_grid.setContentsMargins(0, 0, 0, 0)
        sp_grid.setColumnStretch(3, 1)

        sp_grid.addWidget(self._make_key("Voltage"),  0, 0)
        sp_grid.addWidget(self._volt_edit,            0, 1)
        sp_grid.addWidget(self._make_unit("V"),       0, 2)
        sp_grid.addWidget(self._volt_live,            0, 3, Qt.AlignmentFlag.AlignLeft)

        sp_grid.addWidget(self._make_key("Current"),  1, 0)
        sp_grid.addWidget(self._curr_edit,            1, 1)
        sp_grid.addWidget(self._make_unit("A"),       1, 2)
        sp_grid.addWidget(self._curr_live,            1, 3, Qt.AlignmentFlag.AlignLeft)

        # ── Ramp sub-grid ──────────────────────────────────────────────────
        ramp_grid = QGridLayout()
        ramp_grid.setSpacing(5)
        ramp_grid.setContentsMargins(0, 0, 0, 0)
        ramp_grid.setColumnStretch(3, 1)

        ramp_grid.addWidget(self._ramp_chk,                   0, 0, 1, 2)
        ramp_grid.addWidget(self._make_key("Progress:"),      0, 2)
        ramp_grid.addWidget(self._ramp_voltage_live,          0, 3, Qt.AlignmentFlag.AlignLeft)

        ramp_grid.addWidget(self._make_key("Step size"),      1, 0)
        ramp_grid.addWidget(self._ramp_step_edit,             1, 1)
        ramp_grid.addWidget(self._make_unit("V / step"),      1, 2)

        ramp_grid.addWidget(self._make_key("Step time"),      2, 0)
        ramp_grid.addWidget(self._ramp_time_edit,             2, 1)
        ramp_grid.addWidget(self._make_unit("s"),             2, 2)

        # ── Button row ─────────────────────────────────────────────────────
        apply_row = QHBoxLayout()
        apply_row.setContentsMargins(0, 0, 0, 0)
        apply_row.setSpacing(8)
        apply_row.addWidget(self._btn_apply)
        apply_row.addWidget(self._btn_update_vi)
        apply_row.addStretch()

        # ── Assemble ───────────────────────────────────────────────────────
        vbox = QVBoxLayout(self)
        vbox.setSpacing(6)
        vbox.setContentsMargins(10, 8, 10, 10)
        vbox.addWidget(self._make_section_header("Output Setpoints"))
        vbox.addLayout(sp_grid)
        vbox.addWidget(self._make_divider())
        vbox.addWidget(self._make_section_header("Soft-Start Ramp"))
        vbox.addLayout(ramp_grid)
        vbox.addWidget(self._make_divider())
        vbox.addLayout(apply_row)
        vbox.addStretch()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_connected(self) -> None:
        self._btn_apply.setEnabled(True)
        self._btn_update_vi.setEnabled(True)

    def set_disconnected(self) -> None:
        self._btn_apply.setEnabled(False)
        self._btn_update_vi.setEnabled(False)

    def update_live_voltage(self, v: float | None) -> None:
        self._volt_live.setText(f"{v:.1f} V" if v is not None else "––– V")

    def update_live_current(self, a: float | None) -> None:
        self._curr_live.setText(f"{a:.2f} A" if a is not None else "––– A")

    def update_live_ramp_voltage(self, v: float | None) -> None:
        """Show current ramp voltage progress (V)."""
        if v is not None:
            self._ramp_voltage_live.setText(f"{v:.1f} V")
        else:
            self._ramp_voltage_live.setText("––– V")

    def populate_setpoints(self, voltage_v: float | None, current_a: float | None) -> None:
        """Pre-fill the V/I editor fields with the current PLC setpoints."""
        if voltage_v is not None:
            self._volt_edit.setText(f"{voltage_v:.1f}")
        if current_a is not None:
            self._curr_edit.setText(f"{current_a:.2f}")

    def populate_ramp_settings(
        self,
        enable_ramp: bool | None,
        ramp_step_v: float | None,
        ramp_time_s: float | None,
    ) -> None:
        """Pre-fill ramp fields with the current PLC ramp configuration."""
        if enable_ramp is not None:
            self._ramp_chk.setChecked(bool(enable_ramp))
        if ramp_step_v is not None:
            self._ramp_step_edit.setText(f"{ramp_step_v:.1f}")
        if ramp_time_s is not None:
            self._ramp_time_edit.setText(f"{ramp_time_s:.2f}")

    # ── Slot ──────────────────────────────────────────────────────────────────

    def _on_apply(self) -> None:
        try:
            voltage_v = max(0.0, float(self._volt_edit.text().replace(",", ".")))
            current_a = max(0.0, float(self._curr_edit.text().replace(",", ".")))
        except ValueError:
            return

        enable_ramp = self._ramp_chk.isChecked()

        try:
            ramp_step_v = max(0.0, float(self._ramp_step_edit.text().replace(",", ".")))
        except ValueError:
            ramp_step_v = 10.0  # default 10 V

        try:
            ramp_time_s = float(self._ramp_time_edit.text().replace(",", "."))
            ramp_time_s = max(self._RAMP_TIME_MIN, min(self._RAMP_TIME_MAX, ramp_time_s))
        except ValueError:
            ramp_time_s = 1.0  # default 1 s

        self.apply_requested.emit(voltage_v, current_a, enable_ramp, ramp_step_v, ramp_time_s)

    def _on_update_vi(self) -> None:
        self.update_vi_requested.emit()
