#!/bin/bash
# Stop the Weslr test deployment

echo "Stopping Weslr test deployment..."

# Kill any processes on our test ports
pkill -f "weslr-test-deployment" || true
pkill -f "server.py" || true

echo "Test deployment stopped."
