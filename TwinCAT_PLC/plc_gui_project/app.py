"""
app.py
------
Application entry point for the TwinCAT 3 PLC Monitor GUI.

Responsibilities
~~~~~~~~~~~~~~~~
* Bootstrap the Python path so ``plc_gui`` (in ``src/``) can be imported.
* Create :class:`~PyQt6.QtWidgets.QApplication`.
* Configure HiDPI / font settings.
* Attach :class:`~plc_gui.utils.qt_log_handler.QtLogHandler` to the root
  Python logger so all log output is mirrored to the GUI log panel.
* Show :class:`~plc_gui.views.main_window.MainWindow`.
* Trigger :meth:`~plc_gui.views.main_window.MainWindow.install_controller`
  on the next event-loop tick so the window appears before heavy imports
  (ADS backend) begin.
* Run the Qt event loop and exit cleanly.

Usage::

    python app.py
    # or after installation:
    plcmonitor
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Ensure the src/ package directory is on sys.path so ``import plc_gui``
# works whether the app is run from the repo root OR from a frozen bundle.
# ---------------------------------------------------------------------------
def _bootstrap_path() -> None:
    src_dir = Path(__file__).resolve().parent / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


_bootstrap_path()

# ---------------------------------------------------------------------------
# Now safe to import plc_gui modules.
# ---------------------------------------------------------------------------
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from plc_gui.constants import APP_NAME, APP_VERSION, ORG_NAME, APP_ID
from plc_gui.utils.qt_log_handler import QtLogHandler
from plc_gui.utils.style_manager import StyleManager
from plc_gui.views.main_window import MainWindow


def _configure_logging(handler: QtLogHandler) -> None:
    """Attach the Qt log handler to the root logger."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    # Console handler for developers running from a terminal.
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        root_logger.addHandler(ch)
    root_logger.addHandler(handler)


def main() -> int:
    """Application entry point; returns the process exit code."""

    # Windows: tell the OS this is a custom app (not python.exe) so the
    # taskbar shows the correct icon and title.
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except Exception:
            pass

    # Enable DPI awareness on Windows before creating the QApplication.
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(ORG_NAME)
    app.setOrganizationDomain("twincattools.local")

    # Use the platform default font but bump size to 10pt minimum.
    font = app.font()
    if font.pointSize() < 10:
        font.setPointSize(10)
        app.setFont(font)

    # Apply the persisted (or default) theme.
    StyleManager.apply(app)

    # Main window.
    window = MainWindow()

    # Create the Qt log handler BEFORE showing the window so early log records
    # are captured, then connect it to the log panel model.
    qt_handler = QtLogHandler(level=logging.DEBUG, parent=window)
    _configure_logging(qt_handler)
    qt_handler.record_emitted.connect(window.log_panel.model.append_record)

    window.show()

    # Defer controller construction by one tick so the window paints first.
    QTimer.singleShot(0, window.install_controller)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
