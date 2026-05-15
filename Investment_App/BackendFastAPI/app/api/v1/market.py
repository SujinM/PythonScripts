"""
app/api/v1/market.py
─────────────────────
Market data and statistics endpoints.

The /statistics endpoint derives real counts from the instrument DB.
Market price endpoints fetch live quotes from the eToro Public API
(GET /api/v1/market-data/instruments/rates) using the configured
ETORO_API_KEY + ETORO_USER_KEY credentials.

Routes
------
  GET /api/v1/statistics                    — DB-derived instrument statistics
  GET /api/v1/market-data/{symbol}/history  — OHLCV stub (returns [])
  GET /api/v1/market-data/{symbol}          — live price from eToro API
  GET /api/v1/market-data                   — bulk live prices from eToro API
"""

from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser
from app.db.models import EtoroInstrument
from app.db.session import get_db
from app.services import etoro_market_service

router = APIRouter(tags=["market"])

_DBDep = Annotated[Session, Depends(get_db)]

_TYPE_LABELS: dict[int, str] = {
    1: "FOREX",
    2: "COMMODITIES",
    4: "INDICES",
    5: "STOCKS",
    6: "ETFS",
    10: "CRYPTO",
}


# ── Schemas ───────────────────────────────────────────────────────────────────

class MarketData(BaseModel):
    symbol:        str
    price:         float
    change:        float
    changePercent: float
    volume:        float
    high24h:       float
    low24h:        float
    marketCap:     Optional[float] = None
    open:          Optional[float] = None
    previousClose: Optional[float] = None
    timestamp:     str


class Candle(BaseModel):
    timestamp: str
    open:      float
    high:      float
    low:       float
    close:     float
    volume:    float


class Statistics(BaseModel):
    totalInstruments:   int
    totalExchanges:     int
    totalTradable:      int
    assetTypeBreakdown: dict[str, int]
    exchangeBreakdown:  dict[str, int]
    recentlyUpdated:    list   # Instrument shape — populated in Phase 2
    topActiveSymbols:   list   # MarketData shape — populated in Phase 2
    lastSyncAt:         Optional[str]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/statistics", response_model=Statistics)
def get_statistics(_user: CurrentUser, db: _DBDep) -> Statistics:
    """Compute instrument catalogue statistics from the local database."""
    total    = db.query(EtoroInstrument).count()
    tradable = (
        db.query(EtoroInstrument)
        .filter(EtoroInstrument.is_internal == False)  # noqa: E712
        .count()
    )

    type_rows = (
        db.query(EtoroInstrument.instrument_type_id, func.count())
        .group_by(EtoroInstrument.instrument_type_id)
        .all()
    )
    asset_breakdown: dict[str, int] = {
        _TYPE_LABELS.get(tid or 0, "OTHER"): cnt
        for tid, cnt in type_rows
    }

    exchange_count = (
        db.query(EtoroInstrument.exchange_id)
        .filter(EtoroInstrument.exchange_id.isnot(None))
        .distinct()
        .count()
    )

    last_synced = db.query(func.max(EtoroInstrument.synced_at)).scalar()
    last_sync_at = last_synced.isoformat() if last_synced else None

    return Statistics(
        totalInstruments=total,
        totalExchanges=exchange_count,
        totalTradable=tradable,
        assetTypeBreakdown=asset_breakdown,
        exchangeBreakdown={},
        recentlyUpdated=[],
        topActiveSymbols=[],
        lastSyncAt=last_sync_at,
    )


@router.get("/market-data/{symbol}/history", response_model=List[Candle])
def get_price_history(
    symbol: str,
    _user: CurrentUser,
    days: int = Query(90, ge=1, le=365),
) -> List[Candle]:
    """Return OHLCV candle history.  No live price source in Phase 1 — returns []."""
    return []


@router.get("/market-data/{symbol}", response_model=MarketData)
def get_market_data(symbol: str, _user: CurrentUser, db: _DBDep) -> MarketData:
    """Return a live market quote fetched from the eToro Public API."""
    data = etoro_market_service.fetch_market_data(symbol, db)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No market data available for '{symbol}'. "
                   "Ensure the symbol exists in the eToro instrument catalogue "
                   "and ETORO_API_KEY / ETORO_USER_KEY are configured.",
        )
    return MarketData(**data)


@router.get("/market-data", response_model=List[MarketData])
def get_bulk_market_data(
    _user: CurrentUser,
    db: _DBDep,
    symbols: Optional[str] = Query(None, description="Comma-separated symbol list"),
) -> List[MarketData]:
    """Return bulk quotes from the eToro Public API."""
    if not symbols:
        return []
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    results = etoro_market_service.fetch_bulk_market_data(symbol_list, db)
    return [MarketData(**r) for r in results]
