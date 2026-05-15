"""
app/services/recommendation_service.py
────────────────────────────────────────
Deterministic, auditable recommendation scorer.

No I/O, no external calls — pure functions over Holding data and
optional instrument metadata.  Every output is reproducible for the
same inputs and fully unit-testable.

Scoring formula
───────────────
  score = 0.35 * trend
        + 0.25 * momentum
        + 0.20 * valuation
        + 0.20 * risk

Each component is normalised to [0, 100].

Action bands
────────────
  score >= BUY_THRESHOLD  → BUY
  score <= SELL_THRESHOLD → SELL
  otherwise               → HOLD

Profile adjustments
───────────────────
  conservative : BUY_THRESHOLD raised to 72 (needs stronger conviction)
  aggressive   : SELL_THRESHOLD lowered to 28 (more tolerant of weakness)
  moderate     : defaults (65 / 35)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional

from app.models.portfolio import Holding

# ── Constants ──────────────────────────────────────────────────────────────────

FEATURE_WEIGHTS: dict[str, float] = {
    "trend":      0.35,
    "momentum":   0.25,
    "valuation":  0.20,
    "risk":       0.20,
}

_BUY_THRESHOLD:  dict[str, float] = {
    "conservative": 72.0,
    "moderate":     65.0,
    "aggressive":   60.0,
}
_SELL_THRESHOLD: dict[str, float] = {
    "conservative": 40.0,
    "moderate":     35.0,
    "aggressive":   28.0,
}

RiskProfile = Literal["conservative", "moderate", "aggressive"]
Action      = Literal["BUY", "SELL", "HOLD"]


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class ScoreFeatures:
    """Raw normalised [0-100] scores for each feature dimension."""
    trend:      float   # Price-trend signal
    momentum:   float   # Performance vs portfolio average
    valuation:  float   # Concentration-based valuation
    risk:       float   # Drawdown / downside exposure


@dataclass
class HoldingContext:
    """Derived contextual values used in scoring and explanation."""
    return_pct:           float    # Holding's unrealised return
    portfolio_weight_pct: float    # % of total portfolio value
    avg_portfolio_return: float    # Average return_pct across all holdings
    total_holdings:       int      # Number of holdings in the broker account
    is_tradable:          bool     # From instrument catalogue (default True)


@dataclass
class RecommendationResult:
    """Full recommendation payload returned by the endpoint."""
    symbol:               str
    action:               Action
    score:                float           # Composite 0-100
    confidence:           int             # 0-100 certainty in the action
    features:             dict[str, float]
    feature_weights:      dict[str, float]
    risk_flags:           list[str]
    reason_bullets:       list[str]
    invalidation_conditions: list[str]
    data_timestamp:       str
    is_stale:             bool
    risk_profile:         str
    holding_snapshot:     Optional[dict]  # Abbreviated holding data for audit


# ── Individual feature scorers (pure functions) ────────────────────────────────

def score_trend(return_pct: float) -> float:
    """
    Map a holding's unrealised return percentage to a trend score.

    Scale: each 1 % of return shifts the score 2.5 points from the
    neutral midpoint (50).  ±20 % maps to the full [0, 100] range.

      return_pct = +20 % → 100
      return_pct =   0 % →  50
      return_pct = -20 % →   0
    """
    return max(0.0, min(100.0, 50.0 + return_pct * 2.5))


def score_momentum(return_pct: float, avg_portfolio_return: float) -> float:
    """
    Relative momentum: how far above/below the portfolio average.

    Scale: each 1 % outperformance shifts score 5 points from 50.
    ±10 % outperformance maps to the full range.

      delta = +10 % → 100
      delta =   0 % →  50
      delta = -10 % →   0
    """
    delta = return_pct - avg_portfolio_return
    return max(0.0, min(100.0, 50.0 + delta * 5.0))


def score_valuation(portfolio_weight_pct: float) -> float:
    """
    Concentration-based valuation proxy.

    Lower concentration → more room to add → higher score.

      weight = 0 %        → 60  (not held; neutral-positive)
      weight < 5 %        → 70  (underweight)
      5 % <= weight < 10 %→ 55  (fair weight)
      10 % <= weight < 15%→ 40  (slightly overweight)
      weight >= 15 %      → 25  (significantly overweight)
    """
    if portfolio_weight_pct <= 0:
        return 60.0
    elif portfolio_weight_pct < 5.0:
        return 70.0
    elif portfolio_weight_pct < 10.0:
        return 55.0
    elif portfolio_weight_pct < 15.0:
        return 40.0
    else:
        return 25.0


def score_risk(return_pct: float) -> float:
    """
    Drawdown / downside exposure score.

    Positive returns reduce perceived risk.
    Losses linearly increase risk exposure.

      return_pct >=  0 % → 70 + 1.5 * return_pct  (capped at 100)
      return_pct <   0 % → 70 + 3.0 * return_pct  (floor at 0)

    Examples:
      return_pct = +20 % → 100
      return_pct =   0 % →  70
      return_pct = -10 % →  40
      return_pct = -23 % →   1
    """
    if return_pct >= 0:
        return min(100.0, 70.0 + return_pct * 1.5)
    return max(0.0, 70.0 + return_pct * 3.0)


def compute_composite_score(features: ScoreFeatures) -> float:
    """Apply weighted sum of the four feature scores."""
    return round(
        FEATURE_WEIGHTS["trend"]     * features.trend
        + FEATURE_WEIGHTS["momentum"]  * features.momentum
        + FEATURE_WEIGHTS["valuation"] * features.valuation
        + FEATURE_WEIGHTS["risk"]      * features.risk,
        2,
    )


def score_to_action(score: float, risk_profile: RiskProfile) -> Action:
    """Map composite score to BUY / SELL / HOLD based on risk profile thresholds."""
    buy_threshold  = _BUY_THRESHOLD[risk_profile]
    sell_threshold = _SELL_THRESHOLD[risk_profile]
    if score >= buy_threshold:
        return "BUY"
    if score <= sell_threshold:
        return "SELL"
    return "HOLD"


def score_to_confidence(score: float, action: Action) -> int:
    """
    Confidence in the generated action.

    Measured as distance from the nearest decision boundary (35 or 65),
    scaled to [10, 95] to avoid false certainty.

    Near a boundary (score ≈ 35 or 65) → low confidence (~10).
    Far from both boundaries (score ≈ 0 or 100) → high confidence (~95).
    """
    dist_from_center = abs(score - 50.0)
    raw = dist_from_center * 2.0
    return int(max(10, min(95, round(raw))))


# ── Explanation builders ───────────────────────────────────────────────────────

def build_reason_bullets(
    symbol: str,
    ctx: HoldingContext,
    features: ScoreFeatures,
    action: Action,
) -> list[str]:
    bullets = []

    # Trend
    if features.trend >= 65:
        bullets.append(
            f"Strong uptrend: {ctx.return_pct:+.2f}% unrealised return on current position"
        )
    elif features.trend >= 50:
        bullets.append(
            f"Slight positive trend: {ctx.return_pct:+.2f}% return on current position"
        )
    elif features.trend >= 35:
        bullets.append(
            f"Slight negative trend: {ctx.return_pct:+.2f}% — approaching loss territory"
        )
    else:
        bullets.append(
            f"Significant downtrend: {ctx.return_pct:+.2f}% — position is under pressure"
        )

    # Momentum
    delta = ctx.return_pct - ctx.avg_portfolio_return
    if abs(delta) < 1.0:
        bullets.append(
            f"Inline with portfolio: performing close to portfolio average "
            f"({ctx.avg_portfolio_return:+.2f}%)"
        )
    elif delta > 0:
        bullets.append(
            f"Outperforming portfolio average by {delta:+.2f}% "
            f"(portfolio avg: {ctx.avg_portfolio_return:+.2f}%)"
        )
    else:
        bullets.append(
            f"Underperforming portfolio average by {abs(delta):.2f}% "
            f"(portfolio avg: {ctx.avg_portfolio_return:+.2f}%)"
        )

    # Valuation / concentration
    w = ctx.portfolio_weight_pct
    if w <= 0:
        bullets.append(
            f"{symbol} is not currently held — no concentration constraint"
        )
    elif w < 5:
        bullets.append(f"Underweight position: {w:.1f}% of portfolio — room to increase")
    elif w < 10:
        bullets.append(f"Fair-weight position: {w:.1f}% of portfolio")
    elif w < 15:
        bullets.append(
            f"Slightly overweight: {w:.1f}% of portfolio — concentration caution"
        )
    else:
        bullets.append(
            f"Significantly overweight: {w:.1f}% of portfolio — high concentration risk"
        )

    # Risk / drawdown
    if features.risk >= 70:
        bullets.append("Low drawdown risk: return is positive, protecting downside")
    elif features.risk >= 40:
        bullets.append(
            f"Moderate drawdown risk: {ctx.return_pct:.2f}% return shows limited cushion"
        )
    else:
        bullets.append(
            f"Elevated drawdown: {ctx.return_pct:.2f}% return signals meaningful loss exposure"
        )

    if not ctx.is_tradable:
        bullets.append(
            f"Note: {symbol} is marked as non-tradable in the instrument catalogue"
        )

    return bullets


def build_invalidation_conditions(
    symbol: str,
    ctx: HoldingContext,
    action: Action,
    risk_profile: RiskProfile,
) -> list[str]:
    conditions = []
    buy_t  = _BUY_THRESHOLD[risk_profile]
    sell_t = _SELL_THRESHOLD[risk_profile]

    if action == "BUY":
        # Reversal of current positive trend
        conditions.append(
            f"Signal invalidates if {symbol} return drops below "
            f"{ctx.return_pct - 5.0:.1f}% (5% reversal from current level)"
        )
        conditions.append(
            "Signal invalidates if position concentration rises above 15% "
            "of total portfolio value"
        )
        conditions.append(
            "Signal invalidates if portfolio average return deteriorates "
            "significantly (momentum reversal)"
        )
    elif action == "SELL":
        conditions.append(
            f"Signal invalidates if {symbol} return recovers above "
            f"{ctx.return_pct + 5.0:.1f}% from the current level"
        )
        conditions.append(
            "Signal invalidates if broad portfolio recovers, narrowing "
            "the underperformance gap"
        )
    else:  # HOLD
        conditions.append(
            f"Upgrade to BUY if composite score rises above {buy_t:.0f} "
            f"(needs trend + momentum improvement)"
        )
        conditions.append(
            f"Downgrade to SELL if composite score falls below {sell_t:.0f} "
            f"(continued drawdown or severe underperformance)"
        )

    return conditions


def build_risk_flags(
    symbol: str,
    ctx: HoldingContext,
    features: ScoreFeatures,
    action: Action,
    risk_profile: RiskProfile,
) -> list[str]:
    flags = []

    if ctx.portfolio_weight_pct >= 15.0:
        flags.append(
            f"High concentration: {symbol} represents {ctx.portfolio_weight_pct:.1f}% "
            "of portfolio — exceeds 15% concentration threshold"
        )
    elif ctx.portfolio_weight_pct >= 10.0:
        flags.append(
            f"Elevated concentration: {symbol} at {ctx.portfolio_weight_pct:.1f}% "
            "of portfolio"
        )

    if ctx.return_pct <= -10.0:
        flags.append(
            f"Deep loss alert: {symbol} is down {abs(ctx.return_pct):.2f}% — "
            "review stop-loss or rebalancing strategy"
        )

    if action == "BUY" and risk_profile == "conservative" and features.risk < 60:
        flags.append(
            "Conservative profile: elevated risk score suppresses BUY confidence — "
            "ensure position size is within risk budget"
        )

    if not ctx.is_tradable:
        flags.append(
            f"{symbol} is flagged as non-tradable in the instrument catalogue — "
            "verify availability before executing any trade"
        )

    if ctx.total_holdings == 0:
        flags.append(
            "No holdings data available for this broker — "
            "recommendation is based on instrument defaults only"
        )

    return flags


# ── Main entry point ──────────────────────────────────────────────────────────

def compute_recommendation(
    symbol: str,
    holdings: list[Holding],
    risk_profile: RiskProfile = "moderate",
    is_tradable: bool = True,
    data_timestamp: Optional[datetime] = None,
    cache_ttl_seconds: int = 300,
) -> RecommendationResult:
    """
    Compute a deterministic recommendation for *symbol* given the full
    list of broker holdings and the caller's risk profile.

    Works correctly even when the symbol is not currently held
    (scores default to neutral, action defaults to HOLD).

    Parameters
    ----------
    symbol            : The instrument symbol to score.
    holdings          : All broker holdings (used for portfolio-level context).
    risk_profile      : "conservative" | "moderate" | "aggressive".
    is_tradable       : From instrument catalogue; defaults True when unknown.
    data_timestamp    : UTC datetime of the holdings snapshot (for stale check).
    cache_ttl_seconds : Holdings cache TTL — used to compute staleness.
    """
    now = datetime.now(timezone.utc)
    ts_str = (data_timestamp or now).isoformat()

    # Is the snapshot stale?
    is_stale = False
    if data_timestamp:
        age = (now - data_timestamp).total_seconds()
        is_stale = age > cache_ttl_seconds * 2   # warn after 2× TTL

    # Portfolio-level aggregates
    total_portfolio_value = sum(h.current_value for h in holdings) or 1.0
    avg_portfolio_return = (
        sum(h.return_pct for h in holdings) / len(holdings)
        if holdings else 0.0
    )

    # Find the target holding (may not exist)
    target: Optional[Holding] = next(
        (h for h in holdings if h.trading_symbol.upper() == symbol.upper()),
        None,
    )

    if target:
        return_pct = target.return_pct
        weight_pct = round(target.current_value / total_portfolio_value * 100, 2)
        holding_snap = {
            "return_pct":           round(return_pct, 4),
            "current_value":        round(target.current_value, 2),
            "portfolio_weight_pct": weight_pct,
        }
    else:
        # Not in portfolio — use neutral defaults
        return_pct = 0.0
        weight_pct = 0.0
        holding_snap = None

    ctx = HoldingContext(
        return_pct=return_pct,
        portfolio_weight_pct=weight_pct,
        avg_portfolio_return=round(avg_portfolio_return, 4),
        total_holdings=len(holdings),
        is_tradable=is_tradable,
    )

    # Compute features
    features = ScoreFeatures(
        trend=score_trend(return_pct),
        momentum=score_momentum(return_pct, avg_portfolio_return),
        valuation=score_valuation(weight_pct),
        risk=score_risk(return_pct),
    )

    score = compute_composite_score(features)

    # Apply is_tradable guardrail BEFORE computing action
    effective_risk_profile: RiskProfile = risk_profile
    if not is_tradable:
        # Force HOLD for non-tradable instruments regardless of score
        action: Action = "HOLD"
    else:
        action = score_to_action(score, effective_risk_profile)

    confidence = score_to_confidence(score, action)

    features_dict = {
        "trend":     round(features.trend, 2),
        "momentum":  round(features.momentum, 2),
        "valuation": round(features.valuation, 2),
        "risk":      round(features.risk, 2),
    }

    return RecommendationResult(
        symbol=symbol.upper(),
        action=action,
        score=score,
        confidence=confidence,
        features=features_dict,
        feature_weights=dict(FEATURE_WEIGHTS),
        risk_flags=build_risk_flags(symbol, ctx, features, action, risk_profile),
        reason_bullets=build_reason_bullets(symbol, ctx, features, action),
        invalidation_conditions=build_invalidation_conditions(
            symbol, ctx, action, risk_profile
        ),
        data_timestamp=ts_str,
        is_stale=is_stale,
        risk_profile=risk_profile,
        holding_snapshot=holding_snap,
    )
