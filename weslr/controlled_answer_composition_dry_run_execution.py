"""Controlled answer-composition dry-run execution V1.

Synthetic metadata-only execution wrapper around the reviewed controlled dry-run
helpers. This module does not implement answer composition, generate final
answers, execute prompts, create live dialogue, call providers/search/advisors,
wire runtime behavior, write .weslr state, enable feature flags, create judges
or scores, make official claims, or grant answer/composition/runtime authority.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from weslr.controlled_answer_composition_dry_run import (
    FALSE_AUTHORITY_FIELDS_V1,
    REQUIRED_GATE_STATUSES_V1,
    VISIBLE_RISKS_V1,
    build_controlled_answer_composition_dry_run_artifact_v1,
    render_controlled_answer_composition_dry_run_artifact_markdown_v1,
    summarize_controlled_answer_composition_dry_run_artifact_v1,
    to_controlled_answer_composition_dry_run_artifact_json_safe_v1,
    validate_controlled_answer_composition_dry_run_artifact_v1,
)

RESULT_ARTIFACT_PATH_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_ARTIFACT_V1.md"
SOURCE_EXECUTION_DESIGN_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_EXECUTION_V1.md"
SOURCE_EXECUTION_REVIEW_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_EXECUTION_REVIEW_V1.md"
SOURCE_RESULT_DESIGN_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_V1.md"
SOURCE_RESULT_REVIEW_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_REVIEW_V1.md"
SOURCE_HELPER_REVIEW_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
HELPER_MODULE_PATH_V1 = "weslr/controlled_answer_composition_dry_run.py"
EXECUTION_MODULE_PATH_V1 = "weslr/controlled_answer_composition_dry_run_execution.py"
EXECUTION_TEST_PATH_V1 = "weslr/tests/test_controlled_answer_composition_dry_run_execution_v1.py"
NEXT_LANE_V1 = "REVIEW_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_EXECUTION_RESULT_V1"

ADDITIONAL_FALSE_CONFIRMATION_FIELDS_V1 = (
    "chat_responder_called",
    "chat_responder_modified",
    "runtime_wired",
    "prompt_execution_performed",
    "live_dialogue_performed",
    "dry_run_result_artifact_is_final_answer",
    "user_facing_output_created",
)

FALSE_CONFIRMATION_FIELDS_V1 = (*FALSE_AUTHORITY_FIELDS_V1, *ADDITIONAL_FALSE_CONFIRMATION_FIELDS_V1)

DENIED_AUTHORITY_FIELDS_V1 = {
    "answer_authority": "denied",
    "composition_authority": "denied",
    "runtime_authority": "denied",
    "prompt_execution_authority": "denied",
    "live_dialogue_authority": "denied",
    "provider_authority": "denied",
    "persistence_authority": "denied",
    "feature_flag_authority": "denied",
    "judge_authority": "denied",
    "scoring_authority": "denied",
    "official_claim_authority": "denied",
}

DENIAL_LABELS_V1 = (
    "result_artifact_not_answer_text",
    "metadata_result_not_composition_authority",
    "validation_pass_not_answer_authority",
    "validation_pass_not_runtime_authority",
    "artifact_presence_not_official_claim",
    "artifact_presence_not_judge_or_score",
    "future_answer_composition_requires_separate_approval",
    "future_runtime_wiring_requires_separate_approval",
    "occ_openclaw_not_deployed_weslr",
)

SAFETY_CONFIRMATION_LABELS_V1 = (
    "synthetic_metadata_only",
    "internal_only",
    "validation_before_rendering_completed",
    "safe_markdown_only",
    "json_safe_metadata_preserved",
    "validation_pass_metadata_quality_evidence_only",
    "answer_composition_not_implemented",
    "final_answer_not_generated",
    "runtime_not_wired",
    "prompt_execution_not_performed",
    "live_dialogue_not_created",
    "provider_calls_not_made",
    "dot_weslr_not_written",
    "feature_flags_not_enabled",
    "judges_scores_not_created",
    "official_claims_not_made",
    "occ_openclaw_not_deployed_weslr",
)

FOLLOWUPS_V1 = (
    "review_result_artifact_before_context_alignment",
    "verify_no_raw_content_leakage",
    "verify_no_authority_wording_drift",
    "verify_chat_responder_untouched",
    "separate_approval_required_for_any_runtime_lane",
)


def _safe_bool(value: Any) -> bool:
    return value is True


def _build_base_helper_artifact() -> dict[str, Any]:
    return build_controlled_answer_composition_dry_run_artifact_v1(
        summary_labels=(
            "controlled_answer_composition_dry_run_execution_v1",
            "synthetic_metadata_helper_sequence_completed",
            "validation_pass_metadata_quality_evidence_only",
            "result_artifact_not_answer_text",
            "composition_authority_not_granted",
            "runtime_authority_not_granted",
        ),
        validation_labels=(
            "artifact_schema_valid",
            "metadata_only_valid",
            "internal_only_valid",
            "synthetic_only_valid",
            "allowed_fields_valid",
            "forbidden_content_absent",
            "required_false_fields_valid",
            "denied_authority_fields_valid",
            "gate_statuses_valid",
            "safe_markdown_valid",
            "json_safe_valid",
            "blocked_result_behavior_valid",
            "validation_pass_metadata_quality_evidence_only",
        ),
        visible_risks=(*VISIBLE_RISKS_V1, "result-artifact-as-final-answer"),
    )


def execute_controlled_answer_composition_dry_run_v1() -> dict[str, Any]:
    """Execute the synthetic metadata-only dry-run helper sequence in memory."""

    helper_artifact = _build_base_helper_artifact()

    validation = validate_controlled_answer_composition_dry_run_artifact_v1(helper_artifact)
    if validation.get("valid") is not True or validation.get("safe_to_render") is not True:
        raise ValueError("controlled_answer_composition_dry_run_validation_failed")

    summary = summarize_controlled_answer_composition_dry_run_artifact_v1(helper_artifact)
    json_safe = to_controlled_answer_composition_dry_run_artifact_json_safe_v1(helper_artifact)
    helper_markdown = render_controlled_answer_composition_dry_run_artifact_markdown_v1(helper_artifact)

    if not isinstance(json_safe, Mapping):
        raise ValueError("controlled_answer_composition_dry_run_json_safe_failed")
    if "# Controlled Answer Composition Dry Run Artifact V1" not in helper_markdown:
        raise ValueError("controlled_answer_composition_dry_run_safe_markdown_failed")

    false_confirmations = {field: False for field in FALSE_CONFIRMATION_FIELDS_V1}
    validation_status_fields = {
        "artifact_schema_valid": _safe_bool(validation.get("valid")),
        "metadata_only_valid": helper_artifact.get("metadata_only") is True,
        "internal_only_valid": helper_artifact.get("internal_only") is True,
        "synthetic_only_valid": helper_artifact.get("synthetic_only") is True,
        "allowed_fields_valid": "unknown_allowed_synthetic_metadata_inputs" not in validation.get("errors", ()),
        "forbidden_content_absent": not any(
            validation.get(label) is True
            for label in (
                "raw_content_detected",
                "private_content_detected",
                "hidden_prompt_detected",
                "answer_key_detected",
                "provider_output_detected",
                "runtime_output_detected",
                "live_dialogue_detected",
                "final_answer_detected",
                "official_claim_detected",
                "judge_or_score_detected",
            )
        ),
        "required_false_fields_valid": _safe_bool(validation.get("safety_booleans_valid")),
        "denied_authority_fields_valid": all(value == "denied" for value in DENIED_AUTHORITY_FIELDS_V1.values()),
        "gate_statuses_valid": _safe_bool(validation.get("gate_statuses_valid")),
        "safe_markdown_valid": _safe_bool(validation.get("safe_to_render")),
        "json_safe_valid": _safe_bool(validation.get("json_safe")),
        "blocked_result_behavior_valid": True,
        "release_gate_passed": "not_run_in_artifact_generation",
        "release_check_passed": "not_run_in_artifact_generation",
    }

    return {
        "artifact_type": "controlled_answer_composition_dry_run_execution_result_v1",
        "schema_version": "controlled_answer_composition_dry_run_execution_result_schema_v1",
        "metadata_only": True,
        "internal_only": True,
        "synthetic_only": True,
        "non_runtime": True,
        "non_user_facing": True,
        "qualitative_only": True,
        "result_artifact_path": RESULT_ARTIFACT_PATH_V1,
        "source_execution_design_doc": SOURCE_EXECUTION_DESIGN_DOC_V1,
        "source_execution_review_doc": SOURCE_EXECUTION_REVIEW_DOC_V1,
        "source_result_design_doc": SOURCE_RESULT_DESIGN_DOC_V1,
        "source_result_review_doc": SOURCE_RESULT_REVIEW_DOC_V1,
        "source_helper_review_doc": SOURCE_HELPER_REVIEW_DOC_V1,
        "source_helper_module_path": HELPER_MODULE_PATH_V1,
        "execution_module_path": EXECUTION_MODULE_PATH_V1,
        "execution_test_path": EXECUTION_TEST_PATH_V1,
        "dry_run_execution_label": "controlled_answer_composition_dry_run_execution_v1_synthetic_metadata_only",
        "dry_run_input_profile_label": "synthetic_metadata_only_internal_non_runtime_profile_v1",
        "safe_source_path_labels": (
            SOURCE_EXECUTION_DESIGN_DOC_V1,
            SOURCE_EXECUTION_REVIEW_DOC_V1,
            SOURCE_RESULT_DESIGN_DOC_V1,
            SOURCE_RESULT_REVIEW_DOC_V1,
            SOURCE_HELPER_REVIEW_DOC_V1,
            HELPER_MODULE_PATH_V1,
        ),
        "helper_summary": summary,
        "helper_json_safe_metadata_preserved": isinstance(json_safe, Mapping),
        "helper_safe_markdown_rendered": True,
        "required_false_no_authority_fields": false_confirmations,
        "denied_authority_fields": dict(DENIED_AUTHORITY_FIELDS_V1),
        "denial_labels": tuple(DENIAL_LABELS_V1),
        "gate_status_fields": dict(REQUIRED_GATE_STATUSES_V1),
        "validation_status_fields": validation_status_fields,
        "blocked": False,
        "blocked_result_behavior": "safe_blocked_template_available_if_validation_fails",
        "blocked_reasons": (),
        "visible_risks": (*VISIBLE_RISKS_V1, "result-artifact-as-final-answer"),
        "followups": FOLLOWUPS_V1,
        "abort_conditions_checked": (
            "exact_result_artifact_path_confirmed",
            "synthetic_metadata_only_confirmed",
            "prompt_execution_not_requested",
            "live_dialogue_not_requested",
            "provider_calls_not_requested",
            "runtime_wiring_not_requested",
            "dot_weslr_write_not_requested",
            "feature_flag_enablement_not_requested",
            "judge_scoring_not_requested",
            "official_claim_not_requested",
            "raw_content_absent",
        ),
        "next_lane": NEXT_LANE_V1,
        "safety_confirmation_labels": SAFETY_CONFIRMATION_LABELS_V1,
    }


def render_controlled_answer_composition_dry_run_execution_result_markdown_v1(result: Mapping[str, Any]) -> str:
    """Render safe Markdown for the execution result metadata."""

    if result.get("artifact_type") != "controlled_answer_composition_dry_run_execution_result_v1":
        raise ValueError("controlled_answer_composition_dry_run_execution_result_invalid")
    if result.get("result_artifact_path") != RESULT_ARTIFACT_PATH_V1:
        raise ValueError("controlled_answer_composition_dry_run_result_path_invalid")
    false_fields = result.get("required_false_no_authority_fields")
    denied_fields = result.get("denied_authority_fields")
    validation_fields = result.get("validation_status_fields")
    if not isinstance(false_fields, Mapping) or any(value is not False for value in false_fields.values()):
        raise ValueError("controlled_answer_composition_dry_run_false_fields_invalid")
    if not isinstance(denied_fields, Mapping) or any(value != "denied" for value in denied_fields.values()):
        raise ValueError("controlled_answer_composition_dry_run_denied_fields_invalid")
    if not isinstance(validation_fields, Mapping):
        raise ValueError("controlled_answer_composition_dry_run_validation_fields_invalid")

    lines = [
        "# WESLR Controlled Answer Composition Dry Run Result Artifact V1",
        "",
        "Layer: `WESLR_CANON_ALIGNMENT / synthetic-metadata-only-result`",
        "",
        "Status label: `controlled_answer_composition_dry_run_execution_result_created`",
        "",
        "Implementation status: `synthetic_metadata_only_internal_result_artifact`",
        "",
        f"Result artifact path: `{RESULT_ARTIFACT_PATH_V1}`",
        "",
        f"Next lane: `{NEXT_LANE_V1}`",
        "",
        "This artifact records one controlled dry-run helper execution using synthetic metadata only. It is not answer composition, not final-answer generation, not runtime wiring, not prompt execution, not live dialogue, not provider/model/search/advisor output, not `.weslr` persistence, not feature-flag activation, not judging/scoring, not an official claim, not answer authority, and not composition authority.",
        "",
        "OCC/OpenClaw is construction and execution tooling only. OCC/OpenClaw is not deployed WESLR and is not WESLR.",
        "",
        "---",
        "",
        "## Execution Summary",
        "",
        f"- artifact_type: `{result['artifact_type']}`",
        f"- schema_version: `{result['schema_version']}`",
        f"- metadata_only: `{result['metadata_only']}`",
        f"- internal_only: `{result['internal_only']}`",
        f"- synthetic_only: `{result['synthetic_only']}`",
        f"- non_runtime: `{result['non_runtime']}`",
        f"- non_user_facing: `{result['non_user_facing']}`",
        f"- qualitative_only: `{result['qualitative_only']}`",
        f"- dry_run_execution_label: `{result['dry_run_execution_label']}`",
        f"- dry_run_input_profile_label: `{result['dry_run_input_profile_label']}`",
        f"- helper_json_safe_metadata_preserved: `{result['helper_json_safe_metadata_preserved']}`",
        f"- helper_safe_markdown_rendered: `{result['helper_safe_markdown_rendered']}`",
        "- validation_pass_meaning: `metadata_quality_evidence_only`",
        "",
        "## Required False / No-Authority Fields",
        "",
    ]
    for key in FALSE_CONFIRMATION_FIELDS_V1:
        lines.append(f"- `{key}=false`")

    lines.extend(["", "## Denied Authority Fields", ""])
    for key in sorted(denied_fields):
        lines.append(f"- `{key}: {denied_fields[key]}`")

    lines.extend(["", "## Denial Labels", ""])
    for label in result.get("denial_labels", ()):  # safe labels only
        lines.append(f"- `{label}`")

    lines.extend(["", "## Gate Status Fields", ""])
    gate_statuses = result.get("gate_status_fields", {})
    for key in sorted(gate_statuses):
        lines.append(f"- `{key}: {gate_statuses[key]}`")

    lines.extend(["", "## Validation Status Fields", ""])
    for key in sorted(validation_fields):
        lines.append(f"- `{key}: {validation_fields[key]}`")

    lines.extend(["", "## Blocked Result Behavior", ""])
    lines.append(f"- blocked: `{result['blocked']}`")
    lines.append(f"- blocked_result_behavior: `{result['blocked_result_behavior']}`")
    lines.append("- blocked_reasons: `none`")

    lines.extend(["", "## Visible Risks", ""])
    for risk in result.get("visible_risks", ()):  # safe labels only
        lines.append(f"- `{risk}`")

    lines.extend(["", "## Followups", ""])
    for followup in result.get("followups", ()):  # safe labels only
        lines.append(f"- `{followup}`")

    lines.extend(["", "## Abort Conditions Checked", ""])
    for condition in result.get("abort_conditions_checked", ()):  # safe labels only
        lines.append(f"- `{condition}`")

    lines.extend(["", "## Safety Confirmation", ""])
    for label in result.get("safety_confirmation_labels", ()):  # safe labels only
        lines.append(f"- `{label}`")

    lines.extend(
        [
            "- `validation_pass_metadata_quality_evidence_only`",
            "- `result_artifact_not_answer_text`",
            "- `metadata_result_not_composition_authority`",
            "- `answer_authority_granted=false`",
            "- `composition_authority_granted=false`",
            "- `runtime_authority_granted=false`",
            f"- next_lane: `{NEXT_LANE_V1}`",
        ]
    )
    return "\n".join(lines) + "\n"


def build_controlled_answer_composition_dry_run_result_markdown_v1() -> str:
    """Build the complete safe Markdown result artifact."""

    result = execute_controlled_answer_composition_dry_run_v1()
    return render_controlled_answer_composition_dry_run_execution_result_markdown_v1(result)


def write_controlled_answer_composition_dry_run_result_artifact_v1(
    *,
    repository_root: str | Path = ".",
    overwrite: bool = False,
) -> Path:
    """Write exactly the approved result artifact path under repository_root."""

    root = Path(repository_root)
    target = root / RESULT_ARTIFACT_PATH_V1
    if target.as_posix().endswith(RESULT_ARTIFACT_PATH_V1) is not True:
        raise ValueError("controlled_answer_composition_dry_run_result_path_invalid")
    if target.exists() and not overwrite:
        raise FileExistsError(RESULT_ARTIFACT_PATH_V1)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_controlled_answer_composition_dry_run_result_markdown_v1(), encoding="utf-8")
    return target


if __name__ == "__main__":
    write_controlled_answer_composition_dry_run_result_artifact_v1()
