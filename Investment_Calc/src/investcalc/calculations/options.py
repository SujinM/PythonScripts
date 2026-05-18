"""Basic Options pricing calculations."""

import math
from dataclasses import dataclass


class OptionsCalculator:
    """Options pricing helpers (Black-Scholes, Greeks, intrinsic value)."""

    @staticmethod
    def intrinsic_value(
        option_type: str, spot: float, strike: float
    ) -> dict:
        """
        Intrinsic value of a call or put option.
        option_type: 'call' or 'put'
        """
        ot = option_type.lower()
        if ot == "call":
            iv = max(spot - strike, 0)
        elif ot == "put":
            iv = max(strike - spot, 0)
        else:
            raise ValueError("option_type must be 'call' or 'put'.")
        return {
            "Option Type":     option_type.upper(),
            "Spot Price":      spot,
            "Strike Price":    strike,
            "Intrinsic Value": round(iv, 4),
            "In The Money":    iv > 0,
        }

    @staticmethod
    def black_scholes(
        option_type: str,
        S: float,   # Spot price
        K: float,   # Strike price
        T: float,   # Time to expiry in years
        r: float,   # Risk-free rate (decimal)
        sigma: float,  # Volatility (decimal)
    ) -> dict:
        """Black-Scholes option pricing model."""
        if T <= 0 or sigma <= 0:
            raise ValueError("T and sigma must be positive.")

        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        def _norm_cdf(x: float) -> float:
            return (1.0 + math.erf(x / math.sqrt(2))) / 2.0

        if option_type.lower() == "call":
            price = S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
            delta = _norm_cdf(d1)
        elif option_type.lower() == "put":
            price = K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)
            delta = _norm_cdf(d1) - 1
        else:
            raise ValueError("option_type must be 'call' or 'put'.")

        gamma = (
            math.exp(-0.5 * d1**2)
            / (S * sigma * math.sqrt(T) * math.sqrt(2 * math.pi))
        )
        theta = (
            -(S * sigma * math.exp(-0.5 * d1**2)) / (2 * math.sqrt(T) * math.sqrt(2 * math.pi))
            - r * K * math.exp(-r * T) * _norm_cdf(d2 if option_type.lower() == "call" else -d2)
        ) / 365

        return {
            "Option Type": option_type.upper(),
            "Price":  round(price, 4),
            "Delta":  round(delta, 4),
            "Gamma":  round(gamma, 6),
            "Theta":  round(theta, 6),
            "d1":     round(d1, 4),
            "d2":     round(d2, 4),
        }
