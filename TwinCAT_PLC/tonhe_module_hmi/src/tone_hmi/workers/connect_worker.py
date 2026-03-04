"""
connect_worker.py
─────────────────
QRunnable that opens the ADS connection in a thread-pool thread and fires
Qt signals back to the GUI thread.
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from tone_hmi.app_context import AppContext


class _Signals(QObject):
    connected = pyqtSignal()
    failed = pyqtSignal(str)


class ConnectWorker(QRunnable):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.signals = _Signals()
        self._ctx = ctx
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            self._ctx.connection_manager.open()
            self.signals.connected.emit()
        except Exception as exc:
            self.signals.failed.emit(str(exc))
