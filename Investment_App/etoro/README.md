# eToro Portfolio Analyzer

A **production-grade** Python CLI application for analyzing your eToro investment portfolio.
Fetches open positions and closed trade history via the **eToro Public API** — then computes P&L, returns, top gainers/losers, and threshold alerts.

Also ships as an **installable library** (`etoro_app`) for use in FastAPI backends or other Python projects.

---

## Project Structure

```
etoro/
├── app/                          # CLI application (thin wrappers)
│   ├── __init__.py
│   ├── __main__.py               # python -m app entry point
│   ├── main.py                   # CLI commands (typer + rich)
│   ├── core/
│   │   ├── config.py             # Secure env-var config loader
│   │   └── logger.py             # Centralized logging factory
│   ├── api/
│   │   └── etoro_client.py       # API-key headers + HTTP adapter + retry
│   ├── services/
│   │   ├── portfolio_service.py  # Fetch & normalize portfolio data
│   │   └── analysis_service.py   # Pure investment analysis logic
│   ├── models/
│   │   └── portfolio.py          # Position, ClosedPosition, PortfolioSummary dataclasses
│   └── utils/
│       └── helpers.py            # Formatting utilities
├── etoro_app/                    # Installable library (auto-generated from app/)
│   └── ...                       # Same structure; imports use etoro_app.* prefix
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_portfolio_service.py
│   └── test_analysis_service.py
├── create_etoro_app.py           # Script to regenerate etoro_app/ from app/
├── download_instruments.py       # Download all eToro instruments → instruments.db
├── query_instruments.py          # Query / search instruments.db from the CLI
├── instruments.db                # SQLite database (git-ignored — run download_instruments.py)
├── .env.example                  # Safe template — commit this
├── .env                          # Your secrets — NEVER commit
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Setup

### 1. Prerequisites

- Python 3.11+
- An eToro account with **API Key Management** enabled (see credentials section below)

### 2. Create virtual environment

```bash
cd Investment_App/etoro
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure credentials

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```dotenv
# eToro Public API credentials
ETORO_API_KEY=your_public_api_key_here
ETORO_USER_KEY=your_user_key_here

# Optional overrides
# ETORO_BASE_URL=https://public-api.etoro.com
```

> **Security**: `.env` is listed in `.gitignore` and will never be committed.
> Never paste credentials into source code.

#### Getting your API keys from eToro

