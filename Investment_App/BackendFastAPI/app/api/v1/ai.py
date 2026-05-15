"""
app/api/v1/ai.py
────────────────
AI scoring / recommendation endpoints.

  POST /api/v1/{broker}/ai/recommendation        — Phase 2: BUY/SELL/HOLD score
  GET  /api/v1/{broker}/ai/backtest/{symbol}     — Phase 3: scenario analysis

Phase 2: deterministic BUY/SELL/HOLD scoring with feature breakdown.
Phase 3: natural-language narrative + scenario-based signal sensitivity analysis.

No LLM involved — all outputs are auditable and reproducible for the same inputs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from sqlalchemy.orm import Session

from app.api.deps import get_portfolio_service
from app.auth.deps import CurrentUser
from app.core.config import get_settings
from app.core.exceptions import BrokerAuthError, BrokerError, BrokerNotFoundError
from app.db.models import EtoroInstrument
from app.db.session import get_db
from app.models.responses import APIResponse
from app.services.portfolio_service import PortfolioService
from app.services.backtest_service import BacktestResult, run_backtest
from app.services.recommendation_service import (
    RiskProfile,
    compute_recommendation,
)

router = APIRouter(tags=["ai"])

_ServiceDep = Annotated[PortfolioService, Depends(get_portfolio_service)]
_DBDep      = Annotated[Session, Depends(get_db)]


# ── Request / Response Schemas ────────────────────────────────────────────────

class RecommendationRequest(BaseModel):
    """Body for the recommendation endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    symbol:       str                                       = Field(..., min_length=1, max_length=30)
    risk_profile: Literal["conservative", "moderate", "aggressive"] = "moderate"
    timeframe:    Optional[str]                             = Field(None, max_length=10)


class RecommendationOut(BaseModel):
    """Serialised recommendation payload (Phase 2 + Phase 3 narrative)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    symbol:                  str
    action:                  Literal["BUY", "SELL", "HOLD"]
    score:                   float           = Field(..., ge=0.0, le=100.0)
    confidence:              int             = Field(..., ge=0, le=100)
    features:                dict[str, float]
    feature_weights:         dict[str, float]
    risk_flags:              list[str]
    reason_bullets:          list[str]
    invalidation_conditions: list[str]
    narrative:               str             # Phase 3 — natural language explanation
    data_timestamp:          str
    is_stale:                bool
    risk_profile:            str
    holding_snapshot:        Optional[dict]


class ScenarioPointOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    return_pct:  float
    score:       float
    action:      Literal["BUY", "SELL", "HOLD"]
    label:       str
    is_current:  bool
    features:    dict[str, float]


class FlipInfoOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    direction:      str
    target_action:  Literal["BUY", "SELL", "HOLD"]
    at_return_pct:  float
    margin_pct:     float


class SignalZoneOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    action:      Literal["BUY", "SELL", "HOLD"]
    min_return:  Optional[float]
    max_return:  Optional[float]
    width:       float


class BacktestOut(BaseModel):
    """Serialised signal sensitivity / scenario analysis payload (Phase 3)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    symbol:               str
    risk_profile:         str
    current_return_pct:   float
    current_action:       Literal["BUY", "SELL", "HOLD"]
    current_score:        float
    scenario_analysis:    list[ScenarioPointOut]
    hit_rate_pct:         Optional[float]
    buy_signal_count:     int
    sell_signal_count:    int
    hold_signal_count:    int
    flip_downward:        Optional[FlipInfoOut]
    flip_upward:          Optional[FlipInfoOut]
    signal_zones:         list[SignalZoneOut]
    model_notes:          list[str]
    methodology:          str


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post(
    "/{broker}/ai/recommendation",
    response_model=APIResponse[RecommendationOut],
    summary="AI Recommendation",
    description=(
        "Returns a deterministic BUY / SELL / HOLD recommendation for the "
        "requested symbol, scored against the caller's live portfolio holdings."
    ),
)
def get_recommendation(
    broker:  Annotated[str, Path(description="Broker identifier, e.g. 'etoro' or 'upstox'")],
    body:    RecommendationRequest,
    svc:     _ServiceDep,
    db:      _DBDep,
    _user:   CurrentUser,          # JWT gate — not used in scoring logic
) -> APIResponse[RecommendationOut]:

    settings = get_settings()
    symbol   = body.symbol.strip().upper()

    # ── 1. Fetch broker holdings ───────────────────────────────────────────────
    try:
        holdings = svc.get_holdings(broker)
    except BrokerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BrokerAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except BrokerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    # ── 2. Instrument-catalogue metadata (tradability, staleness) ─────────────
    instrument = (
        db.query(EtoroInstrument)
        .filter(EtoroInstrument.symbol.ilike(symbol))
        .first()
    )

    is_tradable = True
    data_timestamp: Optional[datetime] = None

    if instrument:
        is_tradable     = not instrument.is_internal
        data_timestamp  = instrument.synced_at
        # Normalise synced_at to UTC-aware datetime for staleness check
        if data_timestamp and data_timestamp.tzinfo is None:
            data_timestamp = data_timestamp.replace(tzinfo=timezone.utc)

    # ── 3. Compute recommendation ─────────────────────────────────────────────
    result = compute_recommendation(
        symbol=symbol,
        holdings=holdings,
        risk_profile=body.risk_profile,
        is_tradable=is_tradable,
        data_timestamp=data_timestamp,
        cache_ttl_seconds=settings.cache_ttl_seconds,
    )

    # ── 4. Build response ─────────────────────────────────────────────────────
    out = RecommendationOut(
        symbol=result.symbol,
        action=result.action,
        score=result.score,
        confidence=result.confidence,
        features=result.features,
        feature_weights=result.feature_weights,
        risk_flags=result.risk_flags,
        reason_bullets=result.reason_bullets,
        invalidation_conditions=result.invalidation_conditions,
        narrative=result.narrative,
        data_timestamp=result.data_timestamp,
        is_stale=result.is_stale,
        risk_profile=result.risk_profile,
        holding_snapshot=result.holding_snapshot,
    )

    return APIResponse(data=out)


