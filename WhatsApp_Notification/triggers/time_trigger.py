"""
Time-based trigger.

Fires once per configured interval (interval_minutes in config.ini).
The trigger maintains its own last-fired timestamp so it is independent
of the scheduler frequency — the scheduler can run every 30 s while
the interval is set to 60 min and it will still fire at the right time.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from triggers.base_trigger import BaseTrigger, TriggerEvent
from utils.logger import get_logger

logger = get_logger(__name__)


class TimeTrigger(BaseTrigger):
    """
    Emits a TriggerEvent each time the specified interval elapses.

    Args:
        interval_minutes: How often (in minutes) to fire the trigger.
        message:          Custom message body to include in the event.
    """

    def __init__(self, interval_minutes: int, message: str = "Scheduled notification") -> None:
        if interval_minutes <= 0:
            raise ValueError("interval_minutes must be a positive integer.")
        self._interval = timedelta(minutes=interval_minutes)
        self._message = message
        self._last_fired: Optional[datetime] = None

    # ------------------------------------------------------------------
    # BaseTrigger interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "TimeTrigger"

    def setup(self) -> None:
        # Fire immediately on the first scheduler tick after setup
        self._last_fired = None
        logger.info(
            "%s initialised — interval: %d minute(s).",
            self.name,
            self._interval.seconds // 60,
        )

    def check(self) -> Optional[TriggerEvent]:
        now = datetime.now()

        # Fire immediately if we've never fired before
        if self._last_fired is None or (now - self._last_fired) >= self._interval:
            self._last_fired = now
            logger.debug("%s fired at %s.", self.name, now.isoformat())
            return TriggerEvent(
                source=self.name,
                message=self._message,
                severity="INFO",
                timestamp=now,
                metadata={"interval_minutes": int(self._interval.total_seconds() // 60)},
            )

        logger.debug(
            "%s: next fire in %s.",
            self.name,
            str(self._interval - (now - self._last_fired)).split(".")[0],
        )
        return None
