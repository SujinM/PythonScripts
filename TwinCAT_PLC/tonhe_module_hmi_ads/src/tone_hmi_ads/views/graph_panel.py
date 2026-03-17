"""
graph_panel.py
──────────────
Real-time voltage strip-chart panel using pyqtgraph.

A rolling deque keeps the last GRAPH_MAX_POINTS samples;
a time-window combo-box clips the visible range.
"""

from __future__ import annotations

import bisect
import time
from collections import deque
from typing import Optional

import pyqtgraph as pg
from PyQt6.QtCore import QTimer, Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from tone_hmi_ads.constants import GRAPH_MAX_POINTS

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

# ---------------------------------------------------------------------------
# Popup (full-screen) graph window
# ---------------------------------------------------------------------------

class GraphPopupWindow(QDialog):
    """A standalone resizable window that mirrors the main graph panel's data."""

    def __init__(self, graph_panel: "GraphPanel", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Output Voltage Graph")
        self.setWindowIcon(graph_panel.window().windowIcon())
        self.resize(1200, 700)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self._source = graph_panel

        pg.setConfigOptions(antialias=True)
        pg.setConfigOption('background', '#11111b')
        pg.setConfigOption('foreground', '#cdd6f4')

        self._gw = pg.GraphicsLayoutWidget(parent=self)
        self._gw.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._gw.ci.layout.setContentsMargins(14, 14, 14, 14)
        self._gw.ci.layout.setSpacing(16)

        def _make_plot(row, label, unit, color):
            p = self._gw.addPlot(row=row, col=0)
            p.setLabel("left", label, units=unit)
            if row == 1:
                p.setLabel("bottom", "Elapsed time", units="s")
            p.showGrid(x=True, y=True, alpha=0.12)
            p.setMouseEnabled(x=True, y=True)  # right-drag = box zoom
            p.enableAutoRange(axis=pg.ViewBox.YAxis)
            p.setLimits(yMin=0, xMin=0)
            for ax in ['left', 'bottom']:
                a = p.getAxis(ax)
                a.setPen(pg.mkPen(color="#45475a", width=1))
                a.setTextPen(pg.mkPen(color="#a6adc8"))
            curve = p.plot(pen=pg.mkPen(color=color, width=2.5))
            return p, curve

        self._v_plot, self._v_curve = _make_plot(0, "Voltage", "V", "#a6e3a1")
        self._v_plot.setLabel("bottom", "Elapsed time", units="s")
        self._gw.ci.layout.setRowStretchFactor(0, 1)

        # Crosshairs
        dash_pen = pg.mkPen(color="#6c7086", width=1.5, dash=[4, 4])
        self._v_vline = pg.InfiniteLine(angle=90, movable=False, pen=dash_pen)
        self._v_plot.addItem(self._v_vline, ignoreBounds=True)
        self._v_vline.hide()
        self._gw.scene().sigMouseMoved.connect(self._mouse_moved)

        # Hover label
        self._hover_lbl = QLabel("")
        self._hover_lbl.setStyleSheet(
            "font-family:'Consolas',monospace; font-size:11pt; "
            "font-weight:bold; color:#89b4fa;"
        )

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 4, 8, 4)
        toolbar.addWidget(QLabel("Hover over graph for values"))
        toolbar.addStretch()
        toolbar.addWidget(self._hover_lbl)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar)
        layout.addWidget(toolbar_widget)
        layout.addWidget(self._gw, stretch=1)

        # Refresh timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(250)

    def _refresh(self) -> None:
        if not self._source._t:
            return
        t_arr = list(self._source._t)
        v_arr = list(self._source._v)

        ws = self._source._window_s
        if ws > 0 and t_arr:
            cutoff = t_arr[-1] - ws
            start = next((i for i, t in enumerate(t_arr) if t >= cutoff), 0)
            t_arr = t_arr[start:]
            v_arr = v_arr[start:]

        self._v_curve.setData(t_arr, v_arr)

        if t_arr and ws > 0:
            x_max = t_arr[-1]
            self._v_plot.setXRange(x_max - ws, x_max, padding=0.02)

    @pyqtSlot(object)
    def _mouse_moved(self, pos) -> None:
        if not self._v_plot.sceneBoundingRect().contains(pos):
            self._v_vline.hide()
            self._hover_lbl.setText("")
            return

        mouse_point = self._v_plot.vb.mapSceneToView(pos)
        x_val = mouse_point.x()
        t_arr = list(self._source._t)
        v_arr = list(self._source._v)

        if not t_arr or x_val < t_arr[0] or x_val > t_arr[-1]:
            self._v_vline.hide()
            self._hover_lbl.setText("")
            return

        idx = bisect.bisect_left(t_arr, x_val)
        idx = max(0, min(idx, len(t_arr) - 1))
        if 0 < idx < len(t_arr):
            if abs(x_val - t_arr[idx - 1]) < abs(x_val - t_arr[idx]):
                idx -= 1

        self._v_vline.setPos(t_arr[idx])
        self._v_vline.show()
        self._hover_lbl.setText(
            f" t={t_arr[idx]:.1f}s | V={v_arr[idx]:.1f} V "
        )

    def closeEvent(self, event) -> None:
        self._timer.stop()
        if self._source._popup_win is self:
            self._source._popup_win = None
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# Main embedded panel
# ---------------------------------------------------------------------------


