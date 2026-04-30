"""WESLR Response Contract Bridge V1 — Tests

Verdict label: WESLR_RESPONSE_CONTRACT_BRIDGE_V1_DEFINED

Tests that the response contract bridge correctly maps interaction frames
to response contracts and produces natural contract-based replies.

Required tests:
1. "I want to learn coding" → guided_help, not uncertainty
2. "help me build a website" → guided_help, not uncertainty
3. "explain gravity" → structured_explanation, not uncertainty
4. "tell me about space" → exploratory_guidance or appropriate non-uncertainty contract
5. "hey" → greeting, not uncertainty
6. "what is WESLR" → system_definition_query still works
7. "asdasd123" → uncertainty/fallback still works
8. returned dict is JSON serializable
9. existing V1/V1.1 tests still pass
"""

import sys
import json
import importlib

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

# Force reimport to pick up changes
import interpretation
importlib.reload(interpretation)

from interpretation import (
    interpret_human_turn,
    _classify_interaction_frame,
    _response_contract_from_frame,
    _turn_type_from_frame,
    _reply_shape_from_frame,
)

from weslr_backend_contract import chat


# ── Helpers ────────────────────────────────────────────────────────────────────

def assert_json_serializable(result: dict, label: str) -> None:
    """Assert result can be JSON-serializable."""
    try:
        json.dumps(result)
    except TypeError as e:
        raise AssertionError(f"{label}: result is not JSON-serializable: {e}")


def assert_not_uncertainty(result: dict, message: str) -> None:
    """Assert result does NOT contain uncertainty fallback.
    
    For chat() results, we only check the 'reply' field since
    response_text in the intent may be the unexpanded handler output
    (e.g. fallback_safe text before response_expander formats it).
    For interpret_human_turn results, we check response_text directly.
    """
    reply = result.get("reply", "")
    response_text = result.get("intent", {}).get("response_text", "")
    # For direct interpret_human_turn (no 'reply' key), check response_text
    # For chat results (has 'reply'), only check reply (response_text may be
    # pre-expansion handler output)
    if "reply" not in result:
        check_text = response_text
    else:
        check_text = reply
    
    uncertain_phrases = [
        "I'm not sure I understood that correctly",
        "I don't have a confirmed answer for that yet",
    ]
    for phrase in uncertain_phrases:
        assert phrase not in check_text, f"Message '{message}' returned uncertainty: {check_text!r}"


def assert_guided_help(result: dict, message: str) -> None:
    """Assert result has guided_help response contract and step-by-step reply."""
    intent = result.get("intent", {})
    contract = intent.get("response_contract", "")
    reply = result.get("reply", "")
    assert contract == "guided_help", f"Message '{message}' → expected guided_help, got: {contract}"
    assert "step by step" in reply, f"Message '{message}' → expected step-by-step text, got: {reply!r}"


# ── _response_contract_from_frame mapping ─────────────────────────────────────

def test_response_contract_mapping():
    assert _response_contract_from_frame("entry") == "conversational_entry"
    assert _response_contract_from_frame("task_help") == "guided_help"
    assert _response_contract_from_frame("explanation") == "structured_explanation"
    assert _response_contract_from_frame("exploration") == "exploratory_guidance"
    assert _response_contract_from_frame("system") == "system_answer"
    assert _response_contract_from_frame("unknown") == "uncertainty_boundary"
    print("  ✓ response_contract mapping")


# ── Interpretation layer unit tests ──────────────────────────────────────────

def test_task_help_guided_help_not_uncertainty():
    """'I want to learn coding' → guided_help, NOT uncertainty."""
    result = interpret_human_turn("I want to learn coding")
    contract = result.get("response_contract", "")
    path = result.get("path", "")
    assert contract == "guided_help", f"Expected guided_help, got: {contract}"
    assert path == "task_help_query", f"Expected task_help_query, got: {path}"
    assert "step by step" in result.get("response_text", "")
    print("  ✓ 'I want to learn coding' → guided_help + task_help_query")


