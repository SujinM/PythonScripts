#!/usr/bin/env python
"""
examples/etoro_candles.py
──────────────────────────
Fetch raw candle data for a single eToro instrument and print either the raw
JSON response or a compact OHLC table.

Endpoint used:
    GET /api/v1/market-data/instruments/candles

Authentication:
    ETORO_API_KEY  →  x-api-key header
    ETORO_USER_KEY →  x-user-key header

Usage:
    cd Investment_App/BackendFastAPI
    python examples/etoro_candles.py --instrument-id 1001
    python examples/etoro_candles.py --instrument-id 1001 --period OneYear
    python examples/etoro_candles.py --instrument-id 1001 --raw
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
ENDPOINT = "/api/v1/market-data/instruments/candles"


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


def fetch_candles(instrument_id: int, period: str) -> Any:
    response = requests.get(
        f"{BASE_URL}{ENDPOINT}",
        headers=build_headers(),
        params={"instrumentIds": str(instrument_id), "period": period},
        timeout=20,
    )
    if not response.ok:
        print(
            f"HTTP {response.status_code} from {ENDPOINT}:\n{response.text}",
            file=sys.stderr,
        )
        sys.exit(1)
    return response.json()


def extract_candles(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return []

    for key in ("candles", "bars", "data", "items", "ohlc"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    for value in payload.values():
        if isinstance(value, dict):
            nested = extract_candles(value)
            if nested:
                return nested

    return []


def pick_value(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in item and item[key] is not None:
            return item[key]
    return ""


def print_table(candles: list[dict[str, Any]], limit: int) -> None:
    if not candles:
        print("No candle rows found in the response. Use --raw to inspect the payload.")
        return

    rows = []
    for candle in candles[:limit]:
        rows.append(
            {
                "time": pick_value(candle, "timestamp", "time", "date", "dateTime", "fromTime"),
                "open": pick_value(candle, "open", "Open"),
                "high": pick_value(candle, "high", "High"),
                "low": pick_value(candle, "low", "Low"),
                "close": pick_value(candle, "close", "Close", "bid", "price"),
                "volume": pick_value(candle, "volume", "Volume"),
            }
        )

    widths = {
        "time": max(len("Time"), *(len(str(row["time"])) for row in rows)),
        "open": max(len("Open"), *(len(str(row["open"])) for row in rows)),
        "high": max(len("High"), *(len(str(row["high"])) for row in rows)),
        "low": max(len("Low"), *(len(str(row["low"])) for row in rows)),
        "close": max(len("Close"), *(len(str(row["close"])) for row in rows)),
        "volume": max(len("Volume"), *(len(str(row["volume"])) for row in rows)),
    }

    header = (
        f"{'Time':<{widths['time']}}  {'Open':>{widths['open']}}  "
        f"{'High':>{widths['high']}}  {'Low':>{widths['low']}}  "
        f"{'Close':>{widths['close']}}  {'Volume':>{widths['volume']}}"
    )
    print(header)
    print("-" * len(header))

    for row in rows:
        print(
            f"{str(row['time']):<{widths['time']}}  "
            f"{str(row['open']):>{widths['open']}}  "
            f"{str(row['high']):>{widths['high']}}  "
            f"{str(row['low']):>{widths['low']}}  "
            f"{str(row['close']):>{widths['close']}}  "
            f"{str(row['volume']):>{widths['volume']}}"
        )

    print(f"\nDisplayed {min(limit, len(candles))} of {len(candles)} candles.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch eToro candle data for one instrument")
    parser.add_argument("--instrument-id", type=int, required=True, help="eToro instrument ID")
    parser.add_argument(
        "--period",
        default="OneMonth",
        choices=["OneMonth", "OneYear"],
        help="Candle period supported by the current backend debug route",
    )
    parser.add_argument("--limit", type=int, default=10, help="Number of candle rows to print")
    parser.add_argument("--raw", action="store_true", help="Print raw JSON response")
    args = parser.parse_args()

    print(f"Fetching candles from:\n  {BASE_URL}{ENDPOINT}")
    print(f"Instrument ID: {args.instrument_id}")
    print(f"Period: {args.period}\n")

    payload = fetch_candles(args.instrument_id, args.period)
    if args.raw:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    candles = extract_candles(payload)
    print_table(candles, limit=args.limit)


if __name__ == "__main__":
    main()