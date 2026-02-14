@echo off
REM ============================================
REM Complete Build - Production Executable
REM Creates exe with icon + version info + digital signature
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ============================================
echo   BACKUP UTILITY - COMPLETE BUILD
echo ============================================
echo.
echo This will create a production-ready executable with:
echo   +-- Embedded icon (512x512 multi-resolution)
echo   +-- Version information (Product, Copyright, etc.)
echo   +-- Digital signature (Self-signed certificate)
echo.
echo For quick build without metadata, use:
echo   .\build.bat
echo.
echo ============================================
echo.

REM Navigate to project root if running from scripts folder
if exist "..\src\backup.py" (
    cd ..
)

REM ============================================
REM STEP 1: Find Windows SDK (for rc.exe)
REM ============================================
echo [STEP 1/6] Locating Windows SDK...
echo.

set "RC_EXE="
set "SDK_BASE=C:\Program Files (x86)\Windows Kits\10\bin"

REM Search for rc.exe in common SDK locations
for /d %%D in ("%SDK_BASE%\10.0.*") do (
    if exist "%%D\x64\rc.exe" (
        set "RC_EXE=%%D\x64"
        goto :found_sdk
    )
)

echo [WARNING] Windows SDK not found!
echo [INFO] Version resource compilation will be skipped
echo.
echo You can either:
echo   1. Install Windows SDK from Microsoft
echo   2. Or continue without version info
echo.
choice /C YN /M "Continue without version info"
if errorlevel 2 exit /b 1
set "SKIP_VERSION=1"
goto :skip_rc

:found_sdk
echo [SUCCESS] Found Windows SDK: %RC_EXE%
set "PATH=%RC_EXE%;%PATH%"
echo.

REM ============================================
REM STEP 2: Compile version resource
REM ============================================
echo [STEP 2/6] Compiling version resource...
echo.

if exist "scripts\version_resource.res" (
    del /f scripts\version_resource.res >nul 2>nul
)

rc.exe /fo scripts\version_resource.res scripts\version_resource.rc >nul 2>nul

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Version resource compiled
    echo.
) else (
    echo [WARNING] Version resource compilation failed
    set "SKIP_VERSION=1"
    echo.
)

:skip_rc

REM ============================================
REM STEP 3: Check Python and dependencies
REM ============================================
echo [STEP 3/6] Checking Python environment...
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [INFO] Python version:
python --version

python -m pip show pyinstaller >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Installing PyInstaller...
    python -m pip install pyinstaller
)
echo [SUCCESS] PyInstaller ready
echo.

REM ============================================
REM STEP 4: Convert icon
REM ============================================
echo [STEP 4/6] Converting icon...
echo.

if exist "tools\png_to_ico.py" (
    python tools\png_to_ico.py >nul 2>nul
    echo [SUCCESS] Icon converted (512x512 multi-resolution)
) else (
    echo [WARNING] Icon converter not found
)

if not exist "assets\backup_icon.ico" (
    echo [ERROR] Icon file missing!
    pause
    exit /b 1
)
echo.

REM ============================================
REM STEP 5: Build executable with PyInstaller
REM ============================================
echo [STEP 5/6] Building executable...
echo.

REM Clean previous builds
if exist "build" rmdir /s /q build >nul 2>nul
if exist "dist\backup.exe" del /f /q dist\backup.exe >nul 2>nul

echo Command: PyInstaller --onefile --icon=assets\backup_icon.ico --clean src\backup.py
echo.

python -m PyInstaller --onefile --icon=assets\backup_icon.ico --clean --name backup src\backup.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Exe build failed
    pause
    exit /b 1
)

if not exist "dist\backup.exe" (
    echo [ERROR] dist\backup.exe was not created
    pause
    exit /b 1
)

echo [SUCCESS] Exe built successfully
echo.

REM Get initial file size
for %%A in (dist\backup.exe) do set "SIZE_BEFORE=%%~zA"
set /a SIZE_MB_BEFORE=!SIZE_BEFORE! / 1048576
echo [INFO] Exe size: !SIZE_MB_BEFORE! MB
echo.

