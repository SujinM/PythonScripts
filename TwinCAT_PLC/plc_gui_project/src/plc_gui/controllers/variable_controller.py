"""
variable_controller.py
----------------------
:class:`VariableController` mediates between the
:class:`~plc_gui.views.variable_panel.VariablePanel` and the ADS backend:

* Starts / stops the :class:`~plc_gui.workers.poll_worker.PollWorker`.
* Triggers a one-shot refresh (via thread pool).
* Opens the :class:`~plc_gui.views.write_dialog.WriteDialog` and delegates the
  write to :class:`~services.plc_write_service.PLCWriteService`.
* Handles JSON export of the variable registry.

It owns the :class:`~plc_gui.models.variable_table_model.VariableTableModel`
used by the panel's table view.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from PyQt6.QtCore import QObject, QThreadPool, QRunnable, pyqtSignal, pyqtSlot, QSettings
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from plc_gui.app_context import AppContext
from plc_gui.constants import (
    POLL_INTERVAL_MS, APP_NAME, ORG_NAME,
    SETTING_POLL_ENABLED,
)
from plc_gui.models.variable_table_model import VariableTableModel
from plc_gui.workers.poll_worker import PollWorker

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from plc_gui.views.variable_panel import VariablePanel


# ---------------------------------------------------------------------------
# One-shot read_all QRunnable
# ---------------------------------------------------------------------------

class _ReadAllSignals(QObject):
    done = pyqtSignal(object)   # registry
    error = pyqtSignal(str)


class _ReadAllWorker(QRunnable):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self._ctx = ctx
        self.signals = _ReadAllSignals()
        self.setAutoDelete(True)

    def run(self) -> None:  # noqa: N802
        try:
            self._ctx.read_service.read_all()
            self.signals.done.emit(self._ctx.registry)
        except Exception as exc:  # pylint: disable=broad-except
            self.signals.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class VariableController(QObject):
    """
    Controls the variable panel: polling, one-shot refresh, write, export.

    Args:
        panel:  The variable panel widget.
        ctx:    Shared application context.
        parent: Optional Qt parent.

    Signals:
        status_message: Short status string for the main window status bar.
        error_occurred: Error string for the status bar / message box.
    """

    status_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        panel: "VariablePanel",
        ctx: AppContext,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._panel = panel
        self._ctx = ctx
        self._pool = QThreadPool.globalInstance()
        self._poll_worker: PollWorker | None = None

        # Create and inject the Qt model into the panel.
        self._model = VariableTableModel(self)
        panel.set_model(self._model)

        # Panel toolbar signals → controller slots.
        panel.refresh_requested.connect(self._on_refresh_requested)
        panel.write_requested.connect(self._on_write_requested)
        panel.poll_start_requested.connect(self._on_poll_start)
        panel.poll_stop_requested.connect(self._on_poll_stop)
        panel.export_json_requested.connect(self._on_export_json)

    # ------------------------------------------------------------------
    # Called by AppController on connect / disconnect
    # ------------------------------------------------------------------

    def on_connected(self) -> None:
        """Refresh once immediately and auto-start polling if setting says so."""
        self._on_refresh_requested()
        settings = QSettings(ORG_NAME, APP_NAME)
        if settings.value(SETTING_POLL_ENABLED, True, type=bool):
            self._on_poll_start()

    def on_disconnected(self) -> None:
        """Stop polling and clear the table."""
        self._stop_poll_worker()
        self._model.clear()
        self._panel.set_poll_stopped()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _on_refresh_requested(self) -> None:
        if self._ctx.read_service is None:
            self.error_occurred.emit("Not connected.")
            return
        worker = _ReadAllWorker(self._ctx)
        worker.signals.done.connect(self._model.refresh_rows)
        worker.signals.error.connect(self.error_occurred)
        self._pool.start(worker)

    @pyqtSlot()
    def _on_poll_start(self) -> None:
        if self._poll_worker is not None and self._poll_worker.isRunning():
            return
        if self._ctx.read_service is None:
            self.error_occurred.emit("Not connected.")
            return
        self._poll_worker = PollWorker(self._ctx, POLL_INTERVAL_MS, self)
        self._poll_worker.registry_updated.connect(self._model.refresh_rows)
        self._poll_worker.error_occurred.connect(self.error_occurred)
        self._poll_worker.start()
        self._panel.set_poll_running()
        settings = QSettings(ORG_NAME, APP_NAME)
        settings.setValue(SETTING_POLL_ENABLED, True)

    @pyqtSlot()
    def _on_poll_stop(self) -> None:
        self._stop_poll_worker()
        self._panel.set_poll_stopped()
        settings = QSettings(ORG_NAME, APP_NAME)
        settings.setValue(SETTING_POLL_ENABLED, False)

    @pyqtSlot(int)
    def _on_write_requested(self, row: int) -> None:
        """Open the write dialog for the variable at *row*."""
        from plc_gui.views.write_dialog import WriteDialog

        var_name = self._model.variable_name_at(row)
        if var_name is None:
            self.error_occurred.emit("No variable selected.")
            return

        # Fetch current variable from registry.
        var = self._ctx.registry.get(var_name) if self._ctx.registry else None
        if var is None:
            self.error_occurred.emit(f"Variable '{var_name}' not found in registry.")
            return

        dlg = WriteDialog(
            variable_name=var.name,
            plc_type=var.plc_type,
            current_value=var.current_value,
            parent=self._panel,
        )
        if dlg.exec():
            new_val = dlg.new_value()
            self._do_write(var_name, new_val)

    @pyqtSlot()
    def _on_export_json(self) -> None:
        if self._ctx.registry is None:
            self.error_occurred.emit("Registry not loaded.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self._panel,
            "Export Variables to JSON",
            f"plc_snapshot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)",
        )
        if not file_path:
            return
        try:
            snapshot: dict = {}
            for var in self._ctx.registry:
                snapshot[var.name] = {
                    "type": var.plc_type,
                    "value": var.current_value,
                    "last_updated": (
                        var.last_updated.isoformat() if var.last_updated else None
                    ),
                }
            with open(file_path, "w", encoding="utf-8") as fp:
                json.dump(snapshot, fp, indent=2, default=str)
            self.status_message.emit(f"Exported {len(snapshot)} variables → {os.path.basename(file_path)}")
        except Exception as exc:  # pylint: disable=broad-except
            self.error_occurred.emit(f"Export failed: {exc}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _do_write(self, name: str, value: object) -> None:
        """Write *value* to PLC variable *name* (blocking – off the UI thread)."""
        class _WriteWorker(QRunnable):
            def __init__(self_, n, v, svc, sig_ok, sig_err):  # noqa: N805
                super().__init__()
                self_.n, self_.v, self_.svc = n, v, svc
                self_.sig_ok, self_.sig_err = sig_ok, sig_err
                self_.setAutoDelete(True)

            def run(self_):  # noqa: N805, N802
                try:
                    self_.svc.write_variable(self_.n, self_.v)
                    self_.sig_ok.emit(f"Written {self_.n} = {self_.v!r}")
                except Exception as exc:
                    self_.sig_err.emit(f"Write failed: {exc}")

        worker = _WriteWorker(
            name, value,
            self._ctx.write_service,
            self.status_message,
            self.error_occurred,
        )
        self._pool.start(worker)

    def _stop_poll_worker(self) -> None:
        if self._poll_worker is not None:
            self._poll_worker.stop()
            self._poll_worker.wait(3000)
            self._poll_worker = None
