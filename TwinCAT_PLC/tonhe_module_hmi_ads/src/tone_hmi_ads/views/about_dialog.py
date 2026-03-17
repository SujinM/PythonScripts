"""
about_dialog.py
────────────────
Simple About dialog for the TONHE Module HMI.
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

from tone_hmi_ads.constants import APP_NAME, APP_VERSION


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(420, 280)
        self.setModal(True)

        title = QLabel(f"<h2>{APP_NAME}</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version_label = QLabel(f"<b>Version:</b> {APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc = QLabel(
            "HMI for TONHE CAN charging modules via TwinCAT 3 ADS."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)

        backend_label = QLabel(self._build_backend_info())
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
