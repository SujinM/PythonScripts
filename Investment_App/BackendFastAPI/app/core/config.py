"""
app/core/config.py
──────────────────
Centralised settings loaded once at startup via pydantic-settings.
All values come from environment variables or a .env file.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: Literal["development", "production"] = "development"
    log_level: str = "INFO"
    cache_ttl_seconds: int = 300

    # Logging
    # Log file is written relative to the working directory (BackendFastAPI/).
    # Set LOG_FILE=off to disable file logging (console only).
    log_file: str = "logs/app.log"

    # Debug / tracing
    # Set PORTFOLIO_DEBUG_LOG=true in .env (or env var) to enable on startup.
    # Can also be toggled at runtime via POST /api/v1/debug/portfolio-trace?enabled=true
    portfolio_debug_log: bool = True

    # Upstox
    upstox_api_key: str = ""
    upstox_api_secret: str = ""
    upstox_redirect_uri: str = "https://127.0.0.1"
    upstox_access_token: str = ""
    upstox_base_url: str = "https://api.upstox.com/v2"

    # eToro
    etoro_api_key: str = ""
    etoro_user_key: str = ""
    etoro_base_url: str = "https://public-api.etoro.com"

    # Optional Redis
    redis_url: str = ""

    # ── Auth / JWT ────────────────────────────────────────────────────────
    # Set JWT_SECRET in your .env — never use the default in production
    jwt_secret: str = "dev-only-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7

    # ── Default admin seed (used only on first startup) ───────────────────
    admin_username: str = "admin"
    admin_email: str = "admin@local.com"
    admin_password: str = "Admin@123"

    # ── Database ──────────────────────────────────────────────────────────
    db_url: str = "sqlite:///./investment_app.db"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton Settings instance."""
    return Settings()
