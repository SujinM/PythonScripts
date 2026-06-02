#!/usr/bin/env python
"""
examples/etoro_watchlists.py
────────────────────────────
Fetch eToro watchlists for the authenticated user and print either the raw JSON
response or a compact summary table.

Endpoint used:
    GET /api/v1/watchlists

Authentication:
    ETORO_API_KEY  →  x-api-key header
    ETORO_USER_KEY →  x-user-key header

Usage:
    cd Investment_App/BackendFastAPI
    python examples/etoro_watchlists.py
    python examples/etoro_watchlists.py --items-per-page 200 --add-related-assets
    python examples/etoro_watchlists.py --raw
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import requests

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


BASE_URL = os.getenv("ETORO_BASE_URL", "https://public-api.etoro.com")
ENDPOINT = "/api/v1/watchlists"


def build_headers() -> dict[str, str]:
    api_key = os.getenv("ETORO_API_KEY", "")
    user_key = os.getenv("ETORO_USER_KEY", "")
    if not api_key or not user_key:
        print(
            "WARNING: ETORO_API_KEY or ETORO_USER_KEY is not set.\n"
            "  Add them to BackendFastAPI/.env before running.\n",
            file=sys.stderr,
        )

    return {
        "x-api-key": api_key,
        "x-user-key": user_key,
        "x-request-id": str(uuid.uuid4()),
        "Accept": "application/json",
    }


def fetch_watchlists(items_per_page: int, ensure_builtin: bool, add_related_assets: bool) -> Any:
    response = requests.get(
        f"{BASE_URL}{ENDPOINT}",
        headers=build_headers(),
        params={
            "itemsPerPageForSingle": max(1, min(items_per_page, 1000)),
            "ensureBuiltinWatchlists": str(ensure_builtin).lower(),
            "addRelatedAssets": str(add_related_assets).lower(),
        },
        timeout=20,
    )
    if not response.ok:
        print(
            f"HTTP {response.status_code} from {ENDPOINT}:\n{response.text}",
            file=sys.stderr,
        )
        sys.exit(1)
    return response.json()


def print_watchlists(payload: Any) -> None:
    if not isinstance(payload, dict):
        print("Unexpected response shape. Use --raw to inspect the payload.")
        return

    watchlists = payload.get("watchlists") or []
    meta = payload.get("meta") or {}
    if not watchlists:
        print("No watchlists returned.")
        return

    rows = []
    for item in watchlists:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "id": item.get("watchlistId", ""),
                "name": item.get("name", ""),
                "type": item.get("watchlistType", ""),
                "items": item.get("totalItems", 0),
                "default": item.get("isDefault", False),
                "related": len(item.get("relatedAssets") or []),
            }
        )

    widths = {
        "id": max(len("Watchlist ID"), *(len(str(row["id"])) for row in rows)),
        "name": max(len("Name"), *(len(str(row["name"])) for row in rows)),
        "type": max(len("Type"), *(len(str(row["type"])) for row in rows)),
        "items": max(len("Items"), *(len(str(row["items"])) for row in rows)),
        "default": max(len("Default"), *(len(str(row["default"])) for row in rows)),
        "related": max(len("Related"), *(len(str(row["related"])) for row in rows)),
    }

    header = (
        f"{'Watchlist ID':<{widths['id']}}  {'Name':<{widths['name']}}  {'Type':<{widths['type']}}  "
        f"{'Items':>{widths['items']}}  {'Default':>{widths['default']}}  {'Related':>{widths['related']}}"
    )
    print(header)
    print("-" * len(header))

    for row in rows:
        print(
            f"{str(row['id']):<{widths['id']}}  {str(row['name']):<{widths['name']}}  {str(row['type']):<{widths['type']}}  "
            f"{str(row['items']):>{widths['items']}}  {str(row['default']):>{widths['default']}}  {str(row['related']):>{widths['related']}}"
        )

    print(f"\nWatchlists returned: {len(rows)}")
    if meta:
        print(
            "Meta: "
            f"page={meta.get('pageNumber', '?')}, "
            f"itemsPerPage={meta.get('itemsPerPage', '?')}, "
            f"maxItemsInWatchlist={meta.get('maxItemsInWatchlistLimit', '?')}, "
            f"maxWatchlists={meta.get('maxWatchlistsLimit', '?')}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch eToro watchlists for the authenticated user")
    parser.add_argument("--items-per-page", type=int, default=100, help="Items per watchlist, clamped to 1-1000")
    parser.add_argument(
        "--ensure-builtin",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include built-in watchlists",
    )
    parser.add_argument(
        "--add-related-assets",
        action="store_true",
        help="Include relatedAssets in the response",
    )
    parser.add_argument("--raw", action="store_true", help="Print raw JSON response")
    args = parser.parse_args()

    print(f"Fetching watchlists from:\n  {BASE_URL}{ENDPOINT}")
    print(f"itemsPerPageForSingle: {max(1, min(args.items_per_page, 1000))}")
    print(f"ensureBuiltinWatchlists: {str(args.ensure_builtin).lower()}")
    print(f"addRelatedAssets: {str(args.add_related_assets).lower()}\n")

    payload = fetch_watchlists(args.items_per_page, args.ensure_builtin, args.add_related_assets)
    if args.raw:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    print_watchlists(payload)


if __name__ == "__main__":
    main()