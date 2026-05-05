"""
Unit tests for AnalysisService.

Pure business logic — no mocks, no network.
"""

from datetime import datetime

import pytest

from app.models.portfolio import Holding, Position, Trade
from app.services.analysis_service import AnalysisService


# ---------------------------------------------------------------------------
# Test factories
# ---------------------------------------------------------------------------


def make_holding(
    symbol: str,
    qty: int,
    avg_price: float,
    last_price: float,
    sector: str | None = None,
) -> Holding:
    return Holding(
        isin=f"TEST{symbol}",
        instrument_token=f"NSE_EQ|{symbol}",
        trading_symbol=symbol,
        exchange="NSE",
        quantity=qty,
        average_price=avg_price,
        last_price=last_price,
        close_price=last_price,
        pnl=(last_price - avg_price) * qty,
        day_change=0.0,
        day_change_percentage=0.0,
        sector=sector,
    )


def make_position(symbol: str, pnl: float, realised: float = 0.0) -> Position:
    return Position(
        instrument_token=f"NSE_EQ|{symbol}",
        trading_symbol=symbol,
        exchange="NSE",
        product="I",
        quantity=5,
        overnight_quantity=0,
        buy_price=100.0,
        sell_price=0.0,
        buy_value=500.0,
        sell_value=0.0,
        pnl=pnl,
        realised=realised,
        unrealised=pnl - realised,
    )


def make_trade(symbol: str, tx_type: str, qty: int, price: float) -> Trade:
    return Trade(
        trade_id=f"T_{symbol}",
        order_id=f"O_{symbol}",
        exchange="NSE",
        trading_symbol=symbol,
        instrument_token=f"NSE_EQ|{symbol}",
        transaction_type=tx_type,
        product="D",
        quantity=qty,
        price=price,
        trade_date=datetime.now(),
    )


# ---------------------------------------------------------------------------
# generate_summary tests
# ---------------------------------------------------------------------------


class TestGenerateSummary:
    def test_total_invested(self, analysis_service: AnalysisService) -> None:
        holdings = [
            make_holding("INFY", 10, 1500, 1650),
            make_holding("TCS", 5, 3000, 2800),
        ]
        summary = analysis_service.generate_summary(holdings, [])
        expected = 10 * 1500 + 5 * 3000
        assert summary.total_invested == pytest.approx(expected)

    def test_total_current_value(self, analysis_service: AnalysisService) -> None:
        holdings = [
            make_holding("INFY", 10, 1500, 1650),
            make_holding("TCS", 5, 3000, 2800),
        ]
        summary = analysis_service.generate_summary(holdings, [])
        expected = 10 * 1650 + 5 * 2800
        assert summary.total_current_value == pytest.approx(expected)

    def test_total_pnl(self, analysis_service: AnalysisService) -> None:
        holdings = [make_holding("INFY", 10, 1000, 1200)]
        summary = analysis_service.generate_summary(holdings, [])
        assert summary.total_pnl == pytest.approx(2000.0)

    def test_overall_return_percentage(self, analysis_service: AnalysisService) -> None:
        holdings = [make_holding("INFY", 10, 1000, 1200)]
        summary = analysis_service.generate_summary(holdings, [])
        assert summary.overall_return_pct == pytest.approx(20.0)

    def test_zero_invested_return_is_zero(self, analysis_service: AnalysisService) -> None:
        summary = analysis_service.generate_summary([], [])
        assert summary.overall_return_pct == 0.0

    def test_holdings_and_positions_count(self, analysis_service: AnalysisService) -> None:
        h = [make_holding("A", 1, 100, 110)]
        p = [make_position("B", 50), make_position("C", -30)]
        summary = analysis_service.generate_summary(h, p)
        assert summary.holdings_count == 1
        assert summary.positions_count == 2

    def test_top_gainers_sorted_descending(self, analysis_service: AnalysisService) -> None:
        holdings = [
            make_holding("A", 1, 100, 150),  # +50 %
            make_holding("B", 1, 100, 120),  # +20 %
            make_holding("C", 1, 100, 80),   # -20 %
        ]
        summary = analysis_service.generate_summary(holdings, [], top_n=2)
        assert summary.top_gainers[0].trading_symbol == "A"
        assert summary.top_gainers[1].trading_symbol == "B"

    def test_top_losers_sorted_ascending(self, analysis_service: AnalysisService) -> None:
        holdings = [
            make_holding("A", 1, 100, 150),  # +50 %
            make_holding("B", 1, 100, 70),   # -30 %
            make_holding("C", 1, 100, 80),   # -20 %
        ]
        summary = analysis_service.generate_summary(holdings, [], top_n=2)
        assert summary.top_losers[0].trading_symbol == "B"
        assert summary.top_losers[1].trading_symbol == "C"

    def test_top_n_capped_to_holdings_length(self, analysis_service: AnalysisService) -> None:
        holdings = [make_holding("A", 1, 100, 110)]
        summary = analysis_service.generate_summary(holdings, [], top_n=10)
        assert len(summary.top_gainers) == 1
        assert len(summary.top_losers) == 1


