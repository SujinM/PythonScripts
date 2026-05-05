"""
Upstox Analytics Token HTTP client.

The Analytics Token is a long-lived (1-year), read-only credential generated
directly from the Upstox Developer Apps page — no OAuth2 redirect required.

Supported APIs (read-only market data only):
    Full market quotes      /v2/market-quote/quotes
    OHLC V3                 /v3/market-quote/ohlc
    LTP V3                  /v3/market-quote/ltp
    Historical Candle V3    /v3/historical-candle/{key}/{interval}/{to}/{from}
    Market Data Feed Auth   /v3/feed/market-data-feed/authorize
    Brokerage               /v2/charges/brokerage
    Market Status           /v2/market/status
    Option Chain            /v2/option/chain
    Option Contracts        /v2/option/contract
    Margin                  /v2/charges/margin
    Option Greeks           /v2/option/greeks
    Instrument Search       /v3/instruments/search

RESTRICTIONS:
    - Cannot place, modify, or cancel orders.
    - Cannot access positions, holdings, funds, profile, or trade history.
    - One token per account; valid for 1 year.
    - Never share or log this token.
"""

from typing import Any, Optional, Union

from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from upstox_app.core.config import Config
from upstox_app.core.logger import get_logger

logger = get_logger(__name__)

_REQUEST_TIMEOUT = 30
_RETRY_TOTAL = 3
_RETRY_BACKOFF = 0.5
_RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AnalyticsTokenError(EnvironmentError):
    """
    Raised when UPSTOX_ANALYTICS_TOKEN is absent.

    Resolution: generate one from the Upstox Developer Apps page and add
    UPSTOX_ANALYTICS_TOKEN=<value> to your .env file.
    """


class AnalyticsAPIError(Exception):
    """Raised when the Analytics API returns a non-2xx HTTP status."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"Analytics API error [{status_code}]: {message}")


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class AnalyticsClient:
    """
    Read-only HTTP client for Upstox Analytics APIs.

    Inject this into :class:`~app.services.analytics_service.AnalyticsService`
    rather than instantiating it inside the service, keeping the service
    independently testable.

    Args:
        config: Application config.  ``UPSTOX_ANALYTICS_TOKEN`` must be set.

    Raises:
        AnalyticsTokenError: If the analytics token is absent.

    Example::

        config = Config()
        client = AnalyticsClient(config)
        data = client.get("/v3/market-quote/ltp", params={"instrument_key": "NSE_EQ|INE009A01021"})
    """

    def __init__(self, config: Config) -> None:
        token = config.analytics_token
        if not token:
            raise AnalyticsTokenError(
                "UPSTOX_ANALYTICS_TOKEN is not set.\n"
                "Generate your Analytics Token from the Upstox Developer Apps page "
                "and add it to your .env file:\n"
                "  UPSTOX_ANALYTICS_TOKEN=<your-token>"
            )
        self._token = token
        self._base_url = config.analytics_base_url
        self._session: Session = self._build_session()

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------

    @staticmethod
    def _build_session() -> Session:
        """Create a requests Session with automatic exponential-backoff retries."""
        session = Session()
        retry = Retry(
            total=_RETRY_TOTAL,
            backoff_factor=_RETRY_BACKOFF,
            status_forcelist=list(_RETRY_STATUS_CODES),
            allowed_methods={"GET", "POST"},
            raise_on_status=False,
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))
        return session

    # ------------------------------------------------------------------
    # Auth header
    # ------------------------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        """Return Authorization header with the Analytics Token."""
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # HTTP methods
    # ------------------------------------------------------------------

    def get(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Perform an authenticated GET request.

        Args:
            path:   Full versioned API path, e.g. ``/v3/market-quote/ltp``.
            params: Optional query-string parameters.

        Returns:
            Parsed JSON response body.

        Raises:
            AnalyticsAPIError: For any non-2xx HTTP response.
        """
        url = f"{self._base_url}{path}"
        logger.debug("Analytics GET %s  params=%s", path, params)
        response = self._session.get(
            url,
            headers=self._auth_headers(),
            params=params,
            timeout=_REQUEST_TIMEOUT,
        )
        self._raise_for_status(response)
        return response.json()

    def post(
        self,
        path: str,
        body: Optional[Union[dict[str, Any], list[Any]]] = None,
    ) -> dict[str, Any]:
        """
        Perform an authenticated POST request.

        Args:
            path: Full versioned API path, e.g. ``/v2/charges/margin``.
            body: Optional JSON body (dict or list).

        Returns:
            Parsed JSON response body.

        Raises:
            AnalyticsAPIError: For any non-2xx HTTP response.
        """
        url = f"{self._base_url}{path}"
        logger.debug("Analytics POST %s", path)
        response = self._session.post(
            url,
            headers=self._auth_headers(),
            json=body,
            timeout=_REQUEST_TIMEOUT,
        )
        self._raise_for_status(response)
        return response.json()

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    @staticmethod
    def _raise_for_status(response: Response) -> None:
        """Raise :class:`AnalyticsAPIError` for non-2xx responses."""
        if response.status_code < 400:
            return
        try:
            payload = response.json()
            message = payload.get("message") or payload.get("error") or response.reason
        except Exception:
            message = response.reason or "Unknown error"
        raise AnalyticsAPIError(response.status_code, message)
