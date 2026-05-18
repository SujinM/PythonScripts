"""Returns & P&L calculations."""

from dataclasses import dataclass


@dataclass
class ReturnsResult:
    label: str
    value: float
    unit: str
    description: str = ""

    def __str__(self) -> str:
        sign = "+" if self.value >= 0 else ""
        return f"{self.label}: {sign}{self.value:,.4f} {self.unit}"


class ReturnsCalculator:
    """Profit, Loss, and return calculations."""

    @staticmethod
    def profit_loss(buy_price: float, sell_price: float, quantity: float) -> dict:
        """Total P&L for a trade."""
        invested = buy_price * quantity
        current = sell_price * quantity
        pnl = current - invested
        pct = (pnl / invested) * 100 if invested else 0
        return {
            "Invested":      round(invested, 2),
            "Current Value": round(current, 2),
            "P&L":           round(pnl, 2),
            "P&L %":         round(pct, 4),
        }

    @staticmethod
    def cagr(initial_value: float, final_value: float, years: float) -> ReturnsResult:
        """Compound Annual Growth Rate."""
        if initial_value <= 0 or years <= 0:
            raise ValueError("Initial value and years must be positive.")
        rate = ((final_value / initial_value) ** (1 / years) - 1) * 100
        return ReturnsResult(
            label="CAGR",
            value=round(rate, 4),
            unit="%",
            description=f"{initial_value} → {final_value} over {years}y",
        )

    @staticmethod
    def roi(cost: float, gain: float) -> ReturnsResult:
        """Return on Investment."""
        if cost == 0:
            raise ValueError("Cost cannot be zero.")
        roi_val = ((gain - cost) / cost) * 100
        return ReturnsResult(label="ROI", value=round(roi_val, 4), unit="%")

    @staticmethod
    def breakeven_price(buy_price: float, brokerage_pct: float) -> ReturnsResult:
        """Breakeven price after accounting for brokerage fees."""
        be = buy_price * (1 + brokerage_pct / 100)
        return ReturnsResult(
            label="Breakeven Price",
            value=round(be, 4),
            unit="",
            description=f"Buy: {buy_price}, Fee: {brokerage_pct}%",
        )

    @staticmethod
    def dividend_yield(annual_dividend: float, stock_price: float) -> ReturnsResult:
        """Dividend yield percentage."""
        if stock_price == 0:
            raise ValueError("Stock price cannot be zero.")
        dy = (annual_dividend / stock_price) * 100
        return ReturnsResult(
            label="Dividend Yield",
            value=round(dy, 4),
            unit="%",
            description=f"Dividend: {annual_dividend}, Price: {stock_price}",
        )

    @staticmethod
    def compound_interest(
        principal: float, rate_pct: float, years: float, n: int = 1
    ) -> dict:
        """Compound interest (n = compounding frequency per year)."""
        amount = principal * (1 + rate_pct / (100 * n)) ** (n * years)
        interest = amount - principal
        return {
            "Principal":  round(principal, 2),
            "Amount":     round(amount, 2),
            "Interest":   round(interest, 2),
            "Rate":       f"{rate_pct}% / {years}y (n={n})",
        }
