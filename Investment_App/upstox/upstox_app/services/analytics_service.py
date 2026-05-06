"""
Analytics service.

Fetches market data from Upstox Analytics APIs via AnalyticsClient and
normalizes responses into typed domain models.

Design notes
------------
- AnalyticsClient is injected → easy to mock in tests.
- Short TTL cache (60 s default) avoids duplicate calls within one session
  while respecting that prices change frequently.
- Static _normalize_* methods are pure and independently testable.
- Real-time data (LTP, quotes) should use cache_ttl=0 in production if
  absolute freshness is required.
"""

import time
from datetime import datetime
from typing import Any, Optional
from urllib.parse import quote as url_quote

from upstox_app.api.analytics_client import AnalyticsClient
from upstox_app.core.logger import get_logger
from upstox_app.models.market_data import (
    BrokerageDetail,
    Candle,
    InstrumentSearchResult,
    LTPQuote,
    MarginDetail,
    MarketFeedAuthorization,
    MarketStatusEntry,
    OHLCQuote,
    OptionChainEntry,
    OptionContract,
    OptionGreeks,
    OptionSide,
    Quote,
)

logger = get_logger(__name__)


class AnalyticsService:
    """
    Market data and analytics service backed by the Upstox Analytics Token.

    All methods return typed domain models.  No trading operations are
    supported — this service is strictly read-only.

    Args:
        client:    An initialized :class:`~app.api.analytics_client.AnalyticsClient`.
        cache_ttl: Response cache TTL in seconds.  Use 0 to disable.
                   Default is 60 s — suitable for most market-data use cases.
    """

    def __init__(self, client: AnalyticsClient, cache_ttl: int = 60) -> None:
        self._client = client
        self._cache_ttl = cache_ttl
        self._cache: dict[str, tuple[float, Any]] = {}

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    def _cached(self, key: str, fetch_fn) -> Any:
        if self._cache_ttl > 0:
            now = time.monotonic()
            entry = self._cache.get(key)
            if entry:
                ts, data = entry
                if now - ts < self._cache_ttl:
                    logger.debug("Analytics cache hit: %s", key)
                    return data
        data = fetch_fn()
        if self._cache_ttl > 0:
            self._cache[key] = (time.monotonic(), data)
        return data

    def invalidate_cache(self) -> None:
        """Clear all cached responses."""
        self._cache.clear()
        logger.debug("Analytics cache invalidated.")

    # ------------------------------------------------------------------
    # Full market quotes  —  GET /v2/market-quote/quotes
    # ------------------------------------------------------------------

    def get_quotes(self, instrument_keys: list[str]) -> list[Quote]:
        """
        Return full market quotes (OHLCV + depth + circuit limits).

        Args:
            instrument_keys: List of Upstox instrument keys, e.g.
                             ``["NSE_EQ|INE009A01021", "BSE_EQ|INE009A01021"]``.

        Returns:
            List of :class:`~app.models.market_data.Quote` objects.
        """
        key_str = ",".join(sorted(instrument_keys))
        cache_key = f"quotes:{key_str}"
        return self._cached(
            cache_key,
            lambda: self._fetch_quotes(instrument_keys),
        )

    def _fetch_quotes(self, instrument_keys: list[str]) -> list[Quote]:
        logger.info("Fetching full quotes for %d instrument(s).", len(instrument_keys))
        response = self._client.get(
            "/v2/market-quote/quotes",
            params={"instrument_key": ",".join(instrument_keys)},
        )
        raw: dict = response.get("data") or {}
        quotes = [self._normalize_quote(token, data) for token, data in raw.items()]
        logger.info("Received %d quote(s).", len(quotes))
        return quotes

    @staticmethod
    def _normalize_quote(instrument_token: str, raw: dict) -> Quote:
        ohlc = raw.get("ohlc") or {}
        depth = raw.get("depth") or {}
        buy_depth: list = (depth.get("buy") or [{}])
        sell_depth: list = (depth.get("sell") or [{}])
        last_price = float(raw.get("last_price", 0.0))
        close_price = float(ohlc.get("close", 0.0))

        return Quote(
            instrument_token=instrument_token,
            trading_symbol=raw.get("symbol", raw.get("trading_symbol", "")),
            exchange=raw.get("exchange", ""),
            last_price=last_price,
            open_price=float(ohlc.get("open", 0.0)),
            high_price=float(ohlc.get("high", 0.0)),
            low_price=float(ohlc.get("low", 0.0)),
            close_price=close_price,
            volume=int(raw.get("volume", 0)),
            average_price=float(raw.get("average_price", 0.0)),
            bid_price=float((buy_depth[0] if buy_depth else {}).get("price", 0.0)),
            ask_price=float((sell_depth[0] if sell_depth else {}).get("price", 0.0)),
            bid_qty=int((buy_depth[0] if buy_depth else {}).get("quantity", 0)),
            ask_qty=int((sell_depth[0] if sell_depth else {}).get("quantity", 0)),
            total_buy_qty=int(raw.get("total_buy_quantity", 0)),
            total_sell_qty=int(raw.get("total_sell_quantity", 0)),
            lower_circuit_limit=float(raw.get("lower_circuit_limit", 0.0)),
            upper_circuit_limit=float(raw.get("upper_circuit_limit", 0.0)),
            week_52_high=float(raw.get("52_week_high", 0.0)),
            week_52_low=float(raw.get("52_week_low", 0.0)),
            net_change=float(raw.get("net_change", 0.0)),
            net_change_pct=(
                ((last_price - close_price) / close_price * 100) if close_price else 0.0
            ),
        )

    # ------------------------------------------------------------------
    # OHLC quotes V3  —  GET /v3/market-quote/ohlc
    # ------------------------------------------------------------------

    def get_ohlc(
        self,
        instrument_keys: list[str],
        interval: str = "1d",
    ) -> list[OHLCQuote]:
        """
        Return OHLC quotes.

        Args:
            instrument_keys: Upstox instrument keys.
            interval:        Candle interval, e.g. ``"1d"``, ``"30minute"``.

        Returns:
            List of :class:`~app.models.market_data.OHLCQuote`.
        """
        key_str = ",".join(sorted(instrument_keys))
        cache_key = f"ohlc:{interval}:{key_str}"
        return self._cached(
            cache_key,
            lambda: self._fetch_ohlc(instrument_keys, interval),
        )

    def _fetch_ohlc(self, instrument_keys: list[str], interval: str) -> list[OHLCQuote]:
        logger.info("Fetching OHLC (%s) for %d instrument(s).", interval, len(instrument_keys))
        response = self._client.get(
            "/v3/market-quote/ohlc",
            params={"instrument_key": ",".join(instrument_keys), "interval": interval},
        )
        raw: dict = response.get("data") or {}
        return [self._normalize_ohlc(token, data) for token, data in raw.items()]

    @staticmethod
    def _normalize_ohlc(instrument_token: str, raw: dict) -> OHLCQuote:
        # V3 response uses live_ohlc; fall back to ohlc for older payloads
        ohlc = raw.get("live_ohlc") or raw.get("ohlc") or {}
        # V3 doesn't return a symbol field; derive it from the response key
        # e.g. "NSE_EQ:INFY" → "INFY", "NSE_FO:NIFTY2543021600PE" → "NIFTY2543021600PE"
        symbol = (
            raw.get("symbol")
            or raw.get("trading_symbol")
            or instrument_token.split(":")[-1]
        )
        return OHLCQuote(
            instrument_token=instrument_token,
            trading_symbol=symbol,
            last_price=float(raw.get("last_price", 0.0)),
            open_price=float(ohlc.get("open", 0.0)),
            high_price=float(ohlc.get("high", 0.0)),
            low_price=float(ohlc.get("low", 0.0)),
            close_price=float(ohlc.get("close", 0.0)),
        )

    # ------------------------------------------------------------------
    # LTP quotes V3  —  GET /v3/market-quote/ltp
    # ------------------------------------------------------------------

    def get_ltp(self, instrument_keys: list[str]) -> list[LTPQuote]:
        """
        Return last traded prices — the lightest payload available.

        Args:
            instrument_keys: Upstox instrument keys.

        Returns:
            List of :class:`~app.models.market_data.LTPQuote`.
        """
        key_str = ",".join(sorted(instrument_keys))
        cache_key = f"ltp:{key_str}"
        return self._cached(
            cache_key,
            lambda: self._fetch_ltp(instrument_keys),
        )

    def _fetch_ltp(self, instrument_keys: list[str]) -> list[LTPQuote]:
        logger.info("Fetching LTP for %d instrument(s).", len(instrument_keys))
        response = self._client.get(
            "/v3/market-quote/ltp",
            params={"instrument_key": ",".join(instrument_keys)},
        )
        raw: dict = response.get("data") or {}
        return [self._normalize_ltp(token, data) for token, data in raw.items()]

    @staticmethod
    def _normalize_ltp(instrument_token: str, raw: dict) -> LTPQuote:
        return LTPQuote(
            instrument_token=instrument_token,
            trading_symbol=raw.get("symbol", raw.get("trading_symbol", "")),
            last_price=float(raw.get("last_price", 0.0)),
        )

    # ------------------------------------------------------------------
    # Historical candle data V3
    # GET /v3/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}
    # ------------------------------------------------------------------

    def get_historical_candles(
        self,
        instrument_key: str,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> list[Candle]:
        """
        Return historical OHLCV candles.

        Args:
            instrument_key: Upstox instrument key, e.g. ``NSE_EQ|INE009A01021``.
            interval:       Candle size: ``"1minute"``, ``"30minute"``, ``"day"``,
                            ``"week"``, ``"month"``.
            from_date:      Start date in ``YYYY-MM-DD`` format.
            to_date:        End date in ``YYYY-MM-DD`` format.

        Returns:
            List of :class:`~app.models.market_data.Candle`, oldest first.
        """
        cache_key = f"candles:{instrument_key}:{interval}:{from_date}:{to_date}"
        return self._cached(
            cache_key,
            lambda: self._fetch_candles(instrument_key, interval, from_date, to_date),
        )

    def _fetch_candles(
        self, instrument_key: str, interval: str, from_date: str, to_date: str
    ) -> list[Candle]:
        logger.info(
            "Fetching %s candles for %s (%s → %s).",
            interval,
            instrument_key,
            from_date,
            to_date,
        )
        # The instrument key contains '|' which must be URL-encoded in the path
        encoded_key = url_quote(instrument_key, safe="")
        path = f"/v3/historical-candle/{encoded_key}/{interval}/{to_date}/{from_date}"
        response = self._client.get(path)
        raw_candles: list = (response.get("data") or {}).get("candles") or []
        candles = [self._normalize_candle(c) for c in raw_candles]
        # Upstox returns newest-first; reverse for chronological order
        candles.reverse()
        logger.info("Received %d candle(s).", len(candles))
        return candles

    @staticmethod
    def _normalize_candle(row: list) -> Candle:
        """
        Convert a raw candle array to a Candle model.

        Upstox format: [timestamp, open, high, low, close, volume, open_interest]
        """
        ts_raw = row[0] if len(row) > 0 else ""
        try:
            # Handle ISO strings like "2026-05-05T09:15:00+05:30"
            ts = datetime.fromisoformat(str(ts_raw))
        except (ValueError, TypeError):
            ts = datetime.min

        return Candle(
            timestamp=ts,
            open_price=float(row[1]) if len(row) > 1 else 0.0,
            high_price=float(row[2]) if len(row) > 2 else 0.0,
            low_price=float(row[3]) if len(row) > 3 else 0.0,
            close_price=float(row[4]) if len(row) > 4 else 0.0,
            volume=int(row[5]) if len(row) > 5 else 0,
            open_interest=int(row[6]) if len(row) > 6 else 0,
        )

    # ------------------------------------------------------------------
    # Market Data Feed Authorization V3
    # GET /v3/feed/market-data-feed/authorize
    # ------------------------------------------------------------------

    def authorize_market_feed(self) -> MarketFeedAuthorization:
        """
        Obtain a signed WebSocket URL for the V3 Market Data Feed.

        The returned ``authorized_redirect_uri`` is a ``wss://`` URL valid
        for a short window.  Connect to it with any WebSocket client to
        receive real-time streaming market data.

        Returns:
            :class:`~app.models.market_data.MarketFeedAuthorization` with the WSS URL.
        """
        logger.info("Authorizing Market Data Feed V3...")
        response = self._client.get("/v3/feed/market-data-feed/authorize")
        data = response.get("data") or {}
        uri = data.get("authorized_redirect_uri", "")
        return MarketFeedAuthorization(authorized_redirect_uri=uri)

    # ------------------------------------------------------------------
    # Market status  —  GET /v2/market/status
    # ------------------------------------------------------------------

    def get_market_status(
        self, exchange: Optional[str] = None
    ) -> list[MarketStatusEntry]:
        """
        Return current trading status for all segments (or a specific exchange).

        Args:
            exchange: Optional exchange filter, e.g. ``"NSE"``, ``"BSE"``.

        Returns:
            List of :class:`~app.models.market_data.MarketStatusEntry`.
        """
        cache_key = f"market_status:{exchange or 'all'}"
        return self._cached(
            cache_key,
            lambda: self._fetch_market_status(exchange),
        )

    def _fetch_market_status(self, exchange: Optional[str]) -> list[MarketStatusEntry]:
        logger.info("Fetching market status (exchange=%s).", exchange or "all")
        params = {"exchange": exchange} if exchange else None
        response = self._client.get("/v2/market/status", params=params)
        markets: list = (response.get("data") or {}).get("markets") or []
        return [self._normalize_market_status(m) for m in markets]

    @staticmethod
    def _normalize_market_status(raw: dict) -> MarketStatusEntry:
        return MarketStatusEntry(
            exchange=raw.get("exchange", ""),
            segment=raw.get("segment", ""),
            trading_status=raw.get("trading_status", ""),
        )

    # ------------------------------------------------------------------
    # Option chain  —  GET /v2/option/chain
    # ------------------------------------------------------------------

    def get_option_chain(
        self, instrument_key: str, expiry_date: str
    ) -> list[OptionChainEntry]:
        """
        Return the full Put/Call option chain for an underlying and expiry.

        Args:
            instrument_key: Underlying instrument key, e.g. ``NSE_INDEX|Nifty 50``.
            expiry_date:    Expiry in ``YYYY-MM-DD`` format.

        Returns:
            List of :class:`~app.models.market_data.OptionChainEntry`, one per strike.
        """
        cache_key = f"option_chain:{instrument_key}:{expiry_date}"
        return self._cached(
            cache_key,
            lambda: self._fetch_option_chain(instrument_key, expiry_date),
        )

    def _fetch_option_chain(
        self, instrument_key: str, expiry_date: str
    ) -> list[OptionChainEntry]:
        logger.info("Fetching option chain for %s expiry %s.", instrument_key, expiry_date)
        response = self._client.get(
            "/v2/option/chain",
            params={"instrument_key": instrument_key, "expiry_date": expiry_date},
        )
        raw_entries: list = response.get("data") or []
        entries = [self._normalize_chain_entry(e) for e in raw_entries]
        logger.info("Received %d strike(s).", len(entries))
        return entries

    @staticmethod
    def _normalize_option_side(raw_side: Optional[dict]) -> Optional[OptionSide]:
        if not raw_side:
            return None
        mkt = raw_side.get("market_data") or {}
        greeks = raw_side.get("option_greeks") or {}
        return OptionSide(
            instrument_key=raw_side.get("instrument_key", ""),
            trading_symbol=raw_side.get("trading_symbol", ""),
            ltp=float(mkt.get("ltp", 0.0)),
            iv=float(greeks.get("iv", 0.0)),
            delta=float(greeks.get("delta", 0.0)),
            gamma=float(greeks.get("gamma", 0.0)),
            theta=float(greeks.get("theta", 0.0)),
            vega=float(greeks.get("vega", 0.0)),
            volume=int(mkt.get("volume", 0)),
            open_interest=int(mkt.get("oi", 0)),
            bid_price=float(mkt.get("bid_price", 0.0)),
            ask_price=float(mkt.get("ask_price", 0.0)),
            close_price=float(mkt.get("close_price", 0.0)),
        )

    @classmethod
    def _normalize_chain_entry(cls, raw: dict) -> OptionChainEntry:
        return OptionChainEntry(
            expiry=raw.get("expiry", ""),
            strike_price=float(raw.get("strike_price", 0.0)),
            underlying_spot_price=float(raw.get("underlying_spot_price", 0.0)),
            pcr=float(raw.get("pcr", 0.0)),
            call=cls._normalize_option_side(raw.get("call_options")),
            put=cls._normalize_option_side(raw.get("put_options")),
        )

    # ------------------------------------------------------------------
    # Option contracts  —  GET /v2/option/contract
    # ------------------------------------------------------------------

    def get_option_contracts(
        self, instrument_key: str, expiry_date: Optional[str] = None
    ) -> list[OptionContract]:
        """
        Return tradeable option contracts for an underlying.

        Args:
            instrument_key: Underlying instrument key.
            expiry_date:    Optional expiry filter (``YYYY-MM-DD``).

        Returns:
            List of :class:`~app.models.market_data.OptionContract`.
        """
        cache_key = f"option_contracts:{instrument_key}:{expiry_date or 'all'}"
        return self._cached(
            cache_key,
            lambda: self._fetch_option_contracts(instrument_key, expiry_date),
        )

    def _fetch_option_contracts(
        self, instrument_key: str, expiry_date: Optional[str]
    ) -> list[OptionContract]:
        logger.info("Fetching option contracts for %s.", instrument_key)
        params: dict = {"instrument_key": instrument_key}
        if expiry_date:
            params["expiry_date"] = expiry_date
        response = self._client.get("/v2/option/contract", params=params)
        raw: list = response.get("data") or []
        return [self._normalize_contract(c) for c in raw]

    @staticmethod
    def _normalize_contract(raw: dict) -> OptionContract:
        return OptionContract(
            instrument_key=raw.get("instrument_key", ""),
            trading_symbol=raw.get("trading_symbol", ""),
            exchange=raw.get("exchange", ""),
            strike_price=float(raw.get("strike_price", 0.0)),
            expiry=raw.get("expiry", ""),
            option_type=raw.get("option_type", ""),
            lot_size=int(raw.get("lot_size", 0)),
            underlying=raw.get("underlying", ""),
            underlying_key=raw.get("underlying_key", ""),
        )

    # ------------------------------------------------------------------
    # Option Greeks  —  GET /v2/option/greeks
    # ------------------------------------------------------------------

    def get_option_greeks(
        self, instrument_key: str, expiry_date: str
    ) -> list[OptionGreeks]:
        """
        Return option Greeks for all contracts of an underlying and expiry.

        Args:
            instrument_key: Underlying instrument key.
            expiry_date:    Expiry date in ``YYYY-MM-DD`` format.

        Returns:
            List of :class:`~app.models.market_data.OptionGreeks`.
        """
        cache_key = f"greeks:{instrument_key}:{expiry_date}"
        return self._cached(
            cache_key,
            lambda: self._fetch_greeks(instrument_key, expiry_date),
        )

    def _fetch_greeks(self, instrument_key: str, expiry_date: str) -> list[OptionGreeks]:
        logger.info("Fetching option Greeks for %s expiry %s.", instrument_key, expiry_date)
        response = self._client.get(
            "/v2/option/greeks",
            params={"instrument_key": instrument_key, "expiry_date": expiry_date},
        )
        raw: list = response.get("data") or []
        return [self._normalize_greeks(g) for g in raw]

    @staticmethod
    def _normalize_greeks(raw: dict) -> OptionGreeks:
        return OptionGreeks(
            instrument_token=raw.get("instrument_token", ""),
            trading_symbol=raw.get("trading_symbol", ""),
            expiry=raw.get("expiry", ""),
            strike_price=float(raw.get("strike_price", 0.0)),
            option_type=raw.get("option_type", ""),
            delta=float(raw.get("delta", 0.0)),
            gamma=float(raw.get("gamma", 0.0)),
            theta=float(raw.get("theta", 0.0)),
            vega=float(raw.get("vega", 0.0)),
            rho=float(raw.get("rho", 0.0)),
            iv=float(raw.get("iv", 0.0)),
            theoretical_price=float(raw.get("theoretical_price", 0.0)),
        )

    # ------------------------------------------------------------------
    # Brokerage details  —  GET /v2/charges/brokerage
    # ------------------------------------------------------------------

    def get_brokerage(
        self,
        instrument_token: str,
        quantity: int,
        price: float,
        product: str,
        transaction_type: str,
        exchange: str,
    ) -> BrokerageDetail:
        """
        Calculate brokerage and statutory charges for a hypothetical trade.

        Args:
            instrument_token: Instrument key/token.
            quantity:         Number of shares / units.
            price:            Trade price per unit.
            product:          ``"D"`` (Delivery), ``"I"`` (Intraday), ``"CO"``, ``"OCO"``.
            transaction_type: ``"BUY"`` or ``"SELL"``.
            exchange:         ``"NSE"``, ``"BSE"``, etc.

        Returns:
            :class:`~app.models.market_data.BrokerageDetail` with all charges.
        """
        logger.info(
            "Calculating brokerage: %s %d × %.2f on %s.",
            transaction_type,
            quantity,
            price,
            instrument_token,
        )
        response = self._client.get(
            "/v2/charges/brokerage",
            params={
                "instrument_token": instrument_token,
                "quantity": quantity,
                "price": price,
                "product": product,
                "transaction_type": transaction_type,
                "exchange": exchange,
            },
        )
        data = response.get("data") or {}
        charges = data.get("charges") or {}
        return BrokerageDetail(
            instrument_token=instrument_token,
            trade_value=float(data.get("trade_value", price * quantity)),
            brokerage=float(charges.get("brokerage", 0.0)),
            stt_ctt=float(charges.get("stt", 0.0)),
            exchange_transaction_charges=float(
                charges.get("exchange_transaction_charges", 0.0)
            ),
            gst=float(charges.get("gst", 0.0)),
            sebi_charges=float(charges.get("sebi_charges", 0.0)),
            stamp_duty=float(charges.get("stamp_duty", 0.0)),
            total_charges=float(charges.get("total", 0.0)),
        )

    # ------------------------------------------------------------------
    # Margin details  —  POST /v2/charges/margin
    # ------------------------------------------------------------------

    def calculate_margin(self, orders: list[dict]) -> MarginDetail:
        """
        Calculate margin required for a list of hypothetical orders.

        Each order dict should contain:
            ``exchange``, ``instrument_token``, ``quantity``, ``price``,
            ``product``, ``transaction_type``.

        Args:
            orders: List of order parameter dicts.

        Returns:
            :class:`~app.models.market_data.MarginDetail`.
        """
        logger.info("Calculating margin for %d order(s).", len(orders))
        response = self._client.post("/v2/charges/margin", body=orders)
        data = response.get("data") or {}
        return MarginDetail(
            required_margin=float(data.get("required_margin", 0.0)),
            final_margin=float(data.get("final_margin", 0.0)),
            span_margin=float(data.get("span_margin", 0.0)),
            exposure_margin=float(data.get("exposure_margin", 0.0)),
            available_margin=float(data.get("available_margin", 0.0)),
            total_margin=float(data.get("total_margin", 0.0)),
        )

    # ------------------------------------------------------------------
    # Instrument search V3  —  GET /v3/instruments/search
    # ------------------------------------------------------------------

    def search_instruments(
        self,
        query: str,
        asset_type: Optional[str] = None,
    ) -> list[InstrumentSearchResult]:
        """
        Search for instruments by name, symbol, or ISIN.

        Args:
            query:      Search term, e.g. ``"RELIANCE"``, ``"INE002A01018"``.
            asset_type: Optional filter: ``"equity"``, ``"futures"``, ``"options"``, etc.

        Returns:
            List of :class:`~app.models.market_data.InstrumentSearchResult`.
        """
        logger.info("Searching instruments: query=%s asset_type=%s.", query, asset_type)
        params: dict = {"query": query}
        if asset_type:
            params["asset_type"] = asset_type
        response = self._client.get("/v3/instruments/search", params=params)
        raw: list = response.get("data") or []
        return [self._normalize_search_result(r) for r in raw]

    @staticmethod
    def _normalize_search_result(raw: dict) -> InstrumentSearchResult:
        return InstrumentSearchResult(
            instrument_key=raw.get("instrument_key", ""),
            trading_symbol=raw.get("trading_symbol", ""),
            exchange=raw.get("exchange", ""),
            instrument_type=raw.get("instrument_type", ""),
            name=raw.get("name", ""),
            isin=raw.get("isin") or None,
            lot_size=int(raw.get("lot_size", 1)),
        )
