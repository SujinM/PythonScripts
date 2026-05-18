"""Position & portfolio calculations."""

from dataclasses import dataclass


class PositionCalculator:
    """Portfolio position and allocation calculations."""

    @staticmethod
    def average_buy_price(purchases: list[tuple[float, float]]) -> dict:
        """
        Average cost of a position with multiple buy entries.
        purchases: list of (price, quantity) tuples
        """
        total_qty = sum(q for _, q in purchases)
        total_cost = sum(p * q for p, q in purchases)
        if total_qty == 0:
            raise ValueError("Total quantity cannot be zero.")
        avg = total_cost / total_qty
        return {
            "Average Buy Price": round(avg, 4),
            "Total Quantity":    round(total_qty, 4),
            "Total Cost":        round(total_cost, 2),
        }

    @staticmethod
    def portfolio_allocation(holdings: dict[str, float]) -> dict:
        """
        Percentage allocation of each holding.
        holdings: {symbol: value}
        """
        total = sum(holdings.values())
        if total == 0:
            raise ValueError("Total portfolio value cannot be zero.")
        return {sym: round(val / total * 100, 2) for sym, val in holdings.items()}

    @staticmethod
    def lot_size_calculator(
        capital: float, price: float, allocation_pct: float
    ) -> dict:
        """How many shares to buy given capital and allocation percentage."""
        alloc_amount = capital * allocation_pct / 100
        shares = int(alloc_amount // price)
        actual_cost = shares * price
        remaining = alloc_amount - actual_cost
        return {
            "Allocated Amount": round(alloc_amount, 2),
            "Shares":           shares,
            "Actual Cost":      round(actual_cost, 2),
            "Remaining Cash":   round(remaining, 2),
        }

    @staticmethod
    def unrealised_pnl(
        avg_buy_price: float, current_price: float, quantity: float
    ) -> dict:
        """Unrealised P&L for an open position."""
        invested = avg_buy_price * quantity
        current = current_price * quantity
        pnl = current - invested
        pct = (pnl / invested * 100) if invested else 0
        return {
            "Invested":      round(invested, 2),
            "Current Value": round(current, 2),
            "Unrealised P&L": round(pnl, 2),
            "P&L %":         round(pct, 4),
        }
