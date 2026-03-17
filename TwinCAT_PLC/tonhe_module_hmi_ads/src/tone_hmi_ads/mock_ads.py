"""
mock_ads.py
───────────
Mock ADS backend for the TONHE Module HMI – ADS Notification Edition.

In addition to the read/write interface of the polling edition, this mock
also drives simulated PLCVariable change hooks so the NotificationBridge
receives events exactly as it would from real ADS notifications.
"""

from __future__ import annotations

import math
import random
import threading
import time
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

# ── Internal state IDs (mirrors E_ModuleState) ─────────────────────────────
_IDLE        = 0
_SEND_START  = 2
_WAIT_ACK    = 3
_RUNNING     = 4
_RAMPING     = 5
_SEND_STOP   = 6
_FAULT       = 7

_STATE_TEXT = {
    _IDLE:       "Idle — Ready to start.",
    _SEND_START: "START sent — waiting for ACK…",
    _WAIT_ACK:   "Waiting for ACK (M_C_2)…",
    _RUNNING:    "Running",
    _RAMPING:    "Ramping — soft-start in progress…",
    _SEND_STOP:  "Stop command sent.",
    _FAULT:      "FAULT — check fault bits.",
}


class MockADSConnectionManager(QObject):
    connection_state_changed = pyqtSignal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.is_connected = False

        self._mem: dict[str, Any] = {}
        self._registry = None   # injected after load via set_registry()

        # Simulation state
        self._state          = _IDLE
        self._actual_voltage = 0.0
        self._actual_current = 0.0
        self._ramp_voltage   = 0.0
        self._ack_pending    = False
        self._retry_count    = 0
        self._rx_frame_count = 0
        self._last_cob_id    = 0
        self._fault_bits     = 0
        self._status_received_pulse = False

        # Default setpoints
        self._mem["MAIN.stSettings.nTargetVoltage"]  = 5000
        self._mem["MAIN.stSettings.nTargetCurrent"]  = 4100
        self._mem["MAIN.stSettings.nModuleAddress"]  = 0x01
        self._mem["MAIN.stSettings.nMasterAddress"]  = 0xA0
        self._mem["MAIN.stSettings.bEnableRamp"]     = False
        self._mem["MAIN.stSettings.nRampVoltageStep"] = 100
        self._mem["MAIN.stSettings.tRampStepTime"]   = 1000
        self._mem["MAIN.stSettings.bEnableModule"]   = False
        self._mem["MAIN.stSettings.bDisableModule"]  = False
        self._mem["MAIN.stSettings.bClearFault"]     = False
        self._mem["MAIN.stSettings.bUpdateSetpoint"] = False
        self._mem["MAIN.fbModule.nRetryCount"]       = 0
        self._mem["MAIN.fbModule.nMaxRetries"]       = 10

        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._sim_loop, daemon=True)

    def set_registry(self, registry) -> None:
        """Inject the VariableRegistry so the mock can fire change hooks."""
        self._registry = registry

    def _fire_hook(self, name: str, value: Any) -> None:
        """Update the PLCVariable and trigger its change hooks (simulates notification)."""
        if self._registry is None:
            return
        var = self._registry.get_optional(name)
        if var is not None:
            var.update_value(value)

    # ── Connection helpers ────────────────────────────────────────────────────

    def open(self) -> None:
        self.is_connected = True
        self._stop_event.clear()
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._sim_loop, daemon=True)
            self._thread.start()
        self.connection_state_changed.emit(True)

    @property
    def is_open(self) -> bool:
        return self.is_connected

    def close(self) -> None:
        self.is_connected = False
        self._stop_event.set()
        self.connection_state_changed.emit(False)

    # ── Read ──────────────────────────────────────────────────────────────────

    def read_by_name(self, name: str, pyads_type: int) -> Any:  # noqa: ARG002
        if name == "MAIN.stStatus.rActualVoltage":
            if self._state in (_RUNNING, _RAMPING):
                return self._actual_voltage + random.uniform(-0.5, 0.5)
            return 0.0
        if name == "MAIN.stStatus.rActualCurrent":
            if self._state in (_RUNNING, _RAMPING):
                return self._actual_current + random.uniform(-0.05, 0.05)
            return 0.0
        if name == "MAIN.stStatus.nModuleState":
            if self._state in (_RUNNING, _RAMPING):
                return 0x01
            if self._state == _FAULT:
                return 0x11
            return 0x00
        if name == "MAIN.stStatus.bModuleRunning":
            return self._state in (_RUNNING, _RAMPING)
        if name == "MAIN.stStatus.bModuleFault":
            return self._state == _FAULT
        if name == "MAIN.stStatus.sStatusText":
            text = _STATE_TEXT.get(self._state, "Mock")
            if self._state == _RUNNING:
                text = (
                    f"Running — V:{self._actual_voltage:.1f}V  "
                    f"I:{self._actual_current:.2f}A"
                )
            return text
        if name == "MAIN.stStatus.eControlState":
            return self._state
        if name in ("MAIN.stStatus.rRampCurrentVoltage", "MAIN.stStatus.nRampCurrentVoltage"):
            return self._ramp_voltage
        if name == "MAIN.stStatus.bRampComplete":
            return self._state != _RAMPING
        if name == "MAIN.stStatus.wFaultBits":
            return self._fault_bits & 0xFFFF
        if name == "MAIN.stStatus.nPfcFaultBits":
            return (self._fault_bits >> 16) & 0xFF
        if name == "MAIN.stStatus.wStatusBits":
            return 0x0001 if self._state in (_RUNNING, _RAMPING) else 0x0000
        if name == "MAIN.stStatus.wExtFaultWarningBits":
            return 0x0001 if self._state == _FAULT else 0x0000
        if name == "MAIN.stStatus.bAckReceived":
            return self._state == _RUNNING and not self._ack_pending
        if name == "MAIN.fbComm.bStatusReceived":
            v = self._status_received_pulse
            self._status_received_pulse = False
            return v
        if name in (
            "MAIN.stStatus.rPhaseVoltageA",
            "MAIN.stStatus.rPhaseVoltageB",
            "MAIN.stStatus.rPhaseVoltageC",
        ):
            base = {"A": 0.0, "B": 120.0, "C": 240.0}
            ph = name[-1]
            t = time.monotonic()
            return 230.0 + 5.0 * math.sin(2 * math.pi * 50 * t + math.radians(base[ph]))
        if name == "MAIN.stStatus.nTemperature":
            run_heat = 10.0 if self._state in (_RUNNING, _RAMPING) else 0.0
            return int(25.0 + run_heat + random.uniform(-1.0, 1.0))
        if name == "MAIN.fbComm.nRxFrameCount":
            return self._rx_frame_count
        if name == "MAIN.fbComm.nLastRxCobId":
            return self._last_cob_id
        if name == "MAIN.fbModule.nRetryCount":
            return self._retry_count
        if name == "MAIN.fbModule.nMaxRetries":
            return self._mem.get("MAIN.fbModule.nMaxRetries", 10)
        return self._mem.get(name, 0)

    # ── Write ─────────────────────────────────────────────────────────────────

    def write_by_name(self, name: str, value: Any, pyads_type: Any) -> None:  # noqa: ARG002
        prev = self._mem.get(name)
        self._mem[name] = value
        if name == "MAIN.stSettings.bEnableModule" and value and not prev:
            self._handle_start()
        elif name == "MAIN.stSettings.bDisableModule" and value and not prev:
            self._handle_stop()
        elif name == "MAIN.stSettings.bClearFault" and value and not prev:
            self._handle_clear_fault()
        elif name == "MAIN.stSettings.bUpdateSetpoint" and value and not prev:
            self._handle_update_setpoint()

    # ── Command handlers ──────────────────────────────────────────────────────

    def _handle_start(self) -> None:
        if self._state not in (_IDLE, _FAULT):
            return
        self._fault_bits  = 0
        self._retry_count = 0
        self._state       = _SEND_START
        threading.Timer(0.4, self._ack_received).start()

    def _ack_received(self) -> None:
        if self._state != _SEND_START:
            return
        self._mem["MAIN.stSettings.bEnableModule"] = False
        enable_ramp = bool(self._mem.get("MAIN.stSettings.bEnableRamp", False))
        if enable_ramp:
            self._ramp_voltage = float(self._mem.get("MAIN.stSettings.nRampVoltageStep", 100))
            self._state = _RAMPING
        else:
            target_raw = int(self._mem.get("MAIN.stSettings.nTargetVoltage", 5000))
            self._actual_voltage = target_raw / 10.0
            self._actual_current = 0.0
            self._ramp_voltage   = float(target_raw)
            self._state          = _RUNNING
        self._rx_frame_count += 1

    def _handle_stop(self) -> None:
        if self._state in (_IDLE, _FAULT):
            return
        self._state          = _SEND_STOP
        self._actual_voltage = 0.0
        self._actual_current = 0.0
        self._ramp_voltage   = 0.0
        threading.Timer(0.2, self._stop_complete).start()

    def _stop_complete(self) -> None:
        self._state = _IDLE
        self._mem["MAIN.stSettings.bDisableModule"] = False

    def _handle_clear_fault(self) -> None:
        if self._state == _FAULT:
            self._fault_bits = 0
            self._state      = _IDLE
        self._mem["MAIN.stSettings.bClearFault"] = False

    def _handle_update_setpoint(self) -> None:
        if self._state not in (_RUNNING, _RAMPING):
            return
        target_raw  = int(self._mem.get("MAIN.stSettings.nTargetVoltage", 5000))
        enable_ramp = bool(self._mem.get("MAIN.stSettings.bEnableRamp", False))
        if enable_ramp and self._state == _RUNNING:
            self._ramp_voltage = self._actual_voltage * 10
            self._state        = _RAMPING
        else:
            self._actual_voltage = target_raw / 10.0

    # ── Background simulation loop ────────────────────────────────────────────

    def _sim_loop(self) -> None:
        """Update simulated measurements at ~10 Hz and fire change hooks."""
        last_ramp_step = time.monotonic()

        while not self._stop_event.is_set():
            time.sleep(0.1)
            now = time.monotonic()

            if self._state == _RAMPING:
                target_raw  = int(self._mem.get("MAIN.stSettings.nTargetVoltage", 5000))
                step_raw    = int(self._mem.get("MAIN.stSettings.nRampVoltageStep", 100))
                step_time_s = int(self._mem.get("MAIN.stSettings.tRampStepTime", 1000)) / 1000.0

                if now - last_ramp_step >= step_time_s:
                    last_ramp_step = now
                    self._ramp_voltage = min(self._ramp_voltage + step_raw, target_raw)
                    self._actual_voltage = self._ramp_voltage / 10.0
                    self._rx_frame_count += 1
                    self._status_received_pulse = True
                    if self._ramp_voltage >= target_raw:
                        self._actual_voltage = target_raw / 10.0
                        self._actual_current = (
                            int(self._mem.get("MAIN.stSettings.nTargetCurrent", 4100)) / 100.0
                        )
                        self._state = _RUNNING

            elif self._state == _RUNNING:
                last_ramp_step = now
                target_raw = int(self._mem.get("MAIN.stSettings.nTargetVoltage", 5000))
                curr_raw   = int(self._mem.get("MAIN.stSettings.nTargetCurrent", 4100))
                self._actual_voltage += (target_raw / 10.0 - self._actual_voltage) * 0.05
                self._actual_current += (curr_raw / 100.0 - self._actual_current) * 0.05
                self._rx_frame_count += 1
                self._status_received_pulse = True
                self._last_cob_id = 0x100 | int(
                    self._mem.get("MAIN.stSettings.nModuleAddress", 1)
                )
                if random.random() < 0.0002:
                    self._fault_bits = 0x0001
                    self._state      = _FAULT

            # Fire change hooks to simulate ADS notification dispatch
            self._fire_hook("MAIN.stStatus.rActualVoltage", self.read_by_name("MAIN.stStatus.rActualVoltage", 0))
            self._fire_hook("MAIN.stStatus.rActualCurrent", self.read_by_name("MAIN.stStatus.rActualCurrent", 0))
            self._fire_hook("MAIN.stStatus.nModuleState", self.read_by_name("MAIN.stStatus.nModuleState", 0))
            self._fire_hook("MAIN.stStatus.bModuleRunning", self.read_by_name("MAIN.stStatus.bModuleRunning", 0))
            self._fire_hook("MAIN.stStatus.bModuleFault", self.read_by_name("MAIN.stStatus.bModuleFault", 0))
            self._fire_hook("MAIN.stStatus.sStatusText", self.read_by_name("MAIN.stStatus.sStatusText", 0))
            self._fire_hook("MAIN.stStatus.wFaultBits", self.read_by_name("MAIN.stStatus.wFaultBits", 0))
            self._fire_hook("MAIN.stStatus.rPhaseVoltageA", self.read_by_name("MAIN.stStatus.rPhaseVoltageA", 0))
            self._fire_hook("MAIN.stStatus.rPhaseVoltageB", self.read_by_name("MAIN.stStatus.rPhaseVoltageB", 0))
            self._fire_hook("MAIN.stStatus.rPhaseVoltageC", self.read_by_name("MAIN.stStatus.rPhaseVoltageC", 0))
            self._fire_hook("MAIN.stStatus.nTemperature", self.read_by_name("MAIN.stStatus.nTemperature", 0))
            self._fire_hook("MAIN.fbComm.nRxFrameCount", self.read_by_name("MAIN.fbComm.nRxFrameCount", 0))
            self._fire_hook("MAIN.fbComm.nLastRxCobId", self.read_by_name("MAIN.fbComm.nLastRxCobId", 0))
            self._fire_hook("MAIN.fbModule.nRetryCount", self.read_by_name("MAIN.fbModule.nRetryCount", 0))
            self._fire_hook("MAIN.stStatus.rRampCurrentVoltage", self.read_by_name("MAIN.stStatus.rRampCurrentVoltage", 0))


class MockADSClient:
    def __init__(self, connection_manager: MockADSConnectionManager) -> None:
        self._conn = connection_manager

    def read_by_name(self, name: str, pyads_type: int) -> Any:
        return self._conn.read_by_name(name, pyads_type)

    def write_by_name(self, name: str, value: Any, pyads_type: int) -> None:
        self._conn.write_by_name(name, value, pyads_type)
