"""
app_context.py
──────────────
Dependency container for the TONHE Module HMI – ADS Notification Edition.

Key difference from the polling edition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This context owns one **or more** notification channels.  Each ADS connection
can hold at most ``NOTIFICATION_CHANNEL_LIMIT`` (499) notification handles.
If the variable list exceeds that cap, additional ConnectionManager + ADSClient
+ NotificationManager instances are opened automatically on the same PLC
endpoint, so all variables remain covered.

Channel Layout (example with 600 variables)
::

    Channel 0 : vars[0..498]   → ConnectionManager-0 → NotificationManager-0
    Channel 1 : vars[499..599] → ConnectionManager-1 → NotificationManager-1
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from tone_hmi_ads.constants import ADS_BACKEND_DIR, NOTIFICATION_CHANNEL_LIMIT


def _ensure_ads_on_path() -> None:
    ads_path = str(ADS_BACKEND_DIR)
    if ADS_BACKEND_DIR.exists() and ads_path not in sys.path:
        sys.path.insert(0, ads_path)


def _batched(seq: list, size: int):
    """Yield successive *size*-length chunks from *seq*."""
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


class AppContext:
    """Holds all live service instances for one HMI session."""

    def __init__(self) -> None:
        self.config = None
        self.registry = None

        # Primary channel
        self.connection_manager = None
        self.ads_client = None

        # Read / write services (always use primary channel)
        self.read_service = None
        self.write_service = None

        # Notification managers — one per channel (primary in index 0)
        self.notif_managers: list = []

        # Extra channels opened when >499 variables need notifications
        self._extra_conn_managers: list = []

        self.config_path: str = ""
        self.is_loaded: bool = False
        self._mock_mode: bool = False

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
            from tone_hmi_ads.mock_ads import MockADSConnectionManager, MockADSClient
            self.connection_manager = MockADSConnectionManager()
            self.ads_client = MockADSClient(self.connection_manager)
            self._mock_mode = True
            print("Running with MOCK ADS Client")
        else:
            self.connection_manager = ConnectionManager(
                self.config.connection,
                self.config.reconnect,
                self.config.heartbeat,
            )
            self.ads_client = ADSClient(self.connection_manager)
            self._mock_mode = False

        self.read_service = PLCReadService(self.ads_client, self.registry)
        self.write_service = PLCWriteService(self.ads_client, self.registry)
        self.is_loaded = True

    def setup_notifications(self) -> None:
        """
        Create and start all notification channels, then subscribe variables.

        Splits subscriptions into batches of ``NOTIFICATION_CHANNEL_LIMIT``.
        For most deployments there is only a single channel; additional channels
        are opened transparently when the variable count exceeds 499.

        Must be called after :meth:`load` and after the primary connection is
        open (``connection_manager.open()`` completed successfully).
        """
        _ensure_ads_on_path()

        from core.notification_manager import NotificationManager
        from core.connection_manager import ConnectionManager
        from core.ads_client import ADSClient

        # Tear down any previously created channels first (idempotent re-connect)
        self._teardown_notifications()

        all_vars = list(self.registry)
        batches = list(_batched(all_vars, NOTIFICATION_CHANNEL_LIMIT))

        for idx, batch in enumerate(batches):
            if idx == 0:
                # Primary channel reuses the existing connection
                nm = NotificationManager(
                    self.ads_client,
                    self.registry,
                    self.config.notifications,
                )
            else:
                # Extra channel — open a parallel ADS connections to the same PLC.
                # Each extra connection is independent so it gets its own pool of
                # 500 notification handles.
                import logging
                log = logging.getLogger(__name__)
                log.info(
                    "Opening extra ADS notification channel %d "
                    "(variables %d–%d of %d total)",
                    idx,
                    idx * NOTIFICATION_CHANNEL_LIMIT,
                    idx * NOTIFICATION_CHANNEL_LIMIT + len(batch) - 1,
                    len(all_vars),
                )
                extra_cm = ConnectionManager(
                    self.config.connection,
                    self.config.reconnect,
                    self.config.heartbeat,
                )
                extra_cm.open()
                extra_ac = ADSClient(extra_cm)
                self._extra_conn_managers.append(extra_cm)
                nm = NotificationManager(extra_ac, self.registry, self.config.notifications)

            nm.start()

            for var in batch:
                try:
                    nm.subscribe_variable(var)
                except Exception as exc:  # noqa: BLE001
                    import logging
                    logging.getLogger(__name__).warning(
                        "Could not subscribe '%s' on channel %d: %s",
                        var.name, idx, exc,
                    )

            self.notif_managers.append(nm)

    def _teardown_notifications(self) -> None:
        """Stop all notification managers and close extra channels."""
        for nm in self.notif_managers:
            try:
                nm.stop()
            except Exception:
                pass
        self.notif_managers.clear()

        for cm in self._extra_conn_managers:
            try:
                cm.close()
            except Exception:
                pass
        self._extra_conn_managers.clear()

    def teardown(self) -> None:
        """Close ADS connections and release all resources."""
        self._teardown_notifications()
        try:
            if self.connection_manager:
                self.connection_manager.close()
        except Exception:
            pass

    # ── Convenience helpers ───────────────────────────────────────────────────

    def read_variable(self, name: str):
        """Return the cached value of a PLC variable, or None."""
        if not self.registry:
            return None
        var = self.registry.get_optional(name)
        return var.current_value if var else None

    def write_variable(self, name: str, value) -> None:
        """Write *value* to a PLC variable by name."""
        if not self.write_service:
            return
        if self._mock_mode:
            self.ads_client.write_by_name(name, value, None)
            return
        if self.registry and not self.registry.contains(name):
            plc_type = self._infer_plc_type(value)
            self.registry.register(name, plc_type)
        self.write_service.write_variable(name, value)

    @staticmethod
    def _infer_plc_type(value) -> str:
        if isinstance(value, bool):
            return "BOOL"
        if isinstance(value, float):
            return "REAL"
        if isinstance(value, int):
            return "INT"
        return "STRING"
