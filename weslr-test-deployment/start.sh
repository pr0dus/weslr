#!/bin/bash
# Weslr Test Deployment Script
# Starts the private test instance on ports 8087 (UI) and 8091 (API)

set -e

WORKSPACE="/data/data/com.termux/files/home/.openclaw/workspace"
TEST_DIR="$WORKSPACE/weslr-test-deployment"

echo "============================================"
echo "WESLR PRIVATE TEST DEPLOYMENT"
echo "============================================"
echo ""
echo "Configuration:"
echo "  UI Port: 8087"
echo "  API Port: 8091"
echo "  Test Dir: $TEST_DIR"
echo ""

# Check if weslr_backend_contract exists
if [ ! -f "$WORKSPACE/weslr_backend_contract.py" ]; then
    echo "ERROR: weslr_backend_contract.py not found at $WORKSPACE"
    echo "This file is required for the API endpoints."
    exit 1
fi

# Check if weslr-ui exists
if [ ! -d "$WORKSPACE/weslr-ui" ]; then
    echo "ERROR: weslr-ui directory not found at $WORKSPACE"
    exit 1
fi

echo "✅ Found weslr_backend_contract.py"
echo "✅ Found weslr-ui directory"
echo ""

# Start the test server
cd "$WORKSPACE"
python "$TEST_DIR/server.py" --ui-port 8087 --api-port 8091 --host 0.0.0.0
