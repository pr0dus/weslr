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


def create_post_speak_hook_input_from_metadata(
    *,
    input_id: str,
    hook_id: str,
    pre_speak_result_id: str,
    utterance_id: str,
    output_provenance_id: str,
    attribution_record_id: str,
    pre_speak_log_event_id: str = "",
    source_subsystem: str = "unknown",
    tts_engine: str = "unknown",
    stt_engine: str = "unknown",
    speech_attempted: bool = False,
    speech_success: bool = False,
    speech_failed: bool = False,
    speech_blocked: bool = False,
    failure_reason: str = "",
    no_ownership_claim_required: bool = True,
    operator_review_required: bool = True,
    trace_refs: list[str] | None = None,
    safety_flags: AmbientVoicePostSpeakHookSafetyFlags | dict[str, Any] | None = None,
) -> AmbientVoicePostSpeakHookInput:
    """Create an in-memory post-speak hook input from explicit metadata only."""
    return create_empty_ambient_voice_post_speak_hook_input(
        input_id=input_id,
        hook_id=hook_id,
        pre_speak_result_id=pre_speak_result_id,
        utterance_id=utterance_id,
        output_provenance_id=output_provenance_id,
        attribution_record_id=attribution_record_id,
        pre_speak_log_event_id=pre_speak_log_event_id,
        source_subsystem=source_subsystem,
        tts_engine=tts_engine,
        stt_engine=stt_engine,
        speech_attempted=speech_attempted,
        speech_success=speech_success,
        speech_failed=speech_failed,
        speech_blocked=speech_blocked,
        failure_reason=failure_reason,
        no_ownership_claim_required=no_ownership_claim_required,
        operator_review_required=operator_review_required,
        trace_refs=list(trace_refs or []),
        safety_flags=_coerce_safety_flags(safety_flags),
    )


def create_post_speak_hook_result_from_input(
    input_item: AmbientVoicePostSpeakHookInput | dict[str, Any],
    *,
    result_id: str,
    post_speak_log_event_id: str = "",
) -> AmbientVoicePostSpeakHookResult:
    """Create an in-memory post-speak hook result without side effects."""
    if isinstance(input_item, dict):
        input_item = ambient_voice_post_speak_hook_input_from_dict(input_item)
    return create_empty_ambient_voice_post_speak_hook_result(
        result_id=result_id,
        hook_id=input_item.hook_id,
        input_id=input_item.input_id,
        pre_speak_result_id=input_item.pre_speak_result_id,
        utterance_id=input_item.utterance_id,
        output_provenance_id=input_item.output_provenance_id,
        attribution_record_id=input_item.attribution_record_id,
        pre_speak_log_event_id=input_item.pre_speak_log_event_id,
        post_speak_log_event_id=post_speak_log_event_id,
        source_subsystem=input_item.source_subsystem,
        tts_engine=input_item.tts_engine,
        stt_engine=input_item.stt_engine,
        speech_attempted=input_item.speech_attempted,
        speech_success=input_item.speech_success,
        speech_failed=input_item.speech_failed,
        speech_blocked=input_item.speech_blocked,
        failure_reason=input_item.failure_reason,
        no_ownership_claim_required=input_item.no_ownership_claim_required,
        operator_review_required=input_item.operator_review_required or not input_item.speech_success,
        trace_refs=list(input_item.trace_refs),
        safety_flags=input_item.safety_flags,
    )


def create_successful_post_speak_hook_result(
    *,
    result_id: str,
    input_id: str,
    hook_id: str,
    pre_speak_result_id: str,
    utterance_id: str,
    output_provenance_id: str,
    attribution_record_id: str,
    pre_speak_log_event_id: str = "",
    post_speak_log_event_id: str = "",
    source_subsystem: str = "unknown",
    tts_engine: str = "unknown",
    stt_engine: str = "unknown",
    trace_refs: list[str] | None = None,
) -> AmbientVoicePostSpeakHookResult:
    """Create a successful post-speak result; validation still enforces required references."""
    input_item = create_post_speak_hook_input_from_metadata(
        input_id=input_id,
        hook_id=hook_id,
        pre_speak_result_id=pre_speak_result_id,
        utterance_id=utterance_id,
        output_provenance_id=output_provenance_id,
        attribution_record_id=attribution_record_id,
        pre_speak_log_event_id=pre_speak_log_event_id,
        source_subsystem=source_subsystem,
        tts_engine=tts_engine,
        stt_engine=stt_engine,
        speech_attempted=True,
        speech_success=True,
        speech_failed=False,
        speech_blocked=False,
        failure_reason="",
        no_ownership_claim_required=True,
        operator_review_required=True,
        trace_refs=trace_refs,
    )
    return create_post_speak_hook_result_from_input(input_item, result_id=result_id, post_speak_log_event_id=post_speak_log_event_id)


