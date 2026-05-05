"""
Tests for PortfolioService.

All tests use a mocked EToroClient — no network calls.
"""

from unittest.mock import MagicMock

import pytest

from app.api.etoro_client import EToroAPIError
from app.services.portfolio_service import PortfolioService
from tests.conftest import make_closed_position, make_position

# ---------------------------------------------------------------------------
# Raw API response fixtures (eToro Public API field names)
# ---------------------------------------------------------------------------

RAW_POSITION = {
    "positionID": 1001,
    "instrumentID": 1,
    "instrumentName": "Apple Inc.",
    "instrumentType": "stocks",
    "isBuy": True,
    "amount": 1000.0,
    "units": 5.0,
    "openRate": 190.0,
    "closeRate": 200.0,     # current market rate (eToro naming)
    "leverage": 1,
    "openDateTime": "2024-01-01T00:00:00Z",
    "mirrorID": 0,
    "pnL": 50.0,
}

RAW_CLOSED = {
    "positionId": 2001,
    "instrumentId": 2,
    "instrumentName": "Tesla Inc.",
    "instrumentType": "stocks",
    "isBuy": True,
    "investment": 500.0,
    "units": 2.0,
    "openRate": 230.0,
    "closeRate": 250.0,
    "leverage": 1,
    "netProfit": 40.0,
    "openTimestamp": "2024-01-01T00:00:00Z",
    "closeTimestamp": "2024-06-01T00:00:00Z",
}


# ---------------------------------------------------------------------------
# get_positions
# ---------------------------------------------------------------------------


class TestGetPositions:
    def test_returns_normalized_positions(self, mock_client):
        mock_client.get.return_value = {"clientPortfolio": {"positions": [RAW_POSITION]}}

        service = PortfolioService(mock_client, cache_ttl=0)
        result = service.get_positions()

        assert len(result) == 1
        pos = result[0]
        assert pos.position_id == "1001"
        assert pos.instrument_name == "Apple Inc."
        assert pos.direction == "Buy"
        assert pos.amount == 1000.0
        assert pos.units == 5.0
        assert pos.open_rate == 190.0
        assert pos.current_rate == 200.0
        assert pos.leverage == 1
        assert pos.unrealised_pnl == 50.0
        assert pos.is_copy is False

    def test_empty_portfolio(self, mock_client):
        mock_client.get.return_value = {"clientPortfolio": {"positions": []}}

        service = PortfolioService(mock_client, cache_ttl=0)
        assert service.get_positions() == []

    def test_propagates_api_error(self, mock_client):
        mock_client.get.side_effect = EToroAPIError(500, "Internal Server Error")

        service = PortfolioService(mock_client, cache_ttl=0)
        with pytest.raises(EToroAPIError):
            service.get_positions()

    def test_caches_result(self, mock_client):
        mock_client.get.return_value = {"clientPortfolio": {"positions": [RAW_POSITION]}}

        service = PortfolioService(mock_client, cache_ttl=300)
        _ = service.get_positions()
        _ = service.get_positions()

        # 3 API calls on first fetch (portfolio + metadata + rates); 0 on second (cache hit)
        assert mock_client.get.call_count == 3

    def test_cache_disabled_calls_api_each_time(self, mock_client):
        mock_client.get.return_value = {"clientPortfolio": {"positions": [RAW_POSITION]}}

        service = PortfolioService(mock_client, cache_ttl=0)
        _ = service.get_positions()
        _ = service.get_positions()

        # 3 API calls per fetch × 2 fetches = 6
        assert mock_client.get.call_count == 6

    def test_open_date_parsed(self, mock_client):
        mock_client.get.return_value = {"clientPortfolio": {"positions": [RAW_POSITION]}}

        service = PortfolioService(mock_client, cache_ttl=0)
        pos = service.get_positions()[0]
        assert pos.open_date is not None
        assert pos.open_date.year == 2024

    def test_sell_direction(self, mock_client):
        raw = {**RAW_POSITION, "isBuy": False, "positionID": 1002}
        mock_client.get.return_value = {"clientPortfolio": {"positions": [raw]}}

        service = PortfolioService(mock_client, cache_ttl=0)
        pos = service.get_positions()[0]
        assert pos.direction == "Sell"

    def test_copy_position_detected(self, mock_client):
        raw = {**RAW_POSITION, "mirrorID": 999}
        mock_client.get.return_value = {"clientPortfolio": {"positions": [raw]}}

        service = PortfolioService(mock_client, cache_ttl=0)
        pos = service.get_positions()[0]
        assert pos.is_copy is True

    def test_missing_instrument_name_uses_fallback(self, mock_client):
        raw = {**RAW_POSITION}
        del raw["instrumentName"]
        mock_client.get.return_value = {"clientPortfolio": {"positions": [raw]}}

        service = PortfolioService(mock_client, cache_ttl=0)
        pos = service.get_positions()[0]
        assert pos.instrument_name == "Instrument #1"


# ---------------------------------------------------------------------------
# get_closed_positions
# ---------------------------------------------------------------------------


class TestGetClosedPositions:
    def test_returns_normalized_closed(self, mock_client):
        mock_client.get.return_value = [RAW_CLOSED]

        service = PortfolioService(mock_client, cache_ttl=0)
        result = service.get_closed_positions()

        assert len(result) == 1
        c = result[0]
        assert c.position_id == "2001"
        assert c.realised_pnl == 40.0
        assert c.close_rate == 250.0
        assert c.close_date is not None
        assert c.close_date.year == 2024

    def test_empty_history(self, mock_client):
        mock_client.get.return_value = []

        service = PortfolioService(mock_client, cache_ttl=0)
        assert service.get_closed_positions() == []

    def test_sell_direction(self, mock_client):
        raw = {**RAW_CLOSED, "isBuy": False, "positionId": 2002}
        mock_client.get.return_value = [raw]

        service = PortfolioService(mock_client, cache_ttl=0)
        c = service.get_closed_positions()[0]
        assert c.direction == "Sell"

    def test_net_profit_mapped(self, mock_client):
        raw = {**RAW_CLOSED, "netProfit": -30.0}
        mock_client.get.return_value = [raw]

        service = PortfolioService(mock_client, cache_ttl=0)
        c = service.get_closed_positions()[0]
        assert c.realised_pnl == -30.0


# ---------------------------------------------------------------------------
# Cache invalidation
# ---------------------------------------------------------------------------


class TestCacheInvalidation:
    def test_invalidate_clears_cache(self, mock_client):
        mock_client.get.return_value = {"clientPortfolio": {"positions": [RAW_POSITION]}}

        service = PortfolioService(mock_client, cache_ttl=300)
        _ = service.get_positions()
        service.invalidate_cache()
        _ = service.get_positions()

        # 3 API calls per fetch × 2 fetches = 6
        assert mock_client.get.call_count == 6
