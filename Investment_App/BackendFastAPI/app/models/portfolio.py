"""
app/models/portfolio.py
───────────────────────
Unified, broker-agnostic portfolio models.
All broker adapters normalise their raw API responses into these models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class Holding(BaseModel):
    """A long-term investment holding."""

    broker: str = Field(description="Source broker identifier, e.g. 'upstox'")
    instrument_key: str = Field(description="Broker-specific unique instrument identifier")
    trading_symbol: str
    exchange: str = ""
    isin: Optional[str] = None
    quantity: float
    average_price: float
    last_price: float
    close_price: float = 0.0

    @computed_field  # type: ignore[misc]
    @property
    def invested_value(self) -> float:
        return round(self.quantity * self.average_price, 2)

    @computed_field  # type: ignore[misc]
    @property
    def current_value(self) -> float:
        return round(self.quantity * self.last_price, 2)

    @computed_field  # type: ignore[misc]
    @property
    def unrealised_pnl(self) -> float:
        return round(self.current_value - self.invested_value, 2)

    @computed_field  # type: ignore[misc]
    @property
    def return_pct(self) -> float:
        if self.invested_value == 0:
            return 0.0
        return round(self.unrealised_pnl / self.invested_value * 100, 4)


class Position(BaseModel):
    """An open intraday or F&O position."""

    broker: str
    instrument_key: str
    trading_symbol: str
    exchange: str = ""
    product: str = ""
    quantity: int
    buy_price: float
    sell_price: float = 0.0
    last_price: float
    realised_pnl: float = 0.0
    unrealised_pnl: float = 0.0

    @computed_field  # type: ignore[misc]
    @property
    def total_pnl(self) -> float:
        return round(self.realised_pnl + self.unrealised_pnl, 2)


class Trade(BaseModel):
    """An executed trade."""

    broker: str
    instrument_key: str
    trading_symbol: str
    exchange: str = ""
    product: str = ""
    transaction_type: str  # BUY | SELL
    quantity: float
    price: float
    trade_date: Optional[datetime] = None

    @computed_field  # type: ignore[misc]
    @property
    def trade_value(self) -> float:
        return round(self.quantity * self.price, 2)


class PortfolioSummary(BaseModel):
    """Aggregated summary across all holdings and positions."""

    broker: str
    holdings_count: int
    positions_count: int
    total_invested: float
    total_current_value: float
    total_unrealised_pnl: float
    total_realised_pnl: float
    overall_return_pct: float
    top_gainers: list[Holding] = []
    top_losers: list[Holding] = []
