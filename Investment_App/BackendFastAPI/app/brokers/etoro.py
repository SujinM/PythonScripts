"""
app/brokers/etoro.py
────────────────────
EToroAdapter — eToro does not expose a public trading API for retail accounts.
This adapter provides a realistic stub that returns empty data and can be
wired up when eToro credentials are available.

Registered automatically when this module is imported by app/main.py.
"""

from __future__ import annotations

from app.brokers.base import IBrokerAdapter
from app.brokers.registry import registry
from app.core.config import get_settings
from app.core.logger import get_logger
from app.models.portfolio import Holding, Position, Trade

logger = get_logger(__name__)


class EToroAdapter(IBrokerAdapter):
    """Broker adapter for eToro (stub — extend when API credentials are available)."""

    @property
    def broker_id(self) -> str:
        return "etoro"

    @property
    def display_name(self) -> str:
        return "eToro"

    def is_configured(self) -> bool:
        return bool(get_settings().etoro_api_key)

    # ── Portfolio data ────────────────────────────────────────────────────

    def get_holdings(self) -> list[Holding]:
        """
        TODO: implement when eToro API access is available.
        Map eToro portfolio positions to Holding models here.
        """
        logger.info("eToro adapter: get_holdings() — returning stub empty list")
        return []

    def get_positions(self) -> list[Position]:
        """
        TODO: implement when eToro API access is available.
        Map eToro open trades to Position models here.
        """
        logger.info("eToro adapter: get_positions() — returning stub empty list")
        return []

    def get_trades(self) -> list[Trade]:
        """
        TODO: implement when eToro API access is available.
        Map eToro trade history to Trade models here.
        """
        logger.info("eToro adapter: get_trades() — returning stub empty list")
        return []


# ── Self-register ──────────────────────────────────────────────────────────────
registry.register(EToroAdapter())
