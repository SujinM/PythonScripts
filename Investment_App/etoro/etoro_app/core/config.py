"""
Configuration loader.

Reads settings from a .env file (or OS environment variables) using python-dotenv.
Validates that all required keys are present before the application starts.

eToro Public API authentication uses two static API keys obtained from:
    eToro account → Settings → Trading → API Key Management

Usage:
    from etoro_app.core.config import Config
    config = Config()          # auto-discovers .env in project root
    config = Config(".env")    # explicit path
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Project root is three levels up from this file:
#   app/core/config.py  ->  app/core  ->  app  ->  project root
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class ConfigError(EnvironmentError):
    """Raised when required environment variables are absent or invalid."""


class Config:
    """
    Central, immutable configuration object.

    All secrets are read from environment variables — never from hardcoded
    values in source code.  Store your secrets in a .env file that is listed
    in .gitignore and NEVER committed to version control.

    Authentication
    --------------
    The eToro Public API uses two API keys sent as request headers:
      - ``x-api-key``  : Public API Key   (identifies your application)
      - ``x-user-key`` : User Key         (identifies your eToro account)

    Both keys are available at:
      eToro account → Settings → Trading → API Key Management
    """

    _REQUIRED: tuple[str, ...] = (
        "ETORO_API_KEY",
        "ETORO_USER_KEY",
    )

    def __init__(self, env_file: str | None = None) -> None:
        env_path = Path(env_file) if env_file else _PROJECT_ROOT / ".env"
        load_dotenv(env_path, override=False)
        self._validate()

    def _validate(self) -> None:
        """Raise ConfigError if any required variable is missing."""
        missing = [k for k in self._REQUIRED if not os.getenv(k)]
        if missing:
            raise ConfigError(
                f"Missing required environment variables: {', '.join(missing)}.\n"
                "Copy .env.example to .env and fill in your credentials.\n"
                "Get your keys from: eToro account → Settings → Trading → API Key Management"
            )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def api_key(self) -> str:
        """eToro Public API Key (x-api-key header) — identifies the application."""
        return os.environ["ETORO_API_KEY"]

    @property
    def user_key(self) -> str:
        """eToro User Key (x-user-key header) — identifies your eToro account."""
        return os.environ["ETORO_USER_KEY"]

    @property
    def base_url(self) -> str:
        """eToro Public API base URL."""
        return os.getenv("ETORO_BASE_URL", "https://public-api.etoro.com")

    @property
    def cache_ttl_seconds(self) -> int:
        """Time-to-live for in-memory API response cache (seconds)."""
        return int(os.getenv("CACHE_TTL_SECONDS", "300"))

    @property
    def log_level(self) -> str:
        """Application log level: DEBUG | INFO | WARNING | ERROR."""
        return os.getenv("LOG_LEVEL", "INFO").upper()
