"""
style_manager.py
----------------
Loads and applies QSS (Qt Stylesheet) theme files from the
``resources/styles/`` directory to the running :class:`~PyQt6.QtWidgets.QApplication`.

Supported themes:

* ``"dark"``  – loads ``resources/styles/dark.qss``
* ``"light"`` – loads ``resources/styles/light.qss``

Usage::

    from plc_gui.utils.style_manager import StyleManager

    StyleManager.apply(app, "dark")

The chosen theme name is persisted in :class:`~PyQt6.QtCore.QSettings` so it
is restored on next launch.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings

from plc_gui.constants import STYLES_DIR, SETTING_THEME, APP_NAME, ORG_NAME

# Default if the settings key has never been written.
DEFAULT_THEME: str = "dark"

# Map theme name → QSS file name.
_THEME_FILES: dict[str, str] = {
    "dark": "dark.qss",
    "light": "light.qss",
}


class StyleManager:
    """
    Manages loading and switching of QSS themes at runtime.

    All methods are class-methods so no instance is required.
    """

    _current_theme: str = DEFAULT_THEME

    @classmethod
    def apply(cls, app: QApplication, theme: str | None = None) -> None:
        """
        Load and apply a QSS theme to *app*.

        If *theme* is ``None`` the previously persisted theme (or the default)
        is used.

        Args:
            app:   The running :class:`~PyQt6.QtWidgets.QApplication`.
            theme: ``"dark"`` or ``"light"``.  If ``None``, reads from
                   :class:`~PyQt6.QtCore.QSettings`.
        """
        if theme is None:
            settings = QSettings(ORG_NAME, APP_NAME)
            theme = settings.value(SETTING_THEME, DEFAULT_THEME)

        theme = theme.lower()
        if theme not in _THEME_FILES:
            theme = DEFAULT_THEME

        qss_path = STYLES_DIR / _THEME_FILES[theme]
        qss = cls._load_qss(qss_path)
        app.setStyleSheet(qss)
        cls._current_theme = theme

        # Persist choice.
        settings = QSettings(ORG_NAME, APP_NAME)
        settings.setValue(SETTING_THEME, theme)

    @classmethod
    def current_theme(cls) -> str:
        """Return the name of the currently active theme."""
        return cls._current_theme

    @classmethod
    def available_themes(cls) -> list[str]:
        """Return all theme names that have a corresponding QSS file."""
        return list(_THEME_FILES.keys())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_qss(path: Path) -> str:
        """Read a QSS file and return its content, or empty string on error."""
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""
        except OSError:
            return ""
