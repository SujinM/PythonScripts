"""
Abstract base class for all notification triggers.

Every concrete trigger must implement check() which returns a
TriggerEvent (or None) to signal whether a notification should fire.

OCP / DIP compliance:
  - The Scheduler depends only on this interface, never on concrete triggers.
  - New trigger types are added by subclassing without touching existing code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TriggerEvent:
    """
    Immutable value-object that carries the details of a fired trigger.

    Attributes:
        source:    Identifier of the trigger that produced the event.
        message:   Human-readable description of the event.
        severity:  Severity label (INFO, WARNING, ERROR, CRITICAL).
        timestamp: Exact time the event was detected.
        metadata:  Arbitrary key/value payload for context-specific data.
    """

    source: str
    message: str
    severity: str = "INFO"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"[{self.severity}] {self.source} @ "
            f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} — {self.message}"
        )


class BaseTrigger(ABC):
    """
    Abstract base for all trigger implementations.

    Subclass contract:
      - Implement ``check()`` to inspect the condition and return a
        TriggerEvent if the trigger fires, or None otherwise.
      - Implement ``name`` property to identify the trigger in logs.
      - Optionally override ``setup()`` / ``teardown()`` for resource
        acquisition / release (e.g. opening file handles, DB connections).
    """

    def setup(self) -> None:
        """
        Called once before the scheduler starts polling.
        Override to initialise resources (file handles, connections, etc.).
        """

    def teardown(self) -> None:
        """
        Called once when the application shuts down.
        Override to release acquired resources gracefully.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable identifier for this trigger."""

    @property
    def is_enabled(self) -> bool:
        """Return False to prevent the scheduler from polling this trigger."""
        return True

    @abstractmethod
    def check(self) -> Optional[TriggerEvent]:
        """
        Evaluate the trigger condition.

        Returns:
            TriggerEvent if the condition is met and a notification
            should be sent, otherwise None.
        """
