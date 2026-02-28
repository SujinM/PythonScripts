@echo off
REM Installation script for Windows

echo =====================================
echo Fingerprint R307 Sensor Installation
echo =====================================
echo.

REM Check Python
echo Checking Python installation...
python --version
if errorlevel 1 (
    echo Python not found! Please install Python 3.7 or higher.
    pause
    exit /b 1
)

REM Check pip
echo.
echo Checking pip...
python -m pip --version
if errorlevel 1 (
    echo pip not found! Installing...
    python -m ensurepip --upgrade
)

REM Install dependencies
echo.
echo Installing dependencies...
python -m pip install -r requirements.txt

REM Create config directory
echo.
echo Setting up configuration...
if not exist "%USERPROFILE%\.fingerprint_config.ini" (
    copy config\config.ini.template "%USERPROFILE%\.fingerprint_config.ini"
    echo Configuration template created
) else (
    echo Configuration file already exists
)

REM Install package
echo.
echo Installing package...
python -m pip install -e .

echo.
echo =====================================
echo Installation completed!
echo =====================================
echo.
echo Next steps:
echo 1. Connect your R307 fingerprint sensor via USB-Serial adapter
echo 2. Identify the COM port in Device Manager
echo 3. Update sensor port in code if needed (default: COM3)
echo 4. Run 'fingerprint-admin' to manage users
echo 5. Run 'fingerprint-reader' for verification
echo.
echo For more information, see docs\INSTALLATION.md
echo.
pause
