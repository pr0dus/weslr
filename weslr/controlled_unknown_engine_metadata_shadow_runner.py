"""Controlled UNKNOWN ENGINE metadata shadow runner helpers V1.

This module is deliberately metadata-only.  It creates and validates synthetic or
explicitly approved internal metadata fixtures, then builds internal shadow
reports about UNKNOWN ENGINE helper shape/boundary behavior.

It does not read or write files, touch .weslr, call providers/search/advisors,
run theorem provers, wire runtime/chat/browser behavior, score/judge, claim
proof/capability, or produce final/user-facing output.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

SCHEMA_VERSION = "weslr.controlled_unknown_engine_metadata_shadow_runner.v1"
RUNNER_MODE = "controlled_metadata_shadow_runner_v1"

ALLOWED_FIXTURE_KINDS = frozenset(
    {
        "synthetic_unknown_engine_fixture",
        "synthetic_cognitive_gym_metadata",
        "synthetic_tier_0_2_math_readiness_card",
        "synthetic_candidate_invariant_metadata",
        "synthetic_failed_path_metadata",
        "explicitly_approved_safe_internal_metadata",
    }
)

FORBIDDEN_FIXTURE_MARKERS = frozenset(
    {
        "raw_private_material",
        "live_erdos_solving_prompt",
        "live_millennium_solving_prompt",
        "theorem_prover_task",
        "provider_output",
        "model_output",
        "search_output",
        "advisor_output",
        "hidden_prompt",
        "protected_material",
        "dot_weslr_state",
        "runtime_chat_transcript",
        "unscoped_memory",
        "unscoped_context",
        "unscoped_evidence",
        "unscoped_artifact",
        "final_answer_text",
        "proof_or_solution_claim",
    }
)

UNSAFE_TEXT_MARKERS = frozenset(
    {
        "raw_private_material",
        "private material",
        "live erdos solving prompt",
        "live erdős solving prompt",
        "live millennium solving prompt",
        "theorem prover task",
        "provider output",
        "model output",
        "search output",
        "advisor output",
        "hidden prompt",
        "protected material",
        ".weslr",
        "dot_weslr_state",
        "runtime chat transcript",
        "unscoped memory",
        "unscoped context",
        "unscoped evidence",
        "unscoped artifact",
        "final answer:",
        "final_answer_text",
        "proof_or_solution_claim",
        "i have proved",
        "we have proved",
        "solution claim",
        "external validation granted",
        "official benchmark",
        "turing certification",
        "intelligence certification",
        "prize claim",
        "public release claim",
    }
)

DENIED_AUTHORITY_FIELDS = (
    "grants_runtime_authority",
    "permits_public_browser_runtime",
    "permits_provider_calls",
    "permits_dot_weslr_public_state",
    "permits_final_answer_generation",
    "permits_theorem_solver_execution",
    "permits_scoring_or_judging",
    "permits_official_claims",
    "permits_solution_or_proof_claims",
    "permits_external_validation_claim",
    "permits_chat_wiring",
    "permits_real_problem_solving",
)

NO_RUN_AUTHORITY_FLAGS = (
    "is_engine_execution",
    "is_live_problem_solving",
    "is_theorem_prover_run",
    "is_proof_validation",
    "is_external_validation",
    "is_scoring_or_judging",
    "is_official_benchmark",
    "is_final_answer",
    "is_user_facing_output",
    "is_runtime_wiring",
    "uses_provider_model_search_or_advisor",
    "uses_dot_weslr",
)

REPORT_FIELDS = (
    "schema_version",
    "run_id",
    "runner_mode",
    "input_fixture_summary",
    "engine_helper_paths_observed",
    "result_artifact_shape",
    "produced_metadata_kinds",
    "blocked_claims",
    "denied_authority",
    "validation_status",
    "observed_gaps",
    "next_safe_steps",
    "no_run_authority_flags",
    "expert_lane_handling",
    "safety_boundary_labels",
)

SAFE_NEXT_STEPS = (
    "review_controlled_unknown_engine_metadata_shadow_runner_implementation_v1",
    "analyze_internal_shadow_report_metadata_only",
    "add_synthetic_negative_fixture_coverage",
)

BLOCKED_CLAIMS = (
    "proof",
    "solution",
    "open_problem",
    "score",
    "judge",
    "official",
    "public",
    "prize",
    "product_readiness",
    "intelligence",
    "turing",
    "certification",
    "external_validation",
    "final_answer",
    "provider",
    "search",
    "model",
    "advisor",
    "runtime",
    "dot_weslr",
)

HELPER_PATHS_OBSERVED = (
    "weslr/unknown_engine.py",
    "weslr/unknown_engine_result_artifact.py",
)

RESULT_ARTIFACT_SHAPE = {
    "artifact_kind": "unknown_engine_result_artifact_metadata_shape_only",
    "contains_raw_private_content": False,
    "contains_proof_text": False,
    "contains_final_answer_text": False,
    "contains_user_facing_output": False,
    "fields_observed": (
        "run_metadata",
        "validation_summary",
        "blocked_claim_summary",
        "denied_authority_summary",
        "safe_next_steps",
    ),
}

SAFETY_BOUNDARY_LABELS = (
    "metadata_only",
    "synthetic_or_explicitly_approved_internal_metadata_only",
    "no_run_authority",
    "no_runtime_chat_browser",
    "no_provider_search_model_advisor",
    "no_dot_weslr_io",
    "no_solver_or_prover_execution",
    "no_scoring_or_judging",
    "no_proof_solution_or_capability_claims",
    "no_final_or_user_facing_output",
)


def _false_map(keys: tuple[str, ...]) -> dict[str, bool]:
    return {key: False for key in keys}


def _is_json_safe(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list) or isinstance(value, tuple):
        return all(_is_json_safe(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_json_safe(val) for key, val in value.items())
    return False


def _collect_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for key, val in value.items():
            strings.append(str(key))
            strings.extend(_collect_strings(val))
        return strings
    if isinstance(value, (list, tuple, set)):
        strings = []
        for item in value:
            strings.extend(_collect_strings(item))
        return strings
    return []


def _unsafe_text_hits(value: Any) -> list[str]:
    haystack = "\n".join(_collect_strings(value)).lower()
    return sorted(marker for marker in UNSAFE_TEXT_MARKERS if marker in haystack)


def _normalize_markers(markers: Any) -> tuple[str, ...]:
    if markers is None:
        return ()
    if isinstance(markers, str):
        return (markers,)
    if isinstance(markers, (list, tuple, set)):
        return tuple(str(marker) for marker in markers)
    return (str(markers),)


def _safe_metadata_key_summary(metadata: Any) -> tuple[str, ...]:
    if not isinstance(metadata, dict):
        return ()
    return tuple(sorted(str(key) for key in metadata.keys()))


def build_controlled_unknown_engine_shadow_fixture_v1(
    *,
    fixture_kind: str,
    run_id: str = "controlled_unknown_engine_shadow_fixture_v1",
    metadata: dict[str, Any] | None = None,
    markers: list[str] | tuple[str, ...] | None = None,
    synthetic: bool = True,
    explicitly_approved: bool = False,
    source_scoped: bool = True,
    expert_style_output: bool = False,
    expert_label: str | None = None,
    treats_expert_as_external_validation: bool = False,
) -> dict[str, Any]:
    """Build a JSON-safe fixture dictionary without side effects."""

    return {
        "schema_version": SCHEMA_VERSION,
        "fixture_kind": fixture_kind,
        "run_id": run_id,
        "metadata": deepcopy(metadata or {}),
        "markers": list(_normalize_markers(markers)),
        "synthetic": bool(synthetic),
        "explicitly_approved": bool(explicitly_approved),
        "source_scoped": bool(source_scoped),
        "expert_style_output": bool(expert_style_output),
        "expert_label": expert_label,
        "treats_expert_as_external_validation": bool(treats_expert_as_external_validation),
    }


def validate_controlled_unknown_engine_shadow_fixture_v1(fixture: Any) -> dict[str, Any]:
    """Validate a fixture and fail closed for unknown, unsafe, or non-JSON metadata."""

    errors: list[str] = []
    blocked_markers: list[str] = []

    if not isinstance(fixture, dict):
        return {
            "valid": False,
            "validation_status": "blocked",
            "errors": ["fixture_missing_or_not_dict"],
            "blocked_markers": [],
        }

    fixture_kind = fixture.get("fixture_kind")
    if fixture_kind not in ALLOWED_FIXTURE_KINDS:
        errors.append("unknown_fixture_kind")

    if fixture_kind == "explicitly_approved_safe_internal_metadata":
        if fixture.get("explicitly_approved") is not True:
            errors.append("explicit_internal_metadata_not_approved")
        if fixture.get("source_scoped") is not True:
            errors.append("explicit_internal_metadata_not_source_scoped")
    elif fixture.get("synthetic") is not True:
        errors.append("non_synthetic_fixture_without_explicit_approval")

    markers = set(_normalize_markers(fixture.get("markers")))
    blocked_markers = sorted(markers.intersection(FORBIDDEN_FIXTURE_MARKERS))
    if blocked_markers:
        errors.append("forbidden_fixture_markers_present")

    unsafe_text_hits = _unsafe_text_hits(fixture)
    if unsafe_text_hits:
        errors.append("unsafe_text_markers_present")

    if not _is_json_safe(fixture):
        errors.append("fixture_not_json_safe")

    if fixture.get("expert_style_output") is True:
        if fixture.get("expert_label") not in (None, "internal_expert_simulation"):
            errors.append("expert_style_output_not_labeled_internal_simulation")
        if fixture.get("treats_expert_as_external_validation") is True:
            errors.append("expert_style_output_treated_as_external_validation")

    denied_authority = fixture.get("denied_authority")
    if denied_authority is not None:
        authority_errors = _validate_false_authority_map(denied_authority, DENIED_AUTHORITY_FIELDS)
        if authority_errors:
            errors.extend(f"fixture_{error}" for error in authority_errors)

    return {
        "valid": not errors,
        "validation_status": "valid_fixture" if not errors else "blocked",
        "errors": errors,
        "blocked_markers": blocked_markers,
        "unsafe_text_markers": unsafe_text_hits,
    }


def _validate_false_authority_map(authority: Any, fields: tuple[str, ...]) -> list[str]:
    if not isinstance(authority, dict):
        return ["authority_map_missing_or_not_dict"]
    errors: list[str] = []
    for field in fields:
        if field not in authority:
            errors.append(f"authority_field_missing:{field}")
        elif authority[field] is not False:
            errors.append(f"authority_field_not_false:{field}")
    return errors


def _blocked_report(fixture: Any, fixture_validation: dict[str, Any]) -> dict[str, Any]:
    run_id = fixture.get("run_id") if isinstance(fixture, dict) else "blocked_missing_fixture"
    report = _base_report(run_id=str(run_id or "blocked_missing_fixture"), fixture=fixture)
    report["validation_status"] = "blocked"
    report["observed_gaps"] = tuple(fixture_validation.get("errors", ()))
    report["produced_metadata_kinds"] = ("blocked_fixture_validation_summary",)
    report["input_fixture_summary"] = _fixture_summary(fixture, fixture_validation)
    return report


def _fixture_summary(fixture: Any, fixture_validation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fixture, dict):
        return {
            "fixture_present": False,
            "fixture_kind": None,
            "synthetic": False,
            "explicitly_approved": False,
            "source_scoped": False,
            "marker_count": 0,
            "safe_metadata_keys": (),
            "validation_status": fixture_validation.get("validation_status", "blocked"),
        }
    return {
        "fixture_present": True,
        "fixture_kind": fixture.get("fixture_kind"),
        "synthetic": bool(fixture.get("synthetic")),
        "explicitly_approved": bool(fixture.get("explicitly_approved")),
        "source_scoped": bool(fixture.get("source_scoped")),
        "marker_count": len(_normalize_markers(fixture.get("markers"))),
        "safe_metadata_keys": _safe_metadata_key_summary(fixture.get("metadata")),
        "validation_status": fixture_validation.get("validation_status", "blocked"),
        "blocked_marker_count": len(fixture_validation.get("blocked_markers", ())),
    }


def _expert_lane_handling(fixture: Any) -> dict[str, Any]:
    expert_present = bool(isinstance(fixture, dict) and fixture.get("expert_style_output"))
    return {
        "expert_style_output_present": expert_present,
        "label": "internal_expert_simulation" if expert_present else "not_present",
        "is_external_validation": False,
        "expert_output_analysis_or_adjudication_required": expert_present,
        "public_proof_prize_solution_claims_blocked": True,
    }


def _base_report(run_id: str, fixture: Any) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "runner_mode": RUNNER_MODE,
        "input_fixture_summary": {},
        "engine_helper_paths_observed": HELPER_PATHS_OBSERVED,
        "result_artifact_shape": deepcopy(RESULT_ARTIFACT_SHAPE),
        "produced_metadata_kinds": (
            "unknown_engine_run_metadata_shape",
            "unknown_engine_result_artifact_metadata_shape",
            "validation_summary",
            "blocked_claim_summary",
            "gap_summary",
        ),
        "blocked_claims": BLOCKED_CLAIMS,
        "denied_authority": _false_map(DENIED_AUTHORITY_FIELDS),
        "validation_status": "valid_metadata_shadow_report",
        "observed_gaps": (),
        "next_safe_steps": SAFE_NEXT_STEPS,
        "no_run_authority_flags": _false_map(NO_RUN_AUTHORITY_FLAGS),
        "expert_lane_handling": _expert_lane_handling(fixture),
        "safety_boundary_labels": SAFETY_BOUNDARY_LABELS,
    }


def run_controlled_unknown_engine_metadata_shadow_v1(fixture: Any) -> dict[str, Any]:
    """Build a metadata-only internal shadow report from a safe fixture."""

    fixture_validation = validate_controlled_unknown_engine_shadow_fixture_v1(fixture)
    if not fixture_validation["valid"]:
        return _blocked_report(fixture, fixture_validation)

    run_id = str(fixture.get("run_id") or "controlled_unknown_engine_shadow_run_v1")
    report = _base_report(run_id=run_id, fixture=fixture)
    report["input_fixture_summary"] = _fixture_summary(fixture, fixture_validation)
    report_validation = validate_controlled_unknown_engine_shadow_report_v1(report)
    if not report_validation["valid"]:
        report["validation_status"] = "invalid_metadata_shadow_report"
        report["observed_gaps"] = tuple(report_validation["errors"])
    return report


def validate_controlled_unknown_engine_shadow_report_v1(report: Any) -> dict[str, Any]:
    """Validate report shape, authority denial, JSON safety, and no-run boundaries."""

    errors: list[str] = []
    if not isinstance(report, dict):
        return {"valid": False, "validation_status": "invalid_metadata_shadow_report", "errors": ["report_missing_or_not_dict"]}

    for field in REPORT_FIELDS:
        if field not in report:
            errors.append(f"report_field_missing:{field}")

    if report.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_invalid")
    if report.get("runner_mode") != RUNNER_MODE:
        errors.append("runner_mode_invalid")

    errors.extend(_validate_false_authority_map(report.get("denied_authority"), DENIED_AUTHORITY_FIELDS))
    errors.extend(_validate_false_authority_map(report.get("no_run_authority_flags"), NO_RUN_AUTHORITY_FLAGS))

    if report.get("validation_status") not in {"blocked", "valid_metadata_shadow_report", "valid_with_gaps", "invalid_metadata_shadow_report"}:
        errors.append("validation_status_invalid")

    if not _is_json_safe(report):
        errors.append("report_not_json_safe")

    unsafe_hits = _unsafe_text_hits(report)
    # The report must name blocked categories but must not contain prose that asserts unsafe content.
    allowed_mentions = {
        "provider output",
        "model output",
        "search output",
        "advisor output",
        ".weslr",
        "final_answer_text",
        "proof_or_solution_claim",
    }
    disallowed_hits = [hit for hit in unsafe_hits if hit not in allowed_mentions]
    if disallowed_hits:
        errors.append("report_contains_unsafe_text_marker")

    expert = report.get("expert_lane_handling")
    if isinstance(expert, dict) and expert.get("expert_style_output_present"):
        if expert.get("label") != "internal_expert_simulation":
            errors.append("expert_style_output_not_labeled_internal_simulation")
        if expert.get("is_external_validation") is not False:
            errors.append("expert_style_output_treated_as_external_validation")
        if expert.get("expert_output_analysis_or_adjudication_required") is not True:
            errors.append("expert_adjudication_not_required")

    next_steps = report.get("next_safe_steps", ())
    blocked_next_step_hits = _unsafe_next_step_hits(next_steps)
    if blocked_next_step_hits:
        errors.append("next_step_proposes_forbidden_execution")

    return {
        "valid": not errors,
        "validation_status": "valid_metadata_shadow_report" if not errors else "invalid_metadata_shadow_report",
        "errors": errors,
    }


def _unsafe_next_step_hits(next_steps: Any) -> tuple[str, ...]:
    text = "\n".join(_collect_strings(next_steps)).lower()
    blocked = (
        "runtime",
        "chat",
        "provider",
        "search",
        "model",
        "advisor",
        ".weslr",
        "theorem",
        "solver",
        "final answer",
        "user-facing",
    )
    return tuple(hit for hit in blocked if hit in text)


def summarize_controlled_unknown_engine_shadow_report_v1(report: Any) -> dict[str, Any]:
    """Return counts/status only; never raw proof/final-answer/user-facing text."""

    validation = validate_controlled_unknown_engine_shadow_report_v1(report)
    if not isinstance(report, dict):
        return {
            "schema_version": SCHEMA_VERSION,
            "valid": False,
            "validation_status": validation["validation_status"],
            "error_count": len(validation["errors"]),
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "valid": validation["valid"],
        "validation_status": report.get("validation_status"),
        "runner_mode": report.get("runner_mode"),
        "blocked_claim_count": len(report.get("blocked_claims", ())),
        "denied_authority_count": len(report.get("denied_authority", {})),
        "no_run_authority_flag_count": len(report.get("no_run_authority_flags", {})),
        "observed_gap_count": len(report.get("observed_gaps", ())),
        "next_safe_step_count": len(report.get("next_safe_steps", ())),
        "expert_style_output_present": bool(report.get("expert_lane_handling", {}).get("expert_style_output_present")),
        "error_count": len(validation["errors"]),
    }


def render_controlled_unknown_engine_shadow_report_markdown_v1(report: Any) -> str:
    """Render an internal-only metadata summary, not answer/proof/user-facing text."""

    summary = summarize_controlled_unknown_engine_shadow_report_v1(report)
    lines = [
        "# Internal Controlled UNKNOWN ENGINE Metadata Shadow Report V1",
        "",
        "- Render scope: internal metadata only",
        "- User-facing output: false",
        "- Final-answer generation: false",
        "- Proof or solution claim: false",
        f"- Schema: {summary.get('schema_version')}",
        f"- Runner mode: {summary.get('runner_mode')}",
        f"- Validation status: {summary.get('validation_status')}",
        f"- Valid: {summary.get('valid')}",
        f"- Blocked claim count: {summary.get('blocked_claim_count', 0)}",
        f"- Denied authority count: {summary.get('denied_authority_count', 0)}",
        f"- No-run authority flag count: {summary.get('no_run_authority_flag_count', 0)}",
        f"- Observed gap count: {summary.get('observed_gap_count', 0)}",
        f"- Next safe step count: {summary.get('next_safe_step_count', 0)}",
        f"- Expert simulation present: {summary.get('expert_style_output_present', False)}",
    ]
    return "\n".join(lines) + "\n"


def to_controlled_unknown_engine_shadow_report_json_safe_v1(report: Any) -> dict[str, Any]:
    """Return a deep-copied JSON-safe report or blocked invalid summary."""

    if not _is_json_safe(report):
        return {
            "schema_version": SCHEMA_VERSION,
            "validation_status": "invalid_metadata_shadow_report",
            "valid": False,
            "errors": ("report_not_json_safe",),
        }
    copied = deepcopy(report)
    validation = validate_controlled_unknown_engine_shadow_report_v1(copied)
    copied["report_validation"] = validation
    return copied
