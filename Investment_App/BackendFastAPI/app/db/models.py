"""
app/db/models.py
────────────────
SQLAlchemy ORM models for users, portfolios, and portfolio holdings.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id            = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username      = Column(String(50), unique=True, nullable=False, index=True)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role          = Column(String(20), nullable=False, default="user")
    created_at    = Column(DateTime(timezone=True), default=_now, nullable=False)

    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id          = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id     = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name        = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), default=_now, nullable=False)

    user     = relationship("User", back_populates="portfolios")
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id            = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id  = Column(String(36), ForeignKey("portfolios.id"), nullable=False, index=True)
    instrument_id = Column(String(100), nullable=False)
    quantity      = Column(Float, nullable=False, default=0.0)
    average_price = Column(Float, nullable=False, default=0.0)

    portfolio = relationship("Portfolio", back_populates="holdings")


# ---------------------------------------------------------------------------
# eToro instrument catalogue (populated by the sync script / API endpoint)
# ---------------------------------------------------------------------------

class EtoroInstrument(Base):
    """
    Mirror of the eToro instrument catalogue fetched from:
      https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments

    InstrumentTypeID mapping
    ------------------------
      1 = Currencies / Forex
      2 = Commodities
      3 = Indices
      4 = Stocks
      5 = ETFs
      6 = Crypto
    """

    __tablename__ = "etoro_instruments"

    instrument_id       = Column(Integer, primary_key=True)          # InstrumentID
    symbol              = Column(String(50),  nullable=False, index=True)  # SymbolFull
    display_name        = Column(String(200), nullable=False, index=True)  # InstrumentDisplayName
    instrument_type_id  = Column(Integer,  nullable=True)            # InstrumentTypeID
    exchange_id         = Column(Integer,  nullable=True)            # ExchangeID
    price_source        = Column(String(50),  nullable=True)         # PriceSource
    has_expiration_date = Column(Boolean,  default=False)            # HasExpirationDate
    is_internal         = Column(Boolean,  default=False)            # IsInternalInstrument
    distribution_type   = Column(Integer,  nullable=True)            # DistributionType
    image_url           = Column(String(500), nullable=True)         # best-fit avatar URL
    synced_at           = Column(DateTime(timezone=True), nullable=True)
