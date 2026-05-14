"""
app/core/debug_flags.py
────────────────────────
Runtime-toggleable debug flags.

Initial values are read from .env / environment variables on first access.
They can also be flipped at runtime via POST /api/v1/debug/portfolio-trace
without restarting the server.

Usage
─────
  from app.core.debug_flags import is_portfolio_trace, set_portfolio_trace

  if is_portfolio_trace():
      logger.info("[TRACE] ...")
"""

from __future__ import annotations

# Mutable state — one dict so it is trivial to extend with more flags.
_flags: dict[str, bool] = {}


def _init() -> None:
    """Bootstrap from settings on first access (avoids circular imports at module load)."""
    from app.core.config import get_settings  # local import to avoid circular

    s = get_settings()
    _flags.setdefault("portfolio_trace", getattr(s, "portfolio_debug_log", False))


def _ensure() -> None:
    if not _flags:
        _init()


# ── Public API ────────────────────────────────────────────────────────────────


def is_portfolio_trace() -> bool:
    """Return True when per-holding portfolio trace logging is active."""
    _ensure()
    return _flags.get("portfolio_trace", False)


def set_portfolio_trace(enabled: bool) -> None:
    """Toggle portfolio trace logging at runtime (no server restart needed)."""
    _ensure()
    _flags["portfolio_trace"] = enabled


def get_all_flags() -> dict[str, bool]:
    """Return a snapshot of all current debug flags."""
    _ensure()
    return dict(_flags)
