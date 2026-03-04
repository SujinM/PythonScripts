"""
setup.py
--------
cx_Freeze build script for TwinCAT 3 PLC Monitor.

Produces:
    build/exe.win-amd64-<py_ver>/   – standalone Windows executable tree
    dist/PLCMonitor-<version>.msi   – Windows MSI installer (run bdist_msi)

Quick start
~~~~~~~~~~~
Install build dependencies::

    pip install cx_Freeze pyads PyQt6

Build the executable::

    python setup.py build

Build the Windows MSI installer::

    python setup.py bdist_msi

The resulting MSI in ``dist/`` can be distributed to end-users who do not
have Python installed at all.

Environment notes
~~~~~~~~~~~~~~~~~
* cx_Freeze 7.x is required for Python 3.11+ and PyQt6 support.
* Run from within an activated virtual environment that has all runtime
  dependencies installed.
* The PyQt6 Qt DLLs and plugins are automatically detected by cx_Freeze;
  the ``packages`` list ensures their parent packages are included.
"""

from __future__ import annotations

import sys
from pathlib import Path

from cx_Freeze import Executable, setup

# ---------------------------------------------------------------------------
# Project metadata
# ---------------------------------------------------------------------------
APP_NAME = "PLCMonitor"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "TwinCAT 3 PLC ADS Monitor – PyQt6 GUI"
APP_AUTHOR = "TwinCAT Tools"
APP_UPGRADE_CODE = "{A7B3C421-0D8E-4B1A-9F2E-3E8D7C542190}"   # stable GUID for MSI upgrades
MAIN_SCRIPT = "app.py"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
SRC_DIR = HERE / "src"
ADS_BACKEND_DIR = HERE.parent / "plc_ads_project"
RESOURCES_DIR = HERE / "resources"
ADS_CONFIG_DIR = ADS_BACKEND_DIR / "config"

# ---------------------------------------------------------------------------
# cx_Freeze build options
# ---------------------------------------------------------------------------

#: Python packages that must be explicitly included (cx_Freeze may not
#: detect them through static import analysis when they are imported
#: dynamically or inside try/except blocks).
PACKAGES: list[str] = [
    # GUI
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    # PLC backend
    "pyads",
    "ctypes",
    # Standard library modules that cx_Freeze sometimes misses
    "xml",
    "xml.etree",
    "xml.etree.ElementTree",
    "threading",
    "queue",
    "logging",
    "logging.handlers",
    "dataclasses",
    "pathlib",
    "json",
    "datetime",
    "typing",
    # Application packages
    "plc_gui",
    "plc_gui.models",
    "plc_gui.views",
    "plc_gui.controllers",
    "plc_gui.workers",
    "plc_gui.utils",
    # ADS backend packages (included from sibling project)
    "config",
    "core",
    "models",
    "services",
    "utils",
]

#: Modules to explicitly exclude to reduce bundle size.
EXCLUDES: list[str] = [
    "tkinter",
    "unittest",
    "email",
    "html",
    "http",
    "urllib",
    "xmlrpc",
    "distutils",
    "setuptools",
    "pkg_resources",
    "pydoc",
    "doctest",
    "difflib",
    "ftplib",
    "imaplib",
    "mailbox",
    "mimetypes",
    "smtplib",
    "poplib",
    "telnetlib",
    "nntplib",
    "imghdr",
    "sndhdr",
    "ossaudiodev",
    "sunau",
    "wave",
    "asyncio",
    "concurrent",
    "multiprocessing",
    "sqlite3",
]

#: Files and directories to copy into the build tree as-is.
#: Each entry is (source_path, destination_relative_to_build_dir).
INCLUDE_FILES: list[tuple[str, str]] = [
    # Application resources
    (str(RESOURCES_DIR / "styles" / "dark.qss"),  "resources/styles/dark.qss"),
    (str(RESOURCES_DIR / "styles" / "light.qss"), "resources/styles/light.qss"),
    # Default PLC config so users have a starting-point template
    (str(ADS_CONFIG_DIR / "plc_config.xml"), "config/plc_config.xml"),
]

