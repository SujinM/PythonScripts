@echo off
REM Setup script for Folder Encryptor (Windows Batch version)
REM Run this to set up the development environment

setlocal enabledelayedexpansion

REM Change to project root
cd /d "%~dp0.."

echo.
echo ==================================
echo  Folder Encryptor - Setup Script
echo ==================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo    Found Python %PYTHON_VERSION%

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

REM Install dependencies
echo.
echo Installing production dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Install development dependencies (optional)
set /p INSTALL_DEV="Install development dependencies? (y/N): "
if /i "%INSTALL_DEV%"=="y" (
    echo Installing development dependencies...
    pip install -r requirements-dev.txt
    echo Development dependencies installed
)

REM Install Argon2 (optional)
set /p INSTALL_ARGON2="Install Argon2 support? (y/N): "
if /i "%INSTALL_ARGON2%"=="y" (
    echo Installing argon2-cffi...
    pip install argon2-cffi
    echo Argon2 support installed
)

REM Verify installation
echo.
echo Verifying installation...
python -c "import cryptography; print('cryptography:', cryptography.__version__)"
python -c "import tqdm; print('tqdm:', tqdm.__version__)"

REM Test import
echo.
echo Testing application import...
python -c "from app.cli.main import main; print('Application imports successfully')"

REM Run tests (optional)
set /p RUN_TESTS="Run tests to verify installation? (y/N): "
if /i "%RUN_TESTS%"=="y" (
    echo Running tests...
    pytest tests/ -v --tb=short
    if errorlevel 1 (
        echo Some tests failed ^(may be expected on first run^)
    )
)

echo.
echo ==================================
echo Setup completed successfully!
echo ==================================
echo.
echo Next steps:
echo   1. Activate the virtual environment:
echo      venv\Scripts\activate.bat
echo.
echo   2. Try the CLI:
echo      python -m app.cli.main --help
echo.
echo   3. Read the documentation:
echo      - README.md (full documentation)
echo      - QUICKSTART.md (quick start guide)
echo      - PROJECT_SUMMARY.md (project overview)
echo.

pause
