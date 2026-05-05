"""
General-purpose utility functions.

Pure helpers for formatting and safe data access.
No imports from app.* to avoid circular dependencies.
"""

from typing import Any


def format_currency(amount: float, symbol: str = "$") -> str:
    """
    Format a float as a currency string with thousands separators.

    Examples:
        >>> format_currency(1234567.89)
        '$1,234,567.89'
        >>> format_currency(-500.5, "€")
        '-€500.50'
    """
    prefix = "-" if amount < 0 else ""
    return f"{prefix}{symbol}{abs(amount):,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format a float as a signed percentage string.

    Examples:
        >>> format_percentage(10.5)
        '+10.50%'
        >>> format_percentage(-3.2)
        '-3.20%'
    """
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def pnl_color(value: float) -> str:
    """
    Return 'green' or 'red' based on sign of value.
    Used with Rich markup: ``[{pnl_color(val)}]text[/{pnl_color(val)}]``
    """
    return "green" if value >= 0 else "red"


def truncate(text: str, max_len: int = 20) -> str:
    """
    Truncate text to max_len characters, appending '…' if clipped.

    Examples:
        >>> truncate("Apple Inc. Common Stock", 15)
        'Apple Inc. Com…'
    """
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """
    Safely traverse nested dicts.

    Examples:
        >>> safe_get({"a": {"b": 1}}, "a", "b")
        1
        >>> safe_get({}, "a", "b", default=0)
        0
    """
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current
