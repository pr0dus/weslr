from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from weslr.answer_formation import (
    ADDITIONAL_FALSE_FIELDS_V1,
    ALLOWED_CANDIDATE_FORMATION_LABELS_V1,
    ALLOWED_CANDIDATE_REJECTION_LABELS_V1,
    ALLOWED_GATE_STATUSES_V1,
    ALLOWED_METADATA_INPUTS_V1,
    ARTIFACT_TYPE_V1,
    FALSE_AUTHORITY_FIELDS_V1,
    FORBIDDEN_INPUTS_V1,
    REQUIRED_GATE_STATUSES_V1,
    REQUIRED_NO_AUTHORITY_LABELS_V1,
    SCHEMA_VERSION_V1,
    build_answer_formation_artifact_v1,
    render_answer_formation_artifact_markdown_v1,
    summarize_answer_formation_artifact_v1,
    to_answer_formation_artifact_json_safe_v1,
    validate_answer_formation_artifact_v1,
)


def test_module_import_is_safe_and_public_api_exists():
    before = set(Path(".").glob(".weslr*"))
    module = importlib.import_module("weslr.answer_formation")
    after = set(Path(".").glob(".weslr*"))
    assert before == after
    for name in (
        "build_answer_formation_artifact_v1",
        "validate_answer_formation_artifact_v1",
        "summarize_answer_formation_artifact_v1",
        "render_answer_formation_artifact_markdown_v1",
        "to_answer_formation_artifact_json_safe_v1",
    ):
        assert hasattr(module, name)


def test_build_artifact_required_shape_and_flags():
    artifact = build_answer_formation_artifact_v1()
    assert artifact["artifact_type"] == ARTIFACT_TYPE_V1
    assert artifact["schema_version"] == SCHEMA_VERSION_V1
    for flag in (
        "metadata_only",
        "internal_only",
        "helper_only",
        "non_runtime",
        "non_user_facing",
        "deterministic",
        "import_safe",
        "side_effect_free",
        "in_memory_only",
        "qualitative_only",
    ):
        assert artifact[flag] is True
    assert artifact["blocked"] is False


@pytest.mark.parametrize("flag", FALSE_AUTHORITY_FIELDS_V1 + ADDITIONAL_FALSE_FIELDS_V1)
def test_build_artifact_preserves_authority_flags_false(flag):
    artifact = build_answer_formation_artifact_v1()
    assert artifact[flag] is False


def test_required_false_map_preserves_required_false_fields():
    artifact = build_answer_formation_artifact_v1()
    assert set(artifact["required_false_no_authority_fields"]) == set(FALSE_AUTHORITY_FIELDS_V1)
    assert all(value is False for value in artifact["required_false_no_authority_fields"].values())


def test_build_artifact_includes_required_no_authority_labels():
    artifact = build_answer_formation_artifact_v1()
    for label in REQUIRED_NO_AUTHORITY_LABELS_V1:
        assert label in artifact["required_no_authority_labels"]


def test_build_artifact_includes_allowed_metadata_inputs_and_forbidden_checks():
    artifact = build_answer_formation_artifact_v1()
    assert set(artifact["allowed_metadata_inputs"]) == set(ALLOWED_METADATA_INPUTS_V1)
    assert set(artifact["forbidden_inputs_checked"]) == set(FORBIDDEN_INPUTS_V1)


def test_validate_default_artifact_passes():
    artifact = build_answer_formation_artifact_v1()
    validation = validate_answer_formation_artifact_v1(artifact)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["errors"] == []
    assert validation["safety_booleans_valid"] is True
    assert validation["gate_statuses_valid"] is True
    assert validation["candidate_formation_metadata_valid"] is True
    assert validation["candidate_rejection_metadata_valid"] is True
    assert validation["safe_to_render"] is True
    assert validation["json_safe"] is True


@pytest.mark.parametrize("gate,status", list(REQUIRED_GATE_STATUSES_V1.items()))
def test_required_gate_statuses_present(gate, status):
    artifact = build_answer_formation_artifact_v1()
    assert artifact["gate_statuses"][gate] == status
    assert artifact["gate_statuses"][gate] in ALLOWED_GATE_STATUSES_V1


@pytest.mark.parametrize("gate", list(REQUIRED_GATE_STATUSES_V1))
def test_each_gate_accepts_allowed_non_authority_statuses(gate):
    artifact = build_answer_formation_artifact_v1(gate_statuses={gate: "present"})
    validation = validate_answer_formation_artifact_v1(artifact)
    if REQUIRED_GATE_STATUSES_V1[gate] == "blocked_not_authorized":
        assert validation["valid"] is False
        assert f"authority_gate_not_blocked:{gate}" in validation["errors"]
    else:
        assert f"invalid_gate_status:{gate}" not in validation["errors"]


