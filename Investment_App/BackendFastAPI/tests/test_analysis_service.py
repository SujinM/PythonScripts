"""tests/test_analysis_service.py"""

from __future__ import annotations

from app.services import analysis_service
from tests.conftest import SAMPLE_HOLDING, SAMPLE_HOLDING_LOSS


class TestComputeAlerts:
    def test_loss_alert_triggered(self):
        alerts = analysis_service.compute_alerts([SAMPLE_HOLDING_LOSS])
        assert len(alerts) == 1
        assert alerts[0]["type"] == "LOSS_ALERT"
        assert alerts[0]["symbol"] == "XYZ"

    def test_no_alert_for_normal_holding(self):
        from app.models.portfolio import Holding

        normal = Holding(
            broker="mock",
            instrument_key="NSE_EQ|NRM",
            trading_symbol="NRM",
            exchange="NSE",
            quantity=10,
            average_price=100.0,
            last_price=105.0,  # +5% — within thresholds
            close_price=104.0,
        )
        alerts = analysis_service.compute_alerts([normal])
        assert alerts == []

    def test_gain_alert_triggered(self):
        from app.models.portfolio import Holding

        big_gainer = Holding(
            broker="mock",
            instrument_key="X",
            trading_symbol="MOON",
            exchange="NSE",
            quantity=10,
            average_price=100.0,
            last_price=130.0,  # +30% — triggers GAIN_ALERT
            close_price=125.0,
        )
        alerts = analysis_service.compute_alerts([big_gainer])
        assert len(alerts) == 1
        assert alerts[0]["type"] == "GAIN_ALERT"

    def test_multiple_holdings_multiple_alerts(self):
        alerts = analysis_service.compute_alerts([SAMPLE_HOLDING, SAMPLE_HOLDING_LOSS])
        types = {a["type"] for a in alerts}
        assert "LOSS_ALERT" in types


class TestSectorAllocation:
    def test_returns_list(self):
        result = analysis_service.sector_allocation([SAMPLE_HOLDING, SAMPLE_HOLDING_LOSS])
        assert isinstance(result, list)
        assert all("exchange" in r for r in result)

    def test_weights_sum_to_100(self):
        result = analysis_service.sector_allocation([SAMPLE_HOLDING, SAMPLE_HOLDING_LOSS])
        total_weight = sum(r["weight_pct"] for r in result)
        assert abs(total_weight - 100.0) < 0.01

    def test_empty_holdings(self):
        result = analysis_service.sector_allocation([])
        assert result == []


class TestBuildAnalysisResult:
    def test_result_keys(self, portfolio_service):
        summary = portfolio_service.get_summary("mock")
        holdings = portfolio_service.get_holdings("mock")
        result = analysis_service.build_analysis_result(summary, holdings)
        expected_keys = {
            "broker", "holdings_count", "total_invested", "total_current_value",
            "total_pnl", "overall_return_pct", "top_gainers", "top_losers",
            "alerts", "sector_allocation",
        }
        assert expected_keys.issubset(result.keys())
