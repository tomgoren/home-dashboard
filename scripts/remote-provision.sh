#!/usr/bin/env bash
# Provisions a fresh headless device from this machine over SSH: clones
# the repo there and runs its device-side setup. No need to log into the
# device and clone it yourself first.
#
# Configure the target in .remote.env (copy .remote.env.example first).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source scripts/_remote_env.sh

echo "==> Cloning/updating $REPO_URL on $REMOTE_HOST:$REMOTE_DIR ..."
ssh "$REMOTE_HOST" "
  set -e
  if [ -d '$REMOTE_DIR/.git' ]; then
    git -C '$REMOTE_DIR' pull --ff-only
  else
    git clone '$REPO_URL' '$REMOTE_DIR'
  fi
"

echo "==> Running device setup on $REMOTE_HOST ..."
ssh -t "$REMOTE_HOST" "cd '$REMOTE_DIR' && ./scripts/pi-setup.sh"

if [ -f config.toml ]; then
  echo "==> Copying local config.toml to $REMOTE_HOST:$REMOTE_DIR/config.toml ..."
  scp config.toml "$REMOTE_HOST:$REMOTE_DIR/config.toml"
fi

cat <<EOF

==> Remote provisioning complete.

Next:
EOF

if [ ! -f config.toml ]; then
  cat <<EOF
  1. Set the location on the remote device (no local config.toml was
     found to push automatically):
       ssh $REMOTE_HOST "\$EDITOR $REMOTE_DIR/config.toml"
EOF
fi

cat <<EOF
  2. Reboot the remote device once for video/render/input group
     membership to take effect:
       ssh $REMOTE_HOST sudo reboot
  3. Run it remotely to test on the attached display:
       mise run remote:run
  4. Once it looks right, install it as a service:
       mise run remote:install-service
EOF
