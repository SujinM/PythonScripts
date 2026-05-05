"""
app/brokers/base.py
───────────────────
IBrokerAdapter — the single contract every broker must implement.

To add a new broker:
  1. Create app/brokers/<name>.py
  2. Subclass IBrokerAdapter and implement all abstract methods
  3. Register it in app/brokers/registry.py
  That is ALL — zero changes to routes, services, or models.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.portfolio import Holding, Position, Trade


class IBrokerAdapter(ABC):
    """Abstract broker adapter interface."""

    # ── Identity ──────────────────────────────────────────────────────────
    @property
    @abstractmethod
    def broker_id(self) -> str:
        """Unique lowercase identifier, e.g. 'upstox', 'etoro'."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name, e.g. 'Upstox', 'eToro'."""

    # ── Portfolio data ────────────────────────────────────────────────────
    @abstractmethod
    def get_holdings(self) -> list[Holding]:
        """Fetch and normalise long-term holdings."""

    @abstractmethod
    def get_positions(self) -> list[Position]:
        """Fetch and normalise open positions."""

    @abstractmethod
    def get_trades(self) -> list[Trade]:
        """Fetch and normalise today's executed trades."""

    # ── Health ────────────────────────────────────────────────────────────
    def is_configured(self) -> bool:
        """Return True if the minimum required credentials are present."""
        return True