def test_unknown_gate_status_fails_validation():
    artifact = build_answer_formation_artifact_v1(gate_statuses={"evidence_gate": "ready_for_runtime"})
    validation = validate_answer_formation_artifact_v1(artifact)
    assert validation["valid"] is False
    assert "invalid_gate_status:evidence_gate" in validation["errors"]


@pytest.mark.parametrize("flag", FALSE_AUTHORITY_FIELDS_V1 + ADDITIONAL_FALSE_FIELDS_V1)
def test_authority_flag_true_fails_validation(flag):
    artifact = build_answer_formation_artifact_v1()
    artifact[flag] = True
    validation = validate_answer_formation_artifact_v1(artifact)
    assert validation["valid"] is False
    assert f"authority_flag_not_false:{flag}" in validation["errors"]


def test_missing_required_field_fails_validation():
    artifact = build_answer_formation_artifact_v1()
    artifact.pop("metadata_only")
    validation = validate_answer_formation_artifact_v1(artifact)
    assert validation["valid"] is False
    assert "missing_required_field:metadata_only" in validation["errors"]
    assert "required_true_field_invalid:metadata_only" in validation["errors"]


def test_exact_helper_and_test_paths_are_preserved():
    artifact = build_answer_formation_artifact_v1()
    assert artifact["helper_module_path"] == "weslr/answer_formation.py"
    assert artifact["test_module_path"] == "weslr/tests/test_answer_formation_v1.py"


def test_unknown_allowed_metadata_input_fails_validation():
    artifact = build_answer_formation_artifact_v1(
        allowed_metadata_inputs=[*ALLOWED_METADATA_INPUTS_V1, "raw_prompt_text"]
    )
    validation = validate_answer_formation_artifact_v1(artifact)
    assert validation["valid"] is False
    assert "unknown_allowed_metadata_inputs" in validation["errors"]


def test_missing_forbidden_input_checks_fail_validation():
    artifact = build_answer_formation_artifact_v1(forbidden_inputs_checked=["raw_prompt_text"])
    validation = validate_answer_formation_artifact_v1(artifact)
    assert validation["valid"] is False
    assert "missing_forbidden_input_checks" in validation["errors"]


def test_candidate_formation_metadata_accepts_safe_labels_counts_and_booleans():
    artifact = build_answer_formation_artifact_v1(
        candidate_formation_metadata={
            "candidate_type_labels": ["state_frame_candidate", "governance_safe_candidate"],
            "candidate_count": 2,
            "selected_candidate_metadata_present": True,
        }
    )
    validation = validate_answer_formation_artifact_v1(artifact)
    assert validation["valid"] is True
    assert validation["candidate_formation_metadata_valid"] is True


@pytest.mark.parametrize("label", ALLOWED_CANDIDATE_FORMATION_LABELS_V1)
def test_each_candidate_formation_label_is_allowed(label):
    artifact = build_answer_formation_artifact_v1(candidate_formation_metadata={"candidate_type_labels": [label]})
    validation = validate_answer_formation_artifact_v1(artifact)
    assert "unknown_candidate_formation_labels" not in validation["errors"]


def test_unknown_candidate_formation_label_fails_validation():
    artifact = build_answer_formation_artifact_v1(candidate_formation_metadata={"candidate_type_labels": ["answer_draft_text"]})
    validation = validate_answer_formation_artifact_v1(artifact)
    assert validation["valid"] is False
    assert "unknown_candidate_formation_labels" in validation["errors"]


def test_candidate_count_must_be_nonnegative_integer():
    artifact = build_answer_formation_artifact_v1(candidate_formation_metadata={"candidate_count": -1})
    validation = validate_answer_formation_artifact_v1(artifact)
    assert "candidate_count_invalid" in validation["errors"]


def test_candidate_rejection_metadata_accepts_safe_labels():
    artifact = build_answer_formation_artifact_v1(
        candidate_rejection_metadata={"rejection_reason_labels": ["insufficient_evidence", "governance_blocked"]}
    )
    validation = validate_answer_formation_artifact_v1(artifact)
    assert validation["valid"] is True
    assert validation["candidate_rejection_metadata_valid"] is True


@pytest.mark.parametrize("label", ALLOWED_CANDIDATE_REJECTION_LABELS_V1)
def test_each_candidate_rejection_label_is_allowed(label):
    artifact = build_answer_formation_artifact_v1(candidate_rejection_metadata={"rejection_reason_labels": [label]})
    validation = validate_answer_formation_artifact_v1(artifact)
    assert "unknown_candidate_rejection_labels" not in validation["errors"]


def test_unknown_candidate_rejection_label_fails_validation():
    artifact = build_answer_formation_artifact_v1(candidate_rejection_metadata={"rejection_reason_labels": ["final_answer_prose"]})
    validation = validate_answer_formation_artifact_v1(artifact)
    assert validation["valid"] is False
    assert "unknown_candidate_rejection_labels" in validation["errors"]


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
    artifact = build_answer_formation_artifact_v1()
    artifact[key] = value
    validation = validate_answer_formation_artifact_v1(artifact)
    assert validation["valid"] is False
    assert validation[label] is True