# Add icons directory if it exists.
icons_dir = RESOURCES_DIR / "icons"
if icons_dir.exists():
    # Include all icon files if they exist
    for icon_file in icons_dir.glob("*.ico"):
        INCLUDE_FILES.append((str(icon_file), f"resources/icons/{icon_file.name}"))
    for icon_file in icons_dir.glob("*.png"):
        INCLUDE_FILES.append((str(icon_file), f"resources/icons/{icon_file.name}"))
    for icon_file in icons_dir.glob("*.svg"):
        INCLUDE_FILES.append((str(icon_file), f"resources/icons/{icon_file.name}"))

BUILD_OPTIONS: dict = {
    # sys.path additions for dynamic imports from the sibling ADS project.
    "path": sys.path + [str(SRC_DIR), str(ADS_BACKEND_DIR)],
    "packages": PACKAGES,
    "excludes": EXCLUDES,
    "include_files": INCLUDE_FILES,
    # Keep the build tree lean.
    "optimize": 1,
    "include_msvcr": True,    # bundle MSVC runtime DLLs (Windows)
    "zip_include_packages": [
        # Zip these to reduce file count; PyQt6 DLLs must NOT be zipped.
        "plc_gui",
        "config",
        "core",
        "models",
        "services",
        "utils",
        "pyads",
    ],
    "zip_exclude_packages": ["*"],   # everything else stays as loose files
}

# ---------------------------------------------------------------------------
# Executable definition
# ---------------------------------------------------------------------------
# cx_Freeze 7.x uses "gui" / "console" instead of the legacy "Win32GUI" / "Win32Console".
BASE = "gui" if sys.platform == "win32" else None   # suppress console window

# Check if app icon exists
app_icon_path = RESOURCES_DIR / "icons" / "app.ico"
app_icon = str(app_icon_path) if app_icon_path.exists() else None

EXECUTABLES: list[Executable] = [
    Executable(
        script=MAIN_SCRIPT,
        base=BASE,
        target_name=f"{APP_NAME}.exe",
        icon=app_icon,  # Uses app.ico if it exists, otherwise default icon
        copyright=f"Copyright © 2026 {APP_AUTHOR}",
        shortcut_name=APP_NAME,
        shortcut_dir="DesktopFolder",   # create desktop shortcut
    )
]

# ---------------------------------------------------------------------------
# MSI-specific options
# ---------------------------------------------------------------------------
BDIST_MSI_OPTIONS: dict = {
    "upgrade_code": APP_UPGRADE_CODE,
    "add_to_path": False,
    "initial_target_dir": rf"[ProgramFilesFolder]\{APP_AUTHOR}\{APP_NAME}",
    "all_users": True,
    # Shortcuts
    "data": {
        "Shortcut": [
            # Desktop shortcut
            (
                "DesktopShortcut",            # shortcut key
                "DesktopFolder",              # directory
                APP_NAME,                     # name
                "TARGETDIR",                  # component
                f"[TARGETDIR]{APP_NAME}.exe", # target
                None, None, None, None, None, None, "TARGETDIR",
            ),
            # Start Menu shortcut
            (
                "StartMenuShortcut",
                "StartMenuFolder",
                APP_NAME,
                "TARGETDIR",
                f"[TARGETDIR]{APP_NAME}.exe",
                None, None, None, None, None, None, "TARGETDIR",
            ),
        ]
    },
}

# ---------------------------------------------------------------------------
# setup() call
# ---------------------------------------------------------------------------
setup(
    name=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    author=APP_AUTHOR,
    options={
        "build_exe": BUILD_OPTIONS,
        "bdist_msi": BDIST_MSI_OPTIONS,
    },
    executables=EXECUTABLES,
)
