"""
Unit tests for trigger implementations.
"""

import os
import sys
import tempfile
import time
from datetime import datetime

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from triggers.base_trigger import TriggerEvent
from triggers.time_trigger import TimeTrigger
from triggers.file_trigger import FileTrigger
from triggers.custom_trigger import ThresholdTrigger, LambdaTrigger


class TestTimeTrigger:
    def test_fires_immediately_on_first_check(self):
        trigger = TimeTrigger(interval_minutes=60)
        trigger.setup()
        event = trigger.check()
        assert event is not None
        assert event.source == "TimeTrigger"

    def test_does_not_fire_twice_before_interval(self):
        trigger = TimeTrigger(interval_minutes=60)
        trigger.setup()
        trigger.check()  # first fire
        event = trigger.check()  # should not fire again
        assert event is None

    def test_invalid_interval_raises(self):
        with pytest.raises(ValueError):
            TimeTrigger(interval_minutes=0)

    def test_trigger_name(self):
        assert TimeTrigger(interval_minutes=1).name == "TimeTrigger"


class TestFileTrigger:
    def test_fires_when_file_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")

            # Create the file after setup so it counts as a new file
            trigger = FileTrigger(watch_path=tmpdir)
            trigger.setup()

            # Create a new file — should fire
            with open(test_file, "w") as f:
                f.write("hello")

            event = trigger.check()
            assert event is not None
            assert "test.txt" in event.message

    def test_no_fire_when_nothing_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "stable.txt")
            with open(test_file, "w") as f:
                f.write("stable content")

            trigger = FileTrigger(watch_path=tmpdir)
            trigger.setup()  # snapshot taken now

            event = trigger.check()  # nothing changed since setup
            assert event is None

    def test_extension_filter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            trigger = FileTrigger(watch_path=tmpdir, extensions=[".csv"])
            trigger.setup()

            # Create a .txt file — should NOT trigger
            with open(os.path.join(tmpdir, "ignored.txt"), "w") as f:
                f.write("ignored")
            assert trigger.check() is None

            # Create a .csv file — SHOULD trigger
            with open(os.path.join(tmpdir, "data.csv"), "w") as f:
                f.write("a,b,c")
            event = trigger.check()
            assert event is not None


class TestThresholdTrigger:
    def test_fires_when_above_threshold(self):
        current = [80.0]
        trigger = ThresholdTrigger(
            name_label="Test",
            value_getter=lambda: current[0],
            threshold=75.0,
            above=True,
            cooldown_seconds=0,
        )
        trigger.setup()
        event = trigger.check()
        assert event is not None
        assert "80.0" in event.message

    def test_does_not_fire_below_threshold(self):
        trigger = ThresholdTrigger(
            name_label="Test",
            value_getter=lambda: 50.0,
            threshold=75.0,
            above=True,
            cooldown_seconds=0,
        )
        trigger.setup()
        assert trigger.check() is None

    def test_fires_when_below_threshold(self):
        trigger = ThresholdTrigger(
            name_label="LowTemp",
            value_getter=lambda: 10.0,
            threshold=20.0,
            above=False,
            unit="°C",
            cooldown_seconds=0,
        )
        trigger.setup()
        event = trigger.check()
        assert event is not None

    def test_cooldown_prevents_repeated_events(self):
        trigger = ThresholdTrigger(
            name_label="CooldownTest",
            value_getter=lambda: 100.0,
            threshold=50.0,
            cooldown_seconds=3600,
        )
        trigger.setup()
        assert trigger.check() is not None  # first fire
        assert trigger.check() is None      # in cooldown


class TestLambdaTrigger:
    def test_fires_when_condition_true(self):
        trigger = LambdaTrigger(
            name_label="Lambda",
            condition_fn=lambda: (True, "condition met"),
            cooldown_seconds=0,
        )
        event = trigger.check()
        assert event is not None
        assert event.message == "condition met"

    def test_does_not_fire_when_false(self):
        trigger = LambdaTrigger(
            name_label="Lambda",
            condition_fn=lambda: (False, ""),
            cooldown_seconds=0,
        )
        assert trigger.check() is None

    def test_disable_prevents_firing(self):
        trigger = LambdaTrigger(
            name_label="Lambda",
            condition_fn=lambda: (True, "should not fire"),
            cooldown_seconds=0,
        )
        trigger.disable()
        assert trigger.check() is None
