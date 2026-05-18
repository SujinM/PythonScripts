"""Basic smoke tests for InvestCalc calculations."""

import pytest
from investcalc.calculations.price import PriceCalculator
from investcalc.calculations.returns import ReturnsCalculator
from investcalc.calculations.risk import RiskCalculator
from investcalc.calculations.position import PositionCalculator
from investcalc.calculations.options import OptionsCalculator


class TestPriceCalculator:
    def test_price_difference(self):
        r = PriceCalculator.price_difference(100, 115)
        assert r.value == 15.0

    def test_percentage_up(self):
        r = PriceCalculator.percentage_change(100, 120)
        assert r.value == pytest.approx(20.0)
        assert "UP" in r.label

    def test_percentage_down(self):
        r = PriceCalculator.percentage_change(200, 150)
        assert r.value == pytest.approx(-25.0)
        assert "DOWN" in r.label

    def test_stop_loss(self):
        r = PriceCalculator.stop_loss_price(100, 5)
        assert r.value == pytest.approx(95.0)

    def test_take_profit(self):
        r = PriceCalculator.take_profit_price(100, 10)
        assert r.value == pytest.approx(110.0)

    def test_pivot_points(self):
        pp = PriceCalculator.pivot_points(high=110, low=90, close=100)
        assert "PP" in pp
        assert pp["PP"] == pytest.approx(100.0)

    def test_moving_average(self):
        ma = PriceCalculator.moving_average([100, 200, 300])
        assert ma == pytest.approx(200.0)


class TestReturnsCalculator:
    def test_profit_loss(self):
        r = ReturnsCalculator.profit_loss(100, 120, 10)
        assert r["P&L"] == pytest.approx(200.0)

    def test_cagr(self):
        r = ReturnsCalculator.cagr(1000, 2000, 5)
        assert r.value == pytest.approx(14.8698, abs=0.01)

    def test_roi(self):
        r = ReturnsCalculator.roi(1000, 1200)
        assert r.value == pytest.approx(20.0)

    def test_dividend_yield(self):
        r = ReturnsCalculator.dividend_yield(10, 200)
        assert r.value == pytest.approx(5.0)


class TestRiskCalculator:
    def test_risk_reward(self):
        r = RiskCalculator.risk_reward_ratio(100, 90, 130)
        assert r.value == pytest.approx(3.0)

    def test_volatility(self):
        r = RiskCalculator.volatility([100, 102, 101, 105, 103])
        assert r.value > 0

    def test_max_drawdown(self):
        r = RiskCalculator.max_drawdown([100, 120, 80, 90])
        assert r.value == pytest.approx(33.3333, abs=0.01)


class TestPositionCalculator:
    def test_average_buy_price(self):
        r = PositionCalculator.average_buy_price([(100, 10), (120, 10)])
        assert r["Average Buy Price"] == pytest.approx(110.0)

    def test_unrealised_pnl(self):
        r = PositionCalculator.unrealised_pnl(100, 130, 10)
        assert r["Unrealised P&L"] == pytest.approx(300.0)


class TestOptionsCalculator:
    def test_intrinsic_call(self):
        r = OptionsCalculator.intrinsic_value("call", 110, 100)
        assert r["Intrinsic Value"] == pytest.approx(10.0)
        assert r["In The Money"] is True

    def test_intrinsic_put_otm(self):
        r = OptionsCalculator.intrinsic_value("put", 110, 100)
        assert r["Intrinsic Value"] == 0.0
        assert r["In The Money"] is False

    def test_black_scholes_call(self):
        r = OptionsCalculator.black_scholes("call", S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert r["Price"] == pytest.approx(10.4506, abs=0.01)
