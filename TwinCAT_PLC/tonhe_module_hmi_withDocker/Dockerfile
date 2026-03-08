# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile – TONHE Module HMI
# ─────────────────────────────────────────────────────────────────────────────
# Builds a portable Linux image that can run the PyQt6 HMI by forwarding the
# display to the host (X11 on Linux/macOS, VcXsrv/X410 on Windows).
#
# Build:
#   docker build -t tonehmi .
#
# Run (Linux/macOS):
#   docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix tonehmi
#
# Run (mock mode):
#   docker run --rm -e DISPLAY=$DISPLAY -e MOCK_ADS=1 \
#              -v /tmp/.X11-unix:/tmp/.X11-unix tonehmi
#
# See scripts/docker-run.sh  and  scripts/docker-run.ps1 for one-liner helpers.
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ── System dependencies for Qt6 / PyQt6 ──────────────────────────────────────
# libxcb-* and libGL are required by Qt6's xcb platform plugin.
# libdbus-1-3 is needed by Qt's dbus integration.
# fonts-dejavu gives readable fallback fonts inside the container.
RUN apt-get update && apt-get install -y --no-install-recommends \
        # X11 / XCB platform support
        libxcb1 \
        libxcb-cursor0 \
        libxcb-icccm4 \
        libxcb-image0 \
        libxcb-keysyms1 \
        libxcb-randr0 \
        libxcb-render-util0 \
        libxcb-shape0 \
        libxcb-shm0 \
        libxcb-util1 \
        libxcb-xfixes0 \
        libxcb-xinerama0 \
        libxcb-xkb1 \
        libxkbcommon-x11-0 \
        libxkbcommon0 \
        # OpenGL / EGL
        libgl1 \
        libegl1 \
        # Font / misc Qt runtime
        libfontconfig1 \
        libfreetype6 \
        libdbus-1-3 \
        libxi6 \
        libxrender1 \
        libxext6 \
        libx11-xcb1 \
        # Fonts so labels render correctly
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# ── Create a non-root user (good practice; Qt also behaves better) ────────────
RUN useradd -m -u 1000 appuser

WORKDIR /app

# ── Copy dependency manifest first (layer-cache friendly) ────────────────────
COPY requirements.txt ./

# ── Install Python packages ───────────────────────────────────────────────────
# PyQt6 ships its own Qt libs inside the wheel, so no separate Qt install needed.
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application source ───────────────────────────────────────────────────
COPY app.py         ./
COPY src/           ./src/
COPY config/        ./config/
COPY resources/     ./resources/

# ── Switch to non-root user ───────────────────────────────────────────────────
USER appuser

# ── Qt platform: use xcb (X11 forwarding); override at runtime if needed ─────
ENV QT_QPA_PLATFORM=xcb
# Suppress Qt's "could not connect to dbus" warning (harmless in containers)
ENV DBUS_SESSION_BUS_ADDRESS=disabled

# ── Default: real ADS mode.  Pass -e MOCK_ADS=1 to enable mock simulation ────
ENV MOCK_ADS=0

ENTRYPOINT ["python", "app.py"]
