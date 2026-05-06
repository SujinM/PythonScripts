"""app/api/v1/router.py — aggregates all v1 routes."""

from fastapi import APIRouter

from app.api.v1 import analysis, live, portfolio

router = APIRouter(prefix="/api/v1")
router.include_router(portfolio.router)
router.include_router(analysis.router)
router.include_router(live.router)
