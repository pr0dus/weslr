"""Metadata-only Self-RAG evidence loop boundary helpers v1.

This module evaluates bounded evidence-loop metadata only. It is pure,
deterministic, import-safe, and fail-closed.

It does not implement retrieval, call web/search, call APIs, call
models/providers, vectorize documents, create indexes, write memory, touch
`.weslr`, read files, or assemble final answers.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

HELPER_TYPE_V1 = "self_rag_evidence_loop_boundary_v1"
PACKET_TYPE_V1 = "self_rag_loop_packet_v1"
SUMMARY_TYPE_V1 = "self_rag_loop_packet_summary_v1"

ALLOWED_LOOP_STAGES_V1 = {
    "initial_query_classification",
    "initial_evidence_path_selection",
    "evidence_candidate_collection",
    "access_privacy_poison_check",
    "source_evidence_graph_update_candidate",
    "naie_candidate_check",
    "claim_grounding_assessment",
    "context_compression_assessment",
    "gap_detection",
    "reroute_or_stop_decision",
    "fallback_or_defer_decision",
}

ALLOWED_LOOP_OUTCOMES_V1 = {
    "evidence_sufficient",
    "evidence_sufficient_with_caveat",
    "evidence_missing",
    "evidence_stale",
    "evidence_contradicted",
    "evidence_access_blocked",
    "evidence_poison_blocked",
    "evidence_privacy_blocked",
    "more_evidence_needed",
    "ask_clarification",
    "refuse_unsupported",
    "defer_until_retrieval_available",
    "unknown_outcome",
}

ALLOWED_FALLBACK_BEHAVIORS_V1 = {
    "answer_with_caveat",
    "ask_clarifying_question",
    "request_source_upload",
    "use_existing_graph_only",
    "return_unsupported_claim",
    "refuse_public_claim",
    "block_due_access_policy",
    "block_due_poison_policy",
    "defer_until_retrieval_available",
    "unknown_fallback",
}

ALLOWED_REROUTE_TARGETS_V1 = {
    "same_route_once",
    "source_evidence_graph_lookup",
    "uploaded_file_retrieval",
    "memory_retrieval",
    "signal_metadata_lookup",
    "forecast_error_ledger_lookup",
    "future_web_search",
    "clarification_required",
    "no_reroute_stop",
    "unknown_reroute",
}

ALLOWED_QUERY_CLASSES_V1 = {
    "general_reasoning_query",
    "uploaded_document_query",
    "personal_memory_query",
    "currentness_sensitive_query",
    "public_claim_query",
    "signal_metadata_query",
    "forecast_query",
    "source_graph_query",
    "unknown_query_class",
}

ALLOWED_CONTEXT_BUDGET_STATUSES_V1 = {
    "within_budget",
    "near_budget_limit",
    "over_budget",
    "budget_unknown",
}

ALLOWED_CANDIDATE_STATUS_HINTS_V1 = {
    "accepted",
    "grounded",
    "supported",
    "current",
    "fresh",
    "recent",
    "stale",
    "contradicted",
    "access_blocked",
    "poison_blocked",
    "privacy_blocked",
    "missing",
    "unknown",
}

ALLOWED_ACCESS_STATUS_HINTS_V1 = {
    "access_allowed",
    "public_safe",
    "summary_only",
    "access_restricted",
    "private_source_blocked",
    "public_use_blocked",
    "blocked",
    "unknown",
}

ALLOWED_FRESHNESS_STATUS_HINTS_V1 = {
    "fresh",
    "current",
    "recent",
    "stable",
    "stale",
    "unknown",
}

ALLOWED_PRIVACY_STATUS_HINTS_V1 = {
    "public",
    "public_safe",
    "sensitive",
    "private",
    "restricted",
    "access_restricted",
    "unknown",
}

ALLOWED_POISON_STATUS_HINTS_V1 = {
    "clean",
    "poisoned",
    "quarantined",
    "poison_blocked",
    "blocked",
    "unknown",
}

FORBIDDEN_FIELD_PHRASES_V1 = (
    "hidden prompt",
    "hidden_prompt",
    "raw private",
    "raw_private",
    "private data",
    "secret",
    "token",
    "api key",
    "credential",
    "password",
)

FORBIDDEN_CLAIM_PHRASES_V1 = (
    "hallucination elimination",
    "hallucination-free",
    "hallucination free",
    "public readiness",
    "public ready",
    "public-readiness",
    "proof certainty",
    "truth certainty",
    "proof claim",
    "truth claim",
    "official proof",
    "official truth",
)

DEFAULT_SAFE_METADATA_V1 = {"metadata_only": True, "internal_only": True}
DEFAULT_MAX_ITERATIONS_V1 = 2


class ValidationError(ValueError):
    pass


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
    return " ".join(_safe_text(value).replace("_", " ").split()).lower()



def _status_text(value: Any) -> str:
    return _safe_text(value).strip().lower().replace(" ", "_").replace("-", "_")



def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = _normalize_text(value)
        if normalized in {"", "0", "false", "no", "off", "blocked", "not ready", "not_required", "not required"}:
            return False
        if normalized in {"1", "true", "yes", "on", "ready", "allowed", "allowed to run"}:
            return True
    return bool(value)



def _safe_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]



def _safe_str_list(value: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _safe_list(value):
        text = _safe_text(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out



def _safe_str_list_preserve_order(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        items = list(value.values())
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        items = [value]
    return [text for text in (_safe_text(item) for item in items) if text]



def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))



def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        items = [_json_safe(item) for item in value]
        return sorted(items, key=_json_sort_key)
    return _safe_text(value)



def to_self_rag_loop_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def _contains_forbidden_field(value: Any) -> str:
    if value is None:
        return ""
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            for phrase in FORBIDDEN_FIELD_PHRASES_V1:
                if phrase in key_text:
                    return key_text or phrase
            found = _contains_forbidden_field(item)
            if found:
                return found
        return ""
    if isinstance(value, (list, tuple, set)):
        for item in value:
            found = _contains_forbidden_field(item)
            if found:
                return found
        return ""
    text = _normalize_text(value)
    for phrase in FORBIDDEN_FIELD_PHRASES_V1:
        if phrase in text:
            return phrase
    return ""



def _contains_forbidden_claim_marker(value: Any) -> bool:
    if value is None:
        return False
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for item in value.values():
            if _contains_forbidden_claim_marker(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_claim_marker(item) for item in value)
    text = _normalize_text(value)
    return any(phrase in text for phrase in FORBIDDEN_CLAIM_PHRASES_V1)



def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): val for key, val in value.items()}
    return {}



def _unique_preserve_order(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out



def _flatten_candidate_refs(candidates: list[Mapping[str, Any]]) -> list[str]:
    refs: list[str] = []
    for candidate in candidates:
        refs.extend(_safe_str_list(candidate.get("evidence_ref")))
        refs.extend(_safe_str_list(candidate.get("evidence_refs")))
        refs.extend(_safe_str_list(candidate.get("source_ref")))
        refs.extend(_safe_str_list(candidate.get("source_refs")))
        refs.extend(_safe_str_list(candidate.get("citation_refs")))
    return _unique_preserve_order(refs)



def _candidate_status(candidate: Mapping[str, Any]) -> str:
    for key in (
        "candidate_status",
        "status",
        "grounding_status",
        "evidence_status",
    ):
        status = _status_text(candidate.get(key))
        if status:
            return status
    return "unknown"



def _candidate_access_status(candidate: Mapping[str, Any]) -> str:
    for key in (
        "access_status",
        "source_access_status",
        "privacy_access_status",
    ):
        status = _status_text(candidate.get(key))
        if status:
            return status
    return "unknown"



def _candidate_freshness_status(candidate: Mapping[str, Any]) -> str:
    for key in (
        "freshness_status",
        "source_freshness_status",
        "currentness_status",
    ):
        status = _status_text(candidate.get(key))
        if status:
            return status
    return "unknown"



def _candidate_privacy_status(candidate: Mapping[str, Any]) -> str:
    for key in (
        "privacy_status",
        "source_privacy_status",
        "privacy",
    ):
        status = _status_text(candidate.get(key))
        if status:
            return status
    return "unknown"



def _candidate_poison_status(candidate: Mapping[str, Any]) -> str:
    for key in (
        "poison_status",
        "source_poison_status",
        "poison_policy_status",
    ):
        status = _status_text(candidate.get(key))
        if status:
            return status
    return "unknown"



def _candidate_source_type(candidate: Mapping[str, Any]) -> str:
    for key in (
        "source_type",
        "candidate_source_type",
        "evidence_source_type",
    ):
        source_type = _status_text(candidate.get(key))
        if source_type:
            return source_type
    return "unknown"



def _candidate_is_current(candidate: Mapping[str, Any]) -> bool:
    freshness = _candidate_freshness_status(candidate)
    return freshness in {"fresh", "current", "recent", "stable"}



def _candidate_is_stale(candidate: Mapping[str, Any]) -> bool:
    freshness = _candidate_freshness_status(candidate)
    return freshness == "stale"



def _candidate_is_access_blocked(candidate: Mapping[str, Any]) -> bool:
    access = _candidate_access_status(candidate)
    return access in {"access_restricted", "private_source_blocked", "public_use_blocked", "blocked"}



def _candidate_is_poison_blocked(candidate: Mapping[str, Any]) -> bool:
    poison = _candidate_poison_status(candidate)
    return poison in {"poisoned", "quarantined", "poison_blocked", "blocked"}



def _candidate_is_privacy_blocked(candidate: Mapping[str, Any]) -> bool:
    privacy = _candidate_privacy_status(candidate)
    return privacy in {"private", "restricted", "access_restricted", "sensitive"}



def _candidate_is_contradicted(candidate: Mapping[str, Any]) -> bool:
    status = _candidate_status(candidate)
    return status == "contradicted" or bool(candidate.get("contradiction_present")) or bool(candidate.get("contradicted"))



def _candidate_is_supported(candidate: Mapping[str, Any]) -> bool:
    status = _candidate_status(candidate)
    return status in {"accepted", "grounded", "supported", "current", "fresh", "recent"} or bool(candidate.get("accepted"))



def _candidate_citation_required(candidate: Mapping[str, Any]) -> bool:
    if _safe_bool(candidate.get("citation_required")):
        return True
    return _normalize_text(candidate.get("citation_requirement")) in {"required", "needed", "must cite"}



def _candidate_has_public_safe_evidence(candidate: Mapping[str, Any]) -> bool:
    if _safe_bool(candidate.get("public_safe")):
        return True
    access = _candidate_access_status(candidate)
    privacy = _candidate_privacy_status(candidate)
    return access in {"access_allowed", "public_safe", "summary_only"} and privacy in {"public", "public_safe", "unknown"}



def _candidate_has_private_evidence(candidate: Mapping[str, Any]) -> bool:
    return _candidate_is_access_blocked(candidate) or _candidate_is_privacy_blocked(candidate)



def _candidate_summary(candidate: Mapping[str, Any]) -> str:
    parts = [
        _safe_text(candidate.get("evidence_ref") or candidate.get("source_ref") or candidate.get("id") or candidate.get("candidate_id")),
        _safe_text(candidate.get("summary") or candidate.get("evidence_summary") or candidate.get("source_summary")),
        _candidate_status(candidate),
    ]
    return " | ".join(part for part in parts if part)



def _query_requires_currentness(packet: Mapping[str, Any]) -> bool:
    metadata = _safe_mapping(packet.get("safe_metadata"))
    if _safe_bool(metadata.get("query_requires_currentness")):
        return True
    return _normalize_text(packet.get("initial_query_class")) == "currentness sensitive query"



def _query_requires_citation(packet: Mapping[str, Any]) -> bool:
    metadata = _safe_mapping(packet.get("safe_metadata"))
    if _safe_bool(metadata.get("citation_required")) or _safe_bool(metadata.get("citation_needed")):
        return True
    return _safe_bool(packet.get("citation_required"))



def _query_requests_public_claim(packet: Mapping[str, Any]) -> bool:
    metadata = _safe_mapping(packet.get("safe_metadata"))
    if _safe_bool(metadata.get("public_claim_requested")):
        return True
    return _normalize_text(packet.get("initial_query_class")) == "public claim query"



def _query_requires_source_upload(packet: Mapping[str, Any]) -> bool:
    metadata = _safe_mapping(packet.get("safe_metadata"))
    if _safe_bool(metadata.get("requires_user_file_access")):
        return True
    return _normalize_text(packet.get("initial_query_class")) == "uploaded document query"



def _query_prefers_memory(packet: Mapping[str, Any]) -> bool:
    return _normalize_text(packet.get("initial_query_class")) == "personal memory query"



def _query_prefers_signal_metadata(packet: Mapping[str, Any]) -> bool:
    return _normalize_text(packet.get("initial_query_class")) == "signal metadata query"



def _query_prefers_forecast_ledger(packet: Mapping[str, Any]) -> bool:
    return _normalize_text(packet.get("initial_query_class")) == "forecast query"



def _query_prefers_source_graph(packet: Mapping[str, Any]) -> bool:
    return _normalize_text(packet.get("initial_query_class")) == "source graph query"



def _query_classify(packet: Mapping[str, Any]) -> str:
    explicit = _safe_text(packet.get("initial_query_class"))
    if explicit in ALLOWED_QUERY_CLASSES_V1:
        return explicit
    summary = _normalize_text(packet.get("query_summary"))
    if any(token in summary for token in ("current", "right now", "today", "latest", "now")):
        return "currentness_sensitive_query"
    if any(token in summary for token in ("attach", "uploaded", "pdf", "file", "document")):
        return "uploaded_document_query"
    if any(token in summary for token in ("last time", "we decided", "my project", "remember")):
        return "personal_memory_query"
    if any(token in summary for token in ("public claim", "website claim", "launch readiness", "public")):
        return "public_claim_query"
    if any(token in summary for token in ("signal", "telemetry", "forecast")):
        return "signal_metadata_query" if "signal" in summary else "forecast_query"
    return "general_reasoning_query"



def _detected_stale_candidates(candidates: list[Mapping[str, Any]]) -> list[str]:
    return _unique_preserve_order([_safe_text(candidate.get("evidence_ref") or candidate.get("source_ref") or candidate.get("id") or candidate.get("candidate_id")) for candidate in candidates if _candidate_is_stale(candidate)])



def _detected_contradicted_candidates(candidates: list[Mapping[str, Any]]) -> list[str]:
    return _unique_preserve_order([_safe_text(candidate.get("evidence_ref") or candidate.get("source_ref") or candidate.get("id") or candidate.get("candidate_id")) for candidate in candidates if _candidate_is_contradicted(candidate)])



def _detected_access_blocked_candidates(candidates: list[Mapping[str, Any]]) -> list[str]:
    return _unique_preserve_order([_safe_text(candidate.get("evidence_ref") or candidate.get("source_ref") or candidate.get("id") or candidate.get("candidate_id")) for candidate in candidates if _candidate_is_access_blocked(candidate)])



def _detected_poison_blocked_candidates(candidates: list[Mapping[str, Any]]) -> list[str]:
    return _unique_preserve_order([_safe_text(candidate.get("evidence_ref") or candidate.get("source_ref") or candidate.get("id") or candidate.get("candidate_id")) for candidate in candidates if _candidate_is_poison_blocked(candidate)])



def _detected_privacy_blocked_candidates(candidates: list[Mapping[str, Any]]) -> list[str]:
    return _unique_preserve_order([_safe_text(candidate.get("evidence_ref") or candidate.get("source_ref") or candidate.get("id") or candidate.get("candidate_id")) for candidate in candidates if _candidate_is_privacy_blocked(candidate)])



def _detected_accepted_candidates(candidates: list[Mapping[str, Any]]) -> list[str]:
    return _unique_preserve_order([_safe_text(candidate.get("evidence_ref") or candidate.get("source_ref") or candidate.get("id") or candidate.get("candidate_id")) for candidate in candidates if _candidate_is_supported(candidate) and not (_candidate_is_access_blocked(candidate) or _candidate_is_poison_blocked(candidate) or _candidate_is_privacy_blocked(candidate))])



def _has_current_candidate(candidates: list[Mapping[str, Any]]) -> bool:
    return any(_candidate_is_current(candidate) for candidate in candidates)



def _has_private_candidate(candidates: list[Mapping[str, Any]]) -> bool:
    return any(_candidate_has_private_evidence(candidate) for candidate in candidates)



def _candidate_path_target(candidate: Mapping[str, Any], packet: Mapping[str, Any]) -> str:
    source_type = _candidate_source_type(candidate)
    if _query_requires_source_upload(packet) or source_type in {"uploaded_document", "uploaded_file", "file", "document"}:
        return "uploaded_file_retrieval"
    if _query_prefers_memory(packet) or source_type in {"memory", "memory_summary", "personal_memory"}:
        return "memory_retrieval"
    if _query_prefers_signal_metadata(packet) or source_type in {"signal", "signal_metadata", "signal_metadata_context"}:
        return "signal_metadata_lookup"
    if _query_prefers_forecast_ledger(packet) or source_type in {"forecast", "forecast_error", "forecast_error_context"}:
        return "forecast_error_ledger_lookup"
    if _query_prefers_source_graph(packet) or source_type in {"source_graph", "source_evidence_graph", "graph"}:
        return "source_evidence_graph_lookup"
    if _query_requires_currentness(packet):
        return "future_web_search"
    return "same_route_once"



def _initial_reroute_target(packet: Mapping[str, Any], candidates: list[Mapping[str, Any]]) -> str:
    if _query_requires_source_upload(packet):
        return "uploaded_file_retrieval"
    if _query_prefers_memory(packet):
        return "memory_retrieval"
    if _query_prefers_signal_metadata(packet):
        return "signal_metadata_lookup"
    if _query_prefers_forecast_ledger(packet):
        return "forecast_error_ledger_lookup"
    if _query_prefers_source_graph(packet):
        return "source_evidence_graph_lookup"
    if _query_requires_currentness(packet):
        return "future_web_search"
    if candidates:
        return _candidate_path_target(candidates[0], packet)
    return "clarification_required"



def _normalize_stage(stage: Any) -> str:
    return _safe_text(stage)



def _normalize_outcome(value: Any) -> str:
    return _safe_text(value)



def _normalize_fallback(value: Any) -> str:
    return _safe_text(value)



def _normalize_reroute(value: Any) -> str:
    return _safe_text(value)


# ---------------------------------------------------------------------------
# Packet builders
# ---------------------------------------------------------------------------


def build_self_rag_loop_packet_v1(
    self_rag_loop_packet_id: str,
    query_summary: str,
    initial_query_class: str = "unknown_query_class",
    initial_routing_target: str = "unknown_reroute",
    loop_stage: str = "gap_detection",
    loop_iteration_count: int = 0,
    max_iterations: int = DEFAULT_MAX_ITERATIONS_V1,
    visited_routing_targets: list[Any] | None = None,
    evidence_candidates: list[Any] | None = None,
    accepted_evidence_refs: list[Any] | None = None,
    rejected_evidence_refs: list[Any] | None = None,
    missing_evidence_summary: str = "",
    contradiction_summary: str = "",
    stale_evidence_summary: str = "",
    access_block_summary: str = "",
    poison_block_summary: str = "",
    privacy_block_summary: str = "",
    grounding_status: str = "unknown_outcome",
    citation_readiness: str = "unknown_outcome",
    context_budget_status: str = "budget_unknown",
    reroute_recommended: bool = False,
    reroute_target: str = "unknown_reroute",
    stop_reason: str = "",
    fallback_behavior: str = "unknown_fallback",
    recommended_answer_action: str = "",
    recommended_next_check: str = "",
    runtime_authority: bool = False,
    writes_state: bool = False,
    model_provider_used: bool = False,
    public_claim_allowed: bool = False,
    proof_claim_allowed: bool = False,
    learning_claimed: bool = False,
    safe_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    candidates = [_safe_mapping(candidate) for candidate in (evidence_candidates or [])]
    packet: dict[str, Any] = {
        "helper_type": HELPER_TYPE_V1,
        "packet_type": PACKET_TYPE_V1,
        "self_rag_loop_packet_id": _safe_text(self_rag_loop_packet_id),
        "query_summary": _safe_text(query_summary),
        "initial_query_class": _safe_text(initial_query_class),
        "initial_routing_target": _safe_text(initial_routing_target),
        "loop_stage": _safe_text(loop_stage),
        "loop_iteration_count": int(loop_iteration_count),
        "max_iterations": int(max_iterations) if int(max_iterations) >= 0 else 0,
        "visited_routing_targets": _safe_str_list(visited_routing_targets),
        "evidence_candidates": candidates,
        "accepted_evidence_refs": _safe_str_list(accepted_evidence_refs),
        "rejected_evidence_refs": _safe_str_list(rejected_evidence_refs),
        "missing_evidence_summary": _safe_text(missing_evidence_summary),
        "contradiction_summary": _safe_text(contradiction_summary),
        "stale_evidence_summary": _safe_text(stale_evidence_summary),
        "access_block_summary": _safe_text(access_block_summary),
        "poison_block_summary": _safe_text(poison_block_summary),
        "privacy_block_summary": _safe_text(privacy_block_summary),
        "grounding_status": _safe_text(grounding_status),
        "citation_readiness": _safe_text(citation_readiness),
        "context_budget_status": _safe_text(context_budget_status),
        "reroute_recommended": _safe_bool(reroute_recommended),
        "reroute_target": _safe_text(reroute_target),
        "stop_reason": _safe_text(stop_reason),
        "fallback_behavior": _safe_text(fallback_behavior),
        "recommended_answer_action": _safe_text(recommended_answer_action),
        "recommended_next_check": _safe_text(recommended_next_check),
        "runtime_authority": _safe_bool(runtime_authority),
        "writes_state": _safe_bool(writes_state),
        "model_provider_used": _safe_bool(model_provider_used),
        "public_claim_allowed": _safe_bool(public_claim_allowed),
        "proof_claim_allowed": _safe_bool(proof_claim_allowed),
        "learning_claimed": _safe_bool(learning_claimed),
        "safe_metadata": _json_safe(DEFAULT_SAFE_METADATA_V1 if safe_metadata is None else safe_metadata),
    }

    if packet["initial_query_class"] == "unknown_query_class":
        packet["initial_query_class"] = _query_classify(packet)
    if packet["loop_iteration_count"] < 0:
        packet["loop_iteration_count"] = 0
    if packet["max_iterations"] < 0:
        packet["max_iterations"] = 0
    if packet["context_budget_status"] not in ALLOWED_CONTEXT_BUDGET_STATUSES_V1:
        packet["context_budget_status"] = "budget_unknown"
    if packet["grounding_status"] == "unknown_outcome":
        packet["grounding_status"] = evaluate_self_rag_evidence_state_v1(packet)
    if packet["citation_readiness"] == "unknown_outcome":
        if _query_requires_citation(packet) and not packet["accepted_evidence_refs"]:
            packet["citation_readiness"] = "evidence_missing"
        else:
            packet["citation_readiness"] = packet["grounding_status"]
    if packet["reroute_target"] == "unknown_reroute":
        packet["reroute_target"] = select_self_rag_reroute_v1(packet)
    if not packet["recommended_answer_action"]:
        packet["recommended_answer_action"] = _derive_recommended_answer_action(packet)
    if not packet["recommended_next_check"]:
        packet["recommended_next_check"] = _derive_recommended_next_check(packet)
    if not packet["stop_reason"]:
        packet["stop_reason"] = _derive_stop_reason(packet)

    return packet


# ---------------------------------------------------------------------------
# Evaluation / reroute / recommendation helpers
# ---------------------------------------------------------------------------


def evaluate_self_rag_evidence_state_v1(packet: Any) -> str:
    normalized = to_self_rag_loop_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        return "unknown_outcome"

    explicit = _normalize_outcome(normalized.get("grounding_status"))
    if explicit in ALLOWED_LOOP_OUTCOMES_V1 and explicit != "unknown_outcome":
        return explicit

    candidates = [_safe_mapping(candidate) for candidate in normalized.get("evidence_candidates") or []]
    accepted_refs = _safe_str_list(normalized.get("accepted_evidence_refs"))
    rejected_refs = _safe_str_list(normalized.get("rejected_evidence_refs"))
    citation_required = _query_requires_citation(normalized)
    requires_currentness = _query_requires_currentness(normalized)
    public_claim_requested = _query_requests_public_claim(normalized)
    over_budget = _normalize_text(normalized.get("context_budget_status")) == "over_budget"
    max_iterations = int(normalized.get("max_iterations") or 0)
    loop_iteration_count = int(normalized.get("loop_iteration_count") or 0)
    visited_targets = _safe_str_list_preserve_order(normalized.get("visited_routing_targets"))

    if loop_iteration_count > max_iterations:
        return "defer_until_retrieval_available"

    access_blocked = _detected_access_blocked_candidates(candidates)
    poison_blocked = _detected_poison_blocked_candidates(candidates)
    privacy_blocked = _detected_privacy_blocked_candidates(candidates)
    contradicted = _detected_contradicted_candidates(candidates)
    stale = _detected_stale_candidates(candidates)
    accepted = _detected_accepted_candidates(candidates)
    has_current = _has_current_candidate(candidates)
    has_private = _has_private_candidate(candidates)

    if access_blocked or _safe_text(normalized.get("access_block_summary")):
        return "evidence_access_blocked"
    if poison_blocked or _safe_text(normalized.get("poison_block_summary")):
        return "evidence_poison_blocked"
    if privacy_blocked or _safe_text(normalized.get("privacy_block_summary")):
        return "evidence_privacy_blocked"
    if contradicted or _safe_text(normalized.get("contradiction_summary")):
        return "evidence_contradicted"

    if public_claim_requested and has_private:
        return "refuse_unsupported"

    if requires_currentness and not has_current:
        return "defer_until_retrieval_available"

    if citation_required and not accepted_refs and not accepted:
        return "evidence_missing"

    if over_budget and not any(token in _normalize_text(normalized.get("recommended_answer_action")) for token in ("compress", "defer", "clarif", "question")):
        return "more_evidence_needed"

    if accepted_refs or accepted:
        if stale:
            return "evidence_sufficient_with_caveat"
        return "evidence_sufficient"

    if stale and not has_current:
        return "evidence_stale"

    if loop_iteration_count >= max_iterations:
        if public_claim_requested and has_private:
            return "refuse_unsupported"
        if requires_currentness:
            return "defer_until_retrieval_available"
        if citation_required:
            return "refuse_unsupported"
        return "more_evidence_needed"

    if visited_targets and len(visited_targets) != len(set(visited_targets)):
        return "more_evidence_needed"

    if citation_required:
        return "ask_clarification"
    return "more_evidence_needed"



def select_self_rag_reroute_v1(packet: Any) -> str:
    normalized = to_self_rag_loop_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        return "unknown_reroute"

    explicit = _normalize_reroute(normalized.get("reroute_target"))
    if explicit in ALLOWED_REROUTE_TARGETS_V1 and explicit != "unknown_reroute":
        return explicit

    candidates = [_safe_mapping(candidate) for candidate in normalized.get("evidence_candidates") or []]
    visited = _safe_str_list(normalized.get("visited_routing_targets"))
    max_iterations = int(normalized.get("max_iterations") or 0)
    loop_iteration_count = int(normalized.get("loop_iteration_count") or 0)
    grounding_status = evaluate_self_rag_evidence_state_v1(normalized)

    if loop_iteration_count >= max_iterations:
        return "no_reroute_stop"
    if visited and len(visited) != len(set(visited)):
        if visited[-1] in visited[:-1]:
            return "no_reroute_stop"

    if grounding_status in {"evidence_access_blocked", "evidence_poison_blocked", "evidence_privacy_blocked"}:
        return "no_reroute_stop"
    if grounding_status == "evidence_contradicted":
        return "no_reroute_stop"
    if grounding_status == "evidence_sufficient" or grounding_status == "evidence_sufficient_with_caveat":
        return "no_reroute_stop"

    if not candidates:
        if _query_requires_citation(normalized):
            return "clarification_required"
        if _query_requires_currentness(normalized):
            return "future_web_search"
        return "same_route_once"

    if _query_requires_source_upload(normalized):
        return "uploaded_file_retrieval"
    if _query_prefers_memory(normalized):
        return "memory_retrieval"
    if _query_prefers_signal_metadata(normalized):
        return "signal_metadata_lookup"
    if _query_prefers_forecast_ledger(normalized):
        return "forecast_error_ledger_lookup"
    if _query_prefers_source_graph(normalized):
        return "source_evidence_graph_lookup"
    if _query_requires_currentness(normalized):
        return "future_web_search"

    for candidate in candidates:
        target = _candidate_path_target(candidate, normalized)
        if target in ALLOWED_REROUTE_TARGETS_V1:
            return target

    return "same_route_once"



def _derive_recommended_answer_action(packet: Mapping[str, Any]) -> str:
    grounding_status = evaluate_self_rag_evidence_state_v1(packet)
    if grounding_status == "evidence_sufficient":
        return "use_existing_graph_only"
    if grounding_status == "evidence_sufficient_with_caveat":
        return "answer_with_caveat"
    if grounding_status == "evidence_access_blocked":
        return "block_due_access_policy"
    if grounding_status == "evidence_poison_blocked":
        return "block_due_poison_policy"
    if grounding_status == "evidence_privacy_blocked":
        return "block_due_access_policy"
    if grounding_status == "evidence_contradicted":
        return "return_unsupported_claim"
    if grounding_status == "evidence_stale":
        return "answer_with_caveat"
    if grounding_status == "evidence_missing":
        return "request_source_upload"
    if grounding_status == "ask_clarification":
        return "ask_clarifying_question"
    if grounding_status == "defer_until_retrieval_available":
        return "defer_until_retrieval_available"
    if grounding_status == "refuse_unsupported":
        return "return_unsupported_claim"
    if grounding_status == "more_evidence_needed":
        return "ask_clarifying_question"
    return "unknown_fallback"



def _derive_recommended_next_check(packet: Mapping[str, Any]) -> str:
    grounding_status = evaluate_self_rag_evidence_state_v1(packet)
    reroute_target = select_self_rag_reroute_v1(packet)
    if grounding_status in {"evidence_sufficient", "evidence_sufficient_with_caveat"}:
        return "no additional evidence check needed"
    if grounding_status == "evidence_access_blocked":
        return "respect access policy and stop reroute attempts"
    if grounding_status == "evidence_poison_blocked":
        return "respect poison policy and stop reroute attempts"
    if grounding_status == "evidence_privacy_blocked":
        return "respect privacy policy and stop reroute attempts"
    if grounding_status == "evidence_contradicted":
        return "preserve contradiction and avoid forced winner"
    if grounding_status == "evidence_stale":
        return "reroute only if a fresh source exists; otherwise caveat or defer"
    if grounding_status == "evidence_missing":
        return f"try {reroute_target} if within budget"
    if grounding_status == "defer_until_retrieval_available":
        return "defer until retrieval is available"
    if grounding_status == "ask_clarification":
        return "ask the user for the missing source or scope"
    if grounding_status == "more_evidence_needed":
        if _normalize_text(packet.get("context_budget_status")) == "over_budget":
            return "compress context or defer before another pass"
        return f"try {reroute_target} once more within budget"
    if grounding_status == "refuse_unsupported":
        return "refuse public or unsupported claim"
    return "unknown next check"



def _derive_stop_reason(packet: Mapping[str, Any]) -> str:
    grounding_status = evaluate_self_rag_evidence_state_v1(packet)
    max_iterations = int(packet.get("max_iterations") or 0)
    loop_iteration_count = int(packet.get("loop_iteration_count") or 0)
    if grounding_status in {"evidence_sufficient", "evidence_sufficient_with_caveat"}:
        return "sufficient evidence"
    if grounding_status == "evidence_access_blocked":
        return "access policy block"
    if grounding_status == "evidence_poison_blocked":
        return "poison policy block"
    if grounding_status == "evidence_privacy_blocked":
        return "privacy policy block"
    if grounding_status == "evidence_contradicted":
        return "unresolved contradiction"
    if grounding_status == "evidence_stale":
        return "stale evidence without fresh source"
    if grounding_status == "defer_until_retrieval_available":
        return "retrieval unavailable"
    if grounding_status == "ask_clarification":
        return "clarification required"
    if grounding_status == "refuse_unsupported":
        return "unsupported public claim"
    if loop_iteration_count >= max_iterations:
        return "max iterations reached"
    return "more evidence needed"


# ---------------------------------------------------------------------------
# Validation and summary
# ---------------------------------------------------------------------------


def validate_self_rag_loop_packet_v1(packet: Any) -> bool:
    normalized = to_self_rag_loop_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        raise ValidationError("packet_must_be_mapping")

    forbidden_field = _contains_forbidden_field(normalized)
    if forbidden_field:
        raise ValidationError(f"forbidden_field_present:{forbidden_field}")
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_phrase_present")

    self_rag_loop_packet_id = _safe_text(normalized.get("self_rag_loop_packet_id"))
    query_summary = _safe_text(normalized.get("query_summary"))
    initial_query_class = _safe_text(normalized.get("initial_query_class"))
    initial_routing_target = _safe_text(normalized.get("initial_routing_target"))
    grounding_status = _safe_text(normalized.get("grounding_status"))
    citation_readiness = _safe_text(normalized.get("citation_readiness"))
    context_budget_status = _safe_text(normalized.get("context_budget_status"))
    reroute_target = _safe_text(normalized.get("reroute_target"))
    fallback_behavior = _safe_text(normalized.get("fallback_behavior"))
    recommended_answer_action = _safe_text(normalized.get("recommended_answer_action"))

    if not self_rag_loop_packet_id:
        raise ValidationError("missing_self_rag_loop_packet_id")
    if not query_summary:
        raise ValidationError("missing_query_summary")
    if initial_query_class not in ALLOWED_QUERY_CLASSES_V1:
        raise ValidationError("unknown_initial_query_class")
    if initial_routing_target not in ALLOWED_REROUTE_TARGETS_V1:
        raise ValidationError("unknown_initial_routing_target")
    if _safe_text(normalized.get("loop_stage")) not in ALLOWED_LOOP_STAGES_V1:
        raise ValidationError("unknown_loop_stage")
    if grounding_status not in ALLOWED_LOOP_OUTCOMES_V1:
        raise ValidationError("unknown_loop_outcome")
    if citation_readiness not in ALLOWED_LOOP_OUTCOMES_V1:
        raise ValidationError("unknown_loop_outcome")
    if context_budget_status not in ALLOWED_CONTEXT_BUDGET_STATUSES_V1:
        raise ValidationError("unknown_context_budget_status")
    if fallback_behavior not in ALLOWED_FALLBACK_BEHAVIORS_V1:
        raise ValidationError("unknown_fallback_behavior")
    if reroute_target not in ALLOWED_REROUTE_TARGETS_V1:
        raise ValidationError("unknown_reroute_target")

    loop_iteration_count = int(normalized.get("loop_iteration_count") or 0)
    max_iterations = int(normalized.get("max_iterations") or 0)
    if loop_iteration_count < 0:
        raise ValidationError("loop_iteration_count_must_be_non_negative")
    if max_iterations < 0:
        raise ValidationError("max_iterations_must_be_non_negative")
    if loop_iteration_count > max_iterations:
        raise ValidationError("loop_iteration_count_greater_than_max_iterations")

    if _safe_bool(normalized.get("runtime_authority")):
        raise ValidationError("runtime_authority_must_be_false")
    if _safe_bool(normalized.get("writes_state")):
        raise ValidationError("writes_state_must_be_false")
    if _safe_bool(normalized.get("model_provider_used")):
        raise ValidationError("model_provider_used_must_be_false")
    if _safe_bool(normalized.get("public_claim_allowed")):
        raise ValidationError("public_claim_allowed_must_be_false")
    if _safe_bool(normalized.get("proof_claim_allowed")):
        raise ValidationError("proof_claim_allowed_must_be_false")
    if _safe_bool(normalized.get("learning_claimed")):
        raise ValidationError("learning_claimed_must_be_false")

    candidates = [_safe_mapping(candidate) for candidate in normalized.get("evidence_candidates") or []]
    accepted_refs = _safe_str_list(normalized.get("accepted_evidence_refs"))
    rejected_refs = _safe_str_list(normalized.get("rejected_evidence_refs"))
    visited_targets = _safe_str_list_preserve_order(normalized.get("visited_routing_targets"))

    for candidate in candidates:
        status = _candidate_status(candidate)
        if status not in ALLOWED_CANDIDATE_STATUS_HINTS_V1:
            raise ValidationError("unknown_candidate_status")
        access = _candidate_access_status(candidate)
        if access not in ALLOWED_ACCESS_STATUS_HINTS_V1:
            raise ValidationError("unknown_candidate_access_status")
        freshness = _candidate_freshness_status(candidate)
        if freshness not in ALLOWED_FRESHNESS_STATUS_HINTS_V1:
            raise ValidationError("unknown_candidate_freshness_status")
        privacy = _candidate_privacy_status(candidate)
        if privacy not in ALLOWED_PRIVACY_STATUS_HINTS_V1:
            raise ValidationError("unknown_candidate_privacy_status")
        poison = _candidate_poison_status(candidate)
        if poison not in ALLOWED_POISON_STATUS_HINTS_V1:
            raise ValidationError("unknown_candidate_poison_status")

    access_blocked = _detected_access_blocked_candidates(candidates)
    poison_blocked = _detected_poison_blocked_candidates(candidates)
    privacy_blocked = _detected_privacy_blocked_candidates(candidates)
    contradicted = _detected_contradicted_candidates(candidates)
    stale = _detected_stale_candidates(candidates)
    accepted = _detected_accepted_candidates(candidates)

    if any(ref in access_blocked for ref in accepted_refs):
        raise ValidationError("accepted_access_blocked_evidence")
    if any(ref in poison_blocked for ref in accepted_refs):
        raise ValidationError("accepted_poison_blocked_evidence")
    if any(ref in privacy_blocked for ref in accepted_refs):
        raise ValidationError("accepted_privacy_blocked_evidence")

    if _query_requests_public_claim(normalized) and _has_private_candidate(candidates):
        raise ValidationError("public_claim_from_private_evidence_blocked")

    if contradicted and grounding_status != "evidence_contradicted":
        raise ValidationError("contradiction_must_not_be_hidden")

    if stale and grounding_status == "evidence_sufficient":
        if _status_text(normalized.get("recommended_answer_action")) in {"use_existing_graph_only", "answer_with_caveat"} or _status_text(normalized.get("fallback_behavior")) == "use_existing_graph_only":
            raise ValidationError("stale_evidence_treated_as_current_without_caveat")

    if _query_requires_citation(normalized) and not accepted_refs:
        raise ValidationError("citation_required_but_no_accepted_evidence_refs")

    if _status_text(normalized.get("context_budget_status")) == "over_budget":
        if not any(token in _normalize_text(recommended_answer_action) for token in ("compress", "defer", "clarif", "question")) and not any(token in _normalize_text(normalized.get("recommended_next_check")) for token in ("compress", "defer", "clarif", "question")):
            raise ValidationError("over_budget_requires_compression_defer_or_clarification")

    if _safe_bool(normalized.get("reroute_recommended")):
        if reroute_target == "no_reroute_stop":
            raise ValidationError("reroute_recommended_when_max_reached_or_stop")
        if loop_iteration_count >= max_iterations:
            raise ValidationError("reroute_recommended_when_max_reached")

    if visited_targets and len(visited_targets) != len(set(visited_targets)) and _safe_bool(normalized.get("reroute_recommended")):
        if visited_targets[-1] == reroute_target:
            raise ValidationError("repeated_failed_route_loop")

    if accepted_refs and any(ref in rejected_refs for ref in accepted_refs):
        raise ValidationError("accepted_and_rejected_refs_conflict")

    if _safe_text(normalized.get("fallback_behavior")) == "unknown_fallback":
        raise ValidationError("unknown_fallback_behavior")

    # Keep derived sets exercised for fail-closed checks.
    _ = access_blocked
    _ = poison_blocked
    _ = privacy_blocked
    _ = contradicted
    _ = stale
    _ = accepted

    return True



def summarize_self_rag_loop_packet_v1(packet: Any) -> dict[str, Any]:
    validate_self_rag_loop_packet_v1(packet)
    normalized = to_self_rag_loop_json_safe_v1(packet)
    mapping = dict(normalized)
    candidates = [_safe_mapping(candidate) for candidate in mapping.get("evidence_candidates") or []]
    return {
        "summary_type": SUMMARY_TYPE_V1,
        "self_rag_loop_packet_id": _safe_text(mapping.get("self_rag_loop_packet_id")),
        "query_summary": _safe_text(mapping.get("query_summary")),
        "initial_query_class": _safe_text(mapping.get("initial_query_class")),
        "initial_routing_target": _safe_text(mapping.get("initial_routing_target")),
        "loop_stage": _safe_text(mapping.get("loop_stage")),
        "loop_iteration_count": int(mapping.get("loop_iteration_count") or 0),
        "max_iterations": int(mapping.get("max_iterations") or 0),
        "visited_routing_target_count": len(_safe_str_list_preserve_order(mapping.get("visited_routing_targets"))),
        "evidence_candidate_count": len(candidates),
        "accepted_evidence_ref_count": len(_safe_str_list(mapping.get("accepted_evidence_refs"))),
        "rejected_evidence_ref_count": len(_safe_str_list(mapping.get("rejected_evidence_refs"))),
        "missing_evidence_summary": _safe_text(mapping.get("missing_evidence_summary")),
        "contradiction_summary": _safe_text(mapping.get("contradiction_summary")),
        "stale_evidence_summary": _safe_text(mapping.get("stale_evidence_summary")),
        "access_block_summary": _safe_text(mapping.get("access_block_summary")),
        "poison_block_summary": _safe_text(mapping.get("poison_block_summary")),
        "privacy_block_summary": _safe_text(mapping.get("privacy_block_summary")),
        "grounding_status": _safe_text(mapping.get("grounding_status")),
        "citation_readiness": _safe_text(mapping.get("citation_readiness")),
        "context_budget_status": _safe_text(mapping.get("context_budget_status")),
        "reroute_recommended": _safe_bool(mapping.get("reroute_recommended")),
        "reroute_target": _safe_text(mapping.get("reroute_target")),
        "stop_reason": _safe_text(mapping.get("stop_reason")),
        "fallback_behavior": _safe_text(mapping.get("fallback_behavior")),
        "recommended_answer_action": _safe_text(mapping.get("recommended_answer_action")),
        "recommended_next_check": _safe_text(mapping.get("recommended_next_check")),
        "accepted_evidence_refs": _safe_str_list(mapping.get("accepted_evidence_refs")),
        "rejected_evidence_refs": _safe_str_list(mapping.get("rejected_evidence_refs")),
        "safe_metadata": _json_safe(mapping.get("safe_metadata", DEFAULT_SAFE_METADATA_V1)),
    }


# ---------------------------------------------------------------------------
# Initial examples
# ---------------------------------------------------------------------------


def build_initial_self_rag_loop_examples_v1() -> list[dict[str, Any]]:
    examples = [
        build_self_rag_loop_packet_v1(
            self_rag_loop_packet_id="evidence_sufficient_first_pass",
            query_summary="Answer with grounded metadata-only evidence on the first pass.",
            initial_query_class="general_reasoning_query",
            initial_routing_target="source_evidence_graph_lookup",
            loop_iteration_count=0,
            max_iterations=2,
            visited_routing_targets=["source_evidence_graph_lookup"],
            evidence_candidates=[
                {
                    "evidence_ref": "evidence:1",
                    "candidate_status": "accepted",
                    "source_type": "source_graph",
                    "access_status": "access_allowed",
                    "privacy_status": "public",
                    "poison_status": "clean",
                    "freshness_status": "current",
                    "summary": "grounded evidence",
                    "citation_required": False,
                    "public_safe": True,
                }
            ],
            accepted_evidence_refs=["evidence:1"],
            grounding_status="evidence_sufficient",
            citation_readiness="evidence_sufficient",
            context_budget_status="within_budget",
            reroute_recommended=False,
            reroute_target="no_reroute_stop",
            stop_reason="sufficient evidence",
            fallback_behavior="use_existing_graph_only",
            recommended_answer_action="use_existing_graph_only",
            recommended_next_check="no additional evidence check needed",
            safe_metadata={"example_name": "evidence_sufficient_first_pass"},
        ),
        build_self_rag_loop_packet_v1(
            self_rag_loop_packet_id="missing_citation_source_triggers_one_reroute",
            query_summary="The answer needs a citation source that is not yet accepted.",
            initial_query_class="source_graph_query",
            initial_routing_target="source_evidence_graph_lookup",
            loop_iteration_count=0,
            max_iterations=2,
            visited_routing_targets=["source_evidence_graph_lookup"],
            evidence_candidates=[
                {
                    "evidence_ref": "evidence:2",
                    "candidate_status": "missing",
                    "source_type": "source_graph",
                    "access_status": "access_allowed",
                    "privacy_status": "public",
                    "poison_status": "clean",
                    "freshness_status": "unknown",
                    "citation_required": True,
                    "summary": "missing citation source",
                    "public_safe": True,
                }
            ],
            missing_evidence_summary="citation source missing",
            grounding_status="evidence_missing",
            citation_readiness="evidence_missing",
            context_budget_status="within_budget",
            reroute_recommended=True,
            reroute_target="source_evidence_graph_lookup",
            stop_reason="more evidence needed",
            fallback_behavior="request_source_upload",
            recommended_answer_action="request_source_upload",
            recommended_next_check="try source_evidence_graph_lookup if within budget",
            safe_metadata={"example_name": "missing_citation_source_triggers_one_reroute", "citation_required": True},
        ),
        build_self_rag_loop_packet_v1(
            self_rag_loop_packet_id="stale_support_reroute_then_caveat_when_unavailable",
            query_summary="A stale supporting source should reroute once, then caveat if no fresh source exists.",
            initial_query_class="currentness_sensitive_query",
            initial_routing_target="future_web_search",
            loop_iteration_count=1,
            max_iterations=2,
            visited_routing_targets=["future_web_search"],
            evidence_candidates=[
                {
                    "evidence_ref": "evidence:3",
                    "candidate_status": "stale",
                    "source_type": "source_graph",
                    "access_status": "access_allowed",
                    "privacy_status": "public",
                    "poison_status": "clean",
                    "freshness_status": "stale",
                    "summary": "stale support",
                    "public_safe": True,
                }
            ],
            accepted_evidence_refs=["evidence:3"],
            stale_evidence_summary="stale support needs caveat",
            grounding_status="evidence_stale",
            citation_readiness="evidence_stale",
            context_budget_status="within_budget",
            reroute_recommended=True,
            reroute_target="future_web_search",
            stop_reason="stale evidence without fresh source",
            fallback_behavior="answer_with_caveat",
            recommended_answer_action="answer_with_caveat",
            recommended_next_check="reroute only if a fresh source exists; otherwise caveat or defer",
            safe_metadata={"example_name": "stale_support_reroute_then_caveat_when_unavailable", "query_requires_currentness": True},
        ),
        build_self_rag_loop_packet_v1(
            self_rag_loop_packet_id="contradictory_evidence_preserved_no_forced_winner",
            query_summary="Keep contradictory evidence visible without forcing a winner.",
            initial_query_class="general_reasoning_query",
            initial_routing_target="source_evidence_graph_lookup",
            loop_iteration_count=1,
            max_iterations=2,
            visited_routing_targets=["source_evidence_graph_lookup"],
            evidence_candidates=[
                {
                    "evidence_ref": "evidence:4a",
                    "candidate_status": "accepted",
                    "source_type": "source_graph",
                    "access_status": "access_allowed",
                    "privacy_status": "public",
                    "poison_status": "clean",
                    "freshness_status": "current",
                    "summary": "claim A",
                    "contradiction_present": True,
                    "public_safe": True,
                },
                {
                    "evidence_ref": "evidence:4b",
                    "candidate_status": "contradicted",
                    "source_type": "source_graph",
                    "access_status": "access_allowed",
                    "privacy_status": "public",
                    "poison_status": "clean",
                    "freshness_status": "current",
                    "summary": "claim B",
                    "contradiction_present": True,
                    "public_safe": True,
                },
            ],
            accepted_evidence_refs=["evidence:4a"],
            rejected_evidence_refs=["evidence:4b"],
            contradiction_summary="contradiction preserved",
            grounding_status="evidence_contradicted",
            citation_readiness="evidence_contradicted",
            context_budget_status="within_budget",
            reroute_recommended=False,
            reroute_target="no_reroute_stop",
            stop_reason="unresolved contradiction",
            fallback_behavior="return_unsupported_claim",
            recommended_answer_action="return_unsupported_claim",
            recommended_next_check="preserve contradiction and avoid forced winner",
            safe_metadata={"example_name": "contradictory_evidence_preserved_no_forced_winner"},
        ),
        build_self_rag_loop_packet_v1(
            self_rag_loop_packet_id="access_blocked_source_stops_loop",
            query_summary="An access-blocked source must stop the loop.",
            initial_query_class="uploaded_document_query",
            initial_routing_target="uploaded_file_retrieval",
            loop_iteration_count=0,
            max_iterations=2,
            visited_routing_targets=["uploaded_file_retrieval"],
            evidence_candidates=[
                {
                    "evidence_ref": "evidence:5",
                    "candidate_status": "access_blocked",
                    "source_type": "uploaded_file",
                    "access_status": "access_restricted",
                    "privacy_status": "restricted",
                    "poison_status": "clean",
                    "freshness_status": "current",
                    "summary": "blocked source",
                }
            ],
            access_block_summary="access blocked source",
            grounding_status="evidence_access_blocked",
            citation_readiness="evidence_access_blocked",
            context_budget_status="within_budget",
            reroute_recommended=False,
            reroute_target="no_reroute_stop",
            stop_reason="access policy block",
            fallback_behavior="block_due_access_policy",
            recommended_answer_action="block_due_access_policy",
            recommended_next_check="respect access policy and stop reroute attempts",
            safe_metadata={"example_name": "access_blocked_source_stops_loop"},
        ),
        build_self_rag_loop_packet_v1(
            self_rag_loop_packet_id="poison_blocked_source_stops_loop",
            query_summary="A poison-blocked source must stop the loop.",
            initial_query_class="uploaded_document_query",
            initial_routing_target="uploaded_file_retrieval",
            loop_iteration_count=0,
            max_iterations=2,
            visited_routing_targets=["uploaded_file_retrieval"],
            evidence_candidates=[
                {
                    "evidence_ref": "evidence:6",
                    "candidate_status": "poison_blocked",
                    "source_type": "uploaded_file",
                    "access_status": "access_allowed",
                    "privacy_status": "public",
                    "poison_status": "poisoned",
                    "freshness_status": "current",
                    "summary": "poisoned source",
                }
            ],
            poison_block_summary="poison blocked source",
            grounding_status="evidence_poison_blocked",
            citation_readiness="evidence_poison_blocked",
            context_budget_status="within_budget",
            reroute_recommended=False,
            reroute_target="no_reroute_stop",
            stop_reason="poison policy block",
            fallback_behavior="block_due_poison_policy",
            recommended_answer_action="block_due_poison_policy",
            recommended_next_check="respect poison policy and stop reroute attempts",
            safe_metadata={"example_name": "poison_blocked_source_stops_loop"},
        ),
        build_self_rag_loop_packet_v1(
            self_rag_loop_packet_id="public_claim_unsupported_after_max_iterations_refused",
            query_summary="A public claim should be refused after the loop budget is exhausted.",
            initial_query_class="public_claim_query",
            initial_routing_target="source_evidence_graph_lookup",
            loop_iteration_count=2,
            max_iterations=2,
            visited_routing_targets=["source_evidence_graph_lookup", "future_web_search"],
            evidence_candidates=[],
            missing_evidence_summary="no acceptable public evidence",
            grounding_status="refuse_unsupported",
            citation_readiness="refuse_unsupported",
            context_budget_status="within_budget",
            reroute_recommended=False,
            reroute_target="no_reroute_stop",
            stop_reason="unsupported public claim",
            fallback_behavior="refuse_public_claim",
            recommended_answer_action="return_unsupported_claim",
            recommended_next_check="refuse public or unsupported claim",
            safe_metadata={"example_name": "public_claim_unsupported_after_max_iterations_refused", "public_claim_requested": True},
        ),
        build_self_rag_loop_packet_v1(
            self_rag_loop_packet_id="currentness_sensitive_query_deferred_no_current_source",
            query_summary="This currentness-sensitive query has no current source.",
            initial_query_class="currentness_sensitive_query",
            initial_routing_target="future_web_search",
            loop_iteration_count=1,
            max_iterations=2,
            visited_routing_targets=["future_web_search"],
            evidence_candidates=[
                {
                    "evidence_ref": "evidence:8",
                    "candidate_status": "missing",
                    "source_type": "source_graph",
                    "access_status": "access_allowed",
                    "privacy_status": "public",
                    "poison_status": "clean",
                    "freshness_status": "stale",
                    "summary": "no current source",
                }
            ],
            missing_evidence_summary="no current source",
            grounding_status="defer_until_retrieval_available",
            citation_readiness="defer_until_retrieval_available",
            context_budget_status="within_budget",
            reroute_recommended=False,
            reroute_target="no_reroute_stop",
            stop_reason="retrieval unavailable",
            fallback_behavior="defer_until_retrieval_available",
            recommended_answer_action="defer_until_retrieval_available",
            recommended_next_check="defer until retrieval is available",
            safe_metadata={"example_name": "currentness_sensitive_query_deferred_no_current_source", "query_requires_currentness": True},
        ),
        build_self_rag_loop_packet_v1(
            self_rag_loop_packet_id="context_budget_exceeded_compression_recommended",
            query_summary="The context budget is exceeded and compression is recommended.",
            initial_query_class="general_reasoning_query",
            initial_routing_target="source_evidence_graph_lookup",
            loop_iteration_count=1,
            max_iterations=2,
            visited_routing_targets=["source_evidence_graph_lookup"],
            evidence_candidates=[
                {
                    "evidence_ref": "evidence:9",
                    "candidate_status": "accepted",
                    "source_type": "source_graph",
                    "access_status": "access_allowed",
                    "privacy_status": "public",
                    "poison_status": "clean",
                    "freshness_status": "current",
                    "summary": "too much context",
                    "public_safe": True,
                }
            ],
            accepted_evidence_refs=["evidence:9"],
            grounding_status="more_evidence_needed",
            citation_readiness="more_evidence_needed",
            context_budget_status="over_budget",
            reroute_recommended=True,
            reroute_target="same_route_once",
            stop_reason="max iterations reached",
            fallback_behavior="ask_clarifying_question",
            recommended_answer_action="ask_clarifying_question",
            recommended_next_check="compress context or defer before another pass",
            safe_metadata={"example_name": "context_budget_exceeded_compression_recommended"},
        ),
        build_self_rag_loop_packet_v1(
            self_rag_loop_packet_id="repeated_failed_reroute_path_stops_loop",
            query_summary="Repeatedly rerouting the same failed path should stop the loop.",
            initial_query_class="source_graph_query",
            initial_routing_target="source_evidence_graph_lookup",
            loop_iteration_count=2,
            max_iterations=2,
            visited_routing_targets=["source_evidence_graph_lookup", "source_evidence_graph_lookup"],
            evidence_candidates=[
                {
                    "evidence_ref": "evidence:10",
                    "candidate_status": "missing",
                    "source_type": "source_graph",
                    "access_status": "access_allowed",
                    "privacy_status": "public",
                    "poison_status": "clean",
                    "freshness_status": "unknown",
                    "summary": "repeat failure",
                    "public_safe": True,
                }
            ],
            missing_evidence_summary="repeated route failure",
            grounding_status="more_evidence_needed",
            citation_readiness="more_evidence_needed",
            context_budget_status="within_budget",
            reroute_recommended=False,
            reroute_target="no_reroute_stop",
            stop_reason="max iterations reached",
            fallback_behavior="request_source_upload",
            recommended_answer_action="request_source_upload",
            recommended_next_check="stop because the same failed path repeated",
            safe_metadata={"example_name": "repeated_failed_reroute_path_stops_loop"},
        ),
    ]
    return examples
