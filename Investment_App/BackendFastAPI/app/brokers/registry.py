"""
app/brokers/registry.py
───────────────────────
BrokerRegistry — maps broker_id → adapter instance.

Adding a new broker:
  Call  BrokerRegistry.register(MyAdapter())  inside the new adapter's module,
  then import that module in app/main.py.  No other code changes needed.
"""

from __future__ import annotations

from typing import Iterator

from app.brokers.base import IBrokerAdapter
from app.core.exceptions import BrokerNotFoundError
from app.core.logger import get_logger

logger = get_logger(__name__)


class BrokerRegistry:
    """Holds all registered broker adapter instances."""

    def __init__(self) -> None:
        self._adapters: dict[str, IBrokerAdapter] = {}

    def register(self, adapter: IBrokerAdapter) -> None:
        self._adapters[adapter.broker_id] = adapter
        logger.info("Registered broker adapter: %s", adapter.broker_id)

    def get(self, broker_id: str) -> IBrokerAdapter:
        adapter = self._adapters.get(broker_id)
        if adapter is None:
            raise BrokerNotFoundError(broker_id)
        return adapter

    def all(self) -> list[IBrokerAdapter]:
        return list(self._adapters.values())

    def ids(self) -> list[str]:
        return list(self._adapters.keys())

    def __iter__(self) -> Iterator[IBrokerAdapter]:
        return iter(self._adapters.values())

    def __len__(self) -> int:
        return len(self._adapters)


# Module-level singleton — created once, shared via Depends()
registry = BrokerRegistry()
