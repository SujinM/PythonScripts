"""
InvestCalc — Interactive Stock Market Calculator CLI
"""

import sys
from .calculations.price import PriceCalculator
from .calculations.returns import ReturnsCalculator
from .calculations.risk import RiskCalculator
from .calculations.position import PositionCalculator
from .calculations.options import OptionsCalculator
from .utils.display import print_header, print_result, print_dict, print_menu
from .utils.validators import get_float, get_int, get_choice


# ── Menu tree ──────────────────────────────────────────────────────────────────

MAIN_MENU = {
    "1": "Price Calculations",
    "2": "Returns & P&L",
    "3": "Risk Management",
    "4": "Position & Portfolio",
    "5": "Options",
    "0": "Exit",
}

PRICE_MENU = {
    "1": "Price Difference",
    "2": "Percentage Change (Up / Down)",
    "3": "Target Price from %",
    "4": "Stop Loss Price",
    "5": "Take Profit Price",
    "6": "Pivot Points",
    "7": "Simple Moving Average",
    "0": "Back",
}

RETURNS_MENU = {
    "1": "Profit / Loss (Trade)",
    "2": "CAGR",
    "3": "ROI",
    "4": "Breakeven Price",
    "5": "Dividend Yield",
    "6": "Compound Interest",
    "0": "Back",
}

RISK_MENU = {
    "1": "Position Size by Risk %",
    "2": "Risk / Reward Ratio",
    "3": "Sharpe Ratio",
    "4": "Historical Volatility",
    "5": "Max Drawdown",
    "0": "Back",
}

POSITION_MENU = {
    "1": "Average Buy Price",
    "2": "Portfolio Allocation %",
    "3": "Lot Size Calculator",
    "4": "Unrealised P&L",
    "0": "Back",
}

OPTIONS_MENU = {
    "1": "Intrinsic Value",
    "2": "Black-Scholes Price + Greeks",
    "0": "Back",
}


# ── Sub-menu handlers ──────────────────────────────────────────────────────────

def handle_price(choice: str) -> None:
    pc = PriceCalculator()
    if choice == "1":
        old = get_float("Old Price")
        new = get_float("New Price")
        print_result(pc.price_difference(old, new))
    elif choice == "2":
        old = get_float("Old Price")
        new = get_float("New Price")
        print_result(pc.percentage_change(old, new))
    elif choice == "3":
        cur = get_float("Current Price")
        pct = get_float("Target % (e.g. 10 for +10%)")
        print_result(pc.target_price_from_pct(cur, pct))
    elif choice == "4":
        buy = get_float("Buy Price")
        sl  = get_float("Stop Loss % (e.g. 5 for -5%)")
        print_result(pc.stop_loss_price(buy, sl))
    elif choice == "5":
        buy = get_float("Buy Price")
        tp  = get_float("Take Profit % (e.g. 10 for +10%)")
        print_result(pc.take_profit_price(buy, tp))
    elif choice == "6":
        h = get_float("High")
        l = get_float("Low")
        c = get_float("Close")
        print_dict("Pivot Points", pc.pivot_points(h, l, c))
    elif choice == "7":
        raw = input("Enter prices separated by commas: ").strip()
        prices = [float(x.strip()) for x in raw.split(",")]
        period = get_int("Period (0 = all)")
        sma = pc.moving_average(prices, period if period > 0 else None)
        print(f"\n  Moving Average: {sma}")


def handle_returns(choice: str) -> None:
    rc = ReturnsCalculator()
    if choice == "1":
        buy  = get_float("Buy Price")
        sell = get_float("Sell Price")
        qty  = get_float("Quantity")
        print_dict("Trade P&L", rc.profit_loss(buy, sell, qty))
    elif choice == "2":
        iv = get_float("Initial Value")
        fv = get_float("Final Value")
        yr = get_float("Years")
        print_result(rc.cagr(iv, fv, yr))
    elif choice == "3":
        cost = get_float("Cost / Invested")
        gain = get_float("Final Value")
        print_result(rc.roi(cost, gain))
    elif choice == "4":
        buy = get_float("Buy Price")
        fee = get_float("Brokerage Fee %")
        print_result(rc.breakeven_price(buy, fee))
    elif choice == "5":
        div = get_float("Annual Dividend per Share")
        prc = get_float("Stock Price")
        print_result(rc.dividend_yield(div, prc))
    elif choice == "6":
        p  = get_float("Principal")
        r  = get_float("Annual Rate %")
        yr = get_float("Years")
        n  = get_int("Compounding per year (1=annual, 12=monthly, 365=daily)")
        print_dict("Compound Interest", rc.compound_interest(p, r, yr, n))


