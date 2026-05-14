"""WESLR AI audit safe next-step recommender helpers V1.

Read-only, in-memory helpers that inspect AI audit self-governance outputs and
recommend safe non-executing review/helper phases.

This module is not a runner, not a scoring engine, not an answer evaluator, not
runtime/chat/voice wiring, not persistence, not implementation, not automatic
approval, and not an external model testing surface. It does not call models,
execute probes, grade answers, use protected items, use answer keys, expose
hidden prompts, claim official scores, certify systems, or write `.weslr`
runtime state.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any


CANDIDATE_SCHEMA_VERSION = "ai_audit_safe_next_step_candidate_v1"
RESULT_SCHEMA_VERSION = "ai_audit_safe_next_step_recommendation_result_v1"
NON_EXECUTING_RECOMMENDATION_STATUS = "non_executing_recommendation_only"

AUTHORIZATION_STATUS = [
    "runner_not_authorized",
    "scoring_not_authorized",
    "external_testing_not_authorized",
    "runtime_wiring_not_authorized",
]

SAFETY_ORDER = {"safe_non_executing": 0, "caution_review_only": 1, "blocked": 2}
PHASE_ORDER = {
    "canon_update": 0,
    "read_only_surface": 1,
    "helper_layer": 2,
    "dry_trace_export": 3,
    "readiness_review": 4,
    "consistency_review": 5,
    "drift_review": 6,
    "design_review_only": 7,
    "blocked_runner": 90,
    "blocked_scoring": 91,
    "blocked_external_testing": 92,
}

FORBIDDEN_ACTIONS = [
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

BASE_SAFE_NEXT_STEPS = [
    "review_ranked_recommendations",
    "select_one_non_executing_phase_for_operator_review",
    "request_explicit_operator_approval_before_any_implementation",
    "keep_runner_scoring_external_testing_runtime_wiring_blocked",
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

UNAUTHORIZED_ACTION_PHRASES = (
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
)

MARKDOWN_REDACTIONS = {
    "answer_key": "[redacted_boundary]",
    "hidden_prompt": "[redacted_boundary]",
    "official_score": "[redacted_boundary]",
    "protected_test_item": "[redacted_boundary]",
    "certification": "official endorsement claim",
    "certified": "officially endorsed",
    "scoring": "automated grading",
    "score": "measurement claim",
}


def _stable_id(prefix: str, *parts: str) -> str:
    return prefix + sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]


def _copy_dict(value: dict[str, Any] | None) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _ids(items: list[dict[str, Any]], key: str) -> list[str]:
    return sorted({str(item.get(key, "")) for item in items if str(item.get(key, "")).strip()})


def _merge_unique(*collections: list[str]) -> list[str]:
    merged: list[str] = []
    for collection in collections:
        for item in collection:
            text = str(item)
            if text and text not in merged:
                merged.append(text)
    return merged


def _candidate(
    *,
    title: str,
    reason: str,
    source_signals: list[str] | None = None,
    linked_gap_ids: list[str] | None = None,
    linked_issue_ids: list[str] | None = None,
    linked_drift_signal_ids: list[str] | None = None,
    safety_level: str,
    phase_type: str,
    priority: int,
    complexity: int = 1,
    forbidden_actions: list[str] | None = None,
) -> dict[str, Any]:
    candidate = {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "recommendation_id": _stable_id("weslr_ai_audit_safe_next_step_v1_", title, reason, safety_level, phase_type),
        "title": title,
        "reason": reason,
        "source_signals": sorted(str(item) for item in (source_signals or [])),
        "linked_gap_ids": sorted(str(item) for item in (linked_gap_ids or [])),
        "linked_issue_ids": sorted(str(item) for item in (linked_issue_ids or [])),
        "linked_drift_signal_ids": sorted(str(item) for item in (linked_drift_signal_ids or [])),
        "safety_level": safety_level,
        "phase_type": phase_type,
        "implementation_status": "recommendation_only",
        "requires_operator_approval": True,
        "recommended_does_not_mean_approved": True,
        "priority": int(priority),
        "implementation_complexity": int(complexity),
        "forbidden_actions": list(forbidden_actions or FORBIDDEN_ACTIONS),
    }
    return candidate


def _extract_preflight(preflight: dict[str, Any], card: dict[str, Any], overview: dict[str, Any]) -> tuple[str, int, int, int]:
    recommendation = str(preflight.get("recommendation") or card.get("preflight_recommendation") or "inspect_supplied_results_only")
    readiness_gaps = int((preflight.get("issue_counts") or {}).get("readiness_gaps", card.get("total_readiness_gaps", overview.get("total_readiness_gaps", 0))) or 0)
    consistency_issues = int((preflight.get("issue_counts") or {}).get("consistency_issues", card.get("total_consistency_issues", overview.get("total_consistency_issues", 0))) or 0)
    drift_signals = int((preflight.get("issue_counts") or {}).get("drift_signals", card.get("total_drift_signals", overview.get("total_drift_signals", 0))) or 0)
    return recommendation, readiness_gaps, consistency_issues, drift_signals


def build_ai_audit_safe_next_step_candidates_v1(
    *,
    self_governance_card: dict[str, Any] | None = None,
    self_governance_overview: dict[str, Any] | None = None,
    preflight_review_result: dict[str, Any] | None = None,
    readiness_gap_advisor_result: dict[str, Any] | None = None,
    consistency_review_result: dict[str, Any] | None = None,
    drift_monitor_result: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build ranked-safe candidate recommendations from supplied in-memory signals."""
    card = _copy_dict(self_governance_card)
    overview = _copy_dict(self_governance_overview)
    preflight = _copy_dict(preflight_review_result)
    readiness = _copy_dict(readiness_gap_advisor_result) or _copy_dict(preflight.get("readiness_result"))
    consistency = _copy_dict(consistency_review_result) or _copy_dict(preflight.get("consistency_result"))
    drift = _copy_dict(drift_monitor_result) or _copy_dict(preflight.get("drift_result"))

    recommendation, readiness_gaps, consistency_issues, drift_signals = _extract_preflight(preflight, card, overview)
    gap_records = list(readiness.get("gap_records", []) or [])
    consistency_items = list(consistency.get("issues", []) or [])
    drift_items = list(drift.get("signals", []) or [])
    gap_ids = _ids(gap_records, "gap_id")
    issue_ids = _ids(consistency_items, "issue_id")
    drift_ids = _ids(drift_items, "signal_id")

    candidates: list[dict[str, Any]] = []
    if card or overview:
        candidates.append(
            _candidate(
                title="Canonize the current AI audit self-governance surface",
                reason="A safe surface exists; the next low-risk step is operator-readable canon/review alignment, not execution.",
                source_signals=["self_governance_surface_present"],
                safety_level="safe_non_executing",
                phase_type="canon_update",
                priority=10,
                complexity=1,
            )
        )
    if recommendation == "proceed_with_review_only" and not (readiness_gaps or consistency_issues or drift_signals):
        candidates.append(
            _candidate(
                title="Design a read-only dry trace export helper proposal",
                reason="Preflight is review-only safe; a dry trace export can reduce operator burden without probing or changing runtime behavior.",
                source_signals=["preflight_review_only_safe"],
                safety_level="safe_non_executing",
                phase_type="dry_trace_export",
                priority=20,
                complexity=2,
            )
        )
    if readiness_gaps or gap_ids:
        candidates.append(
            _candidate(
                title="Review readiness gaps before adding new audit layers",
                reason="Known readiness gaps should be inspected before broader audit machinery is proposed.",
                source_signals=["readiness_gaps_present"],
                linked_gap_ids=gap_ids,
                safety_level="caution_review_only",
                phase_type="readiness_review",
                priority=30,
                complexity=1,
            )
        )
    if consistency_issues or issue_ids:
        candidates.append(
            _candidate(
                title="Review consistency issues in supplied artifacts",
                reason="Artifact mismatches should be resolved in-memory before any future operator review packet is expanded.",
                source_signals=["consistency_issues_present"],
                linked_issue_ids=issue_ids,
                safety_level="caution_review_only",
                phase_type="consistency_review",
                priority=40,
                complexity=1,
            )
        )
    if drift_signals or drift_ids:
        candidates.append(
            _candidate(
                title="Review governance drift warnings",
                reason="Drift warnings indicate boundary language or authorization risk that must stay review-only.",
                source_signals=["drift_signals_present"],
                linked_drift_signal_ids=drift_ids,
                safety_level="caution_review_only",
                phase_type="drift_review",
                priority=50,
                complexity=1,
            )
        )
    candidates.extend(
        [
            _candidate(
                title="Keep probe runner work blocked",
                reason="Runner work is not authorized by this recommendation layer.",
                source_signals=["runner_not_authorized"],
                safety_level="blocked",
                phase_type="blocked_runner",
                priority=900,
            ),
            _candidate(
                title="Keep automated grading work blocked",
                reason="Automated grading or answer evaluation is not authorized by this recommendation layer.",
                source_signals=["scoring_not_authorized"],
                safety_level="blocked",
                phase_type="blocked_scoring",
                priority=910,
            ),
            _candidate(
                title="Keep external testing and runtime wiring blocked",
                reason="Live system probing, model calls, and runtime/chat/voice integration are not authorized.",
                source_signals=["external_testing_not_authorized", "runtime_wiring_not_authorized"],
                safety_level="blocked",
                phase_type="blocked_external_testing",
                priority=920,
            ),
        ]
    )
    return rank_ai_audit_safe_next_step_candidates_v1(candidates)


