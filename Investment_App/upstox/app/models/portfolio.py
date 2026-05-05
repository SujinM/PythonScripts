"""
Domain data models for portfolio entities.

These are plain dataclasses — no ORM, no serialization magic.
All computed properties (e.g. return %) live here so services stay thin.

Phase 2 extensibility:
  - Add `sector` / `asset_class` to Holding for sector-allocation analysis.
  - Add `historical_prices: list[float]` to Holding for moving-average support.
  - Swap dataclasses for Pydantic BaseModel for automatic validation if needed.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Holdings (long-term portfolio)
# ---------------------------------------------------------------------------


@dataclass
class Holding:
    """
    Represents a long-term holding fetched from
    ``GET /portfolio/long-term-holdings``.
    """

    isin: str
    instrument_token: str
    trading_symbol: str
    exchange: str
    quantity: int
    average_price: float
    last_price: float
    close_price: float
    pnl: float
    day_change: float
    day_change_percentage: float

    # Optional — populated if sector data is available (Phase 2)
    sector: Optional[str] = None

    # ------------------------------------------------------------------
    # Computed properties — derived from the fields above
    # ------------------------------------------------------------------

    @property
    def invested_value(self) -> float:
        """Total capital deployed: average_price × quantity."""
        return self.average_price * self.quantity

    @property
    def current_value(self) -> float:
        """Mark-to-market value: last_price × quantity."""
        return self.last_price * self.quantity

    @property
    def unrealised_pnl(self) -> float:
        """Unrealised profit/loss in absolute terms."""
        return self.current_value - self.invested_value

    @property
    def return_percentage(self) -> float:
        """Percentage return on invested capital."""
        if self.invested_value == 0:
            return 0.0
        return (self.unrealised_pnl / self.invested_value) * 100


# ---------------------------------------------------------------------------
# Positions (intraday / short-term)
# ---------------------------------------------------------------------------


@dataclass
class Position:
    """
    Represents an open position fetched from
    ``GET /portfolio/short-term-positions``.
    """

    instrument_token: str
    trading_symbol: str
    exchange: str
    product: str          # "D" = Delivery, "I" = Intraday, "CO", "OCO"
    quantity: int
    overnight_quantity: int
    buy_price: float
    sell_price: float
    buy_value: float
    sell_value: float
    pnl: float
    realised: float
    unrealised: float

    @property
    def net_quantity(self) -> int:
        """Net open quantity (positive = long, negative = short)."""
        return self.quantity


# ---------------------------------------------------------------------------
# Trades (executed orders)
# ---------------------------------------------------------------------------


@dataclass
class Trade:
    """
    Represents a single executed trade fetched from
    ``GET /order/trades/get-trades-for-day``.
    """

    trade_id: str
    order_id: str
    exchange: str
    trading_symbol: str
    instrument_token: str
    transaction_type: str    # "BUY" or "SELL"
    product: str
    quantity: int
    price: float
    trade_date: Optional[datetime] = None

    @property
    def trade_value(self) -> float:
        """Gross trade value: price × quantity."""
        return self.price * self.quantity


# ---------------------------------------------------------------------------
# Aggregated analysis output
# ---------------------------------------------------------------------------


@dataclass
class PortfolioSummary:
    """
    Aggregated portfolio analysis result returned by AnalysisService.

    Designed for extension in Phase 2:
      - sector_allocation: populated by a SectorAnalyzer
      - diversification_score: populated by a DiversificationAnalyzer
      - risk_metrics: populated by a RiskAnalyzer
    """

    total_invested: float
    total_current_value: float
    total_pnl: float
    overall_return_pct: float
    holdings_count: int
    positions_count: int

    # Ranked sub-lists (populated by AnalysisService)
    top_gainers: list[Holding] = field(default_factory=list)
    top_losers: list[Holding] = field(default_factory=list)

    # Phase 2 placeholders — kept here so the model is stable
    sector_allocation: dict[str, float] = field(default_factory=dict)
    diversification_score: Optional[float] = None
    risk_metrics: dict[str, float] = field(default_factory=dict)
