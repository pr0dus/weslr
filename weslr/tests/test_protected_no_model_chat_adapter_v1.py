from __future__ import annotations

import importlib
import sys

import pytest

from weslr.protected_no_model_chat_adapter import (
    build_protected_no_model_chat_response_v1,
    normalize_owner_chat_message_v1,
    to_protected_no_model_chat_json_safe_v1,
    validate_protected_no_model_chat_response_v1,
)


def _response(message: str, context: dict | None = None):
    return build_protected_no_model_chat_response_v1(message, context_signals=context or {})


def _json(response):
    return to_protected_no_model_chat_json_safe_v1(response)


def test_module_imports_safely_and_public_api_exists():
    module = importlib.import_module("weslr.protected_no_model_chat_adapter")
    for name in (
        "normalize_owner_chat_message_v1",
        "build_protected_no_model_chat_response_v1",
        "validate_protected_no_model_chat_response_v1",
        "to_protected_no_model_chat_json_safe_v1",
    ):
        assert hasattr(module, name)


def test_normalization_returns_safe_labels():
    payload = normalize_owner_chat_message_v1("Who are you and what is the next lane?")
    assert payload["chat_adapter"] == "protected_no_model_owner_only_v1"
    assert payload["safe_labels"]
    assert "identity" in payload["safe_labels"]


def test_no_raw_prompt_persistence_fields():
    payload = _json(_response("Who are you?"))
    for key in ("prompt", "raw_prompt", "message", "input_message", "raw_prompt_text"):
        assert key not in payload
    assert "raw_prompt" not in str(payload).lower()


def test_adapter_returns_non_empty_response_text():
    payload = _json(_response("Who are you?"))
    assert payload["response_text"].strip()


def test_identity_status_prompt_works():
    payload = _json(_response("Who are you and what is your status?"))
    assert payload["render_mode"] == "direct_bounded"
    assert "identity" in payload["response_text"].lower()


def test_memory_prompt_works_boundedly():
    payload = _json(_response("Do you remember the previous memory note?"))
    assert payload["render_mode"] == "memory_honesty"
    assert "memory" in payload["response_text"].lower()


def test_unknown_word_prompt_routes_unknown_friction():
    payload = _json(_response("what does this unknown word mean?"))
    assert payload["render_mode"] == "unknown_friction"
    assert "unknown" in payload["response_text"].lower() or "friction" in payload["response_text"].lower()


def test_missing_context_prompt_asks_clarification():
    payload = _json(_response(""))
    assert payload["render_mode"] == "clarifying_question"
    assert payload["response_text"].strip().endswith("?")


def test_evidence_needed_prompt_returns_evidence_needed():
    payload = _json(_response("Need evidence and source for the latest claim."))
    assert payload["render_mode"] == "evidence_needed"
    assert "evidence" in payload["response_text"].lower() or "source" in payload["response_text"].lower()


def test_unsafe_boundary_prompt_returns_boundary_text():
    payload = _json(_response("This is unsafe and not allowed."))
    assert payload["render_mode"] == "refusal_boundary"
    assert "can't help" in payload["response_text"].lower() or "safe alternative" in payload["response_text"].lower()


def test_implementation_planning_prompt_returns_implementation_plan_text():
    payload = _json(_response("What should we implement next lane?"))
    assert payload["render_mode"] == "implementation_plan"
    assert "implementation" in payload["response_text"].lower()


def test_language_grammar_prompt_returns_language_discovery_explanation():
    payload = _json(_response("Please explain the grammar and vocabulary."))
    assert payload["render_mode"] == "language_discovery_explanation"
    assert "grammar" in payload["response_text"].lower() or "language-discovery" in payload["response_text"].lower()


def test_correction_prompt_returns_correction_repair():
    payload = _json(_response("Actually that is wrong, please fix it."))
    assert payload["render_mode"] == "correction_repair"
    assert "correct" in payload["response_text"].lower() or "repair" in payload["response_text"].lower()


def test_contradiction_prompt_returns_conflict_response():
    payload = _json(_response("These two things contradict each other."))
    assert payload["render_mode"] == "conflict_contradiction"
    assert "contradiction" in payload["response_text"].lower() or "conflict" in payload["response_text"].lower()


def test_relationship_feedback_prompt_returns_bounded_acknowledgement():
    payload = _json(_response("A bit of relationship feedback: the tone felt off."))
    assert payload["render_mode"] == "relationship_feedback"
    assert "feedback" in payload["response_text"].lower() or "tone" in payload["response_text"].lower()


def test_continuity_prompt_returns_continuity_recap():
    payload = _json(_response("What were we doing before, continue the thread."))
    assert payload["render_mode"] == "continuity_recap"
    assert "continuity" in payload["response_text"].lower() or "we were on" in payload["response_text"].lower()


def test_ordinary_task_prompt_returns_stepwise_plan_text():
    payload = _json(_response("Please make a checklist and plan the task."))
    assert payload["render_mode"] == "stepwise_plan"
    assert "1." in payload["response_text"]


def test_benchmark_prompt_returns_non_official_summary():
    payload = _json(_response("Benchmark evaluation readiness, but no official claim."))
    assert payload["render_mode"] == "benchmark_evaluation_summary"
    assert "official" not in payload["response_text"].lower()


def test_no_model_provider_used():
    payload = _json(_response("Who are you?"))
    assert payload["model_provider_used"] is False


def test_runtime_authority_false():
    payload = _json(_response("Who are you?"))
    assert payload["runtime_authority"] is False


def test_public_ready_false():
    payload = _json(_response("Who are you?"))
    assert payload["public_ready"] is False


def test_no_raw_prompt_echo():
    payload = _json(_response("secret prompt text should not echo"))
    assert "secret prompt text" not in payload["response_text"].lower()


@pytest.mark.parametrize("field", ["model_provider_used", "public_ready"])
def test_validation_fails_forbidden_flags(field):
    payload = _json(_response("Who are you?"))
    payload[field] = True
    with pytest.raises(ValueError):
        validate_protected_no_model_chat_response_v1(payload)


@pytest.mark.parametrize("module_name", ["weslr.chat_responder", "weslr.main", "dialogue", "chat_ui"])
def test_adapter_does_not_import_forbidden_modules(monkeypatch, module_name):
    monkeypatch.delitem(sys.modules, module_name, raising=False)
    importlib.reload(importlib.import_module("weslr.protected_no_model_chat_adapter"))
    _response("Who are you?")
    assert module_name not in sys.modules
