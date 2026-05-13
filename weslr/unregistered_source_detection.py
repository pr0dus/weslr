"""WESLR Unregistered Source Detection Schema V1.

Schema-only dataclasses and validation helpers for future unregistered-source
findings and reports. This module does not scan files, create registry
persistence, write queues, call models/advisors, activate self-improvement,
wire runtime/chat/voice/proactive behavior, select answers, claim
truth/soundness, or claim official scores.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import re


ALLOWED_FINDING_TYPES = {
    "unregistered_source_candidate",
    "missing_source_registry_entry",
    "stale_source_registry_entry",
    "source_without_tests",
    "source_without_docs",
    "unknown_source_in_provenance",
    "unregistered_voice_or_proactive_source",
    "unregistered_self_improvement_source",
    "source_authority_boundary_missing",
    "source_activation_policy_inconsistent",
    "unknown",
}

ALLOWED_DETECTION_SIGNALS = {
    "module_name_output_like",
    "suggestion_generation_function",
    "voice_or_proactive_behavior",
    "advisor_review_behavior",
    "queue_or_review_behavior",
    "memory_write_behavior",
    "routing_or_decision_behavior",
    "self_review_behavior",
    "self_improvement_behavior",
    "doc_reference",
    "test_reference",
    "provenance_unknown_source",
    "seed_entry_stale_or_incomplete",
    "unknown",
}

ALLOWED_CANDIDATE_SOURCE_TYPES = {
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

ALLOWED_AUTHORITY_LEVELS = {
    "unknown",
    "internal_diagnostic",
    "suggestion",
    "advisor_proposal",
}

ALLOWED_RISK_LEVELS = {"low", "medium", "high", "unknown"}
ALLOWED_SCAN_MODES = {"schema_only", "dry_run", "local_scan_only", "manual_review_only"}

UNREGISTERED_FINDING_TYPES_REQUIRING_SOURCE_ID = {
    "unregistered_source_candidate",
    "missing_source_registry_entry",
    "unregistered_voice_or_proactive_source",
    "unregistered_self_improvement_source",
}

PROHIBITED_SAFETY_FLAG_FIELDS = {
    "auto_registration_attempted": "auto registration attempted",
    "auto_activation_attempted": "auto activation attempted",
    "queue_write_attempted": "queue write attempted",
    "registry_persistence_attempted": "registry persistence attempted",
    "runtime_wiring_attempted": "runtime wiring attempted",
    "memory_mutation_attempted": "memory mutation attempted",
    "external_model_call_attempted": "external model call attempted",
    "advisor_call_attempted": "advisor call attempted",
    "self_improvement_activation_attempted": "self-improvement activation attempted",
    "provenance_guessing_attempted": "provenance guessing attempted",
    "answer_selection_attempted": "answer selection attempted",
    "truth_authority_claimed": "truth authority claimed",
    "soundness_authority_claimed": "soundness authority claimed",
    "official_score_claimed": "official score claimed",
    "raw_sensitive_content_stored": "raw sensitive content stored",
}

SENSITIVE_TEXT_PATTERNS = {
    "possible API key": re.compile(r"api[_ -]?key|sk-[A-Za-z0-9]|AIza[0-9A-Za-z_-]", re.IGNORECASE),
    "possible token": re.compile(r"\btoken\b|bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
    "possible secret": re.compile(r"\bsecret\b|password\s*[:=]", re.IGNORECASE),
    "possible raw benchmark text": re.compile(r"raw benchmark|benchmark text|question stem|passage:", re.IGNORECASE),
    "possible answer key": re.compile(r"answer[_ -]?key|official solution|correct answer", re.IGNORECASE),
    "possible official score": re.compile(r"official score|benchmark score", re.IGNORECASE),
    "possible private user data": re.compile(r"private user data|ssn|social security|passport", re.IGNORECASE),
}

SUMMARY_REDACTION = "[redacted]"


@dataclass
class UnregisteredSourceDetectionSafetyFlags:
    auto_registration_attempted: bool = False
    auto_activation_attempted: bool = False
    queue_write_attempted: bool = False
    registry_persistence_attempted: bool = False
    runtime_wiring_attempted: bool = False
    memory_mutation_attempted: bool = False
    external_model_call_attempted: bool = False
    advisor_call_attempted: bool = False
    self_improvement_activation_attempted: bool = False
    provenance_guessing_attempted: bool = False
    answer_selection_attempted: bool = False
    truth_authority_claimed: bool = False
    soundness_authority_claimed: bool = False
    official_score_claimed: bool = False
    raw_sensitive_content_stored: bool = False


@dataclass
class UnregisteredSourceFinding:
    schema_version: str = "1.0"
    finding_id: str = ""
    finding_type: str = "unknown"
    candidate_source_id: str = ""
    candidate_module_path: str = ""
    candidate_source_type: str = "unknown"
    detection_signal: str = "unknown"
    evidence_summary: str = ""
    matched_registry_entry_id: str = ""
    is_registered: bool = False
    authority_level: str = "unknown"
    operator_review_required: bool = True
    recommended_action: str = ""
    risk_level: str = "low"
    created_at: str = ""
    related_docs: list[str] = field(default_factory=list)
    related_tests: list[str] = field(default_factory=list)
    related_queue_item_ids: list[str] = field(default_factory=list)
    safety_flags: UnregisteredSourceDetectionSafetyFlags = field(default_factory=UnregisteredSourceDetectionSafetyFlags)


@dataclass
class UnregisteredSourceDetectionReport:
    schema_version: str = "1.0"
    report_id: str = ""
    scan_mode: str = "schema_only"
    registry_seed_entry_count: int = 0
    finding_count: int = 0
    findings: list[UnregisteredSourceFinding] = field(default_factory=list)
    summary: str = ""
    auto_registration_performed: bool = False
    queue_writes_performed: bool = False
    runtime_changes_performed: bool = False
    external_model_calls_performed: bool = False
    created_at: str = ""
    safety_flags: UnregisteredSourceDetectionSafetyFlags = field(default_factory=UnregisteredSourceDetectionSafetyFlags)


def create_empty_unregistered_source_finding(
    finding_id: str = "",
    candidate_source_id: str = "",
    **overrides: Any,
) -> UnregisteredSourceFinding:
    """Create a schema-only finding with safe defaults."""
    item = UnregisteredSourceFinding(finding_id=finding_id, candidate_source_id=candidate_source_id)
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown unregistered source finding field: {key}")
        setattr(item, key, value)
    return item


def create_empty_unregistered_source_detection_report(
    report_id: str = "",
    findings: list[UnregisteredSourceFinding] | None = None,
    **overrides: Any,
) -> UnregisteredSourceDetectionReport:
    """Create a schema-only detection report with safe defaults."""
    report_findings = list(findings or [])
    item = UnregisteredSourceDetectionReport(
        report_id=report_id,
        findings=report_findings,
        finding_count=len(report_findings),
    )
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown unregistered source report field: {key}")
        setattr(item, key, value)
    return item


def unregistered_source_finding_to_dict(item: UnregisteredSourceFinding) -> dict[str, Any]:
    """Serialize a finding to a plain dict."""
    return asdict(item)


def unregistered_source_finding_from_dict(data: dict[str, Any]) -> UnregisteredSourceFinding:
    """Deserialize a finding from a plain dict."""
    payload = dict(data)
    flags = payload.get("safety_flags")
    if isinstance(flags, UnregisteredSourceDetectionSafetyFlags):
        payload["safety_flags"] = flags
    elif isinstance(flags, dict):
        payload["safety_flags"] = UnregisteredSourceDetectionSafetyFlags(**flags)
    elif flags is None:
        payload["safety_flags"] = UnregisteredSourceDetectionSafetyFlags()
    return UnregisteredSourceFinding(**payload)


def unregistered_source_detection_report_to_dict(item: UnregisteredSourceDetectionReport) -> dict[str, Any]:
    """Serialize a report to a plain dict."""
    return asdict(item)


def unregistered_source_detection_report_from_dict(data: dict[str, Any]) -> UnregisteredSourceDetectionReport:
    """Deserialize a report from a plain dict."""
    payload = dict(data)
    flags = payload.get("safety_flags")
    if isinstance(flags, UnregisteredSourceDetectionSafetyFlags):
        payload["safety_flags"] = flags
    elif isinstance(flags, dict):
        payload["safety_flags"] = UnregisteredSourceDetectionSafetyFlags(**flags)
    elif flags is None:
        payload["safety_flags"] = UnregisteredSourceDetectionSafetyFlags()

    findings = payload.get("findings") or []
    payload["findings"] = [
        finding if isinstance(finding, UnregisteredSourceFinding) else unregistered_source_finding_from_dict(finding)
        for finding in findings
    ]
    return UnregisteredSourceDetectionReport(**payload)


def _finding_text_fields(item: UnregisteredSourceFinding) -> list[str]:
    values = [
        item.finding_id,
        item.finding_type,
        item.candidate_source_id,
        item.candidate_module_path,
        item.candidate_source_type,
        item.detection_signal,
        item.evidence_summary,
        item.matched_registry_entry_id,
        item.authority_level,
        item.recommended_action,
        item.risk_level,
        item.created_at,
    ]
    values.extend(item.related_docs)
    values.extend(item.related_tests)
    values.extend(item.related_queue_item_ids)
    return [value for value in values if isinstance(value, str)]


def _detect_sensitive_text(values: list[str]) -> list[str]:
    joined = "\n".join(values)
    findings: list[str] = []
    for label, pattern in SENSITIVE_TEXT_PATTERNS.items():
        if pattern.search(joined):
            findings.append(label)
    return findings


def _safety_flag_errors(flags: UnregisteredSourceDetectionSafetyFlags) -> list[str]:
    return [label for field_name, label in PROHIBITED_SAFETY_FLAG_FIELDS.items() if getattr(flags, field_name)]


def validate_unregistered_source_finding(item: UnregisteredSourceFinding) -> list[str]:
    """Return validation errors for an unregistered-source finding."""
    errors: list[str] = []

    if not item.finding_id.strip():
        errors.append("missing finding_id")
    if item.finding_type not in ALLOWED_FINDING_TYPES:
        errors.append("invalid finding_type")
    if item.candidate_source_type not in ALLOWED_CANDIDATE_SOURCE_TYPES:
        errors.append("invalid candidate_source_type")
    if item.detection_signal not in ALLOWED_DETECTION_SIGNALS:
        errors.append("invalid detection_signal")
    if item.authority_level not in ALLOWED_AUTHORITY_LEVELS:
        errors.append("invalid authority_level")
    if item.risk_level not in ALLOWED_RISK_LEVELS:
        errors.append("invalid risk_level")
    if item.finding_type in UNREGISTERED_FINDING_TYPES_REQUIRING_SOURCE_ID and not item.candidate_source_id.strip():
        errors.append("missing candidate_source_id")
    if not item.is_registered and item.authority_level == "advisor_proposal":
        errors.append("unregistered finding cannot claim advisor_proposal authority")
    if item.operator_review_required is False:
        errors.append("operator_review_required must remain true")
    if not item.recommended_action.strip():
        errors.append("empty recommended_action")
    if item.finding_type == "unregistered_voice_or_proactive_source" and not item.operator_review_required:
        errors.append("unregistered voice/proactive finding requires operator review")
    if item.finding_type == "unregistered_self_improvement_source" and not item.operator_review_required:
        errors.append("unregistered self-improvement finding requires operator review")

    errors.extend(_safety_flag_errors(item.safety_flags))
    errors.extend(_detect_sensitive_text(_finding_text_fields(item)))
    return errors


def validate_unregistered_source_detection_report(item: UnregisteredSourceDetectionReport) -> list[str]:
    """Return validation errors for an unregistered-source detection report."""
    errors: list[str] = []

    if not item.report_id.strip():
        errors.append("missing report_id")
    if item.scan_mode not in ALLOWED_SCAN_MODES:
        errors.append("invalid scan_mode")
    if item.finding_count != len(item.findings):
        errors.append("finding_count mismatch")
    if item.auto_registration_performed:
        errors.append("auto_registration_performed must remain false")
    if item.queue_writes_performed:
        errors.append("queue_writes_performed must remain false")
    if item.runtime_changes_performed:
        errors.append("runtime_changes_performed must remain false")
    if item.external_model_calls_performed:
        errors.append("external_model_calls_performed must remain false")

    errors.extend(_safety_flag_errors(item.safety_flags))
    errors.extend(_detect_sensitive_text([item.report_id, item.scan_mode, item.summary, item.created_at]))

    for finding in item.findings:
        for error in validate_unregistered_source_finding(finding):
            errors.append(f"{finding.finding_id or 'unknown_finding'}: {error}")

    return errors


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in SENSITIVE_TEXT_PATTERNS.values():
        redacted = pattern.sub(SUMMARY_REDACTION, redacted)
    return redacted


def summarize_unregistered_source_finding(item: UnregisteredSourceFinding) -> dict[str, Any]:
    """Return a redacted/count-only summary for one finding."""
    validation_errors = validate_unregistered_source_finding(item)
    return {
        "schema_version": item.schema_version,
        "finding_id": _redact_text(item.finding_id),
        "finding_type": item.finding_type,
        "candidate_source_type": item.candidate_source_type,
        "detection_signal": item.detection_signal,
        "is_registered": item.is_registered,
        "authority_level": item.authority_level,
        "operator_review_required": item.operator_review_required,
        "risk_level": item.risk_level,
        "related_doc_count": len(item.related_docs),
        "related_test_count": len(item.related_tests),
        "related_queue_item_count": len(item.related_queue_item_ids),
        "safety_error_count": len(_safety_flag_errors(item.safety_flags)),
        "validation_error_count": len(validation_errors),
        "contains_redactions": bool(_detect_sensitive_text(_finding_text_fields(item))),
        "summary_mode": "redacted_count_only",
    }


def summarize_unregistered_source_detection_report(item: UnregisteredSourceDetectionReport) -> dict[str, Any]:
    """Return redacted/count-only summary statistics for a report."""
    by_finding_type: dict[str, int] = {}
    by_signal: dict[str, int] = {}
    by_authority: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    validation_error_count = len(validate_unregistered_source_detection_report(item))
    safety_error_count = len(_safety_flag_errors(item.safety_flags))
    operator_review_required_count = 0
    registered_count = 0

    for finding in item.findings:
        by_finding_type[finding.finding_type] = by_finding_type.get(finding.finding_type, 0) + 1
        by_signal[finding.detection_signal] = by_signal.get(finding.detection_signal, 0) + 1
        by_authority[finding.authority_level] = by_authority.get(finding.authority_level, 0) + 1
        by_risk[finding.risk_level] = by_risk.get(finding.risk_level, 0) + 1
        safety_error_count += len(_safety_flag_errors(finding.safety_flags))
        if finding.operator_review_required:
            operator_review_required_count += 1
        if finding.is_registered:
            registered_count += 1

    return {
        "schema_version": item.schema_version,
        "summary_mode": "redacted_count_only",
        "report_id": _redact_text(item.report_id),
        "scan_mode": item.scan_mode,
        "registry_seed_entry_count": item.registry_seed_entry_count,
        "finding_count": len(item.findings),
        "declared_finding_count": item.finding_count,
        "registered_count": registered_count,
        "unregistered_count": len(item.findings) - registered_count,
        "operator_review_required_count": operator_review_required_count,
        "auto_registration_performed": item.auto_registration_performed,
        "queue_writes_performed": item.queue_writes_performed,
        "runtime_changes_performed": item.runtime_changes_performed,
        "external_model_calls_performed": item.external_model_calls_performed,
        "by_finding_type": by_finding_type,
        "by_detection_signal": by_signal,
        "by_authority_level": by_authority,
        "by_risk_level": by_risk,
        "safety_error_count": safety_error_count,
        "validation_error_count": validation_error_count,
        "contains_redactions": bool(_detect_sensitive_text([item.report_id, item.summary, item.created_at])),
    }


def _metadata_values(*values: Any) -> list[str]:
    collected: list[str] = []

    def collect(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, str):
            collected.append(value)
            return
        if isinstance(value, dict):
            for nested in value.values():
                collect(nested)
            return
        if isinstance(value, (list, tuple, set)):
            for nested in value:
                collect(nested)
            return
        collected.append(str(value))

    for value in values:
        collect(value)
    return collected


def _metadata_text(*values: Any) -> str:
    return " ".join(_metadata_values(*values)).lower().replace("-", "_")


def _registered_source_ids(registered_sources: Any) -> set[str]:
    source_ids: set[str] = set()
    for item in registered_sources or []:
        if isinstance(item, str):
            if item.strip():
                source_ids.add(item.strip())
            continue
        source_id = getattr(item, "source_id", "")
        if isinstance(source_id, str) and source_id.strip():
            source_ids.add(source_id.strip())
    return source_ids


def classify_candidate_source_type(candidate_module_path: str = "", hints: Any = None) -> str:
    """Classify explicit candidate metadata into a conservative source type.

    This helper uses only caller-provided strings/hints. It does not inspect the
    filesystem, scan repository contents, call models, or claim certainty.
    """
    text = _metadata_text(candidate_module_path, hints)
    if "self_improvement" in text or "self improvement" in text:
        return "self_improvement_candidate"
    if "self_review" in text or "self review" in text:
        return "self_review"
    if "ambient" in text:
        return "ambient_loop"
    if "voice" in text:
        return "voice_surface"
    if "proactive" in text or "suggestion" in text:
        return "proactive_suggestion"
    if "advisor" in text or "review" in text or "queue" in text:
        return "advisor_review"
    if "memory" in text:
        return "memory_capture"
    if "checkpoint" in text or "state" in text:
        return "state_checkpoint"
    if "capability" in text:
        return "capability_guidance"
    if "teaching" in text or "synthetic" in text:
        return "teaching_explanation"
    if "cli" in text or "operator" in text:
        return "operator_cli"
    if "institution" in text or "client" in text or "adapter" in text:
        return "institution_extension"
    return "unknown"


def classify_detection_signal(candidate_module_path: str = "", hints: Any = None) -> str:
    """Classify explicit candidate metadata into a conservative signal.

    This helper is non-mutating and does not perform repo-wide scanning.
    """
    text = _metadata_text(candidate_module_path, hints)
    if "self_improvement" in text or "self improvement" in text:
        return "self_improvement_behavior"
    if "self_review" in text or "self review" in text:
        return "self_review_behavior"
    if "voice" in text or "proactive" in text or "ambient" in text:
        return "voice_or_proactive_behavior"
    if "advisor" in text:
        return "advisor_review_behavior"
    if "queue" in text or "review" in text:
        return "queue_or_review_behavior"
    if "memory" in text and ("write" in text or "capture" in text or "mutation" in text):
        return "memory_write_behavior"
    if "route" in text or "routing" in text or "decision" in text:
        return "routing_or_decision_behavior"
    if "suggest" in text or "proposal" in text:
        return "suggestion_generation_function"
    if "doc" in text:
        return "doc_reference"
    if "test" in text:
        return "test_reference"
    if "unknown_source" in text or "unknown source" in text:
        return "provenance_unknown_source"
    if "stale" in text or "incomplete" in text:
        return "seed_entry_stale_or_incomplete"
    if "output" in text or "generate" in text:
        return "module_name_output_like"
    return "unknown"


def _candidate_value(candidate: dict[str, Any], *names: str, default: Any = "") -> Any:
    for name in names:
        if name in candidate and candidate[name] is not None:
            return candidate[name]
    return default


def create_unregistered_source_finding_from_candidate(
    candidate_source_id: str = "",
    candidate_module_path: str = "",
    candidate_metadata: dict[str, Any] | None = None,
    registered_sources: Any = None,
    **overrides: Any,
) -> UnregisteredSourceFinding | None:
    """Create an in-memory finding from explicit candidate metadata.

    Registered candidates return ``None``. Unregistered candidates return a safe
    review-only finding. This helper does not scan files, persist registries,
    write queues, mutate runtime state, or call external models/advisors.
    """
    metadata = dict(candidate_metadata or {})
    source_id = candidate_source_id or str(_candidate_value(metadata, "source_id", "candidate_source_id", default=""))
    module_path = candidate_module_path or str(_candidate_value(metadata, "module_path", "candidate_module_path", "name", default=""))
    registered_ids = _registered_source_ids(registered_sources)
    if source_id and source_id in registered_ids:
        return None

    hints = _candidate_value(metadata, "hints", "hint", "signals", "tags", default=[])
    source_type = overrides.pop("candidate_source_type", "") or classify_candidate_source_type(module_path or source_id, hints)
    signal = overrides.pop("detection_signal", "") or classify_detection_signal(module_path or source_id, hints)
    finding_type = overrides.pop("finding_type", "unregistered_source_candidate")
    if signal == "voice_or_proactive_behavior" or source_type in {"voice_surface", "ambient_loop", "proactive_suggestion"}:
        finding_type = "unregistered_voice_or_proactive_source"
    if signal == "self_improvement_behavior" or source_type == "self_improvement_candidate":
        finding_type = "unregistered_self_improvement_source"

    finding = create_empty_unregistered_source_finding(
        finding_id=overrides.pop("finding_id", f"finding_{source_id or 'unknown_source'}"),
        candidate_source_id=source_id,
        finding_type=finding_type,
        candidate_module_path=module_path,
        candidate_source_type=source_type,
        detection_signal=signal,
        evidence_summary=overrides.pop("evidence_summary", "explicit candidate metadata indicates source review may be required"),
        is_registered=False,
        authority_level=overrides.pop("authority_level", "unknown"),
        operator_review_required=True,
        recommended_action=overrides.pop("recommended_action", "operator review required before registration or activation"),
        risk_level=overrides.pop("risk_level", "medium" if finding_type in {"unregistered_voice_or_proactive_source", "unregistered_self_improvement_source"} else "low"),
        related_docs=list(_candidate_value(metadata, "related_docs", default=[])),
        related_tests=list(_candidate_value(metadata, "related_tests", default=[])),
        safety_flags=UnregisteredSourceDetectionSafetyFlags(),
    )
    for key, value in overrides.items():
        if not hasattr(finding, key):
            raise ValueError(f"unknown unregistered source finding field: {key}")
        setattr(finding, key, value)
    return finding


def create_unregistered_source_detection_report_from_candidates(
    candidates: list[dict[str, Any]],
    registered_sources: Any = None,
    report_id: str = "unregistered_source_detection_report",
    registry_seed_entry_count: int = 0,
    **overrides: Any,
) -> UnregisteredSourceDetectionReport:
    """Create an in-memory report from explicit candidate metadata records."""
    findings: list[UnregisteredSourceFinding] = []
    for candidate in candidates:
        finding = create_unregistered_source_finding_from_candidate(
            candidate_source_id=str(_candidate_value(candidate, "source_id", "candidate_source_id", default="")),
            candidate_module_path=str(_candidate_value(candidate, "module_path", "candidate_module_path", "name", default="")),
            candidate_metadata=candidate,
            registered_sources=registered_sources,
        )
        if finding is not None:
            findings.append(finding)

    report = create_empty_unregistered_source_detection_report(
        report_id=report_id,
        findings=findings,
        scan_mode="manual_review_only",
        registry_seed_entry_count=registry_seed_entry_count,
        summary="explicit candidate metadata converted to review-only findings",
        safety_flags=UnregisteredSourceDetectionSafetyFlags(),
    )
    for key, value in overrides.items():
        if not hasattr(report, key):
            raise ValueError(f"unknown unregistered source report field: {key}")
        setattr(report, key, value)
    report.finding_count = len(report.findings)
    return report


def summarize_unregistered_source_detection_diagnostics(
    report: UnregisteredSourceDetectionReport,
    candidate_count: int | None = None,
    registered_count: int | None = None,
) -> dict[str, Any]:
    """Return redacted/count-only diagnostics for helper-created reports."""
    base = summarize_unregistered_source_detection_report(report)
    inferred_candidate_count = candidate_count if candidate_count is not None else base["finding_count"]
    inferred_registered_count = registered_count if registered_count is not None else max(0, inferred_candidate_count - base["finding_count"])
    return {
        "schema_version": report.schema_version,
        "summary_mode": "redacted_count_only",
        "candidate_count": inferred_candidate_count,
        "finding_count": base["finding_count"],
        "finding_type_counts": base["by_finding_type"],
        "detection_signal_counts": base["by_detection_signal"],
        "risk_counts": base["by_risk_level"],
        "registered_count": inferred_registered_count,
        "unregistered_count": base["finding_count"],
        "operator_review_required_count": base["operator_review_required_count"],
        "unsafe_flag_count": base["safety_error_count"],
        "queue_writes_performed": False,
        "registry_persistence_performed": False,
        "external_model_calls_performed": False,
        "runtime_changes_performed": False,
        "validation_error_count": base["validation_error_count"],
    }
