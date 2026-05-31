from __future__ import annotations

import importlib
import json
import sys

import pytest

from weslr.response_fit_self_check import (
    ResponseFitSelfCheckPacket,
    build_response_fit_self_check_packet_v1,
    check_candidate_response_fit_v1,
    summarize_response_fit_self_check_packet_v1,
    to_response_fit_self_check_json_safe_v1,
    validate_response_fit_self_check_packet_v1,
)


def _packet(labels, context=None):
    return build_response_fit_self_check_packet_v1(labels, context_signals=context or {})


def _json(packet):
    return to_response_fit_self_check_json_safe_v1(packet)


def _final_candidate(packet):
    payload = _json(packet)
    final_id = payload["final_candidate_id"]
    if not final_id:
        return None
    return next(item for item in payload["candidate_fit_results"] if item["candidate_id"] == final_id)


def _assert_final_type(packet, expected_type):
    final = _final_candidate(packet)
    assert final is not None
    assert final["candidate_type"] == expected_type


def test_module_import_is_safe_and_public_api_exists():
    before = set(sys.modules)
    module = importlib.import_module("weslr.response_fit_self_check")
    after = set(sys.modules)
    assert before <= after
    for name in (
        "ResponseFitSelfCheckPacket",
        "ResponseFitSelfCheckSummary",
        "CandidateSelfCheckResult",
        "build_response_fit_self_check_packet_v1",
        "validate_response_fit_self_check_packet_v1",
        "summarize_response_fit_self_check_packet_v1",
        "to_response_fit_self_check_json_safe_v1",
        "check_candidate_response_fit_v1",
    ):
        assert hasattr(module, name)


@pytest.mark.parametrize("labels", [["who are you", "status"], ["identity", "status"]])
def test_builds_deterministic_packet(labels):
    assert _json(_packet(labels)) == _json(_packet(labels))


def test_validates_normal_packet():
    packet = _packet(["who are you", "status"])
    assert validate_response_fit_self_check_packet_v1(packet) is True
    assert isinstance(packet, ResponseFitSelfCheckPacket)


def test_json_safe_export_works():
    payload = _json(_packet(["memory", "remember"]))
    assert isinstance(payload, dict)
    json.dumps(payload)
    assert isinstance(payload["candidate_fit_results"], list)


def test_summary_includes_fit_status_and_final_candidate():
    packet = _packet(["who are you", "status"])
    summary = summarize_response_fit_self_check_packet_v1(packet)
    assert summary.fit_status == _json(packet)["fit_status"]
    assert summary.final_candidate_id == _json(packet)["final_candidate_id"]


def test_direct_candidate_can_pass_fit():
    packet = _packet(["who are you", "status"])
    _assert_final_type(packet, "direct_bounded_candidate")
    assert _json(packet)["fit_status"] == "fit"


def test_clarification_candidate_passes_when_missing_context_exists():
    packet = _packet([])
    _assert_final_type(packet, "clarification_candidate")
    assert _json(packet)["fit_status"] == "needs_clarification"


def test_uncertainty_candidate_passes_when_uncertainty_exists():
    packet = _packet(["uncertain", "not sure", "maybe"])
    _assert_final_type(packet, "bounded_uncertainty_candidate")
    assert _json(packet)["fit_status"] == "fit_with_boundaries"


def test_refusal_candidate_passes_when_unsafe_boundary_signal_exists():
    packet = _packet(["unsafe", "privacy", "not allowed"])
    _assert_final_type(packet, "refusal_boundary_candidate")
    assert _json(packet)["fit_status"] == "fit_with_boundaries"


def test_evidence_candidate_passes_when_evidence_is_missing():
    packet = _packet(["need evidence", "source", "current"])
    _assert_final_type(packet, "evidence_needed_candidate")
    assert _json(packet)["fit_status"] == "needs_evidence"


def test_partial_supported_candidate_passes_for_partial_support():
    packet = _packet(["partial", "supported", "split answer"])
    _assert_final_type(packet, "partial_supported_candidate")


def test_task_plan_candidate_passes_for_ordinary_task():
    packet = _packet(["task", "plan", "checklist"])
    _assert_final_type(packet, "stepwise_plan_candidate")


def test_implementation_plan_candidate_passes_for_implementation_labels():
    packet = _packet(["implementation", "build", "next lane"])
    _assert_final_type(packet, "implementation_plan_candidate")


def test_workflow_next_lane_candidate_passes_for_lane_labels():
    packet = _packet(["next lane", "sequence", "what next"])
    _assert_final_type(packet, "workflow_next_lane_candidate")


def test_governance_escalation_candidate_passes_for_approval_signal():
    packet = _packet(["approval", "operator review", "blocked"])
    _assert_final_type(packet, "governance_escalation_candidate")
    assert _json(packet)["fit_status"] == "needs_owner_approval"


def test_teaching_candidate_passes_for_explanation_labels():
    packet = _packet(["teach", "explain", "education"])
    _assert_final_type(packet, "teaching_explanation_candidate")


