"""
WhatsApp notification service.

Supports two providers selectable via config:
  • ``twilio``    — Twilio WhatsApp Sandbox / Business API
  • ``cloud_api`` — Meta WhatsApp Business Cloud API (v20.0)

Both implement the same BaseNotificationService interface, so swapping
providers is a one-line change in config.ini without touching any other
module.

Retry logic lives in ``RetryMixin`` and is shared by both providers.
"""

from __future__ import annotations

import json
import time
from typing import Optional
from urllib import request, error as urllib_error

from services.base_service import BaseNotificationService, SendResult, SendStatus
from utils.config_loader import WhatsAppConfig
from utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Retry mixin (SRP: extracted so it can be reused by any future service)
# ---------------------------------------------------------------------------


class _RetryMixin:
    """
    Adds retry logic to any class that sets::

        self._retry_attempts: int
        self._retry_delay: int    (seconds)
    """

    def _send_with_retry(
        self,
        to: str,
        body: str,
        _send_once,
    ) -> SendResult:
        """
        Call _send_once(to, body) up to self._retry_attempts times.

        Args:
            to:         Recipient identifier.
            body:       Message body.
            _send_once: Callable(to, body) → SendResult.

        Returns:
            Last SendResult (either SUCCESS or FAILED after all retries).
        """
        last_result: Optional[SendResult] = None

        for attempt in range(1, self._retry_attempts + 1):  # type: ignore[attr-defined]
            last_result = _send_once(to, body)
            if last_result.ok:
                if attempt > 1:
                    logger.info(
                        "Message delivered on attempt %d/%d.",
                        attempt,
                        self._retry_attempts,  # type: ignore[attr-defined]
                    )
                return last_result

            logger.warning(
                "Attempt %d/%d failed: %s",
                attempt,
                self._retry_attempts,  # type: ignore[attr-defined]
                last_result.error,
            )
            if attempt < self._retry_attempts:  # type: ignore[attr-defined]
                logger.info(
                    "Retrying in %d second(s)…",
                    self._retry_delay,  # type: ignore[attr-defined]
                )
                time.sleep(self._retry_delay)  # type: ignore[attr-defined]

        return last_result  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Twilio provider
# ---------------------------------------------------------------------------


class TwilioWhatsAppService(_RetryMixin, BaseNotificationService):
    """
    Sends WhatsApp messages via the Twilio Messaging API.

    Required config.ini fields:
        account_sid  — Twilio Account SID (starts with AC…)
        auth_token   — Twilio Auth Token
        from_number  — whatsapp:+14155238886  (or your approved number)
        to_numbers   — comma-separated whatsapp:+… numbers

    Install dependency:
        pip install twilio
    """

    _API_BASE = "https://api.twilio.com/2010-04-01"

    def __init__(
        self,
        config: WhatsAppConfig,
        retry_attempts: int = 3,
        retry_delay_seconds: int = 10,
    ) -> None:
        self._config = config
        self._retry_attempts = retry_attempts
        self._retry_delay = retry_delay_seconds

    # ------------------------------------------------------------------
    # BaseNotificationService interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "Twilio"

    def validate_config(self) -> None:
        missing = []
        if not self._config.account_sid:
            missing.append("account_sid")
        if not self._config.auth_token:
            missing.append("auth_token")
        if not self._config.from_number:
            missing.append("from_number")
        if not self._config.to_numbers:
            missing.append("to_numbers")
        if missing:
            raise ValueError(
                f"[whatsapp] Twilio provider missing required fields: {', '.join(missing)}"
            )
        if not self._config.account_sid.startswith("AC"):
            raise ValueError("[whatsapp] account_sid must start with 'AC'.")

    def send_message(self, to: str, body: str) -> SendResult:
        return self._send_with_retry(to, body, self._send_once)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _send_once(self, to: str, body: str) -> SendResult:
        """Single HTTP call to the Twilio Messages endpoint."""
        try:
            # Prefer the official SDK when available, fall back to stdlib urllib
            try:
                from twilio.rest import Client  # type: ignore[import]

                client = Client(self._config.account_sid, self._config.auth_token)
                msg = client.messages.create(
                    body=body,
                    from_=self._config.from_number,
                    to=to,
                )
                logger.info("%s: message sent — SID: %s", self.name, msg.sid)
                return SendResult(status=SendStatus.SUCCESS, provider_id=msg.sid)

            except ImportError:
                return self._send_via_urllib(to, body)

        except Exception as exc:  # noqa: BLE001
            logger.error("%s: unexpected error: %s", self.name, exc)
            return SendResult(status=SendStatus.FAILED, error=str(exc))

    def _send_via_urllib(self, to: str, body: str) -> SendResult:
        """Fallback: raw HTTP using stdlib urllib (no extra dependencies)."""
        import base64
        from urllib.parse import urlencode

        url = f"{self._API_BASE}/Accounts/{self._config.account_sid}/Messages.json"
        data = urlencode(
            {"From": self._config.from_number, "To": to, "Body": body}
        ).encode("utf-8")

        credentials = base64.b64encode(
            f"{self._config.account_sid}:{self._config.auth_token}".encode()
        ).decode("ascii")

        req = request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=15) as resp:
                payload = json.loads(resp.read().decode())
                sid = payload.get("sid", "")
                logger.info("%s: message sent (urllib) — SID: %s", self.name, sid)
                return SendResult(status=SendStatus.SUCCESS, provider_id=sid)
        except urllib_error.HTTPError as exc:
            error_body = exc.read().decode()
            logger.error("%s HTTP %d: %s", self.name, exc.code, error_body)
            return SendResult(status=SendStatus.FAILED, error=f"HTTP {exc.code}: {error_body}")
        except urllib_error.URLError as exc:
            logger.error("%s URL error: %s", self.name, exc.reason)
            return SendResult(status=SendStatus.FAILED, error=str(exc.reason))


