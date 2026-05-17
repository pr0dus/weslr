"""Safe helpers for plan-helper flag-on observation reports V1.

These helpers build, validate, summarize, and render sanitized in-memory reports.
They do not call ChatResponder, models, advisors, search, or write files.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

REPORT_TYPE_V1 = "plan_helper_flag_on_observation_report_v1"
SCHEMA_VERSION_V1 = "1.0"
FEATURE_FLAG_V1 = "WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1"
TARGET_BRANCH_V1 = "chat_responder_plan_helper"
TARGET_FILE_V1 = "weslr/chat_responder.py"
OBSERVATION_SCOPE_V1 = "plan_helper_only"

ALLOWED_QUALITY_LABELS_V1 = {
    "useful_enough_disabled_default",
    "safe_but_thin",
    "needs_context_handling_refinement",
    "unsafe_or_too_broad",
    "not_observed",
}

ALLOWED_DECISIONS_V1 = {
    "KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY",
    "REFINE_FLAG_ON_BEHAVIOR",
    "DISABLE_OR_REVERT",
    "CONSIDER_DEFAULT_ENABLEMENT_READINESS_DESIGN",
}

FORBIDDEN_KEYS_V1 = {
    "raw_text",
    "normalized_text",
    "tokens",
    "raw_prompt",
    "safe_prompt",
    "response_text",
    "final_answer",
    "source_urls",
    "hidden_prompt",
    "answer_key",
    "protected_material",
}

FORBIDDEN_CLAIM_PHRASES_V1 = {
    "certified",
    "certification",
    "benchmark score",
    "turing test passed",
    "iq",
    "official evaluation",
    "conscious",
    "sentient",
    "soul",
    "alive",
}

SIDE_EFFECT_KEYS_V1 = (
    "model_calls",
    "advisor_calls",
    "web_search",
    "solver_execution",
    "answer_selection_arbitration",
    "memory_writes",
    "weslr_runtime_state_created",
    "raw_text_stored",
    "source_registry_writes",
    "truth_writes",
)


def _merge(defaults: Mapping[str, Any], override: Mapping[str, Any] | None) -> dict[str, Any]:
    merged = copy.deepcopy(dict(defaults))
    if override:
        merged.update(copy.deepcopy(dict(override)))
    return merged


def _flag_off_defaults() -> dict[str, Any]:
    return {
        "checked": False,
        "plan_metadata_absent": True,
        "existing_behavior_active": True,
    }


def _flag_on_defaults() -> dict[str, Any]:
    return {
        "checked": False,
        "approved_prompt_count": 0,
        "slice_metadata_present": False,
        "quality_shape_present": False,
        "invented_context_observed": False,
    }


def _non_plan_defaults() -> dict[str, Any]:
    return {
        "checked": False,
        "plan_metadata_on_non_plan": False,
        "protected_prompt_count": 0,
    }


def _side_effect_defaults() -> dict[str, Any]:
    return {key: False for key in SIDE_EFFECT_KEYS_V1}


def _fallback_defaults() -> dict[str, Any]:
    return {
        "fallback_available": True,
        "fallback_problem_observed": False,
    }


def _cleanup_defaults() -> dict[str, Any]:
    return {
        "feature_flag_unset_after": True,
        "tracked_diff_after": False,
        "runtime_artifacts_retained": False,
    }


def _quality_defaults(quality_label: str) -> dict[str, Any]:
    return {
        "quality_label": quality_label,
        "reaches_approved_slice": False,
        "asks_useful_clarifying_question": False,
        "includes_bounded_starter_shape": False,
        "invented_project_details": False,
        "old_canned_wording_observed": False,
        "high_stakes_drift": False,
    }


def build_plan_helper_observation_report_v1(
    *,
    repo_head: str,
    timestamp_local: str = "",
    flag_off_baseline: dict | None = None,
    flag_on_plan_checks: dict | None = None,
    non_plan_protection: dict | None = None,
    side_effects: dict | None = None,
    fallback: dict | None = None,
    cleanup: dict | None = None,
    decision: str = "KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY",
    quality_label: str = "not_observed",
) -> dict[str, Any]:
    """Build an in-memory JSON-safe report shape. Performs no persistence."""
    return {
        "report_type": REPORT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "timestamp_local": timestamp_local,
        "repo_head": repo_head,
        "feature_flag": FEATURE_FLAG_V1,
        "feature_flag_default": False,
        "flag_enabled_for_process_only": True,
        "target_branch": TARGET_BRANCH_V1,
        "target_file": TARGET_FILE_V1,
        "observation_scope": OBSERVATION_SCOPE_V1,
        "raw_private_text_included": False,
        "benchmark_claim": False,
        "turing_test_claim": False,
        "official_score_claim": False,
        "certification_claim": False,
        "default_enablement_claim": False,
        "branch_expansion_claim": False,
        "flag_off_baseline": _merge(_flag_off_defaults(), flag_off_baseline),
        "flag_on_plan_checks": _merge(_flag_on_defaults(), flag_on_plan_checks),
        "non_plan_protection": _merge(_non_plan_defaults(), non_plan_protection),
        "side_effects": _merge(_side_effect_defaults(), side_effects),
        "fallback": _merge(_fallback_defaults(), fallback),
        "cleanup": _merge(_cleanup_defaults(), cleanup),
        "quality": _quality_defaults(quality_label),
        "decision": decision,
        "safety": {
            "no_raw_private_text": True,
            "no_benchmark_claims": True,
            "no_turing_test_claims": True,
            "no_default_enablement": True,
            "no_branch_expansion": True,
            "no_persistence": True,
        },
    }


def to_plan_helper_observation_report_json_safe_v1(obj: Any) -> Any:
    """Return a deep JSON-safe copy. This is not a sanitizer."""
    value = copy.deepcopy(obj)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return to_plan_helper_observation_report_json_safe_v1(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): to_plan_helper_observation_report_json_safe_v1(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple, set)):
        return [to_plan_helper_observation_report_json_safe_v1(item) for item in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_plan_helper_observation_report_json_safe_v1(value.to_dict())
    if hasattr(value, "__dict__"):
        return to_plan_helper_observation_report_json_safe_v1(vars(value))
    return repr(value)


def _walk(value: Any, path: str = ""):
    yield path, value
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{path}.{key}" if path else str(key)
            yield from _walk(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")


def _bool_at(report: Mapping[str, Any], dotted: str, default: Any = None) -> Any:
    current: Any = report
    for part in dotted.split("."):
        if not isinstance(current, Mapping):
            return default
        current = current.get(part, default)
    return current


def validate_plan_helper_observation_report_v1(report: dict) -> dict[str, Any]:
    """Validate a plan-helper observation report without side effects."""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(report, Mapping):
        return {"valid": False, "errors": ["report must be a dict"], "warnings": []}

    exact_checks = {
        "report_type": REPORT_TYPE_V1,
        "feature_flag": FEATURE_FLAG_V1,
        "feature_flag_default": False,
        "flag_enabled_for_process_only": True,
        "target_branch": TARGET_BRANCH_V1,
        "target_file": TARGET_FILE_V1,
        "observation_scope": OBSERVATION_SCOPE_V1,
        "raw_private_text_included": False,
        "benchmark_claim": False,
        "turing_test_claim": False,
        "official_score_claim": False,
        "certification_claim": False,
        "default_enablement_claim": False,
        "branch_expansion_claim": False,
    }
    for key, expected in exact_checks.items():
        if report.get(key) != expected:
            errors.append(f"{key} must be {expected!r}")

    if not report.get("repo_head"):
        errors.append("repo_head is required")
    elif len(str(report.get("repo_head"))) < 8 or str(report.get("repo_head")).startswith("<"):
        warnings.append("repo_head looks short/placeholder")

    if not report.get("timestamp_local"):
        warnings.append("timestamp_local missing")

    decision = report.get("decision")
    if decision not in ALLOWED_DECISIONS_V1:
        errors.append("invalid decision")

    quality = report.get("quality", {})
    quality_label = quality.get("quality_label") if isinstance(quality, Mapping) else None
    if quality_label not in ALLOWED_QUALITY_LABELS_V1:
        errors.append("invalid quality label")

    for side_effect_key in SIDE_EFFECT_KEYS_V1:
        if _bool_at(report, f"side_effects.{side_effect_key}") is True:
            errors.append(f"side_effects.{side_effect_key} must be false")

    if _bool_at(report, "non_plan_protection.plan_metadata_on_non_plan") is True:
        errors.append("non_plan_protection.plan_metadata_on_non_plan must be false")
    if _bool_at(report, "fallback.fallback_available") is False:
        errors.append("fallback.fallback_available must be true")
    if _bool_at(report, "cleanup.feature_flag_unset_after") is False:
        errors.append("cleanup.feature_flag_unset_after must be true")
    if _bool_at(report, "cleanup.tracked_diff_after") is True:
        errors.append("cleanup.tracked_diff_after must be false")
    if _bool_at(report, "cleanup.runtime_artifacts_retained") is True:
        errors.append("cleanup.runtime_artifacts_retained must be false")

    for path, value in _walk(report):
        key = path.split(".")[-1].split("[")[0]
        if key in FORBIDDEN_KEYS_V1:
            errors.append(f"forbidden raw/private/protected key: {path}")
        if isinstance(value, str):
            lowered = value.lower()
            for phrase in FORBIDDEN_CLAIM_PHRASES_V1:
                if phrase in lowered:
                    errors.append(f"forbidden claim phrase at {path}: {phrase}")

    if _bool_at(report, "flag_off_baseline.checked") is False:
        warnings.append("flag_off_baseline.checked=false")
    if _bool_at(report, "flag_on_plan_checks.checked") is False:
        warnings.append("flag_on_plan_checks.checked=false")
    if _bool_at(report, "non_plan_protection.checked") is False:
        warnings.append("non_plan_protection.checked=false")
    if _bool_at(report, "flag_on_plan_checks.approved_prompt_count", 0) == 0:
        warnings.append("approved_prompt_count=0")
    if quality_label == "not_observed":
        warnings.append("quality_label=not_observed")
    if decision == "CONSIDER_DEFAULT_ENABLEMENT_READINESS_DESIGN":
        approved_count = _bool_at(report, "flag_on_plan_checks.approved_prompt_count", 0)
        if not isinstance(approved_count, int) or approved_count < 2:
            warnings.append("decision=CONSIDER_DEFAULT_ENABLEMENT_READINESS_DESIGN with too few observations")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def summarize_plan_helper_observation_report_v1(report: dict) -> dict[str, Any]:
    """Return status/count/label-only summary with no raw prompt or response text."""
    validation = validate_plan_helper_observation_report_v1(report)
    side_effects = report.get("side_effects", {}) if isinstance(report, Mapping) else {}
    cleanup = report.get("cleanup", {}) if isinstance(report, Mapping) else {}
    quality = report.get("quality", {}) if isinstance(report, Mapping) else {}
    return {
        "report_type": report.get("report_type"),
        "repo_head": report.get("repo_head"),
        "feature_flag": report.get("feature_flag"),
        "feature_flag_default": report.get("feature_flag_default"),
        "target_branch": report.get("target_branch"),
        "observation_scope": report.get("observation_scope"),
        "decision": report.get("decision"),
        "quality_label": quality.get("quality_label") if isinstance(quality, Mapping) else None,
        "flag_off_checked": _bool_at(report, "flag_off_baseline.checked"),
        "flag_on_checked": _bool_at(report, "flag_on_plan_checks.checked"),
        "approved_prompt_count": _bool_at(report, "flag_on_plan_checks.approved_prompt_count", 0),
        "non_plan_checked": _bool_at(report, "non_plan_protection.checked"),
        "side_effects_clear": isinstance(side_effects, Mapping) and not any(bool(side_effects.get(key)) for key in SIDE_EFFECT_KEYS_V1),
        "fallback_available": _bool_at(report, "fallback.fallback_available"),
        "cleanup_clear": isinstance(cleanup, Mapping)
        and cleanup.get("feature_flag_unset_after") is True
        and cleanup.get("tracked_diff_after") is False
        and cleanup.get("runtime_artifacts_retained") is False,
        "raw_private_text_included": report.get("raw_private_text_included"),
        "benchmark_claim": report.get("benchmark_claim"),
        "turing_test_claim": report.get("turing_test_claim"),
        "default_enablement_claim": report.get("default_enablement_claim"),
        "branch_expansion_claim": report.get("branch_expansion_claim"),
        "valid": validation["valid"],
    }


def render_plan_helper_observation_report_markdown_v1(report: dict) -> str:
    """Render a safe sectioned markdown report from labels/counts/status only."""
    summary = summarize_plan_helper_observation_report_v1(report)
    validation = validate_plan_helper_observation_report_v1(report)
    lines = [
        "SECTION 1 — STATUS",
        f"- report_type: {summary['report_type']}",
        f"- repo_head: {summary['repo_head']}",
        f"- feature_flag: {summary['feature_flag']}",
        f"- feature_flag_default: {summary['feature_flag_default']}",
        f"- target_branch: {summary['target_branch']}",
        f"- observation_scope: {summary['observation_scope']}",
        "SECTION 2 — FLAG-OFF BASELINE",
        f"- checked: {summary['flag_off_checked']}",
        "SECTION 3 — FLAG-ON PLAN OBSERVATION",
        f"- checked: {summary['flag_on_checked']}",
        f"- approved_prompt_count: {summary['approved_prompt_count']}",
        "SECTION 4 — PLAN QUALITY CHECK",
        f"- quality_label: {summary['quality_label']}",
        "SECTION 5 — NON-PLAN PROTECTION",
        f"- checked: {summary['non_plan_checked']}",
        "SECTION 6 — SIDE-EFFECT CHECK",
        f"- side_effects_clear: {summary['side_effects_clear']}",
        "SECTION 7 — FALLBACK / ROLLBACK STATUS",
        f"- fallback_available: {summary['fallback_available']}",
        "- rollback_available: True",
        "SECTION 8 — CLEANUP",
        f"- cleanup_clear: {summary['cleanup_clear']}",
        "SECTION 9 — DECISION",
        f"- decision: {summary['decision']}",
        "SECTION 10 — SAFETY CONFIRMATION",
        f"- raw_private_text_included: {summary['raw_private_text_included']}",
        f"- benchmark_claim: {summary['benchmark_claim']}",
        f"- turing_test_claim: {summary['turing_test_claim']}",
        f"- default_enablement_claim: {summary['default_enablement_claim']}",
        f"- branch_expansion_claim: {summary['branch_expansion_claim']}",
        f"- valid: {validation['valid']}",
    ]
    return "\n".join(lines) + "\n"


def build_plan_helper_observation_report_from_summary_v1(summary: dict) -> dict[str, Any]:
    """Build a safe report from sanitized summary fields only."""
    return build_plan_helper_observation_report_v1(
        repo_head=str(summary.get("repo_head", "")),
        timestamp_local=str(summary.get("timestamp_local", "")),
        flag_off_baseline={"checked": bool(summary.get("flag_off_checked", False))},
        flag_on_plan_checks={
            "checked": bool(summary.get("flag_on_checked", False)),
            "approved_prompt_count": int(summary.get("approved_prompt_count", 0) or 0),
        },
        non_plan_protection={"checked": bool(summary.get("non_plan_checked", False))},
        decision=str(summary.get("decision", "KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY")),
        quality_label=str(summary.get("quality_label", "not_observed")),
    )
