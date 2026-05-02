#!/bin/bash
# weslr_release_check.sh — Minimal WESLR release validation runner
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
echo "=================================================="
echo "WESLR Release Check  —  commit ${COMMIT}"
echo "=================================================="

# Gate 1: Release gate (includes test harness T1-T6)
echo ""
echo "--- Release Gate V1 ---"
if python3 weslr/tests/release_gate_v1.py; then
    echo "RELEASE_GATE_V1: PASS"
else
    echo "RELEASE_GATE_V1: FAIL"
    exit 1
fi

# Gate 2: self_test (DB/files/checkpoints)
echo ""
echo "--- self_test.py ---"
if python3 self_test.py; then
    echo "SELF_TEST: PASS"
else
    echo "SELF_TEST: FAIL"
    exit 1
fi

echo ""
echo "=================================================="
echo "WESLR_RELEASE_CHECK_OK  —  all gates passed"
echo "=================================================="