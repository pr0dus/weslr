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


def create_pre_speak_hook_input_from_metadata(
    *,
    input_id: str,
    hook_id: str,
    source_subsystem: str,
    trigger: str,
    output_channel: str,
    intended_voice_tts_path: str,
    llm_assisted: bool = False,
    model_provider: str = "",
    model_name: str = "",
    output_provenance_id: str = "",
    source_registry_entry_id: str = "",
    trace_refs: list[str] | None = None,
    safety_flags: AmbientVoicePreSpeakHookSafetyFlags | dict[str, Any] | None = None,
) -> AmbientVoicePreSpeakHookInput:
    """Create an in-memory pre-speak hook input from explicit metadata only."""
    return create_empty_ambient_voice_pre_speak_hook_input(
        input_id=input_id,
        hook_id=hook_id,
        source_subsystem=source_subsystem,
        trigger=trigger,
        output_channel=output_channel,
        intended_voice_tts_path=intended_voice_tts_path,
        llm_assisted=llm_assisted,
        model_provider=model_provider,
        model_name=model_name,
        output_provenance_id=output_provenance_id,
        source_registry_entry_id=source_registry_entry_id,
        trace_refs=list(trace_refs or []),
        safety_flags=_coerce_safety_flags(safety_flags),
    )


def create_pre_speak_hook_result_from_input(
    input_item: AmbientVoicePreSpeakHookInput | dict[str, Any],
    *,
    result_id: str,
    attribution_record_id: str = "",
    pre_speak_log_event_id: str = "",
    output_provenance_id: str | None = None,
    source_registry_entry_id: str | None = None,
    trace_refs: list[str] | None = None,
    attribution_created: bool | None = None,
    attribution_validated: bool | None = None,
    operator_review_required: bool = True,
) -> AmbientVoicePreSpeakHookResult:
    """Build and validate an in-memory pre-speak result without side effects."""
    if isinstance(input_item, dict):
        input_item = ambient_voice_pre_speak_hook_input_from_dict(input_item)

    effective_output_provenance_id = input_item.output_provenance_id if output_provenance_id is None else output_provenance_id
    effective_source_registry_entry_id = input_item.source_registry_entry_id if source_registry_entry_id is None else source_registry_entry_id
    effective_trace_refs = list(input_item.trace_refs if trace_refs is None else trace_refs)
    created = bool(attribution_record_id) if attribution_created is None else attribution_created
    validated = bool(attribution_record_id) if attribution_validated is None else attribution_validated

    input_errors = validate_ambient_voice_pre_speak_hook_input(input_item)
    speech_allowed = bool(
        not input_errors
        and created
        and validated
        and effective_output_provenance_id
        and attribution_record_id
        and effective_trace_refs
    )

    return create_empty_ambient_voice_pre_speak_hook_result(
        result_id=result_id,
        input_id=input_item.input_id,
        hook_id=input_item.hook_id,
        source_subsystem=input_item.source_subsystem,
        trigger=input_item.trigger,
        output_channel=input_item.output_channel,
        intended_voice_tts_path=input_item.intended_voice_tts_path,
        llm_assisted=input_item.llm_assisted,
        model_provider=input_item.model_provider,
        model_name=input_item.model_name,
        output_provenance_id=effective_output_provenance_id,
        source_registry_entry_id=effective_source_registry_entry_id,
        attribution_record_id=attribution_record_id,
        pre_speak_log_event_id=pre_speak_log_event_id,
        attribution_created=created,
        attribution_validated=validated,
        speech_allowed=speech_allowed,
        unattributed_unknown_required=not speech_allowed,
        operator_review_required=operator_review_required or not speech_allowed,
        trace_refs=effective_trace_refs,
        safety_flags=input_item.safety_flags,
    )


def create_blocked_pre_speak_hook_result(
    input_item: AmbientVoicePreSpeakHookInput | dict[str, Any],
    *,
    result_id: str,
    reason: str = "missing_attribution",
) -> AmbientVoicePreSpeakHookResult:
    """Create a blocked, unattributed/unknown pre-speak result in memory."""
    if isinstance(input_item, dict):
        input_item = ambient_voice_pre_speak_hook_input_from_dict(input_item)
    return create_empty_ambient_voice_pre_speak_hook_result(
        result_id=result_id,
        input_id=input_item.input_id,
        hook_id=input_item.hook_id,
        source_subsystem=input_item.source_subsystem,
        trigger=input_item.trigger or reason,
        output_channel=input_item.output_channel,
        intended_voice_tts_path=input_item.intended_voice_tts_path,
        llm_assisted=input_item.llm_assisted,
        model_provider=input_item.model_provider,
        model_name=input_item.model_name,
        output_provenance_id=input_item.output_provenance_id,
        source_registry_entry_id=input_item.source_registry_entry_id,
        attribution_record_id="",
        pre_speak_log_event_id="",
        attribution_created=False,
        attribution_validated=False,
        speech_allowed=False,
        unattributed_unknown_required=True,
        operator_review_required=True,
        trace_refs=list(input_item.trace_refs),
        safety_flags=input_item.safety_flags,
    )


def summarize_pre_speak_hook_result(result: AmbientVoicePreSpeakHookResult | dict[str, Any]) -> dict[str, Any]:
    """Return redacted, count-only pre-speak result diagnostics."""
    if isinstance(result, dict):
        result = ambient_voice_pre_speak_hook_result_from_dict(result)
    return {
        "summary_mode": "redacted_count_only",
        "speech_allowed": result.speech_allowed,
        "unattributed_unknown_required": result.unattributed_unknown_required,
        "operator_review_required": result.operator_review_required,
        "llm_assisted": result.llm_assisted,
        "trace_ref_count": len(result.trace_refs),
        "has_output_provenance": bool(result.output_provenance_id),
        "has_source_registry_entry": bool(result.source_registry_entry_id),
        "has_attribution_record": bool(result.attribution_record_id),
        "has_pre_speak_log_event": bool(result.pre_speak_log_event_id),
        "validation_error_count": len(validate_ambient_voice_pre_speak_hook_result(result)),
        "runtime_voice_wiring_performed": False,
        "log_write_performed": False,
        "queue_write_performed": False,
        "memory_mutation_performed": False,
        "model_call_performed": False,
    }


def summarize_pre_speak_hook_results(results: list[AmbientVoicePreSpeakHookResult | dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return redacted aggregate diagnostics for pre-speak hook results."""
    items = [ambient_voice_pre_speak_hook_result_from_dict(item) if isinstance(item, dict) else item for item in (results or [])]
    return {
        "summary_mode": "redacted_count_only",
        "result_count": len(items),
        "speech_allowed_count": sum(1 for item in items if item.speech_allowed),
        "blocked_count": sum(1 for item in items if not item.speech_allowed),
        "unattributed_unknown_count": sum(1 for item in items if item.unattributed_unknown_required),
        "operator_review_required_count": sum(1 for item in items if item.operator_review_required),
        "llm_assisted_count": sum(1 for item in items if item.llm_assisted),
        "trace_ref_count_total": sum(len(item.trace_refs) for item in items),
        "validation_error_count_total": sum(len(validate_ambient_voice_pre_speak_hook_result(item)) for item in items),
        "runtime_voice_wiring_performed": False,
        "log_write_performed": False,
        "queue_write_performed": False,
        "memory_mutation_performed": False,
        "model_call_performed": False,
    }
