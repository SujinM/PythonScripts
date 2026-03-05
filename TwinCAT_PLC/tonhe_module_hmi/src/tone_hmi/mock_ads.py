"""
mock_ads.py
───────────
A mock ADS ConnectionManager to plug into the AppContext to allow
the GUI to run without a real PLC.

Usage: Replace AppContext.connection_manager and ads_client with these mocks.
"""

import time
import random
import threading
from typing import Any
from PyQt6.QtCore import QObject, pyqtSignal

class MockADSConnectionManager(QObject):
    connection_state_changed = pyqtSignal(bool)
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.is_connected = False
        self._memory = {}
        
        # Initialize some default values based on tone_config.xml
        self.write_by_name("GVL.nModuleStatus", 1, pyqt_type=None)
        self.write_by_name("MAIN.bModuleRunning", True, pyqt_type=None)
        self.write_by_name("GVL.nModuleVoltage", 420.5, pyqt_type=None)
        self.write_by_name("GVL.nModuleCurrent", 12.3, pyqt_type=None)

    def connect(self) -> bool:
        self.is_connected = True
        self._start_t = time.monotonic()
        self.connection_state_changed.emit(True)
        return True

    def open(self) -> None:
        self.connect()

    @property
    def is_open(self) -> bool:
        return self.is_connected

    def close(self) -> None:
        self.is_connected = False
        self.connection_state_changed.emit(False)

    def read_by_name(self, name: str, pyads_type: int) -> Any:
        elapsed = time.monotonic() - getattr(self, '_start_t', time.monotonic())
        
        # Simulate some random fluctuations for voltage and current
        if name == "GVL.nModuleVoltage":
            ramp_v = min(400.0, elapsed * 5.0)  # Ascend 10V per second up to 400V
            return ramp_v + random.uniform(-1.0, 1.0)
        elif name == "GVL.nModuleCurrent":
            ramp_a = min(15.0, elapsed * 0.5)    # Ascend 1A per second up to 15A
            return ramp_a + random.uniform(-0.1, 0.1)
        elif name == "GVL.nPhaseVoltageA":
            return 230.0 + random.uniform(-2.0, 2.0)
        elif name == "GVL.nPhaseVoltageB":
            return 230.0 + random.uniform(-2.0, 2.0)
        elif name == "GVL.nPhaseVoltageC":
            return 230.0 + random.uniform(-2.0, 2.0)
        elif name == "GVL.nAmbientTemperature":
            return int(25 + random.uniform(-2, 2))
        elif name == "GVL.nModuleStatus":
            return 1 # ON
        elif name == "MAIN.bModuleRunning":
            return True
        elif name == "MAIN.nTargetVoltage":
            return 4000 # 400.0V
        elif name == "MAIN.nTargetCurrent":
            return 1500 # 15.00A
        elif name == "MAIN.sStatusText":
            return "Mock Running"
            
        return self._memory.get(name, 0)

    def write_by_name(self, name: str, value: Any, pyqt_type: Any) -> None:
        self._memory[name] = value

class MockADSClient:
    def __init__(self, connection_manager):
        self._conn = connection_manager

    def read_by_name(self, name: str, pyads_type: int) -> Any:
        return self._conn.read_by_name(name, pyads_type)

    def write_by_name(self, name: str, value: Any, pyads_type: int) -> None:
        self._conn.write_by_name(name, value, pyads_type)
