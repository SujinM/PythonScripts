# Sujin's Investment App

A full-stack, multi-broker **portfolio management system** — Python FastAPI backend, two broker integrations, a CLI tool, and a .NET 8 interactive console client with a live auto-refresh dashboard.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SujinsInvestment.exe (.NET 8)                   │
│            Interactive menu  +  Live Dashboard (auto-refresh)       │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTP (localhost:8000)
┌───────────────────────────▼─────────────────────────────────────────┐
│                  BackendFastAPI  (Python FastAPI)                    │
│  Swagger UI · REST API · Typer CLI · In-memory TTL cache            │
└──────────┬──────────────────────────────────────┬───────────────────┘
           │ pip install -e                        │ pip install -e
┌──────────▼──────────┐                ┌──────────▼──────────┐
│   upstox_app        │                │   etoro_app         │
│  OAuth2 + Analytics │                │  Static API keys    │
│  Token (1 year)     │                │  (x-api-key +       │
│  NSE / BSE          │                │   x-user-key)       │
└──────────┬──────────┘                └──────────┬──────────┘
           │                                      │
┌──────────▼──────────┐                ┌──────────▼──────────┐
│  Upstox Public API  │                │  eToro Public API   │
│  api.upstox.com     │                │  public-api.etoro.com│
└─────────────────────┘                └─────────────────────┘
```

---

## Project Structure

```
Investment_App/
├── BackendFastAPI/        Python FastAPI server + Typer CLI
├── upstox/                Upstox standalone CLI + upstox_app library
├── etoro/                 eToro standalone CLI + etoro_app library
├── ClientConsolApp/       .NET 8 C# console client (SujinsInvestment.exe)
└── TradeView/             Vue 3 + TypeScript web dashboard
```

---

## Quick Start (full stack)

### 1. Python environment (shared venv)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r Investment_App/BackendFastAPI/requirements.txt
pip install -e Investment_App/upstox      # installs upstox_app
pip install -e Investment_App/etoro       # installs etoro_app
```

### 2. Credentials

Copy the `.env.example` files and fill in your keys:

```powershell
copy Investment_App\BackendFastAPI\.env.example Investment_App\BackendFastAPI\.env
copy Investment_App\upstox\.env.example         Investment_App\upstox\.env
copy Investment_App\etoro\.env.example          Investment_App\etoro\.env
```

> **Security rule:** `.env` files are in `.gitignore` and must **never** be committed.

### 3. Start the FastAPI server

```bat
cd Investment_App\BackendFastAPI
start-dev.bat
```

Opens a separate PowerShell window and starts uvicorn with hot-reload on `http://127.0.0.1:8000`.

### 4. Launch the console client

```powershell
cd Investment_App\ClientConsolApp
dotnet run
```

Or run the pre-built EXE directly:

```
bin\publish\win-x64\SujinsInvestment.exe
```

---

## Components

### BackendFastAPI

Python FastAPI server that normalises Upstox + eToro data into a single portfolio model.

| | |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI + Pydantic v2 |
| CLI | Typer |
| Cache | In-memory TTL (Redis-swap-ready) |
| Swagger UI | http://127.0.0.1:8000/docs |

**REST Endpoints:**

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/v1/brokers` | List registered brokers |
| GET | `/api/v1/{broker}/holdings` | Long-term holdings |
| GET | `/api/v1/{broker}/positions` | Open positions |
| GET | `/api/v1/{broker}/trades` | Today's trades |
| GET | `/api/v1/{broker}/summary` | Portfolio summary + P&L |
| GET | `/api/v1/{broker}/analysis` | Full analysis: top movers, alerts, allocation |
| GET | `/api/v1/{broker}/analysis/alerts` | Active threshold alerts |
| POST | `/api/v1/{broker}/cache/invalidate` | Force fresh broker fetch |

`{broker}` = `upstox` or `etoro`

**CLI (no server needed):**

```bash
cd Investment_App/BackendFastAPI

python -m app.cli summary upstox
python -m app.cli holdings etoro
python -m app.cli positions upstox
python -m app.cli trades etoro
python -m app.cli analysis upstox
python -m app.cli alerts etoro
python -m app.cli invalidate upstox
```

**Environment variables (BackendFastAPI/.env):**

| Variable | Description |
|---|---|
| `UPSTOX_API_KEY` | Upstox API key |
| `UPSTOX_API_SECRET` | Upstox API secret |
| `UPSTOX_ACCESS_TOKEN` | OAuth2 access token (daily, from `auth` command) |
| `UPSTOX_REDIRECT_URI` | OAuth2 redirect URI (must match portal exactly) |
| `ETORO_API_KEY` | eToro Public API Key (`x-api-key` header) |
| `ETORO_USER_KEY` | eToro User Key (`x-user-key` header) |
| `CACHE_TTL_SECONDS` | Cache lifetime in seconds (default `300`) |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

---

### upstox — Upstox CLI + Library

Standalone Python CLI for Upstox with an installable `upstox_app` library used by BackendFastAPI.

| | |
|---|---|
| Language | Python 3.11+ |
| Auth | OAuth2 (portfolio) + Analytics Token (market data, 1-year read-only) |
| Tests | 89 (all mocked, no network) |

**Getting credentials:**

1. [Upstox Developer Apps](https://account.upstox.com/developer/apps) → copy **API Key** and **API Secret**
2. Note the exact **Redirect URL** registered (must match `UPSTOX_REDIRECT_URI` character-for-character)
3. On the same page → **Analytics Token** → generate once, valid 1 year

**Daily access token (two options):**

```bash
cd Investment_App/upstox