def test_build_with_blocked_reasons_returns_blocked_artifact():
    artifact = build_answer_formation_artifact_v1(blocked_reasons=["blocked_raw_prompt_detected"])
    validation = validate_answer_formation_artifact_v1(artifact)
    assert artifact["blocked"] is True
    assert validation["valid"] is False
    assert validation["blocked"] is True


def test_blocked_without_reasons_fails_validation():
    artifact = build_answer_formation_artifact_v1()
    artifact["blocked"] = True
    validation = validate_answer_formation_artifact_v1(artifact)
    assert "blocked_without_reasons" in validation["errors"]


def test_blocked_reasons_present_when_not_blocked_fails_validation():
    artifact = build_answer_formation_artifact_v1()
    artifact["blocked_reasons"] = ["blocked_test"]
    validation = validate_answer_formation_artifact_v1(artifact)
    assert "blocked_reasons_present_when_not_blocked" in validation["errors"]


def test_summary_uses_safe_labels_only():
    artifact = build_answer_formation_artifact_v1(
        candidate_formation_metadata={"candidate_type_labels": ["state_frame_candidate"], "candidate_count": 1}
    )
    summary = summarize_answer_formation_artifact_v1(artifact)
    assert summary["artifact_type"] == ARTIFACT_TYPE_V1
    assert summary["valid"] is True
    assert summary["blocked"] is False
    assert summary["all_authority_flags_false"] is True
    assert summary["gate_statuses_valid"] is True
    assert summary["candidate_count"] == 1
    assert summary["validation_error_labels"] == []


def test_summary_for_invalid_input_is_safe():
    summary = summarize_answer_formation_artifact_v1({"artifact_type": "bad"})
    assert summary["valid"] is False
    assert summary["blocked"] is True
    assert "artifact_type_invalid" in summary["validation_error_labels"]


def test_markdown_render_safe_default_artifact():
    artifact = build_answer_formation_artifact_v1()
    markdown = render_answer_formation_artifact_markdown_v1(artifact)
    assert "# Answer Formation Artifact V1" in markdown
    assert "helper_metadata_not_answer_text" in markdown
    assert "validation_pass_not_answer_authority" in markdown
    assert "final answer:" not in markdown.lower()
    assert "provider output:" not in markdown.lower()


def test_markdown_renderer_blocks_and_does_not_leak_unsafe_content():
    artifact = build_answer_formation_artifact_v1()
    artifact["raw_prompt_text"] = "raw prompt: DO NOT LEAK THIS"
    markdown = render_answer_formation_artifact_markdown_v1(artifact)
    assert "# Answer Formation Artifact V1 — Blocked" in markdown
    assert "raw_content_detected" in markdown
    assert "DO NOT LEAK THIS" not in markdown
    assert "raw prompt: DO NOT LEAK THIS" not in markdown


def test_json_safe_copy_preserves_safe_metadata_and_is_json_serializable():
    artifact = build_answer_formation_artifact_v1(
        candidate_formation_metadata={"candidate_type_labels": ["state_frame_candidate"], "candidate_count": 1}
    )
    safe = to_answer_formation_artifact_json_safe_v1(artifact)
    assert safe == artifact
    assert safe is not artifact
    assert json.loads(json.dumps(safe))["artifact_type"] == ARTIFACT_TYPE_V1


def test_json_safe_invalid_wrapper_does_not_leak_unsafe_content():
    artifact = build_answer_formation_artifact_v1()
    artifact["provider_output"] = "provider output: DO NOT LEAK"
    safe = to_answer_formation_artifact_json_safe_v1(artifact)
    assert safe["artifact_type"].endswith("_invalid")
    assert safe["blocked"] is True
    assert "provider_output_detected" in safe["errors"]
    assert "DO NOT LEAK" not in json.dumps(safe)


def test_validation_pass_is_metadata_quality_only_not_authority():
    artifact = build_answer_formation_artifact_v1()
    validation = validate_answer_formation_artifact_v1(artifact)
    assert validation["valid"] is True
    assert artifact["answer_authority_granted"] is False
    assert artifact["composition_authority_granted"] is False
    assert artifact["runtime_authority_granted"] is False
    assert "validation_pass_metadata_quality_evidence_only" in artifact["validation_labels"]


def test_no_chat_responder_runtime_import_or_call_fields():
    artifact = build_answer_formation_artifact_v1()
    assert artifact["chat_responder_called"] is False
    assert artifact["chat_responder_modified"] is False
    validation = validate_answer_formation_artifact_v1(artifact)
    assert validation["valid"] is True
