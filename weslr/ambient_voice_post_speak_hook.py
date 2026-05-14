"""WESLR Ambient Voice Post-Speak Hook Schema V1.

Schema dataclasses and validation helpers for future post-speak attribution
hook inputs and results. This module is schema-only: it does not implement hook
behavior, wire voice gateway, ambient loop, TTS/STT, runtime/chat, queues,
config, memory, model/advisor calls, trigger speech, or write .weslr/voice_source_attribution.jsonl.
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
class AmbientVoicePostSpeakHookSafetyFlags:
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
class AmbientVoicePostSpeakHookInput:
    schema_version: str = "1.0"
    input_id: str = ""
    hook_id: str = ""
    pre_speak_result_id: str = ""
    utterance_id: str = ""
    output_provenance_id: str = ""
    attribution_record_id: str = ""
    pre_speak_log_event_id: str = ""
    source_subsystem: str = "unknown"
    tts_engine: str = "unknown"
    stt_engine: str = "unknown"
    speech_attempted: bool = False
    speech_success: bool = False
    speech_failed: bool = False
    speech_blocked: bool = False
    failure_reason: str = ""
    no_ownership_claim_required: bool = True
    operator_review_required: bool = True
    trace_refs: list[str] = field(default_factory=list)
    safety_flags: AmbientVoicePostSpeakHookSafetyFlags = field(default_factory=AmbientVoicePostSpeakHookSafetyFlags)


@dataclass
class AmbientVoicePostSpeakHookResult:
    schema_version: str = "1.0"
    result_id: str = ""
    hook_id: str = ""
    input_id: str = ""
    pre_speak_result_id: str = ""
    utterance_id: str = ""
    output_provenance_id: str = ""
    attribution_record_id: str = ""
    pre_speak_log_event_id: str = ""
    post_speak_log_event_id: str = ""
    source_subsystem: str = "unknown"
    tts_engine: str = "unknown"
    stt_engine: str = "unknown"
    speech_attempted: bool = False
    speech_success: bool = False
    speech_failed: bool = False
    speech_blocked: bool = False
    failure_reason: str = ""
    no_ownership_claim_required: bool = True
    operator_review_required: bool = True
    trace_refs: list[str] = field(default_factory=list)
    safety_flags: AmbientVoicePostSpeakHookSafetyFlags = field(default_factory=AmbientVoicePostSpeakHookSafetyFlags)


def create_empty_ambient_voice_post_speak_hook_input(**overrides: Any) -> AmbientVoicePostSpeakHookInput:
    item = AmbientVoicePostSpeakHookInput()
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown post-speak hook input field: {key}")
        setattr(item, key, value)
    return item


def create_empty_ambient_voice_post_speak_hook_result(**overrides: Any) -> AmbientVoicePostSpeakHookResult:
    item = AmbientVoicePostSpeakHookResult()
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown post-speak hook result field: {key}")
        setattr(item, key, value)
    return item


def _coerce_safety_flags(flags: AmbientVoicePostSpeakHookSafetyFlags | dict[str, Any] | None) -> AmbientVoicePostSpeakHookSafetyFlags:
    if flags is None:
        return AmbientVoicePostSpeakHookSafetyFlags()
    if isinstance(flags, AmbientVoicePostSpeakHookSafetyFlags):
        return flags
    if isinstance(flags, dict):
        return AmbientVoicePostSpeakHookSafetyFlags(**flags)
    raise TypeError("invalid post-speak hook safety flags")


def ambient_voice_post_speak_hook_safety_flags_to_dict(item: AmbientVoicePostSpeakHookSafetyFlags) -> dict[str, Any]:
    return asdict(item)


def ambient_voice_post_speak_hook_safety_flags_from_dict(data: dict[str, Any]) -> AmbientVoicePostSpeakHookSafetyFlags:
    return AmbientVoicePostSpeakHookSafetyFlags(**dict(data))


def ambient_voice_post_speak_hook_input_to_dict(item: AmbientVoicePostSpeakHookInput) -> dict[str, Any]:
    return asdict(item)


def ambient_voice_post_speak_hook_input_from_dict(data: dict[str, Any]) -> AmbientVoicePostSpeakHookInput:
    payload = dict(data)
    payload["safety_flags"] = _coerce_safety_flags(payload.get("safety_flags"))
    return AmbientVoicePostSpeakHookInput(**payload)


def ambient_voice_post_speak_hook_result_to_dict(item: AmbientVoicePostSpeakHookResult) -> dict[str, Any]:
    return asdict(item)


def ambient_voice_post_speak_hook_result_from_dict(data: dict[str, Any]) -> AmbientVoicePostSpeakHookResult:
    payload = dict(data)
    payload["safety_flags"] = _coerce_safety_flags(payload.get("safety_flags"))
    return AmbientVoicePostSpeakHookResult(**payload)


def validate_ambient_voice_post_speak_hook_safety_flags(flags: AmbientVoicePostSpeakHookSafetyFlags | dict[str, Any] | None) -> list[str]:
    flags = _coerce_safety_flags(flags)
    errors: list[str] = []
    for field_name, label in PROHIBITED_SAFETY_FLAG_FIELDS.items():
        if getattr(flags, field_name):
            errors.append(label)
    return errors


def _validate_common_fields(item: AmbientVoicePostSpeakHookInput | AmbientVoicePostSpeakHookResult) -> list[str]:
    errors: list[str] = []
    if not item.hook_id:
        errors.append("missing hook id")
    if not item.pre_speak_result_id:
        errors.append("missing pre-speak result ID")
    if not item.utterance_id:
        errors.append("missing utterance ID")
    if not item.output_provenance_id:
        errors.append("missing output provenance ID")
    if not item.attribution_record_id:
        errors.append("missing attribution record ID")
    if item.speech_success and not item.speech_attempted:
        errors.append("speech success without speech attempted")
    if item.speech_success and item.speech_failed:
        errors.append("speech success and failure both true")
    if item.speech_blocked and item.speech_success:
        errors.append("speech blocked and speech success both true")
    if item.speech_success and not item.trace_refs:
        errors.append("speech success without trace refs")
    if item.speech_failed and not item.failure_reason:
        errors.append("speech failure without failure reason")
    if item.speech_blocked and not item.failure_reason:
        errors.append("speech blocked without failure reason")
    if (not item.speech_success) and not item.no_ownership_claim_required:
        errors.append("ownership claim allowed when speech was not emitted")
    errors.extend(validate_ambient_voice_post_speak_hook_safety_flags(item.safety_flags))
    return errors


def validate_ambient_voice_post_speak_hook_input(item: AmbientVoicePostSpeakHookInput | dict[str, Any]) -> list[str]:
    if isinstance(item, dict):
        item = ambient_voice_post_speak_hook_input_from_dict(item)
    errors = []
    if not item.input_id:
        errors.append("missing input id")
    errors.extend(_validate_common_fields(item))
    return errors


def validate_ambient_voice_post_speak_hook_result(item: AmbientVoicePostSpeakHookResult | dict[str, Any]) -> list[str]:
    if isinstance(item, dict):
        item = ambient_voice_post_speak_hook_result_from_dict(item)
    errors = []
    if not item.result_id:
        errors.append("missing result id")
    if not item.input_id:
        errors.append("missing input id")
    errors.extend(_validate_common_fields(item))
    return errors
