from __future__ import annotations

import importlib
import json
import sys

import pytest

from weslr.candidate_response_formation import (
    CandidateResponseFormationPacket,
    build_candidate_response_formation_packet_v1,
    form_candidate_responses_v1,
    summarize_candidate_response_formation_packet_v1,
    to_candidate_response_formation_json_safe_v1,
    validate_candidate_response_formation_packet_v1,
)


def _selected(packet):
    return next(candidate for candidate in packet.candidates if candidate.selected)


def _candidate_type(packet):
    return _selected(packet).candidate_type


def _packet(labels, context=None):
    return build_candidate_response_formation_packet_v1(labels, context_signals=context or {})


def test_module_import_is_safe_and_public_api_exists():
    before = set(sys.modules)
    module = importlib.import_module("weslr.candidate_response_formation")
    after = set(sys.modules)
    assert before <= after
    for name in (
        "CandidateResponsePath",
        "CandidateResponseRejection",
        "CandidateResponseFormationPacket",
        "CandidateResponseFormationSummary",
        "build_candidate_response_formation_packet_v1",
        "validate_candidate_response_formation_packet_v1",
        "summarize_candidate_response_formation_packet_v1",
        "to_candidate_response_formation_json_safe_v1",
        "form_candidate_responses_v1",
    ):
        assert hasattr(module, name)


@pytest.mark.parametrize("labels", [["who are you", "status"], ["implementation", "build"]])
def test_forms_deterministic_packet(labels):
    packet_a = to_candidate_response_formation_json_safe_v1(_packet(labels))
    packet_b = to_candidate_response_formation_json_safe_v1(_packet(labels))
    assert packet_a == packet_b


def test_validates_normal_packet():
    packet = _packet(["who are you", "status"])
    assert validate_candidate_response_formation_packet_v1(packet) is True
    assert isinstance(packet, CandidateResponseFormationPacket)


def test_json_safe_export_works():
    payload = to_candidate_response_formation_json_safe_v1(_packet(["memory", "remember"]))
    assert isinstance(payload, dict)
    json.dumps(payload)
    assert isinstance(payload["candidates"], list)
    assert isinstance(payload["rejected_candidates"], list)


def test_summary_includes_candidate_count_and_selected_candidate():
    packet = _packet(["teach", "explain"])
    summary = summarize_candidate_response_formation_packet_v1(packet)
    assert summary.candidate_count == packet.candidate_count
    assert summary.selected_candidate_id == packet.selected_candidate_id
    assert summary.selected_candidate_type == _candidate_type(packet)


@pytest.mark.parametrize(
    "labels,expected",
    [
        (["who are you", "status"], "direct_bounded_candidate"),
        (["identity", "status"], "direct_bounded_candidate"),
    ],
)
def test_direct_clear_labels_form_direct_bounded_candidate(labels, expected):
    assert _candidate_type(_packet(labels)) == expected


def test_memory_uncertainty_forms_memory_honesty_candidate():
    assert _candidate_type(_packet(["memory", "remember", "do you remember"])) == "memory_honesty_candidate"


def test_continuity_signal_forms_continuity_recap_candidate():
    assert _candidate_type(_packet(["continuity", "follow up", "what were we doing"])) == "continuity_recap_candidate"


def test_missing_context_forms_clarification_candidate():
    assert _candidate_type(_packet([], {})) == "clarification_candidate"


def test_bounded_uncertainty_forms_uncertainty_candidate():
    assert _candidate_type(_packet(["uncertain", "not sure", "maybe"])) == "bounded_uncertainty_candidate"


def test_refusal_boundary_forms_refusal_candidate():
    assert _candidate_type(_packet(["unsafe", "privacy", "not allowed"])) == "refusal_boundary_candidate"


def test_evidence_needed_forms_evidence_candidate():
    assert _candidate_type(_packet(["need evidence", "source", "current"])) == "evidence_needed_candidate"


def test_partial_supported_forms_partial_candidate():
    assert _candidate_type(_packet(["partial", "supported", "split answer"])) == "partial_supported_candidate"


def test_ordinary_task_forms_stepwise_plan_candidate():
    assert _candidate_type(_packet(["task", "plan", "checklist"])) == "stepwise_plan_candidate"


def test_implementation_planning_forms_implementation_plan_candidate():
    assert _candidate_type(_packet(["implementation", "build", "next lane"])) == "implementation_plan_candidate"


def test_next_lane_workflow_forms_workflow_candidate():
    assert _candidate_type(_packet(["next lane", "sequence", "what next"])) == "workflow_next_lane_candidate"


def test_governance_escalation_forms_governance_candidate():
    assert _candidate_type(_packet(["approval", "operator review", "blocked"])) == "governance_escalation_candidate"


def test_teaching_explanation_forms_teaching_candidate():
    assert _candidate_type(_packet(["teach", "explain", "education"])) == "teaching_explanation_candidate"


