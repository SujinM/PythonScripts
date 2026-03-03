"""
variable_panel.py
-----------------
:class:`VariablePanel` is a :class:`~PyQt6.QtWidgets.QGroupBox` that hosts:

* A toolbar with **Refresh**, **Write**, **Start Poll**, **Stop Poll**, and
  **Export JSON** actions.
* A :class:`~PyQt6.QtWidgets.QTableView` backed by
  :class:`~plc_gui.models.variable_table_model.VariableTableModel`.
* A :class:`~PyQt6.QtWidgets.QLineEdit` filter that hides rows whose variable
  name does not contain the search text (client-side proxy filter).

The panel emits signals and exposes :meth:`set_model`.  All logic lives in
:class:`~plc_gui.controllers.variable_controller.VariableController`.
"""

from __future__ import annotations

from PyQt6.QtCore import (
    QSortFilterProxyModel,
    Qt,
    pyqtSignal,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from plc_gui.constants import VAR_COL_NAME
from plc_gui.models.variable_table_model import VariableTableModel


class VariablePanel(QGroupBox):
    """
    PLC variable monitoring and control panel.

    Signals:
        refresh_requested:    User clicked **Refresh**.
        write_requested:      User clicked **Write**; carries the selected row index.
        poll_start_requested: User clicked **Start Poll**.
        poll_stop_requested:  User clicked **Stop Poll**.
        export_json_requested: User clicked **Export JSON**.
    """

    refresh_requested = pyqtSignal()
    write_requested = pyqtSignal(int)          # row index in the SOURCE model
    poll_start_requested = pyqtSignal()
    poll_stop_requested = pyqtSignal()
    export_json_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("PLC Variables", parent)

        # Toolbar buttons
        self._btn_refresh = QPushButton("⟳  Refresh")
        self._btn_refresh.setToolTip("Read all variables once immediately")

        self._btn_write = QPushButton("✎  Write")
        self._btn_write.setToolTip("Write a value to the selected variable")
        self._btn_write.setEnabled(False)

        self._btn_start_poll = QPushButton("▶  Start Poll")
        self._btn_start_poll.setToolTip("Start periodic automatic polling")

        self._btn_stop_poll = QPushButton("■  Stop Poll")
        self._btn_stop_poll.setToolTip("Stop periodic polling")
        self._btn_stop_poll.setEnabled(False)

        self._btn_export = QPushButton("⬇  Export JSON")
        self._btn_export.setToolTip("Export current variable values to JSON")

        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Filter variables…")
        self._filter_edit.setMaximumWidth(260)
        self._filter_edit.setClearButtonEnabled(True)

        # Table
        self._table = QTableView()
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)

        # Proxy model for filtering (populated in set_model)
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(VAR_COL_NAME)
        self._table.setModel(self._proxy)

        self._build_layout()
        self._connect_signals()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        for btn in (
            self._btn_refresh,
            self._btn_write,
            self._btn_start_poll,
            self._btn_stop_poll,
            self._btn_export,
        ):
            toolbar.addWidget(btn)
        toolbar.addStretch()
        toolbar.addWidget(QLabel("Search:"))
        toolbar.addWidget(self._filter_edit)

        vbox = QVBoxLayout(self)
        vbox.addLayout(toolbar)
        vbox.addWidget(self._table)

    def _connect_signals(self) -> None:
        self._btn_refresh.clicked.connect(self.refresh_requested)
        self._btn_start_poll.clicked.connect(self.poll_start_requested)
        self._btn_stop_poll.clicked.connect(self.poll_stop_requested)
        self._btn_export.clicked.connect(self.export_json_requested)
        self._btn_write.clicked.connect(self._emit_write_requested)
        self._filter_edit.textChanged.connect(self._proxy.setFilterFixedString)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # Public API (called by VariableController)
    # ------------------------------------------------------------------

    def set_model(self, model: VariableTableModel) -> None:
        """Inject the Qt data model and resize columns."""
        self._source_model = model
        self._proxy.setSourceModel(model)
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, model.columnCount()):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

    def set_poll_running(self) -> None:
        self._btn_start_poll.setEnabled(False)
        self._btn_stop_poll.setEnabled(True)

    def set_poll_stopped(self) -> None:
        self._btn_start_poll.setEnabled(True)
        self._btn_stop_poll.setEnabled(False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_selection_changed(self) -> None:
        self._btn_write.setEnabled(bool(self._table.selectedIndexes()))

    def _emit_write_requested(self) -> None:
        indexes = self._table.selectedIndexes()
        if not indexes:
            return
        proxy_row = indexes[0].row()
        source_row = self._proxy.mapToSource(self._proxy.index(proxy_row, 0)).row()
        self.write_requested.emit(source_row)
