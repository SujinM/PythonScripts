"""
File-system change trigger.

Monitors a directory (or single file) for modification events.
When any watched path has been modified since the last check, it emits
a TriggerEvent with full details of which file changed.

Designed for:
  - Log file monitoring
  - Config file hot-reload alerts
  - Incoming data file detection
  - Raspberry Pi GPIO or sensor CSV output watching
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Optional

from triggers.base_trigger import BaseTrigger, TriggerEvent
from utils.logger import get_logger

logger = get_logger(__name__)


class FileTrigger(BaseTrigger):
    """
    Fires when a monitored file or directory entry is created or modified.

    Args:
        watch_path:     Absolute or relative path to a file or directory.
        extensions:     Optional list of file extensions to watch (e.g. [".csv", ".log"]).
                        Pass an empty list to watch all files.
        recursive:      Watch sub-directories recursively (default False).
        message_prefix: Prefix used in the event message.
    """

    def __init__(
        self,
        watch_path: str,
        extensions: Optional[List[str]] = None,
        recursive: bool = False,
        message_prefix: str = "File change detected",
    ) -> None:
        self._watch_path = os.path.abspath(watch_path)
        self._extensions: List[str] = [
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in (extensions or [])
        ]
        self._recursive = recursive
        self._message_prefix = message_prefix
        # Map filepath → last known mtime
        self._snapshot: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # BaseTrigger interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "FileTrigger"

    def setup(self) -> None:
        """Take an initial snapshot so we only alert on changes after startup."""
        if not os.path.exists(self._watch_path):
            logger.warning(
                "%s: watch path does not exist yet: %s", self.name, self._watch_path
            )
        self._snapshot = self._collect_mtimes()
        logger.info(
            "%s initialised — watching: %s (%d file(s) in snapshot).",
            self.name,
            self._watch_path,
            len(self._snapshot),
        )

    def check(self) -> Optional[TriggerEvent]:
        current = self._collect_mtimes()
        changed: List[str] = []

        for path, mtime in current.items():
            if path not in self._snapshot or self._snapshot[path] != mtime:
                changed.append(path)

        # Also detect new files
        new_files = set(current) - set(self._snapshot)
        for path in new_files:
            if path not in changed:
                changed.append(path)

        # Update snapshot regardless
        self._snapshot = current

        if changed:
            paths_str = ", ".join(os.path.basename(p) for p in changed[:5])
            if len(changed) > 5:
                paths_str += f" … (+{len(changed) - 5} more)"

            message = f"{self._message_prefix}: {paths_str}"
            logger.info("%s fired — %s", self.name, message)
            return TriggerEvent(
                source=self.name,
                message=message,
                severity="WARNING",
                timestamp=datetime.now(),
                metadata={
                    "changed_files": changed,
                    "watch_path": self._watch_path,
                },
            )

        return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_mtimes(self) -> Dict[str, float]:
        """Walk the watch path and return {filepath: mtime} for matching files."""
        result: Dict[str, float] = {}

        if not os.path.exists(self._watch_path):
            return result

        if os.path.isfile(self._watch_path):
            if self._matches(self._watch_path):
                result[self._watch_path] = os.path.getmtime(self._watch_path)
            return result

        # It's a directory
        walker = os.walk(self._watch_path) if self._recursive else [(
            self._watch_path,
            [],
            os.listdir(self._watch_path),
        )]

        for dirpath, _, filenames in walker:
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                if self._matches(fpath):
                    try:
                        result[fpath] = os.path.getmtime(fpath)
                    except OSError:
                        pass  # File removed between listing and stat

        return result

    def _matches(self, filepath: str) -> bool:
        """Return True if the file should be monitored based on extension filter."""
        if not self._extensions:
            return True
        _, ext = os.path.splitext(filepath)
        return ext.lower() in self._extensions
