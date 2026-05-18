# InvestCalc — Stock Market Calculator

A professional stock market calculator available as both an **interactive Python CLI** and a **Vue 3 web dashboard** (dark theme). Zero Python runtime dependencies — pure stdlib.

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![Vue](https://img.shields.io/badge/Vue-3.5-green) ![TypeScript](https://img.shields.io/badge/TypeScript-5.4-blue) ![Tailwind](https://img.shields.io/badge/Tailwind-3.4-cyan)

---

## Calculations

| Category | What it computes |
|---|---|
| **Price** | Price difference, % up/down, target price, stop-loss, take-profit, pivot points (PP/R1–R3/S1–S3), SMA |
| **Returns & P&L** | Trade P&L, CAGR, ROI, breakeven price, dividend yield, compound interest |
| **Risk** | Position sizing by risk %, risk/reward ratio, Sharpe ratio, historical volatility, max drawdown |
| **Position** | Average buy price, portfolio allocation %, lot size calculator, unrealised P&L |
| **Options** | Intrinsic value, Black-Scholes price + Delta / Gamma / Theta |

---

## Web Dashboard (Vue 3)

Bloomberg-style dark UI with live calculation history.

### macOS / Linux
```bash
chmod +x run-web.sh
./run-web.sh
```

### Windows
Double-click **`run-web.bat`**

Opens at **http://localhost:5174**. The launcher auto-installs npm dependencies on first run.

### Manual start
```bash
cd web
npm install
npm run dev       # dev server → http://localhost:5174
npm run build     # production build → web/dist/
```

### Prerequisites
- Node.js 20+ (install via [nvm](https://github.com/nvm-sh/nvm): `nvm install 20`)

---

## Python CLI

Interactive terminal calculator — no browser required.

### macOS / Linux
```bash
chmod +x run.sh
./run.sh
```

### Windows
Double-click **`run.bat`**

Both launchers automatically detect Python 3.11+, create a `.venv`, and launch the CLI.

### Manual start
```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
. .venv\Scripts\Activate.ps1     # Windows PowerShell
.venv\Scripts\activate.bat       # Windows Command Prompt (cmd)

pip install -e .
python -m investcalc
```

If PowerShell blocks activation, run this once per terminal session, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

---

## Project Structure

```
Investment_Calc/
├── run.sh / run.bat           ← Python CLI launchers
├── run-web.sh / run-web.bat   ← Web dashboard launchers
├── pyproject.toml             ← Python package config
├── requirements.txt           ← Runtime deps (stdlib only)
├── requirements-dev.txt       ← Dev/test deps (pytest)
│
├── src/investcalc/            ← Python CLI package
│   ├── __main__.py            ← python -m investcalc entry point
│   ├── cli.py                 ← Interactive menu loop
│   ├── calculations/
│   │   ├── price.py           ← Price movements
│   │   ├── returns.py         ← P&L, CAGR, ROI, dividends
│   │   ├── risk.py            ← Position sizing, Sharpe, drawdown
│   │   ├── position.py        ← Avg buy, allocation, lot size
│   │   └── options.py         ← Intrinsic value, Black-Scholes
│   └── utils/
│       ├── display.py         ← Terminal colours & formatting
│       └── validators.py      ← Safe numeric input helpers
│
├── web/                       ← Vue 3 web dashboard
│   ├── src/
│   │   ├── utils/calculations.ts  ← All calculations in TypeScript
│   │   ├── stores/historyStore.ts ← Persisted calculation history
│   │   ├── pages/
│   │   │   ├── Dashboard.vue
│   │   │   ├── PriceCalc.vue
│   │   │   ├── ReturnsCalc.vue
│   │   │   ├── RiskCalc.vue
│   │   │   ├── PositionCalc.vue
│   │   │   ├── OptionsCalc.vue
│   │   │   └── History.vue
│   │   └── components/layout/ ← Sidebar, Navbar
│   └── package.json
│
└── tests/
    └── test_calculations.py   ← 19 pytest unit tests
```

---

## Extending the Calculator

### Add a new Python calculation
1. Create `src/investcalc/calculations/mymodule.py` with a class `MyCalculator`.
2. Register it in `src/investcalc/calculations/__init__.py`.
3. Add a menu entry in `cli.py`.
4. Add tests in `tests/test_calculations.py`.

### Add a new web page
1. Add the calculation function to `web/src/utils/calculations.ts`.
2. Create `web/src/pages/MyCalc.vue`.
3. Register the route in `web/src/router/index.ts`.
4. Add a nav entry in `web/src/components/layout/Sidebar.vue`.

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

---

## Optional Python Extras

Uncomment lines in `requirements.txt` to enable:

| Extra | Package | Purpose |
|---|---|---|
| Rich UI | `rich` | Prettier terminal output |
| Live data | `yfinance` | Fetch live prices from Yahoo Finance |
| Data analysis | `pandas`, `numpy` | Bulk historical analysis |
