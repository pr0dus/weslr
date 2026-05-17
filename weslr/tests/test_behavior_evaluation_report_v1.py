from pathlib import Path

import pytest

from weslr.behavior_evaluation_report import (
    ALLOWED_EVALUATION_FAMILIES_V1,
    ALLOWED_PROPERTY_LABELS_V1,
    ALLOWED_READINESS_LABELS_V1,
    SIDE_EFFECT_FLAGS_V1,
    build_behavior_evaluation_family_v1,
    build_behavior_evaluation_report_from_family_summaries_v1,
    build_behavior_evaluation_report_v1,
    render_behavior_evaluation_report_markdown_v1,
    summarize_behavior_evaluation_report_v1,
    to_behavior_evaluation_report_json_safe_v1,
    validate_behavior_evaluation_report_v1,
)

REPO_HEAD = "b0099b63153b6d18e2d4e030ee07b61b20f8b6df"
FORBIDDEN_OUTPUT_TERMS = (
    "raw_prompt",
    "response_text",
    "source_urls",
    "hidden_prompt",
    "answer_key",
    "protected_material",
)


def _report(**kwargs):
    return build_behavior_evaluation_report_v1(repo_head=REPO_HEAD, timestamp_local="2026-05-17 10:55", recommended_next_step="hold", **kwargs)


def _populated_report():
    families = {
        "ordinary_task_behavior": build_behavior_evaluation_family_v1(family="ordinary_task_behavior", label="pass_property", observed=True, strengths=["bounded_help"]),
        "non_canned_cognition": build_behavior_evaluation_family_v1(family="non_canned_cognition", label="needs_review", observed=True, risks=["template_risk"]),
        "guardrail_preservation": build_behavior_evaluation_family_v1(family="guardrail_preservation", label="blocked_by_boundary", observed=True),
    }
    return _report(families=families, readiness_label="early_internal_readiness")


def test_builder_default_shape():
    report = _report()
    assert report["report_type"] == "weslr_behavior_evaluation_report_v1"
    assert report["schema_version"] == "1.0"
    assert report["evaluation_mode"] == "internal_behavior_evaluation"
    for key in ("official_benchmark_claim", "turing_test_claim", "iq_claim", "certification_claim", "raw_private_text_included", "numeric_scores_used", *SIDE_EFFECT_FLAGS_V1):
        assert report[key] is False
    assert set(report["families"]) == set(ALLOWED_EVALUATION_FAMILIES_V1)
    assert report["readiness_label"] == "needs_more_observation"


def test_family_builder_and_validator_label_rules():
    family = build_behavior_evaluation_family_v1(family="ordinary_task_behavior", label="pass_property", observed=True, strengths=["safe summary"], risks=[])
    report = _report(families={"ordinary_task_behavior": family})
    assert report["families"]["ordinary_task_behavior"]["strengths"] == ["safe summary"]
    assert validate_behavior_evaluation_report_v1(report)["valid"] is True

    bad = _report(families={"unknown_family": build_behavior_evaluation_family_v1(family="unknown_family")})
    assert validate_behavior_evaluation_report_v1(bad)["valid"] is False
    bad = _report(families={"ordinary_task_behavior": build_behavior_evaluation_family_v1(family="ordinary_task_behavior", label="score_99")})
    assert validate_behavior_evaluation_report_v1(bad)["valid"] is False


def test_valid_default_report_has_expected_warnings_only():
    result = validate_behavior_evaluation_report_v1(_report())
    assert result["valid"] is True
    assert result["errors"] == []


def test_populated_safe_report_valid():
    result = validate_behavior_evaluation_report_v1(_populated_report())
    assert result["valid"] is True
    assert result["errors"] == []


@pytest.mark.parametrize("claim_key", ["official_benchmark_claim", "turing_test_claim", "iq_claim", "certification_claim", "numeric_scores_used", "raw_private_text_included"])
def test_reject_unsafe_claims(claim_key):
    report = _populated_report()
    report[claim_key] = True
    result = validate_behavior_evaluation_report_v1(report)
    assert result["valid"] is False
    assert any(claim_key in error for error in result["errors"])


@pytest.mark.parametrize("side_effect_key", SIDE_EFFECT_FLAGS_V1)
def test_reject_side_effects(side_effect_key):
    report = _populated_report()
    report[side_effect_key] = True
    result = validate_behavior_evaluation_report_v1(report)
    assert result["valid"] is False
    assert any(side_effect_key in error for error in result["errors"])


