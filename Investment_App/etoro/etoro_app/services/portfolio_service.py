"""
Portfolio service.

Fetches raw data from the eToro Public API via EToroClient and normalizes
it into typed domain models.  Contains NO business/analysis logic.

Endpoint mapping
----------------
  get_positions()        → GET /api/v1/trading/info/real/pnl
                            response: clientPortfolio.positions[]
                                    + clientPortfolio.mirrors[].positions[]
  get_closed_positions() → GET /api/v1/trading/info/trade/history?minDate=...
                            response: array of trade objects

Enrichment (called after fetching open positions)
--------------------------------------------------
  _fetch_instrument_metadata()  → GET /api/v1/market-data/instruments
                                    resolves instrumentID → display name + type
  _fetch_instrument_rates()     → GET /api/v1/market-data/instruments/rates
                                    resolves instrumentID → live bid price

If the live rates call fails (e.g. market closed) the service falls back to
the portfolio's own closeRate field, then to 0.  P&L is computed from the
current rate when the API does not provide it directly.
"""

import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from etoro_app.api.etoro_client import EToroClient
from etoro_app.core.logger import get_logger
from etoro_app.models.portfolio import ClosedPosition, Position

logger = get_logger(__name__)

_HISTORY_DEFAULT_DAYS = 365  # default look-back period for trade history

# eToro instrumentTypeID → human-readable string
# Values confirmed from live API responses; unconfirmed ones are commented.
# Add more IDs as you discover them.
_INSTRUMENT_TYPE_MAP: dict[int, str] = {
    1: "currencies",   # Forex pairs (e.g. EUR/USD)
    2: "commodities",  # Gold, Oil, etc.
    3: "indices",      # S&P 500, NASDAQ, etc.
    4: "etf",          # Exchange-Traded Funds
    5: "stocks",       # ✓ confirmed: AAPL, GTLB, INTC, CSIQ, D-Wave
    6: "currencies",   # (unconfirmed — may be a second currency type)
    10: "crypto",      # ✓ confirmed: Ethereum (100001)
}