def test_language_discovery_forms_language_candidate():
    assert _candidate_type(_packet(["language", "grammar", "vocabulary"])) == "language_discovery_candidate"


def test_scientific_discovery_forms_scientific_guidance_candidate():
    assert _candidate_type(_packet(["scientific", "research", "experiment"])) == "scientific_discovery_guidance_candidate"


def test_benchmark_evaluation_forms_benchmark_candidate():
    assert _candidate_type(_packet(["benchmark", "evaluation", "readiness"])) == "benchmark_evaluation_candidate"


def test_unknown_word_phrase_forms_unknown_friction_candidate():
    assert _candidate_type(_packet(["unknown word", "what does this mean"])) == "unknown_friction_candidate"


def test_unknown_intent_forms_unknown_friction_candidate():
    assert _candidate_type(_packet(["unknown intent", "what do you mean"])) == "unknown_friction_candidate"


def test_unknown_capability_forms_unknown_friction_candidate():
    assert _candidate_type(_packet(["unknown capability", "can you do this"])) == "unknown_friction_candidate"


def test_repeated_friction_forms_unknown_friction_candidate():
    assert _candidate_type(_packet(["repeated failure", "stuck", "friction"])) == "unknown_friction_candidate"


def test_relationship_feedback_forms_relationship_feedback_candidate():
    assert _candidate_type(_packet(["relationship", "feedback", "tone"])) == "relationship_feedback_candidate"


def test_correction_signal_forms_correction_repair_candidate():
    assert _candidate_type(_packet(["actually", "wrong", "fix"])) == "correction_repair_candidate"


def test_contradiction_signal_forms_conflict_candidate():
    assert _candidate_type(_packet(["contradiction", "inconsistent", "clash"])) == "conflict_contradiction_candidate"


def test_non_canned_pressure_forms_non_canned_candidate():
    assert _candidate_type(_packet(["template", "generic", "boilerplate"])) == "non_canned_specificity_candidate"


def test_directness_concern_forms_directness_candidate():
    assert _candidate_type(_packet(["directness", "too direct", "concern"])) == "directness_concern_candidate"


def test_incompatible_alternatives_are_rejected_with_reasons():
    packet = _packet(["who are you", "status"])
    rejected = {item.candidate_type: item for item in packet.rejected_candidates}
    assert rejected["governance_escalation_candidate"].rejection_reason
    assert rejected["benchmark_evaluation_candidate"].rejection_reason


def test_selected_candidate_is_not_rejected():
    packet = _packet(["memory", "remember"])
    selected = _selected(packet)
    assert selected.selected is True
    assert selected.rejected is False
    assert selected.rejection_reason == ""


def test_missing_evidence_sets_needs_evidence_true():
    packet = _packet(["need evidence", "source"])
    assert packet.needs_evidence is True


def test_missing_context_sets_needs_clarification_true():
    packet = _packet([])
    assert packet.needs_clarification is True


def test_owner_approval_signal_sets_needs_owner_approval_true():
    packet = _packet(["approval", "operator review"])
    assert packet.needs_owner_approval is True


def test_unsafe_signal_sets_blocked_refusal_path():
    packet = _packet(["unsafe", "privacy", "not allowed"])
    assert packet.blocked is True
    assert _candidate_type(packet) == "refusal_boundary_candidate"


def test_no_raw_prompt_text_is_returned():
    packet = to_candidate_response_formation_json_safe_v1(_packet(["who are you", "status"], {"raw_prompt_text": "hidden"}))
    assert "raw_prompt_text" not in packet
    assert all("raw_prompt_text" not in candidate for candidate in packet["candidates"])
    assert all("raw_prompt_text" not in item for item in packet["safe_metadata"])


@pytest.mark.parametrize(
    "field_name",
    ["runtime_authority", "model_provider_used", "generates_final_text", "writes_state"],
)
def test_validation_fails_on_authority_drift_and_runtime_flags(field_name):
    packet = to_candidate_response_formation_json_safe_v1(_packet(["who are you", "status"]))
    packet[field_name] = True
    with pytest.raises(ValueError):
        validate_candidate_response_formation_packet_v1(packet)


def test_does_not_import_or_call_chat_responder():
    assert "weslr.chat_responder" not in sys.modules


def test_does_not_import_or_call_main():
    assert "weslr.main" not in sys.modules


def test_does_not_import_or_call_dialogue():
    assert "dialogue" not in sys.modules


def test_does_not_import_or_call_chat_ui():
    assert "chat_ui" not in sys.modules


def test_form_candidate_responses_alias_matches_builder():
    assert to_candidate_response_formation_json_safe_v1(form_candidate_responses_v1(["teach", "explain"])) == to_candidate_response_formation_json_safe_v1(_packet(["teach", "explain"]))
