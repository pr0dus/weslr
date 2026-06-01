"""Metadata-only temporal memory retrieval plan v1.

This module turns a resolved time-anchor packet into a safe planning artifact
for future memory retrieval. It does not retrieve memory, read logs, access
`.weslr`, call providers/models/search/advisors, or route chat.

It is pure, deterministic, import-safe, and fail-closed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import hashlib
import re
from typing import Any, Iterable, Mapping, Sequence

from weslr.time_anchor_resolver import (
    TimeAnchorPacket,
    build_time_anchor_packet_v1,
    resolve_time_anchor_v1,
    validate_time_anchor_packet_v1,
)

HELPER_TYPE_V1 = "temporal_memory_retrieval_plan_v1"
TEMPORAL_MEMORY_RETRIEVAL_PLAN_TYPE_V1 = "temporal_memory_retrieval_plan_v1"
SUMMARY_TYPE_V1 = "temporal_memory_retrieval_plan_summary_v1"

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
}

ALLOWED_RANKING_STRATEGIES_V1 = {
    "time_window_exact",
    "time_window_then_semantic",
    "semantic_then_time_boost",
    "session_order_nearest",
    "event_anchor_before_after",
    "commit_order_before_after",
    "manual_owner_clarification",
}

ALLOWED_EXPECTED_CONFIDENCE_VALUES_V1 = {
    "high",
    "medium",
    "low",
    "unresolved",
    "blocked",
}

ALLOWED_NEXT_STEPS_V1 = {
    "request_memory_authority",
    "request_source_authority",
    "ask_clarifying_question",
    "execute_safe_retrieval_later",
    "blocked_wait_for_source",
    "blocked_wait_for_owner",
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

VAGUE_TEMPORAL_PHRASES_V1 = {
    "recently",
    "lately",
    "the other day",
    "a while ago",
    "some time ago",
}

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

PROJECT_EVENT_PRIORITY_V1 = (
    "lane_report_metadata",
    "repo_commit_metadata",
    "project_memory",
    "approved_memory_index",
    "prior_conversation_summary",
)

TEMPORAL_PRIORITY_V1 = (
    "approved_memory_index",
    "prior_conversation_summary",
    "project_memory",
    "repo_commit_metadata",
    "lane_report_metadata",
    "uploaded_file_reference",
    "current_conversation",
    "unknown_source",
)

SESSION_PRIORITY_V1 = (
    "current_conversation",
    "prior_conversation_summary",
    "runtime_session_log",
    "approved_memory_index",
    "project_memory",
    "unknown_source",
)

SEMANTIC_PRIORITY_V1 = (
    "project_memory",
    "prior_conversation_summary",
    "approved_memory_index",
    "uploaded_file_reference",
    "current_conversation",
    "unknown_source",
)

CLARIFICATION_PRIORITY_V1 = (
    "current_conversation",
    "prior_conversation_summary",
    "unknown_source",
)

UNSAFE_AUTHORITY_SOURCES_V1 = {
    "runtime_session_log",
    ".weslr_state",
}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TemporalMemoryRetrievalPlan:
    retrieval_plan_id: str
    source_time_anchor_id: str
    original_phrase: str
    anchor_type: str
    resolved_start: str | None
    resolved_end: str | None
    timezone: str
    retrieval_mode: str
    semantic_query_present: bool
    semantic_query_summary: str
    source_scope: str
    source_priority: tuple[str, ...]
    project_scope_hint: str
    session_scope_hint: str
    event_anchor: str
    commit_anchor: str
    candidate_source_classes: tuple[str, ...]
    excluded_source_classes: tuple[str, ...]
    authority_required: bool
    memory_read_authority_granted: bool
    source_access_granted: bool
    raw_log_access_allowed: bool
    private_data_access_allowed: bool
    expected_confidence: str
    needs_clarification: bool
    clarification_question: str
    ranking_strategy: str
    result_constraints: tuple[str, ...]
    answer_boundary: tuple[str, ...]
    failure_modes: tuple[str, ...]
    recommended_next_step: str
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    iss_internal_reference_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class TemporalMemoryRetrievalSummary:
    summary_type: str
    retrieval_plan_id: str
    retrieval_mode: str
    source_scope: str
    expected_confidence: str
    needs_clarification: bool
    recommended_next_step: str


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
            key_text = _normalize_text(key)
            if key_text in FORBIDDEN_FIELD_NAMES_V1:
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



def _unique_allowed_sources(source_list: Any) -> tuple[str, ...]:
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



def _summary_for_semantic_query(semantic_query: Any) -> str:
    text = _safe_text(semantic_query)
    if not text:
        return ""
    text = " ".join(text.split())
    if len(text) <= 72:
        return text
    return text[:69].rstrip() + "..."



def _deterministic_id(*parts: Any) -> str:
    payload = "|".join(_normalize_text(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"tmrp_{digest}"



def _select_mode(anchor: TimeAnchorPacket, semantic_query_present: bool, available_sources: tuple[str, ...]) -> str:
    phrase = _normalize_text(anchor.original_phrase)
    anchor_type = _normalize_text(anchor.anchor_type)

    if not available_sources:
        return "blocked_no_source"

    if available_sources and all(source in UNSAFE_AUTHORITY_SOURCES_V1 for source in available_sources):
        return "blocked_no_authority"

    if anchor_type == "unresolved":
        return "clarification_required"

    if anchor_type == "vague_temporal" or phrase in VAGUE_TEMPORAL_PHRASES_V1:
        return "clarification_required"

    if anchor_type == "session_relative":
        return "session_order_retrieval"

    if anchor_type in {"project_relative", "event_relative"}:
        return "event_anchor_retrieval"

    if semantic_query_present:
        return "hybrid_temporal_semantic"

    if anchor_type in {"relative_day", "relative_range", "day_part", "absolute_date"}:
        return "temporal_first"

    return "temporal_first"



def _priority_for_mode(mode: str) -> tuple[str, ...]:
    if mode == "session_order_retrieval":
        return SESSION_PRIORITY_V1
    if mode == "event_anchor_retrieval":
        return PROJECT_EVENT_PRIORITY_V1
    if mode == "clarification_required":
        return CLARIFICATION_PRIORITY_V1
    if mode == "semantic_first":
        return SEMANTIC_PRIORITY_V1
    return TEMPORAL_PRIORITY_V1



def _candidate_sources_for_mode(mode: str, available_sources: tuple[str, ...]) -> tuple[str, ...]:
    if mode == "blocked_no_source":
        return tuple()

    if available_sources:
        preferred = [source for source in _priority_for_mode(mode) if source in available_sources]
        if preferred:
            return tuple(preferred)
        return tuple(available_sources)

    return _priority_for_mode(mode)



def _excluded_sources(candidate_sources: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(source for source in ALLOWED_SOURCE_CLASSES_V1 if source not in set(candidate_sources))



def _source_scope_for_mode(mode: str, candidate_sources: tuple[str, ...]) -> str:
    if candidate_sources:
        return candidate_sources[0]
    if mode == "blocked_no_source":
        return "unknown_source"
    if mode == "blocked_no_authority":
        return "runtime_session_log"
    return "unknown_source"



def _ranking_strategy_for_mode(mode: str, anchor: TimeAnchorPacket, semantic_query_present: bool) -> str:
    anchor_type = _normalize_text(anchor.anchor_type)
    if mode == "session_order_retrieval":
        return "session_order_nearest"
    if mode == "event_anchor_retrieval":
        if _normalize_text(anchor.commit_anchor):
            return "commit_order_before_after"
        return "event_anchor_before_after"
    if mode == "clarification_required":
        return "manual_owner_clarification"
    if semantic_query_present:
        return "time_window_then_semantic"
    if anchor_type == "absolute_date":
        return "time_window_exact"
    return "time_window_exact"



def _expected_confidence_for_mode(mode: str, candidate_sources: tuple[str, ...], needs_clarification: bool) -> str:
    if mode == "blocked_no_source" or mode == "blocked_no_authority":
        return "blocked"
    if needs_clarification:
        return "low" if candidate_sources else "unresolved"
    if mode == "hybrid_temporal_semantic":
        return "high" if candidate_sources else "medium"
    if mode in {"temporal_first", "session_order_retrieval", "event_anchor_retrieval"}:
        return "high" if candidate_sources else "medium"
    if mode == "semantic_first":
        return "medium" if candidate_sources else "low"
    return "low"



def _clarification_for_plan(mode: str, anchor: TimeAnchorPacket, semantic_query_present: bool, candidate_sources: tuple[str, ...]) -> tuple[bool, str]:
    phrase = _normalize_text(anchor.original_phrase)
    if mode == "blocked_no_source":
        return False, ""
    if mode == "blocked_no_authority":
        return False, ""
    if mode == "clarification_required":
        if phrase in VAGUE_TEMPORAL_PHRASES_V1:
            return True, "What exact time window do you mean by this vague temporal phrase?"
        if semantic_query_present:
            return True, "Which exact time window should I use with the semantic query?"
        return True, "Can you specify the time window you mean?"
    if mode == "hybrid_temporal_semantic" and not candidate_sources:
        return True, "Which source scope should I use for this hybrid retrieval?"
    return False, ""



def _authority_required_for_plan(mode: str) -> bool:
    return True



def _next_step_for_plan(mode: str, source_scope: str, needs_clarification: bool) -> str:
    if mode == "blocked_no_source":
        return "blocked_wait_for_source"
    if mode == "blocked_no_authority":
        return "request_source_authority" if source_scope in UNSAFE_AUTHORITY_SOURCES_V1 else "request_memory_authority"
    if needs_clarification:
        return "ask_clarifying_question"
    if mode in {"temporal_first", "semantic_first", "hybrid_temporal_semantic", "session_order_retrieval", "event_anchor_retrieval"}:
        return "request_memory_authority"
    return "execute_safe_retrieval_later"



def _build_plan(
    anchor: TimeAnchorPacket,
    semantic_query: Any = None,
    available_sources: Any = None,
) -> TemporalMemoryRetrievalPlan:
    validate_time_anchor_packet_v1(anchor)
    anchor_map = anchor if isinstance(anchor, Mapping) else asdict(anchor)
    semantic_query_present = bool(_safe_text(semantic_query))
    semantic_query_summary = _summary_for_semantic_query(semantic_query)
    available = _unique_allowed_sources(available_sources)
    mode = _select_mode(anchor, semantic_query_present, available)
    candidate_sources = _candidate_sources_for_mode(mode, available)
    source_scope = _source_scope_for_mode(mode, candidate_sources)
    needs_clarification, clarification_question = _clarification_for_plan(mode, anchor, semantic_query_present, candidate_sources)
    ranking_strategy = _ranking_strategy_for_mode(mode, anchor, semantic_query_present)
    expected_confidence = _expected_confidence_for_mode(mode, candidate_sources, needs_clarification)
    source_priority = _priority_for_mode(mode) if not candidate_sources else tuple(_dedupe_preserve(candidate_sources + _priority_for_mode(mode)))
    excluded_sources = _excluded_sources(candidate_sources)
    authority_required = _authority_required_for_plan(mode)
    recommended_next_step = _next_step_for_plan(mode, source_scope, needs_clarification)

    if mode == "blocked_no_source":
        candidate_sources = tuple()
        source_priority = tuple()
        source_scope = "unknown_source"
        excluded_sources = tuple(ALLOWED_SOURCE_CLASSES_V1)
    elif mode == "blocked_no_authority" and not candidate_sources:
        candidate_sources = tuple(sorted(UNSAFE_AUTHORITY_SOURCES_V1))
        source_priority = tuple(candidate_sources)
        source_scope = candidate_sources[0]
        excluded_sources = _excluded_sources(candidate_sources)

    if mode == "hybrid_temporal_semantic" and not semantic_query_present:
        mode = "temporal_first"
        ranking_strategy = _ranking_strategy_for_mode(mode, anchor, semantic_query_present)
        expected_confidence = _expected_confidence_for_mode(mode, candidate_sources, needs_clarification)
        recommended_next_step = _next_step_for_plan(mode, source_scope, needs_clarification)

    anchor_safe_metadata = anchor_map.get("safe_metadata") or {}
    plan_safe_metadata = {}
    if isinstance(anchor_safe_metadata, Mapping):
        plan_safe_metadata.update({str(key): _json_safe(value) for key, value in anchor_safe_metadata.items()})
    else:
        plan_safe_metadata["anchor_safe_metadata"] = _json_safe(anchor_safe_metadata)
    plan_safe_metadata.update(
        {
            "source_count": len(candidate_sources),
            "available_source_count": len(available),
            "semantic_query_present": semantic_query_present,
            "anchor_type": _safe_text(anchor_map.get("anchor_type")),
            "time_anchor_id": _safe_text(anchor_map.get("time_anchor_id")),
            "retrieval_mode_reason": "metadata_only_planning",
        }
    )

    plan = TemporalMemoryRetrievalPlan(
        retrieval_plan_id=_deterministic_id(
            anchor_map.get("time_anchor_id"),
            anchor_map.get("original_phrase"),
            mode,
            source_scope,
            semantic_query_summary,
            candidate_sources,
        ),
        source_time_anchor_id=_safe_text(anchor_map.get("time_anchor_id")),
        original_phrase=_safe_text(anchor_map.get("original_phrase")),
        anchor_type=_safe_text(anchor_map.get("anchor_type")),
        resolved_start=anchor_map.get("resolved_start") if anchor_map.get("resolved_start") is None else _safe_text(anchor_map.get("resolved_start")),
        resolved_end=anchor_map.get("resolved_end") if anchor_map.get("resolved_end") is None else _safe_text(anchor_map.get("resolved_end")),
        timezone=_safe_text(anchor_map.get("timezone")),
        retrieval_mode=mode,
        semantic_query_present=semantic_query_present,
        semantic_query_summary=semantic_query_summary,
        source_scope=source_scope,
        source_priority=tuple(source_priority),
        project_scope_hint=_safe_text(anchor_map.get("project_scope_hint")),
        session_scope_hint=_safe_text(anchor_map.get("session_scope_hint")),
        event_anchor=_safe_text(anchor_map.get("event_anchor")),
        commit_anchor=_safe_text(anchor_map.get("commit_anchor")),
        candidate_source_classes=tuple(candidate_sources),
        excluded_source_classes=tuple(excluded_sources),
        authority_required=authority_required,
        memory_read_authority_granted=False,
        source_access_granted=False,
        raw_log_access_allowed=False,
        private_data_access_allowed=False,
        expected_confidence=expected_confidence,
        needs_clarification=needs_clarification,
        clarification_question=clarification_question,
        ranking_strategy=ranking_strategy,
        result_constraints=SAFE_RESULT_CONSTRAINTS_V1,
        answer_boundary=SAFE_ANSWER_BOUNDARY_V1,
        failure_modes=DEFAULT_FAILURE_MODES_V1,
        recommended_next_step=recommended_next_step,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        safe_metadata=plan_safe_metadata,
    )
    validate_temporal_memory_retrieval_plan_v1(plan)
    return plan


# ---------------------------------------------------------------------------
# Public APIs
# ---------------------------------------------------------------------------


def build_temporal_memory_retrieval_plan_v1(
    original_phrase: Any,
    reference_time: Any = None,
    timezone: str = "",
    calendar_basis: str = "",
    project_scope_hint: str = "",
    session_scope_hint: str = "",
    source_scope_hint: str = "",
    event_anchor: str = "",
    commit_anchor: str = "",
    semantic_query: Any = None,
    available_sources: Any = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> TemporalMemoryRetrievalPlan:
    time_anchor = build_time_anchor_packet_v1(
        original_phrase=original_phrase,
        reference_time=reference_time,
        timezone=timezone,
        calendar_basis=calendar_basis,
        project_scope_hint=project_scope_hint,
        session_scope_hint=session_scope_hint,
        source_scope_hint=source_scope_hint,
        event_anchor=event_anchor,
        commit_anchor=commit_anchor,
        safe_metadata=safe_metadata,
    )
    return _build_plan(time_anchor, semantic_query=semantic_query, available_sources=available_sources)



def build_temporal_memory_retrieval_plan_from_anchor_v1(
    time_anchor_packet: Any,
    semantic_query: Any = None,
    available_sources: Any = None,
) -> TemporalMemoryRetrievalPlan:
    return _build_plan(time_anchor_packet, semantic_query=semantic_query, available_sources=available_sources)



def validate_temporal_memory_retrieval_plan_v1(plan: Any) -> bool:
    if _contains_forbidden_fields(plan):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_claim_marker(plan):
        raise ValidationError("forbidden_public_or_claim_language_present")

    if is_dataclass(plan):
        normalized = plan
    elif isinstance(plan, Mapping):
        allowed = {field.name for field in TemporalMemoryRetrievalPlan.__dataclass_fields__.values()}
        extra = set(str(key) for key in plan.keys()) - allowed
        if extra:
            raise ValidationError("unknown_fields_present")
        normalized = TemporalMemoryRetrievalPlan(
            retrieval_plan_id=_safe_text(plan.get("retrieval_plan_id")),
            source_time_anchor_id=_safe_text(plan.get("source_time_anchor_id")),
            original_phrase=_safe_text(plan.get("original_phrase")),
            anchor_type=_safe_text(plan.get("anchor_type")),
            resolved_start=plan.get("resolved_start") if plan.get("resolved_start") is None else _safe_text(plan.get("resolved_start")),
            resolved_end=plan.get("resolved_end") if plan.get("resolved_end") is None else _safe_text(plan.get("resolved_end")),
            timezone=_safe_text(plan.get("timezone")),
            retrieval_mode=_safe_text(plan.get("retrieval_mode")),
            semantic_query_present=bool(plan.get("semantic_query_present")),
            semantic_query_summary=_safe_text(plan.get("semantic_query_summary")),
            source_scope=_safe_text(plan.get("source_scope")),
            source_priority=tuple(_dedupe_preserve(plan.get("source_priority") or ())),
            project_scope_hint=_safe_text(plan.get("project_scope_hint")),
            session_scope_hint=_safe_text(plan.get("session_scope_hint")),
            event_anchor=_safe_text(plan.get("event_anchor")),
            commit_anchor=_safe_text(plan.get("commit_anchor")),
            candidate_source_classes=tuple(_dedupe_preserve(plan.get("candidate_source_classes") or ())),
            excluded_source_classes=tuple(_dedupe_preserve(plan.get("excluded_source_classes") or ())),
            authority_required=bool(plan.get("authority_required")),
            memory_read_authority_granted=bool(plan.get("memory_read_authority_granted")),
            source_access_granted=bool(plan.get("source_access_granted")),
            raw_log_access_allowed=bool(plan.get("raw_log_access_allowed")),
            private_data_access_allowed=bool(plan.get("private_data_access_allowed")),
            expected_confidence=_safe_text(plan.get("expected_confidence")),
            needs_clarification=bool(plan.get("needs_clarification")),
            clarification_question=_safe_text(plan.get("clarification_question")),
            ranking_strategy=_safe_text(plan.get("ranking_strategy")),
            result_constraints=tuple(_dedupe_preserve(plan.get("result_constraints") or ())),
            answer_boundary=tuple(_dedupe_preserve(plan.get("answer_boundary") or ())),
            failure_modes=tuple(_dedupe_preserve(plan.get("failure_modes") or ())),
            recommended_next_step=_safe_text(plan.get("recommended_next_step")),
            runtime_authority=bool(plan.get("runtime_authority")),
            writes_state=bool(plan.get("writes_state")),
            model_provider_used=bool(plan.get("model_provider_used")),
            public_claim_allowed=bool(plan.get("public_claim_allowed")),
            iss_internal_reference_allowed=bool(plan.get("iss_internal_reference_allowed")),
            learning_claimed=bool(plan.get("learning_claimed")),
            safe_metadata=plan.get("safe_metadata") if plan.get("safe_metadata") is None else dict(_json_safe(plan.get("safe_metadata"))),
        )
    else:
        raise ValidationError("unsupported_plan_type")

    if normalized.retrieval_mode not in ALLOWED_RETRIEVAL_MODES_V1:
        raise ValidationError("unknown_retrieval_mode")
    if normalized.expected_confidence not in ALLOWED_EXPECTED_CONFIDENCE_VALUES_V1:
        raise ValidationError("unknown_expected_confidence")
    if normalized.ranking_strategy not in ALLOWED_RANKING_STRATEGIES_V1:
        raise ValidationError("unknown_ranking_strategy")
    if normalized.recommended_next_step not in ALLOWED_NEXT_STEPS_V1:
        raise ValidationError("unknown_next_step")

    candidate_sources = tuple(_dedupe_preserve(normalized.candidate_source_classes))
    excluded_sources = tuple(_dedupe_preserve(normalized.excluded_source_classes))
    source_priority = tuple(_dedupe_preserve(normalized.source_priority))

    if any(source not in ALLOWED_SOURCE_CLASSES_V1 for source in candidate_sources):
        raise ValidationError("unknown_source_class")
    if any(source not in ALLOWED_SOURCE_CLASSES_V1 for source in excluded_sources):
        raise ValidationError("unknown_source_class")
    if any(source not in ALLOWED_SOURCE_CLASSES_V1 for source in source_priority):
        raise ValidationError("unknown_source_class")
    if normalized.source_scope and normalized.source_scope not in ALLOWED_SOURCE_CLASSES_V1:
        raise ValidationError("unknown_source_class")

    if normalized.memory_read_authority_granted:
        raise ValidationError("memory_read_authority_granted_must_be_false")
    if normalized.source_access_granted:
        raise ValidationError("source_access_granted_must_be_false")
    if normalized.raw_log_access_allowed:
        raise ValidationError("raw_log_access_allowed_must_be_false")
    if normalized.private_data_access_allowed:
        raise ValidationError("private_data_access_allowed_must_be_false")
    if normalized.runtime_authority:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.public_claim_allowed:
        raise ValidationError("public_claim_allowed_must_be_false")
    if normalized.learning_claimed:
        raise ValidationError("learning_claimed_must_be_false")
    if not normalized.authority_required:
        raise ValidationError("authority_required_must_be_true")

    if normalized.retrieval_mode == "blocked_no_source":
        if normalized.expected_confidence != "blocked":
            raise ValidationError("blocked_plan_must_be_blocked_confidence")
        if candidate_sources:
            raise ValidationError("blocked_no_source_must_not_have_candidate_sources")
        if normalized.recommended_next_step != "blocked_wait_for_source":
            raise ValidationError("blocked_no_source_must_wait_for_source")
    elif normalized.retrieval_mode == "blocked_no_authority":
        if normalized.expected_confidence != "blocked":
            raise ValidationError("blocked_plan_must_be_blocked_confidence")
    else:
        if not candidate_sources:
            raise ValidationError("non_blocked_plan_requires_source_classes")
        if normalized.expected_confidence == "blocked":
            raise ValidationError("non_blocked_plan_cannot_be_blocked_confidence")

    if normalized.retrieval_mode == "clarification_required" and normalized.expected_confidence == "high":
        raise ValidationError("vague_plan_cannot_be_high_confidence")
    if _normalize_text(normalized.original_phrase) in VAGUE_TEMPORAL_PHRASES_V1:
        if normalized.expected_confidence == "high" and not normalized.needs_clarification:
            raise ValidationError("vague_temporal_plan_needs_clarification_or_lower_confidence")

    if normalized.needs_clarification and not normalized.clarification_question:
        raise ValidationError("clarification_requires_question")
    if not normalized.needs_clarification and normalized.clarification_question:
        raise ValidationError("clarification_question_without_need")

    if normalized.retrieval_mode == "hybrid_temporal_semantic" and not normalized.semantic_query_present:
        raise ValidationError("hybrid_mode_requires_semantic_query")
    if normalized.semantic_query_present and not normalized.semantic_query_summary:
        raise ValidationError("semantic_query_requires_summary")

    if normalized.retrieval_mode == "session_order_retrieval" and normalized.ranking_strategy != "session_order_nearest":
        raise ValidationError("session_mode_requires_session_order_ranking")
    if normalized.retrieval_mode == "event_anchor_retrieval":
        if normalized.ranking_strategy not in {"event_anchor_before_after", "commit_order_before_after"}:
            raise ValidationError("event_mode_requires_event_or_commit_ranking")

    if normalized.safe_metadata is not None:
        if _contains_forbidden_fields(normalized.safe_metadata):
            raise ValidationError("forbidden_raw_fields_present")
        if _contains_forbidden_claim_marker(normalized.safe_metadata):
            raise ValidationError("forbidden_public_or_claim_language_present")

    return True



def summarize_temporal_memory_retrieval_plan_v1(plan: Any) -> TemporalMemoryRetrievalSummary:
    if not isinstance(plan, TemporalMemoryRetrievalPlan):
        validate_temporal_memory_retrieval_plan_v1(plan)
        if isinstance(plan, Mapping):
            plan = TemporalMemoryRetrievalPlan(
                retrieval_plan_id=_safe_text(plan.get("retrieval_plan_id")),
                source_time_anchor_id=_safe_text(plan.get("source_time_anchor_id")),
                original_phrase=_safe_text(plan.get("original_phrase")),
                anchor_type=_safe_text(plan.get("anchor_type")),
                resolved_start=plan.get("resolved_start") if plan.get("resolved_start") is None else _safe_text(plan.get("resolved_start")),
                resolved_end=plan.get("resolved_end") if plan.get("resolved_end") is None else _safe_text(plan.get("resolved_end")),
                timezone=_safe_text(plan.get("timezone")),
                retrieval_mode=_safe_text(plan.get("retrieval_mode")),
                semantic_query_present=bool(plan.get("semantic_query_present")),
                semantic_query_summary=_safe_text(plan.get("semantic_query_summary")),
                source_scope=_safe_text(plan.get("source_scope")),
                source_priority=tuple(_dedupe_preserve(plan.get("source_priority") or ())),
                project_scope_hint=_safe_text(plan.get("project_scope_hint")),
                session_scope_hint=_safe_text(plan.get("session_scope_hint")),
                event_anchor=_safe_text(plan.get("event_anchor")),
                commit_anchor=_safe_text(plan.get("commit_anchor")),
                candidate_source_classes=tuple(_dedupe_preserve(plan.get("candidate_source_classes") or ())),
                excluded_source_classes=tuple(_dedupe_preserve(plan.get("excluded_source_classes") or ())),
                authority_required=bool(plan.get("authority_required")),
                memory_read_authority_granted=bool(plan.get("memory_read_authority_granted")),
                source_access_granted=bool(plan.get("source_access_granted")),
                raw_log_access_allowed=bool(plan.get("raw_log_access_allowed")),
                private_data_access_allowed=bool(plan.get("private_data_access_allowed")),
                expected_confidence=_safe_text(plan.get("expected_confidence")),
                needs_clarification=bool(plan.get("needs_clarification")),
                clarification_question=_safe_text(plan.get("clarification_question")),
                ranking_strategy=_safe_text(plan.get("ranking_strategy")),
                result_constraints=tuple(_dedupe_preserve(plan.get("result_constraints") or ())),
                answer_boundary=tuple(_dedupe_preserve(plan.get("answer_boundary") or ())),
                failure_modes=tuple(_dedupe_preserve(plan.get("failure_modes") or ())),
                recommended_next_step=_safe_text(plan.get("recommended_next_step")),
                runtime_authority=bool(plan.get("runtime_authority")),
                writes_state=bool(plan.get("writes_state")),
                model_provider_used=bool(plan.get("model_provider_used")),
                public_claim_allowed=bool(plan.get("public_claim_allowed")),
                iss_internal_reference_allowed=bool(plan.get("iss_internal_reference_allowed")),
                learning_claimed=bool(plan.get("learning_claimed")),
                safe_metadata=plan.get("safe_metadata") if plan.get("safe_metadata") is None else dict(_json_safe(plan.get("safe_metadata"))),
            )
    validate_temporal_memory_retrieval_plan_v1(plan)
    return TemporalMemoryRetrievalSummary(
        summary_type=SUMMARY_TYPE_V1,
        retrieval_plan_id=plan.retrieval_plan_id,
        retrieval_mode=plan.retrieval_mode,
        source_scope=plan.source_scope,
        expected_confidence=plan.expected_confidence,
        needs_clarification=plan.needs_clarification,
        recommended_next_step=plan.recommended_next_step,
    )



def to_temporal_memory_retrieval_plan_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------


def build_initial_temporal_memory_retrieval_plan_examples_v1() -> tuple[TemporalMemoryRetrievalPlan, ...]:
    ref = "2026-06-01T12:00:00"
    tz = "Europe/Berlin"
    examples: list[TemporalMemoryRetrievalPlan] = [
        build_temporal_memory_retrieval_plan_v1(
            "yesterday",
            reference_time=ref,
            timezone=tz,
            available_sources=("approved_memory_index", "prior_conversation_summary", "project_memory"),
            safe_metadata={"example_name": "yesterday_temporal_first_plan"},
        ),
        build_temporal_memory_retrieval_plan_v1(
            "yesterday",
            reference_time=ref,
            timezone=tz,
            semantic_query="WiFi sensing",
            available_sources=("approved_memory_index", "prior_conversation_summary", "project_memory"),
            safe_metadata={"example_name": "yesterday_wifi_hybrid_plan"},
        ),
        build_temporal_memory_retrieval_plan_v1(
            "earlier in this chat",
            reference_time=ref,
            timezone=tz,
            session_scope_hint="current_conversation",
            available_sources=("current_conversation", "prior_conversation_summary", "runtime_session_log"),
            safe_metadata={"example_name": "earlier_in_chat_session_plan"},
        ),
        build_temporal_memory_retrieval_plan_v1(
            "before the file manifest builder",
            reference_time=ref,
            timezone=tz,
            event_anchor="file_manifest_builder",
            commit_anchor="last_commit",
            available_sources=("lane_report_metadata", "repo_commit_metadata", "project_memory"),
            safe_metadata={"example_name": "before_file_manifest_builder_event_plan"},
        ),
        build_temporal_memory_retrieval_plan_v1(
            "recently",
            reference_time=ref,
            timezone=tz,
            available_sources=("approved_memory_index", "prior_conversation_summary"),
            safe_metadata={"example_name": "recently_vague_clarification_plan"},
        ),
        build_temporal_memory_retrieval_plan_v1(
            "last week",
            reference_time=ref,
            timezone=tz,
            semantic_query="public wording",
            available_sources=("project_memory", "lane_report_metadata", "repo_commit_metadata"),
            safe_metadata={"example_name": "last_week_public_wording_hybrid_plan"},
        ),
        build_temporal_memory_retrieval_plan_v1(
            "yesterday",
            reference_time=ref,
            timezone=tz,
            available_sources=(),
            safe_metadata={"example_name": "blocked_no_source_plan"},
        ),
        build_temporal_memory_retrieval_plan_v1(
            "before the last commit",
            reference_time=ref,
            timezone=tz,
            available_sources=("runtime_session_log", ".weslr_state"),
            safe_metadata={"example_name": "blocked_no_authority_plan"},
        ),
    ]
    return tuple(examples)


__all__ = [
    "HELPER_TYPE_V1",
    "TEMPORAL_MEMORY_RETRIEVAL_PLAN_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "TemporalMemoryRetrievalPlan",
    "TemporalMemoryRetrievalSummary",
    "ValidationError",
    "build_temporal_memory_retrieval_plan_v1",
    "build_temporal_memory_retrieval_plan_from_anchor_v1",
    "validate_temporal_memory_retrieval_plan_v1",
    "summarize_temporal_memory_retrieval_plan_v1",
    "to_temporal_memory_retrieval_plan_json_safe_v1",
    "build_initial_temporal_memory_retrieval_plan_examples_v1",
]
