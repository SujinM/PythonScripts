"""
datatype_converter.py
---------------------
Maps PLC type strings (as declared in *plc_config.xml*) to the corresponding
``pyads`` C-type constants used by :func:`pyads.Connection.read_by_name` and
:func:`pyads.Connection.write_by_name`, and provides helpers to convert the
raw values returned by pyads into idiomatic Python objects.

Design decisions
~~~~~~~~~~~~~~~~
* The mapping dictionary ``PLC_TYPE_MAP`` is the single source of truth for
  the type system.  Adding support for a new PLC type therefore requires only
  one entry in the dict (plus, optionally, an entry in ``_PYTHON_COERCERS``).
* STRING handling uses a configurable length property on the pyads
  ``PLCTYPE_STRING`` type – see :meth:`DataTypeConverter.get_pyads_type` and
  :const:`DEFAULT_STRING_LENGTH`.
* ARRAY types require application-level knowledge of the element type and
  array dimensions; a raw ``bytes`` value is returned and the caller must
  decode it.
"""

from __future__ import annotations

from typing import Any, Final

import pyads

from utils.custom_exceptions import DataTypeMismatchError
from utils.logger import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default maximum length (characters) used when creating a STRING pyads type.
DEFAULT_STRING_LENGTH: Final[int] = 80

# ---------------------------------------------------------------------------
# Primary type map  PLC type string → pyads C-type constant
# ---------------------------------------------------------------------------
#: Maps upper-cased PLC type names to the corresponding pyads constant.
PLC_TYPE_MAP: dict[str, Any] = {
    "BOOL":   pyads.PLCTYPE_BOOL,
    "BYTE":   pyads.PLCTYPE_BYTE,
    "INT":    pyads.PLCTYPE_INT,
    "UINT":   pyads.PLCTYPE_UINT,
    "DINT":   pyads.PLCTYPE_DINT,
    "UDINT":  pyads.PLCTYPE_UDINT,
    "SINT":   pyads.PLCTYPE_SINT,
    "USINT":  pyads.PLCTYPE_USINT,
    "LINT":   pyads.PLCTYPE_LINT,
    "ULINT":  pyads.PLCTYPE_ULINT,
    "REAL":   pyads.PLCTYPE_REAL,
    "LREAL":  pyads.PLCTYPE_LREAL,
    # STRING and ARRAY are handled dynamically – see get_pyads_type().
}

# ---------------------------------------------------------------------------
# Python-side coercion helpers
# ---------------------------------------------------------------------------
#: Maps PLC type → callable that converts a raw pyads value to Python.
_PYTHON_COERCERS: dict[str, Any] = {
    "BOOL":   bool,
    "BYTE":   int,
    "INT":    int,
    "UINT":   int,
    "DINT":   int,
    "UDINT":  int,
    "SINT":   int,
    "USINT":  int,
    "LINT":   int,
    "ULINT":  int,
    "REAL":   float,
    "LREAL":  float,
    "STRING": str,
    # ARRAY values pass through as-is (list / bytes from pyads).
}


