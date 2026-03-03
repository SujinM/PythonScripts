"""
write_dialog.py
---------------
:class:`WriteDialog` is a modal :class:`~PyQt6.QtWidgets.QDialog` used to
write a new value to a PLC variable.

The dialog shows:
* The symbolic variable name (read-only).
* The PLC data type (read-only).
* The current value (read-only).
* A :class:`~PyQt6.QtWidgets.QLineEdit` for the new value.
* Standard **Write** / **Cancel** buttons.

Input validation is performed when **Write** is clicked:
* Non-empty.
* Type coercion check (bool/int/float/str) based on the PLC type.
* Integer range validation for bounded integer types.

On ``exec()`` returning ``QDialog.Accepted``, call :meth:`new_value` to
obtain the Python-typed value ready to pass to
:class:`~services.plc_write_service.PLCWriteService`.
"""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

# Range checks for bounded integer PLC types.
_INT_RANGES: dict[str, tuple[int, int]] = {
    "INT":   (-32_768, 32_767),
    "DINT":  (-2_147_483_648, 2_147_483_647),
    "UDINT": (0, 4_294_967_295),
}


class WriteDialog(QDialog):
    """
    Modal dialog to write a value to a PLC variable.

    Args:
        variable_name: Symbolic name of the variable (``MAIN.nSpeed``).
        plc_type:      PLC type string (``INT``, ``BOOL``, ``REAL``, …).
        current_value: Current Python-typed value of the variable (may be ``None``).
        parent:        Optional Qt parent widget.
    """

    def __init__(
        self,
        variable_name: str,
        plc_type: str,
        current_value: Any,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Write PLC Variable")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._plc_type = plc_type.upper()
        self._new_value: Any = None

        # Read-only info fields.
        self._name_label = QLabel(variable_name)
        self._type_label = QLabel(plc_type)
        self._current_label = QLabel(str(current_value) if current_value is not None else "–")
        self._current_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Input field.
        self._value_edit = QLineEdit()
        if current_value is not None:
            self._value_edit.setText(str(current_value))
        self._value_edit.selectAll()
        placeholder = self._placeholder_text()
        self._value_edit.setPlaceholderText(placeholder)

        # Hint label (shows allowed range for integers).
        self._hint_label = QLabel(self._hint_text())
        self._hint_label.setObjectName("labelHint")

        # Buttons.
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Write")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        # Layout.
        form = QFormLayout()
        form.addRow("Variable:", self._name_label)
        form.addRow("Type:", self._type_label)
        form.addRow("Current value:", self._current_label)
        form.addRow("New value:", self._value_edit)
        form.addRow("", self._hint_label)

        vbox = QVBoxLayout(self)
        vbox.addLayout(form)
        vbox.addWidget(buttons)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def new_value(self) -> Any:
        """Return the validated, Python-typed value entered by the user."""
        return self._new_value

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_and_accept(self) -> None:
        raw = self._value_edit.text().strip()
        if not raw:
            QMessageBox.warning(self, "Validation Error", "Please enter a value.")
            return

        try:
            value = self._coerce(raw)
        except (ValueError, TypeError) as exc:
            QMessageBox.warning(
                self,
                "Validation Error",
                f"Cannot convert '{raw}' to {self._plc_type}:\n{exc}",
            )
            return

        self._new_value = value
        self.accept()

    def _coerce(self, raw: str) -> Any:
        """Coerce raw text to the expected Python type."""
        pt = self._plc_type
        if pt == "BOOL":
            lower = raw.lower()
            if lower in ("true", "1", "yes", "on"):
                return True
            if lower in ("false", "0", "no", "off"):
                return False
            raise ValueError(f"Expected true/false/1/0, got '{raw}'")

        if pt in ("INT", "DINT", "UDINT"):
            v = int(raw)
            lo, hi = _INT_RANGES.get(pt, (-2**63, 2**63 - 1))
            if not (lo <= v <= hi):
                raise ValueError(f"Value {v} is out of {pt} range [{lo}, {hi}]")
            return v

        if pt in ("REAL", "LREAL"):
            return float(raw)

        # STRING or unknown.
        return raw

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _placeholder_text(self) -> str:
        pt = self._plc_type
        if pt == "BOOL":
            return "true / false"
        if pt in ("INT", "DINT", "UDINT"):
            return "integer"
        if pt in ("REAL", "LREAL"):
            return "float"
        return "string"

    def _hint_text(self) -> str:
        lo, hi = _INT_RANGES.get(self._plc_type, (None, None))
        if lo is not None:
            return f"Range: {lo:,} … {hi:,}"
        if self._plc_type == "BOOL":
            return "Accepted: true, false, 1, 0, yes, no"
        return ""
