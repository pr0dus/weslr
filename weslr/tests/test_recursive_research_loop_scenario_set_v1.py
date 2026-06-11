from __future__ import annotations

from copy import deepcopy
import json

import pytest

from weslr.minimal_recursive_research_loop_dry_run_executor import (
    validate_minimal_recursive_research_loop_result_v1,
)
from weslr.recursive_research_loop_scenario_set import (
    build_recursive_research_loop_scenario_set_v1,
    build_recursive_research_loop_scenario_v1,
    run_recursive_research_loop_scenario_set_v1,
    summarize_recursive_research_loop_scenario_set_v1,
    to_recursive_research_loop_scenario_set_json_safe_v1,
    validate_recursive_research_loop_scenario_set_result_v1,
    validate_recursive_research_loop_scenario_v1,
)

_REQUIRED_FAMILIES_V1 = {
    "ambiguous_pattern_signal",
    "contradictory_signal",
    "weak_signal_noise",
    "cross_domain_resonance_signal",
    "pressure_test_candidate",
    "calibration_needed_signal",
    "blocked_public_claim_signal",
    "archive_low_value_signal",
}


def _base_scenario(family: str = "ambiguous_pattern_signal"):
    return build_recursive_research_loop_scenario_v1({"scenario_family": family})


def test_build_recursive_research_loop_scenario_set_v1_covers_all_required_families() -> None:
    scenario_set = build_recursive_research_loop_scenario_set_v1()

    assert scenario_set["scenario_count"] == 8
    assert len(scenario_set["scenarios"]) == 8
    assert {item["scenario_family"] for item in scenario_set["scenarios"]} == _REQUIRED_FAMILIES_V1
    assert all(validate_recursive_research_loop_scenario_v1(item)["valid"] for item in scenario_set["scenarios"])


def test_run_recursive_research_loop_scenario_set_v1_validates_and_summarizes() -> None:
    result = run_recursive_research_loop_scenario_set_v1()
    validation = validate_recursive_research_loop_scenario_set_result_v1(result)
    summary = summarize_recursive_research_loop_scenario_set_v1(result)

    assert validation["valid"]
    assert result["scenario_set_id"] == "recursive_research_loop_scenario_set_v1"
    assert result["total_scenarios"] == 8
    assert result["completed_scenarios"] == 8
    assert result["blocked_scenarios"] == 0
    assert result["next_step_distribution"].get("calibrate") == 8
    assert result["stage_failure_distribution"] == {}
    assert result["safety_authority_status"]["all_authority_flags_false"] is True
    assert "next_step_distribution=" in summary
    assert "stage_failure_distribution=" in summary
    assert "safety_authority_status=" in summary
    assert all(item["completion_status"] == "completed" for item in result["scenario_results"])
    assert all(item["dry_run_validation"]["valid"] for item in result["scenario_results"])
    assert all(
        validate_minimal_recursive_research_loop_result_v1(item["dry_run_result"])["valid"]
        for item in result["scenario_results"]
    )


def test_recursive_research_loop_scenario_set_json_safe_redacts_unsafe_raw_fields() -> None:
    class _Opaque:
        pass

    def _callable_marker():
        return "not used"

    result = run_recursive_research_loop_scenario_set_v1()
    result["scenario_results"][0]["dry_run_result"][1] = "numeric key value"
    result["scenario_results"][0]["dry_run_result"]["raw_private_text"] = "hidden prompt secret provider call .weslr"
    result["scenario_results"][0]["dry_run_result"]["extra"] = {2, 1}
    result["scenario_results"][0]["dry_run_result"]["bytes_value"] = b"abc"
    result["scenario_results"][0]["dry_run_result"]["opaque_value"] = _Opaque()
    result["scenario_results"][0]["dry_run_result"]["callable_value"] = _callable_marker
    safe = to_recursive_research_loop_scenario_set_json_safe_v1(result)

    assert safe["scenario_results"][0]["dry_run_result"]["1"] == "numeric key value"
    assert safe["scenario_results"][0]["dry_run_result"]["raw_private_text"] == "[redacted]"
    assert safe["scenario_results"][0]["dry_run_result"]["extra"] == [1, 2]
    assert safe["scenario_results"][0]["dry_run_result"]["bytes_value"] == "[redacted:bytes]"
    assert safe["scenario_results"][0]["dry_run_result"]["opaque_value"] == "[redacted:_Opaque]"
    assert safe["scenario_results"][0]["dry_run_result"]["callable_value"].startswith("[redacted:")
    assert json.dumps(safe)
    assert "hidden prompt" not in repr(safe).lower()
    assert ".weslr" not in repr(safe).lower()


