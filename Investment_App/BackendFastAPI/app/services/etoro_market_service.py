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

    # Build response — use whatever the API provides; fields absent from the
    # eToro rates endpoint (change, high, low, volume) are returned as None
    # so the frontend shows "—" rather than a misleading fallback value.
    def _f(val) -> Optional[float]:
        """Return float if truthy, else None."""
        return float(val) if val else None

    change         = _f(rate.get("change")        or meta.get("change"))
    change_pct     = _f(rate.get("percentage")    or meta.get("percentage")    or
                        rate.get("changePercent") or meta.get("changePercent"))
    volume         = _f(rate.get("volume")        or meta.get("volume"))
    high24h        = _f(rate.get("high")          or meta.get("high"))
    low24h         = _f(rate.get("low")           or meta.get("low"))
    open_price     = _f(rate.get("open")          or meta.get("open"))
    prev_close     = _f(rate.get("prevClose")     or meta.get("prevClose")     or
                        rate.get("previousClose") or meta.get("previousClose"))

    return {
        "symbol":        symbol,
        "price":         price,
        "change":        change     or 0.0,
        "changePercent": change_pct or 0.0,
        "volume":        volume     or 0.0,
        "high24h":       high24h    or price,   # MarketData schema requires float; use price if unavailable
        "low24h":        low24h     or price,   # same
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


# ── Bulk period price-change fetch ────────────────────────────────────────────

def _fetch_candles_first_close(
    base: str,
    hdrs: dict,
    instrument_ids: list[int],
    period: str,
) -> dict[int, float]:
    """
    Call ``GET /api/v1/market-data/instruments/candles`` for *period* and return
    a dict mapping instrumentID → closing price of the **oldest** candle returned
    (i.e. the price at the start of that period).

    If the endpoint is unavailable or returns no data, returns ``{}``.

    Period values accepted by eToro: ``OneMonth``, ``OneYear`` (others possible).
    """
    ids_str = ",".join(str(i) for i in instrument_ids)
    try:
        resp = requests.get(
            f"{base}/api/v1/market-data/instruments/candles",
            headers=hdrs,
            params={"instrumentIds": ids_str, "period": period},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        body = resp.json()
    except Exception:
        return {}

    out: dict[int, float] = {}

    # eToro candles response can come in two shapes:
    #   Shape A: { "candles": [{ "instrumentID": 9425, "candles": [...] }] }
    #   Shape B: [{ "instrumentID": 9425, "candles": [...] }]  (bare array)
    if isinstance(body, dict):
        charts = (
            body.get("candles")
            or body.get("Candles")
            or body.get("charts")
            or []
        )
    elif isinstance(body, list):
        charts = body
    else:
        return {}

    for chart in charts:
        iid = chart.get("instrumentID") or chart.get("InstrumentID")
        candles: list[dict] = chart.get("candles") or chart.get("Candles") or []
        if iid is None or not candles:
            continue
        # Oldest candle first — use its close as "price N period ago"
        oldest = candles[0]
        close = float(
            oldest.get("close") or oldest.get("Close")
            or oldest.get("open")  or oldest.get("Open")
            or 0.0
        )
        if close:
            out[int(iid)] = close
    return out


def fetch_price_changes_bulk(instrument_ids: list[int]) -> dict[int, dict]:
    """
    Return 1-month and 1-year price changes for the given eToro instrument IDs.

    Result dict shape per ID::

        {
          "current_price":  float | None,
          "change_1m_value": float | None,
          "change_1m_pct":   float | None,
          "change_1y_value": float | None,
          "change_1y_pct":   float | None,
        }

    Fields are ``None`` when eToro API does not return the required data.
    """
    s = get_settings()
    if not s.etoro_api_key or not s.etoro_user_key or not instrument_ids:
        return {}

    base = _base_url()
    hdrs = _headers()
    ids_str = ",".join(str(i) for i in instrument_ids)

    # ── Current prices ────────────────────────────────────────────────────────
    current: dict[int, float] = {}
    try:
        resp = requests.get(
            f"{base}/api/v1/market-data/instruments/rates",
            headers=hdrs,
            params={"instrumentIds": ids_str},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        for rate in resp.json().get("rates", []):
            iid = rate.get("instrumentID")
            # bid is preferred; fall back to ask then lastExecution
            price = float(
                rate.get("bid") or rate.get("ask") or rate.get("lastExecution") or 0.0
            )
            if iid is not None and price:
                current[int(iid)] = price
    except Exception:
        pass

    # ── Historical first-close prices ─────────────────────────────────────────
    hdrs1m = _headers()   # fresh x-request-id per call
    past_1m = _fetch_candles_first_close(base, hdrs1m, instrument_ids, "OneMonth")

    hdrs1y = _headers()
    past_1y = _fetch_candles_first_close(base, hdrs1y, instrument_ids, "OneYear")

    # ── Assemble result ───────────────────────────────────────────────────────
    result: dict[int, dict] = {}
    for iid in instrument_ids:
        cur = current.get(iid)
        p1m = past_1m.get(iid)
        p1y = past_1y.get(iid)

        def _change(now: float | None, then: float | None):
            if now is None or then is None or then == 0.0:
                return None, None
            val = round(now - then, 6)
            pct = round((now - then) / then * 100, 4)
            return val, pct

        v1m, p1m_pct = _change(cur, p1m)
        v1y, p1y_pct = _change(cur, p1y)

        result[iid] = {
            "current_price":   cur,
            "change_1m_value": v1m,
            "change_1m_pct":   p1m_pct,
            "change_1y_value": v1y,
            "change_1y_pct":   p1y_pct,
        }
    return result
