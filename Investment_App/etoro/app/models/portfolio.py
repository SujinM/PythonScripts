"""
Domain data models for eToro portfolio entities.

These are plain dataclasses — no ORM, no serialization magic.

eToro Public API field mapping
------------------------------
Position (from GET /api/v1/trading/info/real/pnl → clientPortfolio.positions):
  positionID    → position_id
  instrumentID  → instrument_id
  isBuy         → direction ("Buy" / "Sell")
  openRate      → open_rate
  closeRate     → current_rate  (current market price — eToro naming is misleading)
  pnL           → unrealised_pnl (direct from API; includes fees/overnight charges)
  openDateTime  → open_date
  mirrorID > 0  → is_copy

ClosedPosition (from GET /api/v1/trading/info/trade/history):
  positionId    → position_id
  instrumentId  → instrument_id
  isBuy         → direction
  openRate      → open_rate
  closeRate     → close_rate
  netProfit     → realised_pnl
  investment    → amount
  openTimestamp → open_date
  closeTimestamp→ close_date
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Open Position (eToro "portfolio position")
# ---------------------------------------------------------------------------


@dataclass
class Position:
    """
    Represents a single open position fetched from
    ``GET /api/v1/trading/info/real/pnl`` → ``clientPortfolio.positions``.
    """

    position_id: str
    instrument_id: int
    instrument_name: str            # resolved from instrument metadata or "Instrument #<id>"
    instrument_type: str            # "stocks", "crypto", "etf", "currencies", etc.
    direction: str                  # "Buy" or "Sell"  (from isBuy field)
    amount: float                   # invested amount in USD
    units: float                    # number of units / shares
    open_rate: float                # price at which position was opened
    current_rate: float             # latest market price (eToro "closeRate" field)
    leverage: int                   # 1 = no leverage
    unrealised_pnl: float           # direct from API "pnL" field (includes fees)
    open_date: Optional[datetime] = None
    is_copy: bool = False           # True if mirrorID > 0 (copy-trade position)

    @property
    def return_percentage(self) -> float:
        """Percentage return on invested amount."""
        if self.amount == 0:
            return 0.0
        return round(self.unrealised_pnl / self.amount * 100, 4)

    @property
    def current_value(self) -> float:
        """Current mark-to-market value: current_rate × units."""
        return round(self.current_rate * self.units, 4)


# ---------------------------------------------------------------------------
# Closed Position (eToro "trade history")
# ---------------------------------------------------------------------------


@dataclass
class ClosedPosition:
    """
    Represents a closed trade fetched from
    ``GET /accounts/{loginName}/trade-history``.
    """

    position_id: str
    instrument_id: int
    instrument_name: str
    instrument_type: str
    direction: str              # "Buy" or "Sell"
    amount: float
    units: float
    open_rate: float
    close_rate: float
    leverage: int
    realised_pnl: float
    open_date: Optional[datetime] = None
    close_date: Optional[datetime] = None

    @property
    def trade_value(self) -> float:
        """Gross trade value at close: close_rate × units."""
        return round(self.close_rate * self.units, 4)

    @property
    def return_percentage(self) -> float:
        """Percentage return on invested amount."""
        if self.amount == 0:
            return 0.0
        return round(self.realised_pnl / self.amount * 100, 4)


# ---------------------------------------------------------------------------
# Aggregated analysis output
# ---------------------------------------------------------------------------


@dataclass
class PortfolioSummary:
    """Aggregated portfolio analysis result returned by AnalysisService."""

    total_invested: float
    total_current_value: float
    total_pnl: float
    overall_return_pct: float
    positions_count: int
    closed_positions_count: int

    top_gainers: list[Position] = field(default_factory=list)
    top_losers: list[Position] = field(default_factory=list)
