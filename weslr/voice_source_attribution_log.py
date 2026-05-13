"""WESLR Voice Source Attribution Log Schema V1.

Schema-only dataclasses and validation helpers for future append-only voice
source attribution log records. This module does not implement logging helpers,
write attribution logs, create .weslr/voice_source_attribution.jsonl, wire voice
runtime/chat behavior, write queues, persist registries, call models/advisors,
mutate memory/prompts/config, schedule daemons, select answers, or claim
truth/soundness/official scores.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import json
import re


ALLOWED_STORAGE_FORMATS = {"jsonl", "json", "unknown"}
ALLOWED_EVENT_TYPES = {
    "pre_speak_attribution_draft",
    "post_speak_attribution_confirmed",
    "post_speak_attribution_failed",
    "missing_attribution_detected",
    "attribution_query_requested",
    "unknown",
}
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

PROHIBITED_SAFETY_FLAG_FIELDS = {
    "log_write_attempted": "log write attempted",
    "raw_spoken_text_stored": "raw spoken text stored",
    "provenance_guessing_attempted": "provenance guessing attempted",
    "hidden_llm_authority": "hidden LLM authority",
    "hidden_model_provider_involvement": "hidden model/provider involvement",
    "memory_mutation_attempted": "memory mutation attempted",
    "queue_write_attempted": "queue write attempted",
    "registry_persistence_attempted": "registry persistence attempted",
    "runtime_voice_wiring_attempted": "runtime voice wiring attempted",
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
    "possible raw spoken text": re.compile(r"raw spoken text|spoken text:|transcript:", re.IGNORECASE),
    "possible raw benchmark text": re.compile(r"raw benchmark|benchmark text|question stem|passage:", re.IGNORECASE),
    "possible answer key": re.compile(r"answer[_ -]?key|official solution|correct answer", re.IGNORECASE),
    "possible official score": re.compile(r"official score|benchmark score", re.IGNORECASE),
    "possible private user data": re.compile(r"private user data|ssn|social security|passport", re.IGNORECASE),
}
SUMMARY_REDACTION = "[redacted]"


@dataclass
class VoiceAttributionLogSafetyFlags:
    log_write_attempted: bool = False
    raw_spoken_text_stored: bool = False
    provenance_guessing_attempted: bool = False
    hidden_llm_authority: bool = False
    hidden_model_provider_involvement: bool = False
    memory_mutation_attempted: bool = False
    queue_write_attempted: bool = False
    registry_persistence_attempted: bool = False
    runtime_voice_wiring_attempted: bool = False
    external_model_call_attempted: bool = False
    self_improvement_activation_attempted: bool = False
    answer_selection_attempted: bool = False
    truth_authority_claimed: bool = False
    soundness_authority_claimed: bool = False
    official_score_claimed: bool = False


@dataclass
class VoiceAttributionLogPathPolicy:
    schema_version: str = "1.0"
    log_path: str = ".weslr/voice_source_attribution.jsonl"
    storage_format: str = "jsonl"
    append_only_required: bool = True
    redaction_required: bool = True
    raw_spoken_text_allowed: bool = False
    operator_review_required: bool = True
    allow_absolute_paths: bool = False
    allow_path_traversal: bool = False
    allow_external_storage: bool = False
    institution_storage_policy: str = "local_only_default"
    retention_policy: str = "unspecified"


@dataclass
class VoiceAttributionLogEvent:
    schema_version: str = "1.0"
    event_id: str = ""
    event_type: str = "unknown"
    utterance_id: str = ""
    attribution_record_snapshot: dict[str, Any] = field(default_factory=dict)
    output_provenance_id: str = ""
    source_subsystem: str = "unknown"
    spoken_text_hash: str = ""
    spoken_text_stored: bool = False
    speech_emitted: bool = False
    speech_success: bool = False
    tts_engine: str = "unknown"
    stt_engine: str = "unknown"
    model_provider: str = ""
    model_name: str = ""
    llm_assisted: bool = False
    authority_level: str = "unknown"
    truth_class: str = "unknown"
    redacted_summary: str = ""
    created_at: str = ""
    trace_refs: list[str] = field(default_factory=list)
    safety_flags: VoiceAttributionLogSafetyFlags = field(default_factory=VoiceAttributionLogSafetyFlags)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_empty_voice_attribution_log_path_policy(**overrides: Any) -> VoiceAttributionLogPathPolicy:
    item = VoiceAttributionLogPathPolicy()
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown voice attribution log path policy field: {key}")
        setattr(item, key, value)
    return item


def create_empty_voice_attribution_log_event(
    event_id: str = "",
    utterance_id: str = "",
    **overrides: Any,
) -> VoiceAttributionLogEvent:
    item = VoiceAttributionLogEvent(event_id=event_id, utterance_id=utterance_id, created_at=_utc_now())
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown voice attribution log event field: {key}")
        setattr(item, key, value)
    return item


def voice_attribution_log_path_policy_to_dict(item: VoiceAttributionLogPathPolicy) -> dict[str, Any]:
    return asdict(item)


def voice_attribution_log_path_policy_from_dict(data: dict[str, Any]) -> VoiceAttributionLogPathPolicy:
    return VoiceAttributionLogPathPolicy(**dict(data))


def voice_attribution_log_event_to_dict(item: VoiceAttributionLogEvent) -> dict[str, Any]:
    return asdict(item)


def voice_attribution_log_event_from_dict(data: dict[str, Any]) -> VoiceAttributionLogEvent:
    payload = dict(data)
    flags = payload.get("safety_flags")
    if isinstance(flags, VoiceAttributionLogSafetyFlags):
        payload["safety_flags"] = flags
    elif isinstance(flags, dict):
        payload["safety_flags"] = VoiceAttributionLogSafetyFlags(**flags)
    elif flags is None:
        payload["safety_flags"] = VoiceAttributionLogSafetyFlags()
    return VoiceAttributionLogEvent(**payload)


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in SENSITIVE_TEXT_PATTERNS.values():
        redacted = pattern.sub(SUMMARY_REDACTION, redacted)
    return redacted


def _stringify_snapshot(snapshot: dict[str, Any]) -> str:
    try:
        return json.dumps(snapshot, sort_keys=True, default=str)
    except TypeError:
        return str(snapshot)


def _event_text_fields(item: VoiceAttributionLogEvent) -> list[str]:
    values = [
        item.event_id,
        item.event_type,
        item.utterance_id,
        item.output_provenance_id,
        item.source_subsystem,
        item.spoken_text_hash,
        item.tts_engine,
        item.stt_engine,
        item.model_provider,
        item.model_name,
        item.authority_level,
        item.truth_class,
        item.redacted_summary,
        _stringify_snapshot(item.attribution_record_snapshot),
    ]
    values.extend(item.trace_refs)
    return [v for v in values if isinstance(v, str)]


def _detect_sensitive_text_in_values(values: list[str]) -> list[str]:
    joined = "\n".join(values)
    findings: list[str] = []
    for label, pattern in SENSITIVE_TEXT_PATTERNS.items():
        if pattern.search(joined):
            findings.append(label)
    return findings


def _detect_sensitive_event_text(item: VoiceAttributionLogEvent) -> list[str]:
    return _detect_sensitive_text_in_values(_event_text_fields(item))


def _detect_sensitive_policy_text(item: VoiceAttributionLogPathPolicy) -> list[str]:
    return _detect_sensitive_text_in_values([item.log_path, item.institution_storage_policy, item.retention_policy])


def validate_voice_attribution_log_path_policy(item: VoiceAttributionLogPathPolicy) -> list[str]:
    errors: list[str] = []
    if item.storage_format not in ALLOWED_STORAGE_FORMATS:
        errors.append("invalid storage_format")
    if not item.append_only_required:
        errors.append("append_only_required disabled")
    if not item.redaction_required:
        errors.append("redaction_required disabled")
    if item.raw_spoken_text_allowed:
        errors.append("raw_spoken_text_allowed true")
    if not item.operator_review_required:
        errors.append("operator_review_required disabled")
    if item.allow_absolute_paths:
        errors.append("absolute paths allowed")
    if item.allow_path_traversal:
        errors.append("path traversal allowed")
    if item.allow_external_storage:
        errors.append("external storage allowed")
    for finding in _detect_sensitive_policy_text(item):
        errors.append(finding)
    return errors


def validate_voice_attribution_log_event(item: VoiceAttributionLogEvent) -> list[str]:
    errors: list[str] = []
    if not item.event_id.strip():
        errors.append("missing event_id")
    if item.event_type not in ALLOWED_EVENT_TYPES:
        errors.append("invalid event_type")
    if item.event_type in {
        "pre_speak_attribution_draft",
        "post_speak_attribution_confirmed",
        "post_speak_attribution_failed",
        "missing_attribution_detected",
    } and not item.utterance_id.strip():
        errors.append("missing utterance_id")
    if item.source_subsystem not in ALLOWED_SOURCE_SUBSYSTEMS:
        errors.append("invalid source_subsystem")
    if item.authority_level not in ALLOWED_AUTHORITY_LEVELS:
        errors.append("invalid authority_level")
    if item.truth_class not in ALLOWED_TRUTH_CLASSES:
        errors.append("invalid truth_class")
    if item.spoken_text_stored:
        errors.append("spoken_text_stored true")
    if item.llm_assisted and not item.model_provider.strip():
        errors.append("llm_assisted requires model_provider")
    if item.llm_assisted and not item.model_name.strip():
        errors.append("llm_assisted requires model_name")
    if item.llm_assisted and item.authority_level == "system_fact" and not item.trace_refs:
        errors.append("system_fact authority requires trace_refs for LLM-assisted voice")
    if item.llm_assisted and item.truth_class == "verified_system_fact" and not item.trace_refs:
        errors.append("verified_system_fact truth requires trace_refs for LLM-assisted voice")
    if item.event_type in {"post_speak_attribution_confirmed", "post_speak_attribution_failed"} and not item.trace_refs:
        errors.append("post-speak event requires trace_refs")

    flags = item.safety_flags
    for field_name, label in PROHIBITED_SAFETY_FLAG_FIELDS.items():
        if getattr(flags, field_name):
            errors.append(label)

    for finding in _detect_sensitive_event_text(item):
        errors.append(finding)
    return errors


def summarize_voice_attribution_log_path_policy(item: VoiceAttributionLogPathPolicy) -> dict[str, Any]:
    validation_errors = validate_voice_attribution_log_path_policy(item)
    return {
        "schema_version": item.schema_version,
        "log_path": _redact_text(item.log_path),
        "storage_format": item.storage_format,
        "append_only_required": item.append_only_required,
        "redaction_required": item.redaction_required,
        "raw_spoken_text_allowed": item.raw_spoken_text_allowed,
        "operator_review_required": item.operator_review_required,
        "allow_absolute_paths": item.allow_absolute_paths,
        "allow_path_traversal": item.allow_path_traversal,
        "allow_external_storage": item.allow_external_storage,
        "institution_storage_policy": _redact_text(item.institution_storage_policy),
        "retention_policy": _redact_text(item.retention_policy),
        "validation_error_count": len(validation_errors),
        "contains_redactions": bool(_detect_sensitive_policy_text(item)),
        "summary_mode": "redacted_count_only",
    }


def summarize_voice_attribution_log_event(item: VoiceAttributionLogEvent) -> dict[str, Any]:
    validation_errors = validate_voice_attribution_log_event(item)
    return {
        "schema_version": item.schema_version,
        "event_id": _redact_text(item.event_id),
        "event_type": item.event_type,
        "utterance_id": _redact_text(item.utterance_id),
        "snapshot_field_count": len(item.attribution_record_snapshot),
        "output_provenance_id": _redact_text(item.output_provenance_id),
        "source_subsystem": item.source_subsystem,
        "spoken_text_hash_present": bool(item.spoken_text_hash),
        "spoken_text_stored": item.spoken_text_stored,
        "speech_emitted": item.speech_emitted,
        "speech_success": item.speech_success,
        "tts_engine": _redact_text(item.tts_engine),
        "stt_engine": _redact_text(item.stt_engine),
        "model_provider_present": bool(item.model_provider),
        "model_name_present": bool(item.model_name),
        "llm_assisted": item.llm_assisted,
        "authority_level": item.authority_level,
        "truth_class": item.truth_class,
        "trace_ref_count": len(item.trace_refs),
        "safety_error_count": sum(1 for name in PROHIBITED_SAFETY_FLAG_FIELDS if getattr(item.safety_flags, name)),
        "validation_error_count": len(validation_errors),
        "contains_redactions": bool(_detect_sensitive_event_text(item)),
        "summary_mode": "redacted_count_only",
    }
