"""
connection_manager.py
---------------------
Manages the lifecycle of an ADS connection to a TwinCAT 3 PLC, including:

* Opening / closing the :class:`pyads.Connection`.
* An exponential back-off **auto-reconnect** loop running on a daemon thread.
* A **watchdog** (heartbeat) thread that detects silent connection drops by
  periodically reading the PLC state.
* Context-manager support (``with ConnectionManager(...) as cm: ...``).
* Full thread safety – all state mutations are serialised through a
  :class:`threading.RLock`.

Connection state machine
~~~~~~~~~~~~~~~~~~~~~~~~
::

    DISCONNECTED ──open()──► CONNECTED
         ▲                        │
         │              (link drop detected)
         │                        ▼
         │              RECONNECTING ────(max retries exceeded)──► FAILED
         └──────────────(reconnect OK)

The :class:`ConnectionState` enum is exposed so that external components (e.g.
a GUI status bar) can observe the current state via :attr:`ConnectionManager.state`.
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional

import pyads

from config.config_loader import ConnectionConfig, ReconnectConfig, HeartbeatConfig
from utils.custom_exceptions import PLCConnectionError, PLCReconnectExhaustedError
from utils.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Generator

log = get_logger(__name__)


class ConnectionState(Enum):
    """Observable connection lifecycle state."""
    DISCONNECTED  = auto()
    CONNECTED     = auto()
    RECONNECTING  = auto()
    FAILED        = auto()


class ConnectionManager:
    """
    Manages the ADS connection to a single TwinCAT 3 PLC runtime.

    Args:
        connection_cfg:  ADS transport parameters (AMS Net ID, IP, port).
        reconnect_cfg:   Reconnect / back-off strategy configuration.
        heartbeat_cfg:   Watchdog interval configuration.

    Example::

        from config.config_loader import ConfigLoader
        from core.connection_manager import ConnectionManager

        cfg = ConfigLoader.load("config/plc_config.xml")
        with ConnectionManager(
            cfg.connection, cfg.reconnect, cfg.heartbeat
        ) as cm:
            plc = cm.connection
            value = plc.read_by_name("MAIN.nSpeed", pyads.PLCTYPE_INT)
    """

    def __init__(
        self,
        connection_cfg: ConnectionConfig,
        reconnect_cfg: ReconnectConfig,
        heartbeat_cfg: HeartbeatConfig,
    ) -> None:
        self._conn_cfg = connection_cfg
        self._reconnect_cfg = reconnect_cfg
        self._heartbeat_cfg = heartbeat_cfg

        # The underlying pyads Connection object.
        self._plc: Optional[pyads.Connection] = None
        self._lock: threading.RLock = threading.RLock()

        # Observable state.
        self._state: ConnectionState = ConnectionState.DISCONNECTED

        # Reconnect bookkeeping.
        self._reconnect_thread: Optional[threading.Thread] = None
        self._stop_reconnect_event: threading.Event = threading.Event()

        # Watchdog bookkeeping.
        self._watchdog_thread: Optional[threading.Thread] = None
        self._stop_watchdog_event: threading.Event = threading.Event()

        log.debug(
            "ConnectionManager created for %s (port %d)",
            self._conn_cfg.ams_net_id,
            self._conn_cfg.port,
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> ConnectionState:
        """Current connection state (thread-safe read)."""
        with self._lock:
            return self._state

    @property
    def connection(self) -> pyads.Connection:
        """
        The active :class:`pyads.Connection`.

        Raises:
            PLCConnectionError: When the connection is not currently open.
        """
        with self._lock:
            if self._plc is None or self._state != ConnectionState.CONNECTED:
                raise PLCConnectionError(
                    f"ADS connection to {self._conn_cfg.ams_net_id} is not open "
                    f"(state: {self._state.name}). Call open() first.",
                    ams_net_id=self._conn_cfg.ams_net_id,
                    ip_address=self._conn_cfg.ip_address,
                )
            return self._plc

    @property
    def is_connected(self) -> bool:
        """``True`` when the ADS connection is established and healthy."""
        return self.state == ConnectionState.CONNECTED

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def open(self) -> None:
        """
        Open the ADS connection.

        Configures the AMS Net ID route on the local AMS router, creates a
        :class:`pyads.Connection`, and starts the watchdog thread.

        Raises:
            PLCConnectionError: If the connection cannot be established.
        """
        with self._lock:
            if self._state == ConnectionState.CONNECTED:
                log.warning("open() called but connection is already established")
                return
            self._do_open()

    def close(self) -> None:
        """
        Gracefully close the ADS connection and stop all background threads.

        Safe to call even when not connected.
        """
        log.info("Closing ADS connection to %s", self._conn_cfg.ams_net_id)
        self._stop_watchdog()
        self._stop_reconnect_loop()

        with self._lock:
            self._do_close()
            self._state = ConnectionState.DISCONNECTED

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "ConnectionManager":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @contextmanager
    def managed_connection(self) -> "Generator[pyads.Connection, None, None]":
        """
        Context manager that yields the raw :class:`pyads.Connection`.

        Use this as a shorthand when you only need the connection object::

            with cm.managed_connection() as plc:
                value = plc.read_by_name("MAIN.nSpeed", pyads.PLCTYPE_INT)
        """
        with self:
            yield self.connection

    # ------------------------------------------------------------------
    # Internal open / close helpers (must be called with _lock held or
    # from a context where only one thread is active for these methods)
    # ------------------------------------------------------------------

    def _do_open(self) -> None:
        """Attempt a single connection open (called with _lock held)."""
        ams_id = self._conn_cfg.ams_net_id
        ip = self._conn_cfg.ip_address
        port = self._conn_cfg.port

        log.info("Opening ADS connection: AMS=%s IP=%s Port=%d", ams_id, ip, port)
        try:
            # Add the AMS Net ID route so pyads can reach the PLC.
            pyads.add_route(ams_id, ip)
        except Exception as exc:  # noqa: BLE001
            # add_route may raise if the route already exists; safe to ignore.
            log.debug("add_route result: %s", exc)

        try:
            plc = pyads.Connection(ams_id, port, ip_address=ip)
            plc.open()
        except pyads.ADSError as exc:
            raise PLCConnectionError(
                f"Failed to open ADS connection to {ams_id}: {exc}",
                ams_net_id=ams_id,
                ip_address=ip,
            ) from exc
        except Exception as exc:
            raise PLCConnectionError(
                f"Unexpected error opening ADS connection to {ams_id}: {exc}",
                ams_net_id=ams_id,
                ip_address=ip,
            ) from exc

        self._plc = plc
        self._state = ConnectionState.CONNECTED
        log.info("ADS connection established: AMS=%s Port=%d", ams_id, port)

        # Start watchdog *after* the connection is open.
        self._start_watchdog()

    def _do_close(self) -> None:
        """Close the pyads Connection (called with _lock held)."""
        if self._plc is not None:
            try:
                self._plc.close()
                log.info("ADS connection closed: AMS=%s", self._conn_cfg.ams_net_id)
            except Exception as exc:  # noqa: BLE001
                log.warning("Exception while closing ADS connection: %s", exc)
            finally:
                self._plc = None

    # ------------------------------------------------------------------
    # Watchdog
    # ------------------------------------------------------------------

    def _start_watchdog(self) -> None:
        """Start the heartbeat / watchdog daemon thread."""
        self._stop_watchdog_event.clear()
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            name="plc-watchdog",
            daemon=True,
        )
        self._watchdog_thread.start()
        log.debug("Watchdog thread started (interval=%ds)", self._heartbeat_cfg.interval_seconds)

    def _stop_watchdog(self) -> None:
        """Signal and join the watchdog thread."""
        self._stop_watchdog_event.set()
        if self._watchdog_thread and self._watchdog_thread.is_alive():
            self._watchdog_thread.join(timeout=self._heartbeat_cfg.interval_seconds + 2)
        self._watchdog_thread = None

    def _watchdog_loop(self) -> None:
        """
        Daemon loop that periodically verifies the ADS connection is alive
        by reading the PLC state register.  Triggers reconnect on failure.
        """
        interval = self._heartbeat_cfg.interval_seconds
        while not self._stop_watchdog_event.wait(timeout=interval):
            with self._lock:
                plc = self._plc
                state = self._state

            if state != ConnectionState.CONNECTED or plc is None:
                continue  # Nothing to check.

            try:
                plc.read_state()  # Lightweight ADS read – checks link health.
                log.debug("Watchdog: PLC heartbeat OK")
            except Exception as exc:  # noqa: BLE001
                log.warning("Watchdog: heartbeat failed – %s. Initiating reconnect.", exc)
                self._trigger_reconnect()

    # ------------------------------------------------------------------
    # Reconnect
    # ------------------------------------------------------------------

    def _trigger_reconnect(self) -> None:
        """Mark the connection as lost and start the reconnect loop."""
        with self._lock:
            if self._state in (ConnectionState.RECONNECTING, ConnectionState.FAILED):
                return  # Already in progress.
            self._do_close()
            self._state = ConnectionState.RECONNECTING

        self._stop_watchdog()
        self._start_reconnect_loop()

    def _start_reconnect_loop(self) -> None:
        """Spawn the reconnect background thread."""
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return  # Loop already running.

        self._stop_reconnect_event.clear()
        self._reconnect_thread = threading.Thread(
            target=self._reconnect_loop,
            name="plc-reconnect",
            daemon=True,
        )
        self._reconnect_thread.start()
        log.debug("Reconnect thread started")

    def _stop_reconnect_loop(self) -> None:
        """Signal and join the reconnect thread."""
        self._stop_reconnect_event.set()
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            total = self._reconnect_cfg.max_delay_seconds + 2
            self._reconnect_thread.join(timeout=total)
        self._reconnect_thread = None

    def _reconnect_loop(self) -> None:
        """
        Exponential back-off reconnect loop running on a background thread.

        Strategy:
        * Start with ``initial_delay_seconds``.
        * Multiply the delay by ``backoff_multiplier`` after each failure.
        * Cap at ``max_delay_seconds``.
        * Stop after ``max_attempts`` (0 = unlimited).
        """
        cfg = self._reconnect_cfg
        delay = cfg.initial_delay_seconds
        attempt = 0

        while not self._stop_reconnect_event.is_set():
            attempt += 1
            log.warning(
                "Reconnect attempt %d/%s to %s in %.1fs …",
                attempt,
                cfg.max_attempts or "∞",
                self._conn_cfg.ams_net_id,
                delay,
            )

            # Wait before retrying (interruptible).
            interrupted = self._stop_reconnect_event.wait(timeout=delay)
            if interrupted:
                log.info("Reconnect loop interrupted during back-off wait")
                break

            try:
                with self._lock:
                    self._do_open()

                # Success – restart watchdog and exit the loop.
                log.info("Reconnected to %s after %d attempt(s)", self._conn_cfg.ams_net_id, attempt)
                return

            except PLCConnectionError as exc:
                log.warning("Reconnect attempt %d failed: %s", attempt, exc)

            # Update back-off delay.
            delay = min(delay * cfg.backoff_multiplier, cfg.max_delay_seconds)

            # Check max attempts limit.
            if cfg.max_attempts > 0 and attempt >= cfg.max_attempts:
                with self._lock:
                    self._state = ConnectionState.FAILED
                raise PLCReconnectExhaustedError(
                    f"Exhausted {attempt} reconnect attempt(s) to {self._conn_cfg.ams_net_id}.",
                    attempts=attempt,
                    ams_net_id=self._conn_cfg.ams_net_id,
                    ip_address=self._conn_cfg.ip_address,
                )
