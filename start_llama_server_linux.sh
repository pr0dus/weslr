#!/bin/bash
# Start llama-server for Weslr embedded inference (Linux server-specific)

set -e

MODEL_PATH="/data/data/com.termux/files/home/.openclaw/workspace/models/qwen2.5-0.5b-instruct-q5_k_m.gguf"
LOG_DIR="/data/data/com.termux/files/home/.openclaw/workspace/.circleforge-failsafe"
LOG_FILE="${LOG_DIR}/llama-server.log"
PID_FILE="/data/data/com.termux/files/home/.openclaw/workspace/.circleforge-failsafe/llama-server.pid"
HOST="127.0.0.1"
PORT="18081"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Kill any existing server
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "Stopping existing server (PID: $OLD_PID)..."
    kill "$OLD_PID" 2>/dev/null || true
    sleep 2
  fi
fi

# Start server
echo "Starting llama-server..."
nohup /usr/bin/llama-server \
  -m "$MODEL_PATH" \
  --host "$HOST" \
  --port "$PORT" \
  -c 2048 \
  -n 180 \
  --threads 4 \
  > "$LOG_FILE" 2>&1 &
NEW_PID=$!

echo "$NEW_PID" > "$PID_FILE"
echo "Started llama-server (PID: $NEW_PID) on $HOST:$PORT"

# Wait for ready
for i in $(seq 1 30); do
  if curl -s http://$HOST:$PORT/models >/dev/null 2>&1; then
    echo "Server ready after $i seconds"
    exit 0
  fi
  sleep 1
done

echo "Server failed to start within 30 seconds"
exit 1
