"""
qt_log_handler.py
-----------------
Bridges Python's :mod:`logging` framework with PyQt6 signals so that any log
message emitted anywhere in the application (including the ADS backend) is
delivered to the :class:`~plc_gui.models.log_table_model.LogTableModel` for
display in the GUI log panel.

Architecture
~~~~~~~~~~~~
:class:`QtLogHandler` is a standard :class:`logging.Handler`.  When a record
is emitted it fires :attr:`QtLogHandler.record_emitted` (a ``pyqtSignal``).
Because PyQt6 signal–slot connections across threads are automatically
*queued*, the record is delivered on the GUI thread even when the originating
log call comes from a background worker thread.

Install once in :func:`~plc_gui.app_context.AppContext.load` (or in
``app.py``) and connect the signal to
:meth:`~plc_gui.models.log_table_model.LogTableModel.append_record`::

    handler = QtLogHandler()
    logging.getLogger().addHandler(handler)
    handler.record_emitted.connect(log_model.append_record)
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import QObject, pyqtSignal


class QtLogHandler(logging.Handler, QObject):
    """
    Python logging handler that emits a Qt signal for each log record.

    Because it inherits from both :class:`logging.Handler` and
    :class:`~PyQt6.QtCore.QObject`, the signal is properly subject to Qt's
    event-loop queuing when the connection is cross-thread.

    Signals:
        record_emitted: Carries the :class:`logging.LogRecord` to any slot.
    """

    record_emitted = pyqtSignal(logging.LogRecord)

    def __init__(self, level: int = logging.DEBUG, parent: QObject | None = None) -> None:
        logging.Handler.__init__(self, level)
        QObject.__init__(self, parent)

    # logging.Handler interface
    def emit(self, record: logging.LogRecord) -> None:   # noqa: N802 (stdlib name)
        """Fire the Qt signal with the log *record*."""
        try:
            self.record_emitted.emit(record)
        except Exception:
            self.handleError(record)
