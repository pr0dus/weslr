#!/bin/sh

if [ -n "$PREFIX" ] && [ -w "$PREFIX/tmp" ]; then
  PIDFILE="$PREFIX/tmp/weslr.pid"
else
  PIDFILE=".runtime/weslr.pid"
fi

if [ ! -f "$PIDFILE" ]; then
  echo "WESLR is not running."
  exit 0
fi

PID=$(cat "$PIDFILE")

if kill -0 "$PID" 2>/dev/null; then
  kill "$PID" && rm -f "$PIDFILE"
  echo "WESLR stopped."
else
  echo "Process $PID not running. Removing stale PID file."
  rm -f "$PIDFILE"
fi
exit 0
