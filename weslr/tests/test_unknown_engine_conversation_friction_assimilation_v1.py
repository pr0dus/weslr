"""Tests for UNKNOWN ENGINE conversation friction assimilation helpers V1."""

from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

import pytest

MODULE_NAME = "weslr.unknown_engine_conversation_friction_assimilation"
MODULE_PATH = Path(__file__).resolve().parents[1] / "unknown_engine_conversation_friction_assimilation.py"


def _module():
    return importlib.import_module(MODULE_NAME)


def _valid_friction_item(**overrides):
    m = _module()
    base = {
        "source_turn_id": "turn_001",
        "failure_label": "cannedness",
        "safe_reference_id": "ref_001",
        "transcript_scope": "synthetic",
        "synthetic_only": True,
        "observation_commit": "98a2d1c",
        "observation_note": "synthetic observation metadata only",
    }
    base.update(overrides)
    return m.build_unknown_engine_conversation_friction_item_v1(base)


def _valid_gap_hypothesis(**overrides):
    m = _module()
    base = {
        "source_turn_id": "turn_001",
        "friction_label": "cannedness",
        "gap_labels": ["missing_non_cannedness_pressure"],
        "safe_reference_id": "gap_ref_001",
        "transcript_scope": "synthetic",
        "synthetic_only": True,
    }
    base.update(overrides)
    return m.build_unknown_engine_cognition_gap_hypothesis_v1(base)


def _valid_failed_path_reference(**overrides):
    m = _module()
    base = {
        "source_turn_id": "turn_001",
        "failure_label": "cannedness",
        "gap_label": "missing_non_cannedness_pressure",
        "safe_reference_id": "failed_ref_001",
        "source_observation_path": "docs/WESLR_CONTROLLED_LOCAL_REAL_CONVERSATION_OBSERVATION_V1.md",
        "transcript_scope": "synthetic",
        "synthetic_only": True,
    }
    base.update(overrides)
    return m.build_unknown_engine_failed_path_reference_v1(base)


def _valid_improvement_target(**overrides):
    m = _module()
    base = {
        "target_id": "target_001",
        "gap_label": "missing_non_cannedness_pressure",
        "recommended_helper_name": "add_non_cannedness_pressure_helper",
        "recommended_lane": "helper_design_lane_only",
        "synthetic_only": True,
    }
    base.update(overrides)
    return m.build_unknown_engine_improvement_target_v1(base)


def _valid_assimilation_artifact(**overrides):
    m = _module()
    item = _valid_friction_item()
    base = {
        "source_observation_path": "docs/WESLR_CONTROLLED_LOCAL_REAL_CONVERSATION_OBSERVATION_V1.md",
        "observation_commit": "98a2d1c",
        "transcript_scope": "synthetic",
        "synthetic_only": True,
        "raw_private_data_included": False,
        "provider_model_calls_allowed": False,
        "runtime_wiring_allowed": False,
        "official_score_allowed": False,
        "friction_items": [item],
        "blocked_authority": m.required_unknown_engine_blocked_authority_v1(),
        "recommended_next_lane": "REVIEW_UNKNOWN_ENGINE_CONVERSATION_FRICTION_ARTIFACT_HELPERS_V1",
    }
    base.update(overrides)
    return m.build_unknown_engine_conversation_friction_assimilation_v1(base)


