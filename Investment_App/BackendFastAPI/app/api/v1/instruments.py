"""
app/api/v1/instruments.py
─────────────────────────
Frontend-facing instrument endpoints.

Maps EtoroInstrument ORM rows to the camelCase Instrument contract
expected by TradeView/src/api/instruments.ts and instrumentsStore.ts.

Routes
------
  GET /api/v1/instruments          — paginated, filtered instrument list
  GET /api/v1/instruments/{symbol} — single instrument by symbol string
"""

from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser
from app.db.models import EtoroInstrument
from app.db.session import get_db
from app.core.logger import get_logger

router = APIRouter(prefix="/instruments", tags=["instruments"])
logger = get_logger(__name__)

_DBDep = Annotated[Session, Depends(get_db)]

# eToro InstrumentTypeID  →  frontend AssetType / exchange string
_TYPE_TO_ASSET: dict[int, str] = {
    1: "FOREX",
    2: "COMMODITIES",
    4: "INDICES",
    5: "STOCKS",
    6: "ETFS",
    10: "CRYPTO",
}

_TYPE_TO_EXCHANGE: dict[int, str] = {
    1: "FOREX",
    2: "COMMODITIES",
    4: "INDICES",
    5: "NYSE",
    6: "NASDAQ",
    10: "CRYPTO",
}

# Reverse map — used for filtering by assetType query param
_ASSET_TO_TYPE: dict[str, int] = {v: k for k, v in _TYPE_TO_ASSET.items()}

# Exchange names recognisable from eToro's PriceSource field
_KNOWN_EXCHANGES = {"NASDAQ", "NYSE", "LSE", "EURONEXT", "TSX", "ASX"}


# ── Schemas ───────────────────────────────────────────────────────────────────

class InstrumentOut(BaseModel):
    """Matches TradeView/src/types/instrument.ts Instrument interface."""

    model_config = ConfigDict(populate_by_name=True)

    instrument_id: int    = Field(alias="instrumentId")
    symbol:        str
    display_name:  str    = Field(alias="displayName")
    exchange:      str
    asset_type:    str    = Field(alias="assetType")
    currency:      str
    is_tradable:   bool   = Field(alias="isTradable")
    image_url:     Optional[str] = Field(default=None, alias="imageUrl")


class PaginatedInstruments(BaseModel):
    """Matches TradeView/src/types/instrument.ts PaginatedResponse<Instrument>."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    data:        List[InstrumentOut]
    total:       int
    page:        int
    page_size:   int   # serialised as "pageSize"
    total_pages: int   # serialised as "totalPages"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_out(row: EtoroInstrument) -> dict:
    """Convert an ORM row to the dict that InstrumentOut expects (by alias)."""
    tid = row.instrument_type_id or 0
    ps = (row.price_source or "").upper()
    exchange = ps if ps in _KNOWN_EXCHANGES else _TYPE_TO_EXCHANGE.get(tid, "OTHER")
    return {
        "instrumentId": row.instrument_id,
        "symbol":       row.symbol,
        "displayName":  row.display_name,
        "exchange":     exchange,
        "assetType":    _TYPE_TO_ASSET.get(tid, "STOCKS"),
        "currency":     "USD",
        "isTradable":   not bool(row.is_internal),
        "imageUrl":     row.image_url,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedInstruments, response_model_by_alias=True)
def list_instruments(
    _user: CurrentUser,
    db: _DBDep,
    search:     Optional[str]  = Query(None, description="Search symbol or name"),
    assetType:  Optional[str]  = Query(None, description="Filter by asset type"),
    exchange:   Optional[str]  = Query(None, description="Filter by exchange"),
    isTradable: Optional[bool] = Query(None, description="Filter tradable only"),
    page:       int            = Query(1,  ge=1),
    pageSize:   int            = Query(20, ge=1, le=500),
    sortBy:     str            = Query("instrument_id"),
    sortOrder:  str            = Query("asc", pattern="^(asc|desc)$"),
) -> PaginatedInstruments:
    """Return a paginated, filterable instrument list matching the frontend contract."""
    q = db.query(EtoroInstrument)

    if search:
        term = f"%{search.lower()}%"
        q = q.filter(or_(
            func.lower(EtoroInstrument.symbol).like(term),
            func.lower(EtoroInstrument.display_name).like(term),
        ))

    if assetType and assetType in _ASSET_TO_TYPE:
        q = q.filter(EtoroInstrument.instrument_type_id == _ASSET_TO_TYPE[assetType])

    if isTradable is not None:
        q = q.filter(EtoroInstrument.is_internal == (not isTradable))

    total = q.count()

    col = getattr(EtoroInstrument, sortBy, EtoroInstrument.instrument_id)
    q = q.order_by(col.desc() if sortOrder == "desc" else col.asc())

    offset = (page - 1) * pageSize
    rows = q.offset(offset).limit(pageSize).all()
    total_pages = max(1, (total + pageSize - 1) // pageSize)

    return PaginatedInstruments(
        data=[InstrumentOut.model_validate(_to_out(r)) for r in rows],
        total=total,
        page=page,
        page_size=pageSize,
        total_pages=total_pages,
    )


@router.get("/{symbol}", response_model=InstrumentOut, response_model_by_alias=True)
def get_instrument(
    symbol: str,
    _user: CurrentUser,
    db: _DBDep,
) -> InstrumentOut:
    """Return a single instrument by its symbol string (case-insensitive)."""
    row = (
        db.query(EtoroInstrument)
        .filter(func.lower(EtoroInstrument.symbol) == symbol.lower())
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"Instrument '{symbol}' not found")
    return InstrumentOut.model_validate(_to_out(row))
