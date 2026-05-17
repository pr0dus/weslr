#!/usr/bin/env bash
# WESLR Working Root Guard Script
# Abort if not in the correct WESLR repository and branch.
set -euo pipefail

EXPECTED_ROOT="/data/data/com.termux/files/home/weslr-pr47-clean"
EXPECTED_BRANCH="${WESLR_EXPECTED_BRANCH:-master}"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
BRANCH="$(git branch --show-current 2>/dev/null || true)"
HEAD="$(git rev-parse --short HEAD 2>/dev/null || true)"

if [ "$ROOT" != "$EXPECTED_ROOT" ]; then
    echo "BLOCKED_BY_BOUNDARY: wrong repo root"
    echo "expected: $EXPECTED_ROOT"
    echo "actual: ${ROOT:-<not a git repo>}"
    exit 2
fi

if [ "$BRANCH" != "$EXPECTED_BRANCH" ]; then
    echo "BLOCKED_BY_BOUNDARY: wrong branch"
    echo "expected: $EXPECTED_BRANCH"
    echo "actual: ${BRANCH:-<unknown>}"
    exit 3
fi

echo "WESLR_CORRECT_REPO_OK: $ROOT on $BRANCH at $HEAD"
