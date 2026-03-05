"""
graph_panel.py
──────────────
Real-time voltage and current strip-chart panel using pyqtgraph.

Two vertically stacked plots share a linked X axis so panning one
synchronises the other.  A rolling deque keeps the last GRAPH_MAX_POINTS
samples; a time-window combo-box clips the visible range.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Optional

import pyqtgraph as pg
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from tone_hmi.constants import GRAPH_MAX_POINTS

# ---------------------------------------------------------------------------
# Time-window options  (label → seconds, 0 = show all buffered data)
# ---------------------------------------------------------------------------
_TIME_WINDOWS: dict[str, int] = {
    "30 s":  30,
    "60 s":  60,
    "2 min": 120,
    "5 min": 300,
    "All":   0,
}


class GraphPanel(QWidget):
    """Rolling voltage / current strip-chart.

    Public API
    ~~~~~~~~~~
    append(voltage, current)  -- push a new sample (call from poll handler)
    clear()                   -- discard all data and reset time origin
    reset_time_origin()       -- alias for clear(); call on new connection
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("graphPanel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(220)

        # ── Data buffers ──────────────────────────────────────────────────────
        self._t: deque[float] = deque(maxlen=GRAPH_MAX_POINTS)
        self._v: deque[float] = deque(maxlen=GRAPH_MAX_POINTS)
        self._a: deque[float] = deque(maxlen=GRAPH_MAX_POINTS)
        self._t0: float = time.monotonic()
        self._paused: bool = False
        self._window_s: int = 60

        # ── pyqtgraph setup ───────────────────────────────────────────────────
        pg.setConfigOptions(antialias=True)
        # Apply dark theme configuration
        pg.setConfigOption('background', '#1e1e1e')
        pg.setConfigOption('foreground', '#d4d4d4')
        
        self._gw = pg.GraphicsLayoutWidget(parent=self)
        self._gw.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Add internal padding
        self._gw.ci.layout.setContentsMargins(10, 10, 10, 10)

        # Common axis styling function
        def style_plot(plot: pg.PlotItem):
            plot.showGrid(x=True, y=True, alpha=0.15)
            plot.setMouseEnabled(x=True, y=False)  # Allow X panning, but fix Y auto-scaling behavior
            plot.enableAutoRange(y=True)
            plot.setLimits(yMin=0)  # Y-axis always starts at 0
            plot.setLimits(xMin=0)  # X-axis always starts at 0 
            
            # Style axis lines
            for axis_name in ['left', 'bottom']:
                axis = plot.getAxis(axis_name)
                axis.setPen(pg.mkPen(color="#555555", width=1))
                axis.setTextPen(pg.mkPen(color="#aaaaaa"))

        # Voltage plot (top)
        self._v_plot: pg.PlotItem = self._gw.addPlot(row=0, col=0)
        self._v_plot.setLabel("left", "Voltage", units="V")
        style_plot(self._v_plot)
        self._v_curve = self._v_plot.plot(
            pen=pg.mkPen(color="#2ecc71", width=2.5),
            name="Voltage",
        )

        # Current plot (bottom) — X axis linked to voltage plot
        self._a_plot: pg.PlotItem = self._gw.addPlot(row=1, col=0)
        self._a_plot.setLabel("left", "Current", units="A")
        self._a_plot.setLabel("bottom", "Elapsed time", units="s")
        style_plot(self._a_plot)
        self._a_plot.setXLink(self._v_plot)
        self._a_curve = self._a_plot.plot(
            pen=pg.mkPen(color="#3498db", width=2.5),
            name="Current",
        )

        self._gw.ci.layout.setSpacing(15)
        self._gw.ci.layout.setRowStretchFactor(0, 1)
        self._gw.ci.layout.setRowStretchFactor(1, 1)

        # ── Controls bar ──────────────────────────────────────────────────────
        bar = QHBoxLayout()
        bar.setContentsMargins(4, 2, 4, 2)
        bar.setSpacing(8)

        bar.addWidget(QLabel("Window:"))

        self._win_combo = QComboBox()
        for label in _TIME_WINDOWS:
            self._win_combo.addItem(label)
        self._win_combo.setCurrentText("60 s")
        self._win_combo.currentTextChanged.connect(self._on_window_changed)
        bar.addWidget(self._win_combo)

        bar.addStretch()

        self._pause_btn = QPushButton("⏸  Pause")
        self._pause_btn.setObjectName("btnPauseGraph")
        self._pause_btn.setCheckable(True)
        self._pause_btn.toggled.connect(self._on_pause_toggled)
        bar.addWidget(self._pause_btn)

        self._clear_btn = QPushButton("✕  Clear")
        self._clear_btn.setObjectName("btnClearGraph")
        self._clear_btn.clicked.connect(self.clear)
        bar.addWidget(self._clear_btn)

        bar_widget = QWidget()
        bar_widget.setLayout(bar)

        # ── Assemble ──────────────────────────────────────────────────────────
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.addWidget(bar_widget)
        layout.addWidget(self._gw, stretch=1)

    # ── Public API ────────────────────────────────────────────────────────────

    def append(self, voltage: float | None, current: float | None) -> None:
        """Push a voltage/current sample.  Silently ignored when paused."""
        if self._paused:
            return
        v = float(voltage) if voltage is not None else float("nan")
        a = float(current) if current is not None else float("nan")
        t = time.monotonic() - self._t0
        self._t.append(t)
        self._v.append(v)
        self._a.append(a)
        self._redraw()

    def clear(self) -> None:
        """Discard all buffered samples and reset the time origin."""
        self._t.clear()
        self._v.clear()
        self._a.clear()
        self._t0 = time.monotonic()
        self._v_curve.setData([], [])
        self._a_curve.setData([], [])

    def reset_time_origin(self) -> None:
        """Restart time origin; call whenever a new ADS connection is made."""
        self.clear()

    # ── Slots ─────────────────────────────────────────────────────────────────

    @pyqtSlot(str)
    def _on_window_changed(self, label: str) -> None:
        self._window_s = _TIME_WINDOWS.get(label, 60)
        self._redraw()

    @pyqtSlot(bool)
    def _on_pause_toggled(self, checked: bool) -> None:
        self._paused = checked
        self._pause_btn.setText("▶  Resume" if checked else "⏸  Pause")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _redraw(self) -> None:
        if not self._t:
            return
        t_arr = list(self._t)
        v_arr = list(self._v)
        a_arr = list(self._a)

        if self._window_s > 0 and t_arr:
            cutoff = t_arr[-1] - self._window_s
            start = next((i for i, t in enumerate(t_arr) if t >= cutoff), 0)
            t_arr = t_arr[start:]
            v_arr = v_arr[start:]
            a_arr = a_arr[start:]

        self._v_curve.setData(t_arr, v_arr)
        self._a_curve.setData(t_arr, a_arr)

        # Auto-scroll X to keep the latest data in view
        if t_arr and self._window_s > 0:
            x_max = t_arr[-1]
            x_min = x_max - self._window_s
            self._v_plot.setXRange(x_min, x_max, padding=0.02)
            
        # Force Y-axis to bound between 0 and the max data value (plus a 5% margin)
        if v_arr:
            v_max = max(v_arr)
            v_limit = v_max * 1.05 if v_max > 0 else 10.0
            self._v_plot.setYRange(0, v_limit, padding=0.0)
            
        if a_arr:
            a_max = max(a_arr)
            a_limit = a_max * 1.05 if a_max > 0 else 10.0
            self._a_plot.setYRange(0, a_limit, padding=0.0)
