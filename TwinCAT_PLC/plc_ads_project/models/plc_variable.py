"""
plc_variable.py
---------------
Domain model representing a single PLC variable managed by this application.

A :class:`PLCVariable` instance encapsulates:
    * The symbolic name and declared PLC data type.
    * The most-recently-read value together with the UTC timestamp at which
      the value was last updated.
    * The ADS device-notification *handle* (when an active subscription exists).
    * An optional set of *event hooks* – zero-argument callables that are
      invoked after every successful value update.

Thread Safety
~~~~~~~~~~~~~
All mutable state is protected by a :class:`threading.RLock`.  The lock is
re-entrant so that methods belonging to the same thread can call each other
without deadlocking.

Usage example::

    from models.plc_variable import PLCVariable

    var = PLCVariable(name="MAIN.nSpeed", plc_type="INT")
    var.register_change_hook(lambda v: print(f"Speed changed → {v}"))
    var.update_value(1500)
    print(var.current_value)         # 1500
    print(var.last_updated)          # datetime of the update
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Optional

from utils.custom_exceptions import DataTypeMismatchError
from utils.logger import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Python-side type validation rules for each supported PLC type.
# ---------------------------------------------------------------------------
# Maps PLC type string → tuple of acceptable Python types (passed to isinstance).
_PLC_PYTHON_TYPE_MAP: dict[str, tuple[type, ...]] = {
    "BOOL":   (bool, int),
    "BYTE":   (int,),
    "INT":    (int,),
    "UINT":   (int,),
    "DINT":   (int,),
    "UDINT":  (int,),
    "REAL":   (float, int),
    "LREAL":  (float, int),
    "STRING": (str,),
    "ARRAY":  (list, tuple, bytes, bytearray),
}


class PLCVariable:
    """
    Represents a single PLC variable with its current value and metadata.

    Attributes are intentionally private; access is exclusively through
    properties and methods to allow locking and validation to be enforced
    transparently.

    Args:
        name:     Full symbolic name as declared in the PLC runtime
                  (e.g. ``"MAIN.bMotorOn"``).
        plc_type: PLC data type string (e.g. ``"BOOL"``, ``"INT"``).
    """

    __slots__ = (
        "_name",
        "_plc_type",
        "_current_value",
        "_last_updated",
        "_subscription_handle",
        "_lock",
        "_change_hooks",
    )

    def __init__(self, name: str, plc_type: str) -> None:
        self._name: str = name
        self._plc_type: str = plc_type.upper()
        self._current_value: Any = None
        self._last_updated: Optional[datetime] = None
        self._subscription_handle: Optional[int] = None
        self._lock: threading.RLock = threading.RLock()
        self._change_hooks: list[Callable[[Any], None]] = []

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """The full symbolic name of the PLC variable (immutable)."""
        return self._name

    @property
    def plc_type(self) -> str:
        """PLC data type string, upper-cased (immutable after construction)."""
        return self._plc_type

    @property
    def current_value(self) -> Any:
        """The most recently received value.  ``None`` before the first update."""
        with self._lock:
            return self._current_value

    @property
    def last_updated(self) -> Optional[datetime]:
        """UTC :class:`~datetime.datetime` of the last successful value update."""
        with self._lock:
            return self._last_updated

    @property
    def subscription_handle(self) -> Optional[int]:
        """ADS notification handle, or ``None`` if no subscription is active."""
        with self._lock:
            return self._subscription_handle

    @subscription_handle.setter
    def subscription_handle(self, handle: Optional[int]) -> None:
        with self._lock:
            self._subscription_handle = handle
            log.debug("Variable '%s': subscription handle set to %s", self._name, handle)

    # ------------------------------------------------------------------
    # Public mutating methods
    # ------------------------------------------------------------------

    def update_value(self, new_value: Any) -> None:
        """
        Update the variable's current value and timestamp.

        Performs a lightweight type validation and fires all registered change
        hooks **after** releasing the internal lock (to avoid dead-locks when a
        hook itself tries to read this variable).

        Args:
            new_value: The new value received from the PLC.

        Raises:
            DataTypeMismatchError: If *new_value* is incompatible with the
                declared PLC type.
        """
        self.validate_type(new_value)

        previous_value: Any
        hooks: list[Callable[[Any], None]]

        with self._lock:
            previous_value = self._current_value
            self._current_value = new_value
            self._last_updated = datetime.now(tz=timezone.utc)
            hooks = list(self._change_hooks)  # snapshot to release lock quickly

        if new_value != previous_value:
            log.info(
                "Variable '%s' changed: %r → %r",
                self._name,
                previous_value,
                new_value,
            )
        else:
            log.debug("Variable '%s' refreshed (no change): %r", self._name, new_value)

        # Fire hooks outside the lock.
        for hook in hooks:
            try:
                hook(new_value)
            except Exception as exc:  # noqa: BLE001
                log.warning(
                    "Change hook for variable '%s' raised an exception: %s",
                    self._name,
                    exc,
                    exc_info=True,
                )

    def validate_type(self, value: Any) -> None:
        """
        Assert that *value* is compatible with the declared PLC type.

        This method is **non-destructive** – it does not modify any state.  It
        can be called independently before a write operation.

        Args:
            value: Python value to validate.

        Raises:
            DataTypeMismatchError: When the value's type is incompatible with
                the declared PLC type.
        """
        if value is None:
            # None is used as the initial sentinel; always allow it.
            return

        expected_types = _PLC_PYTHON_TYPE_MAP.get(self._plc_type)
        if expected_types is None:
            # Unknown PLC type – log a warning but do not block.
            log.warning(
                "Variable '%s': no Python type mapping for PLC type '%s'; skipping validation",
                self._name,
                self._plc_type,
            )
            return

        if not isinstance(value, expected_types):
            raise DataTypeMismatchError(
                f"Variable '{self._name}' expects PLC type '{self._plc_type}' "
                f"(Python: {' | '.join(t.__name__ for t in expected_types)}), "
                f"but received {type(value).__name__!r} with value {value!r}.",
                variable_name=self._name,
                expected_type=self._plc_type,
                received_type=type(value).__name__,
                value=value,
            )

    # ------------------------------------------------------------------
    # Change hooks
    # ------------------------------------------------------------------

    def register_change_hook(self, hook: Callable[[Any], None]) -> None:
        """
        Register a callable to be invoked whenever the variable's value changes.

        The hook receives the new value as its sole argument.  If the hook
        raises an exception it is caught and logged; it does not propagate.

        Args:
            hook: A callable accepting a single positional argument (the new value).
        """
        with self._lock:
            if hook not in self._change_hooks:
                self._change_hooks.append(hook)
                log.debug("Variable '%s': registered change hook '%s'", self._name, hook)

    def unregister_change_hook(self, hook: Callable[[Any], None]) -> None:
        """
        Remove a previously registered change hook.

        Args:
            hook: The callable to remove.  Silently ignored if not registered.
        """
        with self._lock:
            try:
                self._change_hooks.remove(hook)
                log.debug("Variable '%s': unregistered change hook '%s'", self._name, hook)
            except ValueError:
                pass

    def clear_change_hooks(self) -> None:
        """Remove all registered change hooks."""
        with self._lock:
            self._change_hooks.clear()
            log.debug("Variable '%s': all change hooks cleared", self._name)

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Return a JSON-serialisable snapshot of the variable's current state.

        Returns:
            A dict with keys ``name``, ``plc_type``, ``current_value``,
            ``last_updated`` (ISO-8601 string, or ``None``).
        """
        with self._lock:
            return {
                "name": self._name,
                "plc_type": self._plc_type,
                "current_value": self._current_value,
                "last_updated": (
                    self._last_updated.isoformat() if self._last_updated else None
                ),
            }

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"PLCVariable(name={self._name!r}, plc_type={self._plc_type!r}, "
            f"current_value={self._current_value!r})"
        )

    def __str__(self) -> str:
        return f"{self._name} [{self._plc_type}] = {self._current_value}"
