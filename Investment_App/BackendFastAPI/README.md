# Investment Portfolio Backend API

A scalable **FastAPI** backend that connects to multiple broker APIs (Upstox, eToro), normalises data into a unified portfolio model, and exposes analysis endpoints. Adding a new broker requires **one new file** — no changes to core logic.

---

## Architecture

```
API Routes  →  Services  →  BrokerRegistry  →  BrokerAdapters  →  External APIs
```

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
│   │   └── analysis_service.py    # Pure analysis: alerts, P&L, allocation
│   └── api/
│       ├── deps.py                # FastAPI Depends() providers
│       └── v1/
│           ├── router.py          # Aggregate v1 router
│           ├── portfolio.py       # /holdings /positions /trades /summary
│           └── analysis.py        # /analysis /alerts /brokers
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

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install broker libraries as editable packages
pip install -e ../upstox     # provides upstox_app
pip install -e ../etoro      # provides etoro_app

# 5. Configure environment
cp .env.example .env
# Edit .env and fill in your broker credentials
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
| `ETORO_BASE_URL` | `https://public-api.etoro.com` | eToro API base URL |
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
# List registered brokers
python -m app.cli brokers

# View holdings
python -m app.cli holdings upstox

# View portfolio summary
python -m app.cli summary upstox

# Start server
python -m app.cli serve --port 8000 --reload
```

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
