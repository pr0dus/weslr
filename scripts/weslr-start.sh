#!/bin/sh
# weslr-start.sh — Start the WESLR HTTP server
#
# Usage: ./weslr-start.sh [port]
#   port  — optional, defaults to WESLR_PORT env or auto-selected free port
#
# Canonical entrypoint. Starts main.py serve which provides:
#   /           — dashboard UI
#   /operator   — operator dashboard
#   /chat       — chat endpoint (POST JSON {message})
#   /onboarding — onboarding flow
#   /api/health, /api/state, /api/initialize
#
# Port priority:
#   1. WESLR_PORT env variable (highest)
#   2. Port stored in .weslr/port.conf (persisted)
#   3. Auto-selection: 8000 → 8090 → 8080 → next free port
#
# Port is persisted to .weslr/port.conf after first successful selection.
# The server is a stdlib ThreadingHTTPServer; no FastAPI/uvicorn required.

set -e

SCRIPT_DIR="$(dirname "$0")"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$WORKSPACE_DIR"

# --- Directory setup ---
RUNTIME_DIR="$WORKSPACE_DIR/.runtime"
CONFIG_DIR="$WORKSPACE_DIR/.weslr"
mkdir -p "$RUNTIME_DIR" "$CONFIG_DIR"

PIDFILE="$RUNTIME_DIR/weslr.pid"
PORTFILE="$CONFIG_DIR/port.conf"

# --- Port selection logic ---
# Priority: WESLR_PORT env > persisted port.conf > auto-select
_check_port() {
    _port="$1"
    if command -v ss >/dev/null 2>&1 && ss -tln 2>/dev/null | grep -q ":${_port}"; then
        return 1
    elif command -v lsof >/dev/null 2>&1 && lsof -i tcp:"$_port" 2>/dev/null | grep -q LISTEN; then
        return 1
    elif command -v netstat >/dev/null 2>&1 && netstat -tln 2>/dev/null | grep -q ":${_port} "; then
        return 1
    else
        return 0
    fi
}

_select_free_port() {
    for _candidate in 8000 8090 8080; do
        if _check_port "$_candidate"; then
            echo "$_candidate"
            return 0
        fi
    done
    # Beyond defaults: find any free port above 9000
    for _p in $(seq 9000 9100); do
        if _check_port "$_p"; then
            echo "$_p"
            return 0
        fi
    done
    echo "ERROR: No free port found in 8000-9100 range" >&2
    return 1
}

# Resolve PORT
if [ -n "$WESLR_PORT" ]; then
    PORT="$WESLR_PORT"
    if ! _check_port "$PORT"; then
        echo "Port $PORT (from WESLR_PORT) is in use. Trying auto-selection..." >&2
        PORT="$(_select_free_port)"
    fi
elif [ -f "$PORTFILE" ]; then
    PORT="$(cat "$PORTFILE")"
    if ! _check_port "$PORT"; then
        echo "Stored port $PORT is no longer free. Re-selecting..." >&2
        PORT="$(_select_free_port)"
    fi
else
    PORT="$(_select_free_port)"
fi

# Persist selected port (only if not from env — env takes precedence on restart)
if [ -z "$WESLR_PORT" ]; then
    echo "$PORT" > "$PORTFILE"
fi

# --- Check if already running on same port ---
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

# --- Start canonical runtime ---
nohup python3 "$WORKSPACE_DIR/main.py" serve --host 0.0.0.0 --port "$PORT" \
    > "$RUNTIME_DIR/weslr.log" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"
echo "WESLR started with PID $PID on port $PORT"
echo "Dashboard:  http://localhost:$PORT/"
echo "Chat:       http://localhost:$PORT/chat"
echo "Operator:   http://localhost:$PORT/operator"
echo "Onboarding: http://localhost:$PORT/onboarding"
echo "Logs:       $RUNTIME_DIR/weslr.log"
echo "Stop:       ./scripts/weslr-stop.sh"
echo "Port config: $PORTFILE (auto-persisted)"
