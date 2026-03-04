"""
poll_worker.py
──────────────
QThread that periodically reads all registered PLC variables and emits the
updated registry so the GUI can refresh.
"""

from __future__ import annotations

from PyQt6.QtCore import QMutex, QThread, pyqtSignal

from tone_hmi.app_context import AppContext
from tone_hmi.constants import POLL_INTERVAL_MS


class PollWorker(QThread):
    """Background read loop.

    Signals:
        polled:        Emitted after each successful read pass; carries the
                       AppContext so controllers can extract specific values.
        error_occurred: Emitted when a read pass raises; carries the message.
    """

    polled = pyqtSignal(object)          # object → AppContext
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        ctx: AppContext,
        interval_ms: int = POLL_INTERVAL_MS,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._interval_ms = interval_ms
        self._mutex = QMutex()
        self._running = False

    def run(self) -> None:
        self._set_running(True)
        while self._is_running():
            self._read_once()
            self.msleep(self._interval_ms)

    def stop(self) -> None:
        self._set_running(False)

    def _read_once(self) -> None:
        try:
            if self._ctx.read_service:
                self._ctx.read_service.read_all()
                self.polled.emit(self._ctx)
        except Exception as exc:
            self.error_occurred.emit(f"Poll error: {exc}")

    def _set_running(self, value: bool) -> None:
        self._mutex.lock()
        try:
            self._running = value
        finally:
            self._mutex.unlock()

    def _is_running(self) -> bool:
        self._mutex.lock()
        try:
            return self._running
        finally:
            self._mutex.unlock()
