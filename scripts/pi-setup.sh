#!/usr/bin/env bash
# First-time setup on the target Linux device (Raspberry Pi or similar).
# Installs system-level SDL2/DRM dependencies, group membership for
# display/input device access, mise, and the project's Python deps.
#
# Usage (from the project root, after `git clone`):
#   ./scripts/pi-setup.sh
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! command -v apt-get >/dev/null 2>&1; then
  echo "error: this script expects a Debian/Raspberry Pi OS system (apt-get not found)." >&2
  exit 1
fi

echo "==> Installing system packages (SDL2 runtime + build headers)..."
sudo apt-get update
sudo apt-get install -y \
  git curl \
  libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 \
  libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
  libfreetype6-dev pkg-config build-essential

echo "==> Adding $(whoami) to video/render/input groups (needed for DRM/KMS without a desktop session)..."
sudo usermod -aG video,render,input "$(whoami)"

if ! command -v mise >/dev/null 2>&1; then
  echo "==> Installing mise..."
  curl -fsSL https://mise.run | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "==> mise install (python + uv, pinned by .mise.toml)..."
mise install

echo "==> Installing Python dependencies into the mise-managed venv..."
mise run setup

echo "==> Creating config.toml if it doesn't exist yet..."
mise run config

if [ "${SKIP_SETUP_NEXT_STEPS:-0}" != "1" ]; then
cat <<EOF

==> Setup complete.

Next steps:
  1. Edit config.toml with your location (latitude/longitude/name):
       \$EDITOR config.toml
  2. Log out and back in (or reboot) so the video/render/input group
     membership takes effect:
       sudo reboot
  3. Check what display devices are actually available:
       mise run check-display
  4. Run it (from the Pi's local console, not a headless SSH session with
     no monitor attached):
       mise run run
  5. Once it looks right, install it as a systemd service so it survives
     reboots:
       ./scripts/install-service.sh
EOF
fi
