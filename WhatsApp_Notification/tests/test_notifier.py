"""
Unit tests for Notifier.
"""

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.notifier import Notifier
from services.base_service import SendResult, SendStatus
from triggers.base_trigger import TriggerEvent
from utils.config_loader import NotificationConfig, WhatsAppConfig


def _make_wa_config(to_numbers=None):
    return WhatsAppConfig(
        provider="twilio",
        account_sid="ACtest",
        auth_token="token",
        from_number="whatsapp:+14155238886",
        to_numbers=to_numbers or ["whatsapp:+1111111111"],
    )


def _make_notif_config(template="[{severity}] {source}: {message}"):
    return NotificationConfig(
        interval_minutes=5,
        retry_attempts=3,
        retry_delay_seconds=10,
        message_template=template,
    )


def _make_event(message="Test message", source="TestTrigger", severity="INFO"):
    return TriggerEvent(
        source=source,
        message=message,
        severity=severity,
        timestamp=datetime(2026, 3, 6, 12, 0, 0),
    )


class TestNotifier:
    def test_dispatch_calls_service_for_each_recipient(self):
        mock_service = MagicMock()
        mock_service.send_message.return_value = SendResult(
            status=SendStatus.SUCCESS, provider_id="SID123"
        )

        notifier = Notifier(
            service=mock_service,
            wa_config=_make_wa_config(["whatsapp:+111", "whatsapp:+222"]),
            notif_config=_make_notif_config(),
        )
        notifier.dispatch(_make_event())

        assert mock_service.send_message.call_count == 2
        assert notifier.stats.total_dispatched == 2
        assert notifier.stats.total_succeeded == 2
        assert notifier.stats.total_failed == 0

    def test_failed_delivery_increments_failed_counter(self):
        mock_service = MagicMock()
        mock_service.send_message.return_value = SendResult(
            status=SendStatus.FAILED, error="network error"
        )

        notifier = Notifier(
            service=mock_service,
            wa_config=_make_wa_config(),
            notif_config=_make_notif_config(),
        )
        notifier.dispatch(_make_event())

        assert notifier.stats.total_failed == 1
        assert notifier.stats.total_succeeded == 0

    def test_message_template_placeholders(self):
        captured = []
        mock_service = MagicMock()

        def capture(to, body):
            captured.append(body)
            return SendResult(status=SendStatus.SUCCESS)

        mock_service.send_message.side_effect = capture

        notifier = Notifier(
            service=mock_service,
            wa_config=_make_wa_config(),
            notif_config=_make_notif_config(template="[{severity}] {source}: {message}"),
        )
        notifier.dispatch(_make_event(message="Hello", source="S1", severity="WARNING"))

        assert captured[0] == "[WARNING] S1: Hello"

    def test_success_rate(self):
        mock_service = MagicMock()
        results = [
            SendResult(status=SendStatus.SUCCESS),
            SendResult(status=SendStatus.FAILED, error="err"),
            SendResult(status=SendStatus.SUCCESS),
        ]
        mock_service.send_message.side_effect = results

        notifier = Notifier(
            service=mock_service,
            wa_config=_make_wa_config(["a", "b", "c"]),
            notif_config=_make_notif_config(),
        )
        notifier.dispatch(_make_event())

        assert notifier.stats.success_rate == pytest.approx(66.67, abs=0.1)
