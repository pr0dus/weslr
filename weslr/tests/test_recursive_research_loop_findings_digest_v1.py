from __future__ import annotations

import json
from copy import deepcopy

import pytest

from weslr.recursive_research_loop_findings_digest import (
    FORBIDDEN_INTERPRETATIONS_V1,
    SCHEMA_VERSION_V1,
    build_initial_recursive_research_loop_findings_digest_examples_v1,
    build_recursive_research_loop_findings_digest_v1,
    render_recursive_research_loop_findings_digest_markdown_v1,
    summarize_recursive_research_loop_findings_digest_v1,
    to_recursive_research_loop_findings_digest_json_safe_v1,
    validate_recursive_research_loop_findings_digest_v1,
)
from weslr.recursive_research_loop_scenario_set import run_recursive_research_loop_scenario_set_v1

SOURCE_COMMIT_V1 = "f118a6990d992197c8313f0a7562e6334dd93880"
BASE_SOURCE_RESULT_V1 = run_recursive_research_loop_scenario_set_v1()
BASE_DIGEST_V1 = build_recursive_research_loop_findings_digest_v1(
    {
        "scenario_set_result": BASE_SOURCE_RESULT_V1,
        "source_run_id": BASE_SOURCE_RESULT_V1["scenario_set_id"],
        "source_commit": SOURCE_COMMIT_V1,
    }
)


def _base_digest():
    return deepcopy(BASE_DIGEST_V1)


def test_build_digest_covers_all_families_and_limitation() -> None:
    digest = _base_digest()
    validation = validate_recursive_research_loop_findings_digest_v1(digest)
    summary = summarize_recursive_research_loop_findings_digest_v1(digest)

    assert validation["valid"]
    assert digest["schema_version"] == SCHEMA_VERSION_V1
    assert len(digest["scenario_families"]) == 8
    assert digest["scenario_families"] == [
        "ambiguous_pattern_signal",
        "contradictory_signal",
        "weak_signal_noise",
        "cross_domain_resonance_signal",
        "pressure_test_candidate",
        "calibration_needed_signal",
        "blocked_public_claim_signal",
        "archive_low_value_signal",
    ]
    assert digest["next_step_distribution"] == {"calibrate": 8}
    assert digest["scenario_count"] == 8
    assert digest["completed_count"] == 8
    assert digest["validated_count"] == 8
    assert digest["stage_failure_count"] == 0
    assert any("All 8 scenario families currently converge to `calibrate`" in item for item in digest["current_limitations"])
    assert any("calibrate: 8" in item for item in digest["cross_family_patterns"])
    assert "calibrate:8" in summary
    assert "limitation=All 8 scenario families currently converge to `calibrate`" in summary


def test_digest_markdown_renders_expected_sections_safely() -> None:
    digest = _base_digest()
    markdown = render_recursive_research_loop_findings_digest_markdown_v1(digest)
    safe = to_recursive_research_loop_findings_digest_json_safe_v1(digest)

    assert "## What WESLR Ran" in markdown
    assert "## What Completed" in markdown
    assert "## What WESLR Appears To Notice" in markdown
    assert "## Candidate Insights" in markdown
    assert "## Candidate Pressure Directions" in markdown
    assert "## Candidate Calibration Directions" in markdown
    assert "## Current Decision-Layer Limitation" in markdown
    assert "## What This Is Not" in markdown
    assert "## What To Do Next" in markdown
    assert "All 8 scenario families currently converge to `calibrate`" in markdown
    assert json.dumps(safe)


def test_initial_digest_examples_build_successfully() -> None:
    examples = build_initial_recursive_research_loop_findings_digest_examples_v1()

    assert len(examples) >= 1
    for example in examples:
        validation = validate_recursive_research_loop_findings_digest_v1(example)
        assert validation["valid"]
        assert example["scenario_count"] == 8
        assert example["next_step_distribution"] == {"calibrate": 8}


@pytest.mark.parametrize(
    ("mutator", "expected_label"),
    [
        (lambda digest: digest.pop("digest_id"), "missing_digest_id"),
        (lambda digest: digest.pop("source_run_id"), "missing_source_run_id"),
        (lambda digest: digest.pop("scenario_families"), "missing_scenario_families"),
        (lambda digest: digest.pop("next_step_distribution"), "missing_next_step_distribution"),
        (lambda digest: digest.pop("current_limitations"), "missing_current_limitations"),
        (lambda digest: digest.pop("forbidden_interpretations"), "missing_forbidden_interpretations"),
        (lambda digest: digest.pop("authority_status"), "missing_authority_status"),
        (lambda digest: digest.pop("safe_metadata"), "missing_safe_metadata"),
    ],
)
def test_digest_validation_fail_closed_on_required_fields(mutator, expected_label) -> None:
    digest = _base_digest()
    mutator(digest)
    validation = validate_recursive_research_loop_findings_digest_v1(digest)

    assert not validation["valid"]
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    ("field", "value", "expected_label"),
    [
        ("candidate_insights", ["discovery claim"], "forbidden_claim_language"),
        ("candidate_pressure_directions", ["proof claim"], "forbidden_claim_language"),
        ("candidate_calibration_directions", ["breakthrough claim"], "forbidden_claim_language"),
        ("current_limitations", ["scientific result claim"], "forbidden_claim_language"),
        ("operator_reading_summary", "hidden prompt secret", "forbidden_private_text"),
        ("operator_reading_summary", "api key and .weslr", "forbidden_private_text"),
    ],
)
def test_digest_validation_fail_closed_on_forbidden_language_and_private_text(field, value, expected_label) -> None:
    digest = _base_digest()
    digest[field] = value
    validation = validate_recursive_research_loop_findings_digest_v1(digest)

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
def test_digest_validation_fail_closed_on_unsafe_authority(field) -> None:
    digest = _base_digest()
    digest["authority_status"][field] = True
    validation = validate_recursive_research_loop_findings_digest_v1(digest)

    assert not validation["valid"]
    assert f"unsafe_{field}" in validation["blocked_labels"]


def test_digest_validation_fail_closed_on_missing_limitation_and_distribution() -> None:
    digest = _base_digest()
    digest["current_limitations"] = ["other limitation"]
    validation = validate_recursive_research_loop_findings_digest_v1(digest)
    assert not validation["valid"]
    assert "missing_calibrate_limitation" in validation["blocked_labels"]

    digest = _base_digest()
    digest.pop("next_step_distribution")
    validation = validate_recursive_research_loop_findings_digest_v1(digest)
    assert not validation["valid"]
    assert "missing_next_step_distribution" in validation["blocked_labels"]


def test_digest_validation_fail_closed_on_non_json_safe_nested_value_and_safe_helper_recovers() -> None:
    digest = _base_digest()
    digest["family_level_notes"][0]["extra"] = {1, 2}
    validation = validate_recursive_research_loop_findings_digest_v1(digest)
    assert not validation["valid"]
    assert "non_json_safe_result_structure" in validation["blocked_labels"]

    safe = to_recursive_research_loop_findings_digest_json_safe_v1(digest)
    assert json.dumps(safe)
    assert safe["family_level_notes"][0]["extra"] == [1, 2]


def test_digest_validation_accepts_canonical_forbidden_interpretation_list() -> None:
    digest = _base_digest()
    assert digest["forbidden_interpretations"] == list(FORBIDDEN_INTERPRETATIONS_V1)
    validation = validate_recursive_research_loop_findings_digest_v1(digest)
    assert validation["valid"]
