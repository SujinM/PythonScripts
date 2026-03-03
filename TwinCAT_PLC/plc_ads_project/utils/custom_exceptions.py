"""
custom_exceptions.py
--------------------
Domain-specific exception hierarchy for the PLC ADS project.

All exceptions inherit from :class:`PLCADSBaseError` so callers can catch
the entire family with a single ``except PLCADSBaseError`` clause while still
being able to target individual subtypes for finer-grained recovery logic.

Exception hierarchy
~~~~~~~~~~~~~~~~~~~
PLCADSBaseError
├── PLCConnectionError
│   └── PLCReconnectExhaustedError
├── PLCReadError
├── PLCWriteError
├── PLCNotificationError
├── PLCVariableNotFoundError
├── DataTypeMismatchError
└── XMLConfigError
"""

from __future__ import annotations

from typing import Any, Optional


# ---------------------------------------------------------------------------
# Base exception
# ---------------------------------------------------------------------------

class PLCADSBaseError(Exception):
    """
    Root exception for this project.

    All project-specific exceptions inherit from this class so that callers
    can use a single broad ``except PLCADSBaseError`` to catch any library
    error while still allowing targeted handling of subtypes.
    """

    def __init__(self, message: str, *, context: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        #: Optional structured metadata (variable name, ADS error code, …).
        self.context: dict[str, Any] = context or {}

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}({self!s}, context={self.context!r})"


# ---------------------------------------------------------------------------
# Connection errors
# ---------------------------------------------------------------------------

class PLCConnectionError(PLCADSBaseError):
    """
    Raised when the ADS transport layer cannot be established or is lost
    during runtime.

    Attributes:
        ams_net_id:  The AMS Net ID of the target PLC, if known.
        ip_address:  The IP address of the target PLC, if known.
    """

    def __init__(
        self,
        message: str,
        *,
        ams_net_id: str = "",
        ip_address: str = "",
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, context=context)
        self.ams_net_id = ams_net_id
        self.ip_address = ip_address


class PLCReconnectExhaustedError(PLCConnectionError):
    """
    Raised when the auto-reconnect strategy has exhausted all retry attempts
    without successfully re-establishing the ADS connection.

    Attributes:
        attempts: Number of reconnect attempts made before giving up.
    """

    def __init__(
        self,
        message: str,
        *,
        attempts: int = 0,
        ams_net_id: str = "",
        ip_address: str = "",
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            ams_net_id=ams_net_id,
            ip_address=ip_address,
            context=context,
        )
        self.attempts = attempts


# ---------------------------------------------------------------------------
# I/O errors
# ---------------------------------------------------------------------------

class PLCReadError(PLCADSBaseError):
    """
    Raised when reading a PLC variable fails at the ADS layer.

    Attributes:
        variable_name: The symbolic name of the variable being read.
        ads_error_code: The raw ADS error code returned by the PLC, if any.
    """

    def __init__(
        self,
        message: str,
        *,
        variable_name: str = "",
        ads_error_code: Optional[int] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, context=context)
        self.variable_name = variable_name
        self.ads_error_code = ads_error_code


class PLCWriteError(PLCADSBaseError):
    """
    Raised when writing a value to a PLC variable fails at the ADS layer.

    Attributes:
        variable_name: The symbolic name of the variable being written.
        value:         The value that was attempted to be written.
        ads_error_code: The raw ADS error code returned by the PLC, if any.
    """

    def __init__(
        self,
        message: str,
        *,
        variable_name: str = "",
        value: Any = None,
        ads_error_code: Optional[int] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, context=context)
        self.variable_name = variable_name
        self.value = value
        self.ads_error_code = ads_error_code


# ---------------------------------------------------------------------------
# Notification errors
# ---------------------------------------------------------------------------

class PLCNotificationError(PLCADSBaseError):
    """
    Raised when registering, processing, or deleting an ADS device
    notification fails.

    Attributes:
        variable_name: The symbolic name of the variable involved.
        handle: The notification handle, if available.
    """

    def __init__(
        self,
        message: str,
        *,
        variable_name: str = "",
        handle: Optional[int] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, context=context)
        self.variable_name = variable_name
        self.handle = handle


# ---------------------------------------------------------------------------
# Variable lookup errors
# ---------------------------------------------------------------------------

class PLCVariableNotFoundError(PLCADSBaseError):
    """
    Raised when a requested variable name is not present in the
    :class:`~models.variable_registry.VariableRegistry`.

    Attributes:
        variable_name: The name that could not be found.
    """

    def __init__(
        self,
        message: str,
        *,
        variable_name: str = "",
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, context=context)
        self.variable_name = variable_name


# ---------------------------------------------------------------------------
# Data-type errors
# ---------------------------------------------------------------------------

class DataTypeMismatchError(PLCADSBaseError):
    """
    Raised when the Python value passed to a write operation is not
    compatible with the declared PLC data type of the target variable.

    Attributes:
        variable_name:   The name of the variable being written.
        expected_type:   The PLC type declared for the variable (e.g. ``"INT"``).
        received_type:   The Python type of the supplied value.
        value:           The actual value that caused the mismatch.
    """

    def __init__(
        self,
        message: str,
        *,
        variable_name: str = "",
        expected_type: str = "",
        received_type: str = "",
        value: Any = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, context=context)
        self.variable_name = variable_name
        self.expected_type = expected_type
        self.received_type = received_type
        self.value = value


# ---------------------------------------------------------------------------
# Configuration errors
# ---------------------------------------------------------------------------

class XMLConfigError(PLCADSBaseError):
    """
    Raised when the XML configuration file cannot be found, parsed, or
    does not contain the required elements.

    Attributes:
        config_path: Path to the problematic XML file.
        xml_path:    XPath expression that failed, if applicable.
    """

    def __init__(
        self,
        message: str,
        *,
        config_path: str = "",
        xml_path: str = "",
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, context=context)
        self.config_path = config_path
        self.xml_path = xml_path
