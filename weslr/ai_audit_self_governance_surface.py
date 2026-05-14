"""WESLR AI audit self-governance surface helpers V1.

Read-only, in-memory helpers that present operator-readable status for the
existing AI audit readiness, consistency, drift, and preflight layers.

This module is not a runner, not a scoring engine, not an answer evaluator, not
runtime/chat/voice wiring, not persistence, and not an external model testing
surface. It does not call models, execute probes, grade answers, use protected
items, use answer keys, expose hidden prompts, claim official scores, certify
systems, or write `.weslr` runtime state.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any


SURFACE_CARD_SCHEMA_VERSION = "ai_audit_self_governance_card_v1"
SURFACE_OVERVIEW_SCHEMA_VERSION = "ai_audit_self_governance_overview_v1"
NON_EXECUTING_SURFACE_STATUS = "non_executing_surface_only"

SEVERITY_RANK = {"none": 0, "info": 1, "low": 2, "medium": 3, "high": 4}

AUTHORIZATION_STATUS = [
    "runner_not_authorized",
    "scoring_not_authorized",
    "external_testing_not_authorized",
    "runtime_wiring_not_authorized",
]

SAFE_NEXT_STEPS = [
    "review_self_governance_surface",
    "inspect_readiness_gaps_in_memory_only",
    "inspect_consistency_issues_in_memory_only",
    "inspect_drift_signals_in_memory_only",
    "prepare_operator_review_question_only",
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
]

FORBIDDEN_FIELDS = {
    "answer",
    "answers",
    "answer_key",
    "answer_keys",
    "model_output",
    "model_outputs",
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
    "protected_prompt",
    "hidden_prompt",
}

FORBIDDEN_TRUE_MARKERS = {
    "executable",
    "runnable",
    "runner_created",
    "execution_allowed",
    "scoring_engine",
    "automated_grading",
    "answer_evaluation",
    "external_model_calls",
    "external_testing_authorized",
    "runtime_authorized",
    "runtime_behavior_change",
    "runtime_behavior_changed",
    "persistence_authorized",
    "report_persistence",
    "automatic_approval",
    "auto_approval",
    "automatic_truth_promotion",
    "truth_promotion",
    "protected_item_present",
    "answer_key_present",
    "hidden_prompt_present",
    "official_score_claimed",
    "certification_claimed",
    "official_benchmark_claimed",
}

FORBIDDEN_RECOMMENDATION_PHRASES = (
    "execute",
    "runner",
    "run probes",
    "probe live",
    "live probing",
    "external probing",
    "external model",
    "model call",
    "scoring",
    "score",
    "grade answers",
    "answer evaluation",
)

MARKDOWN_REDACTIONS = {
    "answer_key": "[redacted_boundary]",
    "answer keys": "redacted boundary materials",
    "hidden_prompt": "[redacted_boundary]",
    "hidden prompts": "redacted boundary materials",
    "official_score": "[redacted_boundary]",
    "official score": "official claim",
    "certification": "official claim",
    "certified": "officially claimed",
    "protected_test_item": "[redacted_boundary]",
    "protected material": "redacted boundary material",
}


def _stable_id(prefix: str, *parts: str) -> str:
    return prefix + sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]


def _copy_dict(value: dict[str, Any] | None) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return deepcopy(list(value))
    return [deepcopy(value)]


def _count_by_severity(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        severity = str(item.get("severity", "info"))
        counts[severity] = counts.get(severity, 0) + 1
    return dict(sorted(counts.items()))


def _highest_severity_from_counts(*counts_list: dict[str, int]) -> str:
    severities: list[str] = []
    for counts in counts_list:
        severities.extend([severity for severity, count in counts.items() if int(count or 0) > 0])
    if not severities:
        return "none"
    return max(severities, key=lambda severity: SEVERITY_RANK.get(severity, 0))


def _merge_unique(*collections: list[str]) -> list[str]:
    merged: list[str] = []
    for collection in collections:
        for item in collection:
            text = str(item)
            if text and text not in merged:
                merged.append(text)
    return merged


def _readiness_status(readiness: dict[str, Any]) -> list[str]:
    report = readiness.get("readiness_report") or {}
    status = report.get("readiness_status")
    if isinstance(status, list):
        return [str(item) for item in status]
    if isinstance(status, str) and status:
        return [status]
    if readiness.get("schema_version"):
        return [str(report.get("readiness_signal") or "readiness_result_supplied")]
    return ["readiness_not_supplied"]


def _readiness_gap_count(readiness: dict[str, Any]) -> int:
    if "gap_count" in readiness:
        return int(readiness.get("gap_count") or 0)
    return len(readiness.get("gap_records", []) or [])


def _readiness_severity_counts(readiness: dict[str, Any]) -> dict[str, int]:
    return _count_by_severity(list(readiness.get("gap_records", []) or []))


def _consistency_status(consistency: dict[str, Any]) -> str:
    if consistency.get("consistency_status"):
        return str(consistency["consistency_status"])
    if consistency.get("schema_version"):
        return "consistency_result_supplied"
    return "consistency_not_supplied"


def _consistency_issue_count(consistency: dict[str, Any]) -> int:
    if "total_issues" in consistency:
        return int(consistency.get("total_issues") or 0)
    return len(consistency.get("issues", []) or [])


def _consistency_severity_counts(consistency: dict[str, Any]) -> dict[str, int]:
    if isinstance(consistency.get("issue_counts_by_severity"), dict):
        return {str(key): int(value) for key, value in consistency["issue_counts_by_severity"].items()}
    return _count_by_severity(list(consistency.get("issues", []) or []))


def _drift_status(drift: dict[str, Any]) -> str:
    summary = drift.get("boundary_summary") or {}
    if summary.get("drift_status"):
        return str(summary["drift_status"])
    if drift.get("schema_version"):
        return "drift_result_supplied"
    return "drift_not_supplied"


def _drift_signal_count(drift: dict[str, Any]) -> int:
    if "signal_count" in drift:
        return int(drift.get("signal_count") or 0)
    summary = drift.get("boundary_summary") or {}
    if "total_signals" in summary:
        return int(summary.get("total_signals") or 0)
    return len(drift.get("signals", []) or [])


def _drift_severity_counts(drift: dict[str, Any]) -> dict[str, int]:
    summary = drift.get("boundary_summary") or {}
    if isinstance(summary.get("counts_by_severity"), dict):
        return {str(key): int(value) for key, value in summary["counts_by_severity"].items()}
    return _count_by_severity(list(drift.get("signals", []) or []))


def _preflight_recommendation(preflight: dict[str, Any]) -> str:
    if preflight.get("recommendation"):
        return str(preflight["recommendation"])
    if preflight.get("schema_version"):
        return "review_supplied_preflight_result_only"
    return "inspect_supplied_results_only"


def build_ai_audit_self_governance_card_v1(
    *,
    readiness_gap_advisor_result: dict[str, Any] | None = None,
    consistency_review_result: dict[str, Any] | None = None,
    drift_monitor_result: dict[str, Any] | None = None,
    preflight_review_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one redacted, non-executing self-governance surface card."""
    readiness = _copy_dict(readiness_gap_advisor_result)
    consistency = _copy_dict(consistency_review_result)
    drift = _copy_dict(drift_monitor_result)
    preflight = _copy_dict(preflight_review_result)

    readiness_counts = _readiness_severity_counts(readiness)
    consistency_counts = _consistency_severity_counts(consistency)
    drift_counts = _drift_severity_counts(drift)
    safe_next_steps = _merge_unique(
        list(preflight.get("safe_next_steps", []) or []),
        list((readiness.get("readiness_report") or {}).get("safe_next_steps", []) or []),
        list((drift.get("boundary_summary") or {}).get("safe_next_steps", []) or []),
        SAFE_NEXT_STEPS,
    )
    forbidden_next_steps = _merge_unique(
        list(preflight.get("forbidden_next_steps", []) or []),
        list((readiness.get("readiness_report") or {}).get("forbidden_next_steps", []) or []),
        list((drift.get("boundary_summary") or {}).get("forbidden_next_steps", []) or []),
        FORBIDDEN_NEXT_STEPS,
    )
    recommendation = _preflight_recommendation(preflight)
    card = {
        "schema_version": SURFACE_CARD_SCHEMA_VERSION,
        "card_id": _stable_id(
            "weslr_ai_audit_self_governance_card_v1_",
            readiness.get("schema_version", ""),
            consistency.get("review_id", consistency.get("schema_version", "")),
            drift.get("monitor_id", drift.get("schema_version", "")),
            preflight.get("preflight_id", preflight.get("schema_version", "")),
            recommendation,
        ),
        "redacted_count_only": True,
        "in_memory_only": True,
        "readiness_status": _readiness_status(readiness),
        "consistency_status": _consistency_status(consistency),
        "drift_status": _drift_status(drift),
        "preflight_recommendation": recommendation,
        "total_readiness_gaps": _readiness_gap_count(readiness),
        "total_consistency_issues": _consistency_issue_count(consistency),
        "total_drift_signals": _drift_signal_count(drift),
        "highest_severity": _highest_severity_from_counts(readiness_counts, consistency_counts, drift_counts),
        "safe_next_steps": safe_next_steps,
        "forbidden_next_steps": forbidden_next_steps,
        "execution_status": NON_EXECUTING_SURFACE_STATUS,
        "authorization_status": list(AUTHORIZATION_STATUS),
        "safety_boundaries": {
            "execution_authorized": False,
            "runner_authorized": False,
            "scoring_authorized": False,
            "external_testing_authorized": False,
            "runtime_wiring_authorized": False,
            "automatic_approval_authorized": False,
            "truth_promotion_authorized": False,
            "persistence_authorized": False,
            "in_memory_only": True,
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
    card["validation_status"] = validate_ai_audit_self_governance_surface_v1(card)
    return card


def _card_from_item(item: dict[str, Any]) -> dict[str, Any]:
    copied = deepcopy(item)
    if copied.get("schema_version") == SURFACE_CARD_SCHEMA_VERSION:
        return copied
    if copied.get("schema_version") == "ai_audit_preflight_review_v1":
        return build_ai_audit_self_governance_card_v1(
            readiness_gap_advisor_result=copied.get("readiness_result"),
            consistency_review_result=copied.get("consistency_result"),
            drift_monitor_result=copied.get("drift_result"),
            preflight_review_result=copied,
        )
    return build_ai_audit_self_governance_card_v1(preflight_review_result=copied)


def build_ai_audit_self_governance_overview_v1(cards_or_results: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None) -> dict[str, Any]:
    """Combine supplied cards/results into one deterministic overview."""
    cards = sorted((_card_from_item(item) for item in _as_list(cards_or_results)), key=lambda item: str(item.get("card_id", "")))
    readiness_states = sorted({state for card in cards for state in card.get("readiness_status", [])})
    consistency_states = sorted({str(card.get("consistency_status", "unknown")) for card in cards})
    drift_states = sorted({str(card.get("drift_status", "unknown")) for card in cards})
    blockers = sorted(
        {
            f"{card['card_id']}: {card['highest_severity']} severity review required"
            for card in cards
            if SEVERITY_RANK.get(str(card.get("highest_severity", "none")), 0) >= SEVERITY_RANK["medium"]
        }
    )
    warnings = sorted(
        {
            f"{card['card_id']}: {card['highest_severity']} severity warning"
            for card in cards
            if 0 < SEVERITY_RANK.get(str(card.get("highest_severity", "none")), 0) < SEVERITY_RANK["medium"]
        }
    )
    overview = {
        "schema_version": SURFACE_OVERVIEW_SCHEMA_VERSION,
        "overview_id": _stable_id("weslr_ai_audit_self_governance_overview_v1_", *[card.get("card_id", "") for card in cards]),
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_SURFACE_STATUS,
        "total_cards": len(cards),
        "readiness_states": readiness_states,
        "consistency_states": consistency_states,
        "drift_states": drift_states,
        "total_readiness_gaps": sum(int(card.get("total_readiness_gaps", 0)) for card in cards),
        "total_consistency_issues": sum(int(card.get("total_consistency_issues", 0)) for card in cards),
        "total_drift_signals": sum(int(card.get("total_drift_signals", 0)) for card in cards),
        "highest_severity": _highest_severity_from_counts({str(card.get("highest_severity", "none")): 1 for card in cards}),
        "blockers": blockers,
        "warnings": warnings,
        "cards": cards,
        "safe_next_steps": _merge_unique(*[list(card.get("safe_next_steps", [])) for card in cards], SAFE_NEXT_STEPS),
        "forbidden_next_steps": _merge_unique(*[list(card.get("forbidden_next_steps", [])) for card in cards], FORBIDDEN_NEXT_STEPS),
        "authorization_status": list(AUTHORIZATION_STATUS),
        "not_a_runner": True,
        "not_a_scoring_engine": True,
        "not_a_certification": True,
        "not_a_benchmark_result": True,
        "not_truth_promotion": True,
        "no_model_calls": True,
        "no_runtime_behavior_change": True,
        "no_persistence": True,
    }
    overview["validation_status"] = validate_ai_audit_self_governance_surface_v1(overview)
    return overview


def _find_forbidden(value: Any, path: str = "surface") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text in {"validation_status"}:
                continue
            if key_text in FORBIDDEN_FIELDS:
                issues.append(f"forbidden surface field: {nested_path}")
            if key_text in FORBIDDEN_TRUE_MARKERS and nested is True:
                issues.append(f"forbidden surface true marker: {nested_path}")
            issues.extend(_find_forbidden(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_find_forbidden(nested, f"{path}[{index}]"))
    return issues


def _recommendation_issues(surface: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    recommendations = []
    if surface.get("preflight_recommendation"):
        recommendations.append(str(surface["preflight_recommendation"]))
    for step in surface.get("safe_next_steps", []) or []:
        recommendations.append(str(step))
    for card in surface.get("cards", []) or []:
        recommendations.extend(str(step) for step in card.get("safe_next_steps", []) or [])
        if card.get("preflight_recommendation"):
            recommendations.append(str(card["preflight_recommendation"]))
    for recommendation in recommendations:
        lowered = recommendation.lower().replace("_", " ").replace("-", " ")
        if any(phrase in lowered for phrase in FORBIDDEN_RECOMMENDATION_PHRASES):
            issues.append("surface recommendation must not imply execution/scoring/external probing")
            break
    return issues


def validate_ai_audit_self_governance_surface_v1(surface: dict[str, Any]) -> dict[str, Any]:
    """Validate that a self-governance surface preserves non-executing boundaries."""
    issues: list[str] = []
    if not isinstance(surface, dict):
        return {"valid": False, "redacted_count_only": True, "issues": ["surface must be a dict"]}
    if surface.get("schema_version") not in {SURFACE_CARD_SCHEMA_VERSION, SURFACE_OVERVIEW_SCHEMA_VERSION}:
        issues.append("invalid schema_version")
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
        if surface.get(key) is not True:
            issues.append(f"surface must be marked {key}")
    if surface.get("execution_status") != NON_EXECUTING_SURFACE_STATUS:
        issues.append("surface execution_status must be non_executing_surface_only")
    auth = set(surface.get("authorization_status") or [])
    for required in AUTHORIZATION_STATUS:
        if required not in auth:
            issues.append(f"authorization_status missing {required}")
    safety = surface.get("safety_boundaries") or {}
    for key in (
        "execution_authorized",
        "runner_authorized",
        "scoring_authorized",
        "external_testing_authorized",
        "runtime_wiring_authorized",
        "automatic_approval_authorized",
        "truth_promotion_authorized",
        "persistence_authorized",
    ):
        if key in safety and safety.get(key) is not False:
            issues.append(f"safety boundary {key} must be False")
    issues.extend(_find_forbidden(surface))
    issues.extend(_recommendation_issues(surface))
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


def _safe_label(item: str) -> str:
    label = str(item).replace("_", " ")
    replacements = {
        "add scoring engine": "add automated grading or measurement engine",
        "add answer evaluation engine": "add answer evaluation engine",
        "claim official benchmark result": "make official benchmark claims",
        "claim certification": "make official endorsement claims",
        "official score": "official claim",
        "score": "measurement claim",
        "certification": "official endorsement",
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


def render_ai_audit_self_governance_surface_markdown_v1(card_or_overview: dict[str, Any]) -> str:
    """Render safe, deterministic Markdown for an operator-facing surface."""
    surface = deepcopy(card_or_overview)
    if surface.get("schema_version") == SURFACE_OVERVIEW_SCHEMA_VERSION:
        readiness = ", ".join(surface.get("readiness_states", [])) or "unknown"
        consistency = ", ".join(surface.get("consistency_states", [])) or "unknown"
        drift = ", ".join(surface.get("drift_states", [])) or "unknown"
        recommendation = "inspect supplied cards only"
        totals = (
            int(surface.get("total_readiness_gaps", 0)),
            int(surface.get("total_consistency_issues", 0)),
            int(surface.get("total_drift_signals", 0)),
        )
    else:
        readiness = ", ".join(surface.get("readiness_status", [])) or "unknown"
        consistency = str(surface.get("consistency_status", "unknown"))
        drift = str(surface.get("drift_status", "unknown"))
        recommendation = str(surface.get("preflight_recommendation", "inspect supplied results only"))
        totals = (
            int(surface.get("total_readiness_gaps", 0)),
            int(surface.get("total_consistency_issues", 0)),
            int(surface.get("total_drift_signals", 0)),
        )
    lines = [
        "# AI Audit Self-Governance Surface",
        "",
        "## Readiness",
        f"- Status: {readiness}",
        f"- Gaps: {totals[0]}",
        "",
        "## Consistency",
        f"- Status: {consistency}",
        f"- Issues: {totals[1]}",
        "",
        "## Drift",
        f"- Status: {drift}",
        f"- Signals: {totals[2]}",
        "",
        "## Preflight",
        f"- Recommendation: {_safe_label(recommendation)}",
        "- Meaning: non-executing review/helper work only.",
        "",
        "## Safe Next Steps",
        *[f"- {_safe_label(step)}" for step in surface.get("safe_next_steps", [])],
        "",
        "## Forbidden Next Steps",
        *[f"- {_safe_label(step)}" for step in surface.get("forbidden_next_steps", [])],
        "",
        "## Boundaries",
        "- Runner authorized: false",
        "- Automated grading authorized: false",
        "- External testing authorized: false",
        "- Runtime wiring authorized: false",
        "- Report persistence authorized: false",
        "- Official claims authorized: false",
    ]
    return _redact_markdown("\n".join(lines))
