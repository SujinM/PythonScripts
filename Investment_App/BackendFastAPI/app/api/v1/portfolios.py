"""
app/api/v1/portfolios.py
────────────────────────
Portfolio management endpoints (per-user):
  GET    /api/v1/portfolios         — list current user's portfolios
  POST   /api/v1/portfolios         — create a new portfolio
  DELETE /api/v1/portfolios/{id}    — delete a portfolio owned by current user
"""

from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser
from app.auth.schemas import PortfolioCreate, PortfolioRead
from app.db.models import Portfolio
from app.db.session import get_db

router = APIRouter(prefix="/portfolios", tags=["portfolios"])

_DBDep = Annotated[Session, Depends(get_db)]


@router.get("", response_model=List[PortfolioRead])
def list_portfolios(user: CurrentUser, db: _DBDep):
    """List all portfolios belonging to the authenticated user."""
    return db.query(Portfolio).filter(Portfolio.user_id == user.id).all()


@router.post("", response_model=PortfolioRead, status_code=status.HTTP_201_CREATED)
def create_portfolio(payload: PortfolioCreate, user: CurrentUser, db: _DBDep):
    """Create a new portfolio for the authenticated user."""
    p = Portfolio(user_id=user.id, name=payload.name, description=payload.description)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(portfolio_id: str, user: CurrentUser, db: _DBDep):
    """Delete a portfolio owned by the authenticated user."""
    p = (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
        .first()
    )
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(p)
    db.commit()
