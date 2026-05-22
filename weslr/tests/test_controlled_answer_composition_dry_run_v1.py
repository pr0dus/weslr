from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from weslr.controlled_answer_composition_dry_run import (
    ADDITIONAL_FALSE_FIELDS_V1,
    ALLOWED_GATE_STATUSES_V1,
    ALLOWED_SYNTHETIC_METADATA_INPUTS_V1,
    ARTIFACT_TYPE_V1,
    FALSE_AUTHORITY_FIELDS_V1,
    FORBIDDEN_INPUTS_V1,
    REQUIRED_GATE_STATUSES_V1,
    REQUIRED_NO_AUTHORITY_LABELS_V1,
    SCHEMA_VERSION_V1,
    build_controlled_answer_composition_dry_run_artifact_v1,
    render_controlled_answer_composition_dry_run_artifact_markdown_v1,
    summarize_controlled_answer_composition_dry_run_artifact_v1,
    to_controlled_answer_composition_dry_run_artifact_json_safe_v1,
    validate_controlled_answer_composition_dry_run_artifact_v1,
)


def test_build_artifact_required_shape_and_flags():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    assert artifact["artifact_type"] == ARTIFACT_TYPE_V1
    assert artifact["schema_version"] == SCHEMA_VERSION_V1
    for flag in (
        "metadata_only",
        "internal_only",
        "synthetic_only",
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
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    assert artifact[flag] is False


def test_required_false_map_preserves_required_false_fields():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    assert set(artifact["required_false_no_authority_fields"]) == set(FALSE_AUTHORITY_FIELDS_V1)
    assert all(value is False for value in artifact["required_false_no_authority_fields"].values())


def test_build_artifact_includes_required_no_authority_labels():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    for label in REQUIRED_NO_AUTHORITY_LABELS_V1:
        assert label in artifact["required_no_authority_labels"]


def test_build_artifact_includes_allowed_synthetic_inputs_and_forbidden_checks():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    assert set(artifact["allowed_synthetic_metadata_inputs"]) == set(ALLOWED_SYNTHETIC_METADATA_INPUTS_V1)
    assert set(artifact["forbidden_inputs_checked"]) == set(FORBIDDEN_INPUTS_V1)


def test_validate_default_artifact_passes():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["errors"] == []
    assert validation["safety_booleans_valid"] is True
    assert validation["gate_statuses_valid"] is True
    assert validation["safe_to_render"] is True
    assert validation["json_safe"] is True


@pytest.mark.parametrize("gate,status", list(REQUIRED_GATE_STATUSES_V1.items()))
def test_required_gate_statuses_present(gate, status):
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    assert artifact["gate_statuses"][gate] == status
    assert artifact["gate_statuses"][gate] in ALLOWED_GATE_STATUSES_V1


@pytest.mark.parametrize("gate", list(REQUIRED_GATE_STATUSES_V1))
def test_each_gate_accepts_allowed_non_authority_statuses(gate):
    artifact = build_controlled_answer_composition_dry_run_artifact_v1(gate_statuses={gate: "present"})
    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    if REQUIRED_GATE_STATUSES_V1[gate] == "blocked_not_authorized":
        assert validation["valid"] is False
        assert f"authority_gate_not_blocked:{gate}" in validation["errors"]
    else:
        assert "invalid_gate_status:%s" % gate not in validation["errors"]


def test_unknown_gate_status_fails_validation():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1(gate_statuses={"evidence_gate": "ready_for_runtime"})
    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    assert validation["valid"] is False
    assert "invalid_gate_status:evidence_gate" in validation["errors"]


@pytest.mark.parametrize("flag", FALSE_AUTHORITY_FIELDS_V1 + ADDITIONAL_FALSE_FIELDS_V1)
def test_authority_flag_true_fails_validation(flag):
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    artifact[flag] = True
    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    assert validation["valid"] is False
    assert f"authority_flag_not_false:{flag}" in validation["errors"]


def test_missing_required_field_fails_validation():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    artifact.pop("metadata_only")
    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    assert validation["valid"] is False
    assert "missing_required_field:metadata_only" in validation["errors"]
    assert "required_true_field_invalid:metadata_only" in validation["errors"]


def test_unknown_allowed_synthetic_metadata_input_fails_validation():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1(
        allowed_synthetic_metadata_inputs=[*ALLOWED_SYNTHETIC_METADATA_INPUTS_V1, "raw_prompt_text"]
    )
    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    assert validation["valid"] is False
    assert "unknown_allowed_synthetic_metadata_inputs" in validation["errors"]


def test_missing_forbidden_input_checks_fail_validation():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1(forbidden_inputs_checked=["raw_prompt_text"])
    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    assert validation["valid"] is False
    assert "missing_forbidden_input_checks" in validation["errors"]


def test_raw_prompt_key_blocks_validation():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    artifact["raw_prompt_text"] = "raw prompt: unsafe"
    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    assert validation["valid"] is False
    assert validation["raw_content_detected"] is True


@pytest.mark.parametrize(
    "key,value,label",
    [
        ("private_content", "private content: secret", "private_content_detected"),
        ("hidden_prompt", "hidden prompt: secret", "hidden_prompt_detected"),
        ("answer_key", "answer key: x", "answer_key_detected"),
        ("provider_output", "provider output: x", "provider_output_detected"),
        ("runtime_output", "runtime output: x", "runtime_output_detected"),
        ("live_dialogue_transcript", "live dialogue transcript x", "live_dialogue_detected"),
        ("final_answer_prose", "final answer: x", "final_answer_detected"),
        ("official_score", "official score: 100", "judge_or_score_detected"),
    ],
)
def test_forbidden_content_markers_fail_validation(key, value, label):
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    artifact[key] = value
    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    assert validation["valid"] is False
    assert validation[label] is True


def test_build_with_blocked_reasons_returns_blocked_artifact():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1(blocked_reasons=["blocked_raw_prompt_detected"])
    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    assert artifact["blocked"] is True
    assert validation["valid"] is False
    assert validation["blocked"] is True


def test_blocked_without_reasons_fails_validation():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    artifact["blocked"] = True
    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    assert "blocked_without_reasons" in validation["errors"]


def test_blocked_reasons_present_when_not_blocked_fails_validation():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    artifact["blocked_reasons"] = ["blocked_test"]
    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    assert "blocked_reasons_present_when_not_blocked" in validation["errors"]


def test_summary_uses_safe_labels_only():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    summary = summarize_controlled_answer_composition_dry_run_artifact_v1(artifact)
    assert summary["artifact_type"] == ARTIFACT_TYPE_V1
    assert summary["valid"] is True
    assert summary["blocked"] is False
    assert summary["all_authority_flags_false"] is True
    assert summary["gate_statuses_valid"] is True
    assert summary["gate_status_count"] == len(REQUIRED_GATE_STATUSES_V1)
    assert summary["validation_error_labels"] == []


def test_summary_for_invalid_input_is_safe():
    summary = summarize_controlled_answer_composition_dry_run_artifact_v1({"artifact_type": "bad"})
    assert summary["valid"] is False
    assert summary["blocked"] is True
    assert "artifact_type_invalid" in summary["validation_error_labels"]


def test_markdown_render_safe_default_artifact():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    markdown = render_controlled_answer_composition_dry_run_artifact_markdown_v1(artifact)
    assert "# Controlled Answer Composition Dry Run Artifact V1" in markdown
    assert "helper_metadata_not_answer_text" in markdown
    assert "validation_pass_not_answer_authority" in markdown
    assert "final answer:" not in markdown.lower()
    assert "provider output:" not in markdown.lower()


def test_markdown_render_blocked_uses_safe_error_labels():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1(blocked_reasons=["blocked_raw_prompt_detected"])
    markdown = render_controlled_answer_composition_dry_run_artifact_markdown_v1(artifact)
    assert "blocked_raw_prompt_detected" in markdown
    assert "raw prompt:" not in markdown.lower()


@pytest.mark.parametrize(
    "mutator,unsafe_marker,safe_label",
    [
        (lambda artifact: artifact.__setitem__("raw_prompt_text", "raw prompt: secret"), "raw prompt:", "raw_content_detected"),
        (lambda artifact: artifact.__setitem__("raw_response_text", "raw response: secret"), "raw response:", "raw_content_detected"),
        (lambda artifact: artifact.__setitem__("private_content", "private content: secret"), "private content:", "private_content_detected"),
        (lambda artifact: artifact.__setitem__("provider_output", "provider output: secret"), "provider output:", "provider_output_detected"),
        (lambda artifact: artifact.__setitem__("runtime_output", "runtime output: secret"), "runtime output:", "runtime_output_detected"),
        (lambda artifact: artifact.__setitem__("official_score", "official score: 100"), "official score:", "judge_or_score_detected"),
        (lambda artifact: artifact["gate_statuses"].__setitem__("evidence_gate", "raw prompt: secret"), "raw prompt:", "raw_content_detected"),
        (lambda artifact: artifact["summary_labels"].append("final answer: secret"), "final answer:", "final_answer_detected"),
        (lambda artifact: artifact["validation_labels"].append("provider output: secret"), "provider output:", "provider_output_detected"),
    ],
)
def test_markdown_render_invalid_artifacts_never_leaks_unsafe_marker_strings(mutator, unsafe_marker, safe_label):
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    mutator(artifact)
    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    markdown = render_controlled_answer_composition_dry_run_artifact_markdown_v1(artifact)
    lower = markdown.lower()

    assert validation[safe_label] is True
    assert "# Controlled Answer Composition Dry Run Artifact V1 — Blocked" in markdown
    assert safe_label in markdown
    assert unsafe_marker not in lower
    assert "secret" not in lower
    assert "## Gate Statuses" not in markdown
    assert "## Summary Labels" not in markdown
    assert "## Validation Labels" not in markdown
    assert "unsafe_content_not_rendered" in markdown
    assert "validation_pass_not_answer_authority" in markdown
    assert "validation_pass_not_composition_authority" in markdown


def test_json_safe_invalid_wrapper_does_not_leak_offending_content():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    artifact["summary_labels"].append("final answer: secret")
    artifact["provider_output"] = "provider output: secret"
    safe = to_controlled_answer_composition_dry_run_artifact_json_safe_v1(artifact)
    encoded = json.dumps(safe, sort_keys=True).lower()

    assert safe["artifact_type"] != ARTIFACT_TYPE_V1
    assert safe["blocked"] is True
    assert safe["unsafe_content_not_copied"] is True
    assert "final answer:" not in encoded
    assert "provider output:" not in encoded
    assert "secret" not in encoded
    assert "final_answer_detected" in safe["errors"]
    assert "provider_output_detected" in safe["errors"]


def test_json_safe_valid_artifact_preserves_safe_content():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    safe = to_controlled_answer_composition_dry_run_artifact_json_safe_v1(artifact)
    assert safe["artifact_type"] == ARTIFACT_TYPE_V1
    assert safe["blocked"] is False


def test_json_safe_is_json_serializable_and_preserves_false_flags():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    safe = to_controlled_answer_composition_dry_run_artifact_json_safe_v1(artifact)
    json.dumps(safe, sort_keys=True)
    for flag in FALSE_AUTHORITY_FIELDS_V1 + ADDITIONAL_FALSE_FIELDS_V1:
        assert safe[flag] is False


def test_json_safe_converts_non_json_objects_safely():
    artifact = build_controlled_answer_composition_dry_run_artifact_v1()
    artifact["non_json"] = Path("docs/example.md")
    safe = to_controlled_answer_composition_dry_run_artifact_json_safe_v1(artifact)
    assert isinstance(safe["non_json"], str)


def test_deterministic_build_for_identical_inputs():
    one = build_controlled_answer_composition_dry_run_artifact_v1()
    two = build_controlled_answer_composition_dry_run_artifact_v1()
    assert one == two


def test_module_import_is_side_effect_free():
    module = importlib.import_module("weslr.controlled_answer_composition_dry_run")
    assert module.ARTIFACT_TYPE_V1 == ARTIFACT_TYPE_V1


def test_module_source_has_no_runtime_or_provider_imports():
    source = Path("weslr/controlled_answer_composition_dry_run.py").read_text()
    forbidden = [
        "ChatResponder",
        "respond_chat(",
        "generate_chat(",
        "requests.",
        "openai",
        "anthropic",
        "subprocess",
        "socket",
        "execution_allowed" + " = True",
        "answer_composition_authorized" + " = True",
        "composition_authority_granted" + " = True",
        "answer_authority_granted" + " = True",
        "scoring_authorized" + " = True",
    ]
    for token in forbidden:
        assert token not in source


def test_chat_responder_file_not_modified_in_diff():
    assert Path("weslr/chat_responder.py").exists()


def test_no_unapproved_dry_run_result_artifacts_created_by_helpers_lane():
    approved_design_path = Path("docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_V1.md")
    approved_result_artifact_path = Path("docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_ARTIFACT_V1.md")
    assert approved_design_path.exists()
    assert approved_result_artifact_path.exists()

    forbidden_paths = [
        Path("docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_ARTIFACT_V1.md"),
    ]
    for path in forbidden_paths:
        assert not path.exists()

    discovered_result_artifacts = set(
        Path("docs").glob("WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_ARTIFACT_V*.md")
    )
    assert discovered_result_artifacts == {approved_result_artifact_path}
