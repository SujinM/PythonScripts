"""
main.py
-------
Application entry point for the TwinCAT 3 PLC ADS communication project.

Responsibilities
~~~~~~~~~~~~~~~~
1. Parse CLI arguments (config path, log level, log file).
2. Set up the logging infrastructure.
3. Load XML configuration.
4. Initialise all layers:
       ConfigLoader → VariableRegistry → ConnectionManager
       → ADSClient → NotificationManager → Read/Write Services
5. Open the ADS connection (with auto-reconnect standing by).
6. Subscribe to ADS device notifications for all configured variables.
7. Register a demo change-hook that prints live updates to stdout.
8. Run a periodic polling loop that:
       * Reads all variables by polling ADS (complements notifications).
       * Prints a formatted status table.
       * Demonstrates a write operation on each iteration.
       * Exports the registry snapshot to JSON on each iteration.
9. Handle SIGINT / KeyboardInterrupt for a clean shutdown.

Usage::

    python main.py
    python main.py --config config/plc_config.xml --log-level DEBUG
    python main.py --config config/plc_config.xml --log-file logs/plc.log
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Bootstrap: add project root to sys.path so that absolute imports work
# regardless of how the script is launched.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Project imports (all after path fix)
# ---------------------------------------------------------------------------
from config.config_loader import ConfigLoader, PLCConfig
from core.connection_manager import ConnectionManager
from core.ads_client import ADSClient
from core.notification_manager import NotificationManager
from models.variable_registry import VariableRegistry
from services.plc_read_service import PLCReadService
from services.plc_write_service import PLCWriteService
from utils.logger import setup_logger, get_logger
from utils.custom_exceptions import (
    PLCADSBaseError,
    PLCConnectionError,
    XMLConfigError,
)

# ---------------------------------------------------------------------------
# Module-level logger (populated after setup_logger is called)
# ---------------------------------------------------------------------------
log = get_logger(__name__)


# ===========================================================================
# Health report
# ===========================================================================

@dataclass
class HealthReport:
    """
    Snapshot of :class:`PLCApplication` runtime health.

    Returned by :meth:`PLCApplication.health`.  Suitable for logging,
    serialisation to JSON, or display in an HMI status panel.
    """
    connected: bool
    connection_state: str
    active_subscriptions: int
    queue_depth: int
    variable_count: int
    uptime_seconds: float


# ===========================================================================
# CLI argument parsing
# ===========================================================================

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TwinCAT 3 PLC ADS communication – production entry point",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        default=str(_PROJECT_ROOT / "config" / "plc_config.xml"),
        help="Path to plc_config.xml",
    )
    parser.add_argument(
        "--log-file",
        default=str(_PROJECT_ROOT / "logs" / "plc_ads.log"),
        help="Path to the rotating log file",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Minimum logging level",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="Seconds between polling cycles",
    )
    parser.add_argument(
        "--demo-writes",
        action="store_true",
        default=True,
        help="Perform demo write operations in each poll cycle",
    )
    parser.add_argument(
        "--export-json",
        action="store_true",
        default=True,
        help="Export variable snapshot to JSON after each poll cycle",
    )
    parser.add_argument(
        "--export-dir",
        default=str(_PROJECT_ROOT / "exports"),
        help="Directory for JSON snapshot exports",
    )
    return parser.parse_args()


# ===========================================================================
# Application class
# ===========================================================================

class PLCApplication:
    """
    Top-level application orchestrator.

    Wires together all project layers and exposes:
    * :meth:`start` – open connection, subscribe notifications, begin polling.
    * :meth:`stop` – graceful clean shutdown.

    Args:
        config_path:   Path to the XML configuration file.
        poll_interval: Seconds between active-polling cycles.
        demo_writes:   Whether to run demo write operations.
        export_json:   Whether to export variable snapshots to JSON files.
        export_dir:    Directory for JSON snapshot exports.
    """

    def __init__(
        self,
        config_path: str,
        poll_interval: float = 2.0,
        demo_writes: bool = True,
        export_json: bool = True,
        export_dir: str = "exports",
    ) -> None:
        self._config_path = config_path
        self._poll_interval = poll_interval
        self._demo_writes = demo_writes
        self._export_json = export_json
        self._export_dir = export_dir

        # Will be initialised in start()
        self._config: Optional[PLCConfig] = None
        self._registry: Optional[VariableRegistry] = None
        self._conn_manager: Optional[ConnectionManager] = None
        self._ads_client: Optional[ADSClient] = None
        self._notif_manager: Optional[NotificationManager] = None
        self._read_service: Optional[PLCReadService] = None
        self._write_service: Optional[PLCWriteService] = None

        self._running: bool = False
        self._start_time: float = 0.0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """
        Initialise all layers, open the PLC connection, and begin the main
        polling loop.

        Blocks until :meth:`stop` is called or a fatal error occurs.
        """
        log.info("=" * 60)
        log.info("PLC ADS Application starting")
        log.info("=" * 60)
        self._start_time = time.monotonic()

        # ------------------------------------------------------------------
        # Step 1 – Load configuration
        # ------------------------------------------------------------------
        log.info("Step 1 – Loading XML configuration …")
        try:
            self._config = ConfigLoader.load(self._config_path)
        except XMLConfigError as exc:
            log.critical("Fatal: cannot load configuration – %s", exc)
            raise

        # ------------------------------------------------------------------
        # Step 2 – Build variable registry
        # ------------------------------------------------------------------
        log.info("Step 2 – Building variable registry …")
        self._registry = VariableRegistry()
        self._registry.load_from_config(self._config)
        log.info("  Registered %d variable(s)", len(self._registry))
        for var in self._registry:
            log.info("  • %s [%s]", var.name, var.plc_type)

        # ------------------------------------------------------------------
        # Step 3 – Open ADS connection
        # ------------------------------------------------------------------
        log.info("Step 3 – Opening ADS connection …")
        self._conn_manager = ConnectionManager(
            connection_cfg=self._config.connection,
            reconnect_cfg=self._config.reconnect,
            heartbeat_cfg=self._config.heartbeat,
        )
        try:
            self._conn_manager.open()
        except PLCConnectionError as exc:
            log.error(
                "Could not connect to PLC at %s – %s",
                self._config.connection.ip_address,
                exc,
            )
            log.warning(
                "Auto-reconnect is active. "
                "The application will continue in degraded mode and retry."
            )

        # ------------------------------------------------------------------
        # Step 4 – Initialise client and service layers
        # ------------------------------------------------------------------
        log.info("Step 4 – Initialising ADS client and services …")
        self._ads_client = ADSClient(self._conn_manager)
        self._read_service = PLCReadService(self._ads_client, self._registry)
        self._write_service = PLCWriteService(self._ads_client, self._registry)

        # ------------------------------------------------------------------
        # Step 5 – Register change hooks (event system demo)
        # ------------------------------------------------------------------
        log.info("Step 5 – Registering variable change hooks …")
        for var in self._registry:
            var.register_change_hook(
                lambda val, name=var.name, typ=var.plc_type: (
                    print(
                        f"  [CHANGE] {name} [{typ}] → {val!r}  "
                        f"({datetime.now(timezone.utc).strftime('%H:%M:%S.%f')[:-3]})"
                    )
                )
            )

        # ------------------------------------------------------------------
        # Step 6 – Start notification manager and subscribe
        # ------------------------------------------------------------------
        log.info("Step 6 – Starting notification manager …")
        self._notif_manager = NotificationManager(
            ads_client=self._ads_client,
            registry=self._registry,
            notif_config=self._config.notifications,
        )
        self._notif_manager.start()

        if self._conn_manager.is_connected:
            log.info("  Subscribing to ADS device notifications …")
            self._notif_manager.subscribe_all()
            log.info(
                "  Active subscriptions: %s",
                self._notif_manager.active_subscriptions,
            )
        else:
            log.warning(
                "  PLC not connected; ADS notifications will be registered "
                "once the connection is established."
            )

        # ------------------------------------------------------------------
        # Step 7 – Main polling loop
        # ------------------------------------------------------------------
        log.info("Step 7 – Entering main polling loop (interval=%.1fs) …", self._poll_interval)
        log.info("  Press Ctrl+C to stop cleanly.")
        print("\n" + "=" * 60)
        print("  PLC ADS Application – Live Variable Monitor")
        print("=" * 60)

        self._running = True
        cycle = 0

        while self._running:
            cycle += 1
            self._poll_cycle(cycle)
            time.sleep(self._poll_interval)

    def stop(self) -> None:
        """Stop the polling loop and clean up all resources."""
        log.info("Shutdown requested …")
        self._running = False

        if self._notif_manager:
            self._notif_manager.stop()

        if self._conn_manager:
            self._conn_manager.close()

        log.info("PLC ADS Application stopped cleanly")
        print("\n  Shutdown complete.")

    def health(self) -> HealthReport:
        """
        Return a snapshot of the current application runtime health.

        All fields are safe to read from any thread.  No PLC I/O is
        performed; the report is composed entirely from in-memory state.

        Example::

            report = app.health()
            print(report.connection_state, report.active_subscriptions)
        """
        return HealthReport(
            connected=(
                self._conn_manager.is_connected if self._conn_manager else False
            ),
            connection_state=(
                self._conn_manager.state.name
                if self._conn_manager
                else "NOT_INITIALISED"
            ),
            active_subscriptions=(
                len(self._notif_manager.active_subscriptions)
                if self._notif_manager
                else 0
            ),
            queue_depth=(
                self._notif_manager.queue_depth if self._notif_manager else 0
            ),
            variable_count=len(self._registry) if self._registry else 0,
            uptime_seconds=(
                time.monotonic() - self._start_time if self._start_time else 0.0
            ),
        )

    # ------------------------------------------------------------------
    # Poll cycle
    # ------------------------------------------------------------------

    def _poll_cycle(self, cycle: int) -> None:
        """
        One iteration of the main polling loop:

        1. Attempt to read all variables via ADS polling.
        2. Print the current variable table.
        3. Optionally perform demo writes.
        4. Optionally export a JSON snapshot.
        """
        print(f"\n[Cycle {cycle}] {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("-" * 50)

        # ---- Read all variables ----
        if self._read_service and self._conn_manager and self._conn_manager.is_connected:
            snapshot = self._read_service.read_all()
        else:
            # Use cached values from the registry when offline.
            snapshot = {
                var.name: var.current_value
                for var in (self._registry or [])
            }

        # ---- Print status table ----
        for var in (self._registry or []):
            value = snapshot.get(var.name)
            updated = var.last_updated.strftime("%H:%M:%S") if var.last_updated else "—"
            print(f"  {var.name:<30} [{var.plc_type:<6}]  {str(value):<20}  @{updated}")

        # ---- Demo write operations ----
        if (
            self._demo_writes
            and self._write_service
            and self._conn_manager
            and self._conn_manager.is_connected
        ):
            self._perform_demo_writes(cycle)

        # ---- JSON export ----
        if self._export_json and self._registry:
            self._export_snapshot_to_json()

    # ------------------------------------------------------------------
    # Demo writes
    # ------------------------------------------------------------------

    def _perform_demo_writes(self, cycle: int) -> None:
        """
        Demonstrate write operations by toggling / updating variables.

        Uses write_variable_safe so a write failure does not crash the loop.
        """
        assert self._write_service is not None  # guarded by caller

        # Toggle motor on every other cycle.
        motor_state = cycle % 2 == 0
        self._write_service.write_variable_safe("MAIN.bMotorOn", motor_state)

        # Ramp speed.
        speed = (cycle * 50) % 32_767
        self._write_service.write_variable_safe("MAIN.nSpeed", speed)

        log.debug("Demo writes: bMotorOn=%s nSpeed=%d", motor_state, speed)

    # ------------------------------------------------------------------
    # JSON export
    # ------------------------------------------------------------------

    def _export_snapshot_to_json(self) -> None:
        """
        Overwrite ``snapshot_latest.json`` with the current registry state.

        Writing to a single fixed file (rather than a new timestamped file
        per cycle) prevents unbounded disk growth at high poll rates while
        still making the latest values available to external consumers.
        """
        assert self._registry is not None  # guarded by caller

        try:
            os.makedirs(self._export_dir, exist_ok=True)
            file_path = os.path.join(self._export_dir, "snapshot_latest.json")
            json_str = self._registry.to_json()
            Path(file_path).write_text(json_str, encoding="utf-8")
            log.debug("Snapshot exported to '%s'", file_path)
        except Exception as exc:  # noqa: BLE001
            log.warning("JSON export failed: %s", exc)


# ===========================================================================
# Signal handling
# ===========================================================================

_app_instance: Optional[PLCApplication] = None


def _signal_handler(signum: int, _frame: object) -> None:
    """Handle SIGINT / SIGTERM for clean shutdown."""
    log.warning("Signal %d received – initiating shutdown …", signum)
    if _app_instance is not None:
        _app_instance.stop()


# ===========================================================================
# Entry point
# ===========================================================================

def main() -> None:
    global _app_instance  # noqa: PLW0603

    args = _parse_args()

    # Initialise logging first.
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    setup_logger(log_level=log_level, log_file=args.log_file)

    # Re-obtain logger after setup (handlers are now attached).
    global log  # noqa: PLW0603
    log = get_logger(__name__)

    # Register signal handlers for clean shutdown.
    signal.signal(signal.SIGINT, _signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _signal_handler)

    app = PLCApplication(
        config_path=args.config,
        poll_interval=args.poll_interval,
        demo_writes=args.demo_writes,
        export_json=args.export_json,
        export_dir=args.export_dir,
    )
    _app_instance = app

    try:
        app.start()
    except KeyboardInterrupt:
        log.warning("KeyboardInterrupt received")
    except XMLConfigError as exc:
        log.critical("Configuration error: %s", exc)
        sys.exit(1)
    except PLCADSBaseError as exc:
        log.critical("Fatal PLC error: %s", exc, exc_info=True)
        sys.exit(2)
    except Exception as exc:  # noqa: BLE001
        log.critical("Unhandled exception: %s", exc, exc_info=True)
        sys.exit(3)
    finally:
        app.stop()


if __name__ == "__main__":
    main()