class PortfolioService:
    """
    Fetches and normalizes portfolio data from the eToro Public API.

    Args:
        client:    An :class:`~app.api.etoro_client.EToroClient` instance.
        cache_ttl: Seconds to cache API responses. Set to 0 to disable.
    """

    def __init__(self, client: EToroClient, cache_ttl: int = 300) -> None:
        self._client = client
        self._cache_ttl = cache_ttl
        self._cache: dict[str, tuple[float, Any]] = {}

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    def _cached(self, key: str, fetch_fn) -> Any:
        """Return cached value if still fresh, otherwise call fetch_fn."""
        if self._cache_ttl > 0:
            now = time.monotonic()
            entry = self._cache.get(key)
            if entry is not None:
                ts, data = entry
                if now - ts < self._cache_ttl:
                    logger.debug("Cache hit: %s", key)
                    return data

        data = fetch_fn()
        if self._cache_ttl > 0:
            self._cache[key] = (time.monotonic(), data)
        return data

    def invalidate_cache(self) -> None:
        """Clear all cached responses."""
        self._cache.clear()
        logger.debug("Portfolio cache invalidated.")

    # ------------------------------------------------------------------
    # Open positions
    # ------------------------------------------------------------------

    def get_positions(self) -> list[Position]:
        """
        Return normalized open positions.

        Endpoint: ``GET /api/v1/trading/info/real/pnl``
        """
        return self._cached("positions", self._fetch_positions)

    def _fetch_positions(self) -> list[Position]:
        logger.info("Fetching open positions...")
        response = self._client.get("/api/v1/trading/info/real/pnl")
        portfolio = response.get("clientPortfolio", {}) if isinstance(response, dict) else {}

        # Direct positions
        raw: list[dict] = list(portfolio.get("positions") or [])

        # Also collect copy-trade positions from mirror arrays
        for mirror in portfolio.get("mirrors") or []:
            raw.extend(mirror.get("positions") or [])

        if not raw:
            logger.info("No open positions found.")
            return []

        # Batch-resolve instrument names/types and live market rates
        instrument_ids = list({
            int(p.get("instrumentID") or p.get("instrumentId", 0))
            for p in raw
            if p.get("instrumentID") or p.get("instrumentId")
        })
        metadata = self._fetch_instrument_metadata(instrument_ids) if instrument_ids else {}
        rates = self._fetch_instrument_rates(instrument_ids) if instrument_ids else {}

        positions = [self._normalize_position(p, metadata, rates) for p in raw]
        logger.info("Fetched %d open position(s).", len(positions))
        return positions

    def _fetch_instrument_metadata(self, instrument_ids: list[int]) -> dict[int, dict]:
        """
        Batch-fetch instrument display names and type IDs.

        Endpoint: ``GET /api/v1/market-data/instruments?instrumentIds=1,2,3``

        Falls back to individual per-ID requests when the batch returns 500,
        which happens if any single ID is invalid/internal on eToro's side.
        """
        result = self._fetch_market_data(
            endpoint="/api/v1/market-data/instruments",
            instrument_ids=instrument_ids,
            items_key="instrumentDisplayDatas",
            label="metadata",
        )
        return result

    def _fetch_instrument_rates(self, instrument_ids: list[int]) -> dict[int, dict]:
        """
        Batch-fetch current live bid/ask rates.

        Endpoint: ``GET /api/v1/market-data/instruments/rates?instrumentIds=1,2,3``

        Falls back to individual per-ID requests when the batch returns 500.
        """
        result = self._fetch_market_data(
            endpoint="/api/v1/market-data/instruments/rates",
            instrument_ids=instrument_ids,
            items_key="rates",
            label="rates",
        )
        return result

    def _fetch_market_data(
        self,
        endpoint: str,
        instrument_ids: list[int],
        items_key: str,
        label: str,
    ) -> dict[int, dict]:
        """
        Shared helper: try a batch request, then fall back to one-by-one if it fails.

        When the batch returns 500 (typically caused by a single invalid instrument ID
        such as a virtual copy-trading instrument with an unusually large ID), this
        method silently retries each ID individually so valid instruments still resolve.
        """

        def _parse(response: dict | list) -> dict[int, dict]:
            out: dict[int, dict] = {}
            if isinstance(response, dict):
                items = response.get(items_key, [])
            else:
                items = response
            for item in items:
                iid = item.get("instrumentID")
                if iid is not None:
                    out[int(iid)] = item
            return out

        # --- batch attempt ---
        ids_str = ",".join(str(i) for i in instrument_ids)
        try:
            return _parse(
                self._client.get(endpoint, params={"instrumentIds": ids_str})
            )
        except Exception as exc:
            logger.warning(
                "Batch %s request failed (%s); retrying individually for %d IDs.",
                label, exc, len(instrument_ids),
            )

        # --- per-ID fallback ---
        result: dict[int, dict] = {}
        for iid in instrument_ids:
            try:
                result.update(
                    _parse(self._client.get(endpoint, params={"instrumentIds": str(iid)}))
                )
            except Exception as exc:
                logger.debug("Skipping instrument %d (%s lookup failed): %s", iid, label, exc)
        return result

    @staticmethod
    def _normalize_position(
        raw: dict,
        metadata: Optional[dict[int, dict]] = None,
        rates: Optional[dict[int, dict]] = None,
    ) -> Position:
        """Map a raw API position dict to a :class:`~app.models.portfolio.Position`."""
        instrument_id = int(raw.get("instrumentID") or raw.get("instrumentId", 0))
        is_buy = bool(raw.get("isBuy", True))

        meta = (metadata or {}).get(instrument_id, {})
        rate_info = (rates or {}).get(instrument_id, {})

        # Instrument name: metadata API → raw field → fallback ID label
        instrument_name = (
            meta.get("instrumentDisplayName")
            or raw.get("instrumentName")
            or f"Instrument #{instrument_id}"
        )

        # Instrument type: metadata type ID → mapped string → raw field → unknown
        type_id = meta.get("instrumentTypeID")
        if type_id is not None:
            instrument_type = _INSTRUMENT_TYPE_MAP.get(int(type_id), f"type#{type_id}")
        else:
            instrument_type = raw.get("instrumentType") or "unknown"

        # Current rate: portfolio closeRate → live bid from rates API → 0
        current_rate = float(raw.get("closeRate") or 0.0)
        if not current_rate:
            current_rate = float(
                rate_info.get("bid") or rate_info.get("lastExecution") or 0.0
            )

        # P&L: from API pnL field → compute from current rate → 0
        pnl = float(raw.get("pnL") or raw.get("pnl") or 0.0)
        if pnl == 0.0 and current_rate > 0:
            units = float(raw.get("units", 0.0))
            open_rate = float(raw.get("openRate", 0.0))
            if is_buy:
                pnl = round((current_rate - open_rate) * units, 4)
            else:
                pnl = round((open_rate - current_rate) * units, 4)

        open_date: Optional[datetime] = None
        ts_str = raw.get("openDateTime")
        if ts_str:
            try:
                open_date = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        return Position(
            position_id=str(raw.get("positionID") or raw.get("positionId", "")),
            instrument_id=instrument_id,
            instrument_name=instrument_name,
            instrument_type=instrument_type,
            direction="Buy" if is_buy else "Sell",
            amount=float(raw.get("amount", 0.0)),
            units=float(raw.get("units", 0.0)),
            open_rate=float(raw.get("openRate", 0.0)),
            current_rate=current_rate,
            leverage=int(raw.get("leverage", 1)),
            unrealised_pnl=pnl,
            open_date=open_date,
            is_copy=bool(raw.get("mirrorID") or raw.get("mirrorId", 0)),
        )

    # ------------------------------------------------------------------
    # Closed positions (trade history)
    # ------------------------------------------------------------------

    def get_closed_positions(self, days: int = _HISTORY_DEFAULT_DAYS) -> list[ClosedPosition]:
        """
        Return normalized closed positions (trade history).

        Endpoint: ``GET /api/v1/trading/info/trade/history``

        Args:
            days: How many calendar days back to fetch (default: 365).
        """
        return self._cached(f"closed_{days}", lambda: self._fetch_closed_positions(days))

    def _fetch_closed_positions(self, days: int) -> list[ClosedPosition]:
        logger.info("Fetching trade history (last %d days)...", days)
        min_date = (date.today() - timedelta(days=days)).isoformat()
        response = self._client.get(
            "/api/v1/trading/info/trade/history",
            params={"minDate": min_date},
        )
        raw: list[dict] = response if isinstance(response, list) else []
        closed = [self._normalize_closed_position(c) for c in raw]
        logger.info("Fetched %d closed position(s).", len(closed))
        return closed

    @staticmethod
    def _normalize_closed_position(raw: dict) -> ClosedPosition:
        """Map a raw trade-history dict to a :class:`~app.models.portfolio.ClosedPosition`."""

        def _parse_dt(key: str) -> Optional[datetime]:
            ts_str = raw.get(key)
            if ts_str:
                try:
                    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass
            return None

        instrument_id = int(raw.get("instrumentId") or raw.get("instrumentID", 0))
        is_buy = bool(raw.get("isBuy", True))

        return ClosedPosition(
            position_id=str(raw.get("positionId") or raw.get("positionID", "")),
            instrument_id=instrument_id,
            instrument_name=raw.get("instrumentName") or f"Instrument #{instrument_id}",
            instrument_type=raw.get("instrumentType") or "unknown",
            direction="Buy" if is_buy else "Sell",
            amount=float(raw.get("investment") or raw.get("amount", 0.0)),
            units=float(raw.get("units", 0.0)),
            open_rate=float(raw.get("openRate", 0.0)),
            close_rate=float(raw.get("closeRate", 0.0)),
            leverage=int(raw.get("leverage", 1)),
            realised_pnl=float(raw.get("netProfit") or raw.get("profit", 0.0)),
            open_date=_parse_dt("openTimestamp"),
            close_date=_parse_dt("closeTimestamp"),
        )
