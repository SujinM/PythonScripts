"""
config_loader.py
----------------
Responsible for parsing *plc_config.xml* and exposing the configuration as
strongly-typed Python dataclasses.

Design notes
~~~~~~~~~~~~
* Uses the standard-library :mod:`xml.etree.ElementTree` – no third-party XML
  dependency required.
* All dataclasses are frozen (``frozen=True``) to prevent accidental mutation
  after loading.
* Raises :class:`~utils.custom_exceptions.XMLConfigError` for every
  recoverable parse issue so that callers receive a consistent, typed error.

Typical usage::

    from config.config_loader import ConfigLoader

    cfg = ConfigLoader.load("config/plc_config.xml")
    print(cfg.connection.ams_net_id)
    for var in cfg.variables:
        print(var.name, var.plc_type)
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Final, Optional

from utils.custom_exceptions import XMLConfigError
from utils.logger import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Supported PLC data types (validated on load)
# ---------------------------------------------------------------------------
SUPPORTED_TYPES: Final[frozenset[str]] = frozenset(
    {
        "BOOL",
        "BYTE",
        "SINT", "USINT",          # 8-bit signed / unsigned
        "INT", "UINT",            # 16-bit signed / unsigned
        "DINT", "UDINT",          # 32-bit signed / unsigned
        "LINT", "ULINT",          # 64-bit signed / unsigned
        "REAL", "LREAL",          # 32-bit / 64-bit float
        "STRING",
        "ARRAY",
    }
)

# Default values used when optional XML elements are absent.
_DEFAULT_MAX_ATTEMPTS: Final[int] = 10
_DEFAULT_INITIAL_DELAY: Final[float] = 1.0
_DEFAULT_BACKOFF_MULT: Final[float] = 2.0
_DEFAULT_MAX_DELAY: Final[float] = 60.0
_DEFAULT_CYCLE_MS: Final[int] = 100
_DEFAULT_MAX_DELAY_MS: Final[int] = 200
_DEFAULT_HEARTBEAT_S: Final[int] = 5


# ---------------------------------------------------------------------------
# Dataclasses – one per logical section of the XML
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConnectionConfig:
    """ADS transport parameters."""
    ams_net_id: str
    ip_address: str
    port: int


@dataclass(frozen=True)
class ReconnectConfig:
    """Exponential back-off reconnect strategy parameters."""
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS
    initial_delay_seconds: float = _DEFAULT_INITIAL_DELAY
    backoff_multiplier: float = _DEFAULT_BACKOFF_MULT
    max_delay_seconds: float = _DEFAULT_MAX_DELAY


@dataclass(frozen=True)
class NotificationConfig:
    """ADS device notification timing parameters."""
    cycle_time_ms: int = _DEFAULT_CYCLE_MS
    max_delay_ms: int = _DEFAULT_MAX_DELAY_MS


@dataclass(frozen=True)
class HeartbeatConfig:
    """Watchdog / heartbeat parameters."""
    interval_seconds: int = _DEFAULT_HEARTBEAT_S


@dataclass(frozen=True)
class VariableConfig:
    """Configuration for a single PLC variable."""
    name: str
    plc_type: str
    description: str = ""


@dataclass(frozen=True)
class PLCConfig:
    """
    Top-level configuration object returned by :func:`ConfigLoader.load`.

    Aggregates all sections of *plc_config.xml* into a single immutable
    structure.
    """
    connection: ConnectionConfig
    reconnect: ReconnectConfig
    notifications: NotificationConfig
    heartbeat: HeartbeatConfig
    variables: tuple[VariableConfig, ...]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require_text(element: ET.Element, tag: str, parent_path: str, config_path: str) -> str:
    """
    Return the stripped text of a child element, raising :class:`XMLConfigError`
    when the child is missing or empty.
    """
    child = element.find(tag)
    if child is None or not (child.text or "").strip():
        raise XMLConfigError(
            f"Missing or empty <{tag}> inside <{parent_path}>",
            config_path=config_path,
            xml_path=f"{parent_path}/{tag}",
        )
    return child.text.strip()  # type: ignore[union-attr]


def _optional_text(
    element: ET.Element,
    tag: str,
    default: str = "",
) -> str:
    """Return the text of an optional child element, or *default*."""
    child = element.find(tag)
    if child is None or not (child.text or "").strip():
        return default
    return child.text.strip()  # type: ignore[union-attr]


def _optional_int(
    element: ET.Element,
    tag: str,
    default: int,
    config_path: str,
) -> int:
    text = _optional_text(element, tag, str(default))
    try:
        return int(text)
    except ValueError as exc:
        raise XMLConfigError(
            f"<{tag}> must be an integer, got {text!r}",
            config_path=config_path,
            xml_path=tag,
        ) from exc


def _optional_float(
    element: ET.Element,
    tag: str,
    default: float,
    config_path: str,
) -> float:
    text = _optional_text(element, tag, str(default))
    try:
        return float(text)
    except ValueError as exc:
        raise XMLConfigError(
            f"<{tag}> must be a float, got {text!r}",
            config_path=config_path,
            xml_path=tag,
        ) from exc


# ---------------------------------------------------------------------------
# ConfigLoader
# ---------------------------------------------------------------------------

class ConfigLoader:
    """
    Static factory that parses a *plc_config.xml* file and returns a
    fully-validated :class:`PLCConfig` instance.

    All methods are class-level; there is no need to instantiate this class.

    Example::

        config = ConfigLoader.load("config/plc_config.xml")
    """

    @classmethod
    def load(cls, config_path: str) -> PLCConfig:
        """
        Parse and validate the given XML configuration file.

        Args:
            config_path: Filesystem path to the XML file.

        Returns:
            An immutable :class:`PLCConfig` instance.

        Raises:
            XMLConfigError: If the file does not exist, cannot be parsed, or
                is missing required elements.
        """
        abs_path = os.path.abspath(config_path)
        log.info("Loading PLC configuration from '%s'", abs_path)

        if not os.path.isfile(abs_path):
            raise XMLConfigError(
                f"Configuration file not found: '{abs_path}'",
                config_path=abs_path,
            )

        try:
            tree = ET.parse(abs_path)
        except ET.ParseError as exc:
            raise XMLConfigError(
                f"XML parse error in '{abs_path}': {exc}",
                config_path=abs_path,
            ) from exc

        root = tree.getroot()
        if root.tag != "PLCConfig":
            raise XMLConfigError(
                f"Root element must be <PLCConfig>, got <{root.tag}>",
                config_path=abs_path,
            )

        connection = cls._parse_connection(root, abs_path)
        reconnect = cls._parse_reconnect(root, abs_path)
        notifications = cls._parse_notifications(root, abs_path)
        heartbeat = cls._parse_heartbeat(root, abs_path)
        variables = cls._parse_variables(root, abs_path)

        cfg = PLCConfig(
            connection=connection,
            reconnect=reconnect,
            notifications=notifications,
            heartbeat=heartbeat,
            variables=variables,
        )
        log.info(
            "Configuration loaded: AMS=%s IP=%s Port=%d Variables=%d",
            cfg.connection.ams_net_id,
            cfg.connection.ip_address,
            cfg.connection.port,
            len(cfg.variables),
        )
        return cfg

    # ------------------------------------------------------------------
    # Section parsers
    # ------------------------------------------------------------------

    @classmethod
    def _parse_connection(cls, root: ET.Element, path: str) -> ConnectionConfig:
        conn_el = root.find("Connection")
        if conn_el is None:
            raise XMLConfigError("Missing <Connection> section", config_path=path, xml_path="Connection")

        ams_net_id = _require_text(conn_el, "AMSNetID", "Connection", path)
        ip_address = _require_text(conn_el, "IPAddress", "Connection", path)
        port_raw = _require_text(conn_el, "Port", "Connection", path)

        try:
            port = int(port_raw)
        except ValueError as exc:
            raise XMLConfigError(
                f"<Port> must be an integer, got {port_raw!r}",
                config_path=path,
                xml_path="Connection/Port",
            ) from exc

        return ConnectionConfig(ams_net_id=ams_net_id, ip_address=ip_address, port=port)

    @classmethod
    def _parse_reconnect(cls, root: ET.Element, path: str) -> ReconnectConfig:
        el = root.find("Reconnect")
        if el is None:
            log.debug("<Reconnect> section absent – using defaults")
            return ReconnectConfig()

        return ReconnectConfig(
            max_attempts=_optional_int(el, "MaxAttempts", _DEFAULT_MAX_ATTEMPTS, path),
            initial_delay_seconds=_optional_float(el, "InitialDelaySeconds", _DEFAULT_INITIAL_DELAY, path),
            backoff_multiplier=_optional_float(el, "BackoffMultiplier", _DEFAULT_BACKOFF_MULT, path),
            max_delay_seconds=_optional_float(el, "MaxDelaySeconds", _DEFAULT_MAX_DELAY, path),
        )

    @classmethod
    def _parse_notifications(cls, root: ET.Element, path: str) -> NotificationConfig:
        el = root.find("Notifications")
        if el is None:
            log.debug("<Notifications> section absent – using defaults")
            return NotificationConfig()

        return NotificationConfig(
            cycle_time_ms=_optional_int(el, "CycleTimeMs", _DEFAULT_CYCLE_MS, path),
            max_delay_ms=_optional_int(el, "MaxDelayMs", _DEFAULT_MAX_DELAY_MS, path),
        )

    @classmethod
    def _parse_heartbeat(cls, root: ET.Element, path: str) -> HeartbeatConfig:
        el = root.find("Heartbeat")
        if el is None:
            log.debug("<Heartbeat> section absent – using defaults")
            return HeartbeatConfig()

        return HeartbeatConfig(
            interval_seconds=_optional_int(el, "IntervalSeconds", _DEFAULT_HEARTBEAT_S, path),
        )

    @classmethod
    def _parse_variables(cls, root: ET.Element, path: str) -> tuple[VariableConfig, ...]:
        variables_el = root.find("Variables")
        if variables_el is None:
            raise XMLConfigError(
                "Missing <Variables> section",
                config_path=path,
                xml_path="Variables",
            )

        var_elements = variables_el.findall("Variable")
        if not var_elements:
            raise XMLConfigError(
                "<Variables> must contain at least one <Variable>",
                config_path=path,
                xml_path="Variables",
            )

        variables: list[VariableConfig] = []
        seen_names: set[str] = set()

        for idx, var_el in enumerate(var_elements):
            name = _require_text(var_el, "Name", f"Variables/Variable[{idx}]", path)
            plc_type = _require_text(var_el, "Type", f"Variables/Variable[{idx}]", path).upper()
            description = _optional_text(var_el, "Description")

            if plc_type not in SUPPORTED_TYPES:
                raise XMLConfigError(
                    f"Variable '{name}': unsupported type '{plc_type}'. "
                    f"Supported: {sorted(SUPPORTED_TYPES)}",
                    config_path=path,
                    xml_path=f"Variables/Variable[{idx}]/Type",
                )

            if name in seen_names:
                raise XMLConfigError(
                    f"Duplicate variable name '{name}' in configuration",
                    config_path=path,
                    xml_path=f"Variables/Variable[{idx}]/Name",
                )
            seen_names.add(name)

            variables.append(VariableConfig(name=name, plc_type=plc_type, description=description))
            log.debug("Parsed variable: name=%s type=%s", name, plc_type)

        return tuple(variables)
