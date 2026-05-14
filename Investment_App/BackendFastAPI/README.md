# Investment Portfolio Backend API

A scalable **FastAPI** backend that connects to multiple broker APIs (Upstox, eToro), normalises data into a unified portfolio model, and exposes analysis endpoints. Adding a new broker requires **one new file** — no changes to core logic.

---

## Architecture

```
API Routes  →  Services  →  BrokerRegistry  →  BrokerAdapters  →  External APIs
```

### CLI vs Server — two entry points, same logic

The CLI and the FastAPI server are independent entry points that share the same underlying code.
The server is **not** required for the CLI to work.

**CLI path** (`python -m app.cli holdings etoro`):
```
app/cli.py
  └─► PortfolioService
        └─► EToroAdapter
              └─► eToro API  (direct HTTP — no server involved)
```

**Server path** (`GET http://127.0.0.1:8000/api/v1/etoro/holdings`):
```
uvicorn → FastAPI routes
  └─► PortfolioService
        └─► EToroAdapter
              └─► eToro API  (direct HTTP)
```

Both paths call the **same `PortfolioService` and `EToroAdapter`** — the server is just an HTTP
wrapper around them. The CLI imports and calls those classes directly in-process.

The server is only needed when:
- A **frontend / browser** needs to hit the REST API
- Another service calls `http://127.0.0.1:8000/api/v1/...`
- You want to use the Swagger UI at `/docs`

### eToro Adapter — uses the etoro_app library

The `EToroAdapter` delegates entirely to the `etoro_app` library, which lives in `Investment_App/etoro/etoro_app/` and is installed as an editable package.

```
BackendFastAPI EToroAdapter
      │
      ├─ etoro_app.api.etoro_client.EToroClient       (requests + API-key headers + retry)
      ├─ etoro_app.services.portfolio_service          (fetch + enrich + normalise to dataclasses)
      └─ _SettingsConfig bridge                        (maps BackendFastAPI Settings → etoro Config)
              │
              ▼  _to_holding / _to_position / _to_trade converters
  app.models.portfolio Pydantic models
```

eToro authentication uses **two static API keys** (no OAuth2):
- `ETORO_API_KEY` — Public API Key (`x-api-key` header)
- `ETORO_USER_KEY` — User Key (`x-user-key` header)

Get both from: eToro account → Settings → Trading → API Key Management

```
BackendFastAPI/
├── app/
│   ├── main.py                    # FastAPI app factory + broker imports
│   ├── cli.py                     # Typer CLI tool
│   ├── core/
│   │   ├── config.py              # pydantic-settings (env vars)
│   │   ├── logger.py              # Structured logging
│   │   ├── cache.py               # In-memory TTL cache (Redis-swap-ready)
│   │   └── exceptions.py          # Domain exceptions
│   ├── models/
│   │   ├── portfolio.py           # Holding, Position, Trade, PortfolioSummary
│   │   └── responses.py           # APIResponse[T], ErrorResponse envelopes
│   ├── brokers/
│   │   ├── base.py                # IBrokerAdapter ABC
│   │   ├── registry.py            # BrokerRegistry — holds all adapters
│   │   ├── upstox.py              # UpstoxAdapter  (delegates to upstox_app)
│   │   └── etoro.py               # EToroAdapter   (delegates to etoro_app)
│   ├── services/
│   │   ├── portfolio_service.py   # Orchestrates broker calls + cache
│   │   ├── analysis_service.py    # Pure analysis: alerts, P&L, allocation
│   │   └── live_service.py        # Live price streaming (Upstox REST poll / eToro WebSocket)
│   └── api/
│       ├── deps.py                # FastAPI Depends() providers
│       └── v1/
│           ├── router.py          # Aggregate v1 router
│           ├── portfolio.py       # /holdings /positions /trades /summary
│           ├── analysis.py        # /analysis /alerts /brokers
│           └── live.py            # WS /api/v1/{broker}/ws/live
├── tests/
│   ├── conftest.py                # Fixtures + MockBrokerAdapter
│   ├── test_portfolio_service.py
│   ├── test_analysis_service.py
│   ├── test_brokers.py
│   └── test_api.py
├── requirements.txt
├── .env.example
└── pyproject.toml
```

