"""
app/db/base.py
──────────────
SQLAlchemy declarative base shared by all DB models.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
