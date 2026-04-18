#!/bin/sh

if [ -n "$PREFIX" ] && [ -w "$PREFIX/tmp" ]; then
  PIDFILE="$PREFIX/tmp/weslr.pid"
else
  PIDFILE=".runtime/weslr.pid"
fi

PORT=8080
URL="http://localhost:$PORT"

if [ -f "$PIDFILE" ]; then
  PID=$(cat "$PIDFILE")
  if kill -0 "$PID" 2>/dev/null; then
    echo "WESLR is running with PID $PID. Access it at $URL"
    exit 0
  else
    echo "WESLR PID file exists but process $PID is not running."
    exit 1
  fi
else
  echo "WESLR is not running."
  exit 1
fi
