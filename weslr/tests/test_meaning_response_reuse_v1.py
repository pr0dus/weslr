"""Focused tests for meaning/obligation/state native reuse helpers V1."""

from pathlib import Path

from weslr.linguistic_meaning import analyze_meaning
from weslr.meaning_response_reuse import (
    build_compact_meaning_payload_v1,
    build_compact_meaning_state_context_bundle_v1,
    build_compact_response_obligation_payload_v1,
    build_native_frame_inputs_from_meaning_reuse_v1,
    derive_known_and_missing_context_from_meaning_state_v1,
    extract_helper_metadata_from_meaning_reuse_v1,
    extract_native_frame_kwargs_from_meaning_reuse_v1,
    to_meaning_response_reuse_json_safe_v1,
    validate_meaning_response_reuse_payload_v1,
)
from weslr.meaning_state_context import MeaningStateContext, gather_meaning_state
from weslr.native_reasoning_frame import build_native_reasoning_frame_v1
from weslr.response_obligation import determine_response_obligation


HELPER_METADATA_KEYS = {
    "raw_text_stored",
    "model_calls",
    "advisor_calls",
    "solver_execution",
    "answer_selection_arbitration",
    "safe_to_wire_runtime",
    "live_runtime_output",
    "runtime_wiring",
}


def _assert_no_raw_prompt_fields(payload):
    rendered = repr(payload)
    assert "raw_text" not in payload
    assert "normalized_text" not in payload
    assert "tokens" not in payload
    assert "What are you?" not in rendered


def _relationship_state_context():
    return MeaningStateContext(
        sender_identity=None,
        known_user_status="claimed",
        sender_confidence=0.4,
        identity_evidence=[],
        onboarding_profile_summary=None,
        relationship_depth=0.42,
        relationship_stage="returning_collaborator",
        relationship_confidence=0.75,
        relationship_limitations=["identity_not_verified"],
        memory_available=True,
        memory_summary="private raw memory must not be emitted",
        memory_sources_checked=["entity_memory"],
        memory_scope_used="bounded_summary",
        self_model_summary="bounded operational self-model summary",
        capability_summary="bounded capability summary",
        continuity_summary="bounded continuity summary",
        timeline_summary="bounded timeline summary",
        sources_used=["entity_memory", "relationship_depth", "https://example.invalid/raw"],
        sources_failed=[{"source": "user_profile", "reason": "unavailable"}],
        state_confidence=0.67,
    )


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
    assert "source_status" in payload
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
        "sources_failed": [],
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


def test_native_frame_kwargs_are_separated_and_directly_splattable():
    meaning = analyze_meaning("What are you?")
    obligation = determine_response_obligation(meaning)
    state_context = gather_meaning_state(obligation)

    payload = build_native_frame_inputs_from_meaning_reuse_v1(meaning, obligation, state_context)
    native_kwargs = extract_native_frame_kwargs_from_meaning_reuse_v1(payload)
    helper_metadata = extract_helper_metadata_from_meaning_reuse_v1(payload)
    frame = build_native_reasoning_frame_v1(request_summary="self model question", **native_kwargs)

    assert payload["payload_type"] == "meaning_response_reuse_native_inputs_v1"
    assert set(payload) == {"payload_type", "native_frame_kwargs", "helper_metadata"}
    assert not (set(native_kwargs) & HELPER_METADATA_KEYS)
    assert frame["frame_type"] == "native_reasoning_frame_v1"
    assert helper_metadata["safe_to_wire_runtime"] is False
    assert helper_metadata["raw_text_stored"] is False
    assert helper_metadata["model_calls"] is False
    assert helper_metadata["advisor_calls"] is False
    assert helper_metadata["solver_execution"] is False
    assert "What are you?" not in repr(payload)
    assert native_kwargs["meaning_vector_result"]["raw_text_included"] is False
    assert native_kwargs["meaning_vector_result"]["normalized_text_included"] is False
    assert validate_meaning_response_reuse_payload_v1(payload)["valid"] is True


def test_relationship_continuity_timeline_and_failed_sources_propagate_safely():
    meaning = analyze_meaning("Do you remember our work?")
    obligation = determine_response_obligation(meaning)
    state_context = _relationship_state_context()

    compact_state = build_compact_meaning_state_context_bundle_v1(state_context)
    derived = derive_known_and_missing_context_from_meaning_state_v1(
        build_compact_meaning_payload_v1(meaning),
        build_compact_response_obligation_payload_v1(obligation),
        compact_state,
    )
    known_kinds = {item["kind"] for item in derived["known_context"]}

    assert "relationship_context_available" in known_kinds
    assert "continuity_summary_available" in known_kinds
    assert "timeline_summary_available" in known_kinds
    assert "source_status" in known_kinds
    assert "relationship_context_limitations" in derived["missing_context"]
    assert "state_source_unavailable:user_profile" in derived["missing_context"]
    assert "source_label_redacted" in compact_state["sources_used"]
    rendered = repr(derived)
    assert "private raw memory" not in rendered
    assert "https://" not in rendered


