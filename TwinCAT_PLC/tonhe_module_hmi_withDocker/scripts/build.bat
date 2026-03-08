@echo off
REM =============================================================================
REM  build.bat  –  Build ToneHMI Windows distribution with PyInstaller
REM
REM  Usage:
REM    scripts\build.bat            (run from project root or scripts\)
REM    scripts\build.bat clean      (remove dist\ and build\ first)
REM
REM  Output:  dist\ToneHMI\ToneHMI.exe  (one-folder distribution)
REM =============================================================================

setlocal enabledelayedexpansion

echo.
echo =============================================================================
echo   TONHE Module HMI  ^|  Windows Build
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

REM ── Optional clean ────────────────────────────────────────────────────────
if /I "%~1"=="clean" (
    echo [STEP] Cleaning previous build artefacts...
    if exist "dist\ToneHMI"  rd /s /q "dist\ToneHMI"
    if exist "build\ToneHMI" rd /s /q "build\ToneHMI"
    if exist "_rthook_plc_ads.py" del /q "_rthook_plc_ads.py"
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

REM ── Check / install PyInstaller ────────────────────────────────────────────
echo.
echo [STEP 2/4] Checking PyInstaller...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller.
        exit /b 1
    )
)
for /f "tokens=*" %%V in ('python -m PyInstaller --version 2^>^&1') do echo [OK]   PyInstaller %%V

REM ── Check plc_ads_project exists ─────────────────────────────────────────
echo.
echo [STEP 3/4] Checking sibling plc_ads_project...
if not exist "..\plc_ads_project\config\config_loader.py" (
    echo [ERROR] plc_ads_project not found at ..\plc_ads_project
    echo         Ensure the folder exists next to tonhe_module_hmi\
    exit /b 1
)
echo [OK]   plc_ads_project found.

REM ── Run PyInstaller ───────────────────────────────────────────────────────
echo.
echo [STEP 4/4] Running PyInstaller...
echo.

python -m PyInstaller tonehmi.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed. Check the output above.
    exit /b 1
)

REM ── Tidy up runtime hook temp file ───────────────────────────────────────
if exist "_rthook_plc_ads.py" del /q "_rthook_plc_ads.py"

REM ── Report ────────────────────────────────────────────────────────────────
echo.
echo =============================================================================
echo   Build complete!
echo.
echo   Executable : %PROJECT_ROOT%\dist\ToneHMI\ToneHMI.exe
echo   Folder     : %PROJECT_ROOT%\dist\ToneHMI\
echo.
echo   To run:  dist\ToneHMI\ToneHMI.exe
echo =============================================================================
echo.

popd
endlocal
exit /b 0
