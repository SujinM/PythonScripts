"""
disconnect_worker.py
--------------------
:class:`DisconnectWorker` closes the ADS connection on a thread-pool thread
so the GUI does not freeze during the ADS teardown sequence.

Usage::

    worker = DisconnectWorker(ctx)
    worker.signals.disconnected.connect(on_disconnected)
    QThreadPool.globalInstance().start(worker)
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot

from plc_gui.app_context import AppContext


class DisconnectSignals(QObject):
    """Qt signals carrier for :class:`DisconnectWorker`."""

    #: Emitted after the connection is closed (even if an error occurred).
    disconnected = pyqtSignal()

    #: Emitted if an unexpected exception occurs during teardown.
    error = pyqtSignal(str)


class DisconnectWorker(QRunnable):
    """
    Closes the ADS connection in a thread-pool thread.

    Args:
        ctx: The :class:`~plc_gui.app_context.AppContext` whose
             ``connection_manager`` will be closed.
    """

    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self._ctx = ctx
        self.signals = DisconnectSignals()
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self) -> None:  # noqa: N802 (Qt override)
        """Execute the blocking ADS close call off the GUI thread."""
        try:
            self._ctx.connection_manager.close()
        except Exception as exc:  # pylint: disable=broad-except
            self.signals.error.emit(str(exc))
        finally:
            self.signals.disconnected.emit()
