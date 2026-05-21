#!/usr/bin/env bash
# ============================================================
#  start-app.sh  —  Launch Investment Portfolio Dashboard
#  Starts BackendFastAPI in a new Terminal window, then runs
#  the Vite dev server and opens the browser automatically.
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../BackendFastAPI" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR"
VENV_ACTIVATE="$SCRIPT_DIR/../../.venv/bin/activate"

echo ""
echo " ====================================================="
echo "  Investment Portfolio Dashboard"
echo " ====================================================="
echo ""

# ── 1. Start BackendFastAPI in a new Terminal window ─────────
echo " [1/3] Starting BackendFastAPI at http://localhost:8000 ..."

# Build the backend command: activate venv then start uvicorn
BACKEND_CMD="cd '$BACKEND_DIR' && source '$VENV_ACTIVATE' && echo '' && echo '  FastAPI dev server' && echo '  http://127.0.0.1:8000      (API root)' && echo '  http://127.0.0.1:8000/docs (Swagger UI)' && echo '' && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --ws-ping-interval 60 --ws-ping-timeout 60"

osascript <<EOF
tell application "Terminal"
    activate
    do script "$BACKEND_CMD"
end tell
EOF

echo " Backend launched in a new Terminal window."

# Give the backend a moment to initialise
sleep 3

# ── 2. Check Node.js (via nvm if available) ──────────────────
if ! command -v node &>/dev/null; then
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
fi

if ! command -v node &>/dev/null; then
    echo " [ERROR] Node.js not found. Install via: nvm install 20"
    echo "         Or visit https://nodejs.org"
    exit 1
fi

echo " Node.js $(node --version) / npm $(npm --version)"

# ── 3. Install npm dependencies if node_modules is missing ───
echo " [2/3] Checking npm dependencies ..."
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    echo " node_modules not found — running npm install ..."
    npm install
fi
echo " node_modules OK."

# ── 4. Start Vite dev server in the background ───────────────
echo " [3/3] Starting Vite dev server at http://localhost:3000 ..."
echo ""
echo " Dashboard : http://localhost:3000"
echo " Backend   : http://localhost:8000"
echo " API Docs  : http://localhost:8000/docs"
echo ""
echo " Press Ctrl+C to stop the frontend server."
echo ""

npm run dev &
VITE_PID=$!

# ── 5. Wait for Vite to be ready, then open browser ──────────
RETRIES=0
MAX_RETRIES=30
echo " Waiting for Vite to be ready..."
while [ $RETRIES -lt $MAX_RETRIES ]; do
    if nc -z localhost 3000 2>/dev/null; then
        break
    fi
    sleep 2
    RETRIES=$((RETRIES + 1))
done

if [ $RETRIES -eq $MAX_RETRIES ]; then
    echo " [WARN] Vite did not respond after 60 s — opening browser anyway..."
else
    echo " Vite is ready — launching browser..."
fi

open "http://localhost:3000"

# Keep script alive so Ctrl+C kills the Vite server
wait $VITE_PID
