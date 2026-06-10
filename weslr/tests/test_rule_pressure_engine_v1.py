from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.cognitive_research_protocol as protocol
from weslr.forecast_calibration_bridge import validate_forecast_calibration_record_v1
from weslr.rule_pressure_engine import (
    ENGINE_FAMILY_V1,
    ENGINE_NAME_V1,
    build_initial_rule_pressure_examples_v1,
    build_rule_pressure_correction_v1,
    build_rule_pressure_packet_v1,
    build_rule_pressure_result_v1,
    build_rule_pressure_target_v1,
    build_rule_pressure_test_v1,
    summarize_rule_pressure_packet_v1,
    to_rule_pressure_json_safe_v1,
    validate_rule_pressure_packet_v1,
)

ROOT = Path(__file__).resolve().parents[2]

PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]


def _target(**overrides):
    base = {
        "source_engine_name": "unknown_engine",
        "source_run_id": "run-rule-pressure-001",
        "target_type": "hidden_rule",
        "target_summary": "Hidden rule candidate with narrow scope and a control case.",
        "candidate_rule_or_operator": "candidate rule",
        "claimed_scope": "bounded claim",
        "known_scope": "metadata-only scope",
        "uncertainty_factors": ["scope may shift under pressure"],
        "invalidation_signals": ["no invalidation observed yet"],
        "public_claim_status": "not_public_claim",
    }
    base.update(overrides)
    return build_rule_pressure_target_v1(base)


def _test(target=None, **overrides):
    target = target or _target()
    base = {
        "target": target,
        "target_id": target["target_id"],
        "target_rule_or_operator": target["candidate_rule_or_operator"],
        "pressure_type": "counterexample_search",
        "pressure_summary": "What would break this?",
        "input_mutation": "metadata-only mutation",
        "expected_failure_mode": "hidden_assumption_failure",
        "control_case_summary": "Control case keeps the baseline intact.",
        "success_criteria": "pressure reveals a bounded weakness",
        "failure_criteria": "pressure leaves an unsupported public or runtime claim",
        "safe_to_run_as_metadata": True,
    }
    base.update(overrides)
    return build_rule_pressure_test_v1(base)


def _result(target=None, test=None, **overrides):
    target = target or _target()
    test = test or _test(target)
    base = {
        "target_id": target["target_id"],
        "pressure_test_id": test["pressure_test_id"],
        "result_status": "not_observed_yet",
        "observed_result_summary": "not observed yet",
        "target_survived": True,
        "breakage_detected": False,
        "breakage_type": "none",
        "scope_changed": False,
        "new_uncertainty": ["not yet observed"],
        "new_invalidation_signal": "none",
        "calibration_outcome_status": "not_yet_calibrated",
    }
    base.update(overrides)
    return build_rule_pressure_result_v1(base)


def _correction(target=None, test=None, result=None, **overrides):
    target = target or _target()
    test = test or _test(target)
    result = result or _result(target, test)
    base = {
        "target_id": target["target_id"],
        "pressure_test_id": test["pressure_test_id"],
        "breakage_type": "scope_failure",
        "failed_assumption": "candidate rule",
        "corrected_scope": "metadata-only scope",
        "model_update_summary": "pressure revealed a bounded failure mode",
        "compressed_lesson": "Pressure reveals limits; survival is not proof.",
        "future_pressure_adjustment": "narrow future pressure and add a control case",
        "calibration_record_ref": "calibration-001",
    }
    base.update(overrides)
    return build_rule_pressure_correction_v1(base)


def _packet(**overrides):
    base = {
        "source_engine_name": "unknown_engine",
        "input_artifact_ref": "artifact:rule-pressure-001",
        "input_artifact_type": "rule-pressure-bundle",
        "input_summary": "Candidate rule pressure with scope update and calibration.",
        "research_mode": "synthetic_test",
        "public_claim_status": "internal_candidate_only",
        "public_gap_card_status": "public_export_blocked",
        "llm_helper_role": "candidate_generator_only",
    }
    base.update(overrides)
    return build_rule_pressure_packet_v1(base)