class DataTypeConverter:
    """
    Stateless converter between PLC type strings and pyads types.

    All methods are class-level so the class acts as a namespace / service
    rather than a stateful object.

    Usage::

        plc_type_obj = DataTypeConverter.get_pyads_type("REAL")
        python_value = DataTypeConverter.to_python("REAL", raw_value)
        DataTypeConverter.validate_write_value("INT", 42)
    """

    @classmethod
    def get_pyads_type(
        cls,
        plc_type: str,
        *,
        string_length: int = DEFAULT_STRING_LENGTH,
        array_type: Any = None,
        array_size: int = 1,
    ) -> Any:
        """
        Return the pyads type constant for a given PLC type string.

        Args:
            plc_type:      Upper-cased PLC type string (e.g. ``"INT"``).
            string_length: Override the maximum string length when
                           *plc_type* is ``"STRING"``.
            array_type:    The element type for ``"ARRAY"`` (a pyads constant).
            array_size:    Number of elements for ``"ARRAY"``.

        Returns:
            The corresponding pyads type constant, or a parametrised type
            for STRING / ARRAY.

        Raises:
            DataTypeMismatchError: If the type string is unknown.
        """
        upper = plc_type.upper()

        if upper == "STRING":
            # In pyads 3.x, PLCTYPE_STRING is ctypes.c_char.
            # read_by_name / write_by_name handle the null-terminated string
            # buffer internally when passed PLCTYPE_STRING.
            # For a custom-length buffer (e.g. STRING(80)), use c_char * length.
            if string_length != DEFAULT_STRING_LENGTH:
                import ctypes  # noqa: PLC0415
                return ctypes.c_char * (string_length + 1)  # +1 for null terminator
            return pyads.PLCTYPE_STRING

        if upper == "ARRAY":
            if array_type is None:
                # Fall back to raw bytes; caller must handle decoding.
                log.warning(
                    "ARRAY type requested without specifying element type; "
                    "returning raw BYTE array of size %d",
                    array_size,
                )
                return pyads.PLCTYPE_BYTE * array_size
            return array_type * array_size

        result = PLC_TYPE_MAP.get(upper)
        if result is None:
            raise DataTypeMismatchError(
                f"Unknown PLC type '{plc_type}'. "
                f"Supported basic types: {sorted(PLC_TYPE_MAP.keys())}",
                expected_type=plc_type,
            )
        log.debug("Resolved PLC type '%s' → %s", plc_type, result)
        return result

    @classmethod
    def to_python(cls, plc_type: str, raw_value: Any) -> Any:
        """
        Convert a raw value returned by pyads into an idiomatic Python object.

        Most conversions are trivial (``int``, ``float``, ``bool``).  STRING
        values are decoded from bytes when necessary.

        Args:
            plc_type:  Upper-cased PLC type string.
            raw_value: Raw value from pyads.

        Returns:
            A Python-native representation of *raw_value*.
        """
        upper = plc_type.upper()
        coercer = _PYTHON_COERCERS.get(upper)

        if coercer is None:
            # ARRAY or unknown – return as-is.
            log.debug("No coercion for PLC type '%s'; returning raw value", plc_type)
            return raw_value

        try:
            if upper == "STRING":
                # pyads may return bytes for strings in notification callbacks.
                if isinstance(raw_value, (bytes, bytearray)):
                    return raw_value.rstrip(b"\x00").decode("utf-8", errors="replace")
                return str(raw_value)

            if upper == "BOOL":
                # pyads sometimes returns 0/1 integers for BOOL.
                return bool(raw_value)

            return coercer(raw_value)

        except (ValueError, TypeError) as exc:
            log.warning(
                "Could not coerce raw value %r (PLC type '%s') to Python: %s",
                raw_value,
                plc_type,
                exc,
            )
            return raw_value

    @classmethod
    def validate_write_value(cls, plc_type: str, value: Any, variable_name: str = "") -> None:
        """
        Raise :class:`~utils.custom_exceptions.DataTypeMismatchError` if
        *value* is not compatible with *plc_type*.

        This method is deliberately strict for numeric types to prevent
        silent data truncation on the PLC side.

        Args:
            plc_type:      The declared PLC type of the target variable.
            value:         The Python value to be written.
            variable_name: Optional variable name used in the exception message.

        Raises:
            DataTypeMismatchError: If the value is incompatible.
        """
        upper = plc_type.upper()

        _strict: dict[str, tuple[type, ...]] = {
            "BOOL":   (bool, int),
            "BYTE":   (int,),
            "INT":    (int,),
            "UINT":   (int,),
            "DINT":   (int,),
            "UDINT":  (int,),
            "SINT":   (int,),
            "USINT":  (int,),
            "LINT":   (int,),
            "ULINT":  (int,),
            "REAL":   (float, int),
            "LREAL":  (float, int),
            "STRING": (str,),
            "ARRAY":  (list, tuple, bytes, bytearray),
        }

        allowed = _strict.get(upper)
        if allowed is None:
            log.warning("No write validation rule for PLC type '%s'; skipping", plc_type)
            return

        if not isinstance(value, allowed):
            raise DataTypeMismatchError(
                f"Cannot write {type(value).__name__!r} to variable '{variable_name}' "
                f"declared as '{plc_type}'. "
                f"Expected one of: {' | '.join(t.__name__ for t in allowed)}.",
                variable_name=variable_name,
                expected_type=plc_type,
                received_type=type(value).__name__,
                value=value,
            )

        # Range checks for bounded integer types.
        _ranges: dict[str, tuple[int, int]] = {
            "SINT":  (-128, 127),
            "USINT": (0, 255),
            "BYTE":  (0, 255),
            "INT":   (-32_768, 32_767),
            "UINT":  (0, 65_535),
            "DINT":  (-2_147_483_648, 2_147_483_647),
            "UDINT": (0, 4_294_967_295),
            "LINT":  (-9_223_372_036_854_775_808, 9_223_372_036_854_775_807),
            "ULINT": (0, 18_446_744_073_709_551_615),
        }
        if upper in _ranges and isinstance(value, int):
            lo, hi = _ranges[upper]
            if not lo <= value <= hi:
                raise DataTypeMismatchError(
                    f"Value {value} is out of range for PLC type '{plc_type}' "
                    f"[{lo}, {hi}].",
                    variable_name=variable_name,
                    expected_type=plc_type,
                    received_type=type(value).__name__,
                    value=value,
                )
