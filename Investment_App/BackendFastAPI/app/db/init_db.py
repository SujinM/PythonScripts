"""
app/db/init_db.py
─────────────────
Creates all tables on startup and seeds the default admin user.
"""

from __future__ import annotations

from app.core.logger import get_logger
from app.db.base import Base
from app.db.session import SessionLocal, engine

from app.core.config import get_settings

logger = get_logger(__name__)


def init_db() -> None:
    """Create all tables and seed the default admin user if absent."""
    # Import models so SQLAlchemy knows about them before create_all
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified.")
    _seed_admin()


def _seed_admin() -> None:
    """Create the built-in admin account if it doesn't exist yet."""
    # Lazy import avoids circular dependency at module load time
    from app.auth.service import create_user, get_user_by_email

    s = get_settings()
    db = SessionLocal()
    try:
        if get_user_by_email(db, s.admin_email):
            return
        create_user(db, s.admin_username, s.admin_email, s.admin_password, role="admin")
        logger.info("Default admin seeded  →  %s", s.admin_email)
    finally:
        db.close()
