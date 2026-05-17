from __future__ import annotations

from pathlib import Path

import pytest

from weslr.plan_helper_observation_report import (
    ALLOWED_DECISIONS_V1,
    ALLOWED_QUALITY_LABELS_V1,
    SIDE_EFFECT_KEYS_V1,
    build_plan_helper_observation_report_v1,
    render_plan_helper_observation_report_markdown_v1,
    summarize_plan_helper_observation_report_v1,
    to_plan_helper_observation_report_json_safe_v1,
    validate_plan_helper_observation_report_v1,
)


REPO_HEAD = "8acae76c240df5d4dbd613223a1fd55f6d217896"
FORBIDDEN_OUTPUT_TERMS = (
    "raw_prompt",
    "response_text",
    "source_urls",
    "hidden_prompt",
    "answer_key",
    "protected_material",
)


def _safe_report(**kwargs):
    return build_plan_helper_observation_report_v1(repo_head=REPO_HEAD, timestamp_local="2026-05-17 10:28", **kwargs)


def _populated_safe_report():
    report = _safe_report(
        flag_off_baseline={"checked": True},
        flag_on_plan_checks={
            "checked": True,
            "approved_prompt_count": 2,
            "slice_metadata_present": True,
            "quality_shape_present": True,
        },
        non_plan_protection={"checked": True, "protected_prompt_count": 4},
        quality_label="useful_enough_disabled_default",
    )
    report["quality"].update(
        {
            "reaches_approved_slice": True,
            "asks_useful_clarifying_question": True,
            "includes_bounded_starter_shape": True,
        }
    )
    return report


def test_builder_default_shape():
    report = _safe_report()
    assert report["report_type"] == "plan_helper_flag_on_observation_report_v1"
    assert report["schema_version"] == "1.0"
    assert report["feature_flag"] == "WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1"
    assert report["target_branch"] == "chat_responder_plan_helper"
    assert report["target_file"] == "weslr/chat_responder.py"
    assert report["feature_flag_default"] is False
    assert report["observation_scope"] == "plan_helper_only"
    assert report["decision"] == "KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY"


def test_valid_default_report_has_only_expected_warnings():
    result = validate_plan_helper_observation_report_v1(_safe_report())
    assert result["valid"] is True
    assert result["errors"] == []
    assert "quality_label=not_observed" in result["warnings"]
    assert "approved_prompt_count=0" in result["warnings"]


def test_populated_safe_observation_report_valid():
    result = validate_plan_helper_observation_report_v1(_populated_safe_report())
    assert result == {"valid": True, "errors": [], "warnings": []}


@pytest.mark.parametrize(
    "claim_key",
    [
        "benchmark_claim",
        "turing_test_claim",
        "official_score_claim",
        "certification_claim",
        "default_enablement_claim",
        "branch_expansion_claim",
    ],
)
def test_reject_unsafe_claims(claim_key):
    report = _populated_safe_report()
    report[claim_key] = True
    result = validate_plan_helper_observation_report_v1(report)
    assert result["valid"] is False
    assert any(claim_key in error for error in result["errors"])


@pytest.mark.parametrize("side_effect_key", SIDE_EFFECT_KEYS_V1)
def test_reject_side_effects(side_effect_key):
    report = _populated_safe_report()
    report["side_effects"][side_effect_key] = True
    result = validate_plan_helper_observation_report_v1(report)
    assert result["valid"] is False
    assert any(side_effect_key in error for error in result["errors"])


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "raw_text",
        "raw_prompt",
        "response_text",
        "final_answer",
        "source_urls",
        "hidden_prompt",
        "answer_key",
        "protected_material",
    ],
)
def test_reject_raw_private_protected_fields(forbidden_key):
    report = _populated_safe_report()
    report["extra"] = {forbidden_key: "synthetic placeholder"}
    result = validate_plan_helper_observation_report_v1(report)
    assert result["valid"] is False
    assert any(forbidden_key in error for error in result["errors"])


