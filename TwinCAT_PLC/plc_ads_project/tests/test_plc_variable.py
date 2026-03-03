"""
test_plc_variable.py
--------------------
Unit tests for :class:`~models.plc_variable.PLCVariable`.

Tests cover:
    * Default initial state.
    * update_value – happy path for each supported PLC type.
    * update_value – type validation (DataTypeMismatchError).
    * Change hook registration and invocation ordering.
    * Change hook exception isolation (one bad hook must not stop others).
    * Thread-safety: concurrent updates from multiple threads.
    * to_dict serialisation.
    * subscription_handle property.
"""

from __future__ import annotations

import threading
import time
from typing import Any
from unittest.mock import MagicMock

import pytest

from models.plc_variable import PLCVariable
from utils.custom_exceptions import DataTypeMismatchError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def bool_var() -> PLCVariable:
    return PLCVariable(name="MAIN.bMotorOn", plc_type="BOOL")


@pytest.fixture
def int_var() -> PLCVariable:
    return PLCVariable(name="MAIN.nSpeed", plc_type="INT")


@pytest.fixture
def real_var() -> PLCVariable:
    return PLCVariable(name="MAIN.rTemp", plc_type="REAL")


@pytest.fixture
def string_var() -> PLCVariable:
    return PLCVariable(name="MAIN.sStatus", plc_type="STRING")


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

class TestInitialState:
    def test_name(self, int_var: PLCVariable) -> None:
        assert int_var.name == "MAIN.nSpeed"

    def test_plc_type_normalised_to_upper(self) -> None:
        var = PLCVariable(name="TEST.x", plc_type="real")
        assert var.plc_type == "REAL"

    def test_current_value_is_none(self, int_var: PLCVariable) -> None:
        assert int_var.current_value is None

    def test_last_updated_is_none(self, int_var: PLCVariable) -> None:
        assert int_var.last_updated is None

    def test_subscription_handle_is_none(self, int_var: PLCVariable) -> None:
        assert int_var.subscription_handle is None


# ---------------------------------------------------------------------------
# update_value – happy path
# ---------------------------------------------------------------------------

class TestUpdateValue:
    def test_bool_update(self, bool_var: PLCVariable) -> None:
        bool_var.update_value(True)
        assert bool_var.current_value is True

    def test_int_update(self, int_var: PLCVariable) -> None:
        int_var.update_value(1500)
        assert int_var.current_value == 1500

    def test_real_update(self, real_var: PLCVariable) -> None:
        real_var.update_value(22.5)
        assert abs(real_var.current_value - 22.5) < 1e-6

    def test_string_update(self, string_var: PLCVariable) -> None:
        string_var.update_value("RUNNING")
        assert string_var.current_value == "RUNNING"

    def test_last_updated_set_after_update(self, int_var: PLCVariable) -> None:
        int_var.update_value(100)
        assert int_var.last_updated is not None

    def test_update_with_none_is_accepted(self, int_var: PLCVariable) -> None:
        """None is the sentinel initial value; must not raise."""
        int_var.update_value(None)
        assert int_var.current_value is None

    def test_timestamp_advances_on_subsequent_updates(self, int_var: PLCVariable) -> None:
        int_var.update_value(1)
        t1 = int_var.last_updated
        time.sleep(0.01)
        int_var.update_value(2)
        t2 = int_var.last_updated
        assert t2 > t1  # type: ignore[operator]


# ---------------------------------------------------------------------------
# validate_type – error cases
# ---------------------------------------------------------------------------

class TestValidateType:
    def test_wrong_type_for_int_raises(self, int_var: PLCVariable) -> None:
        with pytest.raises(DataTypeMismatchError) as exc_info:
            int_var.update_value("not_an_int")
        assert exc_info.value.variable_name == "MAIN.nSpeed"
        assert exc_info.value.expected_type == "INT"

    def test_wrong_type_for_bool_raises(self, bool_var: PLCVariable) -> None:
        with pytest.raises(DataTypeMismatchError):
            bool_var.update_value("yes")

    def test_float_for_string_raises(self, string_var: PLCVariable) -> None:
        with pytest.raises(DataTypeMismatchError):
            string_var.update_value(3.14)

    def test_unknown_plc_type_does_not_raise(self) -> None:
        """Unknown PLC types should be accepted with a warning (log only)."""
        var = PLCVariable(name="TEST.x", plc_type="WORD")
        var.update_value(0xABCD)  # Should not raise.