# ---------------------------------------------------------------------------
# analyse_positions_pnl
# ---------------------------------------------------------------------------


class TestAnalysePositionsPnl:
    def test_aggregates_correctly(self, analysis_service: AnalysisService) -> None:
        positions = [make_position("A", 300, realised=100), make_position("B", -150)]
        result = analysis_service.analyse_positions_pnl(positions)
        assert result["total_pnl"] == pytest.approx(150.0)
        assert result["realised"] == pytest.approx(100.0)
        assert result["unrealised"] == pytest.approx(50.0)  # (300-100) + (-150-0)
        assert result["positions_count"] == 2

    def test_empty_positions(self, analysis_service: AnalysisService) -> None:
        result = analysis_service.analyse_positions_pnl([])
        assert result["total_pnl"] == 0.0
        assert result["positions_count"] == 0


# ---------------------------------------------------------------------------
# analyse_trade_volume
# ---------------------------------------------------------------------------


class TestAnalyseTradeVolume:
    def test_buy_sell_split(self, analysis_service: AnalysisService) -> None:
        trades = [
            make_trade("INFY", "BUY", 10, 1500),
            make_trade("TCS", "SELL", 5, 3000),
        ]
        result = analysis_service.analyse_trade_volume(trades)
        assert result["total_trades"] == 2
        assert result["buy_trades"] == 1
        assert result["sell_trades"] == 1
        assert result["buy_value"] == pytest.approx(15_000.0)
        assert result["sell_value"] == pytest.approx(15_000.0)

    def test_empty_trades(self, analysis_service: AnalysisService) -> None:
        result = analysis_service.analyse_trade_volume([])
        assert result["total_trades"] == 0
        assert result["buy_value"] == 0.0


# ---------------------------------------------------------------------------
# check_alerts
# ---------------------------------------------------------------------------


class TestCheckAlerts:
    def test_profit_target_triggered(self, analysis_service: AnalysisService) -> None:
        holdings = [make_holding("INFY", 1, 100, 125)]  # +25 %
        alerts = analysis_service.check_alerts(holdings, gain_threshold=20.0, loss_threshold=-10.0)
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "PROFIT_TARGET"
        assert alerts[0]["symbol"] == "INFY"

    def test_stop_loss_triggered(self, analysis_service: AnalysisService) -> None:
        holdings = [make_holding("WIPRO", 1, 100, 85)]  # -15 %
        alerts = analysis_service.check_alerts(holdings, gain_threshold=20.0, loss_threshold=-10.0)
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "STOP_LOSS"

    def test_no_alert_within_thresholds(self, analysis_service: AnalysisService) -> None:
        holdings = [make_holding("HCL", 1, 100, 105)]  # +5 %
        alerts = analysis_service.check_alerts(holdings, gain_threshold=20.0, loss_threshold=-10.0)
        assert alerts == []

    def test_multiple_alerts(self, analysis_service: AnalysisService) -> None:
        holdings = [
            make_holding("A", 1, 100, 130),  # +30 % → PROFIT_TARGET
            make_holding("B", 1, 100, 85),   # -15 % → STOP_LOSS
            make_holding("C", 1, 100, 105),  # +5  % → no alert
        ]
        alerts = analysis_service.check_alerts(holdings, gain_threshold=20.0, loss_threshold=-10.0)
        assert len(alerts) == 2


# ---------------------------------------------------------------------------
# analyse_sector_allocation (Phase 2 stub)
# ---------------------------------------------------------------------------


class TestSectorAllocation:
    def test_allocation_percentages_sum_to_100(
        self, analysis_service: AnalysisService
    ) -> None:
        holdings = [
            make_holding("INFY", 10, 1000, 1000, sector="IT"),
            make_holding("TCS", 10, 1000, 1000, sector="IT"),
            make_holding("HDFC", 10, 1000, 1000, sector="Finance"),
        ]
        alloc = analysis_service.analyse_sector_allocation(holdings)
        assert sum(alloc.values()) == pytest.approx(100.0)

    def test_no_sector_data_returns_empty(self, analysis_service: AnalysisService) -> None:
        holdings = [make_holding("INFY", 1, 100, 110)]  # sector=None
        alloc = analysis_service.analyse_sector_allocation(holdings)
        assert alloc == {}
