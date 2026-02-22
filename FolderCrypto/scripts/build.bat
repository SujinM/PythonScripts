@echo off
REM Build script for Folder Encryptor executable (Windows Batch version)

setlocal enabledelayedexpansion

REM Change to project root
cd /d "%~dp0.."

echo.
echo ========================================
echo    Folder Encryptor - Build Script
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
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
del /q *.spec.backup 2>nul

REM Check if .spec file exists
if not exist "folder-encryptor.spec" (
    echo.
    echo ERROR: folder-encryptor.spec not found!
    echo Creating a basic spec file...
    
    REM Create a basic PyInstaller spec
    echo Running PyInstaller to generate spec...
    pyinstaller --name folder-encryptor --onefile --console app\__main__.py
    
    echo.
    echo Basic spec file created. You may want to customize it.
) else (
    REM Run PyInstaller
    echo.
    echo Building executable with PyInstaller...
    pyinstaller folder-encryptor.spec --clean
)

REM Check if build was successful
if exist "dist\folder-encryptor.exe" (
    echo.
    echo Build successful!
    echo.
    
    REM Display build information
    echo Build Information:
    echo    Output directory: dist\
    
    for %%A in ("dist\folder-encryptor.exe") do set SIZE=%%~zA
    set /a SIZE_MB=!SIZE! / 1048576
    echo    Executable: dist\folder-encryptor.exe
    echo    Size: !SIZE_MB! MB
    
    echo.
    echo Usage:
    echo    .\dist\folder-encryptor.exe --help
    echo    .\dist\folder-encryptor.exe encrypt -i ^<input^> -o ^<output^>
    echo    .\dist\folder-encryptor.exe decrypt -i ^<encrypted^> -o ^<output^>
    
    REM Test the executable
    echo.
    echo Testing executable...
    dist\folder-encryptor.exe --version 2>nul
    if errorlevel 1 (
        dist\folder-encryptor.exe --help
    )
    
    echo.
    echo Build complete!
    echo The executable is ready in the dist\ directory
    echo.
) else (
    echo.
    echo Build failed!
    echo Check the output above for errors
    echo.
    pause
    exit /b 1
)

REM Optional: Create distribution package
set /p CREATE_DIST="Create distribution package? (y/N): "
if /i "%CREATE_DIST%"=="y" (
    echo Creating distribution package...
    
    set DIST_NAME=folder-encryptor-v1.0.0-windows-x64
    set DIST_DIR=dist\!DIST_NAME!
    
    mkdir "!DIST_DIR!" 2>nul
    
    REM Copy executable
    if exist "dist\folder-encryptor.exe" (
        copy "dist\folder-encryptor.exe" "!DIST_DIR!\" >nul
    )
    
    REM Copy documentation
    if exist "README.md" copy "README.md" "!DIST_DIR!\" >nul
    if exist "LICENSE" copy "LICENSE" "!DIST_DIR!\" >nul
    if exist "config.ini.template" copy "config.ini.template" "!DIST_DIR!\" >nul
    
    REM Create ZIP archive
    echo Creating ZIP archive...
    powershell -Command "Compress-Archive -Path 'dist\!DIST_NAME!' -DestinationPath 'dist\!DIST_NAME!.zip' -Force" >nul 2>&1
    
    if exist "dist\!DIST_NAME!.zip" (
        echo Distribution package created: dist\!DIST_NAME!.zip
    ) else (
        echo WARNING: ZIP creation failed. Manual archive creation required.
    )
)

echo.
echo ========================================
echo    Build process completed!
echo ========================================
echo.

pause
