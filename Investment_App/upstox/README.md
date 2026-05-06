# Upstox Investment Analyzer

A **production-grade** Python CLI application for analyzing your Upstox investment portfolio.
Fetches real-time holdings, positions, and trades — then computes P&L, returns, top gainers/losers, and threshold alerts.

Also includes a full **Analytics Token subsystem** for read-only market data: live quotes, OHLC, historical candles, option chains, Greeks, instrument search, brokerage calculator, and margin estimator — no OAuth2 redirect required.

---

## Project Structure

```
upstox/
├── app/
│   ├── __init__.py
│   ├── __main__.py              # python -m app entry point
│   ├── main.py                  # CLI commands (typer + rich)
│   ├── core/
│   │   ├── config.py            # Secure env-var config loader
│   │   └── logger.py            # Centralized logging factory
│   ├── api/
│   │   ├── upstox_client.py     # OAuth2 + HTTP adapter (portfolio APIs)
│   │   └── analytics_client.py  # Analytics Token HTTP adapter (market data)
│   ├── services/
│   │   ├── portfolio_service.py  # Fetch & normalize portfolio data
│   │   ├── analysis_service.py   # Pure investment analysis logic
│   │   └── analytics_service.py  # Fetch & normalize market data (read-only)
│   ├── models/
│   │   ├── portfolio.py          # Portfolio domain models
│   │   └── market_data.py        # Market data models (Quote, Candle, Greeks, …)
│   └── utils/
│       └── helpers.py            # Formatting utilities
├── tests/
│   ├── conftest.py
│   ├── test_portfolio_service.py
│   ├── test_analysis_service.py
│   └── test_analytics_service.py
├── .env.example             # Safe template — commit this
├── .env                     # Your secrets — NEVER commit
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Setup

### 1. Prerequisites

- Python 3.11+
- An [Upstox developer account](https://developer.upstox.com/) with an app created

### 2. Clone & create virtual environment

```bash
cd Investment_App/upstox
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
# --- OAuth2 (required for portfolio commands) ---
UPSTOX_API_KEY=your_api_key_here
UPSTOX_API_SECRET=your_api_secret_here
UPSTOX_REDIRECT_URI=https://127.0.0.1   # must match exactly what is registered in your app

# --- Access token (obtained after running auth) ---
UPSTOX_ACCESS_TOKEN=

# --- Analytics Token (required for analytics commands) ---
UPSTOX_ANALYTICS_TOKEN=your_analytics_token_here
```

> **Security**: `.env` is listed in `.gitignore` and will never be committed.
> Never paste credentials into source code.

#### Getting credentials from the Upstox portal

1. Go to [Upstox Developer Apps](https://account.upstox.com/developer/apps)
2. Open your app — copy the **API Key** (`UPSTOX_API_KEY`) and **API Secret** (`UPSTOX_API_SECRET`)
3. Note the exact **Redirect URL** registered — set `UPSTOX_REDIRECT_URI` to match it character-for-character (including or excluding trailing slash)

#### Obtaining the Analytics Token

1. On the same app page, click **Analytics Token** → generate or copy it
2. Paste it as `UPSTOX_ANALYTICS_TOKEN` in `.env`
3. The Analytics Token is **read-only**, valid for **1 year**, and does not require an OAuth2 redirect

---

## Authentication

Upstox access tokens are valid for one trading day and are required for all portfolio commands.
Two methods are available:

### Option A — OAuth2 browser flow

```bash
python -m app auth
```

Steps:
1. A browser tab opens to the Upstox authorization URL
2. Log in and approve the app
3. Copy the `code` value from the redirect URL (e.g. `https://127.0.0.1?code=mk404x`)
4. Paste it into the terminal prompt
5. The access token is printed — add it to `.env`:

```dotenv
UPSTOX_ACCESS_TOKEN=<paste-token-here>
```

### Option B — Direct token request (v3, no browser)

Calls `POST /v3/login/auth/token/request/{api_key}` directly.
Requires only `UPSTOX_API_KEY` and `UPSTOX_API_SECRET` — no redirect URI, no browser.

```bash
python -m app request-token
```

The token is printed — add it to `.env` as `UPSTOX_ACCESS_TOKEN`.

---

## API Endpoints Reference

| Command | Endpoint | Auth required |
|---|---|---|
| `auth` (dialog) | `GET /v2/login/authorization/dialog` | API Key + Secret |
| `auth` (exchange) | `POST /v2/login/authorization/token` | Auth code |
| `request-token` | `POST /v3/login/auth/token/request/{api_key}` | API Key + Secret |
| Portfolio commands | `GET /v2/portfolio/...` | Access Token |
| Analytics commands | `GET /v3/market-quote/...` | Analytics Token |

---

## Usage

### Portfolio commands (require Access Token)

