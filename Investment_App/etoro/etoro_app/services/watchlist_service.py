"""
Watchlist service.

Fetches watchlist data from the eToro Public API via EToroClient and
normalises it into typed domain models.

Endpoint
--------
  GET /api/v1/watchlists
    Query params:
      itemsPerPageForSingle  (int,  1–1000, default 100)
      ensureBuiltinWatchlists (bool, default true)
      addRelatedAssets        (bool, default false)
"""

from __future__ import annotations

from typing import Any, Optional

from etoro_app.api.etoro_client import EToroClient
from etoro_app.core.logger import get_logger
from etoro_app.models.watchlist import (
    Watchlist,
    WatchlistItem,
    WatchlistsMeta,
    WatchlistsResult,
)

logger = get_logger(__name__)

_ENDPOINT = "/api/v1/watchlists"


def _parse_item(raw: dict[str, Any]) -> WatchlistItem:
    return WatchlistItem(
        item_id=int(raw.get("itemId", 0)),
        item_type=str(raw.get("itemType", "Instrument")),
        item_rank=int(raw.get("itemRank", 0)),
    )


def _parse_watchlist(raw: dict[str, Any]) -> Watchlist:
    items = [_parse_item(i) for i in raw.get("items") or []]
    related = [int(a) for a in raw.get("relatedAssets") or []]
    return Watchlist(
        watchlist_id=str(raw.get("watchlistId", "")),
        name=str(raw.get("name", "")),
        gcid=raw.get("Gcid"),
        watchlist_type=str(raw.get("watchlistType", "Static")),
        total_items=int(raw.get("totalItems", 0)),
        is_default=bool(raw.get("isDefault", False)),
        is_user_selected_default=bool(raw.get("isUserSelectedDefault", False)),
        rank=int(raw.get("watchlistRank", 0)),
        dynamic_url=raw.get("dynamicUrl"),
        items=items,
        related_assets=related,
    )


def _parse_meta(raw: Optional[dict[str, Any]]) -> Optional[WatchlistsMeta]:
    if not raw:
        return None
    return WatchlistsMeta(
        page_number=int(raw.get("pageNumber", 0)),
        items_per_page=int(raw.get("itemsPerPage", 100)),
        max_items_in_watchlist_limit=int(raw.get("maxItemsInWatchlistLimit", 1000)),
        max_watchlists_limit=int(raw.get("maxWatchlistsLimit", 10)),
    )


class WatchlistService:
    """
    Fetches and parses eToro user watchlists.

    Example::

        from etoro_app.api.etoro_client import EToroClient
        from etoro_app.core.config import Config
        from etoro_app.services.watchlist_service import WatchlistService

        client = EToroClient(Config())
        svc = WatchlistService(client)
        result = svc.get_watchlists()
        for wl in result.watchlists:
            print(wl.name, wl.total_items)
    """

    def __init__(self, client: EToroClient) -> None:
        self._client = client

    def get_watchlists(
        self,
        items_per_page: int = 100,
        ensure_builtin: bool = True,
        add_related_assets: bool = False,
    ) -> WatchlistsResult:
        """
        Fetch all watchlists for the authenticated user.

        Args:
            items_per_page:      Items per watchlist (1–1000, default 100).
            ensure_builtin:      Include built-in watchlists (default True).
            add_related_assets:  Include relatedAssets list (default False).

        Returns:
            WatchlistsResult with watchlists list and pagination meta.
        """
        params: dict[str, Any] = {
            "itemsPerPageForSingle": max(1, min(items_per_page, 1000)),
            "ensureBuiltinWatchlists": str(ensure_builtin).lower(),
            "addRelatedAssets": str(add_related_assets).lower(),
        }

        logger.info("Fetching eToro watchlists (items_per_page=%d)", items_per_page)
        raw: dict[str, Any] = self._client.get(_ENDPOINT, params=params)  # type: ignore[assignment]

        watchlists = [_parse_watchlist(w) for w in raw.get("watchlists") or []]
        meta = _parse_meta(raw.get("meta"))
        is_succeeded = bool(raw.get("isSucceeded", True))

        logger.info("Fetched %d watchlist(s) from eToro", len(watchlists))
        return WatchlistsResult(
            watchlists=watchlists,
            meta=meta,
            is_succeeded=is_succeeded,
        )