@pytest.mark.parametrize("forbidden_key", ["raw_text", "raw_prompt", "response_text", "final_answer", "full_conversation", "source_urls", "hidden_prompt", "answer_key", "protected_material"])
def test_reject_raw_private_protected_fields(forbidden_key):
    report = _populated_report()
    report["notes"] = {forbidden_key: "synthetic placeholder"}
    result = validate_behavior_evaluation_report_v1(report)
    assert result["valid"] is False
    assert any(forbidden_key in error for error in result["errors"])


@pytest.mark.parametrize("phrase", ["passed Turing test", "official benchmark", "certified intelligent", "IQ score", "human level", "conscious", "sentient", "soul"])
def test_reject_forbidden_claim_text(phrase):
    report = _populated_report()
    report["notes"] = {"claim": phrase}
    result = validate_behavior_evaluation_report_v1(report)
    assert result["valid"] is False
    assert any(phrase.lower() in error for error in result["errors"])


def test_readiness_label_validation():
    for label in ALLOWED_READINESS_LABELS_V1:
        assert validate_behavior_evaluation_report_v1(_report(readiness_label=label))["valid"] is True
    for label in ["passed_turing_test", "certified_intelligent", "official_benchmark_passed", "human_level", "conscious", "sentient", "mystery"]:
        assert validate_behavior_evaluation_report_v1(_report(readiness_label=label))["valid"] is False


def test_required_families_and_unknown_family():
    report = _report()
    report["families"].pop("ordinary_task_behavior")
    assert validate_behavior_evaluation_report_v1(report)["valid"] is False
    report = _report(families={"extra_family": build_behavior_evaluation_family_v1(family="extra_family")})
    assert validate_behavior_evaluation_report_v1(report)["valid"] is False


def test_json_safe_copy_is_not_sanitizer():
    report = _populated_report()
    report["notes"] = {"raw_text": "synthetic unsafe"}
    copied = to_behavior_evaluation_report_json_safe_v1(report)
    assert copied["notes"]["raw_text"] == "synthetic unsafe"
    assert validate_behavior_evaluation_report_v1(copied)["valid"] is False


def test_summary_safety():
    report = _populated_report()
    report["notes"] = {"raw_prompt": "synthetic", "response_text": "synthetic", "source_urls": ["https://example.invalid"], "hidden_prompt": "synthetic", "answer_key": "synthetic", "protected_material": "synthetic"}
    summary = summarize_behavior_evaluation_report_v1(report)
    text = repr(summary)
    assert summary["family_count"] == len(ALLOWED_EVALUATION_FAMILIES_V1)
    assert summary["side_effects_clear"] is True
    for term in FORBIDDEN_OUTPUT_TERMS:
        assert term not in text


def test_markdown_safety_and_sections():
    markdown = render_behavior_evaluation_report_markdown_v1(_populated_report())
    for section in [
        "SECTION 1 — STATUS",
        "SECTION 2 — READINESS LABEL",
        "SECTION 3 — EVALUATION FAMILIES",
        "SECTION 4 — SAFETY / CLAIM BOUNDARIES",
        "SECTION 5 — SIDE-EFFECT CHECK",
        "SECTION 6 — BLOCKED CLAIMS",
        "SECTION 7 — RECOMMENDED NEXT STEP",
        "SECTION 8 — VALIDATION SUMMARY",
    ]:
        assert section in markdown
    for term in FORBIDDEN_OUTPUT_TERMS:
        assert term not in markdown
    lowered = markdown.lower()
    assert "official benchmark" not in lowered
    assert "passed turing test" not in lowered
    assert "certification" not in lowered
    assert "iq score" not in lowered
    assert "conscious" not in lowered


def test_report_from_family_summaries():
    report = build_behavior_evaluation_report_from_family_summaries_v1(
        repo_head=REPO_HEAD,
        family_summaries=[{"family": "ordinary_task_behavior", "label": "pass_property", "observed": True}],
        recommended_next_step="dry report",
    )
    assert report["families"]["ordinary_task_behavior"]["label"] == "pass_property"
    assert validate_behavior_evaluation_report_v1(report)["valid"] is True


def test_no_side_effect_files_created():
    before = set(Path.cwd().glob(".weslr*"))
    report = _populated_report()
    validate_behavior_evaluation_report_v1(report)
    summarize_behavior_evaluation_report_v1(report)
    render_behavior_evaluation_report_markdown_v1(report)
    to_behavior_evaluation_report_json_safe_v1(report)
    after = set(Path.cwd().glob(".weslr*"))
    assert after == before
