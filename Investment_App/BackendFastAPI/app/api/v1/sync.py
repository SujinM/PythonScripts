"""
app/api/v1/sync.py
───────────────────
Instrument sync management endpoints.

Sync state is kept in-process (module-level dict + list).  A threading.Lock
guards writes so the background task and request handlers don't race.
State resets on server restart — sufficient for Phase 1.

NOTE: with multiple Uvicorn workers the state would not be shared; migrate
      to a DB table or Redis when you add multi-worker deployments.

Routes
------
  GET /api/v1/sync-instruments — kick off a background eToro instrument sync
  GET /api/v1/sync-status      — current sync progress
  GET /api/v1/sync-logs        — recent log entries (capped at 500)
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Annotated, List, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser
from app.db.models import EtoroInstrument
from app.db.session import SessionLocal
from app.core.logger import get_logger

router = APIRouter(tags=["sync"])
logger = get_logger(__name__)

_ETORO_API_URL = (
    "https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments"
)

# ── In-memory sync state ──────────────────────────────────────────────────────

_state: dict = {
    "isRunning":        False,
    "progress":         0,
    "startedAt":        None,
    "completedAt":      None,
    "itemsProcessed":   0,
    "totalItems":       0,
    "errors":           [],
    "lastSyncAt":       None,
    "lastSyncDuration": None,
}

_logs: list[dict] = []
_lock = threading.Lock()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _append_log(level: str, message: str, symbol: str | None = None) -> None:
    entry = {
        "id":        str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level":     level,
        "message":   message,
        "symbol":    symbol,
    }
    with _lock:
        _logs.append(entry)
        if len(_logs) > 500:
            _logs.pop(0)
    logger.info("[sync] %s", message)


def _best_image(images: list[dict]) -> str | None:
    """Pick the 50×50 CDN URL from an instrument's Images list."""
    for img in images:
        uri = img.get("Uri", "")
        if img.get("Width") == 50 and uri.startswith("http"):
            return uri
    for img in images:
        uri = img.get("Uri", "")
        if uri.startswith("http"):
            return uri
    return None


# ── Background sync job ───────────────────────────────────────────────────────

def _run_sync() -> None:
    """Full eToro instrument sync — runs in a FastAPI BackgroundTask thread."""
    with _lock:
        if _state["isRunning"]:
            return
        _state.update({
            "isRunning":      True,
            "progress":       0,
            "errors":         [],
            "startedAt":      datetime.now(timezone.utc).isoformat(),
            "completedAt":    None,
            "itemsProcessed": 0,
            "totalItems":     0,
        })

    _append_log("info", "Connecting to eToro metadata API…")

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                _ETORO_API_URL,
                headers={"User-Agent": "InvestmentPortfolio/1.0"},
            )
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPError as exc:
        msg = f"eToro API request failed: {exc}"
        _append_log("error", msg)
        with _lock:
            _state["isRunning"] = False
            _state["errors"].append(msg)
        return

    items: list[dict] = payload.get("InstrumentDisplayDatas", [])
    total = len(items)

    if total == 0:
        msg = "eToro API returned no instruments — aborting sync"
        _append_log("error", msg)
        with _lock:
            _state["isRunning"] = False
            _state["errors"].append(msg)
        return

    with _lock:
        _state["totalItems"] = total

    _append_log("info", f"Fetched {total} instruments — upserting to database…")

    now = datetime.now(timezone.utc)
    db: Session = SessionLocal()
    inserted = updated = 0

    try:
        for idx, item in enumerate(items):
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

            with _lock:
                _state["itemsProcessed"] = idx + 1
                _state["progress"] = round(((idx + 1) / total) * 100)

        db.commit()

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        msg = f"Database error during sync: {exc}"
        _append_log("error", msg)
        with _lock:
            _state["isRunning"] = False
            _state["errors"].append(msg)
        return
    finally:
        db.close()

    completed = datetime.now(timezone.utc)
    started_str = _state.get("startedAt") or completed.isoformat()
    duration = round((completed - datetime.fromisoformat(started_str)).total_seconds())

    _append_log(
        "info",
        f"Sync complete — {inserted} inserted, {updated} updated ({total} total)",
    )

    with _lock:
        _state.update({
            "isRunning":        False,
            "progress":         100,
            "completedAt":      completed.isoformat(),
            "lastSyncAt":       completed.isoformat(),
            "lastSyncDuration": duration,
        })


# ── Schemas ───────────────────────────────────────────────────────────────────

class SyncStatus(BaseModel):
    """Matches TradeView/src/types/api.ts SyncStatus interface."""
    isRunning:        bool
    progress:         int
    startedAt:        Optional[str] = None
    completedAt:      Optional[str] = None
    itemsProcessed:   int = 0
    totalItems:       int = 0
    errors:           List[str] = []
    lastSyncAt:       Optional[str] = None
    lastSyncDuration: Optional[int] = None


class SyncLog(BaseModel):
    """Matches TradeView/src/types/api.ts SyncLog interface."""
    id:        str
    timestamp: str
    level:     str
    message:   str
    symbol:    Optional[str] = None


class TriggerResponse(BaseModel):
    message: str
    taskId:  Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/sync-instruments", response_model=TriggerResponse)
def trigger_sync(
    _user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> TriggerResponse:
    """
    Kick off an eToro instrument sync in the background.
    Returns immediately; poll /sync-status for progress.
    """
    with _lock:
        if _state["isRunning"]:
            return TriggerResponse(message="Sync already in progress")

    background_tasks.add_task(_run_sync)
    return TriggerResponse(
        message="Sync started — poll /api/v1/sync-status for progress",
        taskId=str(uuid.uuid4()),
    )


@router.get("/sync-status", response_model=SyncStatus)
def get_sync_status(_user: CurrentUser) -> SyncStatus:
    """Return the current sync state snapshot."""
    with _lock:
        snapshot = dict(_state)
    return SyncStatus(**snapshot)


@router.get("/sync-logs", response_model=List[SyncLog])
def get_sync_logs(
    _user: CurrentUser,
    limit: int = 50,
) -> List[SyncLog]:
    """Return the most recent sync log entries (newest last)."""
    with _lock:
        entries = list(_logs[-limit:])
    return [SyncLog(**e) for e in entries]
