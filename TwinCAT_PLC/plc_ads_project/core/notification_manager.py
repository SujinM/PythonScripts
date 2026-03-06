"""
notification_manager.py
-----------------------
Manages ADS device-notification subscriptions and dispatches received
notifications to :class:`~models.plc_variable.PLCVariable` instances without
blocking the main thread.

Architecture
~~~~~~~~~~~~
::

    pyads callback (ADS thread)
            │
            ▼
    _notification_queue  (thread-safe Queue)
            │
            ▼
    _dispatcher_thread   (daemon thread)
            │
            ▼
    PLCVariable.update_value()
            │
            ▼
    change hooks (user callbacks)

This two-stage design decouples the latency-sensitive ADS callback from
potentially slow user-registered hooks, and avoids any risk of blocking
the ADS notification thread.

Thread Safety
~~~~~~~~~~~~~
* ``_subscriptions`` dict is protected by ``_lock``.
* The queue is intrinsically thread-safe.
* ``PLCVariable.update_value`` is independently thread-safe.
"""

from __future__ import annotations

import queue
import struct
import threading
from dataclasses import dataclass, field
from typing import Any, Optional

import pyads

from config.config_loader import NotificationConfig
from core.ads_client import ADSClient
from core.datatype_converter import DataTypeConverter
from models.plc_variable import PLCVariable
from models.variable_registry import VariableRegistry
from utils.custom_exceptions import PLCNotificationError
from utils.logger import get_logger

log = get_logger(__name__)

# Maximum number of pending notifications buffered before the oldest is dropped.
_QUEUE_MAX_SIZE: int = 1000

# struct format strings for direct payload decoding (little-endian TwinCAT byte order).
# Types absent from this map (STRING, ARRAY) cannot be decoded from raw bytes and
# will fall back to a read_by_name call in the dispatcher thread.
_STRUCT_FMT: dict[str, str] = {
    "BOOL":  "<?",
    "BYTE":  "<B",
    "SINT":  "<b",
    "USINT": "<B",
    "INT":   "<h",
    "UINT":  "<H",
    "DINT":  "<i",
    "UDINT": "<I",
    "LINT":  "<q",
    "ULINT": "<Q",
    "REAL":  "<f",
    "LREAL": "<d",
}


@dataclass
class _NotificationItem:
    """
    Lightweight payload queued from the ADS callback thread.

    For numeric / boolean PLC types the raw notification bytes are decoded
    inline inside the ADS callback using :data:`_STRUCT_FMT`, so ``value``
    is already populated and the dispatcher can skip the extra
    ``read_by_name`` round-trip.

    For STRING / ARRAY types (or if inline decoding fails) ``value`` is
    ``None`` and the dispatcher falls back to a ``read_by_name`` call.
    """
    variable_name: str
    plc_type: str
    value: Optional[Any] = field(default=None)


