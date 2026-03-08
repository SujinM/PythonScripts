"""
setup.py
--------
cx_Freeze build script for TONHE Module HMI.

Produces:
    build/exe.win-amd64-<py_ver>/   – standalone Windows executable tree
    dist/ToneHMI-<version>.msi      – Windows MSI installer (run bdist_msi)

Quick start
~~~~~~~~~~~
Install build dependencies::

    pip install cx_Freeze pyads PyQt6 pyqtgraph

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
* Themes (QSS files) are bundled into resources/styles/ inside the build
  tree; the application reads them via Path(sys.executable).parent at runtime.
"""

from __future__ import annotations

import sys
from pathlib import Path

from cx_Freeze import Executable, setup

# ---------------------------------------------------------------------------
# Project metadata
# ---------------------------------------------------------------------------
APP_NAME        = "ToneHMI"
APP_DISPLAY     = "TONHE Module HMI"
APP_VERSION     = "1.0.0"
APP_DESCRIPTION = "TONHE Charging Module HMI – PyQt6 GUI"
APP_AUTHOR      = "TwinCAT Tools"
APP_UPGRADE_CODE = "{B9D2A573-1F4C-4E2B-8A3D-7F9C0D863412}"   # stable GUID for MSI upgrades
MAIN_SCRIPT     = "app.py"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE            = Path(__file__).resolve().parent           # tonhe_module_hmi/
SRC_DIR         = HERE / "src"                              # …/src
ADS_BACKEND_DIR = HERE.parent / "plc_ads_project"           # sibling ADS backend
RESOURCES_DIR   = HERE / "resources"
CONFIG_DIR      = HERE / "config"
STYLES_DIR      = RESOURCES_DIR / "styles"
ICONS_DIR       = RESOURCES_DIR / "icons"

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
    # Graph widget + required numeric backend
    "pyqtgraph",
    "numpy",
    "numpy.core",
    "numpy.lib",
    "numpy.linalg",
    "numpy.fft",
    "numpy.random",
    # PLC ADS backend
    "pyads",
    # Standard library modules that cx_Freeze sometimes misses
    "ctypes",
    "ctypes.wintypes",
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
    "collections",
    # Application package
    "tone_hmi",
    "tone_hmi.models",
    "tone_hmi.views",
    "tone_hmi.controllers",
    "tone_hmi.workers",
    "tone_hmi.utils",
    # ADS backend packages loaded dynamically via sys.path at runtime
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
    "distutils",
    "setuptools",
    "pkg_resources",
    "sqlite3",
    "matplotlib",
    "scipy",
    "pandas",
    "PIL",
    "cv2",
    "IPython",
    "notebook",
]

#: Files and directories to copy into the build tree as-is.
#: Each entry is (source_path_or_dir, destination_relative_to_build_dir).
#:
#: IMPORTANT – this is how QSS themes reach the build folder.
#: The frozen app resolves styles via:
#:   Path(sys.executable).parent / "resources" / "styles" / "dark.qss"
#: so the destination MUST match that relative path.
INCLUDE_FILES: list[tuple[str, str]] = [
    # ── QSS theme files (must be loose files on disk for runtime read_text) ──
    (str(STYLES_DIR / "dark.qss"),  "resources/styles/dark.qss"),
    (str(STYLES_DIR / "light.qss"), "resources/styles/light.qss"),
    # ── Default config so users have a starting-point template ────────────────
    (str(CONFIG_DIR / "tone_config.xml"), "config/tone_config.xml"),
]

# Add icon files if they exist
for ext in ("*.ico", "*.png", "*.svg"):
    for icon_file in ICONS_DIR.glob(ext):
        INCLUDE_FILES.append((str(icon_file), f"resources/icons/{icon_file.name}"))

# pyqtgraph ships color-map data files (.csv) that are NOT Python modules.
# Include the whole colors/maps sub-directory so gradient lookups work.
try:
    import pyqtgraph as _pg
    _pg_root = Path(_pg.__file__).parent
    _maps_dir = _pg_root / "colors" / "maps"
    if _maps_dir.exists():
        for _f in _maps_dir.iterdir():
            if _f.is_file():
                INCLUDE_FILES.append((str(_f), f"pyqtgraph/colors/maps/{_f.name}"))
except ImportError:
    pass


