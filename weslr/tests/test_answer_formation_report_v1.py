from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from weslr.answer_formation import build_answer_formation_artifact_v1
from weslr.answer_formation_report import (
    ALLOWED_AGGREGATE_LABELS_V1,
    ALLOWED_METADATA_INPUTS_V1,
    ARTIFACT_TYPE_V1,
    FALSE_AUTHORITY_FIELDS_V1,
    FORBIDDEN_INPUTS_V1,
    REQUIRED_NO_AUTHORITY_LABELS_V1,
    SCHEMA_VERSION_V1,
    build_answer_formation_report_v1,
    derive_answer_formation_report_labels_v1,
    render_answer_formation_report_markdown_v1,
    summarize_answer_formation_report_v1,
    to_answer_formation_report_json_safe_v1,
    validate_answer_formation_report_v1,
)


def test_module_import_is_safe_and_public_api_exists():
    before = set(Path(".").glob(".weslr*"))
    module = importlib.import_module("weslr.answer_formation_report")
    after = set(Path(".").glob(".weslr*"))
    assert before == after
    for name in (
        "build_answer_formation_report_v1",
        "validate_answer_formation_report_v1",
        "summarize_answer_formation_report_v1",
        "derive_answer_formation_report_labels_v1",
        "render_answer_formation_report_markdown_v1",
        "to_answer_formation_report_json_safe_v1",
    ):
        assert hasattr(module, name)


def test_build_report_required_shape_and_flags():
    report = build_answer_formation_report_v1()
    assert report["artifact_type"] == ARTIFACT_TYPE_V1
    assert report["schema_version"] == SCHEMA_VERSION_V1
    for flag in (
        "metadata_only",
        "internal_only",
        "helper_only",
        "report_only",
        "non_runtime",
        "non_user_facing",
        "deterministic",
        "import_safe",
        "side_effect_free",
        "in_memory_only",
        "qualitative_only",
    ):
        assert report[flag] is True
    assert report["blocked"] is False


@pytest.mark.parametrize("flag", FALSE_AUTHORITY_FIELDS_V1)
def test_build_report_preserves_authority_flags_false(flag):
    report = build_answer_formation_report_v1()
    assert report[flag] is False
    assert report["required_false_no_authority_fields"][flag] is False


def test_build_report_includes_required_no_authority_labels():
    report = build_answer_formation_report_v1()
    for label in REQUIRED_NO_AUTHORITY_LABELS_V1:
        assert label in report["required_no_authority_labels"]


def test_build_report_includes_allowed_metadata_inputs_and_forbidden_checks():
    report = build_answer_formation_report_v1()
    assert set(report["allowed_metadata_inputs"]) == set(ALLOWED_METADATA_INPUTS_V1)
    assert set(report["forbidden_inputs_checked"]) == set(FORBIDDEN_INPUTS_V1)


def test_validate_default_report_passes():
    report = build_answer_formation_report_v1()
    validation = validate_answer_formation_report_v1(report)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["errors"] == []
    assert validation["safety_booleans_valid"] is True
    assert validation["source_artifact_summary_valid"] is True
    assert validation["validation_summary_valid"] is True
    assert validation["gate_summary_valid"] is True
    assert validation["candidate_summary_valid"] is True
    assert validation["rejection_summary_valid"] is True
    assert validation["aggregate_labels_valid"] is True
    assert validation["safe_to_render"] is True
    assert validation["json_safe"] is True


def test_report_summarizes_safe_answer_formation_artifacts():
    source = build_answer_formation_artifact_v1(
        gate_statuses={"evidence_gate": "present"},
        candidate_formation_metadata={
            "candidate_type_labels": ["state_frame_candidate", "governance_safe_candidate"],
            "candidate_count": 2,
            "selected_candidate_metadata_present": True,
        },
        candidate_rejection_metadata={"rejection_reason_labels": ["insufficient_evidence"]},
    )
    report = build_answer_formation_report_v1([source])
    validation = validate_answer_formation_report_v1(report)
    assert validation["valid"] is True
    assert report["validation_summary"]["source_artifact_count"] == 1
    assert report["validation_summary"]["valid_source_artifact_count"] == 1
    assert report["gate_summary"]["gate_status_counts"]["present"] == 1
    assert report["candidate_summary"]["candidate_count_total"] == 2
    assert report["candidate_summary"]["selected_candidate_metadata_present_count"] == 1
    assert report["rejection_summary"]["rejection_label_counts"]["insufficient_evidence"] == 1


