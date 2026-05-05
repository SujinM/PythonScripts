"""
Shared pytest fixtures.

All mock objects use spec= so that attribute typos fail loudly in tests
instead of silently passing.
"""

import pytest
from unittest.mock import MagicMock

from app.api.upstox_client import UpstoxClient
from app.core.config import Config
from app.models.portfolio import Holding, Position, Trade
from app.services.analysis_service import AnalysisService
from app.services.portfolio_service import PortfolioService

# ---------------------------------------------------------------------------
# Raw API response stubs
# ---------------------------------------------------------------------------

RAW_HOLDING = {
    "isin": "INE009A01021",
    "instrument_token": "NSE_EQ|INE009A01021",
    "trading_symbol": "INFY",
    "exchange": "NSE",
    "quantity": 10,
    "average_price": 1500.0,
    "last_price": 1650.0,
    "close_price": 1645.0,
    "pnl": 1500.0,
    "day_change": 5.0,
    "day_change_percentage": 0.30,
}

RAW_POSITION = {
    "instrument_token": "NSE_EQ|INE040A01034",
    "trading_symbol": "HDFCBANK",
    "exchange": "NSE",
    "product": "I",
    "quantity": 5,
    "overnight_quantity": 0,
    "buy_price": 1700.0,
    "sell_price": 0.0,
    "buy_value": 8500.0,
    "sell_value": 0.0,
    "pnl": 250.0,
    "realised": 0.0,
    "unrealised": 250.0,
}

RAW_TRADE = {
    "trade_id": "T001",
    "order_id": "O001",
    "exchange": "NSE",
    "trading_symbol": "TCS",
    "instrument_token": "NSE_EQ|TCS",
    "transaction_type": "BUY",
    "product": "D",
    "quantity": 5,
    "average_price": 3200.0,
    "order_timestamp": "2026-05-05T10:30:00",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_config() -> MagicMock:
    """A fully-stubbed Config that passes all attribute accesses."""
    cfg = MagicMock(spec=Config)
    cfg.api_key = "test_api_key"
    cfg.api_secret = "test_api_secret"
    cfg.redirect_uri = "https://localhost/callback"
    cfg.access_token = "test_access_token"
    cfg.base_url = "https://api.upstox.com/v2"
    cfg.cache_ttl_seconds = 0  # disable caching in tests
    cfg.log_level = "DEBUG"
    return cfg


@pytest.fixture
def mock_client() -> MagicMock:
    """A UpstoxClient mock that returns a single holding by default."""
    client = MagicMock(spec=UpstoxClient)
    client.get.return_value = {"status": "success", "data": [RAW_HOLDING]}
    return client


@pytest.fixture
def portfolio_service(mock_client: MagicMock) -> PortfolioService:
    """PortfolioService backed by a mock client (cache disabled)."""
    return PortfolioService(mock_client, cache_ttl=0)


@pytest.fixture
def analysis_service() -> AnalysisService:
    """Real AnalysisService — no mocking needed (pure logic)."""
    return AnalysisService()


@pytest.fixture
def sample_holding() -> Holding:
    return Holding(
        isin="INE009A01021",
        instrument_token="NSE_EQ|INE009A01021",
        trading_symbol="INFY",
        exchange="NSE",
        quantity=10,
        average_price=1500.0,
        last_price=1650.0,
        close_price=1645.0,
        pnl=1500.0,
        day_change=5.0,
        day_change_percentage=0.30,
    )


@pytest.fixture
def sample_position() -> Position:
    return Position(
        instrument_token="NSE_EQ|INE040A01034",
        trading_symbol="HDFCBANK",
        exchange="NSE",
        product="I",
        quantity=5,
        overnight_quantity=0,
        buy_price=1700.0,
        sell_price=0.0,
        buy_value=8500.0,
        sell_value=0.0,
        pnl=250.0,
        realised=0.0,
        unrealised=250.0,
    )
