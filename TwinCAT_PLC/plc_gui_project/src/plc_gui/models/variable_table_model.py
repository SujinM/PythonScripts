"""
variable_table_model.py
-----------------------
:class:`VariableTableModel` is a :class:`~PyQt6.QtCore.QAbstractTableModel`
that presents the live PLC variable registry as a tabular view with four
columns: **Variable Name**, **Type**, **Value**, **Last Updated**.

The model must be refreshed explicitly (or periodically) by a controller; it
does **not** own a polling timer.  To push fresh data from a background worker
use :meth:`refresh_rows`.

Column layout (see also :mod:`plc_gui.constants`)::

    0  VAR_COL_NAME    – full symbolic name  (MAIN.nSpeed)
    1  VAR_COL_TYPE    – PLC type string     (INT)
    2  VAR_COL_VALUE   – current value       (1500)
    3  VAR_COL_UPDATED – ISO timestamp       (2026-03-03 12:34:56)

Thread safety
~~~~~~~~~~~~~
Qt models must be accessed from the GUI thread only.  Workers call
:meth:`refresh_rows` via a signal / slot connection which Qt queues on the
GUI thread automatically when sender and receiver live in different threads.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

from PyQt6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QFont

from plc_gui.constants import (
    VAR_COLUMNS,
    VAR_COL_NAME,
    VAR_COL_TYPE,
    VAR_COL_VALUE,
    VAR_COL_UPDATED,
)

if TYPE_CHECKING:
    from models.variable_registry import VariableRegistry  # ADS backend


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _fmt_datetime(dt: Optional[datetime]) -> str:
    """Format a UTC datetime for display, or return '–' if None."""
    if dt is None:
        return "–"
    return dt.strftime("%H:%M:%S.%f")[:-3]   # HH:MM:SS.mmm


# ---------------------------------------------------------------------------
# Row snapshot dataclass (avoids holding locks during Qt model calls)
# ---------------------------------------------------------------------------

class _VarRow:
    """Immutable snapshot of a single PLCVariable for one table row."""
    __slots__ = ("name", "plc_type", "value", "updated")

    def __init__(
        self,
        name: str,
        plc_type: str,
        value: Any,
        updated: Optional[datetime],
    ) -> None:
        self.name = name
        self.plc_type = plc_type
        self.value = value
        self.updated = updated


# ---------------------------------------------------------------------------
# Qt Model
# ---------------------------------------------------------------------------

class VariableTableModel(QAbstractTableModel):
    """
    Read-only Qt table model for the PLC variable registry.

    Args:
        parent: Optional Qt parent object.

    Signals:
        data_refreshed: Emitted after :meth:`refresh_rows` updates the model.
    """

    data_refreshed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[_VarRow] = []

    # ------------------------------------------------------------------
    # QAbstractTableModel interface
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(VAR_COLUMNS)

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return VAR_COLUMNS[section] if 0 <= section < len(VAR_COLUMNS) else None
            return str(section + 1)
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
            if col == VAR_COL_NAME:
                return row.name
            if col == VAR_COL_TYPE:
                return row.plc_type
            if col == VAR_COL_VALUE:
                return str(row.value) if row.value is not None else "–"
            if col == VAR_COL_UPDATED:
                return _fmt_datetime(row.updated)

        if role == Qt.ItemDataRole.ForegroundRole:
            if col == VAR_COL_VALUE and row.value is None:
                return QColor("#888888")
            if col == VAR_COL_TYPE:
                return QColor("#5dade2")   # blue accent for type column

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (VAR_COL_VALUE, VAR_COL_UPDATED):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        if role == Qt.ItemDataRole.UserRole:
            # Return the full row snapshot for custom delegates / export.
            return row

        return None

    # ------------------------------------------------------------------
    # Public helpers called by controllers / workers
    # ------------------------------------------------------------------

    def refresh_rows(self, registry: "VariableRegistry") -> None:
        """
        Replace all rows with a fresh snapshot from *registry*.

        This method is **GUI-thread only** – connect it via a queued signal
        from any background worker.

        Args:
            registry: Live :class:`~models.variable_registry.VariableRegistry`.
        """
        snapshots: list[_VarRow] = []
        for var in registry:
            snapshots.append(
                _VarRow(
                    name=var.name,
                    plc_type=var.plc_type,
                    value=var.current_value,
                    updated=var.last_updated,
                )
            )

        self.beginResetModel()
        self._rows = snapshots
        self.endResetModel()
        self.data_refreshed.emit()

    def variable_name_at(self, row: int) -> Optional[str]:
        """Return the symbolic variable name for *row*, or ``None``."""
        if 0 <= row < len(self._rows):
            return self._rows[row].name
        return None

    def clear(self) -> None:
        """Remove all rows (e.g. on disconnect)."""
        self.beginResetModel()
        self._rows.clear()
        self.endResetModel()
