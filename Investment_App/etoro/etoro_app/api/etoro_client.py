"""
eToro Public API HTTP client.

Authentication
--------------
The eToro Public API uses two static API keys as request headers — no OAuth2
redirect or token exchange is needed:

  x-api-key   : Public API Key  (identifies the application)
  x-user-key  : User Key        (identifies the eToro account)
  x-request-id: Unique UUID     (required per-request for tracing)

Get both keys from:
  eToro account → Settings → Trading → API Key Management

Endpoints (base: https://public-api.etoro.com):
  GET /api/v1/trading/info/real/pnl              — open positions + PnL
  GET /api/v1/trading/info/trade/history         — closed trade history
  Docs: https://api-portal.etoro.com/
"""

import uuid
from typing import Any, Optional, Union

from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from etoro_app.core.config import Config
from etoro_app.core.logger import get_logger

logger = get_logger(__name__)

_REQUEST_TIMEOUT = 30
_RETRY_TOTAL = 3
_RETRY_BACKOFF = 0.5
# 500 is intentionally excluded — eToro returns 500 for genuine API errors
# (e.g. bad parameters), so retrying wastes time without benefit.
_RETRY_STATUS_CODES = frozenset({429, 502, 503, 504})


class EToroAPIError(Exception):
    """Raised when the eToro API returns a non-2xx status code."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"eToro API error [{status_code}]: {message}")


class EToroAuthError(EToroAPIError):
    """Raised for 401/403 — invalid or missing API keys."""


class EToroClient:
    """
    Low-level eToro Public API HTTP client.

    Example::

        config = Config()
        client = EToroClient(config)
        data = client.get("/api/v1/trading/info/real/pnl")
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._session: Session = self._build_session()

    @staticmethod
    def _build_session() -> Session:
        """Create a requests Session with exponential-backoff retry logic."""
        session = Session()
        retry_policy = Retry(
            total=_RETRY_TOTAL,
            backoff_factor=_RETRY_BACKOFF,
            status_forcelist=list(_RETRY_STATUS_CODES),
            allowed_methods={"GET"},
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_policy)
        session.mount("https://", adapter)
        return session

    def _build_headers(self) -> dict[str, str]:
        """
        Build the three required request headers.

        ``x-request-id`` is a fresh UUID v4 per request — required by eToro for tracing.
        """
        return {
            "x-api-key": self._config.api_key,
            "x-user-key": self._config.user_key,
            "x-request-id": str(uuid.uuid4()),
            "Accept": "application/json",
        }

    def get(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Union[dict[str, Any], list]:
        """
        Perform an authenticated GET request.

        Args:
            endpoint: API path relative to base URL,
                      e.g. ``/api/v1/trading/info/real/pnl``.
            params:   Optional query-string parameters.

        Returns:
            Parsed JSON response body (dict or list depending on endpoint).

        Raises:
            EToroAPIError:  For any non-2xx response.
            EToroAuthError: For 401/403 (invalid or expired API keys).
        """
        url = f"{self._config.base_url}{endpoint}"
        logger.debug("GET %s  params=%s", endpoint, params)
        response = self._session.get(
            url,
            headers=self._build_headers(),
            params=params,
            timeout=_REQUEST_TIMEOUT,
        )
        self._raise_for_status(response)
        return response.json()

    @staticmethod
    def _raise_for_status(response: Response) -> None:
        """Raise a typed exception for non-2xx responses."""
        if response.status_code < 400:
            return

        # Log the raw response body so callers can diagnose errors
        raw_body = response.text[:500] if response.text else "<empty>"
        logger.debug("API error body [%s]: %s", response.status_code, raw_body)

        try:
            payload = response.json()
            message = (
                payload.get("message")
                or payload.get("error_description")
                or payload.get("error")
                or response.reason
            )
        except Exception:
            message = response.reason or "Unknown error"

        if message == response.reason:
            # Include the raw body in the exception so it surfaces in logs
            message = f"{message} — {raw_body}"

        if response.status_code in (401, 403):
            raise EToroAuthError(response.status_code, message)

        raise EToroAPIError(response.status_code, message)