```bash
# Get an access token first (choose one):
python -m app auth             # OAuth2 browser flow (v2)
python -m app request-token   # Direct v3 request — no browser

# Full portfolio report (holdings + positions + trades)
python -m app summary

# Long-term holdings with P&L
python -m app holdings

# Top 10 holdings
python -m app holdings --top 10

# Open intraday/F&O positions
python -m app positions

# Today's executed trades
python -m app trades

# Threshold alerts (default: gain ≥ 20%, loss ≤ -10%)
python -m app alerts

# Custom thresholds
python -m app alerts --gain 30 --loss -15

# Override access token inline (useful for automation/scripts)
python -m app holdings --token "Bearer eyJ..."
```

### Analytics commands (require Analytics Token)

```bash
# Last traded prices — lightest payload
python -m app analytics ltp "NSE_EQ|INE009A01021"
python -m app analytics ltp "NSE_EQ|INE009A01021" "NSE_EQ|INE040A01034"

# Full market quote (OHLCV, bid/ask depth, circuit limits, 52W H/L)
python -m app analytics quotes "NSE_EQ|INE009A01021"

# OHLC snapshot
# Valid intervals: 1d  I1  I30  (aliases: day, 1minute, 1min, 30minute, 30min)
python -m app analytics ohlc "NSE_EQ|INE009A01021"
python -m app analytics ohlc "NSE_EQ|INE009A01021" --interval I30
python -m app analytics ohlc "NSE_EQ|INE009A01021" --interval 30minute   # alias for I30

# Historical OHLCV candles
python -m app analytics candles "NSE_EQ|INE009A01021" --interval day --from 2026-01-01 --to 2026-05-05
python -m app analytics candles "NSE_EQ|INE009A01021" --interval 30minute --from 2026-05-01 --to 2026-05-05 --limit 20

# Exchange market status
python -m app analytics market-status
python -m app analytics market-status --exchange NSE

# Option chain (ATM-centered, 10 strikes each side by default)
python -m app analytics option-chain "NSE_INDEX|Nifty 50" --expiry 2026-05-29
python -m app analytics option-chain "NSE_INDEX|Nifty 50" --expiry 2026-05-29 --strikes 5

# Option Greeks (Î” Î“ Î˜ Vega Ï IV)
python -m app analytics option-greeks "NSE_INDEX|Nifty 50" --expiry 2026-05-29
python -m app analytics option-greeks "NSE_INDEX|Nifty 50" --expiry 2026-05-29 --type CE

# Instrument search by name, symbol, or ISIN
python -m app analytics search RELIANCE
python -m app analytics search NIFTY --type index

# Signed WebSocket URL for V3 real-time market data feed
python -m app analytics feed-url

# Brokerage + statutory charges calculator
python -m app analytics brokerage "NSE_EQ|INE009A01021" --qty 10 --price 1650 --tx BUY
python -m app analytics brokerage "NSE_EQ|INE009A01021" --qty 10 --price 1650 --tx SELL --product D --exchange NSE
```

#### OHLC interval reference

| `--interval` value | API code sent | Meaning |
|---|---|---|
| `1d` or `day` | `1d` | Daily candle |
| `I1`, `1minute`, `1min` | `I1` | 1-minute candle |
| `I30`, `30minute`, `30min` | `I30` | 30-minute candle |

---

## Running Tests

All tests use mocks — no network calls and no credentials required.

```bash
# Run all tests
pytest

# Verbose output with short tracebacks
pytest -v --tb=short
```

| Test file | Tests | Coverage area |
|---|---|---|
| `test_portfolio_service.py` | 20 | Portfolio normalization, API fetch, TTL cache |
| `test_analysis_service.py` | 19 | P&L analysis, alerts, sector allocation, trade volume |
| `test_analytics_service.py` | 50 | All analytics API methods, response normalization, cache, models |
| **Total** | **89** | |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `UPSTOX_API_KEY` | Yes | API Key from the developer portal (OAuth2 client ID) |
| `UPSTOX_API_SECRET` | Yes | API Secret from the developer portal (OAuth2 client secret) |
| `UPSTOX_REDIRECT_URI` | Yes | Redirect URL registered in your app — must match exactly |
| `UPSTOX_ACCESS_TOKEN` | Portfolio commands | Daily access token obtained via `auth` or `request-token` |
| `UPSTOX_ANALYTICS_TOKEN` | Analytics commands | 1-year read-only token from the developer portal |
| `UPSTOX_BASE_URL` | No | Override portfolio API base URL (default: `https://api.upstox.com/v2`) |
| `UPSTOX_ANALYTICS_BASE_URL` | No | Override analytics API base URL (default: `https://api.upstox.com`) |
| `CACHE_TTL_SECONDS` | No | In-memory cache TTL in seconds (default: `300`) |
| `LOG_LEVEL` | No | `DEBUG` / `INFO` / `WARNING` / `ERROR` (default: `INFO`) |

---

## Architecture Decisions

