"""
app/services/backtest_service.py
─────────────────────────────────
Signal sensitivity analysis — a deterministic, scenario-based substitute
for a true backtest when historical price data is unavailable.

What it does
────────────
  1. Generates a sweep of 21 return-percentage scenarios (−25 % to +30 %).
  2. For each scenario, re-runs the Phase-2 scoring model holding all other
     inputs (portfolio weight, avg portfolio return) fixed at their current
     values.
  3. Derives:
       • signal_zones      — which return ranges produce BUY / HOLD / SELL
       • flip points        — minimum return-change needed to flip the action
       • hit_rate_pct       — % of directionally-correct signals across the
                              sweep (BUY correct when return > 0, SELL when < 0)

Methodology note
────────────────
  This is NOT a backtest over historical price data.  It is a static
  sensitivity / scenario analysis of the scoring model at a single point in
  time.  The `methodology` field in the response makes this explicit.

All functions are pure (no I/O) and fully unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.models.portfolio import Holding
from app.services.recommendation_service import (
    Action,
    HoldingContext,
    RiskProfile,
    ScoreFeatures,
    _BUY_THRESHOLD,
    _SELL_THRESHOLD,
    compute_composite_score,
    score_momentum,
    score_risk,
    score_to_action,
    score_trend,
    score_valuation,
)

# ── Scenario sweep definition ─────────────────────────────────────────────────

_SCENARIOS: list[tuple[float, str]] = [
    (-25.0, "Severe drawdown"),
    (-20.0, "Significant loss"),
    (-15.0, "Moderate loss"),
    (-10.0, "Small loss"),
    (-7.5,  "Near-loss"),
    (-5.0,  "Minor loss"),
    (-2.5,  "Slight loss"),
    ( 0.0,  "Breakeven"),
    ( 2.5,  "Minimal gain"),
    ( 5.0,  "Modest gain"),
    ( 7.5,  "Moderate gain"),
    (10.0,  "Good gain"),
    (12.5,  "Solid gain"),
    (15.0,  "Strong gain"),
    (17.5,  "Very strong gain"),
    (20.0,  "Excellent gain"),
    (22.5,  "Outstanding gain"),
    (25.0,  "Exceptional gain"),
    (27.5,  "Top-tier gain"),
    (30.0,  "Maximum gain"),
]

METHODOLOGY = (
    "Signal sensitivity analysis: the scoring model is evaluated across "
    "20 return-percentage scenarios (−25% to +30%) while holding portfolio "
    "concentration and relative momentum fixed at current values.  "
    "Hit rate measures the fraction of scenarios where the signal direction "
    "(BUY → positive return, SELL → negative return) is correct.  "
    "This is NOT a backtest over historical prices."
)


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class ScenarioPoint:
    """Single point in the scenario sweep."""
    return_pct:  float
    score:       float
    action:      Action
    label:       str
    is_current:  bool   # True when closest to the actual current return
    features:    dict[str, float]


@dataclass
class SignalZone:
    """Contiguous return-pct range that generates a specific action."""
    action:     Action
    min_return: Optional[float]   # None = extends to −∞
    max_return: Optional[float]   # None = extends to +∞
    width:      float             # max − min; 0 if one side is unbounded


@dataclass
class FlipInfo:
    """Describes the nearest point where the current action would change."""
    direction:         str    # "downward" or "upward"
    target_action:     Action
    at_return_pct:     float
    margin_pct:        float  # current_return − flip_return (positive = margin to flip)


@dataclass
class BacktestResult:
    """Full sensitivity analysis payload returned by the endpoint."""
    symbol:              str
    risk_profile:        str
    current_return_pct:  float
    current_action:      Action
    current_score:       float
    scenario_analysis:   list[ScenarioPoint]
    hit_rate_pct:        Optional[float]     # None when < 2 non-HOLD signals in sweep
    buy_signal_count:    int
    sell_signal_count:   int
    hold_signal_count:   int
    flip_downward:       Optional[FlipInfo]  # nearest flip going down from current
    flip_upward:         Optional[FlipInfo]  # nearest flip going up from current
    signal_zones:        list[SignalZone]
    model_notes:         list[str]
    methodology:         str


# ── Core analysis ─────────────────────────────────────────────────────────────

def _compute_scene(
    return_pct: float,
    label: str,
    weight_pct: float,
    avg_portfolio_return: float,
    risk_profile: RiskProfile,
    current_return_pct: float,
) -> ScenarioPoint:
    f = ScoreFeatures(
        trend=score_trend(return_pct),
        momentum=score_momentum(return_pct, avg_portfolio_return),
        valuation=score_valuation(weight_pct),
        risk=score_risk(return_pct),
    )
    sc = compute_composite_score(f)
    return ScenarioPoint(
        return_pct=return_pct,
        score=round(sc, 1),
        action=score_to_action(sc, risk_profile),
        label=label,
        is_current=abs(return_pct - current_return_pct) <= 1.5,
        features={
            "trend":     round(f.trend, 1),
            "momentum":  round(f.momentum, 1),
            "valuation": round(f.valuation, 1),
            "risk":      round(f.risk, 1),
        },
    )


def _hit_rate(scenarios: list[ScenarioPoint]) -> Optional[float]:
    """
    Fraction of scenarios where the signal direction is correct.

    BUY is "correct" when return_pct > 0 (position is profitable).
    SELL is "correct" when return_pct < 0 (position is losing).
    HOLD scenarios are excluded from the denominator.
    """
    directional = [s for s in scenarios if s.action != "HOLD"]
    if len(directional) < 2:
        return None
    correct = sum(
        1 for s in directional
        if (s.action == "BUY"  and s.return_pct > 0)
        or (s.action == "SELL" and s.return_pct < 0)
    )
    return round(correct / len(directional) * 100, 1)


def _find_flip(
    current_return: float,
    current_action: Action,
    scenarios: list[ScenarioPoint],
    direction: str,  # "downward" or "upward"
) -> Optional[FlipInfo]:
    """Find the nearest scenario point where the action differs from current."""
    if direction == "downward":
        candidates = sorted(
            [s for s in scenarios if s.return_pct < current_return],
            key=lambda s: s.return_pct,
            reverse=True,  # closest first
        )
    else:
        candidates = sorted(
            [s for s in scenarios if s.return_pct > current_return],
            key=lambda s: s.return_pct,
        )

    for s in candidates:
        if s.action != current_action:
            return FlipInfo(
                direction=direction,
                target_action=s.action,
                at_return_pct=round(s.return_pct, 1),
                margin_pct=round(abs(current_return - s.return_pct), 1),
            )
    return None


def _build_signal_zones(scenarios: list[ScenarioPoint]) -> list[SignalZone]:
    """
    Extract contiguous action zones from the scenario sweep.

    Returns a list of zones ordered by ascending return_pct.
    """
    zones: list[SignalZone] = []
    if not scenarios:
        return zones

    sorted_scenes = sorted(scenarios, key=lambda s: s.return_pct)
    zone_action = sorted_scenes[0].action
    zone_min    = sorted_scenes[0].return_pct

    for s in sorted_scenes[1:]:
        if s.action != zone_action:
            zones.append(SignalZone(
                action=zone_action,
                min_return=zone_min,
                max_return=sorted_scenes[sorted_scenes.index(s) - 1].return_pct,
                width=round(
                    sorted_scenes[sorted_scenes.index(s) - 1].return_pct - zone_min,
                    1,
                ),
            ))
            zone_action = s.action
            zone_min    = s.return_pct

    # Final zone extends to +∞
    zones.append(SignalZone(
        action=zone_action,
        min_return=zone_min,
        max_return=sorted_scenes[-1].return_pct,
        width=round(sorted_scenes[-1].return_pct - zone_min, 1),
    ))
    return zones


def _build_model_notes(
    symbol: str,
    current_return: float,
    avg_portfolio_return: float,
    weight_pct: float,
    risk_profile: RiskProfile,
    flip_down: Optional[FlipInfo],
    flip_up: Optional[FlipInfo],
) -> list[str]:
    notes: list[str] = []

    buy_t  = _BUY_THRESHOLD[risk_profile]
    sell_t = _SELL_THRESHOLD[risk_profile]
    notes.append(
        f"Decision thresholds for {risk_profile} profile: "
        f"BUY ≥ {buy_t:.0f}, SELL ≤ {sell_t:.0f}."
    )

    if weight_pct > 0:
        notes.append(
            f"Valuation score is fixed at the current concentration "
            f"({weight_pct:.1f}% of portfolio) across all scenarios — "
            "it does not vary with return."
        )

    momentum_driver = abs(current_return - avg_portfolio_return)
    if momentum_driver > 5:
        notes.append(
            f"Momentum has an outsized effect here: {symbol} diverges "
            f"{momentum_driver:.1f}% from the portfolio average return."
        )

    if flip_down:
        notes.append(
            f"Signal flips to {flip_down.target_action} if return drops "
            f"{flip_down.margin_pct:.1f}% from the current level."
        )
    if flip_up:
        notes.append(
            f"Signal flips to {flip_up.target_action} if return rises "
            f"{flip_up.margin_pct:.1f}% from the current level."
        )

    return notes


# ── Public API ────────────────────────────────────────────────────────────────

def run_backtest(
    symbol: str,
    holdings: list[Holding],
    risk_profile: RiskProfile = "moderate",
) -> BacktestResult:
    """
    Run a scenario-based signal sensitivity analysis for *symbol*.

    Parameters
    ----------
    symbol       : Instrument symbol to analyse.
    holdings     : All broker holdings for portfolio-level context.
    risk_profile : "conservative" | "moderate" | "aggressive".
    """
    # Portfolio aggregates
    total_pv = sum(h.current_value for h in holdings) or 1.0
    avg_ret  = (
        sum(h.return_pct for h in holdings) / len(holdings)
        if holdings else 0.0
    )

    target = next(
        (h for h in holdings if h.trading_symbol.upper() == symbol.upper()),
        None,
    )
    current_return = target.return_pct if target else 0.0
    weight_pct     = (target.current_value / total_pv * 100) if target else 0.0

    # Score current state
    current_features = ScoreFeatures(
        trend=score_trend(current_return),
        momentum=score_momentum(current_return, avg_ret),
        valuation=score_valuation(weight_pct),
        risk=score_risk(current_return),
    )
    current_score  = compute_composite_score(current_features)
    current_action = score_to_action(current_score, risk_profile)

    # Build scenario sweep
    scenarios = [
        _compute_scene(ret, label, weight_pct, avg_ret, risk_profile, current_return)
        for ret, label in _SCENARIOS
    ]

    # Flip points
    flip_down = _find_flip(current_return, current_action, scenarios, "downward")
    flip_up   = _find_flip(current_return, current_action, scenarios, "upward")

    # Counts
    buy_count  = sum(1 for s in scenarios if s.action == "BUY")
    sell_count = sum(1 for s in scenarios if s.action == "SELL")
    hold_count = sum(1 for s in scenarios if s.action == "HOLD")

    return BacktestResult(
        symbol=symbol.upper(),
        risk_profile=risk_profile,
        current_return_pct=round(current_return, 4),
        current_action=current_action,
        current_score=round(current_score, 2),
        scenario_analysis=scenarios,
        hit_rate_pct=_hit_rate(scenarios),
        buy_signal_count=buy_count,
        sell_signal_count=sell_count,
        hold_signal_count=hold_count,
        flip_downward=flip_down,
        flip_upward=flip_up,
        signal_zones=_build_signal_zones(scenarios),
        model_notes=_build_model_notes(
            symbol, current_return, avg_ret, weight_pct,
            risk_profile, flip_down, flip_up,
        ),
        methodology=METHODOLOGY,
    )
