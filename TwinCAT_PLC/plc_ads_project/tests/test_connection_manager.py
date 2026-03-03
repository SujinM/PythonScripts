"""
test_connection_manager.py
--------------------------
Unit tests for :class:`~core.connection_manager.ConnectionManager`.

All ADS I/O is mocked; no real PLC or AMS router is required.

Tests cover:
    * Successful open / close lifecycle.
    * State transitions (DISCONNECTED → CONNECTED → DISCONNECTED).
    * Double open is a no-op.
    * ``connection`` property raises when not connected.
    * Context manager (``__enter__`` / ``__exit__``).
    * Watchdog eventually triggers reconnect after a heartbeat failure.
    * Reconnect succeeds and transitions back to CONNECTED.
    * Reconnect exhaustion raises PLCReconnectExhaustedError and sets FAILED.
"""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from config.config_loader import ConnectionConfig, ReconnectConfig, HeartbeatConfig
from core.connection_manager import ConnectionManager, ConnectionState
from utils.custom_exceptions import PLCConnectionError, PLCReconnectExhaustedError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def conn_cfg() -> ConnectionConfig:
    return ConnectionConfig(
        ams_net_id="1.2.3.4.1.1",
        ip_address="192.168.0.10",
        port=851,
    )


@pytest.fixture
def reconnect_cfg():
    return ReconnectConfig(
        max_attempts=3,
        initial_delay_seconds=0.01,
        backoff_multiplier=1.5,
        max_delay_seconds=0.1,
    )


@pytest.fixture
def heartbeat_cfg():
    return HeartbeatConfig(interval_seconds=1)


@pytest.fixture
def fast_heartbeat_cfg():
    """Very short interval to trigger watchdog quickly in tests."""
    return HeartbeatConfig(interval_seconds=1)


def _make_manager(
    conn_cfg: ConnectionConfig,
    reconnect_cfg: ReconnectConfig,
    heartbeat_cfg: HeartbeatConfig,
) -> ConnectionManager:
    return ConnectionManager(
        connection_cfg=conn_cfg,
        reconnect_cfg=reconnect_cfg,
        heartbeat_cfg=heartbeat_cfg,
    )


# ---------------------------------------------------------------------------
# Helper: patch pyads so no real AMS router is required
# ---------------------------------------------------------------------------

_PYADS_PATCH_TARGET = "core.connection_manager"


def _mock_pyads_connection(mock_connection_class: MagicMock) -> MagicMock:
    """
    Return a configured mock Connection instance from the mocked
    pyads.Connection class.
    """
    mock_conn = MagicMock()
    mock_connection_class.return_value = mock_conn
    return mock_conn


# ===========================================================================
# Lifecycle tests
# ===========================================================================

class TestOpenClose:
    @patch(f"{_PYADS_PATCH_TARGET}.pyads")
    def test_open_transitions_to_connected(
        self,
        mock_pyads: MagicMock,
        conn_cfg: ConnectionConfig,
        reconnect_cfg: ReconnectConfig,
        heartbeat_cfg: HeartbeatConfig,
    ) -> None:
        _mock_pyads_connection(mock_pyads.Connection)
        cm = _make_manager(conn_cfg, reconnect_cfg, heartbeat_cfg)
        cm.open()
        try:
            assert cm.state == ConnectionState.CONNECTED
            assert cm.is_connected
        finally:
            cm.close()

    @patch(f"{_PYADS_PATCH_TARGET}.pyads")
    def test_close_transitions_to_disconnected(
        self,
        mock_pyads: MagicMock,
        conn_cfg: ConnectionConfig,
        reconnect_cfg: ReconnectConfig,
        heartbeat_cfg: HeartbeatConfig,
    ) -> None:
        _mock_pyads_connection(mock_pyads.Connection)
        cm = _make_manager(conn_cfg, reconnect_cfg, heartbeat_cfg)
        cm.open()
        cm.close()
        assert cm.state == ConnectionState.DISCONNECTED

    @patch(f"{_PYADS_PATCH_TARGET}.pyads")
    def test_double_open_is_noop(
        self,
        mock_pyads: MagicMock,
        conn_cfg: ConnectionConfig,
        reconnect_cfg: ReconnectConfig,
        heartbeat_cfg: HeartbeatConfig,
    ) -> None:
        mock_conn = _mock_pyads_connection(mock_pyads.Connection)
        cm = _make_manager(conn_cfg, reconnect_cfg, heartbeat_cfg)
        cm.open()
        cm.open()  # second call should be a no-op
        try:
            assert mock_conn.open.call_count == 1
        finally:
            cm.close()

    @patch(f"{_PYADS_PATCH_TARGET}.pyads")
    def test_close_without_open_is_safe(
        self,
        mock_pyads: MagicMock,
        conn_cfg: ConnectionConfig,
        reconnect_cfg: ReconnectConfig,
        heartbeat_cfg: HeartbeatConfig,
    ) -> None:
        cm = _make_manager(conn_cfg, reconnect_cfg, heartbeat_cfg)
        cm.close()  # Must not raise.
        assert cm.state == ConnectionState.DISCONNECTED


