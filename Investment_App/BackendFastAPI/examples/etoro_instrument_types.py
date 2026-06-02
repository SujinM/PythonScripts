#!/usr/bin/env python
"""
examples/etoro_instrument_types.py
────────────────────────────────────
Fetch all available instrument types and their IDs from the eToro Public API.

Endpoint:
    GET https://public-api.etoro.com/api/v1/market-data/instrument-types

Authentication headers required:
    x-request-id  — Any unique string (UUID recommended)
    x-api-key     — Your eToro Public API key
    x-user-key    — Your eToro user key

Setup:
    Copy ../.env.example to ../.env and fill in ETORO_API_KEY and ETORO_USER_KEY,
    OR export them as environment variables before running.

Usage:
    cd Investment_App/BackendFastAPI
    python examples/etoro_instrument_types.py
    python examples/etoro_instrument_types.py --raw      # print raw JSON
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

import requests

# ── Load .env if python-dotenv is available ───────────────────────────────────
try:
    from dotenv import load_dotenv

    _env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass  # fall back to environment variables already set in the shell

# ── API constants ─────────────────────────────────────────────────────────────

BASE_URL = os.getenv("ETORO_BASE_URL", "https://public-api.etoro.com")
ENDPOINT = f"{BASE_URL}/api/v1/market-data/instrument-types"

# Known local mapping for reference (matches etoroInstrument.ts)
LOCAL_TYPE_MAP: dict[int, str] = {
    1:  "Forex",
    2:  "Commodity",
    3:  "CFD",
    4:  "Indices",
    5:  "Stocks",
    6:  "ETF",
    7:  "Bonds",
    8:  "TrustFunds",
    9:  "Options",
    10: "Crypto",
}


def build_headers() -> dict[str, str]:
    api_key  = os.getenv("ETORO_API_KEY", "")
    user_key = os.getenv("ETORO_USER_KEY", "")

    if not api_key or not user_key:
        print(
            "WARNING: ETORO_API_KEY or ETORO_USER_KEY is not set.\n"
            "  Set them in BackendFastAPI/.env or as environment variables.\n"
            "  Example:\n"
            "    ETORO_API_KEY=your_api_key\n"
            "    ETORO_USER_KEY=your_user_key\n",
            file=sys.stderr,
        )

    return {
        "x-request-id": str(uuid.uuid4()),
        "x-api-key":    api_key,
        "x-user-key":   user_key,
        "Accept":       "application/json",
    }


def fetch_instrument_types(raw: bool = False) -> None:
    headers = build_headers()

    print(f"Fetching instrument types from:\n  {ENDPOINT}\n")

    response = requests.get(ENDPOINT, headers=headers, timeout=15)

    print(f"Status: {response.status_code}")

    if not response.ok:
        print(f"Error response:\n{response.text}", file=sys.stderr)
        sys.exit(1)

    if raw:
        print(response.text)
        return

    data = response.json()

    # Actual API response: {"instrumentTypes": [{"instrumentTypeID": 1, "instrumentTypeDescription": "Forex"}, ...]}
    if isinstance(data, dict) and "instrumentTypes" in data:
        items: list[dict] = data["instrumentTypes"]
    elif isinstance(data, list):
        items = data
    else:
        items = data.get("data", [])

    if not items:
        print("No instrument types returned.")
        return

    # ── Pretty-print table ────────────────────────────────────────────────────
    col_id   = max(len("ID"),   max(len(str(i.get("instrumentTypeID", ""))) for i in items))
    col_name = max(len("Name"), max(len(str(i.get("instrumentTypeDescription", ""))) for i in items))

    header = f"{'ID':<{col_id}}  {'Name':<{col_name}}  Local Mapping"
    print(header)
    print("-" * len(header))

    for item in sorted(items, key=lambda x: x.get("instrumentTypeID", 0)):
        type_id   = item.get("instrumentTypeID", "?")
        type_name = item.get("instrumentTypeDescription", "?")
        local     = LOCAL_TYPE_MAP.get(int(type_id), "(not in local map)") if str(type_id).isdigit() else ""
        print(f"{str(type_id):<{col_id}}  {str(type_name):<{col_name}}  {local}")

    print(f"\nTotal instrument types: {len(items)}")

    # ── Diff against local map ────────────────────────────────────────────────
    api_ids = {
        int(i.get("instrumentTypeID", -1))
        for i in items
        if str(i.get("instrumentTypeID", "")).isdigit()
    }
    missing_locally = api_ids - set(LOCAL_TYPE_MAP.keys())
    extra_locally   = set(LOCAL_TYPE_MAP.keys()) - api_ids

    if missing_locally:
        print(f"\nIDs returned by API but missing in local map: {sorted(missing_locally)}")
    if extra_locally:
        print(f"IDs in local map but not returned by API:     {sorted(extra_locally)}")
    if not missing_locally and not extra_locally:
        print("\nLocal map is in sync with the API.")


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch eToro instrument types")
    parser.add_argument(
        "--raw", action="store_true", help="Print raw JSON response instead of table"
    )
    args = parser.parse_args()
    fetch_instrument_types(raw=args.raw)


if __name__ == "__main__":
    main()
