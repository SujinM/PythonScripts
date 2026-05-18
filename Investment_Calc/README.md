# InvestCalc — Stock Market Calculator

A pure-Python, zero-dependency interactive calculator for common stock market computations.

## Features

| Category | Calculations |
|---|---|
| **Price** | Price difference, % up/down, target price, stop-loss, take-profit, pivot points, SMA |
| **Returns & P&L** | Trade P&L, CAGR, ROI, breakeven price, dividend yield, compound interest |
| **Risk** | Position sizing by risk %, risk/reward ratio, Sharpe ratio, volatility, max drawdown |
| **Position** | Average buy price, portfolio allocation %, lot size, unrealised P&L |
| **Options** | Intrinsic value, Black-Scholes price + Delta/Gamma/Theta |

## Quick Start

### macOS / Linux
```bash
chmod +x run.sh
./run.sh
```

### Windows
Double-click **`run.bat`**

The launcher will automatically:
1. Detect Python 3.11+
2. Create a `.venv` virtual environment
3. Install the package in editable mode
4. Launch the interactive CLI

## Manual Usage

```bash
# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate.bat       # Windows

# Install
pip install -e .

# Run
python -m investcalc
# or
investcalc
```

## Project Structure

```
Investmet_Calc/
├── run.sh                    ← macOS/Linux launcher
├── run.bat                   ← Windows launcher
├── pyproject.toml            ← Package config (editable install)
├── requirements.txt          ← Runtime deps (stdlib only by default)
├── requirements-dev.txt      ← Dev/test deps
├── src/
│   └── investcalc/
│       ├── __init__.py
│       ├── __main__.py       ← python -m investcalc entry point
│       ├── cli.py            ← Interactive menu loop
│       ├── calculations/
│       │   ├── price.py      ← Price movements
│       │   ├── returns.py    ← P&L, CAGR, ROI, dividends
│       │   ├── risk.py       ← Position sizing, Sharpe, drawdown
│       │   ├── position.py   ← Avg buy, allocation, lot size
│       │   └── options.py    ← Intrinsic value, Black-Scholes
│       └── utils/
│           ├── display.py    ← Terminal colours & formatting
│           └── validators.py ← Safe numeric input helpers
└── tests/
    └── test_calculations.py  ← Pytest unit tests
```

## Extending the Calculator

Adding a new calculation module is straightforward:

1. Create `src/investcalc/calculations/mymodule.py` with a class `MyCalculator`.
2. Import and register it in `src/investcalc/calculations/__init__.py`.
3. Add a menu entry in `cli.py` (add to `MAIN_MENU` / `SUB_MENUS`).
4. Write tests in `tests/test_calculations.py`.

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

## Optional Extras

Uncomment lines in `requirements.txt` to enable:

| Extra | Package | Purpose |
|---|---|---|
| Rich UI | `rich` | Prettier terminal output |
| Live data | `yfinance` | Fetch live prices from Yahoo Finance |
| Data analysis | `pandas`, `numpy` | Bulk historical analysis |
