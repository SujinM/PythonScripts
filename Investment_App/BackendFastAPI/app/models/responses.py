"""
app/models/responses.py
───────────────────────
Pydantic response envelopes for all API endpoints.
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard success envelope."""

    status: str = "success"
    data: T


class ErrorDetail(BaseModel):
    code: str
    message: str
    broker: Optional[str] = None


class ErrorResponse(BaseModel):
    status: str = "error"
    error: ErrorDetail


class AnalysisResult(BaseModel):
    broker: str
    holdings_count: int
    total_invested: float
    total_current_value: float
    total_pnl: float
    overall_return_pct: float
    top_gainers: list[dict[str, Any]] = []
    top_losers: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []
