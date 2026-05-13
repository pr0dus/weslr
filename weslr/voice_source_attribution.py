"""WESLR Voice Source Attribution Schema V1.

Schema-only dataclasses and validation helpers for future voice/proactive
source attribution records. This module does not implement voice wiring,
voice gateway behavior, ambient loop behavior, TTS/STT behavior, query
surfaces, queue writes, registry persistence, model/advisor calls, provider
activation, prompt mutation, memory mutation, daemon/scheduler behavior,
answer selection, scoring, or OpenClaw/runtime/config changes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import re


ALLOWED_SOURCE_SUBSYSTEMS = {
    "voice_gateway",
    "ambient_voice_loop",
    "tts_engine",
    "stt_engine",
    "proactive_suggestions",
    "llm_advisor_mode",
    "local_model",
    "external_model",
    "operator_cli",
    "unknown",
}

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

PROHIBITED_SAFETY_FLAG_FIELDS = {
    "provenance_guessing_attempted": "provenance guessing attempted",
    "hidden_llm_authority": "hidden LLM authority",
    "hidden_model_provider_involvement": "hidden model/provider involvement",
    "unattributed_voice_or_proactive_output": "unattributed voice/proactive output",
    "raw_sensitive_spoken_text_stored": "raw sensitive spoken text stored",
    "memory_mutation_from_attribution": "memory mutation from attribution",
    "runtime_voice_wiring_attempted": "runtime voice wiring attempted",
    "queue_write_attempted": "queue write attempted",
    "registry_persistence_attempted": "registry persistence attempted",
    "external_model_call_attempted": "external model call attempted",
    "self_improvement_activation_attempted": "self-improvement activation attempted",
    "answer_selection_attempted": "answer selection attempted",
    "truth_authority_claimed": "truth authority claimed",
    "soundness_authority_claimed": "soundness authority claimed",
    "official_score_claimed": "official score claimed",
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
class VoiceSourceAttributionSafetyFlags:
    provenance_guessing_attempted: bool = False
    hidden_llm_authority: bool = False
    hidden_model_provider_involvement: bool = False
    unattributed_voice_or_proactive_output: bool = False
    raw_sensitive_spoken_text_stored: bool = False
    memory_mutation_from_attribution: bool = False
    runtime_voice_wiring_attempted: bool = False
    queue_write_attempted: bool = False
    registry_persistence_attempted: bool = False
    external_model_call_attempted: bool = False
    self_improvement_activation_attempted: bool = False
    answer_selection_attempted: bool = False
    truth_authority_claimed: bool = False
    soundness_authority_claimed: bool = False
    official_score_claimed: bool = False


@dataclass
class VoiceSourceAttributionRecord:
    schema_version: str = "1.0"
    utterance_id: str = ""
    output_provenance_id: str = ""
    spoken_text_hash: str = ""
    spoken_text_stored: bool = False
    source_subsystem: str = "unknown"
    source_module: str = ""
    generated_by: str = ""
    trigger: str = ""
    trigger_type: str = "unknown"
    input_channel: str = "unknown"
    output_channel: str = "voice"
    voice_engine: str = "unknown"
    tts_engine: str = "unknown"
    stt_engine: str = "unknown"
    model_provider: str = ""
    model_name: str = ""
    llm_assisted: bool = False
    advisor_assisted: bool = False
    ambient_loop_involved: bool = False
    proactive_suggestion_involved: bool = False
    operator_review_required: bool = True
    authority_level: str = "unknown"
    truth_class: str = "unknown"
    confidence: str = "unknown"
    created_at: str = ""
    trace_refs: list[str] = field(default_factory=list)
    related_queue_item_ids: list[str] = field(default_factory=list)
    related_advisor_review_ids: list[str] = field(default_factory=list)
    safety_flags: VoiceSourceAttributionSafetyFlags = field(default_factory=VoiceSourceAttributionSafetyFlags)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_empty_voice_source_attribution_record(
    utterance_id: str = "",
    output_provenance_id: str = "",
    **overrides: Any,
) -> VoiceSourceAttributionRecord:
    """Create a schema-only voice source attribution record with safe defaults."""
    item = VoiceSourceAttributionRecord(
        utterance_id=utterance_id,
        output_provenance_id=output_provenance_id,
        created_at=_utc_now(),
    )
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown voice source attribution field: {key}")
        setattr(item, key, value)
    return item


def voice_source_attribution_record_to_dict(item: VoiceSourceAttributionRecord) -> dict[str, Any]:
    """Serialize a voice source attribution record to a plain dict."""
    return asdict(item)


def voice_source_attribution_record_from_dict(data: dict[str, Any]) -> VoiceSourceAttributionRecord:
    """Deserialize a voice source attribution record from a plain dict."""
    payload = dict(data)
    flags = payload.get("safety_flags")
    if isinstance(flags, VoiceSourceAttributionSafetyFlags):
        payload["safety_flags"] = flags
    elif isinstance(flags, dict):
        payload["safety_flags"] = VoiceSourceAttributionSafetyFlags(**flags)
    elif flags is None:
        payload["safety_flags"] = VoiceSourceAttributionSafetyFlags()
    return VoiceSourceAttributionRecord(**payload)


def _text_fields(item: VoiceSourceAttributionRecord) -> list[str]:
    values: list[str] = [
        item.utterance_id,
        item.output_provenance_id,
        item.spoken_text_hash,
        item.source_subsystem,
        item.source_module,
        item.generated_by,
        item.trigger,
        item.trigger_type,
        item.input_channel,
        item.output_channel,
        item.voice_engine,
        item.tts_engine,
        item.stt_engine,
        item.model_provider,
        item.model_name,
        item.authority_level,
        item.truth_class,
        item.confidence,
    ]
    values.extend(item.trace_refs)
    values.extend(item.related_queue_item_ids)
    values.extend(item.related_advisor_review_ids)
    return [v for v in values if isinstance(v, str)]


def _detect_sensitive_text(item: VoiceSourceAttributionRecord) -> list[str]:
    joined = "\n".join(_text_fields(item))
    findings: list[str] = []
    for label, pattern in SENSITIVE_TEXT_PATTERNS.items():
        if pattern.search(joined):
            findings.append(label)
    return findings


def _has_verified_trace(item: VoiceSourceAttributionRecord) -> bool:
    return any(ref.strip().startswith("verified:") for ref in item.trace_refs)


def validate_voice_source_attribution_record(item: VoiceSourceAttributionRecord) -> list[str]:
    """Return validation errors for a voice source attribution record."""
    errors: list[str] = []

    if not item.utterance_id.strip():
        errors.append("missing utterance_id")
    if not item.output_provenance_id.strip():
        errors.append("missing output_provenance_id")
    if item.source_subsystem not in ALLOWED_SOURCE_SUBSYSTEMS:
        errors.append("invalid source_subsystem")
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
    if not item.source_module.strip():
        errors.append("missing source_module")
    if not item.generated_by.strip():
        errors.append("missing generated_by")

    is_ambient_or_proactive = (
        item.source_subsystem in {"ambient_voice_loop", "proactive_suggestions"}
        or item.trigger_type in {"ambient_event", "proactive_scan"}
        or item.ambient_loop_involved
        or item.proactive_suggestion_involved
    )
    if is_ambient_or_proactive and not item.trigger.strip():
        errors.append("missing trigger for ambient/proactive voice record")
    if item.spoken_text_stored:
        errors.append("spoken_text_stored true")
    if item.spoken_text_stored and not item.spoken_text_hash.strip():
        errors.append("spoken_text_stored requires spoken_text_hash")
    if item.llm_assisted and not item.model_provider.strip():
        errors.append("llm_assisted requires model_provider")
    if item.llm_assisted and not item.model_name.strip():
        errors.append("llm_assisted requires model_name")
    if item.advisor_assisted and not item.related_advisor_review_ids:
        errors.append("advisor_assisted requires related_advisor_review_ids")
    if item.ambient_loop_involved and (item.source_subsystem == "unknown" or not item.trigger.strip()):
        errors.append("ambient_loop_involved requires source_subsystem and trigger")
    if item.proactive_suggestion_involved and (item.source_subsystem == "unknown" or not item.trigger.strip()):
        errors.append("proactive_suggestion_involved requires source_subsystem and trigger")
    if (
        not item.operator_review_required
        and (
            item.source_subsystem == "unknown"
            or item.llm_assisted
            or item.advisor_assisted
            or item.ambient_loop_involved
            or item.proactive_suggestion_involved
        )
    ):
        errors.append("operator_review_required must remain true for unknown/assisted/ambient/proactive records")
    if item.llm_assisted and item.output_channel == "voice" and item.authority_level == "system_fact" and not _has_verified_trace(item):
        errors.append("system_fact authority requires verified trace for LLM-assisted voice")
    if item.llm_assisted and item.output_channel == "voice" and item.truth_class == "verified_system_fact" and not _has_verified_trace(item):
        errors.append("verified_system_fact truth requires verified trace for LLM-assisted voice")
    if not item.trace_refs:
        errors.append("empty trace_refs")

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


def summarize_voice_source_attribution_record(item: VoiceSourceAttributionRecord) -> dict[str, Any]:
    """Return a redacted/count-only summary for a single attribution record."""
    validation_errors = validate_voice_source_attribution_record(item)
    return {
        "schema_version": item.schema_version,
        "utterance_id": _redact_text(item.utterance_id),
        "output_provenance_id": _redact_text(item.output_provenance_id),
        "spoken_text_hash_present": bool(item.spoken_text_hash),
        "spoken_text_stored": item.spoken_text_stored,
        "source_subsystem": item.source_subsystem,
        "source_module": _redact_text(item.source_module),
        "generated_by": _redact_text(item.generated_by),
        "trigger_type": item.trigger_type,
        "input_channel": item.input_channel,
        "output_channel": item.output_channel,
        "voice_engine": _redact_text(item.voice_engine),
        "tts_engine": _redact_text(item.tts_engine),
        "stt_engine": _redact_text(item.stt_engine),
        "model_provider_present": bool(item.model_provider),
        "model_name_present": bool(item.model_name),
        "llm_assisted": item.llm_assisted,
        "advisor_assisted": item.advisor_assisted,
        "ambient_loop_involved": item.ambient_loop_involved,
        "proactive_suggestion_involved": item.proactive_suggestion_involved,
        "operator_review_required": item.operator_review_required,
        "authority_level": item.authority_level,
        "truth_class": item.truth_class,
        "confidence": item.confidence,
        "trace_ref_count": len(item.trace_refs),
        "related_queue_item_count": len(item.related_queue_item_ids),
        "related_advisor_review_count": len(item.related_advisor_review_ids),
        "safety_error_count": sum(1 for name in PROHIBITED_SAFETY_FLAG_FIELDS if getattr(item.safety_flags, name)),
        "validation_error_count": len(validation_errors),
        "contains_redactions": bool(_detect_sensitive_text(item)),
        "summary_mode": "redacted_count_only",
    }


def summarize_voice_source_attribution_records(items: list[VoiceSourceAttributionRecord]) -> dict[str, Any]:
    """Return redacted/count-only summary statistics for multiple attribution records."""
    by_source_subsystem: dict[str, int] = {}
    by_trigger_type: dict[str, int] = {}
    by_output_channel: dict[str, int] = {}
    by_authority_level: dict[str, int] = {}
    by_truth_class: dict[str, int] = {}
    validation_error_count = 0
    redaction_count = 0
    llm_assisted_count = 0
    advisor_assisted_count = 0
    ambient_count = 0
    proactive_count = 0

    for item in items:
        by_source_subsystem[item.source_subsystem] = by_source_subsystem.get(item.source_subsystem, 0) + 1
        by_trigger_type[item.trigger_type] = by_trigger_type.get(item.trigger_type, 0) + 1
        by_output_channel[item.output_channel] = by_output_channel.get(item.output_channel, 0) + 1
        by_authority_level[item.authority_level] = by_authority_level.get(item.authority_level, 0) + 1
        by_truth_class[item.truth_class] = by_truth_class.get(item.truth_class, 0) + 1
        validation_error_count += len(validate_voice_source_attribution_record(item))
        if _detect_sensitive_text(item):
            redaction_count += 1
        if item.llm_assisted:
            llm_assisted_count += 1
        if item.advisor_assisted:
            advisor_assisted_count += 1
        if item.ambient_loop_involved:
            ambient_count += 1
        if item.proactive_suggestion_involved:
            proactive_count += 1

    return {
        "item_count": len(items),
        "by_source_subsystem": by_source_subsystem,
        "by_trigger_type": by_trigger_type,
        "by_output_channel": by_output_channel,
        "by_authority_level": by_authority_level,
        "by_truth_class": by_truth_class,
        "llm_assisted_count": llm_assisted_count,
        "advisor_assisted_count": advisor_assisted_count,
        "ambient_loop_involved_count": ambient_count,
        "proactive_suggestion_involved_count": proactive_count,
        "validation_error_count": validation_error_count,
        "redaction_count": redaction_count,
        "summary_mode": "redacted_count_only",
    }
