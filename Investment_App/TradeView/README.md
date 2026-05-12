# eToro Instruments Dashboard

A production-ready Vue 3 dashboard for managing and visualising eToro financial instruments data from a FastAPI backend.

![Stack](https://img.shields.io/badge/Vue-3.4-green) ![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue) ![Tailwind](https://img.shields.io/badge/Tailwind-3.3-cyan) ![ECharts](https://img.shields.io/badge/ECharts-5.4-red)

## Features

- **Bloomberg-style dark UI** with optional light theme
- **57 mock instruments** across STOCKS, CRYPTO, FOREX, INDICES, COMMODITIES, ETFs
- **Candlestick charts** with OHLCV data and volume bars
- **Interactive data table** with client-side filtering, sorting, pagination and CSV export
- **Sync management** with live progress bar and real-time log stream
- **Watchlist** management persisted to localStorage
- **Fully offline** — all pages work without a backend via mock data mode
- **Responsive** — optimised for desktop, tablet and mobile

## Tech Stack

| Layer        | Library                         |
|:-------------|:--------------------------------|
| Framework    | Vue 3 (Composition API)         |
| Bundler      | Vite 5                          |
| Language     | TypeScript 5                    |
| Styling      | Tailwind CSS 3                  |
| Charts       | ECharts 5 + vue-echarts 6       |
| State        | Pinia + pinia-plugin-persistedstate |
| Router       | Vue Router 4                    |
| HTTP         | Axios                           |
| Utilities    | @vueuse/core, date-fns, lodash-es |

## Getting Started

### Prerequisites
- Node.js 20+
- npm 9+

### Development

```bash
cd Investment_App/TradeView
npm install
npm run dev
```

Open http://localhost:5173 — sign in with any email/password (mock mode).

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

## Project Structure

```
src/
├── api/          # Axios API clients
├── components/   # Reusable Vue components
│   ├── charts/   # ECharts wrappers
│   ├── common/   # UI primitives
│   ├── dashboard/# Dashboard-specific cards
│   └── layout/   # Sidebar & Navbar
├── composables/  # Vue composables
├── layouts/      # Page layouts
├── pages/        # Route-level views
├── router/       # Vue Router config
├── services/     # Storage service
├── stores/       # Pinia stores
├── styles/       # Global CSS
├── types/        # TypeScript interfaces
└── utils/        # Constants, formatters, mock data
```

## Environment Variables

| Variable          | Default                 | Description               |
|:------------------|:------------------------|:--------------------------|
| `VITE_API_URL`    | `http://localhost:8000` | FastAPI backend URL       |
| `VITE_MOCK_DATA`  | `true`                  | Use mock data (no backend)|
| `VITE_WS_URL`     | `ws://localhost:8000`   | WebSocket URL             |

## Scripts

| Command           | Description                 |
|:------------------|:----------------------------|
| `npm run dev`     | Start dev server (HMR)      |
| `npm run build`   | Production build            |
| `npm run preview` | Preview production build    |
| `npm run lint`    | Run ESLint                  |
| `npm run format`  | Format with Prettier        |
| `npm run type-check` | TypeScript type check    |
