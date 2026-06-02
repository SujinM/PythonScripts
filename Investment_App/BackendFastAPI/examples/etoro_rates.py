#!/usr/bin/env python
"""
examples/etoro_rates.py
────────────────────────
Fetch live rate data for one or more eToro instrument IDs and print either the
raw JSON response or a compact table of the most useful quote fields.

Endpoint used:
    GET /api/v1/market-data/instruments/rates

Authentication:
    ETORO_API_KEY  →  x-api-key header
    ETORO_USER_KEY →  x-user-key header

Usage:
    cd Investment_App/BackendFastAPI
    python examples/etoro_rates.py --instrument-ids 1001
    python examples/etoro_rates.py --instrument-ids 1001,9425,100001
    python examples/etoro_rates.py --instrument-ids 1001 --raw
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
ENDPOINT = "/api/v1/market-data/instruments/rates"


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


def parse_ids(raw_ids: str) -> list[int]:
    instrument_ids: list[int] = []
    for part in raw_ids.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            instrument_ids.append(int(part))
        except ValueError:
            print(f"Invalid instrument ID: {part}", file=sys.stderr)
            sys.exit(2)

    if not instrument_ids:
        print("At least one instrument ID is required.", file=sys.stderr)
        sys.exit(2)

    return instrument_ids


def fetch_rates(instrument_ids: list[int]) -> Any:
    response = requests.get(
        f"{BASE_URL}{ENDPOINT}",
        headers=build_headers(),
        params={"instrumentIds": ",".join(str(i) for i in instrument_ids)},
        timeout=20,
    )
    if not response.ok:
        print(
            f"HTTP {response.status_code} from {ENDPOINT}:\n{response.text}",
            file=sys.stderr,
        )
        sys.exit(1)
    return response.json()


def extract_rates(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        rates = payload.get("rates")
        if isinstance(rates, list):
            return [item for item in rates if isinstance(item, dict)]
    return []


def pick_value(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in item and item[key] is not None:
            return item[key]
    return ""


def print_table(rates: list[dict[str, Any]]) -> None:
    if not rates:
        print("No rates returned.")
        return

    rows = []
    for rate in rates:
        rows.append(
            {
                "id": pick_value(rate, "instrumentID", "instrumentId", "id"),
                "bid": pick_value(rate, "bid", "Bid"),
                "ask": pick_value(rate, "ask", "Ask"),
                "last": pick_value(rate, "lastExecution", "last", "price"),
                "change": pick_value(rate, "change", "Change"),
                "pct": pick_value(rate, "percentage", "changePercent", "percentageChange"),
                "volume": pick_value(rate, "volume", "Volume"),
            }
        )

    widths = {
        "id": max(len("Instrument"), *(len(str(row["id"])) for row in rows)),
        "bid": max(len("Bid"), *(len(str(row["bid"])) for row in rows)),
        "ask": max(len("Ask"), *(len(str(row["ask"])) for row in rows)),
        "last": max(len("Last"), *(len(str(row["last"])) for row in rows)),
        "change": max(len("Change"), *(len(str(row["change"])) for row in rows)),
        "pct": max(len("%Change"), *(len(str(row["pct"])) for row in rows)),
        "volume": max(len("Volume"), *(len(str(row["volume"])) for row in rows)),
    }

    header = (
        f"{'Instrument':<{widths['id']}}  {'Bid':>{widths['bid']}}  "
        f"{'Ask':>{widths['ask']}}  {'Last':>{widths['last']}}  "
        f"{'Change':>{widths['change']}}  {'%Change':>{widths['pct']}}  "
        f"{'Volume':>{widths['volume']}}"
    )
    print(header)
    print("-" * len(header))

    for row in rows:
        print(
            f"{str(row['id']):<{widths['id']}}  "
            f"{str(row['bid']):>{widths['bid']}}  "
            f"{str(row['ask']):>{widths['ask']}}  "
            f"{str(row['last']):>{widths['last']}}  "
            f"{str(row['change']):>{widths['change']}}  "
            f"{str(row['pct']):>{widths['pct']}}  "
            f"{str(row['volume']):>{widths['volume']}}"
        )

    print(f"\nRates returned: {len(rows)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch eToro live rates for one or more instruments")
    parser.add_argument(
        "--instrument-ids",
        required=True,
        help="Comma-separated eToro instrument IDs, for example 1001,9425,100001",
    )
    parser.add_argument("--raw", action="store_true", help="Print raw JSON response")
    args = parser.parse_args()

    instrument_ids = parse_ids(args.instrument_ids)

    print(f"Fetching live rates from:\n  {BASE_URL}{ENDPOINT}")
    print(f"Instrument IDs: {','.join(str(i) for i in instrument_ids)}\n")

    payload = fetch_rates(instrument_ids)
    if args.raw:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    print_table(extract_rates(payload))


if __name__ == "__main__":
    main()