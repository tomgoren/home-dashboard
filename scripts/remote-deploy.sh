#!/usr/bin/env bash
# Pulls the latest code on an already-provisioned remote device,
# reinstalls dependencies, and restarts the service.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source scripts/_remote_env.sh

ssh -t "$REMOTE_HOST" "
  set -e
  cd '$REMOTE_DIR'
  git pull --ff-only
  mise run setup
  sudo systemctl restart home-dashboard
  sudo systemctl --no-pager status home-dashboard
"
