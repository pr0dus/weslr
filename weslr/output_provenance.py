"""WESLR Output Provenance Envelope Schema V1.

Schema-only dataclasses and validation helpers for future unified output
provenance envelopes. This module does not implement runtime/chat routing,
voice/proactive wiring, queue persistence, daemon behavior, scheduling,
model/advisor calls, memory mutation, answer selection, scoring, or
runtime/config changes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import re


ALLOWED_AUTHORITY_LEVELS = {
    "system_fact",
    "observed_event",
    "internal_diagnostic",
    "suggestion",
    "advisor_proposal",
    "voice_surface",
    "teaching_explanation",
    "operator_decision",
    "unknown",
}

ALLOWED_TRUTH_CLASSES = {
    "verified_system_fact",
    "observed",
    "diagnostic",
    "suggestion",
    "proposal",
    "explanation",
    "unverified",
    "unknown",
}

ALLOWED_CONFIDENCE_VALUES = {"low", "medium", "high", "unknown"}

ALLOWED_TRIGGER_TYPES = {
    "user_message",
    "voice_event",
    "ambient_event",
    "proactive_scan",
    "advisor_review",
    "local_scan",
    "operator_action",
    "system_event",
    "unknown",
}

ALLOWED_CHANNELS = {
    "chat",
    "voice",
    "terminal",
    "operator_cli",
    "daemon",
    "internal",
    "unknown",
}

PROHIBITED_SAFETY_FLAG_FIELDS = {
    "answer_selection_performed": "answer selection performed",
    "truth_authority_claimed": "truth authority claimed",
    "soundness_authority_claimed": "soundness authority claimed",
    "official_score_claimed": "official score claimed",
    "hidden_llm_authority": "hidden LLM authority",
    "hidden_memory_mutation": "hidden memory mutation",
    "hidden_queue_write": "hidden queue write",
    "hidden_runtime_action": "hidden runtime action",
    "raw_sensitive_content_stored": "raw sensitive content stored",
    "provenance_guessed": "provenance guessed",
    "unattributed_voice_or_proactive_output": "unattributed voice/proactive output",
    "external_model_call_performed": "external model call performed",
    "runtime_config_change_performed": "runtime config change performed",
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
class OutputProvenanceSafetyFlags:
    answer_selection_performed: bool = False
    truth_authority_claimed: bool = False
    soundness_authority_claimed: bool = False
    official_score_claimed: bool = False
    hidden_llm_authority: bool = False
    hidden_memory_mutation: bool = False
    hidden_queue_write: bool = False
    hidden_runtime_action: bool = False
    raw_sensitive_content_stored: bool = False
    provenance_guessed: bool = False
    unattributed_voice_or_proactive_output: bool = False
    external_model_call_performed: bool = False
    runtime_config_change_performed: bool = False


@dataclass
class OutputProvenanceEnvelope:
    schema_version: str = "1.0"
    output_id: str = ""
    generated_by: str = ""
    source_modules: list[str] = field(default_factory=list)
    trigger: str = ""
    trigger_type: str = "unknown"
    input_channel: str = "unknown"
    output_channel: str = "unknown"
    authority_level: str = "unknown"
    truth_class: str = "unknown"
    confidence: str = "unknown"
    llm_assisted: bool = False
    advisor_assisted: bool = False
    operator_review_required: bool = True
    raw_sensitive_content_stored: bool = False
    memory_write_performed: bool = False
    queue_write_performed: bool = False
    runtime_action_performed: bool = False
    created_at: str = ""
    trace_refs: list[str] = field(default_factory=list)
    related_queue_item_ids: list[str] = field(default_factory=list)
    related_advisor_review_ids: list[str] = field(default_factory=list)
    safety_flags: OutputProvenanceSafetyFlags = field(default_factory=OutputProvenanceSafetyFlags)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_empty_output_provenance_envelope(
    output_id: str = "",
    generated_by: str = "",
    source_modules: list[str] | None = None,
    **overrides: Any,
) -> OutputProvenanceEnvelope:
    """Create a schema-only output provenance envelope with safe defaults."""
    item = OutputProvenanceEnvelope(
        output_id=output_id,
        generated_by=generated_by,
        source_modules=list(source_modules or []),
        created_at=_utc_now(),
    )
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown output provenance envelope field: {key}")
        setattr(item, key, value)
    return item


def output_provenance_envelope_to_dict(item: OutputProvenanceEnvelope) -> dict[str, Any]:
    """Serialize an output provenance envelope to a plain dict."""
    return asdict(item)


def output_provenance_envelope_from_dict(data: dict[str, Any]) -> OutputProvenanceEnvelope:
    """Deserialize an output provenance envelope from a plain dict."""
    payload = dict(data)
    flags = payload.get("safety_flags")
    if isinstance(flags, OutputProvenanceSafetyFlags):
        payload["safety_flags"] = flags
    elif isinstance(flags, dict):
        payload["safety_flags"] = OutputProvenanceSafetyFlags(**flags)
    elif flags is None:
        payload["safety_flags"] = OutputProvenanceSafetyFlags()
    return OutputProvenanceEnvelope(**payload)


def _summary_text_fields(item: OutputProvenanceEnvelope) -> list[str]:
    values: list[str] = [
        item.output_id,
        item.generated_by,
        item.trigger,
        item.trigger_type,
        item.input_channel,
        item.output_channel,
        item.authority_level,
        item.truth_class,
        item.confidence,
    ]
    values.extend(item.source_modules)
    values.extend(item.trace_refs)
    values.extend(item.related_queue_item_ids)
    values.extend(item.related_advisor_review_ids)
    return [v for v in values if isinstance(v, str)]


def _detect_sensitive_text(item: OutputProvenanceEnvelope) -> list[str]:
    joined = "\n".join(_summary_text_fields(item))
    findings: list[str] = []
    for label, pattern in SENSITIVE_TEXT_PATTERNS.items():
        if pattern.search(joined):
            findings.append(label)
    return findings


def validate_output_provenance_envelope(item: OutputProvenanceEnvelope) -> list[str]:
    """Return validation errors for an output provenance envelope."""
    errors: list[str] = []

    if not item.output_id.strip():
        errors.append("missing output_id")
    if not item.generated_by.strip():
        errors.append("missing generated_by")
    if not item.source_modules:
        errors.append("empty source_modules")
    if item.trigger_type not in ALLOWED_TRIGGER_TYPES:
        errors.append("invalid trigger_type")
    if item.input_channel not in ALLOWED_CHANNELS:
        errors.append("invalid input_channel")
    if item.output_channel not in ALLOWED_CHANNELS:
        errors.append("invalid output_channel")
    if item.authority_level not in ALLOWED_AUTHORITY_LEVELS:
        errors.append("invalid authority_level")
    if item.truth_class not in ALLOWED_TRUTH_CLASSES:
        errors.append("invalid truth_class")
    if item.confidence not in ALLOWED_CONFIDENCE_VALUES:
        errors.append("invalid confidence")

    if item.authority_level in {"suggestion", "advisor_proposal", "voice_surface"} and not item.operator_review_required:
        errors.append(f"{item.authority_level} requires operator review")
    if item.raw_sensitive_content_stored:
        errors.append("raw_sensitive_content_stored true")
    if item.memory_write_performed and not item.trace_refs:
        errors.append("memory_write_performed requires trace_refs")
    if item.queue_write_performed and not item.related_queue_item_ids:
        errors.append("queue_write_performed requires related_queue_item_ids")
    if item.runtime_action_performed and not item.trace_refs:
        errors.append("runtime_action_performed requires trace_refs")
    if item.llm_assisted and (not item.source_modules or not item.trace_refs):
        errors.append("llm_assisted requires source_modules and trace_refs")
    if item.advisor_assisted and not item.related_advisor_review_ids:
        errors.append("advisor_assisted requires related_advisor_review_ids")
    if item.authority_level == "voice_surface" and (not item.generated_by.strip() or not item.trigger.strip() or not item.trace_refs):
        errors.append("voice_surface requires attribution")
    if item.trigger_type in {"voice_event", "ambient_event", "proactive_scan"} and (not item.generated_by.strip() or not item.trigger.strip() or not item.trace_refs):
        errors.append("voice/proactive output without attribution")

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


def summarize_output_provenance_envelope(item: OutputProvenanceEnvelope) -> dict[str, Any]:
    """Return a redacted/count-only summary for a single envelope."""
    validation_errors = validate_output_provenance_envelope(item)
    return {
        "schema_version": item.schema_version,
        "output_id": _redact_text(item.output_id),
        "generated_by": _redact_text(item.generated_by),
        "trigger_type": item.trigger_type,
        "input_channel": item.input_channel,
        "output_channel": item.output_channel,
        "authority_level": item.authority_level,
        "truth_class": item.truth_class,
        "confidence": item.confidence,
        "llm_assisted": item.llm_assisted,
        "advisor_assisted": item.advisor_assisted,
        "operator_review_required": item.operator_review_required,
        "raw_sensitive_content_stored": item.raw_sensitive_content_stored,
        "memory_write_performed": item.memory_write_performed,
        "queue_write_performed": item.queue_write_performed,
        "runtime_action_performed": item.runtime_action_performed,
        "source_module_count": len(item.source_modules),
        "trace_ref_count": len(item.trace_refs),
        "related_queue_item_count": len(item.related_queue_item_ids),
        "related_advisor_review_count": len(item.related_advisor_review_ids),
        "safety_error_count": sum(1 for name in PROHIBITED_SAFETY_FLAG_FIELDS if getattr(item.safety_flags, name)),
        "validation_error_count": len(validation_errors),
        "contains_redactions": bool(_detect_sensitive_text(item)),
        "summary_mode": "redacted_count_only",
    }


def summarize_output_provenance_envelopes(items: list[OutputProvenanceEnvelope]) -> dict[str, Any]:
    """Return redacted/count-only summary statistics for multiple envelopes."""
    by_authority_level: dict[str, int] = {}
    by_truth_class: dict[str, int] = {}
    by_trigger_type: dict[str, int] = {}
    by_output_channel: dict[str, int] = {}
    validation_error_count = 0
    redaction_count = 0

    for item in items:
        by_authority_level[item.authority_level] = by_authority_level.get(item.authority_level, 0) + 1
        by_truth_class[item.truth_class] = by_truth_class.get(item.truth_class, 0) + 1
        by_trigger_type[item.trigger_type] = by_trigger_type.get(item.trigger_type, 0) + 1
        by_output_channel[item.output_channel] = by_output_channel.get(item.output_channel, 0) + 1
        validation_error_count += len(validate_output_provenance_envelope(item))
        if _detect_sensitive_text(item):
            redaction_count += 1

    return {
        "item_count": len(items),
        "by_authority_level": by_authority_level,
        "by_truth_class": by_truth_class,
        "by_trigger_type": by_trigger_type,
        "by_output_channel": by_output_channel,
        "validation_error_count": validation_error_count,
        "redaction_count": redaction_count,
        "summary_mode": "redacted_count_only",
    }