def create_failed_post_speak_hook_result(
    *,
    result_id: str,
    input_id: str,
    hook_id: str,
    pre_speak_result_id: str,
    utterance_id: str,
    output_provenance_id: str,
    attribution_record_id: str,
    failure_reason: str,
    pre_speak_log_event_id: str = "",
    post_speak_log_event_id: str = "",
    source_subsystem: str = "unknown",
    tts_engine: str = "unknown",
    stt_engine: str = "unknown",
    trace_refs: list[str] | None = None,
) -> AmbientVoicePostSpeakHookResult:
    """Create a failed post-speak result with no ownership claim allowed."""
    input_item = create_post_speak_hook_input_from_metadata(
        input_id=input_id,
        hook_id=hook_id,
        pre_speak_result_id=pre_speak_result_id,
        utterance_id=utterance_id,
        output_provenance_id=output_provenance_id,
        attribution_record_id=attribution_record_id,
        pre_speak_log_event_id=pre_speak_log_event_id,
        source_subsystem=source_subsystem,
        tts_engine=tts_engine,
        stt_engine=stt_engine,
        speech_attempted=True,
        speech_success=False,
        speech_failed=True,
        speech_blocked=False,
        failure_reason=failure_reason,
        no_ownership_claim_required=True,
        operator_review_required=True,
        trace_refs=trace_refs,
    )
    return create_post_speak_hook_result_from_input(input_item, result_id=result_id, post_speak_log_event_id=post_speak_log_event_id)


def create_blocked_post_speak_hook_result(
    *,
    result_id: str,
    input_id: str,
    hook_id: str,
    pre_speak_result_id: str,
    utterance_id: str,
    output_provenance_id: str,
    attribution_record_id: str,
    failure_reason: str,
    pre_speak_log_event_id: str = "",
    post_speak_log_event_id: str = "",
    source_subsystem: str = "unknown",
    tts_engine: str = "unknown",
    stt_engine: str = "unknown",
    trace_refs: list[str] | None = None,
) -> AmbientVoicePostSpeakHookResult:
    """Create a blocked post-speak result with no ownership claim allowed."""
    input_item = create_post_speak_hook_input_from_metadata(
        input_id=input_id,
        hook_id=hook_id,
        pre_speak_result_id=pre_speak_result_id,
        utterance_id=utterance_id,
        output_provenance_id=output_provenance_id,
        attribution_record_id=attribution_record_id,
        pre_speak_log_event_id=pre_speak_log_event_id,
        source_subsystem=source_subsystem,
        tts_engine=tts_engine,
        stt_engine=stt_engine,
        speech_attempted=False,
        speech_success=False,
        speech_failed=False,
        speech_blocked=True,
        failure_reason=failure_reason,
        no_ownership_claim_required=True,
        operator_review_required=True,
        trace_refs=trace_refs,
    )
    return create_post_speak_hook_result_from_input(input_item, result_id=result_id, post_speak_log_event_id=post_speak_log_event_id)


def summarize_post_speak_hook_result(result: AmbientVoicePostSpeakHookResult | dict[str, Any]) -> dict[str, Any]:
    """Return redacted, count-only post-speak result diagnostics."""
    if isinstance(result, dict):
        result = ambient_voice_post_speak_hook_result_from_dict(result)
    return {
        "summary_mode": "redacted_count_only",
        "speech_attempted": result.speech_attempted,
        "speech_success": result.speech_success,
        "speech_failed": result.speech_failed,
        "speech_blocked": result.speech_blocked,
        "no_ownership_claim_required": result.no_ownership_claim_required,
        "operator_review_required": result.operator_review_required,
        "trace_ref_count": len(result.trace_refs),
        "has_output_provenance": bool(result.output_provenance_id),
        "has_attribution_record": bool(result.attribution_record_id),
        "has_pre_speak_log_event": bool(result.pre_speak_log_event_id),
        "has_post_speak_log_event": bool(result.post_speak_log_event_id),
        "validation_error_count": len(validate_ambient_voice_post_speak_hook_result(result)),
        "runtime_voice_wiring_performed": False,
        "log_write_performed": False,
        "queue_write_performed": False,
        "memory_mutation_performed": False,
        "model_call_performed": False,
        "speech_triggered": False,
    }


def summarize_post_speak_hook_results(results: list[AmbientVoicePostSpeakHookResult | dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return redacted aggregate diagnostics for post-speak hook results."""
    items = [ambient_voice_post_speak_hook_result_from_dict(item) if isinstance(item, dict) else item for item in (results or [])]
    return {
        "summary_mode": "redacted_count_only",
        "result_count": len(items),
        "speech_attempted_count": sum(1 for item in items if item.speech_attempted),
        "speech_success_count": sum(1 for item in items if item.speech_success),
        "speech_failed_count": sum(1 for item in items if item.speech_failed),
        "speech_blocked_count": sum(1 for item in items if item.speech_blocked),
        "no_ownership_claim_required_count": sum(1 for item in items if item.no_ownership_claim_required),
        "operator_review_required_count": sum(1 for item in items if item.operator_review_required),
        "trace_ref_count_total": sum(len(item.trace_refs) for item in items),
        "validation_error_count_total": sum(len(validate_ambient_voice_post_speak_hook_result(item)) for item in items),
        "runtime_voice_wiring_performed": False,
        "log_write_performed": False,
        "queue_write_performed": False,
        "memory_mutation_performed": False,
        "model_call_performed": False,
        "speech_triggered": False,
    }