@pytest.mark.parametrize("label", ALLOWED_AGGREGATE_LABELS_V1)
def test_aggregate_label_allowlist_contains_expected_labels(label):
    assert label in ALLOWED_AGGREGATE_LABELS_V1


def test_derive_report_labels_uses_safe_metadata_only():
    report = build_answer_formation_report_v1([build_answer_formation_artifact_v1()])
    labels = derive_answer_formation_report_labels_v1(report)
    assert "all_source_artifacts_metadata_only" in labels
    assert "all_source_artifacts_internal_only" in labels
    assert "all_authority_fields_false" in labels
    assert "answer_formation_not_attempted" in labels
    assert "answer_composition_not_attempted" in labels
    assert "final_answer_not_generated" in labels
    assert "runtime_not_wired" in labels
    assert "provider_calls_not_made" in labels
    assert "dot_weslr_not_written" in labels
    assert "judges_scoring_not_authorized" in labels
    assert "official_claims_not_allowed" in labels
    assert "safe_markdown_eligible" in labels
    assert "json_safe_eligible" in labels


def test_blocked_source_artifact_creates_blocked_safe_report():
    source = build_answer_formation_artifact_v1(blocked_reasons=["blocked_raw_prompt_detected"])
    report = build_answer_formation_report_v1([source])
    validation = validate_answer_formation_report_v1(report)
    assert report["blocked"] is True
    assert "blocked_source_artifacts_present" in report["blocked_reasons"]
    assert "blocked_artifacts_present" in report["aggregate_labels"]
    assert validation["valid"] is False
    assert validation["blocked"] is True


def test_unknown_allowed_metadata_input_fails_validation():
    report = build_answer_formation_report_v1(allowed_metadata_inputs=[*ALLOWED_METADATA_INPUTS_V1, "raw_prompt_text"])
    validation = validate_answer_formation_report_v1(report)
    assert validation["valid"] is False
    assert "unknown_allowed_metadata_inputs" in validation["errors"]


def test_missing_forbidden_input_checks_fail_validation():
    report = build_answer_formation_report_v1(forbidden_inputs_checked=["raw_prompt_text"])
    validation = validate_answer_formation_report_v1(report)
    assert validation["valid"] is False
    assert "missing_forbidden_input_checks" in validation["errors"]


@pytest.mark.parametrize("flag", FALSE_AUTHORITY_FIELDS_V1)
def test_authority_flag_true_fails_validation(flag):
    report = build_answer_formation_report_v1()
    report[flag] = True
    validation = validate_answer_formation_report_v1(report)
    assert validation["valid"] is False
    assert f"authority_flag_not_false:{flag}" in validation["errors"]


def test_missing_required_field_fails_validation():
    report = build_answer_formation_report_v1()
    report.pop("metadata_only")
    validation = validate_answer_formation_report_v1(report)
    assert validation["valid"] is False
    assert "missing_required_field:metadata_only" in validation["errors"]
    assert "required_true_field_invalid:metadata_only" in validation["errors"]


def test_exact_source_and_future_paths_are_preserved():
    report = build_answer_formation_report_v1()
    assert report["source_answer_formation_helper_module_path"] == "weslr/answer_formation.py"
    assert report["source_answer_formation_test_module_path"] == "weslr/tests/test_answer_formation_v1.py"
    assert report["future_report_helper_module_path"] == "weslr/answer_formation_report.py"
    assert report["future_report_test_module_path"] == "weslr/tests/test_answer_formation_report_v1.py"


def test_unknown_aggregate_label_fails_validation():
    report = build_answer_formation_report_v1()
    report["aggregate_labels"].append("answer_correctness_ready")
    validation = validate_answer_formation_report_v1(report)
    assert validation["valid"] is False
    assert "unknown_aggregate_labels" in validation["errors"]


