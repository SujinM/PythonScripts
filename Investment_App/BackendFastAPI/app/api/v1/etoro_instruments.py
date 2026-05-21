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
from app.services import etoro_market_service

router = APIRouter(prefix="/etoro/instruments", tags=["etoro-instruments"])
logger = get_logger(__name__)

_ETORO_API_URL = "https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments"

_INSTRUMENT_TYPES: dict[int, str] = {
    1: "Forex",
    2: "Commodities",
    4: "Indices",
    5: "Stocks",
    6: "ETFs",
    10: "Crypto",
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


# ── Price-change schema ──────────────────────────────────────────────────────

class InstrumentPriceChange(BaseModel):
    instrument_id:   int
    current_price:   Optional[float]
    change_1d_value: Optional[float]
    change_1d_pct:   Optional[float]
    change_1m_value: Optional[float]
    change_1m_pct:   Optional[float]
    change_1y_value: Optional[float]
    change_1y_pct:   Optional[float]


@router.get("/debug/rates")
def debug_rates(
    instrument_ids: str = Query(..., description="Comma-separated eToro instrument IDs, e.g. 9425,1001"),
) -> dict:
    """
    Return the **raw** eToro rates API response.
    Use this to see every field the rates endpoint actually returns (including 24h change field names).
    """
    import uuid, requests as _req
    from app.core.config import get_settings

    s = get_settings()
    base = s.etoro_base_url.rstrip("/")
    hdrs = {
        "x-api-key":    s.etoro_api_key,
        "x-user-key":   s.etoro_user_key,
        "x-request-id": str(uuid.uuid4()),
        "Accept":       "application/json",
    }

    results = {}

    # ── Rates endpoint ────────────────────────────────────────────────────────
    url = f"{base}/api/v1/market-data/instruments/rates"
    try:
        resp = _req.get(url, headers=hdrs, params={"instrumentIds": instrument_ids}, timeout=10)
        body = resp.json() if "application/json" in resp.headers.get("content-type", "") else resp.text
        first_keys = list(body["rates"][0].keys()) if isinstance(body, dict) and body.get("rates") else []
        results["rates"] = {"status_code": resp.status_code, "first_rate_keys": first_keys, "body": body}
    except Exception as exc:
        results["rates"] = {"error": str(exc)}

    # ── Instruments metadata endpoint (may contain daily % change) ────────────
    url2 = f"{base}/api/v1/market-data/instruments"
    try:
        resp2 = _req.get(url2, headers={**hdrs, "x-request-id": str(uuid.uuid4())},
                         params={"instrumentIds": instrument_ids}, timeout=10)
        body2 = resp2.json() if "application/json" in resp2.headers.get("content-type", "") else resp2.text
        items = (body2.get("instrumentDisplayDatas") or body2.get("instruments") or []) if isinstance(body2, dict) else []
        first_keys2 = list(items[0].keys()) if items else []
        results["instruments_metadata"] = {"status_code": resp2.status_code, "first_item_keys": first_keys2, "body": body2}
    except Exception as exc:
        results["instruments_metadata"] = {"error": str(exc)}

    # ── Try several candle/chart URL patterns ─────────────────────────────────
    candle_candidates = [
        f"{base}/api/v1/market-data/instruments/candles",
        f"{base}/api/v1/market-data/charts/candles",
        f"{base}/api/v1/market-data/instruments/charts",
    ]
    results["candle_probes"] = {}
    for candidate in candle_candidates:
        try:
            r = _req.get(candidate, headers={**hdrs, "x-request-id": str(uuid.uuid4())},
                         params={"instrumentIds": instrument_ids, "period": "OneMonth"}, timeout=10)
            results["candle_probes"][candidate] = {
                "status_code": r.status_code,
                "body": r.json() if "application/json" in r.headers.get("content-type", "") else r.text,
            }
        except Exception as exc:
            results["candle_probes"][candidate] = {"error": str(exc)}

    return results


@router.get("/debug/candles")
def debug_candles(
    instrument_id: int = Query(..., description="Single eToro instrument ID"),
    period: str = Query("OneMonth", description="OneMonth or OneYear"),
) -> dict:
    """
    Return the **raw** eToro candles API response for one instrument.
    Use this to discover the exact response structure so the parser can be fixed.
    """
    import uuid, requests as _req
    from app.core.config import get_settings

    s = get_settings()
    base = s.etoro_base_url.rstrip("/")
    hdrs = {
        "x-api-key":    s.etoro_api_key,
        "x-user-key":   s.etoro_user_key,
        "x-request-id": str(uuid.uuid4()),
        "Accept":       "application/json",
    }
    url = f"{base}/api/v1/market-data/instruments/candles"
    try:
        resp = _req.get(url, headers=hdrs,
                        params={"instrumentIds": str(instrument_id), "period": period},
                        timeout=10)
        return {
            "url":         url,
            "params":      {"instrumentIds": instrument_id, "period": period},
            "status_code": resp.status_code,
            "body":        resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
        }
    except Exception as exc:
        return {"error": str(exc)}


@router.get("/price-changes", response_model=list[InstrumentPriceChange])
def get_price_changes(
    _user: CurrentUser,
    db: _DBDep,
    instrument_ids: str = Query(
        ...,
        description="Comma-separated eToro instrument IDs (e.g. 9425,1001,100001)",
    ),
) -> list[InstrumentPriceChange]:
    """
    Return 1-day, 1-month and 1-year price changes for the given instrument IDs.
    Current price comes from the eToro rates API; historical prices from Yahoo Finance.
    """
    try:
        ids = [int(x.strip()) for x in instrument_ids.split(",") if x.strip().isdigit()]
    except ValueError:
        ids = []
    if not ids:
        return []

    data = etoro_market_service.fetch_price_changes_bulk(ids, db=db)
    return [
        InstrumentPriceChange(instrument_id=iid, **info)
        for iid, info in data.items()
    ]


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
