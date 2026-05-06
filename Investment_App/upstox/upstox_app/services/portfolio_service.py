"""
Portfolio service.

Fetches raw data from the Upstox API via UpstoxClient and normalizes it
into typed domain models.  Contains NO business/analysis logic — that lives
in AnalysisService.

Design notes
------------
- UpstoxClient is injected, not created here → easy to mock in tests.
- A lightweight TTL cache prevents redundant API calls within one session.
- Each _normalize_* method is a static factory: pure, testable, side-effect-free.
"""

import time
from typing import Any, Optional

from upstox_app.api.upstox_client import UpstoxClient
from upstox_app.core.logger import get_logger
from upstox_app.models.portfolio import Holding, Position, Trade

logger = get_logger(__name__)


class PortfolioService:
    """
    Fetches and normalizes portfolio data from the Upstox API.

    Args:
        client:    An authenticated :class:`~app.api.upstox_client.UpstoxClient`.
        cache_ttl: Seconds to cache API responses.  Set to 0 to disable caching
                   (useful in tests).
    """

    def __init__(self, client: UpstoxClient, cache_ttl: int = 300) -> None:
        self._client = client
        self._cache_ttl = cache_ttl
        # {cache_key: (timestamp, data)}
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
        """Clear all cached responses (e.g., after a trade is placed)."""
        self._cache.clear()
        logger.debug("Portfolio cache invalidated.")

    # ------------------------------------------------------------------
    # Holdings
    # ------------------------------------------------------------------

    def get_holdings(self) -> list[Holding]:
        """
        Return normalized long-term holdings.

        Endpoint: ``GET /portfolio/long-term-holdings``
        """
        return self._cached("holdings", self._fetch_holdings)

    def _fetch_holdings(self) -> list[Holding]:
        logger.info("Fetching long-term holdings...")
        response = self._client.get("/portfolio/long-term-holdings")
        raw: list[dict] = response.get("data") or []
        holdings = [self._normalize_holding(h) for h in raw]
        logger.info("Fetched %d holding(s).", len(holdings))
        return holdings

    @staticmethod
    def _normalize_holding(raw: dict) -> Holding:
        """Map a raw API dict to a :class:`~app.models.portfolio.Holding`."""
        return Holding(
            isin=raw.get("isin", ""),
            instrument_token=raw.get("instrument_token", ""),
            trading_symbol=raw.get("trading_symbol", ""),
            exchange=raw.get("exchange", ""),
            quantity=int(raw.get("quantity", 0)),
            average_price=float(raw.get("average_price", 0.0)),
            last_price=float(raw.get("last_price", 0.0)),
            close_price=float(raw.get("close_price", 0.0)),
            pnl=float(raw.get("pnl", 0.0)),
            day_change=float(raw.get("day_change", 0.0)),
            day_change_percentage=float(raw.get("day_change_percentage", 0.0)),
        )

    # ------------------------------------------------------------------
    # Positions
    # ------------------------------------------------------------------

    def get_positions(self) -> list[Position]:
        """
        Return normalized short-term / intraday positions.

        Endpoint: ``GET /portfolio/short-term-positions``
        """
        return self._cached("positions", self._fetch_positions)

    def _fetch_positions(self) -> list[Position]:
        logger.info("Fetching short-term positions...")
        response = self._client.get("/portfolio/short-term-positions")
        raw: list[dict] = response.get("data") or []
        positions = [self._normalize_position(p) for p in raw]
        logger.info("Fetched %d position(s).", len(positions))
        return positions

    @staticmethod
    def _normalize_position(raw: dict) -> Position:
        """Map a raw API dict to a :class:`~app.models.portfolio.Position`."""
        return Position(
            instrument_token=raw.get("instrument_token", ""),
            trading_symbol=raw.get("trading_symbol", ""),
            exchange=raw.get("exchange", ""),
            product=raw.get("product", ""),
            quantity=int(raw.get("quantity", 0)),
            overnight_quantity=int(raw.get("overnight_quantity", 0)),
            buy_price=float(raw.get("buy_price", 0.0)),
            sell_price=float(raw.get("sell_price", 0.0)),
            buy_value=float(raw.get("buy_value", 0.0)),
            sell_value=float(raw.get("sell_value", 0.0)),
            pnl=float(raw.get("pnl", 0.0)),
            realised=float(raw.get("realised", 0.0)),
            unrealised=float(raw.get("unrealised", 0.0)),
        )

    # ------------------------------------------------------------------
    # Trades
    # ------------------------------------------------------------------

    def get_trades(self) -> list[Trade]:
        """
        Return normalized trades executed today.

        Endpoint: ``GET /order/trades/get-trades-for-day``
        """
        return self._cached("trades", self._fetch_trades)

    def _fetch_trades(self) -> list[Trade]:
        logger.info("Fetching today's trades...")
        response = self._client.get("/order/trades/get-trades-for-day")
        raw: list[dict] = response.get("data") or []
        trades = [self._normalize_trade(t) for t in raw]
        logger.info("Fetched %d trade(s).", len(trades))
        return trades

    @staticmethod
    def _normalize_trade(raw: dict) -> Trade:
        """Map a raw API dict to a :class:`~app.models.portfolio.Trade`."""
        from datetime import datetime

        trade_date: Optional[datetime] = None
        ts_str = raw.get("order_timestamp") or raw.get("exchange_timestamp")
        if ts_str:
            try:
                trade_date = datetime.fromisoformat(ts_str)
            except (ValueError, TypeError):
                pass

        return Trade(
            trade_id=raw.get("trade_id", ""),
            order_id=raw.get("order_id", ""),
            exchange=raw.get("exchange", ""),
            trading_symbol=raw.get("trading_symbol", ""),
            instrument_token=raw.get("instrument_token", ""),
            transaction_type=raw.get("transaction_type", ""),
            product=raw.get("product", ""),
            quantity=int(raw.get("quantity", 0)),
            price=float(raw.get("average_price", 0.0)),
            trade_date=trade_date,
        )
