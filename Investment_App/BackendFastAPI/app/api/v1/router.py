"""app/api/v1/router.py — aggregates all v1 routes."""

from fastapi import APIRouter

from app.api.v1 import (
    ai,
    analysis,
    auth,
    debug,
    etoro_instruments,
    instruments,
    live,
    market,
    portfolio,
    portfolios,
    sync,
    upstox_auth,
    users,
)

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(portfolios.router)
router.include_router(portfolio.router)
router.include_router(analysis.router)
router.include_router(live.router)
router.include_router(debug.router)
router.include_router(upstox_auth.router)
router.include_router(etoro_instruments.router)
# Phase 1 — frontend contract endpoints
router.include_router(instruments.router)
router.include_router(market.router)
router.include_router(sync.router)
# Phase 2 — AI scoring endpoint
router.include_router(ai.router)
