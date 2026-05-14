"""WESLR Who Said That Runtime Query Schema V1.

Schema-only dataclasses and validation helpers for future runtime
"who said that?" query routing. This module does not implement runtime
routing, chat responder behavior, voice gateway behavior, ambient loop
behavior, TTS/STT behavior, queue writes, config changes, memory mutation,
attribution log reads/writes, model/advisor calls, answer selection, or
truth/soundness/score authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ALLOWED_INPUT_CHANNELS = {"chat", "voice", "terminal", "operator_cli", "unknown"}
ALLOWED_INTENT_TYPES = {
    "who_said_that",
    "what_generated_that",
    "was_llm_involved",
    "what_triggered_that",
    "why_did_you_say_that",
    "which_subsystem_generated_that",
    "was_that_weslr_owned",
    "show_last_voice_attribution",
    "unknown",
}
ALLOWED_LOOKUP_MODES = {
    "most_recent",
    "by_utterance_id",
    "by_trace_ref",
    "by_time_window",
    "manual_review_only",
    "unknown",
}

PROHIBITED_SAFETY_FLAG_FIELDS = {
    "runtime_integration_attempted": "runtime integration attempted",
    "chat_wiring_attempted": "chat wiring attempted",
    "voice_wiring_attempted": "voice wiring attempted",
    "log_read_attempted": "log read attempted",
    "log_write_attempted": "log write attempted",
    "queue_write_attempted": "queue write attempted",
    "memory_mutation_attempted": "memory mutation attempted",
    "model_call_attempted": "model call attempted",
    "advisor_call_attempted": "advisor call attempted",
    "answer_selection_attempted": "answer selection attempted",
    "truth_authority_claimed": "truth authority claimed",
    "soundness_authority_claimed": "soundness authority claimed",
    "score_authority_claimed": "score authority claimed",
    "official_score_claimed": "official score claimed",
    "raw_text_storage_attempted": "raw text storage attempted",
    "provenance_guessing_attempted": "provenance guessing attempted",
    "unsupported_self_ownership_claimed": "unsupported self-ownership claimed",
    "hidden_llm_authority": "hidden LLM authority",
}


@dataclass
class WhoSaidThatRuntimeQuerySafetyFlags:
    runtime_integration_attempted: bool = False
    chat_wiring_attempted: bool = False
    voice_wiring_attempted: bool = False
    log_read_attempted: bool = False
    log_write_attempted: bool = False
    queue_write_attempted: bool = False
    memory_mutation_attempted: bool = False
    model_call_attempted: bool = False
    advisor_call_attempted: bool = False
    answer_selection_attempted: bool = False
    truth_authority_claimed: bool = False
    soundness_authority_claimed: bool = False
    score_authority_claimed: bool = False
    official_score_claimed: bool = False
    raw_text_storage_attempted: bool = False
    provenance_guessing_attempted: bool = False
    unsupported_self_ownership_claimed: bool = False
    hidden_llm_authority: bool = False


@dataclass
class WhoSaidThatRuntimeQueryRequest:
    schema_version: str = "1.0"
    request_id: str = ""
    input_channel: str = "unknown"
    raw_text_stored: bool = False
    query_text_hash: str = ""
    detected_intent_type: str = "unknown"
    lookup_mode: str = "unknown"
    requested_utterance_id: str = ""
    requested_trace_ref: str = ""
    routing_allowed: bool = False
    operator_review_required: bool = True
    safety_flags: WhoSaidThatRuntimeQuerySafetyFlags = field(default_factory=WhoSaidThatRuntimeQuerySafetyFlags)


@dataclass
class WhoSaidThatRuntimeQueryResult:
    schema_version: str = "1.0"
    result_id: str = ""
    request_id: str = ""
    attribution_answer_id: str = ""
    input_channel: str = "unknown"
    detected_intent_type: str = "unknown"
    lookup_mode: str = "unknown"
    routing_allowed: bool = False
    runtime_integration_performed: bool = False
    log_read_performed: bool = False
    log_write_performed: bool = False
    queue_write_performed: bool = False
    memory_mutation_performed: bool = False
    model_advisor_call_performed: bool = False
    answer_selection_performed: bool = False
    truth_soundness_score_claimed: bool = False
    operator_review_required: bool = True
    safety_flags: WhoSaidThatRuntimeQuerySafetyFlags = field(default_factory=WhoSaidThatRuntimeQuerySafetyFlags)


def _apply_overrides(item: Any, overrides: dict[str, Any], label: str) -> Any:
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown {label} field: {key}")
        setattr(item, key, value)
    return item


def create_empty_who_said_that_runtime_query_safety_flags(**overrides: Any) -> WhoSaidThatRuntimeQuerySafetyFlags:
    return _apply_overrides(WhoSaidThatRuntimeQuerySafetyFlags(), overrides, "who said that runtime query safety flags")


def create_empty_who_said_that_runtime_query_request(request_id: str = "", **overrides: Any) -> WhoSaidThatRuntimeQueryRequest:
    item = WhoSaidThatRuntimeQueryRequest(request_id=request_id)
    return _apply_overrides(item, overrides, "who said that runtime query request")


def create_empty_who_said_that_runtime_query_result(result_id: str = "", request_id: str = "", **overrides: Any) -> WhoSaidThatRuntimeQueryResult:
    item = WhoSaidThatRuntimeQueryResult(result_id=result_id, request_id=request_id)
    return _apply_overrides(item, overrides, "who said that runtime query result")


def _coerce_safety_flags(value: WhoSaidThatRuntimeQuerySafetyFlags | dict[str, Any] | None) -> WhoSaidThatRuntimeQuerySafetyFlags:
    if isinstance(value, WhoSaidThatRuntimeQuerySafetyFlags):
        return value
    if isinstance(value, dict):
        return WhoSaidThatRuntimeQuerySafetyFlags(**value)
    return WhoSaidThatRuntimeQuerySafetyFlags()


def who_said_that_runtime_query_safety_flags_to_dict(item: WhoSaidThatRuntimeQuerySafetyFlags) -> dict[str, Any]:
    return asdict(item)


def who_said_that_runtime_query_safety_flags_from_dict(data: dict[str, Any]) -> WhoSaidThatRuntimeQuerySafetyFlags:
    return WhoSaidThatRuntimeQuerySafetyFlags(**dict(data))


def who_said_that_runtime_query_request_to_dict(item: WhoSaidThatRuntimeQueryRequest) -> dict[str, Any]:
    return asdict(item)


def who_said_that_runtime_query_request_from_dict(data: dict[str, Any]) -> WhoSaidThatRuntimeQueryRequest:
    payload = dict(data)
    payload["safety_flags"] = _coerce_safety_flags(payload.get("safety_flags"))
    return WhoSaidThatRuntimeQueryRequest(**payload)


def who_said_that_runtime_query_result_to_dict(item: WhoSaidThatRuntimeQueryResult) -> dict[str, Any]:
    return asdict(item)


def who_said_that_runtime_query_result_from_dict(data: dict[str, Any]) -> WhoSaidThatRuntimeQueryResult:
    payload = dict(data)
    payload["safety_flags"] = _coerce_safety_flags(payload.get("safety_flags"))
    return WhoSaidThatRuntimeQueryResult(**payload)


def _flag_errors(flags: WhoSaidThatRuntimeQuerySafetyFlags) -> list[str]:
    errors: list[str] = []
    for field_name, label in PROHIBITED_SAFETY_FLAG_FIELDS.items():
        if getattr(flags, field_name):
            errors.append(label)
    return errors


def validate_who_said_that_runtime_query_request(item: WhoSaidThatRuntimeQueryRequest) -> list[str]:
    errors: list[str] = []
    if not item.request_id.strip():
        errors.append("missing request_id")
    if item.input_channel not in ALLOWED_INPUT_CHANNELS:
        errors.append("invalid input_channel")
    if item.detected_intent_type not in ALLOWED_INTENT_TYPES:
        errors.append("invalid detected_intent_type")
    if item.lookup_mode not in ALLOWED_LOOKUP_MODES:
        errors.append("invalid lookup_mode")
    if item.raw_text_stored:
        errors.append("raw_text_stored true")
    if item.lookup_mode == "by_utterance_id" and not item.requested_utterance_id.strip():
        errors.append("by_utterance_id requires requested_utterance_id")
    if item.lookup_mode == "by_trace_ref" and not item.requested_trace_ref.strip():
        errors.append("by_trace_ref requires requested_trace_ref")
    if not item.operator_review_required:
        errors.append("operator_review_required disabled")
    errors.extend(_flag_errors(item.safety_flags))
    return errors


def validate_who_said_that_runtime_query_result(item: WhoSaidThatRuntimeQueryResult) -> list[str]:
    errors: list[str] = []
    if not item.result_id.strip():
        errors.append("missing result_id")
    if not item.request_id.strip():
        errors.append("missing request_id")
    if item.input_channel not in ALLOWED_INPUT_CHANNELS:
        errors.append("invalid input_channel")
    if item.detected_intent_type not in ALLOWED_INTENT_TYPES:
        errors.append("invalid detected_intent_type")
    if item.lookup_mode not in ALLOWED_LOOKUP_MODES:
        errors.append("invalid lookup_mode")
    if item.runtime_integration_performed:
        errors.append("runtime integration performed")
    if item.log_read_performed:
        errors.append("log read performed")
    if item.log_write_performed:
        errors.append("log write performed")
    if item.queue_write_performed:
        errors.append("queue write performed")
    if item.memory_mutation_performed:
        errors.append("memory mutation performed")
    if item.model_advisor_call_performed:
        errors.append("model/advisor call performed")
    if item.answer_selection_performed:
        errors.append("answer selection performed")
    if item.truth_soundness_score_claimed:
        errors.append("truth/soundness/score claim made")
    if not item.operator_review_required:
        errors.append("operator_review_required disabled")
    errors.extend(_flag_errors(item.safety_flags))
    return errors


def summarize_who_said_that_runtime_query_safety() -> dict[str, bool]:
    """Return schema-phase side-effect posture without performing routing."""
    return {
        "runtime_integration_performed": False,
        "chat_wiring_performed": False,
        "voice_wiring_performed": False,
        "log_read_performed": False,
        "log_write_performed": False,
        "queue_write_performed": False,
        "memory_mutation_performed": False,
        "model_advisor_call_performed": False,
        "answer_selection_performed": False,
        "truth_soundness_score_claimed": False,
    }
