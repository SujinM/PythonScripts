"""tests/test_portfolio_service.py"""

from __future__ import annotations

import pytest

from app.core.exceptions import BrokerNotFoundError
from app.services.portfolio_service import PortfolioService


class TestPortfolioService:
    def test_get_holdings_returns_list(self, portfolio_service: PortfolioService):
        holdings = portfolio_service.get_holdings("mock")
        assert len(holdings) == 2
        assert holdings[0].trading_symbol == "ABC"

    def test_get_holdings_cached(self, portfolio_service: PortfolioService):
        portfolio_service.get_holdings("mock")
        portfolio_service.get_holdings("mock")  # second call — from cache
        # ensure no error and same result
        data = portfolio_service.get_holdings("mock")
        assert len(data) == 2

    def test_get_positions(self, portfolio_service: PortfolioService):
        positions = portfolio_service.get_positions("mock")
        assert len(positions) == 1
        assert positions[0].realised_pnl == 50.0

    def test_get_trades(self, portfolio_service: PortfolioService):
        trades = portfolio_service.get_trades("mock")
        assert len(trades) == 1
        assert trades[0].transaction_type == "BUY"

    def test_get_summary_totals(self, portfolio_service: PortfolioService):
        summary = portfolio_service.get_summary("mock")
        assert summary.broker == "mock"
        assert summary.holdings_count == 2
        assert summary.positions_count == 1
        assert summary.total_invested > 0
        assert summary.total_current_value > 0

    def test_summary_unrealised_pnl_correct(self, portfolio_service: PortfolioService):
        holdings = portfolio_service.get_holdings("mock")
        expected_unrealised = sum(h.unrealised_pnl for h in holdings)
        summary = portfolio_service.get_summary("mock")
        assert summary.total_unrealised_pnl == round(expected_unrealised, 2)

    def test_unknown_broker_raises(self, portfolio_service: PortfolioService):
        with pytest.raises(BrokerNotFoundError):
            portfolio_service.get_holdings("nonexistent")

    def test_list_brokers(self, portfolio_service: PortfolioService):
        brokers = portfolio_service.list_brokers()
        assert any(b["id"] == "mock" for b in brokers)

    def test_invalidate_clears_cache(self, portfolio_service: PortfolioService, cache):
        portfolio_service.get_holdings("mock")
        assert cache.get("holdings:mock") is not None
        portfolio_service.invalidate("mock")
        assert cache.get("holdings:mock") is None

    def test_summary_top_gainers_sorted(self, portfolio_service: PortfolioService):
        summary = portfolio_service.get_summary("mock")
        # ABC has positive pnl; XYZ has negative — gainers should be ABC first
        if summary.top_gainers:
            assert summary.top_gainers[0].trading_symbol == "ABC"
