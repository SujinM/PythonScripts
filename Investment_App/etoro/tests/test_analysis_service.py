"""
Tests for AnalysisService.
"""

import pytest

from app.services.analysis_service import AnalysisService
from tests.conftest import make_closed_position, make_position


class TestGenerateSummary:
    def test_totals_calculated_correctly(self, sample_positions, sample_closed):
        svc = AnalysisService()
        summary = svc.generate_summary(sample_positions, sample_closed)

        # total_invested = sum(p.amount)
        expected_invested = sum(p.amount for p in sample_positions)
        assert summary.total_invested == round(expected_invested, 2)

    def test_positions_count(self, sample_positions, sample_closed):
        svc = AnalysisService()
        summary = svc.generate_summary(sample_positions, sample_closed)
        assert summary.positions_count == len(sample_positions)
        assert summary.closed_positions_count == len(sample_closed)

    def test_empty_portfolio(self):
        svc = AnalysisService()
        summary = svc.generate_summary([], [])
        assert summary.total_invested == 0.0
        assert summary.total_pnl == 0.0
        assert summary.overall_return_pct == 0.0
        assert summary.positions_count == 0

    def test_top_gainers_sorted(self):
        p1 = make_position(position_id="a", amount=100.0, units=1.0, unrealised_pnl=30.0)
        p2 = make_position(position_id="b", amount=100.0, units=1.0, unrealised_pnl=10.0)
        svc = AnalysisService()
        summary = svc.generate_summary([p1, p2], [])
        assert summary.top_gainers[0].position_id == "a"

    def test_top_losers_sorted(self):
        p1 = make_position(position_id="a", amount=100.0, units=1.0, unrealised_pnl=-20.0)
        p2 = make_position(position_id="b", amount=100.0, units=1.0, unrealised_pnl=-10.0)
        svc = AnalysisService()
        summary = svc.generate_summary([p1, p2], [])
        assert summary.top_losers[0].position_id == "a"

    def test_top_n_respected(self):
        positions = [
            make_position(position_id=str(i), amount=100.0, units=1.0, unrealised_pnl=float(i))
            for i in range(10)
        ]
        svc = AnalysisService()
        summary = svc.generate_summary(positions, [], top_n=3)
        assert len(summary.top_gainers) <= 3
        assert len(summary.top_losers) <= 3


class TestCheckAlerts:
    def test_gain_alert_triggered(self):
        p = make_position(amount=100.0, units=1.0, unrealised_pnl=25.0)
        alerts = AnalysisService.check_alerts([p], gain_threshold=20.0, loss_threshold=-10.0)
        assert len(alerts) == 1
        assert alerts[0]["type"] == "GAIN"

    def test_loss_alert_triggered(self):
        p = make_position(amount=100.0, units=1.0, unrealised_pnl=-15.0)
        alerts = AnalysisService.check_alerts([p], gain_threshold=20.0, loss_threshold=-10.0)
        assert len(alerts) == 1
        assert alerts[0]["type"] == "LOSS"

    def test_no_alert_within_band(self):
        p = make_position(amount=100.0, units=1.0, unrealised_pnl=5.0)
        alerts = AnalysisService.check_alerts([p], gain_threshold=20.0, loss_threshold=-10.0)
        assert alerts == []

    def test_empty_positions(self):
        assert AnalysisService.check_alerts([]) == []


class TestAnalyseByType:
    def test_groups_by_type(self, sample_positions):
        result = AnalysisService.analyse_by_type(sample_positions)
        assert "stocks" in result
        assert "crypto" in result
        assert "currencies" in result

    def test_count_per_type(self, sample_positions):
        result = AnalysisService.analyse_by_type(sample_positions)
        assert result["stocks"]["count"] == 1
        assert result["crypto"]["count"] == 1

    def test_empty(self):
        assert AnalysisService.analyse_by_type([]) == {}
