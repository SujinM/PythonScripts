@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: run-web.bat — InvestCalc Web Dashboard launcher (Windows)
:: ─────────────────────────────────────────────────────────────────────────────
setlocal EnableDelayedExpansion
title InvestCalc Web Dashboard
set "WEB_DIR=%~dp0web"

echo.
echo  ============================================
echo    InvestCalc Web Dashboard
echo  ============================================
echo.

:: Check node
where node >nul 2>&1
if !errorlevel! neq 0 (
  echo  [ERROR] Node.js not found. Install from https://nodejs.org
  pause & exit /b 1
)

for /f "tokens=*" %%V in ('node --version') do set NODE_VER=%%V
echo  Node: !NODE_VER!

:: Install deps
cd /d "%WEB_DIR%"
if not exist "node_modules\" (
  echo  Installing dependencies...
  npm install --silent
  if !errorlevel! neq 0 (echo  [ERROR] npm install failed & pause & exit /b 1)
  echo  Dependencies installed.
)

:: Launch
echo.
echo  Starting dev server at http://localhost:5174
start http://localhost:5174
npm run dev
pause
