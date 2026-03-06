"""
test_plc_application.py
-----------------------
Unit tests for :class:`~main.PLCApplication`.

Tests cover:
    * ``_export_snapshot_to_json`` writes to a single fixed file
      (``snapshot_latest.json``) instead of creating a new file per cycle,
      preventing unbounded disk growth (improvement #4).
    * ``health()`` returns a :class:`~main.HealthReport` with sensible
      values before and after initialisation (improvement #5).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# ---------------------------------------------------------------------------
# Bootstrap sys.path so imports resolve without an installed package.
# ---------------------------------------------------------------------------
import sys
import os

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from main import PLCApplication, HealthReport
from models.variable_registry import VariableRegistry


# ===========================================================================
# Helpers
# ===========================================================================

def _make_app(tmp_path: Path, export_dir: str | None = None) -> PLCApplication:
    """Return a partially-initialised PLCApplication (start() not called)."""
    return PLCApplication(
        config_path=str(_PROJECT_ROOT / "config" / "plc_config.xml"),
        poll_interval=2.0,
        demo_writes=False,
        export_json=True,
        export_dir=export_dir or str(tmp_path / "exports"),
    )


def _populate_registry(app: PLCApplication) -> VariableRegistry:
    """Inject a minimal registry so export methods work without a real PLC."""
    reg = VariableRegistry()
    reg.register("MAIN.bMotorOn", "BOOL")
    reg.register("MAIN.nSpeed",   "INT")
    app._registry = reg  # type: ignore[attr-defined]
    return reg


# ===========================================================================
# JSON export – single-file behaviour (#4)
# ===========================================================================

class TestExportSnapshotToJson:
    def test_writes_snapshot_latest_json(self, tmp_path: Path) -> None:
        """The export method must write to 'snapshot_latest.json', not a
        per-cycle timestamped file."""
        app = _make_app(tmp_path)
        _populate_registry(app)

        app._export_snapshot_to_json()  # type: ignore[attr-defined]

        export_dir = Path(app._export_dir)  # type: ignore[attr-defined]
        files = list(export_dir.iterdir())
        assert len(files) == 1, f"Expected 1 file, got: {[f.name for f in files]}"
        assert files[0].name == "snapshot_latest.json"

    def test_repeated_calls_do_not_accumulate_files(self, tmp_path: Path) -> None:
        """Calling the export method N times must still yield exactly one file."""
        app = _make_app(tmp_path)
        _populate_registry(app)

        for _ in range(5):
            app._export_snapshot_to_json()  # type: ignore[attr-defined]

        export_dir = Path(app._export_dir)  # type: ignore[attr-defined]
        assert len(list(export_dir.iterdir())) == 1

    def test_export_content_is_valid_json(self, tmp_path: Path) -> None:
        """The written file must contain valid JSON."""
        app = _make_app(tmp_path)
        _populate_registry(app)

        app._export_snapshot_to_json()  # type: ignore[attr-defined]

        file_path = Path(app._export_dir) / "snapshot_latest.json"  # type: ignore[attr-defined]
        content = json.loads(file_path.read_text(encoding="utf-8"))
        assert isinstance(content, (dict, list))

    def test_overwritten_content_reflects_latest_state(self, tmp_path: Path) -> None:
        """The second write must overwrite the first (content changes)."""
        app = _make_app(tmp_path)
        reg = _populate_registry(app)

        app._export_snapshot_to_json()  # type: ignore[attr-defined]
        first = (Path(app._export_dir) / "snapshot_latest.json").read_text(encoding="utf-8")  # type: ignore[attr-defined]

        # Mutate a variable value so the snapshot changes.
        var = reg.get("MAIN.nSpeed")
        var.update_value(9999)

        app._export_snapshot_to_json()  # type: ignore[attr-defined]
        second = (Path(app._export_dir) / "snapshot_latest.json").read_text(encoding="utf-8")  # type: ignore[attr-defined]

        assert second != first, "File content should have changed after value update"


# ===========================================================================
# HealthReport / health() (#5)
# ===========================================================================

class TestHealthReport:
    def test_health_before_start_returns_report_instance(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)
        report = app.health()
        assert isinstance(report, HealthReport)

    def test_health_not_connected_before_start(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)
        report = app.health()
        assert report.connected is False

    def test_health_connection_state_before_start(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)
        report = app.health()
        assert report.connection_state == "NOT_INITIALISED"

    def test_health_variable_count_before_registry(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)
        assert app.health().variable_count == 0

    def test_health_variable_count_after_registry_set(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)
        _populate_registry(app)
        assert app.health().variable_count == 2

    def test_health_uptime_increases_over_time(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)
        app._start_time = time.monotonic()  # type: ignore[attr-defined]
        time.sleep(0.05)
        assert app.health().uptime_seconds >= 0.04

    def test_health_uptime_zero_before_start(self, tmp_path: Path) -> None:
        """uptime_seconds must be 0.0 when start() has not been called."""
        app = _make_app(tmp_path)
        assert app.health().uptime_seconds == 0.0

    def test_health_active_subscriptions_zero_before_notif_manager(
        self, tmp_path: Path
    ) -> None:
        app = _make_app(tmp_path)
        assert app.health().active_subscriptions == 0

    def test_health_queue_depth_zero_before_notif_manager(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)
        assert app.health().queue_depth == 0

    def test_health_with_mock_notif_manager(self, tmp_path: Path) -> None:
        """health() correctly reads active_subscriptions and queue_depth from
        a live NotificationManager mock."""
        app = _make_app(tmp_path)
        mock_nm = MagicMock()
        mock_nm.active_subscriptions = ["MAIN.bMotorOn", "MAIN.nSpeed"]
        mock_nm.queue_depth = 3
        app._notif_manager = mock_nm  # type: ignore[attr-defined]

        report = app.health()
        assert report.active_subscriptions == 2
        assert report.queue_depth == 3
