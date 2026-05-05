"""
Tests for domain models in app.models.portfolio.
"""

import pytest

from app.models.portfolio import ClosedPosition, Position


class TestPosition:
    def _make(self, **kw):
        defaults = dict(
            position_id="p1",
            instrument_id=1,
            instrument_name="Apple",
            instrument_type="stocks",
            direction="Buy",
            amount=1000.0,
            units=5.0,
            open_rate=200.0,
            current_rate=220.0,
            leverage=1,
            unrealised_pnl=100.0,
        )
        defaults.update(kw)
        return Position(**defaults)

    def test_unrealised_pnl_buy(self):
        # unrealised_pnl is now a direct field — API provides it
        p = self._make(unrealised_pnl=100.0)
        assert p.unrealised_pnl == pytest.approx(100.0, abs=1e-4)

    def test_unrealised_pnl_sell(self):
        p = self._make(direction="Sell", unrealised_pnl=50.0)
        assert p.unrealised_pnl == pytest.approx(50.0, abs=1e-4)

    def test_return_percentage(self):
        # pnl=100 / amount=1000 → 10%
        p = self._make(unrealised_pnl=100.0, amount=1000.0)
        assert p.return_percentage == pytest.approx(10.0, abs=1e-2)

    def test_return_percentage_zero_amount(self):
        p = self._make(amount=0.0)
        assert p.return_percentage == 0.0

    def test_current_value(self):
        p = self._make(current_rate=220.0, units=5.0)
        assert p.current_value == pytest.approx(1100.0, abs=1e-4)

    def test_loss_buy(self):
        p = self._make(unrealised_pnl=-100.0, amount=1000.0)
        assert p.unrealised_pnl < 0
        assert p.return_percentage < 0


class TestClosedPosition:
    def _make(self, **kw):
        defaults = dict(
            position_id="cp1",
            instrument_id=2,
            instrument_name="Tesla",
            instrument_type="stocks",
            direction="Buy",
            amount=500.0,
            units=2.0,
            open_rate=230.0,
            close_rate=250.0,
            leverage=1,
            realised_pnl=40.0,
        )
        defaults.update(kw)
        return ClosedPosition(**defaults)

    def test_trade_value(self):
        c = self._make(close_rate=250.0, units=2.0)
        assert c.trade_value == pytest.approx(500.0, abs=1e-4)

    def test_return_percentage(self):
        c = self._make(realised_pnl=40.0, amount=500.0)
        assert c.return_percentage == pytest.approx(8.0, abs=1e-2)

    def test_return_percentage_zero_amount(self):
        c = self._make(amount=0.0)
        assert c.return_percentage == 0.0

    def test_negative_pnl(self):
        c = self._make(realised_pnl=-50.0, amount=500.0)
        assert c.return_percentage < 0
