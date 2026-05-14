"""WESLR AI audit preflight review helpers V1.

In-memory coordinator helpers that combine existing non-executing AI audit
self-governance layers: readiness/gap advisor, consistency review, and drift
monitor. Preflight review is not approval to execute probes, not a runner, not a
scoring engine, not certification, and not persistence.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any

from weslr.ai_audit_consistency_review import build_ai_audit_consistency_review_result_v1, validate_ai_audit_consistency_review_result_v1
from weslr.ai_audit_drift_monitor import build_ai_audit_drift_monitor_result_v1, validate_ai_audit_drift_monitor_result_v1
from weslr.ai_audit_readiness_gap_advisor import build_ai_audit_readiness_gap_advisor_result_v1, validate_ai_audit_readiness_gap_advisor_result_v1


PREFLIGHT_SCHEMA_VERSION = "ai_audit_preflight_review_v1"
PREFLIGHT_INPUT_SCHEMA_VERSION = "ai_audit_preflight_inputs_v1"
PREFLIGHT_SUMMARY_SCHEMA_VERSION = "ai_audit_preflight_issue_summary_v1"
NON_EXECUTING_PREFLIGHT_STATUS = "non_executing_preflight_only"

ALLOWED_RECOMMENDATIONS = {
    "proceed_with_review_only",
    "needs_more_foundation_work",
    "blocked_by_drift",
    "blocked_by_inconsistency",
    "blocked_by_missing_readiness",
    "insufficient_inputs",
}
FORBIDDEN_RECOMMENDATION_WORDS = {"execute", "runner", "scoring", "score", "external probing", "model call", "live probing"}
FORBIDDEN_FIELDS = {
    "answer", "answers", "answer_key", "answer_keys", "model_output", "model_outputs", "score", "scores",
    "official_score", "official_scores", "clinical_score", "iq_score", "benchmark_score", "internal_audit_score",
    "certification", "certified", "official_benchmark_result", "protected_test_item", "protected_prompt", "hidden_prompt",
}
FORBIDDEN_TRUE_MARKERS = {
    "executable", "runnable", "runner_created", "execution_allowed", "scoring_engine", "automated_grading",
    "answer_evaluation", "external_model_calls", "external_testing_authorized", "runtime_authorized",
    "runtime_behavior_change", "persistence_authorized", "report_persistence", "automatic_approval", "auto_approval",
    "automatic_truth_promotion", "truth_promotion", "protected_item_present", "answer_key_present", "hidden_prompt_present",
    "official_score_claimed", "certification_claimed", "official_benchmark_claimed",
}
SAFE_NEXT_STEPS = [
    "review_preflight_summary",
    "resolve_readiness_gaps_before_execution_design",
    "resolve_consistency_issues_before_operator_review",
    "resolve_drift_warnings_before_future_phase",
    "continue_non_executing_helper_work_only",
]
FORBIDDEN_NEXT_STEPS = [
    "execute_probes", "create_probe_runner", "call_external_models", "probe_live_ai_systems", "add_scoring_engine",
    "claim_certification", "claim_official_benchmark_result", "write_weslr_runtime_state", "change_runtime_chat_voice_behavior",
    "auto_approve_audit_findings", "auto_promote_findings_to_truth",
]


def _stable_id(prefix: str, *parts: str) -> str:
    return prefix + sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:12]


def _copy_list(value: Any) -> list[Any]:
    return deepcopy(list(value or []))


def normalize_ai_audit_preflight_inputs_v1(
    *,
    plans: list[dict[str, Any]] | None = None,
    findings: list[dict[str, Any]] | None = None,
    packets: list[dict[str, Any]] | None = None,
    reports: list[dict[str, Any]] | None = None,
    review_cards: list[dict[str, Any]] | None = None,
    file_snapshots: list[dict[str, Any]] | None = None,
    texts: list[str | dict[str, Any]] | None = None,
    readiness_result: dict[str, Any] | None = None,
    consistency_result: dict[str, Any] | None = None,
    drift_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize optional in-memory preflight inputs without side effects."""
    return {
        "schema_version": PREFLIGHT_INPUT_SCHEMA_VERSION,
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_PREFLIGHT_STATUS,
        "plans": _copy_list(plans),
        "findings": _copy_list(findings),
        "packets": _copy_list(packets),
        "reports": _copy_list(reports),
        "review_cards": _copy_list(review_cards),
        "file_snapshots": _copy_list(file_snapshots),
        "texts": deepcopy(list(texts or [])),
        "readiness_result": deepcopy(readiness_result) if isinstance(readiness_result, dict) else None,
        "consistency_result": deepcopy(consistency_result) if isinstance(consistency_result, dict) else None,
        "drift_result": deepcopy(drift_result) if isinstance(drift_result, dict) else None,
        "filesystem_read_performed": False,
        "files_written": False,
        "no_execution": True,
    }


