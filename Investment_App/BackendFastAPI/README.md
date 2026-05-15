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
│   │   ├── portfolio_service.py       # Orchestrates broker calls + cache
│   │   ├── analysis_service.py        # Pure analysis: alerts, P&L, allocation
│   │   ├── live_service.py            # Live price streaming (Upstox REST poll / eToro WebSocket)
│   │   ├── recommendation_service.py  # AI scoring engine (trend/momentum/valuation/risk)
│   │   ├── backtest_service.py        # 20-scenario sweep for signal flip analysis
│   │   └── etoro_market_service.py    # Live eToro prices via Public API (bid, 24h change)
│   └── api/
│       ├── deps.py                # FastAPI Depends() providers
│       └── v1/
│           ├── router.py          # Aggregate v1 router
│           ├── portfolio.py       # /holdings /positions /trades /summary
│           ├── analysis.py        # /analysis /alerts /brokers
│           ├── market.py          # /market/{symbol} live price endpoints
│           ├── ai.py              # /ai/recommendation  /ai/backtest/{symbol}
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
| `UPSTOX_REDIRECT_URI` | `https://127.0.0.1` | OAuth2 redirect URI — **must match** the URI registered in your Upstox Developer App. Set to `http://localhost:8000/callback` for local development |
| `FRONTEND_URL` | `http://localhost:3000` | TradeView frontend URL — used to build the post-auth redirect back to the Settings page |
| `ETORO_API_KEY` | _(empty)_ | eToro Public API Key (`x-api-key` header) |
| `ETORO_USER_KEY` | _(empty)_ | eToro User Key (`x-user-key` header) |
| `ETORO_BASE_URL` | `https://public-api.etoro.com` | eToro REST API base URL (portfolio/holdings) |
| `REDIS_URL` | _(empty)_ | Optional Redis URL (in-memory used if blank) |

---

## Upstox Authentication

The backend implements a full **OAuth2 Authorization Code** flow so the TradeView dashboard can connect a user's Upstox account without any manual copy-paste.

### Prerequisites

