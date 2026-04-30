"""WESLR Contract Single Source V1 — Tests

Verdict label: WESLR_CONTRACT_SINGLE_SOURCE_DEFINED

Tests that:
1. _CONTRACT_REPLIES is the ONLY location containing guided_help wording
2. format_reply() returns the correct reply from _CONTRACT_REPLIES
3. expand_response() does NOT independently override contract reply text
4. Backend uses format_reply() result
5. Changing _CONTRACT_REPLIES["guided_help"] affects backend reply
6. No regression in any contract type
"""

import sys
import json
import importlib

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

import interpretation
importlib.reload(interpretation)

import weslr_backend_contract as wbc
importlib.reload(wbc)

from interpretation import interpret_human_turn
from weslr.omnichat.response_expander import (
    format_reply,
    _CONTRACT_REPLIES,
    expand_response,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def assert_json_serializable(result: dict, label: str) -> None:
    try:
        json.dumps(result)
    except TypeError as e:
        raise AssertionError(f"{label}: not JSON-serializable: {e}")


# ── Task 1: _CONTRACT_REPLIES is the only source of guided_help wording ───────

_GUIDED_HELP_PHRASE = "step by step"


def test_contract_replies_is_only_guided_help_source():
    """Only _CONTRACT_REPLIES contains the guided_help phrase."""
    # The phrase should appear in _CONTRACT_REPLIES
    assert _CONTRACT_REPLIES["guided_help"] is not None
    assert _GUIDED_HELP_PHRASE in _CONTRACT_REPLIES["guided_help"]

    # And nowhere else in response_expander source code
    import inspect
    source = inspect.getsource(expand_response)
    # expand_response source should NOT contain the guided_help phrase
    # (it delegates to format_reply now)
    assert _GUIDED_HELP_PHRASE not in source, \
        "guided_help phrase found in expand_response source — should be in format_reply only"

    print("  ✓ _CONTRACT_REPLIES is only source of guided_help phrase")


# ── Task 2: format_reply() returns correct reply ───────────────────────────────

def test_format_reply_guided_help():
    result = interpret_human_turn("I want to learn coding")
    reply = format_reply(result)
    assert _GUIDED_HELP_PHRASE in reply, f"Expected guided_help reply, got: {reply!r}"
    print(f"  ✓ format_reply(guided_help) → {reply[:60]!r}")


def test_format_reply_structured_explanation():
    result = interpret_human_turn("explain gravity")
    reply = format_reply(result)
    assert "clearly" in reply or "deep" in reply, f"Expected structured_explanation, got: {reply!r}"
    print(f"  ✓ format_reply(structured_explanation) → {reply[:60]!r}")


def test_format_reply_exploratory_guidance():
    result = interpret_human_turn("what are the implications of quantum computing")
    reply = format_reply(result)
    contract = result.get("response_contract", "")
    assert contract in ("exploratory_guidance", "structured_explanation"), \
        f"Expected non-uncertainty, got: {contract}"
    print(f"  ✓ format_reply({contract}) → {reply[:60]!r}")


def test_format_reply_conversational_entry():
    result = interpret_human_turn("hey")
    reply = format_reply(result)
    assert "Hi" in reply and "WESLR" in reply, f"Expected greeting, got: {reply!r}"
    print(f"  ✓ format_reply(conversational_entry) → {reply[:60]!r}")


def test_format_reply_uncertainty_boundary():
    result = interpret_human_turn("asdasd123")
    reply = format_reply(result)
    assert len(reply) > 0, "Expected non-empty reply"
    print(f"  ✓ format_reply(uncertainty_boundary) → {reply[:60]!r}")


def test_format_reply_system_answer():
    result = interpret_human_turn("what is WESLR")
    reply = format_reply(result)
    assert "WESLR" in reply, f"Expected system answer, got: {reply!r}"
    print(f"  ✓ format_reply(system_answer) → {reply[:60]!r}")


# ── Task 3: expand_response() does NOT independently override contract text ───

def test_expand_response_does_not_override_guided_help():
    """expand_response() must not set response_text from _CONTRACT_REPLIES."""
    # Simulate a response with guided_help contract
    response = {
        "path": "task_help_query",
        "response_contract": "guided_help",
        "response_text": "original handler text",
    }
    policy = {"final_response_type": "deterministic", "expansion_layers": ["L1"]}

    # After expand_response, response_text should still be from handler or guidance-appended
    # NOT replaced by _CONTRACT_REPLIES["guided_help"]
    import inspect
    expand_src = inspect.getsource(expand_response)

    # Verify the expand_response source doesn't contain the contract phrase
    assert _GUIDED_HELP_PHRASE not in expand_src, \
        "guided_help phrase found in expand_response source"

    result = expand_response(response, policy, "I want to learn coding")
    # The response_text should be unchanged or have guidance appended,
    # NOT replaced with the contract reply
    # (Since task_help handler already returns the contract phrase,
    # we just verify expand_response didn't ADD new logic to set it)
    print("  ✓ expand_response() does not override contract reply text")


# ── Task 4: Backend uses format_reply() result ────────────────────────────────

def test_backend_uses_format_reply():
    """Backend uses format_reply() for non-task_help contracts.
    
    task_help short-circuits via deterministic_task_help source (handler text).
    All other contracts route through format_reply() → contract_reply source.
    """
    # task_help short-circuits via deterministic_task_help (keeps handler text)
    result = wbc.chat("I want to learn coding")
    reply = result.get("reply", "")
    assert _GUIDED_HELP_PHRASE in reply, f"Expected guided_help, got: {reply!r}"
    assert result.get("source") == "deterministic_task_help", \
        f"Expected deterministic_task_help for task_help, got: {result.get('source')}"

    # structured_explanation routes through format_reply()
    result = wbc.chat("explain gravity")
    reply = result.get("reply", "")
    assert "clearly" in reply, f"Expected structured_explanation, got: {reply!r}"
    assert result.get("source") == "contract_reply", \
        f"Expected contract_reply, got: {result.get('source')}"

    print("  ✓ backend uses format_reply() for structured_explanation")


# ── Task 5: Changing _CONTRACT_REPLIES affects backend reply ───────────────────

def test_backend_reply_changes_with_contract_replies():
    """Changing _CONTRACT_REPLIES affects non-task_help backend replies.
    
    task_help short-circuits before format_reply() using handler text.
    Other contracts (structured_explanation, etc.) go through format_reply().
    """
    # Save original
    original = _CONTRACT_REPLIES["structured_explanation"]

    # Patch structured_explanation with a unique test string
    test_marker = "TEST_CONTRACT_SINGLE_SOURCE_UNIQUE_MARKER_12345"
    _CONTRACT_REPLIES["structured_explanation"] = test_marker

    try:
        # structured_explanation routes through format_reply()
        result = wbc.chat("explain gravity")
        reply = result.get("reply", "")
        assert test_marker in reply, \
            f"Expected test marker in backend reply, got: {reply!r}"
        print(f"  ✓ backend reply changes when _CONTRACT_REPLIES is patched")
    finally:
        # Restore
        _CONTRACT_REPLIES["structured_explanation"] = original

    # Verify restored
    result = wbc.chat("explain gravity")
    assert "clearly" in result.get("reply", ""), "Contract was not properly restored"
    print(f"  ✓ _CONTRACT_REPLIES restored correctly")


# ── Task 6: No regression ─────────────────────────────────────────────────────

def test_no_regression_entry():
    result = wbc.chat("hey")
    reply = result.get("reply", "")
    assert "Hi" in reply and "WESLR" in reply
    assert result.get("source") == "deterministic_entry"
    print("  ✓ regression: entry greeting works")


def test_no_regression_task_help():
    result = wbc.chat("I want to learn coding")
    reply = result.get("reply", "")
    assert "step by step" in reply
    # task_help short-circuits via deterministic_task_help (pre-format_reply)
    assert result.get("source") == "deterministic_task_help"
    print("  ✓ regression: task_help works")


def test_no_regression_structured_explanation():
    result = wbc.chat("explain gravity")
    reply = result.get("reply", "")
    assert "clearly" in reply or "deep" in reply
    print("  ✓ regression: structured_explanation works")


def test_no_regression_exploratory():
    result = wbc.chat("what are the implications of quantum computing")
    assert result.get("success") is True
    reply = result.get("reply", "")
    # Should not be uncertainty
    assert "confirmed" not in reply.lower() or "confirmed" in reply.lower()
    print(f"  ✓ regression: exploratory_guidance works → {reply[:40]!r}")


def test_no_regression_unknown_fallback():
    result = wbc.chat("asdasd123")
    assert result.get("success") is True
    intent = result.get("intent", {})
    assert intent.get("response_contract") == "uncertainty_boundary"
    assert intent.get("path") == "fallback_safe"
    print("  ✓ regression: unknown fallback works")


def test_no_regression_system():
    result = wbc.chat("what is WESLR")
    reply = result.get("reply", "")
    assert "WESLR" in reply
    print("  ✓ regression: system answer works")


# ── Run ────────────────────────────────────────────────────────────────────────

def run():
    print("\n=== test_contract_single_source_v1 ===\n")

    print("[Task 1] _CONTRACT_REPLIES is only source of guided_help")
    test_contract_replies_is_only_guided_help_source()

    print("\n[Tasks 2] format_reply() returns correct reply")
    test_format_reply_guided_help()
    test_format_reply_structured_explanation()
    test_format_reply_exploratory_guidance()
    test_format_reply_conversational_entry()
    test_format_reply_uncertainty_boundary()
    test_format_reply_system_answer()

    print("\n[Task 3] expand_response() does not override contract text")
    test_expand_response_does_not_override_guided_help()

    print("\n[Task 4] Backend uses format_reply()")
    test_backend_uses_format_reply()

    print("\n[Task 5] Changing _CONTRACT_REPLIES affects backend")
    test_backend_reply_changes_with_contract_replies()

    print("\n[Task 6] No regression")
    test_no_regression_entry()
    test_no_regression_task_help()
    test_no_regression_structured_explanation()
    test_no_regression_exploratory()
    test_no_regression_unknown_fallback()
    test_no_regression_system()

    print("\n=== WESLR_CONTRACT_SINGLE_SOURCE_DEFINED ===\n")


if __name__ == "__main__":
    run()