# Option A — OAuth2 browser flow
python -m app auth

# Option B — Direct token request (no browser)
python -m app request-token
```

Both print the token → paste it into `.env` as `UPSTOX_ACCESS_TOKEN`.

**Portfolio commands (require `UPSTOX_ACCESS_TOKEN`):**

```bash
python -m app summary
python -m app holdings
python -m app holdings --top 10
python -m app positions
python -m app trades
python -m app alerts
python -m app alerts --gain 30 --loss -15
```

**Analytics commands (require `UPSTOX_ANALYTICS_TOKEN`, no OAuth2 needed):**

```bash
python -m app analytics ltp "NSE_EQ|INE009A01021"
python -m app analytics quotes "NSE_EQ|INE009A01021"
python -m app analytics ohlc "NSE_EQ|INE009A01021" --interval I30
python -m app analytics candles "NSE_EQ|INE009A01021" --interval day --from 2026-01-01 --to 2026-05-05
python -m app analytics option-chain "NSE_INDEX|Nifty 50" --expiry 2026-05-29
python -m app analytics option-greeks "NSE_INDEX|Nifty 50" --expiry 2026-05-29
python -m app analytics search RELIANCE
python -m app analytics market-status
python -m app analytics brokerage "NSE_EQ|INE009A01021" --qty 10 --price 1650 --tx BUY
```

**upstox/.env template:**

```dotenv
UPSTOX_API_KEY=
UPSTOX_API_SECRET=
UPSTOX_REDIRECT_URI=https://127.0.0.1
UPSTOX_ACCESS_TOKEN=
UPSTOX_ANALYTICS_TOKEN=
```

---

### etoro — eToro CLI + Library

Standalone Python CLI for eToro with an installable `etoro_app` library used by BackendFastAPI.

| | |
|---|---|
| Language | Python 3.11+ |
| Auth | Two static API keys — no OAuth2, no token expiry |
| Requests | Every request sends `x-api-key` + `x-user-key` + auto `x-request-id` |

**Getting credentials:**

1. [etoro.com](https://www.etoro.com) → Settings → Trading → **API Key Management**
2. Copy **Public API Key** → `ETORO_API_KEY`
3. Copy **User Key** → `ETORO_USER_KEY`

**Commands:**

```bash
cd Investment_App/etoro

python -m app positions
python -m app history
python -m app history --limit 20
python -m app summary
python -m app alerts
python -m app alerts --gain 30 --loss -15
```

**Important — eToro rate limits:**

The positions endpoint enriches data with two additional batch calls (instrument metadata + live rates).
If these batch calls hit Cloudflare 429 errors, the service **automatically retries each ID individually**.
This fallback can take 40-70 seconds — this is normal behaviour.

**etoro/.env template:**

```dotenv
ETORO_API_KEY=
ETORO_USER_KEY=
# ETORO_BASE_URL=https://public-api.etoro.com
```

---

### ClientConsolApp — SujinsInvestment.exe

.NET 8 C# interactive console client connecting to the FastAPI backend.

| | |
|---|---|
| Language | C# (.NET 8) |
| Output | `SujinsInvestment.exe` (self-contained, no .NET install needed) |
| Size | ~36 MB |
| Requires | BackendFastAPI running on `http://localhost:8000` |

**Running:**

```powershell
cd Investment_App\ClientConsolApp
dotnet run                        # development
.\bin\publish\win-x64\SujinsInvestment.exe   # pre-built
```

**Menu options:**

| Key | Action |
|-----|--------|
| `1` | Portfolio Summary |
| `2` | Holdings |
| `3` | Positions |
| `4` | Today's Trades |
| `5` | Full Analysis |
| `6` | Active Alerts |
| `7` | List Brokers |
| `8` | Invalidate Cache |
| `9` | Switch Broker (upstox ↔ etoro) |
| `L` | **Live Dashboard** (auto-refresh) |
| `0` | Exit |

**Live Dashboard (option L):**

- Full-screen dark-theme view: portfolio summary, top movers, alerts, exchange allocation bar chart
- Prompts for refresh interval (minimum **3 seconds**, default **5 seconds**)
- On each refresh cycle: invalidates the backend cache first → forces a live broker API fetch
- Press `Q` or `Esc` to exit back to the menu