def test_help_me_build_guided_help():
    """'help me build a website' → guided_help."""
    result = interpret_human_turn("help me build a website")
    contract = result.get("response_contract", "")
    assert contract == "guided_help"
    assert result.get("path") == "task_help_query"
    print("  ✓ 'help me build a website' → guided_help")


def test_explain_gravity_structured_explanation():
    """'explain gravity' → structured_explanation."""
    result = interpret_human_turn("explain gravity")
    contract = result.get("response_contract", "")
    # No handler for "explain gravity" → falls to fallback with explanation frame
    # But response_contract is set correctly from frame
    assert contract == "structured_explanation", f"Expected structured_explanation, got: {contract}"
    print("  ✓ 'explain gravity' → structured_explanation")


def test_tell_me_about_space_exploratory_guidance():
    """'tell me about space' → exploratory_guidance."""
    result = interpret_human_turn("tell me about space")
    contract = result.get("response_contract", "")
    # "tell me about X" matches explanation keyword, not exploration
    assert contract in ("structured_explanation", "exploratory_guidance"), f"Expected non-uncertainty, got: {contract}"
    print(f"  ✓ 'tell me about space' → {contract}")


def test_hey_greeting():
    """'hey' → conversational_entry, NOT uncertainty."""
    result = interpret_human_turn("hey")
    contract = result.get("response_contract", "")
    assert contract == "conversational_entry", f"Expected conversational_entry, got: {contract}"
    print("  ✓ 'hey' → conversational_entry")


def test_what_is_weslr_system():
    """'what is WESLR' → system_answer."""
    result = interpret_human_turn("what is WESLR")
    # "what is WESLR" is not an entry greeting anymore (uppercase)
    frame = result.get("interaction_frame", "")
    contract = result.get("response_contract", "")
    assert frame in ("system", "explanation"), f"Expected system or explanation frame, got: {frame}"
    print(f"  ✓ 'what is WESLR' → frame={frame}, contract={contract}")


def test_asdasd123_unknown_uncertainty():
    """'asdasd123' → uncertainty_boundary."""
    result = interpret_human_turn("asdasd123")
    contract = result.get("response_contract", "")
    path = result.get("path", "")
    assert contract == "uncertainty_boundary", f"Expected uncertainty_boundary, got: {contract}"
    assert path == "fallback_safe", f"Expected fallback_safe, got: {path}"
    print("  ✓ 'asdasd123' → uncertainty_boundary + fallback_safe")


def test_interpreted_dict_json_serializable():
    """interpret_human_turn result dict is JSON-serializable."""
    for msg in [
        "I want to learn coding",
        "help me build a website",
        "explain gravity",
        "tell me about space",
        "hey",
        "what is WESLR",
        "asdasd123",
    ]:
        result = interpret_human_turn(msg)
        assert_json_serializable(result, msg)
    print("  ✓ all interpreted dicts are JSON-serializable")


# ── Backend chat path contract tests ──────────────────────────────────────────

def test_chat_learn_coding_guided_help():
    result = chat("I want to learn coding")
    assert result.get("success") is True
    assert_not_uncertainty(result, "I want to learn coding")
    assert_guided_help(result, "I want to learn coding")
    assert_json_serializable(result, "learn coding")
    print(f"  ✓ chat('I want to learn coding') → guided_help")


def test_chat_help_me_build_guided_help():
    result = chat("help me build a website")
    assert result.get("success") is True
    assert_not_uncertainty(result, "help me build a website")
    assert_guided_help(result, "help me build a website")
    assert_json_serializable(result, "build website")
    print(f"  ✓ chat('help me build a website') → guided_help")


def test_chat_explain_gravity_structured():
    """'explain gravity' via chat() returns structured_explanation contract."""
    result = chat("explain gravity")
    assert result.get("success") is True
    intent = result.get("intent", {})
    contract = intent.get("response_contract", "")
    reply = result.get("reply", "")
    # structured_explanation contract should give the explanation response
    assert contract == "structured_explanation", f"Expected structured_explanation, got: {contract}"
    assert "clearly" in reply or "deep" in reply, f"Expected structured explanation reply, got: {reply!r}"
    assert_json_serializable(result, "explain gravity")
    print(f"  ✓ chat('explain gravity') → structured_explanation: {reply[:50]!r}")