#: These generate "Missing dependencies" warnings from cx_Freeze because PyQt6
#: ships the full Qt installation (including QML, 3D, SQL drivers) even though
#: this app only uses QtWidgets.  They are either:
#:   • Qt modules the app never loads (QML / Quick / 3D / SQL)
#:   • Database driver DLLs (PostgreSQL, Oracle, Firebird) – not used
#:   • Windows OS API forwarder DLLs – always present on Windows itself
#: Listing them here suppresses the warnings without affecting functionality.
BIN_EXCLUDES: list[str] = [
    # Qt QML / Quick / 3D – not used by a Widgets-only app
    "Qt63DAnimation.dll", "Qt63DCore.dll", "Qt63DExtras.dll",
    "Qt63DInput.dll", "Qt63DLogic.dll", "Qt63DQuick.dll",
    "Qt63DQuickAnimation.dll", "Qt63DQuickExtras.dll",
    "Qt63DQuickInput.dll", "Qt63DQuickRender.dll",
    "Qt63DQuickScene2D.dll", "Qt63DQuickScene3D.dll",
    "Qt63DRender.dll",
    "Qt6Qml.dll", "Qt6QmlCompiler.dll", "Qt6QmlCore.dll",
    "Qt6QmlLocalStorage.dll", "Qt6QmlModels.dll",
    "Qt6QmlNetwork.dll", "Qt6QmlXmlListModel.dll",
    "Qt6QmlWorkerScript.dll",
    "Qt6Quick.dll", "Qt6Quick3D.dll", "Qt6Quick3DAssetImport.dll",
    "Qt6Quick3DAssetUtils.dll", "Qt6Quick3DEffects.dll",
    "Qt6Quick3DHelpersImpl.dll", "Qt6Quick3DParticleEffects.dll",
    "Qt6Quick3DParticles.dll", "Qt6Quick3DRuntimeRender.dll",
    "Qt6Quick3DUtils.dll",
    "Qt6QuickControls2.dll", "Qt6QuickControls2Basic.dll",
    "Qt6QuickControls2BasicStyleImpl.dll",
    "Qt6QuickControls2FluentWinUI3StyleImpl.dll",
    "Qt6QuickControls2Fusion.dll", "Qt6QuickControls2FusionStyleImpl.dll",
    "Qt6QuickControls2Imagine.dll", "Qt6QuickControls2ImagineStyleImpl.dll",
    "Qt6QuickControls2Impl.dll", "Qt6QuickControls2Material.dll",
    "Qt6QuickControls2MaterialStyleImpl.dll",
    "Qt6QuickControls2Universal.dll", "Qt6QuickControls2UniversalStyleImpl.dll",
    "Qt6QuickControls2Windows.dll", "Qt6QuickControls2WindowsStyleImpl.dll",
    "Qt6QuickDialogs2.dll", "Qt6QuickDialogs2QuickImpl.dll",
    "Qt6QuickDialogs2Utils.dll",
    "Qt6QuickEffects.dll", "Qt6QuickLayouts.dll",
    "Qt6QuickParticles.dll", "Qt6QuickShapes.dll",
    "Qt6QuickShapesDesignHelpers.dll",
    "Qt6QuickTemplates2.dll", "Qt6QuickTest.dll",
    "Qt6QuickTimeline.dll", "Qt6QuickVector.dll",
    "Qt6QuickVectorImageHelpers.dll",
    # Qt SQL database drivers – not used
    "Qt6Sql.dll",
    "LIBPQ.dll",    # PostgreSQL
    "OCI.dll",      # Oracle
    "fbclient.dll", # Firebird
    # Windows OS API forwarder DLLs (always present on Windows; not standalone)
    "WINSPOOL.DRV",
    "MIMAPI64.dll",
    "api-ms-win-core-com-l1-1-0.dll",
    "api-ms-win-core-heap-l2-1-0.dll",
    "api-ms-win-core-libraryloader-l1-2-0.dll",
    "api-ms-win-core-libraryloader-l1-2-1.dll",
    "api-ms-win-core-path-l1-1-0.dll",
    "api-ms-win-core-winrt-l1-1-0.dll",
    "api-ms-win-core-winrt-string-l1-1-0.dll",
    "api-ms-win-shcore-scaling-l1-1-1.dll",
]

BUILD_OPTIONS: dict = {
    # sys.path additions so cx_Freeze can locate all source packages.
    "path": sys.path + [str(SRC_DIR), str(ADS_BACKEND_DIR)],
    "packages": PACKAGES,
    "excludes": EXCLUDES,
    "include_files": INCLUDE_FILES,
    "bin_excludes": BIN_EXCLUDES,
    "optimize": 1,
    "include_msvcr": True,   # bundle MSVC runtime DLLs
    # ── Zip strategy ──────────────────────────────────────────────────────────
    # Pure-Python packages are zipped to reduce file count.
    # PyQt6 DLLs and pyqtgraph (has C extensions + data files) stay loose.
    "zip_include_packages": [
        "tone_hmi",
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
BASE = "gui" if sys.platform == "win32" else None   # suppress console window

app_icon_path = ICONS_DIR / "app.ico"
app_icon = str(app_icon_path) if app_icon_path.exists() else None

EXECUTABLES: list[Executable] = [
    Executable(
        script=MAIN_SCRIPT,
        base=BASE,
        target_name=f"{APP_NAME}.exe",
        icon=app_icon,
        copyright=f"Copyright © 2026 {APP_AUTHOR}",
        shortcut_name=APP_DISPLAY,
        shortcut_dir="DesktopFolder",
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
    "data": {
        "Shortcut": [
            # Desktop shortcut
            (
                "DesktopShortcut",
                "DesktopFolder",
                APP_DISPLAY,
                "TARGETDIR",
                f"[TARGETDIR]{APP_NAME}.exe",
                None, None, None, None, None, None, "TARGETDIR",
            ),
            # Start Menu shortcut
            (
                "StartMenuShortcut",
                "StartMenuFolder",
                APP_DISPLAY,
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
    name=APP_DISPLAY,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    author=APP_AUTHOR,
    options={
        "build_exe": BUILD_OPTIONS,
        "bdist_msi": BDIST_MSI_OPTIONS,
    },
    executables=EXECUTABLES,
)
