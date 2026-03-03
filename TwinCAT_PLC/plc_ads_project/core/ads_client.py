"""
ads_client.py
-------------
Thin, type-annotated façade over the underlying :class:`pyads.Connection`
provided by :class:`~core.connection_manager.ConnectionManager`.

Responsibilities
~~~~~~~~~~~~~~~~
* Wraps ``read_by_name`` / ``write_by_name`` with proper exception mapping.
* Wraps ``add_device_notification`` / ``del_device_notification``.
* Ensures all calls go through the
  :class:`~core.connection_manager.ConnectionManager` so reconnect logic is
  transparent to callers.
* Translates ``pyads.ADSError`` into domain-specific exceptions from
  :mod:`utils.custom_exceptions`.

This layer intentionally *does not* know about variable registries or
data-type converters – that logic lives in the service layer above.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

import pyads

from core.connection_manager import ConnectionManager
from utils.custom_exceptions import PLCReadError, PLCWriteError, PLCNotificationError
from utils.logger import get_logger

log = get_logger(__name__)


class ADSClient:
    """
    High-level ADS client that delegates transport to a
    :class:`~core.connection_manager.ConnectionManager`.

    Args:
        connection_manager: An open (or auto-reconnecting)
            :class:`~core.connection_manager.ConnectionManager`.

    Example::

        import pyads
        from core.connection_manager import ConnectionManager
        from core.ads_client import ADSClient

        with ConnectionManager(conn_cfg, reconn_cfg, hb_cfg) as cm:
            client = ADSClient(cm)
            speed = client.read_by_name("MAIN.nSpeed", pyads.PLCTYPE_INT)
            client.write_by_name("MAIN.bMotorOn", True, pyads.PLCTYPE_BOOL)
    """

    def __init__(self, connection_manager: ConnectionManager) -> None:
        self._cm = connection_manager

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read_by_name(
        self,
        variable_name: str,
        plc_type: Any,
    ) -> Any:
        """
        Read a PLC variable by its symbolic name.

        Args:
            variable_name: Full symbolic path (e.g. ``"MAIN.nSpeed"``).
            plc_type:      pyads type constant (e.g. ``pyads.PLCTYPE_INT``).

        Returns:
            The raw value returned by pyads (Python-native after pyads
            de-serialisation).

        Raises:
            PLCReadError:      If the ADS call fails.
            PLCConnectionError: If there is no active connection.
        """
        log.debug("ADS read: '%s'", variable_name)
        try:
            value = self._cm.connection.read_by_name(variable_name, plc_type)
            log.debug("ADS read OK: '%s' = %r", variable_name, value)
            return value
        except pyads.ADSError as exc:
            raise PLCReadError(
                f"ADS read failed for '{variable_name}': {exc}",
                variable_name=variable_name,
                ads_error_code=exc.err_code,
            ) from exc
        except Exception as exc:
            raise PLCReadError(
                f"Unexpected error reading '{variable_name}': {exc}",
                variable_name=variable_name,
            ) from exc

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def write_by_name(
        self,
        variable_name: str,
        value: Any,
        plc_type: Any,
    ) -> None:
        """
        Write a value to a PLC variable by its symbolic name.

        Args:
            variable_name: Full symbolic path.
            value:         Python value to write.
            plc_type:      pyads type constant.

        Raises:
            PLCWriteError:      If the ADS call fails.
            PLCConnectionError: If there is no active connection.
        """
        log.debug("ADS write: '%s' ← %r", variable_name, value)
        try:
            self._cm.connection.write_by_name(variable_name, value, plc_type)
            log.info("ADS write OK: '%s' ← %r", variable_name, value)
        except pyads.ADSError as exc:
            raise PLCWriteError(
                f"ADS write failed for '{variable_name}' (value={value!r}): {exc}",
                variable_name=variable_name,
                value=value,
                ads_error_code=exc.err_code,
            ) from exc
        except Exception as exc:
            raise PLCWriteError(
                f"Unexpected error writing '{variable_name}': {exc}",
                variable_name=variable_name,
                value=value,
            ) from exc

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def add_device_notification(
        self,
        variable_name: str,
        attr: pyads.NotificationAttrib,
        callback: Callable[..., None],
    ) -> Optional[tuple[int, int]]:
        """
        Register an ADS device notification for a symbolic variable.

        Args:
            variable_name: Full symbolic path of the PLC variable.
            attr:          :class:`pyads.NotificationAttrib` describing the
                           notification timing and buffer size.
            callback:      Function called by pyads when the value changes.
                           Signature: ``callback(notification, data) → None``.

        Returns:
            A ``(notification_handle, symbol_handle)`` tuple, or ``None`` on
            failure (error is logged rather than raised to allow non-critical
            subscriptions to degrade gracefully).

        Raises:
            PLCNotificationError: If the registration fails definitively.
        """
        log.debug("Subscribing to ADS notification: '%s'", variable_name)
        try:
            handles = self._cm.connection.add_device_notification(
                variable_name, attr, callback
            )
            log.info("Subscribed to '%s': handles=%s", variable_name, handles)
            return handles  # type: ignore[return-value]
        except pyads.ADSError as exc:
            raise PLCNotificationError(
                f"Failed to register notification for '{variable_name}': {exc}",
                variable_name=variable_name,
            ) from exc
        except Exception as exc:
            raise PLCNotificationError(
                f"Unexpected error subscribing to '{variable_name}': {exc}",
                variable_name=variable_name,
            ) from exc

    def del_device_notification(
        self,
        notification_handle: int,
        user_handle: int,
    ) -> None:
        """
        Delete a previously registered ADS device notification.

        Args:
            notification_handle: Handle returned by :meth:`add_device_notification`.
            user_handle:         Symbol/user handle returned by
                                 :meth:`add_device_notification`.

        Raises:
            PLCNotificationError: If deletion fails.
        """
        log.debug(
            "Deleting ADS notification: notif_handle=%d user_handle=%d",
            notification_handle,
            user_handle,
        )
        try:
            self._cm.connection.del_device_notification(notification_handle, user_handle)
            log.info(
                "Deleted notification: notif_handle=%d user_handle=%d",
                notification_handle,
                user_handle,
            )
        except pyads.ADSError as exc:
            raise PLCNotificationError(
                f"Failed to delete notification (handle={notification_handle}): {exc}",
                handle=notification_handle,
            ) from exc
        except Exception as exc:
            raise PLCNotificationError(
                f"Unexpected error deleting notification (handle={notification_handle}): {exc}",
                handle=notification_handle,
            ) from exc

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def get_local_ads_address(self) -> str:
        """Return the local AMS Net ID reported by the ADS router."""
        try:
            return str(self._cm.connection.get_local_address())
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not retrieve local ADS address: %s", exc)
            return "unknown"

    def read_state(self) -> tuple[int, int]:
        """
        Read the current ADS / device state from the PLC.

        Returns:
            A ``(ads_state, device_state)`` integer tuple.

        Raises:
            PLCReadError: If the state read fails.
        """
        try:
            state = self._cm.connection.read_state()
            log.debug("PLC state: ADS=%d Device=%d", state[0], state[1])
            return state  # type: ignore[return-value]
        except pyads.ADSError as exc:
            raise PLCReadError(
                f"Failed to read PLC ADS state: {exc}",
                ads_error_code=exc.err_code,
            ) from exc
