"""
app_context.py
──────────────
Dependency container for the ToneModule HMI.  Holds all live service
instances and wires the ADS backend from the sibling *plc_ads_project*.
"""

from __future__ import annotations

import sys
from pathlib import Path

from tone_hmi.constants import ADS_BACKEND_DIR


def _ensure_ads_on_path() -> None:
    # In a cx_Freeze build the ADS packages are already bundled as Python
    # packages; ADS_BACKEND_DIR does not exist on disk and sys.path injection
    # is not needed.  In a source-tree run the sibling directory is added so
    # the dynamic imports (config.*, core.*, etc.) resolve correctly.
    ads_path = str(ADS_BACKEND_DIR)
    if ADS_BACKEND_DIR.exists() and ads_path not in sys.path:
        sys.path.insert(0, ads_path)


class AppContext:
    """Holds all live service instances for one HMI session."""

    def __init__(self) -> None:
        self.config = None
        self.registry = None
        self.connection_manager = None
        self.ads_client = None
        self.read_service = None
        self.write_service = None
        self.config_path: str = ""
        self.is_loaded: bool = False

    # ── Public API ────────────────────────────────────────────────────────────

    def load(self, config_path: str) -> None:
        """Parse the XML config and initialise all service instances."""
        _ensure_ads_on_path()

        from config.config_loader import ConfigLoader
        from models.variable_registry import VariableRegistry
        from core.connection_manager import ConnectionManager
        from core.ads_client import ADSClient
        from services.plc_read_service import PLCReadService
        from services.plc_write_service import PLCWriteService

        self.config_path = str(Path(config_path).resolve())
        self.config = ConfigLoader.load(self.config_path)

        self.registry = VariableRegistry()
        self.registry.load_from_config(self.config)

        import os
        if os.environ.get("MOCK_ADS") == "1":
            from tone_hmi.mock_ads import MockADSConnectionManager, MockADSClient
            self.connection_manager = MockADSConnectionManager()
            self.ads_client = MockADSClient(self.connection_manager)
            print("Running with MOCK ADS Client")
        else:
            self.connection_manager = ConnectionManager(
                self.config.connection,
                self.config.reconnect,
                self.config.heartbeat,
            )
            self.ads_client = ADSClient(self.connection_manager)

        self.read_service = PLCReadService(self.ads_client, self.registry)
        self.write_service = PLCWriteService(self.ads_client, self.registry)
        self._mock_mode = os.environ.get("MOCK_ADS") == "1"

        self.is_loaded = True

    def teardown(self) -> None:
        """Close the ADS connection and release resources."""
        try:
            if self.connection_manager:
                self.connection_manager.close()
        except Exception:
            pass

    # ── Convenience helpers ───────────────────────────────────────────────────

    def read_variable(self, name: str):
        """Return the cached value of a PLC variable, or None if not registered."""
        if not self.registry:
            return None
        var = self.registry.get_optional(name)
        return var.current_value if var else None

    def write_variable(self, name: str, value) -> None:
        """Write *value* to a PLC variable by name.  Silently ignores unknown names."""
        if not self.write_service:
            return
        # In mock mode the registry may not contain every symbol —
        # write directly through the client so commands always reach the
        # mock state machine regardless of what the registry holds.
        if getattr(self, "_mock_mode", False):
            self.ads_client.write_by_name(name, value, None)
        else:
            self.write_service.write_variable_safe(name, value)
