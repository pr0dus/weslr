"""WESLR AI audit self-consistency review helpers V1.

Safe, in-memory helpers for detecting contradictions between WESLR AI audit
plans, findings, review packets, redacted reports, and operator review cards.

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

from weslr.ai_audit_findings import validate_ai_audit_finding_v1
from weslr.ai_audit_operator_review_surface import validate_ai_audit_operator_review_card_v1
from weslr.ai_audit_plan import validate_ai_audit_plan_v1
from weslr.ai_audit_report import validate_ai_audit_redacted_report_v1
from weslr.ai_audit_review_packet import validate_ai_audit_review_packet_v1


CONSISTENCY_REVIEW_SCHEMA_VERSION = "ai_audit_consistency_review_result_v1"
CONSISTENCY_ISSUE_SCHEMA_VERSION = "ai_audit_consistency_issue_v1"
NON_EXECUTING_ISSUE_STATUS = "non_executing_consistency_issue_only"
NON_EXECUTING_REVIEW_STATUS = "non_executing_review_only"

ISSUE_SEVERITIES = {"info", "low", "medium", "high"}

FORBIDDEN_CONSISTENCY_FIELDS = {
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
    "live_system_testing",
    "real_system_testing",
    "official_score_claimed",
    "certification_claimed",
    "official_benchmark_claimed",
    "clinical_validity_claimed",
    "protected_item_present",
    "answer_key_present",
    "hidden_prompt_present",
    "runtime_behavior_change",
    "report_persistence",
    "automatic_approval",
}

SAFE_NEXT_STEPS = [
    "review_consistency_issues",
    "repair_invalid_artifact_inputs_only",
    "rebuild_redacted_report_in_memory_only",
    "rebuild_operator_review_card_in_memory_only",
    "keep_ai_audit_non_executing",
]


def _stable_id(prefix: str, *parts: str) -> str:
    seed = "|".join(str(part) for part in parts)
    return prefix + sha256(seed.encode("utf-8")).hexdigest()[:12]


def _as_list(value: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None) -> list[dict[str, Any]]:
    return deepcopy(list(value or []))


def _issue(
    *,
    issue_type: str,
    severity: str,
    explanation: str,
    recommended_next_action: str,
    related_plan_id: str = "",
    related_packet_id: str = "",
    related_report_id: str = "",
    related_probe_id: str = "",
) -> dict[str, Any]:
    safe_severity = severity if severity in ISSUE_SEVERITIES else "info"
    seed = "|".join([issue_type, related_plan_id, related_packet_id, related_report_id, related_probe_id, explanation])
    return {
        "schema_version": CONSISTENCY_ISSUE_SCHEMA_VERSION,
        "issue_id": _stable_id("weslr_ai_audit_consistency_issue_v1_", seed),
        "issue_type": issue_type,
        "severity": safe_severity,
        "related_plan_id": related_plan_id,
        "related_packet_id": related_packet_id,
        "related_report_id": related_report_id,
        "related_probe_id": related_probe_id,
        "explanation": explanation,
        "recommended_next_action": recommended_next_action,
        "execution_status": NON_EXECUTING_ISSUE_STATUS,
        "automatic_fix": False,
        "truth_promotion": False,
        "runtime_behavior_change": False,
    }


def _count_values(items: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[str(item)] = counts.get(str(item), 0) + 1
    return dict(sorted(counts.items()))


def _packet_verdict_counts(packet: dict[str, Any]) -> dict[str, int]:
    return dict(((packet.get("finding_summary") or {}).get("verdict_counts") or {}))


def _packet_finding_type_counts(packet: dict[str, Any]) -> dict[str, int]:
    return dict(((packet.get("finding_summary") or {}).get("finding_type_counts") or {}))


def _report_verdict_counts(report: dict[str, Any]) -> dict[str, int]:
    return dict(report.get("verdict_counts") or {})


def _report_finding_type_counts(report: dict[str, Any]) -> dict[str, int]:
    return dict(report.get("finding_type_counts") or {})


def _target_name_kind_from_packet(packet: dict[str, Any]) -> tuple[str, str]:
    target = packet.get("target_summary") or {}
    return str(target.get("target_name", "unknown_target")), str(target.get("target_kind", "unknown"))


def _target_name_kind_from_report(report: dict[str, Any]) -> tuple[str, str]:
    target = report.get("target_summary") or {}
    return str(target.get("target_name", "unknown_target")), str(target.get("target_kind", "unknown"))


def review_ai_audit_plan_finding_consistency_v1(plan: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Review one dry plan and finding envelopes for non-executing consistency."""
    plan_copy = deepcopy(plan)
    finding_items = _as_list(findings)
    issues: list[dict[str, Any]] = []
    plan_id = str(plan_copy.get("plan_id", ""))
    selected_probe_ids = {str(probe_id) for probe_id in plan_copy.get("selected_probe_ids", [])}
    finding_ids: list[str] = []

    plan_validation = validate_ai_audit_plan_v1(plan_copy)
    if not plan_validation.get("valid", False):
        issues.append(
            _issue(
                issue_type="validation_status_mismatch",
                severity="high",
                related_plan_id=plan_id,
                explanation="Dry plan validation failed during consistency review.",
                recommended_next_action="repair_dry_plan_input_only",
            )
        )

    for finding in finding_items:
        finding_plan_id = str(finding.get("plan_id", ""))
        finding_probe_id = str(finding.get("probe_id", ""))
        finding_id = str(finding.get("finding_id", ""))
        if finding_id:
            finding_ids.append(finding_id)
        if finding_plan_id != plan_id:
            issues.append(
                _issue(
                    issue_type="plan_id_mismatch",
                    severity="high",
                    related_plan_id=plan_id,
                    related_probe_id=finding_probe_id,
                    explanation="Finding plan_id does not match the dry plan.",
                    recommended_next_action="rebuild_finding_for_matching_plan_only",
                )
            )
        if selected_probe_ids and finding_probe_id not in selected_probe_ids:
            issues.append(
                _issue(
                    issue_type="unknown_or_unlinked_artifact",
                    severity="medium",
                    related_plan_id=plan_id,
                    related_probe_id=finding_probe_id,
                    explanation="Finding probe_id is not selected by the dry plan.",
                    recommended_next_action="link_finding_to_selected_probe_or_archive_review_only",
                )
            )
        finding_validation = validate_ai_audit_finding_v1(finding, plan=plan_copy)
        if not finding_validation.get("valid", False):
            issues.append(
                _issue(
                    issue_type="validation_status_mismatch",
                    severity="medium",
                    related_plan_id=plan_id,
                    related_probe_id=finding_probe_id,
                    explanation="Finding validation failed during consistency review.",
                    recommended_next_action="repair_finding_envelope_input_only",
                )
            )
        if finding.get("executable") is not False or finding.get("scoring_engine") is not False or finding.get("official_score_claimed") is not False:
            issues.append(
                _issue(
                    issue_type="executable_status_drift",
                    severity="high",
                    related_plan_id=plan_id,
                    related_probe_id=finding_probe_id,
                    explanation="Finding contains executable/scoring/official-status drift.",
                    recommended_next_action="remove_unsafe_status_markers",
                )
            )

    for finding_id, count in _count_values(finding_ids).items():
        if count > 1:
            issues.append(
                _issue(
                    issue_type="unknown_or_unlinked_artifact",
                    severity="medium",
                    related_plan_id=plan_id,
                    explanation=f"Duplicate finding_id detected: {finding_id}.",
                    recommended_next_action="deduplicate_finding_envelopes_only",
                )
            )

    covered_probe_ids = sorted({str(finding.get("probe_id", "")) for finding in finding_items if str(finding.get("probe_id", "")) in selected_probe_ids})
    return {
        "schema_version": "ai_audit_plan_finding_consistency_review_v1",
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_REVIEW_STATUS,
        "plan_id": plan_id,
        "finding_count": len(finding_items),
        "selected_probe_count": len(selected_probe_ids),
        "covered_probe_count": len(covered_probe_ids),
        "covered_probe_ids": covered_probe_ids,
        "issues": sorted(issues, key=lambda item: (item["severity"], item["issue_type"], item["issue_id"])),
        "no_scores": True,
        "no_model_calls": True,
        "not_a_runner": True,
    }


