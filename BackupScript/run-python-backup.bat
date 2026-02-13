@echo off
REM Run Python Backup Script
REM This batch file runs the Python backup utility

setlocal

echo.
echo ?????????????????????????????????????????????????????????????
echo ?                                                           ?
echo ?           PYTHON BACKUP UTILITY - LAUNCHER                ?
echo ?                                                           ?
echo ?????????????????????????????????????????????????????????????
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python 3.7 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Check if config.ini exists
if not exist "config.ini" (
    echo [ERROR] config.ini not found!
    echo.
    echo Please create a config.ini file with the following format:
    echo.
    echo [Backup]
    echo source_folder = C:\YourSourceFolder
    echo destination_folder = D:\YourBackupFolder
    echo.
    pause
    exit /b 1
)

REM Check if backup.py exists
if not exist "backup.py" (
    echo [ERROR] backup.py not found!
    pause
    exit /b 1
)

REM Display Python version
echo [INFO] Python version:
python --version
echo.

REM Run the backup script
echo [INFO] Starting backup...
echo.
python backup.py

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Backup completed successfully!
) else (
    echo.
    echo [ERROR] Backup failed with errors.
)

echo.
pause