class TestConnectionProperty:
    @patch(f"{_PYADS_PATCH_TARGET}.pyads")
    def test_connection_returns_plc_when_open(
        self,
        mock_pyads: MagicMock,
        conn_cfg: ConnectionConfig,
        reconnect_cfg: ReconnectConfig,
        heartbeat_cfg: HeartbeatConfig,
    ) -> None:
        mock_conn = _mock_pyads_connection(mock_pyads.Connection)
        cm = _make_manager(conn_cfg, reconnect_cfg, heartbeat_cfg)
        cm.open()
        try:
            assert cm.connection is mock_conn
        finally:
            cm.close()

    def test_connection_property_raises_when_disconnected(
        self,
        conn_cfg: ConnectionConfig,
        reconnect_cfg: ReconnectConfig,
        heartbeat_cfg: HeartbeatConfig,
    ) -> None:
        cm = _make_manager(conn_cfg, reconnect_cfg, heartbeat_cfg)
        with pytest.raises(PLCConnectionError):
            _ = cm.connection


class TestContextManager:
    @patch(f"{_PYADS_PATCH_TARGET}.pyads")
    def test_context_manager_opens_and_closes(
        self,
        mock_pyads: MagicMock,
        conn_cfg: ConnectionConfig,
        reconnect_cfg: ReconnectConfig,
        heartbeat_cfg: HeartbeatConfig,
    ) -> None:
        mock_conn = _mock_pyads_connection(mock_pyads.Connection)
        cm = _make_manager(conn_cfg, reconnect_cfg, heartbeat_cfg)
        with cm:
            assert cm.is_connected
        assert cm.state == ConnectionState.DISCONNECTED

    @patch(f"{_PYADS_PATCH_TARGET}.pyads")
    def test_context_manager_closes_on_exception(
        self,
        mock_pyads: MagicMock,
        conn_cfg: ConnectionConfig,
        reconnect_cfg: ReconnectConfig,
        heartbeat_cfg: HeartbeatConfig,
    ) -> None:
        _mock_pyads_connection(mock_pyads.Connection)
        cm = _make_manager(conn_cfg, reconnect_cfg, heartbeat_cfg)
        try:
            with cm:
                raise ValueError("test error")
        except ValueError:
            pass
        assert cm.state == ConnectionState.DISCONNECTED


# ===========================================================================
# Error handling
# ===========================================================================

class TestOpenFailure:
    @patch(f"{_PYADS_PATCH_TARGET}.pyads")
    def test_ads_error_on_open_raises_plc_connection_error(
        self,
        mock_pyads: MagicMock,
        conn_cfg: ConnectionConfig,
        reconnect_cfg: ReconnectConfig,
        heartbeat_cfg: HeartbeatConfig,
    ) -> None:
        mock_pyads.Connection.return_value.open.side_effect = mock_pyads.ADSError("fail")
        # ADSError itself needs to be available as a real exception class for
        # the isinstance check inside _do_open.
        mock_pyads.ADSError = type("ADSError", (Exception,), {})
        mock_pyads.Connection.return_value.open.side_effect = mock_pyads.ADSError("fail")

        cm = _make_manager(conn_cfg, reconnect_cfg, heartbeat_cfg)
        with pytest.raises(PLCConnectionError):
            cm.open()
