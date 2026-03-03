"""
plc_read_service.py
-------------------
High-level service for reading PLC variable values through the ADS layer.

The read service: 
    1. Looks up the :class:`~models.plc_variable.PLCVariable` in the
       :class:`~models.variable_registry.VariableRegistry`.
    2. Resolves the pyads type via :class:`~core.datatype_converter.DataTypeConverter`.
    3. Delegates the actual ADS read to :class:`~core.ads_client.ADSClient`.
    4. Converts the raw pyads result to a Python-native value.
    5. Updates the :class:`~models.plc_variable.PLCVariable` with the new value
       and timestamp.
    6. Returns the Python value to the caller.

The service layer is intentionally stateless (no mutable instance variables
beyond injected dependencies), making it straightforward to test.
"""

from __future__ import annotations

from typing import Any

from core.ads_client import ADSClient
from core.datatype_converter import DataTypeConverter
from models.variable_registry import VariableRegistry
from utils.custom_exceptions import PLCReadError, PLCVariableNotFoundError
from utils.logger import get_logger

log = get_logger(__name__)


class PLCReadService:
    """
    Provides high-level ``read_variable`` operations for the application.

    Args:
        ads_client: Low-level ADS client.
        registry:   Variable registry used to look up variable metadata.

    Example::

        read_svc = PLCReadService(ads_client, registry)

        speed = read_svc.read_variable("MAIN.nSpeed")
        print(speed)   # e.g. 1500

        snapshot = read_svc.read_all()
        for name, value in snapshot.items():
            print(name, "=", value)
    """

    def __init__(self, ads_client: ADSClient, registry: VariableRegistry) -> None:
        self._client = ads_client
        self._registry = registry

    # ------------------------------------------------------------------
    # Single variable
    # ------------------------------------------------------------------

    def read_variable(self, name: str) -> Any:
        """
        Read the current value of a registered PLC variable from the PLC.

        The variable's :class:`~models.plc_variable.PLCVariable` instance is
        updated with the freshly read value and an up-to-date timestamp.

        Args:
            name: Symbolic variable name (e.g. ``"MAIN.nSpeed"``).

        Returns:
            The Python-native current value reported by the PLC.

        Raises:
            PLCVariableNotFoundError: If *name* is not in the registry.
            PLCReadError:             If the ADS read operation fails.
        """
        # Step 1 – resolve registered variable metadata.
        var = self._registry.get(name)  # raises PLCVariableNotFoundError if absent

        # Step 2 – resolve pyads type constant.
        plc_type = DataTypeConverter.get_pyads_type(var.plc_type)

        # Step 3 – perform ADS read (raises PLCReadError on failure).
        raw_value = self._client.read_by_name(name, plc_type)

        # Step 4 – convert raw value to Python.
        python_value = DataTypeConverter.to_python(var.plc_type, raw_value)

        # Step 5 – update the domain model.
        var.update_value(python_value)

        log.info("Read '%s' [%s] = %r", name, var.plc_type, python_value)
        return python_value

    def read_variable_safe(self, name: str, default: Any = None) -> Any:
        """
        Read a variable, returning *default* on any error instead of raising.

        Suitable for background polling loops where a single read failure
        should not abort the entire cycle.

        Args:
            name:    Symbolic variable name.
            default: Value to return if the read fails.

        Returns:
            The current PLC value, or *default* on error.
        """
        try:
            return self.read_variable(name)
        except (PLCReadError, PLCVariableNotFoundError) as exc:
            log.warning("read_variable_safe('%s') failed: %s – returning default", name, exc)
            return default
        except Exception as exc:  # noqa: BLE001
            log.error(
                "Unexpected error in read_variable_safe('%s'): %s",
                name,
                exc,
                exc_info=True,
            )
            return default

    # ------------------------------------------------------------------
    # Bulk read
    # ------------------------------------------------------------------

    def read_all(self) -> dict[str, Any]:
        """
        Read every variable registered in the registry from the PLC.

        Failures for individual variables are logged as warnings and the
        corresponding entry in the returned dict is set to ``None``.

        Returns:
            A dict mapping variable names to their current Python values
            (``None`` for any variable whose read failed).
        """
        results: dict[str, Any] = {}
        for var in self._registry:
            results[var.name] = self.read_variable_safe(var.name, default=None)
        return results

    def read_multiple(self, names: list[str]) -> dict[str, Any]:
        """
        Read a specific subset of registered variables.

        Args:
            names: List of symbolic variable names.

        Returns:
            A dict mapping each name to its current Python value (``None``
            for failed reads).
        """
        return {name: self.read_variable_safe(name) for name in names}
