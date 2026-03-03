"""
variable_registry.py
--------------------
Centralised, thread-safe store for all :class:`~models.plc_variable.PLCVariable`
instances known to the application.

Responsibilities
~~~~~~~~~~~~~~~~
* Load variables from a :class:`~config.config_loader.PLCConfig` (or from
  individual :class:`~config.config_loader.VariableConfig` objects).
* Provide O(1) lookup by symbolic name.
* Allow iteration over all registered variables.
* Prevent duplicate registrations.

The registry itself is designed as a plain class (not a singleton) so that
tests can instantiate independent registries without teardown concerns.

Usage example::

    from config.config_loader import ConfigLoader
    from models.variable_registry import VariableRegistry

    cfg = ConfigLoader.load("config/plc_config.xml")
    registry = VariableRegistry()
    registry.load_from_config(cfg)

    speed_var = registry.get("MAIN.nSpeed")
    for var in registry:
        print(var)
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from typing import Any, Optional

from config.config_loader import PLCConfig, VariableConfig
from models.plc_variable import PLCVariable
from utils.custom_exceptions import PLCVariableNotFoundError
from utils.logger import get_logger

log = get_logger(__name__)


class VariableRegistry:
    """
    Manages the complete set of :class:`~models.plc_variable.PLCVariable`
    instances for incoming and outgoing PLC data.

    All public methods are thread-safe.

    Attributes:
        _store:  Internal ``dict[name → PLCVariable]`` protected by ``_lock``.
        _lock:   :class:`threading.RLock` guarding ``_store``.
    """

    def __init__(self) -> None:
        self._store: dict[str, PLCVariable] = {}
        self._lock: threading.RLock = threading.RLock()

    # ------------------------------------------------------------------
    # Loading helpers
    # ------------------------------------------------------------------

    def load_from_config(self, config: PLCConfig) -> None:
        """
        Populate the registry using variable declarations from a
        :class:`~config.config_loader.PLCConfig`.

        Variables that already exist in the registry are **skipped** (their
        current state is preserved).

        Args:
            config: Parsed PLC configuration containing variable declarations.
        """
        for var_cfg in config.variables:
            self.register_from_config(var_cfg)
        log.info("VariableRegistry: loaded %d variable(s) from config", len(config.variables))

    def register_from_config(self, var_cfg: VariableConfig) -> PLCVariable:
        """
        Register a single variable described by a :class:`~config.config_loader.VariableConfig`.

        If a variable with the same name already exists, the existing instance
        is returned unchanged.

        Args:
            var_cfg: Variable descriptor loaded from XML.

        Returns:
            The (new or existing) :class:`PLCVariable` instance.
        """
        with self._lock:
            if var_cfg.name in self._store:
                log.debug("Variable '%s' is already registered; skipping", var_cfg.name)
                return self._store[var_cfg.name]

            var = PLCVariable(name=var_cfg.name, plc_type=var_cfg.plc_type)
            self._store[var_cfg.name] = var
            log.debug("Registered variable: %s [%s]", var_cfg.name, var_cfg.plc_type)
            return var

    def register(self, name: str, plc_type: str) -> PLCVariable:
        """
        Register a variable by name and type directly (without a config object).

        If a variable with the same name already exists, the existing instance
        is returned unchanged.

        Args:
            name:     Full symbolic name (e.g. ``"MAIN.nSpeed"``).
            plc_type: PLC data-type string (e.g. ``"INT"``).

        Returns:
            The (new or existing) :class:`PLCVariable` instance.
        """
        return self.register_from_config(VariableConfig(name=name, plc_type=plc_type))

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, name: str) -> PLCVariable:
        """
        Return the :class:`PLCVariable` with the given name.

        Args:
            name: Symbolic variable name.

        Returns:
            The matching :class:`PLCVariable`.

        Raises:
            PLCVariableNotFoundError: If no variable with that name is registered.
        """
        with self._lock:
            var = self._store.get(name)

        if var is None:
            raise PLCVariableNotFoundError(
                f"Variable '{name}' is not registered in the VariableRegistry.",
                variable_name=name,
            )
        return var

    def get_optional(self, name: str) -> Optional[PLCVariable]:
        """
        Return the :class:`PLCVariable` with the given name, or ``None`` if
        it is not registered.

        Args:
            name: Symbolic variable name.

        Returns:
            The matching :class:`PLCVariable`, or ``None``.
        """
        with self._lock:
            return self._store.get(name)

    def contains(self, name: str) -> bool:
        """Return ``True`` if *name* is registered."""
        with self._lock:
            return name in self._store

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def all_variables(self) -> list[PLCVariable]:
        """Return a snapshot list of all registered :class:`PLCVariable` instances."""
        with self._lock:
            return list(self._store.values())

    def names(self) -> list[str]:
        """Return a snapshot list of all registered variable names."""
        with self._lock:
            return list(self._store.keys())

    def unregister(self, name: str) -> None:
        """
        Remove a variable from the registry.

        Args:
            name: Name of the variable to remove.

        Raises:
            PLCVariableNotFoundError: If the variable is not registered.
        """
        with self._lock:
            if name not in self._store:
                raise PLCVariableNotFoundError(
                    f"Cannot unregister '{name}': variable not found in registry.",
                    variable_name=name,
                )
            del self._store[name]
            log.debug("Unregistered variable: '%s'", name)

    def clear(self) -> None:
        """Remove all variables from the registry."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
        log.warning("VariableRegistry cleared (%d variable(s) removed)", count)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def snapshot(self) -> list[dict[str, Any]]:
        """
        Return a JSON-serialisable list of dicts representing the current
        state of every registered variable.

        Returns:
            A list of dicts, one per variable (see :meth:`PLCVariable.to_dict`).
        """
        with self._lock:
            variables = list(self._store.values())
        return [v.to_dict() for v in variables]

    def to_json(self, *, indent: int = 2) -> str:
        """
        Serialise the full registry snapshot to a JSON string.

        Args:
            indent: JSON indentation level for pretty-printing.

        Returns:
            A JSON string representation of all current variable values.
        """
        return json.dumps(self.snapshot(), indent=indent, default=str)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)

    def __iter__(self) -> Iterator[PLCVariable]:
        with self._lock:
            snapshot = list(self._store.values())
        return iter(snapshot)

    def __contains__(self, name: object) -> bool:
        if not isinstance(name, str):
            return False
        return self.contains(name)

    def __repr__(self) -> str:
        with self._lock:
            names = list(self._store.keys())
        return f"VariableRegistry({names!r})"
