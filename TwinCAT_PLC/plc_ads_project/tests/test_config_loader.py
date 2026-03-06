"""
test_config_loader.py
---------------------
Unit tests for :class:`~config.config_loader.ConfigLoader`.

Tests cover:
    * Successful load of the bundled ``plc_config.xml``.
    * Correct parsing of all sections (Connection, Reconnect, Notifications,
      Heartbeat, Variables).
    * Missing required XML elements raise XMLConfigError.
    * Unsupported PLC type raises XMLConfigError.
    * Duplicate variable names raise XMLConfigError.
    * Non-existent file raises XMLConfigError.
    * Malformed XML raises XMLConfigError.
"""

from __future__ import annotations

import os
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from config.config_loader import ConfigLoader, PLCConfig, SUPPORTED_TYPES
from core.datatype_converter import PLC_TYPE_MAP
from utils.custom_exceptions import XMLConfigError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_xml(tmp_path: Path, content: str) -> str:
    """Write *content* to a temp XML file and return the file path."""
    p = tmp_path / "test_config.xml"
    # strip() removes the leading newline that textwrap.dedent leaves when the
    # triple-quoted string starts with a newline – Python 3.13 XML parser rejects
    # any whitespace before the <?xml ...?> declaration.
    p.write_text(textwrap.dedent(content).strip(), encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------
# Minimal valid XML
# ---------------------------------------------------------------------------

MINIMAL_XML = """
    <?xml version="1.0" encoding="UTF-8"?>
    <PLCConfig>
        <Connection>
            <AMSNetID>1.2.3.4.1.1</AMSNetID>
            <IPAddress>192.168.1.10</IPAddress>
            <Port>851</Port>
        </Connection>
        <Variables>
            <Variable>
                <Name>MAIN.bTest</Name>
                <Type>BOOL</Type>
            </Variable>
        </Variables>
    </PLCConfig>
"""


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestLoadMinimal:
    def test_returns_plc_config(self, tmp_path: Path) -> None:
        cfg = ConfigLoader.load(_write_xml(tmp_path, MINIMAL_XML))
        assert isinstance(cfg, PLCConfig)

    def test_connection_ams_net_id(self, tmp_path: Path) -> None:
        cfg = ConfigLoader.load(_write_xml(tmp_path, MINIMAL_XML))
        assert cfg.connection.ams_net_id == "1.2.3.4.1.1"

    def test_connection_ip(self, tmp_path: Path) -> None:
        cfg = ConfigLoader.load(_write_xml(tmp_path, MINIMAL_XML))
        assert cfg.connection.ip_address == "192.168.1.10"

    def test_connection_port(self, tmp_path: Path) -> None:
        cfg = ConfigLoader.load(_write_xml(tmp_path, MINIMAL_XML))
        assert cfg.connection.port == 851

    def test_variables_count(self, tmp_path: Path) -> None:
        cfg = ConfigLoader.load(_write_xml(tmp_path, MINIMAL_XML))
        assert len(cfg.variables) == 1

    def test_variable_name(self, tmp_path: Path) -> None:
        cfg = ConfigLoader.load(_write_xml(tmp_path, MINIMAL_XML))
        assert cfg.variables[0].name == "MAIN.bTest"

    def test_variable_type_normalised(self, tmp_path: Path) -> None:
        cfg = ConfigLoader.load(_write_xml(tmp_path, MINIMAL_XML))
        assert cfg.variables[0].plc_type == "BOOL"

    def test_defaults_applied_for_reconnect(self, tmp_path: Path) -> None:
        cfg = ConfigLoader.load(_write_xml(tmp_path, MINIMAL_XML))
        assert cfg.reconnect.max_attempts == 10  # default value

    def test_defaults_applied_for_notifications(self, tmp_path: Path) -> None:
        cfg = ConfigLoader.load(_write_xml(tmp_path, MINIMAL_XML))
        assert cfg.notifications.cycle_time_ms == 100  # default

    def test_defaults_applied_for_heartbeat(self, tmp_path: Path) -> None:
        cfg = ConfigLoader.load(_write_xml(tmp_path, MINIMAL_XML))
        assert cfg.heartbeat.interval_seconds == 5  # default


class TestLoadBundledConfig:
    """Validate the actual plc_config.xml shipped with the project."""

    def test_loads_without_error(self) -> None:
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "plc_config.xml"
        )
        cfg = ConfigLoader.load(config_path)
        assert cfg.connection.ams_net_id == "5.1.204.160.1.1"
        assert len(cfg.variables) > 0

    def test_all_expected_variables_present(self) -> None:
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "plc_config.xml"
        )
        cfg = ConfigLoader.load(config_path)
        names = {v.name for v in cfg.variables}
        assert "MAIN.bMotorOn" in names
        assert "MAIN.nSpeed" in names
        assert "MAIN.rTemperature" in names