def _flatten_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _flatten_strings(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _flatten_strings(item)


def test_allowed_labels_exact_and_sufficient():
    m = _module()
    assert m.allowed_unknown_engine_conversation_friction_labels_v1() == (
        "cannedness",
        "missed_local_context",
        "shallow_continuity",
        "over_safety",
        "under_answering",
        "vague_language",
        "weak_tradeoff_reasoning",
        "weak_human_concern_tracking",
        "weak_followup_memory",
        "boundary_overgeneralization",
        "fallback_to_checklist",
        "insufficient_self_correction",
        "unsafe_authority_claim",
        "public_readiness_overclaim",
        "provider_model_fallback_risk",
    )
    assert m.allowed_unknown_engine_conversation_gap_labels_v1() == (
        "missing_conversation_state_frame",
        "missing_current_user_concern_slot",
        "missing_recent_turn_recall_object",
        "missing_goal_subgoal_cache_use",
        "missing_answer_shape_planner",
        "missing_non_cannedness_pressure",
        "missing_tradeoff_reasoning_frame",
        "missing_empathy_concern_integration",
        "missing_boundary_specific_authority_calibration",
        "missing_response_self_check_before_final_answer",
        "missing_failed_path_registry_connection",
        "missing_concrete_next_step_selection",
        "missing_directness_pressure",
        "missing_response_shape_diversity",
        "missing_boundary_specific_fallback_gating",
        "missing_validation_gate",
    )


def test_blocked_authority_all_false():
    blocked = _module().required_unknown_engine_blocked_authority_v1()
    assert blocked == {
        "permits_runtime_changes": False,
        "permits_chat_wiring": False,
        "permits_final_answer_generation": False,
        "permits_provider_calls": False,
        "permits_model_calls": False,
        "permits_search_calls": False,
        "permits_advisor_calls": False,
        "permits_raw_private_data": False,
        "permits_dot_weslr_io": False,
        "permits_memory_claims": False,
        "permits_public_launch": False,
        "permits_product_readiness_claims": False,
        "permits_intelligence_claims": False,
        "permits_turing_claims": False,
        "permits_certification_claims": False,
        "permits_official_scoring": False,
        "permits_auto_implementation": False,
    }


def test_valid_friction_item_passes():
    item = _valid_friction_item()
    validation = _module().validate_unknown_engine_conversation_friction_item_v1(item)
    assert validation["valid"] is True
    assert validation["blocked"] is False


def test_unsupported_friction_label_fails_closed():
    item = _valid_friction_item(failure_label="not_supported")
    validation = _module().validate_unknown_engine_conversation_friction_item_v1(item)
    assert validation["valid"] is False
    assert any("unsupported_friction_label" in label for label in validation["blocked_reason_labels"])


def test_valid_cognition_gap_hypothesis_passes():
    hypothesis = _valid_gap_hypothesis()
    validation = _module().validate_unknown_engine_cognition_gap_hypothesis_v1(hypothesis)
    assert validation["valid"] is True
    assert validation["blocked"] is False


def test_unsupported_gap_label_fails_closed():
    hypothesis = _valid_gap_hypothesis(gap_labels=["not_supported"])
    validation = _module().validate_unknown_engine_cognition_gap_hypothesis_v1(hypothesis)
    assert validation["valid"] is False
    assert any("unsupported_gap_label" in label for label in validation["blocked_reason_labels"])


def test_friction_to_gap_mapping_works_for_all_required_labels():
    m = _module()
    mapping = m.map_unknown_engine_friction_to_cognition_gaps_v1(m.allowed_unknown_engine_conversation_friction_labels_v1())
    assert mapping["blocked"] is False
    assert mapping["blocked_reason_labels"] == []
    assert mapping["friction_to_gap_map"]["cannedness"] == ["missing_non_cannedness_pressure", "missing_answer_shape_planner"]
    assert mapping["friction_to_gap_map"]["missed_local_context"] == ["missing_conversation_state_frame", "missing_current_user_concern_slot"]
    assert mapping["friction_to_gap_map"]["shallow_continuity"] == ["missing_recent_turn_recall_object", "missing_goal_subgoal_cache_use"]
    assert mapping["friction_to_gap_map"]["over_safety"] == ["missing_boundary_specific_authority_calibration", "missing_answer_shape_planner"]
    assert mapping["friction_to_gap_map"]["under_answering"] == ["missing_answer_shape_planner", "missing_concrete_next_step_selection"]
    assert mapping["friction_to_gap_map"]["vague_language"] == ["missing_response_self_check_before_final_answer", "missing_directness_pressure"]
    assert mapping["friction_to_gap_map"]["weak_tradeoff_reasoning"] == ["missing_tradeoff_reasoning_frame"]
    assert mapping["friction_to_gap_map"]["weak_human_concern_tracking"] == ["missing_empathy_concern_integration"]
    assert mapping["friction_to_gap_map"]["weak_followup_memory"] == ["missing_recent_turn_recall_object", "missing_current_user_concern_slot"]
    assert mapping["friction_to_gap_map"]["boundary_overgeneralization"] == ["missing_boundary_specific_authority_calibration"]
    assert mapping["friction_to_gap_map"]["fallback_to_checklist"] == ["missing_non_cannedness_pressure", "missing_response_shape_diversity"]
    assert mapping["friction_to_gap_map"]["insufficient_self_correction"] == ["missing_response_self_check_before_final_answer"]
    assert mapping["friction_to_gap_map"]["unsafe_authority_claim"] == ["missing_boundary_specific_authority_calibration"]
    assert mapping["friction_to_gap_map"]["public_readiness_overclaim"] == ["missing_failed_path_registry_connection", "missing_validation_gate"]
    assert mapping["friction_to_gap_map"]["provider_model_fallback_risk"] == ["missing_boundary_specific_fallback_gating", "missing_boundary_specific_authority_calibration"]


def test_failed_path_reference_is_metadata_only():
    reference = _valid_failed_path_reference()
    validation = _module().validate_unknown_engine_failed_path_reference_v1(reference)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert reference["source_observation_path"].endswith("WESLR_CONTROLLED_LOCAL_REAL_CONVERSATION_OBSERVATION_V1.md")


def test_failed_path_reference_rejects_raw_private_data_marker():
    reference = _valid_failed_path_reference(source_observation_path="raw prompt: hidden secret")
    validation = _module().validate_unknown_engine_failed_path_reference_v1(reference)
    assert validation["valid"] is False
    assert any("raw_private_data_included" in label or "hidden_prompt" in label for label in validation["blocked_reason_labels"])


def test_improvement_target_is_bounded_and_non_runtime_authorizing():
    target = _valid_improvement_target()
    validation = _module().validate_unknown_engine_improvement_target_v1(target)
    assert validation["valid"] is True
    assert target["bounded"] is True
    assert target["recommended_lane"] == "helper_design_lane_only"
    assert "helper" in target["recommended_helper_name"]


def test_artifact_builds_with_required_metadata():
    artifact = _valid_assimilation_artifact()
    assert artifact["schema_version"] == "WeslrUnknownEngineConversationFrictionAssimilationV1"
    assert artifact["artifact_type"] == "WeslrUnknownEngineConversationFrictionAssimilationV1"
    assert artifact["synthetic_only"] is True
    assert artifact["raw_private_data_included"] is False
    assert artifact["provider_model_calls_allowed"] is False
    assert artifact["runtime_wiring_allowed"] is False
    assert artifact["official_score_allowed"] is False
    assert artifact["blocked_authority"] == _module().required_unknown_engine_blocked_authority_v1()


def test_artifact_validates_when_synthetic_only_and_authority_denying():
    artifact = _valid_assimilation_artifact()
    validation = _module().validate_unknown_engine_conversation_friction_assimilation_v1(artifact)
    assert validation["valid"] is True
    assert validation["blocked"] is False


@pytest.mark.parametrize(
    "mutator, expected",
    [
        (lambda a: a.pop("source_observation_path"), "source_observation_path"),
        (lambda a: a.pop("friction_items"), "friction_items"),
    ],
)
def test_artifact_blocks_missing_required_fields(mutator, expected):
    artifact = _valid_assimilation_artifact()
    mutator(artifact)
    validation = _module().validate_unknown_engine_conversation_friction_assimilation_v1(artifact)
    assert validation["valid"] is False
    assert expected in validation["missing_required_fields"]


@pytest.mark.parametrize(
    "field",
    [
        "raw_private_data_included",
        "provider_model_calls_allowed",
        "runtime_wiring_allowed",
        "official_score_allowed",
    ],
)
def test_artifact_blocks_true_safety_flags(field):
    artifact = _valid_assimilation_artifact(**{field: True})
    validation = _module().validate_unknown_engine_conversation_friction_assimilation_v1(artifact)
    assert validation["valid"] is False
    assert any(field in label for label in validation["blocked_reason_labels"])


@pytest.mark.parametrize(
    "authority_field",
    [
        "permits_runtime_changes",
        "permits_chat_wiring",
        "permits_final_answer_generation",
        "permits_provider_calls",
        "permits_model_calls",
        "permits_search_calls",
        "permits_advisor_calls",
        "permits_raw_private_data",
        "permits_dot_weslr_io",
        "permits_memory_claims",
        "permits_public_launch",
        "permits_product_readiness_claims",
        "permits_intelligence_claims",
        "permits_turing_claims",
        "permits_certification_claims",
        "permits_official_scoring",
        "permits_auto_implementation",
    ],
)
def test_artifact_blocks_any_true_blocked_authority_field(authority_field):
    artifact = _valid_assimilation_artifact()
    artifact["blocked_authority"][authority_field] = True
    validation = _module().validate_unknown_engine_conversation_friction_assimilation_v1(artifact)
    assert validation["valid"] is False
    assert any(authority_field in label for label in validation["blocked_reason_labels"])


@pytest.mark.parametrize("path", [".weslr/state.json", "docs/.weslr/private", "x/.weslr/y"])
def test_artifact_blocks_dot_weslr_path(path):
    artifact = _valid_assimilation_artifact(source_observation_path=path)
    validation = _module().validate_unknown_engine_conversation_friction_assimilation_v1(artifact)
    assert validation["valid"] is False
    assert any("dot_weslr_path_detected" in label for label in validation["blocked_reason_labels"])


@pytest.mark.parametrize("marker", ["public readiness", "public-ready", "ready for public launch", "launch now"])
def test_artifact_blocks_public_readiness_claim_marker(marker):
    artifact = _valid_assimilation_artifact()
    artifact["friction_items"][0]["observation_note"] = marker
    validation = _module().validate_unknown_engine_conversation_friction_assimilation_v1(artifact)
    assert validation["valid"] is False
    assert any("public_readiness_implied" in label for label in validation["blocked_reason_labels"])


@pytest.mark.parametrize("marker", ["official score", "benchmark", "turing test", "certification", "intelligence claim"])
def test_artifact_blocks_intelligence_turing_certification_claim_marker(marker):
    artifact = _valid_assimilation_artifact()
    artifact["friction_items"][0]["observation_note"] = marker
    validation = _module().validate_unknown_engine_conversation_friction_assimilation_v1(artifact)
    assert validation["valid"] is False
    assert any("official_claim_implied" in label for label in validation["blocked_reason_labels"])


@pytest.mark.parametrize("marker", ["hidden prompt", "protected item", "protected material", "system prompt:", "developer prompt:"])
def test_artifact_blocks_hidden_prompt_or_protected_item_marker(marker):
    artifact = _valid_assimilation_artifact()
    artifact["friction_items"][0]["observation_note"] = marker
    validation = _module().validate_unknown_engine_conversation_friction_assimilation_v1(artifact)
    assert validation["valid"] is False
    assert any("hidden_prompt_or_protected_item_included" in label for label in validation["blocked_reason_labels"])


def test_artifact_blocks_non_json_safe_metadata():
    artifact = _valid_assimilation_artifact()
    artifact["friction_items"].append(object())
    validation = _module().validate_unknown_engine_conversation_friction_assimilation_v1(artifact)
    assert validation["valid"] is False
    assert "non_json_safe_metadata" in validation["blocked_reason_labels"]


def test_summary_is_safe_and_contains_no_raw_private_text():
    artifact = _valid_assimilation_artifact()
    summary = _module().summarize_unknown_engine_conversation_friction_assimilation_v1(artifact)
    assert summary["blocked"] is False
    assert summary["validation_status"] == "validation_pass_metadata_only"
    assert summary["recommended_next_lane"] == "REVIEW_UNKNOWN_ENGINE_CONVERSATION_FRICTION_ARTIFACT_HELPERS_V1"
    flattened = "\n".join(_flatten_strings(summary)).lower()
    assert "raw prompt" not in flattened
    assert "raw response" not in flattened
    assert "private content" not in flattened


def test_no_provider_model_search_advisor_calls_or_runtime_chat_wiring_or_final_answer_authority_in_source():
    source = MODULE_PATH.read_text()
    for fragment in [
        "respond_chat(",
        "generate_chat(",
        "ChatResponder(",
        "provider_call(",
        "model_call(",
        "search_call(",
        "advisor_call(",
        "open('.weslr",
        'open(".weslr',
        "final_answer_generated",
        "final answer generation",
    ]:
        assert fragment not in source


def test_no_runtime_chat_wiring_authority_no_public_launch_authority_no_memory_or_continuity_raw_access():
    source = MODULE_PATH.read_text().lower()
    for fragment in [
        "permits_runtime_changes = true",
        "permits_chat_wiring = true",
        "permits_final_answer_generation = true",
        "permits_provider_calls = true",
        "permits_model_calls = true",
        "permits_search_calls = true",
        "permits_advisor_calls = true",
        "permits_raw_private_data = true",
        "permits_dot_weslr_io = true",
        "permits_memory_claims = true",
        "permits_public_launch = true",
        "open('continuity",
        'open("continuity',
        "open('.weslr",
        'open(".weslr',
    ]:
        assert fragment not in source


def test_ast_does_not_include_external_io_or_runtime_exec_calls():
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_calls = {"open", "exec", "eval", "compile", "subprocess", "requests", "socket"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            assert name not in forbidden_calls


def test_validation_blocks_non_json_safe_artifact_and_missing_blocked_authority_true():
    artifact = _valid_assimilation_artifact()
    artifact["blocked_authority"] = {"permits_runtime_changes": False, "permits_chat_wiring": False, "permits_final_answer_generation": object()}
    validation = _module().validate_unknown_engine_conversation_friction_assimilation_v1(artifact)
    assert validation["valid"] is False
    assert "non_json_safe_metadata" in validation["blocked_reason_labels"]