1. Log in to your eToro account at [etoro.com](https://www.etoro.com)
2. Go to **Settings** → **Trading** → **API Key Management**
3. Copy the **Public API Key** → `ETORO_API_KEY`
4. Copy the **User Key** → `ETORO_USER_KEY`

API documentation: [api-portal.etoro.com](https://api-portal.etoro.com/)

---

## Authentication

The eToro Public API uses **two static API keys** sent as request headers — no OAuth2 flow, no token exchange, no browser redirect.

Every request automatically includes:

| Header | Value |
|---|---|
| `x-api-key` | Your Public API Key (`ETORO_API_KEY`) |
| `x-user-key` | Your User Key (`ETORO_USER_KEY`) |
| `x-request-id` | Auto-generated UUID per request |

Set both keys in `.env` once and all commands work immediately.

---

## API Endpoints Reference

| Command | Endpoint(s) | Notes |
|---|---|---|
| `positions` | `GET /api/v1/trading/info/real/pnl` | Open positions; enriched with metadata + live rates (see below) |
| `history` | `GET /api/v1/trading/info/trade/history?minDate=...` | Closed trade history |
| `summary` | Both above | — |
| `alerts` | Positions endpoint | — |

### Data enrichment for open positions

The `/api/v1/trading/info/real/pnl` endpoint does **not** return instrument names, types, or live prices.
After fetching positions the service makes two additional batch calls:

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/market-data/instruments?instrumentIds=...` | Resolves `instrumentID` → display name + type ID |
| `GET /api/v1/market-data/instruments/rates?instrumentIds=...` | Resolves `instrumentID` → live bid price |

Both calls use a **batch-then-fallback** strategy: the service first tries a single request with all IDs comma-separated; if that returns 500 (which happens when any single ID is invalid or internal to eToro), it retries each ID individually so valid instruments still resolve.

The `current_rate` is taken from the portfolio's own `closeRate` field if non-zero, otherwise from the live rates response (`bid`). `unrealised_pnl` is taken from the API's `pnL` field if non-zero, otherwise computed as `(current_rate − open_rate) × units` (Buy) or `(open_rate − current_rate) × units` (Sell).

---

## Usage

### Portfolio commands

```bash
# Display all open positions
python -m app positions

# Display closed trade history (last 50 by default)
python -m app history

# Show only the last 20 closed trades
python -m app history --limit 20

# Full portfolio summary with top gainers/losers
python -m app summary
```

### Alerts

```bash
# Threshold alerts (default: gain ≥ 20%, loss ≤ -10%)
python -m app alerts

# Custom thresholds
python -m app alerts --gain 30 --loss -15
```

---

## Sample Output

### `python -m app positions`

```
                                                   Open Positions
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┓
┃ #    ┃ Instrument          ┃ Type   ┃ Dir   ┃ Invested ┃   Units ┃ Open Rate ┃   Current ┃      P&L ┃ Return % ┃   Lev ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━┩
│ 1    │ Apple               │ stocks │ Buy   │  $250.00 │  0.9092 │  274.9800 │  278.6400 │    $3.33 │   +1.33% │    1x │
│ 2    │ Intel               │ stocks │ Buy   │  $200.70 │ 10.0000 │   20.0700 │  105.8800 │  $858.10 │ +427.55% │    1x │
│ 3    │ Canadian Solar Inc. │ stocks │ Buy   │  $500.00 │ 27.7778 │   18.0000 │   16.2800 │  -$47.78 │   -9.56% │    1x │
│ 4    │ Ethereum            │ crypto │ Buy   │  $199.97 │  0.0872 │ 2293.7823 │ 2388.6000 │    $8.27 │   +4.13% │    1x │
└──────┴─────────────────────┴────────┴───────┴──────────┴─────────┴───────────┴───────────┴──────────┴──────────┴───────┘

Total open positions: 4
```

### `python -m app summary`

```
────────────────────── Portfolio Summary ───────────────────────
  Total Invested     : $3,500.00
  Current Value      : $3,360.00
  Unrealised P&L     : -$140.00
  Overall Return     : -4.00%
  Open Positions     : 3
  Closed Positions   : 12

──────────────────────── Top Gainers ───────────────────────────
  Apple Inc.             +5.00%   +$50.00
  EUR/USD                +2.00%   +$10.00

────────────────────────── Top Losers ──────────────────────────
  Bitcoin               -10.00%  -$200.00
```

---

## Instruments Database

Two standalone scripts let you download and query the full eToro instruments catalogue
(15,000+ instruments) from the public metadata endpoint — no API key required.

### Step 1 — Download instruments

Fetches all instruments and stores them in a local SQLite database (`instruments.db`).

```bash
# Default — creates instruments.db next to the script
python download_instruments.py

# Custom database path
python download_instruments.py --db C:\data\etoro.db
```

Expected output:
```
Fetching instruments from:
  https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments

Received 15,497 instruments from API.

Opening database: instruments.db
─────────────────────────────────────────────
  Instruments processed :   15,497
  Total rows in DB      :   15,497
  Database file         : instruments.db
─────────────────────────────────────────────
Done.
```

> Re-running the script refreshes existing rows — no duplicates are created.

---

### Step 2 — Query instruments

```bash
# Default: summary breakdown + first 20 rows
python query_instruments.py

# Search by display name or symbol (case-insensitive)
python query_instruments.py --search Apple
python query_instruments.py --search TSLA
python query_instruments.py --search Bitcoin

# Filter by InstrumentTypeID
python query_instruments.py --type 5          # Stocks (12,407 instruments)
python query_instruments.py --type 10         # Crypto
python query_instruments.py --type 1          # Currencies
python query_instruments.py --type 2          # Commodities
python query_instruments.py --type 4          # ETFs

# Filter by ExchangeID
python query_instruments.py --exchange 4

# Change the number of rows displayed (default: 20)
python query_instruments.py --limit 100
python query_instruments.py --type 5 --limit 50

# List all InstrumentTypeIDs with counts
python query_instruments.py --types

# List all ExchangeIDs with counts
python query_instruments.py --exchanges

# Run any custom SQL SELECT query
python query_instruments.py --sql "SELECT * FROM instruments WHERE SymbolFull = 'AAPL'"
python query_instruments.py --sql "SELECT * FROM instruments WHERE DisplayName LIKE '%Tesla%'"
python query_instruments.py --sql "SELECT COUNT(*) FROM instruments WHERE InstrumentTypeID = 5"

# Use a non-default database file
python query_instruments.py --db C:\data\etoro.db --search Gold
```

### Instrument type reference

| `InstrumentTypeID` | Type |
|---|---|
| 1 | Currencies |
| 2 | Commodities |
| 3 | Indices |
| 4 | ETFs |
| 5 | Stocks |
| 10 | Crypto |

### Database schema

```sql
CREATE TABLE instruments (
    InstrumentID       INTEGER PRIMARY KEY,
    SymbolFull         TEXT,    -- e.g. "AAPL"
    InternalSymbolFull TEXT,    -- e.g. "AAPL.US"
    DisplayName        TEXT,    -- e.g. "Apple"
    ExchangeID         INTEGER,
    InstrumentTypeID   INTEGER
);
```

---

## Running Tests

```bash
# From the etoro/ project root
python -m pytest tests/ -v
```

Expected output: **37 tests passing**

```
tests/test_analysis_service.py::TestGenerateSummary::test_totals_calculated_correctly  PASSED
tests/test_analysis_service.py::TestCheckAlerts::test_gain_alert_triggered             PASSED
tests/test_analysis_service.py::TestAnalyseByType::test_groups_by_type                PASSED
tests/test_models.py::TestPosition::test_unrealised_pnl_buy                           PASSED
tests/test_models.py::TestClosedPosition::test_trade_value                            PASSED
tests/test_portfolio_service.py::TestGetPositions::test_returns_normalized_positions  PASSED
tests/test_portfolio_service.py::TestCacheInvalidation::test_invalidate_clears_cache  PASSED
...
37 passed in 0.28s
```

---

## Using as a Library (`etoro_app`)

The `etoro_app` package is the importable library version of this project.
It is installed alongside the CLI app via `pip install -e .`.

```python
from etoro_app.core.config import Config
from etoro_app.api.etoro_client import EToroClient
from etoro_app.services.portfolio_service import PortfolioService

config = Config()                          # reads ETORO_API_KEY + ETORO_USER_KEY from .env
client = EToroClient(config)               # x-api-key / x-user-key headers added automatically

service = PortfolioService(client, cache_ttl=300)

positions = service.get_positions()        # list[Position]
history   = service.get_closed_positions() # list[ClosedPosition]

for p in positions:
    print(f"{p.instrument_name}: {p.return_percentage:+.2f}%  P&L: ${p.unrealised_pnl:,.2f}")
```

### Install as editable package (for development)

```bash
# From the PythonScripts/ workspace root
pip install -e Investment_App/etoro
```

### Regenerating `etoro_app/` after editing `app/`

```bash
python create_etoro_app.py
```

This copies `app/` to `etoro_app/` and rewrites all `from app.` imports to `from etoro_app.`.

---

## BackendFastAPI Integration

This app is integrated into the multi-broker FastAPI backend at `Investment_App/BackendFastAPI/`.

The `EToroAdapter` in `BackendFastAPI/app/brokers/etoro.py` delegates to `etoro_app` and maps:

| eToro model | Unified model |
|---|---|
| `Position` (open trade) | `Holding` + `Position` |
| `ClosedPosition` | `Trade` |

Required environment variables for BackendFastAPI:

```dotenv
ETORO_API_KEY=your_public_api_key
ETORO_USER_KEY=your_user_key
# ETORO_BASE_URL=https://public-api.etoro.com  # optional
```

REST endpoints available once BackendFastAPI is running:

```
GET  /api/v1/etoro/holdings
GET  /api/v1/etoro/positions
GET  /api/v1/etoro/trades
GET  /api/v1/etoro/summary
GET  /api/v1/etoro/analysis
POST /api/v1/etoro/cache/invalidate
```

---

## Models Reference

### `Position` (open trade)

| Field | Type | Description |
|---|---|---|
| `position_id` | str | Unique position identifier |
| `instrument_id` | int | eToro instrument ID |
| `instrument_name` | str | Instrument display name |
| `instrument_type` | str | `stocks`, `crypto`, `etf`, `currencies`, `indices`, `commodities` — resolved via metadata API |
| `direction` | str | `Buy` or `Sell` |
| `amount` | float | Invested amount (account currency) |
| `units` | float | Number of units / shares |
| `open_rate` | float | Price at open |
| `current_rate` | float | Portfolio `closeRate` if non-zero, otherwise live `bid` from rates API |
| `leverage` | int | Leverage multiplier (1 = no leverage) |
| `unrealised_pnl` | float | API `pnL` field if non-zero, otherwise computed from `current_rate` |
| `return_percentage` | float | Computed: `unrealised_pnl / amount × 100` |
| `current_value` | float | Computed: `current_rate × units` |

### `ClosedPosition` (trade history)

| Field | Type | Description |
|---|---|---|
| `position_id` | str | Unique position identifier |
| `instrument_name` | str | Instrument display name |
| `direction` | str | `Buy` or `Sell` |
| `amount` | float | Original invested amount |
| `open_rate` | float | Price at open |
| `close_rate` | float | Price at close |
| `realised_pnl` | float | Realised profit or loss |
| `open_date` | datetime | When the position was opened |
| `close_date` | datetime | When the position was closed |
| `return_percentage` | float | Computed: `realised_pnl / amount × 100` |

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `ETORO_API_KEY` | ✅ | — | Public API Key (`x-api-key` header) — from eToro Settings → Trading → API Key Management |
| `ETORO_USER_KEY` | ✅ | — | User Key (`x-user-key` header) — from same page |
| `ETORO_BASE_URL` | optional | `https://public-api.etoro.com` | API base URL |
| `LOG_LEVEL` | optional | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `CACHE_TTL_SECONDS` | optional | `300` | API response cache lifetime (seconds) |

---

## Security Notes

- `.env` is git-ignored — never commit secrets to version control
- All credentials are read from environment variables, never hardcoded
- The HTTP client uses HTTPS exclusively
- Retries are limited (3 attempts) with exponential backoff; HTTP 500 is **not** retried (it indicates a genuine API error, not a transient failure)
- Both API keys are validated at startup; a descriptive error is raised if either is missing

---

## Known eToro API Behaviour

- **Batch market-data requests return 500** when any single instrument ID in the list is invalid or internal (e.g. copy-trading virtual instruments with IDs like `100001`). The service handles this automatically by falling back to individual per-ID requests.
- **`closeRate` and `pnL` may be 0** in the portfolio response (observed when querying outside market hours). The service falls back to the live rates endpoint and computes P&L locally.
- **Instrument type IDs** confirmed from live API responses:

| `instrumentTypeID` | `instrument_type` |
|---|---|
| 1 | `currencies` |
| 2 | `commodities` |
| 3 | `indices` |
| 4 | `etf` |
| 5 | `stocks` |
| 10 | `crypto` |
