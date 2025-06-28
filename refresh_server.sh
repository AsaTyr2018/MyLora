#!/usr/bin/env bash
# Restart the MyLora application by killing the running process and
# starting ``main.py`` again. This works when the server was launched
# manually without a systemd service.

set -e

# Resolve the directory of this script so we can locate ``main.py`` even
# when called from elsewhere.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_MAIN="$SCRIPT_DIR/main.py"
PYTHON_BIN="${PYTHON:-python3}"

# Find running main.py processes and terminate them. ``pkill`` returns a
# non-zero exit status if no process matched, so ignore failures.
pkill -f "$APP_MAIN" 2>/dev/null || true

# Give the processes a moment to shut down cleanly.
sleep 2

# Restart the application in the background. ``nohup`` ensures the
# process keeps running if the calling shell exits.
nohup "$PYTHON_BIN" "$APP_MAIN" >/dev/null 2>&1 &

echo "MyLora restarted"
