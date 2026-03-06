"""
Abstract base class for all notification delivery services.

Concrete services (Twilio, WhatsApp Cloud API, SMTP, Slack, …) implement
send_message(). The rest of the application depends only on this interface,
making it trivial to swap or add providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class SendStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


@dataclass
class SendResult:
    """
    Value-object returned by every send_message() call.

    Attributes:
        status:     Outcome of the send attempt.
        provider_id: Optional message-ID or SID returned by the provider.
        error:       Error description when status is FAILED.
    """

    status: SendStatus
    provider_id: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.status == SendStatus.SUCCESS

    def __str__(self) -> str:
        if self.ok:
            return f"SendResult(SUCCESS, id={self.provider_id!r})"
        return f"SendResult(FAILED, error={self.error!r})"


class BaseNotificationService(ABC):
    """
    Pluggable notification service interface.

    Implement this class to add any delivery channel (WhatsApp, SMS,
    email, Slack, PagerDuty, …) without changing any other module.

    Subclass contract:
      - ``send_message(to, body)``  — single delivery.
      - ``name``                    — short provider identifier for logs.
      - ``validate_config()``       — raise ValueError when credentials
                                       are incomplete / invalid format.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short label that appears in all log messages (e.g. 'Twilio')."""

    @abstractmethod
    def validate_config(self) -> None:
        """
        Validate credentials and configuration at startup.

        Raises:
            ValueError: If required configuration is missing or malformed.
        """

    @abstractmethod
    def send_message(self, to: str, body: str) -> SendResult:
        """
        Deliver a single message to the given recipient.

        Args:
            to:   Recipient identifier (phone number, e-mail, channel ID…).
            body: Plain-text message body.

        Returns:
            SendResult describing the outcome.
        """