---

## Setup

```bash
# 1. Clone / navigate to project
cd Investment_App/BackendFastAPI

# 2. Use Python 3.11+ (required by ../upstox and ../etoro)
python3.11 --version

# 3. Create project-local virtual environment
python3.11 -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS

# 4. Verify interpreter inside this shell
python --version               # must be 3.11+

# 5. Install dependencies
pip install -r requirements.txt

# 6. Broker libraries are installed via requirements.txt as editable deps:
#    -e ../upstox
#    -e ../etoro

# 7. Configure environment
cp .env.example .env
# Edit .env and fill in your broker credentials
```

If you still see "requires a different Python: 3.9.6 not in '>=3.11'", your shell is using a
different venv (for example the workspace root .venv). Activate this project venv explicitly:

```bash
source Investment_App/BackendFastAPI/.venv/bin/activate
python --version
pip --version
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development` or `production` |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `CACHE_TTL_SECONDS` | `300` | Cache time-to-live in seconds |
| `UPSTOX_API_KEY` | _(empty)_ | Upstox API key |
| `UPSTOX_API_SECRET` | _(empty)_ | Upstox API secret |
| `UPSTOX_ACCESS_TOKEN` | _(empty)_ | OAuth2 access token (required to call Upstox) |
| `UPSTOX_REDIRECT_URI` | `https://127.0.0.1` | OAuth2 redirect URI |
| `ETORO_API_KEY` | _(empty)_ | eToro Public API Key (`x-api-key` header) |
| `ETORO_USER_KEY` | _(empty)_ | eToro User Key (`x-user-key` header) |
| `ETORO_BASE_URL` | `https://public-api.etoro.com` | eToro REST API base URL (portfolio/holdings) |
| `REDIS_URL` | _(empty)_ | Optional Redis URL (in-memory used if blank) |

---

## Running the Server

```bash
# Development server (hot-reload)
uvicorn app.main:app --reload

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Via CLI
python -m app.cli serve --host 127.0.0.1 --port 8000 --reload
```

Interactive API docs: http://127.0.0.1:8000/docs

---

## API Endpoints

### System
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/brokers` | List all registered brokers |

### Portfolio
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/{broker}/holdings` | Long-term holdings |
| `GET` | `/api/v1/{broker}/positions` | Open positions |
| `GET` | `/api/v1/{broker}/trades` | Today's trades |
| `GET` | `/api/v1/{broker}/summary` | Portfolio summary with P&L |
| `POST` | `/api/v1/{broker}/cache/invalidate` | Clear broker cache |

### Analysis
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/{broker}/analysis` | Full analysis: P&L, alerts, sector allocation |
| `GET` | `/api/v1/{broker}/analysis/alerts` | Active alerts (loss/gain thresholds) |

### Live Prices (WebSocket)
| Method | Endpoint | Description |
|---|---|---|
| `WS` | `/api/v1/{broker}/ws/live` | Real-time price stream (auto-resolves holdings) |
| `WS` | `/api/v1/{broker}/ws/live?instruments=KEY1,KEY2` | Stream specific instruments |

eToro uses the **native eToro WebSocket** (`wss://ws.etoro.com/ws`) — prices are **pushed on every tick** (sub-second latency, no polling, no 429 errors).
Upstox uses REST polling every 1 second (`GET /v2/market-quote/ltp`).

Example tick message (eToro):
```json
{
  "broker": "etoro",
  "ticks": {
    "100001": {"name": "Ethereum", "bid": 1234.5, "ask": 1235.0, "ts": 1746567890.1}
  },
  "ts": 1746567890.1
}
```

**Supported broker IDs:** `upstox`, `etoro`

### Response Envelope