def review_ai_audit_packet_report_consistency_v1(packet: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    """Review a packet and redacted report for count-only consistency."""
    packet_copy = deepcopy(packet)
    report_copy = deepcopy(report)
    issues: list[dict[str, Any]] = []
    packet_id = str(packet_copy.get("packet_id", ""))
    report_id = str(report_copy.get("report_id", ""))
    plan_id = str(packet_copy.get("plan_id", ""))

    if packet_id != str(report_copy.get("packet_id", "")):
        issues.append(_issue(issue_type="packet_report_mismatch", severity="high", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Packet/report packet_id values do not match.", recommended_next_action="rebuild_redacted_report_from_matching_packet_only"))
    if plan_id != str(report_copy.get("plan_id", "")):
        issues.append(_issue(issue_type="plan_id_mismatch", severity="high", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Packet/report plan_id values do not match.", recommended_next_action="rebuild_report_for_matching_plan_only"))
    if _target_name_kind_from_packet(packet_copy) != _target_name_kind_from_report(report_copy):
        issues.append(_issue(issue_type="packet_report_mismatch", severity="medium", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Packet/report target summaries do not match.", recommended_next_action="rebuild_redacted_report_target_summary_only"))
    if int(packet_copy.get("selected_probe_count", 0)) != int(report_copy.get("total_selected_probes", 0)):
        issues.append(_issue(issue_type="probe_count_mismatch", severity="medium", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Packet/report selected probe counts do not match.", recommended_next_action="rebuild_report_counts_from_packet_only"))
    if int(packet_copy.get("finding_count", 0)) != int(report_copy.get("total_findings", 0)):
        issues.append(_issue(issue_type="finding_count_mismatch", severity="medium", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Packet/report finding counts do not match.", recommended_next_action="rebuild_report_counts_from_packet_only"))
    if _packet_verdict_counts(packet_copy) != _report_verdict_counts(report_copy):
        issues.append(_issue(issue_type="verdict_count_mismatch", severity="medium", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Packet/report verdict counts do not match.", recommended_next_action="rebuild_report_verdict_counts_from_packet_only"))
    if _packet_finding_type_counts(packet_copy) != _report_finding_type_counts(report_copy):
        issues.append(_issue(issue_type="finding_type_count_mismatch", severity="medium", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Packet/report finding type counts do not match.", recommended_next_action="rebuild_report_finding_type_counts_from_packet_only"))

    for label, validation in (("packet", validate_ai_audit_review_packet_v1(packet_copy)), ("report", validate_ai_audit_redacted_report_v1(report_copy))):
        if not validation.get("valid", False):
            issues.append(_issue(issue_type="validation_status_mismatch", severity="high", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation=f"{label} validation failed during consistency review.", recommended_next_action=f"repair_{label}_input_only"))

    for item, label in ((packet_copy, "packet"), (report_copy, "report")):
        if item.get("executable") is not False or item.get("scoring_engine") is not False:
            issues.append(_issue(issue_type="executable_status_drift", severity="high", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation=f"{label} contains executable or scoring drift.", recommended_next_action="remove_unsafe_status_markers"))

    return {
        "schema_version": "ai_audit_packet_report_consistency_review_v1",
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_REVIEW_STATUS,
        "plan_id": plan_id,
        "packet_id": packet_id,
        "report_id": report_id,
        "issues": sorted(issues, key=lambda item: (item["severity"], item["issue_type"], item["issue_id"])),
        "no_scores": True,
        "no_model_calls": True,
        "not_a_runner": True,
    }


def review_ai_audit_review_card_consistency_v1(card: dict[str, Any], packet_or_report: dict[str, Any]) -> dict[str, Any]:
    """Review an operator review card against its packet or report source."""
    card_copy = deepcopy(card)
    source = deepcopy(packet_or_report)
    issues: list[dict[str, Any]] = []
    plan_id = str(source.get("plan_id", ""))
    packet_id = str(source.get("packet_id", ""))
    report_id = str(source.get("report_id", ""))
    source_is_report = str(source.get("schema_version", "")) == "ai_audit_redacted_report_v1" or bool(report_id)
    target_name, target_kind = _target_name_kind_from_report(source) if source_is_report else _target_name_kind_from_packet(source)
    total_probes = int(source.get("total_selected_probes", 0) if source_is_report else source.get("selected_probe_count", 0))
    total_findings = int(source.get("total_findings", 0) if source_is_report else source.get("finding_count", 0))
    verdict_counts = _report_verdict_counts(source) if source_is_report else _packet_verdict_counts(source)
    finding_type_counts = _report_finding_type_counts(source) if source_is_report else _packet_finding_type_counts(source)

    if str(card_copy.get("plan_id", "")) != plan_id:
        issues.append(_issue(issue_type="plan_id_mismatch", severity="high", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Card/source plan_id values do not match.", recommended_next_action="rebuild_card_from_matching_source_only"))
    if packet_id and str(card_copy.get("packet_id", "")) != packet_id:
        issues.append(_issue(issue_type="card_report_mismatch", severity="medium", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Card/source packet_id values do not match.", recommended_next_action="rebuild_card_from_source_only"))
    if source_is_report and str(card_copy.get("report_id", "")) != report_id:
        issues.append(_issue(issue_type="card_report_mismatch", severity="medium", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Card/report report_id values do not match.", recommended_next_action="rebuild_card_from_report_only"))
    if (str(card_copy.get("target_name", "")), str(card_copy.get("target_kind", ""))) != (target_name, target_kind):
        issues.append(_issue(issue_type="card_report_mismatch", severity="medium", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Card/source target summary does not match.", recommended_next_action="rebuild_card_target_summary_only"))
    if int(card_copy.get("total_probes", 0)) != total_probes:
        issues.append(_issue(issue_type="probe_count_mismatch", severity="medium", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Card/source probe counts do not match.", recommended_next_action="rebuild_card_counts_from_source_only"))
    if int(card_copy.get("total_findings", 0)) != total_findings:
        issues.append(_issue(issue_type="finding_count_mismatch", severity="medium", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Card/source finding counts do not match.", recommended_next_action="rebuild_card_counts_from_source_only"))
    if dict(card_copy.get("verdict_counts") or {}) != verdict_counts:
        issues.append(_issue(issue_type="verdict_count_mismatch", severity="medium", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Card/source verdict counts do not match.", recommended_next_action="rebuild_card_counts_from_source_only"))
    if dict(card_copy.get("finding_type_counts") or {}) != finding_type_counts:
        issues.append(_issue(issue_type="finding_type_count_mismatch", severity="medium", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Card/source finding type counts do not match.", recommended_next_action="rebuild_card_counts_from_source_only"))
    if card_copy.get("redacted_count_only") is not True or card_copy.get("in_memory_only") is not True:
        issues.append(_issue(issue_type="missing_safety_boundary", severity="high", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Card is missing redacted/count-only or in-memory safety markers.", recommended_next_action="rebuild_safe_review_card_only"))
    if not validate_ai_audit_operator_review_card_v1(card_copy).get("valid", False):
        issues.append(_issue(issue_type="validation_status_mismatch", severity="high", related_plan_id=plan_id, related_packet_id=packet_id, related_report_id=report_id, explanation="Operator review card validation failed.", recommended_next_action="repair_card_input_only"))

    return {
        "schema_version": "ai_audit_review_card_consistency_review_v1",
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_REVIEW_STATUS,
        "plan_id": plan_id,
        "packet_id": packet_id,
        "report_id": report_id,
        "issues": sorted(issues, key=lambda item: (item["severity"], item["issue_type"], item["issue_id"])),
        "no_scores": True,
        "no_model_calls": True,
        "not_a_runner": True,
    }


def _status_for_issues(issues: list[dict[str, Any]], artifact_count: int) -> str:
    if artifact_count == 0:
        return "insufficient_artifacts"
    severities = {str(issue.get("severity", "info")) for issue in issues}
    if "high" in severities or "medium" in severities:
        return "inconsistent"
    if issues:
        return "warnings_present"
    return "consistent"


def build_ai_audit_consistency_review_result_v1(
    *,
    plan: dict[str, Any] | None = None,
    findings: list[dict[str, Any]] | None = None,
    packet: dict[str, Any] | None = None,
    report: dict[str, Any] | None = None,
    cards: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic, in-memory consistency review result."""
    plan_copy = deepcopy(plan) if isinstance(plan, dict) else None
    finding_items = _as_list(findings)
    packet_copy = deepcopy(packet) if isinstance(packet, dict) else None
    report_copy = deepcopy(report) if isinstance(report, dict) else None
    card_items = _as_list(cards)
    subreviews: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []

    if plan_copy is not None:
        review = review_ai_audit_plan_finding_consistency_v1(plan_copy, finding_items)
        subreviews.append(review)
        issues.extend(review["issues"])
    if packet_copy is not None and report_copy is not None:
        review = review_ai_audit_packet_report_consistency_v1(packet_copy, report_copy)
        subreviews.append(review)
        issues.extend(review["issues"])
    for card in card_items:
        source = report_copy if report_copy is not None and card.get("source_type") == "redacted_report" else packet_copy or report_copy
        if source is None:
            issues.append(_issue(issue_type="unknown_or_unlinked_artifact", severity="medium", explanation="Review card was supplied without a packet or report source.", recommended_next_action="provide_matching_card_source_only"))
            continue
        review = review_ai_audit_review_card_consistency_v1(card, source)
        subreviews.append(review)
        issues.extend(review["issues"])

    if packet_copy is not None and plan_copy is not None and str(packet_copy.get("plan_id", "")) != str(plan_copy.get("plan_id", "")):
        issues.append(_issue(issue_type="plan_id_mismatch", severity="high", related_plan_id=str(plan_copy.get("plan_id", "")), related_packet_id=str(packet_copy.get("packet_id", "")), explanation="Packet plan_id does not match supplied dry plan.", recommended_next_action="supply_matching_plan_packet_pair_only"))

    issues = sorted(issues, key=lambda item: (item["severity"], item["issue_type"], item["issue_id"]))
    severity_counts = _count_values([str(issue.get("severity", "info")) for issue in issues])
    type_counts = _count_values([str(issue.get("issue_type", "unknown")) for issue in issues])
    artifact_count = sum(1 for item in (plan_copy, packet_copy, report_copy) if item is not None) + len(finding_items) + len(card_items)
    result = {
        "schema_version": CONSISTENCY_REVIEW_SCHEMA_VERSION,
        "review_id": _stable_id("weslr_ai_audit_consistency_review_v1_", str(artifact_count), *[issue["issue_id"] for issue in issues]),
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_REVIEW_STATUS,
        "total_issues": len(issues),
        "issue_counts_by_severity": severity_counts,
        "issue_counts_by_type": type_counts,
        "consistency_status": _status_for_issues(issues, artifact_count),
        "issues": issues,
        "subreview_count": len(subreviews),
        "subreviews": subreviews,
        "safe_next_steps": list(SAFE_NEXT_STEPS),
        "not_a_runner": True,
        "not_a_scoring_engine": True,
        "not_a_certification": True,
        "not_a_benchmark_result": True,
        "not_truth_promotion": True,
        "no_model_calls": True,
        "no_runtime_behavior_change": True,
        "no_persistence": True,
    }
    result["validation_status"] = validate_ai_audit_consistency_review_result_v1(result)
    return result


def _find_forbidden_fields(value: Any, path: str = "consistency_review") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_CONSISTENCY_FIELDS:
                issues.append(f"forbidden consistency field: {nested_path}")
            if key_text in FORBIDDEN_TRUE_MARKERS and nested is True:
                issues.append(f"forbidden consistency true marker: {nested_path}")
            issues.extend(_find_forbidden_fields(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_find_forbidden_fields(nested, f"{path}[{index}]"))
    return issues


def validate_ai_audit_consistency_review_result_v1(result: dict[str, Any]) -> dict[str, Any]:
    """Validate consistency review output boundaries without side effects."""
    issues: list[str] = []
    if not isinstance(result, dict):
        return {"valid": False, "redacted_count_only": True, "issues": ["consistency review result must be a dict"]}

    if result.get("schema_version") != CONSISTENCY_REVIEW_SCHEMA_VERSION:
        issues.append("invalid schema_version")
    if result.get("redacted_count_only") is not True:
        issues.append("consistency review must be redacted/count-only")
    if result.get("in_memory_only") is not True:
        issues.append("consistency review must be in-memory only")
    if result.get("execution_status") != NON_EXECUTING_REVIEW_STATUS:
        issues.append("consistency review execution_status must be non_executing_review_only")
    if result.get("not_a_runner") is not True:
        issues.append("consistency review must be marked not_a_runner")
    if result.get("not_a_scoring_engine") is not True:
        issues.append("consistency review must be marked not_a_scoring_engine")
    if result.get("not_a_certification") is not True:
        issues.append("consistency review must be marked not_a_certification")
    if result.get("not_a_benchmark_result") is not True:
        issues.append("consistency review must be marked not_a_benchmark_result")
    if result.get("not_truth_promotion") is not True:
        issues.append("consistency review must be marked not_truth_promotion")
    if result.get("no_persistence") is not True:
        issues.append("consistency review must be marked no_persistence")

    for issue in result.get("issues", []) or []:
        if issue.get("execution_status") != NON_EXECUTING_ISSUE_STATUS:
            issues.append(f"issue must be non-executing: {issue.get('issue_id', '')}")
        if issue.get("severity") not in ISSUE_SEVERITIES:
            issues.append(f"invalid issue severity: {issue.get('issue_id', '')}")
        if issue.get("automatic_fix") is not False:
            issues.append(f"issue automatic_fix must be False: {issue.get('issue_id', '')}")
        if issue.get("truth_promotion") is not False:
            issues.append(f"issue truth_promotion must be False: {issue.get('issue_id', '')}")
        if issue.get("runtime_behavior_change") is not False:
            issues.append(f"issue runtime_behavior_change must be False: {issue.get('issue_id', '')}")

    issues.extend(_find_forbidden_fields(result))

    return {
        "valid": not issues,
        "redacted_count_only": True,
        "issues": issues,
        "total_issues": len(result.get("issues", []) or []),
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
