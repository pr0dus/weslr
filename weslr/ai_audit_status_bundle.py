"""WESLR AI audit read-only status bundle helpers V1.

Read-only, in-memory helpers that package AI audit self-governance status into
one portable, redacted structure for inspection.

This module is not a UI, not a runner, not a scoring engine, not an answer
evaluator, not runtime/chat/voice wiring, not persistence, not implementation,
not automatic approval, and not an external model testing surface. It does not
call models, execute probes, grade answers, use protected items, use answer
keys, expose hidden prompts, claim official scores, certify systems, or write
files / `.weslr` runtime state.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any


BUNDLE_SCHEMA_VERSION = "ai_audit_read_only_status_bundle_v1"
BUNDLE_TYPE = "ai_audit_read_only_status_bundle"
EXECUTION_STATUS = "non_executing_status_bundle_only"

AUTHORIZATION_STATUS = {
    "runner_not_authorized": True,
    "scoring_not_authorized": True,
    "external_testing_not_authorized": True,
    "runtime_wiring_not_authorized": True,
    "persistence_not_authorized_by_default": True,
}

DEFAULT_CANON_REFS = [
    "AI_AUDIT_SELF_GOVERNANCE_BOUNDARY_V1",
    "AI_AUDIT_SAFE_NEXT_STEP_RECOMMENDER_V1",
    "AI_AUDIT_DRY_TRACE_EXPORT_V1",
    "AI_AUDIT_NON_EXECUTION_DOCTRINE_V1",
]

SAFETY_BOUNDARIES = {
    "read_only": True,
    "in_memory_only": True,
    "redacted_count_only": True,
    "no_model_calls": True,
    "no_live_ai_system_probing": True,
    "no_runner": True,
    "no_scoring_engine": True,
    "no_answer_evaluation_engine": True,
    "no_runtime_wiring": True,
    "no_ui_integration": True,
    "no_file_writes": True,
    "no_report_persistence": True,
    "no_weslr_runtime_state": True,
    "no_automatic_approval": True,
    "no_automatic_truth_promotion": True,
    "no_automatic_implementation": True,
    "no_official_benchmark_claims": True,
    "no_certification_claims": True,
    "no_protected_items": True,
    "no_answer_keys": True,
    "no_hidden_prompts": True,
}

FORBIDDEN_NEXT_STEPS = [
    "create_probe_runner",
    "call_external_models",
    "probe_live_ai_systems",
    "add_scoring_engine",
    "add_answer_evaluation_engine",
    "claim_official_benchmark_result",
    "claim_certification",
    "write_weslr_runtime_state",
    "persist_report_by_default",
    "change_runtime_chat_voice_behavior",
    "auto_approve_audit_findings",
    "auto_promote_findings_to_truth",
    "auto_implement_recommendation",
]

FORBIDDEN_FIELDS = {
    "answer",
    "answers",
    "answer_key",
    "answer_keys",
    "model_output",
    "model_outputs",
    "raw_model_output",
    "raw_model_outputs",
    "score",
    "scores",
    "official_score",
    "official_scores",
    "clinical_score",
    "iq_score",
    "benchmark_score",
    "internal_audit_score",
    "certification",
    "certified",
    "official_benchmark_result",
    "protected_test_item",
    "protected_test_items",
    "protected_prompt",
    "hidden_prompt",
    "hidden_prompts",
    "file_export_authorized",
    "file_write_authorized",
    "write_files_authorized",
}

FORBIDDEN_TRUE_MARKERS = {
    "executable",
    "runnable",
    "runner_created",
    "runner_authorized",
    "execution_allowed",
    "scoring_engine",
    "scoring_authorized",
    "automated_grading",
    "answer_evaluation",
    "answer_evaluation_authorized",
    "external_model_calls",
    "external_testing_authorized",
    "live_probing_authorized",
    "runtime_authorized",
    "runtime_wiring_authorized",
    "runtime_behavior_change",
    "runtime_behavior_changed",
    "persistence_authorized",
    "report_persistence",
    "file_export_authorized",
    "file_write_authorized",
    "write_files_authorized",
    "automatic_approval",
    "auto_approval",
    "automatic_truth_promotion",
    "truth_promotion",
    "automatic_implementation",
    "auto_implementation",
    "implementation_authorized",
    "protected_item_present",
    "answer_key_present",
    "hidden_prompt_present",
    "official_score_claimed",
    "certification_claimed",
    "official_benchmark_claimed",
}

UNAUTHORIZED_RECOMMENDATION_PHRASES = (
    "runner authorized",
    "authorize runner",
    "create runner",
    "run probes",
    "execute probes",
    "probe live",
    "live probing",
    "external probing authorized",
    "authorize external testing",
    "call external model",
    "model call authorized",
    "scoring authorized",
    "authorize scoring",
    "add scoring engine",
    "grade answers",
    "answer evaluation authorized",
    "runtime wiring authorized",
    "wire runtime",
    "persist report",
    "write report",
    "file export authorized",
)

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
    "scoring": "measurement",
    "score": "measurement claim",
    "execute probes": "perform prohibited probe execution",
    "run probes": "perform prohibited probe execution",
}


def _stable_id(prefix: str, *parts: Any) -> str:
    return prefix + sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]


def _copy_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return deepcopy(list(value))
    return [deepcopy(value)]


def _as_text(value: Any, default: str) -> str:
    text = str(value or "").strip()
    return text or default


def _readiness_status(readiness: dict[str, Any], card: dict[str, Any], overview: dict[str, Any]) -> list[str]:
    for value in (card.get("readiness_status"), readiness.get("readiness_status"), (readiness.get("readiness_report") or {}).get("readiness_status")):
        if isinstance(value, list) and value:
            return [str(item) for item in value]
        if isinstance(value, str) and value:
            return [value]
    states = overview.get("readiness_states")
    if isinstance(states, list) and states:
        return [str(item) for item in states]
    if readiness.get("schema_version") or card.get("schema_version") or overview.get("schema_version"):
        return ["readiness_result_supplied"]
    return ["readiness_not_supplied"]


def _count_from(*values: Any, fallback_items: Any = None) -> int:
    for value in values:
        if value is not None:
            return int(value or 0)
    return len(fallback_items or [])


def _consistency_status(consistency: dict[str, Any], card: dict[str, Any], overview: dict[str, Any]) -> str:
    if card.get("consistency_status"):
        return str(card["consistency_status"])
    states = overview.get("consistency_states")
    if isinstance(states, list) and states:
        return ", ".join(str(item) for item in states)
    if consistency.get("consistency_status"):
        return str(consistency["consistency_status"])
    if consistency.get("schema_version"):
        return "consistency_result_supplied"
    return "consistency_not_supplied"


def _drift_status(drift: dict[str, Any], card: dict[str, Any], overview: dict[str, Any]) -> str:
    if card.get("drift_status"):
        return str(card["drift_status"])
    states = overview.get("drift_states")
    if isinstance(states, list) and states:
        return ", ".join(str(item) for item in states)
    summary = drift.get("boundary_summary") or {}
    if summary.get("drift_status"):
        return str(summary["drift_status"])
    if drift.get("schema_version"):
        return "drift_result_supplied"
    return "drift_not_supplied"


def _preflight_recommendation(preflight: dict[str, Any], card: dict[str, Any], recommendation: dict[str, Any]) -> str:
    top = recommendation.get("top_recommendation") or recommendation.get("selected_recommendation") or {}
    if isinstance(top, dict) and top.get("title"):
        return str(top["title"])
    for key in ("safe_next_step", "recommendation", "preflight_recommendation"):
        if recommendation.get(key):
            return str(recommendation[key])
    if card.get("preflight_recommendation"):
        return str(card["preflight_recommendation"])
    if preflight.get("recommendation"):
        return str(preflight["recommendation"])
    return "inspect_supplied_results_only"


def _recommendation_reason(recommendation: dict[str, Any]) -> str:
    top = recommendation.get("top_recommendation") or recommendation.get("selected_recommendation") or {}
    if isinstance(top, dict) and top.get("reason"):
        return str(top["reason"])
    for key in ("reason", "recommendation_reason", "why"):
        if recommendation.get(key):
            return str(recommendation[key])
    return "derived_from_supplied_in_memory_status_only"


def _dry_trace_summary(dry_trace: dict[str, Any]) -> dict[str, Any]:
    summary = dry_trace.get("summary") if isinstance(dry_trace.get("summary"), dict) else {}
    events = dry_trace.get("trace_events") or dry_trace.get("events") or []
    event_count = _count_from(dry_trace.get("total_trace_events"), summary.get("total_trace_events"), summary.get("event_count"), fallback_items=events)
    layers = dry_trace.get("source_layers_present") or summary.get("source_layers_present") or []
    if not layers and isinstance(events, list):
        layers = sorted({str(event.get("source_layer", "")) for event in events if isinstance(event, dict) and event.get("source_layer")})
    return {
        "trace_supplied": bool(dry_trace),
        "total_trace_events": event_count,
        "source_layer_count": len(layers or []),
        "source_layers_present": [str(item) for item in (layers or [])],
        "redacted": True,
        "raw_trace_events_included": False,
    }


def _merge_unique(*collections: list[Any]) -> list[str]:
    merged: list[str] = []
    for collection in collections:
        for item in collection:
            text = str(item)
            if text and text not in merged:
                merged.append(text)
    return merged


def _safe_label(item: Any) -> str:
    label = str(item).replace("_", " ").replace("-", " ")
    replacements = {
        "add scoring engine": "add measurement engine",
        "add answer evaluation engine": "add answer evaluation engine",
        "claim official benchmark result": "make official benchmark claims",
        "claim certification": "make official endorsement claims",
        "official score": "official claim",
        "score": "measurement claim",
        "scoring": "measurement",
        "answer key": "redacted boundary material",
        "hidden prompt": "redacted boundary material",
    }
    for old, new in replacements.items():
        label = label.replace(old, new)
    return label


def _redact_markdown(text: str) -> str:
    redacted = text
    for old, new in MARKDOWN_REDACTIONS.items():
        redacted = redacted.replace(old, new).replace(old.title(), new)
    return redacted


def build_ai_audit_status_bundle_v1(
    *,
    readiness_gap_advisor_result: dict[str, Any] | None = None,
    consistency_review_result: dict[str, Any] | None = None,
    drift_monitor_result: dict[str, Any] | None = None,
    preflight_review_result: dict[str, Any] | None = None,
    self_governance_surface_card: dict[str, Any] | None = None,
    self_governance_surface_overview: dict[str, Any] | None = None,
    safe_next_step_recommendation_result: dict[str, Any] | None = None,
    dry_trace: dict[str, Any] | None = None,
    canon_refs: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build one redacted, non-executing AI audit status bundle from supplied inputs."""
    readiness = _copy_dict(readiness_gap_advisor_result)
    consistency = _copy_dict(consistency_review_result)
    drift = _copy_dict(drift_monitor_result)
    preflight = _copy_dict(preflight_review_result)
    card = _copy_dict(self_governance_surface_card)
    overview = _copy_dict(self_governance_surface_overview)
    recommendation = _copy_dict(safe_next_step_recommendation_result)
    trace = _copy_dict(dry_trace)

    readiness_status = _readiness_status(readiness, card, overview)
    consistency_status = _consistency_status(consistency, card, overview)
    drift_status = _drift_status(drift, card, overview)
    top_safe_next_step = _preflight_recommendation(preflight, card, recommendation)
    dry_summary = _dry_trace_summary(trace)
    refs = _merge_unique(_as_list(canon_refs), DEFAULT_CANON_REFS)
    forbidden = _merge_unique(
        _as_list(preflight.get("forbidden_next_steps")),
        _as_list(card.get("forbidden_next_steps")),
        _as_list(overview.get("forbidden_next_steps")),
        _as_list(recommendation.get("forbidden_actions")),
        FORBIDDEN_NEXT_STEPS,
    )
    bundle = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "bundle_id": _stable_id(
            "weslr_ai_audit_status_bundle_v1_",
            readiness_status,
            consistency_status,
            drift_status,
            preflight.get("preflight_id", preflight.get("schema_version", "")),
            card.get("card_id", card.get("schema_version", "")),
            overview.get("overview_id", overview.get("schema_version", "")),
            recommendation.get("recommendation_result_id", recommendation.get("result_id", recommendation.get("schema_version", ""))),
            dry_summary,
            refs,
        ),
        "bundle_type": BUNDLE_TYPE,
        "redacted_count_only": True,
        "in_memory_only": True,
        "readiness_status": readiness_status,
        "consistency_status": consistency_status,
        "drift_status": drift_status,
        "preflight_recommendation": _as_text(preflight.get("recommendation") or card.get("preflight_recommendation"), "inspect_supplied_results_only"),
        "top_safe_next_step": {
            "recommendation": top_safe_next_step,
            "reason": _recommendation_reason(recommendation),
            "requires_operator_approval": True,
            "recommendation_does_not_mean_approved": True,
            "implementation_status": "not_implemented_by_bundle",
        },
        "dry_trace_summary": dry_summary,
        "totals": {
            "known_gaps": _count_from(card.get("total_readiness_gaps"), overview.get("total_readiness_gaps"), readiness.get("gap_count"), fallback_items=readiness.get("gap_records")),
            "consistency_issues": _count_from(card.get("total_consistency_issues"), overview.get("total_consistency_issues"), consistency.get("total_issues"), fallback_items=consistency.get("issues")),
            "drift_signals": _count_from(card.get("total_drift_signals"), overview.get("total_drift_signals"), drift.get("signal_count"), (drift.get("boundary_summary") or {}).get("total_signals"), fallback_items=drift.get("signals")),
        },
        "canon_refs": refs,
        "safety_boundaries": deepcopy(SAFETY_BOUNDARIES),
        "forbidden_next_steps": forbidden,
        "execution_status": EXECUTION_STATUS,
        "authorization_status": deepcopy(AUTHORIZATION_STATUS),
        "not_a_runner": True,
        "not_a_scoring_engine": True,
        "not_a_certification": True,
        "not_a_benchmark_result": True,
        "not_truth_promotion": True,
        "no_model_calls": True,
        "no_runtime_behavior_change": True,
        "no_persistence": True,
        "files_written": False,
        "weslr_runtime_state_created": False,
    }
    bundle["validation_status"] = validate_ai_audit_status_bundle_v1(bundle)
    return bundle


