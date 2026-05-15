"""
app/services/etoro_market_service.py
──────────────────────────────────────
Fetches live instrument prices from the eToro Public API.

Endpoint used:
  GET /api/v1/market-data/instruments/rates?instrumentIds={id}
  GET /api/v1/market-data/instruments?instrumentIds={id}

Authentication: x-api-key + x-user-key headers (read from app settings).

The eToro API identifies instruments by a numeric instrumentID, not by
symbol name.  This service resolves symbol → instrumentID by querying the
local EtoroInstrument catalogue table that is populated by the sync script.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

import requests
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import EtoroInstrument

_TIMEOUT = 10  # seconds


def _headers() -> dict[str, str]:
    s = get_settings()
    return {
        "x-api-key":      s.etoro_api_key,
        "x-user-key":     s.etoro_user_key,
        "x-request-id":   str(uuid.uuid4()),
        "Accept":         "application/json",
    }


def _base_url() -> str:
    return get_settings().etoro_base_url.rstrip("/")


# ── Symbol → instrumentID lookup ─────────────────────────────────────────────

def _resolve_instrument_id(symbol: str, db: Session) -> Optional[int]:
    """Return the eToro instrumentID for *symbol*, or None if not found."""
    row: Optional[EtoroInstrument] = (
        db.query(EtoroInstrument)
        .filter(EtoroInstrument.symbol == symbol)
        .first()
    )
    return row.instrument_id if row else None


# ── Single-instrument price fetch ─────────────────────────────────────────────

def fetch_market_data(symbol: str, db: Session) -> Optional[dict]:
    """
    Return a MarketData-compatible dict for *symbol*, or None when:
      - symbol not found in the eToro instrument catalogue
      - eToro API keys are not configured
      - the eToro API call fails or returns no data

    Fields returned:
      symbol, price, change, changePercent, volume,
      high24h, low24h, marketCap, open, previousClose, timestamp
    """
    s = get_settings()
    if not s.etoro_api_key or not s.etoro_user_key:
        return None

    iid = _resolve_instrument_id(symbol, db)
    if iid is None:
        return None

    params = {"instrumentIds": str(iid)}
    hdrs   = _headers()
    base   = _base_url()

    # ── Live rates ────────────────────────────────────────────────────────────
    try:
        resp = requests.get(
            f"{base}/api/v1/market-data/instruments/rates",
            headers=hdrs,
            params=params,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        rates_body = resp.json()
    except Exception:
        return None

    rates_list: list[dict] = (
        rates_body.get("rates", [])
        if isinstance(rates_body, dict)
        else []
    )
    rate: dict = next(
        (r for r in rates_list if int(r.get("instrumentID", -1)) == iid),
        {},
    )

    price = float(rate.get("bid") or rate.get("lastExecution") or 0.0)
    if price == 0.0:
        return None

    # ── Optional instrument metadata (display name, 24h stats) ───────────────
    try:
        meta_resp = requests.get(
            f"{base}/api/v1/market-data/instruments",
            headers=_headers(),       # fresh x-request-id
            params=params,
            timeout=_TIMEOUT,
        )
        meta_resp.raise_for_status()
        meta_body = meta_resp.json()
        metas: list[dict] = (
            meta_body.get("instrumentDisplayDatas", [])
            if isinstance(meta_body, dict)
            else []
        )
        meta: dict = next(
            (m for m in metas if int(m.get("instrumentID", -1)) == iid),
            {},
        )
    except Exception:
        meta = {}

    # Build response — use whatever the API provides, fall back gracefully
    change         = float(rate.get("change")        or meta.get("change")        or 0.0)
    change_pct     = float(rate.get("percentage")    or meta.get("percentage")    or
                           rate.get("changePercent") or meta.get("changePercent") or 0.0)
    volume         = float(rate.get("volume")        or meta.get("volume")        or 0.0)
    high24h        = float(rate.get("high")          or meta.get("high")          or price)
    low24h         = float(rate.get("low")           or meta.get("low")           or price)
    open_price     = float(rate.get("open")          or meta.get("open")          or 0.0) or None
    prev_close     = float(rate.get("prevClose")     or meta.get("prevClose")     or
                           rate.get("previousClose") or meta.get("previousClose") or 0.0) or None

    return {
        "symbol":        symbol,
        "price":         price,
        "change":        change,
        "changePercent": change_pct,
        "volume":        volume,
        "high24h":       high24h,
        "low24h":        low24h,
        "marketCap":     None,
        "open":          open_price,
        "previousClose": prev_close,
        "timestamp":     datetime.now(timezone.utc).isoformat(),
    }


# ── Bulk fetch ────────────────────────────────────────────────────────────────

def fetch_bulk_market_data(symbols: list[str], db: Session) -> list[dict]:
    """
    Fetch live rates for multiple symbols in a single eToro API call.
    Returns only the symbols that resolved successfully.
    """
    s = get_settings()
    if not s.etoro_api_key or not s.etoro_user_key or not symbols:
        return []

    # Resolve all symbols to instrument IDs
    rows: list[EtoroInstrument] = (
        db.query(EtoroInstrument)
        .filter(EtoroInstrument.symbol.in_(symbols))
        .all()
    )
    id_to_symbol = {row.instrument_id: row.symbol for row in rows}
    if not id_to_symbol:
        return []

    ids_str = ",".join(str(i) for i in id_to_symbol)
    hdrs    = _headers()
    base    = _base_url()

    try:
        resp = requests.get(
            f"{base}/api/v1/market-data/instruments/rates",
            headers=hdrs,
            params={"instrumentIds": ids_str},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        rates_list: list[dict] = resp.json().get("rates", [])
    except Exception:
        return []

    now = datetime.now(timezone.utc).isoformat()
    results: list[dict] = []
    for rate in rates_list:
        iid   = int(rate.get("instrumentID", -1))
        sym   = id_to_symbol.get(iid)
        price = float(rate.get("bid") or rate.get("lastExecution") or 0.0)
        if not sym or price == 0.0:
            continue
        results.append({
            "symbol":        sym,
            "price":         price,
            "change":        float(rate.get("change")     or 0.0),
            "changePercent": float(rate.get("percentage") or 0.0),
            "volume":        float(rate.get("volume")     or 0.0),
            "high24h":       float(rate.get("high")       or price),
            "low24h":        float(rate.get("low")        or price),
            "marketCap":     None,
            "open":          float(rate.get("open")       or 0.0) or None,
            "previousClose": float(rate.get("prevClose")  or 0.0) or None,
            "timestamp":     now,
        })
    return results