# ---------------------------------------------------------------------------
# Error cases – missing / malformed elements
# ---------------------------------------------------------------------------

class TestMissingRequiredElements:
    def test_missing_connection_raises(self, tmp_path: Path) -> None:
        xml = """
            <PLCConfig>
                <Variables>
                    <Variable><Name>MAIN.x</Name><Type>BOOL</Type></Variable>
                </Variables>
            </PLCConfig>
        """
        with pytest.raises(XMLConfigError, match="Connection"):
            ConfigLoader.load(_write_xml(tmp_path, xml))

    def test_missing_ams_net_id_raises(self, tmp_path: Path) -> None:
        xml = """
            <PLCConfig>
                <Connection>
                    <IPAddress>1.2.3.4</IPAddress>
                    <Port>851</Port>
                </Connection>
                <Variables><Variable><Name>X</Name><Type>BOOL</Type></Variable></Variables>
            </PLCConfig>
        """
        with pytest.raises(XMLConfigError, match="AMSNetID"):
            ConfigLoader.load(_write_xml(tmp_path, xml))

    def test_missing_variables_raises(self, tmp_path: Path) -> None:
        xml = """
            <PLCConfig>
                <Connection>
                    <AMSNetID>1.2.3.4.1.1</AMSNetID>
                    <IPAddress>1.2.3.4</IPAddress>
                    <Port>851</Port>
                </Connection>
            </PLCConfig>
        """
        with pytest.raises(XMLConfigError, match="Variables"):
            ConfigLoader.load(_write_xml(tmp_path, xml))

    def test_empty_variables_section_raises(self, tmp_path: Path) -> None:
        xml = """
            <PLCConfig>
                <Connection>
                    <AMSNetID>1.2.3.4.1.1</AMSNetID>
                    <IPAddress>1.2.3.4</IPAddress>
                    <Port>851</Port>
                </Connection>
                <Variables></Variables>
            </PLCConfig>
        """
        with pytest.raises(XMLConfigError, match="Variable"):
            ConfigLoader.load(_write_xml(tmp_path, xml))

    def test_non_integer_port_raises(self, tmp_path: Path) -> None:
        xml = """
            <PLCConfig>
                <Connection>
                    <AMSNetID>1.2.3.4.1.1</AMSNetID>
                    <IPAddress>1.2.3.4</IPAddress>
                    <Port>abc</Port>
                </Connection>
                <Variables><Variable><Name>X</Name><Type>BOOL</Type></Variable></Variables>
            </PLCConfig>
        """
        with pytest.raises(XMLConfigError, match="Port"):
            ConfigLoader.load(_write_xml(tmp_path, xml))


# ---------------------------------------------------------------------------
# Unsupported PLC type
# ---------------------------------------------------------------------------

class TestUnsupportedType:
    def test_unknown_plc_type_raises(self, tmp_path: Path) -> None:
        xml = """
            <PLCConfig>
                <Connection>
                    <AMSNetID>1.2.3.4.1.1</AMSNetID>
                    <IPAddress>1.2.3.4</IPAddress>
                    <Port>851</Port>
                </Connection>
                <Variables>
                    <Variable><Name>MAIN.x</Name><Type>WORD</Type></Variable>
                </Variables>
            </PLCConfig>
        """
        with pytest.raises(XMLConfigError, match="WORD"):
            ConfigLoader.load(_write_xml(tmp_path, xml))


