"""WESLR Who Said That Query Surface Schema V1.

Schema-only dataclasses and validation helpers for future record-backed
"who said that?" query intents and attribution answers. This module does not
implement query parsing, read/write attribution logs, wire runtime/chat/voice
behavior, write queues, persist registries, call models/advisors, mutate
memory/prompts/config, schedule daemons, select answers, or claim
truth/soundness/official scores.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import re


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
ALLOWED_CHANNELS = {"chat", "voice", "terminal", "operator_cli", "daemon", "internal", "unknown"}
ALLOWED_LOOKBACK_MODES = {"most_recent", "by_utterance_id", "by_trace_ref", "unknown"}
ALLOWED_OWNERSHIP_CATEGORIES = {
    "weslr_owned",
    "weslr_surface_llm_assisted",
    "advisor_assisted",
    "external_model_surface",
    "operator_triggered",
    "unknown_unattributed",
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
    "unsupported_self_ownership_claimed": "unsupported self-ownership claimed",
    "hidden_llm_authority": "hidden LLM authority",
    "hidden_model_provider_involvement": "hidden model/provider involvement",
    "unattributed_output_treated_as_weslr_owned": "unattributed output treated as WESLR-owned",
    "raw_spoken_text_disclosed": "raw spoken text disclosed",
    "memory_mutation_attempted": "memory mutation attempted",
    "queue_write_attempted": "queue write attempted",
    "log_read_attempted": "log read attempted",
    "log_write_attempted": "log write attempted",
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
class WhoSaidThatQuerySafetyFlags:
    provenance_guessing_attempted: bool = False
    unsupported_self_ownership_claimed: bool = False
    hidden_llm_authority: bool = False
    hidden_model_provider_involvement: bool = False
    unattributed_output_treated_as_weslr_owned: bool = False
    raw_spoken_text_disclosed: bool = False
    memory_mutation_attempted: bool = False
    queue_write_attempted: bool = False
    log_read_attempted: bool = False
    log_write_attempted: bool = False
    runtime_voice_wiring_attempted: bool = False
    external_model_call_attempted: bool = False
    self_improvement_activation_attempted: bool = False
    answer_selection_attempted: bool = False
    truth_authority_claimed: bool = False
    soundness_authority_claimed: bool = False
    official_score_claimed: bool = False


@dataclass
class WhoSaidThatQueryIntent:
    schema_version: str = "1.0"
    query_id: str = ""
    intent_type: str = "unknown"
    raw_query_stored: bool = False
    query_text_hash: str = ""
    input_channel: str = "unknown"
    requested_utterance_id: str = ""
    lookback_mode: str = "most_recent"
    operator_review_required: bool = True
    created_at: str = ""
    safety_flags: WhoSaidThatQuerySafetyFlags = field(default_factory=WhoSaidThatQuerySafetyFlags)


@dataclass
class WhoSaidThatAnswer:
    schema_version: str = "1.0"
    answer_id: str = ""
    query_id: str = ""
    intent_type: str = "unknown"
    attribution_found: bool = False
    attribution_partial: bool = False
    ownership_category: str = "unknown_unattributed"
    source_subsystem: str = "unknown"
    source_module: str = ""
    generated_by: str = ""
    trigger: str = ""
    trigger_type: str = "unknown"
    speech_emitted: bool = False
    tts_engine: str = "unknown"
    stt_engine: str = "unknown"
    llm_assisted: bool = False
    advisor_assisted: bool = False
    ambient_loop_involved: bool = False
    proactive_suggestion_involved: bool = False
    model_provider: str = ""
    model_name: str = ""
    authority_level: str = "unknown"
    truth_class: str = "unknown"
    confidence: str = "unknown"
    trace_ref_count: int = 0
    operator_review_required: bool = True
    missing_attribution_reason: str = ""
    redacted_answer_summary: str = ""
    safety_flags: WhoSaidThatQuerySafetyFlags = field(default_factory=WhoSaidThatQuerySafetyFlags)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_empty_who_said_that_query_intent(query_id: str = "", **overrides: Any) -> WhoSaidThatQueryIntent:
    item = WhoSaidThatQueryIntent(query_id=query_id, created_at=_utc_now())
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown who-said-that query intent field: {key}")
        setattr(item, key, value)
    return item


def create_empty_who_said_that_answer(answer_id: str = "", query_id: str = "", **overrides: Any) -> WhoSaidThatAnswer:
    item = WhoSaidThatAnswer(answer_id=answer_id, query_id=query_id)
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown who-said-that answer field: {key}")
        setattr(item, key, value)
    return item


def who_said_that_query_intent_to_dict(item: WhoSaidThatQueryIntent) -> dict[str, Any]:
    return asdict(item)


def who_said_that_query_intent_from_dict(data: dict[str, Any]) -> WhoSaidThatQueryIntent:
    payload = dict(data)
    flags = payload.get("safety_flags")
    if isinstance(flags, WhoSaidThatQuerySafetyFlags):
        payload["safety_flags"] = flags
    elif isinstance(flags, dict):
        payload["safety_flags"] = WhoSaidThatQuerySafetyFlags(**flags)
    elif flags is None:
        payload["safety_flags"] = WhoSaidThatQuerySafetyFlags()
    return WhoSaidThatQueryIntent(**payload)


def who_said_that_answer_to_dict(item: WhoSaidThatAnswer) -> dict[str, Any]:
    return asdict(item)


def who_said_that_answer_from_dict(data: dict[str, Any]) -> WhoSaidThatAnswer:
    payload = dict(data)
    flags = payload.get("safety_flags")
    if isinstance(flags, WhoSaidThatQuerySafetyFlags):
        payload["safety_flags"] = flags
    elif isinstance(flags, dict):
        payload["safety_flags"] = WhoSaidThatQuerySafetyFlags(**flags)
    elif flags is None:
        payload["safety_flags"] = WhoSaidThatQuerySafetyFlags()
    return WhoSaidThatAnswer(**payload)


def _detect_sensitive_text(values: list[str]) -> list[str]:
    joined = "\n".join(v for v in values if isinstance(v, str))
    findings: list[str] = []
    for label, pattern in SENSITIVE_TEXT_PATTERNS.items():
        if pattern.search(joined):
            findings.append(label)
    return findings


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in SENSITIVE_TEXT_PATTERNS.values():
        redacted = pattern.sub(SUMMARY_REDACTION, redacted)
    return redacted


def _flag_errors(flags: WhoSaidThatQuerySafetyFlags) -> list[str]:
    errors: list[str] = []
    for field_name, label in PROHIBITED_SAFETY_FLAG_FIELDS.items():
        if getattr(flags, field_name):
            errors.append(label)
    return errors


def validate_who_said_that_query_intent(item: WhoSaidThatQueryIntent) -> list[str]:
    errors: list[str] = []
    if not item.query_id.strip():
        errors.append("missing query_id")
    if item.intent_type not in ALLOWED_INTENT_TYPES:
        errors.append("invalid intent_type")
    if item.input_channel not in ALLOWED_CHANNELS:
        errors.append("invalid input_channel")
    if item.lookback_mode not in ALLOWED_LOOKBACK_MODES:
        errors.append("invalid lookback_mode")
    if item.raw_query_stored:
        errors.append("raw_query_stored true")
    if item.raw_query_stored and not item.query_text_hash.strip():
        errors.append("raw_query_stored requires query_text_hash")
    if not item.operator_review_required:
        errors.append("operator_review_required disabled")
    if item.lookback_mode == "by_utterance_id" and not item.requested_utterance_id.strip():
        errors.append("by_utterance_id requires requested_utterance_id")
    errors.extend(_flag_errors(item.safety_flags))
    for finding in _detect_sensitive_text([item.query_id, item.query_text_hash, item.requested_utterance_id]):
        errors.append(finding)
    return errors


def validate_who_said_that_answer(item: WhoSaidThatAnswer) -> list[str]:
    errors: list[str] = []
    if not item.answer_id.strip():
        errors.append("missing answer_id")
    if not item.query_id.strip():
        errors.append("missing query_id")
    if item.intent_type not in ALLOWED_INTENT_TYPES:
        errors.append("invalid intent_type")
    if item.ownership_category not in ALLOWED_OWNERSHIP_CATEGORIES:
        errors.append("invalid ownership_category")
    if item.source_subsystem not in ALLOWED_SOURCE_SUBSYSTEMS:
        errors.append("invalid source_subsystem")
    if item.trigger_type not in ALLOWED_TRIGGER_TYPES:
        errors.append("invalid trigger_type")
    if item.authority_level not in ALLOWED_AUTHORITY_LEVELS:
        errors.append("invalid authority_level")
    if item.truth_class not in ALLOWED_TRUTH_CLASSES:
        errors.append("invalid truth_class")
    if item.confidence not in ALLOWED_CONFIDENCE_VALUES:
        errors.append("invalid confidence")
    if not item.attribution_found and item.ownership_category != "unknown_unattributed":
        errors.append("attribution missing requires unknown_unattributed ownership")
    if not item.attribution_found and any([item.source_module.strip(), item.generated_by.strip(), item.model_provider.strip(), item.model_name.strip()]):
        errors.append("attribution missing cannot claim source/generated_by/model/provider as fact")
    if item.ownership_category == "weslr_owned" and (not item.attribution_found or item.trace_ref_count <= 0):
        errors.append("weslr_owned requires attribution_found and trace refs")
    if item.llm_assisted and not item.model_provider.strip():
        errors.append("llm_assisted requires model_provider")
    if item.llm_assisted and not item.model_name.strip():
        errors.append("llm_assisted requires model_name")
    if item.advisor_assisted and (item.ownership_category not in {"advisor_assisted", "weslr_surface_llm_assisted"} or not item.operator_review_required):
        errors.append("advisor_assisted requires safe ownership category and review posture")
    if item.llm_assisted and item.authority_level == "system_fact" and item.trace_ref_count <= 0:
        errors.append("system_fact authority requires trace refs for LLM-assisted answer")
    if item.llm_assisted and item.truth_class == "verified_system_fact" and item.trace_ref_count <= 0:
        errors.append("verified_system_fact truth requires trace refs for LLM-assisted answer")
    errors.extend(_flag_errors(item.safety_flags))
    for finding in _detect_sensitive_text([
        item.answer_id, item.query_id, item.source_module, item.generated_by, item.trigger,
        item.tts_engine, item.stt_engine, item.model_provider, item.model_name,
        item.missing_attribution_reason, item.redacted_answer_summary,
    ]):
        errors.append(finding)
    return errors


def summarize_who_said_that_answer(item: WhoSaidThatAnswer) -> dict[str, Any]:
    validation_errors = validate_who_said_that_answer(item)
    return {
        "schema_version": item.schema_version,
        "answer_id": _redact_text(item.answer_id),
        "query_id": _redact_text(item.query_id),
        "intent_type": item.intent_type,
        "attribution_found": item.attribution_found,
        "attribution_partial": item.attribution_partial,
        "ownership_category": item.ownership_category,
        "source_subsystem": item.source_subsystem,
        "speech_emitted": item.speech_emitted,
        "llm_assisted": item.llm_assisted,
        "advisor_assisted": item.advisor_assisted,
        "ambient_loop_involved": item.ambient_loop_involved,
        "proactive_suggestion_involved": item.proactive_suggestion_involved,
        "model_provider_present": bool(item.model_provider),
        "model_name_present": bool(item.model_name),
        "authority_level": item.authority_level,
        "truth_class": item.truth_class,
        "confidence": item.confidence,
        "trace_ref_count": item.trace_ref_count,
        "operator_review_required": item.operator_review_required,
        "safety_error_count": sum(1 for name in PROHIBITED_SAFETY_FLAG_FIELDS if getattr(item.safety_flags, name)),
        "validation_error_count": len(validation_errors),
        "contains_redactions": bool(_detect_sensitive_text([item.answer_id, item.query_id, item.source_module, item.generated_by, item.trigger, item.model_provider, item.model_name, item.missing_attribution_reason, item.redacted_answer_summary])),
        "summary_mode": "redacted_count_only",
    }


def summarize_who_said_that_answers(items: list[WhoSaidThatAnswer]) -> dict[str, Any]:
    by_intent_type: dict[str, int] = {}
    by_ownership_category: dict[str, int] = {}
    validation_error_count = 0
    redaction_count = 0
    attribution_found_count = 0
    attribution_missing_count = 0
    llm_assisted_count = 0
    advisor_assisted_count = 0
    for item in items:
        by_intent_type[item.intent_type] = by_intent_type.get(item.intent_type, 0) + 1
        by_ownership_category[item.ownership_category] = by_ownership_category.get(item.ownership_category, 0) + 1
        validation_error_count += len(validate_who_said_that_answer(item))
        if summarize_who_said_that_answer(item)["contains_redactions"]:
            redaction_count += 1
        if item.attribution_found:
            attribution_found_count += 1
        else:
            attribution_missing_count += 1
        if item.llm_assisted:
            llm_assisted_count += 1
        if item.advisor_assisted:
            advisor_assisted_count += 1
    return {
        "item_count": len(items),
        "by_intent_type": by_intent_type,
        "by_ownership_category": by_ownership_category,
        "attribution_found_count": attribution_found_count,
        "attribution_missing_count": attribution_missing_count,
        "llm_assisted_count": llm_assisted_count,
        "advisor_assisted_count": advisor_assisted_count,
        "validation_error_count": validation_error_count,
        "redaction_count": redaction_count,
        "log_reads_performed": False,
        "log_writes_performed": False,
        "queue_writes_performed": False,
        "external_model_calls_performed": False,
        "runtime_changes_performed": False,
        "answer_selection": False,
        "truth_claim": False,
        "official_score": False,
        "summary_mode": "redacted_count_only",
    }
