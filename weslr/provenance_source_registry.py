"""WESLR Provenance Source Registry Schema V1.

Schema-only dataclasses and validation helpers for future living provenance
source registry entries. This module does not create registry files, seed
entries, scan sources, write queues, call advisors/models, activate
self-improvement, wire runtime/chat/voice/proactive behavior, or change config.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import re


ALLOWED_SOURCE_TYPES = {
    "chat_surface",
    "voice_surface",
    "ambient_loop",
    "proactive_suggestion",
    "advisor_review",
    "capability_guidance",
    "memory_capture",
    "state_checkpoint",
    "teaching_explanation",
    "operator_cli",
    "external_provider",
    "institution_extension",
    "self_review",
    "self_improvement_candidate",
    "unknown",
}

ALLOWED_ORIGIN_TYPES = {
    "operator_added",
    "institution_added",
    "advisor_suggested",
    "local_scan_suggested",
    "weslr_self_review_suggested",
    "self_improvement_proposed",
    "unknown",
}

ALLOWED_APPROVAL_STATUSES = {
    "proposed",
    "under_review",
    "approved",
    "rejected",
    "active",
    "deprecated",
    "blocked",
    "unknown",
}

ALLOWED_STATUSES = {"active", "experimental", "deprecated", "blocked", "unknown"}

ALLOWED_OPERATOR_DECISIONS = {
    "pending_review",
    "approved",
    "approved_with_changes",
    "rejected",
    "deferred",
}

PROHIBITED_SAFETY_FLAG_FIELDS = {
    "hidden_llm_authority": "hidden LLM authority",
    "provenance_guessing_allowed": "provenance guessing allowed",
    "unregistered_voice_or_proactive_output_allowed": "unregistered voice/proactive output allowed",
    "unregistered_self_improvement_output_allowed": "unregistered self-improvement output allowed",
    "hidden_memory_mutation_allowed": "hidden memory mutation allowed",
    "hidden_queue_write_allowed": "hidden queue write allowed",
    "hidden_runtime_action_allowed": "hidden runtime action allowed",
    "automatic_activation_allowed": "automatic activation allowed",
    "automatic_self_improvement_deployment_allowed": "automatic self-improvement deployment allowed",
    "answer_selection_allowed": "answer selection allowed",
    "truth_authority_allowed": "truth authority allowed",
    "soundness_authority_allowed": "soundness authority allowed",
    "official_score_claim_allowed": "official score claim allowed",
    "raw_sensitive_content_storage_allowed": "raw sensitive content storage allowed",
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
class ProvenanceSourceSafetyFlags:
    hidden_llm_authority: bool = False
    provenance_guessing_allowed: bool = False
    unregistered_voice_or_proactive_output_allowed: bool = False
    unregistered_self_improvement_output_allowed: bool = False
    hidden_memory_mutation_allowed: bool = False
    hidden_queue_write_allowed: bool = False
    hidden_runtime_action_allowed: bool = False
    automatic_activation_allowed: bool = False
    automatic_self_improvement_deployment_allowed: bool = False
    answer_selection_allowed: bool = False
    truth_authority_allowed: bool = False
    soundness_authority_allowed: bool = False
    official_score_claim_allowed: bool = False
    raw_sensitive_content_storage_allowed: bool = False


@dataclass
class ProvenanceSourceEntry:
    schema_version: str = "1.0"
    source_id: str = ""
    display_name: str = ""
    module_path: str = ""
    source_type: str = "unknown"
    authority_boundary: str = ""
    allowed_outputs: list[str] = field(default_factory=list)
    forbidden_outputs: list[str] = field(default_factory=list)
    llm_assisted: bool = False
    advisor_assisted: bool = False
    operator_review_required: bool = True
    introduced_in_commit: str = ""
    last_reviewed_commit: str = ""
    capability_scope: list[str] = field(default_factory=list)
    status: str = "unknown"
    owner: str = ""
    related_docs: list[str] = field(default_factory=list)
    related_tests: list[str] = field(default_factory=list)
    proposed_by: str = ""
    origin_type: str = "unknown"
    approval_status: str = "proposed"
    operator_decision: str = "pending_review"
    created_from_proposal_id: str = ""
    created_from_advisor_review_id: str = ""
    created_from_queue_item_id: str = ""
    validation_required: bool = True
    tests_required: bool = True
    activation_allowed: bool = False
    safety_flags: ProvenanceSourceSafetyFlags = field(default_factory=ProvenanceSourceSafetyFlags)


@dataclass
class ProvenanceSourceRegistrySummary:
    schema_version: str = "1.0"
    entry_count: int = 0
    active_count: int = 0
    experimental_count: int = 0
    blocked_count: int = 0
    unknown_count: int = 0
    self_improvement_related_count: int = 0
    operator_review_required_count: int = 0
    missing_tests_count: int = 0
    missing_docs_count: int = 0


def create_empty_provenance_source_entry(
    source_id: str = "",
    display_name: str = "",
    **overrides: Any,
) -> ProvenanceSourceEntry:
    """Create a schema-only provenance source entry with safe defaults."""
    item = ProvenanceSourceEntry(source_id=source_id, display_name=display_name)
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown provenance source entry field: {key}")
        setattr(item, key, value)
    return item


def provenance_source_entry_to_dict(item: ProvenanceSourceEntry) -> dict[str, Any]:
    """Serialize a provenance source entry to a plain dict."""
    return asdict(item)


def provenance_source_entry_from_dict(data: dict[str, Any]) -> ProvenanceSourceEntry:
    """Deserialize a provenance source entry from a plain dict."""
    payload = dict(data)
    flags = payload.get("safety_flags")
    if isinstance(flags, ProvenanceSourceSafetyFlags):
        payload["safety_flags"] = flags
    elif isinstance(flags, dict):
        payload["safety_flags"] = ProvenanceSourceSafetyFlags(**flags)
    elif flags is None:
        payload["safety_flags"] = ProvenanceSourceSafetyFlags()
    return ProvenanceSourceEntry(**payload)


def _text_fields(item: ProvenanceSourceEntry) -> list[str]:
    values = [
        item.source_id,
        item.display_name,
        item.module_path,
        item.source_type,
        item.authority_boundary,
        item.status,
        item.owner,
        item.proposed_by,
        item.origin_type,
        item.approval_status,
        item.operator_decision,
        item.created_from_proposal_id,
        item.created_from_advisor_review_id,
        item.created_from_queue_item_id,
    ]
    values.extend(item.allowed_outputs)
    values.extend(item.forbidden_outputs)
    values.extend(item.capability_scope)
    values.extend(item.related_docs)
    values.extend(item.related_tests)
    return [v for v in values if isinstance(v, str)]


def _detect_sensitive_text(item: ProvenanceSourceEntry) -> list[str]:
    joined = "\n".join(_text_fields(item))
    findings: list[str] = []
    for label, pattern in SENSITIVE_TEXT_PATTERNS.items():
        if pattern.search(joined):
            findings.append(label)
    return findings


def _has_proposal_or_advisor_reference(item: ProvenanceSourceEntry) -> bool:
    return bool(item.created_from_proposal_id.strip() or item.created_from_advisor_review_id.strip())


def _has_any_origin_reference(item: ProvenanceSourceEntry) -> bool:
    return bool(
        item.created_from_proposal_id.strip()
        or item.created_from_advisor_review_id.strip()
        or item.created_from_queue_item_id.strip()
    )


def _operator_approved(item: ProvenanceSourceEntry) -> bool:
    return item.operator_decision in {"approved", "approved_with_changes"} and item.approval_status in {"approved", "active"}


def validate_provenance_source_entry(item: ProvenanceSourceEntry) -> list[str]:
    """Return validation errors for a provenance source registry entry."""
    errors: list[str] = []

    if not item.source_id.strip():
        errors.append("missing source_id")
    if not item.display_name.strip():
        errors.append("missing display_name")
    if item.source_type not in ALLOWED_SOURCE_TYPES:
        errors.append("invalid source_type")
    if item.origin_type not in ALLOWED_ORIGIN_TYPES:
        errors.append("invalid origin_type")
    if item.approval_status not in ALLOWED_APPROVAL_STATUSES:
        errors.append("invalid approval_status")
    if item.status not in ALLOWED_STATUSES:
        errors.append("invalid status")
    if item.operator_decision not in ALLOWED_OPERATOR_DECISIONS:
        errors.append("invalid operator_decision")
    if not item.authority_boundary.strip():
        errors.append("empty authority_boundary")
    if not item.allowed_outputs:
        errors.append("empty allowed_outputs")
    if not item.forbidden_outputs:
        errors.append("empty forbidden_outputs")
    if item.operator_review_required is False:
        errors.append("operator_review_required must remain true")
    if item.validation_required is False:
        errors.append("validation_required must remain true")
    if item.tests_required is False:
        errors.append("tests_required must remain true")

    if item.activation_allowed:
        if not _operator_approved(item):
            errors.append("activation_allowed requires approved operator decision")
        if not item.related_tests:
            errors.append("activation_allowed requires related_tests")
        if not item.related_docs:
            errors.append("activation_allowed requires related_docs")
    if item.status == "active" and not item.activation_allowed:
        errors.append("status active requires activation_allowed")
    if item.approval_status == "active" and not item.activation_allowed:
        errors.append("approval_status active requires activation_allowed")

    if item.origin_type == "self_improvement_proposed" and item.activation_allowed:
        if not (_operator_approved(item) and item.related_tests and item.related_docs and item.created_from_proposal_id.strip()):
            errors.append("self_improvement_proposed cannot auto-activate")
    if item.origin_type == "weslr_self_review_suggested" and item.activation_allowed:
        errors.append("weslr_self_review_suggested cannot auto-activate")
    if item.origin_type == "advisor_suggested" and not _has_proposal_or_advisor_reference(item):
        errors.append("advisor_suggested requires advisor/proposal reference")
    if item.origin_type == "local_scan_suggested" and not (item.created_from_queue_item_id.strip() or item.created_from_proposal_id.strip()):
        errors.append("local_scan_suggested requires queue/proposal reference")
    if item.origin_type == "self_improvement_proposed" and not item.created_from_proposal_id.strip():
        errors.append("self_improvement_proposed requires created_from_proposal_id")
    if item.origin_type in {"advisor_suggested", "local_scan_suggested", "self_improvement_proposed", "weslr_self_review_suggested"} and not _has_any_origin_reference(item):
        errors.append("suggested origin requires lifecycle reference")

    if item.llm_assisted and not item.authority_boundary.strip():
        errors.append("llm_assisted requires clear authority_boundary")
    if item.advisor_assisted and not _has_proposal_or_advisor_reference(item):
        errors.append("advisor_assisted requires advisor/proposal reference")

    for field_name, label in PROHIBITED_SAFETY_FLAG_FIELDS.items():
        if getattr(item.safety_flags, field_name):
            errors.append(label)

    for finding in _detect_sensitive_text(item):
        errors.append(finding)

    return errors


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in SENSITIVE_TEXT_PATTERNS.values():
        redacted = pattern.sub(SUMMARY_REDACTION, redacted)
    return redacted


def summarize_provenance_source_entry(item: ProvenanceSourceEntry) -> dict[str, Any]:
    """Return a redacted/count-only summary for one source entry."""
    validation_errors = validate_provenance_source_entry(item)
    return {
        "schema_version": item.schema_version,
        "source_id": _redact_text(item.source_id),
        "display_name": _redact_text(item.display_name),
        "source_type": item.source_type,
        "origin_type": item.origin_type,
        "approval_status": item.approval_status,
        "status": item.status,
        "operator_decision": item.operator_decision,
        "llm_assisted": item.llm_assisted,
        "advisor_assisted": item.advisor_assisted,
        "operator_review_required": item.operator_review_required,
        "validation_required": item.validation_required,
        "tests_required": item.tests_required,
        "activation_allowed": item.activation_allowed,
        "allowed_output_count": len(item.allowed_outputs),
        "forbidden_output_count": len(item.forbidden_outputs),
        "capability_scope_count": len(item.capability_scope),
        "related_doc_count": len(item.related_docs),
        "related_test_count": len(item.related_tests),
        "has_proposal_reference": bool(item.created_from_proposal_id.strip()),
        "has_advisor_review_reference": bool(item.created_from_advisor_review_id.strip()),
        "has_queue_item_reference": bool(item.created_from_queue_item_id.strip()),
        "safety_error_count": sum(1 for name in PROHIBITED_SAFETY_FLAG_FIELDS if getattr(item.safety_flags, name)),
        "validation_error_count": len(validation_errors),
        "contains_redactions": bool(_detect_sensitive_text(item)),
        "summary_mode": "redacted_count_only",
    }


def summarize_provenance_source_entries(items: list[ProvenanceSourceEntry]) -> dict[str, Any]:
    """Return redacted/count-only summary statistics for source entries."""
    by_status: dict[str, int] = {}
    by_source_type: dict[str, int] = {}
    by_origin_type: dict[str, int] = {}
    validation_error_count = 0
    redaction_count = 0
    self_improvement_related_count = 0
    operator_review_required_count = 0
    missing_tests_count = 0
    missing_docs_count = 0

    for item in items:
        by_status[item.status] = by_status.get(item.status, 0) + 1
        by_source_type[item.source_type] = by_source_type.get(item.source_type, 0) + 1
        by_origin_type[item.origin_type] = by_origin_type.get(item.origin_type, 0) + 1
        validation_error_count += len(validate_provenance_source_entry(item))
        if _detect_sensitive_text(item):
            redaction_count += 1
        if item.origin_type in {"self_improvement_proposed", "weslr_self_review_suggested"} or item.source_type == "self_improvement_candidate":
            self_improvement_related_count += 1
        if item.operator_review_required:
            operator_review_required_count += 1
        if not item.related_tests:
            missing_tests_count += 1
        if not item.related_docs:
            missing_docs_count += 1

    return {
        "schema_version": "1.0",
        "entry_count": len(items),
        "active_count": by_status.get("active", 0),
        "experimental_count": by_status.get("experimental", 0),
        "blocked_count": by_status.get("blocked", 0),
        "unknown_count": by_status.get("unknown", 0),
        "self_improvement_related_count": self_improvement_related_count,
        "operator_review_required_count": operator_review_required_count,
        "missing_tests_count": missing_tests_count,
        "missing_docs_count": missing_docs_count,
        "by_status": by_status,
        "by_source_type": by_source_type,
        "by_origin_type": by_origin_type,
        "validation_error_count": validation_error_count,
        "redaction_count": redaction_count,
        "summary_mode": "redacted_count_only",
    }
