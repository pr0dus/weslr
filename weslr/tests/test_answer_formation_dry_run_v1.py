from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from weslr.answer_formation import build_answer_formation_artifact_v1
from weslr.answer_formation_report import build_answer_formation_report_v1
from weslr.answer_formation_dry_run import (
    AGGREGATE_LABELS_V1,
    ALLOWED_SYNTHETIC_METADATA_INPUTS_V1,
    ARTIFACT_TYPE_V1,
    DENIED_AUTHORITY_FIELDS_V1,
    FORBIDDEN_INPUTS_V1,
    REQUIRED_NO_AUTHORITY_LABELS_V1,
    SCHEMA_VERSION_V1,
    build_answer_formation_dry_run_artifact_v1,
    render_answer_formation_dry_run_artifact_markdown_v1,
    summarize_answer_formation_dry_run_artifact_v1,
    to_answer_formation_dry_run_artifact_json_safe_v1,
    validate_answer_formation_dry_run_artifact_v1,
)


def test_module_import_is_safe_and_public_api_exists():
    before = set(Path(".").glob(".weslr*"))
    module = importlib.import_module("weslr.answer_formation_dry_run")
    after = set(Path(".").glob(".weslr*"))
    assert before == after
    for name in (
        "build_answer_formation_dry_run_artifact_v1",
        "validate_answer_formation_dry_run_artifact_v1",
        "summarize_answer_formation_dry_run_artifact_v1",
        "render_answer_formation_dry_run_artifact_markdown_v1",
        "to_answer_formation_dry_run_artifact_json_safe_v1",
    ):
        assert hasattr(module, name)


def test_build_dry_run_required_shape_and_flags():
    artifact = build_answer_formation_dry_run_artifact_v1()
    assert artifact["artifact_type"] == ARTIFACT_TYPE_V1
    assert artifact["schema_version"] == SCHEMA_VERSION_V1
    for flag in (
        "metadata_only",
        "internal_only",
        "dry_run_only",
        "helper_based",
        "synthetic_metadata_only",
        "non_runtime",
        "non_user_facing",
        "deterministic",
        "import_safe",
        "side_effect_free",
        "in_memory_only",
        "qualitative_only",
        "validation_before_rendering",
        "safe_markdown_only",
        "json_safe_behavior_preserved",
    ):
        assert artifact[flag] is True
    assert artifact["blocked_status"] is False
    assert artifact["future_helper_module_path"] == "weslr/answer_formation_dry_run.py"
    assert artifact["future_test_module_path"] == "weslr/tests/test_answer_formation_dry_run_v1.py"


@pytest.mark.parametrize("field", DENIED_AUTHORITY_FIELDS_V1)
def test_denied_authority_fields_remain_false(field):
    artifact = build_answer_formation_dry_run_artifact_v1()
    assert artifact[field] is False
    assert artifact["denied_authority_fields"][field] is False


def test_allowed_inputs_and_forbidden_checks_are_complete():
    artifact = build_answer_formation_dry_run_artifact_v1()
    assert set(artifact["allowed_synthetic_metadata_inputs"]) == set(ALLOWED_SYNTHETIC_METADATA_INPUTS_V1)
    assert set(artifact["forbidden_inputs_checked"]) == set(FORBIDDEN_INPUTS_V1)


def test_required_no_authority_and_aggregate_labels_are_present():
    artifact = build_answer_formation_dry_run_artifact_v1()
    for label in REQUIRED_NO_AUTHORITY_LABELS_V1:
        assert label in artifact["required_no_authority_labels"]
    for label in AGGREGATE_LABELS_V1:
        assert label in artifact["aggregate_labels"]


def test_default_dry_run_artifact_validates():
    artifact = build_answer_formation_dry_run_artifact_v1()
    validation = validate_answer_formation_dry_run_artifact_v1(artifact)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["errors"] == []
    assert validation["safety_booleans_valid"] is True
    assert validation["synthetic_metadata_valid"] is True
    assert validation["safe_to_render"] is True
    assert validation["json_safe"] is True


def test_synthetic_metadata_summary_uses_keys_counts_and_labels_only():
    artifact = build_answer_formation_dry_run_artifact_v1(
        {
            "synthetic_task_type_label": "ordinary_task",
            "gate_status_label": "present",
            "candidate_count_metadata": 2,
            "selected_candidate_metadata_presence_boolean": True,
            "candidate_rejection_reason_label": "insufficient_evidence",
        }
    )
    validation = validate_answer_formation_dry_run_artifact_v1(artifact)
    assert validation["valid"] is True
    assert artifact["synthetic_metadata_summary"]["input_key_count"] == 5
    assert artifact["synthetic_metadata_summary"]["allowed_input_key_count"] == 5
    assert artifact["candidate_metadata_summary"]["candidate_count_total"] == 2
    assert artifact["candidate_metadata_summary"]["selected_candidate_metadata_present_count"] == 1
    assert "insufficient_evidence" in artifact["candidate_metadata_summary"]["rejection_labels"]


def test_source_artifacts_and_report_are_summarized_as_metadata_only():
    source = build_answer_formation_artifact_v1(
        gate_statuses={"evidence_gate": "present"},
        candidate_formation_metadata={
            "candidate_type_labels": ["state_frame_candidate"],
            "candidate_count": 1,
            "selected_candidate_metadata_present": True,
        },
    )
    report = build_answer_formation_report_v1([source])
    artifact = build_answer_formation_dry_run_artifact_v1(source_artifacts=[source], report_artifact=report)
    validation = validate_answer_formation_dry_run_artifact_v1(artifact)
    assert validation["valid"] is True
    assert artifact["validation_summary"]["source_artifact_count"] == 1
    assert artifact["validation_summary"]["valid_source_artifact_count"] == 1
    assert artifact["report_artifact_summary"]["valid"] is True
    assert artifact["gate_metadata_summary"]["gate_status_counts"]["present"] == 1
    assert artifact["candidate_metadata_summary"]["candidate_count_total"] == 1


