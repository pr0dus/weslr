"""WESLR AI audit readiness + gap advisor helpers V1.

Safe, in-memory helpers for inspecting the existing WESLR AI audit foundation
and producing count-only coverage summaries, non-executing gap records,
readiness recommendations, and governed proposal candidates.

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

from weslr.ai_audit_findings import summarize_ai_audit_findings_v1, validate_ai_audit_finding_v1
from weslr.ai_audit_plan import summarize_ai_audit_plan_v1, validate_ai_audit_plan_v1
from weslr.ai_audit_probe_inventory import (
    REQUIRED_AI_AUDIT_SYNTHETIC_PROBE_CATEGORIES,
    load_ai_audit_synthetic_probe_inventory_v1,
    summarize_ai_audit_synthetic_probe_inventory_v1,
    validate_ai_audit_synthetic_probe_inventory_v1,
)
from weslr.ai_audit_report import validate_ai_audit_redacted_report_v1
from weslr.ai_audit_review_packet import validate_ai_audit_review_packet_v1


ADVISOR_RESULT_SCHEMA_VERSION = "ai_audit_readiness_gap_advisor_result_v1"
COVERAGE_SCHEMA_VERSION = "ai_audit_coverage_summary_v1"
GAP_SCHEMA_VERSION = "ai_audit_readiness_gap_v1"
READINESS_SCHEMA_VERSION = "ai_audit_readiness_report_v1"
PROPOSAL_SCHEMA_VERSION = "ai_audit_next_proposal_candidate_v1"

NON_EXECUTING_GAP_STATUS = "non_executing_gap_only"
NON_EXECUTING_ADVISOR_STATUS = "non_executing_advisor_only"
PROPOSAL_ONLY_STATUS = "proposal_only"

GAP_SEVERITIES = {"info", "low", "medium", "high"}

FORBIDDEN_ADVISOR_FIELDS = {
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

FORBIDDEN_ADVISOR_TRUE_FLAGS = {
    "executable",
    "runnable",
    "runner_created",
    "execution_allowed",
    "external_model_calls",
    "external_testing_authorized",
    "live_system_testing",
    "real_system_testing",
    "answer_evaluation",
    "automated_grading",
    "official_score_claimed",
    "certification_claimed",
    "official_benchmark_claimed",
    "clinical_validity_claimed",
    "protected_item_present",
    "answer_key_present",
    "hidden_prompt_present",
    "runtime_behavior_change",
    "report_persistence",
}


EXPECTED_SAFE_NEXT_STEPS = [
    "inspect_gap_report",
    "add_missing_probe_category_proposal_only",
    "add_self_consistency_review_helper_proposal_only",
    "add_drift_monitor_helper_proposal_only",
    "canonize_readiness_gap_advisor_after_operator_review",
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
]


def _stable_id(prefix: str, *parts: str) -> str:
    seed = "|".join(str(part) for part in parts)
    return prefix + sha256(seed.encode("utf-8")).hexdigest()[:12]


def _as_list(value: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None) -> list[dict[str, Any]]:
    return deepcopy(list(value or []))


def _inventory_claim_categories(inventory: list[dict[str, Any]]) -> list[str]:
    return sorted({str(probe.get("claim_category", "unknown")) for probe in inventory})


def _inventory_probe_categories(inventory: list[dict[str, Any]]) -> list[str]:
    return sorted({str(probe.get("probe_category", "unknown")) for probe in inventory})


def _selected_probe_ids_from_plans(plans: list[dict[str, Any]]) -> list[str]:
    selected: list[str] = []
    for plan in plans:
        if isinstance(plan, dict):
            selected.extend(str(probe_id) for probe_id in plan.get("selected_probe_ids", []) if str(probe_id).strip())
    return sorted(set(selected))


def _planned_categories(plans: list[dict[str, Any]]) -> list[str]:
    categories: set[str] = set()
    for plan in plans:
        if isinstance(plan, dict):
            categories.update(str(category) for category in plan.get("probe_categories", []) if str(category).strip())
    return sorted(categories)


def _planned_claim_categories(plans: list[dict[str, Any]]) -> list[str]:
    categories: set[str] = set()
    for plan in plans:
        if isinstance(plan, dict):
            categories.update(str(category) for category in plan.get("claim_categories", []) if str(category).strip())
    return sorted(categories)


def _finding_probe_ids(findings: list[dict[str, Any]]) -> list[str]:
    return sorted({str(finding.get("probe_id", "")) for finding in findings if str(finding.get("probe_id", "")).strip()})


def _packet_ids(packets: list[dict[str, Any]]) -> list[str]:
    return sorted({str(packet.get("packet_id", "")) for packet in packets if str(packet.get("packet_id", "")).strip()})


def _report_packet_ids(reports: list[dict[str, Any]]) -> list[str]:
    return sorted({str(report.get("packet_id", "")) for report in reports if str(report.get("packet_id", "")).strip()})


def _default_safety_boundaries() -> dict[str, Any]:
    return {
        "execution_authorized": False,
        "runner_authorized": False,
        "scoring_authorized": False,
        "external_testing_authorized": False,
        "model_calls_authorized": False,
        "runtime_chat_voice_changes_authorized": False,
        "persistence_authorized": False,
        "protected_items_allowed": False,
        "answer_keys_allowed": False,
        "hidden_prompts_allowed": False,
        "official_claims_allowed": False,
        "proposal_requires_operator_approval": True,
        "in_memory_only": True,
    }


def summarize_ai_audit_coverage_v1(
    *,
    inventory: list[dict[str, Any]] | None = None,
    plans: list[dict[str, Any]] | None = None,
    findings: list[dict[str, Any]] | None = None,
    packets: list[dict[str, Any]] | None = None,
    reports: list[dict[str, Any]] | None = None,
    expected_probe_categories: list[str] | set[str] | tuple[str, ...] | None = None,
    expected_claim_categories: list[str] | set[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Return a deterministic count-only AI audit coverage summary.

    The summary inspects provided in-memory structures only. It does not execute
    probes, call models, score targets, persist reports, or claim target truth.
    """
    probes = load_ai_audit_synthetic_probe_inventory_v1() if inventory is None else deepcopy(list(inventory))
    plan_items = _as_list(plans)
    finding_items = _as_list(findings)
    packet_items = _as_list(packets)
    report_items = _as_list(reports)

    inventory_summary = summarize_ai_audit_synthetic_probe_inventory_v1(probes)
    categories = _inventory_probe_categories(probes)
    claim_categories = _inventory_claim_categories(probes)
    expected_categories = sorted(str(item) for item in (expected_probe_categories or REQUIRED_AI_AUDIT_SYNTHETIC_PROBE_CATEGORIES))
    if expected_claim_categories is None:
        canonical_claims = _inventory_claim_categories(load_ai_audit_synthetic_probe_inventory_v1())
        expected_claims = canonical_claims
    else:
        expected_claims = sorted(str(item) for item in expected_claim_categories)

    selected_probe_ids = _selected_probe_ids_from_plans(plan_items)
    planned_categories = _planned_categories(plan_items)
    planned_claim_categories = _planned_claim_categories(plan_items)
    finding_probe_ids = _finding_probe_ids(finding_items)
    packet_ids = _packet_ids(packet_items)
    report_packet_ids = _report_packet_ids(report_items)

    missing_categories = sorted(set(expected_categories) - set(categories))
    missing_claim_categories = sorted(set(expected_claims) - set(claim_categories))

    return {
        "schema_version": COVERAGE_SCHEMA_VERSION,
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_ADVISOR_STATUS,
        "total_probes": len(probes),
        "categories_covered": categories,
        "category_count": len(categories),
        "claim_categories_covered": claim_categories,
        "claim_category_count": len(claim_categories),
        "missing_expected_categories": missing_categories,
        "missing_expected_category_count": len(missing_categories),
        "missing_expected_claim_categories": missing_claim_categories,
        "missing_expected_claim_category_count": len(missing_claim_categories),
        "inventory_summary": inventory_summary,
        "plan_coverage": {
            "redacted_count_only": True,
            "plan_count": len(plan_items),
            "selected_probe_count": len(selected_probe_ids),
            "selected_probe_ids": selected_probe_ids,
            "planned_categories": planned_categories,
            "planned_category_count": len(planned_categories),
            "planned_claim_categories": planned_claim_categories,
            "planned_claim_category_count": len(planned_claim_categories),
        },
        "finding_coverage": {
            "redacted_count_only": True,
            "finding_count": len(finding_items),
            "finding_probe_count": len(finding_probe_ids),
            "finding_probe_ids": finding_probe_ids,
        },
        "review_coverage": {
            "redacted_count_only": True,
            "packet_count": len(packet_items),
            "report_count": len(report_items),
            "packet_ids": packet_ids,
            "reported_packet_ids": report_packet_ids,
            "packet_without_report_count": len(set(packet_ids) - set(report_packet_ids)) if report_items else 0,
        },
        "no_scores": True,
        "no_model_calls": True,
        "no_execution": True,
        "not_certification": True,
    }


