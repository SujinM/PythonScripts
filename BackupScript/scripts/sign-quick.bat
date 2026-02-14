@echo off
REM ============================================
REM Quick Digital Signature (PowerShell Only)
REM No Windows SDK or External Tools Required
REM ============================================

echo.
echo ============================================
echo Add Digital Signature to backup.exe
echo Using PowerShell (No SDK Required)
echo ============================================
echo.

REM Navigate to project root if running from scripts folder
if exist "..\src\backup.py" (
    cd ..
)

REM Check if exe exists
if not exist "dist\backup.exe" (
    echo [ERROR] dist\backup.exe not found
    echo Please build the exe first: build-exe.bat
    pause
    exit /b 1
)

echo [INFO] Creating self-signed certificate...
echo [INFO] This will be stored in your personal certificate store
echo.

REM Create certificate and sign using PowerShell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\sign-helper.ps1"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo Signing Complete!
    echo ============================================
    echo.
    echo Your exe is now digitally signed!
    echo.
) else (
    echo.
    echo [ERROR] Signing process failed
    echo.
)

pause
