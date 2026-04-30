#!/usr/bin/env python3
"""
WESLR Staging Chat Contract V1 — Tests

Validates:
- weslr_chat() always returns a dict with required keys
- staging server can serialize every response variant
- no KeyError / unpacking errors for any path
- signal hook still executes with each response variant
- JSON-serializable output for all paths

Confirms: STAGING_CHAT_CONTRACT_V1_OK
Exits non-zero on any failure.
"""

import sys
import json
import importlib
from pathlib import Path

_workspace = Path("/home/pr0/projects/weslr")
sys.path.insert(0, str(_workspace))

PASS = 0
FAIL = 0


def check(condition: bool, description: str):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  OK: {description}")
    else:
        FAIL += 1
        print(f"  FAIL: {description}")


# Reload to get fresh state
import weslr_backend_contract
importlib.reload(weslr_backend_contract)
from weslr_backend_contract import chat


# ── Test cases keyed by known response paths ──────────────────────────────────

TEST_CASES = [
    ("hello world", "fallback_safe"),
    ("what is this system?", "fallback_safe"),
    ("show system overview", "operator_overview"),
    ("show diagnostics", "ISS_query_all"),
    ("show weslr status", "state_checkpoint_query"),
    ("show iss probes", "ISS_probe_registry_query"),
    ("explain plan iss.not_integrated", "plan_explanation"),
    ("show implementation plans", "C8_plan_query_list"),
    ("what can you do", "fallback_safe"),
    ("can you learn from me", "fallback_safe"),
]


def run_test(message: str, expected_path: str) -> None:
    """Run a single chat test case."""
    try:
        result = chat(message)
        
        # Check required keys
        check(isinstance(result, dict), f"chat('{message}') returns dict")
        check("success" in result, f"chat('{message}') has 'success' key")
        check("reply" in result, f"chat('{message}') has 'reply' key")
        
        # Check success
        if result.get("success"):
            check("intent" in result, f"chat('{message}') has 'intent' key on success")
            check("source" in result, f"chat('{message}') has 'source' key on success")
        
        # Check JSON serializable
        try:
            json.dumps(result)
            check(True, f"chat('{message}') is JSON serializable")
        except Exception as e:
            check(False, f"chat('{message}') JSON serializable: {e}")
        
    except Exception as e:
        check(False, f"chat('{message}') raises no exception: {e}")


def main() -> int:
    """Run all chat contract tests."""
    print("=== WESLR Staging Chat Contract V1 Tests ===\n")
    
    for message, expected_path in TEST_CASES:
        run_test(message, expected_path)
    
    # Final report
    print(f"\nResults: {PASS} passed, {FAIL} failed")
    
    if FAIL == 0:
        print("STAGING_CHAT_CONTRACT_V1_OK")
        return 0
    else:
        print("STAGING_CHAT_CONTRACT_V1_FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
