"""WESLR Who Said That Read-Only Log Lookup Schema V1.

Schema dataclasses and validation helpers for a future read-only attribution
log lookup layer. This module does not implement log readers, read real logs,
write attribution logs, create .weslr/voice_source_attribution.jsonl, wire
runtime/chat/voice behavior, write queues, persist registries, call external
models/advisors, mutate memory/prompts/config, schedule daemons, select
answers, or claim truth/soundness/official scores.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import os
import re
import tempfile

from weslr.voice_source_attribution_log import (
    VoiceAttributionLogEvent,
    validate_voice_attribution_log_event,
    voice_attribution_log_event_from_dict,
    voice_attribution_log_event_to_dict,
)
from weslr.who_said_that_query_surface import (
    WhoSaidThatQueryIntent,
    create_missing_attribution_answer,
    resolve_who_said_that_from_provided_records,
)


ALLOWED_STORAGE_FORMATS = {"jsonl", "json", "unknown"}
ALLOWED_LOOKUP_MODES = {
    "most_recent",
    "by_utterance_id",
    "by_trace_ref",
    "by_time_window",
    "manual_review_only",
    "unknown",
}

SUMMARY_REDACTION = "[redacted]"

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

PROHIBITED_SAFETY_FLAG_FIELDS = {
    "log_write_attempted": "log write attempted",
    "log_creation_attempted": "log creation attempted",
    "queue_write_attempted": "queue write attempted",
    "registry_persistence_attempted": "registry persistence attempted",
    "runtime_chat_voice_wiring_attempted": "runtime/chat/voice wiring attempted",
    "memory_mutation_attempted": "memory mutation attempted",
    "external_model_call_attempted": "external model call attempted",
    "advisor_call_attempted": "advisor call attempted",
    "provenance_guessing_attempted": "provenance guessing attempted",
    "unsupported_self_ownership_claimed": "unsupported self-ownership claimed",
    "hidden_llm_authority": "hidden LLM authority",
    "hidden_model_provider_involvement": "hidden model/provider involvement",
    "self_improvement_activation_attempted": "self-improvement activation attempted",
    "answer_selection_attempted": "answer selection attempted",
    "truth_authority_claimed": "truth authority claimed",
    "soundness_authority_claimed": "soundness authority claimed",
    "official_score_claimed": "official score claimed",
    "raw_sensitive_content_disclosed": "raw sensitive content disclosed",
}


@dataclass
class WhoSaidThatLogLookupSafetyFlags:
    log_write_attempted: bool = False
    log_creation_attempted: bool = False
    queue_write_attempted: bool = False
    registry_persistence_attempted: bool = False
    runtime_chat_voice_wiring_attempted: bool = False
    memory_mutation_attempted: bool = False
    external_model_call_attempted: bool = False
    advisor_call_attempted: bool = False
    provenance_guessing_attempted: bool = False
    unsupported_self_ownership_claimed: bool = False
    hidden_llm_authority: bool = False
    hidden_model_provider_involvement: bool = False
    self_improvement_activation_attempted: bool = False
    answer_selection_attempted: bool = False
    truth_authority_claimed: bool = False
    soundness_authority_claimed: bool = False
    official_score_claimed: bool = False
    raw_sensitive_content_disclosed: bool = False


@dataclass
class WhoSaidThatLogLookupPathPolicy:
    schema_version: str = "1.0"
    log_path: str = ".weslr/voice_source_attribution.jsonl"
    storage_format: str = "jsonl"
    read_only_required: bool = True
    explicit_path_policy_required: bool = True
    redaction_required: bool = True
    raw_spoken_text_allowed: bool = False
    create_if_missing_allowed: bool = False
    writes_allowed: bool = False
    allow_absolute_paths: bool = False
    allow_path_traversal: bool = False
    allow_external_storage: bool = False
    operator_review_required: bool = True


@dataclass
class WhoSaidThatLogLookupRequest:
    schema_version: str = "1.0"
    request_id: str = ""
    query_id: str = ""
    lookup_mode: str = "most_recent"
    requested_utterance_id: str = ""
    requested_trace_ref: str = ""
    time_window_start: str = ""
    time_window_end: str = ""
    max_events: int = 20
    redacted_only: bool = True
    manual_review_only: bool = False
    operator_review_required: bool = True
    path_policy: WhoSaidThatLogLookupPathPolicy = field(default_factory=WhoSaidThatLogLookupPathPolicy)
    safety_flags: WhoSaidThatLogLookupSafetyFlags = field(default_factory=WhoSaidThatLogLookupSafetyFlags)


@dataclass
class WhoSaidThatLogLookupResult:
    schema_version: str = "1.0"
    result_id: str = ""
    request_id: str = ""
    lookup_mode: str = "unknown"
    log_exists: bool = False
    missing_log: bool = False
    records_found: int = 0
    selected_event_count: int = 0
    selected_event_snapshots: list[dict[str, Any]] = field(default_factory=list)
    redacted_event_summaries: list[str] = field(default_factory=list)
    attribution_missing: bool = False
    attribution_partial: bool = False
    ambiguous_matches: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    read_only: bool = True
    log_read_performed: bool = False
    log_write_performed: bool = False
    log_created: bool = False
    queue_write_performed: bool = False
    runtime_change_performed: bool = False
    external_model_call_performed: bool = False
    answer_selection_performed: bool = False
    truth_claim_made: bool = False
    official_score_claimed: bool = False
    safety_flags: WhoSaidThatLogLookupSafetyFlags = field(default_factory=WhoSaidThatLogLookupSafetyFlags)


def _apply_overrides(item: Any, overrides: dict[str, Any], label: str) -> Any:
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown {label} field: {key}")
        setattr(item, key, value)
    return item


def create_empty_who_said_that_log_lookup_path_policy(**overrides: Any) -> WhoSaidThatLogLookupPathPolicy:
    return _apply_overrides(WhoSaidThatLogLookupPathPolicy(), overrides, "who said that log lookup path policy")


def create_empty_who_said_that_log_lookup_request(request_id: str = "", **overrides: Any) -> WhoSaidThatLogLookupRequest:
    item = WhoSaidThatLogLookupRequest(request_id=request_id)
    return _apply_overrides(item, overrides, "who said that log lookup request")


def create_empty_who_said_that_log_lookup_result(result_id: str = "", request_id: str = "", **overrides: Any) -> WhoSaidThatLogLookupResult:
    item = WhoSaidThatLogLookupResult(result_id=result_id, request_id=request_id)
    return _apply_overrides(item, overrides, "who said that log lookup result")


def who_said_that_log_lookup_path_policy_to_dict(item: WhoSaidThatLogLookupPathPolicy) -> dict[str, Any]:
    return asdict(item)


def who_said_that_log_lookup_path_policy_from_dict(data: dict[str, Any]) -> WhoSaidThatLogLookupPathPolicy:
    return WhoSaidThatLogLookupPathPolicy(**dict(data))


def who_said_that_log_lookup_request_to_dict(item: WhoSaidThatLogLookupRequest) -> dict[str, Any]:
    return asdict(item)


def _coerce_path_policy(value: WhoSaidThatLogLookupPathPolicy | dict[str, Any] | None) -> WhoSaidThatLogLookupPathPolicy:
    if isinstance(value, WhoSaidThatLogLookupPathPolicy):
        return value
    if isinstance(value, dict):
        return who_said_that_log_lookup_path_policy_from_dict(value)
    return WhoSaidThatLogLookupPathPolicy()


def _coerce_safety_flags(value: WhoSaidThatLogLookupSafetyFlags | dict[str, Any] | None) -> WhoSaidThatLogLookupSafetyFlags:
    if isinstance(value, WhoSaidThatLogLookupSafetyFlags):
        return value
    if isinstance(value, dict):
        return WhoSaidThatLogLookupSafetyFlags(**value)
    return WhoSaidThatLogLookupSafetyFlags()


def who_said_that_log_lookup_request_from_dict(data: dict[str, Any]) -> WhoSaidThatLogLookupRequest:
    payload = dict(data)
    payload["path_policy"] = _coerce_path_policy(payload.get("path_policy"))
    payload["safety_flags"] = _coerce_safety_flags(payload.get("safety_flags"))
    return WhoSaidThatLogLookupRequest(**payload)


def who_said_that_log_lookup_result_to_dict(item: WhoSaidThatLogLookupResult) -> dict[str, Any]:
    return asdict(item)


def who_said_that_log_lookup_result_from_dict(data: dict[str, Any]) -> WhoSaidThatLogLookupResult:
    payload = dict(data)
    payload["safety_flags"] = _coerce_safety_flags(payload.get("safety_flags"))
    return WhoSaidThatLogLookupResult(**payload)


def _stringify(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, default=str)
    except TypeError:
        return str(value)


def _detect_sensitive_text(values: list[str]) -> list[str]:
    joined = "\n".join(values)
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


def _flag_errors(flags: WhoSaidThatLogLookupSafetyFlags) -> list[str]:
    errors: list[str] = []
    for field_name, label in PROHIBITED_SAFETY_FLAG_FIELDS.items():
        if getattr(flags, field_name):
            errors.append(label)
    return errors


def validate_who_said_that_log_lookup_path_policy(item: WhoSaidThatLogLookupPathPolicy) -> list[str]:
    errors: list[str] = []
    if item.storage_format not in ALLOWED_STORAGE_FORMATS:
        errors.append("invalid storage_format")
    if not item.read_only_required:
        errors.append("read_only_required disabled")
    if not item.explicit_path_policy_required:
        errors.append("explicit_path_policy_required disabled")
    if not item.redaction_required:
        errors.append("redaction_required disabled")
    if item.raw_spoken_text_allowed:
        errors.append("raw_spoken_text_allowed true")
    if item.create_if_missing_allowed:
        errors.append("create_if_missing_allowed true")
    if item.writes_allowed:
        errors.append("writes_allowed true")
    if item.allow_absolute_paths:
        errors.append("absolute paths allowed")
    if item.allow_path_traversal:
        errors.append("path traversal allowed")
    if item.allow_external_storage:
        errors.append("external storage allowed")
    if not item.operator_review_required:
        errors.append("operator_review_required disabled")
    for finding in _detect_sensitive_text([item.log_path]):
        errors.append(finding)
    return errors


def validate_who_said_that_log_lookup_request(item: WhoSaidThatLogLookupRequest) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_who_said_that_log_lookup_path_policy(item.path_policy))
    errors.extend(_flag_errors(item.safety_flags))
    if not item.request_id.strip():
        errors.append("missing request_id")
    if item.lookup_mode not in ALLOWED_LOOKUP_MODES:
        errors.append("invalid lookup_mode")
    if item.lookup_mode == "by_utterance_id" and not item.requested_utterance_id.strip():
        errors.append("by_utterance_id requires requested_utterance_id")
    if item.lookup_mode == "by_trace_ref" and not item.requested_trace_ref.strip():
        errors.append("by_trace_ref requires requested_trace_ref")
    if item.lookup_mode == "by_time_window" and (not item.time_window_start.strip() or not item.time_window_end.strip()):
        errors.append("by_time_window requires time_window_start and time_window_end")
    if item.max_events <= 0:
        errors.append("max_events must be positive")
    if not item.redacted_only:
        errors.append("redacted_only false")
    if not item.operator_review_required:
        errors.append("operator_review_required disabled")
    text_values = [
        item.request_id,
        item.query_id,
        item.requested_utterance_id,
        item.requested_trace_ref,
        item.time_window_start,
        item.time_window_end,
    ]
    for finding in _detect_sensitive_text(text_values):
        errors.append(finding)
    return errors


def _snapshot_sensitive_errors(snapshots: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for snapshot in snapshots:
        lowered_keys = {str(key).lower() for key in snapshot.keys()}
        if "raw_spoken_text" in lowered_keys or "spoken_text" in lowered_keys or "transcript" in lowered_keys:
            errors.append("selected event snapshot contains raw spoken text")
        for finding in _detect_sensitive_text([_stringify(snapshot)]):
            errors.append(f"selected event snapshot contains {finding}")
    return errors


def validate_who_said_that_log_lookup_result(item: WhoSaidThatLogLookupResult) -> list[str]:
    errors: list[str] = []
    errors.extend(_flag_errors(item.safety_flags))
    if not item.result_id.strip():
        errors.append("missing result_id")
    if not item.request_id.strip():
        errors.append("missing result request_id")
    if item.lookup_mode not in ALLOWED_LOOKUP_MODES:
        errors.append("invalid lookup_mode")
    if not item.read_only:
        errors.append("result not read-only")
    if item.log_write_performed:
        errors.append("log write performed")
    if item.log_created:
        errors.append("log created")
    if item.queue_write_performed:
        errors.append("queue write performed")
    if item.runtime_change_performed:
        errors.append("runtime change performed")
    if item.external_model_call_performed:
        errors.append("external model call performed")
    if item.answer_selection_performed:
        errors.append("answer selection performed")
    if item.truth_claim_made:
        errors.append("truth claim made")
    if item.official_score_claimed:
        errors.append("official score claimed")
    errors.extend(_snapshot_sensitive_errors(item.selected_event_snapshots))
    for finding in _detect_sensitive_text(item.redacted_event_summaries + item.errors + item.warnings):
        errors.append(f"redacted summary contains {finding}")
    return errors


def summarize_who_said_that_log_lookup_result(item: WhoSaidThatLogLookupResult) -> dict[str, Any]:
    validation_errors = validate_who_said_that_log_lookup_result(item)
    return {
        "schema_version": item.schema_version,
        "lookup_mode": item.lookup_mode,
        "log_exists": item.log_exists,
        "missing_log": item.missing_log,
        "records_found": item.records_found,
        "selected_event_count": item.selected_event_count,
        "redacted_event_summary_count": len(item.redacted_event_summaries),
        "attribution_missing": item.attribution_missing,
        "attribution_partial": item.attribution_partial,
        "ambiguous_matches": item.ambiguous_matches,
        "error_count": len(item.errors),
        "warning_count": len(item.warnings),
        "validation_error_count": len(validation_errors),
        "safe": not validation_errors,
        "read_only": item.read_only,
        "log_read_performed": item.log_read_performed,
        "log_write_performed": item.log_write_performed,
        "log_created": item.log_created,
        "queue_write_performed": item.queue_write_performed,
        "runtime_change_performed": item.runtime_change_performed,
        "external_model_call_performed": item.external_model_call_performed,
        "answer_selection_performed": item.answer_selection_performed,
        "truth_claim_made": item.truth_claim_made,
        "official_score_claimed": item.official_score_claimed,
        "safety_flag_error_count": len(_flag_errors(item.safety_flags)),
    }


def summarize_who_said_that_log_lookup_results(items: list[WhoSaidThatLogLookupResult]) -> dict[str, Any]:
    summaries = [summarize_who_said_that_log_lookup_result(item) for item in items]
    return {
        "result_count": len(items),
        "log_exists_count": sum(1 for item in items if item.log_exists),
        "missing_log_count": sum(1 for item in items if item.missing_log),
        "records_found_total": sum(item.records_found for item in items),
        "selected_event_count_total": sum(item.selected_event_count for item in items),
        "attribution_missing_count": sum(1 for item in items if item.attribution_missing),
        "attribution_partial_count": sum(1 for item in items if item.attribution_partial),
        "ambiguous_match_count": sum(1 for item in items if item.ambiguous_matches),
        "safe_count": sum(1 for summary in summaries if summary["safe"]),
        "unsafe_count": sum(1 for summary in summaries if not summary["safe"]),
        "log_read_performed_count": sum(1 for item in items if item.log_read_performed),
        "log_write_performed_count": sum(1 for item in items if item.log_write_performed),
        "log_created_count": sum(1 for item in items if item.log_created),
        "queue_write_performed_count": sum(1 for item in items if item.queue_write_performed),
        "runtime_change_performed_count": sum(1 for item in items if item.runtime_change_performed),
        "external_model_call_performed_count": sum(1 for item in items if item.external_model_call_performed),
        "answer_selection_performed_count": sum(1 for item in items if item.answer_selection_performed),
        "truth_claim_made_count": sum(1 for item in items if item.truth_claim_made),
        "official_score_claimed_count": sum(1 for item in items if item.official_score_claimed),
        "validation_error_count_total": sum(summary["validation_error_count"] for summary in summaries),
    }


# ---------------------------------------------------------------------------
# Read-only helper layer V1
# ---------------------------------------------------------------------------

def _stable_lookup_result_id(request_id: str, suffix: str = "result") -> str:
    safe_request_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", request_id.strip() or "unknown_request")
    return f"{safe_request_id}_{suffix}"


def _is_external_storage_path(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith(("s3://", "gs://", "http://", "https://", "ftp://", "file://"))


def _has_path_traversal(path: Path) -> bool:
    return any(part == ".." for part in path.parts)


def validate_who_said_that_lookup_path(
    path: str | os.PathLike[str],
    policy: WhoSaidThatLogLookupPathPolicy,
) -> list[str]:
    """Validate an explicit lookup path without creating or reading files."""
    errors = validate_who_said_that_log_lookup_path_policy(policy)
    raw_path = os.fspath(path)
    if not raw_path.strip():
        errors.append("missing explicit lookup path")
        return errors
    if _is_external_storage_path(raw_path) and not policy.allow_external_storage:
        errors.append("external storage path rejected")
    candidate = Path(raw_path)
    safe_temp_root = Path(tempfile.gettempdir()).resolve()
    is_safe_temp_path = False
    if candidate.is_absolute():
        try:
            is_safe_temp_path = candidate.resolve(strict=False).is_relative_to(safe_temp_root)
        except OSError:
            is_safe_temp_path = False
    if candidate.is_absolute() and not policy.allow_absolute_paths and not is_safe_temp_path:
        errors.append("absolute path rejected")
    if _has_path_traversal(candidate) and not policy.allow_path_traversal:
        errors.append("path traversal rejected")
    if policy.create_if_missing_allowed:
        errors.append("create_if_missing_allowed true")
    if policy.writes_allowed:
        errors.append("writes_allowed true")
    if not policy.read_only_required:
        errors.append("read_only_required disabled")
    if not policy.explicit_path_policy_required:
        errors.append("explicit_path_policy_required disabled")
    if not policy.redaction_required:
        errors.append("redaction_required disabled")
    return list(dict.fromkeys(errors))


def _safe_event_snapshot(event: VoiceAttributionLogEvent) -> dict[str, Any]:
    data = voice_attribution_log_event_to_dict(event)
    allowed_keys = [
        "schema_version",
        "event_id",
        "event_type",
        "utterance_id",
        "output_provenance_id",
        "source_subsystem",
        "spoken_text_hash",
        "spoken_text_stored",
        "speech_emitted",
        "speech_success",
        "tts_engine",
        "stt_engine",
        "model_provider",
        "model_name",
        "llm_assisted",
        "authority_level",
        "truth_class",
        "redacted_summary",
        "created_at",
        "trace_refs",
        "attribution_record_snapshot",
    ]
    snapshot = {key: data.get(key) for key in allowed_keys if key in data}
    if snapshot.get("spoken_text_stored") is True:
        snapshot["spoken_text_stored"] = False
        snapshot["redaction_note"] = "raw spoken text not included"
    snapshot.pop("raw_spoken_text", None)
    snapshot.pop("spoken_text", None)
    snapshot.pop("transcript", None)
    return snapshot


def _redacted_event_summary(event: VoiceAttributionLogEvent) -> str:
    parts = [
        f"event_type={event.event_type or 'unknown'}",
        f"utterance_id_present={bool(event.utterance_id)}",
        f"trace_ref_count={len(event.trace_refs)}",
        f"source_subsystem={event.source_subsystem or 'unknown'}",
    ]
    if event.redacted_summary:
        parts.append(f"summary={_redact_text(event.redacted_summary)}")
    return "; ".join(parts)


def _event_sort_key(event: VoiceAttributionLogEvent) -> tuple[str, str]:
    return (event.created_at or "", event.event_id or "")


def _within_time_window(event: VoiceAttributionLogEvent, start: str, end: str) -> bool:
    created = event.created_at or ""
    if not created:
        return False
    return start <= created <= end


def select_voice_attribution_log_events(
    events: list[VoiceAttributionLogEvent | dict[str, Any]],
    request: WhoSaidThatLogLookupRequest,
) -> list[VoiceAttributionLogEvent]:
    """Pure in-memory event selection. It performs no disk IO and no answer selection."""
    parsed: list[VoiceAttributionLogEvent] = []
    for event in events:
        try:
            candidate = event if isinstance(event, VoiceAttributionLogEvent) else voice_attribution_log_event_from_dict(event)
            if not validate_voice_attribution_log_event(candidate):
                parsed.append(candidate)
        except (TypeError, ValueError):
            continue
    limit = max(1, request.max_events)
    if request.lookup_mode == "by_utterance_id":
        selected = [event for event in parsed if event.utterance_id == request.requested_utterance_id]
    elif request.lookup_mode == "by_trace_ref":
        selected = [event for event in parsed if request.requested_trace_ref in event.trace_refs]
    elif request.lookup_mode == "by_time_window":
        selected = [event for event in parsed if _within_time_window(event, request.time_window_start, request.time_window_end)]
    elif request.lookup_mode == "manual_review_only" or request.manual_review_only:
        selected = []
    else:
        selected = sorted(parsed, key=_event_sort_key, reverse=True)[:limit]
    return selected[:limit]


def load_voice_attribution_log_events_read_only(
    path: str | os.PathLike[str],
    request: WhoSaidThatLogLookupRequest,
    policy: WhoSaidThatLogLookupPathPolicy | None = None,
) -> WhoSaidThatLogLookupResult:
    """Load JSONL voice attribution events from an explicit path only, read-only."""
    active_policy = policy or request.path_policy
    result = create_empty_who_said_that_log_lookup_result(
        result_id=_stable_lookup_result_id(request.request_id, "lookup"),
        request_id=request.request_id,
        lookup_mode=request.lookup_mode,
        read_only=True,
    )
    request_errors = validate_who_said_that_log_lookup_request(request)
    path_errors = validate_who_said_that_lookup_path(path, active_policy)
    if request_errors or path_errors:
        result.errors.extend(request_errors + path_errors)
        result.attribution_missing = True
        return result
    lookup_path = Path(os.fspath(path))
    if not lookup_path.exists():
        result.log_exists = False
        result.missing_log = True
        result.records_found = 0
        result.attribution_missing = True
        result.warnings.append("missing explicit attribution log")
        return result
    if not lookup_path.is_file():
        result.errors.append("explicit lookup path is not a file")
        result.attribution_missing = True
        return result

    events: list[VoiceAttributionLogEvent] = []
    result.log_exists = True
    result.log_read_performed = True
    with lookup_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                data = json.loads(stripped)
                event = voice_attribution_log_event_from_dict(data)
            except (json.JSONDecodeError, TypeError, ValueError):
                result.warnings.append(f"invalid jsonl line ignored: {line_number}")
                continue
            event_errors = validate_voice_attribution_log_event(event)
            if event_errors:
                result.warnings.append(f"invalid attribution event ignored: {line_number}")
                continue
            events.append(event)
    result.records_found = len(events)
    selected = select_voice_attribution_log_events(events, request)
    result.selected_event_snapshots = [_safe_event_snapshot(event) for event in selected]
    result.redacted_event_summaries = [_redacted_event_summary(event) for event in selected]
    result.selected_event_count = len(selected)
    result.attribution_missing = len(selected) == 0
    result.attribution_partial = bool(selected) and any(not event.trace_refs or event.source_subsystem == "unknown" for event in selected)
    result.ambiguous_matches = request.lookup_mode in {"by_utterance_id", "by_trace_ref", "by_time_window"} and len(selected) > 1
    return result


def _query_intent_from_request(request_or_intent: WhoSaidThatLogLookupRequest | WhoSaidThatQueryIntent | dict[str, Any]) -> WhoSaidThatQueryIntent:
    if isinstance(request_or_intent, WhoSaidThatQueryIntent):
        return request_or_intent
    if isinstance(request_or_intent, WhoSaidThatLogLookupRequest):
        return WhoSaidThatQueryIntent(
            query_id=request_or_intent.query_id or request_or_intent.request_id,
            intent_type="who_said_that",
            lookback_mode=request_or_intent.lookup_mode if request_or_intent.lookup_mode in {"most_recent", "by_utterance_id", "by_trace_ref", "unknown"} else "unknown",
            requested_utterance_id=request_or_intent.requested_utterance_id,
            operator_review_required=True,
        )
    data = dict(request_or_intent)
    if "request_id" in data and "query_id" not in data:
        data["query_id"] = data.get("request_id", "")
    return WhoSaidThatQueryIntent(
        query_id=str(data.get("query_id") or data.get("request_id") or "lookup_query"),
        intent_type=str(data.get("intent_type") or "who_said_that"),
        lookback_mode=str(data.get("lookback_mode") or data.get("lookup_mode") or "unknown"),
        requested_utterance_id=str(data.get("requested_utterance_id") or ""),
        operator_review_required=True,
    )


def resolve_who_said_that_from_lookup_result(
    request_or_intent: WhoSaidThatLogLookupRequest | WhoSaidThatQueryIntent | dict[str, Any],
    lookup_result: WhoSaidThatLogLookupResult,
):
    """Resolve from already-provided lookup snapshots only. No log IO and no guessing."""
    intent = _query_intent_from_request(request_or_intent)
    if lookup_result.missing_log or lookup_result.records_found == 0 or not lookup_result.selected_event_snapshots:
        return create_missing_attribution_answer(
            answer_id=f"answer_{intent.query_id or lookup_result.request_id or 'lookup'}",
            query_id=intent.query_id or lookup_result.request_id,
            intent_type="who_said_that",
            reason="missing attribution from read-only lookup result; no provenance guessed",
        )
    return resolve_who_said_that_from_provided_records(
        intent,
        attribution_records=[],
        log_events=lookup_result.selected_event_snapshots,
        requested_trace_ref="",
        answer_id=f"answer_{intent.query_id or lookup_result.request_id or 'lookup'}",
    )


def summarize_who_said_that_log_lookup_diagnostics(results: list[WhoSaidThatLogLookupResult]) -> dict[str, Any]:
    """Return redacted/count-only diagnostics for read-only lookup helper results."""
    safe_results = results or []
    return {
        "summary_mode": "redacted_count_only",
        "lookup_request_count": len(safe_results),
        "missing_log_count": sum(1 for item in safe_results if item.missing_log),
        "records_found_total": sum(item.records_found for item in safe_results),
        "selected_event_count_total": sum(item.selected_event_count for item in safe_results),
        "error_count_total": sum(len(item.errors) for item in safe_results),
        "warning_count_total": sum(len(item.warnings) for item in safe_results),
        "log_writes_performed": False,
        "log_created": False,
        "queue_writes_performed": False,
        "external_model_calls_performed": False,
        "runtime_changes_performed": False,
        "answer_selection": False,
        "truth_claim": False,
        "official_score": False,
    }
