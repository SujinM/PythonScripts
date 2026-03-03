"""
log_table_model.py
------------------
:class:`LogTableModel` is a :class:`~PyQt6.QtCore.QAbstractTableModel` that
stores recent Python :class:`logging.LogRecord` data for display in the
log panel.

Column layout (see also :mod:`plc_gui.constants`)::

    0  LOG_COL_TIME    – HH:MM:SS.mmm
    1  LOG_COL_LEVEL   – DEBUG / INFO / WARNING / ERROR / CRITICAL
    2  LOG_COL_MODULE  – logger name (module)
    3  LOG_COL_MSG     – formatted log message

The model keeps at most ``LOG_MAX_ROWS`` rows.  When the limit is reached the
oldest row is silently discarded.

Thread safety
~~~~~~~~~~~~~
The :mod:`~plc_gui.utils.qt_log_handler` appends rows via the
``append_record`` slot, which Qt delivers on the GUI thread through an
auto-connection so the model is always mutated on the correct thread.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from PyQt6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    pyqtSlot,
)
from PyQt6.QtGui import QColor, QFont

from plc_gui.constants import (
    LOG_COLUMNS, LOG_MAX_ROWS,
    LOG_COL_TIME, LOG_COL_LEVEL, LOG_COL_MODULE, LOG_COL_MSG,
)

# ---------------------------------------------------------------------------
# Level → display colour mapping
# ---------------------------------------------------------------------------
_LEVEL_COLOURS: dict[int, str] = {
    logging.DEBUG:    "#888888",
    logging.INFO:     "#ecf0f1",
    logging.WARNING:  "#f39c12",
    logging.ERROR:    "#e74c3c",
    logging.CRITICAL: "#ff00ff",
}


@dataclass(slots=True)
class _LogRow:
    """Lightweight snapshot of a single log record for display."""
    time_str: str
    level: int
    level_name: str
    module: str
    message: str


class LogTableModel(QAbstractTableModel):
    """
    Append-only Qt table model for log records.

    Args:
        max_rows: Maximum number of rows retained before oldest are dropped.
        parent:   Optional Qt parent.
    """

    def __init__(self, max_rows: int = LOG_MAX_ROWS, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[_LogRow] = []
        self._max_rows = max_rows

    # ------------------------------------------------------------------
    # QAbstractTableModel interface
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(LOG_COLUMNS)

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return LOG_COLUMNS[section] if 0 <= section < len(LOG_COLUMNS) else None
            return None
        if role == Qt.ItemDataRole.FontRole and orientation == Qt.Orientation.Horizontal:
            f = QFont()
            f.setBold(True)
            return f
        return None

    def data(  # noqa: N802
        self,
        index: QModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._rows)):
            return None

        row = self._rows[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == LOG_COL_TIME:
                return row.time_str
            if col == LOG_COL_LEVEL:
                return row.level_name
            if col == LOG_COL_MODULE:
                return row.module
            if col == LOG_COL_MSG:
                return row.message

        if role == Qt.ItemDataRole.ForegroundRole:
            colour = _LEVEL_COLOURS.get(row.level, "#ecf0f1")
            return QColor(colour)

        if role == Qt.ItemDataRole.FontRole and col == LOG_COL_LEVEL:
            f = QFont()
            f.setBold(True)
            return f

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (LOG_COL_TIME, LOG_COL_LEVEL):
                return Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @pyqtSlot(logging.LogRecord)
    def append_record(self, record: logging.LogRecord) -> None:
        """
        Append a Python :class:`logging.LogRecord` as a new row.

        Called from :class:`~plc_gui.utils.qt_log_handler.QtLogHandler` via a
        queued signal so it is always executed on the GUI thread.

        Args:
            record: The log record emitted by any Python logger.
        """
        # Format timestamp
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
        log_row = _LogRow(
            time_str=ts,
            level=record.levelno,
            level_name=record.levelname,
            module=record.name,
            message=record.getMessage(),
        )

        if len(self._rows) >= self._max_rows:
            # Drop oldest row without a full model reset.
            self.beginRemoveRows(QModelIndex(), 0, 0)
            self._rows.pop(0)
            self.endRemoveRows()

        dest_row = len(self._rows)
        self.beginInsertRows(QModelIndex(), dest_row, dest_row)
        self._rows.append(log_row)
        self.endInsertRows()

    def clear(self) -> None:
        """Remove all log rows."""
        self.beginResetModel()
        self._rows.clear()
        self.endResetModel()
