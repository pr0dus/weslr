"""Metadata-only memory source scope registry v1.

This module defines safe source-scope records and resolves temporal retrieval
plans into source-access decisions without reading memory, logs, `.weslr`, or
files. It is pure, deterministic, import-safe, and fail-closed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import hashlib
from typing import Any, Iterable, Mapping, Sequence

from weslr.temporal_memory_retrieval_plan import (
    TemporalMemoryRetrievalPlan,
    build_temporal_memory_retrieval_plan_v1,
    validate_temporal_memory_retrieval_plan_v1,
)

HELPER_TYPE_V1 = "memory_source_scope_registry_v1"
MEMORY_SOURCE_SCOPE_RECORD_TYPE_V1 = "memory_source_scope_record_v1"
MEMORY_SOURCE_SCOPE_REGISTRY_TYPE_V1 = "memory_source_scope_registry_v1"
SOURCE_RESOLUTION_TYPE_V1 = "memory_source_scope_resolution_v1"
SUMMARY_TYPE_V1 = "memory_source_scope_registry_summary_v1"

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

ALLOWED_CONTENT_LEVELS_V1 = {
    "metadata_only",
    "summary_only",
    "redacted_summary",
    "owner_visible_content",
    "raw_log",
    "private_state",
    "unknown_content",
}

ALLOWED_ACCESS_DECISIONS_V1 = {
    "allow_metadata_only",
    "allow_summary_only",
    "allow_redacted_summary",
    "requires_owner_authority",
    "requires_operator_authority",
    "blocked_by_default",
    "clarification_required",
    "unknown_blocked",
}

ALLOWED_AUTHORITY_LEVELS_V1 = {
    "no_authority",
    "metadata_authority",
    "summary_authority",
    "redacted_summary_authority",
    "owner_content_authority",
    "raw_log_authority",
    "private_state_authority",
    "operator_runtime_authority",
}

ALLOWED_SAFE_RESULT_FORMATS_V1 = {
    "metadata_summary",
    "redacted_summary",
    "owner_visible_excerpt",
    "source_reference_only",
    "blocked_authority_required",
    "clarification_needed",
}

ALLOWED_TEMPORAL_RETRIEVAL_MODES_V1 = {
    "temporal_first",
    "semantic_first",
    "hybrid_temporal_semantic",
    "event_anchor_retrieval",
    "session_order_retrieval",
    "clarification_required",
    "blocked_no_authority",
    "blocked_no_source",
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

SAFE_RESULT_CONSTRAINTS_V1 = (
    "no raw private dump",
    "no hidden prompt exposure",
    "no full transcript by default",
    "no cross-user retrieval",
    "safe summary preferred",
    "confidence required",
    "source class required",
)

SAFE_ANSWER_BOUNDARY_V1 = (
    "state uncertainty if retrieval is partial",
    "say source unavailable if blocked",
    "do not fabricate memory",
    "do not expose raw logs without authority",
)

DEFAULT_FAILURE_MODES_V1 = (
    "unresolved_time_anchor",
    "semantic_ambiguity",
    "source_unavailable",
    "authority_not_granted",
    "partial_recall",
)

SOURCE_POLICY_ORDER_V1 = (
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
)

REQUIRED_STANDARD_SOURCE_CLASSES_V1 = (
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
)

TEMPORAL_FIRST_PRIORITY_V1 = (
    "approved_memory_index",
    "prior_conversation_summary",
    "project_memory",
    "repo_commit_metadata",
    "lane_report_metadata",
    "uploaded_file_reference",
    "current_conversation",
    "owner_approved_summary",
)

SESSION_ORDER_PRIORITY_V1 = (
    "current_conversation",
    "prior_conversation_summary",
    "approved_memory_index",
    "project_memory",
    "unknown_source",
)

EVENT_ANCHOR_PRIORITY_V1 = (
    "lane_report_metadata",
    "repo_commit_metadata",
    "project_memory",
    "artifact_validation_report",
    "artifact_manifest_metadata",
)

CLARIFICATION_PRIORITY_V1 = (
    "current_conversation",
    "prior_conversation_summary",
    "unknown_source",
)

UNSAFE_DEFAULT_SOURCE_CLASSES_V1 = {
    "runtime_session_log",
    ".weslr_state",
}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MemorySourceScopeRecord:
    source_scope_id: str
    source_class: str
    source_label: str
    description: str
    content_level: str
    authority_required: str
    default_access_decision: str
    raw_access_allowed: bool
    summary_access_allowed: bool
    metadata_access_allowed: bool
    private_data_possible: bool
    cross_user_allowed: bool
    cross_project_allowed: bool
    cross_session_allowed: bool
    temporal_filter_supported: bool
    semantic_filter_supported: bool
    event_anchor_supported: bool
    commit_anchor_supported: bool
    owner_authority_required: bool
    operator_authority_required: bool
    runtime_authority_required: bool
    retention_sensitivity: str
    privacy_risk: str
    public_claim_risk: str
    safe_result_format: str
    blocked_reason: str
    required_redactions: tuple[str, ...]
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class MemorySourceScopeRegistry:
    registry_id: str
    registry_type: str
    records: tuple[MemorySourceScopeRecord, ...]
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class MemorySourceScopeResolution:
    source_resolution_id: str
    retrieval_plan_id: str
    candidate_sources: tuple[str, ...]
    allowed_sources: tuple[str, ...]
    blocked_sources: tuple[str, ...]
    requires_authority_sources: tuple[str, ...]
    selected_source_priority: tuple[str, ...]
    effective_access_decision: str
    authority_required: str
    authority_missing: bool
    clarification_required: bool
    clarification_question: str
    safe_result_format: str
    redaction_required: bool
    raw_access_allowed: bool
    summary_access_allowed: bool
    metadata_access_allowed: bool
    private_data_access_allowed: bool
    memory_read_authority_granted: bool
    source_access_granted: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class MemorySourceScopeRegistrySummary:
    summary_type: str
    registry_id: str
    source_class_count: int
    source_classes: tuple[str, ...]
    access_decisions: tuple[str, ...]
    blocked_source_classes: tuple[str, ...]
    authority_required_source_classes: tuple[str, ...]
    safe_result_formats: tuple[str, ...]
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
        return [_json_safe(item) for item in sorted(value, key=lambda item: _safe_text(item))]
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



def _deterministic_id(*parts: Any) -> str:
    payload = "|".join(_normalize_text(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"mssr_{digest}"



def _maybe_mapping(value: Any) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value
    if is_dataclass(value):
        return asdict(value)
    return None



def _registry_records(registry: Any) -> tuple[MemorySourceScopeRecord, ...]:
    if registry is None:
        return build_memory_source_scope_registry_v1().records
    if isinstance(registry, MemorySourceScopeRegistry):
        return registry.records
    if isinstance(registry, Mapping):
        records = registry.get("records")
        if records is None:
            return tuple()
        if isinstance(records, tuple):
            return tuple(records)
        if isinstance(records, list):
            return tuple(records)
    if isinstance(registry, (list, tuple)):
        return tuple(registry)
    return tuple()



def _record_to_mapping(record: Any) -> Mapping[str, Any]:
    if is_dataclass(record):
        return asdict(record)
    if isinstance(record, Mapping):
        return record
    raise ValidationError("unsupported_record_type")



def _record_by_class(registry: Any) -> dict[str, MemorySourceScopeRecord]:
    out: dict[str, MemorySourceScopeRecord] = {}
    for record in _registry_records(registry):
        if isinstance(record, MemorySourceScopeRecord):
            out[record.source_class] = record
        elif isinstance(record, Mapping):
            cls = _safe_text(record.get("source_class"))
            out[cls] = build_memory_source_scope_record_v1(**_record_kwargs_from_mapping(record))
    return out



def _record_kwargs_from_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_class": mapping.get("source_class"),
        "source_label": mapping.get("source_label"),
        "description": mapping.get("description"),
        "content_level": mapping.get("content_level"),
        "authority_required": mapping.get("authority_required"),
        "default_access_decision": mapping.get("default_access_decision"),
        "raw_access_allowed": mapping.get("raw_access_allowed"),
        "summary_access_allowed": mapping.get("summary_access_allowed"),
        "metadata_access_allowed": mapping.get("metadata_access_allowed"),
        "private_data_possible": mapping.get("private_data_possible"),
        "cross_user_allowed": mapping.get("cross_user_allowed"),
        "cross_project_allowed": mapping.get("cross_project_allowed"),
        "cross_session_allowed": mapping.get("cross_session_allowed"),
        "temporal_filter_supported": mapping.get("temporal_filter_supported"),
        "semantic_filter_supported": mapping.get("semantic_filter_supported"),
        "event_anchor_supported": mapping.get("event_anchor_supported"),
        "commit_anchor_supported": mapping.get("commit_anchor_supported"),
        "owner_authority_required": mapping.get("owner_authority_required"),
        "operator_authority_required": mapping.get("operator_authority_required"),
        "runtime_authority_required": mapping.get("runtime_authority_required"),
        "retention_sensitivity": mapping.get("retention_sensitivity"),
        "privacy_risk": mapping.get("privacy_risk"),
        "public_claim_risk": mapping.get("public_claim_risk"),
        "safe_result_format": mapping.get("safe_result_format"),
        "blocked_reason": mapping.get("blocked_reason"),
        "required_redactions": mapping.get("required_redactions"),
        "safe_metadata": mapping.get("safe_metadata"),
    }

def _normalize_record_mapping(mapping: Mapping[str, Any]) -> MemorySourceScopeRecord:
    return MemorySourceScopeRecord(
        source_scope_id=_safe_text(mapping.get("source_scope_id")),
        source_class=_safe_text(mapping.get("source_class")),
        source_label=_safe_text(mapping.get("source_label")),
        description=_safe_text(mapping.get("description")),
        content_level=_safe_content_level(mapping.get("content_level")),
        authority_required=_safe_authority(mapping.get("authority_required")),
        default_access_decision=_safe_access_decision(mapping.get("default_access_decision")),
        raw_access_allowed=bool(mapping.get("raw_access_allowed")),
        summary_access_allowed=bool(mapping.get("summary_access_allowed")),
        metadata_access_allowed=bool(mapping.get("metadata_access_allowed")),
        private_data_possible=bool(mapping.get("private_data_possible")),
        cross_user_allowed=bool(mapping.get("cross_user_allowed")),
        cross_project_allowed=bool(mapping.get("cross_project_allowed")),
        cross_session_allowed=bool(mapping.get("cross_session_allowed")),
        temporal_filter_supported=bool(mapping.get("temporal_filter_supported")),
        semantic_filter_supported=bool(mapping.get("semantic_filter_supported")),
        event_anchor_supported=bool(mapping.get("event_anchor_supported")),
        commit_anchor_supported=bool(mapping.get("commit_anchor_supported")),
        owner_authority_required=bool(mapping.get("owner_authority_required")),
        operator_authority_required=bool(mapping.get("operator_authority_required")),
        runtime_authority_required=bool(mapping.get("runtime_authority_required")),
        retention_sensitivity=_safe_text(mapping.get("retention_sensitivity")) or "low",
        privacy_risk=_safe_text(mapping.get("privacy_risk")) or "low",
        public_claim_risk=_safe_text(mapping.get("public_claim_risk")) or "low",
        safe_result_format=_safe_result_format(mapping.get("safe_result_format")),
        blocked_reason=_safe_text(mapping.get("blocked_reason")),
        required_redactions=tuple(_dedupe_preserve(mapping.get("required_redactions") or ())),
        safe_metadata=_safe_record_metadata(mapping.get("safe_metadata")),
    )



def _safe_authority(value: Any) -> str:
    text = _normalize_text(value)
    if not text:
        return "no_authority"
    if text not in ALLOWED_AUTHORITY_LEVELS_V1:
        return "no_authority"
    return text



def _safe_access_decision(value: Any) -> str:
    text = _normalize_text(value)
    if not text:
        return "unknown_blocked"
    if text not in ALLOWED_ACCESS_DECISIONS_V1:
        return "unknown_blocked"
    return text



def _safe_content_level(value: Any) -> str:
    text = _normalize_text(value)
    if not text:
        return "unknown_content"
    if text not in ALLOWED_CONTENT_LEVELS_V1:
        return "unknown_content"
    return text



def _safe_result_format(value: Any) -> str:
    text = _normalize_text(value)
    if not text:
        return "metadata_summary"
    if text not in ALLOWED_SAFE_RESULT_FORMATS_V1:
        return "metadata_summary"
    return text



def _safe_record_metadata(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    mapping = _maybe_mapping(value)
    if mapping is None:
        return {"value": _json_safe(value)}
    return {str(key): _json_safe(item) for key, item in mapping.items()}



def _build_source_scope_id(source_class: str, source_label: str, content_level: str, default_access_decision: str) -> str:
    return _deterministic_id(source_class, source_label, content_level, default_access_decision)



def _build_registry_id(records: Sequence[MemorySourceScopeRecord]) -> str:
    return _deterministic_id("registry", [record.source_scope_id for record in records], len(records))



def _source_priority_for_mode(mode: str) -> tuple[str, ...]:
    if mode == "session_order_retrieval":
        return SESSION_ORDER_PRIORITY_V1
    if mode == "event_anchor_retrieval":
        return EVENT_ANCHOR_PRIORITY_V1
    if mode == "clarification_required":
        return CLARIFICATION_PRIORITY_V1
    if mode == "temporal_first" or mode == "hybrid_temporal_semantic":
        return TEMPORAL_FIRST_PRIORITY_V1
    return tuple()



def _clarification_question_for_mode(mode: str) -> str:
    if mode == "blocked_no_source":
        return "Which source should I use?"
    if mode == "blocked_no_authority":
        return "Which authority level is available for this source?"
    if mode == "clarification_required":
        return "Which source scope or time window should I use?"
    return ""



def _plan_mode_candidate_sources(plan: TemporalMemoryRetrievalPlan) -> tuple[str, ...]:
    if plan.retrieval_mode == "temporal_first":
        return ("approved_memory_index", "prior_conversation_summary", "project_memory")
    if plan.retrieval_mode == "hybrid_temporal_semantic":
        return ("approved_memory_index", "prior_conversation_summary", "project_memory")
    if plan.retrieval_mode == "session_order_retrieval":
        return ("current_conversation", "prior_conversation_summary")
    if plan.retrieval_mode == "event_anchor_retrieval":
        return ("lane_report_metadata", "repo_commit_metadata", "project_memory")
    if plan.retrieval_mode == "blocked_no_source":
        return tuple()
    if plan.retrieval_mode == "blocked_no_authority":
        return tuple(plan.candidate_source_classes or ())
    if plan.retrieval_mode == "clarification_required":
        return tuple(plan.candidate_source_classes or ())
    return tuple(plan.candidate_source_classes or ())



def _default_decision_priority(record: MemorySourceScopeRecord) -> int:
    order = {
        "allow_metadata_only": 0,
        "allow_summary_only": 1,
        "allow_redacted_summary": 2,
        "requires_owner_authority": 3,
        "requires_operator_authority": 4,
        "clarification_required": 5,
        "blocked_by_default": 6,
        "unknown_blocked": 7,
    }
    return order.get(record.default_access_decision, 99)



def _build_default_record(
    source_class: str,
    *,
    source_label: str,
    description: str,
    content_level: str,
    authority_required: str,
    default_access_decision: str,
    raw_access_allowed: bool = False,
    summary_access_allowed: bool = False,
    metadata_access_allowed: bool = False,
    private_data_possible: bool = False,
    cross_user_allowed: bool = False,
    cross_project_allowed: bool = False,
    cross_session_allowed: bool = False,
    temporal_filter_supported: bool = False,
    semantic_filter_supported: bool = False,
    event_anchor_supported: bool = False,
    commit_anchor_supported: bool = False,
    owner_authority_required: bool = False,
    operator_authority_required: bool = False,
    runtime_authority_required: bool = False,
    retention_sensitivity: str = "low",
    privacy_risk: str = "low",
    public_claim_risk: str = "low",
    safe_result_format: str = "metadata_summary",
    blocked_reason: str = "",
    required_redactions: Sequence[str] | None = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> MemorySourceScopeRecord:
    record = MemorySourceScopeRecord(
        source_scope_id=_build_source_scope_id(source_class, source_label, content_level, default_access_decision),
        source_class=source_class,
        source_label=_safe_text(source_label) or source_class,
        description=_safe_text(description),
        content_level=_safe_content_level(content_level),
        authority_required=_safe_authority(authority_required),
        default_access_decision=_safe_access_decision(default_access_decision),
        raw_access_allowed=bool(raw_access_allowed),
        summary_access_allowed=bool(summary_access_allowed),
        metadata_access_allowed=bool(metadata_access_allowed),
        private_data_possible=bool(private_data_possible),
        cross_user_allowed=bool(cross_user_allowed),
        cross_project_allowed=bool(cross_project_allowed),
        cross_session_allowed=bool(cross_session_allowed),
        temporal_filter_supported=bool(temporal_filter_supported),
        semantic_filter_supported=bool(semantic_filter_supported),
        event_anchor_supported=bool(event_anchor_supported),
        commit_anchor_supported=bool(commit_anchor_supported),
        owner_authority_required=bool(owner_authority_required),
        operator_authority_required=bool(operator_authority_required),
        runtime_authority_required=bool(runtime_authority_required),
        retention_sensitivity=_safe_text(retention_sensitivity) or "low",
        privacy_risk=_safe_text(privacy_risk) or "low",
        public_claim_risk=_safe_text(public_claim_risk) or "low",
        safe_result_format=_safe_result_format(safe_result_format),
        blocked_reason=_safe_text(blocked_reason),
        required_redactions=tuple(_dedupe_preserve(required_redactions or ())),
        safe_metadata=_safe_record_metadata(safe_metadata),
    )
    validate_memory_source_scope_record_v1(record)
    return record


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------


def build_memory_source_scope_record_v1(
    source_class: Any,
    source_label: Any = None,
    description: Any = None,
    content_level: Any = None,
    authority_required: Any = None,
    default_access_decision: Any = None,
    raw_access_allowed: bool = False,
    summary_access_allowed: bool = False,
    metadata_access_allowed: bool = False,
    private_data_possible: bool = False,
    cross_user_allowed: bool = False,
    cross_project_allowed: bool = False,
    cross_session_allowed: bool = False,
    temporal_filter_supported: bool = False,
    semantic_filter_supported: bool = False,
    event_anchor_supported: bool = False,
    commit_anchor_supported: bool = False,
    owner_authority_required: bool = False,
    operator_authority_required: bool = False,
    runtime_authority_required: bool = False,
    retention_sensitivity: Any = "low",
    privacy_risk: Any = "low",
    public_claim_risk: Any = "low",
    safe_result_format: Any = "metadata_summary",
    blocked_reason: Any = "",
    required_redactions: Sequence[str] | None = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> MemorySourceScopeRecord:
    return _build_default_record(
        _safe_text(source_class),
        source_label=_safe_text(source_label) or _safe_text(source_class),
        description=_safe_text(description),
        content_level=_safe_text(content_level),
        authority_required=_safe_text(authority_required),
        default_access_decision=_safe_text(default_access_decision),
        raw_access_allowed=bool(raw_access_allowed),
        summary_access_allowed=bool(summary_access_allowed),
        metadata_access_allowed=bool(metadata_access_allowed),
        private_data_possible=bool(private_data_possible),
        cross_user_allowed=bool(cross_user_allowed),
        cross_project_allowed=bool(cross_project_allowed),
        cross_session_allowed=bool(cross_session_allowed),
        temporal_filter_supported=bool(temporal_filter_supported),
        semantic_filter_supported=bool(semantic_filter_supported),
        event_anchor_supported=bool(event_anchor_supported),
        commit_anchor_supported=bool(commit_anchor_supported),
        owner_authority_required=bool(owner_authority_required),
        operator_authority_required=bool(operator_authority_required),
        runtime_authority_required=bool(runtime_authority_required),
        retention_sensitivity=_safe_text(retention_sensitivity),
        privacy_risk=_safe_text(privacy_risk),
        public_claim_risk=_safe_text(public_claim_risk),
        safe_result_format=_safe_text(safe_result_format),
        blocked_reason=_safe_text(blocked_reason),
        required_redactions=required_redactions,
        safe_metadata=safe_metadata,
    )



def build_memory_source_scope_registry_v1(
    records: Sequence[MemorySourceScopeRecord] | None = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> MemorySourceScopeRegistry:
    if records is None:
        records = _build_default_registry_records_v1()
    normalized = tuple(records)
    registry = MemorySourceScopeRegistry(
        registry_id=_build_registry_id(normalized),
        registry_type=MEMORY_SOURCE_SCOPE_REGISTRY_TYPE_V1,
        records=normalized,
        safe_metadata=_safe_record_metadata(safe_metadata),
    )
    validate_memory_source_scope_registry_v1(registry)
    return registry



def resolve_memory_source_scope_v1(
    retrieval_plan: Any,
    registry: Any = None,
    owner_authority: Any = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> MemorySourceScopeResolution:
    validate_temporal_memory_retrieval_plan_v1(retrieval_plan)
    plan_map = _maybe_mapping(retrieval_plan) or {}
    plan = retrieval_plan if isinstance(retrieval_plan, TemporalMemoryRetrievalPlan) else None
    if plan is None:
        plan = TemporalMemoryRetrievalPlan(
            retrieval_plan_id=_safe_text(plan_map.get("retrieval_plan_id")),
            source_time_anchor_id=_safe_text(plan_map.get("source_time_anchor_id")),
            original_phrase=_safe_text(plan_map.get("original_phrase")),
            anchor_type=_safe_text(plan_map.get("anchor_type")),
            resolved_start=plan_map.get("resolved_start") if plan_map.get("resolved_start") is None else _safe_text(plan_map.get("resolved_start")),
            resolved_end=plan_map.get("resolved_end") if plan_map.get("resolved_end") is None else _safe_text(plan_map.get("resolved_end")),
            timezone=_safe_text(plan_map.get("timezone")),
            retrieval_mode=_safe_text(plan_map.get("retrieval_mode")),
            semantic_query_present=bool(plan_map.get("semantic_query_present")),
            semantic_query_summary=_safe_text(plan_map.get("semantic_query_summary")),
            source_scope=_safe_text(plan_map.get("source_scope")),
            source_priority=tuple(plan_map.get("source_priority") or ()),
            project_scope_hint=_safe_text(plan_map.get("project_scope_hint")),
            session_scope_hint=_safe_text(plan_map.get("session_scope_hint")),
            event_anchor=_safe_text(plan_map.get("event_anchor")),
            commit_anchor=_safe_text(plan_map.get("commit_anchor")),
            candidate_source_classes=tuple(plan_map.get("candidate_source_classes") or ()),
            excluded_source_classes=tuple(plan_map.get("excluded_source_classes") or ()),
            authority_required=bool(plan_map.get("authority_required")),
            memory_read_authority_granted=bool(plan_map.get("memory_read_authority_granted")),
            source_access_granted=bool(plan_map.get("source_access_granted")),
            raw_log_access_allowed=bool(plan_map.get("raw_log_access_allowed")),
            private_data_access_allowed=bool(plan_map.get("private_data_access_allowed")),
            expected_confidence=_safe_text(plan_map.get("expected_confidence")),
            needs_clarification=bool(plan_map.get("needs_clarification")),
            clarification_question=_safe_text(plan_map.get("clarification_question")),
            ranking_strategy=_safe_text(plan_map.get("ranking_strategy")),
            result_constraints=tuple(plan_map.get("result_constraints") or ()),
            answer_boundary=tuple(plan_map.get("answer_boundary") or ()),
            failure_modes=tuple(plan_map.get("failure_modes") or ()),
            recommended_next_step=_safe_text(plan_map.get("recommended_next_step")),
            runtime_authority=bool(plan_map.get("runtime_authority")),
            writes_state=bool(plan_map.get("writes_state")),
            model_provider_used=bool(plan_map.get("model_provider_used")),
            public_claim_allowed=bool(plan_map.get("public_claim_allowed")),
            iss_internal_reference_allowed=bool(plan_map.get("iss_internal_reference_allowed")),
            learning_claimed=bool(plan_map.get("learning_claimed")),
            safe_metadata=plan_map.get("safe_metadata") if plan_map.get("safe_metadata") is None else dict(_json_safe(plan_map.get("safe_metadata"))),
        )

    records_map = _record_by_class(registry)
    candidate_source_classes = _plan_mode_candidate_sources(plan)
    if plan.candidate_source_classes:
        candidate_source_classes = tuple(_dedupe_preserve(plan.candidate_source_classes))
    if not candidate_source_classes and plan.retrieval_mode not in {"blocked_no_source", "blocked_no_authority"}:
        candidate_source_classes = _source_priority_for_mode(plan.retrieval_mode)

    owner_authority_level = _safe_authority(owner_authority)
    selected_source_priority = tuple(
        source for source in _source_priority_for_mode(plan.retrieval_mode) if source in records_map
    )
    if not selected_source_priority and candidate_source_classes:
        selected_source_priority = tuple(source for source in candidate_source_classes if source in records_map)

    allowed_sources: list[str] = []
    blocked_sources: list[str] = []
    requires_authority_sources: list[str] = []
    access_decisions: list[str] = []
    safe_result_format = "metadata_summary"
    clarification_required = bool(plan.retrieval_mode == "clarification_required")
    clarification_question = _clarification_question_for_mode(plan.retrieval_mode)
    authority_required = "no_authority"
    authority_missing = False
    redaction_required = False

    for source_class in selected_source_priority or candidate_source_classes:
        record = records_map.get(source_class)
        if record is None:
            blocked_sources.append(source_class)
            continue
        access_decisions.append(record.default_access_decision)
        if record.default_access_decision in {"allow_metadata_only", "allow_summary_only", "allow_redacted_summary"}:
            if record.default_access_decision == "allow_metadata_only":
                safe_result_format = "metadata_summary"
            elif record.default_access_decision == "allow_summary_only":
                safe_result_format = "redacted_summary" if record.private_data_possible else "metadata_summary"
            else:
                safe_result_format = "redacted_summary"
            allowed_sources.append(source_class)
            redaction_required = redaction_required or record.private_data_possible or record.content_level in {"redacted_summary", "private_state", "raw_log"}
            continue
        if record.default_access_decision in {"requires_owner_authority", "requires_operator_authority"}:
            requires_authority_sources.append(source_class)
            if not authority_required or authority_required == "no_authority":
                authority_required = record.authority_required
            authority_missing = True
            blocked_sources.append(source_class)
            continue
        if record.default_access_decision in {"blocked_by_default", "unknown_blocked"}:
            blocked_sources.append(source_class)
            authority_missing = True
            continue
        if record.default_access_decision == "clarification_required":
            clarification_required = True
            blocked_sources.append(source_class)
            continue
        blocked_sources.append(source_class)

    if plan.retrieval_mode == "blocked_no_source":
        allowed_sources = []
        blocked_sources = list(candidate_source_classes or records_map.keys())
        requires_authority_sources = []
        authority_required = "no_authority"
        authority_missing = False
        safe_result_format = "blocked_authority_required"
        clarification_required = False
        clarification_question = ""
        redaction_required = False
    elif plan.retrieval_mode == "blocked_no_authority":
        allowed_sources = []
        blocked_sources = list(candidate_source_classes or selected_source_priority)
        requires_authority_sources = list(candidate_source_classes or selected_source_priority)
        authority_required = "owner_content_authority"
        authority_missing = True
        safe_result_format = "blocked_authority_required"
        redaction_required = True
    elif plan.retrieval_mode == "clarification_required":
        safe_result_format = "clarification_needed"
        redaction_required = True
    elif not allowed_sources and not blocked_sources and candidate_source_classes:
        blocked_sources = list(candidate_source_classes)
        safe_result_format = "blocked_authority_required"
        authority_missing = True

    if plan.retrieval_mode == "session_order_retrieval" and "current_conversation" in allowed_sources:
        safe_result_format = "metadata_summary"
    elif plan.retrieval_mode == "event_anchor_retrieval" and allowed_sources:
        safe_result_format = "metadata_summary"
    elif plan.retrieval_mode in {"temporal_first", "hybrid_temporal_semantic"} and allowed_sources:
        safe_result_format = "redacted_summary" if redaction_required else "metadata_summary"

    if owner_authority_level == "operator_runtime_authority" and any(
        source in UNSAFE_DEFAULT_SOURCE_CLASSES_V1 for source in candidate_source_classes
    ):
        authority_missing = True

    resolution_safe_metadata = {
        "retrieval_mode": plan.retrieval_mode,
        "source_count": len(records_map),
        "allowed_source_count": len(allowed_sources),
        "blocked_source_count": len(blocked_sources),
        "authority_level": owner_authority_level,
        "source_scope": plan.source_scope,
    }
    if safe_metadata:
        resolution_safe_metadata.update({str(key): _json_safe(value) for key, value in safe_metadata.items()})

    resolution = MemorySourceScopeResolution(
        source_resolution_id=_deterministic_id(plan.retrieval_plan_id, candidate_source_classes, allowed_sources, blocked_sources),
        retrieval_plan_id=_safe_text(plan.retrieval_plan_id),
        candidate_sources=tuple(candidate_source_classes),
        allowed_sources=tuple(_dedupe_preserve(allowed_sources)),
        blocked_sources=tuple(_dedupe_preserve(blocked_sources)),
        requires_authority_sources=tuple(_dedupe_preserve(requires_authority_sources)),
        selected_source_priority=tuple(selected_source_priority),
        effective_access_decision=safe_result_format if safe_result_format in ALLOWED_ACCESS_DECISIONS_V1 else (
            "blocked_by_default" if plan.retrieval_mode == "blocked_no_source" else "requires_owner_authority" if authority_missing else "allow_metadata_only"
        ),
        authority_required=authority_required if authority_required in ALLOWED_AUTHORITY_LEVELS_V1 else "no_authority",
        authority_missing=authority_missing,
        clarification_required=clarification_required,
        clarification_question=clarification_question,
        safe_result_format=safe_result_format,
        redaction_required=redaction_required,
        raw_access_allowed=False,
        summary_access_allowed=bool(allowed_sources),
        metadata_access_allowed=bool(allowed_sources or blocked_sources),
        private_data_access_allowed=False,
        memory_read_authority_granted=False,
        source_access_granted=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        learning_claimed=False,
        safe_metadata={
            "retrieval_mode": plan.retrieval_mode,
            "source_count": len(records_map),
            "allowed_source_count": len(allowed_sources),
            "blocked_source_count": len(blocked_sources),
            "authority_level": owner_authority_level,
        },
    )
    validate_memory_source_scope_resolution_v1(resolution)
    return resolution


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_memory_source_scope_record_v1(record: Any) -> bool:
    if _contains_forbidden_fields(record):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_claim_marker(record):
        raise ValidationError("forbidden_public_or_claim_language_present")

    mapping = _record_to_mapping(record)
    allowed = {field.name for field in MemorySourceScopeRecord.__dataclass_fields__.values()}
    extra = set(str(key) for key in mapping.keys()) - allowed
    if extra:
        raise ValidationError("unknown_fields_present")

    raw_source_class = _safe_text(mapping.get("source_class"))
    raw_content_level = _safe_text(mapping.get("content_level"))
    raw_default_access_decision = _safe_text(mapping.get("default_access_decision"))
    raw_authority_required = _safe_text(mapping.get("authority_required"))
    raw_safe_result_format = _safe_text(mapping.get("safe_result_format"))

    if raw_source_class not in ALLOWED_SOURCE_CLASSES_V1:
        raise ValidationError("unknown_source_class")
    if raw_content_level not in ALLOWED_CONTENT_LEVELS_V1:
        raise ValidationError("unknown_content_level")
    if raw_default_access_decision not in ALLOWED_ACCESS_DECISIONS_V1:
        raise ValidationError("unknown_access_decision")
    if raw_authority_required not in ALLOWED_AUTHORITY_LEVELS_V1:
        raise ValidationError("unknown_authority_level")
    if raw_safe_result_format not in ALLOWED_SAFE_RESULT_FORMATS_V1:
        raise ValidationError("unknown_safe_result_format")

    normalized = _normalize_record_mapping(mapping)

    if normalized.cross_user_allowed:
        raise ValidationError("cross_user_allowed_must_be_false")
    if normalized.raw_access_allowed:
        raise ValidationError("raw_access_allowed_must_be_false")
    if normalized.private_data_possible and normalized.default_access_decision == "allow_metadata_only" and normalized.raw_access_allowed:
        raise ValidationError("private_data_requires_redaction_or_blocking")
    if normalized.runtime_authority_required and normalized.authority_required == "no_authority":
        raise ValidationError("runtime_authority_requires_authority_level")

    if normalized.source_class in UNSAFE_DEFAULT_SOURCE_CLASSES_V1:
        if normalized.default_access_decision not in {"blocked_by_default", "unknown_blocked"}:
            raise ValidationError("unsafe_default_source_must_be_blocked")
        if normalized.raw_access_allowed:
            raise ValidationError("unsafe_source_raw_access_not_allowed")
    if normalized.source_class == "unknown_source" and normalized.default_access_decision not in {"unknown_blocked", "clarification_required"}:
        raise ValidationError("unknown_source_must_be_blocked_or_clarification")

    if normalized.blocked_reason and normalized.default_access_decision not in {
        "blocked_by_default",
        "unknown_blocked",
        "clarification_required",
        "requires_owner_authority",
        "requires_operator_authority",
    }:
        raise ValidationError("blocked_reason_without_blocked_decision")

    return True



def validate_memory_source_scope_registry_v1(registry: Any) -> bool:
    if _contains_forbidden_fields(registry):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_claim_marker(registry):
        raise ValidationError("forbidden_public_or_claim_language_present")

    if is_dataclass(registry):
        mapping = asdict(registry)
    elif isinstance(registry, Mapping):
        mapping = dict(registry)
    else:
        raise ValidationError("unsupported_registry_type")

    allowed = {field.name for field in MemorySourceScopeRegistry.__dataclass_fields__.values()}
    extra = set(str(key) for key in mapping.keys()) - allowed
    if extra:
        raise ValidationError("unknown_fields_present")

    records = mapping.get("records", ())
    if isinstance(records, list):
        records = tuple(records)
    if not isinstance(records, tuple):
        raise ValidationError("records_must_be_sequence")
    normalized_records = []
    seen_classes: set[str] = set()
    seen_scope_ids: set[str] = set()
    for item in records:
        validate_memory_source_scope_record_v1(item)
        record = _normalize_record_mapping(_record_to_mapping(item))
        if record.source_class in seen_classes:
            raise ValidationError("duplicate_source_class")
        if record.source_scope_id in seen_scope_ids:
            raise ValidationError("duplicate_source_scope_id")
        seen_classes.add(record.source_class)
        seen_scope_ids.add(record.source_scope_id)
        normalized_records.append(record)

    registry_type = _safe_text(mapping.get("registry_type"))
    if registry_type != MEMORY_SOURCE_SCOPE_REGISTRY_TYPE_V1:
        raise ValidationError("unknown_registry_type")

    return True



def validate_memory_source_scope_resolution_v1(resolution: Any) -> bool:
    if _contains_forbidden_fields(resolution):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_claim_marker(resolution):
        raise ValidationError("forbidden_public_or_claim_language_present")

    mapping = _maybe_mapping(resolution)
    if mapping is None:
        raise ValidationError("unsupported_resolution_type")
    allowed = {field.name for field in MemorySourceScopeResolution.__dataclass_fields__.values()}
    extra = set(str(key) for key in mapping.keys()) - allowed
    if extra:
        raise ValidationError("unknown_fields_present")

    if mapping.get("raw_access_allowed"):
        raise ValidationError("raw_access_allowed_must_be_false")
    if mapping.get("private_data_access_allowed"):
        raise ValidationError("private_data_access_allowed_must_be_false")
    if mapping.get("memory_read_authority_granted"):
        raise ValidationError("memory_read_authority_granted_must_be_false")
    if mapping.get("source_access_granted"):
        raise ValidationError("source_access_granted_must_be_false")
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
    if _safe_text(mapping.get("safe_result_format")) not in ALLOWED_SAFE_RESULT_FORMATS_V1:
        raise ValidationError("unknown_safe_result_format")

    return True


# ---------------------------------------------------------------------------
# Summary and JSON safety
# ---------------------------------------------------------------------------


def summarize_memory_source_scope_registry_v1(registry: Any) -> MemorySourceScopeRegistrySummary:
    validate_memory_source_scope_registry_v1(registry)
    if not isinstance(registry, MemorySourceScopeRegistry):
        if isinstance(registry, Mapping):
            registry = MemorySourceScopeRegistry(
                registry_id=_safe_text(registry.get("registry_id")),
                registry_type=_safe_text(registry.get("registry_type")),
                records=tuple(registry.get("records") or ()),
                safe_metadata=registry.get("safe_metadata") if registry.get("safe_metadata") is None else dict(_json_safe(registry.get("safe_metadata"))),
            )
    records = registry.records
    source_classes = tuple(record.source_class for record in records)
    access_decisions = tuple(record.default_access_decision for record in records)
    blocked_source_classes = tuple(record.source_class for record in records if record.default_access_decision in {"blocked_by_default", "unknown_blocked"})
    authority_required_source_classes = tuple(record.source_class for record in records if record.default_access_decision in {"requires_owner_authority", "requires_operator_authority"})
    safe_result_formats = tuple(record.safe_result_format for record in records)
    return MemorySourceScopeRegistrySummary(
        summary_type=SUMMARY_TYPE_V1,
        registry_id=registry.registry_id,
        source_class_count=len(records),
        source_classes=source_classes,
        access_decisions=access_decisions,
        blocked_source_classes=blocked_source_classes,
        authority_required_source_classes=authority_required_source_classes,
        safe_result_formats=safe_result_formats,
        safe_metadata=registry.safe_metadata,
    )



def to_memory_source_scope_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


# ---------------------------------------------------------------------------
# Default registry and examples
# ---------------------------------------------------------------------------


def _build_default_registry_records_v1() -> tuple[MemorySourceScopeRecord, ...]:
    return (
        _build_default_record(
            "current_conversation",
            source_label="Current Conversation",
            description="Current-session owner-visible conversation context and summary metadata.",
            content_level="owner_visible_content",
            authority_required="no_authority",
            default_access_decision="allow_summary_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            private_data_possible=False,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            event_anchor_supported=False,
            commit_anchor_supported=False,
            owner_authority_required=False,
            operator_authority_required=False,
            runtime_authority_required=False,
            retention_sensitivity="medium",
            privacy_risk="low",
            public_claim_risk="low",
            safe_result_format="metadata_summary",
            required_redactions=(),
            safe_metadata={"policy": "summary_or_metadata_within_current_session"},
        ),
        _build_default_record(
            "prior_conversation_summary",
            source_label="Prior Conversation Summary",
            description="Owner-scoped prior conversation summaries for continuity.",
            content_level="summary_only",
            authority_required="no_authority",
            default_access_decision="allow_summary_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            private_data_possible=False,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            event_anchor_supported=False,
            commit_anchor_supported=False,
            retention_sensitivity="medium",
            privacy_risk="medium",
            public_claim_risk="low",
            safe_result_format="redacted_summary",
            required_redactions=("raw_transcript",),
            safe_metadata={"policy": "summary_only_if_scoped"},
        ),
        _build_default_record(
            "project_memory",
            source_label="Project Memory",
            description="Project-scoped memory and continuity metadata.",
            content_level="summary_only",
            authority_required="no_authority",
            default_access_decision="allow_summary_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            private_data_possible=False,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            event_anchor_supported=True,
            commit_anchor_supported=True,
            retention_sensitivity="medium",
            privacy_risk="medium",
            public_claim_risk="low",
            safe_result_format="redacted_summary",
            required_redactions=("raw_project_memory",),
            safe_metadata={"policy": "project_scoped_summary_only"},
        ),
        _build_default_record(
            "repo_commit_metadata",
            source_label="Repo Commit Metadata",
            description="Commit hashes, timestamps, and repository metadata only.",
            content_level="metadata_only",
            authority_required="metadata_authority",
            default_access_decision="allow_metadata_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            private_data_possible=False,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=False,
            event_anchor_supported=True,
            commit_anchor_supported=True,
            retention_sensitivity="low",
            privacy_risk="low",
            public_claim_risk="low",
            safe_result_format="metadata_summary",
            required_redactions=(),
            safe_metadata={"policy": "metadata_only_commit_anchor_support"},
        ),
        _build_default_record(
            "lane_report_metadata",
            source_label="Lane Report Metadata",
            description="Lane and report metadata with optional summary context.",
            content_level="summary_only",
            authority_required="summary_authority",
            default_access_decision="allow_summary_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            private_data_possible=False,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            event_anchor_supported=True,
            commit_anchor_supported=True,
            retention_sensitivity="low",
            privacy_risk="low",
            public_claim_risk="low",
            safe_result_format="metadata_summary",
            required_redactions=(),
            safe_metadata={"policy": "event_anchor_metadata"},
        ),
        _build_default_record(
            "uploaded_file_reference",
            source_label="Uploaded File Reference",
            description="File references and metadata; raw file access requires explicit authority.",
            content_level="metadata_only",
            authority_required="owner_content_authority",
            default_access_decision="requires_owner_authority",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            private_data_possible=True,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            event_anchor_supported=True,
            commit_anchor_supported=False,
            owner_authority_required=True,
            retention_sensitivity="high",
            privacy_risk="high",
            public_claim_risk="low",
            safe_result_format="source_reference_only",
            blocked_reason="raw_file_access_requires_explicit_authority",
            required_redactions=("raw_file_contents",),
            safe_metadata={"policy": "reference_metadata_until_authorized"},
        ),
        _build_default_record(
            "approved_memory_index",
            source_label="Approved Memory Index",
            description="Approved memory index entries and summary metadata only.",
            content_level="summary_only",
            authority_required="summary_authority",
            default_access_decision="allow_summary_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            private_data_possible=False,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            event_anchor_supported=True,
            commit_anchor_supported=True,
            retention_sensitivity="medium",
            privacy_risk="medium",
            public_claim_risk="low",
            safe_result_format="redacted_summary",
            required_redactions=("raw_memory_entries",),
            safe_metadata={"policy": "approved_summary_index"},
        ),
        _build_default_record(
            "runtime_session_log",
            source_label="Runtime Session Log",
            description="Runtime session logs; raw access blocked by default.",
            content_level="raw_log",
            authority_required="operator_runtime_authority",
            default_access_decision="blocked_by_default",
            raw_access_allowed=False,
            summary_access_allowed=False,
            metadata_access_allowed=True,
            private_data_possible=True,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=False,
            temporal_filter_supported=True,
            semantic_filter_supported=False,
            event_anchor_supported=False,
            commit_anchor_supported=False,
            operator_authority_required=True,
            runtime_authority_required=True,
            retention_sensitivity="high",
            privacy_risk="high",
            public_claim_risk="medium",
            safe_result_format="blocked_authority_required",
            blocked_reason="raw_log_access_not_allowed_by_default",
            required_redactions=("runtime_log_entries", "private_fields"),
            safe_metadata={"policy": "blocked_by_default"},
        ),
        _build_default_record(
            ".weslr_state",
            source_label="WESLR State",
            description="Private state file; blocked by default.",
            content_level="private_state",
            authority_required="private_state_authority",
            default_access_decision="blocked_by_default",
            raw_access_allowed=False,
            summary_access_allowed=False,
            metadata_access_allowed=True,
            private_data_possible=True,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=False,
            temporal_filter_supported=False,
            semantic_filter_supported=False,
            event_anchor_supported=False,
            commit_anchor_supported=False,
            owner_authority_required=True,
            operator_authority_required=True,
            runtime_authority_required=True,
            retention_sensitivity="high",
            privacy_risk="high",
            public_claim_risk="high",
            safe_result_format="blocked_authority_required",
            blocked_reason="private_state_not_read_implicitly",
            required_redactions=("private_state",),
            safe_metadata={"policy": "blocked_by_default"},
        ),
        _build_default_record(
            "unknown_source",
            source_label="Unknown Source",
            description="Unknown source class; blocked or clarification required.",
            content_level="unknown_content",
            authority_required="no_authority",
            default_access_decision="unknown_blocked",
            raw_access_allowed=False,
            summary_access_allowed=False,
            metadata_access_allowed=False,
            private_data_possible=False,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=False,
            temporal_filter_supported=False,
            semantic_filter_supported=False,
            event_anchor_supported=False,
            commit_anchor_supported=False,
            retention_sensitivity="unknown",
            privacy_risk="high",
            public_claim_risk="high",
            safe_result_format="blocked_authority_required",
            blocked_reason="unknown_source_class",
            required_redactions=("unknown_source",),
            safe_metadata={"policy": "unknown_blocked"},
        ),
        _build_default_record(
            "artifact_manifest_metadata",
            source_label="Artifact Manifest Metadata",
            description="Artifact manifest hashes and metadata.",
            content_level="metadata_only",
            authority_required="metadata_authority",
            default_access_decision="allow_metadata_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            private_data_possible=False,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            event_anchor_supported=True,
            commit_anchor_supported=True,
            retention_sensitivity="low",
            privacy_risk="low",
            public_claim_risk="low",
            safe_result_format="metadata_summary",
            safe_metadata={"policy": "artifact_provenance_metadata"},
        ),
        _build_default_record(
            "artifact_validation_report",
            source_label="Artifact Validation Report",
            description="Validation report metadata and summaries.",
            content_level="summary_only",
            authority_required="summary_authority",
            default_access_decision="allow_summary_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            private_data_possible=False,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            event_anchor_supported=True,
            commit_anchor_supported=True,
            retention_sensitivity="low",
            privacy_risk="low",
            public_claim_risk="low",
            safe_result_format="metadata_summary",
            safe_metadata={"policy": "validation_report_summary"},
        ),
        _build_default_record(
            "behavior_pack_registry",
            source_label="Behavior Pack Registry",
            description="Behavior pack registry metadata for provenance and lineage.",
            content_level="metadata_only",
            authority_required="metadata_authority",
            default_access_decision="allow_metadata_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            private_data_possible=False,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            event_anchor_supported=True,
            commit_anchor_supported=True,
            retention_sensitivity="low",
            privacy_risk="low",
            public_claim_risk="low",
            safe_result_format="metadata_summary",
            safe_metadata={"policy": "behavior_pack_lineage"},
        ),
        _build_default_record(
            "friction_case_registry",
            source_label="Friction Case Registry",
            description="Friction cases and summary metadata for continuity learning.",
            content_level="summary_only",
            authority_required="summary_authority",
            default_access_decision="allow_summary_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            private_data_possible=False,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            event_anchor_supported=True,
            commit_anchor_supported=True,
            retention_sensitivity="medium",
            privacy_risk="medium",
            public_claim_risk="low",
            safe_result_format="redacted_summary",
            required_redactions=("raw_case_text",),
            safe_metadata={"policy": "friction_summary_only"},
        ),
        _build_default_record(
            "owner_approved_summary",
            source_label="Owner Approved Summary",
            description="Owner-approved summary metadata for continuity and safe reuse.",
            content_level="summary_only",
            authority_required="summary_authority",
            default_access_decision="allow_summary_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            private_data_possible=False,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            event_anchor_supported=True,
            commit_anchor_supported=True,
            retention_sensitivity="medium",
            privacy_risk="medium",
            public_claim_risk="low",
            safe_result_format="redacted_summary",
            required_redactions=("raw_owner_notes",),
            safe_metadata={"policy": "owner_approved_summary"},
        ),
        _build_default_record(
            "external_connector_reference",
            source_label="External Connector Reference",
            description="External connector reference metadata only.",
            content_level="metadata_only",
            authority_required="metadata_authority",
            default_access_decision="allow_metadata_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            private_data_possible=False,
            cross_user_allowed=False,
            cross_project_allowed=False,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            event_anchor_supported=True,
            commit_anchor_supported=True,
            retention_sensitivity="low",
            privacy_risk="low",
            public_claim_risk="low",
            safe_result_format="source_reference_only",
            safe_metadata={"policy": "connector_reference_only"},
        ),
    )



def build_initial_memory_source_scope_examples_v1() -> tuple[Any, ...]:
    registry = build_memory_source_scope_registry_v1()
    examples: list[Any] = [
        build_memory_source_scope_record_v1(
            "current_conversation",
            source_label="Current Conversation Scope Record",
            description="Example record for current conversation scope.",
            content_level="owner_visible_content",
            authority_required="no_authority",
            default_access_decision="allow_summary_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            safe_result_format="metadata_summary",
            safe_metadata={"example_name": "current_conversation_scope_record"},
        ),
        build_memory_source_scope_record_v1(
            "prior_conversation_summary",
            source_label="Prior Conversation Summary Scope Record",
            description="Example record for prior conversation summaries.",
            content_level="summary_only",
            authority_required="no_authority",
            default_access_decision="allow_summary_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            cross_session_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            safe_result_format="redacted_summary",
            safe_metadata={"example_name": "prior_conversation_summary_scope_record"},
        ),
        build_memory_source_scope_record_v1(
            "project_memory",
            source_label="Project Memory Scope Record",
            description="Example record for project memory scope.",
            content_level="summary_only",
            authority_required="no_authority",
            default_access_decision="allow_summary_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            cross_project_allowed=False,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            event_anchor_supported=True,
            commit_anchor_supported=True,
            safe_result_format="redacted_summary",
            safe_metadata={"example_name": "project_memory_scope_record"},
        ),
        build_memory_source_scope_record_v1(
            "repo_commit_metadata",
            source_label="Repo Commit Metadata Scope Record",
            description="Example record for repository commit metadata.",
            content_level="metadata_only",
            authority_required="metadata_authority",
            default_access_decision="allow_metadata_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            temporal_filter_supported=True,
            event_anchor_supported=True,
            commit_anchor_supported=True,
            safe_result_format="metadata_summary",
            safe_metadata={"example_name": "repo_commit_metadata_scope_record"},
        ),
        build_memory_source_scope_record_v1(
            "lane_report_metadata",
            source_label="Lane Report Metadata Scope Record",
            description="Example record for lane report metadata.",
            content_level="summary_only",
            authority_required="summary_authority",
            default_access_decision="allow_summary_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            temporal_filter_supported=True,
            event_anchor_supported=True,
            commit_anchor_supported=True,
            safe_result_format="metadata_summary",
            safe_metadata={"example_name": "lane_report_metadata_scope_record"},
        ),
        build_memory_source_scope_record_v1(
            "uploaded_file_reference",
            source_label="Uploaded File Reference Scope Record",
            description="Example record for uploaded file references.",
            content_level="metadata_only",
            authority_required="owner_content_authority",
            default_access_decision="requires_owner_authority",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            private_data_possible=True,
            safe_result_format="source_reference_only",
            blocked_reason="explicit_file_source_authority_required",
            safe_metadata={"example_name": "uploaded_file_reference_scope_record"},
        ),
        build_memory_source_scope_record_v1(
            "approved_memory_index",
            source_label="Approved Memory Index Scope Record",
            description="Example record for approved memory index.",
            content_level="summary_only",
            authority_required="summary_authority",
            default_access_decision="allow_summary_only",
            raw_access_allowed=False,
            summary_access_allowed=True,
            metadata_access_allowed=True,
            temporal_filter_supported=True,
            semantic_filter_supported=True,
            safe_result_format="redacted_summary",
            safe_metadata={"example_name": "approved_memory_index_scope_record"},
        ),
        build_memory_source_scope_record_v1(
            "runtime_session_log",
            source_label="Runtime Session Log Scope Record",
            description="Example record for runtime session logs.",
            content_level="raw_log",
            authority_required="operator_runtime_authority",
            default_access_decision="blocked_by_default",
            raw_access_allowed=False,
            summary_access_allowed=False,
            metadata_access_allowed=True,
            private_data_possible=True,
            operator_authority_required=True,
            runtime_authority_required=True,
            safe_result_format="blocked_authority_required",
            blocked_reason="blocked_by_default",
            safe_metadata={"example_name": "runtime_session_log_scope_record"},
        ),
        build_memory_source_scope_record_v1(
            ".weslr_state",
            source_label="WESLR State Scope Record",
            description="Example record for WESLR private state.",
            content_level="private_state",
            authority_required="private_state_authority",
            default_access_decision="blocked_by_default",
            raw_access_allowed=False,
            summary_access_allowed=False,
            metadata_access_allowed=True,
            private_data_possible=True,
            owner_authority_required=True,
            operator_authority_required=True,
            runtime_authority_required=True,
            safe_result_format="blocked_authority_required",
            blocked_reason="blocked_by_default",
            safe_metadata={"example_name": "weslr_state_scope_record"},
        ),
        build_memory_source_scope_record_v1(
            "unknown_source",
            source_label="Unknown Source Scope Record",
            description="Example record for unknown source handling.",
            content_level="unknown_content",
            authority_required="no_authority",
            default_access_decision="unknown_blocked",
            raw_access_allowed=False,
            summary_access_allowed=False,
            metadata_access_allowed=False,
            safe_result_format="blocked_authority_required",
            blocked_reason="unknown_source_class",
            safe_metadata={"example_name": "unknown_source_scope_record"},
        ),
        build_memory_source_scope_resolution_v1(
            build_temporal_memory_retrieval_plan_v1(
                "yesterday",
                reference_time="2026-06-01T12:00:00",
                timezone="Europe/Berlin",
                available_sources=("approved_memory_index", "prior_conversation_summary", "project_memory"),
            ),
            registry=registry,
            safe_metadata={"example_name": "yesterday_temporal_source_resolution"},
        ),
    ]

    examples.append(
        build_memory_source_scope_resolution_v1(
            build_temporal_memory_retrieval_plan_v1(
                "earlier in this chat",
                reference_time="2026-06-01T12:00:00",
                timezone="Europe/Berlin",
                available_sources=("current_conversation", "prior_conversation_summary"),
            ),
            registry=registry,
            safe_metadata={"example_name": "earlier_chat_source_resolution"},
        )
    )
    examples.append(
        build_memory_source_scope_resolution_v1(
            build_temporal_memory_retrieval_plan_v1(
                "before the file manifest builder",
                reference_time="2026-06-01T12:00:00",
                timezone="Europe/Berlin",
                event_anchor="file_manifest_builder",
                commit_anchor="last_commit",
                available_sources=("lane_report_metadata", "repo_commit_metadata", "project_memory"),
            ),
            registry=registry,
            safe_metadata={"example_name": "before_file_manifest_source_resolution"},
        )
    )
    examples.append(
        build_memory_source_scope_resolution_v1(
            build_temporal_memory_retrieval_plan_v1(
                "yesterday",
                reference_time="2026-06-01T12:00:00",
                timezone="Europe/Berlin",
                available_sources=(),
            ),
            registry=registry,
            safe_metadata={"example_name": "runtime_log_blocked_resolution"},
        )
    )
    examples.append(
        build_memory_source_scope_resolution_v1(
            build_temporal_memory_retrieval_plan_v1(
                "before the last commit",
                reference_time="2026-06-01T12:00:00",
                timezone="Europe/Berlin",
                available_sources=("runtime_session_log", ".weslr_state"),
            ),
            registry=registry,
            safe_metadata={"example_name": "weslr_state_blocked_resolution"},
        )
    )
    return tuple(examples)


# ---------------------------------------------------------------------------
# Alias functions for decision packets
# ---------------------------------------------------------------------------


def build_memory_source_scope_resolution_v1(
    retrieval_plan: Any,
    registry: Any = None,
    owner_authority: Any = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> MemorySourceScopeResolution:
    return resolve_memory_source_scope_v1(
        retrieval_plan,
        registry=registry,
        owner_authority=owner_authority,
        safe_metadata=safe_metadata,
    )



def resolve_memory_source_scope_v1(
    retrieval_plan: Any,
    registry: Any = None,
    owner_authority: Any = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> MemorySourceScopeResolution:
    validate_temporal_memory_retrieval_plan_v1(retrieval_plan)
    plan_map = _maybe_mapping(retrieval_plan) or {}
    plan = retrieval_plan if isinstance(retrieval_plan, TemporalMemoryRetrievalPlan) else None
    if plan is None:
        plan = TemporalMemoryRetrievalPlan(
            retrieval_plan_id=_safe_text(plan_map.get("retrieval_plan_id")),
            source_time_anchor_id=_safe_text(plan_map.get("source_time_anchor_id")),
            original_phrase=_safe_text(plan_map.get("original_phrase")),
            anchor_type=_safe_text(plan_map.get("anchor_type")),
            resolved_start=plan_map.get("resolved_start") if plan_map.get("resolved_start") is None else _safe_text(plan_map.get("resolved_start")),
            resolved_end=plan_map.get("resolved_end") if plan_map.get("resolved_end") is None else _safe_text(plan_map.get("resolved_end")),
            timezone=_safe_text(plan_map.get("timezone")),
            retrieval_mode=_safe_text(plan_map.get("retrieval_mode")),
            semantic_query_present=bool(plan_map.get("semantic_query_present")),
            semantic_query_summary=_safe_text(plan_map.get("semantic_query_summary")),
            source_scope=_safe_text(plan_map.get("source_scope")),
            source_priority=tuple(plan_map.get("source_priority") or ()),
            project_scope_hint=_safe_text(plan_map.get("project_scope_hint")),
            session_scope_hint=_safe_text(plan_map.get("session_scope_hint")),
            event_anchor=_safe_text(plan_map.get("event_anchor")),
            commit_anchor=_safe_text(plan_map.get("commit_anchor")),
            candidate_source_classes=tuple(plan_map.get("candidate_source_classes") or ()),
            excluded_source_classes=tuple(plan_map.get("excluded_source_classes") or ()),
            authority_required=bool(plan_map.get("authority_required")),
            memory_read_authority_granted=bool(plan_map.get("memory_read_authority_granted")),
            source_access_granted=bool(plan_map.get("source_access_granted")),
            raw_log_access_allowed=bool(plan_map.get("raw_log_access_allowed")),
            private_data_access_allowed=bool(plan_map.get("private_data_access_allowed")),
            expected_confidence=_safe_text(plan_map.get("expected_confidence")),
            needs_clarification=bool(plan_map.get("needs_clarification")),
            clarification_question=_safe_text(plan_map.get("clarification_question")),
            ranking_strategy=_safe_text(plan_map.get("ranking_strategy")),
            result_constraints=tuple(plan_map.get("result_constraints") or ()),
            answer_boundary=tuple(plan_map.get("answer_boundary") or ()),
            failure_modes=tuple(plan_map.get("failure_modes") or ()),
            recommended_next_step=_safe_text(plan_map.get("recommended_next_step")),
            runtime_authority=bool(plan_map.get("runtime_authority")),
            writes_state=bool(plan_map.get("writes_state")),
            model_provider_used=bool(plan_map.get("model_provider_used")),
            public_claim_allowed=bool(plan_map.get("public_claim_allowed")),
            iss_internal_reference_allowed=bool(plan_map.get("iss_internal_reference_allowed")),
            learning_claimed=bool(plan_map.get("learning_claimed")),
            safe_metadata=plan_map.get("safe_metadata") if plan_map.get("safe_metadata") is None else dict(_json_safe(plan_map.get("safe_metadata"))),
        )

    records_map = _record_by_class(registry)
    candidate_source_classes = _plan_mode_candidate_sources(plan)
    if plan.candidate_source_classes:
        candidate_source_classes = tuple(_dedupe_preserve(plan.candidate_source_classes))
    if not candidate_source_classes and plan.retrieval_mode not in {"blocked_no_source", "blocked_no_authority"}:
        candidate_source_classes = _source_priority_for_mode(plan.retrieval_mode)

    owner_authority_level = _safe_authority(owner_authority)
    selected_source_priority = tuple(
        source for source in _source_priority_for_mode(plan.retrieval_mode) if source in records_map
    )
    if not selected_source_priority and candidate_source_classes:
        selected_source_priority = tuple(source for source in candidate_source_classes if source in records_map)

    allowed_sources: list[str] = []
    blocked_sources: list[str] = []
    requires_authority_sources: list[str] = []
    safe_result_format = "metadata_summary"
    clarification_required = bool(plan.retrieval_mode == "clarification_required")
    clarification_question = _clarification_question_for_mode(plan.retrieval_mode)
    authority_required = "no_authority"
    authority_missing = False
    redaction_required = False

    for source_class in selected_source_priority or candidate_source_classes:
        record = records_map.get(source_class)
        if record is None:
            blocked_sources.append(source_class)
            continue
        if record.default_access_decision in {"allow_metadata_only", "allow_summary_only", "allow_redacted_summary"}:
            allowed_sources.append(source_class)
            if record.default_access_decision == "allow_metadata_only":
                safe_result_format = "metadata_summary"
            elif record.default_access_decision == "allow_summary_only":
                safe_result_format = "redacted_summary" if record.private_data_possible else "metadata_summary"
            else:
                safe_result_format = "redacted_summary"
            redaction_required = redaction_required or record.private_data_possible or record.content_level in {"redacted_summary", "private_state", "raw_log"}
            continue
        if record.default_access_decision in {"requires_owner_authority", "requires_operator_authority"}:
            requires_authority_sources.append(source_class)
            if authority_required == "no_authority":
                authority_required = record.authority_required
            authority_missing = True
            blocked_sources.append(source_class)
            continue
        if record.default_access_decision in {"blocked_by_default", "unknown_blocked"}:
            blocked_sources.append(source_class)
            authority_missing = True
            continue
        if record.default_access_decision == "clarification_required":
            clarification_required = True
            blocked_sources.append(source_class)
            continue
        blocked_sources.append(source_class)

    if plan.retrieval_mode == "blocked_no_source":
        allowed_sources = []
        blocked_sources = list(candidate_source_classes or records_map.keys())
        requires_authority_sources = []
        authority_required = "no_authority"
        authority_missing = False
        safe_result_format = "blocked_authority_required"
        clarification_required = False
        clarification_question = ""
        redaction_required = False
    elif plan.retrieval_mode == "blocked_no_authority":
        allowed_sources = []
        blocked_sources = list(candidate_source_classes or selected_source_priority)
        requires_authority_sources = list(candidate_source_classes or selected_source_priority)
        authority_required = "owner_content_authority"
        authority_missing = True
        safe_result_format = "blocked_authority_required"
        redaction_required = True
    elif plan.retrieval_mode == "clarification_required":
        safe_result_format = "clarification_needed"
        redaction_required = True
    elif not allowed_sources and not blocked_sources and candidate_source_classes:
        blocked_sources = list(candidate_source_classes)
        safe_result_format = "blocked_authority_required"
        authority_missing = True

    if plan.retrieval_mode == "session_order_retrieval" and "current_conversation" in allowed_sources:
        safe_result_format = "metadata_summary"
    elif plan.retrieval_mode == "event_anchor_retrieval" and allowed_sources:
        safe_result_format = "metadata_summary"
    elif plan.retrieval_mode in {"temporal_first", "hybrid_temporal_semantic"} and allowed_sources:
        safe_result_format = "redacted_summary" if redaction_required else "metadata_summary"

    if owner_authority_level == "operator_runtime_authority" and any(source in UNSAFE_DEFAULT_SOURCE_CLASSES_V1 for source in candidate_source_classes):
        authority_missing = True

    resolution_safe_metadata = {
        "retrieval_mode": plan.retrieval_mode,
        "source_count": len(records_map),
        "allowed_source_count": len(allowed_sources),
        "blocked_source_count": len(blocked_sources),
        "authority_level": owner_authority_level,
        "source_scope": plan.source_scope,
    }
    if safe_metadata:
        resolution_safe_metadata.update({str(key): _json_safe(value) for key, value in safe_metadata.items()})

    resolution = MemorySourceScopeResolution(
        source_resolution_id=_deterministic_id(plan.retrieval_plan_id, candidate_source_classes, allowed_sources, blocked_sources),
        retrieval_plan_id=_safe_text(plan.retrieval_plan_id),
        candidate_sources=tuple(candidate_source_classes),
        allowed_sources=tuple(_dedupe_preserve(allowed_sources)),
        blocked_sources=tuple(_dedupe_preserve(blocked_sources)),
        requires_authority_sources=tuple(_dedupe_preserve(requires_authority_sources)),
        selected_source_priority=tuple(selected_source_priority),
        effective_access_decision=(
            "blocked_by_default"
            if plan.retrieval_mode == "blocked_no_source"
            else "requires_owner_authority"
            if authority_missing and requires_authority_sources
            else "clarification_required"
            if clarification_required
            else "allow_redacted_summary"
            if safe_result_format == "redacted_summary"
            else "allow_summary_only"
            if safe_result_format in {"metadata_summary", "owner_visible_excerpt", "source_reference_only"}
            else "blocked_by_default"
        ),
        authority_required=authority_required if authority_required in ALLOWED_AUTHORITY_LEVELS_V1 else "no_authority",
        authority_missing=authority_missing,
        clarification_required=clarification_required,
        clarification_question=clarification_question,
        safe_result_format=safe_result_format,
        redaction_required=redaction_required,
        raw_access_allowed=False,
        summary_access_allowed=bool(allowed_sources),
        metadata_access_allowed=bool(allowed_sources or blocked_sources),
        private_data_access_allowed=False,
        memory_read_authority_granted=False,
        source_access_granted=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        learning_claimed=False,
        safe_metadata=resolution_safe_metadata,
    )
    validate_memory_source_scope_resolution_v1(resolution)
    return resolution


__all__ = [
    "HELPER_TYPE_V1",
    "MEMORY_SOURCE_SCOPE_RECORD_TYPE_V1",
    "MEMORY_SOURCE_SCOPE_REGISTRY_TYPE_V1",
    "SOURCE_RESOLUTION_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "MemorySourceScopeRecord",
    "MemorySourceScopeRegistry",
    "MemorySourceScopeResolution",
    "MemorySourceScopeRegistrySummary",
    "ValidationError",
    "build_memory_source_scope_record_v1",
    "build_memory_source_scope_registry_v1",
    "build_memory_source_scope_resolution_v1",
    "resolve_memory_source_scope_v1",
    "validate_memory_source_scope_record_v1",
    "validate_memory_source_scope_registry_v1",
    "validate_memory_source_scope_resolution_v1",
    "summarize_memory_source_scope_registry_v1",
    "to_memory_source_scope_json_safe_v1",
    "build_initial_memory_source_scope_examples_v1",
]
