"""
app/api/v1/portfolio.py
───────────────────────
Portfolio endpoints:
  GET /api/v1/{broker}/holdings
  GET /api/v1/{broker}/positions
  GET /api/v1/{broker}/trades
  GET /api/v1/{broker}/summary
  POST /api/v1/{broker}/cache/invalidate
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.deps import get_portfolio_service
from app.core.exceptions import BrokerAuthError, BrokerError, BrokerNotFoundError
from app.models.portfolio import Holding, PortfolioSummary, Position, Trade
from app.models.responses import APIResponse
from app.services.portfolio_service import PortfolioService

router = APIRouter(tags=["portfolio"])

_ServiceDep = Annotated[PortfolioService, Depends(get_portfolio_service)]


def _resolve(broker_id: str, svc: PortfolioService):
    """Validate broker and raise proper HTTP errors."""
    try:
        svc._require(broker_id)
    except BrokerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{broker}/holdings", response_model=APIResponse[list[Holding]])
def get_holdings(
    broker: Annotated[str, Path(description="Broker identifier, e.g. 'upstox'")],
    svc: _ServiceDep,
) -> APIResponse[list[Holding]]:
    _resolve(broker, svc)
    try:
        return APIResponse(data=svc.get_holdings(broker))
    except BrokerAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except BrokerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/{broker}/positions", response_model=APIResponse[list[Position]])
def get_positions(
    broker: Annotated[str, Path()],
    svc: _ServiceDep,
) -> APIResponse[list[Position]]:
    _resolve(broker, svc)
    try:
        return APIResponse(data=svc.get_positions(broker))
    except BrokerAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except BrokerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/{broker}/trades", response_model=APIResponse[list[Trade]])
def get_trades(
    broker: Annotated[str, Path()],
    svc: _ServiceDep,
) -> APIResponse[list[Trade]]:
    _resolve(broker, svc)
    try:
        return APIResponse(data=svc.get_trades(broker))
    except BrokerAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except BrokerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/{broker}/summary", response_model=APIResponse[PortfolioSummary])
def get_summary(
    broker: Annotated[str, Path()],
    svc: _ServiceDep,
) -> APIResponse[PortfolioSummary]:
    _resolve(broker, svc)
    try:
        return APIResponse(data=svc.get_summary(broker))
    except BrokerAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except BrokerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/{broker}/cache/invalidate", response_model=APIResponse[dict])
def invalidate_cache(
    broker: Annotated[str, Path()],
    svc: _ServiceDep,
) -> APIResponse[dict]:
    _resolve(broker, svc)
    svc.invalidate(broker)
    return APIResponse(data={"message": f"Cache cleared for broker '{broker}'"})