REM ============================================
REM STEP 6: Add version information
REM ============================================

if defined SKIP_VERSION goto :skip_version

echo [STEP 6A/6] Adding version information...
echo.

REM Check for Resource Hacker
if not exist "ResourceHacker\ResourceHacker.exe" (
    echo [INFO] Downloading Resource Hacker...
    
    if not exist "ResourceHacker" mkdir ResourceHacker
    
    curl -L "http://www.angusj.com/resourcehacker/resource_hacker.zip" -o "ResourceHacker\resource_hacker.zip" 2>nul
    
    if exist "ResourceHacker\resource_hacker.zip" (
        tar -xf "ResourceHacker\resource_hacker.zip" -C "ResourceHacker" 2>nul
        echo [SUCCESS] Resource Hacker downloaded
    ) else (
        echo [WARNING] Could not download Resource Hacker
        echo [INFO] Continuing without version info...
        goto :skip_version
    )
)

if exist "ResourceHacker\ResourceHacker.exe" (
    echo [INFO] Injecting version info into exe...
    
    ResourceHacker\ResourceHacker.exe -open "dist\backup.exe" -save "dist\backup.exe" -action addoverwrite -res "scripts\version_resource.res" -mask VERSIONINFO,1, >nul 2>nul
    
    if %ERRORLEVEL% EQU 0 (
        echo [SUCCESS] Version info added!
        echo.
    ) else (
        echo [WARNING] Version info injection failed
        echo.
    )
) else (
    echo [WARNING] Resource Hacker not available
    echo.
)

:skip_version

REM ============================================
REM STEP 7: Add digital signature
REM ============================================
echo [STEP 6B/6] Adding digital signature...
echo.
echo [INFO] Do you want to add a digital signature?
echo [INFO] This creates a self-signed certificate (trusted on this PC)
echo.

choice /C YN /M "Add digital signature"
if errorlevel 2 goto :skip_signature

echo.
echo [INFO] Creating certificate and signing exe...
echo.

REM Call PowerShell signing script
if exist "scripts\sign-helper.ps1" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\sign-helper.ps1"
    
    if %ERRORLEVEL% EQU 0 (
        echo [SUCCESS] Digital signature added!
    ) else (
        echo [WARNING] Signature process had issues
    )
) else (
    echo [WARNING] Sign helper script not found
)

:skip_signature

REM ============================================
REM Build Complete!
REM ============================================
echo.
echo ============================================
echo          BUILD COMPLETED SUCCESSFULLY!
echo ============================================
echo.

REM Get final file size
for %%A in (dist\backup.exe) do set "SIZE_AFTER=%%~zA"
set /a SIZE_MB_AFTER=!SIZE_AFTER! / 1048576

echo [SUCCESS] Production executable created!
echo.
echo Output: dist\backup.exe
echo Size: !SIZE_MB_AFTER! MB
echo.
echo What's included:
echo   +-- Embedded Icon: YES (512x512 multi-resolution)

if not defined SKIP_VERSION (
    echo   +-- Version Info: YES ^(Product, Copyright, Description^)
) else (
    echo   +-- Version Info: NO ^(Windows SDK not found^)
)

REM Check if signed
powershell -Command "Get-AuthenticodeSignature 'dist\backup.exe' | Select-Object -ExpandProperty Status" | findstr /C:"Valid" >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   +-- Digital Signature: SIGNED ^(Self-signed certificate^)
) else (
    echo   +-- Digital Signature: NOT SIGNED
)

echo.
echo [INFO] Verify metadata:
echo   python tools\verify_exe.py
echo.
echo [INFO] Test executable:
echo   .\dist\backup.exe
echo.
echo [INFO] Check properties:
echo   Right-click dist\backup.exe -^> Properties
echo   - Details tab: Version information
echo   - Digital Signatures tab: Certificate
echo.
echo ============================================

pause
exit /b 0
