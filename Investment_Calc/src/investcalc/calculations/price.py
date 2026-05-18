"""Price-related calculations."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PriceResult:
    label: str
    value: float
    unit: str
    description: str = ""

    def __str__(self) -> str:
        return f"{self.label}: {self.value:,.4f} {self.unit}"


class PriceCalculator:
    """Calculations based on stock price movements."""

    @staticmethod
    def price_difference(old_price: float, new_price: float) -> PriceResult:
        """Absolute price difference between two prices."""
        diff = new_price - old_price
        return PriceResult(
            label="Price Difference",
            value=round(diff, 4),
            unit="",
            description=f"{old_price} → {new_price}",
        )

    @staticmethod
    def percentage_change(old_price: float, new_price: float) -> PriceResult:
        """Percentage change from old to new price."""
        if old_price == 0:
            raise ValueError("Old price cannot be zero.")
        pct = ((new_price - old_price) / old_price) * 100
        direction = "UP" if pct >= 0 else "DOWN"
        return PriceResult(
            label=f"Percentage {direction}",
            value=round(pct, 4),
            unit="%",
            description=f"{old_price} → {new_price}",
        )

    @staticmethod
    def target_price_from_pct(current_price: float, target_pct: float) -> PriceResult:
        """Calculate target price given a percentage move."""
        target = current_price * (1 + target_pct / 100)
        return PriceResult(
            label="Target Price",
            value=round(target, 4),
            unit="",
            description=f"{current_price} + {target_pct}%",
        )

    @staticmethod
    def stop_loss_price(buy_price: float, stop_loss_pct: float) -> PriceResult:
        """Calculate stop-loss price based on percentage below buy price."""
        sl = buy_price * (1 - abs(stop_loss_pct) / 100)
        return PriceResult(
            label="Stop Loss Price",
            value=round(sl, 4),
            unit="",
            description=f"Buy: {buy_price}, SL: -{abs(stop_loss_pct)}%",
        )

    @staticmethod
    def take_profit_price(buy_price: float, target_pct: float) -> PriceResult:
        """Calculate take-profit price based on percentage above buy price."""
        tp = buy_price * (1 + abs(target_pct) / 100)
        return PriceResult(
            label="Take Profit Price",
            value=round(tp, 4),
            unit="",
            description=f"Buy: {buy_price}, TP: +{abs(target_pct)}%",
        )

    @staticmethod
    def pivot_points(high: float, low: float, close: float) -> dict:
        """Classic floor pivot points (PP, R1, R2, R3, S1, S2, S3)."""
        pp = (high + low + close) / 3
        r1 = (2 * pp) - low
        r2 = pp + (high - low)
        r3 = high + 2 * (pp - low)
        s1 = (2 * pp) - high
        s2 = pp - (high - low)
        s3 = low - 2 * (high - pp)
        return {
            "PP":  round(pp, 4),
            "R1":  round(r1, 4),
            "R2":  round(r2, 4),
            "R3":  round(r3, 4),
            "S1":  round(s1, 4),
            "S2":  round(s2, 4),
            "S3":  round(s3, 4),
        }

    @staticmethod
    def moving_average(prices: list[float], period: Optional[int] = None) -> float:
        """Simple moving average over a list of prices (or a custom period)."""
        data = prices if period is None else prices[-period:]
        if not data:
            raise ValueError("Price list is empty.")
        return round(sum(data) / len(data), 4)