def test_engine_identity_is_fixed():
    packet = _packet()
    assert packet["engine_name"] == ENGINE_NAME_V1
    assert packet["engine_family"] == ENGINE_FAMILY_V1
    assert packet["public_claim_status"] == "internal_candidate_only"
    assert packet["public_gap_card_status"] == "public_export_blocked"


@pytest.mark.parametrize(
    "target_type",
    ["hidden_rule", "operator_candidate", "translation_candidate", "structural_match"],
)
def test_valid_targets_cover_required_shapes(target_type):
    target = _target(target_type=target_type)
    assert target["target_type"] == target_type
    assert target["target_id"]
    assert target["public_claim_status"] == "not_public_claim"
    assert target["uncertainty_factors"]
    assert target["invalidation_signals"]


@pytest.mark.parametrize(
    "research_mode",
    ["shadow_evaluation", "owner_preview", "recursive_generation", "rule_pressure_test", "public_export_blocked"],
)
def test_rule_pressure_research_mode_is_stricter_than_shared_protocol(research_mode):
    shared_packet = _packet()
    shared_packet["research_mode"] = research_mode
    protocol_validation = protocol.validate_cognitive_research_run_v1(shared_packet)
    validation = validate_rule_pressure_packet_v1(shared_packet)

    assert protocol_validation["blocked"] is False
    assert validation["valid"] is False
    assert "invalid_research_mode" in validation["violations"]


@pytest.mark.parametrize(
    "target_public_claim_status",
    ["internal_candidate_only"],
)
def test_internal_candidate_only_target_public_status_is_allowed(target_public_claim_status):
    target = _target(public_claim_status=target_public_claim_status)
    test = _test(target=target)
    result = _result(target, test, observed_result_summary="not observed yet")
    correction = _correction(target, test, result, calibration_record_ref="")
    packet = _packet(
        target=target,
        pressure_test=test,
        pressure_result=result,
        corrections=[correction],
        compressed_lesson="Pressure reveals limits; survival is not evidence.",
        public_claim_status="internal_candidate_only",
    )
    validation = validate_rule_pressure_packet_v1(packet)
    assert packet["rule_pressure_targets"][0]["public_claim_status"] == "internal_candidate_only"
    assert validation["valid"] is True


def test_public_export_blocked_packet_status_keeps_target_internal():
    packet = _packet(public_claim_status="public_export_blocked")
    validation = validate_rule_pressure_packet_v1(packet)
    assert packet["public_claim_status"] == "public_export_blocked"
    assert packet["rule_pressure_targets"][0]["public_claim_status"] == "internal_candidate_only"
    assert validation["valid"] is True


@pytest.mark.parametrize(
    "target_public_claim_status",
    ["public_safe_summary_required", "public_gap_card_candidate"],
)
def test_public_safe_target_public_status_fails_closed(target_public_claim_status):
    packet = _packet(
        pressure_test=_test(),
        pressure_result=_result(),
        corrections=[_correction()],
        compressed_lesson="Pressure reveals limits; survival is not evidence.",
    )
    packet["rule_pressure_targets"][0]["public_claim_status"] = target_public_claim_status
    validation = validate_rule_pressure_packet_v1(packet)
    assert validation["valid"] is False
    assert any("target_marked_public_claim_or_export_safe" in violation for violation in validation["violations"])


@pytest.mark.parametrize(
    "pressure_type",
    [
        "counterexample_search",
        "boundary_case",
        "noise_injection",
        "false_pattern_insertion",
        "scale_shift",
        "axiom_mutation",
        "control_case",
    ],
)
def test_valid_pressure_tests_cover_required_shapes(pressure_type):
    test = _test(pressure_type=pressure_type)
    assert test["pressure_type"] == pressure_type
    assert test["pressure_test_id"]
    assert test["safe_to_run_as_metadata"] is True
    assert test["calibration_prediction"]["prediction_type"] == "rule_pressure_prediction"