def rank_ai_audit_safe_next_step_candidates_v1(candidates: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None) -> list[dict[str, Any]]:
    """Rank candidate recommendations deterministically with safety first."""
    copied = deepcopy(list(candidates or []))
    return sorted(
        copied,
        key=lambda item: (
            SAFETY_ORDER.get(str(item.get("safety_level", "blocked")), 9),
            int(item.get("priority", 999)),
            PHASE_ORDER.get(str(item.get("phase_type", "design_review_only")), 50),
            int(item.get("implementation_complexity", 9)),
            str(item.get("recommendation_id", "")),
        ),
    )


def build_ai_audit_safe_next_step_recommendation_result_v1(
    *,
    self_governance_card: dict[str, Any] | None = None,
    self_governance_overview: dict[str, Any] | None = None,
    preflight_review_result: dict[str, Any] | None = None,
    readiness_gap_advisor_result: dict[str, Any] | None = None,
    consistency_review_result: dict[str, Any] | None = None,
    drift_monitor_result: dict[str, Any] | None = None,
    candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a non-executing safe next-step recommendation result."""
    ranked = rank_ai_audit_safe_next_step_candidates_v1(candidates) if candidates is not None else build_ai_audit_safe_next_step_candidates_v1(
        self_governance_card=self_governance_card,
        self_governance_overview=self_governance_overview,
        preflight_review_result=preflight_review_result,
        readiness_gap_advisor_result=readiness_gap_advisor_result,
        consistency_review_result=consistency_review_result,
        drift_monitor_result=drift_monitor_result,
    )
    active = [candidate for candidate in ranked if candidate.get("safety_level") != "blocked"]
    blocked = [candidate for candidate in ranked if candidate.get("safety_level") == "blocked"]
    top = deepcopy(active[0] if active else (ranked[0] if ranked else {}))
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "result_id": _stable_id("weslr_ai_audit_safe_next_step_result_v1_", *[candidate.get("recommendation_id", "") for candidate in ranked]),
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_RECOMMENDATION_STATUS,
        "top_recommendation": top,
        "ranked_recommendations": ranked,
        "blocked_recommendations": blocked,
        "safe_next_steps": _merge_unique(BASE_SAFE_NEXT_STEPS, [candidate.get("title", "") for candidate in active]),
        "forbidden_next_steps": list(FORBIDDEN_ACTIONS),
        "explanation": "Recommendations are safe to propose for operator review only; recommended does not mean approved, is not approved, and is not implemented.",
        "authorization_status": list(AUTHORIZATION_STATUS),
        "safety_boundaries": {
            "execution_authorized": False,
            "runner_authorized": False,
            "scoring_authorized": False,
            "external_testing_authorized": False,
            "runtime_wiring_authorized": False,
            "automatic_approval_authorized": False,
            "truth_promotion_authorized": False,
            "automatic_implementation_authorized": False,
            "persistence_authorized": False,
            "in_memory_only": True,
        },
        "recommended_does_not_mean_approved": True,
        "not_implementation": True,
        "not_a_runner": True,
        "not_a_scoring_engine": True,
        "not_a_certification": True,
        "not_a_benchmark_result": True,
        "not_truth_promotion": True,
        "no_model_calls": True,
        "no_runtime_behavior_change": True,
        "no_persistence": True,
    }
    result["validation_status"] = validate_ai_audit_safe_next_step_recommendation_result_v1(result)
    return result


def _find_forbidden(value: Any, path: str = "result") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text == "validation_status":
                continue
            if key_text in FORBIDDEN_FIELDS:
                issues.append(f"forbidden recommendation field: {nested_path}")
            if key_text in FORBIDDEN_TRUE_MARKERS and nested is True:
                issues.append(f"forbidden recommendation true marker: {nested_path}")
            issues.extend(_find_forbidden(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_find_forbidden(nested, f"{path}[{index}]"))
    return issues


def _authorization_phrase_issues(result: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    candidates = list(result.get("ranked_recommendations", []) or [])
    if isinstance(result.get("top_recommendation"), dict):
        candidates.append(result["top_recommendation"])
    for candidate in candidates:
        safety = str(candidate.get("safety_level", ""))
        if safety == "blocked":
            continue
        text = " ".join(str(candidate.get(key, "")) for key in ("title", "reason", "phase_type"))
        lowered = text.lower().replace("_", " ").replace("-", " ")
        if any(phrase in lowered for phrase in UNAUTHORIZED_ACTION_PHRASES):
            issues.append("recommendation must not imply runner/scoring/external probing is authorized")
            break
    return issues


def validate_ai_audit_safe_next_step_recommendation_result_v1(result: dict[str, Any]) -> dict[str, Any]:
    """Validate safe next-step recommendations preserve non-executing boundaries."""
    issues: list[str] = []
    if not isinstance(result, dict):
        return {"valid": False, "redacted_count_only": True, "issues": ["recommendation result must be a dict"]}
    if result.get("schema_version") != RESULT_SCHEMA_VERSION:
        issues.append("invalid schema_version")
    for key in (
        "redacted_count_only",
        "in_memory_only",
        "recommended_does_not_mean_approved",
        "not_implementation",
        "not_a_runner",
        "not_a_scoring_engine",
        "not_a_certification",
        "not_a_benchmark_result",
        "not_truth_promotion",
        "no_model_calls",
        "no_runtime_behavior_change",
        "no_persistence",
    ):
        if result.get(key) is not True:
            issues.append(f"recommendation result must be marked {key}")
    if result.get("execution_status") != NON_EXECUTING_RECOMMENDATION_STATUS:
        issues.append("recommendation execution_status must be non_executing_recommendation_only")
    auth = set(result.get("authorization_status") or [])
    for required in AUTHORIZATION_STATUS:
        if required not in auth:
            issues.append(f"authorization_status missing {required}")
    safety = result.get("safety_boundaries") or {}
    for key in (
        "execution_authorized",
        "runner_authorized",
        "scoring_authorized",
        "external_testing_authorized",
        "runtime_wiring_authorized",
        "automatic_approval_authorized",
        "truth_promotion_authorized",
        "automatic_implementation_authorized",
        "persistence_authorized",
    ):
        if safety.get(key) is not False:
            issues.append(f"safety boundary {key} must be False")
    for candidate in result.get("ranked_recommendations", []) or []:
        if candidate.get("implementation_status") != "recommendation_only":
            issues.append("candidate implementation_status must be recommendation_only")
        if candidate.get("requires_operator_approval") is not True:
            issues.append("candidate requires_operator_approval must be true")
        if candidate.get("safety_level") not in {"safe_non_executing", "caution_review_only", "blocked"}:
            issues.append("candidate has invalid safety_level")
    issues.extend(_find_forbidden(result))
    issues.extend(_authorization_phrase_issues(result))
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


def render_ai_audit_safe_next_step_recommendations_markdown_v1(result: dict[str, Any]) -> str:
    """Render safe Markdown for recommendation review without executable instructions."""
    safe = deepcopy(result)
    top = safe.get("top_recommendation") or {}
    lines = [
        "# AI Audit Safe Next-Step Recommendations",
        "",
        "## Top Recommendation",
        f"- {top.get('title', 'No active recommendation')}",
        "- Status: recommendation only; not approved; not implemented.",
        "",
        "## Why",
        f"- {top.get('reason', safe.get('explanation', 'Review supplied recommendations only.'))}",
        "",
        "## Safe Next Steps",
        *[f"- {step}" for step in safe.get("safe_next_steps", [])],
        "",
        "## Blocked / Forbidden Steps",
        *[f"- {step}" for step in safe.get("forbidden_next_steps", [])],
        "",
        "## Authorization Boundaries",
        "- Runner authorized: false",
        "- Automated grading authorized: false",
        "- External testing authorized: false",
        "- Runtime wiring authorized: false",
        "- Automatic approval authorized: false",
        "- Automatic implementation authorized: false",
        "- Persistence authorized: false",
    ]
    return _redact_markdown("\n".join(lines))
