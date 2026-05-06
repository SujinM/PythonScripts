@echo off
setlocal EnableDelayedExpansion
title Sujin's Investment — Release Builder

:: ============================================================================
::  build-release.bat
::  Builds SujinsInvestment.exe and (optionally) the Windows installer.
::
::  Usage:
::    build-release.bat            — build EXE only
::    build-release.bat /installer — build EXE + Inno Setup installer
:: ============================================================================

set "ROOT=%~dp0"
set "VERSION=1.0.0"
set "PUBLISH_DIR=%ROOT%bin\publish\win-x64"
set "INSTALLER_DIR=%ROOT%installer"
set "INSTALLER_OUTPUT=%INSTALLER_DIR%\Output"

echo.
echo  =====================================================
echo   Sujin's Investment  ^|  Release Build v%VERSION%
echo  =====================================================
echo.

:: ── Step 1: Regenerate icon ───────────────────────────────────────────────
echo [1/3] Generating icon...
set "PYTHON="
for %%P in (
    "C:\CT\GITHUBREPO\PythonScripts\.venv\Scripts\python.exe"
    python
) do (
    if not defined PYTHON (
        "%%~P" --version >nul 2>&1 && set "PYTHON=%%~P"
    )
)
if defined PYTHON (
    "%PYTHON%" "%ROOT%Assets\create_icon.py"
    if errorlevel 1 (
        echo   [WARN] Icon generation failed — using existing Assets\app.ico
    ) else (
        echo   Icon generated OK.
    )
) else (
    echo   [WARN] Python not found — using existing Assets\app.ico
)

:: ── Step 2: dotnet publish (self-contained single-file) ───────────────────
echo.
echo [2/3] Publishing SujinsInvestment.exe (win-x64, self-contained)...
dotnet publish "%ROOT%ClientConsolApp.csproj" ^
    -p:PublishProfile=win-x64 ^
    --nologo

if errorlevel 1 (
    echo.
    echo  [ERROR] dotnet publish failed. Check errors above.
    goto :end_fail
)

if not exist "%PUBLISH_DIR%\SujinsInvestment.exe" (
    echo  [ERROR] Expected EXE not found: %PUBLISH_DIR%\SujinsInvestment.exe
    goto :end_fail
)

echo.
echo   Published to: %PUBLISH_DIR%
for %%F in ("%PUBLISH_DIR%\SujinsInvestment.exe") do (
    set /a SIZE_MB=%%~zF / 1048576
    echo   EXE size: !SIZE_MB! MB
)

:: ── Step 3: Inno Setup installer (optional) ───────────────────────────────
if /I not "%~1"=="/installer" goto :skip_installer

echo.
echo [3/3] Building Windows installer with Inno Setup...

:: Locate iscc.exe (Inno Setup compiler)
set "ISCC="
for %%P in (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) do (
    if not defined ISCC (
        if exist "%%~P" set "ISCC=%%~P"
    )
)

if not defined ISCC (
    echo.
    echo   [WARN] Inno Setup 6 not found. Download from:
    echo          https://jrsoftware.org/isdl.php
    echo   The EXE was still published to:
    echo   %PUBLISH_DIR%\SujinsInvestment.exe
    goto :skip_installer
)

if not exist "%INSTALLER_OUTPUT%" mkdir "%INSTALLER_OUTPUT%"

"%ISCC%" "%INSTALLER_DIR%\SujinsInvestment.iss" /Q
if errorlevel 1 (
    echo   [ERROR] Inno Setup compilation failed.
    goto :end_fail
)

echo.
echo   Installer: %INSTALLER_OUTPUT%\SujinsInvestment-Setup-%VERSION%.exe
:skip_installer

:: ── Done ──────────────────────────────────────────────────────────────────
echo.
echo  =====================================================
echo   Build complete!
echo.
echo   Standalone EXE:
echo     %PUBLISH_DIR%\SujinsInvestment.exe
if /I "%~1"=="/installer" (
    echo.
    echo   Installer (if Inno Setup was found):
    echo     %INSTALLER_OUTPUT%\SujinsInvestment-Setup-%VERSION%.exe
)
echo  =====================================================
echo.
goto :end_ok

:end_fail
echo.
echo  Build FAILED.
endlocal
exit /b 1

:end_ok
endlocal
exit /b 0
