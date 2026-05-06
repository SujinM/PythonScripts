"""
Analysis service.

Pure business logic — no API calls, no I/O.
Operates on normalized domain models returned by PortfolioService.

Phase 2 extension points (clearly marked below):
  - Sector allocation analysis
  - Diversification scoring
  - Risk metrics (volatility, Sharpe ratio)
  - Moving averages
  - Threshold-based alerts
"""

from typing import Optional

from upstox_app.core.logger import get_logger
from upstox_app.models.portfolio import Holding, PortfolioSummary, Position, Trade

logger = get_logger(__name__)


class AnalysisService:
    """
    Stateless investment analysis service.

    All methods are pure functions of their arguments.  No shared mutable
    state means this class is trivially thread-safe and easy to test.
    """

    # ------------------------------------------------------------------
    # Primary entry point
    # ------------------------------------------------------------------

    def generate_summary(
        self,
        holdings: list[Holding],
        positions: list[Position],
        trades: Optional[list[Trade]] = None,
        top_n: int = 5,
    ) -> PortfolioSummary:
        """
        Compute a full :class:`~app.models.portfolio.PortfolioSummary`.

        Args:
            holdings:  Long-term holdings from PortfolioService.
            positions: Open positions from PortfolioService.
            trades:    Today's trades (optional, not used in summary yet).
            top_n:     How many top gainers / losers to include.

        Returns:
            PortfolioSummary with all Phase 1 metrics populated.
        """
        total_invested = self._total_invested(holdings)
        total_current = self._total_current_value(holdings)
        total_pnl = total_current - total_invested
        return_pct = self._return_percentage(total_invested, total_current)

        summary = PortfolioSummary(
            total_invested=total_invested,
            total_current_value=total_current,
            total_pnl=total_pnl,
            overall_return_pct=return_pct,
            holdings_count=len(holdings),
            positions_count=len(positions),
            top_gainers=self._top_gainers(holdings, n=top_n),
            top_losers=self._top_losers(holdings, n=top_n),
        )

        logger.info(
            "Analysis complete — invested: %.2f | current: %.2f | P&L: %.2f (%.2f%%)",
            total_invested,
            total_current,
            total_pnl,
            return_pct,
        )
        return summary

    # ------------------------------------------------------------------
    # Holdings analysis
    # ------------------------------------------------------------------

    @staticmethod
    def _total_invested(holdings: list[Holding]) -> float:
        """Sum of average_price × quantity across all holdings."""
        return sum(h.invested_value for h in holdings)

    @staticmethod
    def _total_current_value(holdings: list[Holding]) -> float:
        """Sum of last_price × quantity across all holdings."""
        return sum(h.current_value for h in holdings)

    @staticmethod
    def _return_percentage(invested: float, current: float) -> float:
        """Overall percentage return on invested capital."""
        if invested == 0:
            return 0.0
        return ((current - invested) / invested) * 100

    @staticmethod
    def _top_gainers(holdings: list[Holding], n: int = 5) -> list[Holding]:
        """Return the n highest-returning holdings, best first."""
        return sorted(holdings, key=lambda h: h.return_percentage, reverse=True)[:n]

    @staticmethod
    def _top_losers(holdings: list[Holding], n: int = 5) -> list[Holding]:
        """Return the n worst-returning holdings, worst first."""
        return sorted(holdings, key=lambda h: h.return_percentage)[:n]

    # ------------------------------------------------------------------
    # Positions analysis
    # ------------------------------------------------------------------

    @staticmethod
    def analyse_positions_pnl(positions: list[Position]) -> dict[str, float | int]:
        """
        Summarise P&L across all open positions.

        Returns:
            dict with keys: total_pnl, realised, unrealised, positions_count.
        """
        return {
            "total_pnl": sum(p.pnl for p in positions),
            "realised": sum(p.realised for p in positions),
            "unrealised": sum(p.unrealised for p in positions),
            "positions_count": len(positions),
        }

    # ------------------------------------------------------------------
    # Trade analysis
    # ------------------------------------------------------------------

    @staticmethod
    def analyse_trade_volume(trades: list[Trade]) -> dict[str, float | int]:
        """
        Break down today's trade activity by direction.

        Returns:
            dict with keys: total_trades, buy_trades, sell_trades,
            buy_value, sell_value.
        """
        buy_trades = [t for t in trades if t.transaction_type == "BUY"]
        sell_trades = [t for t in trades if t.transaction_type == "SELL"]
        return {
            "total_trades": len(trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "buy_value": sum(t.trade_value for t in buy_trades),
            "sell_value": sum(t.trade_value for t in sell_trades),
        }

    # ------------------------------------------------------------------
    # Phase 2 stubs — implement these in the next iteration
    # ------------------------------------------------------------------

    @staticmethod
    def analyse_sector_allocation(holdings: list[Holding]) -> dict[str, float]:
        """
        [Phase 2] Compute sector allocation as a percentage of total portfolio.

        Requires Holding.sector to be populated.
        Returns a dict mapping sector name → percentage of portfolio value.
        """
        holdings_with_sector = [h for h in holdings if h.sector]
        if not holdings_with_sector:
            return {}

        total_value = sum(h.current_value for h in holdings_with_sector)
        if total_value == 0:
            return {}

        allocation: dict[str, float] = {}
        for h in holdings_with_sector:
            allocation[h.sector] = allocation.get(h.sector, 0.0) + h.current_value  # type: ignore[index]

        return {sector: (val / total_value) * 100 for sector, val in allocation.items()}

    @staticmethod
    def compute_diversification_score(holdings: list[Holding]) -> float:
        """
        [Phase 2] Return a simple diversification score (0–100).

        Higher = more diversified.  Currently uses a naive count-based proxy;
        replace with HHI (Herfindahl–Hirschman Index) for production use.
        """
        if not holdings:
            return 0.0
        # Placeholder: 100 points spread across sqrt(n) unique names
        import math
        return min(100.0, math.sqrt(len(holdings)) * 10)

    @staticmethod
    def check_alerts(
        holdings: list[Holding],
        gain_threshold: float = 20.0,
        loss_threshold: float = -10.0,
    ) -> list[dict[str, str | float]]:
        """
        [Phase 2] Return holdings that have breached gain or loss thresholds.

        Args:
            holdings:        Portfolio holdings to scan.
            gain_threshold:  Alert when return_percentage ≥ this value.
            loss_threshold:  Alert when return_percentage ≤ this value.

        Returns:
            List of alert dicts: {symbol, return_pct, alert_type}.
        """
        alerts = []
        for h in holdings:
            if h.return_percentage >= gain_threshold:
                alerts.append(
                    {
                        "symbol": h.trading_symbol,
                        "return_pct": h.return_percentage,
                        "alert_type": "PROFIT_TARGET",
                    }
                )
            elif h.return_percentage <= loss_threshold:
                alerts.append(
                    {
                        "symbol": h.trading_symbol,
                        "return_pct": h.return_percentage,
                        "alert_type": "STOP_LOSS",
                    }
                )
        return alerts
