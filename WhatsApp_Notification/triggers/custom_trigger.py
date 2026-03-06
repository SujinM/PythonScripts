"""
Custom / user-defined trigger template.

This module provides two things:

1. ``CustomTrigger`` — a ready-made trigger base that users extend to
   implement their own condition checks without touching any other module.

2. ``ThresholdTrigger`` — a concrete example that fires when a numeric
   value crosses a configurable threshold.  It demonstrates how PLC alarms,
   sensor alerts, database values, or any other custom signal can be plugged
   into the notification pipeline.

How to add your own trigger
---------------------------
1. Subclass ``CustomTrigger`` (or BaseTrigger directly).
2. Override ``name`` and ``check()``.
3. Register the instance in ``triggers/__init__.py`` or in ``main.py``.

That's it — no other file needs to change (Open/Closed Principle).
"""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Any, Callable, Optional

from triggers.base_trigger import BaseTrigger, TriggerEvent
from utils.logger import get_logger

logger = get_logger(__name__)


class CustomTrigger(BaseTrigger):
    """
    Convenience base class for user-defined triggers.

    Provides common state management (enable/disable, cooldown) so
    concrete subclasses only need to focus on their detection logic.

    Args:
        cooldown_seconds: Minimum seconds between consecutive events to
                          prevent notification floods.  Default is 60 s.
    """

    def __init__(self, cooldown_seconds: int = 60) -> None:
        self._cooldown_seconds = cooldown_seconds
        self._last_event_time: Optional[datetime] = None
        self._enabled: bool = True

    # ------------------------------------------------------------------
    # Enable / disable at runtime
    # ------------------------------------------------------------------

    def enable(self) -> None:
        self._enabled = True
        logger.info("%s enabled.", self.name)

    def disable(self) -> None:
        self._enabled = False
        logger.info("%s disabled.", self.name)

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    # ------------------------------------------------------------------
    # BaseTrigger requires concrete check() — delegate to _evaluate()
    # ------------------------------------------------------------------

    def check(self) -> Optional[TriggerEvent]:
        if not self._enabled:
            return None

        if self._is_in_cooldown():
            elapsed = (datetime.now() - self._last_event_time).total_seconds()
            remaining = self._cooldown_seconds - elapsed
            logger.debug(
                "%s in cooldown — %.0f s remaining.", self.name, remaining
            )
            return None

        event = self._evaluate()
        if event is not None:
            self._last_event_time = datetime.now()

        return event

    @abstractmethod
    def _evaluate(self) -> Optional[TriggerEvent]:
        """
        Implement your trigger logic here.

        Returns:
            TriggerEvent if the condition is met, else None.
        """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_in_cooldown(self) -> bool:
        if self._last_event_time is None:
            return False
        elapsed = (datetime.now() - self._last_event_time).total_seconds()
        return elapsed < self._cooldown_seconds


# ---------------------------------------------------------------------------
# Example concrete custom trigger: threshold-based numeric check
# ---------------------------------------------------------------------------


class ThresholdTrigger(CustomTrigger):
    """
    Fires when a numeric value returned by a getter function exceeds
    (or falls below) a configured threshold.

    Typical use-cases:
      - PLC register value alarm
      - CPU / memory usage alert
      - Raspberry Pi ADC / sensor reading
      - Database row count threshold
      - Queue depth monitoring

    Args:
        name_label:    Display name shown in logs and event messages.
        value_getter:  Zero-argument callable that returns the current value.
        threshold:     Numeric boundary.
        above:         If True, fire when value >= threshold (default).
                       If False, fire when value <= threshold.
        unit:          Optional unit label (e.g. "°C", "%", "items").
        cooldown_seconds: Minimum interval between repeated alerts.

    Example::

        import psutil

        cpu_trigger = ThresholdTrigger(
            name_label="CPUAlert",
            value_getter=lambda: psutil.cpu_percent(interval=1),
            threshold=85.0,
            above=True,
            unit="%",
            cooldown_seconds=120,
        )
    """

    def __init__(
        self,
        name_label: str,
        value_getter: Callable[[], Any],
        threshold: float,
        above: bool = True,
        unit: str = "",
        cooldown_seconds: int = 60,
    ) -> None:
        super().__init__(cooldown_seconds=cooldown_seconds)
        self._name_label = name_label
        self._value_getter = value_getter
        self._threshold = threshold
        self._above = above
        self._unit = unit

    @property
    def name(self) -> str:
        return self._name_label

    def setup(self) -> None:
        logger.info(
            "%s initialised — threshold: %s%s (%s).",
            self.name,
            self._threshold,
            self._unit,
            "above" if self._above else "below",
        )

    def _evaluate(self) -> Optional[TriggerEvent]:
        try:
            value = float(self._value_getter())
        except Exception as exc:  # noqa: BLE001
            logger.error("%s error reading value: %s", self.name, exc)
            return None

        condition_met = (value >= self._threshold) if self._above else (value <= self._threshold)

        if condition_met:
            direction = ">=" if self._above else "<="
            message = (
                f"{self.name}: value {value}{self._unit} "
                f"{direction} threshold {self._threshold}{self._unit}"
            )
            logger.warning("%s fired: %s", self.name, message)
            return TriggerEvent(
                source=self.name,
                message=message,
                severity="WARNING",
                timestamp=datetime.now(),
                metadata={
                    "value": value,
                    "threshold": self._threshold,
                    "unit": self._unit,
                },
            )

        logger.debug(
            "%s: value=%s%s, threshold=%s%s — condition not met.",
            self.name, value, self._unit, self._threshold, self._unit,
        )
        return None


# ---------------------------------------------------------------------------
# Lambda-based one-liner trigger for quick prototypes
# ---------------------------------------------------------------------------


class LambdaTrigger(CustomTrigger):
    """
    Wrap an arbitrary callable as a trigger — useful for quick prototypes
    and unit tests without creating a full subclass.

    Args:
        name_label:   Display name.
        condition_fn: Zero-arg callable returning (bool, message_str).
        severity:     Event severity when condition is True.
        cooldown_seconds: Flood protection interval.

    Example::

        from pathlib import Path

        sentinel = LambdaTrigger(
            name_label="SentinelFileTrigger",
            condition_fn=lambda: (
                Path("/tmp/alert.flag").exists(),
                "Sentinel file /tmp/alert.flag detected.",
            ),
            severity="ERROR",
        )
    """

    def __init__(
        self,
        name_label: str,
        condition_fn: Callable[[], tuple[bool, str]],
        severity: str = "WARNING",
        cooldown_seconds: int = 60,
    ) -> None:
        super().__init__(cooldown_seconds=cooldown_seconds)
        self._name_label = name_label
        self._condition_fn = condition_fn
        self._severity = severity

    @property
    def name(self) -> str:
        return self._name_label

    def _evaluate(self) -> Optional[TriggerEvent]:
        try:
            fired, message = self._condition_fn()
        except Exception as exc:  # noqa: BLE001
            logger.error("%s condition function raised: %s", self.name, exc)
            return None

        if fired:
            return TriggerEvent(
                source=self.name,
                message=message,
                severity=self._severity,
                timestamp=datetime.now(),
            )
        return None
