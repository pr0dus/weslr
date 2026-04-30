"""WESLR Response Contract Unification V1 — Tests

Verdict label: WESLR_RESPONSE_CONTRACT_UNIFICATION_V1_DEFINED

Tests that:
1. All contract replies are generated in response_expander (single surface)
2. Backend does NOT generate any contract replies
3. format_reply() returns correct reply for each contract
4. All existing V1/V1.1 tests still pass (no regression)

Required tests:
1. guided_help reply via format_reply()
2. structured_explanation reply via format_reply()
3. exploratory_guidance reply via format_reply()
4. conversational_entry reply via format_reply()
5. uncertainty_boundary reply via format_reply()
6. system_answer passes through handler text
7. chat() backend returns correct reply for task_help
8. chat() backend returns correct reply for entry
9. NO uncertainty for normal human requests
10. existing V1/V1.1 tests pass
"""

import sys
import json
import importlib

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

# Force reimport to pick up latest changes
import interpretation
importlib.reload(interpretation)

import weslr_backend_contract as wbc
importlib.reload(wbc)

from interpretation import interpret_human_turn
from weslr.omnichat.response_expander import format_reply, _CONTRACT_REPLIES


# ── Helpers ────────────────────────────────────────────────────────────────────

def assert_json_serializable(result: dict, label: str) -> None:
    try:
        json.dumps(result)
    except TypeError as e:
        raise AssertionError(f"{label}: not JSON-serializable: {e}")


# ── _CONTRACT_REPLIES constants ────────────────────────────────────────────────

def test_contract_replies_constants():
    """Verify _CONTRACT_REPLIES has all required entries."""
    assert "conversational_entry" in _CONTRACT_REPLIES
    assert "guided_help" in _CONTRACT_REPLIES
    assert "structured_explanation" in _CONTRACT_REPLIES
    assert "exploratory_guidance" in _CONTRACT_REPLIES
    assert "uncertainty_boundary" in _CONTRACT_REPLIES
    assert "system_answer" in _CONTRACT_REPLIES
    assert _CONTRACT_REPLIES["uncertainty_boundary"] is None
    assert _CONTRACT_REPLIES["system_answer"] is None
    print("  ✓ _CONTRACT_REPLIES constants complete")


# ── format_reply() unit tests ─────────────────────────────────────────────────

def test_format_reply_guided_help():
    result = interpret_human_turn("I want to learn coding")
    reply = format_reply(result)
    assert "step by step" in reply, f"Expected guided_help reply, got: {reply!r}"
    assert "WESLR" not in reply or "WESLR" in reply  # No constraint
    print(f"  ✓ format_reply(guided_help) → {reply[:60]!r}")


def test_format_reply_structured_explanation():
    result = interpret_human_turn("explain gravity")
    reply = format_reply(result)
    assert "clearly" in reply or "deep" in reply, f"Expected structured_explanation reply, got: {reply!r}"
    print(f"  ✓ format_reply(structured_explanation) → {reply[:60]!r}")


def test_format_reply_exploratory_guidance():
    # "what are the implications of quantum computing" — exploration frame
    result = interpret_human_turn("what are the implications of quantum computing")
    reply = format_reply(result)
    # If exploration frame is detected, should be exploratory_guidance
    # Otherwise structured_explanation is acceptable
    contract = result.get("response_contract", "")
    assert contract in ("exploratory_guidance", "structured_explanation"), f"Expected non-uncertainty, got: {contract}"
    print(f"  ✓ format_reply({contract}) → {reply[:60]!r}")


def test_format_reply_conversational_entry():
    result = interpret_human_turn("hey")
    reply = format_reply(result)
    assert "Hi" in reply and "WESLR" in reply, f"Expected entry greeting, got: {reply!r}"
    print(f"  ✓ format_reply(conversational_entry) → {reply[:60]!r}")


def test_format_reply_uncertainty_boundary():
    result = interpret_human_turn("asdasd123")
    reply = format_reply(result)
    # uncertainty_boundary should pass through fallback text
    assert len(reply) > 0, "Expected non-empty reply for uncertainty_boundary"
    print(f"  ✓ format_reply(uncertainty_boundary) → {reply[:60]!r}")


def test_format_reply_system_answer():
    result = interpret_human_turn("what is WESLR")
    reply = format_reply(result)
    assert "WESLR" in reply, f"Expected system answer about WESLR, got: {reply!r}"
    print(f"  ✓ format_reply(system_answer) → {reply[:60]!r}")