@pytest.mark.parametrize(
    "mutator, expected",
    [
        (lambda r: r.update({"feature_flag": "OTHER_FLAG"}), "feature_flag"),
        (lambda r: r.update({"feature_flag_default": True}), "feature_flag_default"),
        (lambda r: r.update({"target_branch": "email_helper"}), "target_branch"),
        (lambda r: r.update({"target_file": "weslr/other.py"}), "target_file"),
        (lambda r: r.update({"observation_scope": "all_branches"}), "observation_scope"),
        (lambda r: r["non_plan_protection"].update({"plan_metadata_on_non_plan": True}), "plan_metadata_on_non_plan"),
        (lambda r: r["fallback"].update({"fallback_available": False}), "fallback_available"),
        (lambda r: r["cleanup"].update({"feature_flag_unset_after": False}), "feature_flag_unset_after"),
        (lambda r: r["cleanup"].update({"tracked_diff_after": True}), "tracked_diff_after"),
        (lambda r: r["cleanup"].update({"runtime_artifacts_retained": True}), "runtime_artifacts_retained"),
    ],
)
def test_reject_scope_drift(mutator, expected):
    report = _populated_safe_report()
    mutator(report)
    result = validate_plan_helper_observation_report_v1(report)
    assert result["valid"] is False
    assert any(expected in error for error in result["errors"])


def test_decision_and_quality_validation():
    for decision in ALLOWED_DECISIONS_V1:
        report = _populated_safe_report()
        report["decision"] = decision
        assert validate_plan_helper_observation_report_v1(report)["valid"] is True

    report = _populated_safe_report()
    report["decision"] = "ENABLE_BY_DEFAULT"
    assert validate_plan_helper_observation_report_v1(report)["valid"] is False

    for label in ALLOWED_QUALITY_LABELS_V1:
        report = _populated_safe_report()
        report["quality"]["quality_label"] = label
        assert validate_plan_helper_observation_report_v1(report)["valid"] is True

    report = _populated_safe_report()
    report["quality"]["quality_label"] = "benchmark_winner"
    assert validate_plan_helper_observation_report_v1(report)["valid"] is False


def test_json_safe_copy_is_not_sanitizer():
    report = _populated_safe_report()
    report["unsafe"] = {"raw_text": "synthetic unsafe field"}
    copied = to_plan_helper_observation_report_json_safe_v1(report)
    assert copied["unsafe"]["raw_text"] == "synthetic unsafe field"
    assert validate_plan_helper_observation_report_v1(copied)["valid"] is False


def test_summary_safety():
    report = _populated_safe_report()
    report["unsafe"] = {
        "raw_prompt": "synthetic",
        "response_text": "synthetic",
        "source_urls": ["https://example.invalid"],
        "hidden_prompt": "synthetic",
        "answer_key": "synthetic",
        "protected_material": "synthetic",
    }
    summary = summarize_plan_helper_observation_report_v1(report)
    text = repr(summary)
    assert summary["approved_prompt_count"] == 2
    assert summary["side_effects_clear"] is True
    for term in FORBIDDEN_OUTPUT_TERMS:
        assert term not in text


def test_markdown_safety_and_sections():
    report = _populated_safe_report()
    markdown = render_plan_helper_observation_report_markdown_v1(report)
    for section in [
        "SECTION 1 — STATUS",
        "SECTION 2 — FLAG-OFF BASELINE",
        "SECTION 3 — FLAG-ON PLAN OBSERVATION",
        "SECTION 4 — PLAN QUALITY CHECK",
        "SECTION 5 — NON-PLAN PROTECTION",
        "SECTION 6 — SIDE-EFFECT CHECK",
        "SECTION 7 — FALLBACK / ROLLBACK STATUS",
        "SECTION 8 — CLEANUP",
        "SECTION 9 — DECISION",
        "SECTION 10 — SAFETY CONFIRMATION",
    ]:
        assert section in markdown
    for term in FORBIDDEN_OUTPUT_TERMS:
        assert term not in markdown
    lowered = markdown.lower()
    assert "benchmark score" not in lowered
    assert "turing test passed" not in lowered
    assert "certification" not in lowered


def test_no_side_effect_files_created(tmp_path):
    before = set(Path.cwd().glob(".weslr*"))
    report = _populated_safe_report()
    validate_plan_helper_observation_report_v1(report)
    summarize_plan_helper_observation_report_v1(report)
    render_plan_helper_observation_report_markdown_v1(report)
    to_plan_helper_observation_report_json_safe_v1(report)
    after = set(Path.cwd().glob(".weslr*"))
    assert after == before
