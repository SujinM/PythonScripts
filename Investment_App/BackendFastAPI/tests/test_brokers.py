"""tests/test_brokers.py — broker adapter unit tests."""

from __future__ import annotations

import pytest

from app.brokers.base import IBrokerAdapter
from app.brokers.registry import BrokerRegistry
from app.core.exceptions import BrokerNotFoundError
from tests.conftest import MockBrokerAdapter


class TestBrokerRegistry:
    def test_register_and_get(self):
        reg = BrokerRegistry()
        adapter = MockBrokerAdapter()
        reg.register(adapter)
        assert reg.get("mock") is adapter

    def test_get_unknown_raises(self):
        reg = BrokerRegistry()
        with pytest.raises(BrokerNotFoundError):
            reg.get("ghost")

    def test_ids_returns_list(self):
        reg = BrokerRegistry()
        reg.register(MockBrokerAdapter())
        assert "mock" in reg.ids()

    def test_all_returns_list(self):
        reg = BrokerRegistry()
        reg.register(MockBrokerAdapter())
        assert len(reg.all()) == 1

    def test_len(self):
        reg = BrokerRegistry()
        reg.register(MockBrokerAdapter())
        assert len(reg) == 1

    def test_iter(self):
        reg = BrokerRegistry()
        reg.register(MockBrokerAdapter())
        adapters = list(reg)
        assert len(adapters) == 1
        assert isinstance(adapters[0], IBrokerAdapter)


class TestMockAdapter:
    def test_broker_id(self):
        assert MockBrokerAdapter().broker_id == "mock"

    def test_display_name(self):
        assert MockBrokerAdapter().display_name == "Mock Broker"

    def test_get_holdings(self):
        holdings = MockBrokerAdapter().get_holdings()
        assert len(holdings) == 2

    def test_get_positions(self):
        positions = MockBrokerAdapter().get_positions()
        assert len(positions) == 1

    def test_get_trades(self):
        trades = MockBrokerAdapter().get_trades()
        assert len(trades) == 1


class TestHoldingComputedFields:
    def test_invested_value(self):
        from tests.conftest import SAMPLE_HOLDING
        assert SAMPLE_HOLDING.invested_value == 10 * 100.0

    def test_current_value(self):
        from tests.conftest import SAMPLE_HOLDING
        assert SAMPLE_HOLDING.current_value == 10 * 120.0

    def test_unrealised_pnl(self):
        from tests.conftest import SAMPLE_HOLDING
        assert SAMPLE_HOLDING.unrealised_pnl == 200.0

    def test_return_pct(self):
        from tests.conftest import SAMPLE_HOLDING
        assert SAMPLE_HOLDING.return_pct == 20.0


class TestPositionComputedFields:
    def test_total_pnl(self):
        from tests.conftest import SAMPLE_POSITION
        assert SAMPLE_POSITION.total_pnl == 75.0


class TestTradeComputedFields:
    def test_trade_value(self):
        from tests.conftest import SAMPLE_TRADE
        assert SAMPLE_TRADE.trade_value == 1000.0
