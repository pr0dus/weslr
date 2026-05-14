"""WESLR Ambient Voice Pre-Speak Hook Schema V1.

Schema dataclasses and validation helpers for future pre-speak attribution
hook inputs and results. This module is schema-only: it does not implement hook
behavior, wire voice gateway, ambient loop, TTS/STT, runtime/chat, queues,
config, memory, model/advisor calls, or write .weslr/voice_source_attribution.jsonl.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


PROHIBITED_SAFETY_FLAG_FIELDS = {
    "raw_spoken_text_stored": "raw spoken text storage",
    "hidden_llm_authority": "hidden LLM authority",
    "hidden_provider_authority": "hidden provider authority",
    "memory_mutation_attempted": "memory mutation attempted",
    "queue_write_attempted": "queue write attempted",
    "log_write_attempted": "log write attempted",
    "runtime_wiring_attempted": "runtime wiring attempted",
    "voice_wiring_attempted": "voice wiring attempted",
    "model_call_attempted": "model call attempted",
    "advisor_call_attempted": "advisor call attempted",
    "self_improvement_activation_attempted": "self-improvement activation attempted",
    "truth_authority_claimed": "truth authority claimed",
    "soundness_authority_claimed": "soundness authority claimed",
    "official_score_claimed": "official score claimed",
}


@dataclass
class AmbientVoicePreSpeakHookSafetyFlags:
    raw_spoken_text_stored: bool = False
    hidden_llm_authority: bool = False
    hidden_provider_authority: bool = False
    memory_mutation_attempted: bool = False
    queue_write_attempted: bool = False
    log_write_attempted: bool = False
    runtime_wiring_attempted: bool = False
    voice_wiring_attempted: bool = False
    model_call_attempted: bool = False
    advisor_call_attempted: bool = False
    self_improvement_activation_attempted: bool = False
    truth_authority_claimed: bool = False
    soundness_authority_claimed: bool = False
    official_score_claimed: bool = False


@dataclass
class AmbientVoicePreSpeakHookInput:
    schema_version: str = "1.0"
    input_id: str = ""
    hook_id: str = ""
    source_subsystem: str = "unknown"
    trigger: str = ""
    output_channel: str = "voice"
    intended_voice_tts_path: str = "unknown"
    llm_assisted: bool = False
    model_provider: str = ""
    model_name: str = ""
    output_provenance_id: str = ""
    source_registry_entry_id: str = ""
    trace_refs: list[str] = field(default_factory=list)
    safety_flags: AmbientVoicePreSpeakHookSafetyFlags = field(default_factory=AmbientVoicePreSpeakHookSafetyFlags)


@dataclass
class AmbientVoicePreSpeakHookResult:
    schema_version: str = "1.0"
    result_id: str = ""
    hook_id: str = ""
    input_id: str = ""
    source_subsystem: str = "unknown"
    trigger: str = ""
    output_channel: str = "voice"
    intended_voice_tts_path: str = "unknown"
    llm_assisted: bool = False
    model_provider: str = ""
    model_name: str = ""
    output_provenance_id: str = ""
    source_registry_entry_id: str = ""
    attribution_record_id: str = ""
    pre_speak_log_event_id: str = ""
    attribution_created: bool = False
    attribution_validated: bool = False
    speech_allowed: bool = False
    unattributed_unknown_required: bool = True
    operator_review_required: bool = True
    trace_refs: list[str] = field(default_factory=list)
    safety_flags: AmbientVoicePreSpeakHookSafetyFlags = field(default_factory=AmbientVoicePreSpeakHookSafetyFlags)


def create_empty_ambient_voice_pre_speak_hook_input(**overrides: Any) -> AmbientVoicePreSpeakHookInput:
    item = AmbientVoicePreSpeakHookInput()
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown pre-speak hook input field: {key}")
        setattr(item, key, value)
    return item


def create_empty_ambient_voice_pre_speak_hook_result(**overrides: Any) -> AmbientVoicePreSpeakHookResult:
    item = AmbientVoicePreSpeakHookResult()
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown pre-speak hook result field: {key}")
        setattr(item, key, value)
    return item


def ambient_voice_pre_speak_hook_safety_flags_to_dict(item: AmbientVoicePreSpeakHookSafetyFlags) -> dict[str, Any]:
    return asdict(item)


def ambient_voice_pre_speak_hook_safety_flags_from_dict(data: dict[str, Any]) -> AmbientVoicePreSpeakHookSafetyFlags:
    return AmbientVoicePreSpeakHookSafetyFlags(**dict(data))


def ambient_voice_pre_speak_hook_input_to_dict(item: AmbientVoicePreSpeakHookInput) -> dict[str, Any]:
    return asdict(item)


def ambient_voice_pre_speak_hook_input_from_dict(data: dict[str, Any]) -> AmbientVoicePreSpeakHookInput:
    payload = dict(data)
    payload["safety_flags"] = _coerce_safety_flags(payload.get("safety_flags"))
    return AmbientVoicePreSpeakHookInput(**payload)


def ambient_voice_pre_speak_hook_result_to_dict(item: AmbientVoicePreSpeakHookResult) -> dict[str, Any]:
    return asdict(item)


def ambient_voice_pre_speak_hook_result_from_dict(data: dict[str, Any]) -> AmbientVoicePreSpeakHookResult:
    payload = dict(data)
    payload["safety_flags"] = _coerce_safety_flags(payload.get("safety_flags"))
    return AmbientVoicePreSpeakHookResult(**payload)


def _coerce_safety_flags(flags: AmbientVoicePreSpeakHookSafetyFlags | dict[str, Any] | None) -> AmbientVoicePreSpeakHookSafetyFlags:
    if flags is None:
        return AmbientVoicePreSpeakHookSafetyFlags()
    if isinstance(flags, AmbientVoicePreSpeakHookSafetyFlags):
        return flags
    if isinstance(flags, dict):
        return AmbientVoicePreSpeakHookSafetyFlags(**flags)
    raise TypeError("invalid pre-speak hook safety flags")


def validate_ambient_voice_pre_speak_hook_safety_flags(
    flags: AmbientVoicePreSpeakHookSafetyFlags | dict[str, Any] | None,
) -> list[str]:
    flags = _coerce_safety_flags(flags)
    errors: list[str] = []
    for field_name, label in PROHIBITED_SAFETY_FLAG_FIELDS.items():
        if getattr(flags, field_name):
            errors.append(label)
    return errors


def _validate_common_fields(item: AmbientVoicePreSpeakHookInput | AmbientVoicePreSpeakHookResult) -> list[str]:
    errors: list[str] = []
    if not item.hook_id:
        errors.append("missing hook id")
    if not item.source_subsystem or item.source_subsystem == "unknown":
        errors.append("missing source subsystem")
    if not item.trigger:
        errors.append("missing trigger")
    if not item.output_channel:
        errors.append("missing output channel")
    if item.llm_assisted and (not item.model_provider or not item.model_name):
        errors.append("LLM-assisted hook requires provider/model")
    errors.extend(validate_ambient_voice_pre_speak_hook_safety_flags(item.safety_flags))
    return errors


def validate_ambient_voice_pre_speak_hook_input(
    item: AmbientVoicePreSpeakHookInput | dict[str, Any],
) -> list[str]:
    if isinstance(item, dict):
        item = ambient_voice_pre_speak_hook_input_from_dict(item)
    errors = []
    if not item.input_id:
        errors.append("missing input id")
    errors.extend(_validate_common_fields(item))
    return errors


def validate_ambient_voice_pre_speak_hook_result(
    item: AmbientVoicePreSpeakHookResult | dict[str, Any],
) -> list[str]:
    if isinstance(item, dict):
        item = ambient_voice_pre_speak_hook_result_from_dict(item)
    errors = []
    if not item.result_id:
        errors.append("missing result id")
    if not item.input_id:
        errors.append("missing input id")
    errors.extend(_validate_common_fields(item))

    if item.speech_allowed:
        if not item.attribution_created or not item.attribution_validated:
            errors.append("speech allowed without attribution validated")
        if not item.output_provenance_id:
            errors.append("speech allowed without output provenance ID")
        if not item.attribution_record_id:
            errors.append("speech allowed without attribution record ID")
        if not item.trace_refs:
            errors.append("speech allowed without trace refs")
        if item.unattributed_unknown_required:
            errors.append("speech allowed while unattributed/unknown required")
    else:
        if not item.unattributed_unknown_required:
            errors.append("blocked speech must be marked unattributed/unknown")

    return errors
