"""
app/api/v1/upstox_instruments.py
──────────────────────────────────
Upstox instrument catalogue endpoints.

Endpoints
---------
  GET  /api/v1/upstox/instruments          — paginated, searchable instrument list
  GET  /api/v1/upstox/instruments/{key}    — single instrument detail by instrument_key
  POST /api/v1/upstox/instruments/sync     — load from local JSON file and upsert DB
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser
from app.core.config import get_settings
from app.core.logger import get_logger
from app.db.models import UpstoxInstrument
from app.db.session import get_db

router = APIRouter(prefix="/upstox/instruments", tags=["upstox-instruments"])
logger = get_logger(__name__)

_SEGMENT_LABELS: dict[str, str] = {
    "BSE_EQ":           "BSE Equity",
    "BSE_FO":           "BSE F&O",
    "BSE_INDEX":        "BSE Index",
    "NSE_EQ":           "NSE Equity",
    "NSE_FO":           "NSE F&O",
    "NSE_INDEX":        "NSE Index",
    "NSE_COM":          "NSE Commodities",
    "MCX_FO":           "MCX F&O",
    "NCD_FO":           "NCD F&O",
    "BCD_FO":           "BCD F&O",
    "GLOBAL_INDEX":     "Global Index",
    "GLOBAL_INDICATOR": "Global Indicator",
}

_DBDep = Annotated[Session, Depends(get_db)]


# ── Schemas ───────────────────────────────────────────────────────────────────

class UpstoxInstrumentRead(BaseModel):
    instrument_key:  str
    trading_symbol:  str
    name:            str
    exchange:        str
    segment:         str
    segment_label:   Optional[str]
    instrument_type: Optional[str]
    isin:            Optional[str]
    lot_size:        Optional[int]
    tick_size:       Optional[float]
    freeze_quantity: Optional[float]
    exchange_token:  Optional[str]
    qty_multiplier:  Optional[float]
    synced_at:       Optional[datetime]

    model_config = {"from_attributes": True}


class PaginatedUpstoxInstruments(BaseModel):
    data:        List[UpstoxInstrumentRead]
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

def _row_to_schema(row: UpstoxInstrument) -> UpstoxInstrumentRead:
    return UpstoxInstrumentRead(
        instrument_key=row.instrument_key,
        trading_symbol=row.trading_symbol,
        name=row.name,
        exchange=row.exchange,
        segment=row.segment,
        segment_label=_SEGMENT_LABELS.get(row.segment),
        instrument_type=row.instrument_type,
        isin=row.isin,
        lot_size=row.lot_size,
        tick_size=row.tick_size,
        freeze_quantity=row.freeze_quantity,
        exchange_token=row.exchange_token,
        qty_multiplier=row.qty_multiplier,
        synced_at=row.synced_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedUpstoxInstruments)
def list_instruments(
    _user: CurrentUser,
    db: _DBDep,
    search: Optional[str] = Query(None, description="Search by trading symbol or name"),
    segment: Optional[str] = Query(None, description="Filter by segment (e.g. NSE_EQ)"),
    exchange: Optional[str] = Query(None, description="Filter by exchange (BSE/NSE/MCX/GLOBAL)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    sort_by: str = Query("trading_symbol", description="Field to sort by"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
) -> PaginatedUpstoxInstruments:
    """Return a paginated, filterable list of Upstox instruments from the local DB."""
    q = db.query(UpstoxInstrument)

    if search:
        term = f"%{search.lower()}%"
        from sqlalchemy import func, or_
        q = q.filter(
            or_(
                func.lower(UpstoxInstrument.trading_symbol).like(term),
                func.lower(UpstoxInstrument.name).like(term),
                func.lower(UpstoxInstrument.isin).like(term),
            )
        )
    if segment:
        q = q.filter(UpstoxInstrument.segment == segment)
    if exchange:
        q = q.filter(UpstoxInstrument.exchange == exchange)

    total = q.count()

    col = getattr(UpstoxInstrument, sort_by, UpstoxInstrument.trading_symbol)
    q = q.order_by(col.desc() if sort_order == "desc" else col.asc())

    offset = (page - 1) * page_size
    rows = q.offset(offset).limit(page_size).all()
    total_pages = max(1, (total + page_size - 1) // page_size)

    return PaginatedUpstoxInstruments(
        data=[_row_to_schema(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{instrument_key:path}", response_model=UpstoxInstrumentRead)
def get_instrument(
    instrument_key: str,
    _user: CurrentUser,
    db: _DBDep,
) -> UpstoxInstrumentRead:
    """Return a single Upstox instrument by its instrument_key."""
    row = db.query(UpstoxInstrument).filter(
        UpstoxInstrument.instrument_key == instrument_key
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Instrument '{instrument_key}' not found")
    return _row_to_schema(row)


@router.post("/sync", response_model=SyncResult, status_code=status.HTTP_200_OK)
def sync_instruments(
    _user: CurrentUser,
    db: _DBDep,
) -> SyncResult:
    """
    Load all instruments from the local Upstox JSON master file and bulk-upsert
    them into the database using INSERT OR REPLACE for maximum performance.
    Returns counts of inserted / updated rows.
    """
    from sqlalchemy import text

    settings = get_settings()
    json_path = Path(settings.upstox_instruments_file)
    if not json_path.is_absolute():
        json_path = Path(__file__).resolve().parents[3] / settings.upstox_instruments_file

    if not json_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upstox instruments file not found: {json_path}",
        )

    logger.info("Loading Upstox instruments from %s", json_path)
    with json_path.open(encoding="utf-8") as fh:
        items: list[dict] = json.load(fh)

    now = datetime.now(timezone.utc).isoformat()
    BATCH = 2000

    # Count existing rows before sync
    existing_count: int = db.execute(text("SELECT COUNT(*) FROM upstox_instruments")).scalar() or 0

    rows = [
        {
            "instrument_key":  item["instrument_key"],
            "trading_symbol":  item.get("trading_symbol", ""),
            "name":            item.get("name", ""),
            "exchange":        item.get("exchange", ""),
            "segment":         item.get("segment", ""),
            "instrument_type": item.get("instrument_type") or None,
            "isin":            item.get("isin") or None,
            "lot_size":        item.get("lot_size"),
            "tick_size":       item.get("tick_size"),
            "freeze_quantity": item.get("freeze_quantity"),
            "exchange_token":  item.get("exchange_token") or None,
            "qty_multiplier":  item.get("qty_multiplier"),
            "synced_at":       now,
        }
        for item in items
        if item.get("instrument_key")
    ]

    total = len(rows)
    logger.info("Upserting %d instruments in batches of %d…", total, BATCH)

    upsert_sql = text("""
        INSERT OR REPLACE INTO upstox_instruments
            (instrument_key, trading_symbol, name, exchange, segment,
             instrument_type, isin, lot_size, tick_size, freeze_quantity,
             exchange_token, qty_multiplier, synced_at)
        VALUES
            (:instrument_key, :trading_symbol, :name, :exchange, :segment,
             :instrument_type, :isin, :lot_size, :tick_size, :freeze_quantity,
             :exchange_token, :qty_multiplier, :synced_at)
    """)

    for i in range(0, total, BATCH):
        db.execute(upsert_sql, rows[i : i + BATCH])
        db.commit()

    new_count: int = db.execute(text("SELECT COUNT(*) FROM upstox_instruments")).scalar() or 0
    inserted = max(0, new_count - existing_count)
    updated  = total - inserted

    logger.info("Upstox sync done — inserted=%d updated=%d total=%d", inserted, updated, total)
    return SyncResult(
        total=total,
        inserted=inserted,
        updated=updated,
        message=f"Sync complete — {inserted} inserted, {updated} updated ({total:,} total instruments)",
    )
