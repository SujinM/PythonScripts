@echo off
REM ============================================
REM Simple Build - Quick Executable Creation
REM Creates exe with icon only (no version info or signature)
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ============================================
echo    BACKUP UTILITY - SIMPLE BUILD
echo ============================================
echo.
echo This will create a basic executable with icon
echo No version information or digital signature
echo.
echo For complete build with metadata, use:
echo   .\build-complete.bat
echo.
echo ============================================
echo.

REM Navigate to project root if running from scripts folder
if exist "..\src\backup.py" (
    cd ..
)

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python 3.7 or higher from:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [INFO] Python version:
python --version
echo.

REM Check if PyInstaller is installed
echo [INFO] Checking PyInstaller...
python -m pip show pyinstaller >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] PyInstaller not found. Installing...
    python -m pip install pyinstaller
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install PyInstaller
        pause
        exit /b 1
    )
)
echo [SUCCESS] PyInstaller is available
echo.

REM Check if required files exist
echo [INFO] Checking required files...
if not exist "src\backup.py" (
    echo [ERROR] src\backup.py not found!
    pause
    exit /b 1
)
echo [OK] src\backup.py found

if not exist "assets\backup_icon.png" (
    echo [ERROR] assets\backup_icon.png not found!
    pause
    exit /b 1
)
echo [OK] assets\backup_icon.png found
echo.

REM Convert PNG to ICO
echo [INFO] Converting icon PNG to ICO format...
if exist "tools\png_to_ico.py" (
    python tools\png_to_ico.py
    if %ERRORLEVEL% NEQ 0 (
        echo [WARNING] Icon conversion failed
    )
) else (
    echo [WARNING] png_to_ico.py not found
)

if not exist "assets\backup_icon.ico" (
    echo [ERROR] assets\backup_icon.ico not found!
    pause
    exit /b 1
)
echo [OK] Icon ready
echo.

REM Clean previous build
echo [INFO] Cleaning previous builds...
if exist "build" (
    rmdir /s /q build >nul 2>nul
    echo [OK] Removed build folder
)
if exist "dist\backup.exe" (
    del /f /q dist\backup.exe >nul 2>nul
    echo [OK] Removed old exe
)
echo.

REM Build the EXE
echo ============================================
echo [INFO] Building executable...
echo ============================================
echo.
echo Command: PyInstaller --onefile --icon=assets\backup_icon.ico --name backup src\backup.py
echo.

python -m PyInstaller --onefile --icon=assets\backup_icon.ico --name backup src\backup.py

REM Check if build was successful
if %ERRORLEVEL% EQU 0 (
    if exist "dist\backup.exe" (
        echo.
        echo ============================================
        echo          BUILD COMPLETED SUCCESSFULLY!
        echo ============================================
        echo.
        
        REM Get file size
        for %%A in (dist\backup.exe) do set size=%%~zA
        set /a sizeMB=!size! / 1048576
        
        echo [SUCCESS] Executable created: dist\backup.exe
        echo [INFO] Size: !sizeMB! MB
        echo.
        echo [INFO] What's included:
        echo   +-- Icon: Embedded
        echo   +-- Version Info: Not included
        echo   +-- Digital Signature: Not included
        echo.
        echo [INFO] Next steps:
        echo   1. Test the exe: .\dist\backup.exe
        echo   2. For complete metadata, run: .\build-complete.bat
        echo.
        echo ============================================
        echo.
        
        pause
        exit /b 0
    )
)

echo.
echo ============================================
echo              BUILD FAILED!
echo ============================================
echo.
echo [ERROR] PyInstaller encountered an error
echo.
echo Troubleshooting:
echo   - Verify Python and PyInstaller are installed
echo   - Check if src\backup.py has no syntax errors
echo   - Try: pip install --upgrade pyinstaller
echo.
pause
exit /b 1
