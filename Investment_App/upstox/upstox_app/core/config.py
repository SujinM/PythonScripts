"""
Configuration loader.

Reads settings from a .env file (or OS environment variables) using python-dotenv.
Validates that all required keys are present before the application starts.

Usage:
    from upstox_app.core.config import Config
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
    """

    # Keys that must be present for the application to start
    _REQUIRED: tuple[str, ...] = (
        "UPSTOX_API_KEY",
        "UPSTOX_API_SECRET",
        "UPSTOX_REDIRECT_URI",
    )

    def __init__(self, env_file: str | None = None) -> None:
        """
        Load and validate configuration.

        Args:
            env_file: Optional explicit path to a .env file.
                      Defaults to <project_root>/.env.
        """
        env_path = Path(env_file) if env_file else _PROJECT_ROOT / ".env"
        # load_dotenv does NOT overwrite variables already set in the OS env
        load_dotenv(env_path, override=False)
        self._validate()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate(self) -> None:
        """Raise ConfigError if any required variable is missing."""
        missing = [k for k in self._REQUIRED if not os.getenv(k)]
        if missing:
            raise ConfigError(
                f"Missing required environment variables: {', '.join(missing)}.\n"
                "Copy .env.example to .env and fill in your credentials."
            )

    # ------------------------------------------------------------------
    # Properties — each reads directly from the process environment so
    # that tests can patch os.environ without recreating Config instances.
    # ------------------------------------------------------------------

    @property
    def api_key(self) -> str:
        """Upstox API key (client ID)."""
        return os.environ["UPSTOX_API_KEY"]

    @property
    def api_secret(self) -> str:
        """Upstox API secret (client secret)."""
        return os.environ["UPSTOX_API_SECRET"]

    @property
    def redirect_uri(self) -> str:
        """OAuth2 redirect URI registered in the Upstox developer portal."""
        return os.environ["UPSTOX_REDIRECT_URI"]

    @property
    def access_token(self) -> str | None:
        """
        Upstox access token obtained after OAuth2 authorization.
        Optional at startup — the 'auth' CLI command is used to obtain it.
        """
        return os.getenv("UPSTOX_ACCESS_TOKEN") or None

    @property
    def base_url(self) -> str:
        """Upstox API v2 base URL."""
        return os.getenv("UPSTOX_BASE_URL", "https://api.upstox.com/v2")

    @property
    def cache_ttl_seconds(self) -> int:
        """Time-to-live for in-memory API response cache (seconds)."""
        return int(os.getenv("CACHE_TTL_SECONDS", "300"))

    @property
    def log_level(self) -> str:
        """Application log level: DEBUG | INFO | WARNING | ERROR."""
        return os.getenv("LOG_LEVEL", "INFO").upper()

    # ------------------------------------------------------------------
    # Analytics Token (long-lived, read-only — no OAuth2 required)
    # ------------------------------------------------------------------

    @property
    def analytics_token(self) -> str | None:
        """
        Upstox Analytics Token (1-year validity, read-only).

        Generated from the Upstox Developer Apps page.
        Optional at startup — only required for ``python -m app analytics *`` commands.
        """
        return os.getenv("UPSTOX_ANALYTICS_TOKEN") or None

    @property
    def analytics_base_url(self) -> str:
        """
        Base URL for Analytics API calls — no version suffix.

        Analytics endpoints span both /v2/ and /v3/ paths, so the version
        is included in each endpoint path rather than the base URL.
        """
        return os.getenv("UPSTOX_ANALYTICS_BASE_URL", "https://api.upstox.com")
