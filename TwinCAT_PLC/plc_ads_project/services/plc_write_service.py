"""
plc_write_service.py
--------------------
High-level service for writing values to PLC variables through the ADS layer.

The write service:
    1. Looks up the :class:`~models.plc_variable.PLCVariable` in the
       :class:`~models.variable_registry.VariableRegistry`.
    2. Validates that the Python value is type-compatible with the declared
       PLC data type via :class:`~core.datatype_converter.DataTypeConverter`.
    3. Resolves the pyads type constant.
    4. Delegates to :class:`~core.ads_client.ADSClient`.
    5. Optimistically updates the local :class:`~models.plc_variable.PLCVariable`
       if the write succeeds (the ADS notification will later confirm the
       actual PLC value).
"""

from __future__ import annotations

from typing import Any

from core.ads_client import ADSClient
from core.datatype_converter import DataTypeConverter
from models.variable_registry import VariableRegistry
from utils.custom_exceptions import PLCWriteError, PLCVariableNotFoundError, DataTypeMismatchError
from utils.logger import get_logger

log = get_logger(__name__)


class PLCWriteService:
    """
    Provides high-level ``write_variable`` operations for the application.

    Args:
        ads_client: Low-level ADS client.
        registry:   Variable registry used to look up variable metadata.

    Example::

        write_svc = PLCWriteService(ads_client, registry)

        write_svc.write_variable("MAIN.bMotorOn", True)
        write_svc.write_variable("MAIN.nSpeed", 1500)
        write_svc.write_variable("MAIN.rTemperature", 22.5)
    """

    def __init__(self, ads_client: ADSClient, registry: VariableRegistry) -> None:
        self._client = ads_client
        self._registry = registry

    # ------------------------------------------------------------------
    # Single variable
    # ------------------------------------------------------------------

    def write_variable(self, name: str, value: Any) -> None:
        """
        Write *value* to the PLC variable identified by *name*.

        Validates the value type against the declared PLC type **before**
        making the ADS call, preventing silent data truncation or corruption
        on the PLC side.

        Args:
            name:  Symbolic variable name (e.g. ``"MAIN.nSpeed"``).
            value: Python value to write.  Must be compatible with the
                   variable's declared PLC type.

        Raises:
            PLCVariableNotFoundError: If *name* is not registered.
            DataTypeMismatchError:    If *value* is incompatible with the
                                      declared PLC type.
            PLCWriteError:            If the ADS write operation fails.
        """
        # Step 1 – resolve variable metadata.
        var = self._registry.get(name)  # raises PLCVariableNotFoundError

        # Step 2 – validate Python value type *before* making the ADS call.
        DataTypeConverter.validate_write_value(
            plc_type=var.plc_type,
            value=value,
            variable_name=name,
        )

        # Step 3 – resolve pyads type constant.
        plc_type = DataTypeConverter.get_pyads_type(var.plc_type)

        # Step 4 – perform ADS write.
        self._client.write_by_name(name, value, plc_type)

        # Step 5 – update local model optimistically.
        # The notification callback will overwrite this with the confirmed
        # PLC value; this update keeps read-your-writes consistent.
        try:
            var.update_value(value)
        except DataTypeMismatchError:
            # update_value performs its own validation; swallow here because
            # the write already succeeded on the PLC side.
            pass

        log.info("Wrote '%s' [%s] ← %r", name, var.plc_type, value)

    def write_variable_safe(self, name: str, value: Any) -> bool:
        """
        Write a variable, returning ``False`` on any error instead of raising.

        Suitable for fire-and-forget write scenarios.

        Args:
            name:  Symbolic variable name.
            value: Value to write.

        Returns:
            ``True`` if the write succeeded, ``False`` on any error.
        """
        try:
            self.write_variable(name, value)
            return True
        except (PLCWriteError, PLCVariableNotFoundError, DataTypeMismatchError) as exc:
            log.warning("write_variable_safe('%s', %r) failed: %s", name, value, exc)
            return False
        except Exception as exc:  # noqa: BLE001
            log.error(
                "Unexpected error in write_variable_safe('%s'): %s",
                name,
                exc,
                exc_info=True,
            )
            return False

    # ------------------------------------------------------------------
    # Bulk write
    # ------------------------------------------------------------------

    def write_multiple(self, values: dict[str, Any]) -> dict[str, bool]:
        """
        Write multiple variables in sequence.

        Args:
            values: ``{variable_name: value}`` mapping.

        Returns:
            A ``{variable_name: success}`` dict indicating the outcome for
            each variable.
        """
        results: dict[str, bool] = {}
        for name, value in values.items():
            results[name] = self.write_variable_safe(name, value)
        return results

    # ------------------------------------------------------------------
    # Convenience typed write methods
    # ------------------------------------------------------------------

    def write_bool(self, name: str, value: bool) -> None:
        """Write a BOOL value with enforced Python ``bool`` type."""
        if not isinstance(value, bool):
            raise DataTypeMismatchError(
                f"write_bool expects a Python bool, got {type(value).__name__!r}.",
                variable_name=name,
                expected_type="BOOL",
                received_type=type(value).__name__,
                value=value,
            )
        self.write_variable(name, value)

    def write_int(self, name: str, value: int) -> None:
        """Write an integer value (INT / DINT / UDINT …) with enforced Python ``int`` type."""
        if not isinstance(value, int) or isinstance(value, bool):
            raise DataTypeMismatchError(
                f"write_int expects a Python int, got {type(value).__name__!r}.",
                variable_name=name,
                expected_type="INT",
                received_type=type(value).__name__,
                value=value,
            )
        self.write_variable(name, value)

    def write_float(self, name: str, value: float) -> None:
        """Write a floating-point value (REAL / LREAL) with enforced Python ``float`` type."""
        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise DataTypeMismatchError(
                f"write_float expects a Python float or int, got {type(value).__name__!r}.",
                variable_name=name,
                expected_type="REAL",
                received_type=type(value).__name__,
                value=value,
            )
        self.write_variable(name, float(value))

    def write_string(self, name: str, value: str) -> None:
        """Write a STRING value with enforced Python ``str`` type."""
        if not isinstance(value, str):
            raise DataTypeMismatchError(
                f"write_string expects a Python str, got {type(value).__name__!r}.",
                variable_name=name,
                expected_type="STRING",
                received_type=type(value).__name__,
                value=value,
            )
        self.write_variable(name, value)
