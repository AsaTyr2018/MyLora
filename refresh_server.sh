#!/usr/bin/env bash
# Display a restart page on port 5001 while the main server reloads.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_MAIN="$SCRIPT_DIR/main.py"
RESTART_SERVER="$SCRIPT_DIR/restart_server.py"
PYTHON_BIN="${PYTHON:-python3}"

# Launch temporary restart server
nohup "$PYTHON_BIN" "$RESTART_SERVER" >/dev/null 2>&1 &
RESTART_PID=$!

# Give the API time to redirect to the restart page
sleep 1

# Stop running main.py instances (ignore failure when not running)
pkill -f "$APP_MAIN" 2>/dev/null || true
sleep 2

# Relaunch the application
nohup "$PYTHON_BIN" "$APP_MAIN" >/dev/null 2>&1 &
MAIN_PID=$!

# Wait for the main server to come back up
sleep 5

# Shutdown temporary restart server
kill $RESTART_PID

echo "MyLora restarted"