def test_language_discovery_candidate_passes_for_language_labels():
    packet = _packet(["language", "grammar", "vocabulary"])
    _assert_final_type(packet, "language_discovery_candidate")


def test_scientific_guidance_candidate_passes_for_research_labels():
    packet = _packet(["scientific", "research", "experiment"])
    _assert_final_type(packet, "scientific_discovery_guidance_candidate")


def test_benchmark_candidate_passes_for_evaluation_labels():
    packet = _packet(["benchmark", "evaluation", "readiness"])
    _assert_final_type(packet, "benchmark_evaluation_candidate")


def test_unknown_friction_candidate_passes_for_unknown_friction_labels():
    packet = _packet(["unknown", "friction", "stuck"])
    _assert_final_type(packet, "unknown_friction_candidate")
    assert _json(packet)["fit_status"] == "unknown_friction"


def test_memory_honesty_candidate_passes_for_memory_uncertainty():
    packet = _packet(["memory", "remember", "do you remember"])
    _assert_final_type(packet, "memory_honesty_candidate")


def test_continuity_recap_candidate_passes_for_continuity_signal():
    packet = _packet(["continuity", "follow up", "what were we doing"])
    _assert_final_type(packet, "continuity_recap_candidate")


def test_relationship_feedback_candidate_passes_for_feedback_frustration_signal():
    packet = _packet(["relationship", "feedback", "frustration"])
    _assert_final_type(packet, "relationship_feedback_candidate")


def test_correction_repair_candidate_passes_for_correction_signal():
    packet = _packet(["actually", "wrong", "fix"])
    _assert_final_type(packet, "correction_repair_candidate")


def test_conflict_candidate_passes_for_contradiction_signal():
    packet = _packet(["contradiction", "inconsistent", "clash"])
    _assert_final_type(packet, "conflict_contradiction_candidate")


def test_non_canned_candidate_adds_template_risk_handling():
    packet = _packet(["template", "generic", "boilerplate"])
    _assert_final_type(packet, "non_canned_specificity_candidate")
    assert "canned_template_risk" in _json(packet)["quality_pressure_labels"]


def test_directness_concern_candidate_handles_concern_signal():
    packet = _packet(["directness", "too direct", "concern"])
    _assert_final_type(packet, "directness_concern_candidate")


def test_incompatible_candidate_is_rejected_with_reason():
    packet = _packet(["who are you", "status"])
    payload = _json(packet)
    rejected = {item["candidate_type"]: item for item in payload["candidate_fit_results"] if item["rejected"]}
    assert rejected["governance_escalation_candidate"]["reason"]


def test_candidate_with_missing_evidence_is_rejected_unless_evidence_needed_path():
    packet = _packet(["need evidence", "source"])
    payload = _json(packet)
    assert payload["final_candidate_id"]
    assert payload["final_candidate_id"] != ""
    assert any(item["candidate_type"] == "evidence_needed_candidate" and item["accepted"] for item in payload["candidate_fit_results"])


def test_candidate_with_missing_context_is_rejected_unless_clarification_path():
    packet = _packet([])
    payload = _json(packet)
    assert any(item["candidate_type"] == "clarification_candidate" and item["accepted"] for item in payload["candidate_fit_results"])
    assert any(item["candidate_type"] == "direct_bounded_candidate" and item["rejected"] for item in payload["candidate_fit_results"])


def test_authority_drift_fails_validation():
    packet = _packet(["who are you", "status"], {"runtime_authority": True})
    with pytest.raises(ValueError):
        validate_response_fit_self_check_packet_v1(packet)


def test_model_provider_used_true_fails_validation():
    packet = _packet(["who are you", "status"], {"model_provider_used": True})
    with pytest.raises(ValueError):
        validate_response_fit_self_check_packet_v1(packet)


def test_generates_final_text_true_fails_validation():
    packet = _packet(["who are you", "status"], {"generates_final_text": True})
    with pytest.raises(ValueError):
        validate_response_fit_self_check_packet_v1(packet)


def test_writes_state_true_fails_validation():
    packet = _packet(["who are you", "status"], {"writes_state": True})
    with pytest.raises(ValueError):
        validate_response_fit_self_check_packet_v1(packet)


def test_raw_prompt_leakage_fails_validation():
    packet = _packet(["who are you", "status"], {"raw_prompt_text": "secret"})
    with pytest.raises(ValueError):
        validate_response_fit_self_check_packet_v1(packet)


def test_no_final_prose_is_generated():
    packet = _packet(["who are you", "status"])
    payload = _json(packet)
    assert payload["generates_final_text"] is False
    assert all(result["generates_final_text"] is False for result in payload["candidate_fit_results"])
    assert "final_answer_text" not in payload


@pytest.mark.parametrize("module_name", ["weslr.chat_responder", "weslr.main", "dialogue", "chat_ui"])
def test_does_not_import_forbidden_modules(monkeypatch, module_name):
    monkeypatch.delitem(sys.modules, module_name, raising=False)
    importlib.import_module("weslr.response_fit_self_check")
    _packet(["who are you", "status"])
    assert module_name not in sys.modules
