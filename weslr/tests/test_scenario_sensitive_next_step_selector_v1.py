from __future__ import annotations

import json
from copy import deepcopy

import pytest

from weslr.recursive_research_loop_findings_digest import build_recursive_research_loop_findings_digest_v1
from weslr.recursive_research_loop_scenario_set import run_recursive_research_loop_scenario_set_v1
from weslr.scenario_sensitive_next_step_selector import (
    ALLOWED_NEXT_STEP_LABELS_V1,
    SCHEMA_VERSION_V1,
    build_initial_scenario_sensitive_next_step_examples_v1,
    build_scenario_sensitive_next_step_input_v1,
    build_scenario_sensitive_next_step_packet_v1,
    select_scenario_sensitive_next_step_v1,
    summarize_scenario_sensitive_next_step_packet_v1,
    to_scenario_sensitive_next_step_json_safe_v1,
    validate_scenario_sensitive_next_step_packet_v1,
)

SOURCE_COMMIT_V1 = "c94aadddd7a0f37d20ddf7cb1f7a02c41e73902b"
BASE_SCENARIO_SET_RESULT_V1 = run_recursive_research_loop_scenario_set_v1()
BASE_FINDINGS_DIGEST_V1 = build_recursive_research_loop_findings_digest_v1(
    {
        "scenario_set_result": BASE_SCENARIO_SET_RESULT_V1,
        "source_run_id": BASE_SCENARIO_SET_RESULT_V1["scenario_set_id"],
        "source_commit": SOURCE_COMMIT_V1,
    }
)


def _scenario_result(family: str):
    for item in BASE_SCENARIO_SET_RESULT_V1["scenario_results"]:
        if item["scenario_family"] == family:
            return deepcopy(item)
    raise AssertionError(f"missing scenario family: {family}")


def _base_input(family: str):
    return build_scenario_sensitive_next_step_input_v1(
        {
            "scenario_set_result": BASE_SCENARIO_SET_RESULT_V1,
            "findings_digest": BASE_FINDINGS_DIGEST_V1,
            "scenario_result": _scenario_result(family),
            "scenario_family": family,
            "source_run_id": BASE_SCENARIO_SET_RESULT_V1["scenario_set_id"],
            "source_commit": SOURCE_COMMIT_V1,
        }
    )


def _base_packet(family: str):
    return build_scenario_sensitive_next_step_packet_v1(_base_input(family))


def test_build_examples_cover_all_families_and_validate() -> None:
    examples = build_initial_scenario_sensitive_next_step_examples_v1()

    assert len(examples) == 8
    assert {item["scenario_family"] for item in examples} == {
        "ambiguous_pattern_signal",
        "contradictory_signal",
        "weak_signal_noise",
        "cross_domain_resonance_signal",
        "pressure_test_candidate",
        "calibration_needed_signal",
        "blocked_public_claim_signal",
        "archive_low_value_signal",
    }
    for example in examples:
        validation = validate_scenario_sensitive_next_step_packet_v1(example)
        assert validation["valid"]
        assert example["schema_version"] == SCHEMA_VERSION_V1
        assert example["selected_next_step"] in ALLOWED_NEXT_STEP_LABELS_V1
        assert json.dumps(to_scenario_sensitive_next_step_json_safe_v1(example))


def test_family_mapping_selects_expected_safe_next_steps() -> None:
    assert select_scenario_sensitive_next_step_v1(_base_input("ambiguous_pattern_signal")) == "probe"
    assert select_scenario_sensitive_next_step_v1(_base_input("contradictory_signal")) == "pressure_test"
    assert select_scenario_sensitive_next_step_v1(_base_input("cross_domain_resonance_signal")) == "probe"
    assert select_scenario_sensitive_next_step_v1(_base_input("pressure_test_candidate")) == "pressure_test"
    assert select_scenario_sensitive_next_step_v1(_base_input("calibration_needed_signal")) == "calibrate"
    assert select_scenario_sensitive_next_step_v1(_base_input("archive_low_value_signal")) == "archive"
    assert select_scenario_sensitive_next_step_v1(_base_input("blocked_public_claim_signal")) in {"operator_review", "blocked"}
    assert select_scenario_sensitive_next_step_v1(_base_input("weak_signal_noise")) in {"watch", "archive"}


def test_validation_failure_selects_needs_repair_and_unsafe_authority_selects_blocked() -> None:
    invalid = _base_input("ambiguous_pattern_signal")
    invalid["validation_signal"]["valid"] = False
    assert select_scenario_sensitive_next_step_v1(invalid) == "needs_repair"

    unsafe = _base_input("ambiguous_pattern_signal")
    unsafe["authority_status"]["runtime_action_authorized"] = True
    assert select_scenario_sensitive_next_step_v1(unsafe) == "blocked"


