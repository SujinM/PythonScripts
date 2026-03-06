"""
Scheduler — the heartbeat of the notification system.

The Scheduler runs a tight polling loop at a configurable tick interval
(default 30 s).  On each tick it asks the TriggerManager whether any
triggers have fired, and for each fired event it asks the Notifier to
dispatch the notification.

Design goals:
  - Never block indefinitely (SIGINT / SIGTERM safe).
  - Isolate crashes inside a single tick so the loop keeps running.
  - Cross-platform: uses threading.Event for clean shutdown on all OSes.
"""

from __future__ import annotations

import signal
import threading
import time
from typing import Optional

from core.notifier import Notifier
from core.trigger_manager import TriggerManager
from utils.logger import get_logger

logger = get_logger(__name__)


class Scheduler:
    """
    Polling scheduler that drives the trigger-check / notify cycle.

    Args:
        trigger_manager: Pre-populated TriggerManager.
        notifier:        Configured Notifier instance.
        tick_seconds:    How often (in seconds) to poll triggers.
                         Default 30 s (sub-minute resolution while still
                         being light on CPU).
    """

    def __init__(
        self,
        trigger_manager: TriggerManager,
        notifier: Notifier,
        tick_seconds: int = 30,
    ) -> None:
        self._trigger_manager = trigger_manager
        self._notifier = notifier
        self._tick_seconds = max(1, tick_seconds)
        self._stop_event = threading.Event()
        self._tick_count = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """
        Start the blocking scheduler loop.

        Registers SIGINT / SIGTERM handlers so Ctrl-C and process
        signals produce a graceful shutdown instead of a traceback.
        """
        self._register_signal_handlers()
        self._trigger_manager.setup_all()

        logger.info(
            "Scheduler started — tick interval: %d s.  Press Ctrl-C to stop.",
            self._tick_seconds,
        )

        try:
            self._run_loop()
        finally:
            self._trigger_manager.teardown_all()
            self._notifier.log_stats()
            logger.info("Scheduler stopped.")

    def stop(self) -> None:
        """Signal the scheduler loop to exit after the current tick."""
        logger.info("Shutdown requested.")
        self._stop_event.set()

    # ------------------------------------------------------------------
    # Private loop
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            tick_start = time.monotonic()
            self._tick()
            elapsed = time.monotonic() - tick_start
            sleep_for = max(0.0, self._tick_seconds - elapsed)

            # Use Event.wait() so the sleep is interruptible by stop()
            self._stop_event.wait(timeout=sleep_for)

    def _tick(self) -> None:
        """Single scheduler tick: poll all triggers and dispatch events."""
        self._tick_count += 1
        logger.debug("Tick #%d", self._tick_count)

        try:
            events = self._trigger_manager.poll()
        except Exception as exc:  # noqa: BLE001
            logger.error("Error during trigger poll (tick #%d): %s", self._tick_count, exc)
            return

        for event in events:
            try:
                self._notifier.dispatch(event)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Error dispatching event from '%s' (tick #%d): %s",
                    event.source,
                    self._tick_count,
                    exc,
                    exc_info=True,
                )

    # ------------------------------------------------------------------
    # Signal handling
    # ------------------------------------------------------------------

    def _register_signal_handlers(self) -> None:
        """Register SIGINT and SIGTERM handlers for graceful shutdown."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, self._handle_signal)
            except (OSError, ValueError):
                # Signals can only be set from the main thread; ignore otherwise.
                pass

    def _handle_signal(self, signum: int, _frame: Optional[object]) -> None:
        sig_name = signal.Signals(signum).name
        logger.info("Received %s — initiating graceful shutdown…", sig_name)
        self.stop()
