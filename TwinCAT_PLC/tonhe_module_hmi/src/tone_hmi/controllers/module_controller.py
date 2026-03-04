"""
module_controller.py
─────────────────────
Orchestrates periodic polling of ToneModule PLC variables and updates
all the specialized HMI panels with fresh data.

Also handles:
  • START / STOP / CLEAR FAULT writes to the PLC
  • Setpoint (V/I) write + bUpdateVI pulse
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from tone_hmi.app_context import AppContext
from tone_hmi.constants import (
    VAR_MODULE_STATUS, VAR_MODULE_VOLTAGE, VAR_MODULE_CURRENT,
    VAR_MODULE_FAULTS, VAR_PFC_FAULTS, VAR_MODULE_FAULT,
    VAR_STATUS_RECEIVED, VAR_ACK_RECEIVED,
    VAR_PHASE_A, VAR_PHASE_B, VAR_PHASE_C, VAR_TEMPERATURE,
    VAR_STATUS_BITS, VAR_EXT_FAULTS, VAR_RX_FRAME_COUNT, VAR_LAST_COB_ID,
    VAR_START, VAR_STOP, VAR_CLEAR_FAULT, VAR_MODULE_RUNNING,
    VAR_STATUS_TEXT, VAR_TARGET_VOLTAGE, VAR_TARGET_CURRENT, VAR_UPDATE_VI,
    VAR_MODULE_ADDRESS, VAR_MASTER_ADDRESS, VAR_RETRY_COUNT, VAR_MAX_RETRIES,
)
from tone_hmi.workers.poll_worker import PollWorker

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from tone_hmi.views.module_status_panel import ModuleStatusPanel
    from tone_hmi.views.module_control_panel import ModuleControlPanel
    from tone_hmi.views.setpoint_panel import SetpointPanel
    from tone_hmi.views.phase_info_panel import PhaseInfoPanel
    from tone_hmi.views.fault_panel import FaultPanel
    from tone_hmi.views.graph_panel import GraphPanel

log = logging.getLogger(__name__)


class ModuleController(QObject):
    """
    Drives all module-specific panels from polled PLC data.

    Args:
        status_panel:  ModuleStatusPanel widget.
        control_panel: ModuleControlPanel widget.
        setpoint_panel: SetpointPanel widget.
        phase_panel:   PhaseInfoPanel widget.
        fault_panel:   FaultPanel widget.
        ctx:           Shared AppContext.
        parent:        Qt parent.
    """

    status_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        status_panel: "ModuleStatusPanel",
        control_panel: "ModuleControlPanel",
        setpoint_panel: "SetpointPanel",
        phase_panel: "PhaseInfoPanel",
        fault_panel: "FaultPanel",
        ctx: AppContext,
        graph_panel: "Optional[GraphPanel]" = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._status_panel = status_panel
        self._control_panel = control_panel
        self._setpoint_panel = setpoint_panel
        self._phase_panel = phase_panel
        self._fault_panel = fault_panel
        self._graph_panel = graph_panel
        self._ctx = ctx
        self._poll_worker: PollWorker | None = None

        # Wire control panel buttons
        control_panel.start_requested.connect(self._on_start)
        control_panel.stop_requested.connect(self._on_stop)
        control_panel.clear_fault_requested.connect(self._on_clear_fault)

        # Wire setpoint panel
        setpoint_panel.apply_requested.connect(self._on_apply_setpoint)

    # ── Connection state callbacks ────────────────────────────────────────────

    @pyqtSlot()
    def on_connected(self) -> None:
        self._control_panel.set_connected()
        self._setpoint_panel.set_connected()
        if self._graph_panel:
            self._graph_panel.reset_time_origin()
        self._start_poll()
        # Pre-fill setpoints from PLC
        v_raw = self._ctx.read_variable(VAR_TARGET_VOLTAGE)
        a_raw = self._ctx.read_variable(VAR_TARGET_CURRENT)
        self._setpoint_panel.populate_setpoints(v_raw, a_raw)
        self.status_message.emit("Connected – polling started")

    @pyqtSlot()
    def on_disconnected(self) -> None:
        self._stop_poll()
        self._control_panel.set_disconnected()
        self._setpoint_panel.set_disconnected()
        self.status_message.emit("Disconnected")

    # ── Poll worker lifecycle ─────────────────────────────────────────────────

    def _start_poll(self) -> None:
        if self._poll_worker and self._poll_worker.isRunning():
            return
        self._poll_worker = PollWorker(self._ctx, parent=self)
        self._poll_worker.polled.connect(self._on_polled)
        self._poll_worker.error_occurred.connect(self._on_poll_error)
        self._poll_worker.start()

    def _stop_poll(self) -> None:
        if self._poll_worker:
            self._poll_worker.stop()
            self._poll_worker.wait(2000)
            self._poll_worker = None

    # ── Poll update handler ───────────────────────────────────────────────────

    @pyqtSlot(object)
    def _on_polled(self, ctx: AppContext) -> None:
        r = ctx.read_variable  # shorthand

        # Module status panel
        self._status_panel.update_module_status(r(VAR_MODULE_STATUS))
        self._status_panel.update_voltage(r(VAR_MODULE_VOLTAGE))
        self._status_panel.update_current(r(VAR_MODULE_CURRENT))
        self._status_panel.update_status_text(r(VAR_STATUS_TEXT))
        self._status_panel.update_flags(
            running=bool(r(VAR_MODULE_RUNNING)),
            status_received=bool(r(VAR_STATUS_RECEIVED)),
            ack_received=bool(r(VAR_ACK_RECEIVED)),
            fault=bool(r(VAR_MODULE_FAULT)),
        )

        # Setpoint live readback
        self._setpoint_panel.update_live_voltage(r(VAR_MODULE_VOLTAGE))
        self._setpoint_panel.update_live_current(r(VAR_MODULE_CURRENT))

        # Phase info
        self._phase_panel.update_phases(
            r(VAR_PHASE_A), r(VAR_PHASE_B), r(VAR_PHASE_C)
        )
        self._phase_panel.update_temperature(r(VAR_TEMPERATURE))

        # Fault panel
        self._fault_panel.update_faults(
            faults=r(VAR_MODULE_FAULTS),
            ext_faults=r(VAR_EXT_FAULTS),
            status_bits=r(VAR_STATUS_BITS),
            pfc_faults=r(VAR_PFC_FAULTS),
        )
        self._fault_panel.update_diagnostics(
            rx_count=r(VAR_RX_FRAME_COUNT),
            last_cob_id=r(VAR_LAST_COB_ID),
        )

        # Module address / retry counters
        self._control_panel.update_addresses(
            r(VAR_MODULE_ADDRESS), r(VAR_MASTER_ADDRESS)
        )
        self._control_panel.update_retries(r(VAR_RETRY_COUNT), r(VAR_MAX_RETRIES))

        # Graph panel — voltage and current trend
        if self._graph_panel:
            self._graph_panel.append(r(VAR_MODULE_VOLTAGE), r(VAR_MODULE_CURRENT))

    @pyqtSlot(str)
    def _on_poll_error(self, msg: str) -> None:
        log.warning(msg)
        self.error_occurred.emit(msg)

    # ── Command slots ─────────────────────────────────────────────────────────

    @pyqtSlot()
    def _on_start(self) -> None:
        try:
            self._ctx.write_variable(VAR_START, True)
            log.info("START command sent to PLC")
            self.status_message.emit("START command sent")
        except Exception as exc:
            self.error_occurred.emit(f"Start failed: {exc}")

    @pyqtSlot()
    def _on_stop(self) -> None:
        try:
            self._ctx.write_variable(VAR_STOP, True)
            log.info("STOP command sent to PLC")
            self.status_message.emit("STOP command sent")
        except Exception as exc:
            self.error_occurred.emit(f"Stop failed: {exc}")

    @pyqtSlot()
    def _on_clear_fault(self) -> None:
        try:
            self._ctx.write_variable(VAR_CLEAR_FAULT, True)
            log.info("CLEAR FAULT command sent to PLC")
            self.status_message.emit("Clear Fault command sent")
        except Exception as exc:
            self.error_occurred.emit(f"Clear fault failed: {exc}")

    @pyqtSlot(int, int)
    def _on_apply_setpoint(self, voltage_raw: int, current_raw: int) -> None:
        try:
            self._ctx.write_variable(VAR_TARGET_VOLTAGE, voltage_raw)
            self._ctx.write_variable(VAR_TARGET_CURRENT, current_raw)
            self._ctx.write_variable(VAR_UPDATE_VI, True)
            v_display = voltage_raw / 10
            a_display = current_raw / 100
            log.info(
                "Setpoint written: %.1f V  /  %.2f A  (raw %d / %d)",
                v_display, a_display, voltage_raw, current_raw,
            )
            self.status_message.emit(
                f"Setpoint applied: {v_display:.1f} V  /  {a_display:.2f} A"
            )
        except Exception as exc:
            self.error_occurred.emit(f"Setpoint write failed: {exc}")

    def teardown(self) -> None:
        self._stop_poll()
