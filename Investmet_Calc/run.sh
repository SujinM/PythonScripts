#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# run.sh — InvestCalc launcher (macOS / Linux)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_MIN="3.11"

# ── Colour helpers ────────────────────────────────────────────────────────────
cyan()   { echo -e "\033[96m$*\033[0m"; }
green()  { echo -e "\033[92m$*\033[0m"; }
yellow() { echo -e "\033[93m$*\033[0m"; }
red()    { echo -e "\033[91m$*\033[0m"; }

cyan "════════════════════════════════════════════"
cyan "  InvestCalc — Stock Market Calculator"
cyan "════════════════════════════════════════════"

# ── 1. Find Python ────────────────────────────────────────────────────────────
find_python() {
    for cmd in python3.12 python3.11 python3 python; do
        if command -v "$cmd" &>/dev/null; then
            ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
            major=${ver%%.*}
            minor=${ver##*.}
            if [[ "$major" -ge 3 && "$minor" -ge 11 ]]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

PYTHON=$(find_python) || {
    red "Error: Python $PYTHON_MIN+ not found. Please install it first."
    exit 1
}
green "  Python: $($PYTHON --version)"

# ── 2. Create virtual environment ─────────────────────────────────────────────
if [[ ! -d "$VENV_DIR" ]]; then
    yellow "  Creating virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"
    green "  venv created at $VENV_DIR"
fi

# ── 3. Activate ───────────────────────────────────────────────────────────────
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ── 4. Install package in editable mode (first run only) ──────────────────────
if ! python -c "import investcalc" &>/dev/null; then
    yellow "  Installing InvestCalc..."
    pip install --quiet -e "$SCRIPT_DIR"
    green "  Installation complete."
fi

# ── 5. Launch ─────────────────────────────────────────────────────────────────
echo ""
python -m investcalc