| Concern | Decision | Reason |
|---|---|---|
| Config | `python-dotenv` + env vars | Secrets never in source code |
| HTTP | `requests` + retry adapter | Battle-tested, easy to mock; retries 429/5xx with backoff |
| CLI | `typer` + `rich` | Clean UX, minimal boilerplate, colour-coded tables |
| Models | `dataclasses` | Lightweight, typed, no ORM overhead |
| Caching | In-memory TTL dict | Avoids redundant API calls within a session |
| DI | Constructor injection | Services fully testable without patching internals |
| Analytics vs Portfolio | Separate clients | Different auth schemes; analytics is strictly read-only |
| Analytics token validation | Fail-fast in `__init__` | Clear error before any network call is made |

---

## Extending the Application

### Regenerating the `upstox_app` installable package

The `upstox_app/` directory is a **generated copy** of `app/` with all internal
imports rewritten from `from app.` → `from upstox_app.`.
It exists so that other projects (e.g. `BackendFastAPI`) can install and import
this library without conflicting with their own `app/` package.

```bash
# Run from the upstox/ project root
python create_upstox_app.py
```

**What it does:**
1. Removes the existing `upstox_app/` directory
2. Copies the entire `app/` tree into `upstox_app/`
3. Rewrites every `from app.` → `from upstox_app.` and `import app.` → `import upstox_app.` in the copied files

**When to run it:**
- After adding or renaming any module inside `app/`
- After changing any internal import paths
- Before publishing or installing the package into another project

**Installing the generated package (editable mode):**
```bash
# From BackendFastAPI or any other project that consumes upstox_app
pip install -e ../upstox
```

### Add a new broker (e.g. Zerodha Kite)

1. Create `app/api/kite_client.py` implementing the same `get()` / `post()` interface
2. Create `app/services/kite_portfolio_service.py` reusing the same normalization pattern
3. `AnalysisService` requires **zero changes** — it operates on domain models only

### Add ML-based prediction (Phase 3)

```python
# app/services/prediction_service.py
class PredictionService:
    def predict_trend(self, holdings: list[Holding]) -> dict[str, str]: ...
```

Inject it alongside `AnalysisService` in `main.py`.

### Add database persistence

Replace the in-memory cache in `PortfolioService` with a repository pattern:

```python
# app/repositories/holdings_repository.py
class HoldingsRepository:
    def save(self, holdings: list[Holding]) -> None: ...
    def load_latest(self) -> list[Holding]: ...
```

### Expose a REST API (Vue.js / FastAPI)

```python
# app/api/router.py
@router.get("/holdings")
def get_holdings() -> list[dict]:
    return [asdict(h) for h in portfolio_svc.get_holdings()]
```

---

## Completed Phases

### Phase 1 — Portfolio Analyzer
- [x] OAuth2 browser flow (`auth`) and direct token request (`request-token`)
- [x] Holdings, positions, trades, and summary commands with rich tables
- [x] P&L analysis, top gainers/losers, configurable gain/loss alerts
- [x] Retry-backed HTTP adapter, in-memory TTL cache, structured logging
- [x] 39 unit tests (portfolio service + analysis service)

### Phase 2 — Analytics Token Subsystem
- [x] `AnalyticsClient` — dedicated read-only HTTP client using the Analytics Token
- [x] `AnalyticsService` — normalization layer with TTL cache for all 13 market data APIs
- [x] 13 typed market data models (`Quote`, `OHLCQuote`, `LTPQuote`, `Candle`, `MarketStatusEntry`, `OptionChainEntry`, `OptionSide`, `OptionGreeks`, `OptionContract`, `InstrumentSearchResult`, `MarketFeedAuthorization`, `BrokerageDetail`, `MarginDetail`)
- [x] 10 CLI analytics commands: `ltp`, `quotes`, `ohlc`, `candles`, `market-status`, `option-chain`, `option-greeks`, `search`, `feed-url`, `brokerage`
- [x] OHLC interval alias mapping (`30minute` → `I30`, `1minute` → `I1`, `day` → `1d`)
- [x] Symbol derived from V3 response key when no symbol field is present
- [x] 50 unit tests (all analytics service methods, cache, computed model properties)

---

## Phase 3 Roadmap

- [ ] Sector allocation breakdown
- [ ] Diversification score (HHI-based)
- [ ] Historical performance tracking
- [ ] Moving averages (7-day, 30-day) using historical candles
- [ ] Risk metrics (volatility, Sharpe ratio)
- [ ] Scheduled alerts via email / WhatsApp
- [ ] WebSocket live feed integration (V3 market data stream)

---

## Security

- API keys stored in `.env` — excluded from git via `.gitignore`
- Access tokens **never logged** — only printed to stdout on auth
- No credentials stored in code, comments, or config files
- Input validation at system boundaries (config loader raises on missing keys)

---

## License

MIT
