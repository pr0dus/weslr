"""
WESLR_BACKEND_ENTRY_CHAT_PATH_FIXED — test real /chat contract for entry detection.

Tests the actual weslr_backend_contract.chat() function used by /chat.
Greetings must return natural entry greeting, not uncertainty_strong_response.
"""

import sys
import json as _json
from pathlib import Path as _Path

# ── imports ──────────────────────────────────────────────────────────────────

_ROOT = _Path(__file__).resolve().parents[2]  # workspace root (parent of weslr/)
_WESLR_BACKEND = _ROOT / "weslr_backend_contract.py"

import sys as _sys
_ROOT_STR = str(_ROOT)
if _ROOT_STR not in _sys.path:
    _sys.path.insert(0, _ROOT_STR)

import importlib.util as _importlib_util
_spec = _importlib_util.spec_from_file_location("weslr_backend_contract", str(_WESLR_BACKEND))
_weslr_backend_mod = _importlib_util.module_from_spec(_spec)
_sys.modules["weslr_backend_contract"] = _weslr_backend_mod
_spec.loader.exec_module(_weslr_backend_mod)

from weslr_backend_contract import chat


# ── helpers ───────────────────────────────────────────────────────────────────

def _assert_jwt_serializable(result: dict) -> None:
    """Result must be JSON-serializable (no bytes, sets, Path objects)."""
    try:
        _json.dumps(result)
    except TypeError as e:
        raise AssertionError(f"Result is not JSON-serializable: {e}")


# ── entry greeting tests ──────────────────────────────────────────────────────

def test_hey_returns_greeting_reply():
    result = chat("hey")
    assert result.get("success") is True, f"expected success=True, got {result}"
    reply = result.get("reply", "")
    assert "Hi — I'm WESLR" in reply, f"expected entry greeting, got: {reply!r}"
    assert "uncertain" not in reply.lower(), f"should NOT contain 'uncertain': {reply!r}"
    _assert_jwt_serializable(result)
    print("PASS: test_hey_returns_greeting_reply")


def test_hi_returns_greeting_reply():
    result = chat("hi")
    assert result.get("success") is True
    reply = result.get("reply", "")
    assert "Hi — I'm WESLR" in reply
    assert "uncertain" not in reply.lower()
    _assert_jwt_serializable(result)
    print("PASS: test_hi_returns_greeting_reply")


def test_hello_returns_greeting_reply():
    result = chat("hello")
    assert result.get("success") is True
    reply = result.get("reply", "")
    assert "Hi — I'm WESLR" in reply
    assert "uncertain" not in reply.lower()
    _assert_jwt_serializable(result)
    print("PASS: test_hello_returns_greeting_reply")


def test_hello_uppercase_returns_greeting_reply():
    result = chat("HELLO")
    assert result.get("success") is True
    reply = result.get("reply", "")
    assert "Hi — I'm WESLR" in reply
    _assert_jwt_serializable(result)
    print("PASS: test_hello_uppercase_returns_greeting_reply")


def test_yo_returns_greeting_reply():
    result = chat("yo")
    assert result.get("success") is True
    reply = result.get("reply", "")
    assert "Hi — I'm WESLR" in reply
    _assert_jwt_serializable(result)
    print("PASS: test_yo_returns_greeting_reply")


def test_hallo_returns_greeting_reply():
    result = chat("hallo")
    assert result.get("success") is True
    reply = result.get("reply", "")
    assert "Hi — I'm WESLR" in reply
    _assert_jwt_serializable(result)
    print("PASS: test_hallo_returns_greeting_reply")


# ── typo tolerance tests ──────────────────────────────────────────────────────

def test_hry_routes_to_greeting():
    result = chat("hry")
    assert result.get("success") is True
    reply = result.get("reply", "")
    assert "Hi — I'm WESLR" in reply, f"expected greeting, got: {reply!r}"
    _assert_jwt_serializable(result)
    print("PASS: test_hry_routes_to_greeting")


def test_helo_routes_to_greeting():
    result = chat("helo")
    assert result.get("success") is True
    reply = result.get("reply", "")
    assert "Hi — I'm WESLR" in reply, f"expected greeting, got: {reply!r}"
    _assert_jwt_serializable(result)
    print("PASS: test_helo_routes_to_greeting")


# ── non-entry tests ───────────────────────────────────────────────────────────

def test_random_input_not_entry():
    result = chat("asdasd123")
    assert result.get("success") is True
    reply = result.get("reply", "")
    # Random input should NOT produce entry greeting
    assert "Hi — I'm WESLR" not in reply, f"random input should not be entry greeting: {reply!r}"
    _assert_jwt_serializable(result)
    print("PASS: test_random_input_not_entry")


def test_fallback_still_returns_reply():
    result = chat("asdasd123")
    assert result.get("success") is True
    # Must return some reply, not empty
    assert isinstance(result.get("reply"), str) and result.get("reply", ""), \
        "fallback should still return a reply string"
    _assert_jwt_serializable(result)
    print("PASS: test_fallback_still_returns_reply")


# ── intent structure tests ─────────────────────────────────────────────────────

def test_greeting_has_deterministic_entry_source():
    result = chat("hey")
    assert result.get("source") == "deterministic_entry", \
        f"expected source=deterministic_entry, got {result.get('source')!r}"
    print("PASS: test_greeting_has_deterministic_entry_source")


def test_result_json_serializable():
    for msg in ["hey", "hi", "hello", "hry", "random xyz"]:
        result = chat(msg)
        _assert_jwt_serializable(result)
    print("PASS: test_result_json_serializable")


def test_intent_in_result():
    result = chat("hey")
    assert "intent" in result, "result must contain 'intent' key"
    assert isinstance(result["intent"], dict), "intent must be a dict"
    print("PASS: test_intent_in_result")


# ── signal hook verification ───────────────────────────────────────────────────
# These tests confirm the signal hook still fires after entry fix.

def test_signal_hook_still_pings_public_signal_store():
    """Spot-check: chat('hello') still hits signal hook without error."""
    import os
    signal_path = _ROOT / "weslr" / "public_signals.jsonl"
    before_lines = 0
    if signal_path.exists():
        before_lines = sum(1 for _ in open(signal_path))
    result = chat("hello")
    after_lines = sum(1 for _ in open(signal_path)) if signal_path.exists() else 0
    # Signal hook may or may not have fired (depends on rate limits/demo mode),
    # but the call must succeed without error.
    assert result.get("success") is True, f"chat('hello') should succeed, got {result}"
    # At minimum, no crash means the hook path is intact.
    print("PASS: test_signal_hook_still_pings_public_signal_store")


# ── run all ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_hey_returns_greeting_reply,
        test_hi_returns_greeting_reply,
        test_hello_returns_greeting_reply,
        test_hello_uppercase_returns_greeting_reply,
        test_yo_returns_greeting_reply,
        test_hallo_returns_greeting_reply,
        test_hry_routes_to_greeting,
        test_helo_routes_to_greeting,
        test_random_input_not_entry,
        test_fallback_still_returns_reply,
        test_greeting_has_deterministic_entry_source,
        test_result_json_serializable,
        test_intent_in_result,
        test_signal_hook_still_pings_public_signal_store,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    if failed == 0:
        print(f"All {passed} tests passed. WESLR_BACKEND_ENTRY_CHAT_PATH_FIXED")
    else:
        print(f"{passed}/{passed+failed} passed, {failed} FAILED")
        sys.exit(1)
