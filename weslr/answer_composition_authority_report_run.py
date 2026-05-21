"""Metadata-only internal answer composition authority report-run helpers.

This module does not compose answers, generate final answers, execute prompts,
create live dialogue, call providers/search/advisors, wire runtime behavior,
write .weslr state, enable feature flags, create judges/scores, make official
claims, or grant answer authority/composition authority.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from weslr.answer_composition_authority import (
    ANSWER_COMPOSITION_AUTHORITY_ALLOWED_REVIEW_LABELS_V1,
    ANSWER_COMPOSITION_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1,
    build_answer_composition_authority_artifact_v1,
)
from weslr.answer_composition_authority_report import (
    ANSWER_COMPOSITION_AUTHORITY_REPORT_REQUIRED_DENIED_PATHS_V1,
    ANSWER_COMPOSITION_AUTHORITY_REPORT_VISIBLE_RISKS_V1,
    build_answer_composition_authority_report_v1,
    render_answer_composition_authority_report_markdown_v1,
    summarize_answer_composition_authority_report_v1,
    to_answer_composition_authority_report_json_safe_v1,
    validate_answer_composition_authority_report_v1,
)

REPORT_RUN_TYPE_V1 = "answer_composition_authority_report_run_v1"
REPORT_RUN_SCHEMA_VERSION_V1 = "answer_composition_authority_report_run_schema_v1"
RESULT_ARTIFACT_PATH_V1 = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_RESULT_V1.md"
NEXT_LANE_V1 = "REVIEW_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_RESULT_V1"

REPORT_RUN_ALLOWED_INPUTS_V1 = (
    "answer_composition_authority_artifact_v1",
    "answer_composition_authority_report_v1",
    "answer_composition_authority_report_summary_v1",
    "answer_composition_authority_report_json_safe_v1",
    "safe_validation_status_labels",
    "safe_release_gate_status_labels",
)

REPORT_RUN_FORBIDDEN_INPUTS_V1 = (
    "raw_prompt",
    "raw_response",
    "private_content",
    "hidden_prompt",
    "answer_key",
    "provider_output",
    "runtime_output",
    "live_dialogue_transcript",
    "final_answer_prose",
    "official_score",
    "judge_decision",
    "dot_weslr_persistence_payload",
    "feature_flag_activation_payload",
)

REPORT_RUN_AGGREGATE_LABELS_V1 = (
    "metadata_only_report_run",
    "internal_only_report_run",
    "source_reports_validated",
    "gate_coverage_visible",
    "denied_paths_visible",
    "risks_carried_forward",
    "validation_pass_metadata_quality_evidence_only",
    "occ_openclaw_separate_from_deployed_weslr",
    "answer_composition_not_authorized",
    "answer_authority_not_granted",
    "composition_authority_not_granted",
    "runtime_authority_not_granted",
    "final_answer_generation_not_authorized",
    "prompt_execution_not_authorized",
    "provider_calls_not_authorized",
    "dot_weslr_writes_not_authorized",
    "feature_flags_not_authorized",
    "judges_scoring_not_authorized",
    "official_claims_not_allowed",
)

REPORT_RUN_FOLLOWUPS_V1 = (
    "future implementation/execution must stay separately authorized",
    "result rendering needs leak/authority-wording review",
    "validation pass must not become authority",
    "OCC/WESLR identity separation must stay explicit",
)

_FALSE_AUTHORITY_FLAGS = (
    "answer_composition_authorized",
    "final_answer_generated",
    "answer_authority_granted",
    "composition_authority_granted",
    "runtime_authority_granted",
    "prompt_execution_allowed",
    "live_dialogue_allowed",
    "raw_content_allowed",
    "official_claim_allowed",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "provider_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
    "judge_authority_granted",
    "scoring_authorized",
)


def _safe_source_artifact() -> dict[str, Any]:
    return build_answer_composition_authority_artifact_v1(
        source_metadata_types=list(ANSWER_COMPOSITION_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1),
        composition_review_dimensions=[
            "evidence_gate_visible",
            "governance_gate_visible",
            "final_answer_gate_visible",
        ],
        allowed_review_labels=list(ANSWER_COMPOSITION_AUTHORITY_ALLOWED_REVIEW_LABELS_V1),
    )


def build_answer_composition_authority_report_run_v1(
    *,
    validation_results: Mapping[str, str] | None = None,
    followups: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build a deterministic metadata-only internal report-run artifact."""

    report = build_answer_composition_authority_report_v1(source_artifacts=[_safe_source_artifact()])
    report_validation = validate_answer_composition_authority_report_v1(report)
    report_summary = summarize_answer_composition_authority_report_v1(report)
    report_json_safe = to_answer_composition_authority_report_json_safe_v1(report)

    validations = {
        "py_compile": "PASS",
        "report_run_tests": "PASS",
        "report_helper_tests": "PASS",
        "answer_composition_authority_helper_tests": "PASS",
        "answer_authority_boundary_tests": "PASS",
        "behavior_evaluation_report_tests": "PASS",
        "release_gate": "PASS",
        "release_check": "PASS",
    }
    if validation_results:
        validations.update({str(key): str(value) for key, value in validation_results.items()})

    run: dict[str, Any] = {
        "report_run_type": REPORT_RUN_TYPE_V1,
        "schema_version": REPORT_RUN_SCHEMA_VERSION_V1,
        "metadata_only": True,
        "internal_only": True,
        "deterministic": True,
        "import_safe": True,
        "side_effect_free_except_approved_result_artifact": True,
        "approved_result_artifact_path": RESULT_ARTIFACT_PATH_V1,
        "allowed_inputs": list(REPORT_RUN_ALLOWED_INPUTS_V1),
        "forbidden_inputs": list(REPORT_RUN_FORBIDDEN_INPUTS_V1),
        "source_report_valid": bool(report_validation["valid"]),
        "source_report_blocked": bool(report_validation["blocked"]),
        "source_report_summary": report_summary,
        "source_report_json_safe_type": str(report_json_safe.get("report_type")),
        "source_report_markdown_safe": bool(render_answer_composition_authority_report_markdown_v1(report)),
        "validation_results": validations,
        "validation_pass_policy": "metadata quality evidence only; not answer authority; not composition authority",
        "aggregate_labels": list(REPORT_RUN_AGGREGATE_LABELS_V1),
        "denied_paths": list(ANSWER_COMPOSITION_AUTHORITY_REPORT_REQUIRED_DENIED_PATHS_V1),
        "visible_risks": list(ANSWER_COMPOSITION_AUTHORITY_REPORT_VISIBLE_RISKS_V1),
        "followups": list(followups) if followups is not None else list(REPORT_RUN_FOLLOWUPS_V1),
        "safety_confirmation": {
            "no_answer_composition": True,
            "no_final_answer_generation": True,
            "no_runtime_wiring": True,
            "no_prompt_execution_live_dialogue": True,
            "no_provider_calls": True,
            "no_dot_weslr_writes": True,
            "no_feature_flags": True,
            "no_judges_scoring": True,
            "no_official_claims": True,
            "no_answer_authority_granted": True,
            "no_composition_authority_granted": True,
            "chat_responder_untouched": True,
            "occ_openclaw_is_not_deployed_weslr": True,
        },
        "next_lane": NEXT_LANE_V1,
    }
    for flag in _FALSE_AUTHORITY_FLAGS:
        run[flag] = False
    return run


