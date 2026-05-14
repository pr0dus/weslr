"""WESLR AI audit dry trace export helpers V1.

Read-only, in-memory helpers that explain how WESLR reached an AI audit
self-governance or safe-next-step recommendation by producing a redacted trace.

This module is not a runner, not a scoring engine, not an answer evaluator, not
runtime/chat/voice wiring, not persistence, not implementation, not automatic
approval, and not an external model testing surface. It does not call models,
execute probes, grade answers, use protected items, use answer keys, expose
hidden prompts, claim official scores, certify systems, or write files.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any


TRACE_EVENT_SCHEMA_VERSION = "ai_audit_dry_trace_event_v1"
TRACE_SCHEMA_VERSION = "ai_audit_dry_trace_v1"
TRACE_SUMMARY_SCHEMA_VERSION = "ai_audit_dry_trace_summary_v1"
NON_EXECUTING_EVENT_STATUS = "non_executing_trace_event_only"
NON_EXECUTING_TRACE_STATUS = "non_executing_dry_trace_only"

AUTHORIZATION_STATUS = [
    "runner_not_authorized",
    "scoring_not_authorized",
    "external_testing_not_authorized",
    "runtime_wiring_not_authorized",
]

FORBIDDEN_NEXT_STEPS = [
    "create_probe_runner",
    "call_external_models",
    "probe_live_ai_systems",
    "add_scoring_engine",
    "add_answer_evaluation_engine",
    "claim_official_benchmark_result",
    "claim_certification",
    "write_weslr_runtime_state",
    "change_runtime_chat_voice_behavior",
    "auto_approve_audit_findings",
    "auto_promote_findings_to_truth",
    "auto_implement_recommendation",
]

FORBIDDEN_FIELDS = {
    "answer", "answers", "answer_key", "answer_keys", "model_output", "model_outputs", "score", "scores",
    "official_score", "official_scores", "clinical_score", "iq_score", "benchmark_score", "internal_audit_score",
    "certification", "certified", "official_benchmark_result", "protected_test_item", "protected_prompt", "hidden_prompt",
}

FORBIDDEN_TRUE_MARKERS = {
    "executable", "runnable", "runner_created", "execution_allowed", "scoring_engine", "automated_grading",
    "answer_evaluation", "external_model_calls", "external_testing_authorized", "runtime_authorized",
    "runtime_behavior_change", "runtime_behavior_changed", "persistence_authorized", "report_persistence",
    "automatic_approval", "auto_approval", "automatic_truth_promotion", "truth_promotion", "automatic_implementation",
    "auto_implementation", "implementation_authorized", "protected_item_present", "answer_key_present", "hidden_prompt_present",
    "official_score_claimed", "certification_claimed", "official_benchmark_claimed",
}

UNAUTHORIZED_ACTION_PHRASES = (
    "runner authorized", "authorize runner", "create runner", "run probes", "execute probes", "probe live",
    "live probing", "external probing authorized", "authorize external testing", "call external model",
    "model call authorized", "scoring authorized", "authorize scoring", "add scoring engine", "grade answers",
    "answer evaluation authorized", "runtime wiring authorized", "wire runtime",
)

SEVERITY_RANK = {"none": 0, "info": 1, "low": 2, "medium": 3, "high": 4}

MARKDOWN_REDACTIONS = {
    "answer_key": "[redacted_boundary]",
    "answer key": "redacted boundary material",
    "hidden_prompt": "[redacted_boundary]",
    "hidden prompt": "redacted boundary material",
    "official_score": "[redacted_boundary]",
    "official score": "official claim",
    "protected_test_item": "[redacted_boundary]",
    "protected material": "redacted boundary material",
    "certification": "official endorsement claim",
    "certified": "officially endorsed",
    "scoring": "automated grading",
    "score": "measurement claim",
    "execute probes": "perform prohibited probe execution",
    "run probes": "perform prohibited probe execution",
}


def _stable_id(prefix: str, *parts: str) -> str:
    return prefix + sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]


def _copy_dict(value: dict[str, Any] | None) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _merge_unique(*collections: list[str]) -> list[str]:
    out: list[str] = []
    for collection in collections:
        for item in collection:
            text = str(item)
            if text and text not in out:
                out.append(text)
    return out


def _ids(items: list[dict[str, Any]], *keys: str) -> list[str]:
    found: set[str] = set()
    for item in items:
        for key in keys:
            value = str(item.get(key, ""))
            if value.strip():
                found.add(value)
    return sorted(found)


def _safe_counts(result: dict[str, Any], keys: tuple[str, ...]) -> dict[str, int]:
    return {key: int(result.get(key, 0) or 0) for key in keys if key in result}


def _boundary_summary() -> dict[str, Any]:
    return {
        "runner_authorized": False,
        "scoring_authorized": False,
        "external_testing_authorized": False,
        "runtime_wiring_authorized": False,
        "automatic_approval_authorized": False,
        "truth_promotion_authorized": False,
        "automatic_implementation_authorized": False,
        "persistence_authorized": False,
        "in_memory_only": True,
        "redacted": True,
    }


def build_ai_audit_dry_trace_event_v1(
    *,
    step_name: str,
    source_layer: str,
    input_summary: dict[str, Any] | None = None,
    output_summary: dict[str, Any] | None = None,
    linked_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Build one redacted non-executing trace event."""
    safe_input = deepcopy(input_summary or {})
    safe_output = deepcopy(output_summary or {})
    event = {
        "schema_version": TRACE_EVENT_SCHEMA_VERSION,
        "trace_event_id": _stable_id("weslr_ai_audit_dry_trace_event_v1_", step_name, source_layer, safe_input, safe_output, linked_ids or []),
        "step_name": str(step_name),
        "source_layer": str(source_layer),
        "input_summary": safe_input,
        "output_summary": safe_output,
        "safety_boundary_summary": _boundary_summary(),
        "linked_ids": sorted(str(item) for item in (linked_ids or [])),
        "redaction_status": "redacted",
        "execution_status": NON_EXECUTING_EVENT_STATUS,
        "not_a_runner": True,
        "not_a_scoring_engine": True,
        "no_model_calls": True,
        "no_persistence": True,
    }
    return event