def test_unknown_family_is_internal_only() -> None:
    packet = _base_input("ambiguous_pattern_signal")
    packet["scenario_family"] = "unknown_family"
    selected = select_scenario_sensitive_next_step_v1(packet)
    assert selected in {"unknown", "operator_review"}


def test_packet_validates_and_summarizes() -> None:
    packet = _base_packet("ambiguous_pattern_signal")
    validation = validate_scenario_sensitive_next_step_packet_v1(packet)
    summary = summarize_scenario_sensitive_next_step_packet_v1(packet)

    assert validation["valid"]
    assert packet["selected_next_step"] == "probe"
    assert summary["selected_next_step"] == "probe"
    assert "Scenario-sensitive selector" in summary["summary_text"]
    assert json.dumps(to_scenario_sensitive_next_step_json_safe_v1(packet))


@pytest.mark.parametrize(
    ("mutator", "expected_label"),
    [
        (lambda packet: packet.pop("selector_id"), "missing_selector_id"),
        (lambda packet: packet.pop("scenario_family"), "missing_scenario_family"),
        (lambda packet: packet.pop("selected_next_step"), "missing_selected_next_step"),
        (lambda packet: packet.__setitem__("selected_next_step", "not_allowed"), "invalid_selected_next_step"),
        (lambda packet: packet.pop("selection_reason"), "missing_selection_reason"),
        (lambda packet: packet.pop("denied_authority"), "missing_denied_authority"),
        (lambda packet: packet.pop("authority_status"), "missing_authority_status"),
        (lambda packet: packet.pop("safe_metadata"), "missing_safe_metadata"),
    ],
)
def test_validation_fail_closed_on_required_fields(mutator, expected_label) -> None:
    packet = _base_packet("ambiguous_pattern_signal")
    mutator(packet)
    validation = validate_scenario_sensitive_next_step_packet_v1(packet)

    assert not validation["valid"]
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field",
    [
        "runtime_action_authorized",
        "storage_write_authorized",
        "memory_mutation_authorized",
        "project_mutation_authorized",
        "behavior_promotion_authorized",
        "public_claim_authorized",
        "final_answer_authority",
        "provider_model_call_authority",
        "retrieval_tool_authority",
    ],
)
def test_validation_fail_closed_on_unsafe_authority(field) -> None:
    packet = _base_packet("ambiguous_pattern_signal")
    packet["authority_status"][field] = True
    validation = validate_scenario_sensitive_next_step_packet_v1(packet)

    assert not validation["valid"]
    assert f"unsafe_{field}" in validation["blocked_labels"]


def test_validation_fail_closed_on_forbidden_claim_language_and_private_text() -> None:
    packet = _base_packet("ambiguous_pattern_signal")
    packet["selection_reason"] = "discovery proof breakthrough scientific result"
    validation = validate_scenario_sensitive_next_step_packet_v1(packet)
    assert not validation["valid"]
    assert "forbidden_claim_language" in validation["blocked_labels"]

    packet = _base_packet("ambiguous_pattern_signal")
    packet["gap_signal"] = "hidden prompt api key .weslr"
    validation = validate_scenario_sensitive_next_step_packet_v1(packet)
    assert not validation["valid"]
    assert "forbidden_claim_language" in validation["blocked_labels"] or "unsafe_denied_authority" in validation["blocked_labels"]

    packet = _base_packet("ambiguous_pattern_signal")
    packet["source_run_id"] = "hidden prompt secret"
    validation = validate_scenario_sensitive_next_step_packet_v1(packet)
    assert not validation["valid"]
    assert "forbidden_claim_language" in validation["blocked_labels"]


def test_validation_fail_closed_on_non_json_safe_nested_value_and_safe_helper_recovers() -> None:
    packet = _base_packet("ambiguous_pattern_signal")
    packet["operator_notes"] = [{"unsafe": {1, 2}}]
    validation = validate_scenario_sensitive_next_step_packet_v1(packet)

    assert not validation["valid"]
    assert "non_json_safe_result_structure" in validation["blocked_labels"]

    safe = to_scenario_sensitive_next_step_json_safe_v1(packet)
    assert json.dumps(safe)
    assert safe["operator_notes"][0]["unsafe"] == [1, 2]


def test_validation_accepts_needs_repair_and_safe_blocked_states() -> None:
    needs_repair = _base_packet("ambiguous_pattern_signal")
    needs_repair["validation_signal"]["valid"] = False
    needs_repair["selected_next_step"] = "needs_repair"
    validation = validate_scenario_sensitive_next_step_packet_v1(needs_repair)
    assert validation["valid"]

    blocked = _base_packet("blocked_public_claim_signal")
    blocked["selected_next_step"] = "blocked"
    validation = validate_scenario_sensitive_next_step_packet_v1(blocked)
    assert validation["valid"]
