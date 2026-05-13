"""WESLR Local-Scan Advisor Review Schema V1.

Schema-only dataclasses and validation helpers for future local-scan advisor
review findings and reports. This module does not implement scanning,
persistence, queue creation, scheduling, daemon behavior, model calls, prompt
mutation, provider activation, or runtime/config changes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import re


ALLOWED_FINDING_TYPES = {
    "stale_prompt_template",
    "missing_template_coverage",
    "provider_health_note",
    "provider_registry_gap",
    "capability_scope_gap",
    "safety_policy_drift",
    "unsupported_gap_trend",
    "review_due",
    "unknown",
}

ALLOWED_RISK_LEVELS = {"low", "medium", "high", "unknown"}
ALLOWED_ADVISOR_CALL_MODES = {"local_scan_only", "operator_approved_advisor_call", "disabled"}
ALLOWED_SCAN_MODES = {"local_scan_only", "dry_run", "manual_review_only"}

UNSAFE_SAFETY_FLAG_FIELDS = {
    "external_model_call_attempted": "external model call attempted",
    "advisor_call_attempted": "advisor call attempted",
    "queue_item_created": "queue item created",
    "prompt_mutation_requested": "prompt mutation requested",
    "provider_activation_requested": "provider activation requested",
    "provider_registry_mutation_requested": "provider registry mutation requested",
    "runtime_action_requested": "runtime action requested",
    "runtime_config_change_requested": "runtime/config change requested",
    "memory_mutation_requested": "memory mutation requested",
    "governance_override_requested": "governance override requested",
    "answer_selection_requested": "answer selection requested",
    "truth_authority_requested": "truth authority requested",
    "soundness_authority_requested": "soundness authority requested",
    "official_score_requested": "official score requested",
    "answer_key_requested": "answer key requested",
    "raw_benchmark_text_requested": "raw benchmark text requested",
    "secrets_requested": "secrets requested",
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

PROHIBITED_ACTION_PATTERNS = {
    "possible model call request": re.compile(r"call model|run advisor|invoke advisor|external model", re.IGNORECASE),
    "possible provider activation request": re.compile(r"activate provider|enable provider", re.IGNORECASE),
    "possible prompt mutation request": re.compile(r"edit prompt|mutate prompt|rewrite prompt|update prompt", re.IGNORECASE),
    "possible config mutation request": re.compile(r"update config|change runtime|runtime config", re.IGNORECASE),
    "possible memory mutation request": re.compile(r"write memory|mutate memory|edit memory", re.IGNORECASE),
    "possible governance override request": re.compile(r"override governance|bypass governance", re.IGNORECASE),
    "possible answer selection request": re.compile(r"select answer|choose answer|pick answer", re.IGNORECASE),
    "possible truth authority request": re.compile(r"prove true|claim truth|truth authority", re.IGNORECASE),
    "possible soundness authority request": re.compile(r"soundness claim|claim sound|prove sound", re.IGNORECASE),
    "possible official score request": re.compile(r"official score|score claim", re.IGNORECASE),
}

SUMMARY_REDACTION = "[redacted]"


@dataclass
class LocalScanSafetyFlags:
    external_model_call_attempted: bool = False
    advisor_call_attempted: bool = False
    queue_item_created: bool = False
    prompt_mutation_requested: bool = False
    provider_activation_requested: bool = False
    provider_registry_mutation_requested: bool = False
    runtime_action_requested: bool = False
    runtime_config_change_requested: bool = False
    memory_mutation_requested: bool = False
    governance_override_requested: bool = False
    answer_selection_requested: bool = False
    truth_authority_requested: bool = False
    soundness_authority_requested: bool = False
    official_score_requested: bool = False
    answer_key_requested: bool = False
    raw_benchmark_text_requested: bool = False
    secrets_requested: bool = False


@dataclass
class LocalScanFinding:
    schema_version: str = "1.0"
    finding_id: str = ""
    finding_type: str = "unknown"
    source_artifact: str = ""
    trigger_reason: str = ""
    affected_templates: list[str] = field(default_factory=list)
    affected_providers: list[str] = field(default_factory=list)
    capability_scope: list[str] = field(default_factory=list)
    risk_level: str = "low"
    recommended_action: str = ""
    suggested_queue_type: str = "advisor_review"
    requires_operator_approval: bool = True
    advisor_call_mode: str = "local_scan_only"
    advisor_call_allowed: bool = False
    evidence_summary: str = ""
    notes: list[str] = field(default_factory=list)
    safety_flags: LocalScanSafetyFlags = field(default_factory=LocalScanSafetyFlags)


@dataclass
class LocalScanReport:
    schema_version: str = "1.0"
    scan_id: str = ""
    scan_mode: str = "local_scan_only"
    trigger_reason: str = ""
    findings: list[LocalScanFinding] = field(default_factory=list)
    summary: str = ""
    would_create_queue_items: bool = False
    external_model_calls_made: bool = False
    runtime_changes_made: bool = False
    created_at: str = ""
    safety_flags: LocalScanSafetyFlags = field(default_factory=LocalScanSafetyFlags)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_empty_local_scan_finding(
    finding_id: str = "",
    trigger_reason: str = "",
    recommended_action: str = "",
    **overrides: Any,
) -> LocalScanFinding:
    finding = LocalScanFinding(
        finding_id=finding_id,
        trigger_reason=trigger_reason,
        recommended_action=recommended_action,
    )
    for key, value in overrides.items():
        if not hasattr(finding, key):
            raise ValueError(f"unknown local scan finding field: {key}")
        setattr(finding, key, value)
    return finding


def create_empty_local_scan_report(
    scan_id: str = "",
    trigger_reason: str = "",
    summary: str = "",
    findings: list[LocalScanFinding] | None = None,
    **overrides: Any,
) -> LocalScanReport:
    report = LocalScanReport(
        scan_id=scan_id,
        trigger_reason=trigger_reason,
        summary=summary,
        findings=list(findings or []),
        created_at=_utc_now(),
    )
    for key, value in overrides.items():
        if not hasattr(report, key):
            raise ValueError(f"unknown local scan report field: {key}")
        setattr(report, key, value)
    return report


def local_scan_finding_to_dict(finding: LocalScanFinding) -> dict[str, Any]:
    return asdict(finding)


def local_scan_finding_from_dict(data: dict[str, Any]) -> LocalScanFinding:
    payload = dict(data)
    flags = payload.get("safety_flags")
    if isinstance(flags, LocalScanSafetyFlags):
        payload["safety_flags"] = flags
    elif isinstance(flags, dict):
        payload["safety_flags"] = LocalScanSafetyFlags(**flags)
    elif flags is None:
        payload["safety_flags"] = LocalScanSafetyFlags()
    return LocalScanFinding(**payload)


def local_scan_report_to_dict(report: LocalScanReport) -> dict[str, Any]:
    return asdict(report)


def local_scan_report_from_dict(data: dict[str, Any]) -> LocalScanReport:
    payload = dict(data)
    flags = payload.get("safety_flags")
    if isinstance(flags, LocalScanSafetyFlags):
        payload["safety_flags"] = flags
    elif isinstance(flags, dict):
        payload["safety_flags"] = LocalScanSafetyFlags(**flags)
    elif flags is None:
        payload["safety_flags"] = LocalScanSafetyFlags()
    payload["findings"] = [
        finding if isinstance(finding, LocalScanFinding) else local_scan_finding_from_dict(finding)
        for finding in payload.get("findings", [])
    ]
    return LocalScanReport(**payload)


def _safety_flag_errors(flags: LocalScanSafetyFlags) -> list[str]:
    return [label for field_name, label in UNSAFE_SAFETY_FLAG_FIELDS.items() if getattr(flags, field_name)]


def _finding_text_fields(finding: LocalScanFinding) -> list[str]:
    values: list[str] = [
        finding.finding_id,
        finding.finding_type,
        finding.source_artifact,
        finding.trigger_reason,
        finding.risk_level,
        finding.recommended_action,
        finding.suggested_queue_type,
        finding.advisor_call_mode,
        finding.evidence_summary,
    ]
    values.extend(finding.affected_templates)
    values.extend(finding.affected_providers)
    values.extend(finding.capability_scope)
    values.extend(finding.notes)
    return [value for value in values if isinstance(value, str)]


def _report_text_fields(report: LocalScanReport) -> list[str]:
    values = [report.scan_id, report.scan_mode, report.trigger_reason, report.summary]
    for finding in report.findings:
        values.extend(_finding_text_fields(finding))
    return [value for value in values if isinstance(value, str)]


def _detect_text_risks(values: list[str]) -> list[str]:
    joined = "\n".join(values)
    findings: list[str] = []
    for label, pattern in SENSITIVE_TEXT_PATTERNS.items():
        if pattern.search(joined):
            findings.append(label)
    for label, pattern in PROHIBITED_ACTION_PATTERNS.items():
        if pattern.search(joined):
            findings.append(label)
    return findings


def validate_local_scan_finding(finding: LocalScanFinding) -> list[str]:
    errors: list[str] = []
    if not finding.finding_id.strip():
        errors.append("missing finding_id")
    if finding.finding_type not in ALLOWED_FINDING_TYPES:
        errors.append("invalid finding_type")
    if finding.risk_level not in ALLOWED_RISK_LEVELS:
        errors.append("invalid risk_level")
    if finding.advisor_call_mode not in ALLOWED_ADVISOR_CALL_MODES:
        errors.append("invalid advisor_call_mode")
    if not finding.recommended_action.strip():
        errors.append("missing recommended_action")
    if finding.requires_operator_approval is False:
        errors.append("requires_operator_approval must remain true")
    if finding.advisor_call_allowed and finding.advisor_call_mode == "local_scan_only":
        errors.append("advisor_call_allowed true is incompatible with local_scan_only")
    if finding.advisor_call_mode != "local_scan_only" and finding.advisor_call_allowed is False:
        errors.append("non-local scan advisor call mode requires explicit approval path")
    errors.extend(_safety_flag_errors(finding.safety_flags))
    errors.extend(_detect_text_risks(_finding_text_fields(finding)))
    return errors


def validate_local_scan_report(report: LocalScanReport) -> list[str]:
    errors: list[str] = []
    if not report.scan_id.strip():
        errors.append("missing scan_id")
    if report.scan_mode not in ALLOWED_SCAN_MODES:
        errors.append("invalid scan_mode")
    if report.would_create_queue_items:
        errors.append("would_create_queue_items must remain false")
    if report.external_model_calls_made:
        errors.append("external_model_calls_made must remain false")
    if report.runtime_changes_made:
        errors.append("runtime_changes_made must remain false")
    errors.extend(_safety_flag_errors(report.safety_flags))
    errors.extend(_detect_text_risks(_report_text_fields(report)))
    for index, finding in enumerate(report.findings):
        for error in validate_local_scan_finding(finding):
            errors.append(f"finding[{index}]: {error}")
    return errors


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in list(SENSITIVE_TEXT_PATTERNS.values()) + list(PROHIBITED_ACTION_PATTERNS.values()):
        redacted = pattern.sub(SUMMARY_REDACTION, redacted)
    return redacted


def summarize_local_scan_finding(finding: LocalScanFinding) -> dict[str, Any]:
    validation_errors = validate_local_scan_finding(finding)
    return {
        "schema_version": finding.schema_version,
        "finding_id": _redact_text(finding.finding_id),
        "finding_type": finding.finding_type,
        "source_artifact_present": bool(finding.source_artifact),
        "risk_level": finding.risk_level,
        "suggested_queue_type": finding.suggested_queue_type,
        "requires_operator_approval": finding.requires_operator_approval,
        "advisor_call_mode": finding.advisor_call_mode,
        "advisor_call_allowed": finding.advisor_call_allowed,
        "affected_template_count": len(finding.affected_templates),
        "affected_provider_count": len(finding.affected_providers),
        "capability_scope_count": len(finding.capability_scope),
        "note_count": len(finding.notes),
        "safety_error_count": len(_safety_flag_errors(finding.safety_flags)),
        "validation_error_count": len(validation_errors),
        "contains_redactions": bool(_detect_text_risks(_finding_text_fields(finding))),
    }


def summarize_local_scan_report(report: LocalScanReport) -> dict[str, Any]:
    by_type: dict[str, int] = {}
    by_risk_level: dict[str, int] = {}
    validation_error_count = len(validate_local_scan_report(report))
    redaction_count = 1 if _detect_text_risks(_report_text_fields(report)) else 0

    for finding in report.findings:
        by_type[finding.finding_type] = by_type.get(finding.finding_type, 0) + 1
        by_risk_level[finding.risk_level] = by_risk_level.get(finding.risk_level, 0) + 1

    return {
        "schema_version": report.schema_version,
        "scan_id": _redact_text(report.scan_id),
        "scan_mode": report.scan_mode,
        "finding_count": len(report.findings),
        "by_finding_type": by_type,
        "by_risk_level": by_risk_level,
        "would_create_queue_items": report.would_create_queue_items,
        "external_model_calls_made": report.external_model_calls_made,
        "runtime_changes_made": report.runtime_changes_made,
        "safety_error_count": len(_safety_flag_errors(report.safety_flags)),
        "validation_error_count": validation_error_count,
        "redaction_count": redaction_count,
        "summary_mode": "redacted_count_only",
    }
