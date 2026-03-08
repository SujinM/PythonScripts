"""
log_table_model.py
──────────────────
Qt data model that backs the log panel table.  Log records are appended on
the GUI thread (via a queued Qt signal) and the oldest rows are pruned once
LOG_MAX_ROWS is exceeded.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt6.QtGui import QColor

from tone_hmi.constants import LOG_COLUMNS, LOG_MAX_ROWS

# Colour map for log-level badges
_LEVEL_COLORS: dict[int, QColor] = {
    logging.DEBUG:    QColor("#7f8c8d"),
    logging.INFO:     QColor("#2980b9"),
    logging.WARNING:  QColor("#e67e22"),
    logging.ERROR:    QColor("#e74c3c"),
    logging.CRITICAL: QColor("#8e44ad"),
}


class LogTableModel(QAbstractTableModel):
    """Stores :class:`logging.LogRecord` rows for the log panel."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[tuple[str, str, str, str]] = []

    # ── Qt overrides ──────────────────────────────────────────────────────────

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(LOG_COLUMNS)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return LOG_COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return row[col]
        if role == Qt.ItemDataRole.ForegroundRole and col == 1:
            level = getattr(logging, row[1], logging.DEBUG)
            return _LEVEL_COLORS.get(level, _LEVEL_COLORS[logging.DEBUG])
        return None

    # ── Public API ────────────────────────────────────────────────────────────

    def append_record(self, record: logging.LogRecord) -> None:
        """Append a :class:`logging.LogRecord` and prune oldest if needed."""
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
        row = (ts, record.levelname, record.name, record.getMessage())

        first_row = len(self._rows)
        self.beginInsertRows(QModelIndex(), first_row, first_row)
        self._rows.append(row)
        self.endInsertRows()

        if len(self._rows) > LOG_MAX_ROWS:
            self.beginRemoveRows(QModelIndex(), 0, 0)
            self._rows.pop(0)
            self.endRemoveRows()

    def clear(self) -> None:
        self.beginResetModel()
        self._rows.clear()
        self.endResetModel()