def _find_forbidden(value: Any, path: str = "bundle") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text == "validation_status":
                continue
            if key_text in FORBIDDEN_FIELDS:
                issues.append(f"forbidden status bundle field: {nested_path}")
            if key_text in FORBIDDEN_TRUE_MARKERS and nested is True:
                issues.append(f"forbidden status bundle true marker: {nested_path}")
            issues.extend(_find_forbidden(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_find_forbidden(nested, f"{path}[{index}]"))
    return issues


def _recommendation_issues(bundle: dict[str, Any]) -> list[str]:
    recommendations = [
        str(bundle.get("preflight_recommendation", "")),
        str((bundle.get("top_safe_next_step") or {}).get("recommendation", "")),
        str((bundle.get("top_safe_next_step") or {}).get("reason", "")),
    ]
    issues: list[str] = []
    for recommendation in recommendations:
        lowered = recommendation.lower().replace("_", " ").replace("-", " ")
        if any(phrase in lowered for phrase in UNAUTHORIZED_RECOMMENDATION_PHRASES):
            issues.append("status bundle recommendation must not imply runner/scoring/external probing/persistence is authorized")
            break
    return issues


def validate_ai_audit_status_bundle_v1(bundle: dict[str, Any]) -> dict[str, Any]:
    """Validate that a status bundle preserves read-only non-execution boundaries."""
    issues: list[str] = []
    if not isinstance(bundle, dict):
        return {"valid": False, "redacted_count_only": True, "issues": ["bundle must be a dict"]}
    if bundle.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        issues.append("invalid schema_version")
    if bundle.get("bundle_type") != BUNDLE_TYPE:
        issues.append("bundle_type must be ai_audit_read_only_status_bundle")
    if bundle.get("execution_status") != EXECUTION_STATUS:
        issues.append("execution_status must be non_executing_status_bundle_only")
    for key in (
        "redacted_count_only",
        "in_memory_only",
        "not_a_runner",
        "not_a_scoring_engine",
        "not_a_certification",
        "not_a_benchmark_result",
        "not_truth_promotion",
        "no_model_calls",
        "no_runtime_behavior_change",
        "no_persistence",
    ):
        if bundle.get(key) is not True:
            issues.append(f"status bundle must be marked {key}")
    if bundle.get("files_written") is not False:
        issues.append("files_written must be False")
    if bundle.get("weslr_runtime_state_created") is not False:
        issues.append("weslr_runtime_state_created must be False")
    auth = bundle.get("authorization_status") or {}
    if not isinstance(auth, dict):
        issues.append("authorization_status must be a dict")
    else:
        for key, expected in AUTHORIZATION_STATUS.items():
            if auth.get(key) is not expected:
                issues.append(f"authorization_status missing {key}")
    boundaries = bundle.get("safety_boundaries") or {}
    for key in SAFETY_BOUNDARIES:
        if boundaries.get(key) is not True:
            issues.append(f"safety boundary {key} must be True")
    issues.extend(_find_forbidden(bundle))
    issues.extend(_recommendation_issues(bundle))
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
        "files_written": False,
        "runtime_behavior_changed": False,
        "protected_items_copied": False,
        "answer_keys_used": False,
        "hidden_prompts_used": False,
        "official_score_claimed": False,
        "certification_claimed": False,
        "official_benchmark_claimed": False,
        "automatic_approval_authorized": False,
        "automatic_implementation_authorized": False,
    }