def _readiness_event(readiness: dict[str, Any]) -> dict[str, Any] | None:
    if not readiness:
        return None
    gaps = list(readiness.get("gap_records", []) or [])
    report = readiness.get("readiness_report") or {}
    return build_ai_audit_dry_trace_event_v1(
        step_name="readiness gaps considered",
        source_layer="readiness_gap_advisor",
        input_summary={"schema_version": readiness.get("schema_version", "unknown"), "in_memory_result_supplied": True},
        output_summary={
            "gap_count": int(readiness.get("gap_count", len(gaps)) or 0),
            "readiness_status": list(report.get("readiness_status", []) or []),
            "readiness_signal": str(report.get("readiness_signal", "")),
            "highest_severity_if_available": _highest_from_items(gaps),
        },
        linked_ids=_ids(gaps, "gap_id"),
    )


def _consistency_event(consistency: dict[str, Any]) -> dict[str, Any] | None:
    if not consistency:
        return None
    issues = list(consistency.get("issues", []) or [])
    return build_ai_audit_dry_trace_event_v1(
        step_name="consistency issues considered",
        source_layer="consistency_review",
        input_summary={"schema_version": consistency.get("schema_version", "unknown"), "in_memory_result_supplied": True},
        output_summary={
            "consistency_status": str(consistency.get("consistency_status", "unknown")),
            "total_issues": int(consistency.get("total_issues", len(issues)) or 0),
            "issue_counts_by_severity": dict(consistency.get("issue_counts_by_severity", {}) or {}),
            "highest_severity_if_available": _highest_from_counts(dict(consistency.get("issue_counts_by_severity", {}) or {})) or _highest_from_items(issues),
        },
        linked_ids=_ids(issues, "issue_id"),
    )


def _drift_event(drift: dict[str, Any]) -> dict[str, Any] | None:
    if not drift:
        return None
    signals = list(drift.get("signals", []) or [])
    summary = drift.get("boundary_summary") or {}
    return build_ai_audit_dry_trace_event_v1(
        step_name="drift signals considered",
        source_layer="drift_monitor",
        input_summary={"schema_version": drift.get("schema_version", "unknown"), "in_memory_result_supplied": True},
        output_summary={
            "drift_status": str(summary.get("drift_status", "unknown")),
            "signal_count": int(drift.get("signal_count", summary.get("total_signals", len(signals))) or 0),
            "counts_by_severity": dict(summary.get("counts_by_severity", {}) or {}),
            "highest_severity_if_available": str(summary.get("highest_severity", "")) or _highest_from_items(signals),
        },
        linked_ids=_ids(signals, "signal_id"),
    )


