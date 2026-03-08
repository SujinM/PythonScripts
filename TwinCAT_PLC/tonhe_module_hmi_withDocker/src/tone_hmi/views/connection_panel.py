"""
connection_panel.py
────────────────────
ADS connection settings and status panel.
Shows AMS Net ID / IP / Port from config and a colour-coded status LED.
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
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

from tone_hmi.constants import STATUS_CONNECTED, STATUS_CONNECTING, STATUS_DISCONNECTED


class ConnectionPanel(QGroupBox):
    """ADS connection control panel.

    Signals:
        connect_requested:    User clicked Connect.
        disconnect_requested: User clicked Disconnect.
    """

    connect_requested = pyqtSignal()
    disconnect_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("ADS Connection", parent)
        self.setMinimumWidth(240)

        self._led = QLabel("●")
        self._led.setFixedWidth(18)
        self._status_label = QLabel("Disconnected")

        self._ams_field = QLineEdit()
        self._ams_field.setReadOnly(True)
        self._ams_field.setPlaceholderText("–")

        self._ip_field = QLineEdit()
        self._ip_field.setReadOnly(True)
        self._ip_field.setPlaceholderText("–")

        self._port_field = QLineEdit()
        self._port_field.setReadOnly(True)
        self._port_field.setPlaceholderText("–")
        self._port_field.setMaximumWidth(70)

        self._btn_connect = QPushButton("Connect")
        self._btn_connect.setObjectName("btnConnect")
        self._btn_disconnect = QPushButton("Disconnect")
        self._btn_disconnect.setObjectName("btnDisconnect")
        self._btn_disconnect.setEnabled(False)

        self._btn_connect.clicked.connect(self.connect_requested)
        self._btn_disconnect.clicked.connect(self.disconnect_requested)

        self._build_layout()
        self.set_disconnected()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        form = QFormLayout()
        form.setSpacing(6)
        form.addRow("AMS Net ID:", self._ams_field)
        form.addRow("IP Address:", self._ip_field)
        form.addRow("Port:", self._port_field)

        status_row = QHBoxLayout()
        status_row.addWidget(self._led)
        status_row.addWidget(self._status_label)
        status_row.addStretch()
        status_widget = QWidget()
        status_widget.setLayout(status_row)
        form.addRow("Status:", status_widget)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self._btn_connect)
        btn_row.addWidget(self._btn_disconnect)

        vbox = QVBoxLayout(self)
        vbox.addLayout(form)
        vbox.addLayout(btn_row)
        vbox.addStretch()

    # ── Public API ────────────────────────────────────────────────────────────

    def populate_from_config(self, cfg) -> None:
        self._ams_field.setText(cfg.connection.ams_net_id)
        self._ip_field.setText(cfg.connection.ip_address)
        self._port_field.setText(str(cfg.connection.port))

    def set_connecting(self) -> None:
        self._apply_led(STATUS_CONNECTING)
        self._status_label.setText("Connecting…")
        self._btn_connect.setEnabled(False)
        self._btn_disconnect.setEnabled(False)

    def set_connected(self, label: str = "Connected") -> None:
        self._apply_led(STATUS_CONNECTED)
        self._status_label.setText(label)
        self._btn_connect.setEnabled(False)
        self._btn_disconnect.setEnabled(True)

    def set_disconnected(self) -> None:
        self._apply_led(STATUS_DISCONNECTED)
        self._status_label.setText("Disconnected")
        self._btn_connect.setEnabled(True)
        self._btn_disconnect.setEnabled(False)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _apply_led(self, color: str) -> None:
        self._led.setStyleSheet(f"color: {color}; font-size: 18px;")
