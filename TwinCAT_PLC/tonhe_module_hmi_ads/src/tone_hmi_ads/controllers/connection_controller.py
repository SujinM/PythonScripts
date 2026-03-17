"""
connection_controller.py
─────────────────────────
Wires the ConnectionPanel buttons to ConnectWorker / DisconnectWorker.

On successful connection the worker returns a ``NotificationBridge``
which this controller passes to the ModuleController via the ``connected``
signal so it can start listening for variable-change events.
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import QObject, QThreadPool, pyqtSignal

from tone_hmi_ads.app_context import AppContext
from tone_hmi_ads.workers.connect_worker import ConnectWorker
from tone_hmi_ads.workers.disconnect_worker import DisconnectWorker
from tone_hmi_ads.workers.notification_bridge import NotificationBridge

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tone_hmi_ads.views.connection_panel import ConnectionPanel

log = logging.getLogger(__name__)


class ConnectionController(QObject):
    # carries the NotificationBridge so ModuleController can wire it up
    connected = pyqtSignal(object)
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

    def _on_connected(self, bridge: NotificationBridge) -> None:
        cfg = self._ctx.config
        if cfg:
            label = f"{cfg.connection.ams_net_id} @ {cfg.connection.ip_address}"
            n_channels = len(self._ctx.notif_managers)
            n_vars = sum(
                len(nm.active_subscriptions) for nm in self._ctx.notif_managers
            )
            log.info(
                "Connected – %d notification channel(s), %d subscriptions",
                n_channels,
                n_vars,
            )
        else:
            label = "PLC"
        self._panel.set_connected(label)
        if cfg:
            self._panel.populate_from_config(cfg)
        self.connected.emit(bridge)

    def _on_failed(self, msg: str) -> None:
        self._panel.set_disconnected()
        self.connect_failed.emit(msg)

    def _on_disconnected(self) -> None:
        self._panel.set_disconnected()
        self.disconnected.emit()

    def _on_disconnect_error(self, msg: str) -> None:
        log.warning("Disconnect error: %s", msg)
        self._panel.set_disconnected()
        self.disconnected.emit()