# ---------------------------------------------------------------------------
# Duplicate variable names
# ---------------------------------------------------------------------------

class TestDuplicateVariables:
    def test_duplicate_name_raises(self, tmp_path: Path) -> None:
        xml = """
            <PLCConfig>
                <Connection>
                    <AMSNetID>1.2.3.4.1.1</AMSNetID>
                    <IPAddress>1.2.3.4</IPAddress>
                    <Port>851</Port>
                </Connection>
                <Variables>
                    <Variable><Name>MAIN.x</Name><Type>BOOL</Type></Variable>
                    <Variable><Name>MAIN.x</Name><Type>INT</Type></Variable>
                </Variables>
            </PLCConfig>
        """
        with pytest.raises(XMLConfigError, match="Duplicate"):
            ConfigLoader.load(_write_xml(tmp_path, xml))


# ---------------------------------------------------------------------------
# File-level errors
# ---------------------------------------------------------------------------

class TestFileErrors:
    def test_missing_file_raises(self) -> None:
        with pytest.raises(XMLConfigError, match="not found"):
            ConfigLoader.load("/nonexistent/path/plc_config.xml")

    def test_malformed_xml_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.xml"
        p.write_text("<PLCConfig><Connection>no closing tag", encoding="utf-8")
        with pytest.raises(XMLConfigError, match="parse error"):
            ConfigLoader.load(str(p))

    def test_wrong_root_element_raises(self, tmp_path: Path) -> None:
        xml = "<WrongRoot><Connection/></WrongRoot>"
        p = tmp_path / "wrong_root.xml"
        p.write_text(xml, encoding="utf-8")
        with pytest.raises(XMLConfigError, match="PLCConfig"):
            ConfigLoader.load(str(p))


# ---------------------------------------------------------------------------
# SUPPORTED_TYPES vs. PLC_TYPE_MAP completeness
# ---------------------------------------------------------------------------

class TestSupportedTypesCompleteness:
    """
    Regression guard for the bug where SINT / USINT / LINT / ULINT were
    present in ``PLC_TYPE_MAP`` (fully implemented) but absent from
    ``SUPPORTED_TYPES`` (rejected at config-load time with a misleading error).

    If either mapping grows, these tests will catch the discrepancy
    immediately rather than waiting for a runtime failure.
    """

    def test_all_plc_type_map_keys_are_in_supported_types(self) -> None:
        """Every numeric PLC type that has a pyads mapping must be accepted by the loader."""
        missing = set(PLC_TYPE_MAP.keys()) - SUPPORTED_TYPES
        assert not missing, (
            f"Types in PLC_TYPE_MAP but missing from SUPPORTED_TYPES: {missing}. "
            "Add them to SUPPORTED_TYPES in config_loader.py."
        )

    def test_no_unknown_types_in_supported_types(self) -> None:
        """Every type in SUPPORTED_TYPES must either be in PLC_TYPE_MAP or be STRING/ARRAY."""
        allowed = set(PLC_TYPE_MAP.keys()) | {"STRING", "ARRAY"}
        unknown = SUPPORTED_TYPES - allowed
        assert not unknown, (
            f"Types in SUPPORTED_TYPES but not in PLC_TYPE_MAP or allowed specials: {unknown}."
        )

    def test_supported_types_equals_plc_type_map_plus_specials(self) -> None:
        """Symmetric check: SUPPORTED_TYPES == PLC_TYPE_MAP keys ∪ {STRING, ARRAY}."""
        expected = set(PLC_TYPE_MAP.keys()) | {"STRING", "ARRAY"}
        assert SUPPORTED_TYPES == expected, (
            f"Extra in SUPPORTED_TYPES: {SUPPORTED_TYPES - expected}; "
            f"Extra in expected: {expected - SUPPORTED_TYPES}"
        )
