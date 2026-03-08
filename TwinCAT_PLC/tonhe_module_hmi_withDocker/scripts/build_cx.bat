@echo off
REM =============================================================================
REM  build_cx.bat  –  Build ToneHMI Windows distribution with cx_Freeze
REM
REM  Usage (run from project root or scripts\):
REM    scripts\build_cx.bat              – build exe tree
REM    scripts\build_cx.bat msi          – build exe tree + MSI installer
REM    scripts\build_cx.bat clean        – remove build\ and dist\ first
REM    scripts\build_cx.bat clean msi    – clean then build MSI
REM
REM  Output:
REM    build\exe.win-amd64-<ver>\ToneHMI.exe   (standalone folder)
REM    dist\ToneHMI-1.0.0-win64.msi            (if msi flag given)
REM =============================================================================

setlocal enabledelayedexpansion

echo.
echo =============================================================================
echo   TONHE Module HMI  ^|  Windows Build  ^(cx_Freeze^)
echo =============================================================================
echo.

REM ── Navigate to project root if invoked from scripts\ ─────────────────────
if exist "..\app.py" (
    pushd ..
) else if not exist "app.py" (
    echo [ERROR] Run this script from the project root or the scripts\ folder.
    exit /b 1
)
set "PROJECT_ROOT=%CD%"
echo [INFO] Project root : %PROJECT_ROOT%
echo.

REM ── Parse arguments ───────────────────────────────────────────────────────
set "DO_CLEAN=0"
set "DO_MSI=0"
for %%A in (%*) do (
    if /I "%%A"=="clean" set "DO_CLEAN=1"
    if /I "%%A"=="msi"   set "DO_MSI=1"
)

REM ── Optional clean ────────────────────────────────────────────────────────
if "%DO_CLEAN%"=="1" (
    echo [STEP] Cleaning previous build artefacts...
    if exist "build" rd /s /q "build"
    if exist "dist"  rd /s /q "dist"
    echo [OK]   Clean done.
    echo.
)

REM ── Check Python ──────────────────────────────────────────────────────────
echo [STEP 1/4] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Activate your .venv first:
    echo         ^& .venv\Scripts\Activate.ps1
    exit /b 1
)
for /f "tokens=*" %%V in ('python --version 2^>^&1') do echo [OK]   %%V

REM ── Check / install cx_Freeze ─────────────────────────────────────────────
echo.
echo [STEP 2/4] Checking cx_Freeze...
python -m cx_Freeze --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] cx_Freeze not found. Installing...
    pip install "cx_Freeze>=7.0"
    if errorlevel 1 (
        echo [ERROR] Failed to install cx_Freeze.
        exit /b 1
    )
)
for /f "tokens=*" %%V in ('python -m cx_Freeze --version 2^>^&1') do echo [OK]   cx_Freeze %%V

REM ── Check plc_ads_project ─────────────────────────────────────────────────
echo.
echo [STEP 3/4] Checking sibling plc_ads_project...
if not exist "..\plc_ads_project\config\config_loader.py" (
    echo [ERROR] plc_ads_project not found at ..\plc_ads_project
    echo         Ensure the folder exists next to tonhe_module_hmi\
    exit /b 1
)
echo [OK]   plc_ads_project found.

REM ── Run cx_Freeze ─────────────────────────────────────────────────────────
echo.
if "%DO_MSI%"=="1" (
    echo [STEP 4/4] Building exe + MSI installer...
    python setup.py build bdist_msi
) else (
    echo [STEP 4/4] Building exe tree...
    python setup.py build
)

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check the output above.
    exit /b 1
)

REM ── Report ────────────────────────────────────────────────────────────────
echo.
echo =============================================================================
echo   Build complete!
echo.
for /d %%D in ("build\exe.win-amd64-*") do (
    echo   Folder     : %PROJECT_ROOT%\%%D\
    echo   Executable : %PROJECT_ROOT%\%%D\ToneHMI.exe
)
if "%DO_MSI%"=="1" (
    echo   Installer  : %PROJECT_ROOT%\dist\
)
echo.
echo   To run:  build\exe.win-amd64-3.x\ToneHMI.exe
echo =============================================================================
echo.

popd
endlocal
exit /b 0
