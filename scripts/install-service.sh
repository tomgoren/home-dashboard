#!/usr/bin/env bash
# Installs and starts weathr-panel as a systemd service using the current
# user and the mise-managed venv already set up by pi-setup.sh.
#
# Usage: ./scripts/install-service.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_USER="$(whoami)"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
SERVICE_FILE=/etc/systemd/system/weathr-panel.service

if [ ! -x "$VENV_PYTHON" ]; then
  echo "error: $VENV_PYTHON not found." >&2
  echo "Run ./scripts/pi-setup.sh (or 'mise run setup') first." >&2
  exit 1
fi

echo "==> Writing $SERVICE_FILE ..."
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=weathr-panel weather appliance
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_PYTHON -m app.main
Restart=on-failure
RestartSec=3
# Needed for direct DRM/KMS + input access without a desktop session.
SupplementaryGroups=video input render

[Install]
WantedBy=multi-user.target
EOF

echo "==> Enabling and starting the service..."
sudo systemctl daemon-reload
sudo systemctl enable --now weathr-panel

cat <<EOF

==> Installed and started.

  Status: sudo systemctl status weathr-panel
  Logs:   journalctl -u weathr-panel -f
  Stop:   sudo systemctl stop weathr-panel
EOF
