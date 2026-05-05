"""
Market data domain models.

Typed dataclasses for all entities returned by the Upstox Analytics APIs.
No ORM, no serialization magic — plain Python dataclasses with computed
properties where useful.

Phase 2 extension points (marked below):
  - Add `Candle.adjusted_close` for corporate-action-adjusted candles.
  - Add `Quote.depth` (full 5-level order book) once needed.
  - Add `OptionChainEntry.iv_skew` for volatility skew analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Real-time price quotes
# ---------------------------------------------------------------------------


@dataclass
class Quote:
    """
    Full market quote from ``GET /v2/market-quote/quotes``.

    Contains OHLC, volume, top-of-book depth, circuit limits, and 52-week range.
    """

    instrument_token: str
    trading_symbol: str
    exchange: str
    last_price: float
    open_price: float
    high_price: float
    low_price: float
    close_price: float          # Previous close
    volume: int
    average_price: float
    bid_price: float
    ask_price: float
    bid_qty: int
    ask_qty: int
    total_buy_qty: int
    total_sell_qty: int
    lower_circuit_limit: float
    upper_circuit_limit: float
    week_52_high: float
    week_52_low: float
    net_change: float           # Absolute change from prev close
    net_change_pct: float       # Percentage change from prev close

    @property
    def is_upper_circuit(self) -> bool:
        """True if LTP has hit the upper circuit limit."""
        return self.last_price >= self.upper_circuit_limit

    @property
    def is_lower_circuit(self) -> bool:
        """True if LTP has hit the lower circuit limit."""
        return self.last_price <= self.lower_circuit_limit


@dataclass
class OHLCQuote:
    """
    OHLC quote from ``GET /v3/market-quote/ohlc``.

    Lightweight — contains only OHLC and the last price.
    """

    instrument_token: str
    trading_symbol: str
    last_price: float
    open_price: float
    high_price: float
    low_price: float
    close_price: float          # Previous close

    @property
    def intraday_range(self) -> float:
        """High - Low for the current session."""
        return self.high_price - self.low_price

    @property
    def change_from_open(self) -> float:
        """Absolute change of LTP from today's open."""
        return self.last_price - self.open_price


@dataclass
class LTPQuote:
    """
    Last Traded Price quote from ``GET /v3/market-quote/ltp``.

    Minimal payload — use when you only need the current price.
    """

    instrument_token: str
    trading_symbol: str
    last_price: float


# ---------------------------------------------------------------------------
# Historical candle data
# ---------------------------------------------------------------------------


@dataclass
class Candle:
    """
    Single OHLCV candle from ``GET /v3/historical-candle/{...}``.

    The Upstox API returns candles as arrays:
    ``[timestamp, open, high, low, close, volume, open_interest]``
    """

    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    open_interest: int

    @property
    def body(self) -> float:
        """Absolute candle body size (|close - open|)."""
        return abs(self.close_price - self.open_price)

    @property
    def is_bullish(self) -> bool:
        """True if close > open."""
        return self.close_price > self.open_price


# ---------------------------------------------------------------------------
# Market status
# ---------------------------------------------------------------------------


@dataclass
class MarketStatusEntry:
    """
    Per-segment trading status from ``GET /v2/market/status``.

    ``trading_status`` values: "open", "closed", "pre_open", "pre_close",
    "post_close", "after_market_orders" (Upstox terminology may vary).
    """

    exchange: str
    segment: str
    trading_status: str

    @property
    def is_open(self) -> bool:
        """True when the segment is actively tradeable."""
        return self.trading_status.lower() == "open"


# ---------------------------------------------------------------------------
# Options data
# ---------------------------------------------------------------------------


@dataclass
class OptionSide:
    """
    One side (call or put) of an option chain entry.

    Used as a nested field inside :class:`OptionChainEntry`.
    """

    instrument_key: str
    trading_symbol: str
    ltp: float
    iv: float               # Implied volatility (%)
    delta: float
    gamma: float
    theta: float
    vega: float
    volume: int
    open_interest: int
    bid_price: float
    ask_price: float
    close_price: float      # Previous close for the option


@dataclass
class OptionChainEntry:
    """
    One strike row in the option chain from ``GET /v2/option/chain``.

    Contains both call and put sides for the same strike and expiry.
    Either side may be None if no contract exists at that strike.
    """

    expiry: str
    strike_price: float
    underlying_spot_price: float
    pcr: float              # Put-Call Ratio (OI based) at this strike
    call: Optional[OptionSide]
    put: Optional[OptionSide]

    @property
    def call_put_oi_diff(self) -> float:
        """
        Difference in open interest: call OI - put OI.
        Positive = more call OI (bullish skew); negative = more put OI (bearish skew).
        """
        call_oi = self.call.open_interest if self.call else 0
        put_oi = self.put.open_interest if self.put else 0
        return float(call_oi - put_oi)


@dataclass
class OptionGreeks:
    """
    Option Greeks for a single contract from ``GET /v2/option/greeks``.
    """

    instrument_token: str
    trading_symbol: str
    expiry: str
    strike_price: float
    option_type: str        # "CE" or "PE"
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    iv: float               # Implied volatility (%)
    theoretical_price: float


@dataclass
class OptionContract:
    """
    Option contract specification from ``GET /v2/option/contract``.
    """

    instrument_key: str
    trading_symbol: str
    exchange: str
    strike_price: float
    expiry: str
    option_type: str        # "CE" or "PE"
    lot_size: int
    underlying: str
    underlying_key: str


# ---------------------------------------------------------------------------
# Instrument search
# ---------------------------------------------------------------------------


@dataclass
class InstrumentSearchResult:
    """
    Search result from ``GET /v3/instruments/search``.
    """

    instrument_key: str
    trading_symbol: str
    exchange: str
    instrument_type: str    # "EQUITY", "FUTURES", "OPTIONS", "INDEX", etc.
    name: str
    isin: Optional[str] = None
    lot_size: int = 1


# ---------------------------------------------------------------------------
# Market data feed
# ---------------------------------------------------------------------------


@dataclass
class MarketFeedAuthorization:
    """
    WebSocket authorization from ``GET /v3/feed/market-data-feed/authorize``.

    ``authorized_redirect_uri`` is a signed WSS URL valid for a short window.
    Connect to it with any WebSocket client to receive real-time Level-1
    and Level-2 market data.
    """

    authorized_redirect_uri: str


# ---------------------------------------------------------------------------
# Charges
# ---------------------------------------------------------------------------


@dataclass
class BrokerageDetail:
    """
    Brokerage and statutory charges from ``GET /v2/charges/brokerage``.
    """

    instrument_token: str
    trade_value: float
    brokerage: float
    stt_ctt: float
    exchange_transaction_charges: float
    gst: float
    sebi_charges: float
    stamp_duty: float
    total_charges: float

    @property
    def net_cost(self) -> float:
        """Total outflow = trade value + all charges."""
        return self.trade_value + self.total_charges

    @property
    def effective_rate_pct(self) -> float:
        """All-in charges as a % of trade value."""
        if self.trade_value == 0:
            return 0.0
        return (self.total_charges / self.trade_value) * 100


@dataclass
class MarginDetail:
    """
    Margin requirement from ``POST /v2/charges/margin``.
    """

    required_margin: float
    final_margin: float
    span_margin: float
    exposure_margin: float
    available_margin: float
    total_margin: float
    is_margin_sufficient: bool = field(init=False)

    def __post_init__(self) -> None:
        self.is_margin_sufficient = self.available_margin >= self.final_margin
