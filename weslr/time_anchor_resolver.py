"""Metadata-only time anchor resolver v1.

This module resolves temporal phrases into bounded time-anchor packets before
any memory retrieval logic runs.

It is pure, deterministic, import-safe, and fail-closed.
No model/provider/search/advisor calls. No network. No I/O. No state writes.
No chat routing. No runtime behavior changes. No memory reads.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime, timedelta
from typing import Any, Iterable, Mapping, Sequence

HELPER_TYPE_V1 = "time_anchor_resolver_v1"
TIME_ANCHOR_PACKET_TYPE_V1 = "time_anchor_packet_v1"
SUMMARY_TYPE_V1 = "time_anchor_summary_v1"

ALLOWED_ANCHOR_TYPES_V1 = {
    "absolute_date",
    "relative_day",
    "relative_range",
    "day_part",
    "session_relative",
    "project_relative",
    "event_relative",
    "vague_temporal",
    "unresolved",
}

ALLOWED_RETRIEVAL_MODE_HINTS_V1 = {
    "temporal_first",
    "semantic_first",
    "hybrid_temporal_semantic",
    "event_anchor_retrieval",
    "clarification_required",
}

ALLOWED_CONFIDENCE_VALUES_V1 = {"high", "medium", "low", "unresolved"}

ALLOWED_CALENDAR_BASES_V1 = {
    "local_calendar_day",
    "local_calendar_week",
    "local_day_part",
    "session_order",
    "project_event_order",
    "explicit_absolute_date",
    "unknown",
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

FORBIDDEN_CLAIM_PHRASES_V1 = (
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

CLAIM_BASE_TERMS_V1 = {"agi", "consciousness", "sentience", "turing", "certification"}
CLAIM_QUALIFIERS_V1 = {"claim", "claims", "claimed", "official", "certification", "certified", "public", "readiness"}

RELATIVE_DAY_PHRASES_V1 = {"today", "yesterday", "tomorrow"}
DAY_PART_PHRASES_V1 = {"this morning", "this afternoon", "this evening", "last night"}
RELATIVE_RANGE_PHRASES_V1 = {"last week", "past few days", "recently", "a few days ago", "last month", "the other day"}
SESSION_RELATIVE_PHRASES_V1 = {
    "earlier in this chat",
    "earlier",
    "previous session",
    "last session",
    "previous conversation",
    "in the last session",
    "earlier in the conversation",
}
PROJECT_RELATIVE_PREFIXES_V1 = {
    "before the last commit",
    "after the last commit",
    "before the last lane",
    "after the file manifest builder",
    "before code scaffold generator",
}
EVENT_RELATIVE_PREFIXES_V1 = {
    "after occ replied",
    "before i sent the report",
    "when we implemented",
    "after i sent",
    "before i sent",
}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TimeAnchorPacket:
    time_anchor_id: str
    original_phrase: str
    normalized_phrase: str
    anchor_type: str
    reference_time: str | None
    timezone: str
    resolved_start: str | None
    resolved_end: str | None
    calendar_basis: str
    confidence: str
    needs_clarification: bool
    source_scope_hint: str
    project_scope_hint: str
    session_scope_hint: str
    event_anchor: str
    commit_anchor: str
    retrieval_mode_hint: str
    semantic_filter_required: bool
    temporal_first: bool
    source_access_granted: bool
    memory_read_authority_granted: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    iss_internal_reference_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class TimeAnchorSummary:
    summary_type: str
    time_anchor_id: str
    original_phrase: str
    anchor_type: str
    confidence: str
    retrieval_mode_hint: str
    window_summary: str
    needs_clarification: bool


# ---------------------------------------------------------------------------
# Safe conversion helpers
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
    return copy.deepcopy(value)



def _get_field(value: Any, *names: str, default: Any = "") -> Any:
    if value is None:
        return default
    if is_dataclass(value):
        for name in names:
            if hasattr(value, name):
                return getattr(value, name)
        return default
    if isinstance(value, Mapping):
        for name in names:
            if name in value:
                return value[name]
        return default
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return default



def _as_mapping(value: Any) -> Mapping[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return value
    raise ValidationError("time_anchor_packet_must_be_dataclass_or_mapping")



def _contains_forbidden_fields(value: Any, path: str = "") -> list[str]:
    blocked: list[str] = []
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _safe_text(key).lower()
            next_path = f"{path}.{key_text}" if path else key_text
            if key_text in FORBIDDEN_FIELD_NAMES_V1:
                blocked.append(next_path)
            blocked.extend(_contains_forbidden_fields(item, next_path))
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            blocked.extend(_contains_forbidden_fields(item, f"{path}[{index}]"))
    return blocked



def _contains_forbidden_claim_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_forbidden_claim_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_claim_marker(item) for item in value)
    if isinstance(value, str):
        blob = _normalize_text(value)
        if any(phrase in blob for phrase in FORBIDDEN_CLAIM_PHRASES_V1):
            return True
        has_base = any(term in blob for term in CLAIM_BASE_TERMS_V1)
        has_qualifier = any(term in blob for term in CLAIM_QUALIFIERS_V1)
        return has_base and has_qualifier
    return False



def _contains_negated_marker(value: str, marker: str) -> bool:
    text = _normalize_text(value)
    for prefix in ("no ", "not ", "without ", "never ", "no-", "not-", "without-", "never-"):
        if f"{prefix}{marker}" in text:
            return True
    compact = re.sub(r"[\s/]+", "-", text)
    for prefix in ("no-", "not-", "without-", "never-"):
        if f"{prefix}{marker}" in compact:
            return True
    return False



def _contains_missing_reference_time_fake_window(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        reference_time = _safe_text(value.get("reference_time"))
        anchor_type = _safe_text(value.get("anchor_type"))
        resolved_start = _safe_text(value.get("resolved_start"))
        resolved_end = _safe_text(value.get("resolved_end"))
        confidence = _safe_text(value.get("confidence"))
        if not reference_time and anchor_type in {
            "relative_day",
            "relative_range",
            "day_part",
            "session_relative",
            "project_relative",
            "event_relative",
            "vague_temporal",
        }:
            if resolved_start or resolved_end or confidence == "high":
                return True
        return any(_contains_missing_reference_time_fake_window(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_missing_reference_time_fake_window(item) for item in value)
    return False



def _normalize_reference_time(reference_time: Any) -> tuple[str | None, datetime | None]:
    if reference_time is None or reference_time == "":
        return None, None
    if isinstance(reference_time, datetime):
        return reference_time.isoformat(timespec="seconds"), reference_time
    if isinstance(reference_time, date):
        dt = datetime(reference_time.year, reference_time.month, reference_time.day)
        return dt.isoformat(timespec="seconds"), dt
    text = _safe_text(reference_time)
    if not text:
        return None, None
    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
        return dt.isoformat(timespec="seconds"), dt
    except ValueError:
        try:
            d = date.fromisoformat(normalized)
        except ValueError:
            return text, None
        dt = datetime(d.year, d.month, d.day)
        return dt.isoformat(timespec="seconds"), dt



def _datetime_iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")



def _day_bounds(reference_dt: datetime, offset_days: int = 0) -> tuple[datetime, datetime]:
    base = reference_dt.date() + timedelta(days=offset_days)
    start = datetime(base.year, base.month, base.day)
    end = start + timedelta(days=1) - timedelta(seconds=1)
    return start, end



def _week_bounds(reference_dt: datetime, offset_weeks: int = -1) -> tuple[datetime, datetime]:
    monday = reference_dt.date() - timedelta(days=reference_dt.date().weekday())
    target_start_date = monday + timedelta(weeks=offset_weeks)
    start = datetime(target_start_date.year, target_start_date.month, target_start_date.day)
    end = start + timedelta(days=7) - timedelta(seconds=1)
    return start, end



def _day_part_bounds(reference_dt: datetime, part: str) -> tuple[datetime, datetime]:
    day_start, day_end = _day_bounds(reference_dt, 0)
    if part == "this morning":
        return day_start + timedelta(hours=5), day_start + timedelta(hours=12)
    if part == "this afternoon":
        return day_start + timedelta(hours=12), day_start + timedelta(hours=18)
    if part == "this evening":
        return day_start + timedelta(hours=18), day_end
    if part == "last night":
        previous_day_start, _ = _day_bounds(reference_dt, -1)
        return previous_day_start + timedelta(hours=20), day_start + timedelta(hours=5)
    return day_start, day_end



def _time_anchor_id(original_phrase: str, anchor_type: str, reference_time: str | None) -> str:
    blob = _normalize_text(f"{anchor_type} {original_phrase} {reference_time or 'unresolved'}")
    blob = re.sub(r"[^a-z0-9]+", "_", blob).strip("_")
    return f"time_anchor_{blob or 'unresolved'}"



def _detect_anchor_type(normalized_phrase: str) -> str:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", normalized_phrase):
        return "absolute_date"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}[t ]\d{2}:\d{2}(:\d{2})?(?:[+-]\d{2}:\d{2}|z)?", normalized_phrase):
        return "absolute_date"
    if normalized_phrase == "recently":
        return "vague_temporal"
    if normalized_phrase in RELATIVE_DAY_PHRASES_V1:
        return "relative_day"
    if normalized_phrase in DAY_PART_PHRASES_V1:
        return "day_part"
    if normalized_phrase in RELATIVE_RANGE_PHRASES_V1:
        return "relative_range"
    if normalized_phrase in SESSION_RELATIVE_PHRASES_V1 or normalized_phrase.startswith("earlier "):
        return "session_relative"
    if normalized_phrase in PROJECT_RELATIVE_PREFIXES_V1 or normalized_phrase.startswith("before the ") or normalized_phrase.startswith("after the "):
        return "project_relative"
    if normalized_phrase in EVENT_RELATIVE_PREFIXES_V1 or normalized_phrase.startswith("after ") or normalized_phrase.startswith("before ") or normalized_phrase.startswith("when we "):
        return "event_relative"
    if normalized_phrase:
        return "vague_temporal" if any(token in normalized_phrase for token in ("recent", "other day", "a while", "sometime", "earlier")) else "unresolved"
    return "unresolved"



def _retrieval_mode_for_anchor(anchor_type: str, normalized_phrase: str) -> str:
    if anchor_type == "absolute_date":
        return "temporal_first"
    if anchor_type in {"relative_day", "relative_range", "day_part"}:
        return "temporal_first"
    if anchor_type == "session_relative":
        if normalized_phrase in {"previous session", "last session", "previous conversation", "in the last session"}:
            return "event_anchor_retrieval"
        return "temporal_first"
    if anchor_type == "project_relative":
        return "event_anchor_retrieval"
    if anchor_type == "event_relative":
        return "event_anchor_retrieval"
    if anchor_type == "vague_temporal":
        return "clarification_required"
    return "clarification_required"



def _calendar_basis_for_anchor(anchor_type: str, normalized_phrase: str) -> str:
    if anchor_type == "absolute_date":
        return "explicit_absolute_date"
    if anchor_type == "relative_day":
        return "local_calendar_day"
    if anchor_type == "relative_range":
        return "local_calendar_week" if normalized_phrase == "last week" else "local_calendar_day"
    if anchor_type == "day_part":
        return "local_day_part"
    if anchor_type == "session_relative":
        return "session_order"
    if anchor_type == "project_relative":
        return "project_event_order"
    if anchor_type == "event_relative":
        return "project_event_order"
    return "unknown"



def _default_scope_hint(anchor_type: str, normalized_phrase: str) -> tuple[str, str, str]:
    if anchor_type == "session_relative":
        if normalized_phrase in {"previous session", "last session", "previous conversation"}:
            return "previous_session", "", "previous_session"
        return "current_conversation", "", "current_conversation"
    if anchor_type in {"project_relative", "event_relative"}:
        return "project_history", "project_history", ""
    if anchor_type in {"relative_day", "relative_range", "day_part", "absolute_date", "vague_temporal"}:
        return "owner_memory", "", ""
    return "unknown", "", ""



def _confidence_and_clarification(
    anchor_type: str,
    reference_time_text: str | None,
    timezone: str,
    normalized_phrase: str,
) -> tuple[str, bool]:
    if anchor_type == "absolute_date":
        return "high", False
    if not reference_time_text:
        return "unresolved", True
    if anchor_type == "relative_day":
        if timezone:
            return "high", False
        return "low", True
    if anchor_type == "day_part":
        if timezone:
            return "high", False
        return "low", True
    if anchor_type == "relative_range":
        if normalized_phrase == "last week" and timezone:
            return "medium", False
        if normalized_phrase == "past few days" and timezone:
            return "medium", False
        if timezone:
            return "medium", False
        return "low", True
    if anchor_type == "session_relative":
        return ("medium" if normalized_phrase in {"earlier in this chat", "earlier", "earlier in the conversation"} else "low"), False
    if anchor_type in {"project_relative", "event_relative"}:
        return "medium", False
    if anchor_type == "vague_temporal":
        return "low", True
    return "unresolved", True



def _window_for_packet(anchor_type: str, normalized_phrase: str, reference_dt: datetime | None) -> tuple[str | None, str | None]:
    if anchor_type == "absolute_date":
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", normalized_phrase):
            d = date.fromisoformat(normalized_phrase)
            start = datetime(d.year, d.month, d.day)
            end = start + timedelta(days=1) - timedelta(seconds=1)
            return _datetime_iso(start), _datetime_iso(end)
        try:
            dt = datetime.fromisoformat(normalized_phrase.replace("z", "+00:00").replace("Z", "+00:00"))
        except ValueError:
            return None, None
        iso = dt.isoformat(timespec="seconds")
        return iso, iso
    if reference_dt is None:
        return None, None
    if anchor_type == "relative_day":
        offset = {"today": 0, "yesterday": -1, "tomorrow": 1}.get(normalized_phrase, 0)
        start, end = _day_bounds(reference_dt, offset)
        return _datetime_iso(start), _datetime_iso(end)
    if anchor_type == "day_part":
        start, end = _day_part_bounds(reference_dt, normalized_phrase)
        return _datetime_iso(start), _datetime_iso(end)
    if anchor_type == "relative_range":
        if normalized_phrase == "last week":
            start, end = _week_bounds(reference_dt, -1)
            return _datetime_iso(start), _datetime_iso(end)
        if normalized_phrase == "past few days":
            start = datetime(*(reference_dt.date() - timedelta(days=3)).timetuple()[:3])
            return _datetime_iso(start), _datetime_iso(reference_dt)
        if normalized_phrase == "last month":
            first_of_current = datetime(reference_dt.year, reference_dt.month, 1)
            prev_month_end = first_of_current - timedelta(seconds=1)
            prev_month_start = datetime(prev_month_end.year, prev_month_end.month, 1)
            end = datetime(prev_month_end.year, prev_month_end.month, prev_month_end.day, 23, 59, 59)
            return _datetime_iso(prev_month_start), _datetime_iso(end)
        start = datetime(*(reference_dt.date() - timedelta(days=3)).timetuple()[:3])
        return _datetime_iso(start), _datetime_iso(reference_dt)
    return None, None



def _resolve_packet_fields(
    original_phrase: Any,
    reference_time: Any = None,
    timezone: str = "",
    calendar_basis: str = "",
    project_scope_hint: str = "",
    session_scope_hint: str = "",
    source_scope_hint: str = "",
    event_anchor: str = "",
    commit_anchor: str = "",
    safe_metadata: Mapping[str, Any] | None = None,
) -> TimeAnchorPacket:
    phrase = _safe_text(original_phrase)
    normalized_phrase = _normalize_text(phrase)
    reference_time_text, reference_dt = _normalize_reference_time(reference_time)
    anchor_type = _detect_anchor_type(normalized_phrase)
    retrieval_mode_hint = _retrieval_mode_for_anchor(anchor_type, normalized_phrase)
    calendar_basis_value = calendar_basis or _calendar_basis_for_anchor(anchor_type, normalized_phrase)
    if calendar_basis_value not in ALLOWED_CALENDAR_BASES_V1:
        calendar_basis_value = "unknown"
    resolved_start, resolved_end = _window_for_packet(anchor_type, normalized_phrase, reference_dt)
    confidence, needs_clarification = _confidence_and_clarification(anchor_type, reference_time_text, timezone, normalized_phrase)
    if anchor_type == "unresolved":
        retrieval_mode_hint = "clarification_required"
        needs_clarification = True
        confidence = "unresolved"
        resolved_start = None
        resolved_end = None
    if anchor_type in {"relative_day", "relative_range", "day_part", "session_relative", "project_relative", "event_relative", "vague_temporal"} and not reference_time_text:
        confidence = "unresolved"
        needs_clarification = True
        retrieval_mode_hint = "clarification_required"
        resolved_start = None
        resolved_end = None
    if anchor_type in {"relative_day", "relative_range", "day_part"} and not timezone:
        if confidence != "unresolved":
            confidence = "low"
        needs_clarification = True
    source_scope_default, project_scope_default, session_scope_default = _default_scope_hint(anchor_type, normalized_phrase)
    source_scope_hint = _safe_text(source_scope_hint) or source_scope_default
    project_scope_hint = _safe_text(project_scope_hint) or project_scope_default
    session_scope_hint = _safe_text(session_scope_hint) or session_scope_default
    packet = TimeAnchorPacket(
        time_anchor_id=_time_anchor_id(phrase, anchor_type, reference_time_text),
        original_phrase=phrase,
        normalized_phrase=normalized_phrase,
        anchor_type=anchor_type,
        reference_time=reference_time_text,
        timezone=_safe_text(timezone),
        resolved_start=resolved_start,
        resolved_end=resolved_end,
        calendar_basis=calendar_basis_value,
        confidence=confidence,
        needs_clarification=needs_clarification,
        source_scope_hint=source_scope_hint,
        project_scope_hint=project_scope_hint,
        session_scope_hint=session_scope_hint,
        event_anchor=_safe_text(event_anchor),
        commit_anchor=_safe_text(commit_anchor),
        retrieval_mode_hint=retrieval_mode_hint,
        semantic_filter_required=anchor_type in {"project_relative", "event_relative", "vague_temporal", "unresolved"},
        temporal_first=anchor_type in {"absolute_date", "relative_day", "relative_range", "day_part", "session_relative"},
        source_access_granted=False,
        memory_read_authority_granted=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        safe_metadata=dict(safe_metadata or {}),
    )
    validate_time_anchor_packet_v1(packet)
    return packet


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_time_anchor_packet_v1(
    original_phrase: Any,
    reference_time: Any = None,
    timezone: str = "",
    calendar_basis: str = "",
    project_scope_hint: str = "",
    session_scope_hint: str = "",
    source_scope_hint: str = "",
    event_anchor: str = "",
    commit_anchor: str = "",
    safe_metadata: Mapping[str, Any] | None = None,
) -> TimeAnchorPacket:
    return _resolve_packet_fields(
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



def resolve_time_anchor_v1(
    original_phrase: Any,
    reference_time: Any = None,
    timezone: str = "",
    calendar_basis: str = "",
    project_scope_hint: str = "",
    session_scope_hint: str = "",
    source_scope_hint: str = "",
    event_anchor: str = "",
    commit_anchor: str = "",
    safe_metadata: Mapping[str, Any] | None = None,
) -> TimeAnchorPacket:
    return build_time_anchor_packet_v1(
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



def validate_time_anchor_packet_v1(packet: Any) -> bool:
    if _contains_forbidden_fields(packet):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_claim_marker(packet):
        raise ValidationError("forbidden_public_or_claim_language_present")
    if _contains_missing_reference_time_fake_window(packet):
        raise ValidationError("relative_phrase_without_reference_time_cannot_have_fake_window")

    if is_dataclass(packet):
        normalized = packet
    elif isinstance(packet, Mapping):
        allowed = {field.name for field in TimeAnchorPacket.__dataclass_fields__.values()}
        extra = set(str(key) for key in packet.keys()) - allowed
        if extra:
            raise ValidationError("unknown_fields_present")
        normalized = TimeAnchorPacket(
            time_anchor_id=_safe_text(packet.get("time_anchor_id")),
            original_phrase=_safe_text(packet.get("original_phrase")),
            normalized_phrase=_safe_text(packet.get("normalized_phrase")),
            anchor_type=_safe_text(packet.get("anchor_type")),
            reference_time=packet.get("reference_time"),
            timezone=_safe_text(packet.get("timezone")),
            resolved_start=packet.get("resolved_start") if packet.get("resolved_start") is None else _safe_text(packet.get("resolved_start")),
            resolved_end=packet.get("resolved_end") if packet.get("resolved_end") is None else _safe_text(packet.get("resolved_end")),
            calendar_basis=_safe_text(packet.get("calendar_basis")),
            confidence=_safe_text(packet.get("confidence")),
            needs_clarification=bool(packet.get("needs_clarification")),
            source_scope_hint=_safe_text(packet.get("source_scope_hint")),
            project_scope_hint=_safe_text(packet.get("project_scope_hint")),
            session_scope_hint=_safe_text(packet.get("session_scope_hint")),
            event_anchor=_safe_text(packet.get("event_anchor")),
            commit_anchor=_safe_text(packet.get("commit_anchor")),
            retrieval_mode_hint=_safe_text(packet.get("retrieval_mode_hint")),
            semantic_filter_required=bool(packet.get("semantic_filter_required")),
            temporal_first=bool(packet.get("temporal_first")),
            source_access_granted=bool(packet.get("source_access_granted")),
            memory_read_authority_granted=bool(packet.get("memory_read_authority_granted")),
            runtime_authority=bool(packet.get("runtime_authority")),
            writes_state=bool(packet.get("writes_state")),
            model_provider_used=bool(packet.get("model_provider_used")),
            public_claim_allowed=bool(packet.get("public_claim_allowed")),
            iss_internal_reference_allowed=bool(packet.get("iss_internal_reference_allowed")),
            learning_claimed=bool(packet.get("learning_claimed")),
            safe_metadata=dict(packet.get("safe_metadata") or {}),
        )
    else:
        raise ValidationError("time_anchor_packet_must_be_dataclass_or_mapping")

    if not normalized.time_anchor_id:
        raise ValidationError("time_anchor_id_required")
    if not normalized.original_phrase:
        raise ValidationError("original_phrase_required")
    if not normalized.normalized_phrase:
        raise ValidationError("normalized_phrase_required")
    if normalized.anchor_type not in ALLOWED_ANCHOR_TYPES_V1:
        raise ValidationError("unknown_anchor_type")
    if normalized.retrieval_mode_hint not in ALLOWED_RETRIEVAL_MODE_HINTS_V1:
        raise ValidationError("unknown_retrieval_mode_hint")
    if normalized.confidence not in ALLOWED_CONFIDENCE_VALUES_V1:
        raise ValidationError("unknown_confidence")
    if normalized.calendar_basis not in ALLOWED_CALENDAR_BASES_V1:
        raise ValidationError("unknown_calendar_basis")

    for field_name in (
        "needs_clarification",
        "semantic_filter_required",
        "temporal_first",
        "source_access_granted",
        "memory_read_authority_granted",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "iss_internal_reference_allowed",
        "learning_claimed",
    ):
        if type(getattr(normalized, field_name)) is not bool:
            raise ValidationError(f"{field_name}_must_be_bool")

    if normalized.source_access_granted:
        raise ValidationError("source_access_granted_must_be_false")
    if normalized.memory_read_authority_granted:
        raise ValidationError("memory_read_authority_granted_must_be_false")
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

    if normalized.anchor_type == "unresolved":
        if normalized.resolved_start or normalized.resolved_end or normalized.confidence != "unresolved" or not normalized.needs_clarification:
            raise ValidationError("unresolved_anchor_must_not_fake_window")

    if normalized.reference_time is None:
        if normalized.anchor_type in {"relative_day", "relative_range", "day_part", "session_relative", "project_relative", "event_relative", "vague_temporal"}:
            if normalized.confidence == "high":
                raise ValidationError("relative_phrase_without_reference_time_cannot_be_high_confidence")
            if normalized.resolved_start or normalized.resolved_end:
                raise ValidationError("relative_phrase_without_reference_time_cannot_have_window")

    if normalized.anchor_type == "absolute_date":
        if normalized.confidence != "high":
            raise ValidationError("absolute_date_must_be_high_confidence")

    if normalized.anchor_type in {"relative_day", "day_part", "relative_range"} and not normalized.timezone:
        if normalized.confidence == "high":
            raise ValidationError("local_relative_phrase_without_timezone_cannot_be_high_confidence")

    if normalized.anchor_type in {"project_relative", "event_relative"} and normalized.retrieval_mode_hint != "event_anchor_retrieval":
        raise ValidationError("project_or_event_relative_must_use_event_anchor_retrieval")

    if normalized.anchor_type == "session_relative" and normalized.calendar_basis != "session_order":
        raise ValidationError("session_relative_must_use_session_order")

    if normalized.anchor_type == "project_relative" and normalized.calendar_basis != "project_event_order":
        raise ValidationError("project_relative_must_use_project_event_order")

    if normalized.anchor_type == "event_relative" and normalized.calendar_basis != "project_event_order":
        raise ValidationError("event_relative_must_use_project_event_order")

    return True



def summarize_time_anchor_packet_v1(packet: Any) -> TimeAnchorSummary:
    if not isinstance(packet, TimeAnchorPacket):
        validate_time_anchor_packet_v1(packet)
        if isinstance(packet, Mapping):
            packet = TimeAnchorPacket(
                time_anchor_id=_safe_text(packet.get("time_anchor_id")),
                original_phrase=_safe_text(packet.get("original_phrase")),
                normalized_phrase=_safe_text(packet.get("normalized_phrase")),
                anchor_type=_safe_text(packet.get("anchor_type")),
                reference_time=packet.get("reference_time"),
                timezone=_safe_text(packet.get("timezone")),
                resolved_start=packet.get("resolved_start") if packet.get("resolved_start") is None else _safe_text(packet.get("resolved_start")),
                resolved_end=packet.get("resolved_end") if packet.get("resolved_end") is None else _safe_text(packet.get("resolved_end")),
                calendar_basis=_safe_text(packet.get("calendar_basis")),
                confidence=_safe_text(packet.get("confidence")),
                needs_clarification=bool(packet.get("needs_clarification")),
                source_scope_hint=_safe_text(packet.get("source_scope_hint")),
                project_scope_hint=_safe_text(packet.get("project_scope_hint")),
                session_scope_hint=_safe_text(packet.get("session_scope_hint")),
                event_anchor=_safe_text(packet.get("event_anchor")),
                commit_anchor=_safe_text(packet.get("commit_anchor")),
                retrieval_mode_hint=_safe_text(packet.get("retrieval_mode_hint")),
                semantic_filter_required=bool(packet.get("semantic_filter_required")),
                temporal_first=bool(packet.get("temporal_first")),
                source_access_granted=bool(packet.get("source_access_granted")),
                memory_read_authority_granted=bool(packet.get("memory_read_authority_granted")),
                runtime_authority=bool(packet.get("runtime_authority")),
                writes_state=bool(packet.get("writes_state")),
                model_provider_used=bool(packet.get("model_provider_used")),
                public_claim_allowed=bool(packet.get("public_claim_allowed")),
                iss_internal_reference_allowed=bool(packet.get("iss_internal_reference_allowed")),
                learning_claimed=bool(packet.get("learning_claimed")),
                safe_metadata=dict(packet.get("safe_metadata") or {}),
            )
    window_summary = "unresolved"
    if packet.resolved_start or packet.resolved_end:
        window_summary = f"{packet.resolved_start or 'null'}..{packet.resolved_end or 'null'}"
    return TimeAnchorSummary(
        summary_type=SUMMARY_TYPE_V1,
        time_anchor_id=packet.time_anchor_id,
        original_phrase=packet.original_phrase,
        anchor_type=packet.anchor_type,
        confidence=packet.confidence,
        retrieval_mode_hint=packet.retrieval_mode_hint,
        window_summary=window_summary,
        needs_clarification=packet.needs_clarification,
    )



def to_time_anchor_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------


def build_initial_time_anchor_examples_v1() -> tuple[TimeAnchorPacket, ...]:
    ref = "2026-06-01T12:00:00"
    tz = "Europe/Berlin"
    examples: list[TimeAnchorPacket] = [
        build_time_anchor_packet_v1("yesterday", reference_time=ref, timezone=tz, safe_metadata={"example_name": "yesterday_anchor_example"}),
        build_time_anchor_packet_v1("today", reference_time=ref, timezone=tz, safe_metadata={"example_name": "today_anchor_example"}),
        build_time_anchor_packet_v1("this morning", reference_time=ref, timezone=tz, safe_metadata={"example_name": "this_morning_anchor_example"}),
        build_time_anchor_packet_v1("last night", reference_time=ref, timezone=tz, safe_metadata={"example_name": "last_night_anchor_example"}),
        build_time_anchor_packet_v1("last week", reference_time=ref, timezone=tz, safe_metadata={"example_name": "last_week_anchor_example"}),
        build_time_anchor_packet_v1("past few days", reference_time=ref, timezone=tz, safe_metadata={"example_name": "past_few_days_anchor_example"}),
        build_time_anchor_packet_v1("previous session", reference_time=ref, timezone=tz, session_scope_hint="previous_session", safe_metadata={"example_name": "previous_session_anchor_example"}),
        build_time_anchor_packet_v1("earlier in this chat", reference_time=ref, timezone=tz, session_scope_hint="current_conversation", safe_metadata={"example_name": "earlier_in_this_chat_anchor_example"}),
        build_time_anchor_packet_v1("before the last commit", reference_time=ref, timezone=tz, commit_anchor="last_commit", safe_metadata={"example_name": "before_last_commit_anchor_example"}),
        build_time_anchor_packet_v1("after the file manifest builder", reference_time=ref, timezone=tz, event_anchor="file_manifest_builder", safe_metadata={"example_name": "after_file_manifest_builder_anchor_example"}),
        build_time_anchor_packet_v1("2026-05-31", safe_metadata={"example_name": "absolute_date_anchor_example"}),
        build_time_anchor_packet_v1("recently", reference_time=ref, timezone=tz, safe_metadata={"example_name": "recently_vague_anchor_example"}),
        build_time_anchor_packet_v1("yesterday", timezone=tz, safe_metadata={"example_name": "missing_reference_time_anchor_example"}),
    ]
    return tuple(examples)


# Backwards-compatible aliases.
build_time_anchor_packet = build_time_anchor_packet_v1
resolve_time_anchor = resolve_time_anchor_v1
validate_time_anchor_packet = validate_time_anchor_packet_v1
summarize_time_anchor_packet = summarize_time_anchor_packet_v1
to_time_anchor_json_safe = to_time_anchor_json_safe_v1
build_initial_time_anchor_examples = build_initial_time_anchor_examples_v1
