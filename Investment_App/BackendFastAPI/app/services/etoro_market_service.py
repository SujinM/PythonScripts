"""
app/services/etoro_market_service.py
──────────────────────────────────────
Fetches live instrument prices from the eToro Public API.

  Current price  : GET /api/v1/market-data/instruments/rates  (eToro)
  Historical data: Yahoo Finance via yfinance (eToro Public API has no candle/history endpoints)

Authentication for eToro: x-api-key + x-user-key headers (read from app settings).
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta, timezone
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

_log = logging.getLogger(__name__)


# ── Yahoo Finance helpers ─────────────────────────────────────────────────────

# eToro instrument_type_id values
_TYPE_CRYPTO = 10
_TYPE_FOREX  = 1

# eToro uses $-prefixed symbols for indices and commodities that don't exist
# on Yahoo Finance. Map them to their Yahoo Finance equivalents.
_ETORO_TO_YF: dict[str, str] = {
    # Indices
    "$SPX500":   "^GSPC",       # S&P 500
    "$NSDQ100":  "^NDX",        # NASDAQ-100
    "$DJ30":     "^DJI",        # Dow Jones Industrial Average
    "$FTSE100":  "^FTSE",       # FTSE 100
    "$GER40":    "^GDAXI",      # DAX 40
    "$NKY225":   "^N225",       # Nikkei 225
    "$HK50":     "^HSI",        # Hang Seng
    "$AUS200":   "^AXJO",       # ASX 200
    "$FRA40":    "^FCHI",       # CAC 40
    # Commodities (futures)
    "$OIL":      "CL=F",        # WTI Crude Oil
    "$NATGAS":   "NG=F",        # Natural Gas
    "$GOLD":     "GC=F",        # Gold
    "$SILVER":   "SI=F",        # Silver
    "$COPPER":   "HG=F",        # Copper
    "$USDOLLAR": "DX-Y.NYB",    # US Dollar Index
    "$WHEAT":    "ZW=F",        # Wheat
    "$CORN":     "ZC=F",        # Corn
}


def _to_yf_ticker(symbol: str, type_id: int | None) -> str:
    """Convert an eToro symbol + type to a Yahoo Finance ticker string."""
    sym = symbol.upper()
    # eToro $-prefixed special symbols (indices, commodities)
    if sym in _ETORO_TO_YF:
        return _ETORO_TO_YF[sym]
    if type_id == _TYPE_CRYPTO:
        return f"{sym}-USD"          # ETH → ETH-USD
    if type_id == _TYPE_FOREX:
        if len(sym) == 6 and not sym.endswith("=X"):
            return f"{sym}=X"        # EURUSD → EURUSD=X
    return sym                       # AMD, AAPL, SMH, etc. → unchanged


def _fetch_yf_history(id_sym_map: dict[int, tuple[str, int | None]]) -> dict[int, dict]:
    """
    Download ~400 days of daily close prices from Yahoo Finance for all
    instruments in *id_sym_map* and return a dict::

        { iid: { "prev_close": float|None,
                 "price_1m_ago": float|None,
                 "price_1y_ago": float|None } }

    Any ticker that Yahoo Finance cannot resolve will have all-None values.
    """
    try:
        import yfinance as yf
    except ImportError:
        _log.warning("[yfinance] not installed — pip install yfinance")
        return {}

    today   = date.today()
    t_1m    = today - timedelta(days=31)   # a day's buffer for weekends/holidays
    t_1y    = today - timedelta(days=366)

    result: dict[int, dict] = {}

    for iid, (sym, type_id) in id_sym_map.items():
        ticker_str = _to_yf_ticker(sym, type_id)
        empty = {"prev_close": None, "price_1m_ago": None, "price_1y_ago": None}
        try:
            hist = yf.Ticker(ticker_str).history(period="400d", interval="1d", auto_adjust=True)
            if hist.empty:
                _log.debug("[yfinance] no data for %s (iid=%s)", ticker_str, iid)
                result[iid] = empty
                continue

            # Normalize timezone-aware index to plain date objects
            dates  = [ts.date() if hasattr(ts, "date") else ts for ts in hist.index]
            closes = list(hist["Close"])

            def _price_on_or_after(target: date) -> float | None:
                for d, c in zip(dates, closes):
                    if d >= target:
                        return round(float(c), 6)
                return None

            latest_close = round(float(closes[-1]), 6) if closes else None
            prev_close   = round(float(closes[-2]), 6) if len(closes) >= 2 else None
            price_1m     = _price_on_or_after(t_1m)
            price_1y     = _price_on_or_after(t_1y)

            result[iid] = {
                "latest_close":  latest_close,
                "prev_close":    prev_close,
                "price_1m_ago":  price_1m,
                "price_1y_ago":  price_1y,
            }
        except Exception as exc:
            _log.warning("[yfinance] %s (iid=%s): %s", ticker_str, iid, exc)
            result[iid] = empty

    return result


# ── Bulk period price-change fetch ────────────────────────────────────────────

def fetch_price_changes_bulk(
    instrument_ids: list[int],
    db: Optional[Session] = None,
) -> dict[int, dict]:
    """
    Return 1-day, 1-month and 1-year price changes for the given eToro instrument IDs.

    *db* is optional but **strongly recommended** — without it the function cannot
    map instrument IDs to Yahoo Finance tickers and all historical columns will be None.

    Result dict shape per ID::

        {
          "current_price":   float | None,
          "change_1d_value": float | None,   # current − yesterday close
          "change_1d_pct":   float | None,
          "change_1m_value": float | None,   # current − price 1 month ago
          "change_1m_pct":   float | None,
          "change_1y_value": float | None,   # current − price 1 year ago
          "change_1y_pct":   float | None,
        }
    """
    s = get_settings()
    if not s.etoro_api_key or not s.etoro_user_key or not instrument_ids:
        return {}

    base    = _base_url()
    hdrs    = _headers()
    ids_str = ",".join(str(i) for i in instrument_ids)

    # ── Current prices from eToro rates API ──────────────────────────────────
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
            iid   = rate.get("instrumentID")
            price = float(rate.get("bid") or rate.get("ask") or rate.get("lastExecution") or 0.0)
            if iid is not None and price:
                current[int(iid)] = price
    except Exception as exc:
        _log.warning("[etoro rates] fetch failed: %s", exc)

    # ── Historical prices from Yahoo Finance ─────────────────────────────────
    yf_data: dict[int, dict] = {}
    if db is not None:
        from app.db.models import EtoroInstrument
        rows = db.query(EtoroInstrument).filter(
            EtoroInstrument.instrument_id.in_(instrument_ids)
        ).all()
        id_sym_map = {r.instrument_id: (r.symbol, r.instrument_type_id) for r in rows}
        yf_data = _fetch_yf_history(id_sym_map)

    # ── Assemble result ───────────────────────────────────────────────────────
    def _change(now: float | None, then: float | None) -> tuple[float | None, float | None]:
        if now is None or then is None or then == 0.0:
            return None, None
        return round(now - then, 6), round((now - then) / then * 100, 4)

    result: dict[int, dict] = {}
    for iid in instrument_ids:
        yf  = yf_data.get(iid, {})
        cur = current.get(iid) or yf.get("latest_close")  # fall back to yfinance when eToro API fails

        v1d, p1d = _change(cur, yf.get("prev_close"))
        v1m, p1m = _change(cur, yf.get("price_1m_ago"))
        v1y, p1y = _change(cur, yf.get("price_1y_ago"))

        result[iid] = {
            "current_price":   cur,
            "change_1d_value": v1d,
            "change_1d_pct":   p1d,
            "change_1m_value": v1m,
            "change_1m_pct":   p1m,
            "change_1y_value": v1y,
            "change_1y_pct":   p1y,
        }
    return result
