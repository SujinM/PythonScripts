"""
app/auth/schemas.py
───────────────────
Pydantic request / response models for the auth system.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


# ── Requests ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 50:
            raise ValueError("Username must be at most 50 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    # Accept both camelCase (frontend) and snake_case
    refreshToken: Optional[str] = None
    refresh_token: Optional[str] = None

    def get_token(self) -> str:
        return self.refreshToken or self.refresh_token or ""


# ── Responses ─────────────────────────────────────────────────────────────────

class UserRead(BaseModel):
    id: str
    username: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(TokenResponse):
    """Login response that also embeds the user so the frontend avoids a second round-trip."""
    user: UserRead


# ── Portfolio schemas ─────────────────────────────────────────────────────────

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None


class PortfolioRead(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
