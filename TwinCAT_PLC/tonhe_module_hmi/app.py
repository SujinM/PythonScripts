"""
app.py
──────
Entry point for the TONHE Module HMI.

Usage::

    python app.py
"""

from __future__ import annotations

import logging
import os
import sys
import traceback
from pathlib import Path


def _bootstrap_path() -> None:
    """Add src/ to sys.path when running from source or frozen."""
    if getattr(sys, "frozen", False):
        # cx_Freeze: exe lives at bundle root; tone_hmi package is zipped inside
        # _internal/lib/library.zip – cx_Freeze adds that automatically.
        # Nothing extra needed here.
        pass
    else:
        src_dir = Path(__file__).resolve().parent / "src"
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))


def _setup_crash_log() -> Path:
    """Return path to crash log file next to the exe (or cwd from source)."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent
    return base / "ToneHMI_crash.log"


_bootstrap_path()

# ---------------------------------------------------------------------------
# Top-level import guard  (catches missing-module errors in GUI / frozen builds)
# ---------------------------------------------------------------------------
try:
    from PyQt6.QtCore import QTimer, Qt
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QApplication

    from tone_hmi.constants import APP_NAME, APP_VERSION, ORG_NAME, APP_ID
    from tone_hmi.utils.qt_log_handler import QtLogHandler
    from tone_hmi.utils.style_manager import StyleManager
    from tone_hmi.views.main_window import MainWindow
except Exception:  # noqa: BLE001
    import traceback
    crash_log = _setup_crash_log()
    try:
        crash_log.write_text(traceback.format_exc(), encoding="utf-8")
    except Exception:
        pass
    raise


def _configure_logging(handler: QtLogHandler) -> None:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        root.addHandler(ch)
    root.addHandler(handler)


def main() -> int:
    # Windows app model ID (taskbar icon)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except Exception:
            pass

    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(ORG_NAME)

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Log handler – wired to the log panel after window is ready
    qt_handler = QtLogHandler()

    window = MainWindow()

    # Wire the Qt log handler to the log panel model
    qt_handler.record_emitted.connect(window.log_panel.model.append_record)
    qt_handler.record_emitted.connect(lambda _: window.log_panel.scroll_to_bottom())
    _configure_logging(qt_handler)

    # Apply dark theme by default (user can switch via View menu)
    StyleManager.apply(app)

    window.show()

    # Deferred controller init so the window appears before heavy imports
    QTimer.singleShot(0, window.install_controller)

    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001
        crash_log = _setup_crash_log()
        try:
            crash_log.write_text(
                traceback.format_exc(), encoding="utf-8"
            )
        except Exception:
            pass
        # Re-raise so a console build still shows the traceback
        raise