All endpoints return:
```json
{
  "status": "success",
  "data": { ... }
}
```
Errors:
```json
{
  "status": "error",
  "error": { "code": "BROKER_NOT_FOUND", "message": "Broker 'x' is not registered." }
}
```

---

## CLI Tool

```bash
# List registered brokers (shows all configured brokers)
python -m app.cli brokers

# ── Holdings ──────────────────────────────────────────────────────────────────

# View long-term holdings
python -m app.cli holdings upstox
python -m app.cli holdings etoro

# ── Positions ─────────────────────────────────────────────────────────────────

# View open / intraday positions
python -m app.cli positions upstox
python -m app.cli positions etoro

# ── Trades ────────────────────────────────────────────────────────────────────

# View today's executed trades
python -m app.cli trades upstox
python -m app.cli trades etoro

# ── Summary ───────────────────────────────────────────────────────────────────

# View portfolio summary (invested, current value, unrealised P&L, return %)
python -m app.cli summary upstox
python -m app.cli summary etoro

# ── Analysis ──────────────────────────────────────────────────────────────────

# Full analysis: P&L, top gainers/losers, exchange allocation, alerts
python -m app.cli analysis upstox
python -m app.cli analysis etoro

# ── Alerts ────────────────────────────────────────────────────────────────────

# Active alerts only (holdings down >5% or up >20%)
python -m app.cli alerts upstox
python -m app.cli alerts etoro

# ── Cache ─────────────────────────────────────────────────────────────────────

# Invalidate cached data and force a fresh API fetch
python -m app.cli invalidate upstox
python -m app.cli invalidate etoro

# ── Server ────────────────────────────────────────────────────────────────────

# Start server (development — hot reload)
python -m app.cli serve --port 8000 --reload

# Start server (production — custom host)
python -m app.cli serve --host 0.0.0.0 --port 8000
```

**Available broker IDs:** `upstox`, `etoro`

---

## Running Tests

```bash
pytest tests/ -v
```

**50 tests** covering:
- Broker registry (register, get, unknown)
- Unified model computed fields (P&L, return %)
- Portfolio service (fetch, cache, invalidate, summary)
- Analysis service (alerts, sector allocation, result builder)
- FastAPI routes (all endpoints, 404 handling, response structure)

---

## Adding a New Broker

1. Create `app/brokers/zerodha.py` (or any broker name)
2. Subclass `IBrokerAdapter` and implement `get_holdings()`, `get_positions()`, `get_trades()`
3. Call `registry.register(ZerodhaAdapter())` at the bottom of the file
4. Add `import app.brokers.zerodha` in `app/main.py` (and `app/cli.py`)

**That is all.** No changes to routes, services, models, or any other file.

### Using an existing broker app (e.g. a new broker)

If you have a standalone broker app with its own HTTP client and service layer, follow the pattern used by `UpstoxAdapter` and `EToroAdapter`:

1. Install the broker app as a library: `pip install -e ../newbroker`
2. Create `app/brokers/newbroker.py` and delegate to the broker app's client/service
3. Add a `_SettingsConfig`-style bridge that maps BackendFastAPI's `Settings` to the broker app's config interface
4. Convert the broker app's models to BackendFastAPI's unified Pydantic models

---

## Unified Portfolio Models

All broker adapters normalise to these Pydantic v2 models:

**`Holding`** — computed fields: `invested_value`, `current_value`, `unrealised_pnl`, `return_pct`

**`Position`** — computed fields: `total_pnl`

**`Trade`** — computed fields: `trade_value`

**`PortfolioSummary`** — aggregate totals + `top_gainers`, `top_losers`

---

## Security Notes

- Access tokens and API keys are read from environment variables — never hardcoded
- CORS is restricted to `[]` (empty) in `production` mode
- All external broker calls use HTTPS with a configurable timeout
- Upstox uses OAuth2 access tokens; eToro uses static API key pair (`x-api-key` + `x-user-key`)
- Auth errors return HTTP 401; broker errors return appropriate 4xx/5xx codes

---

## License

MIT