> **eToro note:** Set the live dashboard interval to **30+ seconds** for eToro — the enrichment fallback takes up to 70s. For Upstox, 5 seconds works well.

**appsettings.json:**

```json
{
  "ApiSettings": {
    "BaseUrl": "http://localhost:8000",
    "TimeoutSeconds": 120,
    "MaxRetries": 2,
    "RetryDelayMs": 1000
  },
  "DefaultBroker": "upstox"
}
```

**Building the production EXE:**

```bat
cd Investment_App\ClientConsolApp
build-release.bat              # EXE only
build-release.bat /installer   # EXE + Windows installer (requires Inno Setup 6)
```

Output: `bin\publish\win-x64\SujinsInvestment.exe`
Installer: `installer\Output\SujinsInvestment-Setup-1.0.0.exe`

EXE properties: Product = `Sujin's Investment` · Version = `1.0.0` · Company = `Sujin M`

---

### TradeView — Vue 3 Web Dashboard

Browser-based trading dashboard connecting to the FastAPI backend.

| | |
|---|---|
| Language | TypeScript |
| Framework | Vue 3 + Vite + Tailwind CSS |
| State | Pinia |
| Real-time | WebSocket (`/api/v1/etoro/ws/live`) |
| Requires | BackendFastAPI running on `http://localhost:8000` |

**Starting the dev server:**

```powershell
cd Investment_App\TradeView
npm install
npm run dev        # http://localhost:5173
```

**`TradeView/.env` (local dev):**

```dotenv
VITE_API_URL=http://localhost:8000
```

**Features:**

#### eToro Watchlists

Browse, search, and inspect all eToro watchlists from the web UI.

- **Watchlist cards** — shows type (Dynamic / Static), rank, item count, and first 5 instrument IDs
- **Detail modal** — click any watchlist to open a live instrument table:

| Column | Source |
|---|---|
| Symbol | eToro instrument catalogue (local DB) |
| Price | Live via WebSocket — flashes green/red on tick |
| 1-Day | Yahoo Finance daily close: today vs yesterday |
| 1-Month | Yahoo Finance daily close: today vs ~30 days ago |
| 1-Year | Yahoo Finance daily close: today vs ~365 days ago |

- Price color flashes only on the number, not the whole row
- Change columns auto-reconnect on WebSocket drop
- Falls back to Yahoo Finance `latest_close` when the eToro rates API is unavailable

**Historical data note:** The eToro Public API has no candle or historical price endpoints. All period changes (1-Day, 1-Month, 1-Year) are sourced from **Yahoo Finance** via `yfinance`. Symbol mapping:

| eToro type | Example | Yahoo Finance ticker |
|---|---|---|
| Crypto (type 10) | `ETH` | `ETH-USD` |
| Forex (type 1) | `EURUSD` | `EURUSD=X` |
| Stocks / ETFs / Indices | `AMD`, `SMH` | `AMD`, `SMH` (unchanged) |

---

## Important Notes

### Cache behaviour

The FastAPI backend caches all broker responses for `CACHE_TTL_SECONDS` (default **5 minutes**).

- The CLI and REST API share the same cache instance within a running server process
- **Live Dashboard** automatically calls `POST /cache/invalidate` before each refresh cycle to bypass the cache and fetch live data from the broker
- Call `POST /api/v1/{broker}/cache/invalidate` manually (or use menu option 8) to force a fresh fetch at any time

### eToro rate limits (Cloudflare 1015)

eToro's public API is protected by Cloudflare. Rapid repeated requests trigger HTTP 429 with error code `1015`.

Mitigations already in place:
- Sequential (not parallel) `/analysis` + `/summary` fetches in the live dashboard
- `TimeoutSeconds: 120` in the C# client (covers ~70s worst-case fallback)
- Minimum 3s live dashboard refresh interval

If you see persistent 429 errors, increase the dashboard interval or increase `CACHE_TTL_SECONDS` in the server `.env`.

### Upstox access token expiry

Upstox access tokens are valid for **one trading day** only. Each morning:

```bash
cd Investment_App/upstox
python -m app request-token     # prints new token
# paste into Investment_App/BackendFastAPI/.env → UPSTOX_ACCESS_TOKEN
# restart the FastAPI server
```

### Adding a new broker

1. Create `BackendFastAPI/app/brokers/newbroker.py` — subclass `IBrokerAdapter`
2. Implement `get_holdings()`, `get_positions()`, `get_trades()`
3. Call `registry.register(NewBrokerAdapter())` at the bottom
4. Add `import app.brokers.newbroker` in `app/main.py` and `app/cli.py`

No changes to routes, services, models, or the C# client are needed.

### Running tests

```bash
# BackendFastAPI — 50 tests
cd Investment_App/BackendFastAPI
pytest tests/ -v

# Upstox — 89 tests
cd Investment_App/upstox
pytest -v --tb=short

# eToro
cd Investment_App/etoro
pytest -v
```

All tests are fully mocked — no credentials or network access required.

---

## License

MIT
