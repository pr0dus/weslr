"""WESLR Advisor Review Queue Schema V1.

Schema-only dataclasses and validation helpers for future advisor-review
queue items. This module does not implement persistence, local scans,
scheduling, daemon behavior, model calls, prompt mutation, provider activation,
or runtime/config changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
import re


ALLOWED_SUGGESTION_TYPES = {
    "advisor_review",
    "prompt_template_review",
    "provider_registry_review",
    "capability_scope_review",
    "safety_policy_review",
    "gap_taxonomy_review",
    "style_review",
    "test_coverage_review",
    "unknown",
}

ALLOWED_SOURCES = {
    "local_scan",
    "operator_request",
    "diagnostic",
    "capability_change",
    "provider_health_check",
    "prompt_template_staleness_check",
    "manual_entry",
    "unknown",
}

ALLOWED_RISK_LEVELS = {"low", "medium", "high", "unknown"}
ALLOWED_ADVISOR_CALL_MODES = {"local_scan_only", "operator_approved_advisor_call", "disabled"}
ALLOWED_REVIEW_STATUSES = {"pending_review", "accepted", "rejected", "deferred", "archived"}
ALLOWED_OPERATOR_DECISIONS = {"pending_review", "approved", "approved_with_changes", "rejected", "deferred"}

PROHIBITED_SAFETY_FLAG_FIELDS = {
    "answer_selection_requested": "answer selection requested",
    "truth_authority_requested": "truth authority requested",
    "soundness_authority_requested": "soundness authority requested",
    "official_score_requested": "official score requested",
    "answer_key_requested": "answer key requested",
    "benchmark_specific_tuning_requested": "benchmark-specific tuning requested",
    "raw_benchmark_text_requested": "raw benchmark text requested",
    "secrets_requested": "secrets requested",
    "private_user_data_requested": "private user data requested",
    "memory_mutation_requested": "memory mutation requested",
    "runtime_config_change_requested": "runtime/config change requested",
    "governance_override_requested": "governance override requested",
    "external_model_call_auto_allowed": "automatic external model call allowed",
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
class AdvisorReviewQueueSafetyFlags:
    answer_selection_requested: bool = False
    truth_authority_requested: bool = False
    soundness_authority_requested: bool = False
    official_score_requested: bool = False
    answer_key_requested: bool = False
    benchmark_specific_tuning_requested: bool = False
    raw_benchmark_text_requested: bool = False
    secrets_requested: bool = False
    private_user_data_requested: bool = False
    memory_mutation_requested: bool = False
    runtime_config_change_requested: bool = False
    governance_override_requested: bool = False
    external_model_call_auto_allowed: bool = False


@dataclass
class AdvisorReviewQueueItem:
    schema_version: str = "1.0"
    suggestion_id: str = ""
    suggestion_type: str = "advisor_review"
    source: str = "local_scan"
    trigger_reason: str = ""
    affected_templates: list[str] = field(default_factory=list)
    affected_providers: list[str] = field(default_factory=list)
    capability_scope: list[str] = field(default_factory=list)
    risk_level: str = "low"
    recommended_action: str = ""
    requires_operator_approval: bool = True
    advisor_call_allowed: bool = False
    advisor_call_mode: str = "local_scan_only"
    review_status: str = "pending_review"
    safety_flags: AdvisorReviewQueueSafetyFlags = field(default_factory=AdvisorReviewQueueSafetyFlags)
    created_at: str = ""
    updated_at: str = ""
    operator_decision: str = "pending_review"
    linked_advisor_review_ids: list[str] = field(default_factory=list)
    linked_proposal_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_empty_advisor_review_queue_item(
    suggestion_id: str = "",
    trigger_reason: str = "",
    recommended_action: str = "",
    **overrides: Any,
) -> AdvisorReviewQueueItem:
    """Create a schema-only queue item with safe defaults."""
    now = _utc_now()
    item = AdvisorReviewQueueItem(
        suggestion_id=suggestion_id,
        trigger_reason=trigger_reason,
        recommended_action=recommended_action,
        created_at=now,
        updated_at=now,
    )
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown advisor review queue item field: {key}")
        setattr(item, key, value)
    return item


def advisor_review_queue_item_to_dict(item: AdvisorReviewQueueItem) -> dict[str, Any]:
    """Serialize an advisor-review queue item to a plain dict."""
    return asdict(item)


def advisor_review_queue_item_from_dict(data: dict[str, Any]) -> AdvisorReviewQueueItem:
    """Deserialize an advisor-review queue item from a plain dict."""
    payload = dict(data)
    flags = payload.get("safety_flags")
    if isinstance(flags, AdvisorReviewQueueSafetyFlags):
        payload["safety_flags"] = flags
    elif isinstance(flags, dict):
        payload["safety_flags"] = AdvisorReviewQueueSafetyFlags(**flags)
    elif flags is None:
        payload["safety_flags"] = AdvisorReviewQueueSafetyFlags()
    return AdvisorReviewQueueItem(**payload)


def _summary_text_fields(item: AdvisorReviewQueueItem) -> list[str]:
    values: list[str] = [
        item.suggestion_id,
        item.suggestion_type,
        item.source,
        item.trigger_reason,
        item.risk_level,
        item.recommended_action,
        item.advisor_call_mode,
        item.review_status,
        item.operator_decision,
    ]
    values.extend(item.affected_templates)
    values.extend(item.affected_providers)
    values.extend(item.capability_scope)
    values.extend(item.linked_advisor_review_ids)
    values.extend(item.linked_proposal_ids)
    values.extend(item.notes)
    return [v for v in values if isinstance(v, str)]


def _detect_sensitive_text(item: AdvisorReviewQueueItem) -> list[str]:
    joined = "\n".join(_summary_text_fields(item))
    findings: list[str] = []
    for label, pattern in SENSITIVE_TEXT_PATTERNS.items():
        if pattern.search(joined):
            findings.append(label)
    return findings


def validate_advisor_review_queue_item(item: AdvisorReviewQueueItem) -> list[str]:
    """Return validation errors for an advisor-review queue item."""
    errors: list[str] = []

    if not item.suggestion_id.strip():
        errors.append("missing suggestion_id")
    if item.suggestion_type not in ALLOWED_SUGGESTION_TYPES:
        errors.append("invalid suggestion_type")
    if item.source not in ALLOWED_SOURCES:
        errors.append("invalid source")
    if item.risk_level not in ALLOWED_RISK_LEVELS:
        errors.append("invalid risk_level")
    if item.advisor_call_mode not in ALLOWED_ADVISOR_CALL_MODES:
        errors.append("invalid advisor_call_mode")
    if item.review_status not in ALLOWED_REVIEW_STATUSES:
        errors.append("invalid review_status")
    if item.operator_decision not in ALLOWED_OPERATOR_DECISIONS:
        errors.append("invalid operator_decision")
    if item.requires_operator_approval is False:
        errors.append("requires_operator_approval must remain true")
    if item.advisor_call_allowed and item.advisor_call_mode == "local_scan_only":
        errors.append("advisor_call_allowed true is incompatible with local_scan_only")
    if not item.recommended_action.strip():
        errors.append("empty recommended_action")
    if item.risk_level == "high" and not item.notes:
        errors.append("high risk item requires notes")

    flags = item.safety_flags
    for field_name, label in PROHIBITED_SAFETY_FLAG_FIELDS.items():
        if getattr(flags, field_name):
            errors.append(label)

    for finding in _detect_sensitive_text(item):
        errors.append(finding)

    return errors


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in SENSITIVE_TEXT_PATTERNS.values():
        redacted = pattern.sub(SUMMARY_REDACTION, redacted)
    return redacted


def summarize_advisor_review_queue_item(item: AdvisorReviewQueueItem) -> dict[str, Any]:
    """Return a redacted/count-only summary for a single queue item."""
    validation_errors = validate_advisor_review_queue_item(item)
    return {
        "schema_version": item.schema_version,
        "suggestion_id": _redact_text(item.suggestion_id),
        "suggestion_type": item.suggestion_type,
        "source": item.source,
        "risk_level": item.risk_level,
        "advisor_call_mode": item.advisor_call_mode,
        "review_status": item.review_status,
        "operator_decision": item.operator_decision,
        "requires_operator_approval": item.requires_operator_approval,
        "advisor_call_allowed": item.advisor_call_allowed,
        "affected_template_count": len(item.affected_templates),
        "affected_provider_count": len(item.affected_providers),
        "capability_scope_count": len(item.capability_scope),
        "note_count": len(item.notes),
        "linked_advisor_review_count": len(item.linked_advisor_review_ids),
        "linked_proposal_count": len(item.linked_proposal_ids),
        "safety_error_count": sum(1 for name in PROHIBITED_SAFETY_FLAG_FIELDS if getattr(item.safety_flags, name)),
        "validation_error_count": len(validation_errors),
        "contains_redactions": bool(_detect_sensitive_text(item)),
    }


def summarize_advisor_review_queue_items(items: list[AdvisorReviewQueueItem]) -> dict[str, Any]:
    """Return redacted/count-only summary statistics for multiple queue items."""
    by_status: dict[str, int] = {}
    by_risk_level: dict[str, int] = {}
    by_source: dict[str, int] = {}
    validation_error_count = 0
    redaction_count = 0

    for item in items:
        by_status[item.review_status] = by_status.get(item.review_status, 0) + 1
        by_risk_level[item.risk_level] = by_risk_level.get(item.risk_level, 0) + 1
        by_source[item.source] = by_source.get(item.source, 0) + 1
        validation_error_count += len(validate_advisor_review_queue_item(item))
        if _detect_sensitive_text(item):
            redaction_count += 1

    return {
        "item_count": len(items),
        "by_status": by_status,
        "by_risk_level": by_risk_level,
        "by_source": by_source,
        "validation_error_count": validation_error_count,
        "redaction_count": redaction_count,
        "summary_mode": "redacted_count_only",
    }
