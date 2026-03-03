"""
log_panel.py
------------
:class:`LogPanel` is a :class:`~PyQt6.QtWidgets.QGroupBox` that displays the
application log stream.

It hosts:
* A :class:`~PyQt6.QtWidgets.QTableView` backed by
  :class:`~plc_gui.models.log_table_model.LogTableModel`.
* A **Clear** button that erases all log rows.
* A **level filter** :class:`~PyQt6.QtWidgets.QComboBox` so operators can
  limit display to WARNING and above when needed.
* An **auto-scroll** checkbox that keeps the latest entry visible.

The panel is purely presentational – it owns the Qt model and wires it to
:class:`~plc_gui.utils.qt_log_handler.QtLogHandler` externally (in
``app.py`` or ``AppController``).
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from plc_gui.constants import LOG_MAX_ROWS, LOG_COL_LEVEL, LOG_COL_TIME, LOG_COL_MSG
from plc_gui.models.log_table_model import LogTableModel


# ---------------------------------------------------------------------------
# Proxy model that filters by minimum log level
# ---------------------------------------------------------------------------

class _LevelFilterProxy(QSortFilterProxyModel):
    """Proxy that hides rows whose level is below the configured minimum."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._min_level: int = logging.DEBUG

    def set_min_level(self, level: int) -> None:
        self._min_level = level
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:  # noqa: N802
        model = self.sourceModel()
        if model is None:
            return True
        idx = model.index(source_row, LOG_COL_LEVEL, source_parent)
        record_level = model.data(idx, Qt.ItemDataRole.UserRole)
        # LogTableModel doesn't expose UserRole for level – fall back to text.
        level_name = model.data(idx, Qt.ItemDataRole.DisplayRole) or ""
        level_int = logging.getLevelName(level_name) if isinstance(level_name, str) else logging.DEBUG
        if not isinstance(level_int, int):
            level_int = logging.DEBUG
        return level_int >= self._min_level


# ---------------------------------------------------------------------------
# Panel widget
# ---------------------------------------------------------------------------

class LogPanel(QGroupBox):
    """
    Application log panel.

    Args:
        max_rows: Maximum log rows retained in the model.
        parent:   Optional Qt parent.

    Attributes:
        model: The :class:`~plc_gui.models.log_table_model.LogTableModel`
               that stores log records.  Connect
               :class:`~plc_gui.utils.qt_log_handler.QtLogHandler`.``record_emitted``
               to ``model.append_record``.
    """

    def __init__(self, max_rows: int = LOG_MAX_ROWS, parent: QWidget | None = None) -> None:
        super().__init__("Application Log", parent)

        self.model = LogTableModel(max_rows=max_rows, parent=self)
        self._proxy = _LevelFilterProxy(self)
        self._proxy.setSourceModel(self.model)

        # Toolbar
        self._level_combo = QComboBox()
        self._level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self._level_combo.setCurrentText("DEBUG")
        self._level_combo.setToolTip("Minimum log level to display")
        self._level_combo.currentTextChanged.connect(self._on_level_changed)

        self._auto_scroll_cb = QCheckBox("Auto-scroll")
        self._auto_scroll_cb.setChecked(True)

        self._btn_clear = QPushButton("Clear")
        self._btn_clear.setMaximumWidth(70)
        self._btn_clear.clicked.connect(self.model.clear)

        # Table
        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setWordWrap(False)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(LOG_COL_TIME, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(LOG_COL_LEVEL, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)   # module
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)            # message

        # Auto-scroll: scroll to bottom after each row is appended.
        self.model.rowsInserted.connect(self._auto_scroll)

        self._build_layout()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        toolbar.addWidget(QLabel("Level:"))
        toolbar.addWidget(self._level_combo)
        toolbar.addWidget(self._auto_scroll_cb)
        toolbar.addStretch()
        toolbar.addWidget(self._btn_clear)

        vbox = QVBoxLayout(self)
        vbox.addLayout(toolbar)
        vbox.addWidget(self._table)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_level_changed(self, text: str) -> None:
        level = logging.getLevelName(text)
        if isinstance(level, int):
            self._proxy.set_min_level(level)

    def _auto_scroll(self) -> None:
        if self._auto_scroll_cb.isChecked():
            self._table.scrollToBottom()