class NotificationManager:
    """
    Registers ADS device notifications, receives raw callbacks from pyads,
    and updates :class:`~models.plc_variable.PLCVariable` instances via a
    background dispatcher thread.

    Args:
        ads_client:    The :class:`~core.ads_client.ADSClient` used to register
                       and delete notifications.
        registry:      The :class:`~models.variable_registry.VariableRegistry`
                       that owns the :class:`~models.plc_variable.PLCVariable`
                       instances to be updated.
        notif_config:  ADS notification timing configuration.

    Example::

        nm = NotificationManager(client, registry, cfg.notifications)
        nm.start()
        nm.subscribe_variable(var)   # var is a PLCVariable
        # ... PLC runs, PLCVariable.current_value updates automatically ...
        nm.unsubscribe_variable("MAIN.nSpeed")
        nm.stop()
    """

    def __init__(
        self,
        ads_client: ADSClient,
        registry: VariableRegistry,
        notif_config: NotificationConfig,
    ) -> None:
        self._client = ads_client
        self._registry = registry
        self._notif_cfg = notif_config

        # Map: variable_name → (notification_handle, user_handle)
        self._subscriptions: dict[str, tuple[int, int]] = {}
        self._lock: threading.RLock = threading.RLock()

        # Internal work queue fed by ADS callbacks.
        self._queue: "queue.Queue[Optional[_NotificationItem]]" = queue.Queue(
            maxsize=_QUEUE_MAX_SIZE
        )

        # Dispatcher thread.
        self._dispatcher_thread: Optional[threading.Thread] = None
        self._running: bool = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """
        Start the background dispatcher thread.

        Safe to call multiple times; subsequent calls are no-ops.
        """
        if self._running:
            return
        self._running = True
        self._dispatcher_thread = threading.Thread(
            target=self._dispatcher_loop,
            name="plc-notif-dispatcher",
            daemon=True,
        )
        self._dispatcher_thread.start()
        log.info("NotificationManager dispatcher thread started")

    def stop(self) -> None:
        """
        Unsubscribe all active notifications, drain the queue, and stop
        the dispatcher thread.

        Blocks until the dispatcher thread has exited (up to 5 seconds).
        """
        log.info("NotificationManager stopping …")
        self.unsubscribe_all()

        self._running = False
        # Poison-pill to unblock the dispatcher's blocking get().
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass

        if self._dispatcher_thread and self._dispatcher_thread.is_alive():
            self._dispatcher_thread.join(timeout=5.0)
        log.info("NotificationManager stopped")

    # ------------------------------------------------------------------
    # Subscription management
    # ------------------------------------------------------------------

    def subscribe_variable(self, variable: PLCVariable) -> None:
        """
        Register an ADS device notification for *variable*.

        The pyads callback queues a :class:`_NotificationItem`; the dispatcher
        thread picks it up and calls ``variable.update_value()``.

        Args:
            variable: A :class:`~models.plc_variable.PLCVariable` that is
                      already registered in the
                      :class:`~models.variable_registry.VariableRegistry`.

        Raises:
            PLCNotificationError: If the ADS notification registration fails.
        """
        name = variable.name

        with self._lock:
            if name in self._subscriptions:
                log.debug("Variable '%s' is already subscribed; skipping", name)
                return

        # Build the notification attribute using config-supplied timing.
        # pyads 3.x NotificationAttrib expects max_delay and cycle_time in
        # SECONDS (float), not milliseconds – divide the config values.
        attr = pyads.NotificationAttrib(
            length=self._plc_type_byte_length(variable.plc_type),
            trans_mode=pyads.constants.ADSTRANS_SERVERONCHA,
            max_delay=self._notif_cfg.max_delay_ms / 1000.0,
            cycle_time=self._notif_cfg.cycle_time_ms / 1000.0,
        )

        # Build a closure that captures the variable's name and type.
        callback = self._build_callback(name, variable.plc_type)

        handles = self._client.add_device_notification(name, attr, callback)
        if handles is None:
            raise PLCNotificationError(
                f"add_device_notification returned None for '{name}'",
                variable_name=name,
            )

        with self._lock:
            self._subscriptions[name] = handles
            variable.subscription_handle = handles[0]

        log.info("Subscribed to notification for '%s'", name)

    def unsubscribe_variable(self, variable_name: str) -> None:
        """
        Delete the ADS device notification for *variable_name*.

        Silently ignores variables that are not currently subscribed.

        Args:
            variable_name: Symbolic name of the variable to unsubscribe.
        """
        with self._lock:
            handles = self._subscriptions.pop(variable_name, None)

        if handles is None:
            log.debug("unsubscribe_variable: '%s' was not subscribed", variable_name)
            return

        notif_handle, user_handle = handles
        try:
            self._client.del_device_notification(notif_handle, user_handle)
        except PLCNotificationError as exc:
            log.warning("Could not delete notification for '%s': %s", variable_name, exc)

        # Clear the handle on the PLCVariable, if still in registry.
        var = self._registry.get_optional(variable_name)
        if var is not None:
            var.subscription_handle = None

        log.info("Unsubscribed from notification for '%s'", variable_name)

    def unsubscribe_all(self) -> None:
        """Unsubscribe every active notification."""
        with self._lock:
            names = list(self._subscriptions.keys())
        for name in names:
            self.unsubscribe_variable(name)

    def subscribe_all(self) -> None:
        """
        Subscribe to ADS notifications for every variable in the registry.

        Variables that fail to subscribe are logged as warnings; the method
        does not raise so that a single bad variable does not block the rest.
        """
        for var in self._registry:
            try:
                self.subscribe_variable(var)
            except PLCNotificationError as exc:
                log.warning("Could not subscribe to '%s': %s", var.name, exc)

    # ------------------------------------------------------------------
    # Internal: callback builder
    # ------------------------------------------------------------------

    def _build_callback(
        self, variable_name: str, plc_type: str
    ) -> Any:
        """
        Return a pyads-compatible callback closure for *variable_name*.

        Strategy (pyads 3.x compatible)
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Rather than attempting to decode the raw ctypes bytes from the
        ``SAdsNotificationHeader`` (which requires version-specific knowledge
        of the internal struct layout), this callback simply enqueues the
        variable name as a *change trigger*.  The dispatcher thread then
        performs a fresh ``read_by_name`` call to retrieve the current value.

        This approach is:
        * Simpler – no manual ctypes deserialisation.
        * Safer – always uses the same code-path as explicit reads.
        * Compatible with all pyads 3.x releases.

        Args:
            variable_name: Symbolic name of the variable.
            plc_type:      PLC type string (passed through to the item).

        Returns:
            A ``callback(notification, data) → None`` callable.
        """
        fmt = _STRUCT_FMT.get(plc_type.upper())

        def _callback(
            notification: Any,  # SAdsNotificationHeader (pyads 3.x)
            data: Any,           # (name, handle) tuple from pyads
            _name: str = variable_name,
            _type: str = plc_type,
            _fmt: Optional[str] = fmt,
        ) -> None:
            try:
                # Fast path: decode the raw notification payload in-place so
                # the dispatcher thread can skip the round-trip read_by_name.
                decoded_value: Optional[Any] = None
                if _fmt is not None:
                    try:
                        payload = bytes(notification.payload)
                        size = struct.calcsize(_fmt)
                        if len(payload) >= size:
                            (decoded_value,) = struct.unpack(_fmt, payload[:size])
                    except Exception:  # noqa: BLE001
                        decoded_value = None  # Dispatcher will fall back to read_by_name.

                item = _NotificationItem(
                    variable_name=_name,
                    plc_type=_type,
                    value=decoded_value,
                )
                try:
                    self._queue.put_nowait(item)
                except queue.Full:
                    log.warning(
                        "Notification queue full; dropping trigger for '%s'", _name
                    )
            except Exception as exc:  # noqa: BLE001
                log.error(
                    "Exception in ADS callback for '%s': %s",
                    variable_name,
                    exc,
                    exc_info=True,
                )

        return _callback

    # ------------------------------------------------------------------
    # Internal: dispatcher loop
    # ------------------------------------------------------------------

    def _dispatcher_loop(self) -> None:
        """
        Background thread that dequeues :class:`_NotificationItem` objects
        and applies them to the corresponding :class:`PLCVariable`.
        """
        log.debug("Notification dispatcher loop started")
        while self._running:
            try:
                item = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if item is None:
                # Poison pill – exit the loop.
                break

            try:
                var = self._registry.get_optional(item.variable_name)
                if var is None:
                    log.warning(
                        "Received notification for unregistered variable '%s'; discarding",
                        item.variable_name,
                    )
                    continue

                if item.value is not None:
                    # Fast path: value was decoded inline in the ADS callback;
                    # no extra round-trip to the PLC is required.
                    python_value = item.value
                    log.debug(
                        "Dispatched notification (inline): '%s' = %r",
                        item.variable_name,
                        python_value,
                    )
                else:
                    # Slow path: STRING, ARRAY, or inline decode failed –
                    # fetch the current value via a fresh read_by_name.
                    plc_type_obj = DataTypeConverter.get_pyads_type(item.plc_type)
                    raw = self._client.read_by_name(item.variable_name, plc_type_obj)
                    python_value = DataTypeConverter.to_python(item.plc_type, raw)
                    log.debug(
                        "Dispatched notification (read_by_name): '%s' = %r",
                        item.variable_name,
                        python_value,
                    )

                var.update_value(python_value)
            except Exception as exc:  # noqa: BLE001
                log.error(
                    "Dispatcher error processing notification for '%s': %s",
                    item.variable_name,
                    exc,
                    exc_info=True,
                )
            finally:
                self._queue.task_done()

        log.debug("Notification dispatcher loop exited")

    # ------------------------------------------------------------------
    # Helper: byte-length estimation for NotificationAttrib
    # ------------------------------------------------------------------

    @staticmethod
    def _plc_type_byte_length(plc_type: str) -> int:
        """
        Return an appropriate byte size for :class:`pyads.NotificationAttrib`.

        This is used only to size the pyads notification buffer; the actual
        de-serialisation is done by pyads itself.
        """
        _sizes: dict[str, int] = {
            "BOOL":   1,
            "BYTE":   1,
            "SINT":   1,
            "USINT":  1,
            "INT":    2,
            "UINT":   2,
            "DINT":   4,
            "UDINT":  4,
            "REAL":   4,
            "LINT":   8,
            "ULINT":  8,
            "LREAL":  8,
        }
        upper = plc_type.upper()
        if upper == "STRING":
            return 82  # 80 chars + 2-byte null terminator (pyads convention)
        return _sizes.get(upper, 4)  # Default to DINT-sized buffer.

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    @property
    def active_subscriptions(self) -> list[str]:
        """Return the names of all currently-subscribed variables."""
        with self._lock:
            return list(self._subscriptions.keys())

    @property
    def queue_depth(self) -> int:
        """Return the current number of pending notification items in the queue."""
        return self._queue.qsize()
