"""
test_read_write_services.py
---------------------------
Unit tests for :class:`~services.plc_read_service.PLCReadService` and
:class:`~services.plc_write_service.PLCWriteService`.

All ADS I/O is mocked so these tests run without a real PLC.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch, call
from typing import Any

import pytest

from models.plc_variable import PLCVariable
from models.variable_registry import VariableRegistry
from services.plc_read_service import PLCReadService
from services.plc_write_service import PLCWriteService
from utils.custom_exceptions import (
    PLCReadError,
    PLCWriteError,
    PLCVariableNotFoundError,
    DataTypeMismatchError,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def registry() -> VariableRegistry:
    reg = VariableRegistry()
    reg.register("MAIN.bMotorOn",    "BOOL")
    reg.register("MAIN.nSpeed",      "INT")
    reg.register("MAIN.rTemperature","REAL")
    reg.register("MAIN.sStatus",     "STRING")
    return reg


@pytest.fixture
def mock_ads_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def read_service(mock_ads_client: MagicMock, registry: VariableRegistry) -> PLCReadService:
    return PLCReadService(ads_client=mock_ads_client, registry=registry)


@pytest.fixture
def write_service(mock_ads_client: MagicMock, registry: VariableRegistry) -> PLCWriteService:
    return PLCWriteService(ads_client=mock_ads_client, registry=registry)


# ===========================================================================
# PLCReadService
# ===========================================================================

class TestPLCReadServiceHappyPath:
    def test_read_bool_returns_python_bool(
        self, read_service: PLCReadService, mock_ads_client: MagicMock
    ) -> None:
        mock_ads_client.read_by_name.return_value = 1  # pyads returns int for BOOL
        value = read_service.read_variable("MAIN.bMotorOn")
        assert value is True

    def test_read_int_returns_int(
        self, read_service: PLCReadService, mock_ads_client: MagicMock
    ) -> None:
        mock_ads_client.read_by_name.return_value = 1500
        value = read_service.read_variable("MAIN.nSpeed")
        assert value == 1500
        assert isinstance(value, int)

    def test_read_real_returns_float(
        self, read_service: PLCReadService, mock_ads_client: MagicMock
    ) -> None:
        mock_ads_client.read_by_name.return_value = 22.5
        value = read_service.read_variable("MAIN.rTemperature")
        assert isinstance(value, float)

    def test_read_updates_variable_in_registry(
        self,
        read_service: PLCReadService,
        mock_ads_client: MagicMock,
        registry: VariableRegistry,
    ) -> None:
        mock_ads_client.read_by_name.return_value = 999
        read_service.read_variable("MAIN.nSpeed")
        var = registry.get("MAIN.nSpeed")
        assert var.current_value == 999

    def test_read_all_returns_all_variables(
        self, read_service: PLCReadService, mock_ads_client: MagicMock
    ) -> None:
        mock_ads_client.read_by_name.return_value = 0
        results = read_service.read_all()
        assert set(results.keys()) == {
            "MAIN.bMotorOn", "MAIN.nSpeed", "MAIN.rTemperature", "MAIN.sStatus"
        }

    def test_read_multiple_subset(
        self, read_service: PLCReadService, mock_ads_client: MagicMock
    ) -> None:
        mock_ads_client.read_by_name.return_value = 5
        results = read_service.read_multiple(["MAIN.bMotorOn", "MAIN.nSpeed"])
        assert len(results) == 2


class TestPLCReadServiceErrorHandling:
    def test_unknown_variable_raises(self, read_service: PLCReadService) -> None:
        with pytest.raises(PLCVariableNotFoundError):
            read_service.read_variable("MAIN.nonExistent")

    def test_ads_error_raises_plc_read_error(
        self, read_service: PLCReadService, mock_ads_client: MagicMock
    ) -> None:
        mock_ads_client.read_by_name.side_effect = PLCReadError("ADS error")
        with pytest.raises(PLCReadError):
            read_service.read_variable("MAIN.nSpeed")

    def test_read_variable_safe_returns_default_on_error(
        self, read_service: PLCReadService, mock_ads_client: MagicMock
    ) -> None:
        mock_ads_client.read_by_name.side_effect = PLCReadError("fail")
        result = read_service.read_variable_safe("MAIN.nSpeed", default=-1)
        assert result == -1

    def test_read_all_returns_none_for_failed_variable(
        self, read_service: PLCReadService, mock_ads_client: MagicMock
    ) -> None:
        mock_ads_client.read_by_name.side_effect = PLCReadError("fail")
        results = read_service.read_all()
        assert all(v is None for v in results.values())


# ===========================================================================
# PLCWriteService
# ===========================================================================

class TestPLCWriteServiceHappyPath:
    def test_write_bool(
        self, write_service: PLCWriteService, mock_ads_client: MagicMock
    ) -> None:
        write_service.write_variable("MAIN.bMotorOn", True)
        mock_ads_client.write_by_name.assert_called_once()
        args = mock_ads_client.write_by_name.call_args[0]
        assert args[0] == "MAIN.bMotorOn"
        assert args[1] is True

    def test_write_int(
        self, write_service: PLCWriteService, mock_ads_client: MagicMock
    ) -> None:
        write_service.write_variable("MAIN.nSpeed", 1500)
        mock_ads_client.write_by_name.assert_called_once()

    def test_write_real(
        self, write_service: PLCWriteService, mock_ads_client: MagicMock
    ) -> None:
        write_service.write_variable("MAIN.rTemperature", 37.5)
        mock_ads_client.write_by_name.assert_called_once()

    def test_write_updates_local_variable(
        self,
        write_service: PLCWriteService,
        mock_ads_client: MagicMock,
        registry: VariableRegistry,
    ) -> None:
        write_service.write_variable("MAIN.nSpeed", 800)
        var = registry.get("MAIN.nSpeed")
        assert var.current_value == 800

    def test_write_multiple_returns_true_for_success(
        self, write_service: PLCWriteService, mock_ads_client: MagicMock
    ) -> None:
        results = write_service.write_multiple({"MAIN.nSpeed": 0, "MAIN.bMotorOn": False})
        assert all(results.values())

    def test_write_bool_convenience(
        self, write_service: PLCWriteService, mock_ads_client: MagicMock
    ) -> None:
        write_service.write_bool("MAIN.bMotorOn", False)
        mock_ads_client.write_by_name.assert_called_once()

    def test_write_int_convenience(
        self, write_service: PLCWriteService, mock_ads_client: MagicMock
    ) -> None:
        write_service.write_int("MAIN.nSpeed", 123)
        mock_ads_client.write_by_name.assert_called_once()

    def test_write_float_convenience(
        self, write_service: PLCWriteService, mock_ads_client: MagicMock
    ) -> None:
        write_service.write_float("MAIN.rTemperature", 19.9)
        mock_ads_client.write_by_name.assert_called_once()

    def test_write_string_convenience(
        self, write_service: PLCWriteService, mock_ads_client: MagicMock
    ) -> None:
        write_service.write_string("MAIN.sStatus", "OK")
        mock_ads_client.write_by_name.assert_called_once()


class TestPLCWriteServiceErrorHandling:
    def test_unknown_variable_raises(self, write_service: PLCWriteService) -> None:
        with pytest.raises(PLCVariableNotFoundError):
            write_service.write_variable("MAIN.nonExistent", 0)

    def test_type_mismatch_raises(self, write_service: PLCWriteService) -> None:
        with pytest.raises(DataTypeMismatchError):
            write_service.write_variable("MAIN.nSpeed", "not_an_int")

    def test_ads_error_raises_plc_write_error(
        self, write_service: PLCWriteService, mock_ads_client: MagicMock
    ) -> None:
        mock_ads_client.write_by_name.side_effect = PLCWriteError("ADS error")
        with pytest.raises(PLCWriteError):
            write_service.write_variable("MAIN.nSpeed", 100)

    def test_write_variable_safe_returns_false_on_type_error(
        self, write_service: PLCWriteService
    ) -> None:
        # Write a string to an INT variable – type mismatch.
        result = write_service.write_variable_safe("MAIN.nSpeed", "bad")
        assert result is False

    def test_write_variable_safe_returns_false_on_ads_error(
        self, write_service: PLCWriteService, mock_ads_client: MagicMock
    ) -> None:
        mock_ads_client.write_by_name.side_effect = PLCWriteError("fail")
        result = write_service.write_variable_safe("MAIN.nSpeed", 10)
        assert result is False

    def test_write_bool_convenience_rejects_int(
        self, write_service: PLCWriteService
    ) -> None:
        with pytest.raises(DataTypeMismatchError):
            write_service.write_bool("MAIN.bMotorOn", 1)  # int, not bool

    def test_write_int_convenience_rejects_bool(
        self, write_service: PLCWriteService
    ) -> None:
        with pytest.raises(DataTypeMismatchError):
            write_service.write_int("MAIN.nSpeed", True)  # bool is a subclass of int

    def test_out_of_range_int_raises(self, write_service: PLCWriteService) -> None:
        """INT range is [-32768, 32767]; writing 99999 should raise DataTypeMismatchError."""
        # The registry has MAIN.nSpeed as type INT.
        with pytest.raises(DataTypeMismatchError):
            write_service.write_variable("MAIN.nSpeed", 99_999)
