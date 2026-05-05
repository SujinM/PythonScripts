"""
app/brokers/upstox.py
─────────────────────
UpstoxAdapter — delegates ALL HTTP and normalisation work to the
upstox_app library (Investment_App/upstox/upstox_app/).

Architecture
────────────
  BackendFastAPI UpstoxAdapter
        │
        ├─ upstox_app.api.upstox_client.UpstoxClient   (HTTP + OAuth2 + retry)
        ├─ upstox_app.services.portfolio_service.PortfolioService  (fetch + cache + normalise)
        └─ upstox_app.models.portfolio.*               (Holding, Position, Trade dataclasses)
                │
                ▼  converted to BackendFastAPI Pydantic models
  app.models.portfolio.Holding / Position / Trade

Adding a new broker: create a new file in app/brokers/ — no other changes.
"""

from __future__ import annotations

import upstox_app.models.portfolio as _um
from upstox_app.api.upstox_client import UpstoxAPIError
from upstox_app.api.upstox_client import UpstoxAuthError as _UpstoxAuthError
from upstox_app.api.upstox_client import UpstoxClient
from upstox_app.services.portfolio_service import PortfolioService as _UpstoxPortfolioService

from app.brokers.base import IBrokerAdapter
from app.brokers.registry import registry
from app.core.config import get_settings
from app.core.exceptions import BrokerAuthError, BrokerError
from app.core.logger import get_logger
from app.models.portfolio import Holding, Position, Trade

logger = get_logger(__name__)


# ── Config bridge ─────────────────────────────────────────────────────────────

class _SettingsConfig:
    """
    Adapts BackendFastAPI's Settings into the interface expected by
    upstox_app's UpstoxClient (api_key, api_secret, redirect_uri,
    access_token, base_url properties).
    """

    def __init__(self) -> None:
        s = get_settings()
        self._api_key = s.upstox_api_key
        self._api_secret = s.upstox_api_secret
        self._redirect_uri = s.upstox_redirect_uri
        self._access_token = s.upstox_access_token or None
        self._base_url = s.upstox_base_url

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def api_secret(self) -> str:
        return self._api_secret

    @property
    def redirect_uri(self) -> str:
        return self._redirect_uri

    @property
    def access_token(self) -> str | None:
        return self._access_token

    @property
    def base_url(self) -> str:
        return self._base_url


# ── Model converters ──────────────────────────────────────────────────────────

def _to_holding(h: _um.Holding) -> Holding:
    return Holding(
        broker="upstox",
        instrument_key=h.instrument_token,
        trading_symbol=h.trading_symbol,
        exchange=h.exchange,
        isin=h.isin,
        quantity=float(h.quantity),
        average_price=h.average_price,
        last_price=h.last_price,
        close_price=h.close_price,
    )


def _to_position(p: _um.Position) -> Position:
    return Position(
        broker="upstox",
        instrument_key=p.instrument_token,
        trading_symbol=p.trading_symbol,
        exchange=p.exchange,
        product=p.product,
        quantity=p.quantity,
        buy_price=p.buy_price,
        sell_price=p.sell_price,
        last_price=p.buy_price,  # upstox Position has no separate last_price field
        realised_pnl=p.realised,
        unrealised_pnl=p.unrealised,
    )


def _to_trade(t: _um.Trade) -> Trade:
    return Trade(
        broker="upstox",
        instrument_key=t.instrument_token,
        trading_symbol=t.trading_symbol,
        exchange=t.exchange,
        product=t.product,
        transaction_type=t.transaction_type,
        quantity=float(t.quantity),
        price=t.price,
        trade_date=t.trade_date,
    )


# ── Adapter ───────────────────────────────────────────────────────────────────

class UpstoxAdapter(IBrokerAdapter):
    """
    Broker adapter for Upstox.

    Uses upstox_app's UpstoxClient (requests + retry) and PortfolioService
    (normalisation) under the hood.  BackendFastAPI's own TTL cache sits above
    this layer, so cache_ttl=0 is passed to the inner PortfolioService.
    """

    @property
    def broker_id(self) -> str:
        return "upstox"

    @property
    def display_name(self) -> str:
        return "Upstox"

    def is_configured(self) -> bool:
        return bool(get_settings().upstox_access_token)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _build_service(self) -> _UpstoxPortfolioService:
        """Construct an authenticated PortfolioService from current settings."""
        config = _SettingsConfig()
        if not config.access_token:
            raise BrokerAuthError(self.broker_id, "UPSTOX_ACCESS_TOKEN is not set")
        client = UpstoxClient(config)
        client.set_access_token(config.access_token)
        return _UpstoxPortfolioService(client, cache_ttl=0)

    def _raise(self, exc: UpstoxAPIError) -> None:
        """Convert upstox_app exceptions to BackendFastAPI exceptions."""
        if isinstance(exc, _UpstoxAuthError):
            raise BrokerAuthError(self.broker_id, str(exc)) from exc
        raise BrokerError(self.broker_id, str(exc), status_code=exc.status_code) from exc

    # ── Portfolio data ────────────────────────────────────────────────────

    def get_holdings(self) -> list[Holding]:
        try:
            return [_to_holding(h) for h in self._build_service().get_holdings()]
        except UpstoxAPIError as exc:
            self._raise(exc)
            return []  # unreachable

    def get_positions(self) -> list[Position]:
        try:
            return [_to_position(p) for p in self._build_service().get_positions()]
        except UpstoxAPIError as exc:
            self._raise(exc)
            return []

    def get_trades(self) -> list[Trade]:
        try:
            return [_to_trade(t) for t in self._build_service().get_trades()]
        except UpstoxAPIError as exc:
            self._raise(exc)
            return []


# ── Self-register ──────────────────────────────────────────────────────────────
registry.register(UpstoxAdapter())