@pytest.mark.parametrize(
    "key,value,label",
    [
        ("raw_prompt_text", "raw prompt: unsafe", "raw_content_detected"),
        ("private_content", "private content: secret", "private_content_detected"),
        ("hidden_prompt", "hidden prompt: secret", "hidden_prompt_detected"),
        ("answer_key", "answer key: x", "answer_key_detected"),
        ("provider_output", "provider output: x", "provider_output_detected"),
        ("runtime_output", "runtime output: x", "runtime_output_detected"),
        ("live_dialogue_transcript", "live dialogue transcript x", "live_dialogue_detected"),
        ("final_answer_prose", "final answer: x", "final_answer_detected"),
        ("answer_draft_text", "answer draft: x", "answer_draft_detected"),
        ("official_score", "official score: 100", "judge_or_score_detected"),
    ],
)
def test_forbidden_content_markers_fail_validation(key, value, label):
    report = build_answer_formation_report_v1()
    report[key] = value
    validation = validate_answer_formation_report_v1(report)
    assert validation["valid"] is False
    assert validation[label] is True


def test_source_artifact_with_unsafe_raw_content_is_summarized_without_leaking():
    source = build_answer_formation_artifact_v1()
    source["raw_prompt_text"] = "raw prompt: DO NOT LEAK SOURCE"
    report = build_answer_formation_report_v1([source])
    encoded = json.dumps(report)
    assert "DO NOT LEAK SOURCE" not in encoded
    assert report["blocked"] is True
    assert "source_validation_errors_present" in report["blocked_reasons"]


def test_summary_uses_safe_labels_counts_and_booleans_only():
    report = build_answer_formation_report_v1([build_answer_formation_artifact_v1()])
    summary = summarize_answer_formation_report_v1(report)
    assert summary["artifact_type"] == ARTIFACT_TYPE_V1
    assert summary["valid"] is True
    assert summary["blocked"] is False
    assert summary["all_authority_fields_false"] is True
    assert summary["source_artifact_count"] == 1
    assert summary["valid_source_artifact_count"] == 1
    assert summary["candidate_count_total"] == 0
    assert summary["validation_error_labels"] == []


def test_summary_for_invalid_input_is_safe():
    summary = summarize_answer_formation_report_v1({"artifact_type": "bad"})
    assert summary["valid"] is False
    assert summary["blocked"] is True
    assert "artifact_type_invalid" in summary["validation_error_labels"]


def test_markdown_render_safe_default_report():
    report = build_answer_formation_report_v1([build_answer_formation_artifact_v1()])
    markdown = render_answer_formation_report_markdown_v1(report)
    assert "# Answer Formation Report V1" in markdown
    assert "report_metadata_not_answer_text" in markdown
    assert "validation_pass_not_answer_authority" in markdown
    assert "final answer:" not in markdown.lower()
    assert "provider output:" not in markdown.lower()


def test_markdown_renderer_blocks_and_does_not_leak_unsafe_content():
    report = build_answer_formation_report_v1()
    report["raw_prompt_text"] = "raw prompt: DO NOT LEAK THIS"
    markdown = render_answer_formation_report_markdown_v1(report)
    assert "# Answer Formation Report V1 — Blocked" in markdown
    assert "raw_content_detected" in markdown
    assert "DO NOT LEAK THIS" not in markdown
    assert "raw prompt: DO NOT LEAK THIS" not in markdown


def test_json_safe_copy_preserves_safe_metadata_and_is_json_serializable():
    report = build_answer_formation_report_v1([build_answer_formation_artifact_v1()])
    safe = to_answer_formation_report_json_safe_v1(report)
    assert safe == report
    assert safe is not report
    assert json.loads(json.dumps(safe))["artifact_type"] == ARTIFACT_TYPE_V1


def test_json_safe_invalid_wrapper_does_not_leak_unsafe_content():
    report = build_answer_formation_report_v1()
    report["provider_output"] = "provider output: DO NOT LEAK"
    safe = to_answer_formation_report_json_safe_v1(report)
    assert safe["artifact_type"].endswith("_invalid")
    assert safe["blocked"] is True
    assert "provider_output_detected" in safe["errors"]
    assert "DO NOT LEAK" not in json.dumps(safe)


def test_validation_pass_is_metadata_quality_only_not_authority():
    report = build_answer_formation_report_v1()
    validation = validate_answer_formation_report_v1(report)
    assert validation["valid"] is True
    assert report["answer_authority_granted"] is False
    assert report["composition_authority_granted"] is False
    assert report["runtime_authority_granted"] is False
    assert "validation_pass_metadata_quality_evidence_only" in report["validation_labels"]


def test_no_chat_responder_runtime_import_or_call_fields():
    report = build_answer_formation_report_v1()
    assert report["chat_responder_called"] is False
    assert report["chat_responder_modified"] is False
    validation = validate_answer_formation_report_v1(report)
    assert validation["valid"] is True
