"""Metadata-only RAG query routing boundary helpers v1.

This module classifies query intent and selects safe evidence-routing targets
from explicit metadata only. It does not retrieve documents, vectorize files,
read files, create indexes, call models/providers, write memory, touch `.weslr`,
or assemble final answers/citations.

It is pure, deterministic, import-safe, and fail-closed.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

HELPER_TYPE_V1 = "rag_query_routing_boundary_v1"
PACKET_TYPE_V1 = "rag_query_routing_packet_v1"
SUMMARY_TYPE_V1 = "rag_query_routing_packet_summary_v1"

ALLOWED_QUERY_CLASSES_V1 = {
    "general_reasoning_query",
    "personal_memory_query",
    "uploaded_document_query",
    "source_grounded_claim_query",
    "currentness_sensitive_query",
    "technical_documentation_query",
    "legal_or_policy_query",
    "medical_or_safety_query",
    "public_claim_query",
    "energy_signal_query",
    "artifact_or_code_query",
    "unknown_query",
}

ALLOWED_ROUTING_TARGETS_V1 = {
    "pure_reasoning",
    "memory_retrieval",
    "uploaded_file_retrieval",
    "source_evidence_graph_lookup",
    "artifact_provenance_lookup",
    "signal_metadata_lookup",
    "forecast_error_ledger_lookup",
    "capability_maturity_lookup",
    "future_web_search",
    "future_document_index",
    "clarification_required",
    "unsupported_answer_refusal",
    "blocked_by_access_policy",
    "blocked_by_poison_policy",
    "refuse_public_claim",
    "defer_until_retrieval_available",
}

ALLOWED_FALLBACK_MODES_V1 = {
    "answer_from_general_reasoning_with_caveat",
    "ask_clarifying_question",
    "request_source_upload",
    "use_existing_graph_only",
    "return_unsupported_claim",
    "refuse_public_claim",
    "block_due_access_policy",
    "block_due_poison_policy",
    "defer_until_retrieval_available",
}

ROUTING_TARGET_CATEGORIES_V1 = {
    "pure_reasoning": "reasoning",
    "memory_retrieval": "memory",
    "uploaded_file_retrieval": "file",
    "source_evidence_graph_lookup": "graph",
    "artifact_provenance_lookup": "graph",
    "signal_metadata_lookup": "signal",
    "forecast_error_ledger_lookup": "signal",
    "capability_maturity_lookup": "maturity",
    "future_web_search": "future",
    "future_document_index": "future",
    "clarification_required": "control",
    "unsupported_answer_refusal": "control",
    "blocked_by_access_policy": "policy",
    "blocked_by_poison_policy": "policy",
    "refuse_public_claim": "policy",
    "defer_until_retrieval_available": "future",
}

ALLOWED_ACCESS_POLICY_STATUS_V1 = {
    "allowed",
    "access_allowed",
    "restricted",
    "access_restricted",
    "blocked",
    "access_blocked",
    "unknown",
}

ALLOWED_POISON_POLICY_STATUS_V1 = {
    "clean",
    "safe",
    "quarantined",
    "poisoned",
    "blocked",
    "poison_blocked",
    "unknown",
}

ALLOWED_PRIVACY_STATUS_V1 = {
    "public",
    "private",
    "restricted",
    "unknown",
    "low_sensitivity",
    "medium_sensitivity",
    "high_sensitivity",
    "restricted_sensitive",
}

ALLOWED_SOURCE_FRESHNESS_REQUIREMENTS_V1 = {
    "not_required",
    "current",
    "fresh",
    "stale_ok",
    "unknown",
}

ALLOWED_CITATION_REQUIREMENTS_V1 = {
    "not_required",
    "preferred",
    "required",
    "blocked",
    "unknown",
}

ALLOWED_CLAIM_GROUNDING_REQUIREMENTS_V1 = {
    "not_required",
    "preferred",
    "required",
    "blocked",
    "unknown",
}

ALLOWED_RUNTIME_AUTHORITY_STATUSES_V1 = {
    "no_authority",
    "metadata_only",
    "blocked",
}

ALLOWED_BOOL_FLAGS_V1 = {
    "runtime_authority",
    "writes_state",
    "model_provider_used",
    "public_claim_allowed",
    "proof_claim_allowed",
    "learning_claimed",
}

FORBIDDEN_FIELD_PHRASES_V1 = (
    "hidden prompt",
    "raw private",
    "private data",
    "api key",
    "credential",
    "password",
)
FORBIDDEN_FIELD_SINGLE_TOKENS_V1 = {
    "secret",
    "token",
    "key",
}

FORBIDDEN_CLAIM_PHRASES_V1 = (
    "hallucination elimination",
    "hallucination-free",
    "no hallucinations",
    "public readiness",
    "public ready",
    "proof certainty",
    "truth certainty",
    "proof claim",
    "truth claim",
    "official proof",
    "official truth",
)

GENERAL_REASONING_HINTS_V1 = (
    "why",
    "how does",
    "explain",
    "concept",
    "conceptual",
    "general reasoning",
    "what is",
    "compare",
    "difference",
)

MEMORY_HINTS_V1 = (
    "my",
    "our",
    "remember",
    "previous",
    "earlier",
    "project history",
    "what did we decide",
    "last time",
    "before",
    "continuity",
)

FILE_HINTS_V1 = (
    "attached",
    "upload",
    "uploaded",
    "file",
    "document",
    "pdf",
    "spreadsheet",
    "worksheet",
    "csv",
    "image",
    "diagram",
)

CURRENTNESS_HINTS_V1 = (
    "current",
    "latest",
    "today",
    "this week",
    "recent",
    "up to date",
    "now",
    "current law",
    "law today",
)

PUBLIC_CLAIM_HINTS_V1 = (
    "public",
    "website",
    "claim",
    "launch",
    "readiness",
    "official",
    "public-facing",
)

ENERGY_HINTS_V1 = (
    "energy",
    "grid",
    "battery",
    "solar",
    "load",
    "forecast",
    "meter",
    "signal",
    "demand",
)

ARTIFACT_HINTS_V1 = (
    "code",
    "repo",
    "commit",
    "patch",
    "function",
    "class",
    "file",
    "module",
    "artifact",
)

LEGAL_HINTS_V1 = (
    "law",
    "legal",
    "policy",
    "regulation",
    "compliance",
    "contract",
    "terms",
)

MEDICAL_SAFETY_HINTS_V1 = (
    "medical",
    "safety",
    "health",
    "diagnosis",
    "emergency",
    "injury",
    "risk",
)

CONTRADICTION_HINTS_V1 = (
    "contradict",
    "conflict",
    "inconsistent",
    "disagree",
    "discrepancy",
    "two sources",
)

DEFAULT_SAFE_METADATA_V1 = {
    "metadata_only": True,
    "internal_only": True,
}

DEFAULT_QUERY_CLASS_V1 = "unknown_query"
DEFAULT_ROUTING_TARGET_V1 = "clarification_required"
DEFAULT_FALLBACK_V1 = "ask_clarifying_question"
DEFAULT_ACCESS_POLICY_STATUS_V1 = "unknown"
DEFAULT_POISON_POLICY_STATUS_V1 = "unknown"
DEFAULT_PRIVACY_STATUS_V1 = "unknown"
DEFAULT_SOURCE_FRESHNESS_REQUIREMENT_V1 = "not_required"
DEFAULT_CITATION_REQUIREMENT_V1 = "not_required"
DEFAULT_CLAIM_GROUNDING_REQUIREMENT_V1 = "not_required"
DEFAULT_REASON_FOR_SELECTION_V1 = "metadata-only routing decision"
DEFAULT_RECOMMENDED_NEXT_CHECK_V1 = "classify the query and route only from explicit metadata before any retrieval, citation, or answer assembly"


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



def _safe_bool(value: Any) -> bool:
    return bool(value) is True



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



def to_rag_query_routing_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def _contains_forbidden_field(value: Any) -> str:
    if value is None:
        return ""
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            key_raw = _safe_text(key).lower()
            if key_text in FORBIDDEN_FIELD_PHRASES_V1 or key_raw in {phrase.replace(" ", "_") for phrase in FORBIDDEN_FIELD_PHRASES_V1}:
                return _safe_text(key)
            key_tokens = set(key_text.split()) | set(key_raw.replace("_", " ").split())
            if key_tokens & FORBIDDEN_FIELD_SINGLE_TOKENS_V1:
                return _safe_text(key)
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
        return ""
    if isinstance(value, (list, tuple, set)):
        for item in value:
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
        return ""
    return ""



def _contains_forbidden_claim_marker(value: Any) -> bool:
    if value is None:
        return False
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_forbidden_claim_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_claim_marker(item) for item in value)
    text = _normalize_text(value)
    return any(phrase in text for phrase in FORBIDDEN_CLAIM_PHRASES_V1)



def _text_has_any(text: Any, hints: tuple[str, ...]) -> bool:
    normalized = _normalize_text(text)
    return any(hint in normalized for hint in hints)



def _list_has_any(items: Any, hints: tuple[str, ...]) -> bool:
    return any(_text_has_any(item, hints) for item in _safe_list(items))



def _classify_by_summary(query_summary: str, requested_claims: list[str]) -> str:
    text = _normalize_text(query_summary)
    claims_blob = " ".join(_normalize_text(item) for item in requested_claims)

    if _text_has_any(text, MEMORY_HINTS_V1):
        return "personal_memory_query"
    if _text_has_any(text, FILE_HINTS_V1):
        return "uploaded_document_query"
    if _text_has_any(text, CURRENTNESS_HINTS_V1) or "current" in claims_blob or "latest" in claims_blob:
        return "currentness_sensitive_query"
    if _text_has_any(text, PUBLIC_CLAIM_HINTS_V1):
        return "public_claim_query"
    if _text_has_any(text, ENERGY_HINTS_V1):
        return "energy_signal_query"
    if _text_has_any(text, ARTIFACT_HINTS_V1):
        return "artifact_or_code_query"
    if _text_has_any(text, LEGAL_HINTS_V1):
        return "legal_or_policy_query"
    if _text_has_any(text, MEDICAL_SAFETY_HINTS_V1):
        return "medical_or_safety_query"
    if _text_has_any(text, CONTRADICTION_HINTS_V1):
        return "source_grounded_claim_query"
    if _text_has_any(text, GENERAL_REASONING_HINTS_V1):
        return "general_reasoning_query"
    if claims_blob:
        if any(word in claims_blob for word in ("public", "website", "claim")):
            return "public_claim_query"
        if any(word in claims_blob for word in ("law", "policy", "regulation")):
            return "legal_or_policy_query"
        if any(word in claims_blob for word in ("medical", "safety", "risk")):
            return "medical_or_safety_query"
        if any(word in claims_blob for word in ("energy", "grid", "battery", "signal")):
            return "energy_signal_query"
    return "unknown_query"


# ---------------------------------------------------------------------------
# Public APIs
# ---------------------------------------------------------------------------


def classify_rag_query_v1(
    *,
    query_summary: str = "",
    requested_claims: Any = None,
    requires_grounding: bool = False,
    requires_currentness: bool = False,
    requires_private_data: bool = False,
    requires_user_file_access: bool = False,
    requires_web_access: bool = False,
    requires_memory_access: bool = False,
    requires_source_evidence_graph: bool = False,
    contradiction_detected: bool = False,
    energy_signal_present: bool = False,
    artifact_or_code_present: bool = False,
    public_claim_present: bool = False,
    technical_documentation_present: bool = False,
    legal_or_policy_present: bool = False,
    medical_or_safety_present: bool = False,
) -> str:
    claims = _safe_str_list(requested_claims)
    summary = _normalize_text(query_summary)

    if requires_memory_access or _text_has_any(summary, MEMORY_HINTS_V1):
        return "personal_memory_query"
    if requires_user_file_access or _text_has_any(summary, FILE_HINTS_V1):
        return "uploaded_document_query"
    if requires_currentness or requires_web_access or _text_has_any(summary, CURRENTNESS_HINTS_V1):
        return "currentness_sensitive_query"
    if public_claim_present or _text_has_any(summary, PUBLIC_CLAIM_HINTS_V1):
        return "public_claim_query"
    if energy_signal_present or _text_has_any(summary, ENERGY_HINTS_V1):
        return "energy_signal_query"
    if artifact_or_code_present or _text_has_any(summary, ARTIFACT_HINTS_V1):
        return "artifact_or_code_query"
    if legal_or_policy_present or _text_has_any(summary, LEGAL_HINTS_V1):
        return "legal_or_policy_query"
    if medical_or_safety_present or _text_has_any(summary, MEDICAL_SAFETY_HINTS_V1):
        return "medical_or_safety_query"
    if contradiction_detected or _text_has_any(summary, CONTRADICTION_HINTS_V1):
        return "source_grounded_claim_query"
    if requires_source_evidence_graph or requires_grounding:
        return "source_grounded_claim_query"

    classified = _classify_by_summary(query_summary, claims)
    if classified != "unknown_query":
        return classified
    return "general_reasoning_query" if summary else "unknown_query"



def select_rag_routing_target_v1(
    *,
    query_class: str,
    query_summary: str = "",
    requested_claims: Any = None,
    requires_grounding: bool = False,
    requires_currentness: bool = False,
    requires_private_data: bool = False,
    requires_user_file_access: bool = False,
    requires_web_access: bool = False,
    requires_memory_access: bool = False,
    requires_source_evidence_graph: bool = False,
    contradiction_detected: bool = False,
    access_policy_status: str = DEFAULT_ACCESS_POLICY_STATUS_V1,
    poison_policy_status: str = DEFAULT_POISON_POLICY_STATUS_V1,
    privacy_status: str = DEFAULT_PRIVACY_STATUS_V1,
    citation_requirement: str = DEFAULT_CITATION_REQUIREMENT_V1,
    claim_grounding_requirement: str = DEFAULT_CLAIM_GROUNDING_REQUIREMENT_V1,
    source_freshness_requirement: str = DEFAULT_SOURCE_FRESHNESS_REQUIREMENT_V1,
    allowed_routing_targets: Any = None,
    blocked_routing_targets: Any = None,
    fallback_behavior: str = DEFAULT_FALLBACK_V1,
) -> str:
    allowed = _safe_str_list(allowed_routing_targets)
    blocked = set(_safe_str_list(blocked_routing_targets))
    summary = _normalize_text(query_summary)
    claims = _safe_str_list(requested_claims)
    qclass = _safe_text(query_class)

    if _text_has_any(poison_policy_status, ("blocked", "poison", "quarantined", "poisoned")):
        return "blocked_by_poison_policy"
    if _text_has_any(access_policy_status, ("blocked", "restricted", "access blocked", "access restricted")):
        return "blocked_by_access_policy"
    if requires_private_data and _text_has_any(privacy_status, ("blocked", "private", "restricted")):
        return "blocked_by_access_policy"

    if qclass == "personal_memory_query":
        if requires_memory_access and access_policy_status in {"allowed", "access_allowed", "unknown"}:
            return "memory_retrieval"
        return "clarification_required" if fallback_behavior == "ask_clarifying_question" else "blocked_by_access_policy"

    if qclass == "uploaded_document_query":
        if requires_user_file_access and access_policy_status in {"allowed", "access_allowed", "unknown"} and privacy_status not in {"private", "restricted"}:
            return "uploaded_file_retrieval"
        return "blocked_by_access_policy" if _text_has_any(access_policy_status, ("blocked", "restricted")) else "clarification_required"

    if qclass == "currentness_sensitive_query":
        if requires_web_access and access_policy_status in {"allowed", "access_allowed", "unknown"}:
            return "future_web_search"
        if source_freshness_requirement in {"current", "fresh"}:
            return "future_document_index"
        return "defer_until_retrieval_available"

    if qclass == "public_claim_query":
        if _text_has_any(access_policy_status, ("blocked", "restricted")) or _text_has_any(privacy_status, ("private", "restricted")):
            return "blocked_by_access_policy"
        if _text_has_any(poison_policy_status, ("blocked", "poison", "quarantined")):
            return "blocked_by_poison_policy"
        return "capability_maturity_lookup" if _text_has_any(summary, ("website", "public", "readiness", "launch")) else "source_evidence_graph_lookup"

    if qclass == "energy_signal_query":
        return "signal_metadata_lookup" if not contradiction_detected else "forecast_error_ledger_lookup"

    if qclass == "artifact_or_code_query":
        return "artifact_provenance_lookup" if not requires_grounding else "source_evidence_graph_lookup"

    if qclass == "legal_or_policy_query":
        if requires_web_access or requires_currentness:
            return "future_web_search"
        return "source_evidence_graph_lookup"

    if qclass == "medical_or_safety_query":
        return "pure_reasoning" if not requires_grounding else "clarification_required"

    if qclass == "source_grounded_claim_query":
        if contradiction_detected:
            return "source_evidence_graph_lookup"
        if requires_source_evidence_graph or requires_grounding:
            return "source_evidence_graph_lookup"
        return "artifact_provenance_lookup" if _text_has_any(summary, ARTIFACT_HINTS_V1) else "source_evidence_graph_lookup"

    if qclass == "general_reasoning_query":
        if requires_grounding or requires_currentness or requires_user_file_access or requires_memory_access or requires_web_access:
            return "clarification_required"
        return "pure_reasoning"

    if qclass == "technical_documentation_query":
        return "uploaded_file_retrieval" if requires_user_file_access else "source_evidence_graph_lookup"

    if qclass == "unknown_query":
        if fallback_behavior == "return_unsupported_claim":
            return "unsupported_answer_refusal"
        if fallback_behavior == "refuse_public_claim":
            return "refuse_public_claim"
        return "clarification_required"

    if qclass not in ALLOWED_QUERY_CLASSES_V1:
        return "clarification_required"

    candidate = "clarification_required"
    if candidate in blocked and allowed:
        for target in allowed:
            if target not in blocked:
                return target
    return candidate



def build_rag_query_routing_packet_v1(
    *,
    routing_packet_id: str,
    query_summary: str = "",
    query_class: str = DEFAULT_QUERY_CLASS_V1,
    requested_claims: Any = None,
    requires_grounding: bool = False,
    requires_currentness: bool = False,
    requires_private_data: bool = False,
    requires_user_file_access: bool = False,
    requires_web_access: bool = False,
    requires_memory_access: bool = False,
    requires_source_evidence_graph: bool = False,
    allowed_routing_targets: Any = None,
    blocked_routing_targets: Any = None,
    selected_routing_target: str | None = None,
    reason_for_selection: str = DEFAULT_REASON_FOR_SELECTION_V1,
    access_policy_status: str = DEFAULT_ACCESS_POLICY_STATUS_V1,
    poison_policy_status: str = DEFAULT_POISON_POLICY_STATUS_V1,
    privacy_status: str = DEFAULT_PRIVACY_STATUS_V1,
    source_freshness_requirement: str = DEFAULT_SOURCE_FRESHNESS_REQUIREMENT_V1,
    citation_requirement: str = DEFAULT_CITATION_REQUIREMENT_V1,
    claim_grounding_requirement: str = DEFAULT_CLAIM_GROUNDING_REQUIREMENT_V1,
    fallback_behavior: str = DEFAULT_FALLBACK_V1,
    recommended_next_check: str = DEFAULT_RECOMMENDED_NEXT_CHECK_V1,
    runtime_authority: bool = False,
    writes_state: bool = False,
    model_provider_used: bool = False,
    public_claim_allowed: bool = False,
    proof_claim_allowed: bool = False,
    learning_claimed: bool = False,
    safe_metadata: Mapping[str, Any] | None = None,
    **extra_fields: Any,
) -> dict[str, Any]:
    if selected_routing_target is None:
        query_class = classify_rag_query_v1(
            query_summary=query_summary,
            requested_claims=requested_claims,
            requires_grounding=requires_grounding,
            requires_currentness=requires_currentness,
            requires_private_data=requires_private_data,
            requires_user_file_access=requires_user_file_access,
            requires_web_access=requires_web_access,
            requires_memory_access=requires_memory_access,
            requires_source_evidence_graph=requires_source_evidence_graph,
        ) if query_class in {DEFAULT_QUERY_CLASS_V1, "", None} else _safe_text(query_class)
        selected_routing_target = select_rag_routing_target_v1(
            query_class=query_class,
            query_summary=query_summary,
            requested_claims=requested_claims,
            requires_grounding=requires_grounding,
            requires_currentness=requires_currentness,
            requires_private_data=requires_private_data,
            requires_user_file_access=requires_user_file_access,
            requires_web_access=requires_web_access,
            requires_memory_access=requires_memory_access,
            requires_source_evidence_graph=requires_source_evidence_graph,
            access_policy_status=access_policy_status,
            poison_policy_status=poison_policy_status,
            privacy_status=privacy_status,
            citation_requirement=citation_requirement,
            claim_grounding_requirement=claim_grounding_requirement,
            source_freshness_requirement=source_freshness_requirement,
            allowed_routing_targets=allowed_routing_targets,
            blocked_routing_targets=blocked_routing_targets,
            fallback_behavior=fallback_behavior,
        )
    allowed = _safe_str_list(allowed_routing_targets)
    blocked = _safe_str_list(blocked_routing_targets)
    if not allowed:
        allowed = [selected_routing_target] if selected_routing_target else []
    if selected_routing_target and selected_routing_target not in allowed:
        allowed = allowed + [selected_routing_target]
    if selected_routing_target in blocked:
        blocked = [item for item in blocked if item != selected_routing_target]
    packet: dict[str, Any] = {
        "routing_packet_id": _safe_text(routing_packet_id),
        "query_summary": _safe_text(query_summary),
        "query_class": _safe_text(query_class),
        "requested_claims": _safe_str_list(requested_claims),
        "requires_grounding": _safe_bool(requires_grounding),
        "requires_currentness": _safe_bool(requires_currentness),
        "requires_private_data": _safe_bool(requires_private_data),
        "requires_user_file_access": _safe_bool(requires_user_file_access),
        "requires_web_access": _safe_bool(requires_web_access),
        "requires_memory_access": _safe_bool(requires_memory_access),
        "requires_source_evidence_graph": _safe_bool(requires_source_evidence_graph),
        "allowed_routing_targets": allowed,
        "blocked_routing_targets": blocked,
        "selected_routing_target": _safe_text(selected_routing_target or DEFAULT_ROUTING_TARGET_V1),
        "reason_for_selection": _safe_text(reason_for_selection),
        "access_policy_status": _safe_text(access_policy_status),
        "poison_policy_status": _safe_text(poison_policy_status),
        "privacy_status": _safe_text(privacy_status),
        "source_freshness_requirement": _safe_text(source_freshness_requirement),
        "citation_requirement": _safe_text(citation_requirement),
        "claim_grounding_requirement": _safe_text(claim_grounding_requirement),
        "fallback_behavior": _safe_text(fallback_behavior),
        "recommended_next_check": _safe_text(recommended_next_check),
        "runtime_authority": _safe_bool(runtime_authority),
        "writes_state": _safe_bool(writes_state),
        "model_provider_used": _safe_bool(model_provider_used),
        "public_claim_allowed": _safe_bool(public_claim_allowed),
        "proof_claim_allowed": _safe_bool(proof_claim_allowed),
        "learning_claimed": _safe_bool(learning_claimed),
        "safe_metadata": dict(safe_metadata or DEFAULT_SAFE_METADATA_V1),
    }
    if extra_fields:
        packet.update({str(key): value for key, value in extra_fields.items()})
    return packet



def validate_rag_query_routing_packet_v1(packet: Any) -> bool:
    if not isinstance(packet, Mapping):
        raise ValidationError("packet_must_be_mapping")

    forbidden_field = _contains_forbidden_field(packet)
    if forbidden_field:
        raise ValidationError(f"forbidden_field_present:{forbidden_field}")
    if _contains_forbidden_claim_marker(packet):
        raise ValidationError("forbidden_claim_phrase_present")

    query_class = _safe_text(packet.get("query_class"))
    if query_class not in ALLOWED_QUERY_CLASSES_V1:
        raise ValidationError("unknown_query_class")

    selected = _safe_text(packet.get("selected_routing_target"))
    if selected not in ALLOWED_ROUTING_TARGETS_V1:
        raise ValidationError("unknown_routing_target")

    fallback_behavior = _safe_text(packet.get("fallback_behavior"))
    if fallback_behavior not in ALLOWED_FALLBACK_MODES_V1:
        raise ValidationError("unknown_fallback_behavior")

    allowed = _safe_str_list(packet.get("allowed_routing_targets"))
    blocked = set(_safe_str_list(packet.get("blocked_routing_targets")))
    if selected not in allowed:
        raise ValidationError("selected_target_not_allowed")

    access_policy_status = _safe_text(packet.get("access_policy_status"))
    poison_policy_status = _safe_text(packet.get("poison_policy_status"))
    privacy_status = _safe_text(packet.get("privacy_status"))
    source_freshness_requirement = _safe_text(packet.get("source_freshness_requirement"))
    citation_requirement = _safe_text(packet.get("citation_requirement"))
    claim_grounding_requirement = _safe_text(packet.get("claim_grounding_requirement"))

    if access_policy_status not in ALLOWED_ACCESS_POLICY_STATUS_V1:
        raise ValidationError("unknown_access_policy_status")
    if poison_policy_status not in ALLOWED_POISON_POLICY_STATUS_V1:
        raise ValidationError("unknown_poison_policy_status")
    if privacy_status not in ALLOWED_PRIVACY_STATUS_V1:
        raise ValidationError("unknown_privacy_status")
    if source_freshness_requirement not in ALLOWED_SOURCE_FRESHNESS_REQUIREMENTS_V1:
        raise ValidationError("unknown_source_freshness_requirement")
    if citation_requirement not in ALLOWED_CITATION_REQUIREMENTS_V1:
        raise ValidationError("unknown_citation_requirement")
    if claim_grounding_requirement not in ALLOWED_CLAIM_GROUNDING_REQUIREMENTS_V1:
        raise ValidationError("unknown_claim_grounding_requirement")

    requires_user_file_access = _safe_bool(packet.get("requires_user_file_access"))
    requires_memory_access = _safe_bool(packet.get("requires_memory_access"))
    requires_web_access = _safe_bool(packet.get("requires_web_access"))
    requires_private_data = _safe_bool(packet.get("requires_private_data"))
    requires_grounding = _safe_bool(packet.get("requires_grounding"))
    requires_currentness = _safe_bool(packet.get("requires_currentness"))
    requires_source_evidence_graph = _safe_bool(packet.get("requires_source_evidence_graph"))

    if selected == "uploaded_file_retrieval" and not requires_user_file_access:
        raise ValidationError("uploaded_file_retrieval_requires_user_file_access")
    if selected == "memory_retrieval" and not requires_memory_access:
        raise ValidationError("memory_retrieval_requires_memory_access")
    if selected == "future_web_search" and not (requires_web_access or requires_currentness or source_freshness_requirement in {"current", "fresh"}):
        raise ValidationError("future_web_search_requires_web_authorization")
    if selected == "blocked_by_access_policy" and access_policy_status not in {"blocked", "access_blocked", "restricted", "access_restricted"}:
        raise ValidationError("blocked_access_policy_target_requires_blocked_access_status")
    if selected == "blocked_by_poison_policy" and poison_policy_status not in {"blocked", "poison_blocked", "quarantined", "poisoned"}:
        raise ValidationError("blocked_poison_policy_target_requires_blocked_poison_status")
    if _text_has_any(access_policy_status, ("blocked", "restricted", "access blocked", "access restricted")) and selected not in {"blocked_by_access_policy", "clarification_required", "unsupported_answer_refusal", "refuse_public_claim"}:
        raise ValidationError("access_restricted_source_routed_usable")
    if _text_has_any(poison_policy_status, ("blocked", "poison", "quarantined")) and selected not in {"blocked_by_poison_policy", "clarification_required", "unsupported_answer_refusal", "refuse_public_claim"}:
        raise ValidationError("poisoned_source_routed_usable")

    if citation_requirement in {"required"} and selected not in {
        "source_evidence_graph_lookup",
        "artifact_provenance_lookup",
        "signal_metadata_lookup",
        "forecast_error_ledger_lookup",
        "capability_maturity_lookup",
    }:
        raise ValidationError("citation_required_without_source_graph_path")

    if requires_private_data and _text_has_any(privacy_status, ("blocked", "restricted")):
        raise ValidationError("private_data_requires_allowed_privacy_status")

    if selected in blocked:
        raise ValidationError("selected_target_blocked")

    if query_class == "public_claim_query" and _text_has_any(privacy_status, ("private", "restricted")):
        raise ValidationError("public_claim_cannot_use_private_evidence")
    if query_class == "public_claim_query" and _text_has_any(access_policy_status, ("blocked", "restricted")):
        raise ValidationError("public_claim_cannot_use_access_restricted_evidence")
    if query_class == "public_claim_query" and selected in {"blocked_by_access_policy", "blocked_by_poison_policy", "unsupported_answer_refusal"}:
        raise ValidationError("public_claim_path_must_not_use_blocked_evidence")

    if selected == "future_web_search" and not requires_web_access:
        raise ValidationError("future_web_search_requires_web_access")
    if selected == "source_evidence_graph_lookup" and not (requires_source_evidence_graph or requires_grounding or citation_requirement in {"required", "preferred"} or claim_grounding_requirement in {"required", "preferred"} or query_class in {"source_grounded_claim_query", "public_claim_query", "legal_or_policy_query", "artifact_or_code_query"}):
        raise ValidationError("graph_lookup_requires_grounding_or_graph_need")

    if _safe_bool(packet.get("runtime_authority")):
        raise ValidationError("runtime_authority_must_be_false")
    if _safe_bool(packet.get("writes_state")):
        raise ValidationError("writes_state_must_be_false")
    if _safe_bool(packet.get("model_provider_used")):
        raise ValidationError("model_provider_used_must_be_false")
    if _safe_bool(packet.get("public_claim_allowed")):
        raise ValidationError("public_claim_allowed_must_be_false")
    if _safe_bool(packet.get("proof_claim_allowed")):
        raise ValidationError("proof_claim_allowed_must_be_false")
    if _safe_bool(packet.get("learning_claimed")):
        raise ValidationError("learning_claimed_must_be_false")

    safe_metadata = packet.get("safe_metadata")
    if safe_metadata is not None and _contains_forbidden_field(safe_metadata):
        raise ValidationError("forbidden_field_present:safe_metadata")

    return True



def summarize_rag_query_routing_packet_v1(packet: Any) -> dict[str, Any]:
    validate_rag_query_routing_packet_v1(packet)
    mapping = dict(packet)
    allowed = _safe_str_list(mapping.get("allowed_routing_targets"))
    blocked = _safe_str_list(mapping.get("blocked_routing_targets"))
    return {
        "summary_type": SUMMARY_TYPE_V1,
        "routing_packet_id": _safe_text(mapping.get("routing_packet_id")),
        "query_class": _safe_text(mapping.get("query_class")),
        "selected_routing_target": _safe_text(mapping.get("selected_routing_target")),
        "access_policy_status": _safe_text(mapping.get("access_policy_status")),
        "poison_policy_status": _safe_text(mapping.get("poison_policy_status")),
        "privacy_status": _safe_text(mapping.get("privacy_status")),
        "fallback_behavior": _safe_text(mapping.get("fallback_behavior")),
        "allowed_target_count": len(allowed),
        "blocked_target_count": len(blocked),
        "requires_grounding": _safe_bool(mapping.get("requires_grounding")),
        "requires_currentness": _safe_bool(mapping.get("requires_currentness")),
        "requires_private_data": _safe_bool(mapping.get("requires_private_data")),
        "requires_user_file_access": _safe_bool(mapping.get("requires_user_file_access")),
        "requires_web_access": _safe_bool(mapping.get("requires_web_access")),
        "requires_memory_access": _safe_bool(mapping.get("requires_memory_access")),
        "requires_source_evidence_graph": _safe_bool(mapping.get("requires_source_evidence_graph")),
        "selected_target_category": ROUTING_TARGET_CATEGORIES_V1.get(_safe_text(mapping.get("selected_routing_target")), "unknown"),
        "safe_metadata": _json_safe(mapping.get("safe_metadata", DEFAULT_SAFE_METADATA_V1)),
    }



def build_initial_rag_query_routing_examples_v1() -> list[dict[str, Any]]:
    examples = [
        build_rag_query_routing_packet_v1(
            routing_packet_id="stable_conceptual_question_pure_reasoning",
            query_summary="Explain the conceptual difference between a graph and a tree.",
            query_class="general_reasoning_query",
            requested_claims=["conceptual explanation"],
            requires_grounding=False,
            requires_currentness=False,
            requires_private_data=False,
            requires_user_file_access=False,
            requires_web_access=False,
            requires_memory_access=False,
            requires_source_evidence_graph=False,
            allowed_routing_targets=["pure_reasoning", "clarification_required"],
            blocked_routing_targets=["memory_retrieval", "uploaded_file_retrieval"],
            selected_routing_target="pure_reasoning",
            reason_for_selection="stable conceptual question can be answered without evidence acquisition",
            access_policy_status="allowed",
            poison_policy_status="clean",
            privacy_status="public",
            source_freshness_requirement="not_required",
            citation_requirement="not_required",
            claim_grounding_requirement="not_required",
            fallback_behavior="answer_from_general_reasoning_with_caveat",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
        ),
        build_rag_query_routing_packet_v1(
            routing_packet_id="uploaded_document_question_routes_to_uploaded_file_retrieval",
            query_summary="Use the attached project brief PDF to answer the question.",
            query_class="uploaded_document_query",
            requested_claims=["document answer"],
            requires_grounding=True,
            requires_currentness=False,
            requires_private_data=False,
            requires_user_file_access=True,
            requires_web_access=False,
            requires_memory_access=False,
            requires_source_evidence_graph=False,
            allowed_routing_targets=["uploaded_file_retrieval", "clarification_required"],
            blocked_routing_targets=["pure_reasoning"],
            selected_routing_target="uploaded_file_retrieval",
            reason_for_selection="uploaded file access is required and allowed",
            access_policy_status="allowed",
            poison_policy_status="clean",
            privacy_status="public",
            source_freshness_requirement="not_required",
            citation_requirement="preferred",
            claim_grounding_requirement="preferred",
            fallback_behavior="request_source_upload",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
        ),
        build_rag_query_routing_packet_v1(
            routing_packet_id="current_law_question_future_web_or_source_required",
            query_summary="What is the current law on this topic in Germany right now?",
            query_class="currentness_sensitive_query",
            requested_claims=["current law"],
            requires_grounding=True,
            requires_currentness=True,
            requires_private_data=False,
            requires_user_file_access=False,
            requires_web_access=True,
            requires_memory_access=False,
            requires_source_evidence_graph=False,
            allowed_routing_targets=["future_web_search", "future_document_index", "clarification_required"],
            blocked_routing_targets=["pure_reasoning"],
            selected_routing_target="future_web_search",
            reason_for_selection="current law is currentness-sensitive and needs future retrieval, not fabricated recall",
            access_policy_status="allowed",
            poison_policy_status="clean",
            privacy_status="public",
            source_freshness_requirement="current",
            citation_requirement="preferred",
            claim_grounding_requirement="preferred",
            fallback_behavior="defer_until_retrieval_available",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
        ),
        build_rag_query_routing_packet_v1(
            routing_packet_id="personal_project_history_memory_if_allowed",
            query_summary="What did we decide about the project history last time?",
            query_class="personal_memory_query",
            requested_claims=["continuity"],
            requires_grounding=False,
            requires_currentness=False,
            requires_private_data=False,
            requires_user_file_access=False,
            requires_web_access=False,
            requires_memory_access=True,
            requires_source_evidence_graph=False,
            allowed_routing_targets=["memory_retrieval", "clarification_required"],
            blocked_routing_targets=["pure_reasoning"],
            selected_routing_target="memory_retrieval",
            reason_for_selection="continuity question is user-specific and allowed memory access is present",
            access_policy_status="allowed",
            poison_policy_status="clean",
            privacy_status="public",
            source_freshness_requirement="not_required",
            citation_requirement="not_required",
            claim_grounding_requirement="not_required",
            fallback_behavior="answer_from_general_reasoning_with_caveat",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
        ),
        build_rag_query_routing_packet_v1(
            routing_packet_id="public_website_claim_graph_and_maturity_check",
            query_summary="Can we make a public website claim about launch readiness?",
            query_class="public_claim_query",
            requested_claims=["website claim", "launch status"],
            requires_grounding=True,
            requires_currentness=False,
            requires_private_data=False,
            requires_user_file_access=False,
            requires_web_access=False,
            requires_memory_access=False,
            requires_source_evidence_graph=True,
            allowed_routing_targets=["source_evidence_graph_lookup", "capability_maturity_lookup", "refuse_public_claim"],
            blocked_routing_targets=["pure_reasoning"],
            selected_routing_target="capability_maturity_lookup",
            reason_for_selection="public website claims must be checked against source evidence and maturity metadata, not assumed",
            access_policy_status="allowed",
            poison_policy_status="clean",
            privacy_status="public",
            source_freshness_requirement="not_required",
            citation_requirement="required",
            claim_grounding_requirement="required",
            fallback_behavior="refuse_public_claim",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
        ),
        build_rag_query_routing_packet_v1(
            routing_packet_id="energy_signal_question_signal_metadata_lookup",
            query_summary="Analyze the energy signal metadata and forecast drift.",
            query_class="energy_signal_query",
            requested_claims=["signal analysis"],
            requires_grounding=True,
            requires_currentness=False,
            requires_private_data=False,
            requires_user_file_access=False,
            requires_web_access=False,
            requires_memory_access=False,
            requires_source_evidence_graph=True,
            allowed_routing_targets=["signal_metadata_lookup", "forecast_error_ledger_lookup", "source_evidence_graph_lookup"],
            blocked_routing_targets=["pure_reasoning"],
            selected_routing_target="signal_metadata_lookup",
            reason_for_selection="energy signal metadata is the safest evidence path for signal-shaped queries",
            access_policy_status="allowed",
            poison_policy_status="clean",
            privacy_status="public",
            source_freshness_requirement="not_required",
            citation_requirement="preferred",
            claim_grounding_requirement="preferred",
            fallback_behavior="use_existing_graph_only",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
        ),
        build_rag_query_routing_packet_v1(
            routing_packet_id="poisoned_document_blocked_by_poison_policy",
            query_summary="The uploaded document is poisoned and should not be used.",
            query_class="uploaded_document_query",
            requested_claims=["document use"],
            requires_grounding=True,
            requires_currentness=False,
            requires_private_data=False,
            requires_user_file_access=True,
            requires_web_access=False,
            requires_memory_access=False,
            requires_source_evidence_graph=False,
            allowed_routing_targets=["blocked_by_poison_policy"],
            blocked_routing_targets=["uploaded_file_retrieval", "pure_reasoning"],
            selected_routing_target="blocked_by_poison_policy",
            reason_for_selection="poisoned content must be quarantined and never routed as usable evidence",
            access_policy_status="allowed",
            poison_policy_status="poison_blocked",
            privacy_status="public",
            source_freshness_requirement="not_required",
            citation_requirement="blocked",
            claim_grounding_requirement="blocked",
            fallback_behavior="block_due_poison_policy",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
        ),
        build_rag_query_routing_packet_v1(
            routing_packet_id="access_restricted_document_blocked_by_access_policy",
            query_summary="The user document is access restricted and cannot be used.",
            query_class="uploaded_document_query",
            requested_claims=["restricted document"],
            requires_grounding=True,
            requires_currentness=False,
            requires_private_data=False,
            requires_user_file_access=True,
            requires_web_access=False,
            requires_memory_access=False,
            requires_source_evidence_graph=False,
            allowed_routing_targets=["blocked_by_access_policy"],
            blocked_routing_targets=["uploaded_file_retrieval", "pure_reasoning"],
            selected_routing_target="blocked_by_access_policy",
            reason_for_selection="access-restricted content must not become usable evidence",
            access_policy_status="access_blocked",
            poison_policy_status="clean",
            privacy_status="restricted",
            source_freshness_requirement="not_required",
            citation_requirement="blocked",
            claim_grounding_requirement="blocked",
            fallback_behavior="block_due_access_policy",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
        ),
        build_rag_query_routing_packet_v1(
            routing_packet_id="unsupported_factual_claim_refusal",
            query_summary="Make a factual claim that cannot be grounded here.",
            query_class="unknown_query",
            requested_claims=["unsupported factual claim"],
            requires_grounding=True,
            requires_currentness=False,
            requires_private_data=False,
            requires_user_file_access=False,
            requires_web_access=False,
            requires_memory_access=False,
            requires_source_evidence_graph=False,
            allowed_routing_targets=["unsupported_answer_refusal", "clarification_required"],
            blocked_routing_targets=["pure_reasoning"],
            selected_routing_target="unsupported_answer_refusal",
            reason_for_selection="unsupported factual claims should be refused rather than fabricated",
            access_policy_status="allowed",
            poison_policy_status="clean",
            privacy_status="public",
            source_freshness_requirement="not_required",
            citation_requirement="not_required",
            claim_grounding_requirement="not_required",
            fallback_behavior="return_unsupported_claim",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
        ),
        build_rag_query_routing_packet_v1(
            routing_packet_id="contradictory_sources_graph_contradiction_handling",
            query_summary="Two sources contradict each other; reconcile the contradiction.",
            query_class="source_grounded_claim_query",
            requested_claims=["contradiction handling"],
            requires_grounding=True,
            requires_currentness=False,
            requires_private_data=False,
            requires_user_file_access=False,
            requires_web_access=False,
            requires_memory_access=False,
            requires_source_evidence_graph=True,
            allowed_routing_targets=["source_evidence_graph_lookup", "artifact_provenance_lookup", "clarification_required"],
            blocked_routing_targets=["pure_reasoning"],
            selected_routing_target="source_evidence_graph_lookup",
            reason_for_selection="contradictory sources should be routed to graph-based evidence handling",
            access_policy_status="allowed",
            poison_policy_status="clean",
            privacy_status="public",
            source_freshness_requirement="not_required",
            citation_requirement="required",
            claim_grounding_requirement="required",
            fallback_behavior="use_existing_graph_only",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
        ),
    ]
    return examples


__all__ = [
    "HELPER_TYPE_V1",
    "PACKET_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "ValidationError",
    "ALLOWED_QUERY_CLASSES_V1",
    "ALLOWED_ROUTING_TARGETS_V1",
    "ALLOWED_FALLBACK_MODES_V1",
    "build_rag_query_routing_packet_v1",
    "classify_rag_query_v1",
    "select_rag_routing_target_v1",
    "validate_rag_query_routing_packet_v1",
    "summarize_rag_query_routing_packet_v1",
    "to_rag_query_routing_json_safe_v1",
    "build_initial_rag_query_routing_examples_v1",
]
