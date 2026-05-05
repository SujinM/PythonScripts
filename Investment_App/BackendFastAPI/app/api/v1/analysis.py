"""
app/api/v1/analysis.py
──────────────────────
Analysis endpoints:
  GET /api/v1/{broker}/analysis
  GET /api/v1/{broker}/analysis/alerts
  GET /api/v1/{broker}/brokers
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.deps import get_portfolio_service
from app.core.exceptions import BrokerAuthError, BrokerError, BrokerNotFoundError
from app.models.responses import APIResponse
from app.services import analysis_service
from app.services.portfolio_service import PortfolioService

router = APIRouter(tags=["analysis"])

_ServiceDep = Annotated[PortfolioService, Depends(get_portfolio_service)]


@router.get("/brokers", response_model=APIResponse[list[dict]])
def list_brokers(svc: _ServiceDep) -> APIResponse[list[dict]]:
    return APIResponse(data=svc.list_brokers())


@router.get("/{broker}/analysis", response_model=APIResponse[dict])
def full_analysis(
    broker: Annotated[str, Path()],
    svc: _ServiceDep,
) -> APIResponse[dict]:
    try:
        summary = svc.get_summary(broker)
        holdings = svc.get_holdings(broker)
    except BrokerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BrokerAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except BrokerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return APIResponse(data=analysis_service.build_analysis_result(summary, holdings))


@router.get("/{broker}/analysis/alerts", response_model=APIResponse[list[dict]])
def get_alerts(
    broker: Annotated[str, Path()],
    svc: _ServiceDep,
) -> APIResponse[list[dict]]:
    try:
        holdings = svc.get_holdings(broker)
    except BrokerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BrokerAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except BrokerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return APIResponse(data=analysis_service.compute_alerts(holdings))
