"""Risk management calculations."""

import math
from dataclasses import dataclass


@dataclass
class RiskResult:
    label: str
    value: float
    unit: str
    description: str = ""

    def __str__(self) -> str:
        return f"{self.label}: {self.value:,.4f} {self.unit}"


class RiskCalculator:
    """Position sizing and risk calculations."""

    @staticmethod
    def position_size_by_risk(
        account_size: float, risk_pct: float, buy_price: float, stop_loss_price: float
    ) -> dict:
        """How many shares to buy given account risk tolerance."""
        risk_amount = account_size * risk_pct / 100
        risk_per_share = abs(buy_price - stop_loss_price)
        if risk_per_share == 0:
            raise ValueError("Buy price and stop loss price cannot be equal.")
        shares = risk_amount / risk_per_share
        total_cost = shares * buy_price
        return {
            "Risk Amount":    round(risk_amount, 2),
            "Risk Per Share": round(risk_per_share, 4),
            "Shares to Buy":  math.floor(shares),
            "Total Cost":     round(math.floor(shares) * buy_price, 2),
        }

    @staticmethod
    def risk_reward_ratio(
        buy_price: float, stop_loss: float, target: float
    ) -> RiskResult:
        """Risk-to-reward ratio of a trade."""
        risk = abs(buy_price - stop_loss)
        reward = abs(target - buy_price)
        if risk == 0:
            raise ValueError("Risk (buy - stop loss) cannot be zero.")
        rr = reward / risk
        return RiskResult(
            label="Risk/Reward Ratio",
            value=round(rr, 4),
            unit="",
            description=f"Risk: {risk:.4f}  Reward: {reward:.4f}",
        )

    @staticmethod
    def sharpe_ratio(
        avg_return: float, risk_free_rate: float, std_dev: float
    ) -> RiskResult:
        """Sharpe ratio (all values as percentages)."""
        if std_dev == 0:
            raise ValueError("Standard deviation cannot be zero.")
        sr = (avg_return - risk_free_rate) / std_dev
        return RiskResult(label="Sharpe Ratio", value=round(sr, 4), unit="")

    @staticmethod
    def volatility(prices: list[float]) -> RiskResult:
        """Historical volatility (std deviation of daily returns %)."""
        if len(prices) < 2:
            raise ValueError("Need at least 2 prices.")
        returns = [
            (prices[i] - prices[i - 1]) / prices[i - 1] * 100
            for i in range(1, len(prices))
        ]
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        vol = math.sqrt(variance)
        return RiskResult(
            label="Volatility (Daily)",
            value=round(vol, 4),
            unit="%",
            description=f"Based on {len(prices)} prices",
        )

    @staticmethod
    def max_drawdown(prices: list[float]) -> RiskResult:
        """Maximum drawdown from peak to trough."""
        if not prices:
            raise ValueError("Price list is empty.")
        peak = prices[0]
        max_dd = 0.0
        for p in prices:
            if p > peak:
                peak = p
            dd = (peak - p) / peak * 100
            if dd > max_dd:
                max_dd = dd
        return RiskResult(
            label="Max Drawdown",
            value=round(max_dd, 4),
            unit="%",
            description=f"Over {len(prices)} prices",
        )
