"""
app/api/v1/users.py
───────────────────
User management endpoints (admin-only):
  GET /api/v1/users — list all registered users
"""

from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import AdminUser
from app.auth.schemas import UserRead
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserRead])
def list_users(_: AdminUser, db: Annotated[Session, Depends(get_db)]):
    """Return all registered users.  Requires admin role."""
    return db.query(User).order_by(User.created_at).all()
