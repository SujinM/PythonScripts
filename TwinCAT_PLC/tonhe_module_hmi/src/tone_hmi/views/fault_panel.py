"""
fault_panel.py
───────────────
Fault and diagnostic information panel.

Shows:
  • wModuleFaults (M_C_1 fault word) bit descriptions
  • wModuleExtFaultWarningBits (M_C_4 extended bits)
  • wModuleStatusBits (M_C_4 status bits)
  • PFC fault byte
  • CAN diagnostic counters
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# TONHE V1.3 wModuleFaults (M_C_1 bytes 4-5) bit descriptions
_FAULT_BITS: dict[int, str] = {
    0:  "Output over-voltage",
    1:  "Output under-voltage",
    2:  "Output over-current",
    3:  "Output short-circuit",
    4:  "Input over-voltage",
    5:  "Input under-voltage",
    6:  "Input phase loss",
    7:  "Over-temperature",
    8:  "Fan failure",
    9:  "Communication timeout",
    10: "PFC fault",
    11: "LLC fault",
    12: "Relay fault",
    13: "EEPROM fault",
    14: "Reserved",
    15: "General fault",
}

_EXT_FAULT_BITS: dict[int, str] = {
    0:  "AC input over-voltage (ext)",
    1:  "AC input under-voltage (ext)",
    2:  "DC bus over-voltage",
    3:  "DC bus under-voltage",
    4:  "Output over-current (ext)",
    5:  "Over-temperature (ext)",
    6:  "Ambient over-temperature",
    7:  "Fan fault (ext)",
    8:  "Input phase loss (ext)",
    9:  "PFC over-current",
    10: "LLC over-current",
    11: "Parallel current imbalance",
    14: "Warning: current limiting",
    15: "Warning: voltage derating",
}


def _decode_word(word: int, bit_map: dict[int, str]) -> str:
    active = [desc for bit, desc in bit_map.items() if word & (1 << bit)]
    return "\n".join(f"  • {d}" for d in active) if active else "  (none)"


class FaultPanel(QGroupBox):
    """Fault status and CAN diagnostic display."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Faults & Diagnostics", parent)

        mono = QFont("Consolas", 9)

        # ── Fault text areas ──────────────────────────────────────────────────
        self._faults_edit = QTextEdit()
        self._faults_edit.setReadOnly(True)
        self._faults_edit.setFont(mono)
        self._faults_edit.setFixedHeight(90)
        self._faults_edit.setPlaceholderText("wModuleFaults bits will appear here")

        self._ext_faults_edit = QTextEdit()
        self._ext_faults_edit.setReadOnly(True)
        self._ext_faults_edit.setFont(mono)
        self._ext_faults_edit.setFixedHeight(90)
        self._ext_faults_edit.setPlaceholderText("wModuleExtFaultWarningBits will appear here")

        # ── Quick-read labels ─────────────────────────────────────────────────
        self._faults_word_lbl = QLabel("–")
        self._ext_word_lbl = QLabel("–")
        self._status_bits_lbl = QLabel("–")
        self._pfc_lbl = QLabel("–")
        self._rx_count_lbl = QLabel("–")
        self._last_cobid_lbl = QLabel("–")
        for lbl in (self._faults_word_lbl, self._ext_word_lbl,
                    self._status_bits_lbl, self._pfc_lbl,
                    self._rx_count_lbl, self._last_cobid_lbl):
            lbl.setFont(QFont("Consolas", 10))

        self._build_layout()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        form = QFormLayout()
        form.setSpacing(6)
        form.addRow("Fault Word (hex):", self._faults_word_lbl)
        form.addRow("Ext Fault Word (hex):", self._ext_word_lbl)
        form.addRow("Status Bits (hex):", self._status_bits_lbl)
        form.addRow("PFC Faults (hex):", self._pfc_lbl)
        form.addRow("RX Frame Count:", self._rx_count_lbl)
        form.addRow("Last COB-ID:", self._last_cobid_lbl)

        g_faults = QGroupBox("wModuleFaults Decoded")
        g_faults_l = QVBoxLayout(g_faults)
        g_faults_l.addWidget(self._faults_edit)

        g_ext = QGroupBox("wModuleExtFaultWarningBits Decoded")
        g_ext_l = QVBoxLayout(g_ext)
        g_ext_l.addWidget(self._ext_faults_edit)

        vbox = QVBoxLayout(self)
        vbox.setSpacing(8)
        vbox.addLayout(form)
        vbox.addWidget(g_faults)
        vbox.addWidget(g_ext)

    # ── Public update API ─────────────────────────────────────────────────────

    def update_faults(
        self,
        faults: int | None,
        ext_faults: int | None,
        status_bits: int | None,
        pfc_faults: int | None,
    ) -> None:
        fw = faults or 0
        ef = ext_faults or 0
        self._faults_word_lbl.setText(f"0x{fw:04X}" if faults is not None else "–")
        self._ext_word_lbl.setText(f"0x{ef:04X}" if ext_faults is not None else "–")
        self._status_bits_lbl.setText(
            f"0x{status_bits:04X}" if status_bits is not None else "–"
        )
        self._pfc_lbl.setText(f"0x{pfc_faults:02X}" if pfc_faults is not None else "–")

        self._faults_edit.setPlainText(_decode_word(fw, _FAULT_BITS))
        self._ext_faults_edit.setPlainText(_decode_word(ef, _EXT_FAULT_BITS))

        # Colour the fault word red when non-zero
        color = "#e74c3c" if fw else "#27ae60"
        self._faults_word_lbl.setStyleSheet(f"color: {color};")
        color2 = "#e74c3c" if ef else "#27ae60"
        self._ext_word_lbl.setStyleSheet(f"color: {color2};")

    def update_diagnostics(self, rx_count: int | None, last_cob_id: int | None) -> None:
        self._rx_count_lbl.setText(str(rx_count) if rx_count is not None else "–")
        self._last_cobid_lbl.setText(
            f"0x{last_cob_id:08X}" if last_cob_id is not None else "–"
        )
