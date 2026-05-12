# Investment Portfolio Dashboard

A production-ready Vue 3 portfolio dashboard that connects to the **BackendFastAPI** service to display real-time holdings, positions, trades, and analysis from **eToro** and **Upstox** brokers.

![Stack](https://img.shields.io/badge/Vue-3.4-green) ![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue) ![Tailwind](https://img.shields.io/badge/Tailwind-3.3-cyan) ![ECharts](https://img.shields.io/badge/ECharts-5.4-red)

## Features

- **Multi-broker support** — eToro and Upstox portfolio data from a single dashboard
- **Live portfolio KPIs** — Total invested, current value, unrealised P&L, and overall return %
- **Holdings, Positions & Trades** — Tabbed data tables with search and broker selector
- **Portfolio analysis** — Top gainers/losers bar charts, per-holding P&L progress bars
- **Alerts** — Severity-coded alert table sourced from `/analysis/alerts`
- **Live tick streaming** — WebSocket connection per broker with auto-reconnect
- **Cache invalidation** — Per-broker cache reset from the Brokers management page
- **Bloomberg-style dark UI** with optional light theme
- **Responsive** — optimised for desktop, tablet and mobile

## Architecture

```
┌─────────────────────┐        HTTP / WebSocket        ┌─────────────────────┐
│   TradeView (Vue 3) │ ──────────────────────────────► │  BackendFastAPI     │
│   localhost:5173    │ ◄────────────────────────────── │  localhost:8000     │
└─────────────────────┘                                 └──────────┬──────────┘
                                                                   │
                                                         ┌─────────┴─────────┐
                                                         │  eToro  │  Upstox │
                                                         └─────────┴─────────┘
```

## Tech Stack

| Layer        | Library                              |
|:-------------|:-------------------------------------|
| Framework    | Vue 3 (Composition API)              |
| Bundler      | Vite 4                               |
| Language     | TypeScript 5                         |
| Styling      | Tailwind CSS 3                       |
| Charts       | ECharts 5 + vue-echarts 6            |
| State        | Pinia + pinia-plugin-persistedstate  |
| Router       | Vue Router 4                         |
| HTTP         | Axios                                |
| WebSocket    | Native browser WebSocket (composable)|
| Utilities    | @vueuse/core, date-fns, lodash-es    |

## Getting Started

### Prerequisites
- Node.js 20+
- npm 9+
- BackendFastAPI running at `http://localhost:8000`

### Quickstart (Windows)

Double-click **`start-app.bat`** in this folder. It will:
1. Start the **BackendFastAPI** server in a new window
2. Install npm dependencies (if needed)
3. Start the **Vite dev server** and open `http://localhost:5173`

### Manual start

**1 — Start the backend** (from `Investment_App/BackendFastAPI/`):
```bash
start-dev.bat
```

**2 — Start the frontend** (from `Investment_App/TradeView/`):
```bash
npm install
npm run dev
```

Open http://localhost:5173 — sign in with any email/password (mock auth mode).

### Build for production

```bash
npm run build
npm run preview
```

### Docker

```bash
docker compose up --build
```

Dashboard available at http://localhost:3000.

## Pages

| Route          | Page              | Description                                              |
|:---------------|:------------------|:---------------------------------------------------------|
| `/`            | Dashboard         | Portfolio KPIs, exchange breakdown chart, gainers/losers |
| `/holdings`    | Holdings          | Holdings / Positions / Trades tabs with broker selector  |
| `/statistics`  | Analysis          | Portfolio analysis, alerts, per-holding P&L table        |
| `/sync`        | Brokers           | Broker cards, cache invalidation, live tick toggle       |
| `/settings`    | Settings          | Theme, display preferences                               |

## API Endpoints (BackendFastAPI)

| Method | Endpoint                              | Description              |
|:-------|:--------------------------------------|:--------------------------|
| GET    | `/api/v1/brokers`                     | List available brokers   |
| GET    | `/api/v1/{broker}/holdings`           | Portfolio holdings        |
| GET    | `/api/v1/{broker}/positions`          | Open positions            |
| GET    | `/api/v1/{broker}/trades`             | Trade history             |
| GET    | `/api/v1/{broker}/summary`            | Portfolio summary KPIs    |
| GET    | `/api/v1/{broker}/analysis`           | Analysis + alerts         |
| GET    | `/api/v1/{broker}/analysis/alerts`    | Alerts only               |
| POST   | `/api/v1/{broker}/cache/invalidate`   | Invalidate broker cache   |
| WS     | `/api/v1/{broker}/ws/live`            | Live tick stream          |

## Project Structure

```
src/
├── api/
│   ├── index.ts        # Axios base instance (http://localhost:8000)
│   └── portfolio.ts    # Portfolio API client (all broker endpoints)
├── composables/
│   └── useLiveTick.ts  # WebSocket composable with auto-reconnect
├── components/         # Reusable Vue components
│   ├── charts/         # ECharts wrappers (Bar, Pie, Line, Candlestick)
│   ├── common/         # UI primitives (Badge, Modal, Spinner...)
│   ├── dashboard/      # StatisticCard, ChartCard
│   └── layout/         # Sidebar & Navbar
├── layouts/            # AuthLayout, DefaultLayout
├── pages/
│   ├── Dashboard.vue       # Portfolio overview
│   ├── Holdings.vue        # Holdings / Positions / Trades
│   ├── Statistics.vue      # Portfolio analysis & alerts
│   └── SyncManagement.vue  # Broker management
├── router/             # Vue Router config
├── stores/
│   └── portfolioStore.ts   # Central Pinia store (all portfolio state)
├── styles/             # Global CSS
├── types/
│   └── portfolio.ts    # TypeScript interfaces mirroring FastAPI models
└── utils/              # Constants, formatters, mock data
```

## Environment Variables

| Variable            | Default                        | Description                          |
|:--------------------|:-------------------------------|:-------------------------------------|
| `VITE_API_URL`      | `http://localhost:8000`        | FastAPI backend base URL             |
| `VITE_WS_URL`       | `ws://localhost:8000/api/v1`   | WebSocket base URL                   |
| `VITE_MOCK_DATA`    | `true`                         | `true` = bypass login with mock auth |
| `VITE_API_TIMEOUT`  | `10000`                        | Axios request timeout (ms)           |

> **Note:** `VITE_MOCK_DATA=true` only bypasses the login screen. All portfolio data is always fetched from the real backend.

## Scripts

| Command              | Description                  |
|:---------------------|:-----------------------------|
| `npm run dev`        | Start dev server (HMR)       |
| `npm run build`      | Production build             |
| `npm run preview`    | Preview production build     |
| `npm run lint`       | Run ESLint                   |
| `npm run format`     | Format with Prettier         |
| `npm run type-check` | Run TypeScript type checker  |
| `npm run type-check` | TypeScript type check    |
