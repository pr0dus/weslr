from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from weslr.answer_formation_dry_run_execution import (
    AGGREGATE_LABELS_V1,
    ARTIFACT_TYPE_V1,
    RESULT_ARTIFACT_PATH_V1,
    SCHEMA_VERSION_V1,
    SAFETY_FLAGS_V1,
    build_answer_formation_dry_run_execution_result_v1,
    render_answer_formation_dry_run_execution_result_markdown_v1,
    run_answer_formation_dry_run_execution_v1,
    to_answer_formation_dry_run_execution_result_json_safe_v1,
    validate_answer_formation_dry_run_execution_result_v1,
    write_answer_formation_dry_run_result_artifact_v1,
)
from weslr.answer_formation_dry_run import DENIED_AUTHORITY_FIELDS_V1


def test_module_import_is_safe_and_public_api_exists():
    before = set(Path(".").glob(".weslr*"))
    module = importlib.import_module("weslr.answer_formation_dry_run_execution")
    after = set(Path(".").glob(".weslr*"))
    assert before == after
    for name in (
        "run_answer_formation_dry_run_execution_v1",
        "build_answer_formation_dry_run_execution_result_v1",
        "validate_answer_formation_dry_run_execution_result_v1",
        "render_answer_formation_dry_run_execution_result_markdown_v1",
        "to_answer_formation_dry_run_execution_result_json_safe_v1",
        "write_answer_formation_dry_run_result_artifact_v1",
    ):
        assert hasattr(module, name)


def test_build_execution_result_required_shape_and_flags():
    result = build_answer_formation_dry_run_execution_result_v1()
    assert result["artifact_type"] == ARTIFACT_TYPE_V1
    assert result["schema_version"] == SCHEMA_VERSION_V1
    for flag in (
        "metadata_only",
        "internal_only",
        "dry_run_execution_only",
        "helper_based",
        "synthetic_input_only",
        "non_runtime",
        "non_user_facing",
        "deterministic",
        "import_safe",
        "side_effect_free_except_result_write",
        "qualitative_only",
        "validation_before_rendering",
        "safe_markdown_only",
        "json_safe_behavior_preserved",
    ):
        assert result[flag] is True
    assert result["execution_label"] == "answer_formation_dry_run_execution_v1"
    assert result["result_artifact_path"] == RESULT_ARTIFACT_PATH_V1
    assert result["dry_run_helper_module_path"] == "weslr/answer_formation_dry_run.py"
    assert result["dry_run_helper_test_module_path"] == "weslr/tests/test_answer_formation_dry_run_v1.py"
    assert result["blocked"] is False


@pytest.mark.parametrize("field", DENIED_AUTHORITY_FIELDS_V1)
def test_denied_authority_fields_remain_false(field):
    result = build_answer_formation_dry_run_execution_result_v1()
    assert result[field] is False
    assert result["denied_authority_fields"][field] is False


def test_default_execution_result_validates():
    result = build_answer_formation_dry_run_execution_result_v1()
    validation = validate_answer_formation_dry_run_execution_result_v1(result)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["errors"] == []
    assert validation["safety_booleans_valid"] is True
    assert validation["dry_run_helper_validation_valid"] is True
    assert validation["result_artifact_path_valid"] is True
    assert validation["safe_to_render"] is True
    assert validation["json_safe"] is True


def test_uses_existing_dry_run_helpers_with_synthetic_metadata_only():
    result = build_answer_formation_dry_run_execution_result_v1(
        {
            "execution_label": "synthetic_execution_fixture",
            "synthetic_task_type_label": "ordinary_task",
            "gate_status_label": "present",
            "candidate_count_metadata": 2,
            "selected_candidate_metadata_presence_boolean": True,
            "candidate_rejection_reason_label": "not_final_answer",
        }
    )
    validation = validate_answer_formation_dry_run_execution_result_v1(result)
    assert validation["valid"] is True
    assert result["execution_label"] == "synthetic_execution_fixture"
    assert result["dry_run_helper_validation"]["valid"] is True
    assert result["dry_run_helper_summary"]["candidate_count_total"] == 2
    assert result["dry_run_status"] == "dry_run_helper_artifact_built_and_validated"
    assert result["validation_status"] == "validation_pass_metadata_quality_evidence_only"


def test_aggregate_labels_and_safety_flags_are_present():
    result = build_answer_formation_dry_run_execution_result_v1()
    for label in AGGREGATE_LABELS_V1:
        assert label in result["aggregate_labels"]
    for label in SAFETY_FLAGS_V1:
        assert label in result["safety_flags"]


