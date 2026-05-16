"""Focused tests for meaning/obligation/state native reuse helpers V1."""

import copy
from pathlib import Path

from weslr.linguistic_meaning import analyze_meaning
from weslr.meaning_response_reuse import (
    build_compact_meaning_payload_v1,
    build_compact_meaning_state_context_bundle_v1,
    build_compact_response_obligation_payload_v1,
    build_native_frame_inputs_from_meaning_reuse_v1,
    derive_known_and_missing_context_from_meaning_state_v1,
    to_meaning_response_reuse_json_safe_v1,
    validate_meaning_response_reuse_payload_v1,
)
from weslr.meaning_state_context import gather_meaning_state
from weslr.native_reasoning_frame import build_native_reasoning_frame_v1
from weslr.response_obligation import determine_response_obligation


def _assert_no_raw_prompt_fields(payload):
    rendered = repr(payload)
    assert "raw_text" not in payload
    assert "normalized_text" not in payload
    assert "tokens" not in payload
    assert "What are you?" not in rendered


def test_compact_meaning_payload_omits_raw_text_and_validates_safe():
    meaning = analyze_meaning("What are you?")

    payload = build_compact_meaning_payload_v1(meaning)

    assert payload["payload_type"] == "compact_meaning_payload_v1"
    assert payload["primary_speech_act"]
    assert payload["primary_state_query"]
    assert isinstance(payload["confidence"], float)
    assert isinstance(payload["ambiguity"], float)
    assert payload["raw_text_included"] is False
    assert payload["normalized_text_included"] is False
    _assert_no_raw_prompt_fields(payload)
    assert validate_meaning_response_reuse_payload_v1(payload)["valid"] is True


def test_compact_obligation_payload_omits_raw_prompt_and_validates_safe():
    meaning = analyze_meaning("What are you?")
    obligation = determine_response_obligation(meaning)

    payload = build_compact_response_obligation_payload_v1(obligation)

    assert payload["payload_type"] == "compact_response_obligation_payload_v1"
    assert payload["obligation_type"]
    assert isinstance(payload["required_state"], list)
    assert "should_answer_bounded" in payload
    assert "should_ask_clarifying" in payload
    assert "What are you?" not in repr(payload)
    assert validate_meaning_response_reuse_payload_v1(payload)["valid"] is True


def test_compact_state_context_bundle_includes_summaries_without_writes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    meaning = analyze_meaning("What are you?")
    obligation = determine_response_obligation(meaning)
    state_context = gather_meaning_state(obligation)

    payload = build_compact_meaning_state_context_bundle_v1(state_context)

    assert payload["payload_type"] == "compact_meaning_state_context_bundle_v1"
    assert "known_user_status" in payload
    assert "memory_available" in payload
    assert "capability_summary" in payload
    assert "self_model_summary" in payload
    assert "sources_used" in payload
    assert payload["raw_private_text_stored"] is False
    assert payload["writes_performed"] is False
    assert not (tmp_path / ".weslr").exists()
    assert validate_meaning_response_reuse_payload_v1(payload)["valid"] is True


def test_known_missing_context_derivation_identity_memory_self_and_capability():
    compact_meaning = {
        "payload_type": "compact_meaning_payload_v1",
        "required_state": ["identity_state", "memory_state", "self_model", "capability_model"],
    }
    compact_obligation = {
        "payload_type": "compact_response_obligation_payload_v1",
        "required_state": ["identity_state", "memory_state", "self_model", "capability_model"],
        "identity_verification_required": True,
        "memory_evidence_required": True,
    }
    compact_state = {
        "payload_type": "compact_meaning_state_context_bundle_v1",
        "known_user_status": "unknown",
        "sender_confidence": 0.0,
        "memory_available": False,
        "memory_sources_checked": [],
        "memory_access_limitations": [],
        "self_model_summary": "WESLR operational self-model summary",
        "capability_summary": "WESLR capability summary",
        "sources_used": ["SOUL.md", "default_capability"],
    }

    derived = derive_known_and_missing_context_from_meaning_state_v1(
        compact_meaning,
        compact_obligation,
        compact_state,
    )

    assert "verified identity context" in derived["missing_context"]
    assert "verified memory context" in derived["missing_context"]
    assert {item["kind"] for item in derived["known_context"]} >= {"self_model_summary", "capability_summary"}
    assert derived["raw_text_stored"] is False
    assert derived["identity_status"]["known_user_status"] == "unknown"


def test_native_frame_compatibility_from_reuse_inputs():
    meaning = analyze_meaning("What are you?")
    obligation = determine_response_obligation(meaning)
    state_context = gather_meaning_state(obligation)

    inputs = build_native_frame_inputs_from_meaning_reuse_v1(meaning, obligation, state_context)
    native_kwargs = {
        key: inputs[key]
        for key in (
            "meaning_vector_result",
            "response_obligation_result",
            "selected_context_bundle",
            "known_context",
            "missing_context",
            "memory_context_hints",
            "self_model_or_identity_status",
            "capability_boundary_result",
            "provenance_refs",
        )
    }
    frame = build_native_reasoning_frame_v1(request_summary="self model question", **native_kwargs)

    assert frame["frame_type"] == "native_reasoning_frame_v1"
    assert inputs["safe_to_wire_runtime"] is False
    assert inputs["raw_text_stored"] is False
    assert "What are you?" not in repr(inputs)
    assert inputs["meaning_vector_result"]["raw_text_included"] is False
    assert inputs["meaning_vector_result"]["normalized_text_included"] is False
    assert validate_meaning_response_reuse_payload_v1(inputs)["valid"] is True


def test_validation_rejects_forbidden_payload_shapes_and_markers():
    invalid_cases = [
        {"raw_text": "private"},
        {"normalized_text": "private"},
        {"tokens": ["private"]},
        {"note": "hidden prompt"},
        {"note": "answer key"},
        {"note": "protected material"},
        {"note": "official IQ score"},
        {"note": "I am sentient"},
        {"model_calls": True},
        {"advisor_calls": True},
        {"web_search": True},
        {"solver_execution": True},
        {"answer_selection_arbitration": True},
        {"writes_performed": True},
        {"safe_to_wire_runtime": True},
    ]

    for payload in invalid_cases:
        result = validate_meaning_response_reuse_payload_v1(payload)
        assert result["valid"] is False
        assert result["violations"]


def test_json_safe_copy_is_deep_and_mutation_isolated():
    original = {"outer": {"items": [1, {"value": "stable"}]}}
    copied = to_meaning_response_reuse_json_safe_v1(original)

    copied["outer"]["items"][1]["value"] = "changed"

    assert original["outer"]["items"][1]["value"] == "stable"


def test_helpers_have_no_side_effect_state_or_runtime_edits(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    meaning = analyze_meaning("What are you?")
    obligation = determine_response_obligation(meaning)
    state_context = gather_meaning_state(obligation)

    inputs = build_native_frame_inputs_from_meaning_reuse_v1(meaning, obligation, state_context)

    assert inputs["model_calls"] is False
    assert inputs["advisor_calls"] is False
    assert inputs["solver_execution"] is False
    assert inputs["safe_to_wire_runtime"] is False
    assert not (tmp_path / ".weslr").exists()

    root = Path(__file__).resolve().parents[2]
    assert not (root / "chat_responder.py").exists()
    assert (root / "weslr" / "chat_responder.py").exists()
