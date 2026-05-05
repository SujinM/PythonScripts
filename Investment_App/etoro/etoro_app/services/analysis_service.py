"""
Analysis service.

Pure business logic — no API calls, no I/O.
Operates on normalized domain models returned by PortfolioService.
"""

from etoro_app.core.logger import get_logger
from etoro_app.models.portfolio import ClosedPosition, PortfolioSummary, Position

logger = get_logger(__name__)


class AnalysisService:
    """
    Stateless eToro portfolio analysis service.

    All methods are pure functions of their arguments — thread-safe and trivially testable.
    """

    def generate_summary(
        self,
        positions: list[Position],
        closed_positions: list[ClosedPosition],
        top_n: int = 5,
    ) -> PortfolioSummary:
        """Compute a full PortfolioSummary from open and closed positions."""
        total_invested = sum(p.amount for p in positions)
        total_current = sum(p.current_value for p in positions)
        total_pnl = sum(p.unrealised_pnl for p in positions)
        return_pct = (
            round(total_pnl / total_invested * 100, 4) if total_invested else 0.0
        )

        summary = PortfolioSummary(
            total_invested=round(total_invested, 2),
            total_current_value=round(total_current, 2),
            total_pnl=round(total_pnl, 2),
            overall_return_pct=return_pct,
            positions_count=len(positions),
            closed_positions_count=len(closed_positions),
            top_gainers=self._top_gainers(positions, n=top_n),
            top_losers=self._top_losers(positions, n=top_n),
        )
        logger.info(
            "Analysis complete — invested: %.2f | current: %.2f | P&L: %.2f (%.2f%%)",
            total_invested,
            total_current,
            total_pnl,
            return_pct,
        )
        return summary

    @staticmethod
    def _top_gainers(positions: list[Position], n: int = 5) -> list[Position]:
        return sorted(positions, key=lambda p: p.return_percentage, reverse=True)[:n]

    @staticmethod
    def _top_losers(positions: list[Position], n: int = 5) -> list[Position]:
        return sorted(positions, key=lambda p: p.return_percentage)[:n]

    @staticmethod
    def check_alerts(
        positions: list[Position],
        gain_threshold: float = 20.0,
        loss_threshold: float = -10.0,
    ) -> list[dict]:
        """Return positions that have breached gain or loss thresholds."""
        alerts = []
        for p in positions:
            if p.return_percentage >= gain_threshold:
                alerts.append({
                    "type": "GAIN",
                    "instrument": p.instrument_name,
                    "return_pct": p.return_percentage,
                    "message": f"{p.instrument_name} is up {p.return_percentage:.2f}%",
                })
            elif p.return_percentage <= loss_threshold:
                alerts.append({
                    "type": "LOSS",
                    "instrument": p.instrument_name,
                    "return_pct": p.return_percentage,
                    "message": f"{p.instrument_name} is down {abs(p.return_percentage):.2f}%",
                })
        return alerts

    @staticmethod
    def analyse_by_type(positions: list[Position]) -> dict[str, dict]:
        """Break down positions by instrument_type (stocks, crypto, etf, etc.)."""
        groups: dict[str, list[Position]] = {}
        for p in positions:
            groups.setdefault(p.instrument_type, []).append(p)

        result = {}
        for asset_type, group in groups.items():
            total_invested = sum(p.amount for p in group)
            total_pnl = sum(p.unrealised_pnl for p in group)
            result[asset_type] = {
                "count": len(group),
                "total_invested": round(total_invested, 2),
                "total_pnl": round(total_pnl, 2),
            }
        return result
