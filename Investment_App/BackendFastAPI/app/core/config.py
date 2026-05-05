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

    # Upstox
    upstox_api_key: str = ""
    upstox_api_secret: str = ""
    upstox_redirect_uri: str = "https://127.0.0.1"
    upstox_access_token: str = ""
    upstox_base_url: str = "https://api.upstox.com/v2"

    # eToro
    etoro_api_key: str = ""
    etoro_base_url: str = "https://api.etoro.com/v1"

    # Optional Redis
    redis_url: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton Settings instance."""
    return Settings()
