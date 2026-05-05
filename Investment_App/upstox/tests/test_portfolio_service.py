"""
Unit tests for PortfolioService.

All HTTP calls are replaced with mocks — no network I/O in these tests.
"""

import pytest
from unittest.mock import MagicMock

from app.models.portfolio import Holding, Position, Trade
from app.services.portfolio_service import PortfolioService
from tests.conftest import RAW_HOLDING, RAW_POSITION, RAW_TRADE


class TestNormalizeHolding:
    """Static normalization — no mocking required."""

    def test_fields_mapped_correctly(self) -> None:
        h = PortfolioService._normalize_holding(RAW_HOLDING)
        assert h.trading_symbol == "INFY"
        assert h.quantity == 10
        assert h.average_price == 1500.0
        assert h.last_price == 1650.0
        assert h.exchange == "NSE"

    def test_computed_invested_value(self) -> None:
        h = PortfolioService._normalize_holding(RAW_HOLDING)
        assert h.invested_value == pytest.approx(15_000.0)

    def test_computed_current_value(self) -> None:
        h = PortfolioService._normalize_holding(RAW_HOLDING)
        assert h.current_value == pytest.approx(16_500.0)

    def test_return_percentage(self) -> None:
        h = PortfolioService._normalize_holding(RAW_HOLDING)
        assert h.return_percentage == pytest.approx(10.0)

    def test_zero_quantity_return_is_zero(self) -> None:
        raw = {**RAW_HOLDING, "quantity": 0}
        h = PortfolioService._normalize_holding(raw)
        assert h.return_percentage == 0.0

    def test_missing_fields_use_defaults(self) -> None:
        h = PortfolioService._normalize_holding({})
        assert h.quantity == 0
        assert h.average_price == 0.0
        assert h.isin == ""


class TestNormalizePosition:
    def test_fields_mapped_correctly(self) -> None:
        p = PortfolioService._normalize_position(RAW_POSITION)
        assert p.trading_symbol == "HDFCBANK"
        assert p.product == "I"
        assert p.pnl == 250.0
        assert p.unrealised == 250.0

    def test_missing_fields_use_defaults(self) -> None:
        p = PortfolioService._normalize_position({})
        assert p.quantity == 0
        assert p.pnl == 0.0


class TestNormalizeTrade:
    def test_fields_mapped_correctly(self) -> None:
        t = PortfolioService._normalize_trade(RAW_TRADE)
        assert t.trading_symbol == "TCS"
        assert t.transaction_type == "BUY"
        assert t.quantity == 5
        assert t.price == 3200.0

    def test_trade_date_parsed(self) -> None:
        t = PortfolioService._normalize_trade(RAW_TRADE)
        assert t.trade_date is not None
        assert t.trade_date.hour == 10

    def test_invalid_date_is_none(self) -> None:
        raw = {**RAW_TRADE, "order_timestamp": "not-a-date"}
        t = PortfolioService._normalize_trade(raw)
        assert t.trade_date is None

    def test_trade_value(self) -> None:
        t = PortfolioService._normalize_trade(RAW_TRADE)
        assert t.trade_value == pytest.approx(16_000.0)  # 5 * 3200


class TestPortfolioServiceFetch:
    def test_get_holdings_returns_list_of_holdings(
        self, portfolio_service: PortfolioService, mock_client: MagicMock
    ) -> None:
        mock_client.get.return_value = {"status": "success", "data": [RAW_HOLDING]}
        result = portfolio_service.get_holdings()
        assert len(result) == 1
        assert isinstance(result[0], Holding)

    def test_get_holdings_empty_data(
        self, portfolio_service: PortfolioService, mock_client: MagicMock
    ) -> None:
        mock_client.get.return_value = {"status": "success", "data": []}
        assert portfolio_service.get_holdings() == []

    def test_get_holdings_missing_data_key(
        self, portfolio_service: PortfolioService, mock_client: MagicMock
    ) -> None:
        mock_client.get.return_value = {"status": "success"}
        assert portfolio_service.get_holdings() == []

    def test_get_positions_returns_list(
        self, portfolio_service: PortfolioService, mock_client: MagicMock
    ) -> None:
        mock_client.get.return_value = {"status": "success", "data": [RAW_POSITION]}
        result = portfolio_service.get_positions()
        assert len(result) == 1
        assert isinstance(result[0], Position)

    def test_get_trades_returns_list(
        self, portfolio_service: PortfolioService, mock_client: MagicMock
    ) -> None:
        mock_client.get.return_value = {"status": "success", "data": [RAW_TRADE]}
        result = portfolio_service.get_trades()
        assert len(result) == 1
        assert isinstance(result[0], Trade)


class TestPortfolioServiceCache:
    def test_cache_hit_avoids_second_api_call(self, mock_client: MagicMock) -> None:
        svc = PortfolioService(mock_client, cache_ttl=300)
        mock_client.get.return_value = {"status": "success", "data": []}
        svc.get_holdings()
        svc.get_holdings()
        assert mock_client.get.call_count == 1

    def test_invalidate_cache_forces_refetch(self, mock_client: MagicMock) -> None:
        svc = PortfolioService(mock_client, cache_ttl=300)
        mock_client.get.return_value = {"status": "success", "data": []}
        svc.get_holdings()
        svc.invalidate_cache()
        svc.get_holdings()
        assert mock_client.get.call_count == 2

    def test_cache_disabled_when_ttl_zero(self, mock_client: MagicMock) -> None:
        svc = PortfolioService(mock_client, cache_ttl=0)
        mock_client.get.return_value = {"status": "success", "data": []}
        svc.get_holdings()
        svc.get_holdings()
        assert mock_client.get.call_count == 2
