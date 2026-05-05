"""
Shared pytest fixtures for the eToro app test suite.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.models.portfolio import ClosedPosition, Position

# ---------------------------------------------------------------------------
# Sample data factories
# ---------------------------------------------------------------------------


def make_position(**overrides) -> Position:
    defaults = dict(
        position_id="p1",
        instrument_id=1,
        instrument_name="Apple Inc.",
        instrument_type="stocks",
        direction="Buy",
        amount=1000.0,
        units=5.0,
        open_rate=190.0,
        current_rate=200.0,
        leverage=1,
        unrealised_pnl=50.0,
        open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        is_copy=False,
    )
    defaults.update(overrides)
    return Position(**defaults)


def make_closed_position(**overrides) -> ClosedPosition:
    defaults = dict(
        position_id="cp1",
        instrument_id=2,
        instrument_name="Tesla Inc.",
        instrument_type="stocks",
        direction="Buy",
        amount=500.0,
        units=2.0,
        open_rate=230.0,
        close_rate=250.0,
        leverage=1,
        realised_pnl=40.0,
        open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        close_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return ClosedPosition(**defaults)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client():
    """Return a MagicMock that mimics EToroClient."""
    return MagicMock()


@pytest.fixture
def sample_positions() -> list[Position]:
    return [
        make_position(position_id="p1", instrument_name="Apple Inc.", amount=1000.0, units=5.0, open_rate=190.0, current_rate=200.0),
        make_position(position_id="p2", instrument_name="Bitcoin", instrument_type="crypto", amount=2000.0, units=0.05, open_rate=30000.0, current_rate=25000.0, direction="Buy"),
        make_position(position_id="p3", instrument_name="EUR/USD", instrument_type="currencies", amount=500.0, units=500.0, open_rate=1.08, current_rate=1.10, direction="Buy"),
    ]


@pytest.fixture
def sample_closed() -> list[ClosedPosition]:
    return [
        make_closed_position(position_id="cp1", realised_pnl=40.0),
        make_closed_position(position_id="cp2", realised_pnl=-20.0),
    ]
