#!/bin/sh
# weslr-start.sh — Start the WESLR HTTP server
#
# Usage: ./weslr-start.sh [port]
#   port  — optional, defaults to 8080
#
# Canonical entrypoint. Starts main.py serve which provides:
#   /           — dashboard UI
#   /operator   — operator dashboard
#   /chat       — chat endpoint (POST JSON {message})
#   /onboarding — onboarding flow
#   /artifact-review, /category/update, /pack/decision, /api/clearance/verify
#
# The server is a stdlib ThreadingHTTPServer; no FastAPI/uvicorn required.

set -e

SCRIPT_DIR="$(dirname "$0")"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$WORKSPACE_DIR"

# Port argument or default
PORT="${1:-8080}"

# PID file in workspace
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

# Start main.py serve — the canonical runtime server
# Provides /chat, /operator, /onboarding, and all state + artifact endpoints
nohup python3 "$WORKSPACE_DIR/main.py" serve --host 0.0.0.0 --port "$PORT" \
    > "$WORKSPACE_DIR/.runtime/weslr.log" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"
echo "WESLR started with PID $PID on port $PORT"
echo "Dashboard:  http://localhost:$PORT/"
echo "Chat:       http://localhost:$PORT/chat"
echo "Operator:   http://localhost:$PORT/operator"
echo "Onboarding: http://localhost:$PORT/onboarding"
echo "Logs: $WORKSPACE_DIR/.runtime/weslr.log"
echo "Stop:  ./scripts/weslr-stop.sh"
