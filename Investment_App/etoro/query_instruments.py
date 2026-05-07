"""
query_instruments.py
====================
Interactive query tool for the instruments SQLite database.

Usage:
    python query_instruments.py                          # show summary + first 20 rows
    python query_instruments.py --search Apple           # search by name or symbol
    python query_instruments.py --type 1                 # filter by InstrumentTypeID
    python query_instruments.py --exchange 4             # filter by ExchangeID
    python query_instruments.py --limit 50               # change row limit
    python query_instruments.py --sql "SELECT * FROM instruments WHERE SymbolFull='AAPL'"
    python query_instruments.py --types                  # list all instrument types + counts
    python query_instruments.py --exchanges              # list all exchanges + counts
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_DB_PATH = Path(__file__).parent / "instruments.db"
TABLE = "instruments"

# Column widths for the main display table
COL_WIDTHS = {
    "InstrumentID":       10,
    "SymbolFull":         12,
    "InternalSymbolFull": 20,
    "DisplayName":        30,
    "ExchangeID":          6,
    "InstrumentTypeID":    6,
}


# ──────────────────────────────────────────────────────────────────────────────
# Display helpers
# ──────────────────────────────────────────────────────────────────────────────


def _trunc(value: object, width: int) -> str:
    """Truncate a value to fit within `width` characters."""
    s = str(value) if value is not None else ""
    return s[:width - 1] + "…" if len(s) > width else s.ljust(width)


def print_header() -> None:
    cols = COL_WIDTHS
    header = "  ".join(_trunc(col, w) for col, w in cols.items())
    sep    = "  ".join("─" * w for w in cols.values())
    print(header)
    print(sep)


def print_row(row: sqlite3.Row) -> None:
    cols = COL_WIDTHS
    line = "  ".join(_trunc(row[col], cols[col]) for col in cols)
    print(line)


def print_rows(rows: list[sqlite3.Row], title: str = "") -> None:
    if title:
        print(f"\n{'─' * 90}")
        print(f"  {title}")
        print(f"{'─' * 90}")
    print_header()
    for row in rows:
        print_row(row)
    print(f"\n  {len(rows):,} row(s) shown.")


# ──────────────────────────────────────────────────────────────────────────────
# Query functions
# ──────────────────────────────────────────────────────────────────────────────


def show_summary(conn: sqlite3.Connection) -> None:
    """Print total count and a breakdown by InstrumentTypeID."""
    total = conn.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
    print(f"\n{'═' * 50}")
    print(f"  Database: {DEFAULT_DB_PATH.name}")
    print(f"  Total instruments: {total:,}")
    print(f"{'═' * 50}")

    print("\n  Breakdown by InstrumentTypeID:")
    rows = conn.execute(
        f"SELECT InstrumentTypeID, COUNT(*) as cnt "
        f"FROM {TABLE} GROUP BY InstrumentTypeID ORDER BY cnt DESC"
    ).fetchall()
    for r in rows:
        print(f"    Type {r[0]:>4}  →  {r[1]:>6,} instruments")


def show_first(conn: sqlite3.Connection, limit: int) -> None:
    """Show the first N rows ordered by InstrumentID."""
    rows = conn.execute(
        f"SELECT * FROM {TABLE} ORDER BY InstrumentID LIMIT ?", (limit,)
    ).fetchall()
    print_rows(rows, f"First {limit} instruments (ordered by InstrumentID)")


def search(conn: sqlite3.Connection, term: str, limit: int) -> None:
    """Search DisplayName, SymbolFull, and InternalSymbolFull (case-insensitive)."""
    pattern = f"%{term}%"
    rows = conn.execute(
        f"""
        SELECT * FROM {TABLE}
        WHERE DisplayName        LIKE ? COLLATE NOCASE
           OR SymbolFull         LIKE ? COLLATE NOCASE
           OR InternalSymbolFull LIKE ? COLLATE NOCASE
        ORDER BY DisplayName
        LIMIT ?
        """,
        (pattern, pattern, pattern, limit),
    ).fetchall()
    print_rows(rows, f'Search results for "{term}" (limit {limit})')


def filter_by_type(conn: sqlite3.Connection, type_id: int, limit: int) -> None:
    """Show instruments with a specific InstrumentTypeID."""
    rows = conn.execute(
        f"SELECT * FROM {TABLE} WHERE InstrumentTypeID = ? ORDER BY DisplayName LIMIT ?",
        (type_id, limit),
    ).fetchall()
    print_rows(rows, f"InstrumentTypeID = {type_id} (limit {limit})")


def filter_by_exchange(conn: sqlite3.Connection, exchange_id: int, limit: int) -> None:
    """Show instruments listed on a specific exchange."""
    rows = conn.execute(
        f"SELECT * FROM {TABLE} WHERE ExchangeID = ? ORDER BY DisplayName LIMIT ?",
        (exchange_id, limit),
    ).fetchall()
    print_rows(rows, f"ExchangeID = {exchange_id} (limit {limit})")


def list_types(conn: sqlite3.Connection) -> None:
    """List all distinct InstrumentTypeIDs with counts."""
    rows = conn.execute(
        f"SELECT InstrumentTypeID, COUNT(*) as cnt "
        f"FROM {TABLE} GROUP BY InstrumentTypeID ORDER BY cnt DESC"
    ).fetchall()
    print(f"\n{'─' * 30}")
    print(f"  {'TypeID':<10}  {'Count':>8}")
    print(f"{'─' * 30}")
    for r in rows:
        print(f"  {r[0]:<10}  {r[1]:>8,}")
    print(f"\n  {len(rows)} distinct types.")


def list_exchanges(conn: sqlite3.Connection) -> None:
    """List all distinct ExchangeIDs with counts."""
    rows = conn.execute(
        f"SELECT ExchangeID, COUNT(*) as cnt "
        f"FROM {TABLE} GROUP BY ExchangeID ORDER BY cnt DESC"
    ).fetchall()
    print(f"\n{'─' * 30}")
    print(f"  {'ExchangeID':<12}  {'Count':>8}")
    print(f"{'─' * 30}")
    for r in rows:
        print(f"  {r[0]:<12}  {r[1]:>8,}")
    print(f"\n  {len(rows)} distinct exchanges.")


def run_custom_sql(conn: sqlite3.Connection, sql: str) -> None:
    """Execute a custom SELECT query and display results."""
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as exc:
        print(f"SQL error: {exc}")
        sys.exit(1)

    rows = cursor.fetchall()
    if not rows:
        print("No rows returned.")
        return

    # Build column info from cursor description
    col_names = [d[0] for d in cursor.description]
    col_widths = {col: max(len(col), 10) for col in col_names}

    # Measure actual data widths (cap at 40)
    for row in rows:
        for col, val in zip(col_names, row):
            col_widths[col] = min(40, max(col_widths[col], len(str(val or ""))))

    header = "  ".join(col.ljust(col_widths[col]) for col in col_names)
    sep    = "  ".join("─" * col_widths[col] for col in col_names)
    print(f"\n{header}")
    print(sep)
    for row in rows:
        line = "  ".join(
            (str(v) if v is not None else "")[:col_widths[col]].ljust(col_widths[col])
            for col, v in zip(col_names, row)
        )
        print(line)
    print(f"\n  {len(rows):,} row(s).")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query the eToro instruments SQLite database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--db",       type=Path, default=DEFAULT_DB_PATH, help="Path to SQLite DB")
    parser.add_argument("--search",   type=str,  help="Search by name or symbol")
    parser.add_argument("--type",     type=int,  dest="type_id",     help="Filter by InstrumentTypeID")
    parser.add_argument("--exchange", type=int,  dest="exchange_id", help="Filter by ExchangeID")
    parser.add_argument("--limit",    type=int,  default=20,         help="Max rows to display (default: 20)")
    parser.add_argument("--sql",      type=str,  help="Run a custom SQL SELECT query")
    parser.add_argument("--types",    action="store_true", help="List all InstrumentTypeIDs with counts")
    parser.add_argument("--exchanges",action="store_true", help="List all ExchangeIDs with counts")
    args = parser.parse_args()

    # Verify DB exists
    if not args.db.exists():
        print(f"ERROR: Database not found at {args.db}")
        print("Run download_instruments.py first to create it.")
        sys.exit(1)

    # Open connection with row_factory for named column access
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    try:
        if args.sql:
            run_custom_sql(conn, args.sql)
        elif args.search:
            search(conn, args.search, args.limit)
        elif args.type_id is not None:
            filter_by_type(conn, args.type_id, args.limit)
        elif args.exchange_id is not None:
            filter_by_exchange(conn, args.exchange_id, args.limit)
        elif args.types:
            list_types(conn)
        elif args.exchanges:
            list_exchanges(conn)
        else:
            # Default: summary + first N rows
            show_summary(conn)
            show_first(conn, args.limit)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
