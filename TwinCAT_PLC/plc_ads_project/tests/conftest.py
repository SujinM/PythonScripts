"""
conftest.py
-----------
Pytest configuration for the plc_ads_project test suite.

Adds the project root directory to ``sys.path`` so that all test modules can
use absolute imports (e.g. ``from models.plc_variable import PLCVariable``)
without installing the package.

This file is auto-discovered by pytest when it exists in the tests/ directory
or any parent directory.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Project root is the parent of this conftest.py (i.e. plc_ads_project/).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