class GraphPanel(QWidget):
    """Rolling voltage strip-chart.

    Public API
    ~~~~~~~~~~
    append(voltage)       -- push a new sample (call from poll handler)
    clear()               -- discard all data and reset time origin
    reset_time_origin()   -- alias for clear(); call on new connection
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("graphPanel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(220)

        # ── Data buffers ──────────────────────────────────────────────────────
        self._t: deque[float] = deque(maxlen=GRAPH_MAX_POINTS)
        self._v: deque[float] = deque(maxlen=GRAPH_MAX_POINTS)
        self._t0: float = time.monotonic()
        self._paused: bool = False
        self._window_s: int = 60
        self._popup_win: Optional["GraphPopupWindow"] = None

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
            plot.setMouseEnabled(x=True, y=True)  # right-drag = box zoom, scroll = zoom X
            plot.enableAutoRange(axis=pg.ViewBox.YAxis)  # Y scales to data automatically
            plot.setLimits(xMin=0, yMin=0)  # never scroll below 0
            
            # Style axis lines
            for axis_name in ['left', 'bottom']:
                axis = plot.getAxis(axis_name)
                axis.setPen(pg.mkPen(color="#555555", width=1))
                axis.setTextPen(pg.mkPen(color="#aaaaaa"))

        # Voltage plot
        self._v_plot: pg.PlotItem = self._gw.addPlot(row=0, col=0)
        self._v_plot.setLabel("left", "Voltage", units="V")
        self._v_plot.setLabel("bottom", "Elapsed time", units="s")
        style_plot(self._v_plot)
        self._v_curve = self._v_plot.plot(
            pen=pg.mkPen(color="#2ecc71", width=2.5),
            name="Voltage",
        )

        self._gw.ci.layout.setSpacing(0)
        self._gw.ci.layout.setRowStretchFactor(0, 1)

        # ── Crosshairs ────────────────────────────────────────────────────────
        dash_pen = pg.mkPen(color="#888888", width=1.5, dash=[4, 4])
        self._v_vline = pg.InfiniteLine(angle=90, movable=False, pen=dash_pen)
        self._v_plot.addItem(self._v_vline, ignoreBounds=True)
        self._v_vline.hide()

        self._gw.scene().sigMouseMoved.connect(self._mouse_moved)

        # ── Controls bar ──────────────────────────────────────────────────────
        bar = QHBoxLayout()
        bar.setContentsMargins(8, 6, 8, 6)
        bar.setSpacing(10)

        bar.addWidget(QLabel("Window:"))

        self._win_combo = QComboBox()
        for label in _TIME_WINDOWS:
            self._win_combo.addItem(label)
        self._win_combo.setCurrentText("60 s")
        self._win_combo.currentTextChanged.connect(self._on_window_changed)
        bar.addWidget(self._win_combo)

        bar.addStretch()

        self._hover_label = QLabel("")
        self._hover_label.setStyleSheet(
            "font-family:'Consolas',monospace; font-size:11pt; "
            "font-weight:bold; color:#89b4fa;"
        )
        bar.addWidget(self._hover_label)

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

        self._reset_zoom_btn = QPushButton("⟳  Reset Zoom")
        self._reset_zoom_btn.setObjectName("btnResetZoom")
        self._reset_zoom_btn.setToolTip("Reset zoom / pan to default view")
        self._reset_zoom_btn.clicked.connect(self._reset_zoom)
        bar.addWidget(self._reset_zoom_btn)

        self._expand_btn = QPushButton("⛶")
        self._expand_btn.setObjectName("btnExpandGraph")
        self._expand_btn.setToolTip("Open graph in larger popup window")
        self._expand_btn.clicked.connect(self._toggle_popup)
        bar.addWidget(self._expand_btn)

        bar_widget = QWidget()
        bar_widget.setLayout(bar)

        # ── Assemble ──────────────────────────────────────────────────────────
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.addWidget(bar_widget)
        layout.addWidget(self._gw, stretch=1)

    # ── Public API ────────────────────────────────────────────────────────────

    def append(self, voltage: float | None) -> None:
        """Push a voltage sample.  Silently ignored when paused."""
        if self._paused:
            return
        v = float(voltage) if voltage is not None else float("nan")
        t = time.monotonic() - self._t0
        self._t.append(t)
        self._v.append(v)
        self._redraw()

    def clear(self) -> None:
        """Discard all buffered samples and reset the time origin."""
        self._t.clear()
        self._v.clear()
        self._t0 = time.monotonic()
        self._v_curve.setData([], [])

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

    @pyqtSlot()
    def _reset_zoom(self) -> None:
        """Reset X/Y zoom back to auto-range."""
        self._v_plot.enableAutoRange()
        if self._t and self._window_s > 0:
            self._redraw()

    @pyqtSlot()
    def _toggle_popup(self) -> None:
        """Open the popup graph window, or bring it to front if already open."""
        if self._popup_win is not None:
            self._popup_win.raise_()
            self._popup_win.activateWindow()
        else:
            self._popup_win = GraphPopupWindow(self, parent=None)
            self._popup_win.show()

    @pyqtSlot(object)
    def _mouse_moved(self, pos) -> None:
        """Handle mouse movement to update crosshairs and hover readout."""
        if self._v_plot.sceneBoundingRect().contains(pos):
            mouse_point = self._v_plot.vb.mapSceneToView(pos)
            self._update_hover(mouse_point.x())
        else:
            self._v_vline.hide()
            self._hover_label.setText("")

    def _update_hover(self, x_val: float) -> None:
        """Find the closest data point and update the UI."""
        if not self._t:
            return

        t_arr = list(self._t)
        v_arr = list(self._v)

        if not t_arr or x_val < t_arr[0] or x_val > t_arr[-1]:
            self._v_vline.hide()
            self._hover_label.setText("")
            return

        idx = bisect.bisect_left(t_arr, x_val)
        if idx == 0:
            idx = 0
        elif idx == len(t_arr):
            idx = len(t_arr) - 1
        else:
            if abs(x_val - t_arr[idx - 1]) < abs(x_val - t_arr[idx]):
                idx = idx - 1

        actual_t = t_arr[idx]
        v_val = v_arr[idx]

        self._v_vline.setPos(actual_t)
        self._v_vline.show()
        self._hover_label.setText(f" Time: {actual_t:.1f}s | Voltage: {v_val:.1f} V ")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _redraw(self) -> None:
        if not self._t:
            return
        t_arr = list(self._t)
        v_arr = list(self._v)

        if self._window_s > 0 and t_arr:
            cutoff = t_arr[-1] - self._window_s
            start = next((i for i, t in enumerate(t_arr) if t >= cutoff), 0)
            t_arr = t_arr[start:]
            v_arr = v_arr[start:]

        self._v_curve.setData(t_arr, v_arr)

        # Auto-scroll X to keep the latest data in view
        if t_arr and self._window_s > 0:
            x_max = t_arr[-1]
            x_min = x_max - self._window_s
            self._v_plot.setXRange(x_min, x_max, padding=0.02)
