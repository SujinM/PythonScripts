"""
app/services/analysis_service.py
─────────────────────────────────
Pure analysis functions — no I/O, no external calls.
Input: unified portfolio models. Output: analysis dicts / primitives.
"""

from __future__ import annotations

from app.models.portfolio import Holding, PortfolioSummary


_ALERT_LOSS_THRESHOLD_PCT = -5.0   # flag holdings losing more than 5 %
_ALERT_GAIN_THRESHOLD_PCT = 20.0   # flag holdings gaining more than 20 %


def compute_alerts(holdings: list[Holding]) -> list[dict]:
    """Return a list of alert dicts for holdings outside normal P&L range."""
    alerts = []
    for h in holdings:
        if h.return_pct <= _ALERT_LOSS_THRESHOLD_PCT:
            alerts.append(
                {
                    "symbol": h.trading_symbol,
                    "type": "LOSS_ALERT",
                    "return_pct": h.return_pct,
                    "message": f"{h.trading_symbol} is down {abs(h.return_pct):.2f}%",
                }
            )
        elif h.return_pct >= _ALERT_GAIN_THRESHOLD_PCT:
            alerts.append(
                {
                    "symbol": h.trading_symbol,
                    "type": "GAIN_ALERT",
                    "return_pct": h.return_pct,
                    "message": f"{h.trading_symbol} is up {h.return_pct:.2f}%",
                }
            )
    return alerts


def sector_allocation(holdings: list[Holding]) -> list[dict]:
    """
    Compute investment weight per exchange (proxy for sector allocation).
    Replace with actual sector data when available.
    """
    total = sum(h.current_value for h in holdings) or 1.0
    groups: dict[str, float] = {}
    for h in holdings:
        groups[h.exchange] = groups.get(h.exchange, 0.0) + h.current_value
    return [
        {
            "exchange": exchange,
            "current_value": round(value, 2),
            "weight_pct": round(value / total * 100, 4),
        }
        for exchange, value in sorted(groups.items(), key=lambda x: x[1], reverse=True)
    ]


def build_analysis_result(summary: PortfolioSummary, holdings: list[Holding]) -> dict:
    """Aggregate analysis result for the /analysis endpoint."""
    return {
        "broker": summary.broker,
        "holdings_count": summary.holdings_count,
        "total_invested": summary.total_invested,
        "total_current_value": summary.total_current_value,
        "total_pnl": round(summary.total_unrealised_pnl + summary.total_realised_pnl, 2),
        "overall_return_pct": summary.overall_return_pct,
        "top_gainers": [h.model_dump() for h in summary.top_gainers],
        "top_losers": [h.model_dump() for h in summary.top_losers],
        "alerts": compute_alerts(holdings),
        "sector_allocation": sector_allocation(holdings),
    }
