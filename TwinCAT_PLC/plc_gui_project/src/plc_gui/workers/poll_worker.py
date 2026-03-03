"""
poll_worker.py
--------------
:class:`PollWorker` is a :class:`~PyQt6.QtCore.QThread` that calls
``read_all()`` on the ADS read service at a configurable interval and emits a
signal with the updated :class:`~models.variable_registry.VariableRegistry`
so that the Qt model can be refreshed on the GUI thread.

Design
~~~~~~
* Uses :meth:`~PyQt6.QtCore.QThread.msleep` (non-blocking sleep) so the
  thread responds promptly to :meth:`stop`.
* A single ``QMutex``-guarded ``_running`` flag ensures a clean shutdown with
  no lingering threads.
* The signal carries the *registry* reference (not a copy); the Qt model must
  snapshot it quickly on the GUI thread.

Usage::

    worker = PollWorker(ctx, interval_ms=500)
    worker.registry_updated.connect(var_model.refresh_rows)
    worker.error_occurred.connect(status_bar.showMessage)
    worker.start()
    ...
    worker.stop()
    worker.wait()
"""

from __future__ import annotations

from PyQt6.QtCore import QMutex, QThread, pyqtSignal

from plc_gui.app_context import AppContext
from plc_gui.constants import POLL_INTERVAL_MS


class PollWorker(QThread):
    """
    Background thread that periodically reads all registered PLC variables.

    Signals:
        registry_updated: Emitted after every successful ``read_all`` pass;
                          carries the live
                          :class:`~models.variable_registry.VariableRegistry`.
        error_occurred:   Emitted when a read pass raises an exception; carries
                          the error message string.
    """

    registry_updated = pyqtSignal(object)   # object → VariableRegistry
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

    # ------------------------------------------------------------------
    # QThread interface
    # ------------------------------------------------------------------

    def run(self) -> None:  # noqa: N802 (Qt override)
        """Thread entry point: read loop until :meth:`stop` is called."""
        self._set_running(True)
        while self._is_running():
            self._poll_once()
            self.msleep(self._interval_ms)

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def stop(self) -> None:
        """Signal the worker loop to exit on the next iteration."""
        self._set_running(False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _poll_once(self) -> None:
        """Perform one read_all pass and emit the result."""
        try:
            if self._ctx.read_service is None:
                return
            self._ctx.read_service.read_all()
            self.registry_updated.emit(self._ctx.registry)
        except Exception as exc:  # pylint: disable=broad-except
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