def _gap(
    *,
    gap_type: str,
    severity: str,
    explanation: str,
    recommended_next_action: str,
    related_category: str = "",
    related_claim_category: str = "",
    related_probe_id: str = "",
    related_plan_id: str = "",
    related_packet_id: str = "",
) -> dict[str, Any]:
    safe_severity = severity if severity in GAP_SEVERITIES else "info"
    related = "|".join([gap_type, related_category, related_claim_category, related_probe_id, related_plan_id, related_packet_id, explanation])
    return {
        "schema_version": GAP_SCHEMA_VERSION,
        "gap_id": _stable_id("weslr_ai_audit_gap_v1_", related),
        "gap_type": gap_type,
        "severity": safe_severity,
        "related_category": related_category,
        "related_claim_category": related_claim_category,
        "related_probe_id": related_probe_id,
        "related_plan_id": related_plan_id,
        "related_packet_id": related_packet_id,
        "explanation": explanation,
        "recommended_next_action": recommended_next_action,
        "execution_status": NON_EXECUTING_GAP_STATUS,
        "automatic_fix": False,
        "truth_promotion": False,
        "runtime_behavior_change": False,
    }


def detect_ai_audit_readiness_gaps_v1(
    *,
    inventory: list[dict[str, Any]] | None = None,
    plans: list[dict[str, Any]] | None = None,
    findings: list[dict[str, Any]] | None = None,
    packets: list[dict[str, Any]] | None = None,
    reports: list[dict[str, Any]] | None = None,
    expected_probe_categories: list[str] | set[str] | tuple[str, ...] | None = None,
    expected_claim_categories: list[str] | set[str] | tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    """Detect non-executing readiness gaps from safe in-memory audit artifacts."""
    probes = load_ai_audit_synthetic_probe_inventory_v1() if inventory is None else deepcopy(list(inventory))
    plan_items = _as_list(plans)
    finding_items = _as_list(findings)
    packet_items = _as_list(packets)
    report_items = _as_list(reports)
    coverage = summarize_ai_audit_coverage_v1(
        inventory=probes,
        plans=plan_items,
        findings=finding_items,
        packets=packet_items,
        reports=report_items,
        expected_probe_categories=expected_probe_categories,
        expected_claim_categories=expected_claim_categories,
    )

    gaps: list[dict[str, Any]] = []
    for category in coverage["missing_expected_categories"]:
        gaps.append(
            _gap(
                gap_type="category_missing",
                severity="medium",
                related_category=category,
                explanation=f"Expected AI audit probe category is not represented: {category}.",
                recommended_next_action="propose_missing_probe_category_only",
            )
        )
    for claim_category in coverage["missing_expected_claim_categories"]:
        gaps.append(
            _gap(
                gap_type="claim_category_missing",
                severity="medium",
                related_claim_category=claim_category,
                explanation=f"Expected AI audit claim category is not represented: {claim_category}.",
                recommended_next_action="propose_missing_claim_category_only",
            )
        )

    if plan_items:
        planned_categories = set(coverage["plan_coverage"]["planned_categories"])
        for category in coverage["categories_covered"]:
            if category not in planned_categories:
                gaps.append(
                    _gap(
                        gap_type="no_plan_for_category",
                        severity="low",
                        related_category=category,
                        explanation=f"Inventory category has no provided dry plan coverage: {category}.",
                        recommended_next_action="prepare_dry_plan_proposal_only",
                    )
                )
    if plan_items and finding_items:
        finding_probe_ids = set(coverage["finding_coverage"]["finding_probe_ids"])
        for probe_id in coverage["plan_coverage"]["selected_probe_ids"]:
            if probe_id not in finding_probe_ids:
                gaps.append(
                    _gap(
                        gap_type="no_findings_for_planned_probe",
                        severity="low",
                        related_probe_id=probe_id,
                        explanation=f"Planned probe has no provided dry/manual finding envelope: {probe_id}.",
                        recommended_next_action="prepare_non_executing_finding_placeholder_only",
                    )
                )
    if packet_items and report_items:
        report_packet_ids = set(coverage["review_coverage"]["reported_packet_ids"])
        for packet_id in coverage["review_coverage"]["packet_ids"]:
            if packet_id not in report_packet_ids:
                gaps.append(
                    _gap(
                        gap_type="report_missing_for_packet",
                        severity="low",
                        related_packet_id=packet_id,
                        explanation=f"Review packet has no provided redacted report: {packet_id}.",
                        recommended_next_action="build_redacted_report_in_memory_only",
                    )
                )

    inventory_issues = validate_ai_audit_synthetic_probe_inventory_v1(probes)
    for issue in inventory_issues:
        gaps.append(
            _gap(
                gap_type="validation_missing_or_failed",
                severity="high",
                explanation=f"Inventory validation issue: {issue}",
                recommended_next_action="fix_inventory_schema_with_operator_approval",
            )
        )
    for plan in plan_items:
        validation = validate_ai_audit_plan_v1(plan, inventory=probes)
        if not validation.get("valid", False):
            gaps.append(
                _gap(
                    gap_type="validation_missing_or_failed",
                    severity="high",
                    related_plan_id=str(plan.get("plan_id", "")),
                    explanation="Dry plan validation failed or is missing required safety markers.",
                    recommended_next_action="repair_dry_plan_helper_input_only",
                )
            )
    for finding in finding_items:
        validation = validate_ai_audit_finding_v1(finding)
        if not validation.get("valid", False):
            gaps.append(
                _gap(
                    gap_type="validation_missing_or_failed",
                    severity="medium",
                    related_probe_id=str(finding.get("probe_id", "")),
                    related_plan_id=str(finding.get("plan_id", "")),
                    explanation="Finding envelope validation failed or is missing required safety markers.",
                    recommended_next_action="repair_finding_envelope_input_only",
                )
            )
    for packet in packet_items:
        validation = validate_ai_audit_review_packet_v1(packet)
        if not validation.get("valid", False):
            gaps.append(
                _gap(
                    gap_type="validation_missing_or_failed",
                    severity="medium",
                    related_plan_id=str(packet.get("plan_id", "")),
                    related_packet_id=str(packet.get("packet_id", "")),
                    explanation="Review packet validation failed or is missing required safety markers.",
                    recommended_next_action="repair_review_packet_input_only",
                )
            )
    for report in report_items:
        validation = validate_ai_audit_redacted_report_v1(report)
        if not validation.get("valid", False):
            gaps.append(
                _gap(
                    gap_type="validation_missing_or_failed",
                    severity="medium",
                    related_plan_id=str(report.get("plan_id", "")),
                    related_packet_id=str(report.get("packet_id", "")),
                    explanation="Redacted report validation failed or is missing required safety markers.",
                    recommended_next_action="repair_redacted_report_input_only",
                )
            )

    gaps.extend(
        [
            _gap(
                gap_type="runner_not_authorized",
                severity="info",
                explanation="AI audit execution remains outside this phase and is not authorized.",
                recommended_next_action="keep_advisor_non_executing",
            ),
            _gap(
                gap_type="scoring_not_authorized",
                severity="info",
                explanation="Scoring, grading, official scores, and benchmark-result claims remain unauthorized.",
                recommended_next_action="keep_outputs_as_readiness_signals_not_scores",
            ),
            _gap(
                gap_type="external_probe_not_authorized",
                severity="info",
                explanation="External model calls and live AI system probing remain unauthorized.",
                recommended_next_action="use_existing_in_memory_artifacts_only",
            ),
        ]
    )

    return sorted(gaps, key=lambda gap: (gap["severity"], gap["gap_type"], gap["gap_id"]))


def advise_ai_audit_readiness_v1(
    *,
    coverage_summary: dict[str, Any] | None = None,
    gaps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a readiness-status report from coverage and non-executing gaps."""
    coverage = deepcopy(coverage_summary or summarize_ai_audit_coverage_v1())
    gap_items = deepcopy(list(gaps or []))
    high_or_medium = [gap for gap in gap_items if gap.get("severity") in {"high", "medium"}]
    warnings = [gap for gap in gap_items if gap.get("severity") in {"low", "info"}]
    statuses = ["foundation_ready"]
    if coverage.get("plan_coverage", {}).get("plan_count", 0) > 0:
        statuses.append("planning_ready")
    if coverage.get("review_coverage", {}).get("packet_count", 0) > 0 or coverage.get("review_coverage", {}).get("report_count", 0) > 0:
        statuses.append("review_ready")
    statuses.extend(["execution_not_authorized", "scoring_not_authorized", "external_testing_not_authorized"])

    return {
        "schema_version": READINESS_SCHEMA_VERSION,
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_ADVISOR_STATUS,
        "readiness_status": statuses,
        "readiness_signal": "ready_for_governed_planning_review" if not high_or_medium else "gaps_require_operator_review",
        "blockers": [gap["gap_id"] for gap in high_or_medium],
        "warnings": [gap["gap_id"] for gap in warnings],
        "safe_next_steps": list(EXPECTED_SAFE_NEXT_STEPS),
        "forbidden_next_steps": list(FORBIDDEN_NEXT_STEPS),
        "confidence_bound_recommendations": [
            {
                "recommendation_id": "readiness_gap_review_first",
                "confidence_band": "bounded_by_supplied_artifacts",
                "recommendation": "Review structured gaps before approving any new audit capability.",
                "not_a_score": True,
            },
            {
                "recommendation_id": "no_execution_until_separate_approval",
                "confidence_band": "doctrine_bound",
                "recommendation": "Keep AI audit work non-executing until a separately approved runner design exists.",
                "not_a_score": True,
            },
        ],
        "no_scores": True,
        "no_certification": True,
        "no_external_testing": True,
    }


def _proposal(
    *,
    title: str,
    reason: str,
    linked_gap_ids: list[str],
    safety_level: str = "high",
) -> dict[str, Any]:
    return {
        "schema_version": PROPOSAL_SCHEMA_VERSION,
        "proposal_id": _stable_id("weslr_ai_audit_proposal_v1_", title, reason, *sorted(linked_gap_ids)),
        "title": title,
        "reason": reason,
        "linked_gap_ids": sorted(linked_gap_ids),
        "safety_level": safety_level,
        "requires_operator_approval": True,
        "implementation_status": PROPOSAL_ONLY_STATUS,
        "forbidden_actions": list(FORBIDDEN_NEXT_STEPS),
        "automatic_approval": False,
        "runtime_behavior_change": False,
    }


def build_ai_audit_next_proposal_candidates_v1(
    gaps: list[dict[str, Any]],
    readiness_report: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build governed proposal candidates only; never approval or implementation."""
    gap_items = deepcopy(list(gaps or []))
    by_type: dict[str, list[str]] = {}
    for gap in gap_items:
        by_type.setdefault(str(gap.get("gap_type", "unknown")), []).append(str(gap.get("gap_id", "")))

    proposals: list[dict[str, Any]] = []
    if by_type.get("category_missing") or by_type.get("claim_category_missing"):
        proposals.append(
            _proposal(
                title="Add missing AI audit probe coverage proposal",
                reason="Coverage summary found missing expected probe or claim categories.",
                linked_gap_ids=by_type.get("category_missing", []) + by_type.get("claim_category_missing", []),
            )
        )
    if by_type.get("validation_missing_or_failed"):
        proposals.append(
            _proposal(
                title="Improve AI audit validation consistency proposal",
                reason="One or more supplied AI audit artifacts failed validation.",
                linked_gap_ids=by_type["validation_missing_or_failed"],
            )
        )
    if by_type.get("no_findings_for_planned_probe") or by_type.get("no_plan_for_category"):
        proposals.append(
            _proposal(
                title="Add AI audit self-consistency review helper proposal",
                reason="Plans, findings, or category coverage need cross-artifact consistency review.",
                linked_gap_ids=by_type.get("no_findings_for_planned_probe", []) + by_type.get("no_plan_for_category", []),
            )
        )
    if by_type.get("report_missing_for_packet"):
        proposals.append(
            _proposal(
                title="Improve redacted review report coverage proposal",
                reason="One or more review packets lack provided redacted report coverage.",
                linked_gap_ids=by_type["report_missing_for_packet"],
            )
        )

    proposals.append(
        _proposal(
            title="Add AI audit drift monitor proposal",
            reason="Future changes should remain guarded against runner, scoring, certification, and runtime drift.",
            linked_gap_ids=by_type.get("runner_not_authorized", []) + by_type.get("scoring_not_authorized", []) + by_type.get("external_probe_not_authorized", []),
        )
    )
    proposals.append(
        _proposal(
            title="Canonize AI audit readiness gap advisor proposal",
            reason="Readiness/gap advising is a safer next layer than operator-heavy manual case import.",
            linked_gap_ids=list(readiness_report.get("blockers", [])) + list(readiness_report.get("warnings", [])),
        )
    )

    return sorted(proposals, key=lambda proposal: (proposal["title"], proposal["proposal_id"]))


def build_ai_audit_readiness_gap_advisor_result_v1(
    *,
    inventory: list[dict[str, Any]] | None = None,
    plans: list[dict[str, Any]] | None = None,
    findings: list[dict[str, Any]] | None = None,
    packets: list[dict[str, Any]] | None = None,
    reports: list[dict[str, Any]] | None = None,
    expected_probe_categories: list[str] | set[str] | tuple[str, ...] | None = None,
    expected_claim_categories: list[str] | set[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build a complete deterministic in-memory readiness gap advisor result."""
    coverage = summarize_ai_audit_coverage_v1(
        inventory=inventory,
        plans=plans,
        findings=findings,
        packets=packets,
        reports=reports,
        expected_probe_categories=expected_probe_categories,
        expected_claim_categories=expected_claim_categories,
    )
    gaps = detect_ai_audit_readiness_gaps_v1(
        inventory=inventory,
        plans=plans,
        findings=findings,
        packets=packets,
        reports=reports,
        expected_probe_categories=expected_probe_categories,
        expected_claim_categories=expected_claim_categories,
    )
    readiness = advise_ai_audit_readiness_v1(coverage_summary=coverage, gaps=gaps)
    proposals = build_ai_audit_next_proposal_candidates_v1(gaps, readiness)
    result = {
        "schema_version": ADVISOR_RESULT_SCHEMA_VERSION,
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_ADVISOR_STATUS,
        "coverage_summary": coverage,
        "gap_records": gaps,
        "gap_count": len(gaps),
        "readiness_report": readiness,
        "proposal_candidates": proposals,
        "proposal_count": len(proposals),
        "safety_boundaries": _default_safety_boundaries(),
        "not_a_runner": True,
        "not_a_scoring_engine": True,
        "not_a_certification": True,
        "not_a_benchmark_result": True,
        "not_truth_promotion": True,
        "no_model_calls": True,
        "no_runtime_behavior_change": True,
    }
    result["validation_status"] = validate_ai_audit_readiness_gap_advisor_result_v1(result)
    return result


def _find_forbidden_advisor_fields(value: Any, path: str = "advisor_result") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_ADVISOR_FIELDS:
                issues.append(f"forbidden advisor field: {nested_path}")
            if key_text in FORBIDDEN_ADVISOR_TRUE_FLAGS and nested is True:
                issues.append(f"forbidden advisor true marker: {nested_path}")
            issues.extend(_find_forbidden_advisor_fields(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_find_forbidden_advisor_fields(nested, f"{path}[{index}]"))
    return issues


def validate_ai_audit_readiness_gap_advisor_result_v1(result: dict[str, Any]) -> dict[str, Any]:
    """Validate advisor output boundaries without execution, scoring, or persistence."""
    issues: list[str] = []
    if not isinstance(result, dict):
        return {"valid": False, "redacted_count_only": True, "issues": ["advisor result must be a dict"]}

    if result.get("schema_version") != ADVISOR_RESULT_SCHEMA_VERSION:
        issues.append("invalid schema_version")
    if result.get("redacted_count_only") is not True:
        issues.append("advisor result must be redacted/count-only")
    if result.get("in_memory_only") is not True:
        issues.append("advisor result must be in-memory only")
    if result.get("execution_status") != NON_EXECUTING_ADVISOR_STATUS:
        issues.append("advisor result execution_status must be non_executing_advisor_only")
    if result.get("not_a_runner") is not True:
        issues.append("advisor result must be marked not_a_runner")
    if result.get("not_a_scoring_engine") is not True:
        issues.append("advisor result must be marked not_a_scoring_engine")
    if result.get("not_a_certification") is not True:
        issues.append("advisor result must be marked not_a_certification")
    if result.get("not_a_benchmark_result") is not True:
        issues.append("advisor result must be marked not_a_benchmark_result")
    if result.get("not_truth_promotion") is not True:
        issues.append("advisor result must be marked not_truth_promotion")

    for key, expected in _default_safety_boundaries().items():
        if (result.get("safety_boundaries") or {}).get(key) is not expected:
            issues.append(f"safety boundary {key} must be {expected}")

    for gap in result.get("gap_records", []) or []:
        if gap.get("execution_status") != NON_EXECUTING_GAP_STATUS:
            issues.append(f"gap must be non-executing: {gap.get('gap_id', '')}")
        if gap.get("severity") not in GAP_SEVERITIES:
            issues.append(f"invalid gap severity: {gap.get('gap_id', '')}")
        if gap.get("automatic_fix") is not False:
            issues.append(f"gap automatic_fix must be False: {gap.get('gap_id', '')}")
        if gap.get("truth_promotion") is not False:
            issues.append(f"gap truth_promotion must be False: {gap.get('gap_id', '')}")

    for proposal in result.get("proposal_candidates", []) or []:
        if proposal.get("implementation_status") != PROPOSAL_ONLY_STATUS:
            issues.append(f"proposal must be proposal_only: {proposal.get('proposal_id', '')}")
        if proposal.get("requires_operator_approval") is not True:
            issues.append(f"proposal must require operator approval: {proposal.get('proposal_id', '')}")
        if proposal.get("automatic_approval") is not False:
            issues.append(f"proposal automatic_approval must be False: {proposal.get('proposal_id', '')}")
        if proposal.get("runtime_behavior_change") is not False:
            issues.append(f"proposal runtime_behavior_change must be False: {proposal.get('proposal_id', '')}")

    issues.extend(_find_forbidden_advisor_fields(result))

    return {
        "valid": not issues,
        "redacted_count_only": True,
        "issues": issues,
        "gap_count": len(result.get("gap_records", []) or []),
        "proposal_count": len(result.get("proposal_candidates", []) or []),
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
