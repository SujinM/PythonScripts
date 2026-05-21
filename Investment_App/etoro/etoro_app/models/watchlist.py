"""
Domain data models for eToro watchlist entities.

API reference
─────────────
  GET /api/v1/watchlists
  Response: { watchlists: [...], meta: {...}, isSucceeded: bool }

Field mapping
─────────────
  watchlistId           → watchlist_id
  name                  → name
  Gcid                  → gcid
  watchlistType         → watchlist_type  ("Static" | "Dynamic")
  totalItems            → total_items
  isDefault             → is_default
  isUserSelectedDefault → is_user_selected_default
  watchlistRank         → rank
  dynamicUrl            → dynamic_url
  items[]               → items  (list of WatchlistItem)
  relatedAssets[]       → related_assets
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WatchlistItem:
    """A single instrument entry inside a watchlist."""

    item_id: int
    item_type: str          # "Instrument"
    item_rank: int


@dataclass
class Watchlist:
    """
    A user watchlist returned by GET /api/v1/watchlists.
    """

    watchlist_id: str
    name: str
    gcid: Optional[int]
    watchlist_type: str                         # "Static" | "Dynamic"
    total_items: int
    is_default: bool
    is_user_selected_default: bool
    rank: int
    dynamic_url: Optional[str] = None
    items: list[WatchlistItem] = field(default_factory=list)
    related_assets: list[int] = field(default_factory=list)


@dataclass
class WatchlistsMeta:
    """Pagination / limit metadata from the watchlists response."""

    page_number: int
    items_per_page: int
    max_items_in_watchlist_limit: int
    max_watchlists_limit: int


@dataclass
class WatchlistsResult:
    """Top-level result returned by the watchlist service."""

    watchlists: list[Watchlist]
    meta: Optional[WatchlistsMeta]
    is_succeeded: bool
