"""
tests/conftest.py
─────────────────
Shared fixtures for the BackendFastAPI test suite.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.brokers.base import IBrokerAdapter
from app.brokers.registry import BrokerRegistry
from app.core.cache import InMemoryCache
from app.models.portfolio import Holding, Position, Trade
from app.services.portfolio_service import PortfolioService


# ── Sample data ───────────────────────────────────────────────────────────────

SAMPLE_HOLDING = Holding(
    broker="mock",
    instrument_key="NSE_EQ|ABC",
    trading_symbol="ABC",
    exchange="NSE",
    isin="INE000A01000",
    quantity=10,
    average_price=100.0,
    last_price=120.0,
    close_price=118.0,
)

SAMPLE_HOLDING_LOSS = Holding(
    broker="mock",
    instrument_key="NSE_EQ|XYZ",
    trading_symbol="XYZ",
    exchange="NSE",
    quantity=5,
    average_price=200.0,
    last_price=185.0,   # -7.5% — triggers LOSS_ALERT
    close_price=188.0,
)

SAMPLE_POSITION = Position(
    broker="mock",
    instrument_key="NSE_EQ|ABC",
    trading_symbol="ABC",
    exchange="NSE",
    product="INTRADAY",
    quantity=5,
    buy_price=110.0,
    sell_price=0.0,
    last_price=115.0,
    realised_pnl=50.0,
    unrealised_pnl=25.0,
)

SAMPLE_TRADE = Trade(
    broker="mock",
    instrument_key="NSE_EQ|ABC",
    trading_symbol="ABC",
    exchange="NSE",
    product="DELIVERY",
    transaction_type="BUY",
    quantity=10,
    price=100.0,
)


# ── Mock broker adapter ───────────────────────────────────────────────────────

class MockBrokerAdapter(IBrokerAdapter):
    @property
    def broker_id(self) -> str:
        return "mock"

    @property
    def display_name(self) -> str:
        return "Mock Broker"

    def get_holdings(self) -> list[Holding]:
        return [SAMPLE_HOLDING, SAMPLE_HOLDING_LOSS]

    def get_positions(self) -> list[Position]:
        return [SAMPLE_POSITION]

    def get_trades(self) -> list[Trade]:
        return [SAMPLE_TRADE]


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def mock_adapter() -> MockBrokerAdapter:
    return MockBrokerAdapter()


@pytest.fixture()
def mock_registry(mock_adapter) -> BrokerRegistry:
    reg = BrokerRegistry()
    reg.register(mock_adapter)
    return reg


@pytest.fixture()
def cache() -> InMemoryCache:
    return InMemoryCache()


@pytest.fixture()
def portfolio_service(mock_registry, cache) -> PortfolioService:
    return PortfolioService(registry=mock_registry, cache=cache)


@pytest.fixture()
def test_client(mock_registry, cache) -> TestClient:
    """TestClient with broker adapters swapped for mocks."""
    from app.main import create_app
    from app.api import deps

    app = create_app()

    def _override_svc():
        return PortfolioService(registry=mock_registry, cache=cache)

    app.dependency_overrides[deps.get_portfolio_service] = _override_svc
    return TestClient(app)
