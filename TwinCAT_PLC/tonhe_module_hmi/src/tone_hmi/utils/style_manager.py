"""
style_manager.py
────────────────
Loads and applies QSS theme files to the running QApplication.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from tone_hmi.constants import APP_NAME, ORG_NAME, SETTING_THEME, STYLES_DIR

DEFAULT_THEME: str = "dark"

_THEME_FILES: dict[str, str] = {
    "dark": "dark.qss",
    "light": "light.qss",
}


class StyleManager:
    _current_theme: str = DEFAULT_THEME

    @classmethod
    def apply(cls, app: QApplication, theme: str | None = None) -> None:
        if theme is None:
            settings = QSettings(ORG_NAME, APP_NAME)
            theme = settings.value(SETTING_THEME, DEFAULT_THEME)

        theme = (theme or DEFAULT_THEME).lower()
        if theme not in _THEME_FILES:
            theme = DEFAULT_THEME

        qss_path = STYLES_DIR / _THEME_FILES[theme]
        qss = cls._load_qss(qss_path)
        app.setStyleSheet(qss)
        cls._current_theme = theme

        settings = QSettings(ORG_NAME, APP_NAME)
        settings.setValue(SETTING_THEME, theme)

    @classmethod
    def current_theme(cls) -> str:
        return cls._current_theme

    @staticmethod
    def _load_qss(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""
