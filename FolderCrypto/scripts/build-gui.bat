@echo off
REM Build script for FolderCrypto GUI executable

setlocal enabledelayedexpansion

REM Change to project root
cd /d "%~dp0.."

echo.
echo ========================================
echo    FolderCrypto GUI - Build Script
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo WARNING: Virtual environment not found
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade PyInstaller
echo Installing PyInstaller...
pip install pyinstaller --upgrade

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Clean previous builds
echo Cleaning previous GUI builds...
if exist "build\FolderCrypto-GUI" rmdir /s /q "build\FolderCrypto-GUI"
if exist "dist\FolderCrypto-GUI.exe" del /q "dist\FolderCrypto-GUI.exe"

REM Check if .spec file exists
if not exist "folder-crypto-gui.spec" (
    echo.
    echo ERROR: folder-crypto-gui.spec not found!
    echo Please ensure the spec file exists in the project root.
    pause
    exit /b 1
)

REM Run PyInstaller
echo.
echo Building GUI executable with PyInstaller...
echo This may take a few minutes...
echo.
pyinstaller folder-crypto-gui.spec --clean

REM Check if build was successful
if exist "dist\FolderCrypto-GUI.exe" (
    echo.
    echo ========================================
    echo    Build Successful!
    echo ========================================
    echo.
    
    REM Display build information
    echo Build Information:
    echo    Output directory: dist\
    
    for %%A in ("dist\FolderCrypto-GUI.exe") do set SIZE=%%~zA
    set /a SIZE_MB=!SIZE! / 1048576
    echo    Executable: dist\FolderCrypto-GUI.exe
    echo    Size: ~!SIZE_MB! MB
    
    echo.
    echo Usage:
    echo    Double-click: dist\FolderCrypto-GUI.exe
    echo    Or run from command line: .\dist\FolderCrypto-GUI.exe
    
    echo.
    echo The GUI application is a standalone executable
    echo No Python installation required on target machines
    
    echo.
    echo ========================================
    echo    Build Complete!
    echo ========================================
    echo.
    
    REM Offer to run the executable
    set /p RUN_GUI="Run the GUI now? (y/N): "
    if /i "!RUN_GUI!"=="y" (
        echo.
        echo Launching FolderCrypto GUI...
        start "" "dist\FolderCrypto-GUI.exe"
    )
    
) else (
    echo.
    echo ========================================
    echo    Build Failed!
    echo ========================================
    echo.
    echo Check the output above for errors.
    echo.
    echo Common issues:
    echo  - Missing dependencies (run: pip install -r requirements.txt)
    echo  - PyQt6 not installed (run: pip install PyQt6)
    echo  - Antivirus blocking PyInstaller
    echo.
    pause
    exit /b 1
)

echo.
pause
