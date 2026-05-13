"""WESLR Source Registry Review Queue Mapping Helpers V1.

Pure in-memory helpers that convert unregistered-source detection findings into
AdvisorReviewQueueItem proposal objects. This module does not write queue files,
persist registry data, scan repositories, call advisors/models, wire runtime
behavior, mutate memory, select answers, claim truth/soundness, or claim
official scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re

from weslr.advisor_review_queue import (
    AdvisorReviewQueueItem,
    AdvisorReviewQueueSafetyFlags,
    advisor_review_queue_item_from_dict,
    create_empty_advisor_review_queue_item,
    validate_advisor_review_queue_item,
)
from weslr.unregistered_source_detection import (
    UnregisteredSourceDetectionReport,
    UnregisteredSourceFinding,
    summarize_unregistered_source_detection_report,
    unregistered_source_detection_report_from_dict,
    unregistered_source_finding_from_dict,
    validate_unregistered_source_detection_report,
    validate_unregistered_source_finding,
)


FINDING_TYPE_TO_SUGGESTION_TYPE = {
    "unregistered_source_candidate": "provider_registry_review",
    "missing_source_registry_entry": "provider_registry_review",
    "stale_source_registry_entry": "provider_registry_review",
    "source_without_tests": "test_coverage_review",
    "source_without_docs": "capability_scope_review",
    "unknown_source_in_provenance": "capability_scope_review",
    "unregistered_voice_or_proactive_source": "capability_scope_review",
    "unregistered_self_improvement_source": "safety_policy_review",
    "source_authority_boundary_missing": "safety_policy_review",
    "source_activation_policy_inconsistent": "safety_policy_review",
    "unknown": "advisor_review",
}

SENSITIVE_TEXT_PATTERNS = {
    "possible API key": re.compile(r"api[_ -]?key|sk-[A-Za-z0-9]|AIza[0-9A-Za-z_-]", re.IGNORECASE),
    "possible token": re.compile(r"\btoken\b|token[_ -]?[A-Za-z0-9_-]*|bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
    "possible secret": re.compile(r"\bsecret\b|secret[_ -]?[A-Za-z0-9_-]*|password\s*[:=]", re.IGNORECASE),
    "possible raw benchmark text": re.compile(r"raw benchmark|benchmark text|question stem|passage:", re.IGNORECASE),
    "possible answer key": re.compile(r"answer[_ -]?key|official solution|correct answer", re.IGNORECASE),
    "possible official score": re.compile(r"official score|benchmark score", re.IGNORECASE),
    "possible private user data": re.compile(r"private user data|ssn|social security|passport", re.IGNORECASE),
}
SUMMARY_REDACTION = "[redacted]"


@dataclass
class SourceRegistryReviewQueueMappingResult:
    items: list[AdvisorReviewQueueItem] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)
    queue_writes_performed: bool = False
    registry_persistence_performed: bool = False
    external_model_calls_performed: bool = False
    runtime_changes_performed: bool = False
    answer_selection_performed: bool = False
    truth_claim_performed: bool = False
    official_score_claimed: bool = False


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in SENSITIVE_TEXT_PATTERNS.values():
        redacted = pattern.sub(SUMMARY_REDACTION, redacted)
    return redacted


def _as_finding(finding: UnregisteredSourceFinding | dict[str, Any]) -> UnregisteredSourceFinding:
    if isinstance(finding, UnregisteredSourceFinding):
        return finding
    return unregistered_source_finding_from_dict(finding)


def _as_report(report: UnregisteredSourceDetectionReport | dict[str, Any]) -> UnregisteredSourceDetectionReport:
    if isinstance(report, UnregisteredSourceDetectionReport):
        return report
    return unregistered_source_detection_report_from_dict(report)


def _suggestion_id_for_finding(finding: UnregisteredSourceFinding) -> str:
    source_id = finding.candidate_source_id.strip() or "unknown_source"
    finding_id = finding.finding_id.strip() or "unknown_finding"
    return _redact_text(f"source_registry_review_{finding_id}_{source_id}")


def _trigger_reason_for_finding(finding: UnregisteredSourceFinding) -> str:
    parts = [
        f"source registry review: {finding.finding_type}",
        f"signal: {finding.detection_signal}",
    ]
    if finding.evidence_summary.strip():
        parts.append(f"evidence: {finding.evidence_summary.strip()}")
    return _redact_text("; ".join(parts))


def _notes_for_finding(finding: UnregisteredSourceFinding, suggestion_type: str) -> list[str]:
    notes = [
        _redact_text(f"candidate_source_id: {finding.candidate_source_id}"),
        _redact_text(f"candidate_source_type: {finding.candidate_source_type}"),
        _redact_text(f"candidate_module_path: {finding.candidate_module_path}"),
        _redact_text(f"mapped_from_finding_type: {finding.finding_type}"),
        _redact_text(f"mapped_to_suggestion_type: {suggestion_type}"),
    ]
    for doc in finding.related_docs:
        notes.append(_redact_text(f"related_doc: {doc}"))
    for test in finding.related_tests:
        notes.append(_redact_text(f"related_test: {test}"))
    return [note for note in notes if note.strip()]


def map_unregistered_source_finding_to_review_queue_item(
    finding: UnregisteredSourceFinding | dict[str, Any],
) -> AdvisorReviewQueueItem:
    """Map one valid unregistered-source finding to an in-memory queue proposal."""
    item_finding = _as_finding(finding)
    errors = validate_unregistered_source_finding(item_finding)
    if errors:
        raise ValueError("invalid unregistered-source finding: " + "; ".join(errors))

    suggestion_type = FINDING_TYPE_TO_SUGGESTION_TYPE.get(item_finding.finding_type, "advisor_review")
    notes = _notes_for_finding(item_finding, suggestion_type)
    queue_item = create_empty_advisor_review_queue_item(
        suggestion_id=_suggestion_id_for_finding(item_finding),
        trigger_reason=_trigger_reason_for_finding(item_finding),
        recommended_action=_redact_text(item_finding.recommended_action or "operator review required"),
        suggestion_type=suggestion_type,
        source="diagnostic",
        capability_scope=[_redact_text(item_finding.candidate_source_type)],
        risk_level=item_finding.risk_level,
        requires_operator_approval=True,
        advisor_call_allowed=False,
        advisor_call_mode="local_scan_only",
        review_status="pending_review",
        operator_decision="pending_review",
        notes=notes,
        safety_flags=AdvisorReviewQueueSafetyFlags(),
    )
    queue_errors = validate_advisor_review_queue_item(queue_item)
    if queue_errors:
        raise ValueError("mapped advisor-review queue item invalid: " + "; ".join(queue_errors))
    return queue_item


def map_unregistered_source_report_to_review_queue_items(
    report: UnregisteredSourceDetectionReport | dict[str, Any],
) -> SourceRegistryReviewQueueMappingResult:
    """Map a detection report into in-memory queue proposals and errors."""
    item_report = _as_report(report)
    report_errors = validate_unregistered_source_detection_report(item_report)
    result = SourceRegistryReviewQueueMappingResult(validation_errors=list(report_errors))
    if report_errors:
        return result

    for finding in item_report.findings:
        finding_errors = validate_unregistered_source_finding(finding)
        if finding_errors:
            result.validation_errors.extend(f"{finding.finding_id or 'unknown_finding'}: {error}" for error in finding_errors)
            continue
        try:
            result.items.append(map_unregistered_source_finding_to_review_queue_item(finding))
        except ValueError as exc:
            result.validation_errors.append(str(exc))
    return result


def summarize_source_registry_review_queue_mapping_diagnostics(
    report_or_result: UnregisteredSourceDetectionReport | SourceRegistryReviewQueueMappingResult | dict[str, Any],
) -> dict[str, Any]:
    """Return redacted/count-only mapping diagnostics."""
    if isinstance(report_or_result, SourceRegistryReviewQueueMappingResult):
        result = report_or_result
        finding_count = len(result.items) + len(result.validation_errors)
        finding_type_counts: dict[str, int] = {}
        risk_level_counts: dict[str, int] = {}
    else:
        report = _as_report(report_or_result)
        result = map_unregistered_source_report_to_review_queue_items(report)
        report_summary = summarize_unregistered_source_detection_report(report)
        finding_count = report_summary["finding_count"]
        finding_type_counts = report_summary["by_finding_type"]
        risk_level_counts = report_summary["by_risk_level"]

    suggestion_type_counts: dict[str, int] = {}
    operator_review_required_count = 0
    advisor_call_allowed_count = 0
    for item in result.items:
        suggestion_type_counts[item.suggestion_type] = suggestion_type_counts.get(item.suggestion_type, 0) + 1
        if item.requires_operator_approval:
            operator_review_required_count += 1
        if item.advisor_call_allowed:
            advisor_call_allowed_count += 1

    return {
        "schema_version": "1.0",
        "summary_mode": "redacted_count_only",
        "finding_count": finding_count,
        "mapped_queue_proposal_count": len(result.items),
        "validation_error_count": len(result.validation_errors),
        "finding_type_counts": finding_type_counts,
        "suggestion_type_counts": suggestion_type_counts,
        "risk_level_counts": risk_level_counts,
        "operator_review_required_count": operator_review_required_count,
        "advisor_call_allowed_count": advisor_call_allowed_count,
        "queue_writes_performed": False,
        "registry_persistence_performed": False,
        "external_model_calls_performed": False,
        "runtime_changes_performed": False,
        "answer_selection": False,
        "truth_claim": False,
        "official_score": False,
    }
