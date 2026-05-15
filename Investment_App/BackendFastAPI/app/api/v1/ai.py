"""
app/api/v1/ai.py
────────────────
AI scoring / recommendation endpoints.

  POST /api/v1/{broker}/ai/recommendation

Returns a deterministic, rules-based recommendation for a given
instrument symbol using the caller's live portfolio holdings as
scoring context.

No large-language-model is involved — the score is fully auditable
and reproducible for the same inputs.
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
    """Serialised recommendation payload."""

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
    data_timestamp:          str
    is_stale:                bool
    risk_profile:            str
    holding_snapshot:        Optional[dict]


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
        data_timestamp=result.data_timestamp,
        is_stale=result.is_stale,
        risk_profile=result.risk_profile,
        holding_snapshot=result.holding_snapshot,
    )

    return APIResponse(data=out)
