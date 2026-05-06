# start-dev.ps1 — FastAPI development server launcher
# Called by start-dev.bat; can also be run directly in PowerShell.

Set-Location $PSScriptRoot

$activate = Join-Path $PSScriptRoot "..\..\.venv\Scripts\Activate.ps1" | Resolve-Path
& $activate

Write-Host ""
Write-Host "Starting FastAPI dev server..." -ForegroundColor Cyan
Write-Host "  http://127.0.0.1:8000      (API root)" -ForegroundColor Green
Write-Host "  http://127.0.0.1:8000/docs (Swagger UI)" -ForegroundColor Green
Write-Host ""

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --ws-ping-interval 60 --ws-ping-timeout 60
