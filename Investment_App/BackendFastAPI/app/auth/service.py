"""
app/auth/service.py
───────────────────
Password hashing, JWT creation/verification, and user CRUD helpers.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import User

# ── Password hashing (using bcrypt directly) ──────────────────────────────────

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_access_token(user_id: str, role: str) -> str:
    s = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=s.jwt_expire_minutes)
    payload = {"sub": user_id, "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def create_refresh_token(user_id: str) -> str:
    s = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    payload = {"sub": user_id, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT.  Raises JWTError on failure."""
    s = get_settings()
    return jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])


# ── User CRUD ─────────────────────────────────────────────────────────────────

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    role: str = "user",
) -> User:
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
