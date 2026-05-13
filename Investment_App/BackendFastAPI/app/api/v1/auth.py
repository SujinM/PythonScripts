"""
app/api/v1/auth.py
──────────────────
Auth endpoints:
  POST /api/v1/auth/register  — create a new user account
  POST /api/v1/auth/login     — exchange credentials for tokens
  POST /api/v1/auth/refresh   — exchange refresh token for new access token
  GET  /api/v1/auth/me        — return current user profile
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser
from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
)
from app.auth.service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    decode_token,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
)
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

_DBDep = Annotated[Session, Depends(get_db)]


# ── Register ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: _DBDep):
    """Create a new user account."""
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    if get_user_by_username(db, payload.username):
        raise HTTPException(status_code=409, detail="Username already taken")
    user = create_user(db, payload.username, payload.email, payload.password)
    return user


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: _DBDep):
    """Authenticate and return access + refresh tokens together with user info."""
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return LoginResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
        user=UserRead.model_validate(user),
    )


# ── Refresh ───────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: _DBDep):
    """Return a new access token given a valid refresh token."""
    token = body.get_token()
    if not token:
        raise HTTPException(status_code=400, detail="refresh_token is required")
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")
        user = get_user_by_id(db, payload["sub"])
        if not user:
            raise ValueError("User not found")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserRead)
def me(user: CurrentUser):
    """Return the currently authenticated user's profile."""
    return user
