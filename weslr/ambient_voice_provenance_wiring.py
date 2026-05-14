"""WESLR Ambient Voice Provenance Wiring Schema V1.

Schema dataclasses and validation helpers for future ambient/voice provenance
wiring hook records. This module is schema-only: it does not wire voice gateway,
ambient loop, TTS/STT, runtime/chat behavior, queues, config, memory, model or
advisor calls, and it does not write .weslr/voice_source_attribution.jsonl.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ALLOWED_AMBIENT_VOICE_PROVENANCE_HOOK_TYPES = {
    "pre_speak",
    "post_speak_success",
    "post_speak_failure",
    "missing_attribution",
    "stt_transcript_received",
    "proactive_surface_attempt",
    "unknown",
}

POST_SPEAK_HOOK_TYPES = {"post_speak_success", "post_speak_failure"}

PROHIBITED_SAFETY_FLAG_FIELDS = {
    "runtime_integration_attempted": "runtime integration attempted",
    "voice_wiring_attempted": "voice wiring attempted",
    "voice_gateway_mutation_attempted": "voice gateway mutation attempted",
    "ambient_loop_mutation_attempted": "ambient loop mutation attempted",
    "tts_stt_mutation_attempted": "TTS/STT mutation attempted",
    "chat_behavior_mutation_attempted": "chat behavior mutation attempted",
    "log_write_attempted": "log write attempted",
    "queue_write_attempted": "queue write attempted",
    "config_mutation_attempted": "config mutation attempted",
    "memory_mutation_attempted": "memory mutation attempted",
    "model_call_attempted": "model call attempted",
    "advisor_call_attempted": "advisor call attempted",
    "provenance_guessing_attempted": "provenance guessing attempted",
    "hidden_llm_authority": "hidden LLM authority",
    "truth_authority_claimed": "truth authority claimed",
    "soundness_authority_claimed": "soundness authority claimed",
    "official_score_claimed": "official score claimed",
}


@dataclass
class AmbientVoiceProvenanceWiringSafetyFlags:
    runtime_integration_attempted: bool = False
    voice_wiring_attempted: bool = False
    voice_gateway_mutation_attempted: bool = False
    ambient_loop_mutation_attempted: bool = False
    tts_stt_mutation_attempted: bool = False
    chat_behavior_mutation_attempted: bool = False
    log_write_attempted: bool = False
    queue_write_attempted: bool = False
    config_mutation_attempted: bool = False
    memory_mutation_attempted: bool = False
    model_call_attempted: bool = False
    advisor_call_attempted: bool = False
    provenance_guessing_attempted: bool = False
    hidden_llm_authority: bool = False
    truth_authority_claimed: bool = False
    soundness_authority_claimed: bool = False
    official_score_claimed: bool = False


@dataclass
class AmbientVoiceProvenanceHookRecord:
    schema_version: str = "1.0"
    hook_id: str = ""
    hook_type: str = "unknown"
    source_subsystem: str = "unknown"
    trigger_type: str = "unknown"
    intended_output_channel: str = "voice"
    requires_pre_speak_attribution: bool = True
    requires_output_provenance: bool = True
    requires_source_registry_entry: bool = True
    requires_post_speak_confirmation: bool = True
    requires_append_only_log: bool = True
    operator_review_required: bool = True
    llm_assisted: bool = False
    model_provider: str = ""
    model_name: str = ""
    trace_refs: list[str] = field(default_factory=list)
    safety_flags: AmbientVoiceProvenanceWiringSafetyFlags = field(default_factory=AmbientVoiceProvenanceWiringSafetyFlags)


def create_empty_ambient_voice_provenance_hook_record(
    hook_id: str = "",
    hook_type: str = "unknown",
    **overrides: Any,
) -> AmbientVoiceProvenanceHookRecord:
    item = AmbientVoiceProvenanceHookRecord(hook_id=hook_id, hook_type=hook_type)
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown ambient voice provenance hook field: {key}")
        setattr(item, key, value)
    return item


def ambient_voice_provenance_wiring_safety_flags_to_dict(item: AmbientVoiceProvenanceWiringSafetyFlags) -> dict[str, Any]:
    return asdict(item)


def ambient_voice_provenance_wiring_safety_flags_from_dict(data: dict[str, Any]) -> AmbientVoiceProvenanceWiringSafetyFlags:
    return AmbientVoiceProvenanceWiringSafetyFlags(**dict(data))


def ambient_voice_provenance_hook_record_to_dict(item: AmbientVoiceProvenanceHookRecord) -> dict[str, Any]:
    return asdict(item)


def ambient_voice_provenance_hook_record_from_dict(data: dict[str, Any]) -> AmbientVoiceProvenanceHookRecord:
    payload = dict(data)
    flags = payload.get("safety_flags")
    if isinstance(flags, AmbientVoiceProvenanceWiringSafetyFlags):
        payload["safety_flags"] = flags
    elif isinstance(flags, dict):
        payload["safety_flags"] = AmbientVoiceProvenanceWiringSafetyFlags(**flags)
    elif flags is None:
        payload["safety_flags"] = AmbientVoiceProvenanceWiringSafetyFlags()
    return AmbientVoiceProvenanceHookRecord(**payload)


def validate_ambient_voice_provenance_wiring_safety_flags(
    flags: AmbientVoiceProvenanceWiringSafetyFlags | dict[str, Any] | None,
) -> list[str]:
    if flags is None:
        flags = AmbientVoiceProvenanceWiringSafetyFlags()
    if isinstance(flags, dict):
        flags = AmbientVoiceProvenanceWiringSafetyFlags(**flags)

    errors: list[str] = []
    for field_name, label in PROHIBITED_SAFETY_FLAG_FIELDS.items():
        if getattr(flags, field_name):
            errors.append(label)
    return errors


def validate_ambient_voice_provenance_hook_record(
    item: AmbientVoiceProvenanceHookRecord | dict[str, Any],
) -> list[str]:
    if isinstance(item, dict):
        item = ambient_voice_provenance_hook_record_from_dict(item)

    errors: list[str] = []
    if not item.hook_id:
        errors.append("missing hook id")
    if item.hook_type not in ALLOWED_AMBIENT_VOICE_PROVENANCE_HOOK_TYPES:
        errors.append("invalid hook type")
    if not item.source_subsystem or item.source_subsystem == "unknown":
        errors.append("missing source subsystem")
    if item.hook_type in POST_SPEAK_HOOK_TYPES and not item.trace_refs:
        errors.append("missing trace refs for post-speak hook")
    if item.llm_assisted and (not item.model_provider or not item.model_name):
        errors.append("LLM-assisted hook requires provider/model")

    required_fields = {
        "requires_pre_speak_attribution": item.requires_pre_speak_attribution,
        "requires_output_provenance": item.requires_output_provenance,
        "requires_source_registry_entry": item.requires_source_registry_entry,
        "requires_post_speak_confirmation": item.requires_post_speak_confirmation,
        "requires_append_only_log": item.requires_append_only_log,
    }
    for field_name, enabled in required_fields.items():
        if not enabled:
            errors.append(f"required provenance field disabled: {field_name}")

    errors.extend(validate_ambient_voice_provenance_wiring_safety_flags(item.safety_flags))
    return errors