# ── Phase 3: Backtest / scenario analysis ─────────────────────────────────────

@router.get(
    "/{broker}/ai/backtest/{symbol}",
    response_model=APIResponse[BacktestOut],
    summary="Signal Sensitivity Analysis",
    description=(
        "Runs the scoring model across 20 return-percentage scenarios "
        "(−25% to +30%) and returns signal zones, flip points, and a "
        "simulated hit rate.  Portfolio concentration is held fixed at "
        "current values.  This is a sensitivity analysis, not a historical backtest."
    ),
)
def get_backtest(
    broker:       Annotated[str, Path(description="Broker identifier")],
    symbol:       Annotated[str, Path(description="Instrument symbol")],
    risk_profile: Literal["conservative", "moderate", "aggressive"] = "moderate",
    svc:          _ServiceDep = ...,
    _user:        CurrentUser = ...,
) -> APIResponse[BacktestOut]:

    sym = symbol.strip().upper()

    try:
        holdings = svc.get_holdings(broker)
    except BrokerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BrokerAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except BrokerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    result: BacktestResult = run_backtest(sym, holdings, risk_profile)

    out = BacktestOut(
        symbol=result.symbol,
        risk_profile=result.risk_profile,
        current_return_pct=result.current_return_pct,
        current_action=result.current_action,
        current_score=result.current_score,
        scenario_analysis=[
            ScenarioPointOut(
                return_pct=s.return_pct,
                score=s.score,
                action=s.action,
                label=s.label,
                is_current=s.is_current,
                features=s.features,
            )
            for s in result.scenario_analysis
        ],
        hit_rate_pct=result.hit_rate_pct,
        buy_signal_count=result.buy_signal_count,
        sell_signal_count=result.sell_signal_count,
        hold_signal_count=result.hold_signal_count,
        flip_downward=(
            FlipInfoOut(
                direction=result.flip_downward.direction,
                target_action=result.flip_downward.target_action,
                at_return_pct=result.flip_downward.at_return_pct,
                margin_pct=result.flip_downward.margin_pct,
            )
            if result.flip_downward else None
        ),
        flip_upward=(
            FlipInfoOut(
                direction=result.flip_upward.direction,
                target_action=result.flip_upward.target_action,
                at_return_pct=result.flip_upward.at_return_pct,
                margin_pct=result.flip_upward.margin_pct,
            )
            if result.flip_upward else None
        ),
        signal_zones=[
            SignalZoneOut(
                action=z.action,
                min_return=z.min_return,
                max_return=z.max_return,
                width=z.width,
            )
            for z in result.signal_zones
        ],
        model_notes=result.model_notes,
        methodology=result.methodology,
    )

    return APIResponse(data=out)
