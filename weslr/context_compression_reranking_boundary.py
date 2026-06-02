"""Metadata-only context compression and reranking boundary helpers v1.

This module selects, compresses, ranks, summarizes, drops, blocks, cavesat, or
deferred context units from explicit metadata only. It is pure, deterministic,
import-safe, and fail-closed.

It does not compress raw documents, retrieve evidence, call models/providers,
create indexes, write memory, touch `.weslr`, or assemble final answers.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

HELPER_TYPE_V1 = "context_compression_reranking_boundary_v1"
PACKET_TYPE_V1 = "context_compression_reranking_packet_v1"
SUMMARY_TYPE_V1 = "context_compression_reranking_packet_summary_v1"

ALLOWED_CONTEXT_UNIT_TYPES_V1 = {
    "claim_context",
    "source_summary_context",
    "citation_context",
    "document_summary_context",
    "chunk_summary_context",
    "memory_summary_context",
    "artifact_provenance_context",
    "signal_metadata_context",
    "forecast_context",
    "scenario_context",
    "forecast_error_context",
    "naie_inference_context",
    "daemon_verdict_context",
    "unknown_context",
}

ALLOWED_COMPRESSION_MODES_V1 = {
    "no_compression",
    "metadata_only",
    "summary_only",
    "claim_preserving_summary",
    "citation_preserving_summary",
    "contradiction_preserving_summary",
    "freshness_preserving_summary",
    "privacy_preserving_summary",
    "hash_reference_only",
    "drop_blocked_context",
    "defer_due_missing_context",
    "unknown_compression_mode",
}

ALLOWED_RERANKING_MODES_V1 = {
    "source_freshness_first",
    "claim_relevance_first",
    "citation_readiness_first",
    "access_allowed_first",
    "contradiction_visibility_first",
    "owner_priority_first",
    "safety_risk_first",
    "public_claim_safety_first",
    "no_reranking",
    "unknown_reranking_mode",
}

ALLOWED_CONTEXT_BUDGET_STATUSES_V1 = {
    "within_budget",
    "near_budget_limit",
    "over_budget",
    "budget_unknown",
}

FORBIDDEN_FIELD_PHRASES_V1 = (
    "hidden prompt",
    "raw private",
    "private data",
    "api key",
    "credential",
    "password",
)
FORBIDDEN_FIELD_SINGLE_TOKENS_V1 = {"secret", "token", "key"}

FORBIDDEN_CLAIM_PHRASES_V1 = (
    "hallucination elimination",
    "hallucination-free",
    "no hallucinations",
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
DEFAULT_SELECTED_LIMITS_V1 = {
    "within_budget": None,
    "near_budget_limit": 4,
    "over_budget": 2,
    "budget_unknown": 3,
}

FRESHNESS_ORDER_V1 = {
    "fresh": 5,
    "current": 4,
    "recent": 3,
    "stable": 2,
    "stale": 1,
    "unknown": 0,
}

CLAIM_RELEVANCE_ORDER_V1 = {
    "high": 3,
    "medium": 2,
    "low": 1,
    "unknown": 0,
}

CITATION_READINESS_ORDER_V1 = {
    True: 2,
    False: 0,
}

ACCESS_ORDER_V1 = {
    "access_allowed": 3,
    "public_safe": 3,
    "summary_only": 2,
    "access_restricted": 1,
    "private_source_blocked": 0,
    "public_use_blocked": 0,
    "blocked": 0,
    "unknown": 1,
}

RISK_ORDER_V1 = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "blocked": 4,
    "unknown": 0,
}

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



def to_context_compression_json_safe_v1(value: Any) -> Any:
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
            if any(hint.replace("_", " ") in key_text or hint in key_raw for hint in FORBIDDEN_FIELD_PHRASES_V1):
                return _safe_text(key)
            if any(token in key_text.split() or token in key_raw for token in FORBIDDEN_FIELD_SINGLE_TOKENS_V1):
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
    if any(hint.replace("_", " ") in text or hint in raw for hint in FORBIDDEN_FIELD_PHRASES_V1):
        return _safe_text(value)
    if any(token in text.split() or token in raw for token in FORBIDDEN_FIELD_SINGLE_TOKENS_V1):
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
    return any(phrase in text for phrase in FORBIDDEN_CLAIM_PHRASES_V1)



def _safe_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        value = [value]
    if isinstance(value, Mapping):
        value = list(value.values())
    if not isinstance(value, (list, tuple, set)):
        text = _safe_text(value)
        return [text] if text else []
    items = []
    for item in value:
        text = _safe_text(item)
        if text:
            items.append(text)
    return items



def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}



def _safe_unit(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return _json_safe(dict(value))
    if is_dataclass(value):
        return _json_safe(asdict(value))
    return {"context_unit_id": _safe_text(value)} if _safe_text(value) else {}



def _normalize_units(values: Any) -> list[dict[str, Any]]:
    return [_safe_unit(item) for item in _safe_str_list(values)] if not isinstance(values, (list, tuple, set, Mapping)) else [
        _safe_unit(item) for item in (list(values.values()) if isinstance(values, Mapping) else values)
    ]



def _unit_type(unit: Mapping[str, Any]) -> str:
    return _safe_text(unit.get("context_unit_type") or unit.get("unit_type") or unit.get("type"))



def _unit_id(unit: Mapping[str, Any]) -> str:
    return _safe_text(unit.get("context_unit_id") or unit.get("unit_id") or unit.get("id") or unit.get("ref"))



def _unit_summary(unit: Mapping[str, Any]) -> str:
    return _safe_text(unit.get("summary") or unit.get("unit_summary") or unit.get("text_summary") or unit.get("label"))



def _unit_public_safe(unit: Mapping[str, Any]) -> bool:
    if "public_safe" in unit:
        return _safe_bool(unit.get("public_safe"))
    access_status = _safe_text(unit.get("access_status") or unit.get("source_access_status") or unit.get("privacy_status"))
    if access_status in {"access_restricted", "private_source_blocked", "public_use_blocked", "privacy_blocked"}:
        return False
    privacy_status = _safe_text(unit.get("privacy_status"))
    if privacy_status in {"high_sensitivity", "privacy_blocked"}:
        return False
    return True



def _unit_access_status(unit: Mapping[str, Any]) -> str:
    return _safe_text(unit.get("access_status") or unit.get("source_access_status") or "access_allowed")



def _unit_poison_status(unit: Mapping[str, Any]) -> str:
    return _safe_text(unit.get("poison_status") or unit.get("poison_flag") or "clean")



def _unit_freshness_status(unit: Mapping[str, Any]) -> str:
    return _safe_text(unit.get("freshness_status") or unit.get("freshness") or "unknown")



def _unit_citation_required(unit: Mapping[str, Any]) -> bool:
    if "citation_required" in unit:
        return _safe_bool(unit.get("citation_required"))
    return _safe_bool(unit.get("citation_needed"))



def _unit_contradictory(unit: Mapping[str, Any]) -> bool:
    status = _safe_text(unit.get("claim_status") or unit.get("grounding_status") or unit.get("evidence_status"))
    if status == "contradicted":
        return True
    if _safe_bool(unit.get("contradiction_present")):
        return True
    if _safe_str_list(unit.get("contradiction_refs")):
        return True
    return False



def _unit_unsupported(unit: Mapping[str, Any]) -> bool:
    status = _safe_text(unit.get("claim_status") or unit.get("grounding_status") or unit.get("evidence_status"))
    return status == "unsupported" or _safe_bool(unit.get("unsupported_claim"))



def _unit_stale(unit: Mapping[str, Any]) -> bool:
    status = _unit_freshness_status(unit)
    return status in {"stale", "stale_support", "stale_source", "stale_signal"}



def _unit_private(unit: Mapping[str, Any]) -> bool:
    privacy = _safe_text(unit.get("privacy_status") or unit.get("privacy_level") or "")
    if privacy in {"private", "restricted", "high_sensitivity", "privacy_blocked"}:
        return True
    access_status = _unit_access_status(unit)
    return access_status in {"access_restricted", "private_source_blocked", "public_use_blocked"}



def _unit_secret(unit: Mapping[str, Any]) -> bool:
    if _safe_bool(unit.get("contains_secret")) or _safe_bool(unit.get("contains_private_data")):
        return True
    if any(key in unit for key in ("api_key", "token", "secret", "credential", "password")):
        return True
    if _contains_forbidden_field(unit):
        return True
    return False



def _unit_has_freshness_caveat(unit: Mapping[str, Any]) -> bool:
    return _unit_stale(unit) or _safe_text(unit.get("freshness_caveat")) != ""



def _unit_risk_score(unit: Mapping[str, Any]) -> int:
    status = _safe_text(unit.get("risk_status") or unit.get("safety_risk") or "unknown")
    return RISK_ORDER_V1.get(status, RISK_ORDER_V1["unknown"])



def _unit_freshness_score(unit: Mapping[str, Any]) -> int:
    status = _unit_freshness_status(unit)
    return FRESHNESS_ORDER_V1.get(status, FRESHNESS_ORDER_V1["unknown"])



def _unit_claim_relevance_score(unit: Mapping[str, Any]) -> int:
    relevance = _safe_text(unit.get("claim_relevance") or unit.get("relevance") or "unknown")
    return CLAIM_RELEVANCE_ORDER_V1.get(relevance, CLAIM_RELEVANCE_ORDER_V1["unknown"])



def _unit_citation_score(unit: Mapping[str, Any]) -> int:
    return 2 if _unit_citation_required(unit) or _safe_str_list(unit.get("citation_refs")) else 0



def _unit_access_score(unit: Mapping[str, Any]) -> int:
    status = _unit_access_status(unit)
    if _unit_public_safe(unit) and status == "access_allowed":
        return 3
    return ACCESS_ORDER_V1.get(status, ACCESS_ORDER_V1["unknown"])



def _unit_owner_priority_score(unit: Mapping[str, Any]) -> int:
    return 1 if _safe_bool(unit.get("owner_priority")) else 0



def _unit_deadline_score(unit: Mapping[str, Any]) -> int:
    relevance = _safe_text(unit.get("deadline_relevance") or unit.get("urgency") or "unknown")
    if relevance in {"urgent", "high", "now", "deadline"}:
        return 3
    if relevance in {"medium", "soon", "near"}:
        return 2
    if relevance in {"low", "later"}:
        return 1
    return 0



def _unit_public_claim_safety_score(unit: Mapping[str, Any]) -> int:
    return 1 if _unit_public_safe(unit) else 0



def _unit_sort_key(unit: Mapping[str, Any], mode: str) -> tuple:
    base = (_unit_id(unit), _unit_type(unit))
    if mode == "source_freshness_first":
        return (-_unit_freshness_score(unit), -_unit_deadline_score(unit), -_unit_claim_relevance_score(unit), base)
    if mode == "claim_relevance_first":
        return (-_unit_claim_relevance_score(unit), -_unit_citation_score(unit), -_unit_freshness_score(unit), base)
    if mode == "citation_readiness_first":
        return (-_unit_citation_score(unit), -_unit_claim_relevance_score(unit), -_unit_freshness_score(unit), base)
    if mode == "access_allowed_first":
        return (-_unit_access_score(unit), -_unit_freshness_score(unit), base)
    if mode == "contradiction_visibility_first":
        return (0 if _unit_contradictory(unit) else 1, -_unit_claim_relevance_score(unit), -_unit_freshness_score(unit), base)
    if mode == "owner_priority_first":
        return (-_unit_owner_priority_score(unit), -_unit_claim_relevance_score(unit), -_unit_freshness_score(unit), base)
    if mode == "safety_risk_first":
        return (-_unit_risk_score(unit), -_unit_access_score(unit), -_unit_freshness_score(unit), base)
    if mode == "public_claim_safety_first":
        return (-_unit_public_claim_safety_score(unit), -_unit_freshness_score(unit), -_unit_claim_relevance_score(unit), base)
    if mode == "no_reranking":
        return base
    return base



def _unit_blocked_public(unit: Mapping[str, Any], public_context: bool) -> bool:
    if _unit_secret(unit):
        return True
    if not public_context:
        return False
    if _unit_private(unit):
        return True
    if not _unit_public_safe(unit):
        return True
    return False



def _unit_block_reason(unit: Mapping[str, Any], public_context: bool) -> str:
    if _unit_secret(unit):
        return "secret_or_private_data"
    if public_context and _unit_private(unit):
        return "access_restricted"
    if public_context and not _unit_public_safe(unit):
        return "public_not_safe"
    return "blocked"



def _unit_compression_payload(unit: Mapping[str, Any], mode: str) -> dict[str, Any]:
    uid = _unit_id(unit)
    payload = {
        "context_unit_id": uid,
        "context_unit_type": _unit_type(unit),
    }
    if mode == "no_compression":
        return _json_safe(unit)
    if mode == "metadata_only":
        return {
            **payload,
            "summary": _unit_summary(unit),
            "access_status": _unit_access_status(unit),
            "poison_status": _unit_poison_status(unit),
            "freshness_status": _unit_freshness_status(unit),
            "citation_refs": _safe_str_list(unit.get("citation_refs")),
            "claim_status": _safe_text(unit.get("claim_status") or unit.get("grounding_status") or ""),
        }
    if mode == "summary_only":
        return {**payload, "summary": _unit_summary(unit)}
    if mode == "claim_preserving_summary":
        return {
            **payload,
            "summary": _unit_summary(unit),
            "claim_status": _safe_text(unit.get("claim_status") or unit.get("grounding_status") or ""),
            "claim_refs": _safe_str_list(unit.get("claim_refs") or unit.get("claim_ids")),
        }
    if mode == "citation_preserving_summary":
        return {
            **payload,
            "summary": _unit_summary(unit),
            "citation_refs": _safe_str_list(unit.get("citation_refs")),
        }
    if mode == "contradiction_preserving_summary":
        return {
            **payload,
            "summary": _unit_summary(unit),
            "contradiction_refs": _safe_str_list(unit.get("contradiction_refs")),
            "contradiction_present": _unit_contradictory(unit),
        }
    if mode == "freshness_preserving_summary":
        return {
            **payload,
            "summary": _unit_summary(unit),
            "freshness_status": _unit_freshness_status(unit),
            "freshness_caveat": _safe_text(unit.get("freshness_caveat")),
        }
    if mode == "privacy_preserving_summary":
        return {
            **payload,
            "summary": _unit_summary(unit),
            "access_status": _unit_access_status(unit),
            "privacy_status": _safe_text(unit.get("privacy_status") or ""),
            "poison_status": _unit_poison_status(unit),
        }
    if mode == "hash_reference_only":
        hash_ref = _safe_text(unit.get("hash_ref") or unit.get("content_hash") or f"hash:{uid}")
        return {**payload, "hash_ref": hash_ref}
    if mode == "drop_blocked_context":
        return {**payload, "summary": _unit_summary(unit)}
    if mode == "defer_due_missing_context":
        return {**payload, "summary": _unit_summary(unit)}
    return {**payload, "summary": _unit_summary(unit)}



def _context_budget_limit(status: str) -> int | None:
    return DEFAULT_SELECTED_LIMITS_V1.get(status, 3)



def _detect_context_budget_status(context_units: list[Mapping[str, Any]], packet: Mapping[str, Any] | None = None) -> str:
    if packet is not None:
        explicit = _safe_text(packet.get("context_budget_status"))
        if explicit in ALLOWED_CONTEXT_BUDGET_STATUSES_V1:
            return explicit
    count = len(context_units)
    if count <= 4:
        return "within_budget"
    if count <= 7:
        return "near_budget_limit"
    return "over_budget"



def _derive_lost_in_middle_risk(selected_count: int, total_count: int, budget_status: str) -> str:
    if budget_status == "over_budget" or total_count > 7:
        return "high"
    if budget_status == "near_budget_limit" or total_count > 4:
        return "medium"
    if selected_count and total_count > selected_count:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Packet builders
# ---------------------------------------------------------------------------


def build_context_compression_packet_v1(
    context_packet_id: str,
    query_summary: str,
    context_units: list[Any] | None = None,
    selected_context_units: list[Any] | None = None,
    dropped_context_units: list[Any] | None = None,
    blocked_context_units: list[Any] | None = None,
    compression_mode: str = "unknown_compression_mode",
    reranking_mode: str = "unknown_reranking_mode",
    selection_reason: str = "",
    dropped_reason_summary: str = "",
    contradictions_preserved: bool = False,
    unsupported_claims_preserved: bool = False,
    citation_refs_preserved: bool = False,
    freshness_refs_preserved: bool = False,
    access_restrictions_preserved: bool = False,
    privacy_restrictions_preserved: bool = False,
    poison_flags_preserved: bool = False,
    lost_in_middle_risk: str = "unknown",
    context_budget_status: str = "budget_unknown",
    recommended_next_check: str = "",
    runtime_authority: bool = False,
    writes_state: bool = False,
    model_provider_used: bool = False,
    public_claim_allowed: bool = False,
    proof_claim_allowed: bool = False,
    learning_claimed: bool = False,
    safe_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    units = [_safe_unit(unit) for unit in (context_units or [])]
    packet: dict[str, Any] = {
        "helper_type": HELPER_TYPE_V1,
        "packet_type": PACKET_TYPE_V1,
        "context_packet_id": _safe_text(context_packet_id),
        "query_summary": _safe_text(query_summary),
        "context_units": units,
        "selected_context_units": [_safe_unit(unit) for unit in (selected_context_units or [])],
        "dropped_context_units": [_safe_unit(unit) for unit in (dropped_context_units or [])],
        "blocked_context_units": [_safe_unit(unit) for unit in (blocked_context_units or [])],
        "compression_mode": _safe_text(compression_mode),
        "reranking_mode": _safe_text(reranking_mode),
        "selection_reason": _safe_text(selection_reason),
        "dropped_reason_summary": _safe_text(dropped_reason_summary),
        "contradictions_preserved": _safe_bool(contradictions_preserved),
        "unsupported_claims_preserved": _safe_bool(unsupported_claims_preserved),
        "citation_refs_preserved": _safe_bool(citation_refs_preserved),
        "freshness_refs_preserved": _safe_bool(freshness_refs_preserved),
        "access_restrictions_preserved": _safe_bool(access_restrictions_preserved),
        "privacy_restrictions_preserved": _safe_bool(privacy_restrictions_preserved),
        "poison_flags_preserved": _safe_bool(poison_flags_preserved),
        "lost_in_middle_risk": _safe_text(lost_in_middle_risk),
        "context_budget_status": _safe_text(context_budget_status),
        "recommended_next_check": _safe_text(recommended_next_check),
        "runtime_authority": _safe_bool(runtime_authority),
        "writes_state": _safe_bool(writes_state),
        "model_provider_used": _safe_bool(model_provider_used),
        "public_claim_allowed": _safe_bool(public_claim_allowed),
        "proof_claim_allowed": _safe_bool(proof_claim_allowed),
        "learning_claimed": _safe_bool(learning_claimed),
        "safe_metadata": _json_safe(DEFAULT_SAFE_METADATA_V1 if safe_metadata is None else safe_metadata),
    }

    if packet["compression_mode"] == "unknown_compression_mode":
        packet["compression_mode"] = "metadata_only"
    if packet["reranking_mode"] == "unknown_reranking_mode":
        packet["reranking_mode"] = "no_reranking"
    if packet["context_budget_status"] == "budget_unknown":
        packet["context_budget_status"] = _detect_context_budget_status(units, packet)
    if packet["lost_in_middle_risk"] == "unknown":
        packet["lost_in_middle_risk"] = _derive_lost_in_middle_risk(len(packet["selected_context_units"]), len(units), packet["context_budget_status"])

    if not packet["selected_context_units"] and units:
        packet["selected_context_units"] = select_context_units_v1(packet)
    if not packet["blocked_context_units"] and units:
        packet["blocked_context_units"] = [unit for unit in units if unit not in packet["selected_context_units"] and _unit_secret(unit)]
    if not packet["dropped_context_units"] and units:
        packet["dropped_context_units"] = [unit for unit in units if unit not in packet["selected_context_units"] and unit not in packet["blocked_context_units"]]

    return packet


# ---------------------------------------------------------------------------
# Ranking / selection / compression
# ---------------------------------------------------------------------------


def rank_context_units_v1(packet: Any) -> list[dict[str, Any]]:
    normalized = to_context_compression_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        return []
    units = [_safe_unit(unit) for unit in _safe_str_list(normalized.get("context_units"))] if not isinstance(normalized.get("context_units"), list) else [_safe_unit(unit) for unit in normalized.get("context_units", [])]
    mode = _safe_text(normalized.get("reranking_mode"))
    if mode not in ALLOWED_RERANKING_MODES_V1:
        return units
    if mode == "no_reranking":
        return units
    return sorted(units, key=lambda unit: _unit_sort_key(unit, mode))



def select_context_units_v1(packet: Any) -> list[dict[str, Any]]:
    normalized = to_context_compression_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        return []
    context_units = normalized.get("context_units") or []
    units = [_safe_unit(unit) for unit in context_units]
    public_context = _safe_bool(_safe_dict(normalized.get("safe_metadata")).get("public_context")) or _safe_bool(normalized.get("public_claim_allowed"))
    ranked = rank_context_units_v1(normalized)
    budget_status = _safe_text(normalized.get("context_budget_status"))
    limit = _context_budget_limit(budget_status)
    selected: list[dict[str, Any]] = []
    for unit in ranked:
        if _unit_secret(unit):
            continue
        if _unit_blocked_public(unit, public_context):
            continue
        selected.append(unit)
        if limit is not None and len(selected) >= limit:
            break
    if not selected and ranked:
        for unit in ranked:
            if not _unit_secret(unit) and not _unit_blocked_public(unit, False):
                selected.append(unit)
                if limit is not None and len(selected) >= limit:
                    break
    return selected



def compress_context_units_v1(packet: Any) -> list[dict[str, Any]]:
    normalized = to_context_compression_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        return []
    mode = _safe_text(normalized.get("compression_mode"))
    selected = normalized.get("selected_context_units") or select_context_units_v1(normalized)
    selected_units = [_safe_unit(unit) for unit in selected]
    if mode == "drop_blocked_context":
        return [unit for unit in selected_units if not _unit_secret(unit)]
    if mode == "defer_due_missing_context":
        return []
    return [_unit_compression_payload(unit, mode) for unit in selected_units]


# ---------------------------------------------------------------------------
# Validation and summary
# ---------------------------------------------------------------------------


def validate_context_compression_packet_v1(packet: Any) -> bool:
    normalized = to_context_compression_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        raise ValidationError("packet_must_be_mapping")

    forbidden_field = _contains_forbidden_field(normalized)
    if forbidden_field:
        raise ValidationError(f"forbidden_field_present:{forbidden_field}")
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_phrase_present")

    compression_mode = _safe_text(normalized.get("compression_mode"))
    reranking_mode = _safe_text(normalized.get("reranking_mode"))
    context_budget_status = _safe_text(normalized.get("context_budget_status"))

    if compression_mode not in ALLOWED_COMPRESSION_MODES_V1:
        raise ValidationError("unknown_compression_mode")
    if reranking_mode not in ALLOWED_RERANKING_MODES_V1:
        raise ValidationError("unknown_reranking_mode")
    if context_budget_status not in ALLOWED_CONTEXT_BUDGET_STATUSES_V1:
        raise ValidationError("unknown_context_budget_status")

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

    context_units = [_safe_unit(unit) for unit in normalized.get("context_units") or []]
    selected_units = [_safe_unit(unit) for unit in normalized.get("selected_context_units") or []]
    dropped_units = [_safe_unit(unit) for unit in normalized.get("dropped_context_units") or []]
    blocked_units = [_safe_unit(unit) for unit in normalized.get("blocked_context_units") or []]
    public_context = _safe_bool(_safe_dict(normalized.get("safe_metadata")).get("public_context")) or _safe_bool(normalized.get("public_claim_allowed"))

    unit_types = {_unit_type(unit) for unit in context_units}
    for unit_type in unit_types:
        if unit_type not in ALLOWED_CONTEXT_UNIT_TYPES_V1:
            raise ValidationError("unknown_context_unit_type")

    if any(_unit_secret(unit) for unit in selected_units):
        raise ValidationError("selected_secret_or_api_key_blocked")
    if public_context and any(_unit_private(unit) for unit in selected_units):
        raise ValidationError("selected_private_or_access_restricted_context_not_public_safe")
    if public_context and any(not _unit_public_safe(unit) for unit in selected_units):
        raise ValidationError("selected_private_or_access_restricted_context_not_public_safe")

    contradictory_units = [unit for unit in context_units if _unit_contradictory(unit)]
    stale_units = [unit for unit in context_units if _unit_stale(unit)]
    restricted_units = [unit for unit in context_units if _unit_private(unit)]
    poison_units = [unit for unit in context_units if _unit_poison_status(unit) in {"poison_blocked", "quarantined", "poisoned"}]
    citation_required_units = [unit for unit in context_units if _unit_citation_required(unit)]

    if contradictory_units and not _safe_bool(normalized.get("contradictions_preserved")):
        raise ValidationError("contradictions_not_preserved")
    if restricted_units and not _safe_bool(normalized.get("access_restrictions_preserved")):
        raise ValidationError("access_restrictions_not_preserved")
    if poison_units and not _safe_bool(normalized.get("poison_flags_preserved")):
        raise ValidationError("poison_flags_not_preserved")
    if stale_units and not _safe_bool(normalized.get("freshness_refs_preserved")):
        raise ValidationError("freshness_caveats_not_preserved")
    if citation_required_units and not _safe_bool(normalized.get("citation_refs_preserved")):
        raise ValidationError("citation_refs_not_preserved_when_required")

    selected_ids = {_unit_id(unit) for unit in selected_units}
    blocked_ids = {_unit_id(unit) for unit in blocked_units}
    dropped_ids = {_unit_id(unit) for unit in dropped_units}
    all_ids = {_unit_id(unit) for unit in context_units}
    if not selected_ids.issubset(all_ids):
        raise ValidationError("selected_context_unit_unknown")
    if not blocked_ids.issubset(all_ids):
        raise ValidationError("blocked_context_unit_unknown")
    if not dropped_ids.issubset(all_ids):
        raise ValidationError("dropped_context_unit_unknown")

    for unit in context_units:
        if _unit_secret(unit):
            if _unit_id(unit) not in blocked_ids and _unit_id(unit) not in dropped_ids:
                raise ValidationError("selected_secret_or_api_key_blocked")

    if context_budget_status == "over_budget":
        next_check = _normalize_text(normalized.get("recommended_next_check"))
        if not any(token in next_check for token in ("defer", "clarif", "ask")):
            raise ValidationError("over_budget_requires_defer_or_clarification")

    if public_context and any(_unit_private(unit) or not _unit_public_safe(unit) for unit in selected_units):
        raise ValidationError("selected_private_or_access_restricted_context_not_public_safe")

    if any(_unit_secret(unit) for unit in context_units):
        if any(_unit_secret(unit) for unit in selected_units):
            raise ValidationError("selected_secret_or_api_key_blocked")

    return True



def summarize_context_compression_packet_v1(packet: Any) -> dict[str, Any]:
    validate_context_compression_packet_v1(packet)
    normalized = to_context_compression_json_safe_v1(packet)
    mapping = dict(normalized)
    return {
        "summary_type": SUMMARY_TYPE_V1,
        "context_packet_id": _safe_text(mapping.get("context_packet_id")),
        "query_summary": _safe_text(mapping.get("query_summary")),
        "context_unit_count": len(_safe_str_list(mapping.get("context_units"))) if not isinstance(mapping.get("context_units"), list) else len(mapping.get("context_units") or []),
        "selected_context_unit_count": len(_safe_str_list(mapping.get("selected_context_units"))) if not isinstance(mapping.get("selected_context_units"), list) else len(mapping.get("selected_context_units") or []),
        "blocked_context_unit_count": len(_safe_str_list(mapping.get("blocked_context_units"))) if not isinstance(mapping.get("blocked_context_units"), list) else len(mapping.get("blocked_context_units") or []),
        "compression_mode": _safe_text(mapping.get("compression_mode")),
        "reranking_mode": _safe_text(mapping.get("reranking_mode")),
        "context_budget_status": _safe_text(mapping.get("context_budget_status")),
        "lost_in_middle_risk": _safe_text(mapping.get("lost_in_middle_risk")),
        "recommended_next_check": _safe_text(mapping.get("recommended_next_check")),
        "contradictions_preserved": _safe_bool(mapping.get("contradictions_preserved")),
        "unsupported_claims_preserved": _safe_bool(mapping.get("unsupported_claims_preserved")),
        "citation_refs_preserved": _safe_bool(mapping.get("citation_refs_preserved")),
        "freshness_refs_preserved": _safe_bool(mapping.get("freshness_refs_preserved")),
        "access_restrictions_preserved": _safe_bool(mapping.get("access_restrictions_preserved")),
        "privacy_restrictions_preserved": _safe_bool(mapping.get("privacy_restrictions_preserved")),
        "poison_flags_preserved": _safe_bool(mapping.get("poison_flags_preserved")),
        "safe_metadata": _json_safe(mapping.get("safe_metadata", DEFAULT_SAFE_METADATA_V1)),
    }


# ---------------------------------------------------------------------------
# Initial examples
# ---------------------------------------------------------------------------


def build_initial_context_compression_examples_v1() -> list[dict[str, Any]]:
    examples = [
        build_context_compression_packet_v1(
            context_packet_id="fresh_supported_claim_selected_citation_preserved",
            query_summary="Answer a fresh supported claim.",
            context_units=[
                {
                    "context_unit_id": "claim:1",
                    "context_unit_type": "claim_context",
                    "summary": "supported claim",
                    "claim_status": "grounded",
                    "citation_required": True,
                    "citation_refs": ["cite:1"],
                    "freshness_status": "fresh",
                    "access_status": "access_allowed",
                    "public_safe": True,
                    "claim_relevance": "high",
                }
            ],
            compression_mode="citation_preserving_summary",
            reranking_mode="claim_relevance_first",
            selected_context_units=[
                {
                    "context_unit_id": "claim:1",
                    "context_unit_type": "claim_context",
                    "summary": "supported claim",
                    "claim_status": "grounded",
                    "citation_refs": ["cite:1"],
                    "freshness_status": "fresh",
                    "access_status": "access_allowed",
                    "public_safe": True,
                }
            ],
            contradictions_preserved=False,
            unsupported_claims_preserved=False,
            citation_refs_preserved=True,
            freshness_refs_preserved=True,
            access_restrictions_preserved=False,
            privacy_restrictions_preserved=False,
            poison_flags_preserved=False,
            context_budget_status="within_budget",
            recommended_next_check="none",
            safe_metadata={"example_name": "fresh_supported_claim_selected_citation_preserved", "public_context": False},
        ),
        build_context_compression_packet_v1(
            context_packet_id="stale_source_compressed_with_freshness_caveat",
            query_summary="Compress a stale source but keep the caveat.",
            context_units=[
                {
                    "context_unit_id": "source:2",
                    "context_unit_type": "source_summary_context",
                    "summary": "stale source",
                    "freshness_status": "stale",
                    "freshness_caveat": "source is stale",
                    "access_status": "access_allowed",
                    "public_safe": True,
                    "claim_relevance": "medium",
                }
            ],
            compression_mode="freshness_preserving_summary",
            reranking_mode="source_freshness_first",
            selected_context_units=[
                {
                    "context_unit_id": "source:2",
                    "context_unit_type": "source_summary_context",
                    "summary": "stale source",
                    "freshness_status": "stale",
                    "freshness_caveat": "source is stale",
                }
            ],
            freshness_refs_preserved=True,
            context_budget_status="within_budget",
            recommended_next_check="refresh_source_if_available",
            safe_metadata={"example_name": "stale_source_compressed_with_freshness_caveat", "public_context": False},
        ),
        build_context_compression_packet_v1(
            context_packet_id="contradictory_sources_both_retained",
            query_summary="Retain both contradictory sources.",
            context_units=[
                {
                    "context_unit_id": "source:3a",
                    "context_unit_type": "source_summary_context",
                    "summary": "source A",
                    "claim_status": "grounded",
                    "contradiction_present": True,
                    "access_status": "access_allowed",
                    "public_safe": True,
                },
                {
                    "context_unit_id": "source:3b",
                    "context_unit_type": "source_summary_context",
                    "summary": "source B",
                    "claim_status": "grounded",
                    "contradiction_present": True,
                    "access_status": "access_allowed",
                    "public_safe": True,
                },
            ],
            compression_mode="contradiction_preserving_summary",
            reranking_mode="contradiction_visibility_first",
            selected_context_units=[
                {
                    "context_unit_id": "source:3a",
                    "context_unit_type": "source_summary_context",
                    "summary": "source A",
                    "contradiction_present": True,
                },
                {
                    "context_unit_id": "source:3b",
                    "context_unit_type": "source_summary_context",
                    "summary": "source B",
                    "contradiction_present": True,
                },
            ],
            contradictions_preserved=True,
            context_budget_status="within_budget",
            recommended_next_check="surface_contradiction",
            safe_metadata={"example_name": "contradictory_sources_both_retained", "public_context": False},
        ),
        build_context_compression_packet_v1(
            context_packet_id="access_restricted_source_dropped_from_public_context",
            query_summary="Drop access-restricted source from public context.",
            context_units=[
                {
                    "context_unit_id": "source:4a",
                    "context_unit_type": "source_summary_context",
                    "summary": "public source",
                    "access_status": "access_allowed",
                    "public_safe": True,
                },
                {
                    "context_unit_id": "source:4b",
                    "context_unit_type": "source_summary_context",
                    "summary": "restricted source",
                    "access_status": "access_restricted",
                    "public_safe": False,
                },
            ],
            compression_mode="privacy_preserving_summary",
            reranking_mode="access_allowed_first",
            selected_context_units=[
                {
                    "context_unit_id": "source:4a",
                    "context_unit_type": "source_summary_context",
                    "summary": "public source",
                    "access_status": "access_allowed",
                    "public_safe": True,
                }
            ],
            blocked_context_units=[
                {
                    "context_unit_id": "source:4b",
                    "context_unit_type": "source_summary_context",
                    "summary": "restricted source",
                    "access_status": "access_restricted",
                    "public_safe": False,
                }
            ],
            access_restrictions_preserved=True,
            privacy_restrictions_preserved=True,
            context_budget_status="within_budget",
            recommended_next_check="use_public_safe_source_only",
            safe_metadata={"example_name": "access_restricted_source_dropped_from_public_context", "public_context": True},
        ),
        build_context_compression_packet_v1(
            context_packet_id="poison_quarantined_source_blocked_from_context",
            query_summary="Block poison-quarantined source.",
            context_units=[
                {
                    "context_unit_id": "source:5",
                    "context_unit_type": "source_summary_context",
                    "summary": "quarantined source",
                    "poison_status": "poison_blocked",
                    "access_status": "access_allowed",
                    "public_safe": False,
                }
            ],
            compression_mode="drop_blocked_context",
            reranking_mode="safety_risk_first",
            blocked_context_units=[
                {
                    "context_unit_id": "source:5",
                    "context_unit_type": "source_summary_context",
                    "summary": "quarantined source",
                    "poison_status": "poison_blocked",
                }
            ],
            poison_flags_preserved=True,
            context_budget_status="within_budget",
            recommended_next_check="quarantine_source",
            safe_metadata={"example_name": "poison_quarantined_source_blocked_from_context", "public_context": True},
        ),
        build_context_compression_packet_v1(
            context_packet_id="private_project_memory_summary_only",
            query_summary="Compress private project memory as summary-only.",
            context_units=[
                {
                    "context_unit_id": "memory:6",
                    "context_unit_type": "memory_summary_context",
                    "summary": "private project memory summary",
                    "raw_content": "private notes",
                    "privacy_status": "high_sensitivity",
                    "access_status": "access_restricted",
                    "public_safe": False,
                    "owner_priority": True,
                }
            ],
            compression_mode="summary_only",
            reranking_mode="owner_priority_first",
            selected_context_units=[
                {
                    "context_unit_id": "memory:6",
                    "context_unit_type": "memory_summary_context",
                    "summary": "private project memory summary",
                    "privacy_status": "high_sensitivity",
                    "access_status": "access_restricted",
                }
            ],
            privacy_restrictions_preserved=True,
            access_restrictions_preserved=True,
            context_budget_status="within_budget",
            recommended_next_check="summary_only_internal_use",
            safe_metadata={"example_name": "private_project_memory_summary_only", "public_context": False},
        ),
        build_context_compression_packet_v1(
            context_packet_id="api_key_context_blocked_not_summarized",
            query_summary="Block API key context.",
            context_units=[
                {
                    "context_unit_id": "chunk:7",
                    "context_unit_type": "chunk_summary_context",
                    "summary": "contains API key",
                    "api_key": "sk-test-123",
                    "access_status": "access_restricted",
                    "public_safe": False,
                }
            ],
            compression_mode="drop_blocked_context",
            reranking_mode="safety_risk_first",
            blocked_context_units=[
                {
                    "context_unit_id": "chunk:7",
                    "context_unit_type": "chunk_summary_context",
                    "summary": "contains API key",
                    "api_key": "sk-test-123",
                }
            ],
            privacy_restrictions_preserved=True,
            context_budget_status="within_budget",
            recommended_next_check="block_secret_material",
            safe_metadata={"example_name": "api_key_context_blocked_not_summarized", "public_context": True},
        ),
        build_context_compression_packet_v1(
            context_packet_id="energy_signal_ranked_by_freshness_and_deadline",
            query_summary="Rank energy signal context by freshness and deadline.",
            context_units=[
                {
                    "context_unit_id": "signal:8a",
                    "context_unit_type": "signal_metadata_context",
                    "summary": "fresh signal",
                    "freshness_status": "fresh",
                    "deadline_relevance": "urgent",
                    "claim_relevance": "high",
                    "access_status": "access_allowed",
                    "public_safe": True,
                },
                {
                    "context_unit_id": "signal:8b",
                    "context_unit_type": "forecast_context",
                    "summary": "stale forecast",
                    "freshness_status": "stale",
                    "deadline_relevance": "low",
                    "claim_relevance": "medium",
                    "access_status": "access_allowed",
                    "public_safe": True,
                },
            ],
            compression_mode="metadata_only",
            reranking_mode="source_freshness_first",
            selected_context_units=[
                {
                    "context_unit_id": "signal:8a",
                    "context_unit_type": "signal_metadata_context",
                    "summary": "fresh signal",
                    "freshness_status": "fresh",
                    "deadline_relevance": "urgent",
                },
                {
                    "context_unit_id": "signal:8b",
                    "context_unit_type": "forecast_context",
                    "summary": "stale forecast",
                    "freshness_status": "stale",
                    "deadline_relevance": "low",
                },
            ],
            freshness_refs_preserved=True,
            context_budget_status="within_budget",
            recommended_next_check="prioritize_fresh_signal",
            safe_metadata={"example_name": "energy_signal_ranked_by_freshness_and_deadline", "public_context": False},
        ),
        build_context_compression_packet_v1(
            context_packet_id="public_claim_context_blocked_not_public_safe",
            query_summary="Block a public claim context that is not public safe.",
            context_units=[
                {
                    "context_unit_id": "claim:9",
                    "context_unit_type": "claim_context",
                    "summary": "public claim candidate",
                    "public_safe": False,
                    "access_status": "access_restricted",
                    "claim_status": "grounded",
                }
            ],
            compression_mode="defer_due_missing_context",
            reranking_mode="public_claim_safety_first",
            blocked_context_units=[
                {
                    "context_unit_id": "claim:9",
                    "context_unit_type": "claim_context",
                    "summary": "public claim candidate",
                    "public_safe": False,
                    "access_status": "access_restricted",
                }
            ],
            access_restrictions_preserved=True,
            privacy_restrictions_preserved=True,
            context_budget_status="within_budget",
            recommended_next_check="defer_public_claim",
            safe_metadata={"example_name": "public_claim_context_blocked_not_public_safe", "public_context": True},
        ),
        build_context_compression_packet_v1(
            context_packet_id="long_context_budget_exceeded_ask_clarification",
            query_summary="Too much context to fit.",
            context_units=[
                {"context_unit_id": f"chunk:10{i}", "context_unit_type": "chunk_summary_context", "summary": f"chunk {i}", "access_status": "access_allowed", "public_safe": True}
                for i in range(1, 7)
            ],
            compression_mode="defer_due_missing_context",
            reranking_mode="claim_relevance_first",
            selected_context_units=[
                {"context_unit_id": "chunk:101", "context_unit_type": "chunk_summary_context", "summary": "chunk 1"},
                {"context_unit_id": "chunk:102", "context_unit_type": "chunk_summary_context", "summary": "chunk 2"},
            ],
            dropped_context_units=[
                {"context_unit_id": "chunk:103", "context_unit_type": "chunk_summary_context", "summary": "chunk 3"},
            ],
            context_budget_status="over_budget",
            recommended_next_check="ask_clarifying_question",
            lost_in_middle_risk="high",
            safe_metadata={"example_name": "long_context_budget_exceeded_ask_clarification", "public_context": False},
        ),
    ]
    return examples


__all__ = [
    "HELPER_TYPE_V1",
    "PACKET_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "ValidationError",
    "ALLOWED_CONTEXT_UNIT_TYPES_V1",
    "ALLOWED_COMPRESSION_MODES_V1",
    "ALLOWED_RERANKING_MODES_V1",
    "ALLOWED_CONTEXT_BUDGET_STATUSES_V1",
    "build_context_compression_packet_v1",
    "select_context_units_v1",
    "compress_context_units_v1",
    "rank_context_units_v1",
    "validate_context_compression_packet_v1",
    "summarize_context_compression_packet_v1",
    "to_context_compression_json_safe_v1",
    "build_initial_context_compression_examples_v1",
]
