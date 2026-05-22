from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from weslr.answer_formation_report_run import (
    ARTIFACT_TYPE_V1,
    DENIED_AUTHORITY_FIELDS_V1,
    RESULT_ARTIFACT_PATH_V1,
    SCHEMA_VERSION_V1,
    build_answer_formation_report_run_v1,
    render_answer_formation_report_run_markdown_v1,
    run_answer_formation_report_run_v1,
    summarize_answer_formation_report_run_v1,
    to_answer_formation_report_run_json_safe_v1,
    validate_answer_formation_report_run_v1,
    write_answer_formation_report_run_result_v1,
)


def test_module_import_is_safe_and_public_api_exists():
    before = set(Path(".").glob(".weslr*"))
    module = importlib.import_module("weslr.answer_formation_report_run")
    after = set(Path(".").glob(".weslr*"))
    assert before == after
    for name in (
        "build_answer_formation_report_run_v1",
        "validate_answer_formation_report_run_v1",
        "summarize_answer_formation_report_run_v1",
        "render_answer_formation_report_run_markdown_v1",
        "to_answer_formation_report_run_json_safe_v1",
        "write_answer_formation_report_run_result_v1",
        "run_answer_formation_report_run_v1",
    ):
        assert hasattr(module, name)


def test_build_report_run_required_shape_and_flags():
    artifact = build_answer_formation_report_run_v1()
    assert artifact["artifact_type"] == ARTIFACT_TYPE_V1
    assert artifact["schema_version"] == SCHEMA_VERSION_V1
    for flag in (
        "metadata_only",
        "internal_only",
        "report_run_only",
        "helper_based",
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
        assert artifact[flag] is True
    assert artifact["result_artifact_path"] == RESULT_ARTIFACT_PATH_V1
    assert artifact["blocked"] is False


@pytest.mark.parametrize("field", DENIED_AUTHORITY_FIELDS_V1)
def test_denied_authority_fields_remain_false(field):
    artifact = build_answer_formation_report_run_v1()
    assert artifact[field] is False
    assert artifact["denied_authority_fields"][field] is False


def test_default_report_run_validates_and_uses_report_helpers():
    artifact = build_answer_formation_report_run_v1()
    validation = validate_answer_formation_report_run_v1(artifact)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["report_helper_validation_valid"] is True
    assert artifact["report_helper_validation"]["valid"] is True
    assert artifact["report_helper_summary"]["valid"] is True
    assert "safe_markdown_eligible" in artifact["report_helper_aggregate_labels"]


def test_render_result_markdown_is_safe_and_confirms_boundaries():
    artifact = build_answer_formation_report_run_v1()
    markdown = render_answer_formation_report_run_markdown_v1(artifact)
    assert "# WESLR Answer Formation Report Run Result V1" in markdown
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
    artifact = build_answer_formation_report_run_v1()
    safe = to_answer_formation_report_run_json_safe_v1(artifact)
    assert safe == artifact
    assert safe is not artifact
    assert json.loads(json.dumps(safe))["artifact_type"] == ARTIFACT_TYPE_V1


def test_unsafe_content_blocks_without_leaking_value():
    artifact = build_answer_formation_report_run_v1()
    artifact["provider_output"] = "provider output: DO NOT LEAK"
    validation = validate_answer_formation_report_run_v1(artifact)
    assert validation["valid"] is False
    assert validation["provider_output_detected"] is True
    markdown = render_answer_formation_report_run_markdown_v1(artifact)
    assert "provider_output_detected" in markdown
    assert "DO NOT LEAK" not in markdown
    safe = to_answer_formation_report_run_json_safe_v1(artifact)
    assert safe["artifact_type"].endswith("_invalid")
    assert "DO NOT LEAK" not in json.dumps(safe)


def test_wrong_result_path_blocks_and_does_not_write(tmp_path):
    wrong = tmp_path / "wrong.md"
    artifact = build_answer_formation_report_run_v1(result_artifact_path=str(wrong))
    validation = validate_answer_formation_report_run_v1(artifact)
    assert validation["valid"] is False
    assert "result_artifact_path_invalid" in validation["errors"]
    result = write_answer_formation_report_run_result_v1(artifact, result_artifact_path=str(wrong))
    assert result["written"] is False
    assert not wrong.exists()


def test_validation_pass_is_metadata_quality_only_not_authority():
    artifact = build_answer_formation_report_run_v1()
    validation = validate_answer_formation_report_run_v1(artifact)
    assert validation["valid"] is True
    assert "validation_pass_metadata_quality_evidence_only" in artifact["validation_labels"]
    assert artifact["answer_authority_granted"] is False
    assert artifact["composition_authority_granted"] is False
    assert artifact["runtime_authority_granted"] is False


def test_run_writes_exact_approved_result_artifact():
    result = run_answer_formation_report_run_v1()
    assert result["written"] is True
    assert result["path"] == RESULT_ARTIFACT_PATH_V1
    path = Path(RESULT_ARTIFACT_PATH_V1)
    assert path.exists()
    content = path.read_text()
    assert "# WESLR Answer Formation Report Run Result V1" in content
    assert "REVIEW_ANSWER_FORMATION_REPORT_RUN_RESULT_V1" in content
    assert "weslr_chat_responder_py_untouched" in content
    assert "final answer:" not in content.lower()
    assert "provider output:" not in content.lower()


def test_summary_uses_safe_labels_counts_and_booleans_only():
    artifact = build_answer_formation_report_run_v1()
    summary = summarize_answer_formation_report_run_v1(artifact)
    assert summary["artifact_type"] == ARTIFACT_TYPE_V1
    assert summary["valid"] is True
    assert summary["blocked"] is False
    assert summary["metadata_only"] is True
    assert summary["all_authority_fields_false"] is True
    assert summary["next_lane"] == "REVIEW_ANSWER_FORMATION_REPORT_RUN_RESULT_V1"
