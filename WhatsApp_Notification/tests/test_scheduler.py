"""
Unit tests for Scheduler and TriggerManager.
"""

import os
import sys
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.scheduler import Scheduler
from core.trigger_manager import TriggerManager
from triggers.base_trigger import BaseTrigger, TriggerEvent
from datetime import datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _always_fires_trigger(name="AlwaysFires"):
    """Return a mock trigger that always emits a TriggerEvent."""
    trigger = MagicMock(spec=BaseTrigger)
    trigger.name = name
    trigger.is_enabled = True
    trigger.check.return_value = TriggerEvent(
        source=name,
        message="test event",
        timestamp=datetime.now(),
    )
    return trigger


def _never_fires_trigger(name="NeverFires"):
    trigger = MagicMock(spec=BaseTrigger)
    trigger.name = name
    trigger.is_enabled = True
    trigger.check.return_value = None
    return trigger


# ---------------------------------------------------------------------------
# TriggerManager tests
# ---------------------------------------------------------------------------

class TestTriggerManager:
    def test_register_and_poll(self):
        t = _always_fires_trigger()
        manager = TriggerManager()
        manager.register(t)
        manager.setup_all()
        events = manager.poll()
        assert len(events) == 1
        assert events[0].source == "AlwaysFires"
        t.setup.assert_called_once()

    def test_disabled_trigger_skipped(self):
        t = _always_fires_trigger()
        t.is_enabled = False
        manager = TriggerManager()
        manager.register(t)
        events = manager.poll()
        assert events == []
        t.check.assert_not_called()

    def test_trigger_exception_does_not_crash_manager(self):
        t = MagicMock(spec=BaseTrigger)
        t.name = "Broken"
        t.is_enabled = True
        t.check.side_effect = RuntimeError("boom")

        manager = TriggerManager()
        manager.register(t)
        events = manager.poll()  # should not raise
        assert events == []

    def test_unregister(self):
        t1 = _always_fires_trigger("T1")
        t2 = _always_fires_trigger("T2")
        manager = TriggerManager()
        manager.register(t1).register(t2)
        removed = manager.unregister("T1")
        assert removed is True
        assert "T1" not in manager.trigger_names
        assert "T2" in manager.trigger_names

    def test_teardown_all_called(self):
        t = _always_fires_trigger()
        manager = TriggerManager()
        manager.register(t)
        manager.teardown_all()
        t.teardown.assert_called_once()


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

class TestScheduler:
    def test_scheduler_calls_notifier_on_fired_event(self):
        t = _always_fires_trigger()
        manager = TriggerManager()
        manager.register(t)

        notifier = MagicMock()

        scheduler = Scheduler(
            trigger_manager=manager,
            notifier=notifier,
            tick_seconds=1,
        )

        # Run for 1.5 ticks then stop
        def _stop():
            time.sleep(0.5)
            scheduler.stop()

        thread = threading.Thread(target=_stop, daemon=True)
        thread.start()
        scheduler.start()
        thread.join()

        assert notifier.dispatch.call_count >= 1

    def test_scheduler_stops_gracefully(self):
        manager = TriggerManager()
        manager.register(_never_fires_trigger())
        notifier = MagicMock()

        scheduler = Scheduler(
            trigger_manager=manager,
            notifier=notifier,
            tick_seconds=60,  # long tick — we stop externally
        )

        thread = threading.Thread(target=scheduler.start, daemon=True)
        thread.start()
        time.sleep(0.2)
        scheduler.stop()
        thread.join(timeout=3)

        assert not thread.is_alive(), "Scheduler did not stop within timeout."
