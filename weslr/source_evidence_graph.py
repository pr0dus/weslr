"""Metadata-only source evidence graph helpers v1.

This module builds bounded source-evidence graph packets from supplied metadata
only. It is pure, deterministic, import-safe, and fail-closed.

It does not implement RAG. It does not retrieve documents. It does not
vectorize content. It does not call models/providers or search. It does not
write memory or `.weslr`. It does not authorize public claims or claim proof,
truth, hallucination elimination, AGI, consciousness, sentience, Turing, or
certification.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

HELPER_TYPE_V1 = "source_evidence_graph_v1"
GRAPH_TYPE_V1 = "source_evidence_graph_v1"
SUMMARY_TYPE_V1 = "source_evidence_graph_summary_v1"
NODE_TYPE_SOURCE_V1 = "source_node"
NODE_TYPE_DOCUMENT_V1 = "document_node"
NODE_TYPE_CHUNK_V1 = "chunk_node"
NODE_TYPE_CLAIM_V1 = "claim_node"
NODE_TYPE_CITATION_V1 = "citation_node"
NODE_TYPE_ARTIFACT_V1 = "artifact_node"
NODE_TYPE_SIGNAL_V1 = "signal_node"
NODE_TYPE_MEMORY_V1 = "memory_node"
NODE_TYPE_FORECAST_V1 = "forecast_node"
NODE_TYPE_SCENARIO_V1 = "scenario_node"
NODE_TYPE_FORECAST_ERROR_V1 = "forecast_error_node"
NODE_TYPE_CAPABILITY_V1 = "capability_node"
NODE_TYPE_INFERENCE_V1 = "inference_packet_node"
NODE_TYPE_CANDIDATE_ANSWER_V1 = "candidate_answer_node"
NODE_TYPE_OWNER_INSTRUCTION_V1 = "owner_instruction_node"
NODE_TYPE_PUBLIC_CLAIM_V1 = "public_claim_node"
NODE_TYPE_UNKNOWN_V1 = "unknown_node"

ALLOWED_NODE_TYPES_V1 = {
    NODE_TYPE_SOURCE_V1,
    NODE_TYPE_DOCUMENT_V1,
    NODE_TYPE_CHUNK_V1,
    NODE_TYPE_CLAIM_V1,
    NODE_TYPE_CITATION_V1,
    NODE_TYPE_ARTIFACT_V1,
    NODE_TYPE_SIGNAL_V1,
    NODE_TYPE_MEMORY_V1,
    NODE_TYPE_FORECAST_V1,
    NODE_TYPE_SCENARIO_V1,
    NODE_TYPE_FORECAST_ERROR_V1,
    NODE_TYPE_CAPABILITY_V1,
    NODE_TYPE_INFERENCE_V1,
    NODE_TYPE_CANDIDATE_ANSWER_V1,
    NODE_TYPE_OWNER_INSTRUCTION_V1,
    NODE_TYPE_PUBLIC_CLAIM_V1,
    NODE_TYPE_UNKNOWN_V1,
}

ALLOWED_EDGE_TYPES_V1 = {
    "supports",
    "contradicts",
    "depends_on",
    "invalidates",
    "qualifies",
    "came_from",
    "cites",
    "summarizes",
    "derived_from",
    "requires_owner_approval",
    "blocked_by",
    "generated_candidate",
    "observed_result",
    "same_source_as",
    "newer_than",
    "older_than",
    "same_claim_as",
    "conflicts_with",
    "requires_freshness_check",
    "requires_access_check",
    "requires_poison_check",
}

ALLOWED_CLAIM_STATUSES_V1 = {
    "supported",
    "partially_supported",
    "contradicted",
    "unsupported",
    "stale_support",
    "access_restricted",
    "poison_quarantined",
    "unknown_status",
}

ALLOWED_GRAPH_GROUNDING_STATUSES_V1 = {
    "grounded",
    "partially_grounded",
    "blocked",
    "unknown_status",
}

ALLOWED_CITATION_READINESS_V1 = {
    "ready",
    "partially_ready",
    "blocked",
    "unknown_status",
}

ALLOWED_RAG_READINESS_V1 = {
    "ready",
    "partially_ready",
    "blocked",
    "unknown_status",
}

ALLOWED_PUBLIC_CLAIM_READINESS_V1 = {
    "ready",
    "partially_ready",
    "blocked",
    "unknown_status",
}

ALLOWED_FIELD_HINTS_V1 = (
    "hidden_prompt",
    "raw_private",
    "private_data",
    "secret",
    "token",
    "key",
    "api_key",
    "credential",
    "password",
)

ALLOWED_CLAIM_PHRASES_V1 = (
    "agi",
    "consciousness",
    "sentience",
    "turing",
    "certification",
    "public readiness",
    "public ready",
    "proof certainty",
    "truth certainty",
    "proof claim",
    "truth claim",
    "hallucination elimination",
    "hallucination-free",
    "no hallucinations",
)

STALE_FRESHNESS_STATUSES_V1 = {
    "stale",
    "expired",
    "missing_timestamp",
    "future_timestamp",
}

POISON_STATUSES_V1 = {
    "quarantined",
    "blocked",
    "poisoned",
    "poison_quarantined",
}

DEFAULT_CREATED_TIMESTAMP_V1 = "2026-06-02T06:42:00+02:00"
DEFAULT_GRAPH_SCOPE_V1 = "metadata_only"
DEFAULT_GROUNDING_STATUS_V1 = "unknown_status"
DEFAULT_CITATION_READINESS_V1 = "unknown_status"
DEFAULT_RAG_READINESS_V1 = "unknown_status"
DEFAULT_PUBLIC_CLAIM_READINESS_V1 = "unknown_status"
DEFAULT_RECOMMENDED_NEXT_CHECK_V1 = "design the missing graph lane before any grounded retrieval or citation routing"


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



def to_source_evidence_graph_json_safe_v1(value: Any) -> Any:
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
            if any(hint.replace("_", " ") in key_text or hint in key_raw for hint in ALLOWED_FIELD_HINTS_V1):
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
    text = _normalize_text(value)
    raw = _safe_text(value).lower()
    if any(hint.replace("_", " ") in text or hint in raw for hint in ALLOWED_FIELD_HINTS_V1):
        return _safe_text(value)
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
    raw = _safe_text(value).lower()
    return any(phrase in text or phrase in raw for phrase in ALLOWED_CLAIM_PHRASES_V1)



def _coerce_dict_list(value: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in _safe_list(value):
        if is_dataclass(item):
            out.append(_json_safe(asdict(item)))
        elif isinstance(item, Mapping):
            out.append(_json_safe(dict(item)))
        else:
            out.append({"value": _safe_text(item)})
    return out



def _dedupe_str_list(value: Any) -> list[str]:
    return _safe_str_list(value)



def _node_identifier(node: Mapping[str, Any]) -> str:
    for key in ("node_id", "source_id", "claim_id", "artifact_id", "signal_id", "memory_id", "forecast_id", "scenario_id", "error_id", "capability_id", "inference_packet_id", "candidate_answer_id", "citation_id"):
        if key in node and _safe_text(node[key]):
            return _safe_text(node[key])
    return _safe_text(node.get("node_id", ""))



def _claim_nodes(graph: Mapping[str, Any]) -> list[dict[str, Any]]:
    return _coerce_dict_list(graph.get("claim_nodes"))



def _source_nodes(graph: Mapping[str, Any]) -> list[dict[str, Any]]:
    return _coerce_dict_list(graph.get("source_nodes"))



def _all_nodes(graph: Mapping[str, Any]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for field in (
        "source_nodes",
        "claim_nodes",
        "artifact_nodes",
        "signal_nodes",
        "memory_nodes",
        "forecast_nodes",
        "scenario_nodes",
        "error_nodes",
        "capability_nodes",
        "inference_nodes",
        "candidate_answer_nodes",
        "public_claim_nodes",
    ):
        nodes.extend(_coerce_dict_list(graph.get(field)))
    return nodes



def _all_edges(graph: Mapping[str, Any]) -> list[dict[str, Any]]:
    return _coerce_dict_list(graph.get("edges"))



def _first_matching_node(graph: Mapping[str, Any], node_id: str) -> dict[str, Any] | None:
    for node in _all_nodes(graph):
        if _node_identifier(node) == node_id:
            return node
    return None



def _freshness_issue(status: str) -> bool:
    return _safe_text(status) in STALE_FRESHNESS_STATUSES_V1



def _poison_issue(status: str) -> bool:
    return _safe_text(status) in POISON_STATUSES_V1



def _derive_claim_grounding_status(graph: Mapping[str, Any]) -> str:
    claims = _claim_nodes(graph)
    if not claims:
        return "unknown_status"
    if any(_safe_text(item.get("claim_status")) in {"unsupported", "contradicted", "access_restricted", "poison_quarantined"} for item in claims):
        return "blocked"
    if any(_safe_text(item.get("claim_status")) == "stale_support" for item in claims):
        return "partially_grounded"
    return "grounded"



def _derive_citation_readiness(graph: Mapping[str, Any]) -> str:
    if not graph.get("source_nodes") or not graph.get("claim_nodes"):
        return "blocked"
    if graph.get("poison_quarantined_sources") or graph.get("access_restricted_sources"):
        return "blocked"
    if graph.get("stale_sources"):
        return "partially_ready"
    return "ready"



def _derive_rag_readiness(graph: Mapping[str, Any]) -> str:
    if graph.get("poison_quarantined_sources") or graph.get("access_restricted_sources"):
        return "blocked"
    if not graph.get("source_nodes"):
        return "blocked"
    if graph.get("missing_sources") or graph.get("stale_sources"):
        return "partially_ready"
    return "ready"



def _derive_public_claim_readiness(graph: Mapping[str, Any]) -> str:
    if not graph.get("public_claim_nodes"):
        return "blocked"
    if not graph.get("public_claim_allowed"):
        return "blocked"
    if graph.get("access_restricted_sources") or graph.get("poison_quarantined_sources"):
        return "blocked"
    if graph.get("unsupported_claims"):
        return "partially_ready"
    return "ready"



def _contradicting_pairs(graph: Mapping[str, Any]) -> list[dict[str, str]]:
    pairs: list[dict[str, str]] = []
    for edge in _all_edges(graph):
        if _safe_text(edge.get("edge_type")) in {"contradicts", "conflicts_with"}:
            pairs.append(
                {
                    "from_node_id": _safe_text(edge.get("from_node_id")),
                    "to_node_id": _safe_text(edge.get("to_node_id")),
                    "edge_id": _safe_text(edge.get("edge_id")),
                }
            )
    return pairs



def _stale_source_ids(graph: Mapping[str, Any]) -> list[str]:
    return [
        _safe_text(node.get("source_id"))
        for node in _source_nodes(graph)
        if _freshness_issue(node.get("freshness_status"))
    ]



def _poison_source_ids(graph: Mapping[str, Any]) -> list[str]:
    return [
        _safe_text(node.get("source_id"))
        for node in _source_nodes(graph)
        if _poison_issue(node.get("poison_shield_status"))
    ]



def _access_restricted_source_ids(graph: Mapping[str, Any]) -> list[str]:
    return [
        _safe_text(node.get("source_id"))
        for node in _source_nodes(graph)
        if _safe_text(node.get("access_level")) in {"restricted", "private", "cross_user_blocked"}
        or _safe_bool(node.get("owner_authorized")) is False and _safe_text(node.get("source_scope")) == "public"
    ]



def _unsupported_claim_ids(graph: Mapping[str, Any]) -> list[str]:
    ids: list[str] = []
    for claim in _claim_nodes(graph):
        status = _safe_text(claim.get("claim_status"))
        if status in {"unsupported", "contradicted", "access_restricted", "poison_quarantined", "stale_support"}:
            ids.append(_safe_text(claim.get("claim_id")))
    return ids



def _missing_sources(graph: Mapping[str, Any]) -> list[str]:
    return _dedupe_str_list(graph.get("missing_sources"))



def _require_known_graph_booleans(graph: Mapping[str, Any]) -> None:
    for field_name in (
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "proof_claim_allowed",
        "learning_claimed",
    ):
        if _safe_bool(graph.get(field_name)):
            raise ValidationError(f"{field_name}_true")



def _validate_node(node: Mapping[str, Any]) -> None:
    node_type = _safe_text(node.get("node_type"))
    if node_type not in ALLOWED_NODE_TYPES_V1:
        raise ValidationError("unknown_node_type")
    if _contains_forbidden_field(node):
        raise ValidationError("hidden_prompt_or_raw_private_field")
    if _contains_forbidden_claim_marker(node):
        raise ValidationError("claim_marker_blocked")
    if node_type in {NODE_TYPE_CLAIM_V1, NODE_TYPE_PUBLIC_CLAIM_V1}:
        claim_status = _safe_text(node.get("claim_status"))
        if claim_status not in ALLOWED_CLAIM_STATUSES_V1:
            raise ValidationError("unknown_claim_status")
        if _safe_text(node.get("claim_scope")) == "public" and _safe_bool(node.get("public_claim_sensitive")) is False:
            # public claims should remain explicitly marked
            pass



def _validate_edge(edge: Mapping[str, Any], graph: Mapping[str, Any]) -> None:
    edge_type = _safe_text(edge.get("edge_type"))
    if edge_type not in ALLOWED_EDGE_TYPES_V1:
        raise ValidationError("unknown_edge_type")
    if _contains_forbidden_field(edge):
        raise ValidationError("hidden_prompt_or_raw_private_field")
    if _contains_forbidden_claim_marker(edge):
        raise ValidationError("claim_marker_blocked")

    from_node = _first_matching_node(graph, _safe_text(edge.get("from_node_id")))
    to_node = _first_matching_node(graph, _safe_text(edge.get("to_node_id")))
    if edge_type == "supports" and from_node and to_node:
        if _poison_issue(from_node.get("poison_shield_status")) and _safe_text(to_node.get("node_type")) in {NODE_TYPE_CLAIM_V1, NODE_TYPE_PUBLIC_CLAIM_V1} and _safe_bool(to_node.get("public_claim_sensitive")):
            raise ValidationError("poisoned_source_supports_public_claim")


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------


def build_source_evidence_node_v1(
    *,
    source_id: str,
    source_type: str,
    source_name: str,
    source_scope: str,
    source_reference: str,
    created_timestamp: str = DEFAULT_CREATED_TIMESTAMP_V1,
    retrieved_timestamp: str = DEFAULT_CREATED_TIMESTAMP_V1,
    reported_timestamp: str = DEFAULT_CREATED_TIMESTAMP_V1,
    freshness_status: str = "fresh",
    quality_status: str = "high_quality",
    poison_shield_status: str = "clean",
    access_level: str = "public",
    privacy_sensitivity: str = "low",
    owner_authorized: bool = True,
    operator_authorized: bool = True,
    raw_content_stored: bool = False,
    summary_only: bool = True,
    safe_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "node_type": NODE_TYPE_SOURCE_V1,
        "node_id": _safe_text(source_id),
        "source_id": _safe_text(source_id),
        "source_type": _safe_text(source_type),
        "source_name": _safe_text(source_name),
        "source_scope": _safe_text(source_scope),
        "source_reference": _safe_text(source_reference),
        "created_timestamp": _safe_text(created_timestamp),
        "retrieved_timestamp": _safe_text(retrieved_timestamp),
        "reported_timestamp": _safe_text(reported_timestamp),
        "freshness_status": _safe_text(freshness_status),
        "quality_status": _safe_text(quality_status),
        "poison_shield_status": _safe_text(poison_shield_status),
        "access_level": _safe_text(access_level),
        "privacy_sensitivity": _safe_text(privacy_sensitivity),
        "owner_authorized": _safe_bool(owner_authorized),
        "operator_authorized": _safe_bool(operator_authorized),
        "raw_content_stored": _safe_bool(raw_content_stored),
        "summary_only": _safe_bool(summary_only),
        "safe_metadata": _json_safe(dict(safe_metadata or {})),
    }



def build_claim_node_v1(
    *,
    claim_id: str,
    claim_text_summary: str,
    claim_type: str = "factual_claim",
    claim_scope: str = "internal",
    claim_status: str = "unknown_status",
    supporting_sources: Any = None,
    contradicting_sources: Any = None,
    citation_refs: Any = None,
    freshness_required: bool = True,
    public_claim_sensitive: bool = False,
    requires_owner_approval: bool = False,
    unsupported_reason: str = "",
    safe_metadata: Mapping[str, Any] | None = None,
    node_type: str = NODE_TYPE_CLAIM_V1,
) -> dict[str, Any]:
    return {
        "node_type": _safe_text(node_type),
        "node_id": _safe_text(claim_id),
        "claim_id": _safe_text(claim_id),
        "claim_text_summary": _safe_text(claim_text_summary),
        "claim_type": _safe_text(claim_type),
        "claim_scope": _safe_text(claim_scope),
        "claim_status": _safe_text(claim_status),
        "supporting_sources": _dedupe_str_list(supporting_sources),
        "contradicting_sources": _dedupe_str_list(contradicting_sources),
        "citation_refs": _dedupe_str_list(citation_refs),
        "freshness_required": _safe_bool(freshness_required),
        "public_claim_sensitive": _safe_bool(public_claim_sensitive),
        "requires_owner_approval": _safe_bool(requires_owner_approval),
        "unsupported_reason": _safe_text(unsupported_reason),
        "safe_metadata": _json_safe(dict(safe_metadata or {})),
    }



def build_evidence_edge_v1(
    *,
    edge_id: str,
    edge_type: str,
    from_node_id: str,
    to_node_id: str,
    edge_summary: str = "",
    source_refs: Any = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "edge_id": _safe_text(edge_id),
        "edge_type": _safe_text(edge_type),
        "from_node_id": _safe_text(from_node_id),
        "to_node_id": _safe_text(to_node_id),
        "edge_summary": _safe_text(edge_summary),
        "source_refs": _dedupe_str_list(source_refs),
        "safe_metadata": _json_safe(dict(safe_metadata or {})),
    }



def build_source_evidence_graph_v1(
    *,
    evidence_graph_id: str,
    graph_version: str = GRAPH_TYPE_V1,
    created_timestamp: str = DEFAULT_CREATED_TIMESTAMP_V1,
    scope: str = DEFAULT_GRAPH_SCOPE_V1,
    source_nodes: Any = None,
    claim_nodes: Any = None,
    artifact_nodes: Any = None,
    signal_nodes: Any = None,
    memory_nodes: Any = None,
    forecast_nodes: Any = None,
    scenario_nodes: Any = None,
    error_nodes: Any = None,
    capability_nodes: Any = None,
    inference_nodes: Any = None,
    candidate_answer_nodes: Any = None,
    public_claim_nodes: Any = None,
    edges: Any = None,
    contradiction_summary: Mapping[str, Any] | None = None,
    unsupported_claims: Any = None,
    stale_sources: Any = None,
    poison_quarantined_sources: Any = None,
    access_restricted_sources: Any = None,
    missing_sources: Any = None,
    claim_grounding_status: str = DEFAULT_GROUNDING_STATUS_V1,
    citation_readiness: str = DEFAULT_CITATION_READINESS_V1,
    rag_readiness: str = DEFAULT_RAG_READINESS_V1,
    public_claim_readiness: str = DEFAULT_PUBLIC_CLAIM_READINESS_V1,
    recommended_next_check: str = DEFAULT_RECOMMENDED_NEXT_CHECK_V1,
    runtime_authority: bool = False,
    writes_state: bool = False,
    model_provider_used: bool = False,
    public_claim_allowed: bool = False,
    proof_claim_allowed: bool = False,
    learning_claimed: bool = False,
    safe_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    graph = {
        "evidence_graph_id": _safe_text(evidence_graph_id),
        "graph_version": _safe_text(graph_version),
        "created_timestamp": _safe_text(created_timestamp),
        "scope": _safe_text(scope),
        "source_nodes": _coerce_dict_list(source_nodes),
        "claim_nodes": _coerce_dict_list(claim_nodes),
        "artifact_nodes": _coerce_dict_list(artifact_nodes),
        "signal_nodes": _coerce_dict_list(signal_nodes),
        "memory_nodes": _coerce_dict_list(memory_nodes),
        "forecast_nodes": _coerce_dict_list(forecast_nodes),
        "scenario_nodes": _coerce_dict_list(scenario_nodes),
        "error_nodes": _coerce_dict_list(error_nodes),
        "capability_nodes": _coerce_dict_list(capability_nodes),
        "inference_nodes": _coerce_dict_list(inference_nodes),
        "candidate_answer_nodes": _coerce_dict_list(candidate_answer_nodes),
        "public_claim_nodes": _coerce_dict_list(public_claim_nodes),
        "edges": _coerce_dict_list(edges),
        "contradiction_summary": _json_safe(dict(contradiction_summary or {})),
        "unsupported_claims": _dedupe_str_list(unsupported_claims),
        "stale_sources": _dedupe_str_list(stale_sources),
        "poison_quarantined_sources": _dedupe_str_list(poison_quarantined_sources),
        "access_restricted_sources": _dedupe_str_list(access_restricted_sources),
        "missing_sources": _dedupe_str_list(missing_sources),
        "claim_grounding_status": _safe_text(claim_grounding_status),
        "citation_readiness": _safe_text(citation_readiness),
        "rag_readiness": _safe_text(rag_readiness),
        "public_claim_readiness": _safe_text(public_claim_readiness),
        "recommended_next_check": _safe_text(recommended_next_check),
        "runtime_authority": _safe_bool(runtime_authority),
        "writes_state": _safe_bool(writes_state),
        "model_provider_used": _safe_bool(model_provider_used),
        "public_claim_allowed": _safe_bool(public_claim_allowed),
        "proof_claim_allowed": _safe_bool(proof_claim_allowed),
        "learning_claimed": _safe_bool(learning_claimed),
        "safe_metadata": _json_safe(dict(safe_metadata or {"metadata_only": True, "internal_only": True})),
    }

    if contradiction_summary is None:
        contradictory = _contradicting_pairs(graph)
        graph["contradiction_summary"] = {
            "contradiction_count": len(contradictory),
            "contradicting_pairs": contradictory,
        }
    if not graph["stale_sources"]:
        graph["stale_sources"] = _stale_source_ids(graph)
    if not graph["poison_quarantined_sources"]:
        graph["poison_quarantined_sources"] = _poison_source_ids(graph)
    if not graph["access_restricted_sources"]:
        graph["access_restricted_sources"] = _access_restricted_source_ids(graph)
    if not graph["unsupported_claims"]:
        graph["unsupported_claims"] = _unsupported_claim_ids(graph)
    if not graph["missing_sources"] and graph["claim_nodes"]:
        graph["missing_sources"] = [
            _safe_text(node.get("claim_id"))
            for node in graph["claim_nodes"]
            if _safe_text(node.get("claim_status")) in {"unsupported", "stale_support", "access_restricted", "poison_quarantined"}
        ]

    if claim_grounding_status == DEFAULT_GROUNDING_STATUS_V1:
        graph["claim_grounding_status"] = _derive_claim_grounding_status(graph)
    if citation_readiness == DEFAULT_CITATION_READINESS_V1:
        graph["citation_readiness"] = _derive_citation_readiness(graph)
    if rag_readiness == DEFAULT_RAG_READINESS_V1:
        graph["rag_readiness"] = _derive_rag_readiness(graph)
    if public_claim_readiness == DEFAULT_PUBLIC_CLAIM_READINESS_V1:
        graph["public_claim_readiness"] = _derive_public_claim_readiness(graph)

    return graph


# ---------------------------------------------------------------------------
# Public summary and validation
# ---------------------------------------------------------------------------


def summarize_source_evidence_graph_v1(graph: Any) -> dict[str, Any]:
    graph = to_source_evidence_graph_json_safe_v1(graph)
    contradiction_summary = graph.get("contradiction_summary") or {}
    contradictory_pairs = contradiction_summary.get("contradicting_pairs") or _contradicting_pairs(graph)
    return {
        "summary_type": SUMMARY_TYPE_V1,
        "evidence_graph_id": _safe_text(graph.get("evidence_graph_id")),
        "scope": _safe_text(graph.get("scope")),
        "source_count": len(_coerce_dict_list(graph.get("source_nodes"))),
        "claim_count": len(_coerce_dict_list(graph.get("claim_nodes"))),
        "edge_count": len(_coerce_dict_list(graph.get("edges"))),
        "contradiction_count": len(contradictory_pairs),
        "unsupported_claim_count": len(_dedupe_str_list(graph.get("unsupported_claims"))),
        "stale_source_count": len(_dedupe_str_list(graph.get("stale_sources"))),
        "poison_quarantined_source_count": len(_dedupe_str_list(graph.get("poison_quarantined_sources"))),
        "access_restricted_source_count": len(_dedupe_str_list(graph.get("access_restricted_sources"))),
        "claim_grounding_status": _safe_text(graph.get("claim_grounding_status")),
        "citation_readiness": _safe_text(graph.get("citation_readiness")),
        "rag_readiness": _safe_text(graph.get("rag_readiness")),
        "public_claim_readiness": _safe_text(graph.get("public_claim_readiness")),
        "recommended_next_check": _safe_text(graph.get("recommended_next_check")),
    }



def validate_source_evidence_graph_v1(graph: Any) -> bool:
    graph = to_source_evidence_graph_json_safe_v1(graph)
    if _contains_forbidden_field(graph):
        raise ValidationError("hidden_prompt_or_raw_private_field")
    if _contains_forbidden_claim_marker(graph):
        raise ValidationError("claim_marker_blocked")
    _require_known_graph_booleans(graph)

    if _safe_text(graph.get("claim_grounding_status")) not in ALLOWED_GRAPH_GROUNDING_STATUSES_V1:
        raise ValidationError("unknown_graph_grounding_status")
    if _safe_text(graph.get("citation_readiness")) not in ALLOWED_CITATION_READINESS_V1:
        raise ValidationError("unknown_citation_readiness")
    if _safe_text(graph.get("rag_readiness")) not in ALLOWED_RAG_READINESS_V1:
        raise ValidationError("unknown_rag_readiness")
    if _safe_text(graph.get("public_claim_readiness")) not in ALLOWED_PUBLIC_CLAIM_READINESS_V1:
        raise ValidationError("unknown_public_claim_readiness")

    for node in _all_nodes(graph):
        _validate_node(node)
    for edge in _all_edges(graph):
        _validate_edge(edge, graph)

    for claim in _claim_nodes(graph):
        if _safe_text(claim.get("claim_status")) not in ALLOWED_CLAIM_STATUSES_V1:
            raise ValidationError("unknown_claim_status")

    if _safe_text(graph.get("public_claim_readiness")) == "ready" and not _safe_bool(graph.get("public_claim_allowed")):
        raise ValidationError("public_claim_allowed_true_required_for_public_ready")

    return True


# ---------------------------------------------------------------------------
# Initial examples
# ---------------------------------------------------------------------------


def build_initial_source_evidence_graph_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []

    source_fresh = build_source_evidence_node_v1(
        source_id="fresh_source_supports_claim:source",
        source_type="signal_provenance",
        source_name="Fresh source",
        source_scope="internal",
        source_reference="signal:fresh",
        freshness_status="fresh",
        quality_status="high_quality",
        access_level="public",
        privacy_sensitivity="low",
        owner_authorized=True,
        operator_authorized=True,
        safe_metadata={"example_name": "fresh_source_supports_claim"},
    )
    claim_fresh = build_claim_node_v1(
        claim_id="fresh_source_supports_claim:claim",
        claim_text_summary="fresh source supports a simple claim",
        claim_status="supported",
        claim_scope="internal",
        supporting_sources=[source_fresh["source_id"]],
        citation_refs=[source_fresh["source_reference"]],
        safe_metadata={"example_name": "fresh_source_supports_claim"},
    )
    examples.append(
        build_source_evidence_graph_v1(
            evidence_graph_id="fresh_source_supports_claim",
            source_nodes=[source_fresh],
            claim_nodes=[claim_fresh],
            edges=[
                build_evidence_edge_v1(
                    edge_id="fresh_source_supports_claim:edge",
                    edge_type="supports",
                    from_node_id=source_fresh["source_id"],
                    to_node_id=claim_fresh["claim_id"],
                    edge_summary="fresh evidence supports the claim",
                )
            ],
            claim_grounding_status="grounded",
            citation_readiness="ready",
            rag_readiness="ready",
            public_claim_readiness="blocked",
            recommended_next_check="use the fresh evidence as a grounded input, not as proof",
        )
    )

    source_stale = build_source_evidence_node_v1(
        source_id="stale_source_supports_claim_with_warning:source",
        source_type="signal_provenance",
        source_name="Stale source",
        source_scope="internal",
        source_reference="signal:stale",
        freshness_status="stale",
        quality_status="medium_quality",
        access_level="public",
        privacy_sensitivity="low",
        safe_metadata={"example_name": "stale_source_supports_claim_with_warning"},
    )
    claim_stale = build_claim_node_v1(
        claim_id="stale_source_supports_claim_with_warning:claim",
        claim_text_summary="stale evidence supports a claim with warning",
        claim_status="stale_support",
        claim_scope="internal",
        supporting_sources=[source_stale["source_id"]],
        citation_refs=[source_stale["source_reference"]],
        unsupported_reason="freshness warning applies",
        safe_metadata={"example_name": "stale_source_supports_claim_with_warning"},
    )
    examples.append(
        build_source_evidence_graph_v1(
            evidence_graph_id="stale_source_supports_claim_with_warning",
            source_nodes=[source_stale],
            claim_nodes=[claim_stale],
            stale_sources=[source_stale["source_id"]],
            edges=[
                build_evidence_edge_v1(
                    edge_id="stale_source_supports_claim_with_warning:edge",
                    edge_type="qualifies",
                    from_node_id=source_stale["source_id"],
                    to_node_id=claim_stale["claim_id"],
                    edge_summary="freshness warning qualifies the claim",
                )
            ],
            claim_grounding_status="partially_grounded",
            citation_readiness="partially_ready",
            rag_readiness="partially_ready",
            public_claim_readiness="blocked",
            recommended_next_check="refresh the stale source before stronger grounding",
        )
    )

    source_a = build_source_evidence_node_v1(
        source_id="two_sources_contradict_same_claim:source_a",
        source_type="signal_provenance",
        source_name="Source A",
        source_scope="internal",
        source_reference="signal:a",
        freshness_status="fresh",
        quality_status="high_quality",
        safe_metadata={"example_name": "two_sources_contradict_same_claim"},
    )
    source_b = build_source_evidence_node_v1(
        source_id="two_sources_contradict_same_claim:source_b",
        source_type="signal_provenance",
        source_name="Source B",
        source_scope="internal",
        source_reference="signal:b",
        freshness_status="fresh",
        quality_status="high_quality",
        safe_metadata={"example_name": "two_sources_contradict_same_claim"},
    )
    claim_contradicted = build_claim_node_v1(
        claim_id="two_sources_contradict_same_claim:claim",
        claim_text_summary="two sources disagree on the same claim",
        claim_status="contradicted",
        claim_scope="internal",
        supporting_sources=[source_a["source_id"]],
        contradicting_sources=[source_b["source_id"]],
        citation_refs=[source_a["source_reference"], source_b["source_reference"]],
        unsupported_reason="contradicting sources remain visible",
        safe_metadata={"example_name": "two_sources_contradict_same_claim"},
    )
    examples.append(
        build_source_evidence_graph_v1(
            evidence_graph_id="two_sources_contradict_same_claim",
            source_nodes=[source_a, source_b],
            claim_nodes=[claim_contradicted],
            edges=[
                build_evidence_edge_v1(
                    edge_id="two_sources_contradict_same_claim:support",
                    edge_type="supports",
                    from_node_id=source_a["source_id"],
                    to_node_id=claim_contradicted["claim_id"],
                    edge_summary="source A supports the claim",
                ),
                build_evidence_edge_v1(
                    edge_id="two_sources_contradict_same_claim:contradict",
                    edge_type="contradicts",
                    from_node_id=source_b["source_id"],
                    to_node_id=claim_contradicted["claim_id"],
                    edge_summary="source B contradicts the claim",
                ),
            ],
            contradiction_summary={
                "contradiction_count": 1,
                "contradicting_pairs": [
                    {
                        "from_node_id": source_b["source_id"],
                        "to_node_id": claim_contradicted["claim_id"],
                        "edge_id": "two_sources_contradict_same_claim:contradict",
                    }
                ],
            },
            claim_grounding_status="partially_grounded",
            citation_readiness="partially_ready",
            rag_readiness="partially_ready",
            public_claim_readiness="blocked",
            recommended_next_check="resolve the contradiction explicitly before grounding further",
        )
    )

    poisoned_source = build_source_evidence_node_v1(
        source_id="poisoned_source_quarantined_cannot_support_claim:source",
        source_type="retrieved_content",
        source_name="Quarantined source",
        source_scope="internal",
        source_reference="retrieved:poisoned",
        freshness_status="fresh",
        quality_status="low_quality",
        poison_shield_status="quarantined",
        access_level="restricted",
        privacy_sensitivity="medium",
        owner_authorized=False,
        operator_authorized=False,
        safe_metadata={"example_name": "poisoned_source_quarantined_cannot_support_claim"},
    )
    poisoned_claim = build_claim_node_v1(
        claim_id="poisoned_source_quarantined_cannot_support_claim:claim",
        claim_text_summary="poisoned source cannot support a public claim",
        claim_status="poison_quarantined",
        claim_scope="public",
        public_claim_sensitive=True,
        requires_owner_approval=True,
        unsupported_reason="poisoned source remains quarantined",
        safe_metadata={"example_name": "poisoned_source_quarantined_cannot_support_claim"},
        node_type=NODE_TYPE_PUBLIC_CLAIM_V1,
    )
    examples.append(
        build_source_evidence_graph_v1(
            evidence_graph_id="poisoned_source_quarantined_cannot_support_claim",
            source_nodes=[poisoned_source],
            claim_nodes=[poisoned_claim],
            poison_quarantined_sources=[poisoned_source["source_id"]],
            access_restricted_sources=[poisoned_source["source_id"]],
            edges=[
                build_evidence_edge_v1(
                    edge_id="poisoned_source_quarantined_cannot_support_claim:blocked",
                    edge_type="blocked_by",
                    from_node_id=poisoned_claim["claim_id"],
                    to_node_id=poisoned_source["source_id"],
                    edge_summary="quarantined source blocks public use",
                    source_refs=[poisoned_source["source_reference"]],
                )
            ],
            claim_grounding_status="blocked",
            citation_readiness="blocked",
            rag_readiness="blocked",
            public_claim_readiness="blocked",
            recommended_next_check="keep the source quarantined and do not support public claims with it",
        )
    )

    restricted_source = build_source_evidence_node_v1(
        source_id="access_restricted_document_blocked_for_public_answer:source",
        source_type="document",
        source_name="Restricted document",
        source_scope="private",
        source_reference="doc:restricted",
        freshness_status="fresh",
        quality_status="high_quality",
        access_level="restricted",
        privacy_sensitivity="high",
        owner_authorized=True,
        operator_authorized=False,
        safe_metadata={"example_name": "access_restricted_document_blocked_for_public_answer"},
    )
    restricted_claim = build_claim_node_v1(
        claim_id="access_restricted_document_blocked_for_public_answer:claim",
        claim_text_summary="restricted document cannot be used in a public answer",
        claim_status="access_restricted",
        claim_scope="public",
        public_claim_sensitive=True,
        requires_owner_approval=True,
        unsupported_reason="access restriction prevents public answer use",
        safe_metadata={"example_name": "access_restricted_document_blocked_for_public_answer"},
        node_type=NODE_TYPE_PUBLIC_CLAIM_V1,
    )
    examples.append(
        build_source_evidence_graph_v1(
            evidence_graph_id="access_restricted_document_blocked_for_public_answer",
            source_nodes=[restricted_source],
            claim_nodes=[restricted_claim],
            access_restricted_sources=[restricted_source["source_id"]],
            edges=[
                build_evidence_edge_v1(
                    edge_id="access_restricted_document_blocked_for_public_answer:blocked",
                    edge_type="requires_access_check",
                    from_node_id=restricted_claim["claim_id"],
                    to_node_id=restricted_source["source_id"],
                    edge_summary="public answer use requires an access check",
                )
            ],
            claim_grounding_status="blocked",
            citation_readiness="blocked",
            rag_readiness="blocked",
            public_claim_readiness="blocked",
            recommended_next_check="obtain an explicit access boundary before public use",
        )
    )

    artifact_source = build_source_evidence_node_v1(
        source_id="artifact_provenance_supports_generated_artifact_claim:source",
        source_type="artifact_provenance",
        source_name="Artifact provenance record",
        source_scope="internal",
        source_reference="artifact:provenance:1",
        freshness_status="fresh",
        quality_status="high_quality",
        safe_metadata={"example_name": "artifact_provenance_supports_generated_artifact_claim"},
    )
    artifact_node = {
        "node_type": NODE_TYPE_ARTIFACT_V1,
        "node_id": "artifact_provenance_supports_generated_artifact_claim:artifact",
        "artifact_id": "artifact_provenance_supports_generated_artifact_claim:artifact",
        "artifact_label": "generated artifact",
        "safe_metadata": {"example_name": "artifact_provenance_supports_generated_artifact_claim"},
    }
    artifact_claim = build_claim_node_v1(
        claim_id="artifact_provenance_supports_generated_artifact_claim:claim",
        claim_text_summary="artifact provenance supports the generated artifact claim",
        claim_status="supported",
        claim_scope="internal",
        supporting_sources=[artifact_source["source_id"]],
        citation_refs=[artifact_source["source_reference"]],
        safe_metadata={"example_name": "artifact_provenance_supports_generated_artifact_claim"},
    )
    examples.append(
        build_source_evidence_graph_v1(
            evidence_graph_id="artifact_provenance_supports_generated_artifact_claim",
            source_nodes=[artifact_source],
            artifact_nodes=[artifact_node],
            claim_nodes=[artifact_claim],
            edges=[
                build_evidence_edge_v1(
                    edge_id="artifact_provenance_supports_generated_artifact_claim:edge",
                    edge_type="derived_from",
                    from_node_id=artifact_claim["claim_id"],
                    to_node_id=artifact_node["node_id"],
                    edge_summary="claim derived from artifact provenance",
                )
            ],
            claim_grounding_status="grounded",
            citation_readiness="ready",
            rag_readiness="ready",
            public_claim_readiness="blocked",
            recommended_next_check="use artifact provenance as metadata evidence only",
        )
    )

    signal_source = build_source_evidence_node_v1(
        source_id="signal_freshness_supports_energy_forecast_claim:source",
        source_type="signal_provenance",
        source_name="Fresh signal",
        source_scope="internal",
        source_reference="signal:forecast:fresh",
        freshness_status="fresh",
        quality_status="high_quality",
        safe_metadata={"example_name": "signal_freshness_supports_energy_forecast_claim"},
    )
    forecast_node = {
        "node_type": NODE_TYPE_FORECAST_V1,
        "node_id": "signal_freshness_supports_energy_forecast_claim:forecast",
        "forecast_id": "signal_freshness_supports_energy_forecast_claim:forecast",
        "forecast_label": "energy forecast claim",
        "safe_metadata": {"example_name": "signal_freshness_supports_energy_forecast_claim"},
    }
    signal_claim = build_claim_node_v1(
        claim_id="signal_freshness_supports_energy_forecast_claim:claim",
        claim_text_summary="fresh signal supports an energy forecast claim",
        claim_status="supported",
        claim_scope="internal",
        supporting_sources=[signal_source["source_id"]],
        citation_refs=[signal_source["source_reference"]],
        safe_metadata={"example_name": "signal_freshness_supports_energy_forecast_claim"},
    )
    examples.append(
        build_source_evidence_graph_v1(
            evidence_graph_id="signal_freshness_supports_energy_forecast_claim",
            source_nodes=[signal_source],
            forecast_nodes=[forecast_node],
            claim_nodes=[signal_claim],
            edges=[
                build_evidence_edge_v1(
                    edge_id="signal_freshness_supports_energy_forecast_claim:edge",
                    edge_type="supports",
                    from_node_id=signal_source["source_id"],
                    to_node_id=signal_claim["claim_id"],
                    edge_summary="fresh signal supports forecast reasoning",
                )
            ],
            claim_grounding_status="grounded",
            citation_readiness="ready",
            rag_readiness="ready",
            public_claim_readiness="blocked",
            recommended_next_check="use the fresh signal as evidence for a bounded forecast",
        )
    )

    error_source = build_source_evidence_node_v1(
        source_id="forecast_error_invalidates_prior_assumption:source",
        source_type="forecast_error",
        source_name="Forecast error record",
        source_scope="internal",
        source_reference="forecast:error:1",
        freshness_status="fresh",
        quality_status="high_quality",
        safe_metadata={"example_name": "forecast_error_invalidates_prior_assumption"},
    )
    error_node = {
        "node_type": NODE_TYPE_FORECAST_ERROR_V1,
        "node_id": "forecast_error_invalidates_prior_assumption:error",
        "error_id": "forecast_error_invalidates_prior_assumption:error",
        "error_label": "prior assumption invalidated",
        "safe_metadata": {"example_name": "forecast_error_invalidates_prior_assumption"},
    }
    error_claim = build_claim_node_v1(
        claim_id="forecast_error_invalidates_prior_assumption:claim",
        claim_text_summary="forecast error invalidates the prior assumption",
        claim_status="contradicted",
        claim_scope="internal",
        contradicting_sources=[error_source["source_id"]],
        citation_refs=[error_source["source_reference"]],
        unsupported_reason="prior assumption invalidated by observed error",
        safe_metadata={"example_name": "forecast_error_invalidates_prior_assumption"},
    )
    examples.append(
        build_source_evidence_graph_v1(
            evidence_graph_id="forecast_error_invalidates_prior_assumption",
            source_nodes=[error_source],
            error_nodes=[error_node],
            claim_nodes=[error_claim],
            edges=[
                build_evidence_edge_v1(
                    edge_id="forecast_error_invalidates_prior_assumption:edge",
                    edge_type="invalidates",
                    from_node_id=error_node["node_id"],
                    to_node_id=error_claim["claim_id"],
                    edge_summary="forecast error invalidates the assumption",
                )
            ],
            claim_grounding_status="blocked",
            citation_readiness="partially_ready",
            rag_readiness="partially_ready",
            public_claim_readiness="blocked",
            recommended_next_check="revise the assumption and keep the error visible",
        )
    )

    inference_node = {
        "node_type": NODE_TYPE_INFERENCE_V1,
        "node_id": "naie_rejects_llm_candidate_missing_source_edge:inference",
        "inference_packet_id": "naie_rejects_llm_candidate_missing_source_edge:inference",
        "inference_mode": "candidate_rejection",
        "safe_metadata": {"example_name": "naie_rejects_llm_candidate_missing_source_edge"},
    }
    candidate_node = {
        "node_type": NODE_TYPE_CANDIDATE_ANSWER_V1,
        "node_id": "naie_rejects_llm_candidate_missing_source_edge:candidate",
        "candidate_answer_id": "naie_rejects_llm_candidate_missing_source_edge:candidate",
        "candidate_status": "candidate_rejected",
        "candidate_label": "llm_candidate_without_source_edge",
        "unsupported_reason": "missing source edge prevents candidate promotion",
        "safe_metadata": {"example_name": "naie_rejects_llm_candidate_missing_source_edge"},
    }
    examples.append(
        build_source_evidence_graph_v1(
            evidence_graph_id="naie_rejects_llm_candidate_missing_source_edge",
            inference_nodes=[inference_node],
            candidate_answer_nodes=[candidate_node],
            missing_sources=["source_edge:llm_candidate"],
            unsupported_claims=[candidate_node["candidate_answer_id"]],
            claim_grounding_status="blocked",
            citation_readiness="blocked",
            rag_readiness="blocked",
            public_claim_readiness="blocked",
            recommended_next_check="add the missing source edge before considering the candidate",
        )
    )

    public_source = build_source_evidence_node_v1(
        source_id="public_claim_blocked_not_public_safe:source",
        source_type="signal_provenance",
        source_name="Public claim source",
        source_scope="internal",
        source_reference="signal:public:1",
        freshness_status="fresh",
        quality_status="high_quality",
        safe_metadata={"example_name": "public_claim_blocked_not_public_safe"},
    )
    public_claim = build_claim_node_v1(
        claim_id="public_claim_blocked_not_public_safe:claim",
        claim_text_summary="public claim blocked because maturity is not public safe",
        claim_status="unsupported",
        claim_scope="public",
        public_claim_sensitive=True,
        requires_owner_approval=True,
        unsupported_reason="public-safe maturity is missing",
        safe_metadata={"example_name": "public_claim_blocked_not_public_safe"},
        node_type=NODE_TYPE_PUBLIC_CLAIM_V1,
    )
    examples.append(
        build_source_evidence_graph_v1(
            evidence_graph_id="public_claim_blocked_not_public_safe",
            source_nodes=[public_source],
            public_claim_nodes=[public_claim],
            claim_nodes=[public_claim],
            claim_grounding_status="blocked",
            citation_readiness="blocked",
            rag_readiness="blocked",
            public_claim_readiness="blocked",
            recommended_next_check="wait for public-safe maturity and owner/operator approval",
        )
    )

    return examples
