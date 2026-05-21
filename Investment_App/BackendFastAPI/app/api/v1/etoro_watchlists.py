"""
app/api/v1/etoro_watchlists.py
────────────────────────────────
eToro user watchlist endpoints.

Endpoints
─────────
  GET  /api/v1/etoro/watchlists          — all watchlists for the authenticated user
  GET  /api/v1/etoro/watchlists/{id}     — single watchlist by ID
"""

from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.auth.deps import CurrentUser
from app.core.config import get_settings
from app.core.exceptions import BrokerAuthError, BrokerError
from app.core.logger import get_logger
from etoro_app.api.etoro_client import EToroAuthError, EToroAPIError, EToroClient
from etoro_app.core.config import Config as _EtoroConfig
from etoro_app.services.watchlist_service import WatchlistService

router = APIRouter(prefix="/etoro/watchlists", tags=["etoro-watchlists"])
logger = get_logger(__name__)


# ── eToro client factory ──────────────────────────────────────────────────────

def _make_client() -> EToroClient:
    s = get_settings()

    class _Cfg(_EtoroConfig):
        def __init__(self) -> None:
            pass  # skip .env discovery
        @property
        def api_key(self) -> str:   return s.etoro_api_key
        @property
        def user_key(self) -> str:  return s.etoro_user_key
        @property
        def base_url(self) -> str:  return s.etoro_base_url

    return EToroClient(_Cfg())


# ── Response schemas ──────────────────────────────────────────────────────────

class WatchlistItemOut(BaseModel):
    item_id:   int
    item_type: str
    item_rank: int


class WatchlistOut(BaseModel):
    watchlist_id:             str
    name:                     str
    gcid:                     Optional[int]
    watchlist_type:           str
    total_items:              int
    is_default:               bool
    is_user_selected_default: bool
    rank:                     int
    dynamic_url:              Optional[str]
    items:                    List[WatchlistItemOut]
    related_assets:           List[int]


class WatchlistsMetaOut(BaseModel):
    page_number:                   int
    items_per_page:                int
    max_items_in_watchlist_limit:  int
    max_watchlists_limit:          int


class WatchlistsResponse(BaseModel):
    watchlists:   List[WatchlistOut]
    meta:         Optional[WatchlistsMetaOut]
    is_succeeded: bool
    total:        int


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_out(wl) -> WatchlistOut:
    return WatchlistOut(
        watchlist_id=wl.watchlist_id,
        name=wl.name,
        gcid=wl.gcid,
        watchlist_type=wl.watchlist_type,
        total_items=wl.total_items,
        is_default=wl.is_default,
        is_user_selected_default=wl.is_user_selected_default,
        rank=wl.rank,
        dynamic_url=wl.dynamic_url,
        items=[WatchlistItemOut(item_id=i.item_id, item_type=i.item_type, item_rank=i.item_rank)
               for i in wl.items],
        related_assets=wl.related_assets,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=WatchlistsResponse)
def get_watchlists(
    _current_user: CurrentUser,
    items_per_page: Annotated[int, Query(ge=1, le=1000, description="Items per watchlist")] = 100,
    ensure_builtin: Annotated[bool, Query(description="Include built-in watchlists")] = True,
    add_related_assets: Annotated[bool, Query(description="Include related assets")] = False,
) -> WatchlistsResponse:
    """Retrieve all watchlists for the authenticated eToro user."""
    try:
        svc = WatchlistService(_make_client())
        result = svc.get_watchlists(
            items_per_page=items_per_page,
            ensure_builtin=ensure_builtin,
            add_related_assets=add_related_assets,
        )
    except EToroAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except EToroAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    meta_out = None
    if result.meta:
        meta_out = WatchlistsMetaOut(
            page_number=result.meta.page_number,
            items_per_page=result.meta.items_per_page,
            max_items_in_watchlist_limit=result.meta.max_items_in_watchlist_limit,
            max_watchlists_limit=result.meta.max_watchlists_limit,
        )

    watchlists_out = [_to_out(wl) for wl in result.watchlists]
    return WatchlistsResponse(
        watchlists=watchlists_out,
        meta=meta_out,
        is_succeeded=result.is_succeeded,
        total=len(watchlists_out),
    )


@router.get("/{watchlist_id}", response_model=WatchlistOut)
def get_watchlist_by_id(
    watchlist_id: str,
    _current_user: CurrentUser,
    items_per_page: Annotated[int, Query(ge=1, le=1000)] = 100,
    ensure_builtin: Annotated[bool, Query()] = True,
    add_related_assets: Annotated[bool, Query()] = False,
) -> WatchlistOut:
    """Retrieve a single watchlist by its ID."""
    try:
        svc = WatchlistService(_make_client())
        result = svc.get_watchlists(
            items_per_page=items_per_page,
            ensure_builtin=ensure_builtin,
            add_related_assets=add_related_assets,
        )
    except EToroAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except EToroAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    match = next((wl for wl in result.watchlists if wl.watchlist_id == watchlist_id), None)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Watchlist '{watchlist_id}' not found.",
        )
    return _to_out(match)