@pytest.mark.parametrize(
    ("mutator", "expected_label"),
    [
        (lambda scenario: scenario.pop("scenario_id"), "missing_scenario_id"),
        (lambda scenario: scenario.pop("scenario_family"), "missing_scenario_family"),
        (lambda scenario: scenario.__setitem__("scenario_family", "bogus_family"), "invalid_scenario_family"),
        (lambda scenario: scenario.pop("input_signal"), "missing_input_signal"),
        (lambda scenario: scenario.__setitem__("public_claim_authorized", True), "unsafe_public_claim_authorized"),
        (lambda scenario: scenario.__setitem__("runtime_action_authorized", True), "unsafe_runtime_action_authorized"),
        (lambda scenario: scenario.__setitem__("storage_write_authorized", True), "unsafe_storage_write_authorized"),
        (lambda scenario: scenario.__setitem__("memory_mutation_authorized", True), "unsafe_memory_mutation_authorized"),
        (lambda scenario: scenario.__setitem__("behavior_promotion_authorized", True), "unsafe_behavior_promotion_authorized"),
    ],
)
def test_recursive_research_loop_scenario_validation_fail_closed_on_required_fields_and_authority_flags(
    mutator,
    expected_label,
) -> None:
    scenario = _base_scenario()
    mutator(scenario)
    validation = validate_recursive_research_loop_scenario_v1(scenario)

    assert not validation["valid"]
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    ("signal_summary", "expected_label"),
    [
        ("hidden prompt secret", "forbidden_input_signal_text"),
        ("system prompt api key", "forbidden_input_signal_text"),
        ("provider call tool execution retrieval", "forbidden_input_signal_text"),
        (".weslr path reference", "forbidden_input_signal_text"),
        ("live ingestion should stay blocked", "forbidden_input_signal_text"),
        ("public discovery proof breakthrough claim", "forbidden_input_signal_text"),
        ("AGI sentience consciousness claim", "forbidden_input_signal_text"),
    ],
)
def test_recursive_research_loop_scenario_validation_fail_closed_on_private_or_public_implication_texts(
    signal_summary,
    expected_label,
) -> None:
    scenario = _base_scenario()
    scenario["input_signal"]["signal_summary"] = signal_summary
    validation = validate_recursive_research_loop_scenario_v1(scenario)

    assert not validation["valid"]
    assert expected_label in validation["blocked_labels"]


def test_recursive_research_loop_scenario_validation_fail_closed_on_public_breakthrough_and_final_answer_authority() -> None:
    scenario = _base_scenario()
    scenario["public_claim_status"] = "public_breakthrough_claim"
    scenario["denied_authority"]["final_answer_generation_authority"] = True
    validation = validate_recursive_research_loop_scenario_v1(scenario)

    assert not validation["valid"]
    assert "public_breakthrough_claim" in validation["blocked_labels"]
    assert "granted_denied_authority" in validation["blocked_labels"]


def test_recursive_research_loop_scenario_set_result_fail_closed_on_invalid_dry_run_output() -> None:
    result = run_recursive_research_loop_scenario_set_v1()
    result["scenario_results"][0].pop("dry_run_result")
    validation = validate_recursive_research_loop_scenario_set_result_v1(result)

    assert not validation["valid"]
    assert "missing_dry_run_result" in validation["blocked_labels"]


def test_recursive_research_loop_scenario_set_result_fail_closed_on_missing_distribution_summary() -> None:
    result = run_recursive_research_loop_scenario_set_v1()
    result.pop("next_step_distribution")
    validation = validate_recursive_research_loop_scenario_set_result_v1(result)

    assert not validation["valid"]
    assert "missing_next_step_distribution" in validation["blocked_labels"]


def test_recursive_research_loop_scenario_set_result_fail_closed_on_nested_non_json_safe_values() -> None:
    result = run_recursive_research_loop_scenario_set_v1()
    result["scenario_results"][0]["dry_run_result"]["extra"] = {1, 2}
    validation = validate_recursive_research_loop_scenario_set_result_v1(result)

    assert not validation["valid"]
    assert "non_json_safe_result_structure" in validation["blocked_labels"]
