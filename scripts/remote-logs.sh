#!/usr/bin/env bash
# Tails the service log on the remote device over SSH.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source scripts/_remote_env.sh

ssh -t "$REMOTE_HOST" "journalctl -u home-dashboard -f"
