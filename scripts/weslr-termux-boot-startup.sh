#!/bin/sh
# weslr-termux-boot-startup.sh — Termux:Boot-compatible WESLR startup
# Place in: $PREFIX/var/service/weslr/run  (Termux service style)
# Or link via Termux:Boot: cp to ~/.termux/boot/
#
# Termux:Boot executes scripts in ~/.termux/boot/ at device boot.
# This script starts the WESLR canonical runtime with proper defaults.

set -e

WORKSPACE_DIR="/data/data/com.termux/files/home/.openclaw/workspace"
cd "$WORKSPACE_DIR"

PORT="${WESLR_PORT:-8000}"
HOST="${WESLR_HOST:-0.0.0.0}"
PIDFILE="$WORKSPACE_DIR/.runtime/weslr.pid"
LOGFILE="$WORKSPACE_DIR/.runtime/weslr.log"

# Ensure runtime directory exists
if [ ! -d "$WORKSPACE_DIR/.runtime" ]; then
    mkdir -p "$WORKSPACE_DIR/.runtime"
fi

# Stop any existing instance first
if [ -f "$PIDFILE" ]; then
    OLD_PID="$(cat "$PIDFILE")"
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "WESLR already running as PID $OLD_PID"
        exit 0
    else
        rm -f "$PIDFILE"
    fi
fi

# Start canonical runtime
nohup python3 "$WORKSPACE_DIR/main.py" serve --host "$HOST" --port "$PORT" \
    > "$LOGFILE" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"

echo "WESLR started (PID $PID) on port $PORT"
echo "Workspace: $WORKSPACE_DIR"
echo "Logs: $LOGFILE"

# Wait for health check
sleep 3
if curl -sf "http://localhost:$PORT/api/health" > /dev/null 2>&1; then
    echo "Health check passed."
else
    echo "WARNING: Health endpoint not responding yet. Check logs: $LOGFILE"
fi
