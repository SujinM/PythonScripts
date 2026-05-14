"""
app/api/v1/debug.py
────────────────────
Runtime debug flag endpoints (no server restart needed).

  GET  /api/v1/debug/flags
        → returns all current debug flag values

  POST /api/v1/debug/portfolio-trace?enabled=true
  POST /api/v1/debug/portfolio-trace?enabled=false
        → enable / disable per-holding portfolio trace logging

When portfolio trace is ON, every call to GET /{broker}/holdings or
GET /{broker}/summary prints detailed rows to the server console:

  [TRACE etoro] AAPL  | RAW: amount=100.00  units=0.5000  open_rate=200.00
                          curr_rate=210.00  etoro_pnl=+4.87  leverage=2
                        | COMPUTED: invested_value=100.00  current_value=104.87
                          unrealised_pnl=+4.87  return_pct=+4.8700%

  [TRACE summary] TOTAL: invested=500.00  current=525.43  pnl=+25.43  return=+5.09%
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.debug_flags import get_all_flags, is_portfolio_trace, set_portfolio_trace

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/flags", summary="Show all runtime debug flags")
def get_flags() -> dict:
    """Return the current state of all runtime debug flags."""
    return {"flags": get_all_flags()}


@router.post(
    "/portfolio-trace",
    summary="Enable or disable per-holding portfolio trace logging",
)
def toggle_portfolio_trace(
    enabled: bool = Query(..., description="true to enable trace, false to disable"),
) -> dict:
    """
    Toggle detailed portfolio trace logging at runtime.

    When **enabled**, every holdings/summary fetch prints per-holding rows
    (raw broker values AND computed model values) to the server console so
    you can verify that the eToro values are calculated correctly.

    Tip: set ``PORTFOLIO_DEBUG_LOG=true`` in your ``.env`` to enable
    automatically on startup.
    """
    set_portfolio_trace(enabled)
    status = "ENABLED" if enabled else "DISABLED"
    return {
        "portfolio_trace": enabled,
        "message": f"Portfolio trace logging {status}. "
                   f"Fetch /{'{broker}'}/holdings or /{'{broker}'}/summary to see logs.",
    }


@router.get("/portfolio-trace", summary="Check portfolio trace logging status")
def get_portfolio_trace_status() -> dict:
    """Return whether portfolio trace logging is currently active."""
    return {"portfolio_trace": is_portfolio_trace()}