def handle_risk(choice: str) -> None:
    ric = RiskCalculator()
    if choice == "1":
        acc = get_float("Account Size")
        rp  = get_float("Risk %")
        buy = get_float("Buy Price")
        sl  = get_float("Stop Loss Price")
        print_dict("Position Size", ric.position_size_by_risk(acc, rp, buy, sl))
    elif choice == "2":
        buy = get_float("Buy Price")
        sl  = get_float("Stop Loss Price")
        tp  = get_float("Target Price")
        print_result(ric.risk_reward_ratio(buy, sl, tp))
    elif choice == "3":
        avg = get_float("Average Return %")
        rfr = get_float("Risk-Free Rate %")
        std = get_float("Standard Deviation %")
        print_result(ric.sharpe_ratio(avg, rfr, std))
    elif choice == "4":
        raw = input("Enter prices separated by commas: ").strip()
        prices = [float(x.strip()) for x in raw.split(",")]
        print_result(ric.volatility(prices))
    elif choice == "5":
        raw = input("Enter prices separated by commas: ").strip()
        prices = [float(x.strip()) for x in raw.split(",")]
        print_result(ric.max_drawdown(prices))


def handle_position(choice: str) -> None:
    psc = PositionCalculator()
    if choice == "1":
        n = get_int("Number of buy entries")
        purchases = []
        for i in range(n):
            p = get_float(f"  Entry {i+1} Price")
            q = get_float(f"  Entry {i+1} Quantity")
            purchases.append((p, q))
        print_dict("Average Buy Price", psc.average_buy_price(purchases))
    elif choice == "2":
        n = get_int("Number of holdings")
        holdings: dict[str, float] = {}
        for _ in range(n):
            sym = input("  Symbol: ").strip().upper()
            val = get_float(f"  Value of {sym}")
            holdings[sym] = val
        print_dict("Portfolio Allocation", psc.portfolio_allocation(holdings))
    elif choice == "3":
        cap = get_float("Total Capital")
        prc = get_float("Stock Price")
        pct = get_float("Allocation %")
        print_dict("Lot Size", psc.lot_size_calculator(cap, prc, pct))
    elif choice == "4":
        avg = get_float("Average Buy Price")
        cur = get_float("Current Price")
        qty = get_float("Quantity")
        print_dict("Unrealised P&L", psc.unrealised_pnl(avg, cur, qty))


def handle_options(choice: str) -> None:
    oc = OptionsCalculator()
    if choice == "1":
        ot  = get_choice("Option Type", ["call", "put"])
        sp  = get_float("Spot Price")
        sk  = get_float("Strike Price")
        print_dict("Intrinsic Value", oc.intrinsic_value(ot, sp, sk))
    elif choice == "2":
        ot    = get_choice("Option Type", ["call", "put"])
        S     = get_float("Spot Price (S)")
        K     = get_float("Strike Price (K)")
        T     = get_float("Time to Expiry in Years (e.g. 0.25 = 3 months)")
        r     = get_float("Risk-Free Rate % (e.g. 6.5)")
        sigma = get_float("Implied Volatility % (e.g. 20)")
        print_dict(
            "Black-Scholes",
            oc.black_scholes(ot, S, K, T, r / 100, sigma / 100),
        )


# ── Main loop ──────────────────────────────────────────────────────────────────

SUB_MENUS = {
    "1": (PRICE_MENU,    handle_price,    "Price Calculations"),
    "2": (RETURNS_MENU,  handle_returns,  "Returns & P&L"),
    "3": (RISK_MENU,     handle_risk,     "Risk Management"),
    "4": (POSITION_MENU, handle_position, "Position & Portfolio"),
    "5": (OPTIONS_MENU,  handle_options,  "Options"),
}


def run() -> None:
    print_header("InvestCalc — Stock Market Calculator")
    while True:
        print_menu("Main Menu", MAIN_MENU)
        choice = input("  Select: ").strip()
        if choice == "0":
            print("\n  Goodbye!\n")
            sys.exit(0)
        if choice not in SUB_MENUS:
            print("  Invalid choice.\n")
            continue

        menu, handler, title = SUB_MENUS[choice]
        while True:
            print_menu(title, menu)
            sub = input("  Select: ").strip()
            if sub == "0":
                break
            if sub not in menu:
                print("  Invalid choice.\n")
                continue
            try:
                handler(sub)
            except (ValueError, ZeroDivisionError) as exc:
                print(f"\n  [Error] {exc}\n")
            except KeyboardInterrupt:
                print()
                break
