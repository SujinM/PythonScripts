"""
notification_bridge.py
──────────────────────
Bridges PLCVariable change-hook callbacks (fired from the ADS dispatcher
thread) to the Qt GUI thread via a thread-safe queued signal.

Architecture
~~~~~~~~~~~~
::

    ADS dispatcher thread
          │  (PLCVariable change hook fires)
          ▼
    NotificationBridge.variable_changed  (pyqtSignal – auto-queued across threads)
          │
          ▼
    ModuleController._on_variable_changed(name)  (runs on Qt main thread)
          │
          ▼
    Panel update methods

Why is this safe?
~~~~~~~~~~~~~~~~~
PyQt6 signals emitted from a non-GUI thread to a slot in the GUI thread are
automatically delivered via a QueuedConnection.  No manual locking or
QMetaObject.invokeMethod calls are required.
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from tone_hmi_ads.app_context import AppContext


class NotificationBridge(QObject):
    """
    Receives PLCVariable change-hook callbacks and re-emits them as a
    thread-safe Qt signal carrying the changed variable's name.

    Signals:
        variable_changed: Emitted (with the variable name) whenever a
                          subscribed PLCVariable's value changes.  Always
                          delivered on the Qt main thread regardless of which
                          thread fired the underlying change hook.
    """

    variable_changed = pyqtSignal(str)   # variable name

    def __init__(self, ctx: AppContext, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._ctx = ctx

    def register_all_hooks(self) -> None:
        """
        Register this bridge as a change hook on every variable in the registry.

        Must be called after ``AppContext.load()`` and before
        ``AppContext.setup_notifications()``.  The ordering ensures that when
        the first ADS notification fires, the hook is already in place.
        """
        if not self._ctx.registry:
            return
        for var in self._ctx.registry:
            name = var.name
            # Capture `name` per-iteration with a default-argument closure.
            var.register_change_hook(
                lambda val, n=name: self.variable_changed.emit(n)
            )