def _severity_counts_from_readiness(readiness: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for gap in readiness.get("gap_records", []) or []:
        sev = str(gap.get("severity", "info"))
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def _severity_counts_from_consistency(consistency: dict[str, Any]) -> dict[str, int]:
    return dict(consistency.get("issue_counts_by_severity") or {})


def _severity_counts_from_drift(drift: dict[str, Any]) -> dict[str, int]:
    return dict((drift.get("boundary_summary") or {}).get("counts_by_severity") or {})


def _count_blockers(counts: dict[str, int]) -> int:
    return int(counts.get("high", 0)) + int(counts.get("medium", 0))


def _count_warnings(counts: dict[str, int]) -> int:
    return int(counts.get("low", 0)) + int(counts.get("info", 0))


def _recommendation(readiness: dict[str, Any], consistency: dict[str, Any], drift: dict[str, Any], artifact_count: int) -> str:
    if artifact_count == 0:
        return "insufficient_inputs"
    if int((drift.get("boundary_summary") or {}).get("counts_by_severity", {}).get("high", 0)) > 0:
        return "blocked_by_drift"
    if consistency.get("consistency_status") == "inconsistent" or _count_blockers(_severity_counts_from_consistency(consistency)) > 0:
        return "blocked_by_inconsistency"
    readiness_signal = (readiness.get("readiness_report") or {}).get("readiness_signal", "")
    if readiness_signal == "gaps_require_operator_review" or _count_blockers(_severity_counts_from_readiness(readiness)) > 0:
        return "blocked_by_missing_readiness"
    if readiness.get("schema_version") != "ai_audit_readiness_gap_advisor_result_v1":
        return "needs_more_foundation_work"
    return "proceed_with_review_only"


def build_ai_audit_preflight_review_v1(
    *,
    plans: list[dict[str, Any]] | None = None,
    findings: list[dict[str, Any]] | None = None,
    packets: list[dict[str, Any]] | None = None,
    reports: list[dict[str, Any]] | None = None,
    review_cards: list[dict[str, Any]] | None = None,
    file_snapshots: list[dict[str, Any]] | None = None,
    texts: list[str | dict[str, Any]] | None = None,
    readiness_result: dict[str, Any] | None = None,
    consistency_result: dict[str, Any] | None = None,
    drift_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one non-executing preflight result from safe helper outputs."""
    normalized = normalize_ai_audit_preflight_inputs_v1(
        plans=plans, findings=findings, packets=packets, reports=reports, review_cards=review_cards,
        file_snapshots=file_snapshots, texts=texts, readiness_result=readiness_result,
        consistency_result=consistency_result, drift_result=drift_result,
    )
    readiness = normalized["readiness_result"] or build_ai_audit_readiness_gap_advisor_result_v1(
        plans=normalized["plans"], findings=normalized["findings"], packets=normalized["packets"], reports=normalized["reports"]
    )
    consistency = normalized["consistency_result"] or build_ai_audit_consistency_review_result_v1(
        plan=normalized["plans"][0] if normalized["plans"] else None,
        findings=normalized["findings"],
        packet=normalized["packets"][0] if normalized["packets"] else None,
        report=normalized["reports"][0] if normalized["reports"] else None,
        cards=normalized["review_cards"],
    )
    drift = normalized["drift_result"] or build_ai_audit_drift_monitor_result_v1(file_snapshots=normalized["file_snapshots"], texts=normalized["texts"])
    artifact_count = sum(len(normalized[key]) for key in ("plans", "findings", "packets", "reports", "review_cards", "file_snapshots", "texts"))
    readiness_counts = _severity_counts_from_readiness(readiness)
    consistency_counts = _severity_counts_from_consistency(consistency)
    drift_counts = _severity_counts_from_drift(drift)
    blocker_counts = {
        "readiness": _count_blockers(readiness_counts),
        "consistency": _count_blockers(consistency_counts),
        "drift": int(drift_counts.get("high", 0)),
    }
    warning_counts = {
        "readiness": _count_warnings(readiness_counts),
        "consistency": _count_warnings(consistency_counts),
        "drift": _count_warnings(drift_counts) + int(drift_counts.get("medium", 0)),
    }
    recommendation = _recommendation(readiness, consistency, drift, artifact_count)
    result = {
        "schema_version": PREFLIGHT_SCHEMA_VERSION,
        "preflight_id": _stable_id("weslr_ai_audit_preflight_v1_", recommendation, readiness.get("schema_version", ""), consistency.get("review_id", ""), drift.get("monitor_id", "")),
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_PREFLIGHT_STATUS,
        "readiness_status": list((readiness.get("readiness_report") or {}).get("readiness_status", [])),
        "consistency_status": consistency.get("consistency_status", "insufficient_artifacts"),
        "drift_status": (drift.get("boundary_summary") or {}).get("drift_status", "no_drift_signals"),
        "issue_counts": {
            "readiness_gaps": int(readiness.get("gap_count", len(readiness.get("gap_records", []) or []))),
            "consistency_issues": int(consistency.get("total_issues", 0)),
            "drift_signals": int(drift.get("signal_count", 0)),
        },
        "blocker_counts": blocker_counts,
        "warning_counts": warning_counts,
        "safe_next_steps": list(dict.fromkeys(SAFE_NEXT_STEPS + list((readiness.get("readiness_report") or {}).get("safe_next_steps", [])) + list((drift.get("boundary_summary") or {}).get("safe_next_steps", [])))),
        "forbidden_next_steps": list(dict.fromkeys(FORBIDDEN_NEXT_STEPS + list((readiness.get("readiness_report") or {}).get("forbidden_next_steps", [])) + list((drift.get("boundary_summary") or {}).get("forbidden_next_steps", [])))),
        "recommendation": recommendation,
        "authorization_status": ["runner_not_authorized", "scoring_not_authorized", "external_testing_not_authorized", "runtime_wiring_not_authorized"],
        "readiness_result": readiness,
        "consistency_result": consistency,
        "drift_result": drift,
        "safety_boundaries": {
            "execution_authorized": False, "runner_authorized": False, "scoring_authorized": False,
            "external_testing_authorized": False, "runtime_wiring_authorized": False, "automatic_approval_authorized": False,
            "truth_promotion_authorized": False, "persistence_authorized": False, "in_memory_only": True,
        },
        "not_a_runner": True,
        "not_a_scoring_engine": True,
        "not_a_certification": True,
        "not_a_benchmark_result": True,
        "not_truth_promotion": True,
        "no_model_calls": True,
        "no_runtime_behavior_change": True,
        "no_persistence": True,
    }
    result["validation_status"] = validate_ai_audit_preflight_review_v1(result)
    return result


def _all_counts(result: dict[str, Any]) -> dict[str, int]:
    return {
        "readiness_gaps": int((result.get("issue_counts") or {}).get("readiness_gaps", 0)),
        "consistency_issues": int((result.get("issue_counts") or {}).get("consistency_issues", 0)),
        "drift_signals": int((result.get("issue_counts") or {}).get("drift_signals", 0)),
    }


def summarize_ai_audit_preflight_issues_v1(preflight_result: dict[str, Any]) -> dict[str, Any]:
    """Return count-only issue summary for a preflight result."""
    result = deepcopy(preflight_result)
    counts = _all_counts(result)
    severity_sources = []
    for source in (result.get("readiness_result", {}).get("gap_records", []) or []):
        severity_sources.append(str(source.get("severity", "info")))
    severity_sources.extend((result.get("consistency_result", {}).get("issue_counts_by_severity") or {}).keys())
    severity_sources.extend((result.get("drift_result", {}).get("boundary_summary", {}).get("counts_by_severity") or {}).keys())
    rank = {"none": 0, "info": 1, "low": 2, "medium": 3, "high": 4}
    highest = "none" if not severity_sources else max(severity_sources, key=lambda s: rank.get(s, 0))
    return {
        "schema_version": PREFLIGHT_SUMMARY_SCHEMA_VERSION,
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_PREFLIGHT_STATUS,
        "total_issues": sum(counts.values()),
        **counts,
        "highest_severity": highest,
        "blockers": dict(result.get("blocker_counts") or {}),
        "warnings": dict(result.get("warning_counts") or {}),
        "safe_next_steps": list(result.get("safe_next_steps", [])),
        "forbidden_next_steps": list(result.get("forbidden_next_steps", [])),
        "not_a_score": True,
        "not_certification": True,
    }


def _find_forbidden(value: Any, path: str = "preflight") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_FIELDS:
                issues.append(f"forbidden preflight field: {nested_path}")
            if key_text in FORBIDDEN_TRUE_MARKERS and nested is True:
                issues.append(f"forbidden preflight true marker: {nested_path}")
            issues.extend(_find_forbidden(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_find_forbidden(nested, f"{path}[{index}]"))
    return issues


def validate_ai_audit_preflight_review_v1(result: dict[str, Any]) -> dict[str, Any]:
    """Validate preflight output boundaries without execution or persistence."""
    issues: list[str] = []
    if not isinstance(result, dict):
        return {"valid": False, "redacted_count_only": True, "issues": ["preflight result must be a dict"]}
    if result.get("schema_version") != PREFLIGHT_SCHEMA_VERSION:
        issues.append("invalid schema_version")
    for key in ("redacted_count_only", "in_memory_only", "not_a_runner", "not_a_scoring_engine", "not_a_certification", "not_a_benchmark_result", "not_truth_promotion", "no_model_calls", "no_runtime_behavior_change", "no_persistence"):
        if result.get(key) is not True:
            issues.append(f"preflight must be marked {key}")
    if result.get("execution_status") != NON_EXECUTING_PREFLIGHT_STATUS:
        issues.append("preflight execution_status must be non_executing_preflight_only")
    recommendation = str(result.get("recommendation", ""))
    if recommendation not in ALLOWED_RECOMMENDATIONS:
        issues.append("invalid preflight recommendation")
    lowered = recommendation.lower().replace("_", " ")
    for word in FORBIDDEN_RECOMMENDATION_WORDS:
        if word in lowered:
            issues.append("preflight recommendation must not imply execution/scoring/external probing")
    safety = result.get("safety_boundaries") or {}
    for key in ("execution_authorized", "runner_authorized", "scoring_authorized", "external_testing_authorized", "runtime_wiring_authorized", "automatic_approval_authorized", "truth_promotion_authorized", "persistence_authorized"):
        if safety.get(key) is not False:
            issues.append(f"safety boundary {key} must be False")
    if isinstance(result.get("readiness_result"), dict) and result["readiness_result"].get("schema_version"):
        validation = validate_ai_audit_readiness_gap_advisor_result_v1(result["readiness_result"])
        if not validation.get("valid", False):
            issues.append("readiness_result validation failed")
    if isinstance(result.get("consistency_result"), dict) and result["consistency_result"].get("schema_version"):
        validation = validate_ai_audit_consistency_review_result_v1(result["consistency_result"])
        if not validation.get("valid", False):
            issues.append("consistency_result validation failed")
    if isinstance(result.get("drift_result"), dict) and result["drift_result"].get("schema_version"):
        validation = validate_ai_audit_drift_monitor_result_v1(result["drift_result"])
        if not validation.get("valid", False):
            issues.append("drift_result validation failed")
    issues.extend(_find_forbidden(result))
    return {
        "valid": not issues,
        "redacted_count_only": True,
        "issues": issues,
        "execution_authorized": False,
        "runner_authorized": False,
        "scoring_authorized": False,
        "external_testing_authorized": False,
        "model_calls_made": False,
        "report_persisted": False,
        "runtime_behavior_changed": False,
        "protected_items_copied": False,
        "answer_keys_used": False,
        "hidden_prompts_used": False,
        "official_score_claimed": False,
        "certification_claimed": False,
        "official_benchmark_claimed": False,
    }


def render_ai_audit_preflight_review_markdown_v1(result: dict[str, Any]) -> str:
    """Render deterministic redacted Markdown for operator review."""
    safe = deepcopy(result)
    summary = summarize_ai_audit_preflight_issues_v1(safe)
    lines = [
        "# AI Audit Preflight Review",
        "",
        "## Readiness",
        f"- Status: {', '.join(safe.get('readiness_status', [])) or 'unknown'}",
        "",
        "## Consistency",
        f"- Status: {safe.get('consistency_status', 'unknown')}",
        "",
        "## Drift",
        f"- Status: {safe.get('drift_status', 'unknown')}",
        "",
        "## Recommendation",
        f"- {safe.get('recommendation', 'unknown')}",
        "- Meaning: non-executing review/helper work only; not probe execution.",
        "",
        "## Safety Boundaries",
        "- Runner authorized: false",
        "- Scoring authorized: false",
        "- External testing authorized: false",
        "- Runtime wiring authorized: false",
        "",
        "## Forbidden Next Steps",
        *[f"- {item}" for item in safe.get("forbidden_next_steps", [])],
        "",
        "## Issue Summary",
        f"- Total issues: {summary['total_issues']}",
        f"- Highest severity: {summary['highest_severity']}",
    ]
    forbidden = ("answer_key", "hidden_prompt", "protected_test_item", "model_output", "official_score")
    rendered = "\n".join(lines)
    for token in forbidden:
        rendered = rendered.replace(token, "[redacted_forbidden_token]")
    return rendered
