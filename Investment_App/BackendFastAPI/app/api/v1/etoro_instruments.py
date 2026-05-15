"""
app/api/v1/etoro_instruments.py
────────────────────────────────
eToro instrument catalogue endpoints.

Endpoints
---------
  GET  /api/v1/etoro/instruments         — paginated, searchable instrument list
  GET  /api/v1/etoro/instruments/{id}    — single instrument detail
  POST /api/v1/etoro/instruments/sync    — fetch from eToro static API and upsert DB
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser
from app.db.models import EtoroInstrument
from app.db.session import get_db
from app.core.logger import get_logger

router = APIRouter(prefix="/etoro/instruments", tags=["etoro-instruments"])
logger = get_logger(__name__)

_ETORO_API_URL = "https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments"

_INSTRUMENT_TYPES: dict[int, str] = {
    1: "Forex",
    2: "Commodities",
    3: "Indices",
    4: "Stocks",
    5: "ETFs",
    6: "Crypto",
}

_DBDep = Annotated[Session, Depends(get_db)]


# ── Schemas ───────────────────────────────────────────────────────────────────

class EtoroInstrumentRead(BaseModel):
    instrument_id:       int
    symbol:              str
    display_name:        str
    instrument_type_id:  Optional[int]
    instrument_type:     Optional[str]   # human-readable label
    exchange_id:         Optional[int]
    price_source:        Optional[str]
    has_expiration_date: bool
    is_internal:         bool
    distribution_type:   Optional[int]
    image_url:           Optional[str]
    synced_at:           Optional[datetime]

    model_config = {"from_attributes": True}


class PaginatedInstruments(BaseModel):
    data:        List[EtoroInstrumentRead]
    total:       int
    page:        int
    page_size:   int
    total_pages: int


class SyncResult(BaseModel):
    total:    int
    inserted: int
    updated:  int
    message:  str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _best_image(images: list[dict]) -> str | None:
    """Pick the 50×50 CDN URL from an instrument's Images list."""
    for img in images:
        uri = img.get("Uri", "")
        if img.get("Width") == 50 and uri.startswith("http"):
            return uri
    # fallback: first http URI
    for img in images:
        uri = img.get("Uri", "")
        if uri.startswith("http"):
            return uri
    return None


def _row_to_schema(row: EtoroInstrument) -> EtoroInstrumentRead:
    return EtoroInstrumentRead(
        instrument_id=row.instrument_id,
        symbol=row.symbol,
        display_name=row.display_name,
        instrument_type_id=row.instrument_type_id,
        instrument_type=_INSTRUMENT_TYPES.get(row.instrument_type_id or 0),
        exchange_id=row.exchange_id,
        price_source=row.price_source,
        has_expiration_date=bool(row.has_expiration_date),
        is_internal=bool(row.is_internal),
        distribution_type=row.distribution_type,
        image_url=row.image_url,
        synced_at=row.synced_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedInstruments)
def list_instruments(
    _user: CurrentUser,
    db: _DBDep,
    search: Optional[str] = Query(None, description="Search by symbol or display name"),
    instrument_type_id: Optional[int] = Query(None),
    exchange_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    sort_by: str = Query("instrument_id", description="Field to sort by"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
) -> PaginatedInstruments:
    """Return a paginated, filterable list of eToro instruments from the local DB."""
    q = db.query(EtoroInstrument)

    if search:
        term = f"%{search.lower()}%"
        from sqlalchemy import func, or_
        q = q.filter(
            or_(
                func.lower(EtoroInstrument.symbol).like(term),
                func.lower(EtoroInstrument.display_name).like(term),
            )
        )
    if instrument_type_id is not None:
        q = q.filter(EtoroInstrument.instrument_type_id == instrument_type_id)
    if exchange_id is not None:
        q = q.filter(EtoroInstrument.exchange_id == exchange_id)

    total = q.count()

    # Sorting
    col = getattr(EtoroInstrument, sort_by, EtoroInstrument.instrument_id)
    q = q.order_by(col.desc() if sort_order == "desc" else col.asc())

    offset = (page - 1) * page_size
    rows = q.offset(offset).limit(page_size).all()
    total_pages = max(1, (total + page_size - 1) // page_size)

    return PaginatedInstruments(
        data=[_row_to_schema(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{instrument_id}", response_model=EtoroInstrumentRead)
def get_instrument(
    instrument_id: int,
    _user: CurrentUser,
    db: _DBDep,
) -> EtoroInstrumentRead:
    """Return a single eToro instrument by its InstrumentID."""
    row = db.query(EtoroInstrument).filter(
        EtoroInstrument.instrument_id == instrument_id
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Instrument {instrument_id} not found")
    return _row_to_schema(row)


@router.post("/sync", response_model=SyncResult, status_code=status.HTTP_200_OK)
def sync_instruments(
    _user: CurrentUser,
    db: _DBDep,
) -> SyncResult:
    """
    Fetch all instruments from the eToro static metadata API and upsert
    them into the local database.  Existing records are updated in-place;
    new ones are inserted.  Returns counts of inserted / updated rows.
    """
    logger.info("Starting eToro instruments sync from %s", _ETORO_API_URL)
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(_ETORO_API_URL, headers={"User-Agent": "InvestmentPortfolio/1.0"})
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPError as exc:
        logger.error("eToro API request failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to reach eToro API: {exc}",
        ) from exc

    items: list[dict] = payload.get("InstrumentDisplayDatas", [])
    if not items:
        raise HTTPException(status_code=502, detail="eToro API returned no instruments")

    now = datetime.now(timezone.utc)
    inserted = updated = 0

    for item in items:
        iid = item.get("InstrumentID")
        if iid is None:
            continue

        existing = db.get(EtoroInstrument, iid)
        data = {
            "symbol":              item.get("SymbolFull", ""),
            "display_name":        item.get("InstrumentDisplayName", ""),
            "instrument_type_id":  item.get("InstrumentTypeID"),
            "exchange_id":         item.get("ExchangeID"),
            "price_source":        item.get("PriceSource"),
            "has_expiration_date": bool(item.get("HasExpirationDate", False)),
            "is_internal":         bool(item.get("IsInternalInstrument", False)),
            "distribution_type":   item.get("DistributionType"),
            "image_url":           _best_image(item.get("Images", [])),
            "synced_at":           now,
        }

        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(EtoroInstrument(instrument_id=iid, **data))
            inserted += 1

    db.commit()
    total = inserted + updated
    logger.info("Sync complete — total=%d inserted=%d updated=%d", total, inserted, updated)
    return SyncResult(
        total=total,
        inserted=inserted,
        updated=updated,
        message=f"Sync complete: {inserted} new, {updated} updated ({total} total)",
    )
