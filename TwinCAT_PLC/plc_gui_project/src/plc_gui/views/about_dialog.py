"""
about_dialog.py
---------------
Minimal **About** dialog that shows application name, version, and backend
library versions at runtime.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from plc_gui.constants import APP_NAME, APP_VERSION


class AboutDialog(QDialog):
    """
    Simple 'About' dialog.

    Args:
        parent: Optional Qt parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(400, 260)
        self.setModal(True)

        title = QLabel(f"<h2>{APP_NAME}</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version_label = QLabel(f"<b>Version:</b> {APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc = QLabel(
            "A PyQt6 GUI for bidirectional communication with<br>"
            "TwinCAT 3 PLCs using the ADS (AMS/TCP) protocol."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)

        backend_info = self._build_backend_info()
        backend_label = QLabel(backend_info)
        backend_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)

        vbox = QVBoxLayout(self)
        vbox.setSpacing(12)
        vbox.addWidget(title)
        vbox.addWidget(version_label)
        vbox.addWidget(desc)
        vbox.addWidget(backend_label)
        vbox.addStretch()
        vbox.addWidget(buttons)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_backend_info() -> str:
        lines: list[str] = []
        try:
            import PyQt6.QtCore as _qtc
            lines.append(f"<b>PyQt6:</b> {_qtc.PYQT_VERSION_STR}")
        except Exception:
            pass
        try:
            import pyads
            lines.append(f"<b>pyads:</b> {pyads.__version__}")
        except Exception:
            pass
        try:
            import sys
            lines.append(f"<b>Python:</b> {sys.version.split()[0]}")
        except Exception:
            pass
        return "<br>".join(lines) if lines else ""
