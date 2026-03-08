# scripts/docker-run.ps1
# ──────────────────────
# Run the TONHE Module HMI in Docker on Windows.
#
# Requirements:
#   - Docker Desktop for Windows (Linux containers mode)
#   - An X server running on the host:
#       VcXsrv  : https://sourceforge.net/projects/vcxsrv/
#       X410    : https://x410.app  (Microsoft Store)
#       MobaXterm includes a built-in X server
#
# Usage (from the tonhe_module_hmi\ directory):
#   .\scripts\docker-run.ps1             # real ADS mode
#   .\scripts\docker-run.ps1 -Mock       # mock PLC simulator
#   .\scripts\docker-run.ps1 -Build      # (re)build image before running
#
# VcXsrv quick-start:
#   1. Launch XLaunch → Multiple windows → Display 0
#   2. Tick "Disable access control"
#   3. Start → then run this script

param(
    [switch]$Mock,
    [switch]$Build
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Guard: Docker must be installed ──────────────────────────────────────────
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "ERROR: 'docker' command not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "Install Docker Desktop for Windows:" -ForegroundColor Yellow
    Write-Host "  https://docs.docker.com/desktop/install/windows-install/"
    Write-Host ""
    Write-Host "After installing, restart your terminal and run this script again."
    exit 1
}

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$Image      = "tonehmi:latest"

# ── Detect host IP for X11 (Docker containers can't reach 'localhost' directly)
$HostIP = (
    Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.InterfaceAlias -notmatch 'Loopback|vEthernet' } |
    Select-Object -First 1 -ExpandProperty IPAddress
)

if (-not $HostIP) {
    Write-Error "Could not determine host IP address for X11 forwarding."
    exit 1
}

$DisplayVar = "${HostIP}:0.0"

Write-Host ""
Write-Host "Host IP for X11  : $HostIP"
Write-Host "DISPLAY          : $DisplayVar"
Write-Host ""

# ── (Re)build if requested or image doesn't exist ────────────────────────────
$ImageExists = docker image inspect $Image 2>$null
if ($Build -or -not $ImageExists) {
    Write-Host "Building Docker image..."
    docker build -t $Image $ProjectDir
}

# ── Run ───────────────────────────────────────────────────────────────────────
$MockValue = if ($Mock) { "1" } else { "0" }

$RunArgs = @(
    "run", "--rm",
    "--name", "tonehmi-run",
    "-e", "DISPLAY=$DisplayVar",
    "-e", "MOCK_ADS=$MockValue",
    # Config persistence
    "-v", "tonehmi-config:/home/appuser/.config"
)

# ADS needs host networking; on Windows Docker Desktop uses a VM so we map
# the port range instead (ADS uses TCP 48898 / UDP 48899).
if (-not $Mock) {
    $RunArgs += @("-p", "48898:48898", "-p", "48899:48899/udp")
    Write-Host "Real ADS mode – ensure your TwinCAT route is configured for the container IP."
} else {
    Write-Host "Mock mode – no PLC connection needed."
}

Write-Host ""

docker @RunArgs $Image
