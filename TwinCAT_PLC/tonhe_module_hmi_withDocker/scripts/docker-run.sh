#!/usr/bin/env bash
# scripts/docker-run.sh
# ─────────────────────
# Run the TONHE Module HMI in Docker on Linux or macOS.
#
# Usage:
#   ./scripts/docker-run.sh          # real ADS mode
#   ./scripts/docker-run.sh --mock   # mock PLC simulator
#   ./scripts/docker-run.sh --build  # (re)build image first
#
# Requirements:
#   - Docker installed and running
#   - X11 server accessible (standard on Linux; on macOS install XQuartz
#     and run: defaults write org.xquartz.X11 enable_iglx -bool true)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
IMAGE="tonehmi:latest"

MOCK=0
BUILD=0

for arg in "$@"; do
  case "$arg" in
    --mock)  MOCK=1 ;;
    --build) BUILD=1 ;;
    *)
      echo "Unknown option: $arg"
      echo "Usage: $0 [--mock] [--build]"
      exit 1
      ;;
  esac
done

# ── (Re)build if requested or image doesn't exist ────────────────────────────
if [[ "$BUILD" -eq 1 ]] || ! docker image inspect "$IMAGE" &>/dev/null; then
  echo "Building Docker image…"
  docker build -t "$IMAGE" "$PROJECT_DIR"
fi

# ── Allow the container to connect to the host X server ──────────────────────
xhost +local:docker 2>/dev/null || true

# ── Assemble run arguments ────────────────────────────────────────────────────
RUN_ARGS=(
  --rm
  --name tonehmi-run
  -e "DISPLAY=${DISPLAY:-:0}"
  -e "MOCK_ADS=${MOCK}"
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw
  -v tonehmi-config:/home/appuser/.config
)

# ADS requires host networking so UDP broadcast discovery works
if [[ "$MOCK" -eq 0 ]]; then
  RUN_ARGS+=(--network host)
fi

echo ""
if [[ "$MOCK" -eq 1 ]]; then
  echo "▶  Starting ToneHMI in MOCK mode…"
else
  echo "▶  Starting ToneHMI in REAL ADS mode…"
  echo "   Set ADS_TARGET_IP / ADS_TARGET_AMS env vars if needed."
fi
echo ""

docker run "${RUN_ARGS[@]}" "$IMAGE"
