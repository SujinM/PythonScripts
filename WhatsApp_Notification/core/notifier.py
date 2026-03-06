"""
Notifier — the central message dispatcher.

Responsibilities:
  - Accept TriggerEvents from the Scheduler.
  - Format the message body using the configured template.
  - Deliver to every recipient via the injected notification service.
  - Collect and expose delivery metrics.

This class is intentionally thin: it does no scheduling, no trigger
evaluation — just formatting and delivery.  This satisfies SRP and
makes unit-testing trivial.
"""

from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass, field
from typing import List

from services.base_service import BaseNotificationService, SendResult, SendStatus
from triggers.base_trigger import TriggerEvent
from utils.config_loader import NotificationConfig, WhatsAppConfig
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DeliveryRecord:
    """Immutable record of a single message delivery attempt."""

    timestamp: datetime
    to: str
    message: str
    result: SendResult
    trigger_source: str


@dataclass
class NotifierStats:
    """Running counters updated after every dispatch."""

    total_dispatched: int = 0
    total_succeeded: int = 0
    total_failed: int = 0
    records: List[DeliveryRecord] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_dispatched == 0:
            return 0.0
        return self.total_succeeded / self.total_dispatched * 100


class Notifier:
    """
    Formats events and delivers notifications to all configured recipients.

    Args:
        service:     Concrete notification service (Twilio, CloudAPI, …).
        wa_config:   WhatsApp config (provides the recipient list).
        notif_config: Notification config (provides the message template).
    """

    def __init__(
        self,
        service: BaseNotificationService,
        wa_config: WhatsAppConfig,
        notif_config: NotificationConfig,
    ) -> None:
        self._service = service
        self._recipients = wa_config.to_numbers
        self._template = notif_config.message_template
        self.stats = NotifierStats()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def dispatch(self, event: TriggerEvent) -> None:
        """
        Send a notification for the given TriggerEvent to all recipients.

        Args:
            event: The TriggerEvent produced by a trigger.
        """
        body = self._format_message(event)
        logger.info(
            "Dispatching notification from '%s' to %d recipient(s).",
            event.source,
            len(self._recipients),
        )

        for recipient in self._recipients:
            self.stats.total_dispatched += 1
            result = self._service.send_message(to=recipient, body=body)

            record = DeliveryRecord(
                timestamp=datetime.now(),
                to=recipient,
                message=body,
                result=result,
                trigger_source=event.source,
            )
            self.stats.records.append(record)

            if result.ok:
                self.stats.total_succeeded += 1
                logger.info(
                    "✓ Delivered to %s | provider_id=%s",
                    recipient,
                    result.provider_id,
                )
            else:
                self.stats.total_failed += 1
                logger.error(
                    "✗ Failed to deliver to %s | error=%s",
                    recipient,
                    result.error,
                )

    def log_stats(self) -> None:
        """Log a summary of all delivery attempts since startup."""
        logger.info(
            "Notifier stats — dispatched: %d | succeeded: %d | failed: %d | "
            "success rate: %.1f%%",
            self.stats.total_dispatched,
            self.stats.total_succeeded,
            self.stats.total_failed,
            self.stats.success_rate,
        )

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _format_message(self, event: TriggerEvent) -> str:
        """
        Render the message body using the configured template.

        Supported placeholders:
          {timestamp}  — ISO timestamp of the event
          {message}    — Event's message string
          {source}     — Trigger source label
          {severity}   — Severity level
        """
        try:
            return self._template.format(
                timestamp=event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                message=event.message,
                source=event.source,
                severity=event.severity,
            )
        except KeyError as exc:
            logger.warning("Unknown template placeholder %s — using raw message.", exc)
            return event.message
