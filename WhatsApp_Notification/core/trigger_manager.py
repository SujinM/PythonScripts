"""
TriggerManager — registry and orchestrator for all active triggers.

Responsibilities:
  - Maintain the registered trigger list.
  - Expose a single poll() method that checks every enabled trigger
    and returns fired TriggerEvents.
  - Call setup() / teardown() on managed triggers at the right times.

Design notes:
  - Depends only on BaseTrigger (DIP).
  - Open for extension: call register() to add any new trigger type
    without changing this module (OCP).
"""

from __future__ import annotations

from typing import List, Optional

from triggers.base_trigger import BaseTrigger, TriggerEvent
from utils.logger import get_logger

logger = get_logger(__name__)


class TriggerManager:
    """
    Registry that manages the lifecycle of all registered triggers.

    Usage::

        manager = TriggerManager()
        manager.register(TimeTrigger(interval_minutes=5))
        manager.register(FileTrigger(watch_path="/data"))
        manager.setup_all()

        events = manager.poll()   # call this on every scheduler tick
    """

    def __init__(self) -> None:
        self._triggers: List[BaseTrigger] = []

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, trigger: BaseTrigger) -> "TriggerManager":
        """
        Add a trigger to the managed pool.

        Returns self to support fluent chaining::

            manager.register(t1).register(t2).register(t3)
        """
        self._triggers.append(trigger)
        logger.debug("Registered trigger: %s", trigger.name)
        return self

    def unregister(self, trigger_name: str) -> bool:
        """
        Remove a trigger by name.

        Returns:
            True if a trigger was found and removed, False otherwise.
        """
        original_count = len(self._triggers)
        self._triggers = [t for t in self._triggers if t.name != trigger_name]
        removed = len(self._triggers) < original_count
        if removed:
            logger.info("Unregistered trigger: %s", trigger_name)
        return removed

    @property
    def trigger_names(self) -> List[str]:
        """Names of all currently registered triggers."""
        return [t.name for t in self._triggers]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def setup_all(self) -> None:
        """Call setup() on every registered trigger."""
        logger.info(
            "Setting up %d trigger(s): %s",
            len(self._triggers),
            ", ".join(self.trigger_names),
        )
        for trigger in self._triggers:
            try:
                trigger.setup()
            except Exception as exc:  # noqa: BLE001
                logger.error("Error during setup of '%s': %s", trigger.name, exc)

    def teardown_all(self) -> None:
        """Call teardown() on every registered trigger (LIFO order)."""
        logger.info("Tearing down all triggers…")
        for trigger in reversed(self._triggers):
            try:
                trigger.teardown()
            except Exception as exc:  # noqa: BLE001
                logger.error("Error during teardown of '%s': %s", trigger.name, exc)

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    def poll(self) -> List[TriggerEvent]:
        """
        Evaluate all enabled triggers and return any that fired.

        Called on every scheduler tick.

        Returns:
            List of TriggerEvent objects (may be empty).
        """
        fired: List[TriggerEvent] = []

        for trigger in self._triggers:
            if not trigger.is_enabled:
                logger.debug("Skipping disabled trigger: %s", trigger.name)
                continue
            try:
                event: Optional[TriggerEvent] = trigger.check()
                if event is not None:
                    logger.info("Trigger fired: %s", event)
                    fired.append(event)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Unhandled exception in trigger '%s': %s",
                    trigger.name,
                    exc,
                    exc_info=True,
                )

        return fired
