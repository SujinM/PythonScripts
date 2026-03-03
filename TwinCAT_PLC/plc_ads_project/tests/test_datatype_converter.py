"""
test_datatype_converter.py
--------------------------
Unit tests for :class:`~core.datatype_converter.DataTypeConverter`.

Tests cover:
    * get_pyads_type – correct pyads constants returned for known types.
    * get_pyads_type – STRING returns a parametrised type.
    * get_pyads_type – unknown type raises DataTypeMismatchError.
    * to_python – coercion for each supported type.
    * to_python – STRING bytes decoding.
    * validate_write_value – passes for compatible values.
    * validate_write_value – raises for incompatible values.
    * validate_write_value – raises for out-of-range integers.
"""

from __future__ import annotations

import pyads
import pytest

from core.datatype_converter import DataTypeConverter, PLC_TYPE_MAP
from utils.custom_exceptions import DataTypeMismatchError


# ---------------------------------------------------------------------------
# get_pyads_type – known types
# ---------------------------------------------------------------------------

class TestGetPyadsType:
    @pytest.mark.parametrize("plc_type,expected", [
        ("BOOL",  pyads.PLCTYPE_BOOL),
        ("INT",   pyads.PLCTYPE_INT),
        ("DINT",  pyads.PLCTYPE_DINT),
        ("UDINT", pyads.PLCTYPE_UDINT),
        ("REAL",  pyads.PLCTYPE_REAL),
        ("LREAL", pyads.PLCTYPE_LREAL),
    ])
    def test_returns_correct_constant(self, plc_type: str, expected: object) -> None:
        result = DataTypeConverter.get_pyads_type(plc_type)
        assert result is expected

    def test_case_insensitive(self) -> None:
        lower_result = DataTypeConverter.get_pyads_type("int")
        upper_result = DataTypeConverter.get_pyads_type("INT")
        assert lower_result is upper_result

    def test_string_returns_parametrised_type(self) -> None:
        result = DataTypeConverter.get_pyads_type("STRING")
        # pyads.PLCTYPE_STRING() returns a ctypes array type; it should be callable.
        assert result is not None

    def test_string_custom_length(self) -> None:
        result = DataTypeConverter.get_pyads_type("STRING", string_length=40)
        assert result is not None

    def test_unknown_type_raises(self) -> None:
        with pytest.raises(DataTypeMismatchError, match="WORD"):
            DataTypeConverter.get_pyads_type("WORD")


# ---------------------------------------------------------------------------
# to_python – coercion
# ---------------------------------------------------------------------------

class TestToPython:
    @pytest.mark.parametrize("plc_type,raw,expected_type", [
        ("BOOL",  1,     bool),
        ("BOOL",  0,     bool),
        ("INT",   100,   int),
        ("DINT",  -500,  int),
        ("UDINT", 1000,  int),
        ("REAL",  3.14,  float),
        ("LREAL", 2.718, float),
    ])
    def test_numeric_coercion(
        self, plc_type: str, raw: object, expected_type: type
    ) -> None:
        result = DataTypeConverter.to_python(plc_type, raw)
        assert isinstance(result, expected_type)

    def test_bool_coercion_from_zero(self) -> None:
        assert DataTypeConverter.to_python("BOOL", 0) is False

    def test_bool_coercion_from_one(self) -> None:
        assert DataTypeConverter.to_python("BOOL", 1) is True

    def test_string_passthrough(self) -> None:
        result = DataTypeConverter.to_python("STRING", "RUNNING")
        assert result == "RUNNING"
        assert isinstance(result, str)

    def test_string_from_bytes(self) -> None:
        raw = b"RUNNING\x00\x00"
        result = DataTypeConverter.to_python("STRING", raw)
        assert result == "RUNNING"
        assert isinstance(result, str)

    def test_string_from_bytes_strips_null(self) -> None:
        raw = b"OK\x00\x00\x00"
        result = DataTypeConverter.to_python("STRING", raw)
        assert result == "OK"

    def test_array_passthrough(self) -> None:
        raw = [1, 2, 3]
        result = DataTypeConverter.to_python("ARRAY", raw)
        assert result == raw  # No coercion for ARRAY

    def test_unknown_type_passthrough(self) -> None:
        raw = 0xFF
        result = DataTypeConverter.to_python("WORD", raw)
        assert result == raw


# ---------------------------------------------------------------------------
# validate_write_value – happy path
# ---------------------------------------------------------------------------

class TestValidateWriteValueHappyPath:
    @pytest.mark.parametrize("plc_type,value", [
        ("BOOL",   True),
        ("BOOL",   False),
        ("INT",    0),
        ("INT",    -1000),
        ("INT",    32767),
        ("DINT",   2_000_000),
        ("UDINT",  0),
        ("REAL",   1.5),
        ("LREAL",  3.14),
        ("STRING", "hello"),
    ])
    def test_no_exception_for_valid(self, plc_type: str, value: object) -> None:
        DataTypeConverter.validate_write_value(plc_type, value, "TEST.x")


# ---------------------------------------------------------------------------
# validate_write_value – type mismatch
# ---------------------------------------------------------------------------

class TestValidateWriteValueTypeMismatch:
    @pytest.mark.parametrize("plc_type,bad_value", [
        ("BOOL",   "yes"),
        ("INT",    3.14),
        ("REAL",   "hot"),
        ("STRING", 42),
        ("DINT",   [1, 2]),
    ])
    def test_type_mismatch_raises(self, plc_type: str, bad_value: object) -> None:
        with pytest.raises(DataTypeMismatchError):
            DataTypeConverter.validate_write_value(plc_type, bad_value, "TEST.x")

    def test_error_includes_variable_name(self) -> None:
        with pytest.raises(DataTypeMismatchError) as exc_info:
            DataTypeConverter.validate_write_value("INT", "bad", "MAIN.nSpeed")
        assert exc_info.value.variable_name == "MAIN.nSpeed"


# ---------------------------------------------------------------------------
# validate_write_value – range errors
# ---------------------------------------------------------------------------

class TestValidateWriteValueRangeErrors:
    @pytest.mark.parametrize("plc_type,out_of_range", [
        ("SINT",   200),     # max 127
        ("SINT",  -200),     # min -128
        ("USINT",  300),     # max 255
        ("USINT",  -1),      # min 0
        ("INT",    40_000),  # max 32767
        ("INT",   -40_000),  # min -32768
        ("UINT",   70_000),  # max 65535
        ("DINT",   3_000_000_000),   # max ~2.1B
        ("UDINT",  5_000_000_000),   # max ~4.3B
    ])
    def test_out_of_range_raises(self, plc_type: str, out_of_range: int) -> None:
        with pytest.raises(DataTypeMismatchError, match="out of range"):
            DataTypeConverter.validate_write_value(plc_type, out_of_range, "TEST.x")

    def test_boundary_value_accepted(self) -> None:
        # INT max = 32767
        DataTypeConverter.validate_write_value("INT", 32767, "TEST.x")

    def test_below_boundary_accepted(self) -> None:
        # INT min = -32768
        DataTypeConverter.validate_write_value("INT", -32768, "TEST.x")


# ---------------------------------------------------------------------------
# PLC_TYPE_MAP completeness
# ---------------------------------------------------------------------------

class TestPLCTypeMap:
    def test_map_contains_basic_types(self) -> None:
        for t in ("BOOL", "INT", "DINT", "UDINT", "REAL", "LREAL"):
            assert t in PLC_TYPE_MAP, f"Missing PLC type '{t}' in PLC_TYPE_MAP"
