# Sourced by the remote-*.sh scripts. Not a standalone script.
if [ ! -f .remote.env ]; then
  echo "error: .remote.env not found. Copy .remote.env.example to .remote.env and set REMOTE_HOST." >&2
  exit 1
fi
# shellcheck disable=SC1091
source .remote.env

: "${REMOTE_HOST:?REMOTE_HOST must be set in .remote.env, e.g. pi@10.0.0.37}"
: "${REMOTE_DIR:=~/home-dashboard}"
: "${REPO_URL:=https://github.com/tomgoren/home-dashboard.git}"
