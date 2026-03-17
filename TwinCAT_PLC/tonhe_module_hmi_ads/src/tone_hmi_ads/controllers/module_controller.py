"""
module_controller.py
─────────────────────
Orchestrates ADS notification-driven updates for all TONHE module panels.

Key difference from the polling edition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
There is **no** PollWorker.  Instead a :class:`NotificationBridge` delivers
``variable_changed(name)`` signals to :meth:`_on_variable_changed` whenever
a PLCVariable value is updated by the ADS dispatcher thread.

The method dispatches to the correct panel based on *name*, so only the
relevant widget is refreshed — not the entire panel tree on every cycle.

Write operations (START / STOP / CLEAR FAULT / setpoints) are unchanged;
they still use :meth:`AppContext.write_variable`.
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from tone_hmi_ads.app_context import AppContext
from tone_hmi_ads.constants import (
    VAR_MODULE_STATUS, VAR_MODULE_VOLTAGE, VAR_MODULE_CURRENT,
    VAR_MODULE_FAULTS, VAR_PFC_FAULTS, VAR_MODULE_FAULT,
    VAR_STATUS_RECEIVED, VAR_ACK_RECEIVED,
    VAR_PHASE_A, VAR_PHASE_B, VAR_PHASE_C, VAR_TEMPERATURE,
    VAR_STATUS_BITS, VAR_EXT_FAULTS, VAR_RX_FRAME_COUNT, VAR_LAST_COB_ID,
    VAR_START, VAR_STOP, VAR_CLEAR_FAULT, VAR_MODULE_RUNNING,
    VAR_STATUS_TEXT, VAR_TARGET_VOLTAGE, VAR_TARGET_CURRENT, VAR_UPDATE_VI,
    VAR_MODULE_ADDRESS, VAR_MASTER_ADDRESS, VAR_RETRY_COUNT, VAR_MAX_RETRIES,
    VAR_ENABLE_RAMP, VAR_RAMP_STEP, VAR_RAMP_TIME_S,
    VAR_RAMP_CURR_VOLT, VAR_RAMP_COMPLETE,
)
from tone_hmi_ads.workers.notification_bridge import NotificationBridge

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from tone_hmi_ads.views.module_status_panel import ModuleStatusPanel
    from tone_hmi_ads.views.module_control_panel import ModuleControlPanel
    from tone_hmi_ads.views.setpoint_panel import SetpointPanel
    from tone_hmi_ads.views.phase_info_panel import PhaseInfoPanel
    from tone_hmi_ads.views.fault_panel import FaultPanel
    from tone_hmi_ads.views.graph_panel import GraphPanel

log = logging.getLogger(__name__)

# Variables that affect the status panel
_STATUS_VARS = frozenset({
    VAR_MODULE_STATUS, VAR_MODULE_VOLTAGE, VAR_MODULE_CURRENT,
    VAR_STATUS_TEXT, VAR_MODULE_RUNNING, VAR_STATUS_RECEIVED,
    VAR_ACK_RECEIVED, VAR_MODULE_FAULT,
})
# Variables that affect the setpoint panel readback
_SETPOINT_VARS = frozenset({
    VAR_MODULE_VOLTAGE, VAR_MODULE_CURRENT, VAR_RAMP_CURR_VOLT,
    VAR_TARGET_VOLTAGE, VAR_TARGET_CURRENT,
    VAR_ENABLE_RAMP, VAR_RAMP_STEP, VAR_RAMP_TIME_S,
})
# Variables that affect the phase panel
_PHASE_VARS = frozenset({VAR_PHASE_A, VAR_PHASE_B, VAR_PHASE_C, VAR_TEMPERATURE})
# Variables that affect the fault panel
_FAULT_VARS = frozenset({
    VAR_MODULE_FAULTS, VAR_EXT_FAULTS, VAR_STATUS_BITS,
    VAR_PFC_FAULTS, VAR_RX_FRAME_COUNT, VAR_LAST_COB_ID,
})
# Variables that affect the control panel
_CONTROL_VARS = frozenset({
    VAR_MODULE_ADDRESS, VAR_MASTER_ADDRESS, VAR_RETRY_COUNT,
    VAR_MAX_RETRIES, VAR_MODULE_RUNNING,
})


class ModuleController(QObject):
    """
    Drives all module-specific panels from ADS notification events.

    Args:
        status_panel:   ModuleStatusPanel widget.
        control_panel:  ModuleControlPanel widget.
        setpoint_panel: SetpointPanel widget.
        phase_panel:    PhaseInfoPanel widget.
        fault_panel:    FaultPanel widget.
        ctx:            Shared AppContext.
        graph_panel:    Optional GraphPanel.
        parent:         Qt parent.
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
        self._status_panel  = status_panel
        self._control_panel = control_panel
        self._setpoint_panel = setpoint_panel
        self._phase_panel   = phase_panel
        self._fault_panel   = fault_panel
        self._graph_panel   = graph_panel
        self._ctx           = ctx
        self._bridge: Optional[NotificationBridge] = None

        # Wire control panel buttons
        control_panel.start_requested.connect(self._on_start)
        control_panel.stop_requested.connect(self._on_stop)
        status_panel.clear_fault_requested.connect(self._on_clear_fault)

        # Wire setpoint panel
        setpoint_panel.apply_requested.connect(self._on_apply_setpoint)
        setpoint_panel.update_vi_requested.connect(self._on_update_vi)

    # ── Connection state callbacks ────────────────────────────────────────────

    @pyqtSlot(object)
    def on_connected(self, bridge: NotificationBridge) -> None:
        """Called by ConnectionController when ADS connection + subscriptions are ready."""
        self._bridge = bridge
        self._bridge.variable_changed.connect(self._on_variable_changed)

        self._control_panel.set_connected()
        self._status_panel.set_connected()
        self._setpoint_panel.set_connected()
        if self._graph_panel:
            self._graph_panel.reset_time_origin()

        # Pre-fill setpoints and ramp settings from registry (initial read)
        r = self._ctx.read_variable
        self._setpoint_panel.populate_setpoints(r(VAR_TARGET_VOLTAGE), r(VAR_TARGET_CURRENT))
        self._setpoint_panel.populate_ramp_settings(
            r(VAR_ENABLE_RAMP), r(VAR_RAMP_STEP), r(VAR_RAMP_TIME_S)
        )
        self.status_message.emit("Connected – ADS notifications active")

    @pyqtSlot()
    def on_disconnected(self) -> None:
        if self._bridge:
            try:
                self._bridge.variable_changed.disconnect(self._on_variable_changed)
            except TypeError:
                pass
            self._bridge = None

        self._control_panel.set_disconnected()
        self._status_panel.set_disconnected()
        self._setpoint_panel.set_disconnected()
        self.status_message.emit("Disconnected")

    # ── ADS notification handler ──────────────────────────────────────────────

    @pyqtSlot(str)
    def _on_variable_changed(self, name: str) -> None:
        """
        Dispatched on the Qt main thread whenever a PLCVariable value changes.

        Only the panels affected by *name* are updated to minimise unnecessary
        Qt widget redraws.
        """
        r = self._ctx.read_variable

        if name in _STATUS_VARS:
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

        if name in _SETPOINT_VARS:
            self._setpoint_panel.update_live_voltage(r(VAR_MODULE_VOLTAGE))
            self._setpoint_panel.update_live_current(r(VAR_MODULE_CURRENT))
            self._setpoint_panel.update_live_ramp_voltage(r(VAR_RAMP_CURR_VOLT))

        if name in _PHASE_VARS:
            self._phase_panel.update_phases(r(VAR_PHASE_A), r(VAR_PHASE_B), r(VAR_PHASE_C))
            self._phase_panel.update_temperature(r(VAR_TEMPERATURE))

        if name in _FAULT_VARS:
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

        if name in _CONTROL_VARS:
            self._control_panel.update_addresses(r(VAR_MODULE_ADDRESS), r(VAR_MASTER_ADDRESS))
            self._control_panel.update_retries(r(VAR_RETRY_COUNT), r(VAR_MAX_RETRIES))
            self._control_panel.update_running_state(bool(r(VAR_MODULE_RUNNING)))

        # Graph panel — voltage trend (appended on every voltage notification)
        if name == VAR_MODULE_VOLTAGE and self._graph_panel:
            self._graph_panel.append(r(VAR_MODULE_VOLTAGE))

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

    @pyqtSlot(float, float, bool, float, float)
    def _on_apply_setpoint(
        self,
        voltage_v: float,
        current_a: float,
        enable_ramp: bool,
        ramp_step_v: float,
        ramp_time_s: float,
    ) -> None:
        try:
            self._ctx.write_variable(VAR_TARGET_VOLTAGE, voltage_v)
            self._ctx.write_variable(VAR_TARGET_CURRENT, current_a)
            self._ctx.write_variable(VAR_ENABLE_RAMP, enable_ramp)
            self._ctx.write_variable(VAR_RAMP_STEP, ramp_step_v)
            self._ctx.write_variable(VAR_RAMP_TIME_S, ramp_time_s)
            log.info(
                "Setpoints written: %.1f V / %.2f A  ramp=%s step=%.1f V time=%.2f s",
                voltage_v, current_a, enable_ramp, ramp_step_v, ramp_time_s,
            )
            self.status_message.emit(
                f"Setpoints written: {voltage_v:.1f} V / {current_a:.2f} A"
                + (f"  ramp: {ramp_step_v:.1f} V every {ramp_time_s:.2f} s" if enable_ramp else "")
                + "  ← now press 'Send Update Signal' to apply"
            )
        except Exception as exc:
            self.error_occurred.emit(f"Setpoint write failed: {exc}")

    @pyqtSlot()
    def _on_update_vi(self) -> None:
        try:
            self._ctx.write_variable(VAR_UPDATE_VI, True)
            log.info("bUpdateSetpoint pulsed TRUE")
            self.status_message.emit("Update signal sent — PLC applying new setpoints")
        except Exception as exc:
            self.error_occurred.emit(f"Update signal failed: {exc}")

    def teardown(self) -> None:
        """Release the notification bridge connection."""
        if self._bridge:
            try:
                self._bridge.variable_changed.disconnect(self._on_variable_changed)
            except TypeError:
                pass
            self._bridge = None