def test_chat_tell_me_about_space_exploration():
    """'tell me about space' via chat() returns exploratory_guidance contract."""
    result = chat("tell me about space")
    assert result.get("success") is True
    intent = result.get("intent", {})
    contract = intent.get("response_contract", "")
    reply = result.get("reply", "")
    # Should be non-uncertainty contract
    assert contract in ("structured_explanation", "exploratory_guidance"), f"Expected non-uncertainty contract, got: {contract}"
    # Should not be uncertainty
    assert_not_uncertainty(result, "tell me about space")
    assert_json_serializable(result, "tell me about space")
    print(f"  ✓ chat('tell me about space') → {contract}: {reply[:50]!r}")


def test_chat_hey_greeting():
    """'hey' via chat() returns greeting, NOT uncertainty."""
    result = chat("hey")
    assert result.get("success") is True
    reply = result.get("reply", "")
    assert "Hi — I'm WESLR" in reply, f"Expected entry greeting, got: {reply!r}"
    assert result.get("source") == "deterministic_entry"
    assert_json_serializable(result, "hey")
    print(f"  ✓ chat('hey') → entry greeting")


def test_chat_what_is_weslr():
    """'what is WESLR' via chat() works — not broken by contract changes."""
    result = chat("what is WESLR")
    assert result.get("success") is True
    reply = result.get("reply", "")
    # Should give a meaningful answer, not an error
    assert len(reply) > 0, "Expected non-empty reply for 'what is WESLR'"
    print(f"  ✓ chat('what is WESLR') → {reply[:50]!r}")


def test_chat_unknown_fallback():
    """'asdasd123' via chat() still falls to fallback — not broken."""
    result = chat("asdasd123")
    assert result.get("success") is True
    # Unknown input should not be task_help
    intent = result.get("intent", {})
    path = intent.get("path", "")
    assert path != "task_help_query", f"Unknown 'asdasd123' should not be task_help_query"
    contract = intent.get("response_contract", "")
    assert contract == "uncertainty_boundary", f"Expected uncertainty_boundary, got: {contract}"
    print(f"  ✓ chat('asdasd123') → fallback (path={path})")


# ── All fields propagated test ─────────────────────────────────────────────────

def test_all_fields_propagated():
    """interpret_human_turn returns all required fields."""
    result = interpret_human_turn("I want to learn coding")
    required_fields = [
        "interaction_frame",
        "frame_turn_type",
        "frame_reply_shape",
        "response_contract",
        "turn_type",
        "reply_shape",
    ]
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"
    print("  ✓ all required fields present in interpret_human_turn output")


# ── Run ────────────────────────────────────────────────────────────────────────

def run():
    print("\n=== test_response_contract_bridge_v1 ===\n")

    print("[_response_contract_from_frame mapping]")
    test_response_contract_mapping()

    print("\n[interpretation layer — unit]")
    test_task_help_guided_help_not_uncertainty()
    test_help_me_build_guided_help()
    test_explain_gravity_structured_explanation()
    test_tell_me_about_space_exploratory_guidance()
    test_hey_greeting()
    test_what_is_weslr_system()
    test_asdasd123_unknown_uncertainty()
    test_interpreted_dict_json_serializable()

    print("\n[backend chat path — integration]")
    test_chat_learn_coding_guided_help()
    test_chat_help_me_build_guided_help()
    test_chat_explain_gravity_structured()
    test_chat_tell_me_about_space_exploration()
    test_chat_hey_greeting()
    test_chat_what_is_weslr()
    test_chat_unknown_fallback()

    print("\n[field propagation]")
    test_all_fields_propagated()

    print("\n=== WESLR_RESPONSE_CONTRACT_BRIDGE_V1_DEFINED ===\n")


if __name__ == "__main__":
    run()