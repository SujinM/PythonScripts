#!/usr/bin/env python
"""
examples/etoro_portfolio.py
────────────────────────────
Fetch all currently invested instruments (stocks, ETFs, crypto, forex, etc.)
from the eToro Public API and display them in a readable table.

Endpoints used:
    GET /api/v1/trading/info/real/pnl          — open positions + unrealised P&L
    GET /api/v1/market-data/instruments        — instrument metadata (name, type)
    GET /api/v1/market-data/instruments/rates  — live bid prices

Authentication:
    ETORO_API_KEY  →  x-api-key header
    ETORO_USER_KEY →  x-user-key header

Setup:
    Set credentials in BackendFastAPI/.env, or export as environment variables.

Usage:
    cd Investment_App/BackendFastAPI
    python examples/etoro_portfolio.py
    python examples/etoro_portfolio.py --type stocks       # filter by type
    python examples/etoro_portfolio.py --type etf
    python examples/etoro_portfolio.py --raw               # print raw JSON
    python examples/etoro_portfolio.py --no-enrich         # skip metadata lookup
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

# ── Load .env if python-dotenv is available ───────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# ── Constants ─────────────────────────────────────────────────────────────────

BASE_URL = os.getenv("ETORO_BASE_URL", "https://public-api.etoro.com")

ENDPOINTS = {
    "pnl":       "/api/v1/trading/info/real/pnl",
    "metadata":  "/api/v1/market-data/instruments",
    "rates":     "/api/v1/market-data/instruments/rates",
}

# Confirmed from live API — /api/v1/market-data/instrument-types
INSTRUMENT_TYPE_MAP: dict[int, str] = {
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


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _headers() -> dict[str, str]:
    api_key  = os.getenv("ETORO_API_KEY", "")
    user_key = os.getenv("ETORO_USER_KEY", "")
    if not api_key or not user_key:
        print(
            "WARNING: ETORO_API_KEY or ETORO_USER_KEY is not set.\n"
            "  Add them to BackendFastAPI/.env before running.\n",
            file=sys.stderr,
        )
    return {
        "x-api-key":    api_key,
        "x-user-key":   user_key,
        "x-request-id": str(uuid.uuid4()),
        "Accept":       "application/json",
    }


def _get(endpoint: str, params: dict | None = None) -> Any:
    url = f"{BASE_URL}{endpoint}"
    resp = requests.get(url, headers=_headers(), params=params, timeout=30)
    if not resp.ok:
        print(f"HTTP {resp.status_code} from {endpoint}:\n{resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


# ── Data fetching ─────────────────────────────────────────────────────────────

def fetch_open_positions() -> list[dict]:
    """
    Fetch open positions from the portfolio P&L endpoint.
    Returns a flat list of raw position dicts.
    """
    data = _get(ENDPOINTS["pnl"])
    portfolio = data.get("clientPortfolio", {}) if isinstance(data, dict) else {}

    positions: list[dict] = list(portfolio.get("positions") or [])

    # Mirrors (copy trading / smart portfolios) — flatten their positions too
    for mirror in portfolio.get("mirrors") or []:
        positions.extend(mirror.get("positions") or [])

    return positions


def fetch_instrument_metadata(instrument_ids: list[int]) -> dict[int, dict]:
    """
    Fetch display name and instrument type for each instrument ID.
    Returns a mapping of instrumentID → metadata dict.
    """
    if not instrument_ids:
        return {}

    # The endpoint accepts a comma-separated list of IDs via the
    # instrumentIds query param.
    params = {"instrumentIds": ",".join(str(i) for i in instrument_ids)}
    data = _get(ENDPOINTS["metadata"], params=params)

    items: list[dict] = (
        data if isinstance(data, list)
        else data.get("instruments", data.get("data", []))
    )

    result: dict[int, dict] = {}
    for item in items:
        iid = item.get("instrumentId") or item.get("InstrumentID") or item.get("id")
        if iid is not None:
            result[int(iid)] = item
    return result


def fetch_live_rates(instrument_ids: list[int]) -> dict[int, float]:
    """
    Fetch live bid prices for each instrument ID.
    Returns a mapping of instrumentID → bid price.
    """
    if not instrument_ids:
        return {}

    params = {"instrumentIds": ",".join(str(i) for i in instrument_ids)}
    data = _get(ENDPOINTS["rates"], params=params)

    items: list[dict] = (
        data if isinstance(data, list)
        else data.get("rates", data.get("data", []))
    )

    result: dict[int, float] = {}
    for item in items:
        iid = item.get("instrumentId") or item.get("InstrumentID") or item.get("id")
        bid = item.get("bid") or item.get("Bid") or item.get("rate") or item.get("Rate")
        if iid is not None and bid is not None:
            try:
                result[int(iid)] = float(bid)
            except (TypeError, ValueError):
                pass
    return result


# ── Display ───────────────────────────────────────────────────────────────────

def _col(value: Any, width: int) -> str:
    return str(value)[:width].ljust(width)


def print_positions(
    positions: list[dict],
    metadata: dict[int, dict],
    rates: dict[int, float],
    type_filter: str | None,
) -> None:
    if not positions:
        print("No open positions found.")
        return

    # Build enriched rows
    rows = []
    for pos in positions:
        iid = pos.get("instrumentID") or pos.get("instrumentId") or pos.get("InstrumentID")
        if iid is None:
            continue
        iid = int(iid)

        meta = metadata.get(iid, {})

        # Resolve display name
        name = (
            meta.get("symbolFull")
            or meta.get("instrumentDisplayName")
            or meta.get("displayName")
            or meta.get("name")
            or meta.get("InstrumentDisplayName")
            or pos.get("instrumentName")
            or str(iid)
        )

        # Resolve instrument type
        type_id = (
            meta.get("instrumentTypeID")
            or meta.get("instrumentTypeId")
            or pos.get("instrumentTypeID")
        )
        type_label = INSTRUMENT_TYPE_MAP.get(int(type_id), f"Type#{type_id}") if type_id else "Unknown"

        # Filter by type if requested
        if type_filter and type_label.lower() != type_filter.lower():
            continue

        # Financial values
        invested   = pos.get("invested")       or pos.get("Invested")       or 0
        net_profit = pos.get("netProfit")      or pos.get("NetProfit")      or 0
        open_rate  = pos.get("openRate")       or pos.get("OpenRate")       or pos.get("openPrice") or 0
        close_rate = rates.get(iid) or pos.get("closeRate") or pos.get("CloseRate") or 0
        direction  = "BUY" if not pos.get("isSell") else "SELL"

        rows.append({
            "id":          iid,
            "name":        name,
            "type":        type_label,
            "direction":   direction,
            "invested":    float(invested),
            "open_rate":   float(open_rate),
            "current":     float(close_rate),
            "net_profit":  float(net_profit),
        })

    if not rows:
        label = f" of type '{type_filter}'" if type_filter else ""
        print(f"No open positions{label} found.")
        return

    # Sort by type then name
    rows.sort(key=lambda r: (r["type"], r["name"]))

    # Column widths
    w_name   = max(len("Instrument"), max(len(r["name"])  for r in rows))
    w_type   = max(len("Type"),       max(len(r["type"])  for r in rows))
    w_dir    = len("Direction")

    header = (
        f"{'Instrument':<{w_name}}  {'Type':<{w_type}}  {'Dir':<{w_dir}}"
        f"  {'Invested':>10}  {'Open Rate':>10}  {'Current':>10}  {'Net P&L':>10}"
    )
    print(header)
    print("-" * len(header))

    total_invested = 0.0
    total_pnl = 0.0

    for r in rows:
        pnl_str = f"{r['net_profit']:+.2f}"
        print(
            f"{r['name']:<{w_name}}  {r['type']:<{w_type}}  {r['direction']:<{w_dir}}"
            f"  {r['invested']:>10.2f}  {r['open_rate']:>10.4f}  {r['current']:>10.4f}  {pnl_str:>10}"
        )
        total_invested += r["invested"]
        total_pnl      += r["net_profit"]

    print("-" * len(header))
    print(
        f"{'TOTAL':<{w_name}}  {'':<{w_type}}  {'':<{w_dir}}"
        f"  {total_invested:>10.2f}  {'':>10}  {'':>10}  {total_pnl:+10.2f}"
    )
    print(f"\nPositions shown: {len(rows)}")

    # Summary by type
    print("\n--- By Instrument Type ---")
    by_type: dict[str, dict] = {}
    for r in rows:
        t = r["type"]
        if t not in by_type:
            by_type[t] = {"count": 0, "invested": 0.0, "pnl": 0.0}
        by_type[t]["count"]    += 1
        by_type[t]["invested"] += r["invested"]
        by_type[t]["pnl"]      += r["net_profit"]

    for t, s in sorted(by_type.items()):
        print(f"  {t:<12}  {s['count']:>3} positions  invested: {s['invested']:>10.2f}  P&L: {s['pnl']:>+10.2f}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch invested instruments from eToro")
    parser.add_argument("--raw",      action="store_true", help="Print raw JSON from the P&L endpoint")
    parser.add_argument("--no-enrich", action="store_true", help="Skip metadata and rates lookup")
    parser.add_argument(
        "--type",
        metavar="TYPE",
        help="Filter by instrument type (e.g. Stocks, ETF, Crypto, Forex, Commodity)",
    )
    args = parser.parse_args()

    print(f"Fetching open positions from:\n  {BASE_URL}{ENDPOINTS['pnl']}\n")

    if args.raw:
        data = _get(ENDPOINTS["pnl"])
        print(json.dumps(data, indent=2))
        return

    positions = fetch_open_positions()
    print(f"Open positions found: {len(positions)}")

    if not positions:
        return

    instrument_ids = list({
        int(p.get("instrumentID") or p.get("instrumentId") or p.get("InstrumentID"))
        for p in positions
        if p.get("instrumentID") or p.get("instrumentId") or p.get("InstrumentID")
    })

    metadata: dict[int, dict] = {}
    rates:    dict[int, float] = {}

    if not args.no_enrich:
        print(f"Fetching metadata for {len(instrument_ids)} instruments...")
        try:
            metadata = fetch_instrument_metadata(instrument_ids)
        except SystemExit:
            print("  (metadata lookup failed — continuing without enrichment)", file=sys.stderr)

        print("Fetching live rates...")
        try:
            rates = fetch_live_rates(instrument_ids)
        except SystemExit:
            print("  (rates lookup failed — continuing without live prices)", file=sys.stderr)

    print()
    print_positions(positions, metadata, rates, type_filter=args.type)


if __name__ == "__main__":
    main()
