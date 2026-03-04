"""
disconnect_worker.py
────────────────────
QRunnable that closes the ADS connection in a thread-pool thread.
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from tone_hmi.app_context import AppContext


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
            self._ctx.connection_manager.close()
            self.signals.disconnected.emit()
        except Exception as exc:
            self.signals.error.emit(str(exc))
