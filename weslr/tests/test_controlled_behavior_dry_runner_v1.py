from __future__ import annotations

from pathlib import Path

import pytest

from weslr.behavior_evaluation_report import ALLOWED_EVALUATION_FAMILIES_V1
from weslr.controlled_behavior_dry_runner import (
    build_controlled_behavior_dry_observation_v1,
    derive_family_label_from_observations_v1,
    derive_readiness_label_from_family_results_v1,
    render_controlled_behavior_dry_run_markdown_v1,
    run_controlled_behavior_evaluation_dry_v1,
    summarize_controlled_behavior_dry_run_v1,
    to_controlled_behavior_dry_run_json_safe_v1,
    validate_controlled_behavior_dry_run_result_v1,
)
from weslr.controlled_behavior_prompt_set import build_default_controlled_behavior_prompt_set_v1

REPO_HEAD = "6cd6364236f8b2ae9983864d60f1f07ccb362666"
FORBIDDEN_OUTPUT_TERMS = (
    "raw_prompt",
    "response_text",
    "source_urls",
    "hidden_prompt",
    "answer_key",
    "protected_material",
)


def _result(**kwargs):
    return run_controlled_behavior_evaluation_dry_v1(repo_head=REPO_HEAD, timestamp_local="2026-05-17 12:31", **kwargs)


def test_dry_observation_builder_shape_and_label_rules():
    observation = build_controlled_behavior_dry_observation_v1(
        prompt_id="ordinary_task_behavior_001",
        family="ordinary_task_behavior",
        property_label="pass_property",
        observed=True,
        expected_properties_seen=["bounded", "useful"],
        missing_properties=[],
        safe_summary="Bounded synthetic dry metadata observed.",
    )
    assert observation["prompt_id"] == "ordinary_task_behavior_001"
    assert observation["family"] == "ordinary_task_behavior"
    assert observation["property_label"] == "pass_property"
    assert observation["observed"] is True
    assert "raw_prompt" not in observation
    assert "response_text" not in observation
    with pytest.raises(ValueError):
        build_controlled_behavior_dry_observation_v1(prompt_id="x", family="ordinary_task_behavior", property_label="score_99")


def test_raw_private_summary_rejected_by_validator_when_inserted_into_result():
    result = _result()
    result["family_results"]["ordinary_task_behavior"]["evidence_properties"]["observations"][0]["safe_summary"] = "contains raw private placeholder"
    result["family_results"]["ordinary_task_behavior"]["evidence_properties"]["observations"][0]["raw_text"] = "synthetic unsafe"
    validation = validate_controlled_behavior_dry_run_result_v1(result)
    assert validation["valid"] is False
    assert any("raw_text" in error for error in validation["errors"])


def test_default_dry_runner_safe_shape_and_report_valid():
    result = _result()
    assert result["runner_type"] == "weslr_controlled_behavior_evaluation_dry_runner_v1"
    assert result["dry_run"] is True
    assert result["prompt_execution"] is False
    assert result["chat_responder_calls"] is False
    assert result["model_calls"] is False
    assert result["advisor_calls"] is False
    assert result["web_search"] is False
    assert result["numeric_scores_used"] is False
    assert result["official_benchmark_claim"] is False
    assert result["turing_test_claim"] is False
    assert result["iq_claim"] is False
    assert result["certification_claim"] is False
    assert result["report"]["report_type"] == "weslr_behavior_evaluation_report_v1"
    assert result["validation"]["valid"] is True


def test_observation_overrides_safe_metadata_accepted():
    result = _result(
        observation_overrides={
            "ordinary_task_behavior_001": {
                "property_label": "pass_property",
                "observed": True,
                "expected_properties_seen": ["bounded", "useful"],
                "missing_properties": [],
                "safe_summary": "Bounded ordinary-task behavior observed in synthetic dry metadata.",
            },
            "conduct_alignment_001": {
                "property_label": "pass_property",
                "observed": True,
                "expected_properties_seen": ["transparent_uncertainty"],
                "missing_properties": [],
                "safe_summary": "Boundary-following metadata observed in synthetic dry metadata.",
            },
            "live_slice_behavior_001": {
                "property_label": "pass_property",
                "observed": True,
                "expected_properties_seen": ["plan_slice_metadata_when_enabled"],
                "missing_properties": [],
                "safe_summary": "Approved live-slice metadata observed in synthetic dry metadata.",
            },
        }
    )
    assert result["validation"]["valid"] is True
    assert result["family_results"]["ordinary_task_behavior"]["label"] == "pass_property"
    assert result["family_results"]["conduct_alignment"]["label"] == "pass_property"
    assert result["report"]["readiness_label"] == "bounded_task_readiness"


@pytest.mark.parametrize("bad_key", ["response_text", "raw_text", "source_urls"])
def test_observation_overrides_reject_raw_response_and_source_fields(bad_key):
    result = _result(observation_overrides={"ordinary_task_behavior_001": {bad_key: "synthetic unsafe"}})
    assert result["validation"]["valid"] is False
    assert any(bad_key in error for error in result["validation"]["errors"])


def test_observation_overrides_unknown_prompt_id_invalid():
    result = _result(observation_overrides={"unknown_prompt": {"property_label": "pass_property"}})
    assert result["validation"]["valid"] is False
    assert any("unknown" in error for error in result["validation"]["errors"])


@pytest.mark.parametrize("flag", ["model_calls", "advisor_calls", "web_search", "solver_execution", "answer_selection_arbitration"])
def test_observation_overrides_cannot_request_execution_flags(flag):
    result = _result(observation_overrides={"ordinary_task_behavior_001": {flag: True}})
    assert result["validation"]["valid"] is False
    assert any(flag in error for error in result["validation"]["errors"])


