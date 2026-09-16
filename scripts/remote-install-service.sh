#!/usr/bin/env bash
# Installs and starts the systemd service on the remote device, over SSH.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source scripts/_remote_env.sh

ssh -t "$REMOTE_HOST" "cd '$REMOTE_DIR' && ./scripts/install-service.sh"
