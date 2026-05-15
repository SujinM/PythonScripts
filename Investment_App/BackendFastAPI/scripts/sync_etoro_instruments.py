#!/usr/bin/env python
"""
scripts/sync_etoro_instruments.py
───────────────────────────────────
Standalone script to fetch all eToro instrument metadata and store it in the
investment_app SQLite database.

Usage (run from BackendFastAPI/ directory):
    python scripts/sync_etoro_instruments.py
    python scripts/sync_etoro_instruments.py --db path/to/investment_app.db

The script can also be run directly from the project root:
    cd Investment_App/BackendFastAPI
    python scripts/sync_etoro_instruments.py
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

# ── Allow running without installing the package ──────────────────────────────
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import EtoroInstrument

# ── Constants ─────────────────────────────────────────────────────────────────

_API_URL = "https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments"

_INSTRUMENT_TYPES: dict[int, str] = {
    1: "Forex",
    2: "Commodities",
    3: "Indices",
    4: "Stocks",
    5: "ETFs",
    6: "Crypto",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _best_image(images: list[dict]) -> str | None:
    """Pick the 50×50 CDN URL; fall back to first http URI."""
    for img in images:
        uri = img.get("Uri", "")
        if img.get("Width") == 50 and uri.startswith("http"):
            return uri
    for img in images:
        uri = img.get("Uri", "")
        if uri.startswith("http"):
            return uri
    return None


def _fetch_instruments() -> list[dict]:
    print(f"  Fetching instruments from {_API_URL} …")
    with httpx.Client(timeout=30) as client:
        resp = client.get(_API_URL, headers={"User-Agent": "InvestmentPortfolio/1.0"})
        resp.raise_for_status()
    items: list[dict] = resp.json().get("InstrumentDisplayDatas", [])
    print(f"  ✓  Received {len(items):,} instruments from eToro API")
    return items


def sync(db_path: Path) -> None:
    print(f"\n{'─'*60}")
    print("  eToro Instrument Sync")
    print(f"{'─'*60}")
    print(f"  Database : {db_path}")

    # ── Engine ────────────────────────────────────────────────────
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        items = _fetch_instruments()
    except httpx.HTTPError as exc:
        print(f"\n  ERROR: Could not reach eToro API — {exc}")
        sys.exit(1)

    if not items:
        print("  ERROR: API returned no instruments")
        sys.exit(1)

    now = datetime.now(timezone.utc)
    inserted = updated = skipped = 0

    print("  Upserting records …", end="", flush=True)

    for i, item in enumerate(items):
        iid = item.get("InstrumentID")
        if iid is None:
            skipped += 1
            continue

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

        existing = db.get(EtoroInstrument, iid)
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(EtoroInstrument(instrument_id=iid, **data))
            inserted += 1

        # Commit in batches to avoid a single huge transaction
        if (i + 1) % 1000 == 0:
            db.commit()
            print(".", end="", flush=True)

    db.commit()
    db.close()

    print(f"\n\n{'─'*60}")
    print(f"  Sync complete")
    print(f"  Total    : {inserted + updated + skipped:>7,}")
    print(f"  Inserted : {inserted:>7,}  (new)")
    print(f"  Updated  : {updated:>7,}  (existing)")
    print(f"  Skipped  : {skipped:>7,}  (no InstrumentID)")
    print(f"{'─'*60}\n")

    # ── Summary by type ───────────────────────────────────────────
    db2 = Session()
    try:
        print("  Breakdown by instrument type:")
        rows = db2.query(
            EtoroInstrument.instrument_type_id,
            func.count(EtoroInstrument.instrument_id).label("cnt"),
        ).group_by(EtoroInstrument.instrument_type_id).all()
        for type_id, cnt in sorted(rows, key=lambda r: r[1], reverse=True):
            label = _INSTRUMENT_TYPES.get(type_id or 0, f"Unknown({type_id})")
            print(f"    {label:<15} {cnt:>6,}")
        print()
    finally:
        db2.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync eToro instruments into the local DB")
    parser.add_argument(
        "--db",
        type=Path,
        default=_ROOT / "investment_app.db",
        help="Path to the SQLite database file (default: BackendFastAPI/investment_app.db)",
    )
    args = parser.parse_args()
    sync(args.db)


if __name__ == "__main__":
    main()
