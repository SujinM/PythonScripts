"""
app/db/session.py
─────────────────
Database engine, session factory, and get_db FastAPI dependency.
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _make_engine():
    settings = get_settings()
    connect_args = (
        {"check_same_thread": False} if "sqlite" in settings.db_url else {}
    )
    return create_engine(settings.db_url, connect_args=connect_args)


engine = _make_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
