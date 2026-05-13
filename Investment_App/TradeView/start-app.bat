@echo off
:: ============================================================
:: start-app.bat  —  Launch Investment Portfolio Dashboard
:: Starts BackendFastAPI in a new window, then runs Vite dev
:: ============================================================

setlocal

set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%..\BackendFastAPI"
set "FRONTEND_DIR=%SCRIPT_DIR%"

echo.
echo  =====================================================
echo   Investment Portfolio Dashboard
echo  =====================================================
echo.

:: ── 1. Start BackendFastAPI in a separate window ─────────────
echo  [1/3] Starting BackendFastAPI at http://localhost:8000 ...
if exist "%BACKEND_DIR%\start-dev.bat" (
    start "BackendFastAPI" cmd /c "cd /d "%BACKEND_DIR%" && call start-dev.bat"
) else (
    echo  [WARN] start-dev.bat not found in BackendFastAPI — skipping backend start.
)

:: Give the backend a moment to initialise
timeout /t 3 /nobreak >nul

:: ── 2. Install npm dependencies if node_modules is missing ───
echo  [2/3] Checking npm dependencies ...
if not exist "%FRONTEND_DIR%\node_modules" (
    echo  node_modules not found — running npm install ...
    cd /d "%FRONTEND_DIR%"
    npm install
    if errorlevel 1 (
        echo  [ERROR] npm install failed. Aborting.
        pause
        exit /b 1
    )
) else (
    echo  node_modules OK — skipping install.
)

:: ── 3. Start Vite dev server in background ───────────────────
echo  [3/3] Starting Vite dev server at http://localhost:5173 ...
echo.
echo  Dashboard : http://localhost:5173
echo  Backend   : http://localhost:8000
echo  API Docs  : http://localhost:8000/docs
echo.
echo  Press Ctrl+C to stop the frontend server.
echo.
cd /d "%FRONTEND_DIR%"
start "ViteDev" cmd /c "npm run dev"

:: ── 4. Wait for Vite to be ready, then open Edge ─────────────
echo  Waiting for Vite to be ready...
:wait_loop
timeout /t 2 /nobreak >nul
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:5173' -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 goto wait_loop

echo  Vite is ready — launching Microsoft Edge...
start "" "msedge.exe" "http://localhost:5173"

:: Keep this window open so user can see status
echo.
echo  Browser launched. Close this window or press any key to exit.
pause >nul

endlocal
