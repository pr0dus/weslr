from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.controlled_answer_composition_dry_run_execution import (
    DENIED_AUTHORITY_FIELDS_V1,
    FALSE_CONFIRMATION_FIELDS_V1,
    NEXT_LANE_V1,
    RESULT_ARTIFACT_PATH_V1,
    build_controlled_answer_composition_dry_run_result_markdown_v1,
    execute_controlled_answer_composition_dry_run_v1,
    render_controlled_answer_composition_dry_run_execution_result_markdown_v1,
    write_controlled_answer_composition_dry_run_result_artifact_v1,
)


REQUIRED_FALSE_MARKERS = (
    "answer_composition_attempted=false",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
)

FORBIDDEN_RENDER_MARKERS = (
    "raw prompt:",
    "raw response:",
    "private content:",
    "hidden prompt:",
    "answer key:",
    "provider output:",
    "model output:",
    "search output:",
    "advisor output:",
    "runtime output:",
    "live dialogue transcript:",
    "final answer:",
    "official score:",
    "judge decision:",
    "composed reply:",
)


def test_execute_result_is_synthetic_metadata_only_and_json_safe():
    result = execute_controlled_answer_composition_dry_run_v1()
    assert result["metadata_only"] is True
    assert result["internal_only"] is True
    assert result["synthetic_only"] is True
    assert result["non_runtime"] is True
    assert result["non_user_facing"] is True
    assert result["result_artifact_path"] == RESULT_ARTIFACT_PATH_V1
    assert result["helper_summary"]["valid"] is True
    assert result["helper_summary"]["blocked"] is False
    assert result["helper_json_safe_metadata_preserved"] is True
    assert result["helper_safe_markdown_rendered"] is True
    json.dumps(result, sort_keys=True)


def test_execute_result_preserves_all_false_and_denied_authority_fields():
    result = execute_controlled_answer_composition_dry_run_v1()
    false_fields = result["required_false_no_authority_fields"]
    assert set(false_fields) == set(FALSE_CONFIRMATION_FIELDS_V1)
    assert all(value is False for value in false_fields.values())
    assert result["denied_authority_fields"] == DENIED_AUTHORITY_FIELDS_V1
    assert all(value == "denied" for value in result["denied_authority_fields"].values())


def test_execute_result_validation_statuses_are_metadata_quality_only():
    result = execute_controlled_answer_composition_dry_run_v1()
    validation = result["validation_status_fields"]
    assert validation["artifact_schema_valid"] is True
    assert validation["metadata_only_valid"] is True
    assert validation["internal_only_valid"] is True
    assert validation["synthetic_only_valid"] is True
    assert validation["forbidden_content_absent"] is True
    assert validation["required_false_fields_valid"] is True
    assert validation["denied_authority_fields_valid"] is True
    assert validation["gate_statuses_valid"] is True
    assert validation["safe_markdown_valid"] is True
    assert validation["json_safe_valid"] is True
    assert validation["release_gate_passed"] == "not_run_in_artifact_generation"
    assert validation["release_check_passed"] == "not_run_in_artifact_generation"


def test_markdown_contains_required_confirmations_and_next_lane():
    markdown = build_controlled_answer_composition_dry_run_result_markdown_v1()
    assert "# WESLR Controlled Answer Composition Dry Run Result Artifact V1" in markdown
    assert f"Result artifact path: `{RESULT_ARTIFACT_PATH_V1}`" in markdown
    assert f"Next lane: `{NEXT_LANE_V1}`" in markdown
    assert "validation_pass_meaning: `metadata_quality_evidence_only`" in markdown
    assert "OCC/OpenClaw is not deployed WESLR and is not WESLR" in markdown
    for marker in REQUIRED_FALSE_MARKERS:
        assert f"`{marker}`" in markdown
    for authority in DENIED_AUTHORITY_FIELDS_V1:
        assert f"`{authority}: denied`" in markdown


@pytest.mark.parametrize("marker", FORBIDDEN_RENDER_MARKERS)
def test_markdown_does_not_render_forbidden_content_markers(marker):
    markdown = build_controlled_answer_composition_dry_run_result_markdown_v1().lower()
    assert marker not in markdown


def test_render_rejects_path_drift():
    result = execute_controlled_answer_composition_dry_run_v1()
    result["result_artifact_path"] = "docs/OTHER.md"
    with pytest.raises(ValueError, match="result_path_invalid"):
        render_controlled_answer_composition_dry_run_execution_result_markdown_v1(result)


def test_render_rejects_authority_flag_drift():
    result = execute_controlled_answer_composition_dry_run_v1()
    result["required_false_no_authority_fields"]["answer_authority_granted"] = True
    with pytest.raises(ValueError, match="false_fields_invalid"):
        render_controlled_answer_composition_dry_run_execution_result_markdown_v1(result)


def test_render_rejects_denied_authority_drift():
    result = execute_controlled_answer_composition_dry_run_v1()
    result["denied_authority_fields"]["answer_authority"] = "granted"
    with pytest.raises(ValueError, match="denied_fields_invalid"):
        render_controlled_answer_composition_dry_run_execution_result_markdown_v1(result)


def test_write_result_artifact_exact_path_under_repository_root(tmp_path: Path):
    target = write_controlled_answer_composition_dry_run_result_artifact_v1(repository_root=tmp_path)
    assert target == tmp_path / RESULT_ARTIFACT_PATH_V1
    assert target.exists()
    markdown = target.read_text(encoding="utf-8")
    assert "controlled_answer_composition_dry_run_execution_result_created" in markdown
    for marker in REQUIRED_FALSE_MARKERS:
        assert f"`{marker}`" in markdown
    with pytest.raises(FileExistsError):
        write_controlled_answer_composition_dry_run_result_artifact_v1(repository_root=tmp_path)
