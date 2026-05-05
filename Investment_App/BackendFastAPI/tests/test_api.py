"""tests/test_api.py — FastAPI route integration tests using TestClient."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health_ok(self, test_client: TestClient):
        resp = test_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestBrokersEndpoint:
    def test_list_brokers(self, test_client: TestClient):
        resp = test_client.get("/api/v1/brokers")
        assert resp.status_code == 200
        data = resp.json()["data"]
        ids = [b["id"] for b in data]
        assert "mock" in ids


class TestHoldingsEndpoint:
    def test_get_holdings_success(self, test_client: TestClient):
        resp = test_client.get("/api/v1/mock/holdings")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert len(body["data"]) == 2

    def test_get_holdings_unknown_broker(self, test_client: TestClient):
        resp = test_client.get("/api/v1/unknown_broker/holdings")
        assert resp.status_code == 404

    def test_holdings_data_fields(self, test_client: TestClient):
        resp = test_client.get("/api/v1/mock/holdings")
        holding = resp.json()["data"][0]
        assert "trading_symbol" in holding
        assert "invested_value" in holding
        assert "unrealised_pnl" in holding
        assert "return_pct" in holding


class TestPositionsEndpoint:
    def test_get_positions_success(self, test_client: TestClient):
        resp = test_client.get("/api/v1/mock/positions")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_positions_data_fields(self, test_client: TestClient):
        position = test_client.get("/api/v1/mock/positions").json()["data"][0]
        assert "total_pnl" in position
        assert "realised_pnl" in position


class TestTradesEndpoint:
    def test_get_trades_success(self, test_client: TestClient):
        resp = test_client.get("/api/v1/mock/trades")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_trades_data_fields(self, test_client: TestClient):
        trade = test_client.get("/api/v1/mock/trades").json()["data"][0]
        assert "transaction_type" in trade
        assert "trade_value" in trade


class TestSummaryEndpoint:
    def test_get_summary_success(self, test_client: TestClient):
        resp = test_client.get("/api/v1/mock/summary")
        assert resp.status_code == 200
        summary = resp.json()["data"]
        assert summary["broker"] == "mock"
        assert summary["holdings_count"] == 2

    def test_summary_unknown_broker(self, test_client: TestClient):
        resp = test_client.get("/api/v1/ghost/summary")
        assert resp.status_code == 404


class TestAnalysisEndpoints:
    def test_full_analysis(self, test_client: TestClient):
        resp = test_client.get("/api/v1/mock/analysis")
        assert resp.status_code == 200
        result = resp.json()["data"]
        assert "alerts" in result
        assert "sector_allocation" in result
        assert "top_gainers" in result

    def test_alerts_endpoint(self, test_client: TestClient):
        resp = test_client.get("/api/v1/mock/analysis/alerts")
        assert resp.status_code == 200
        alerts = resp.json()["data"]
        assert isinstance(alerts, list)

    def test_analysis_unknown_broker(self, test_client: TestClient):
        resp = test_client.get("/api/v1/ghost/analysis")
        assert resp.status_code == 404


class TestCacheInvalidation:
    def test_invalidate_cache(self, test_client: TestClient):
        resp = test_client.post("/api/v1/mock/cache/invalidate")
        assert resp.status_code == 200
        assert "Cache cleared" in resp.json()["data"]["message"]