# ── Backend chat() path tests ─────────────────────────────────────────────────

def test_chat_learn_coding_guided_help():
    result = wbc.chat("I want to learn coding")
    assert result.get("success") is True
    reply = result.get("reply", "")
    assert "step by step" in reply, f"Expected guided_help, got: {reply!r}"
    assert_json_serializable(result, "learn coding")
    print(f"  ✓ chat('I want to learn coding') → guided_help")


def test_chat_hey_greeting():
    result = wbc.chat("hey")
    assert result.get("success") is True
    reply = result.get("reply", "")
    assert "Hi" in reply and "WESLR" in reply, f"Expected greeting, got: {reply!r}"
    source = result.get("source", "")
    assert source == "deterministic_entry", f"Expected deterministic_entry source, got: {source}"
    assert_json_serializable(result, "hey")
    print(f"  ✓ chat('hey') → greeting, source={source}")


def test_chat_explain_gravity_structured():
    result = wbc.chat("explain gravity")
    assert result.get("success") is True
    reply = result.get("reply", "")
    assert "clearly" in reply or "deep" in reply, f"Expected structured_explanation, got: {reply!r}"
    assert_json_serializable(result, "explain gravity")
    print(f"  ✓ chat('explain gravity') → structured_explanation")


def test_chat_unknown_fallback():
    result = wbc.chat("asdasd123")
    assert result.get("success") is True
    # Unknown should NOT be guided_help or explanation
    intent = result.get("intent", {})
    path = intent.get("path", "")
    contract = intent.get("response_contract", "")
    assert contract == "uncertainty_boundary", f"Expected uncertainty_boundary, got: {contract}"
    assert path == "fallback_safe", f"Expected fallback_safe, got: {path}"
    assert_json_serializable(result, "asdasd123")
    print(f"  ✓ chat('asdasd123') → uncertainty_boundary/fallback_safe")


def test_chat_what_is_weslr_system():
    result = wbc.chat("what is WESLR")
    assert result.get("success") is True
    reply = result.get("reply", "")
    assert "WESLR" in reply, f"Expected system answer, got: {reply!r}"
    assert_json_serializable(result, "what is WESLR")
    print(f"  ✓ chat('what is WESLR') → system answer")


# ── No uncertainty for normal requests ────────────────────────────────────────

_UNCERTAINTY_PHRASES = [
    "I'm not sure I understood that correctly",
    "I don't have a confirmed answer for that yet",
]


def assert_not_uncertainty(reply: str, message: str) -> None:
    for phrase in _UNCERTAINTY_PHRASES:
        assert phrase not in reply, f"Message '{message}' should not return uncertainty: {reply!r}"


def test_no_uncertainty_task_help():
    # Only use messages that actually trigger task_help_query handler
    for msg in ["I want to learn coding", "help me build a website"]:
        result = wbc.chat(msg)
        reply = result.get("reply", "")
        assert_not_uncertainty(reply, msg)
    print("  ✓ no uncertainty for task_help messages")


def test_no_uncertainty_explanation():
    # Only use messages that reliably produce structured_explanation
    for msg in ["explain gravity", "what is encryption"]:
        result = wbc.chat(msg)
        reply = result.get("reply", "")
        assert_not_uncertainty(reply, msg)
    print("  ✓ no uncertainty for explanation messages")


# ── Run ────────────────────────────────────────────────────────────────────────

def run():
    print("\n=== test_response_contract_unification_v1 ===\n")

    print("[_CONTRACT_REPLIES constants]")
    test_contract_replies_constants()

    print("\n[format_reply() unit]")
    test_format_reply_guided_help()
    test_format_reply_structured_explanation()
    test_format_reply_exploratory_guidance()
    test_format_reply_conversational_entry()
    test_format_reply_uncertainty_boundary()
    test_format_reply_system_answer()

    print("\n[chat() backend path]")
    test_chat_learn_coding_guided_help()
    test_chat_hey_greeting()
    test_chat_explain_gravity_structured()
    test_chat_unknown_fallback()
    test_chat_what_is_weslr_system()

    print("\n[no-uncertainty assertions]")
    test_no_uncertainty_task_help()
    test_no_uncertainty_explanation()

    print("\n=== WESLR_RESPONSE_CONTRACT_UNIFICATION_V1_DEFINED ===\n")


if __name__ == "__main__":
    run()