#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# run-web.sh — InvestCalc Web Dashboard launcher (macOS / Linux)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="$SCRIPT_DIR/web"

cyan()  { echo -e "\033[96m$*\033[0m"; }
green() { echo -e "\033[92m$*\033[0m"; }
red()   { echo -e "\033[91m$*\033[0m"; }

cyan "════════════════════════════════════════════"
cyan "  InvestCalc Web Dashboard"
cyan "════════════════════════════════════════════"

# ── 1. Check Node.js ──────────────────────────────────────────────────────────
# Load nvm if available
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

if ! command -v node &>/dev/null; then
  red "Error: Node.js not found."
  red "Install via: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash"
  red "Then: nvm install 20"
  exit 1
fi

green "  Node: $(node --version)  npm: $(npm --version)"

# ── 2. Install deps ───────────────────────────────────────────────────────────
cd "$WEB_DIR"
if [[ ! -d node_modules ]]; then
  cyan "  Installing dependencies..."
  npm install --silent
  green "  Dependencies installed."
fi

# ── 3. Launch dev server ──────────────────────────────────────────────────────
cyan "  Starting dev server → http://localhost:5174"
npm run dev
