#!/usr/bin/env bash
# Runs the app directly on the remote device's own display, in the
# foreground, over SSH — for testing before installing it as a service.
# Ctrl+C here stops it. Calls the venv's python directly rather than
# `mise run run`, since that wrapper does not forward signals (including
# the SIGUSR1 debug-screenshot trigger) to the underlying process.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source scripts/_remote_env.sh

ssh -t "$REMOTE_HOST" "cd '$REMOTE_DIR' && .venv/bin/python -m app.main"
