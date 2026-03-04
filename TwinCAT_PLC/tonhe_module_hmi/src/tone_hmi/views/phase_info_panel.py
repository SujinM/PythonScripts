"""
phase_info_panel.py
────────────────────
Displays AC input phase voltages (Va, Vb, Vc) and ambient temperature
received from M_C_3 exchange-info frames.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

_VAL_FONT = QFont("Consolas", 13, QFont.Weight.Bold)


class PhaseInfoPanel(QGroupBox):
    """AC phase voltage and temperature monitor (M_C_3 data)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("AC Input / Environment (M_C_3)", parent)

        self._va = self._make_val_label()
        self._vb = self._make_val_label()
        self._vc = self._make_val_label()
        self._temp = self._make_val_label()

        self._build_layout()

    def _build_layout(self) -> None:
        form = QFormLayout()
        form.setSpacing(8)
        form.addRow("Phase A Voltage:", self._row(self._va, "V"))
        form.addRow("Phase B Voltage:", self._row(self._vb, "V"))
        form.addRow("Phase C Voltage:", self._row(self._vc, "V"))
        form.addRow("Ambient Temp:", self._row(self._temp, "°C"))

        vbox = QVBoxLayout(self)
        vbox.addLayout(form)
        vbox.addStretch()

    @staticmethod
    def _make_val_label() -> QLabel:
        lbl = QLabel("–")
        lbl.setFont(_VAL_FONT)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl.setMinimumWidth(80)
        return lbl

    @staticmethod
    def _row(val_lbl: QLabel, unit: str) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(val_lbl)
        h.addWidget(QLabel(unit))
        return w

    # ── Public update API ─────────────────────────────────────────────────────

    def update_phases(
        self,
        va: float | None,
        vb: float | None,
        vc: float | None,
    ) -> None:
        for lbl, v in ((self._va, va), (self._vb, vb), (self._vc, vc)):
            lbl.setText(f"{v:.1f}" if v is not None else "–")

    def update_temperature(self, temp: int | None) -> None:
        if temp is None:
            self._temp.setText("–")
        else:
            color = "#e74c3c" if temp > 75 else "#27ae60"
            self._temp.setText(f"{temp}")
            self._temp.setStyleSheet(f"color: {color};")
