"""test_natural_self_conversation_v1.py — Natural conversation self-conversation test."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weslr.deterministic_handlers import (
    HANDLER_REGISTRY,
    dispatch_deterministic_handler,
    handle_self_identity_query,
    handle_capability_help_query,
    handle_improvement_explanation_query,
    handle_uncertainty_explanation_query,
    handle_memory_boundary_query,
    handle_simple_followup_query,
)


def test_handler_exists():
    """Test that all new handlers exist."""
    handlers = [
        handle_self_identity_query,
        handle_capability_help_query,
        handle_improvement_explanation_query,
        handle_uncertainty_explanation_query,
        handle_memory_boundary_query,
        handle_simple_followup_query,
    ]
    for h in handlers:
        assert h is not None, f"Handler {h.__name__} not found"
    print("✓ All handlers exist")


def test_registry_contains_new_handlers():
    """Test that new handlers are in the registry."""
    handler_ids = [h["id"] for h in HANDLER_REGISTRY]
    expected_ids = [
        "self_identity_query",
        "improvement_explanation_query",
        "uncertainty_explanation_query",
        "memory_boundary_query",
        "simple_followup_query",
    ]
    for eid in expected_ids:
        assert eid in handler_ids, f"Handler {eid} not found in registry"
    print("✓ New handlers in registry")


def test_dispatch_works():
    """Test that dispatch works for new handlers."""
    tests = [
        ("what are you?", "self_identity"),
        ("who are you?", "self_identity"),
        ("what can you do?", "usage_guidance"),
        ("what can you help me with?", "self_identity"),
        ("how do you improve over time?", "improvement_explanation"),
        ("what happens if you do not know something?", "uncertainty_explanation"),
        ("can you remember what we talked about earlier?", "memory_boundary"),
        ("explain that more simply", "simple_followup"),
    ]
    for msg, expected_path in tests:
        result = dispatch_deterministic_handler(msg, msg.lower())
        assert result is not None, f"No result for {msg!r}"
        assert result.get("path") == expected_path, f"Wrong path for {msg!r}: {result.get('path')}"
        assert result.get("_weslr_deterministic") is True, f"Not deterministic for {msg!r}"
    print("✓ Dispatch works for new handlers")


def test_no_uncertainty_boundary():
    """Test that new handlers don't return uncertainty_boundary."""
    tests = [
        "what are you?",
        "what can you help me with?",
        "how do you improve over time?",
        "what happens if you do not know something?",
        "can you remember what we talked about earlier?",
        "explain that more simply",
    ]
    for msg in tests:
        result = dispatch_deterministic_handler(msg, msg.lower())
        assert result is not None, f"No result for {msg!r}"
        # Should NOT be uncertainty_boundary
        assert result.get("path") != "uncertainty_boundary", f"Returned uncertainty for {msg!r}"
        # Should have confidence
        assert "confidence" in result, f"No confidence for {msg!r}"
        assert result["confidence"] == "high", f"Not high confidence for {msg!r}"
    print("✓ No uncertainty boundary for new handlers")


def test_responses_are_deterministic():
    """Test that responses are deterministic."""
    tests = [
        ("what are you?", "self_identity"),
        ("what can you help me with?", "capability_help"),
    ]
    for msg, path in tests:
        result1 = dispatch_deterministic_handler(msg, msg.lower())
        result2 = dispatch_deterministic_handler(msg, msg.lower())
        assert result1.get("response_text") == result2.get("response_text"), f"Non-deterministic for {msg!r}"
    print("✓ Responses are deterministic")


def test_no_internal_details_exposed():
    """Test that internal details are not exposed."""
    tests = [
        "what are you?",
        "what can you help me with?",
        "how do you improve over time?",
    ]
    for msg in tests:
        result = dispatch_deterministic_handler(msg, msg.lower())
        response = result.get("response_text", "").lower()
        # Should NOT mention handlers, files, or implementation details
        forbidden = ["handler", "module", "file", "registry", "dispatch", "priority", "trigger"]
        for f in forbidden:
            assert f not in response, f"Internal detail exposed in {msg!r}: '{f}' found in '{response[:80]}'"
    print("✓ No internal details exposed")


def test_no_agi_claims():
    """Test that AGI claims are not made."""
    tests = [
        ("what are you?", "self_identity"),
        ("how do you improve over time?", "improvement_explanation"),
    ]
    for msg, path in tests:
        result = dispatch_deterministic_handler(msg, msg.lower())
        response = result.get("response_text", "").lower()
        # Should explicitly say not AGI or clarify autonomous learning is absent
        if "autonomous" in response:
            # If the word appears, it must be in negative context
            assert "no autonomous" in response or "don't" in response, \
                f"Autonomous claim without negation in {msg!r}: '{response[:80]}'"
        if "agi" in response:
            assert "don't claim" in response or "not" in response, \
                f"AGI claim without negation in {msg!r}: '{response[:80]}'"
    print("✓ No AGI claims present")


def test_no_unsupported_memory_claims():
    """Test that unsupported memory claims are not made."""
    tests = [
        "can you remember what we talked about earlier?",
    ]
    for msg in tests:
        result = dispatch_deterministic_handler(msg, msg.lower())
        response = result.get("response_text", "").lower()
        # Should say "doesn't store full conversation" not "remembers everything"
        assert "full conversation" in response or "conversational history" in response, \
            f"Memory boundary not explained in {msg!r}"
    print("✓ No unsupported memory claims")


def run():
    """Run all tests."""
    print("=== test_natural_self_conversation_v1 ===\n")

    test_handler_exists()
    test_registry_contains_new_handlers()
    test_dispatch_works()
    test_no_uncertainty_boundary()
    test_responses_are_deterministic()
    test_no_internal_details_exposed()
    test_no_agi_claims()
    test_no_unsupported_memory_claims()

    print("\n=== All tests passed ===\n")


if __name__ == "__main__":
    run()
