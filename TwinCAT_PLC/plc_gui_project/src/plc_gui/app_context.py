"""
app_context.py
--------------
Application-level dependency container (service locator / context object).

:class:`AppContext` holds the single set of live service instances shared
across every controller and worker:

* :class:`~config.config_loader.PLCConfig` – parsed XML configuration.
* :class:`~models.variable_registry.VariableRegistry` – all PLC variables.
* :class:`~core.connection_manager.ConnectionManager` – ADS transport lifecycle.
* :class:`~core.ads_client.ADSClient` – read / write / notification facade.
* :class:`~services.plc_read_service.PLCReadService` – high-level reads.
* :class:`~services.plc_write_service.PLCWriteService` – high-level writes.

The context is created during application start-up by :class:`AppController`
and passed (via constructor injection) to each controller and background worker.
It is **not** a global singleton; tests can instantiate independent contexts.

Design
~~~~~~
The heavy imports of the ADS backend happen inside :meth:`AppContext.load` so
the GUI can start and display itself before the backend is imported (faster
first-frame).  The ADS project directory is added to :data:`sys.path` only
when needed.

Usage::

    ctx = AppContext()
    ctx.load("path/to/plc_config.xml")
    ctx.connection_manager.open()
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from plc_gui.constants import ADS_BACKEND_DIR


def _ensure_ads_backend_on_path() -> None:
    """Add the ADS backend project root to ``sys.path`` once."""
    ads_path = str(ADS_BACKEND_DIR)
    if ads_path not in sys.path:
        sys.path.insert(0, ads_path)


class AppContext:
    """
    Holds all live service instances for one application session.

    Attributes:
        config:             Parsed :class:`~config.config_loader.PLCConfig`.
        registry:           :class:`~models.variable_registry.VariableRegistry`.
        connection_manager: :class:`~core.connection_manager.ConnectionManager`.
        ads_client:         :class:`~core.ads_client.ADSClient`.
        read_service:       :class:`~services.plc_read_service.PLCReadService`.
        write_service:      :class:`~services.plc_write_service.PLCWriteService`.
        config_path:        Absolute path to the loaded XML config file.
        is_loaded:          ``True`` once :meth:`load` completes without error.
    """

    def __init__(self) -> None:
        self.config = None
        self.registry = None
        self.connection_manager = None
        self.ads_client = None
        self.read_service = None
        self.write_service = None
        self.config_path: str = ""
        self.is_loaded: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, config_path: str) -> None:
        """
        Parse the XML config and initialise all service instances.

        This method imports the ADS backend modules on first call.

        Args:
            config_path: Absolute (or relative) path to *plc_config.xml*.

        Raises:
            XMLConfigError: If the XML is malformed or missing required fields.
            FileNotFoundError: If *config_path* does not exist.
        """
        _ensure_ads_backend_on_path()

        # Deferred imports so GUI can render before backend is imported.
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

        self.connection_manager = ConnectionManager(
            self.config.connection,
            self.config.reconnect,
            self.config.heartbeat,
        )

        self.ads_client = ADSClient(self.connection_manager)
        self.read_service = PLCReadService(self.ads_client, self.registry)
        self.write_service = PLCWriteService(self.ads_client, self.registry)

        self.is_loaded = True

    def teardown(self) -> None:
        """
        Gracefully shut down the ADS connection and stop background threads.

        Safe to call even if :meth:`load` was never called.
        """
        if self.connection_manager is not None:
            try:
                self.connection_manager.close()
            except Exception:
                pass
        self.is_loaded = False