def test_unknown_synthetic_metadata_input_blocks_without_value_leak():
    artifact = build_answer_formation_dry_run_artifact_v1({"unexpected_label": "SAFE VALUE"})
    validation = validate_answer_formation_dry_run_artifact_v1(artifact)
    assert validation["valid"] is False
    assert artifact["blocked_status"] is True
    assert "unknown_synthetic_metadata_inputs" in artifact["blocked_reason_labels"]
    safe = to_answer_formation_dry_run_artifact_json_safe_v1(artifact)
    assert safe["artifact_type"].endswith("_invalid")
    assert "SAFE VALUE" not in json.dumps(safe)


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
def test_forbidden_content_markers_fail_validation_without_leak(key, value, label):
    artifact = build_answer_formation_dry_run_artifact_v1()
    artifact[key] = value
    validation = validate_answer_formation_dry_run_artifact_v1(artifact)
    assert validation["valid"] is False
    assert validation[label] is True
    markdown = render_answer_formation_dry_run_artifact_markdown_v1(artifact)
    safe = to_answer_formation_dry_run_artifact_json_safe_v1(artifact)
    assert value not in markdown
    assert value not in json.dumps(safe)
    assert label in markdown or label in json.dumps(safe)


def test_source_artifact_with_unsafe_raw_content_is_summarized_without_leaking():
    source = build_answer_formation_artifact_v1()
    source["raw_prompt_text"] = "raw prompt: DO NOT LEAK SOURCE"
    artifact = build_answer_formation_dry_run_artifact_v1(source_artifacts=[source])
    encoded = json.dumps(artifact)
    assert "DO NOT LEAK SOURCE" not in encoded
    assert artifact["blocked_status"] is True
    assert "raw_content_detected" in artifact["blocked_reason_labels"]


def test_markdown_render_safe_default_artifact():
    artifact = build_answer_formation_dry_run_artifact_v1()
    markdown = render_answer_formation_dry_run_artifact_markdown_v1(artifact)
    assert "# WESLR Answer Formation Dry-Run Artifact V1" in markdown
    assert "dry_run_metadata_not_answer_text" in markdown
    assert "dry_run_artifact_not_final_answer" in markdown
    assert "candidate_metadata_not_answer_draft" in markdown
    assert "selected_candidate_metadata_not_final_answer" in markdown
    assert "validation_pass_not_answer_correctness" in markdown
    assert "no_dry_run_execution" in markdown
    assert "no_dry_run_result_artifact_created" in markdown
    assert "no_answer_formation_execution" in markdown
    assert "no_answer_composition" in markdown
    assert "no_final_answer_generation" in markdown
    assert "no_runtime_wiring" in markdown
    assert "no_provider_search_advisor_calls" in markdown
    assert "no_dot_weslr_writes" in markdown
    assert "no_feature_flags" in markdown
    assert "no_judges_or_scoring" in markdown
    assert "no_official_claims" in markdown
    assert "no_answer_authority_granted" in markdown
    assert "no_composition_authority_granted" in markdown
    assert "no_runtime_authority_granted" in markdown
    assert "weslr_chat_responder_py_untouched" in markdown
    assert "final answer:" not in markdown.lower()
    assert "provider output:" not in markdown.lower()
    assert "raw prompt:" not in markdown.lower()


def test_json_safe_copy_is_serializable():
    artifact = build_answer_formation_dry_run_artifact_v1()
    safe = to_answer_formation_dry_run_artifact_json_safe_v1(artifact)
    assert safe == artifact
    assert safe is not artifact
    assert json.loads(json.dumps(safe))["artifact_type"] == ARTIFACT_TYPE_V1


def test_summary_uses_safe_labels_counts_and_booleans_only():
    artifact = build_answer_formation_dry_run_artifact_v1({"candidate_count_metadata": 3})
    summary = summarize_answer_formation_dry_run_artifact_v1(artifact)
    assert summary["artifact_type"] == ARTIFACT_TYPE_V1
    assert summary["valid"] is True
    assert summary["blocked"] is False
    assert summary["metadata_only"] is True
    assert summary["dry_run_only"] is True
    assert summary["all_authority_fields_false"] is True
    assert summary["candidate_count_total"] == 3
    assert summary["next_lane"] == "REVIEW_ANSWER_FORMATION_DRY_RUN_HELPERS_IMPLEMENTATION_V1"


def test_validation_pass_is_metadata_quality_only_not_authority():
    artifact = build_answer_formation_dry_run_artifact_v1()
    validation = validate_answer_formation_dry_run_artifact_v1(artifact)
    assert validation["valid"] is True
    assert artifact["answer_authority_granted"] is False
    assert artifact["composition_authority_granted"] is False
    assert artifact["runtime_authority_granted"] is False
    assert artifact["dry_run_result_artifact_created"] is False


def test_no_result_artifact_written_by_helpers():
    before = {path for path in Path("docs").glob("*DRY_RUN_RESULT*ARTIFACT*.md")}
    artifact = build_answer_formation_dry_run_artifact_v1()
    render_answer_formation_dry_run_artifact_markdown_v1(artifact)
    to_answer_formation_dry_run_artifact_json_safe_v1(artifact)
    after = {path for path in Path("docs").glob("*DRY_RUN_RESULT*ARTIFACT*.md")}
    assert before == after
