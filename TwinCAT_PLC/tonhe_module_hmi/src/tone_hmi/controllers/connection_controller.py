"""
connection_controller.py
─────────────────────────
Wires the ConnectionPanel buttons to the background Connect/Disconnect workers.
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, QThreadPool, pyqtSignal

from tone_hmi.app_context import AppContext
from tone_hmi.workers.connect_worker import ConnectWorker
from tone_hmi.workers.disconnect_worker import DisconnectWorker

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tone_hmi.views.connection_panel import ConnectionPanel


class ConnectionController(QObject):
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

        panel.connect_requested.connect(self._on_connect_requested)
        panel.disconnect_requested.connect(self._on_disconnect_requested)

    def _on_connect_requested(self) -> None:
        if not self._ctx.is_loaded:
            self.connect_failed.emit("No configuration loaded. Open a config file first.")
            return
        self._panel.set_connecting()
        worker = ConnectWorker(self._ctx)
        worker.signals.connected.connect(self._on_connected)
        worker.signals.failed.connect(self._on_failed)
        self._pool.start(worker)

    def _on_disconnect_requested(self) -> None:
        self._panel.set_connecting()
        worker = DisconnectWorker(self._ctx)
        worker.signals.disconnected.connect(self._on_disconnected)
        worker.signals.error.connect(self._on_disconnect_error)
        self._pool.start(worker)

    def _on_connected(self) -> None:
        cfg = self._ctx.config
        if cfg:
            label = f"{cfg.connection.ams_net_id} @ {cfg.connection.ip_address}"
        else:
            label = "PLC"
        self._panel.set_connected(label)
        # Populate config fields
        if cfg:
            self._panel.populate_from_config(cfg)
        self.connected.emit()

    def _on_failed(self, msg: str) -> None:
        self._panel.set_disconnected()
        self.connect_failed.emit(msg)

    def _on_disconnected(self) -> None:
        self._panel.set_disconnected()
        self.disconnected.emit()

    def _on_disconnect_error(self, msg: str) -> None:
        self._panel.set_disconnected()
        self.disconnected.emit()