# ---------------------------------------------------------------------------
# Change hooks
# ---------------------------------------------------------------------------

class TestChangeHooks:
    def test_hook_called_on_update(self, int_var: PLCVariable) -> None:
        hook = MagicMock()
        int_var.register_change_hook(hook)
        int_var.update_value(42)
        hook.assert_called_once_with(42)

    def test_multiple_hooks_all_called(self, int_var: PLCVariable) -> None:
        hook1, hook2 = MagicMock(), MagicMock()
        int_var.register_change_hook(hook1)
        int_var.register_change_hook(hook2)
        int_var.update_value(99)
        hook1.assert_called_once_with(99)
        hook2.assert_called_once_with(99)

    def test_duplicate_hook_not_registered_twice(self, int_var: PLCVariable) -> None:
        hook = MagicMock()
        int_var.register_change_hook(hook)
        int_var.register_change_hook(hook)  # Second call should be a no-op.
        int_var.update_value(10)
        hook.assert_called_once()

    def test_bad_hook_does_not_prevent_other_hooks(self, int_var: PLCVariable) -> None:
        bad_hook = MagicMock(side_effect=RuntimeError("boom"))
        good_hook = MagicMock()
        int_var.register_change_hook(bad_hook)
        int_var.register_change_hook(good_hook)
        # Should not raise; bad_hook exception is swallowed.
        int_var.update_value(5)
        good_hook.assert_called_once_with(5)

    def test_unregister_hook(self, int_var: PLCVariable) -> None:
        hook = MagicMock()
        int_var.register_change_hook(hook)
        int_var.unregister_change_hook(hook)
        int_var.update_value(7)
        hook.assert_not_called()

    def test_unregister_nonexistent_hook_is_silent(self, int_var: PLCVariable) -> None:
        """Unregistering a hook that was not registered must not raise."""
        int_var.unregister_change_hook(MagicMock())

    def test_clear_change_hooks(self, int_var: PLCVariable) -> None:
        hook = MagicMock()
        int_var.register_change_hook(hook)
        int_var.clear_change_hooks()
        int_var.update_value(3)
        hook.assert_not_called()


# ---------------------------------------------------------------------------
# Subscription handle
# ---------------------------------------------------------------------------

class TestSubscriptionHandle:
    def test_set_and_get_handle(self, int_var: PLCVariable) -> None:
        int_var.subscription_handle = 12345
        assert int_var.subscription_handle == 12345

    def test_clear_handle(self, int_var: PLCVariable) -> None:
        int_var.subscription_handle = 1
        int_var.subscription_handle = None
        assert int_var.subscription_handle is None


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

class TestThreadSafety:
    def test_concurrent_updates_do_not_corrupt_state(self, int_var: PLCVariable) -> None:
        """
        Launch 20 threads each writing a distinct value.  After all threads
        complete, current_value must be one of the values written (not None
        or an intermediate corrupted state).
        """
        values_written: list[int] = list(range(20))
        threads = [
            threading.Thread(target=int_var.update_value, args=(v,))
            for v in values_written
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert int_var.current_value in values_written


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

class TestToDict:
    def test_to_dict_structure(self, int_var: PLCVariable) -> None:
        int_var.update_value(500)
        d = int_var.to_dict()
        assert d["name"] == "MAIN.nSpeed"
        assert d["plc_type"] == "INT"
        assert d["current_value"] == 500
        assert d["last_updated"] is not None  # ISO-8601 string

    def test_to_dict_before_update(self, int_var: PLCVariable) -> None:
        d = int_var.to_dict()
        assert d["current_value"] is None
        assert d["last_updated"] is None


# ---------------------------------------------------------------------------
# Repr / str
# ---------------------------------------------------------------------------

class TestDunderMethods:
    def test_repr(self, int_var: PLCVariable) -> None:
        repr_str = repr(int_var)
        assert "MAIN.nSpeed" in repr_str
        assert "INT" in repr_str

    def test_str(self, int_var: PLCVariable) -> None:
        int_var.update_value(42)
        s = str(int_var)
        assert "MAIN.nSpeed" in s
        assert "42" in s
