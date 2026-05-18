@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: run.bat — InvestCalc launcher (Windows)
:: ─────────────────────────────────────────────────────────────────────────────
setlocal EnableDelayedExpansion
title InvestCalc — Stock Market Calculator
set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"

echo.
echo  ============================================
echo    InvestCalc -- Stock Market Calculator
echo  ============================================
echo.

:: ── 1. Find Python ─────────────────────────────────────────────────────────
set "PYTHON="
for %%C in (python3.12 python3.11 python3 python py) do (
    where %%C >nul 2>&1
    if !errorlevel! == 0 (
        for /f "tokens=2 delims= " %%V in ('%%C --version 2^>^&1') do (
            set "PY_VER=%%V"
        )
        set "PYTHON=%%C"
        goto :found_python
    )
)
echo  [ERROR] Python 3.11+ not found. Please install from https://python.org
pause
exit /b 1

:found_python
echo  Python: !PY_VER! (!PYTHON!)

:: ── 2. Create virtual environment ──────────────────────────────────────────
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo  Creating virtual environment...
    !PYTHON! -m venv "%VENV_DIR%"
    if !errorlevel! neq 0 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  venv created.
)

:: ── 3. Activate ────────────────────────────────────────────────────────────
call "%VENV_DIR%\Scripts\activate.bat"

:: ── 4. Install package (first run) ─────────────────────────────────────────
python -c "import investcalc" >nul 2>&1
if !errorlevel! neq 0 (
    echo  Installing InvestCalc...
    pip install --quiet -e "%SCRIPT_DIR%"
    if !errorlevel! neq 0 (
        echo  [ERROR] Installation failed.
        pause
        exit /b 1
    )
    echo  Installation complete.
)

:: ── 5. Launch ───────────────────────────────────────────────────────────────
echo.
python -m investcalc
pause