1. Log in to the [Upstox Developer Portal](https://developer.upstox.com/) and create (or open) your app.
2. Set the **Redirect URL** field to:
   ```
   http://localhost:8000/callback
   ```
3. Copy your **API Key** and **API Secret** into `.env`:
   ```env
   UPSTOX_API_KEY=<your-api-key>
   UPSTOX_API_SECRET=<your-api-secret>
   UPSTOX_REDIRECT_URI=http://localhost:8000/callback
   FRONTEND_URL=http://localhost:3000
   ```

### How the flow works

```
User clicks "Connect Upstox" in Settings
         │
         ▼
GET /api/v1/upstox/auth/url          ← frontend asks backend for the login URL
         │  returns { url: "https://api.upstox.com/v2/login/..." }
         ▼
window.location.href = url           ← browser navigates to Upstox login page
         │
         │  (user logs in)
         ▼
Upstox redirects →  http://localhost:8000/callback?code=<auth-code>
         │
         ▼
GET /callback  (public endpoint — no JWT needed)
  ├─ exchanges auth code for access token  (POST to Upstox token URL)
  ├─ writes UPSTOX_ACCESS_TOKEN to BackendFastAPI/.env
  ├─ writes UPSTOX_ACCESS_TOKEN to upstox/.env
  ├─ clears settings cache so new token is live immediately
  └─ RedirectResponse → http://localhost:3000/settings?upstox_auth=success
         │
         ▼
Settings page reads ?upstox_auth=success
  ├─ shows success notification
  ├─ removes query param from URL
  └─ fetches /api/v1/upstox/auth/status → badge changes to "Connected"
```

If the user denies access or an error occurs, Upstox sends `?error=...` and the user is redirected to `/settings?upstox_auth=error&message=<reason>` where the dashboard shows the error notification.

### Endpoints reference

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /callback` | None (public) | Receives Upstox redirect, exchanges code, saves token |
| `GET /api/v1/upstox/auth/url` | Bearer JWT | Returns the authorization URL to open in the browser |
| `GET /api/v1/upstox/auth/status` | Bearer JWT | Returns `{ configured: bool, token_preview: "eyJ0eXA…" }` |
| `POST /api/v1/upstox/auth/callback` | Bearer JWT | Manual code exchange fallback |

### Token persistence

The access token is written to two files on the server:

| File | Purpose |
|---|---|
| `BackendFastAPI/.env` → `UPSTOX_ACCESS_TOKEN` | Used by the FastAPI portfolio endpoints |
| `upstox/.env` → `UPSTOX_ACCESS_TOKEN` | Used by the `upstox_app` CLI tool |

After writing, `get_settings.cache_clear()` is called so every subsequent API call immediately uses the new token without a server restart.

### Re-authentication

Upstox access tokens expire daily (at midnight IST). Simply click **Re-authenticate** in the dashboard Settings to repeat the flow and get a fresh token.

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

### Upstox Authentication
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/callback` | Public | OAuth2 redirect handler — Upstox calls this automatically after login |
| `GET` | `/api/v1/upstox/auth/url` | Bearer JWT | Returns the Upstox OAuth2 login URL |
| `POST` | `/api/v1/upstox/auth/callback` | Bearer JWT | Manual code exchange (fallback) |
| `GET` | `/api/v1/upstox/auth/status` | Bearer JWT | Whether an access token is currently configured |

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

### Market Data
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/market/{symbol}` | Live price for a single instrument (eToro API) |
| `GET` | `/api/v1/market/bulk?symbols=A,B,C` | Batch live prices for multiple instruments |

### AI Signals
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/{broker}/ai/recommendation` | BUY / SELL / HOLD signal with composite score |
| `GET` | `/api/v1/{broker}/ai/backtest/{symbol}` | 20-scenario score sweep (backtest analysis) |

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

## AI Signals

The AI signal engine computes a deterministic **BUY / SELL / HOLD** recommendation for any instrument using a four-factor composite score.

### Scoring model

```
Score = 0.35 × Trend  +  0.25 × Momentum  +  0.20 × Valuation  +  0.20 × Risk
```

| Factor | Source | What it measures |
|---|---|---|
| **Trend** | Unrealised return % (held) or live 24h change % (not held) | Price direction |
| **Momentum** | Return vs portfolio average | Relative outperformance |
| **Valuation** | Portfolio weight % | Concentration risk |
| **Risk** | Return % magnitude | Downside exposure |

Signal thresholds (moderate profile): **BUY ≥ 65 · SELL ≤ 35 · HOLD otherwise**

### Portfolio vs non-portfolio instruments

When the requested symbol **is in your portfolio**, the scorer uses the actual unrealised return and portfolio weight for full context-aware analysis.

When the symbol **is not in your portfolio**, the scorer previously defaulted to `return_pct = 0.0` for every non-held instrument — causing all of them to collapse to the same identical score (43.5 at a typical portfolio average). This is now fixed:

- The recommendation endpoint fetches the instrument's **live 24h price change** from the eToro market data API.
- That `changePercent` is passed into the scorer as a **market trend proxy** for `return_pct`.
- Each non-held instrument now receives a **distinct score** driven by its current market movement.
- The response includes `isPortfolioInstrument: bool` so the frontend can surface a clear notice:
  > ⚠ Not in your portfolio — score uses live market trend as proxy.

### Recommendation response fields

```json
{
  "symbol": "CSCO",
  "action": "HOLD",
  "score": 51.4,
  "confidence": 58,
  "features": { "trend": 52.5, "momentum": 41.0, "valuation": 60.0, "risk": 71.5 },
  "featureWeights": { "trend": 0.35, "momentum": 0.25, "valuation": 0.20, "risk": 0.20 },
  "riskFlags": [],
  "reasonBullets": ["..."],
  "invalidationConditions": ["..."],
  "narrative": "CSCO is tracking a modest positive market trend of +1.0% ...",
  "isPortfolioInstrument": false,
  "holdingSnapshot": null,
  "riskProfile": "moderate",
  "dataTimestamp": "2026-05-15T10:00:00+00:00",
  "isStale": false
}
```

### Backtest / scenario analysis

`GET /api/v1/{broker}/ai/backtest/{symbol}` sweeps 20 return scenarios from −25 % to +30 % and returns:
- Per-scenario score and action label
- Hit-rate % (how many scenarios produce the same action as current)
- Flip-point info — the return level at which the signal changes
- Signal zones: SELL / HOLD / BUY bands with their score ranges

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
