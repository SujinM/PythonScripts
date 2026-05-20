"""
app/api/v1/upstox_historical.py
───────────────────────────────
Proxy endpoint for Upstox Historical Candle Data v3.

  GET /api/v1/upstox/historical/{instrument_key}/{unit}/{interval}/{to_date}
      ?from_date=YYYY-MM-DD   (optional)

Path parameters
---------------
  instrument_key  e.g. "NSE_EQ|INE848E01016"  (url-encoded on the wire)
  unit            minutes | hours | days | weeks | months
  interval        1-300 for minutes, 1-5 for hours, 1 for days/weeks/months
  to_date         YYYY-MM-DD  (inclusive end)

Query parameters
----------------
  from_date       YYYY-MM-DD  (optional start; Upstox applies unit-specific limits)

Response shape
--------------
{
  "instrument_key": "...",
  "unit": "days",
  "interval": "1",
  "candles": [
    {"timestamp": "2025-01-01T00:00:00+05:30",
     "open": 53.1, "high": 53.95, "low": 51.6,
     "close": 52.05, "volume": 235519861, "oi": 0},
    ...
  ]
}
"""

from __future__ import annotations

import re
from typing import Any, Literal, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.auth.deps import CurrentUser
from app.core.config import get_settings
from app.core.logger import get_logger

router = APIRouter(prefix="/upstox/historical", tags=["upstox-historical"])
logger = get_logger(__name__)

_UPSTOX_HIST_BASE = "https://api.upstox.com/v3/historical-candle"

VALID_UNITS = {"minutes", "hours", "days", "weeks", "months"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ── Schemas ────────────────────────────────────────────────────────────────────

class CandleBar(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    oi: float = 0.0


class HistoricalResponse(BaseModel):
    instrument_key: str
    unit: str
    interval: str
    candles: list[CandleBar]


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.get(
    "/{instrument_key:path}/{unit}/{interval}/{to_date}",
    response_model=HistoricalResponse,
    summary="Get historical candle data (Upstox v3)",
)
async def get_historical_candles(
    instrument_key: str,
    unit: str,
    interval: str,
    to_date: str,
    _user: CurrentUser,
    from_date: Optional[str] = Query(default=None, description="YYYY-MM-DD start date"),
) -> HistoricalResponse:
    """
    Proxy the Upstox v3 historical-candle endpoint.

    The access token is read from ``UPSTOX_ACCESS_TOKEN`` in the backend
    .env file (populated during the OAuth2 flow on the Settings page).
    """

    # ── Validate inputs ────────────────────────────────────────────────────
    if unit not in VALID_UNITS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid unit '{unit}'. Must be one of: {', '.join(sorted(VALID_UNITS))}",
        )

    if not DATE_RE.match(to_date):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="to_date must be YYYY-MM-DD",
        )

    if from_date and not DATE_RE.match(from_date):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="from_date must be YYYY-MM-DD",
        )

    # ── Access token ───────────────────────────────────────────────────────
    settings = get_settings()
    access_token = settings.upstox_access_token
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Upstox access token not configured. Connect via Settings → Brokers.",
        )

    # ── Build Upstox URL ───────────────────────────────────────────────────
    # URL-encode the pipe character in instrument_key
    from urllib.parse import quote
    encoded_key = quote(instrument_key, safe="")
    url = f"{_UPSTOX_HIST_BASE}/{encoded_key}/{unit}/{interval}/{to_date}"
    if from_date:
        url += f"/{from_date}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    logger.debug("Fetching historical candles: %s", url)

    # ── Call Upstox ────────────────────────────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        logger.error("Network error calling Upstox: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Network error contacting Upstox: {exc}",
        )

    if resp.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Upstox token expired or invalid. Re-authenticate via Settings → Brokers.",
        )
    if resp.status_code != 200:
        logger.warning("Upstox returned %d: %s", resp.status_code, resp.text[:300])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstox API error {resp.status_code}: {resp.text[:200]}",
        )

    # ── Parse response ─────────────────────────────────────────────────────
    body: dict[str, Any] = resp.json()
    raw_candles: list[list[Any]] = body.get("data", {}).get("candles", [])

    # Upstox returns candles newest-first for intraday; normalise to oldest-first
    raw_candles = list(reversed(raw_candles))

    candles = [
        CandleBar(
            timestamp=c[0],
            open=float(c[1]),
            high=float(c[2]),
            low=float(c[3]),
            close=float(c[4]),
            volume=float(c[5]),
            oi=float(c[6]) if len(c) > 6 else 0.0,
        )
        for c in raw_candles
    ]

    return HistoricalResponse(
        instrument_key=instrument_key,
        unit=unit,
        interval=interval,
        candles=candles,
    )
