@echo off
:: ──────────────────────────────────────────────────────────────────────────────
:: start-dev.bat  —  Launch FastAPI dev server in a new PowerShell window
:: Usage: double-click or run from any directory
:: ──────────────────────────────────────────────────────────────────────────────

start "FastAPI Dev Server" powershell -NoExit -ExecutionPolicy RemoteSigned -File "%~dp0start-dev.ps1"
