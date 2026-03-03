"""
connect_worker.py
-----------------
:class:`ConnectWorker` is a :class:`~PyQt6.QtCore.QRunnable` that opens the
ADS connection on a thread-pool thread so the GUI remains responsive during
the (potentially slow) TCP/ADS handshake.

Signals are emitted via a companion :class:`ConnectSignals` object (Qt
requires a separate :class:`QObject` to host signals on a
:class:`QRunnable`).

Usage::

    worker = ConnectWorker(ctx)
    worker.signals.connected.connect(on_connected)
    worker.signals.failed.connect(on_failed)
    QThreadPool.globalInstance().start(worker)
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot

from plc_gui.app_context import AppContext


class ConnectSignals(QObject):
    """Qt signals carrier for :class:`ConnectWorker`."""

    #: Emitted when the connection is established successfully.
    connected = pyqtSignal()

    #: Emitted when the connection attempt fails; carries the error message.
    failed = pyqtSignal(str)


class ConnectWorker(QRunnable):
    """
    Opens the ADS connection in a thread-pool thread.

    Args:
        ctx: The :class:`~plc_gui.app_context.AppContext` whose
             ``connection_manager`` will be opened.
    """

    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self._ctx = ctx
        self.signals = ConnectSignals()
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self) -> None:  # noqa: N802 (Qt override)
        """Execute the blocking ADS open call off the GUI thread."""
        try:
            self._ctx.connection_manager.open()
            self.signals.connected.emit()
        except Exception as exc:  # pylint: disable=broad-except
            self.signals.failed.emit(str(exc))