# ---------------------------------------------------------------------------
# Meta WhatsApp Cloud API provider
# ---------------------------------------------------------------------------


class CloudAPIWhatsAppService(_RetryMixin, BaseNotificationService):
    """
    Sends WhatsApp messages via the Meta WhatsApp Business Cloud API.

    Required config.ini fields:
        account_sid  — Phone Number ID  (numeric, e.g. 123456789012345)
        auth_token   — Permanent / temporary Cloud API bearer token
        from_number  — Same as account_sid (reused for consistency)
        to_numbers   — Recipient phone numbers in E.164 format (+1415…)

    Docs: https://developers.facebook.com/docs/whatsapp/cloud-api/messages
    """

    _API_VERSION = "v20.0"

    def __init__(
        self,
        config: WhatsAppConfig,
        retry_attempts: int = 3,
        retry_delay_seconds: int = 10,
    ) -> None:
        self._config = config
        self._retry_attempts = retry_attempts
        self._retry_delay = retry_delay_seconds

    # ------------------------------------------------------------------
    # BaseNotificationService interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "CloudAPI"

    def validate_config(self) -> None:
        missing = []
        if not self._config.account_sid:
            missing.append("account_sid (Phone Number ID)")
        if not self._config.auth_token:
            missing.append("auth_token (Bearer token)")
        if not self._config.to_numbers:
            missing.append("to_numbers")
        if missing:
            raise ValueError(
                f"[whatsapp] CloudAPI provider missing required fields: {', '.join(missing)}"
            )

    def send_message(self, to: str, body: str) -> SendResult:
        return self._send_with_retry(to, body, self._send_once)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _send_once(self, to: str, body: str) -> SendResult:
        phone_number_id = self._config.account_sid
        url = (
            f"https://graph.facebook.com/{self._API_VERSION}"
            f"/{phone_number_id}/messages"
        )

        # Strip any "whatsapp:" prefix in case config re-uses Twilio format
        clean_to = to.replace("whatsapp:", "").strip()

        payload = json.dumps({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_to,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }).encode("utf-8")

        req = request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {self._config.auth_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=15) as resp:
                response_data = json.loads(resp.read().decode())
                msg_id = (
                    response_data.get("messages", [{}])[0].get("id", "")
                    if response_data.get("messages")
                    else ""
                )
                logger.info("%s: message sent — ID: %s", self.name, msg_id)
                return SendResult(status=SendStatus.SUCCESS, provider_id=msg_id)
        except urllib_error.HTTPError as exc:
            error_body = exc.read().decode()
            logger.error("%s HTTP %d: %s", self.name, exc.code, error_body)
            return SendResult(status=SendStatus.FAILED, error=f"HTTP {exc.code}: {error_body}")
        except urllib_error.URLError as exc:
            logger.error("%s URL error: %s", self.name, exc)
            return SendResult(status=SendStatus.FAILED, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.error("%s unexpected error: %s", self.name, exc)
            return SendResult(status=SendStatus.FAILED, error=str(exc))


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_whatsapp_service(
    config: WhatsAppConfig,
    retry_attempts: int = 3,
    retry_delay_seconds: int = 10,
) -> BaseNotificationService:
    """
    Factory that returns the correct WhatsApp service based on config.provider.

    Args:
        config:               WhatsApp configuration data class.
        retry_attempts:       Max send retries before giving up.
        retry_delay_seconds:  Delay between retries.

    Returns:
        Concrete BaseNotificationService instance.

    Raises:
        ValueError: If provider name is unknown.
    """
    provider = config.provider.lower().strip()

    if provider == "twilio":
        svc = TwilioWhatsAppService(config, retry_attempts, retry_delay_seconds)
    elif provider in ("cloud_api", "cloudapi", "meta"):
        svc = CloudAPIWhatsAppService(config, retry_attempts, retry_delay_seconds)
    else:
        raise ValueError(
            f"Unknown WhatsApp provider: {config.provider!r}. "
            "Valid options: 'twilio', 'cloud_api'."
        )

    svc.validate_config()
    logger.info("WhatsApp service provider: %s", svc.name)
    return svc