def _preflight_event(preflight: dict[str, Any]) -> dict[str, Any] | None:
    if not preflight:
        return None
    return build_ai_audit_dry_trace_event_v1(
        step_name="preflight recommendation considered",
        source_layer="preflight_review",
        input_summary={"schema_version": preflight.get("schema_version", "unknown"), "in_memory_result_supplied": True},
        output_summary={
            "recommendation": str(preflight.get("recommendation", "unknown")),
            "readiness_status": list(preflight.get("readiness_status", []) or []),
            "consistency_status": str(preflight.get("consistency_status", "unknown")),
            "drift_status": str(preflight.get("drift_status", "unknown")),
            "issue_counts": dict(preflight.get("issue_counts", {}) or {}),
        },
        linked_ids=[str(preflight.get("preflight_id", ""))] if preflight.get("preflight_id") else [],
    )


def _surface_event(surface: dict[str, Any]) -> dict[str, Any] | None:
    if not surface:
        return None
    is_overview = surface.get("schema_version") == "ai_audit_self_governance_overview_v1"
    return build_ai_audit_dry_trace_event_v1(
        step_name="self-governance surface considered",
        source_layer="self_governance_surface",
        input_summary={"schema_version": surface.get("schema_version", "unknown"), "in_memory_result_supplied": True},
        output_summary={
            "surface_kind": "overview" if is_overview else "card",
            "total_readiness_gaps": int(surface.get("total_readiness_gaps", 0) or 0),
            "total_consistency_issues": int(surface.get("total_consistency_issues", 0) or 0),
            "total_drift_signals": int(surface.get("total_drift_signals", 0) or 0),
            "highest_severity_if_available": str(surface.get("highest_severity", "none")),
        },
        linked_ids=[str(surface.get("overview_id") or surface.get("card_id") or "")],
    )


def _recommendation_event(recommendation: dict[str, Any]) -> dict[str, Any] | None:
    if not recommendation:
        return None
    top = recommendation.get("top_recommendation") or {}
    return build_ai_audit_dry_trace_event_v1(
        step_name="safe next-step recommendation considered",
        source_layer="safe_next_step_recommender",
        input_summary={"schema_version": recommendation.get("schema_version", "unknown"), "in_memory_result_supplied": True},
        output_summary={
            "top_recommendation_title": str(top.get("title", "")),
            "top_recommendation_safety_level": str(top.get("safety_level", "")),
            "ranked_recommendation_count": len(recommendation.get("ranked_recommendations", []) or []),
            "blocked_recommendation_count": len(recommendation.get("blocked_recommendations", []) or []),
            "recommended_does_not_mean_approved": bool(recommendation.get("recommended_does_not_mean_approved", True)),
        },
        linked_ids=[str(recommendation.get("result_id", "")), str(top.get("recommendation_id", ""))],
    )


def _highest_from_counts(counts: dict[str, Any]) -> str:
    present = [str(k) for k, v in counts.items() if int(v or 0) > 0]
    return max(present, key=lambda s: SEVERITY_RANK.get(s, 0)) if present else "none"


def _highest_from_items(items: list[dict[str, Any]]) -> str:
    return _highest_from_counts({str(item.get("severity", "info")): 1 for item in items}) if items else "none"


