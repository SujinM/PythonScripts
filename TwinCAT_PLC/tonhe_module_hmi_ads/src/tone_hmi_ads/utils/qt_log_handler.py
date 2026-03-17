"""
qt_log_handler.py
─────────────────
Bridges Python logging to a PyQt6 signal so all log output is delivered to
the GUI log panel on the Qt main thread.
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import QObject, pyqtSignal


class QtLogHandler(logging.Handler, QObject):
    """Logging handler that re-emits records as a Qt signal."""

    record_emitted = pyqtSignal(logging.LogRecord)

    def __init__(self, level: int = logging.DEBUG, parent: QObject | None = None) -> None:
        logging.Handler.__init__(self, level)
        QObject.__init__(self, parent)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.record_emitted.emit(record)
        except Exception:
            self.handleError(record)
