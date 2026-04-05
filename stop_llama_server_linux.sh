#!/bin/bash
# Stop llama-server for Weslr embedded inference (Linux server-specific)

set -e

PID_FILE="/data/data/com.termux/files/home/.openclaw/workspace/.circleforge-failsafe/llama-server.pid"

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" 2>/dev/null; then
    echo "Stopping llama-server (PID: $PID)..."
    kill "$PID" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "Server stopped"
  else
    echo "No running server (stale PID file removed)"
    rm -f "$PID_FILE"
  fi
else
  echo "No PID file - checking for orphan processes..."
  PIDS=$(pgrep -f "llama-server.*qwen2.5-0.5b-instruct-q5_k_m" 2>/dev/null || true)
  if [ -n "$PIDS" ]; then
    echo "Found orphan process(es): $PIDS"
    kill $PIDS 2>/dev/null || true
  fi
fi