def build_ai_audit_dry_trace_v1(
    *,
    readiness_gap_advisor_result: dict[str, Any] | None = None,
    consistency_review_result: dict[str, Any] | None = None,
    drift_monitor_result: dict[str, Any] | None = None,
    preflight_review_result: dict[str, Any] | None = None,
    self_governance_card_or_overview: dict[str, Any] | None = None,
    safe_next_step_recommendation_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a redacted non-executing dry trace from supplied in-memory outputs."""
    readiness = _copy_dict(readiness_gap_advisor_result)
    consistency = _copy_dict(consistency_review_result)
    drift = _copy_dict(drift_monitor_result)
    preflight = _copy_dict(preflight_review_result)
    surface = _copy_dict(self_governance_card_or_overview)
    recommendation = _copy_dict(safe_next_step_recommendation_result)
    if preflight:
        readiness = readiness or _copy_dict(preflight.get("readiness_result"))
        consistency = consistency or _copy_dict(preflight.get("consistency_result"))
        drift = drift or _copy_dict(preflight.get("drift_result"))
    events = [event for event in (
        _readiness_event(readiness), _consistency_event(consistency), _drift_event(drift), _preflight_event(preflight),
        _surface_event(surface), _recommendation_event(recommendation),
    ) if event]
    top = recommendation.get("top_recommendation") or {}
    final_summary = {
        "preflight_recommendation": str(preflight.get("recommendation", "")),
        "safe_next_step": str(top.get("title", "")),
        "safe_next_step_safety_level": str(top.get("safety_level", "")),
        "recommended_does_not_mean_approved": True,
        "trace_does_not_mean_implementation": True,
    }
    forbidden = _merge_unique(
        list(preflight.get("forbidden_next_steps", []) or []),
        list(surface.get("forbidden_next_steps", []) or []),
        list(recommendation.get("forbidden_next_steps", []) or []),
        FORBIDDEN_NEXT_STEPS,
    )
    trace = {
        "schema_version": TRACE_SCHEMA_VERSION,
        "trace_id": _stable_id("weslr_ai_audit_dry_trace_v1_", *[event.get("trace_event_id", "") for event in events], final_summary),
        "redacted_count_only": True,
        "in_memory_only": True,
        "trace_events": events,
        "final_recommendation_summary": final_summary,
        "safety_boundaries": _boundary_summary(),
        "forbidden_next_steps": forbidden,
        "execution_status": NON_EXECUTING_TRACE_STATUS,
        "authorization_status": list(AUTHORIZATION_STATUS),
        "not_a_runner": True,
        "not_a_scoring_engine": True,
        "not_a_certification": True,
        "not_a_benchmark_result": True,
        "not_truth_promotion": True,
        "not_implementation": True,
        "no_model_calls": True,
        "no_runtime_behavior_change": True,
        "no_persistence": True,
        "no_file_writes": True,
    }
    trace["validation_status"] = validate_ai_audit_dry_trace_v1(trace)
    return trace


def summarize_ai_audit_dry_trace_v1(trace: dict[str, Any]) -> dict[str, Any]:
    """Return a count-only redacted summary of a dry trace."""
    safe = deepcopy(trace)
    events = list(safe.get("trace_events", []) or [])
    severities = [str((event.get("output_summary") or {}).get("highest_severity_if_available", "none")) for event in events]
    highest = max(severities, key=lambda s: SEVERITY_RANK.get(s, 0)) if severities else "none"
    summary = {
        "schema_version": TRACE_SUMMARY_SCHEMA_VERSION,
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_TRACE_STATUS,
        "total_events": len(events),
        "source_layers_present": sorted({str(event.get("source_layer", "unknown")) for event in events}),
        "highest_severity_if_available": highest,
        "final_recommendation": dict(safe.get("final_recommendation_summary", {}) or {}),
        "safe_next_steps": [str((safe.get("final_recommendation_summary") or {}).get("safe_next_step", ""))],
        "forbidden_next_steps": list(safe.get("forbidden_next_steps", []) or []),
        "validation_status": validate_ai_audit_dry_trace_v1(safe),
    }
    return summary


def to_ai_audit_dry_trace_json_safe_v1(trace: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON-serializable redacted dry trace dict without file writes."""
    safe = deepcopy(trace)
    safe["json_safe_export"] = True
    safe["files_written"] = False
    safe["report_persisted"] = False
    safe["validation_status"] = validate_ai_audit_dry_trace_v1(safe)
    return safe


def _find_forbidden(value: Any, path: str = "trace") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text == "validation_status":
                continue
            if key_text in FORBIDDEN_FIELDS:
                issues.append(f"forbidden dry trace field: {nested_path}")
            if key_text in FORBIDDEN_TRUE_MARKERS and nested is True:
                issues.append(f"forbidden dry trace true marker: {nested_path}")
            issues.extend(_find_forbidden(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_find_forbidden(nested, f"{path}[{index}]"))
    return issues


def _authorization_phrase_issues(trace: dict[str, Any]) -> list[str]:
    chunks: list[str] = []
    chunks.extend(str(v) for v in (trace.get("final_recommendation_summary") or {}).values())
    for event in trace.get("trace_events", []) or []:
        chunks.extend(str(v) for v in (event.get("output_summary") or {}).values())
    lowered = " ".join(chunks).lower().replace("_", " ").replace("-", " ")
    if any(phrase in lowered for phrase in UNAUTHORIZED_ACTION_PHRASES):
        return ["dry trace recommendation must not imply runner/scoring/external probing is authorized"]
    return []


def validate_ai_audit_dry_trace_v1(trace: dict[str, Any]) -> dict[str, Any]:
    """Validate dry trace outputs preserve non-executing boundaries."""
    issues: list[str] = []
    if not isinstance(trace, dict):
        return {"valid": False, "redacted_count_only": True, "issues": ["dry trace must be a dict"]}
    if trace.get("schema_version") != TRACE_SCHEMA_VERSION:
        issues.append("invalid schema_version")
    for key in ("redacted_count_only", "in_memory_only", "not_a_runner", "not_a_scoring_engine", "not_a_certification", "not_a_benchmark_result", "not_truth_promotion", "not_implementation", "no_model_calls", "no_runtime_behavior_change", "no_persistence", "no_file_writes"):
        if trace.get(key) is not True:
            issues.append(f"dry trace must be marked {key}")
    if trace.get("execution_status") != NON_EXECUTING_TRACE_STATUS:
        issues.append("dry trace execution_status must be non_executing_dry_trace_only")
    auth = set(trace.get("authorization_status") or [])
    for required in AUTHORIZATION_STATUS:
        if required not in auth:
            issues.append(f"authorization_status missing {required}")
    safety = trace.get("safety_boundaries") or {}
    for key in ("runner_authorized", "scoring_authorized", "external_testing_authorized", "runtime_wiring_authorized", "automatic_approval_authorized", "truth_promotion_authorized", "automatic_implementation_authorized", "persistence_authorized"):
        if safety.get(key) is not False:
            issues.append(f"safety boundary {key} must be False")
    for event in trace.get("trace_events", []) or []:
        if event.get("schema_version") != TRACE_EVENT_SCHEMA_VERSION:
            issues.append("trace event has invalid schema_version")
        if event.get("redaction_status") != "redacted":
            issues.append("trace event must be redacted")
        if event.get("execution_status") != NON_EXECUTING_EVENT_STATUS:
            issues.append("trace event execution_status must be non_executing_trace_event_only")
    issues.extend(_find_forbidden(trace))
    issues.extend(_authorization_phrase_issues(trace))
    return {
        "valid": not issues,
        "redacted_count_only": True,
        "issues": issues,
        "execution_authorized": False,
        "runner_authorized": False,
        "scoring_authorized": False,
        "external_testing_authorized": False,
        "model_calls_made": False,
        "automatic_approval_granted": False,
        "automatic_implementation_started": False,
        "report_persisted": False,
        "files_written": False,
        "runtime_behavior_changed": False,
        "protected_items_copied": False,
        "answer_keys_used": False,
        "hidden_prompts_used": False,
        "official_score_claimed": False,
        "certification_claimed": False,
        "official_benchmark_claimed": False,
    }


def _redact_markdown(text: str) -> str:
    redacted = text
    for old, new in MARKDOWN_REDACTIONS.items():
        redacted = redacted.replace(old, new).replace(old.title(), new)
    return redacted


def render_ai_audit_dry_trace_markdown_v1(trace: dict[str, Any]) -> str:
    """Render deterministic redacted Markdown for dry trace review."""
    safe = deepcopy(trace)
    by_layer = {event.get("source_layer"): event for event in safe.get("trace_events", []) or []}

    def line(layer: str, label: str) -> str:
        event = by_layer.get(layer) or {}
        output = event.get("output_summary") or {}
        return f"- {label}: {output if output else 'not supplied'}"

    final = safe.get("final_recommendation_summary") or {}
    lines = [
        "# AI Audit Dry Trace",
        "",
        "## Inputs Considered",
        f"- Total trace events: {len(safe.get('trace_events', []) or [])}",
        "- Input mode: supplied in-memory helper outputs only",
        "",
        "## Readiness",
        line("readiness_gap_advisor", "Readiness output"),
        "",
        "## Consistency",
        line("consistency_review", "Consistency output"),
        "",
        "## Drift",
        line("drift_monitor", "Drift output"),
        "",
        "## Preflight",
        line("preflight_review", "Preflight output"),
        "",
        "## Self-Governance Surface",
        line("self_governance_surface", "Surface output"),
        "",
        "## Safe Next-Step Recommendation",
        f"- Final recommendation: {final.get('safe_next_step', '')}",
        f"- Preflight recommendation: {final.get('preflight_recommendation', '')}",
        "- Meaning: trace/recommendation only; not approved and not implemented.",
        "",
        "## Safety Boundaries",
        "- Runner authorized: false",
        "- Automated grading authorized: false",
        "- External testing authorized: false",
        "- Runtime wiring authorized: false",
        "- Persistence authorized: false",
        "- Automatic approval authorized: false",
        "- Automatic implementation authorized: false",
        "",
        "## Forbidden Next Steps",
        *[f"- {item}" for item in safe.get("forbidden_next_steps", [])],
        "",
        "## Non-Execution Disclaimer",
        "- This dry trace explains supplied in-memory review outputs only.",
        "- It does not authorize audits, implementation, live probing, automated grading, runtime wiring, persistence, or public claims.",
    ]
    return _redact_markdown("\n".join(lines))
