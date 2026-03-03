"""
connection_controller.py
------------------------
:class:`ConnectionController` wires the
:class:`~plc_gui.views.connection_panel.ConnectionPanel` UI signals to the
background workers (:class:`~plc_gui.workers.connect_worker.ConnectWorker`
and :class:`~plc_gui.workers.disconnect_worker.DisconnectWorker`) and keeps
the UI state (LED colour, button enable/disable, status-bar text) consistent
with the actual ADS connection state.

Responsibilities (single)
~~~~~~~~~~~~~~~~~~~~~~~~~
This controller is responsible **only** for connecting / disconnecting and
reflecting that state in the connection panel.  It knows nothing about
variable reading, polling, or config loading.

Signals emitted upward (consumed by AppController)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* :attr:`connected`      – ADS connection established.
* :attr:`disconnected`   – ADS connection closed.
* :attr:`connect_failed` – ADS connection attempt failed; carries error string.
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, QThreadPool, pyqtSignal

from plc_gui.app_context import AppContext
from plc_gui.workers.connect_worker import ConnectWorker
from plc_gui.workers.disconnect_worker import DisconnectWorker

# Imported lazily so the view package is not required for tests.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from plc_gui.views.connection_panel import ConnectionPanel


class ConnectionController(QObject):
    """
    Mediates between :class:`~plc_gui.views.connection_panel.ConnectionPanel`
    and the ADS background workers.

    Args:
        panel: The connection panel widget.
        ctx:   The shared application context.
        parent: Optional Qt parent.
    """

    connected = pyqtSignal()
    disconnected = pyqtSignal()
    connect_failed = pyqtSignal(str)

    def __init__(
        self,
        panel: "ConnectionPanel",
        ctx: AppContext,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._panel = panel
        self._ctx = ctx
        self._pool = QThreadPool.globalInstance()

        # Connect panel buttons → controller slots.
        panel.connect_requested.connect(self._on_connect_requested)
        panel.disconnect_requested.connect(self._on_disconnect_requested)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_connect_requested(self) -> None:
        """Disable UI and spin up a ConnectWorker."""
        if not self._ctx.is_loaded:
            self.connect_failed.emit("No configuration loaded.  Open a config file first.")
            return

        self._panel.set_connecting()
        worker = ConnectWorker(self._ctx)
        worker.signals.connected.connect(self._on_connected)
        worker.signals.failed.connect(self._on_connect_failed)
        self._pool.start(worker)

    def _on_disconnect_requested(self) -> None:
        """Disable UI and spin up a DisconnectWorker."""
        self._panel.set_connecting()   # amber while disconnecting
        worker = DisconnectWorker(self._ctx)
        worker.signals.disconnected.connect(self._on_disconnected)
        worker.signals.error.connect(self._on_disconnect_error)
        self._pool.start(worker)

    def _on_connected(self) -> None:
        cfg = self._ctx.config
        label = (
            f"{cfg.connection.ams_net_id} @ {cfg.connection.ip_address}:{cfg.connection.port}"
            if cfg else "PLC"
        )
        self._panel.set_connected(label)
        self.connected.emit()

    def _on_connect_failed(self, error_msg: str) -> None:
        self._panel.set_disconnected()
        self.connect_failed.emit(error_msg)

    def _on_disconnected(self) -> None:
        self._panel.set_disconnected()
        self.disconnected.emit()

    def _on_disconnect_error(self, error_msg: str) -> None:
        # Still treat it as disconnected – the ADS link is broken.
        self._panel.set_disconnected()
        self.disconnected.emit()
