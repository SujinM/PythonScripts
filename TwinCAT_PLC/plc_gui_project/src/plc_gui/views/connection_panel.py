"""
connection_panel.py
-------------------
:class:`ConnectionPanel` is a :class:`~PyQt6.QtWidgets.QGroupBox` containing:

* Read-only fields showing AMS Net ID, IP Address and Port (populated from the
  loaded XML config).
* A colour-coded status LED + label showing **Connected / Connecting... /
  Disconnected**.
* **Connect** and **Disconnect** push-buttons.

The panel is purely presentational – it emits signals and its visual state is
set by :class:`~plc_gui.controllers.connection_controller.ConnectionController`.
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
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from plc_gui.constants import STATUS_CONNECTED, STATUS_CONNECTING, STATUS_DISCONNECTED

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from config.config_loader import PLCConfig   # ADS backend


class ConnectionPanel(QGroupBox):
    """
    ADS connection status / control panel.

    Signals:
        connect_requested:    User clicked **Connect**.
        disconnect_requested: User clicked **Disconnect**.
    """

    connect_requested = pyqtSignal()
    disconnect_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("ADS Connection", parent)

        # Fields
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
        self._port_field.setMaximumWidth(80)

        self._btn_connect = QPushButton("Connect")
        self._btn_connect.setObjectName("btnConnect")
        self._btn_disconnect = QPushButton("Disconnect")
        self._btn_disconnect.setObjectName("btnDisconnect")
        self._btn_disconnect.setEnabled(False)

        # Buttons signal forwarding.
        self._btn_connect.clicked.connect(self.connect_requested)
        self._btn_disconnect.clicked.connect(self.disconnect_requested)

        self._build_layout()
        self.set_disconnected()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

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
        form.addRow("Status:", self._status_row_widget(status_row))

        btn_row = QHBoxLayout()
        btn_row.addWidget(self._btn_connect)
        btn_row.addWidget(self._btn_disconnect)
        btn_row.addStretch()

        vbox = QVBoxLayout(self)
        vbox.addLayout(form)
        vbox.addLayout(btn_row)

    @staticmethod
    def _status_row_widget(layout: QHBoxLayout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

    # ------------------------------------------------------------------
    # Public API (called by ConnectionController)
    # ------------------------------------------------------------------

    def populate_from_config(self, cfg: "PLCConfig") -> None:
        """Fill the read-only fields from a loaded :class:`PLCConfig`."""
        self._ams_field.setText(cfg.connection.ams_net_id)
        self._ip_field.setText(cfg.connection.ip_address)
        self._port_field.setText(str(cfg.connection.port))

    def set_connecting(self) -> None:
        """Show amber 'Connecting…' state and disable both buttons."""
        self._apply_led(STATUS_CONNECTING)
        self._status_label.setText("Connecting…")
        self._btn_connect.setEnabled(False)
        self._btn_disconnect.setEnabled(False)

    def set_connected(self, label: str = "Connected") -> None:
        """Show green 'Connected' state."""
        self._apply_led(STATUS_CONNECTED)
        self._status_label.setText(f"Connected  –  {label}")
        self._btn_connect.setEnabled(False)
        self._btn_disconnect.setEnabled(True)

    def set_disconnected(self) -> None:
        """Show red 'Disconnected' state."""
        self._apply_led(STATUS_DISCONNECTED)
        self._status_label.setText("Disconnected")
        self._btn_connect.setEnabled(True)
        self._btn_disconnect.setEnabled(False)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply_led(self, colour: str) -> None:
        self._led.setStyleSheet(f"color: {colour}; font-size: 18px;")
