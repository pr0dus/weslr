"""WESLR Who Said That Chat Routing Schema V1.

Schema-only dataclasses and validation helpers for future chat routing of
"who said that?" attribution queries. This module does not implement chat
routing, modify chat responders, wire runtime/voice behavior, read or write
attribution logs, write queues, mutate memory/config, call models/advisors,
select answers, or claim truth/soundness/score authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ALLOWED_INPUT_CHANNELS = {"chat", "webchat", "discord", "telegram", "signal", "operator_cli", "unknown"}
ALLOWED_ATTRIBUTION_INTENTS = {
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
ALLOWED_PHRASE_FAMILIES = {
    "who_said_that",
    "what_generated_that",
    "was_that_weslr",
    "was_that_weslr_owned",
    "was_llm_involved",
    "what_triggered_that",
    "why_did_you_say_that",
    "show_last_voice_attribution",
    "unknown",
}
ALLOWED_CONFIDENCE_VALUES = {"low", "medium", "high", "unknown"}

PROHIBITED_SAFETY_FLAG_FIELDS = {
    "routing_attempted": "routing attempted",
    "chat_responder_modified": "chat responder modified",
    "runtime_integration_attempted": "runtime integration attempted",
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
class WhoSaidThatChatRoutingSafetyFlags:
    routing_attempted: bool = False
    chat_responder_modified: bool = False
    runtime_integration_attempted: bool = False
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
class WhoSaidThatChatRoutingRequest:
    schema_version: str = "1.0"
    request_id: str = ""
    input_channel: str = "unknown"
    raw_text_stored: bool = False
    message_text_hash: str = ""
    detected_attribution_intent: str = "unknown"
    matched_phrase_family: str = "unknown"
    confidence: str = "unknown"
    operator_review_required: bool = True
    safety_flags: WhoSaidThatChatRoutingSafetyFlags = field(default_factory=WhoSaidThatChatRoutingSafetyFlags)


@dataclass
class WhoSaidThatChatRoutingDecision:
    schema_version: str = "1.0"
    decision_id: str = ""
    request_id: str = ""
    input_channel: str = "unknown"
    detected_attribution_intent: str = "unknown"
    matched_phrase_family: str = "unknown"
    confidence: str = "unknown"
    should_route: bool = False
    runtime_query_request_id: str = ""
    routing_performed: bool = False
    log_read_performed: bool = False
    log_write_performed: bool = False
    queue_write_performed: bool = False
    memory_mutation_performed: bool = False
    model_advisor_call_performed: bool = False
    answer_selection_performed: bool = False
    truth_soundness_score_claimed: bool = False
    operator_review_required: bool = True
    safety_flags: WhoSaidThatChatRoutingSafetyFlags = field(default_factory=WhoSaidThatChatRoutingSafetyFlags)


def _apply_overrides(item: Any, overrides: dict[str, Any], label: str) -> Any:
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown {label} field: {key}")
        setattr(item, key, value)
    return item


def create_empty_who_said_that_chat_routing_safety_flags(**overrides: Any) -> WhoSaidThatChatRoutingSafetyFlags:
    return _apply_overrides(WhoSaidThatChatRoutingSafetyFlags(), overrides, "who said that chat routing safety flags")


def create_empty_who_said_that_chat_routing_request(request_id: str = "", **overrides: Any) -> WhoSaidThatChatRoutingRequest:
    item = WhoSaidThatChatRoutingRequest(request_id=request_id)
    return _apply_overrides(item, overrides, "who said that chat routing request")


def create_empty_who_said_that_chat_routing_decision(decision_id: str = "", request_id: str = "", **overrides: Any) -> WhoSaidThatChatRoutingDecision:
    item = WhoSaidThatChatRoutingDecision(decision_id=decision_id, request_id=request_id)
    return _apply_overrides(item, overrides, "who said that chat routing decision")


def _coerce_safety_flags(value: WhoSaidThatChatRoutingSafetyFlags | dict[str, Any] | None) -> WhoSaidThatChatRoutingSafetyFlags:
    if isinstance(value, WhoSaidThatChatRoutingSafetyFlags):
        return value
    if isinstance(value, dict):
        return WhoSaidThatChatRoutingSafetyFlags(**value)
    return WhoSaidThatChatRoutingSafetyFlags()


def who_said_that_chat_routing_safety_flags_to_dict(item: WhoSaidThatChatRoutingSafetyFlags) -> dict[str, Any]:
    return asdict(item)


def who_said_that_chat_routing_safety_flags_from_dict(data: dict[str, Any]) -> WhoSaidThatChatRoutingSafetyFlags:
    return WhoSaidThatChatRoutingSafetyFlags(**dict(data))


def who_said_that_chat_routing_request_to_dict(item: WhoSaidThatChatRoutingRequest) -> dict[str, Any]:
    return asdict(item)


def who_said_that_chat_routing_request_from_dict(data: dict[str, Any]) -> WhoSaidThatChatRoutingRequest:
    payload = dict(data)
    payload["safety_flags"] = _coerce_safety_flags(payload.get("safety_flags"))
    return WhoSaidThatChatRoutingRequest(**payload)


def who_said_that_chat_routing_decision_to_dict(item: WhoSaidThatChatRoutingDecision) -> dict[str, Any]:
    return asdict(item)


def who_said_that_chat_routing_decision_from_dict(data: dict[str, Any]) -> WhoSaidThatChatRoutingDecision:
    payload = dict(data)
    payload["safety_flags"] = _coerce_safety_flags(payload.get("safety_flags"))
    return WhoSaidThatChatRoutingDecision(**payload)


def _flag_errors(flags: WhoSaidThatChatRoutingSafetyFlags) -> list[str]:
    errors: list[str] = []
    for field_name, label in PROHIBITED_SAFETY_FLAG_FIELDS.items():
        if getattr(flags, field_name):
            errors.append(label)
    return errors


def validate_who_said_that_chat_routing_request(item: WhoSaidThatChatRoutingRequest) -> list[str]:
    errors: list[str] = []
    if not item.request_id.strip():
        errors.append("missing request_id")
    if item.input_channel not in ALLOWED_INPUT_CHANNELS:
        errors.append("invalid input_channel")
    if item.detected_attribution_intent not in ALLOWED_ATTRIBUTION_INTENTS:
        errors.append("invalid detected_attribution_intent")
    if item.matched_phrase_family not in ALLOWED_PHRASE_FAMILIES:
        errors.append("invalid matched_phrase_family")
    if item.confidence not in ALLOWED_CONFIDENCE_VALUES:
        errors.append("invalid confidence")
    if item.raw_text_stored:
        errors.append("raw_text_stored true")
    if not item.operator_review_required:
        errors.append("operator_review_required disabled")
    errors.extend(_flag_errors(item.safety_flags))
    return errors


def validate_who_said_that_chat_routing_decision(item: WhoSaidThatChatRoutingDecision) -> list[str]:
    errors: list[str] = []
    if not item.decision_id.strip():
        errors.append("missing decision_id")
    if not item.request_id.strip():
        errors.append("missing request_id")
    if item.input_channel not in ALLOWED_INPUT_CHANNELS:
        errors.append("invalid input_channel")
    if item.detected_attribution_intent not in ALLOWED_ATTRIBUTION_INTENTS:
        errors.append("invalid detected_attribution_intent")
    if item.matched_phrase_family not in ALLOWED_PHRASE_FAMILIES:
        errors.append("invalid matched_phrase_family")
    if item.confidence not in ALLOWED_CONFIDENCE_VALUES:
        errors.append("invalid confidence")
    if item.routing_performed:
        errors.append("routing performed")
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


def summarize_who_said_that_chat_routing_safety() -> dict[str, bool]:
    return {
        "routing_performed": False,
        "chat_responder_modified": False,
        "runtime_integration_performed": False,
        "voice_wiring_performed": False,
        "log_read_performed": False,
        "log_write_performed": False,
        "queue_write_performed": False,
        "memory_mutation_performed": False,
        "model_advisor_call_performed": False,
        "answer_selection_performed": False,
        "truth_soundness_score_claimed": False,
    }


def classify_who_said_that_phrase_family(text: str) -> str:
    """Classify a transient explicit phrase into a safe attribution family.

    The phrase is used only for in-memory classification and is not stored in
    request or decision objects.
    """
    normalized = " ".join(text.strip().lower().replace("?", "").split())
    if not normalized:
        return "unknown"
    if normalized in {"who said that", "who said this", "who said it"}:
        return "who_said_that"
    if normalized in {"what generated that", "what generated this", "what produced that", "what produced this"}:
        return "what_generated_that"
    if normalized in {"was an llm involved", "was a model involved", "was ai involved"}:
        return "was_llm_involved"
    if normalized in {"what triggered that", "what triggered this"}:
        return "what_triggered_that"
    if normalized in {"why did you say that", "why did you say this"}:
        return "why_did_you_say_that"
    if normalized in {"was that weslr", "was this weslr", "was that weslr owned", "was this weslr owned"}:
        return "was_that_weslr_owned"
    if normalized in {"show last voice attribution", "show the last voice attribution"}:
        return "show_last_voice_attribution"
    return "unknown"


def _intent_from_phrase_family(phrase_family: str) -> str:
    if phrase_family == "was_that_weslr":
        return "was_that_weslr_owned"
    if phrase_family in ALLOWED_ATTRIBUTION_INTENTS:
        return phrase_family
    return "unknown"


def create_chat_routing_request_from_metadata(
    request_id: str,
    input_channel: str,
    message_text_hash: str,
    matched_phrase_family: str = "unknown",
    detected_attribution_intent: str = "unknown",
    confidence: str = "unknown",
    operator_review_required: bool = True,
    safety_flags: WhoSaidThatChatRoutingSafetyFlags | dict[str, Any] | None = None,
    **metadata: Any,
) -> WhoSaidThatChatRoutingRequest:
    """Build a validated chat routing request from explicit metadata only."""
    if "raw_text" in metadata or "message_text" in metadata or "raw_message_text" in metadata:
        raise ValueError("raw text metadata is not accepted")
    if detected_attribution_intent == "unknown" and matched_phrase_family != "unknown":
        detected_attribution_intent = _intent_from_phrase_family(matched_phrase_family)
    item = create_empty_who_said_that_chat_routing_request(
        request_id=request_id,
        input_channel=input_channel,
        raw_text_stored=False,
        message_text_hash=message_text_hash,
        detected_attribution_intent=detected_attribution_intent,
        matched_phrase_family=matched_phrase_family,
        confidence=confidence,
        operator_review_required=operator_review_required,
        safety_flags=_coerce_safety_flags(safety_flags),
    )
    errors = validate_who_said_that_chat_routing_request(item)
    if errors:
        raise ValueError(f"invalid who-said-that chat routing request: {errors}")
    return item


def create_chat_routing_decision_from_request(
    request: WhoSaidThatChatRoutingRequest | dict[str, Any],
    decision_id: str,
    runtime_query_request_id: str = "",
    safety_flags: WhoSaidThatChatRoutingSafetyFlags | dict[str, Any] | None = None,
) -> WhoSaidThatChatRoutingDecision:
    """Create a safe in-memory routing decision without performing routing."""
    request_obj = who_said_that_chat_routing_request_from_dict(request) if isinstance(request, dict) else request
    should_route = (
        request_obj.detected_attribution_intent != "unknown"
        and request_obj.matched_phrase_family != "unknown"
        and request_obj.confidence in {"medium", "high"}
    )
    item = create_empty_who_said_that_chat_routing_decision(
        decision_id=decision_id,
        request_id=request_obj.request_id,
        input_channel=request_obj.input_channel,
        detected_attribution_intent=request_obj.detected_attribution_intent,
        matched_phrase_family=request_obj.matched_phrase_family,
        confidence=request_obj.confidence,
        should_route=should_route,
        runtime_query_request_id=runtime_query_request_id if should_route else "",
        routing_performed=False,
        log_read_performed=False,
        log_write_performed=False,
        queue_write_performed=False,
        memory_mutation_performed=False,
        model_advisor_call_performed=False,
        answer_selection_performed=False,
        truth_soundness_score_claimed=False,
        operator_review_required=True,
        safety_flags=_coerce_safety_flags(safety_flags),
    )
    errors = validate_who_said_that_chat_routing_decision(item)
    if errors:
        raise ValueError(f"invalid who-said-that chat routing decision: {errors}")
    return item


def summarize_chat_routing_decision(item: WhoSaidThatChatRoutingDecision) -> dict[str, Any]:
    """Return a redacted/count-only summary for one chat routing decision."""
    errors = validate_who_said_that_chat_routing_decision(item)
    return {
        "schema_version": item.schema_version,
        "has_decision_id": bool(item.decision_id),
        "has_request_id": bool(item.request_id),
        "has_runtime_query_request_id": bool(item.runtime_query_request_id),
        "input_channel": item.input_channel,
        "detected_attribution_intent": item.detected_attribution_intent,
        "matched_phrase_family": item.matched_phrase_family,
        "confidence": item.confidence,
        "should_route": item.should_route,
        "operator_review_required": item.operator_review_required,
        "validation_error_count": len(errors),
        "routing_performed": item.routing_performed,
        "log_read_performed": item.log_read_performed,
        "log_write_performed": item.log_write_performed,
        "queue_write_performed": item.queue_write_performed,
        "memory_mutation_performed": item.memory_mutation_performed,
        "model_advisor_call_performed": item.model_advisor_call_performed,
        "answer_selection_performed": item.answer_selection_performed,
        "truth_soundness_score_claimed": item.truth_soundness_score_claimed,
        "safety_error_count": sum(1 for name in PROHIBITED_SAFETY_FLAG_FIELDS if getattr(item.safety_flags, name)),
        "summary_mode": "redacted_count_only",
    }


def summarize_chat_routing_decisions(items: list[WhoSaidThatChatRoutingDecision]) -> dict[str, Any]:
    """Return redacted aggregate counts for chat routing decisions."""
    by_intent: dict[str, int] = {}
    by_phrase_family: dict[str, int] = {}
    by_confidence: dict[str, int] = {}
    route_count = 0
    validation_error_count = 0
    operator_review_required_count = 0
    for item in items:
        by_intent[item.detected_attribution_intent] = by_intent.get(item.detected_attribution_intent, 0) + 1
        by_phrase_family[item.matched_phrase_family] = by_phrase_family.get(item.matched_phrase_family, 0) + 1
        by_confidence[item.confidence] = by_confidence.get(item.confidence, 0) + 1
        if item.should_route:
            route_count += 1
        if item.operator_review_required:
            operator_review_required_count += 1
        validation_error_count += len(validate_who_said_that_chat_routing_decision(item))
    return {
        "decision_count": len(items),
        "route_count": route_count,
        "no_route_count": len(items) - route_count,
        "operator_review_required_count": operator_review_required_count,
        "by_intent": by_intent,
        "by_phrase_family": by_phrase_family,
        "by_confidence": by_confidence,
        "validation_error_count": validation_error_count,
        "routing_performed": False,
        "log_reads_performed": False,
        "log_writes_performed": False,
        "queue_writes_performed": False,
        "memory_mutations_performed": False,
        "model_advisor_calls_performed": False,
        "answer_selection_performed": False,
        "truth_soundness_score_claimed": False,
        "summary_mode": "redacted_count_only",
    }


def create_chat_integration_fallthrough_result(
    integration_result_id: str,
    request_id: str,
    reason: str = "normal_chat_fallthrough",
) -> dict[str, Any]:
    """Create a safe fallthrough result without changing runtime chat."""
    return {
        "schema_version": "1.0",
        "integration_result_id": integration_result_id,
        "request_id": request_id,
        "integration_path": "normal_chat_fallthrough",
        "fallthrough_to_normal_chat": True,
        "who_said_that_path_selected": False,
        "reason": reason,
        "routing_performed": False,
        "runtime_integration_performed": False,
        "chat_responder_modified": False,
        "runtime_output_created": False,
        "log_read_performed": False,
        "log_write_performed": False,
        "queue_write_performed": False,
        "memory_mutation_performed": False,
        "config_mutation_performed": False,
        "model_call_performed": False,
        "advisor_call_performed": False,
        "voice_wiring_performed": False,
        "operator_review_required": True,
        "summary_mode": "redacted_count_only",
    }


def simulate_who_said_that_chat_integration_from_metadata(
    integration_result_id: str,
    request_id: str,
    input_channel: str,
    message_text_hash: str,
    confidence: str = "high",
    transient_phrase: str = "",
    matched_phrase_family: str = "unknown",
    detected_attribution_intent: str = "unknown",
    runtime_query_request_id: str = "",
    **metadata: Any,
) -> dict[str, Any]:
    """Simulate future chat integration in memory without runtime wiring.

    The transient phrase is only classified in memory and is never copied into
    the returned request, decision, or result dictionaries.
    """
    if "raw_text" in metadata or "message_text" in metadata or "raw_message_text" in metadata:
        raise ValueError("raw text metadata is not accepted")
    if transient_phrase and matched_phrase_family == "unknown":
        matched_phrase_family = classify_who_said_that_phrase_family(transient_phrase)
    request = create_chat_routing_request_from_metadata(
        request_id=request_id,
        input_channel=input_channel,
        message_text_hash=message_text_hash,
        matched_phrase_family=matched_phrase_family,
        detected_attribution_intent=detected_attribution_intent,
        confidence=confidence,
    )
    decision = create_chat_routing_decision_from_request(
        request,
        decision_id=f"{integration_result_id}:decision",
        runtime_query_request_id=runtime_query_request_id,
    )
    if not decision.should_route:
        result = create_chat_integration_fallthrough_result(integration_result_id, request.request_id)
    else:
        result = {
            "schema_version": "1.0",
            "integration_result_id": integration_result_id,
            "request_id": request.request_id,
            "integration_path": "who_said_that_path",
            "fallthrough_to_normal_chat": False,
            "who_said_that_path_selected": True,
            "detected_attribution_intent": decision.detected_attribution_intent,
            "matched_phrase_family": decision.matched_phrase_family,
            "confidence": decision.confidence,
            "should_route": True,
            "runtime_query_request_id": decision.runtime_query_request_id,
            "routing_performed": False,
            "runtime_integration_performed": False,
            "chat_responder_modified": False,
            "runtime_output_created": False,
            "log_read_performed": False,
            "log_write_performed": False,
            "queue_write_performed": False,
            "memory_mutation_performed": False,
            "config_mutation_performed": False,
            "model_call_performed": False,
            "advisor_call_performed": False,
            "voice_wiring_performed": False,
            "operator_review_required": True,
            "summary_mode": "redacted_count_only",
        }
    result["chat_routing_request"] = who_said_that_chat_routing_request_to_dict(request)
    result["chat_routing_decision"] = who_said_that_chat_routing_decision_to_dict(decision)
    return result


def summarize_chat_integration_result(item: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted/count-only summary for one integration simulation."""
    return {
        "schema_version": item.get("schema_version", "1.0"),
        "has_integration_result_id": bool(item.get("integration_result_id")),
        "has_request_id": bool(item.get("request_id")),
        "integration_path": item.get("integration_path", "unknown"),
        "fallthrough_to_normal_chat": bool(item.get("fallthrough_to_normal_chat", False)),
        "who_said_that_path_selected": bool(item.get("who_said_that_path_selected", False)),
        "has_runtime_query_request_id": bool(item.get("runtime_query_request_id")),
        "routing_performed": bool(item.get("routing_performed", False)),
        "runtime_integration_performed": bool(item.get("runtime_integration_performed", False)),
        "chat_responder_modified": bool(item.get("chat_responder_modified", False)),
        "runtime_output_created": bool(item.get("runtime_output_created", False)),
        "log_read_performed": bool(item.get("log_read_performed", False)),
        "log_write_performed": bool(item.get("log_write_performed", False)),
        "queue_write_performed": bool(item.get("queue_write_performed", False)),
        "memory_mutation_performed": bool(item.get("memory_mutation_performed", False)),
        "config_mutation_performed": bool(item.get("config_mutation_performed", False)),
        "model_call_performed": bool(item.get("model_call_performed", False)),
        "advisor_call_performed": bool(item.get("advisor_call_performed", False)),
        "voice_wiring_performed": bool(item.get("voice_wiring_performed", False)),
        "operator_review_required": bool(item.get("operator_review_required", True)),
        "summary_mode": "redacted_count_only",
    }


def summarize_chat_integration_results(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Return redacted aggregate counts for integration simulations."""
    route_count = sum(1 for item in items if item.get("who_said_that_path_selected"))
    fallthrough_count = sum(1 for item in items if item.get("fallthrough_to_normal_chat"))
    return {
        "result_count": len(items),
        "route_count": route_count,
        "fallthrough_count": fallthrough_count,
        "routing_performed": False,
        "runtime_integration_performed": False,
        "chat_responder_modified": False,
        "runtime_outputs_created": False,
        "log_reads_performed": False,
        "log_writes_performed": False,
        "queue_writes_performed": False,
        "memory_mutations_performed": False,
        "config_mutations_performed": False,
        "model_calls_performed": False,
        "advisor_calls_performed": False,
        "voice_wiring_performed": False,
        "summary_mode": "redacted_count_only",
    }
