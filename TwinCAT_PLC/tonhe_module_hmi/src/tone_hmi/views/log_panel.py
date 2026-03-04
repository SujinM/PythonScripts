"""
log_panel.py
─────────────
Scrollable log panel backed by LogTableModel.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from tone_hmi.models.log_table_model import LogTableModel
from tone_hmi.constants import LOG_COL_TIME, LOG_COL_LEVEL


class LogPanel(QGroupBox):
    """Application log viewer."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Application Log", parent)

        self._model = LogTableModel(self)

        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(False)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(LOG_COL_TIME, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(LOG_COL_LEVEL, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self._btn_clear = QPushButton("Clear")
        self._btn_clear.setMaximumWidth(80)
        self._btn_clear.clicked.connect(self._model.clear)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        toolbar.addWidget(self._btn_clear)

        vbox = QVBoxLayout(self)
        vbox.addLayout(toolbar)
        vbox.addWidget(self._table)

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def model(self) -> LogTableModel:
        return self._model

    def scroll_to_bottom(self) -> None:
        self._table.scrollToBottom()
