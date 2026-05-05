"""
app/services/portfolio_service.py
──────────────────────────────────
PortfolioService — orchestrates broker calls and builds unified models.
All caching lives here; adapters are always called without state.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from app.brokers.registry import BrokerRegistry
from app.core.cache import InMemoryCache
from app.core.config import get_settings
from app.core.exceptions import BrokerNotFoundError
from app.core.logger import get_logger
from app.models.portfolio import Holding, PortfolioSummary, Position, Trade

logger = get_logger(__name__)


class PortfolioService:
    def __init__(self, registry: BrokerRegistry, cache: InMemoryCache) -> None:
        self._registry = registry
        self._cache = cache
        self._ttl = get_settings().cache_ttl_seconds

    # ── Helpers ───────────────────────────────────────────────────────────

    def _require(self, broker_id: str):
        """Raise BrokerNotFoundError if broker is not registered."""
        return self._registry.get(broker_id)  # raises if missing

    # ── Public API ────────────────────────────────────────────────────────

    def get_holdings(self, broker_id: str) -> list[Holding]:
        cache_key = f"holdings:{broker_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        adapter = self._require(broker_id)
        data = adapter.get_holdings()
        self._cache.set(cache_key, data, self._ttl)
        logger.info("Fetched %d holdings from %s", len(data), broker_id)
        return data

    def get_positions(self, broker_id: str) -> list[Position]:
        cache_key = f"positions:{broker_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        adapter = self._require(broker_id)
        data = adapter.get_positions()
        self._cache.set(cache_key, data, self._ttl)
        logger.info("Fetched %d positions from %s", len(data), broker_id)
        return data

    def get_trades(self, broker_id: str) -> list[Trade]:
        cache_key = f"trades:{broker_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        adapter = self._require(broker_id)
        data = adapter.get_trades()
        self._cache.set(cache_key, data, self._ttl)
        logger.info("Fetched %d trades from %s", len(data), broker_id)
        return data

    def get_summary(self, broker_id: str) -> PortfolioSummary:
        cache_key = f"summary:{broker_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        with ThreadPoolExecutor(max_workers=2) as executor:
            f_holdings = executor.submit(self.get_holdings, broker_id)
            f_positions = executor.submit(self.get_positions, broker_id)
            holdings = f_holdings.result()
            positions = f_positions.result()

        total_invested = sum(h.invested_value for h in holdings)
        total_current = sum(h.current_value for h in holdings)
        total_unrealised = sum(h.unrealised_pnl for h in holdings)
        total_realised = sum(p.realised_pnl for p in positions)
        return_pct = (
            round(total_unrealised / total_invested * 100, 4) if total_invested else 0.0
        )

        sorted_holdings = sorted(holdings, key=lambda h: h.unrealised_pnl, reverse=True)
        top_gainers = sorted_holdings[:3]
        top_losers = sorted_holdings[-3:][::-1]

        summary = PortfolioSummary(
            broker=broker_id,
            holdings_count=len(holdings),
            positions_count=len(positions),
            total_invested=round(total_invested, 2),
            total_current_value=round(total_current, 2),
            total_unrealised_pnl=round(total_unrealised, 2),
            total_realised_pnl=round(total_realised, 2),
            overall_return_pct=return_pct,
            top_gainers=top_gainers,
            top_losers=top_losers,
        )
        self._cache.set(cache_key, summary, self._ttl)
        return summary

    def list_brokers(self) -> list[dict]:
        return [
            {"id": a.broker_id, "name": a.display_name, "configured": a.is_configured()}
            for a in self._registry.all()
        ]

    def invalidate(self, broker_id: str) -> None:
        for prefix in ("holdings", "positions", "trades", "summary"):
            self._cache.invalidate(f"{prefix}:{broker_id}")
        logger.info("Cache invalidated for broker: %s", broker_id)