@pytest.mark.parametrize(
    "key,value,label",
    [
        ("raw_prompt_text", "raw prompt: unsafe", "raw_content_detected"),
        ("private_content", "private content: secret", "private_content_detected"),
        ("provider_output", "provider output: x", "provider_output_detected"),
        ("runtime_output", "runtime output: x", "runtime_output_detected"),
        ("final_answer_prose", "final answer: x", "final_answer_detected"),
        ("answer_draft_text", "answer draft: x", "answer_draft_detected"),
        ("official_score", "official score: 100", "judge_or_score_detected"),
    ],
)
def test_forbidden_content_markers_fail_validation_without_leak(key, value, label):
    result = build_answer_formation_dry_run_execution_result_v1()
    result[key] = value
    validation = validate_answer_formation_dry_run_execution_result_v1(result)
    assert validation["valid"] is False
    assert validation[label] is True
    markdown = render_answer_formation_dry_run_execution_result_markdown_v1(result)
    safe = to_answer_formation_dry_run_execution_result_json_safe_v1(result)
    assert value not in markdown
    assert value not in json.dumps(safe)
    assert label in markdown or label in json.dumps(safe)


def test_invalid_result_path_blocks_and_does_not_write(tmp_path):
    bad_path = str(tmp_path / "not-approved.md")
    result = build_answer_formation_dry_run_execution_result_v1(result_artifact_path=bad_path)
    validation = validate_answer_formation_dry_run_execution_result_v1(result)
    assert validation["valid"] is False
    assert "result_artifact_path_invalid" in validation["errors"]
    write_result = write_answer_formation_dry_run_result_artifact_v1(result, result_artifact_path=bad_path)
    assert write_result["written"] is False
    assert not Path(bad_path).exists()


def test_markdown_render_safe_default_result():
    result = build_answer_formation_dry_run_execution_result_v1()
    markdown = render_answer_formation_dry_run_execution_result_markdown_v1(result)
    assert "# WESLR Answer Formation Dry-Run Result V1" in markdown
    assert "answer_formation_dry_run_execution_v1" in markdown
    assert "docs/WESLR_ANSWER_FORMATION_DRY_RUN_EXECUTION_V1.md" in markdown
    assert "docs/WESLR_ANSWER_FORMATION_DRY_RUN_EXECUTION_REVIEW_V1.md" in markdown
    assert "weslr/answer_formation_dry_run.py" in markdown
    assert "weslr/tests/test_answer_formation_dry_run_v1.py" in markdown
    assert "dry_run_helper_artifact_built_and_validated" in markdown
    assert "validation_pass_metadata_quality_evidence_only" in markdown
    assert "no_runtime_wiring" in markdown
    assert "no_provider_search_advisor_calls" in markdown
    assert "no_final_answer_generation" in markdown
    assert "no_answer_draft" in markdown
    assert "no_authority_grant" in markdown
    assert "REVIEW_ANSWER_FORMATION_DRY_RUN_EXECUTION_RESULT_V1" in markdown
    assert "final answer:" not in markdown.lower()
    assert "provider output:" not in markdown.lower()
    assert "raw prompt:" not in markdown.lower()


def test_json_safe_copy_is_serializable():
    result = build_answer_formation_dry_run_execution_result_v1()
    safe = to_answer_formation_dry_run_execution_result_json_safe_v1(result)
    assert safe == result
    assert safe is not result
    assert json.loads(json.dumps(safe))["artifact_type"] == ARTIFACT_TYPE_V1


def test_write_result_artifact_writes_only_approved_path():
    path = Path(RESULT_ARTIFACT_PATH_V1)
    before = path.read_text() if path.exists() else None
    write_result = run_answer_formation_dry_run_execution_v1()
    assert write_result["written"] is True
    assert write_result["path"] == RESULT_ARTIFACT_PATH_V1
    assert path.exists()
    markdown = path.read_text()
    assert "# WESLR Answer Formation Dry-Run Result V1" in markdown
    assert "REVIEW_ANSWER_FORMATION_DRY_RUN_EXECUTION_RESULT_V1" in markdown
    assert "final answer:" not in markdown.lower()
    assert "provider output:" not in markdown.lower()
    if before is not None:
        path.write_text(before)
    else:
        path.unlink()


def test_validation_pass_is_not_authority():
    result = build_answer_formation_dry_run_execution_result_v1()
    validation = validate_answer_formation_dry_run_execution_result_v1(result)
    assert validation["valid"] is True
    assert result["answer_authority_granted"] is False
    assert result["composition_authority_granted"] is False
    assert result["runtime_authority_granted"] is False
    assert result["final_answer_generated"] is False
    assert result["provider_call_made"] is False
    assert result["chat_responder_called"] is False
