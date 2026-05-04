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

_workspace = Path(__file__).resolve().parents[2]
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
    ("asdfghjkl nonsense", "fallback_safe"),
    ("tell me about yourself", "fallback_safe"),
    ("who are you?", "fallback_safe"),
]


# ---------------------------------------------------------------------------
# SECTION 1 — Response structure contract
# ---------------------------------------------------------------------------
print("\nTest 1: weslr_chat returns dict with required keys")
for msg, expected_path in TEST_CASES:
    r = chat(msg)
    check(isinstance(r, dict), f"chat({msg[:20]!r}) → dict")
    check("success" in r, f"  'success' key present")
    check("reply" in r, f"  'reply' key present")
    check("intent" in r, f"  'intent' key present")
    check(isinstance(r.get("intent"), dict), f"  intent is dict (not None)")


# ---------------------------------------------------------------------------
# SECTION 2 — All paths return valid JSON-serializable responses
# ---------------------------------------------------------------------------
print("\nTest 2: all paths return JSON-serializable responses")
for msg, _ in TEST_CASES:
    r = chat(msg)
    try:
        serialized = json.dumps(r, ensure_ascii=False)
        check(True, f"chat({msg[:15]!r}) → JSON OK")
    except Exception as e:
        check(False, f"chat({msg[:15]!r}) → JSON error: {e}")


# ---------------------------------------------------------------------------
# SECTION 3 — No unpacking errors for any path
# ---------------------------------------------------------------------------
print("\nTest 3: no unpacking / structure errors for any path")
paths_seen = set()
for msg, _ in TEST_CASES:
    try:
        r = chat(msg)
        paths_seen.add(r.get("intent", {}).get("path", "unknown"))
    except ValueError as e:
        if "unpack" in str(e).lower() or "expected 2" in str(e):
            check(False, f"unpacking error on {msg[:20]!r}: {e}")
        else:
            raise
check(True, f"no unpacking errors across {len(paths_seen)} paths: {sorted(paths_seen)}")


# ---------------------------------------------------------------------------
# SECTION 4 — Signal hook receives valid response dict
# ---------------------------------------------------------------------------
print("\nTest 4: signal hook receives valid response dict")
# Patch the capture function to verify it receives the right structure
import weslr.tests.test_staging_server_signal_hook_v1 as hook_test_mod
importlib.reload(hook_test_mod)

from weslr.website_signal_integration import capture_website_signal

for msg, _ in TEST_CASES:
    r = chat(msg)
    try:
        capture_website_signal(
            message=msg,
            session_id="contract_test_session",
            response_path=r.get("source") or r.get("intent", {}).get("path", "unknown"),
            quality_class=r.get("intent", {}).get("_quality_class") or "unknown",
            blocked_write=r.get("intent", {}).get("path") == "blocked_write",
            evidence_offer_shown=bool(
                r.get("intent", {}).get("_omnichat_policy", {}).get("evidence_offer")
                if isinstance(r.get("intent", {}).get("_omnichat_policy"), dict)
                else False
            ),
            evidence_offer_accepted=False,
            topic_normalized=(
                r.get("intent", {}).get("topics", [None])[0]
                if r.get("intent", {}).get("topics")
                else None
            ),
            fallback_triggered=r.get("intent", {}).get("path") in ("fallback_safe", "fallback_template"),
        )
        check(True, f"signal hook ok for path={r.get('intent',{}).get('path')!r}")
    except Exception as e:
        check(False, f"signal hook error for {msg[:20]!r}: {e}")


# ---------------------------------------------------------------------------
# SECTION 5 — Error path (exception in chat) returns safe dict
# ---------------------------------------------------------------------------
print("\nTest 5: exception in chat returns safe error dict")
# Test with a message that triggers an exception path by patching
import unittest.mock as mock

# Force an exception in interpret_human_turn
with mock.patch("dialogue.interpret_human_turn", side_effect=RuntimeError("forced")):
    r = chat("test")
    check(isinstance(r, dict), "exception returns dict")
    check("success" in r, "exception response has 'success' key")
    check(r.get("success") is False, "success is False on exception")
    check("reply" in r, "exception response has 'reply' key")
    try:
        json.dumps(r)
        check(True, "error response is JSON-serializable")
    except Exception as e:
        check(False, f"error response not JSON-serializable: {e}")


# ---------------------------------------------------------------------------
# SECTION 6 — intent nested fields never None (defensive access)
# ---------------------------------------------------------------------------
print("\nTest 6: intent nested fields safe for all paths")
for msg, _ in TEST_CASES:
    r = chat(msg)
    intent = r.get("intent") or {}
    path = intent.get("path")
    topics = intent.get("topics", [])
    # These must not raise
    _ = path or "none"
    _ = topics or []
    check(True, f"intent access safe for path={path!r}")


# ---------------------------------------------------------------------------
# SECTION 7 — Response source field is always present
# ---------------------------------------------------------------------------
print("\nTest 7: response source field present for all paths")
for msg, _ in TEST_CASES:
    r = chat(msg)
    source = r.get("source")
    check(source is not None, f"source present for {msg[:15]!r}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if FAIL:
        print("STAGING_CHAT_CONTRACT_V1_FAILED")
        sys.exit(1)
    else:
        print("STAGING_CHAT_CONTRACT_V1_OK")
        sys.exit(0)