"""
mock_ads.py
───────────
A mock ADS ConnectionManager to plug into the AppContext so the GUI
can be exercised without a real PLC.

Simulates:
  • Start / Stop commands (bEnableModule / bDisableModule rising edges)
  • Soft-start voltage ramp (bEnableRamp, nRampVoltageStep, tRampStepTime)
  • Fault injection and Clear-Fault recovery
  • Live V / I / temperature / phase-voltage readbacks with noise
  • Retry counter during WaitAck phase
  • All variable paths introduced in the latest refactor
    (MAIN.stStatus.*, MAIN.stSettings.*, MAIN.fbComm.*, MAIN.fbModule.*)
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

        # ── Persisted write-back memory (for reads of setpoints / commands) ──
        self._mem: dict[str, Any] = {}

        # ── Simulation state ──────────────────────────────────────────────────
        self._state         = _IDLE
        self._actual_voltage = 0.0
        self._actual_current = 0.0
        self._ramp_voltage   = 0.0        # current ramp step voltage
        self._ack_pending    = False      # TRUE while waiting for M_C_2
        self._ack_timer      = 0.0
        self._retry_count    = 0
        self._rx_frame_count = 0
        self._last_cob_id    = 0
        self._fault_bits     = 0
        self._status_received_pulse = False
        self._connect_time   = 0.0

        # ── Default setpoints ─────────────────────────────────────────────────
        self._mem["MAIN.stSettings.nTargetVoltage"]  = 5000    # 500.0 V
        self._mem["MAIN.stSettings.nTargetCurrent"]  = 4100    # 41.00 A
        self._mem["MAIN.stSettings.nModuleAddress"]  = 0x01
        self._mem["MAIN.stSettings.nMasterAddress"]  = 0xA0
        self._mem["MAIN.stSettings.bEnableRamp"]     = False
        self._mem["MAIN.stSettings.nRampVoltageStep"] = 100    # 10 V / step
        self._mem["MAIN.stSettings.tRampStepTime"]   = 1000    # 1 s
        self._mem["MAIN.stSettings.bEnableModule"]   = False
        self._mem["MAIN.stSettings.bDisableModule"]  = False
        self._mem["MAIN.stSettings.bClearFault"]     = False
        self._mem["MAIN.stSettings.bUpdateSetpoint"] = False
        self._mem["MAIN.fbModule.nRetryCount"]       = 0
        self._mem["MAIN.fbModule.nMaxRetries"]       = 10

        # ── Background simulation thread ──────────────────────────────────────
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._sim_loop, daemon=True)

    # ── Connection helpers ────────────────────────────────────────────────────

    def connect(self) -> bool:
        self.is_connected = True
        self._connect_time = time.monotonic()
        self._stop_event.clear()
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._sim_loop, daemon=True)
            self._thread.start()
        self.connection_state_changed.emit(True)
        return True

    def open(self) -> None:
        self.connect()

    @property
    def is_open(self) -> bool:
        return self.is_connected

    def close(self) -> None:
        self.is_connected = False
        self._stop_event.set()
        self.connection_state_changed.emit(False)

    # ── Read ──────────────────────────────────────────────────────────────────

    def read_by_name(self, name: str, pyads_type: int) -> Any:  # noqa: ARG002
        # ── Live-computed values ───────────────────────────────────────────────

        # Module status measurements
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
                return 0x01   # ON
            if self._state == _FAULT:
                return 0x11   # FAULT
            return 0x00       # OFF

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

        # Ramp progress
        if name == "MAIN.stStatus.nRampCurrentVoltage":
            return int(self._ramp_voltage)

        if name == "MAIN.stStatus.bRampComplete":
            return self._state != _RAMPING

        # Fault bits
        if name == "MAIN.stStatus.wFaultBits":
            return self._fault_bits & 0xFFFF

        if name == "MAIN.stStatus.nPfcFaultBits":
            return (self._fault_bits >> 16) & 0xFF

        if name == "MAIN.stStatus.wStatusBits":
            return 0x0001 if self._state in (_RUNNING, _RAMPING) else 0x0000

        if name == "MAIN.stStatus.wExtFaultWarningBits":
            return 0x0001 if self._state == _FAULT else 0x0000

        # ACK / status received pulses
        if name == "MAIN.stStatus.bAckReceived":
            return self._state == _RUNNING and self._ack_pending is False

        if name == "MAIN.fbComm.bStatusReceived":
            v = self._status_received_pulse
            self._status_received_pulse = False   # auto-clear after read
            return v

        # Phase voltages — simulated AC ripple
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

        # CAN diagnostics
        if name == "MAIN.fbComm.nRxFrameCount":
            return self._rx_frame_count

        if name == "MAIN.fbComm.nLastRxCobId":
            return self._last_cob_id

        # FB internals
        if name == "MAIN.fbModule.nRetryCount":
            return self._retry_count

        if name == "MAIN.fbModule.nMaxRetries":
            return self._mem.get("MAIN.fbModule.nMaxRetries", 10)

        # Setpoints / commands — return whatever was last written
        return self._mem.get(name, 0)

    # ── Write ─────────────────────────────────────────────────────────────────

    def write_by_name(self, name: str, value: Any, pyqt_type: Any) -> None:  # noqa: ARG002
        prev = self._mem.get(name)
        self._mem[name] = value

        # Detect rising edges on command bits
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
        # Simulate brief ACK delay (0.4 s) then transition to Running/Ramping
        threading.Timer(0.4, self._ack_received).start()

    def _ack_received(self) -> None:
        if self._state != _SEND_START:
            return
        # Reset the command bit so a new rising edge can be detected next time
        self._mem["MAIN.stSettings.bEnableModule"] = False
        enable_ramp = bool(self._mem.get("MAIN.stSettings.bEnableRamp", False))
        if enable_ramp:
            self._ramp_voltage = float(
                self._mem.get("MAIN.stSettings.nRampVoltageStep", 100)
            )
            self._state = _RAMPING
        else:
            target_raw = int(self._mem.get("MAIN.stSettings.nTargetVoltage", 5000))
            self._actual_voltage = target_raw / 10.0
            self._actual_current = 0.0
            self._ramp_voltage   = int(target_raw)
            self._state          = _RUNNING
        self._rx_frame_count += 1

    def _handle_stop(self) -> None:
        if self._state in (_IDLE, _FAULT):
            return
        self._state          = _SEND_STOP
        self._actual_voltage = 0.0
        self._actual_current = 0.0
        self._ramp_voltage   = 0
        threading.Timer(0.2, self._stop_complete).start()

    def _stop_complete(self) -> None:
        self._state = _IDLE
        # Reset the command bit so a new rising edge can be detected next time
        self._mem["MAIN.stSettings.bDisableModule"] = False

    def _handle_clear_fault(self) -> None:
        if self._state == _FAULT:
            self._fault_bits = 0
            self._state      = _IDLE
        # Always reset the command bit for re-triggering
        self._mem["MAIN.stSettings.bClearFault"] = False

    def _handle_update_setpoint(self) -> None:
        """Apply new V/I and ramp settings while running."""
        if self._state not in (_RUNNING, _RAMPING):
            return
        target_raw = int(self._mem.get("MAIN.stSettings.nTargetVoltage", 5000))
        curr_raw   = int(self._mem.get("MAIN.stSettings.nTargetCurrent", 4100))
        enable_ramp = bool(self._mem.get("MAIN.stSettings.bEnableRamp", False))
        if enable_ramp and self._state == _RUNNING:
            # Restart ramp from current voltage toward new target
            self._ramp_voltage = int(self._actual_voltage * 10)
            self._state        = _RAMPING
        else:
            self._actual_voltage = target_raw / 10.0
            # current ramps to new target over ~2 s (handled in sim loop)

    # ── Background simulation loop ────────────────────────────────────────────

    def _sim_loop(self) -> None:
        """Update simulated measurements at ~10 Hz."""
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
                    self._ramp_voltage = min(
                        self._ramp_voltage + step_raw,
                        target_raw,
                    )
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
                last_ramp_step = now   # keep timer consistent
                target_raw = int(self._mem.get("MAIN.stSettings.nTargetVoltage", 5000))
                curr_raw   = int(self._mem.get("MAIN.stSettings.nTargetCurrent", 4100))
                # Slowly converge actual values to target (simulate controller settling)
                self._actual_voltage += (target_raw / 10.0 - self._actual_voltage) * 0.05
                self._actual_current += (curr_raw / 100.0 - self._actual_current) * 0.05
                self._rx_frame_count += 1
                self._status_received_pulse = True
                self._last_cob_id = 0x100 | int(
                    self._mem.get("MAIN.stSettings.nModuleAddress", 1)
                )

                # Randomised fault injection: 0.02 % chance per cycle (~once / 50 s)
                if random.random() < 0.0002:
                    self._fault_bits = 0x0001
                    self._state      = _FAULT


class MockADSClient:
    def __init__(self, connection_manager: MockADSConnectionManager) -> None:
        self._conn = connection_manager

    def read_by_name(self, name: str, pyads_type: int) -> Any:
        return self._conn.read_by_name(name, pyads_type)

    def write_by_name(self, name: str, value: Any, pyads_type: int) -> None:
        self._conn.write_by_name(name, value, pyads_type)
