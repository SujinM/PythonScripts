"""
app/brokers/etoro.py
────────────────────
EToroAdapter — delegates all HTTP and normalisation work to the
etoro_app library (Investment_App/etoro/etoro_app/).

Architecture
────────────
  BackendFastAPI EToroAdapter
        │
        ├─ etoro_app.api.etoro_client.EToroClient    (HTTP + API-key headers + retry)
        ├─ etoro_app.services.portfolio_service.PortfolioService  (fetch + cache + normalise)
        └─ etoro_app.models.portfolio.*              (Position, ClosedPosition dataclasses)
                │
                ▼  converted to BackendFastAPI Pydantic models
  app.models.portfolio.Holding / Position / Trade

eToro Public API auth
─────────────────────
  ETORO_API_KEY  (x-api-key header)
  ETORO_USER_KEY (x-user-key header)
  Get from: eToro account → Settings → Trading → API Key Management

eToro mapping
────────────────
  eToro Position        → Holding  (open positions treated as holdings)
  eToro Position        → Position (same data, different context)
  eToro ClosedPosition  → Trade

Adding a new broker: create a new file in app/brokers/ — no other changes.
"""

from __future__ import annotations

import etoro_app.models.portfolio as _em
from etoro_app.api.etoro_client import EToroAPIError
from etoro_app.api.etoro_client import EToroAuthError as _EToroAuthError
from etoro_app.api.etoro_client import EToroClient
from etoro_app.services.portfolio_service import PortfolioService as _EToroPortfolioService

from app.brokers.base import IBrokerAdapter
from app.brokers.registry import registry
from app.core.config import get_settings
from app.core.debug_flags import is_portfolio_trace
from app.core.exceptions import BrokerAuthError, BrokerError
from app.core.logger import get_logger
from app.models.portfolio import Holding, Position, Trade

logger = get_logger(__name__)


# ── Config bridge ─────────────────────────────────────────────────────────────


class _SettingsConfig:
    """
    Adapts BackendFastAPI's Settings into the interface expected by
    etoro_app's Config (api_key, user_key, base_url properties).
    """

    def __init__(self) -> None:
        s = get_settings()
        self._api_key = s.etoro_api_key
        self._user_key = s.etoro_user_key
        self._base_url = s.etoro_base_url

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def user_key(self) -> str:
        return self._user_key

    @property
    def base_url(self) -> str:
        return self._base_url


# ── Model converters ──────────────────────────────────────────────────────────


def _to_holding(p: _em.Position) -> Holding:
    """eToro open Position → unified Holding."""
    h = Holding(
        broker="etoro",
        instrument_key=str(p.instrument_id),
        trading_symbol=p.instrument_name,
        exchange=p.instrument_type,
        isin=None,
        quantity=float(p.units),
        average_price=p.open_rate,
        last_price=p.current_rate,
        close_price=p.current_rate,
        invested_amount=p.amount,     # actual invested USD (not units × open_rate)
        broker_pnl=p.unrealised_pnl,  # eToro P&L includes leverage, fees, overnight
    )
    if is_portfolio_trace():
        logger.info(
            "[TRACE etoro] %-22s | "
            "RAW: amount=%9.2f  units=%9.4f  open_rate=%9.4f  curr_rate=%9.4f  "
            "etoro_pnl=%+10.4f  leverage=%s  "
            "| COMPUTED: invested_value=%9.2f  current_value=%9.2f  "
            "unrealised_pnl=%+10.4f  return_pct=%+8.4f%%",
            p.instrument_name,
            p.amount, float(p.units), p.open_rate, p.current_rate,
            p.unrealised_pnl, getattr(p, "leverage", "?"),
            h.invested_value, h.current_value, h.unrealised_pnl, h.return_pct,
        )
    return h


def _to_position(p: _em.Position) -> Position:
    """eToro open Position → unified Position."""
    return Position(
        broker="etoro",
        instrument_key=str(p.instrument_id),
        trading_symbol=p.instrument_name,
        exchange=p.instrument_type,
        product=f"{p.direction}_{p.leverage}x",
        quantity=int(round(p.units)),
        buy_price=p.open_rate if p.direction == "Buy" else 0.0,
        sell_price=p.open_rate if p.direction == "Sell" else 0.0,
        last_price=p.current_rate,
        realised_pnl=0.0,
        unrealised_pnl=p.unrealised_pnl,
    )


def _to_trade(c: _em.ClosedPosition) -> Trade:
    """eToro ClosedPosition → unified Trade."""
    return Trade(
        broker="etoro",
        instrument_key=str(c.instrument_id),
        trading_symbol=c.instrument_name,
        exchange=c.instrument_type,
        product=f"{c.direction}_{c.leverage}x",
        transaction_type=c.direction.upper(),
        quantity=float(c.units),
        price=c.close_rate,
        trade_date=c.close_date,
    )


# ── Adapter ───────────────────────────────────────────────────────────────────


class EToroAdapter(IBrokerAdapter):
    """
    Broker adapter for eToro.

    Uses etoro_app's EToroClient (requests + retry) and PortfolioService
    (normalisation) under the hood.  BackendFastAPI's own TTL cache sits above
    this layer, so cache_ttl=0 is passed to the inner PortfolioService.
    """

    @property
    def broker_id(self) -> str:
        return "etoro"

    @property
    def display_name(self) -> str:
        return "eToro"

    def is_configured(self) -> bool:
        s = get_settings()
        return bool(s.etoro_api_key and s.etoro_user_key)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _build_service(self) -> _EToroPortfolioService:
        """Construct an authenticated PortfolioService from current settings."""
        config = _SettingsConfig()
        if not config.api_key or not config.user_key:
            raise BrokerAuthError(
                self.broker_id,
                "ETORO_API_KEY and ETORO_USER_KEY must be set. "
                "Get them from: eToro account → Settings → Trading → API Key Management",
            )
        client = EToroClient(config)
        return _EToroPortfolioService(client, cache_ttl=0)

    def _raise(self, exc: EToroAPIError) -> None:
        """Convert etoro_app exceptions to BackendFastAPI exceptions."""
        if isinstance(exc, _EToroAuthError):
            raise BrokerAuthError(self.broker_id, str(exc)) from exc
        raise BrokerError(self.broker_id, str(exc), status_code=exc.status_code) from exc

    # ── Portfolio data ────────────────────────────────────────────────────

    def get_holdings(self) -> list[Holding]:
        """Return open positions treated as long-term holdings."""
        try:
            service = self._build_service()
            return [_to_holding(p) for p in service.get_positions()]
        except EToroAPIError as exc:
            self._raise(exc)
            return []

    def get_positions(self) -> list[Position]:
        """Return open positions."""
        try:
            service = self._build_service()
            return [_to_position(p) for p in service.get_positions()]
        except EToroAPIError as exc:
            self._raise(exc)
            return []

    def get_trades(self) -> list[Trade]:
        """Return closed position history as trades."""
        try:
            service = self._build_service()
            return [_to_trade(c) for c in service.get_closed_positions()]
        except EToroAPIError as exc:
            self._raise(exc)
            return []


# ── Self-register ──────────────────────────────────────────────────────────────
registry.register(EToroAdapter())
