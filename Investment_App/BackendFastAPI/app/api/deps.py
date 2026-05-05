"""
app/api/deps.py
───────────────
FastAPI Depends() providers — single place to swap implementations.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.brokers.registry import registry
from app.core.cache import InMemoryCache, get_cache
from app.services.portfolio_service import PortfolioService


def get_portfolio_service(
    cache: Annotated[InMemoryCache, Depends(get_cache)],
) -> PortfolioService:
    return PortfolioService(registry=registry, cache=cache)
