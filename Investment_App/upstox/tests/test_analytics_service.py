"""
Unit tests for AnalyticsService.

All HTTP calls are replaced with mocks — no network I/O.
Tests focus on normalization logic and correct endpoint/parameter usage.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.api.analytics_client import AnalyticsClient
from app.models.market_data import (
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
    Quote,
)
from app.services.analytics_service import AnalyticsService

# ---------------------------------------------------------------------------
# Raw API response stubs
# ---------------------------------------------------------------------------

RAW_QUOTE_DATA = {
    "NSE_EQ|INE009A01021": {
        "symbol": "INFY",
        "exchange": "NSE",
        "last_price": 1650.0,
        "ohlc": {"open": 1620.0, "high": 1660.0, "low": 1610.0, "close": 1600.0},
        "volume": 5_000_000,
        "average_price": 1635.0,
        "depth": {
            "buy": [{"price": 1649.0, "quantity": 100}],
            "sell": [{"price": 1651.0, "quantity": 200}],
        },
        "total_buy_quantity": 500_000,
        "total_sell_quantity": 600_000,
        "lower_circuit_limit": 1440.0,
        "upper_circuit_limit": 1760.0,
        "52_week_high": 1900.0,
        "52_week_low": 1200.0,
        "net_change": 50.0,
    }
}

RAW_OHLC_DATA = {
    "NSE_EQ:INFY": {
        "last_price": 1650.0,
        "live_ohlc": {"open": 1620.0, "high": 1660.0, "low": 1610.0, "close": 1600.0},
    }
}

RAW_LTP_DATA = {
    "NSE_EQ|INE009A01021": {
        "symbol": "INFY",
        "last_price": 1650.0,
    }
}

RAW_CANDLES = [
    ["2026-05-05T09:15:00+05:30", 1620.0, 1660.0, 1610.0, 1650.0, 5_000_000, 0],
    ["2026-05-04T09:15:00+05:30", 1580.0, 1630.0, 1570.0, 1600.0, 4_500_000, 0],
]

RAW_MARKET_STATUS = {
    "markets": [
        {"exchange": "NSE", "segment": "Capital Market", "trading_status": "open"},
        {"exchange": "BSE", "segment": "Equity", "trading_status": "Closed"},
    ]
}

RAW_OPTION_CHAIN = [
    {
        "expiry": "2026-05-29",
        "strike_price": 22000.0,
        "underlying_spot_price": 22500.0,
        "pcr": 1.2,
        "call_options": {
            "instrument_key": "NSE_FO|CE001",
            "trading_symbol": "NIFTY26MAY22000CE",
            "market_data": {
                "ltp": 600.0,
                "volume": 10000,
                "oi": 50000,
                "bid_price": 599.0,
                "ask_price": 601.0,
                "close_price": 580.0,
            },
            "option_greeks": {"delta": 0.6, "gamma": 0.001, "theta": -10.0, "vega": 5.0, "iv": 15.5},
        },
        "put_options": {
            "instrument_key": "NSE_FO|PE001",
            "trading_symbol": "NIFTY26MAY22000PE",
            "market_data": {
                "ltp": 400.0,
                "volume": 12000,
                "oi": 60000,
                "bid_price": 399.0,
                "ask_price": 401.0,
                "close_price": 390.0,
            },
            "option_greeks": {"delta": -0.4, "gamma": 0.001, "theta": -8.0, "vega": 5.0, "iv": 14.2},
        },
    }
]

RAW_GREEKS = [
    {
        "instrument_token": "NSE_FO|CE001",
        "trading_symbol": "NIFTY26MAY22000CE",
        "expiry": "2026-05-29",
        "strike_price": 22000.0,
        "option_type": "CE",
        "delta": 0.6,
        "gamma": 0.001,
        "theta": -10.0,
        "vega": 5.0,
        "rho": 0.02,
        "iv": 15.5,
        "theoretical_price": 605.0,
    }
]

RAW_CONTRACT = [
    {
        "instrument_key": "NSE_FO|CE001",
        "trading_symbol": "NIFTY26MAY22000CE",
        "exchange": "NSE",
        "strike_price": 22000.0,
        "expiry": "2026-05-29",
        "option_type": "CE",
        "lot_size": 50,
        "underlying": "NIFTY",
        "underlying_key": "NSE_INDEX|Nifty 50",
    }
]

RAW_SEARCH = [
    {
        "instrument_key": "NSE_EQ|INE002A01018",
        "trading_symbol": "RELIANCE",
        "exchange": "NSE",
        "instrument_type": "EQUITY",
        "name": "Reliance Industries Limited",
        "isin": "INE002A01018",
        "lot_size": 1,
    }
]

RAW_BROKERAGE = {
    "trade_value": 16500.0,
    "charges": {
        "brokerage": 20.0,
        "stt": 16.5,
        "exchange_transaction_charges": 4.95,
        "gst": 4.47,
        "sebi_charges": 0.12,
        "stamp_duty": 8.25,
        "total": 54.29,
    },
}

RAW_MARGIN = {
    "required_margin": 50000.0,
    "final_margin": 52500.0,
    "span_margin": 40000.0,
    "exposure_margin": 12500.0,
    "available_margin": 100000.0,
    "total_margin": 100000.0,
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_analytics_client() -> MagicMock:
    return MagicMock(spec=AnalyticsClient)


@pytest.fixture
def svc(mock_analytics_client: MagicMock) -> AnalyticsService:
    """AnalyticsService with cache disabled for test isolation."""
    return AnalyticsService(mock_analytics_client, cache_ttl=0)


# ---------------------------------------------------------------------------
# LTP tests
# ---------------------------------------------------------------------------


class TestGetLTP:
    def test_returns_ltp_quote_objects(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_LTP_DATA}
        results = svc.get_ltp(["NSE_EQ|INE009A01021"])
        assert len(results) == 1
        assert isinstance(results[0], LTPQuote)

    def test_ltp_fields_correct(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_LTP_DATA}
        q = svc.get_ltp(["NSE_EQ|INE009A01021"])[0]
        assert q.instrument_token == "NSE_EQ|INE009A01021"
        assert q.trading_symbol == "INFY"
        assert q.last_price == pytest.approx(1650.0)

    def test_empty_data_returns_empty_list(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": {}}
        assert svc.get_ltp(["NSE_EQ|INE009A01021"]) == []

    def test_correct_endpoint_called(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"data": {}}
        svc.get_ltp(["NSE_EQ|INE009A01021"])
        call_args = mock_analytics_client.get.call_args
        assert "/v3/market-quote/ltp" in call_args[0][0]


# ---------------------------------------------------------------------------
# Quote tests
# ---------------------------------------------------------------------------


class TestGetQuotes:
    def test_returns_quote_objects(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_QUOTE_DATA}
        results = svc.get_quotes(["NSE_EQ|INE009A01021"])
        assert len(results) == 1
        assert isinstance(results[0], Quote)

    def test_quote_fields_correct(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_QUOTE_DATA}
        q = svc.get_quotes(["NSE_EQ|INE009A01021"])[0]
        assert q.last_price == pytest.approx(1650.0)
        assert q.open_price == pytest.approx(1620.0)
        assert q.week_52_high == pytest.approx(1900.0)
        assert q.lower_circuit_limit == pytest.approx(1440.0)

    def test_bid_ask_from_depth(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_QUOTE_DATA}
        q = svc.get_quotes(["NSE_EQ|INE009A01021"])[0]
        assert q.bid_price == pytest.approx(1649.0)
        assert q.ask_price == pytest.approx(1651.0)

    def test_net_change_pct_computed(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_QUOTE_DATA}
        q = svc.get_quotes(["NSE_EQ|INE009A01021"])[0]
        # (1650 - 1600) / 1600 * 100 = 3.125
        assert q.net_change_pct == pytest.approx(3.125)

    def test_is_upper_circuit_false(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_QUOTE_DATA}
        q = svc.get_quotes(["NSE_EQ|INE009A01021"])[0]
        assert not q.is_upper_circuit

    def test_is_lower_circuit_false(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_QUOTE_DATA}
        q = svc.get_quotes(["NSE_EQ|INE009A01021"])[0]
        assert not q.is_lower_circuit


# ---------------------------------------------------------------------------
# OHLC tests
# ---------------------------------------------------------------------------


class TestGetOHLC:
    def test_returns_ohlc_objects(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_OHLC_DATA}
        results = svc.get_ohlc(["NSE_EQ|INE009A01021"])
        assert isinstance(results[0], OHLCQuote)

    def test_intraday_range_computed(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_OHLC_DATA}
        q = svc.get_ohlc(["NSE_EQ|INE009A01021"])[0]
        # high 1660 - low 1610 = 50
        assert q.intraday_range == pytest.approx(50.0)

    def test_change_from_open_computed(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_OHLC_DATA}
        q = svc.get_ohlc(["NSE_EQ|INE009A01021"])[0]
        # ltp 1650 - open 1620 = 30
        assert q.change_from_open == pytest.approx(30.0)

    def test_symbol_derived_from_response_key(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        """V3 has no symbol field — trading_symbol must be parsed from the dict key."""
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_OHLC_DATA}
        q = svc.get_ohlc(["NSE_EQ|INE009A01021"])[0]
        assert q.trading_symbol == "INFY"

    def test_interval_passed_to_client(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"data": {}}
        svc.get_ohlc(["NSE_EQ|INE009A01021"], interval="30minute")
        call_params = mock_analytics_client.get.call_args[1]["params"]
        assert call_params["interval"] == "30minute"


# ---------------------------------------------------------------------------
# Historical candles tests
# ---------------------------------------------------------------------------


class TestGetHistoricalCandles:
    def test_returns_candle_objects(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {
            "status": "success",
            "data": {"candles": RAW_CANDLES},
        }
        candles = svc.get_historical_candles(
            "NSE_EQ|INE009A01021", "day", "2026-05-01", "2026-05-05"
        )
        assert len(candles) == 2
        assert isinstance(candles[0], Candle)

    def test_candles_sorted_oldest_first(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        """API returns newest-first; service must reverse to chronological order."""
        mock_analytics_client.get.return_value = {
            "data": {"candles": RAW_CANDLES}
        }
        candles = svc.get_historical_candles("NSE_EQ|INE009A01021", "day", "2026-05-01", "2026-05-05")
        # After reversal, the May 4 candle should be first
        assert candles[0].timestamp.day == 4
        assert candles[1].timestamp.day == 5

    def test_candle_fields_correct(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {
            "data": {"candles": [RAW_CANDLES[0]]}
        }
        c = svc.get_historical_candles("NSE_EQ|INE009A01021", "day", "2026-05-05", "2026-05-05")[0]
        assert c.open_price == pytest.approx(1620.0)
        assert c.high_price == pytest.approx(1660.0)
        assert c.volume == 5_000_000
        assert c.is_bullish is True  # close (1650) > open (1620)

    def test_empty_candles(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"data": {"candles": []}}
        assert svc.get_historical_candles("NSE_EQ|INE009A01021", "day", "2026-05-01", "2026-05-01") == []

    def test_instrument_key_url_encoded_in_path(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        """The '|' in instrument_key must be encoded as %7C in the path."""
        mock_analytics_client.get.return_value = {"data": {"candles": []}}
        svc.get_historical_candles("NSE_EQ|INE009A01021", "day", "2026-05-01", "2026-05-05")
        call_path = mock_analytics_client.get.call_args[0][0]
        assert "NSE_EQ%7CINE009A01021" in call_path
        assert "|" not in call_path  # raw pipe must NOT appear in path


# ---------------------------------------------------------------------------
# Market status tests
# ---------------------------------------------------------------------------


class TestGetMarketStatus:
    def test_returns_market_status_objects(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_MARKET_STATUS}
        results = svc.get_market_status()
        assert len(results) == 2
        assert isinstance(results[0], MarketStatusEntry)

    def test_is_open_flag(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_MARKET_STATUS}
        results = svc.get_market_status()
        nse = next(r for r in results if r.exchange == "NSE")
        bse = next(r for r in results if r.exchange == "BSE")
        assert nse.is_open is True
        assert bse.is_open is False

    def test_exchange_filter_passed_to_client(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"data": {"markets": []}}
        svc.get_market_status(exchange="NSE")
        call_params = mock_analytics_client.get.call_args[1]["params"]
        assert call_params["exchange"] == "NSE"


# ---------------------------------------------------------------------------
# Option chain tests
# ---------------------------------------------------------------------------


class TestGetOptionChain:
    def test_returns_option_chain_entries(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {
            "status": "success",
            "data": RAW_OPTION_CHAIN,
        }
        entries = svc.get_option_chain("NSE_INDEX|Nifty 50", "2026-05-29")
        assert len(entries) == 1
        assert isinstance(entries[0], OptionChainEntry)

    def test_call_side_normalized(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_OPTION_CHAIN}
        entry = svc.get_option_chain("NSE_INDEX|Nifty 50", "2026-05-29")[0]
        assert entry.call is not None
        assert entry.call.ltp == pytest.approx(600.0)
        assert entry.call.iv == pytest.approx(15.5)
        assert entry.call.delta == pytest.approx(0.6)

    def test_put_side_normalized(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_OPTION_CHAIN}
        entry = svc.get_option_chain("NSE_INDEX|Nifty 50", "2026-05-29")[0]
        assert entry.put is not None
        assert entry.put.ltp == pytest.approx(400.0)

    def test_call_put_oi_diff(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_OPTION_CHAIN}
        entry = svc.get_option_chain("NSE_INDEX|Nifty 50", "2026-05-29")[0]
        # CE OI 50000 - PE OI 60000 = -10000
        assert entry.call_put_oi_diff == pytest.approx(-10000.0)

    def test_missing_call_side_is_none(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        raw = [{"expiry": "2026-05-29", "strike_price": 22000, "underlying_spot_price": 22500, "pcr": 1.0}]
        mock_analytics_client.get.return_value = {"status": "success", "data": raw}
        entry = svc.get_option_chain("NSE_INDEX|Nifty 50", "2026-05-29")[0]
        assert entry.call is None
        assert entry.put is None


# ---------------------------------------------------------------------------
# Option Greeks tests
# ---------------------------------------------------------------------------


class TestGetOptionGreeks:
    def test_returns_greeks_objects(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_GREEKS}
        results = svc.get_option_greeks("NSE_INDEX|Nifty 50", "2026-05-29")
        assert len(results) == 1
        assert isinstance(results[0], OptionGreeks)

    def test_greeks_fields_correct(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_GREEKS}
        g = svc.get_option_greeks("NSE_INDEX|Nifty 50", "2026-05-29")[0]
        assert g.delta == pytest.approx(0.6)
        assert g.iv == pytest.approx(15.5)
        assert g.theoretical_price == pytest.approx(605.0)
        assert g.option_type == "CE"


# ---------------------------------------------------------------------------
# Option contracts tests
# ---------------------------------------------------------------------------


class TestGetOptionContracts:
    def test_returns_contract_objects(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_CONTRACT}
        contracts = svc.get_option_contracts("NSE_INDEX|Nifty 50")
        assert len(contracts) == 1
        assert isinstance(contracts[0], OptionContract)

    def test_contract_fields(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_CONTRACT}
        c = svc.get_option_contracts("NSE_INDEX|Nifty 50")[0]
        assert c.lot_size == 50
        assert c.option_type == "CE"
        assert c.underlying == "NIFTY"


# ---------------------------------------------------------------------------
# Instrument search tests
# ---------------------------------------------------------------------------


class TestSearchInstruments:
    def test_returns_search_results(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_SEARCH}
        results = svc.search_instruments("RELIANCE")
        assert len(results) == 1
        assert isinstance(results[0], InstrumentSearchResult)

    def test_fields_correct(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_SEARCH}
        r = svc.search_instruments("RELIANCE")[0]
        assert r.instrument_key == "NSE_EQ|INE002A01018"
        assert r.isin == "INE002A01018"
        assert r.instrument_type == "EQUITY"

    def test_query_passed_to_client(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"data": []}
        svc.search_instruments("INFOSYS")
        call_params = mock_analytics_client.get.call_args[1]["params"]
        assert call_params["query"] == "INFOSYS"

    def test_empty_result(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"data": []}
        assert svc.search_instruments("UNKNOWN_XYZ") == []


# ---------------------------------------------------------------------------
# Brokerage tests
# ---------------------------------------------------------------------------


class TestGetBrokerage:
    def test_returns_brokerage_detail(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_BROKERAGE}
        detail = svc.get_brokerage("NSE_EQ|INE009A01021", 10, 1650.0, "D", "BUY", "NSE")
        assert isinstance(detail, BrokerageDetail)

    def test_total_charges(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_BROKERAGE}
        detail = svc.get_brokerage("NSE_EQ|INE009A01021", 10, 1650.0, "D", "BUY", "NSE")
        assert detail.total_charges == pytest.approx(54.29)

    def test_effective_rate_computed(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_BROKERAGE}
        detail = svc.get_brokerage("NSE_EQ|INE009A01021", 10, 1650.0, "D", "BUY", "NSE")
        assert detail.effective_rate_pct == pytest.approx(54.29 / 16500.0 * 100)

    def test_net_cost_computed(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {"status": "success", "data": RAW_BROKERAGE}
        detail = svc.get_brokerage("NSE_EQ|INE009A01021", 10, 1650.0, "D", "BUY", "NSE")
        assert detail.net_cost == pytest.approx(16500.0 + 54.29)


# ---------------------------------------------------------------------------
# Margin tests
# ---------------------------------------------------------------------------


class TestCalculateMargin:
    def test_returns_margin_detail(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.post.return_value = {"status": "success", "data": RAW_MARGIN}
        detail = svc.calculate_margin([{"instrument_token": "NSE_FO|123", "quantity": 50}])
        assert isinstance(detail, MarginDetail)

    def test_margin_sufficient_when_available_exceeds_final(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.post.return_value = {"status": "success", "data": RAW_MARGIN}
        detail = svc.calculate_margin([])
        # available 100000 > final 52500
        assert detail.is_margin_sufficient is True

    def test_margin_insufficient(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        insufficient = {**RAW_MARGIN, "available_margin": 30000.0}
        mock_analytics_client.post.return_value = {"status": "success", "data": insufficient}
        detail = svc.calculate_margin([])
        assert detail.is_margin_sufficient is False


# ---------------------------------------------------------------------------
# Market Feed Authorization tests
# ---------------------------------------------------------------------------


class TestAuthorizeMarketFeed:
    def test_returns_authorization_object(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {
            "status": "success",
            "data": {"authorized_redirect_uri": "wss://api.upstox.com/feeds/v3?token=abc"},
        }
        auth = svc.authorize_market_feed()
        assert isinstance(auth, MarketFeedAuthorization)

    def test_wss_uri_populated(
        self, svc: AnalyticsService, mock_analytics_client: MagicMock
    ) -> None:
        mock_analytics_client.get.return_value = {
            "data": {"authorized_redirect_uri": "wss://api.upstox.com/feeds/v3?token=abc"},
        }
        auth = svc.authorize_market_feed()
        assert auth.authorized_redirect_uri.startswith("wss://")


# ---------------------------------------------------------------------------
# Cache tests
# ---------------------------------------------------------------------------


class TestAnalyticsCache:
    def test_cache_hit_avoids_second_call(self, mock_analytics_client: MagicMock) -> None:
        svc = AnalyticsService(mock_analytics_client, cache_ttl=300)
        mock_analytics_client.get.return_value = {"data": {}}
        svc.get_ltp(["NSE_EQ|INE009A01021"])
        svc.get_ltp(["NSE_EQ|INE009A01021"])
        assert mock_analytics_client.get.call_count == 1

    def test_invalidate_cache_forces_refetch(self, mock_analytics_client: MagicMock) -> None:
        svc = AnalyticsService(mock_analytics_client, cache_ttl=300)
        mock_analytics_client.get.return_value = {"data": {}}
        svc.get_ltp(["NSE_EQ|INE009A01021"])
        svc.invalidate_cache()
        svc.get_ltp(["NSE_EQ|INE009A01021"])
        assert mock_analytics_client.get.call_count == 2

    def test_cache_disabled_always_fetches(self, mock_analytics_client: MagicMock) -> None:
        svc = AnalyticsService(mock_analytics_client, cache_ttl=0)
        mock_analytics_client.get.return_value = {"data": {}}
        svc.get_ltp(["NSE_EQ|INE009A01021"])
        svc.get_ltp(["NSE_EQ|INE009A01021"])
        assert mock_analytics_client.get.call_count == 2


# ---------------------------------------------------------------------------
# Candle model unit tests (no network)
# ---------------------------------------------------------------------------


class TestCandleModel:
    def test_bullish_candle(self) -> None:
        c = Candle(
            timestamp=datetime(2026, 5, 5, 9, 15),
            open_price=100.0,
            high_price=110.0,
            low_price=95.0,
            close_price=108.0,
            volume=1000,
            open_interest=0,
        )
        assert c.is_bullish is True
        assert c.body == pytest.approx(8.0)

    def test_bearish_candle(self) -> None:
        c = Candle(
            timestamp=datetime(2026, 5, 5, 9, 15),
            open_price=100.0,
            high_price=105.0,
            low_price=90.0,
            close_price=92.0,
            volume=1000,
            open_interest=0,
        )
        assert c.is_bullish is False
        assert c.body == pytest.approx(8.0)
