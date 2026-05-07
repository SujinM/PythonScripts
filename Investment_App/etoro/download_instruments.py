"""
download_instruments.py
=======================
Downloads all available stock instruments from the eToro metadata endpoint
and stores them in a local SQLite database.

Endpoint:
    https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments

Stored fields per instrument:
    - InstrumentID       : Unique numeric ID used by eToro
    - SymbolFull         : Full trading symbol  (e.g. "AAPL")
    - InternalSymbolFull : eToro-internal symbol (e.g. "AAPL.US")
    - DisplayName        : Human-readable name  (e.g. "Apple")
    - ExchangeID         : Numeric ID of the exchange it trades on
    - InstrumentTypeID   : Numeric ID of the asset type (1=Stocks, etc.)

Usage:
    python download_instruments.py
    python download_instruments.py --db my_instruments.db
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import requests

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

# Public eToro metadata endpoint — no authentication required
INSTRUMENTS_URL = (
    "https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments"
)

# Default SQLite database file (created next to this script)
DEFAULT_DB_PATH = Path(__file__).parent / "instruments.db"

# Table name inside the database
TABLE_NAME = "instruments"

# Fields to extract from each instrument object in the API response
FIELDS = (
    "InstrumentID",
    "SymbolFull",
    "InternalSymbolFull",
    "DisplayName",
    "ExchangeID",
    "InstrumentTypeID",
)


# ──────────────────────────────────────────────────────────────────────────────
# Database helpers
# ──────────────────────────────────────────────────────────────────────────────


def create_table(conn: sqlite3.Connection) -> None:
    """
    Create the instruments table if it doesn't already exist.

    The table uses InstrumentID as the primary key so re-running the script
    updates existing rows instead of creating duplicates.
    """
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            InstrumentID       INTEGER PRIMARY KEY,
            SymbolFull         TEXT,
            InternalSymbolFull TEXT,
            DisplayName        TEXT,
            ExchangeID         INTEGER,
            InstrumentTypeID   INTEGER
        )
        """
    )
    conn.commit()


def upsert_instruments(
    conn: sqlite3.Connection, instruments: list[dict]
) -> int:
    """
    Insert or replace all instruments into the database.

    Uses INSERT OR REPLACE so that re-running the script refreshes data
    without creating duplicate rows.

    Returns the number of rows written.
    """
    rows = [
        (
            item.get("InstrumentID"),
            item.get("SymbolFull"),
            item.get("InternalSymbolFull"),
            item.get("DisplayName"),
            item.get("ExchangeID"),
            item.get("InstrumentTypeID"),
        )
        for item in instruments
        # Skip items that have no InstrumentID (malformed data guard)
        if item.get("InstrumentID") is not None
    ]

    conn.executemany(
        f"""
        INSERT OR REPLACE INTO {TABLE_NAME}
            (InstrumentID, SymbolFull, InternalSymbolFull,
             DisplayName, ExchangeID, InstrumentTypeID)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return len(rows)


# ──────────────────────────────────────────────────────────────────────────────
# API fetch
# ──────────────────────────────────────────────────────────────────────────────


def fetch_instruments() -> list[dict]:
    """
    Fetch the full instruments list from the eToro metadata API.

    The endpoint is public and requires no API key.
    Returns a flat list of instrument dicts.
    Raises SystemExit on network or JSON errors.
    """
    print(f"Fetching instruments from:\n  {INSTRUMENTS_URL}\n")

    try:
        # Set a 30-second timeout to avoid hanging indefinitely
        response = requests.get(INSTRUMENTS_URL, timeout=30)
        response.raise_for_status()  # raises HTTPError for 4xx/5xx responses
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect. Check your internet connection.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out after 30 seconds.")
        sys.exit(1)
    except requests.exceptions.HTTPError as exc:
        print(f"ERROR: HTTP {exc.response.status_code} — {exc}")
        sys.exit(1)
    except requests.exceptions.RequestException as exc:
        print(f"ERROR: Unexpected network error — {exc}")
        sys.exit(1)

    try:
        data = response.json()
    except ValueError:
        print("ERROR: Response is not valid JSON.")
        sys.exit(1)

    # The API returns a dict with an "InstrumentDisplayDatas" key
    # containing the list of instruments
    instruments: list[dict] = data.get("InstrumentDisplayDatas", [])

    if not instruments:
        # Fallback: maybe the response itself is a list
        if isinstance(data, list):
            instruments = data
        else:
            print("WARNING: No instruments found in the API response.")
            print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")

    return instruments


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────


def main(db_path: Path) -> None:
    """
    Full pipeline:
      1. Fetch instruments from eToro API
      2. Open (or create) the SQLite database
      3. Create the table if it doesn't exist
      4. Upsert all instruments
      5. Print a summary
    """
    # Step 1 — Download
    instruments = fetch_instruments()
    print(f"Received {len(instruments):,} instruments from API.")

    if not instruments:
        print("Nothing to store. Exiting.")
        return

    # Step 2 & 3 — Open DB and ensure table exists
    print(f"\nOpening database: {db_path}")
    with sqlite3.connect(db_path) as conn:
        create_table(conn)

        # Step 4 — Store
        count = upsert_instruments(conn, instruments)

        # Step 5 — Summary
        total_in_db = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE_NAME}"
        ).fetchone()[0]

    print(f"\n{'─' * 45}")
    print(f"  Instruments processed : {count:>8,}")
    print(f"  Total rows in DB      : {total_in_db:>8,}")
    print(f"  Database file         : {db_path}")
    print(f"{'─' * 45}")
    print("Done.")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download eToro instruments metadata into a SQLite database."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to the SQLite database file (default: {DEFAULT_DB_PATH})",
    )
    args = parser.parse_args()

    main(args.db)