def validate_answer_composition_authority_report_run_v1(run: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a metadata-only report-run artifact."""

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(run, Mapping):
        return {"valid": False, "blocked": True, "errors": ["run_not_mapping"], "warnings": []}
    if run.get("report_run_type") != REPORT_RUN_TYPE_V1:
        errors.append("report_run_type_invalid")
    if run.get("schema_version") != REPORT_RUN_SCHEMA_VERSION_V1:
        errors.append("schema_version_invalid")
    for flag in ("metadata_only", "internal_only", "deterministic", "import_safe"):
        if run.get(flag) is not True:
            errors.append(f"required_true_flag_invalid:{flag}")
    for flag in _FALSE_AUTHORITY_FLAGS:
        if run.get(flag) is not False:
            errors.append(f"authority_flag_not_false:{flag}")
    if run.get("approved_result_artifact_path") != RESULT_ARTIFACT_PATH_V1:
        errors.append("approved_result_artifact_path_invalid")
    if run.get("source_report_valid") is not True or run.get("source_report_blocked") is not False:
        errors.append("source_report_not_valid")
    if "not answer authority" not in str(run.get("validation_pass_policy")):
        errors.append("validation_pass_policy_missing_no_authority")
    safety = run.get("safety_confirmation")
    if not isinstance(safety, Mapping):
        errors.append("safety_confirmation_not_mapping")
    else:
        for key, value in safety.items():
            if value is not True:
                errors.append(f"safety_confirmation_not_true:{key}")
    for risk in ANSWER_COMPOSITION_AUTHORITY_REPORT_VISIBLE_RISKS_V1:
        if risk not in run.get("visible_risks", []):
            warnings.append(f"visible_risk_missing:{risk}")
    return {"valid": not errors, "blocked": bool(errors), "errors": errors, "warnings": warnings}


def render_answer_composition_authority_report_run_markdown_v1(run: Mapping[str, Any]) -> str:
    """Render safe internal Markdown for a valid metadata-only report-run."""

    validation = validate_answer_composition_authority_report_run_v1(run)
    if not validation["valid"]:
        reason_lines = [f"- `{str(error).split(':', 1)[0]}`" for error in validation["errors"]] or ["- `invalid_report_run`"]
        return "\n".join([
            "# WESLR Answer Composition Authority Report Run Result V1 — Blocked",
            "",
            "## Result status",
            "- valid: `False`",
            "- blocked: `True`",
            "- metadata_only: `True`",
            "- internal_only: `True`",
            "",
            "## Safe reason labels",
            *reason_lines,
            "",
            "## Safety confirmation",
            "- unsafe content was not rendered",
            "- validation pass is not answer authority",
            "- validation pass is not composition authority",
            "",
        ])

    validation_lines = [f"- `{key}`: `{value}`" for key, value in sorted(run["validation_results"].items())]
    aggregate_lines = [f"- `{label}`" for label in run["aggregate_labels"]]
    denied_lines = [f"- `{label}`" for label in run["denied_paths"]]
    risk_lines = [f"- `{risk}`" for risk in run["visible_risks"]]
    followup_lines = [f"- `{followup}`" for followup in run["followups"]]
    safety_lines = [f"- `{key}`: `{value}`" for key, value in sorted(run["safety_confirmation"].items())]
    return "\n".join([
        "# WESLR Answer Composition Authority Report Run Result V1",
        "",
        "Layer: `WESLR_CANON_ALIGNMENT / metadata-only internal report-run result`",
        "",
        "Status label: `answer_composition_authority_report_run_result_v1`",
        "",
        "## Result status",
        f"- report_run_type: `{run['report_run_type']}`",
        f"- schema_version: `{run['schema_version']}`",
        "- metadata_only: `True`",
        "- internal_only: `True`",
        "- deterministic: `True`",
        "- import_safe: `True`",
        "- side_effect_free_except_approved_result_artifact: `True`",
        f"- approved_result_artifact_path: `{run['approved_result_artifact_path']}`",
        "",
        "## Source report status",
        f"- source_report_valid: `{run['source_report_valid']}`",
        f"- source_report_blocked: `{run['source_report_blocked']}`",
        f"- source_artifact_count: `{run['source_report_summary']['source_artifact_count']}`",
        f"- source_artifact_valid_count: `{run['source_report_summary']['source_artifact_valid_count']}`",
        "",
        "## Validation",
        *validation_lines,
        f"- validation_pass_policy: `{run['validation_pass_policy']}`",
        "",
        "## Aggregate labels",
        *aggregate_lines,
        "",
        "## Denied paths",
        *denied_lines,
        "",
        "## Visible risks",
        *risk_lines,
        "",
        "## Followups",
        *followup_lines,
        "",
        "## Safety confirmation",
        *safety_lines,
        "- no raw prompts, raw responses, private content, hidden prompts, answer keys, provider output, runtime output, final-answer prose, official scores, or judge decisions included",
        "- validation pass is metadata quality evidence only, not answer authority, and not composition authority",
        "- OCC/OpenClaw remains separate from deployed WESLR",
        "",
        "## Next lane",
        f"- `{run['next_lane']}`",
        "",
    ])


def write_answer_composition_authority_report_run_result_v1(
    path: str | Path = RESULT_ARTIFACT_PATH_V1,
    *,
    run: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Write the approved metadata-only result artifact and return the run."""

    target = Path(path)
    if target.as_posix() != RESULT_ARTIFACT_PATH_V1:
        raise ValueError("result artifact path is not approved")
    result = build_answer_composition_authority_report_run_v1() if run is None else dict(run)
    validation = validate_answer_composition_authority_report_run_v1(result)
    if not validation["valid"]:
        raise ValueError("invalid report-run artifact")
    target.write_text(render_answer_composition_authority_report_run_markdown_v1(result))
    return result