def summarize_ai_audit_status_bundle_v1(bundle: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted/count-only status bundle summary."""
    copied = deepcopy(bundle)
    totals = copied.get("totals") or {}
    trace_summary = copied.get("dry_trace_summary") or {}
    summary = {
        "bundle_id": copied.get("bundle_id", "unknown"),
        "readiness_status": deepcopy(copied.get("readiness_status", [])),
        "consistency_status": copied.get("consistency_status", "unknown"),
        "drift_status": copied.get("drift_status", "unknown"),
        "recommendation": (copied.get("top_safe_next_step") or {}).get("recommendation", "inspect_supplied_results_only"),
        "total_known_gaps": int(totals.get("known_gaps", 0) or 0),
        "total_consistency_issues": int(totals.get("consistency_issues", 0) or 0),
        "total_drift_signals": int(totals.get("drift_signals", 0) or 0),
        "total_trace_events": int(trace_summary.get("total_trace_events", 0) or 0),
        "canon_ref_count": len(copied.get("canon_refs", []) or []),
        "forbidden_next_step_count": len(copied.get("forbidden_next_steps", []) or []),
        "validation_status": validate_ai_audit_status_bundle_v1(copied),
        "redacted_count_only": True,
        "raw_outputs_included": False,
    }
    return summary


def render_ai_audit_status_bundle_markdown_v1(bundle: dict[str, Any]) -> str:
    """Render deterministic redacted Markdown for one status bundle."""
    copied = deepcopy(bundle)
    totals = copied.get("totals") or {}
    top_step = copied.get("top_safe_next_step") or {}
    trace = copied.get("dry_trace_summary") or {}
    lines = [
        "# AI Audit Status Bundle",
        "",
        "## Readiness",
        f"- Status: {', '.join(str(item) for item in copied.get('readiness_status', [])) or 'unknown'}",
        f"- Known gaps: {int(totals.get('known_gaps', 0) or 0)}",
        "",
        "## Consistency",
        f"- Status: {copied.get('consistency_status', 'unknown')}",
        f"- Issues: {int(totals.get('consistency_issues', 0) or 0)}",
        "",
        "## Drift",
        f"- Status: {copied.get('drift_status', 'unknown')}",
        f"- Signals: {int(totals.get('drift_signals', 0) or 0)}",
        "",
        "## Preflight",
        f"- Recommendation: {_safe_label(copied.get('preflight_recommendation', 'inspect supplied results only'))}",
        "- Meaning: operator inspection only; no execution authority is granted.",
        "",
        "## Recommendation",
        f"- Top safe next step: {_safe_label(top_step.get('recommendation', 'inspect supplied results only'))}",
        f"- Reason: {_safe_label(top_step.get('reason', 'derived from supplied in-memory status only'))}",
        "- Requires operator approval: true",
        "- Recommendation means approved: false",
        "",
        "## Dry Trace Summary",
        f"- Trace supplied: {str(bool(trace.get('trace_supplied'))).lower()}",
        f"- Events: {int(trace.get('total_trace_events', 0) or 0)}",
        f"- Source layers: {int(trace.get('source_layer_count', 0) or 0)}",
        "- Raw events included: false",
        "",
        "## Canon References",
        *[f"- {_safe_label(ref)}" for ref in copied.get("canon_refs", [])],
        "",
        "## Safety Boundaries",
        "- Read-only: true",
        "- In-memory only: true",
        "- Model calls: false",
        "- Live probing: false",
        "- Runner: false",
        "- Measurement engine: false",
        "- Runtime wiring: false",
        "- UI integration: false",
        "- File writes: false",
        "- Report persistence: false",
        "- Automatic approval: false",
        "- Automatic implementation: false",
        "",
        "## Forbidden Next Steps",
        *[f"- {_safe_label(step)}" for step in copied.get("forbidden_next_steps", [])],
        "",
        "## Non-Execution Disclaimer",
        "This bundle packages redacted AI-audit self-governance status for inspection only. It is not approval, not implementation, not file export, not live probing, not official measurement, and not an official endorsement claim.",
    ]
    return _redact_markdown("\n".join(lines))


def to_ai_audit_status_bundle_json_safe_v1(bundle: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON-serializable, redacted copy of a status bundle without writing files."""
    copied = deepcopy(bundle)
    copied["validation_status"] = validate_ai_audit_status_bundle_v1(copied)
    copied["json_safe_export"] = True
    copied["files_written"] = False
    copied["report_persisted"] = False
    copied["raw_outputs_included"] = False
    copied["raw_trace_events_included"] = False
    return copied