@pytest.mark.parametrize(
    "result_status",
    ["not_observed_yet", "survived_pressure", "failed_pressure"],
)
def test_valid_results_cover_required_shapes(result_status):
    result = _result(result_status=result_status, observed_result_summary="observed result" if result_status != "not_observed_yet" else "not observed yet")
    assert result["result_status"] == result_status
    assert result["pressure_result_id"]
    assert result["calibration_outcome_status"]


def test_valid_correction_covers_required_shapes():
    correction = _correction()
    assert correction["correction_id"]
    assert correction["corrected_scope"]
    assert correction["compressed_lesson"]


def test_valid_full_packet_is_protocol_compatible_and_bridge_compatible():
    target = _target(target_type="hidden_rule", candidate_rule_or_operator="hidden rule")
    test = _test(target, pressure_type="counterexample_search")
    result = _result(target, test, result_status="failed_pressure", observed_result_summary="pressure revealed a hidden assumption", breakage_type="hidden_assumption_failure", breakage_detected=True, target_survived=False, scope_changed=True, new_uncertainty=["hidden assumption exposed"], new_invalidation_signal="candidate no longer holds")
    correction = _correction(target, test, result, breakage_type="hidden_assumption_failure", corrected_scope="narrowed metadata-only scope", calibration_record_ref="")
    packet = _packet(
        target=target,
        pressure_test=test,
        pressure_result=result,
        corrections=[correction],
        compressed_lesson="Pressure reveals limits; survival is not evidence.",
        next_experiments=["narrow the scope", "add a counterexample"],
    )

    validation = validate_rule_pressure_packet_v1(packet)
    protocol_validation = protocol.validate_cognitive_research_run_v1(packet)
    bridge_validation = validate_forecast_calibration_record_v1(packet["calibration_record"])

    assert validation["valid"] is True
    assert protocol_validation["blocked"] is False
    assert protocol_validation["classification"] == ENGINE_NAME_V1
    assert bridge_validation["valid"] is True
    assert packet["rule_pressure_targets"]
    assert packet["rule_pressure_tests"]
    assert packet["rule_pressure_results"]
    assert packet["calibration_record"]["prediction_type"] == "rule_pressure_prediction"
    assert packet["predictions"]


def test_json_safe_copy_removes_unsafe_raw_fields():
    unsafe = deepcopy(_packet())
    unsafe["hidden_prompt"] = "system prompt leakage"
    unsafe["raw_response"] = "super secret raw response"
    safe = to_rule_pressure_json_safe_v1(unsafe)
    assert "hidden_prompt" not in safe
    assert "raw_response" not in safe
    json.dumps(safe, sort_keys=True)


def test_summary_is_concise_and_private_text_safe():
    packet = _packet(input_summary="raw private text with hidden system prompt")
    summary = summarize_rule_pressure_packet_v1(packet)
    assert len(summary["summary_text"]) <= 320
    assert "raw private" not in summary["summary_text"].lower()
    assert "hidden prompt" not in summary["summary_text"].lower()


def test_examples_include_required_pressure_variants():
    examples = build_initial_rule_pressure_examples_v1()
    target_types = {example["rule_pressure_targets"][0]["target_type"] for example in examples}
    pressure_types = {example["rule_pressure_tests"][0]["pressure_type"] for example in examples}
    assert "hidden_rule" in target_types
    assert "operator_candidate" in target_types
    assert "translation_candidate" in target_types
    assert "motif_candidate" in target_types
    assert "counterexample_search" in pressure_types
    assert "operator_substitution" in pressure_types
    assert "false_pattern_insertion" in pressure_types
    assert "noise_injection" in pressure_types


