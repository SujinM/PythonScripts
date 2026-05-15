"""app/api/v1/router.py — aggregates all v1 routes."""

from fastapi import APIRouter

from app.api.v1 import analysis, auth, debug, live, portfolio, portfolios, upstox_auth, users

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(portfolios.router)
router.include_router(portfolio.router)
router.include_router(analysis.router)
router.include_router(live.router)
router.include_router(debug.router)
router.include_router(upstox_auth.router)
