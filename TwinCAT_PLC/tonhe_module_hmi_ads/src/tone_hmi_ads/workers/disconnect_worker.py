"""
disconnect_worker.py
────────────────────
QRunnable that unsubscribes all ADS notifications and closes all connections.
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from tone_hmi_ads.app_context import AppContext


class _Signals(QObject):
    disconnected = pyqtSignal()
    error = pyqtSignal(str)


class DisconnectWorker(QRunnable):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.signals = _Signals()
        self._ctx = ctx
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            self._ctx.teardown()
            self.signals.disconnected.emit()
        except Exception as exc:
            self.signals.error.emit(str(exc))