@pytest.mark.parametrize(
    "mutator, expected_fragment",
    [
        (lambda packet: packet["rule_pressure_targets"].__setitem__(0, {**packet["rule_pressure_targets"][0], "target_id": ""}), "missing_target_id"),
        (lambda packet: packet["rule_pressure_targets"].__setitem__(0, {**packet["rule_pressure_targets"][0], "candidate_rule_or_operator": ""}), "missing_candidate_rule_or_operator"),
        (lambda packet: packet["rule_pressure_targets"].__setitem__(0, {**packet["rule_pressure_targets"][0], "uncertainty_factors": []}), "missing_uncertainty_factors"),
        (lambda packet: packet["rule_pressure_targets"].__setitem__(0, {**packet["rule_pressure_targets"][0], "invalidation_signals": []}), "missing_invalidation_signals"),
        (lambda packet: packet["rule_pressure_targets"].__setitem__(0, {**packet["rule_pressure_targets"][0], "public_claim_status": "public_export_blocked"}), "target_marked_public_claim_or_export_safe"),
        (lambda packet: packet["rule_pressure_tests"].__setitem__(0, {**packet["rule_pressure_tests"][0], "expected_failure_mode": ""}), "missing_expected_failure_mode"),
        (lambda packet: packet["rule_pressure_tests"].__setitem__(0, {**packet["rule_pressure_tests"][0], "success_criteria": "", "failure_criteria": ""}), "missing_success_or_failure_criteria"),
        (lambda packet: packet["rule_pressure_tests"].__setitem__(0, {**packet["rule_pressure_tests"][0], "safe_to_run_as_metadata": False}), "pressure_test_executable_or_runtime_safe"),
        (lambda packet: packet["rule_pressure_results"].__setitem__(0, {**packet["rule_pressure_results"][0], "result_status": "failed_pressure", "observed_result_summary": ""}), "missing_observed_result_summary"),
        (lambda packet: packet["rule_pressure_corrections"].__setitem__(0, {**packet["rule_pressure_corrections"][0], "compressed_lesson": ""}), "missing_compressed_lesson"),
        (lambda packet: packet["rule_pressure_corrections"].__setitem__(0, {**packet["rule_pressure_corrections"][0], "breakage_type": "scope_failure", "corrected_scope": ""}), "missing_corrected_scope_after_breakage"),
    ],
)
def test_required_field_fail_closed(mutator, expected_fragment):
    packet = _packet(
        target=_target(),
        pressure_test=_test(),
        pressure_result=_result(),
        corrections=[_correction()],
        compressed_lesson="Pressure reveals limits; survival is not evidence.",
    )
    mutator(packet)
    validation = validate_rule_pressure_packet_v1(packet)
    assert validation["valid"] is False
    assert any(expected_fragment in violation for violation in validation["violations"])


@pytest.mark.parametrize(
    "packet_mutation, expected_fragment",
    [
        (lambda packet: packet["rule_pressure_results"].__setitem__(0, {**packet["rule_pressure_results"][0], "observed_result_summary": "proof of truth breakthrough"}), "proof_or_truth_claim"),
        (lambda packet: packet.__setitem__("compressed_lesson", "public breakthrough proof of a solution"), "forbidden_text_marker"),
        (lambda packet: packet.__setitem__("denied_authority", None), "missing_denied_authority"),
        (lambda packet: packet.__setitem__("safe_metadata", {"safe": False}), "unsafe_safe_metadata"),
        (lambda packet: packet.__setitem__("calibration_record", {}), "missing_calibration_record"),
    ],
)
def test_public_and_authority_fail_closed(packet_mutation, expected_fragment):
    packet = _packet(target=_target(), pressure_test=_test(), pressure_result=_result(), corrections=[_correction()], compressed_lesson="Pressure reveals limits; survival is not evidence.")
    packet_mutation(packet)
    validation = validate_rule_pressure_packet_v1(packet)
    assert validation["valid"] is False
    assert any(expected_fragment in violation for violation in validation["violations"])


@pytest.mark.parametrize(
    "summary_text",
    [
        "AGI sentience consciousness official intelligence proof",
        "final answer authority and LLM authority and runtime authority",
        "provider authority tool authority persistence memory mutation project mutation behavior pack promotion",
        ".weslr live ingestion network github rss lab notebook",
        "raw private text hidden prompt secret password api key",
    ],
)
def test_forbidden_text_markers_fail_closed(summary_text):
    packet = _packet(input_summary=summary_text, target=_target(target_summary=summary_text))
    validation = validate_rule_pressure_packet_v1(packet)
    assert validation["valid"] is False
    assert any("forbidden_text_marker" in violation for violation in validation["violations"])
