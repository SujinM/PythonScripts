"""
Upstox API v2 HTTP client.

Responsibilities
----------------
- Manage OAuth2 authorization code flow
- Exchange auth code for access token
- Execute authenticated GET / POST requests
- Retry on transient errors (429, 5xx)
- Raise typed exceptions for all non-2xx responses

This module contains NO business logic — it is a pure adapter layer.
Business services depend on this client via constructor injection, making
it straightforward to swap for a different broker client later.

Upstox OAuth2 references:
  Authorization URL  : https://api.upstox.com/v2/login/authorization/dialog
  Token URL (OAuth2) : https://api.upstox.com/v2/login/authorization/token
  Token URL (direct) : https://api.upstox.com/v3/login/auth/token/request/{client_id}
  API docs           : https://upstox.com/developer/api-documentation/
"""

from typing import Any, Optional
from urllib.parse import urlencode

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import Config
from app.core.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_AUTHORIZE_URL = "https://api.upstox.com/v2/login/authorization/dialog"
_TOKEN_URL = "https://api.upstox.com/v2/login/authorization/token"

_REQUEST_TIMEOUT = 30  # seconds
_RETRY_TOTAL = 3
_RETRY_BACKOFF = 0.5
_RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class UpstoxAPIError(Exception):
    """
    Raised when the Upstox API returns a non-2xx status code.

    Attributes:
        status_code: HTTP status code from the response.
    """

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"Upstox API error [{status_code}]: {message}")


class UpstoxAuthError(UpstoxAPIError):
    """Raised specifically for authentication / authorization failures."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class UpstoxClient:
    """
    Low-level Upstox API v2 client.

    Inject this into services rather than instantiating it inside them so
    that tests can mock it without patching internals.

    Example::

        config = Config()
        client = UpstoxClient(config)
        client.set_access_token(token)
        data = client.get("/portfolio/long-term-holdings")
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._access_token: Optional[str] = config.access_token
        self._session: Session = self._build_session()

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------

    @staticmethod
    def _build_session() -> Session:
        """Create a requests Session with exponential-backoff retry logic."""
        session = Session()
        retry_policy = Retry(
            total=_RETRY_TOTAL,
            backoff_factor=_RETRY_BACKOFF,
            status_forcelist=list(_RETRY_STATUS_CODES),
            allowed_methods={"GET", "POST"},
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_policy)
        session.mount("https://", adapter)
        return session

    # ------------------------------------------------------------------
    # Authentication — OAuth2 authorization code flow
    # ------------------------------------------------------------------

    def get_authorization_url(self) -> str:
        """
        Build and return the Upstox OAuth2 authorization URL.

        Open this URL in a browser.  After the user authorizes the app,
        Upstox redirects to ``redirect_uri`` with a ``code`` query parameter.
        Pass that code to :meth:`exchange_code_for_token`.
        """
        params = {
            "response_type": "code",
            "client_id": self._config.api_key,
            "redirect_uri": self._config.redirect_uri,
        }
        return f"{_AUTHORIZE_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, auth_code: str) -> str:
        """
        Exchange an authorization code for an access token.

        Args:
            auth_code: The ``code`` value from the OAuth2 redirect URL.

        Returns:
            The access token string.  Store this in UPSTOX_ACCESS_TOKEN
            in your .env file for subsequent runs.

        Raises:
            UpstoxAuthError: If the token exchange fails.
        """
        payload = {
            "code": auth_code,
            "client_id": self._config.api_key,
            "client_secret": self._config.api_secret,
            "redirect_uri": self._config.redirect_uri,
            "grant_type": "authorization_code",
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        response = self._session.post(
            _TOKEN_URL, data=payload, headers=headers, timeout=_REQUEST_TIMEOUT
        )
        self._raise_for_status(response)

        token: Optional[str] = response.json().get("access_token")
        if not token:
            raise UpstoxAuthError(response.status_code, "No access_token in response payload.")

        self._access_token = token
        logger.info("Access token obtained successfully.")
        return token

    def request_access_token(self) -> str:
        """
        Request an Access Token directly using the v3 API — no browser required.

        Calls ``POST /v3/login/auth/token/request/{client_id}`` where
        ``client_id`` is the configured ``api_key``, with ``client_secret``
        in the JSON body.

        This is a headless alternative to the OAuth2 browser redirect flow,
        useful for automation and scripts running without a browser.

        The returned token works identically to the one from
        :meth:`exchange_code_for_token`. Store it as ``UPSTOX_ACCESS_TOKEN``
        in your ``.env`` file.

        Returns:
            The access token string.

        Raises:
            UpstoxAPIError: For any non-2xx response.
        """
        url = f"https://api.upstox.com/v3/login/auth/token/request/{self._config.api_key}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {"client_secret": self._config.api_secret}

        logger.debug("Requesting Access Token via v3 direct endpoint.")
        response = self._session.post(
            url, headers=headers, json=payload, timeout=_REQUEST_TIMEOUT
        )
        self._raise_for_status(response)

        body = response.json()
        token: Optional[str] = (
            body.get("data", {}).get("access_token")
            or body.get("access_token")
            or body.get("token")
        )
        if not token:
            raise UpstoxAPIError(response.status_code, "No access_token found in response payload.")

        self._access_token = token
        logger.info("Access Token obtained via v3 direct request.")
        return token

    def set_access_token(self, token: str) -> None:
        """
        Set the access token directly (e.g., loaded from UPSTOX_ACCESS_TOKEN).

        Args:
            token: A valid Upstox access token.
        """
        self._access_token = token

    # ------------------------------------------------------------------
    # Authenticated HTTP helpers
    # ------------------------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        """Return headers required for authenticated API calls."""
        if not self._access_token:
            raise UpstoxAuthError(
                401,
                "No access token available.  Run 'upstox-analyzer auth' first "
                "or set UPSTOX_ACCESS_TOKEN in your .env file.",
            )
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }

    def get(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Perform an authenticated GET request.

        Args:
            endpoint: API path relative to base URL, e.g. ``/portfolio/long-term-holdings``.
            params:   Optional query-string parameters.

        Returns:
            Parsed JSON response body as a dict.

        Raises:
            UpstoxAPIError: For any non-2xx response.
        """
        url = f"{self._config.base_url}{endpoint}"
        logger.debug("GET %s  params=%s", endpoint, params)
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
        endpoint: str,
        body: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Perform an authenticated POST request.

        Args:
            endpoint: API path relative to base URL.
            body:     Optional JSON request body.

        Returns:
            Parsed JSON response body as a dict.

        Raises:
            UpstoxAPIError: For any non-2xx response.
        """
        url = f"{self._config.base_url}{endpoint}"
        logger.debug("POST %s", endpoint)
        response = self._session.post(
            url,
            headers=self._auth_headers(),
            json=body,
            timeout=_REQUEST_TIMEOUT,
        )
        self._raise_for_status(response)
        return response.json()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _raise_for_status(response: Response) -> None:
        """Raise a typed exception for non-2xx responses."""
        if response.status_code < 400:
            return

        # Extract the error message without leaking sensitive request data
        try:
            payload = response.json()
            message = payload.get("message") or payload.get("error") or response.reason
        except Exception:
            message = response.reason or "Unknown error"

        if response.status_code in (401, 403):
            raise UpstoxAuthError(response.status_code, message)
        raise UpstoxAPIError(response.status_code, message)
