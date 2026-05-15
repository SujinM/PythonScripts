"""
app/api/v1/upstox_auth.py
─────────────────────────
Upstox OAuth2 authentication endpoints exposed to the TradeView frontend.

Endpoints
---------
  GET  /api/v1/upstox/auth/url       — Return the Upstox OAuth2 authorization URL
  POST /api/v1/upstox/auth/callback  — Exchange auth code for access token & persist it
  GET  /api/v1/upstox/auth/status    — Check whether a valid access token is configured
"""

from __future__ import annotations

import re
from pathlib import Path

from urllib.parse import quote

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.auth.deps import CurrentUser
from app.brokers.upstox import _SettingsConfig, UpstoxAPIError, UpstoxClient
from app.core.config import get_settings
from app.core.logger import get_logger

# Protected JSON API router (requires JWT bearer token)
router = APIRouter(prefix="/upstox/auth", tags=["upstox-auth"])
# Public router — registered at app root so /callback matches the Upstox redirect URI
callback_router = APIRouter(tags=["upstox-auth"])
logger = get_logger(__name__)

# upstox_auth.py lives at:  BackendFastAPI/app/api/v1/upstox_auth.py
#   parents[0] = v1/
#   parents[1] = api/
#   parents[2] = app/
#   parents[3] = BackendFastAPI/   ← backend root
#   parents[4] = Investment_App/
_BACKEND_ENV = Path(__file__).resolve().parents[3] / ".env"
_UPSTOX_ENV  = Path(__file__).resolve().parents[4] / "upstox" / ".env"


# ── Schemas ───────────────────────────────────────────────────────────────────

class AuthUrlResponse(BaseModel):
    url: str


class CallbackRequest(BaseModel):
    code: str


class CallbackResponse(BaseModel):
    message: str
    token_preview: str  # first 8 chars + "…" — never expose the full token


class StatusResponse(BaseModel):
    configured: bool
    token_preview: str | None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_client() -> UpstoxClient:
    """Instantiate UpstoxClient using BackendFastAPI settings."""
    cfg = _SettingsConfig()
    return UpstoxClient(cfg)


def _update_env_token(env_path: Path, token: str) -> bool:
    """Write/replace UPSTOX_ACCESS_TOKEN in a .env file. Returns True if file exists."""
    if not env_path.exists():
        return False
    content = env_path.read_text(encoding="utf-8")
    new_line = f"UPSTOX_ACCESS_TOKEN={token}"
    if re.search(r"^UPSTOX_ACCESS_TOKEN=.*", content, re.MULTILINE):
        content = re.sub(r"^UPSTOX_ACCESS_TOKEN=.*", new_line, content, flags=re.MULTILINE)
    else:
        content = content.rstrip("\n") + f"\n{new_line}\n"
    env_path.write_text(content, encoding="utf-8")
    return True


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/url", response_model=AuthUrlResponse)
def get_auth_url(_user: CurrentUser) -> AuthUrlResponse:
    """
    Return the Upstox OAuth2 authorization URL.

    The frontend should open this URL in a new browser tab/window.
    After the user grants access, Upstox redirects to the configured
    redirect_uri with a ``code`` query parameter.
    """
    settings = get_settings()
    if not settings.upstox_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="UPSTOX_API_KEY is not configured on the server.",
        )
    client = _build_client()
    url = client.get_authorization_url()
    logger.info("Upstox auth URL requested")
    return AuthUrlResponse(url=url)


@router.post("/callback", response_model=CallbackResponse)
def exchange_code(body: CallbackRequest, _user: CurrentUser) -> CallbackResponse:
    """
    Exchange the Upstox OAuth2 authorization code for an access token.

    Persists the token into both the BackendFastAPI and upstox .env files
    so that portfolio endpoints work immediately after auth.
    """
    if not body.code.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="code is required")

    client = _build_client()
    try:
        token = client.exchange_code_for_token(body.code.strip())
    except UpstoxAPIError as exc:
        logger.warning("Upstox token exchange failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token exchange failed: {exc}",
        ) from exc

    # Persist token into .env files
    for env_path in (_BACKEND_ENV, _UPSTOX_ENV):
        updated = _update_env_token(env_path, token)
        logger.info("Token %s in %s", "updated" if updated else "skipped (not found)", env_path)

    # Clear the lru_cache so the next get_settings() call reloads from the
    # updated .env file (otherwise auth_status would return stale empty token).
    get_settings.cache_clear()

    preview = token[:8] + "…" if len(token) > 8 else "…"
    return CallbackResponse(
        message="Upstox access token saved successfully.",
        token_preview=preview,
    )


@router.get("/status", response_model=StatusResponse)
def auth_status(_user: CurrentUser) -> StatusResponse:
    """
    Return whether an Upstox access token is currently configured.
    """
    settings = get_settings()
    token = settings.upstox_access_token
    if token:
        preview = token[:8] + "…" if len(token) > 8 else "…"
        return StatusResponse(configured=True, token_preview=preview)
    return StatusResponse(configured=False, token_preview=None)


# ── Public OAuth2 callback — registered at root level (no /api/v1 prefix) ────
#
# Upstox redirects the user's browser to UPSTOX_REDIRECT_URI after login.
# That URI must be http://localhost:8000/callback (or your production domain).
# This endpoint catches that redirect, exchanges the code, saves the token,
# and bounces the browser to the frontend settings page.

def _save_token(token: str) -> None:
    """Write token to both .env files and bust the settings cache."""
    for env_path in (_BACKEND_ENV, _UPSTOX_ENV):
        updated = _update_env_token(env_path, token)
        logger.info("Token %s in %s", "updated" if updated else "skipped (not found)", env_path)
    get_settings.cache_clear()


@callback_router.get("/callback")
def upstox_oauth_callback(
    code: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
) -> RedirectResponse:
    """
    Public OAuth2 redirect handler.

    Upstox redirects the browser here with ?code=... after the user logs in.
    The endpoint exchanges the code for an access token, persists it, then
    redirects to {FRONTEND_URL}/settings?upstox_auth=success (or ?upstox_auth=error).
    No JWT authentication required — this is called by Upstox, not the app user.
    """
    frontend_settings = get_settings().frontend_url.rstrip("/") + "/settings"

    if error or not code:
        msg = error_description or error or "Authorization denied by user"
        logger.warning("Upstox OAuth callback received error: %s", msg)
        return RedirectResponse(
            url=f"{frontend_settings}?upstox_auth=error&message={quote(msg)}",
            status_code=302,
        )

    client = _build_client()
    try:
        token = client.exchange_code_for_token(code.strip())
    except UpstoxAPIError as exc:
        logger.warning("Upstox token exchange failed: %s", exc)
        return RedirectResponse(
            url=f"{frontend_settings}?upstox_auth=error&message={quote(str(exc))}",
            status_code=302,
        )

    _save_token(token)
    logger.info("Upstox OAuth2 flow completed successfully via /callback")
    return RedirectResponse(url=f"{frontend_settings}?upstox_auth=success", status_code=302)
