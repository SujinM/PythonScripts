"""
connect_worker.py
─────────────────
QRunnable that opens the ADS connection, registers change hooks, and sets up
ADS notification subscriptions in a thread-pool thread.

Steps performed
~~~~~~~~~~~~~~~
1. Open the primary ADS connection (ConnectionManager.open).
2. Register NotificationBridge change hooks on all variables.
3. Call AppContext.setup_notifications() which:
   a. Creates a NotificationManager on the primary channel.
   b. Opens extra channels if the variable count exceeds 499.
   c. Subscribes every variable to an ADS device notification.
4. Emit ``connected`` on success or ``failed`` with the error message.
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from tone_hmi_ads.app_context import AppContext
from tone_hmi_ads.workers.notification_bridge import NotificationBridge


class _Signals(QObject):
    connected = pyqtSignal(object)   # carries the NotificationBridge
    failed = pyqtSignal(str)


class ConnectWorker(QRunnable):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.signals = _Signals()
        self._ctx = ctx
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            # Step 1 – open primary connection
            self._ctx.connection_manager.open()

            # Step 2 – register change hooks (before subscribing notifications
            #           so the hooks are in place when the first callback fires)
            bridge = NotificationBridge(self._ctx)
            bridge.register_all_hooks()

            # For mock mode: inject the registry so the mock can fire hooks
            if hasattr(self._ctx.connection_manager, "set_registry"):
                self._ctx.connection_manager.set_registry(self._ctx.registry)

            # Step 3 – subscribe ADS notifications (across channels if needed)
            self._ctx.setup_notifications()

            self.signals.connected.emit(bridge)

        except Exception as exc:
            self.signals.failed.emit(str(exc))