def test_evidence_provenance_source_status_has_no_authority_elevation_or_raw_urls():
    state_context = _relationship_state_context()
    compact_state = build_compact_meaning_state_context_bundle_v1(state_context)
    derived = derive_known_and_missing_context_from_meaning_state_v1({}, {}, compact_state)

    assert derived["source_status"]["source_labels_only"] is True
    assert derived["source_status"]["source_authority_elevated"] is False
    assert derived["evidence_sufficiency_hint"]["source_authority_elevated"] is False
    assert "entity_memory" in derived["provenance_refs"]
    assert "relationship_depth" in derived["provenance_refs"]
    assert "https://" not in repr(derived)
    assert validate_meaning_response_reuse_payload_v1(compact_state)["valid"] is True


def test_capability_hint_is_not_authorization():
    derived = derive_known_and_missing_context_from_meaning_state_v1(
        {"required_state": ["capability_model"]},
        {"required_state": ["capability_model"]},
        {"capability_summary": "bounded capability summary", "sources_used": []},
    )
    hint = derived["capability_boundary_hint"]

    assert hint["hint_only"] is True
    assert hint["requires_tool"] is False
    assert hint["requires_external_action"] is False
    assert hint["requires_approval"] is False
    assert hint["authorization_granted"] is False


def test_usefulness_validation_warnings_are_non_fatal_but_unsafe_payload_errors():
    sparse = {
        "payload_type": "meaning_response_reuse_native_inputs_v1",
        "native_frame_kwargs": {},
        "helper_metadata": {key: False for key in HELPER_METADATA_KEYS},
    }
    sparse_result = validate_meaning_response_reuse_payload_v1(sparse)

    assert sparse_result["valid"] is True
    assert sparse_result["warnings"]
    assert not sparse_result["errors"]

    unsafe_result = validate_meaning_response_reuse_payload_v1({"raw_text": "private", "safe_to_wire_runtime": True})
    assert unsafe_result["valid"] is False
    assert unsafe_result["errors"]
    assert unsafe_result["violations"] == unsafe_result["errors"]


def test_validation_reports_missing_separation_and_source_status_warnings():
    legacy_shape = {
        "meaning_vector_result": {},
        "selected_context_bundle": {},
        "raw_text_stored": False,
    }
    legacy_result = validate_meaning_response_reuse_payload_v1(legacy_shape)
    assert legacy_result["valid"] is True
    assert any(w["category"] == "native_frame_kwargs_helper_metadata_not_separated" for w in legacy_result["warnings"])

    missing_source_status = {
        "payload_type": "meaning_response_reuse_native_inputs_v1",
        "native_frame_kwargs": {
            "selected_context_bundle": {"sources_used": ["SOUL.md"]},
            "known_context": [],
            "missing_context": [],
            "capability_boundary_result": {"hint_only": True},
        },
        "helper_metadata": {key: False for key in HELPER_METADATA_KEYS},
    }
    result = validate_meaning_response_reuse_payload_v1(missing_source_status)
    assert result["valid"] is True
    assert any(w["category"] == "missing_source_status" for w in result["warnings"])


def test_json_safe_copy_is_not_sanitizer_and_validator_catches_raw_fields():
    raw = {"raw_text": "private prompt", "nested": {"tokens": ["secret"]}}
    copied = to_meaning_response_reuse_json_safe_v1(raw)

    assert copied == raw
    validation = validate_meaning_response_reuse_payload_v1(copied)
    assert validation["valid"] is False
    assert {err["category"] for err in validation["errors"]} >= {"forbidden_key"}

    meaning = analyze_meaning("What are you?")
    compact = build_compact_meaning_payload_v1(meaning)
    assert "raw_text" not in compact
    assert "normalized_text" not in compact
    assert "tokens" not in compact


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

    payload = build_native_frame_inputs_from_meaning_reuse_v1(meaning, obligation, state_context)
    metadata = extract_helper_metadata_from_meaning_reuse_v1(payload)

    assert metadata["model_calls"] is False
    assert metadata["advisor_calls"] is False
    assert metadata["solver_execution"] is False
    assert metadata["answer_selection_arbitration"] is False
    assert metadata["safe_to_wire_runtime"] is False
    assert metadata["live_runtime_output"] is False
    assert metadata["runtime_wiring"] is False
    assert not (tmp_path / ".weslr").exists()

    root = Path(__file__).resolve().parents[2]
    assert not (root / "chat_responder.py").exists()
    assert (root / "weslr" / "chat_responder.py").exists()
