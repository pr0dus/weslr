#!/bin/sh
# weslr-start.sh — Start the WESLR chat server
#
# Usage: ./weslr-start.sh [port]
#   port  — optional, defaults to 8081
#
# What it does:
#   1. Resolves the workspace root (parent of scripts/)
#   2. Creates .runtime/ directory for PID file
#   3. Checks if already running
#   4. Starts chat_ui.py via python3 on the configured port
#   5. Writes PID to .runtime/weslr.pid

set -e

SCRIPT_DIR="$(dirname "$0")"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$WORKSPACE_DIR"

# Port argument or default
PORT="${1:-8081}"

# PID file in workspace (avoids Termux-specific PREFIX assumptions)
PIDFILE="$WORKSPACE_DIR/.runtime/weslr.pid"

# Ensure .runtime directory exists
if [ ! -d "$WORKSPACE_DIR/.runtime" ]; then
    mkdir -p "$WORKSPACE_DIR/.runtime"
fi

# Check if already running
if [ -f "$PIDFILE" ]; then
    PID="$(cat "$PIDFILE")"
    if kill -0 "$PID" 2>/dev/null; then
        echo "WESLR is already running with PID $PID on port $PORT"
        echo "Access it at http://localhost:$PORT"
        exit 0
    else
        echo "Removing stale PID file for dead process $PID."
        rm -f "$PIDFILE"
    fi
fi

# Check if port is already in use
if command -v ss >/dev/null 2>&1; then
    if ss -tln | grep -q ":$PORT"; then
        echo "Port $PORT is already in use. Free it first: lsof -ti tcp:$PORT | xargs kill"
        exit 1
    fi
elif command -v lsof >/dev/null 2>&1; then
    if lsof -i tcp:"$PORT" | grep LISTEN >/dev/null 2>&1; then
        echo "Port $PORT is already in use. Free it first."
        exit 1
    fi
elif command -v netstat >/dev/null 2>&1; then
    if netstat -tln 2>/dev/null | grep -q ":$PORT "; then
        echo "Port $PORT is already in use. Free it first."
        exit 1
    fi
fi

# Start the real server — chat_ui.py (ThreadingHTTPServer)
nohup python3 "$WORKSPACE_DIR/chat_ui.py" > "$WORKSPACE_DIR/.runtime/weslr.log" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"
echo "WESLR started with PID $PID on port $PORT"
echo "Access it at http://localhost:$PORT"
echo "Logs: $WORKSPACE_DIR/.runtime/weslr.log"
echo "Stop:  ./scripts/weslr-stop.sh"
