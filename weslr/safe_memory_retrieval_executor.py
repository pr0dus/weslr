"""Pure safe memory retrieval executor v1.

This module only executes against supplied in-memory fake/source-provider data.
It does not read real memory, logs, `.weslr`, files, conversation history, or
call models/providers/search/advisors. It is deterministic, import-safe, and
fail-closed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
import hashlib
from typing import Any, Iterable, Mapping, Sequence

from weslr.memory_source_scope_registry import (
    MemorySourceScopeResolution,
    validate_memory_source_scope_resolution_v1,
)
from weslr.temporal_memory_retrieval_plan import (
    TemporalMemoryRetrievalPlan,
    validate_temporal_memory_retrieval_plan_v1,
)

HELPER_TYPE_V1 = "safe_memory_retrieval_executor_v1"
SAFE_MEMORY_RETRIEVAL_REQUEST_TYPE_V1 = "safe_memory_retrieval_request_v1"
SAFE_MEMORY_RETRIEVAL_RESULT_TYPE_V1 = "safe_memory_retrieval_result_v1"
SAFE_MEMORY_SOURCE_RESULT_TYPE_V1 = "safe_memory_source_result_v1"
SUMMARY_TYPE_V1 = "safe_memory_retrieval_result_summary_v1"

ALLOWED_RETRIEVAL_MODES_V1 = {
    "temporal_first",
    "semantic_first",
    "hybrid_temporal_semantic",
    "event_anchor_retrieval",
    "session_order_retrieval",
    "clarification_required",
    "blocked_no_authority",
    "blocked_no_source",
}

ALLOWED_SAFE_RESULT_FORMATS_V1 = {
    "metadata_summary",
    "redacted_summary",
    "owner_visible_excerpt",
    "source_reference_only",
    "blocked_authority_required",
    "clarification_needed",
}

ALLOWED_SOURCE_CLASSES_V1 = {
    "current_conversation",
    "prior_conversation_summary",
    "project_memory",
    "repo_commit_metadata",
    "lane_report_metadata",
    "uploaded_file_reference",
    "approved_memory_index",
    "runtime_session_log",
    ".weslr_state",
    "unknown_source",
    "artifact_manifest_metadata",
    "artifact_validation_report",
    "behavior_pack_registry",
    "friction_case_registry",
    "owner_approved_summary",
    "external_connector_reference",
}

FORBIDDEN_FIELD_NAMES_V1 = {
    "raw_prompt",
    "raw_answer",
    "raw_response",
    "raw_transcript",
    "transcript",
    "transcript_text",
    "answer_text",
    "response_text",
    "prompt_text",
    "raw_context",
    "raw_data",
    "raw_prompt_text",
    "raw_answer_text",
    "raw_response_text",
    "final_answer_text",
    "final_answer_prose",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "hidden_prompt",
    "private_data",
    "raw_private_data",
    "private_log",
    "log_dump",
    "trace_dump",
}

FORBIDDEN_PHRASES_V1 = (
    "public iss",
    "iss wording",
    "public intelligence claim",
    "public readiness claim",
    "agi claim",
    "consciousness claim",
    "sentience claim",
    "turing claim",
    "official turing",
    "turing test",
    "certification claim",
)

FORBIDDEN_MARKER_TERMS_V1 = (
    "agi",
    "consciousness",
    "sentience",
    "turing",
    "certification",
)

DEFAULT_RESULT_CONSTRAINTS_V1 = (
    "source-scoped",
    "time-scoped",
    "authority-scoped",
    "privacy-scoped",
    "project/session-scoped",
    "confidence-scored",
    "redacted by default",
)

DEFAULT_FAILURE_MODES_V1 = (
    "source_provider_missing",
    "authority_missing",
    "no_safe_source_available",
    "blocked_source_class",
    "unsafe_source_filtered",
    "time_filter_excluded_item",
    "semantic_filter_excluded_item",
)

DEFAULT_MAX_RESULT_COUNT_V1 = 3
DEFAULT_MAX_EXCERPT_LENGTH_V1 = 120


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SafeMemoryRetrievalRequest:
    retrieval_request_id: str
    retrieval_plan_id: str
    source_resolution_id: str
    allowed_sources: tuple[str, ...]
    blocked_sources: tuple[str, ...]
    requires_authority_sources: tuple[str, ...]
    selected_source_priority: tuple[str, ...]
    resolved_start: str | None
    resolved_end: str | None
    timezone: str
    retrieval_mode: str
    semantic_query_present: bool
    semantic_query_summary: str
    authority_packet_id: str
    authority_level: str
    memory_read_authority_granted: bool
    source_access_granted: bool
    raw_log_access_allowed: bool
    private_data_access_allowed: bool
    redaction_required: bool
    safe_result_format: str
    max_result_count: int
    max_excerpt_length: int
    allow_raw_transcript: bool
    allow_hidden_prompt: bool
    allow_cross_user: bool
    allow_cross_project: bool
    result_constraints: tuple[str, ...]
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class SafeMemorySourceResultItem:
    source_class: str
    source_id: str
    source_label: str
    source_timestamp: str | None
    source_time_window: str
    match_reason: str
    rank_hint: int
    confidence: float
    safe_summary: str
    safe_excerpt: str
    raw_content_omitted: bool
    redactions: tuple[str, ...]
    source_reference: str
    authority_used: str
    private_data_possible: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class SafeMemoryRetrievalResult:
    retrieval_result_id: str
    retrieval_request_id: str
    retrieval_executed: bool
    blocked: bool
    blocked_reason: str
    source_results: tuple[SafeMemorySourceResultItem, ...]
    result_count: int
    partial_result: bool
    expected_confidence: str
    actual_confidence: str
    source_classes_used: tuple[str, ...]
    source_classes_blocked: tuple[str, ...]
    time_window_used: str
    semantic_filter_used: str
    redaction_applied: bool
    raw_content_included: bool
    private_data_included: bool
    hidden_prompt_included: bool
    cross_user_content_included: bool
    cross_project_content_included: bool
    answer_safe_summary: str
    result_constraints: tuple[str, ...]
    failure_modes: tuple[str, ...]
    recommended_next_step: str
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    learning_claimed: bool
    memory_read_authority_granted: bool = False
    source_access_granted: bool = False
    raw_log_access_allowed: bool = False
    private_data_access_allowed: bool = False
    allow_raw_transcript: bool = False
    allow_hidden_prompt: bool = False
    allow_cross_user: bool = False
    allow_cross_project: bool = False
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class SafeMemoryRetrievalResultSummary:
    summary_type: str
    retrieval_result_id: str
    retrieval_request_id: str
    retrieval_executed: bool
    blocked: bool
    result_count: int
    expected_confidence: str
    actual_confidence: str
    source_classes_used: tuple[str, ...]
    source_classes_blocked: tuple[str, ...]
    safe_metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Safe helpers
# ---------------------------------------------------------------------------


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    return default if value == "" else str(value).strip()



def _normalize_text(value: Any) -> str:
    return " ".join(_safe_text(value).split()).lower()



def _dedupe_preserve(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        text = _normalize_text(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out



def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=_safe_text)]
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _safe_text(value)



def _flatten_texts(value: Any) -> list[str]:
    texts: list[str] = []
    if value is None:
        return texts
    if is_dataclass(value):
        return _flatten_texts(asdict(value))
    if isinstance(value, Mapping):
        for key, item in value.items():
            texts.extend(_flatten_texts(key))
            texts.extend(_flatten_texts(item))
        return texts
    if isinstance(value, (list, tuple, set)):
        for item in value:
            texts.extend(_flatten_texts(item))
        return texts
    if isinstance(value, bytes):
        texts.append(value.decode("utf-8", errors="replace"))
        return texts
    if isinstance(value, (str, int, float, bool)):
        texts.append(_safe_text(value))
        return texts
    texts.append(_safe_text(value))
    return texts



def _contains_forbidden_fields(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _normalize_text(key) in FORBIDDEN_FIELD_NAMES_V1:
                return True
            if _contains_forbidden_fields(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_fields(item) for item in value)
    return False



def _contains_forbidden_claim_marker(value: Any) -> bool:
    for text in _flatten_texts(value):
        lower = _normalize_text(text)
        if not lower:
            continue
        if any(phrase in lower for phrase in FORBIDDEN_PHRASES_V1):
            return True
        if any(term in lower for term in FORBIDDEN_MARKER_TERMS_V1):
            if any(token in lower for token in ("claim", "claims", "official", "public", "certification", "certified", "turing", "test")):
                return True
    return False



def _maybe_mapping(value: Any) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value
    if is_dataclass(value):
        return asdict(value)
    return None



def _deterministic_id(*parts: Any) -> str:
    payload = "|".join(_normalize_text(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"smre_{digest}"



def _clip_excerpt(text: Any, limit: int) -> str:
    excerpt = _safe_text(text)
    if not excerpt:
        return ""
    excerpt = " ".join(excerpt.split())
    if len(excerpt) <= limit:
        return excerpt
    return excerpt[: max(0, limit - 3)].rstrip() + "..."



def _parse_timestamp(value: Any) -> datetime | None:
    text = _safe_text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None



def _is_unsafe_source_class(source_class: str) -> bool:
    return _normalize_text(source_class) in {"runtime_session_log", ".weslr_state", "unknown_source"}



def _safe_bool(value: Any) -> bool:
    return bool(value) is True



def _authority_packet_mapping(authority_packet: Any) -> Mapping[str, Any] | None:
    mapping = _maybe_mapping(authority_packet)
    if mapping is None:
        return None
    return mapping



def _resolution_mapping(source_resolution: Any) -> Mapping[str, Any]:
    mapping = _maybe_mapping(source_resolution)
    if mapping is None:
        raise ValidationError("unsupported_source_resolution_type")
    return mapping



def _plan_mapping(retrieval_plan: Any) -> Mapping[str, Any]:
    mapping = _maybe_mapping(retrieval_plan)
    if mapping is None:
        raise ValidationError("unsupported_retrieval_plan_type")
    return mapping



def _source_items_from_provider(source_provider: Any) -> list[Mapping[str, Any]] | None:
    if source_provider is None:
        return None
    if isinstance(source_provider, Mapping):
        items = source_provider.get("source_items")
    else:
        items = getattr(source_provider, "source_items", None)
    if items is None:
        return []
    if isinstance(items, list):
        return [item if isinstance(item, Mapping) else _maybe_mapping(item) or {"value": item} for item in items]
    if isinstance(items, tuple):
        return [item if isinstance(item, Mapping) else _maybe_mapping(item) or {"value": item} for item in items]
    return []



def _normalize_source_list(source_list: Any) -> tuple[str, ...]:
    if source_list is None:
        return tuple()
    if isinstance(source_list, (str, bytes)):
        source_list = [source_list]
    values: list[str] = []
    for item in source_list:
        text = _normalize_text(item)
        if not text:
            continue
        if text not in ALLOWED_SOURCE_CLASSES_V1:
            text = "unknown_source"
        values.append(text)
    return tuple(_dedupe_preserve(values))



def _safe_result_constraints(result_constraints: Any) -> tuple[str, ...]:
    if result_constraints is None:
        return DEFAULT_RESULT_CONSTRAINTS_V1
    if isinstance(result_constraints, (str, bytes)):
        result_constraints = [result_constraints]
    return tuple(_dedupe_preserve(result_constraints)) or DEFAULT_RESULT_CONSTRAINTS_V1



def _safe_time_window(resolved_start: Any, resolved_end: Any) -> str:
    start = _safe_text(resolved_start)
    end = _safe_text(resolved_end)
    if start and end:
        return f"{start}..{end}"
    if start:
        return f"{start}.."
    if end:
        return f"..{end}"
    return "unresolved"



def _semantic_match(item: Mapping[str, Any], semantic_summary: str) -> bool:
    if not semantic_summary:
        return True
    query = _normalize_text(semantic_summary)
    if not query:
        return True
    haystacks = [
        _normalize_text(item.get("safe_summary")),
        _normalize_text(item.get("safe_excerpt")),
        _normalize_text(item.get("source_label")),
        _normalize_text(" ".join(_safe_text(tag) for tag in (item.get("semantic_tags") or ()))),
    ]
    tokens = [token for token in query.split() if len(token) >= 2]
    if not tokens:
        return True
    return any(any(token in hay for hay in haystacks) for token in tokens)



def _time_match(item: Mapping[str, Any], resolved_start: str | None, resolved_end: str | None) -> bool:
    ts = _parse_timestamp(item.get("timestamp") or item.get("source_timestamp"))
    if ts is None:
        return True
    start = _parse_timestamp(resolved_start)
    end = _parse_timestamp(resolved_end)
    if start and ts < start:
        return False
    if end and ts > end:
        return False
    return True



def _source_item_is_safe(item: Mapping[str, Any], request: SafeMemoryRetrievalRequest) -> tuple[bool, list[str]]:
    redactions: list[str] = []
    source_class = _normalize_text(item.get("source_class"))
    if not source_class:
        return False, ["missing_source_class"]
    if source_class not in request.allowed_sources:
        redactions.append("source_class_blocked")
        return False, redactions
    if _is_unsafe_source_class(source_class):
        redactions.append("unsafe_source_class")
        return False, redactions
    if not _time_match(item, request.resolved_start, request.resolved_end):
        redactions.append("time_window_excluded")
        return False, redactions
    if not _semantic_match(item, request.semantic_query_summary):
        redactions.append("semantic_filter_excluded")
        return False, redactions
    if _safe_bool(item.get("hidden_prompt")):
        redactions.append("hidden_prompt")
        return False, redactions
    if _safe_bool(item.get("cross_user")) or not request.allow_cross_user and _safe_text(item.get("session_scope")) not in {"", "same_session", "current_session", "owner", "self", "same_user"}:
        redactions.append("cross_user")
        return False, redactions
    if _safe_bool(item.get("cross_project")) or not request.allow_cross_project and _safe_text(item.get("project_scope")) not in {"", "same_project", "current_project", "owner", "self"}:
        redactions.append("cross_project")
        return False, redactions
    if _safe_bool(item.get("private_data_possible")):
        redactions.append("private_data")
        return False, redactions
    if _safe_text(item.get("raw_content")):
        redactions.append("raw_content")
        return False, redactions
    if _safe_text(item.get("private_data")):
        redactions.append("private_data")
        return False, redactions
    return True, redactions



def _request_safe_metadata(retrieval_plan: Any, source_resolution: Any, authority_packet: Any) -> dict[str, Any]:
    plan_map = _plan_mapping(retrieval_plan)
    resolution_map = _resolution_mapping(source_resolution)
    authority_map = _authority_packet_mapping(authority_packet) or {}
    return {
        "plan_type": _safe_text(plan_map.get("plan_type")),
        "source_resolution_type": _safe_text(resolution_map.get("resolution_type")),
        "authority_present": authority_packet is not None,
        "authority_level": _safe_text(authority_map.get("authority_level")) or "no_authority",
    }



def _build_request_id(plan_id: str, resolution_id: str, authority_id: str) -> str:
    return _deterministic_id("request", plan_id, resolution_id, authority_id)



def _build_result_id(request_id: str, blocked: bool, result_count: int, source_classes_used: Sequence[str]) -> str:
    return _deterministic_id("result", request_id, blocked, result_count, tuple(source_classes_used))



def _request_from_inputs(retrieval_plan: Any, source_resolution: Any, authority_packet: Any = None) -> SafeMemoryRetrievalRequest:
    validate_temporal_memory_retrieval_plan_v1(retrieval_plan)
    validate_memory_source_scope_resolution_v1(source_resolution)

    plan_map = _plan_mapping(retrieval_plan)
    resolution_map = _resolution_mapping(source_resolution)
    authority_map = _authority_packet_mapping(authority_packet) or {}

    retrieval_plan_id = _safe_text(plan_map.get("retrieval_plan_id"))
    source_resolution_id = _safe_text(resolution_map.get("source_resolution_id"))
    authority_packet_id = _safe_text(authority_map.get("authority_packet_id")) or (
        _deterministic_id("authority", retrieval_plan_id, source_resolution_id) if authority_packet is not None else "authority_none"
    )
    memory_read_authority_granted = _safe_bool(authority_map.get("memory_read_authority_granted"))
    source_access_granted = _safe_bool(authority_map.get("source_access_granted"))
    raw_log_access_allowed = _safe_bool(authority_map.get("raw_log_access_allowed"))
    private_data_access_allowed = _safe_bool(authority_map.get("private_data_access_allowed"))
    allow_hidden_prompt = _safe_bool(authority_map.get("allow_hidden_prompt"))
    allow_cross_user = _safe_bool(authority_map.get("allow_cross_user"))
    allow_cross_project = _safe_bool(authority_map.get("allow_cross_project"))

    result_constraints = _safe_result_constraints(resolution_map.get("result_constraints") or plan_map.get("result_constraints"))
    safe_result_format = _safe_text(resolution_map.get("safe_result_format")) or "metadata_summary"
    if safe_result_format not in ALLOWED_SAFE_RESULT_FORMATS_V1:
        safe_result_format = "metadata_summary"

    plan_safe_metadata = plan_map.get("safe_metadata")
    if not isinstance(plan_safe_metadata, Mapping):
        plan_safe_metadata = {}
    max_result_count = int(_safe_text(plan_safe_metadata.get("max_result_count")) or DEFAULT_MAX_RESULT_COUNT_V1)
    max_excerpt_length = int(_safe_text(plan_safe_metadata.get("max_excerpt_length")) or DEFAULT_MAX_EXCERPT_LENGTH_V1)
    if max_result_count <= 0:
        max_result_count = DEFAULT_MAX_RESULT_COUNT_V1
    if max_excerpt_length <= 0:
        max_excerpt_length = DEFAULT_MAX_EXCERPT_LENGTH_V1

    retrieval_mode = _safe_text(plan_map.get("retrieval_mode")) or "blocked_no_source"
    if retrieval_mode not in ALLOWED_RETRIEVAL_MODES_V1:
        retrieval_mode = "blocked_no_source"

    request = SafeMemoryRetrievalRequest(
        retrieval_request_id=_build_request_id(retrieval_plan_id, source_resolution_id, authority_packet_id),
        retrieval_plan_id=retrieval_plan_id,
        source_resolution_id=source_resolution_id,
        allowed_sources=tuple(_normalize_source_list(resolution_map.get("allowed_sources"))),
        blocked_sources=tuple(_normalize_source_list(resolution_map.get("blocked_sources"))),
        requires_authority_sources=tuple(_normalize_source_list(resolution_map.get("requires_authority_sources"))),
        selected_source_priority=tuple(_normalize_source_list(resolution_map.get("selected_source_priority"))),
        resolved_start=_safe_text(plan_map.get("resolved_start")) or None,
        resolved_end=_safe_text(plan_map.get("resolved_end")) or None,
        timezone=_safe_text(plan_map.get("timezone")) or "UTC",
        retrieval_mode=retrieval_mode,
        semantic_query_present=_safe_bool(plan_map.get("semantic_query_present")),
        semantic_query_summary=_safe_text(plan_map.get("semantic_query_summary")),
        authority_packet_id=authority_packet_id,
        authority_level=_safe_text(authority_map.get("authority_level")) or "no_authority",
        memory_read_authority_granted=memory_read_authority_granted,
        source_access_granted=source_access_granted,
        raw_log_access_allowed=raw_log_access_allowed,
        private_data_access_allowed=private_data_access_allowed,
        redaction_required=bool(resolution_map.get("redaction_required", True)),
        safe_result_format=safe_result_format,
        max_result_count=max_result_count,
        max_excerpt_length=max_excerpt_length,
        allow_raw_transcript=False,
        allow_hidden_prompt=allow_hidden_prompt,
        allow_cross_user=allow_cross_user,
        allow_cross_project=allow_cross_project,
        result_constraints=result_constraints,
        runtime_authority=_safe_bool(resolution_map.get("runtime_authority")),
        writes_state=_safe_bool(resolution_map.get("writes_state")),
        model_provider_used=_safe_bool(resolution_map.get("model_provider_used")),
        public_claim_allowed=_safe_bool(resolution_map.get("public_claim_allowed")),
        learning_claimed=_safe_bool(resolution_map.get("learning_claimed")),
        safe_metadata=_request_safe_metadata(retrieval_plan, source_resolution, authority_packet),
    )
    return request



def build_safe_memory_retrieval_request_v1(
    retrieval_plan: Any,
    source_resolution: Any,
    source_provider: Any = None,
    authority_packet: Any = None,
) -> SafeMemoryRetrievalRequest:
    del source_provider
    return _request_from_inputs(retrieval_plan, source_resolution, authority_packet)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


_def_request_fields = {field.name for field in SafeMemoryRetrievalRequest.__dataclass_fields__.values()}
_def_result_fields = {field.name for field in SafeMemoryRetrievalResult.__dataclass_fields__.values()}
_def_source_item_fields = {field.name for field in SafeMemorySourceResultItem.__dataclass_fields__.values()}



def _validate_allowed_fields(mapping: Mapping[str, Any], allowed: set[str], error: str) -> None:
    extra = set(str(key) for key in mapping.keys()) - allowed
    if extra:
        raise ValidationError(error)



def _validate_common_boundary(value: Any) -> None:
    if _contains_forbidden_fields(value):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_claim_marker(value):
        raise ValidationError("forbidden_public_or_claim_language_present")



def validate_safe_memory_retrieval_request_v1(request: Any) -> bool:
    _validate_common_boundary(request)
    mapping = _maybe_mapping(request)
    if mapping is None:
        raise ValidationError("unsupported_request_type")
    _validate_allowed_fields(mapping, _def_request_fields, "unknown_fields_present")

    if _safe_text(mapping.get("retrieval_mode")) not in ALLOWED_RETRIEVAL_MODES_V1:
        raise ValidationError("unknown_retrieval_mode")
    if _safe_text(mapping.get("safe_result_format")) not in ALLOWED_SAFE_RESULT_FORMATS_V1:
        raise ValidationError("unknown_safe_result_format")
    if int(mapping.get("max_result_count", 0)) <= 0:
        raise ValidationError("max_result_count_must_be_positive")
    if int(mapping.get("max_excerpt_length", 0)) <= 0:
        raise ValidationError("max_excerpt_length_must_be_positive")
    for field_name in (
        "memory_read_authority_granted",
        "source_access_granted",
        "raw_log_access_allowed",
        "private_data_access_allowed",
        "allow_raw_transcript",
        "allow_hidden_prompt",
        "allow_cross_user",
        "allow_cross_project",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "learning_claimed",
    ):
        if not isinstance(mapping.get(field_name), bool):
            raise ValidationError(f"{field_name}_must_be_bool")
    return True



def validate_safe_memory_source_result_item_v1(item: Any) -> bool:
    _validate_common_boundary(item)
    mapping = _maybe_mapping(item)
    if mapping is None:
        raise ValidationError("unsupported_source_result_item_type")
    _validate_allowed_fields(mapping, _def_source_item_fields, "unknown_fields_present")
    if _safe_text(mapping.get("source_class")) not in ALLOWED_SOURCE_CLASSES_V1:
        raise ValidationError("unknown_source_class")
    if _safe_text(mapping.get("source_class")) in {"runtime_session_log", ".weslr_state", "unknown_source"}:
        raise ValidationError("blocked_source_class")
    if _safe_bool(mapping.get("raw_content_omitted")) is False:
        raise ValidationError("raw_content_must_be_omitted")
    if _safe_bool(mapping.get("private_data_possible")):
        raise ValidationError("private_data_possible_must_be_false")
    return True



def validate_safe_memory_retrieval_result_v1(result: Any) -> bool:
    _validate_common_boundary(result)
    mapping = _maybe_mapping(result)
    if mapping is None:
        raise ValidationError("unsupported_result_type")
    _validate_allowed_fields(mapping, _def_result_fields, "unknown_fields_present")

    for field_name in (
        "retrieval_executed",
        "blocked",
        "redaction_applied",
        "raw_content_included",
        "private_data_included",
        "hidden_prompt_included",
        "cross_user_content_included",
        "cross_project_content_included",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "learning_claimed",
        "memory_read_authority_granted",
        "source_access_granted",
        "raw_log_access_allowed",
        "private_data_access_allowed",
        "allow_raw_transcript",
        "allow_hidden_prompt",
        "allow_cross_user",
        "allow_cross_project",
    ):
        if not isinstance(mapping.get(field_name), bool):
            raise ValidationError(f"{field_name}_must_be_bool")

    if mapping.get("raw_content_included"):
        raise ValidationError("raw_content_included_must_be_false")
    if mapping.get("private_data_included"):
        raise ValidationError("private_data_included_must_be_false")
    if mapping.get("hidden_prompt_included"):
        raise ValidationError("hidden_prompt_included_must_be_false")
    if mapping.get("cross_user_content_included"):
        raise ValidationError("cross_user_content_included_must_be_false")
    if mapping.get("cross_project_content_included"):
        raise ValidationError("cross_project_content_included_must_be_false")
    if mapping.get("runtime_authority"):
        raise ValidationError("runtime_authority_must_be_false")
    if mapping.get("writes_state"):
        raise ValidationError("writes_state_must_be_false")
    if mapping.get("model_provider_used"):
        raise ValidationError("model_provider_used_must_be_false")
    if mapping.get("public_claim_allowed"):
        raise ValidationError("public_claim_allowed_must_be_false")
    if mapping.get("learning_claimed"):
        raise ValidationError("learning_claimed_must_be_false")
    if mapping.get("memory_read_authority_granted"):
        raise ValidationError("memory_read_authority_granted_must_be_false")
    if mapping.get("source_access_granted"):
        raise ValidationError("source_access_granted_must_be_false")
    if _safe_text(mapping.get("blocked_reason")) == "":
        raise ValidationError("blocked_reason_required")
    return True


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------



def _blocked_result(
    request: SafeMemoryRetrievalRequest,
    blocked_reason: str,
    expected_confidence: str = "blocked",
    failure_modes: Sequence[str] | None = None,
) -> SafeMemoryRetrievalResult:
    failure_modes = tuple(_dedupe_preserve(failure_modes or (blocked_reason,))) or (blocked_reason,)
    result = SafeMemoryRetrievalResult(
        retrieval_result_id=_build_result_id(request.retrieval_request_id, True, 0, ()),
        retrieval_request_id=request.retrieval_request_id,
        retrieval_executed=False,
        blocked=True,
        blocked_reason=blocked_reason,
        source_results=tuple(),
        result_count=0,
        partial_result=False,
        expected_confidence=expected_confidence,
        actual_confidence="blocked",
        source_classes_used=tuple(),
        source_classes_blocked=tuple(request.blocked_sources or request.allowed_sources),
        time_window_used=_safe_time_window(request.resolved_start, request.resolved_end),
        semantic_filter_used=request.semantic_query_summary,
        redaction_applied=True,
        raw_content_included=False,
        private_data_included=False,
        hidden_prompt_included=False,
        cross_user_content_included=False,
        cross_project_content_included=False,
        answer_safe_summary=blocked_reason,
        result_constraints=request.result_constraints,
        failure_modes=failure_modes,
        recommended_next_step="ask_for_authority_or_safe_source",
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        learning_claimed=False,
        memory_read_authority_granted=False,
        source_access_granted=False,
        raw_log_access_allowed=False,
        private_data_access_allowed=False,
        allow_raw_transcript=False,
        allow_hidden_prompt=False,
        allow_cross_user=False,
        allow_cross_project=False,
        safe_metadata={
            "blocked_reason": blocked_reason,
            "source_resolution_id": request.source_resolution_id,
            "retrieval_mode": request.retrieval_mode,
        },
    )
    return result



def _result_confidence_label(count: int, partial: bool, semantic_query_present: bool) -> str:
    if count <= 0:
        return "blocked"
    if partial:
        return "medium"
    if semantic_query_present:
        return "high"
    return "high"



def _build_source_result_item(item: Mapping[str, Any], request: SafeMemoryRetrievalRequest, rank_hint: int) -> SafeMemorySourceResultItem:
    source_class = _safe_text(item.get("source_class"))
    source_id = _safe_text(item.get("source_id")) or _deterministic_id("source", source_class, item.get("timestamp"), item.get("source_label"))
    safe_summary = _safe_text(item.get("safe_summary"))
    if not safe_summary:
        safe_summary = _safe_text(item.get("safe_excerpt"))
    safe_excerpt = _clip_excerpt(item.get("safe_excerpt") or item.get("safe_summary"), request.max_excerpt_length)
    source_label = _safe_text(item.get("source_label")) or source_class
    source_timestamp = _safe_text(item.get("timestamp") or item.get("source_timestamp")) or None
    source_time_window = _safe_time_window(request.resolved_start, request.resolved_end)
    match_reason = _safe_text(item.get("match_reason"))
    if not match_reason:
        if request.semantic_query_present and request.semantic_query_summary:
            match_reason = "time-and-semantic-match"
        elif request.semantic_query_present:
            match_reason = "semantic-match"
        else:
            match_reason = "time-match"
    confidence = float(item.get("confidence") or 0.8)
    redactions = tuple(_dedupe_preserve(item.get("redactions") or ("raw_content", "private_data", "hidden_prompt")))
    source_reference = _safe_text(item.get("source_reference")) or source_id
    authority_used = _safe_text(item.get("authority_used")) or request.authority_level
    private_data_possible = _safe_bool(item.get("private_data_possible"))
    safe_metadata = {
        "source_scope": _safe_text(item.get("project_scope")) or "same_project",
        "session_scope": _safe_text(item.get("session_scope")) or "current_session",
        "rank_source": "source_priority",
    }
    return SafeMemorySourceResultItem(
        source_class=source_class,
        source_id=source_id,
        source_label=source_label,
        source_timestamp=source_timestamp,
        source_time_window=source_time_window,
        match_reason=match_reason,
        rank_hint=rank_hint,
        confidence=confidence,
        safe_summary=safe_summary,
        safe_excerpt=safe_excerpt,
        raw_content_omitted=True,
        redactions=redactions,
        source_reference=source_reference,
        authority_used=authority_used,
        private_data_possible=private_data_possible,
        safe_metadata=safe_metadata,
    )



def execute_safe_memory_retrieval_v1(
    retrieval_plan: Any,
    source_resolution: Any,
    source_provider: Any = None,
    authority_packet: Any = None,
) -> SafeMemoryRetrievalResult:
    try:
        request = _request_from_inputs(retrieval_plan, source_resolution, authority_packet)
    except Exception as exc:
        if isinstance(exc, ValidationError):
            retrieval_plan_map = _maybe_mapping(retrieval_plan) or {}
            source_resolution_map = _maybe_mapping(source_resolution) or {}
            return _blocked_result(
                SafeMemoryRetrievalRequest(
                    retrieval_request_id="invalid_request",
                    retrieval_plan_id=_safe_text(retrieval_plan_map.get("retrieval_plan_id")) or "invalid",
                    source_resolution_id=_safe_text(source_resolution_map.get("source_resolution_id")) or "invalid",
                    allowed_sources=tuple(),
                    blocked_sources=tuple(),
                    requires_authority_sources=tuple(),
                    selected_source_priority=tuple(),
                    resolved_start=None,
                    resolved_end=None,
                    timezone="UTC",
                    retrieval_mode="blocked_no_source",
                    semantic_query_present=False,
                    semantic_query_summary="",
                    authority_packet_id="authority_none",
                    authority_level="no_authority",
                    memory_read_authority_granted=False,
                    source_access_granted=False,
                    raw_log_access_allowed=False,
                    private_data_access_allowed=False,
                    redaction_required=True,
                    safe_result_format="blocked_authority_required",
                    max_result_count=DEFAULT_MAX_RESULT_COUNT_V1,
                    max_excerpt_length=DEFAULT_MAX_EXCERPT_LENGTH_V1,
                    allow_raw_transcript=False,
                    allow_hidden_prompt=False,
                    allow_cross_user=False,
                    allow_cross_project=False,
                    result_constraints=DEFAULT_RESULT_CONSTRAINTS_V1,
                    runtime_authority=False,
                    writes_state=False,
                    model_provider_used=False,
                    public_claim_allowed=False,
                    learning_claimed=False,
                    safe_metadata={"validation_error": _safe_text(exc)},
                ),
                "invalid_retrieval_input",
                failure_modes=("invalid_retrieval_input",),
            )
        raise

    if source_provider is None:
        return _blocked_result(request, "source provider missing", failure_modes=("source_provider_missing",))
    if not (request.memory_read_authority_granted and request.source_access_granted):
        return _blocked_result(request, "authority missing", failure_modes=("authority_missing",))

    source_items = _source_items_from_provider(source_provider)
    if not source_items:
        return _blocked_result(request, "no safe source available", failure_modes=("source_provider_empty",))

    allowed = set(request.allowed_sources)
    blocked = set(request.blocked_sources)
    selected: list[Mapping[str, Any]] = []
    skipped: list[str] = []
    source_classes_blocked: list[str] = []
    for raw_item in source_items:
        if not isinstance(raw_item, Mapping):
            continue
        source_class = _normalize_text(raw_item.get("source_class"))
        if not source_class:
            skipped.append("missing_source_class")
            continue
        if source_class not in allowed or source_class in blocked or _is_unsafe_source_class(source_class):
            source_classes_blocked.append(source_class)
            skipped.append("blocked_source_class")
            continue
        safe, reasons = _source_item_is_safe(raw_item, request)
        if not safe:
            skipped.extend(reasons)
            continue
        selected.append(raw_item)

    if not selected:
        return _blocked_result(
            request,
            "no safe source available",
            failure_modes=("no_safe_source_available",) + tuple(_dedupe_preserve(skipped)),
        )

    priority = {source: index for index, source in enumerate(request.selected_source_priority or request.allowed_sources)}
    selected.sort(key=lambda item: (priority.get(_normalize_text(item.get("source_class")), 999), _safe_text(item.get("timestamp")), _safe_text(item.get("source_id"))))
    limited = selected[: request.max_result_count]
    partial = len(selected) > len(limited) or bool(skipped)

    result_items = tuple(
        _build_source_result_item(item, request, rank_hint=index)
        for index, item in enumerate(limited, start=1)
    )
    source_classes_used = tuple(_dedupe_preserve(item.source_class for item in result_items))
    source_classes_blocked = tuple(_dedupe_preserve(source_classes_blocked))
    result_count = len(result_items)
    actual_confidence = _result_confidence_label(result_count, partial, request.semantic_query_present)
    blocked_flag = False
    retrieval_result = SafeMemoryRetrievalResult(
        retrieval_result_id=_build_result_id(request.retrieval_request_id, blocked_flag, result_count, source_classes_used),
        retrieval_request_id=request.retrieval_request_id,
        retrieval_executed=True,
        blocked=False,
        blocked_reason="not blocked",
        source_results=result_items,
        result_count=result_count,
        partial_result=partial,
        expected_confidence=request.safe_metadata.get("expected_confidence", "high") if request.safe_metadata else "high",
        actual_confidence=actual_confidence,
        source_classes_used=source_classes_used,
        source_classes_blocked=source_classes_blocked,
        time_window_used=_safe_time_window(request.resolved_start, request.resolved_end),
        semantic_filter_used=request.semantic_query_summary,
        redaction_applied=True,
        raw_content_included=False,
        private_data_included=False,
        hidden_prompt_included=False,
        cross_user_content_included=False,
        cross_project_content_included=False,
        answer_safe_summary=f"Retrieved {result_count} safe memory result(s).",
        result_constraints=request.result_constraints,
        failure_modes=tuple(_dedupe_preserve(skipped)),
        recommended_next_step="pass_to_result_ranker",
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        learning_claimed=False,
        memory_read_authority_granted=False,
        source_access_granted=False,
        raw_log_access_allowed=False,
        private_data_access_allowed=False,
        allow_raw_transcript=False,
        allow_hidden_prompt=False,
        allow_cross_user=False,
        allow_cross_project=False,
        safe_metadata={
            "retrieval_mode": request.retrieval_mode,
            "source_resolution_id": request.source_resolution_id,
            "selected_count": result_count,
        },
    )
    validate_safe_memory_retrieval_result_v1(retrieval_result)
    return retrieval_result


# ---------------------------------------------------------------------------
# Summary and JSON safety
# ---------------------------------------------------------------------------



def summarize_safe_memory_retrieval_result_v1(result: Any) -> SafeMemoryRetrievalResultSummary:
    validate_safe_memory_retrieval_result_v1(result)
    if not isinstance(result, SafeMemoryRetrievalResult):
        mapping = _maybe_mapping(result)
        result = SafeMemoryRetrievalResult(
            retrieval_result_id=_safe_text(mapping.get("retrieval_result_id")),
            retrieval_request_id=_safe_text(mapping.get("retrieval_request_id")),
            retrieval_executed=_safe_bool(mapping.get("retrieval_executed")),
            blocked=_safe_bool(mapping.get("blocked")),
            blocked_reason=_safe_text(mapping.get("blocked_reason")),
            source_results=tuple(mapping.get("source_results") or ()),
            result_count=int(mapping.get("result_count") or 0),
            partial_result=_safe_bool(mapping.get("partial_result")),
            expected_confidence=_safe_text(mapping.get("expected_confidence")),
            actual_confidence=_safe_text(mapping.get("actual_confidence")),
            source_classes_used=tuple(mapping.get("source_classes_used") or ()),
            source_classes_blocked=tuple(mapping.get("source_classes_blocked") or ()),
            time_window_used=_safe_text(mapping.get("time_window_used")),
            semantic_filter_used=_safe_text(mapping.get("semantic_filter_used")),
            redaction_applied=_safe_bool(mapping.get("redaction_applied")),
            raw_content_included=_safe_bool(mapping.get("raw_content_included")),
            private_data_included=_safe_bool(mapping.get("private_data_included")),
            hidden_prompt_included=_safe_bool(mapping.get("hidden_prompt_included")),
            cross_user_content_included=_safe_bool(mapping.get("cross_user_content_included")),
            cross_project_content_included=_safe_bool(mapping.get("cross_project_content_included")),
            answer_safe_summary=_safe_text(mapping.get("answer_safe_summary")),
            result_constraints=tuple(mapping.get("result_constraints") or ()),
            failure_modes=tuple(mapping.get("failure_modes") or ()),
            recommended_next_step=_safe_text(mapping.get("recommended_next_step")),
            runtime_authority=_safe_bool(mapping.get("runtime_authority")),
            writes_state=_safe_bool(mapping.get("writes_state")),
            model_provider_used=_safe_bool(mapping.get("model_provider_used")),
            public_claim_allowed=_safe_bool(mapping.get("public_claim_allowed")),
            learning_claimed=_safe_bool(mapping.get("learning_claimed")),
            memory_read_authority_granted=_safe_bool(mapping.get("memory_read_authority_granted")),
            source_access_granted=_safe_bool(mapping.get("source_access_granted")),
            raw_log_access_allowed=_safe_bool(mapping.get("raw_log_access_allowed")),
            private_data_access_allowed=_safe_bool(mapping.get("private_data_access_allowed")),
            allow_raw_transcript=_safe_bool(mapping.get("allow_raw_transcript")),
            allow_hidden_prompt=_safe_bool(mapping.get("allow_hidden_prompt")),
            allow_cross_user=_safe_bool(mapping.get("allow_cross_user")),
            allow_cross_project=_safe_bool(mapping.get("allow_cross_project")),
            safe_metadata=mapping.get("safe_metadata") if mapping.get("safe_metadata") is None else dict(_json_safe(mapping.get("safe_metadata"))),
        )
    return SafeMemoryRetrievalResultSummary(
        summary_type=SUMMARY_TYPE_V1,
        retrieval_result_id=result.retrieval_result_id,
        retrieval_request_id=result.retrieval_request_id,
        retrieval_executed=result.retrieval_executed,
        blocked=result.blocked,
        result_count=result.result_count,
        expected_confidence=result.expected_confidence,
        actual_confidence=result.actual_confidence,
        source_classes_used=result.source_classes_used,
        source_classes_blocked=result.source_classes_blocked,
        safe_metadata=result.safe_metadata,
    )



def to_safe_memory_retrieval_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


# ---------------------------------------------------------------------------
# Initial examples
# ---------------------------------------------------------------------------



def _example_plan_and_resolution(name: str) -> tuple[TemporalMemoryRetrievalPlan, MemorySourceScopeResolution, dict[str, Any] | None, dict[str, Any] | None]:
    from weslr.temporal_memory_retrieval_plan import build_initial_temporal_memory_retrieval_plan_examples_v1
    from weslr.memory_source_scope_registry import build_initial_memory_source_scope_examples_v1

    plans = {ex.safe_metadata["example_name"]: ex for ex in build_initial_temporal_memory_retrieval_plan_examples_v1() if ex.safe_metadata and "example_name" in ex.safe_metadata}
    resolutions = {ex.safe_metadata["example_name"]: ex for ex in build_initial_memory_source_scope_examples_v1() if ex.safe_metadata and "example_name" in ex.safe_metadata}
    return plans[name], resolutions[name], None, None



def _fake_provider(source_items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"source_items": source_items}



def build_initial_safe_memory_retrieval_examples_v1() -> tuple[SafeMemoryRetrievalResult, ...]:
    from weslr.temporal_memory_retrieval_plan import build_initial_temporal_memory_retrieval_plan_examples_v1
    from weslr.memory_source_scope_registry import build_initial_memory_source_scope_examples_v1

    plan_map = {ex.safe_metadata["example_name"]: ex for ex in build_initial_temporal_memory_retrieval_plan_examples_v1() if ex.safe_metadata}
    resolution_map = {ex.safe_metadata["example_name"]: ex for ex in build_initial_memory_source_scope_examples_v1() if ex.safe_metadata}

    examples: list[SafeMemoryRetrievalResult] = []

    examples.append(
        SafeMemoryRetrievalResult(
            retrieval_result_id="smre_blocked_missing_provider",
            retrieval_request_id=_deterministic_id("request", "missing-provider"),
            retrieval_executed=False,
            blocked=True,
            blocked_reason="source provider missing",
            source_results=tuple(),
            result_count=0,
            partial_result=False,
            expected_confidence="blocked",
            actual_confidence="blocked",
            source_classes_used=tuple(),
            source_classes_blocked=tuple(),
            time_window_used="unresolved",
            semantic_filter_used="",
            redaction_applied=True,
            raw_content_included=False,
            private_data_included=False,
            hidden_prompt_included=False,
            cross_user_content_included=False,
            cross_project_content_included=False,
            answer_safe_summary="source provider missing",
            result_constraints=DEFAULT_RESULT_CONSTRAINTS_V1,
            failure_modes=("source_provider_missing",),
            recommended_next_step="ask_for_authority_or_safe_source",
            runtime_authority=False,
            writes_state=False,
            model_provider_used=False,
            public_claim_allowed=False,
            learning_claimed=False,
            safe_metadata={"example_name": "blocked_missing_provider_result"},
        )
    )

    examples.append(
        SafeMemoryRetrievalResult(
            retrieval_result_id="smre_blocked_missing_authority",
            retrieval_request_id=_deterministic_id("request", "missing-authority"),
            retrieval_executed=False,
            blocked=True,
            blocked_reason="authority missing",
            source_results=tuple(),
            result_count=0,
            partial_result=False,
            expected_confidence="blocked",
            actual_confidence="blocked",
            source_classes_used=tuple(),
            source_classes_blocked=("approved_memory_index",),
            time_window_used="2026-05-31T00:00:00..2026-06-01T00:00:00",
            semantic_filter_used="",
            redaction_applied=True,
            raw_content_included=False,
            private_data_included=False,
            hidden_prompt_included=False,
            cross_user_content_included=False,
            cross_project_content_included=False,
            answer_safe_summary="authority missing",
            result_constraints=DEFAULT_RESULT_CONSTRAINTS_V1,
            failure_modes=("authority_missing",),
            recommended_next_step="ask_for_authority_or_safe_source",
            runtime_authority=False,
            writes_state=False,
            model_provider_used=False,
            public_claim_allowed=False,
            learning_claimed=False,
            safe_metadata={"example_name": "blocked_missing_authority_result"},
        )
    )

    examples.append(
        execute_safe_memory_retrieval_v1(
            plan_map["yesterday_temporal_first_plan"],
            resolution_map["yesterday_temporal_source_resolution"],
            _fake_provider([
                {
                    "source_class": "approved_memory_index",
                    "source_id": "mem-001",
                    "source_label": "Yesterday summary",
                    "timestamp": "2026-05-31T12:00:00",
                    "safe_summary": "You asked about yesterday’s work summary.",
                    "safe_excerpt": "Yesterday summary only.",
                    "semantic_tags": ["summary", "yesterday"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                }
            ]),
            {"authority_packet_id": "auth-001", "authority_level": "summary_authority", "memory_read_authority_granted": True, "source_access_granted": True, "raw_log_access_allowed": False, "private_data_access_allowed": False, "allow_hidden_prompt": False, "allow_cross_user": False, "allow_cross_project": False},
        )
    )
    examples[-1] = SafeMemoryRetrievalResult(**{**asdict(examples[-1]), "safe_metadata": {**(examples[-1].safe_metadata or {}), "example_name": "yesterday_summary_fake_provider_result"}})

    examples.append(
        execute_safe_memory_retrieval_v1(
            plan_map["yesterday_wifi_hybrid_plan"],
            resolution_map["yesterday_temporal_source_resolution"],
            _fake_provider([
                {
                    "source_class": "project_memory",
                    "source_id": "mem-wifi-001",
                    "source_label": "Wi-Fi note",
                    "timestamp": "2026-05-31T13:00:00",
                    "safe_summary": "Wi-Fi was the main topic.",
                    "safe_excerpt": "Wi-Fi troubleshooting summary.",
                    "semantic_tags": ["wifi", "network"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                }
            ]),
            {"authority_packet_id": "auth-002", "authority_level": "summary_authority", "memory_read_authority_granted": True, "source_access_granted": True, "raw_log_access_allowed": False, "private_data_access_allowed": False, "allow_hidden_prompt": False, "allow_cross_user": False, "allow_cross_project": False},
        )
    )
    examples[-1] = SafeMemoryRetrievalResult(**{**asdict(examples[-1]), "safe_metadata": {**(examples[-1].safe_metadata or {}), "example_name": "yesterday_wifi_fake_provider_result"}})

    examples.append(
        execute_safe_memory_retrieval_v1(
            plan_map["earlier_in_chat_session_plan"],
            resolution_map["earlier_chat_source_resolution"],
            _fake_provider([
                {
                    "source_class": "current_conversation",
                    "source_id": "chat-001",
                    "source_label": "Earlier chat mention",
                    "timestamp": "2026-06-01T11:00:00",
                    "safe_summary": "Earlier you said ISS internally.",
                    "safe_excerpt": "ISS mention.",
                    "semantic_tags": ["iss", "chat"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                }
            ]),
            {"authority_packet_id": "auth-003", "authority_level": "summary_authority", "memory_read_authority_granted": True, "source_access_granted": True, "raw_log_access_allowed": False, "private_data_access_allowed": False, "allow_hidden_prompt": False, "allow_cross_user": False, "allow_cross_project": False},
        )
    )
    examples[-1] = SafeMemoryRetrievalResult(**{**asdict(examples[-1]), "safe_metadata": {**(examples[-1].safe_metadata or {}), "example_name": "earlier_chat_fake_provider_result"}})

    examples.append(
        execute_safe_memory_retrieval_v1(
            plan_map["before_file_manifest_builder_event_plan"],
            resolution_map["before_file_manifest_source_resolution"],
            _fake_provider([
                {
                    "source_class": "lane_report_metadata",
                    "source_id": "lane-001",
                    "source_label": "Before file manifest builder",
                    "timestamp": "2026-06-01T10:30:00",
                    "safe_summary": "File manifest builder followed this lane.",
                    "safe_excerpt": "Manifest lane metadata.",
                    "semantic_tags": ["manifest", "lane"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                }
            ]),
            {"authority_packet_id": "auth-004", "authority_level": "metadata_authority", "memory_read_authority_granted": True, "source_access_granted": True, "raw_log_access_allowed": False, "private_data_access_allowed": False, "allow_hidden_prompt": False, "allow_cross_user": False, "allow_cross_project": False},
        )
    )
    examples[-1] = SafeMemoryRetrievalResult(**{**asdict(examples[-1]), "safe_metadata": {**(examples[-1].safe_metadata or {}), "example_name": "before_file_manifest_fake_provider_result"}})

    examples.append(
        execute_safe_memory_retrieval_v1(
            plan_map["blocked_no_source_plan"],
            resolution_map["runtime_log_blocked_resolution"],
            _fake_provider([
                {
                    "source_class": "runtime_session_log",
                    "source_id": "log-001",
                    "source_label": "Runtime log",
                    "timestamp": "2026-05-31T09:00:00",
                    "safe_summary": "runtime log",
                    "safe_excerpt": "runtime log excerpt",
                    "semantic_tags": ["log"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                }
            ]),
            {"authority_packet_id": "auth-005", "authority_level": "operator_runtime_authority", "memory_read_authority_granted": True, "source_access_granted": True, "raw_log_access_allowed": False, "private_data_access_allowed": False, "allow_hidden_prompt": False, "allow_cross_user": False, "allow_cross_project": False},
        )
    )
    examples[-1] = SafeMemoryRetrievalResult(**{**asdict(examples[-1]), "safe_metadata": {**(examples[-1].safe_metadata or {}), "example_name": "runtime_log_blocked_result"}})

    examples.append(
        execute_safe_memory_retrieval_v1(
            plan_map["blocked_no_source_plan"],
            resolution_map["weslr_state_blocked_resolution"],
            _fake_provider([
                {
                    "source_class": ".weslr_state",
                    "source_id": "state-001",
                    "source_label": "WESLR state",
                    "timestamp": "2026-05-31T09:00:00",
                    "safe_summary": "private state",
                    "safe_excerpt": "private state excerpt",
                    "semantic_tags": ["state"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                }
            ]),
            {"authority_packet_id": "auth-006", "authority_level": "private_state_authority", "memory_read_authority_granted": True, "source_access_granted": True, "raw_log_access_allowed": False, "private_data_access_allowed": False, "allow_hidden_prompt": False, "allow_cross_user": False, "allow_cross_project": False},
        )
    )
    examples[-1] = SafeMemoryRetrievalResult(**{**asdict(examples[-1]), "safe_metadata": {**(examples[-1].safe_metadata or {}), "example_name": "weslr_state_blocked_result"}})

    return tuple(examples)


__all__ = [
    "HELPER_TYPE_V1",
    "SAFE_MEMORY_RETRIEVAL_REQUEST_TYPE_V1",
    "SAFE_MEMORY_RETRIEVAL_RESULT_TYPE_V1",
    "SAFE_MEMORY_SOURCE_RESULT_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "SafeMemoryRetrievalRequest",
    "SafeMemorySourceResultItem",
    "SafeMemoryRetrievalResult",
    "SafeMemoryRetrievalResultSummary",
    "ValidationError",
    "build_safe_memory_retrieval_request_v1",
    "execute_safe_memory_retrieval_v1",
    "validate_safe_memory_retrieval_request_v1",
    "validate_safe_memory_retrieval_result_v1",
    "summarize_safe_memory_retrieval_result_v1",
    "to_safe_memory_retrieval_json_safe_v1",
    "build_initial_safe_memory_retrieval_examples_v1",
]