def test_family_label_derivation_rules():
    assert derive_family_label_from_observations_v1([{"property_label": "pass_property"}, {"property_label": "fail_property"}]) == "fail_property"
    assert derive_family_label_from_observations_v1([{"property_label": "pass_property", "blocked_by_boundary": True}]) == "blocked_by_boundary"
    assert derive_family_label_from_observations_v1([{"property_label": "needs_review"}]) == "needs_review"
    assert derive_family_label_from_observations_v1([{"property_label": "pass_property"}]) == "pass_property"
    assert derive_family_label_from_observations_v1([]) == "not_observed"


def _families_with(label: str):
    return {family: {"label": label} for family in ALLOWED_EVALUATION_FAMILIES_V1}


def test_readiness_derivation_rules():
    families = _families_with("pass_property")
    families["memory_honesty"] = {"label": "fail_property"}
    assert derive_readiness_label_from_family_results_v1(families) == "unsafe_or_inconsistent"

    families = _families_with("not_observed")
    families["live_slice_behavior"] = {"label": "pass_property"}
    families["conduct_alignment"] = {"label": "pass_property"}
    assert derive_readiness_label_from_family_results_v1(families) == "bounded_task_readiness"

    assert derive_readiness_label_from_family_results_v1(_families_with("not_observed")) == "needs_more_observation"
    assert derive_readiness_label_from_family_results_v1(_families_with("pass_property")) == "early_internal_readiness"


@pytest.mark.parametrize(
    "flag",
    [
        "prompt_execution",
        "chat_responder_calls",
        "model_calls",
        "advisor_calls",
        "web_search",
        "numeric_scores_used",
        "official_benchmark_claim",
        "turing_test_claim",
        "iq_claim",
        "certification_claim",
        "raw_private_text_included",
        "weslr_runtime_state_created",
    ],
)
def test_result_validation_rejects_unsafe_flags(flag):
    result = _result()
    result[flag] = True
    validation = validate_controlled_behavior_dry_run_result_v1(result)
    assert validation["valid"] is False
    assert any(flag in error for error in validation["errors"])


@pytest.mark.parametrize("forbidden_key", ["raw_text", "raw_prompt", "response_text", "final_answer", "full_conversation", "source_urls", "hidden_prompt", "answer_key", "protected_material"])
def test_result_validation_rejects_forbidden_keys(forbidden_key):
    result = _result()
    result["unsafe"] = {forbidden_key: "synthetic unsafe"}
    validation = validate_controlled_behavior_dry_run_result_v1(result)
    assert validation["valid"] is False
    assert any(forbidden_key in error for error in validation["errors"])


@pytest.mark.parametrize("phrase", ["passed Turing test", "official benchmark", "IQ score", "conscious", "sentient"])
def test_result_validation_rejects_forbidden_claim_text(phrase):
    result = _result()
    result["unsafe"] = {"claim": phrase}
    validation = validate_controlled_behavior_dry_run_result_v1(result)
    assert validation["valid"] is False
    assert any(phrase.lower() in error for error in validation["errors"])


def test_json_safe_copy_is_not_sanitizer():
    result = _result()
    result["unsafe"] = {"raw_text": "synthetic unsafe"}
    copied = to_controlled_behavior_dry_run_json_safe_v1(result)
    assert copied["unsafe"]["raw_text"] == "synthetic unsafe"
    assert validate_controlled_behavior_dry_run_result_v1(copied)["valid"] is False


def test_summary_safety_labels_counts_status_only():
    result = _result()
    result["unsafe"] = {
        "raw_prompt": "synthetic",
        "response_text": "synthetic",
        "source_urls": ["https://example.invalid"],
        "hidden_prompt": "synthetic",
        "answer_key": "synthetic",
        "protected_material": "synthetic",
    }
    summary = summarize_controlled_behavior_dry_run_v1(result)
    text = repr(summary)
    assert summary["prompt_count"] == build_default_controlled_behavior_prompt_set_v1()["prompts"].__len__()
    assert summary["family_count"] == len(ALLOWED_EVALUATION_FAMILIES_V1)
    for term in FORBIDDEN_OUTPUT_TERMS:
        assert term not in text
    assert "://" not in text


def test_markdown_safety_sections_and_no_raw_dump_or_claims():
    markdown = render_controlled_behavior_dry_run_markdown_v1(_result())
    for section in [
        "SECTION 1 — STATUS",
        "SECTION 2 — DRY RUN BOUNDARIES",
        "SECTION 3 — FAMILY RESULTS",
        "SECTION 4 — READINESS LABEL",
        "SECTION 5 — SAFETY / CLAIM BOUNDARIES",
        "SECTION 6 — VALIDATION SUMMARY",
        "SECTION 7 — RECOMMENDED NEXT STEP",
    ]:
        assert section in markdown
    lowered = markdown.lower()
    for term in FORBIDDEN_OUTPUT_TERMS:
        assert term not in lowered
    assert "://" not in lowered
    assert "official benchmark" not in lowered
    assert "passed turing test" not in lowered
    assert "certification" not in lowered
    assert "iq score" not in lowered
    assert "conscious" not in lowered
    assert "sentient" not in lowered


def test_no_side_effects_from_helpers():
    before = set(Path.cwd().glob(".weslr*"))
    result = _result()
    validate_controlled_behavior_dry_run_result_v1(result)
    summarize_controlled_behavior_dry_run_v1(result)
    render_controlled_behavior_dry_run_markdown_v1(result)
    to_controlled_behavior_dry_run_json_safe_v1(result)
    after = set(Path.cwd().glob(".weslr*"))
    assert after == before
    assert result["chat_responder_calls"] is False
    assert result["model_calls"] is False
    assert result["advisor_calls"] is False
    assert result["web_search"] is False
