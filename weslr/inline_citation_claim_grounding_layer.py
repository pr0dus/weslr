"""Metadata-only inline citation and claim grounding helpers v1.

This module evaluates claim grounding and citation readiness from explicit
metadata only. It is pure, deterministic, import-safe, and fail-closed.

It does not retrieve documents, call web/search or APIs, call models/providers,
assemble final answers, generate real citations, write memory, or touch `.weslr`.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

HELPER_TYPE_V1 = "inline_citation_claim_grounding_layer_v1"
PACKET_TYPE_V1 = "inline_citation_claim_grounding_packet_v1"
SUMMARY_TYPE_V1 = "inline_citation_claim_grounding_packet_summary_v1"

ALLOWED_GROUNDING_STATUSES_V1 = {
    "grounded",
    "partially_grounded",
    "unsupported",
    "contradicted",
    "stale_support",
    "access_restricted",
    "poison_quarantined",
    "citation_not_ready",
    "unknown_status",
}

ALLOWED_CITATION_READINESS_V1 = {
    "citation_ready",
    "citation_ready_with_caveat",
    "citation_blocked_access",
    "citation_blocked_poison",
    "citation_blocked_unsupported",
    "citation_blocked_contradicted",
    "citation_blocked_stale",
    "citation_not_required",
    "unknown_citation_status",
}

ALLOWED_RECOMMENDED_ACTIONS_V1 = {
    "answer_with_citations",
    "answer_with_caveats",
    "ask_for_source",
    "ask_clarifying_question",
    "remove_unsupported_claim",
    "disclose_contradiction",
    "downgrade_confidence",
    "refuse_public_claim",
    "block_answer",
    "unknown_action",
}

ALLOWED_BOOL_FIELDS_V1 = {
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



def _safe_flag(value: Any) -> bool:
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



def to_claim_grounding_json_safe_v1(value: Any) -> Any:
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
        for item in value.values():
            if _contains_forbidden_claim_marker(item):
                return True
        return False
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
        return [_safe_text(value)] if _safe_text(value) else []
    items = []
    for item in value:
        text = _safe_text(item)
        if text:
            items.append(text)
    return items



def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}



def _is_valid_bool_field(value: Any) -> bool:
    return _safe_flag(value) is False



def _dedupe_preserve(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result



def _derived_grounding_status(packet: Mapping[str, Any]) -> str:
    access_restricted = _safe_str_list(packet.get("access_restricted_claims"))
    if access_restricted:
        return "access_restricted"
    poison_quarantined = _safe_str_list(packet.get("poison_quarantined_claims"))
    if poison_quarantined:
        return "poison_quarantined"
    contradicted = _safe_str_list(packet.get("contradicted_claims"))
    if contradicted:
        return "contradicted"
    stale_supported = _safe_str_list(packet.get("stale_supported_claims"))
    if stale_supported:
        return "stale_support"
    grounded = _safe_str_list(packet.get("grounded_claims"))
    if grounded and _safe_str_list(packet.get("source_evidence_refs")):
        return "grounded"
    if grounded:
        return "partially_grounded"
    unsupported = _safe_str_list(packet.get("unsupported_claims"))
    if unsupported:
        return "unsupported"
    citation_ready = _safe_str_list(packet.get("citation_ready_claims"))
    if citation_ready:
        return "citation_not_ready"
    if _safe_str_list(packet.get("claim_nodes")):
        return "partially_grounded"
    return "unknown_status"



def _derived_citation_readiness(packet: Mapping[str, Any]) -> str:
    access_restricted = _safe_str_list(packet.get("access_restricted_claims"))
    if access_restricted:
        return "citation_blocked_access"
    poison_quarantined = _safe_str_list(packet.get("poison_quarantined_claims"))
    if poison_quarantined:
        return "citation_blocked_poison"
    contradicted = _safe_str_list(packet.get("contradicted_claims"))
    if contradicted:
        return "citation_blocked_contradicted"
    stale_supported = _safe_str_list(packet.get("stale_supported_claims"))
    if stale_supported:
        return "citation_ready_with_caveat"
    unsupported = _safe_str_list(packet.get("unsupported_claims"))
    if unsupported:
        return "citation_blocked_unsupported"
    citation_ready = _safe_str_list(packet.get("citation_ready_claims"))
    if citation_ready and _safe_str_list(packet.get("source_evidence_refs")) and _safe_str_list(packet.get("citation_refs")):
        return "citation_ready"
    if citation_ready:
        return "citation_ready_with_caveat"
    if _safe_text(packet.get("claim_grounding_status")) == "citation_not_ready":
        return "citation_not_required"
    return "unknown_citation_status"



def _derived_action(packet: Mapping[str, Any], grounding_status: str, citation_status: str) -> str:
    if citation_status == "citation_ready":
        return "answer_with_citations"
    if citation_status == "citation_ready_with_caveat":
        if grounding_status == "stale_support":
            return "downgrade_confidence"
        return "answer_with_caveats"
    if grounding_status == "contradicted" or citation_status == "citation_blocked_contradicted":
        return "disclose_contradiction"
    if grounding_status == "stale_support" or citation_status == "citation_blocked_stale":
        return "downgrade_confidence"
    if grounding_status == "access_restricted" or citation_status == "citation_blocked_access":
        return "block_answer"
    if grounding_status == "poison_quarantined" or citation_status == "citation_blocked_poison":
        return "block_answer"
    if grounding_status == "unsupported" or citation_status == "citation_blocked_unsupported":
        return "remove_unsupported_claim"
    if citation_status == "citation_not_required":
        return "answer_with_caveats"
    if not _safe_str_list(packet.get("source_evidence_refs")):
        return "ask_for_source"
    return "ask_clarifying_question"


# ---------------------------------------------------------------------------
# Packet builders
# ---------------------------------------------------------------------------


def build_claim_grounding_packet_v1(
    claim_grounding_packet_id: str,
    answer_candidate_id: str,
    claim_nodes: list[Any] | None = None,
    source_evidence_refs: list[Any] | None = None,
    citation_refs: list[Any] | None = None,
    grounded_claims: list[Any] | None = None,
    unsupported_claims: list[Any] | None = None,
    contradicted_claims: list[Any] | None = None,
    stale_supported_claims: list[Any] | None = None,
    access_restricted_claims: list[Any] | None = None,
    poison_quarantined_claims: list[Any] | None = None,
    citation_ready_claims: list[Any] | None = None,
    citation_blocked_claims: list[Any] | None = None,
    claim_grounding_status: str = "unknown_status",
    citation_readiness: str = "unknown_citation_status",
    public_claim_readiness: bool = False,
    recommended_answer_action: str = "unknown_action",
    recommended_next_check: str = "",
    runtime_authority: bool = False,
    writes_state: bool = False,
    model_provider_used: bool = False,
    public_claim_allowed: bool = False,
    proof_claim_allowed: bool = False,
    learning_claimed: bool = False,
    safe_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    packet: dict[str, Any] = {
        "helper_type": HELPER_TYPE_V1,
        "packet_type": PACKET_TYPE_V1,
        "claim_grounding_packet_id": _safe_text(claim_grounding_packet_id),
        "answer_candidate_id": _safe_text(answer_candidate_id),
        "claim_nodes": _json_safe(claim_nodes or []),
        "source_evidence_refs": _safe_str_list(source_evidence_refs),
        "citation_refs": _safe_str_list(citation_refs),
        "grounded_claims": _safe_str_list(grounded_claims),
        "unsupported_claims": _safe_str_list(unsupported_claims),
        "contradicted_claims": _safe_str_list(contradicted_claims),
        "stale_supported_claims": _safe_str_list(stale_supported_claims),
        "access_restricted_claims": _safe_str_list(access_restricted_claims),
        "poison_quarantined_claims": _safe_str_list(poison_quarantined_claims),
        "citation_ready_claims": _safe_str_list(citation_ready_claims),
        "citation_blocked_claims": _safe_str_list(citation_blocked_claims),
        "claim_grounding_status": _safe_text(claim_grounding_status),
        "citation_readiness": _safe_text(citation_readiness),
        "public_claim_readiness": _safe_flag(public_claim_readiness),
        "recommended_answer_action": _safe_text(recommended_answer_action),
        "recommended_next_check": _safe_text(recommended_next_check),
        "runtime_authority": _safe_flag(runtime_authority),
        "writes_state": _safe_flag(writes_state),
        "model_provider_used": _safe_flag(model_provider_used),
        "public_claim_allowed": _safe_flag(public_claim_allowed),
        "proof_claim_allowed": _safe_flag(proof_claim_allowed),
        "learning_claimed": _safe_flag(learning_claimed),
        "safe_metadata": _json_safe(DEFAULT_SAFE_METADATA_V1 if safe_metadata is None else safe_metadata),
    }

    if packet["claim_grounding_status"] == "unknown_status":
        packet["claim_grounding_status"] = _derived_grounding_status(packet)
    if packet["citation_readiness"] == "unknown_citation_status":
        packet["citation_readiness"] = _derived_citation_readiness(packet)
    if packet["recommended_answer_action"] == "unknown_action":
        packet["recommended_answer_action"] = _derived_action(packet, packet["claim_grounding_status"], packet["citation_readiness"])

    return packet


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------


def evaluate_claim_grounding_v1(packet: Any) -> str:
    normalized = to_claim_grounding_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        return "unknown_status"
    status = _safe_text(normalized.get("claim_grounding_status"))
    if status in ALLOWED_GROUNDING_STATUSES_V1 and status != "unknown_status":
        return status
    derived = _derived_grounding_status(normalized)
    return derived if derived in ALLOWED_GROUNDING_STATUSES_V1 else "unknown_status"



def evaluate_citation_readiness_v1(packet: Any) -> str:
    normalized = to_claim_grounding_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        return "unknown_citation_status"
    status = _safe_text(normalized.get("citation_readiness"))
    if status in ALLOWED_CITATION_READINESS_V1 and status != "unknown_citation_status":
        return status
    derived = _derived_citation_readiness(normalized)
    return derived if derived in ALLOWED_CITATION_READINESS_V1 else "unknown_citation_status"


# ---------------------------------------------------------------------------
# Validation and summary
# ---------------------------------------------------------------------------


def validate_claim_grounding_packet_v1(packet: Any) -> bool:
    normalized = to_claim_grounding_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        raise ValidationError("packet_must_be_mapping")

    forbidden_field = _contains_forbidden_field(normalized)
    if forbidden_field:
        raise ValidationError(f"forbidden_field_present:{forbidden_field}")
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_phrase_present")

    claim_grounding_status = _safe_text(normalized.get("claim_grounding_status"))
    citation_readiness = _safe_text(normalized.get("citation_readiness"))
    recommended_action = _safe_text(normalized.get("recommended_answer_action"))

    if claim_grounding_status not in ALLOWED_GROUNDING_STATUSES_V1:
        raise ValidationError("unknown_claim_grounding_status")
    if citation_readiness not in ALLOWED_CITATION_READINESS_V1:
        raise ValidationError("unknown_citation_readiness")
    if recommended_action not in ALLOWED_RECOMMENDED_ACTIONS_V1:
        raise ValidationError("unknown_recommended_answer_action")

    source_evidence_refs = _safe_str_list(normalized.get("source_evidence_refs"))
    citation_refs = _safe_str_list(normalized.get("citation_refs"))
    grounded_claims = _safe_str_list(normalized.get("grounded_claims"))
    unsupported_claims = _safe_str_list(normalized.get("unsupported_claims"))
    contradicted_claims = _safe_str_list(normalized.get("contradicted_claims"))
    stale_supported_claims = _safe_str_list(normalized.get("stale_supported_claims"))
    access_restricted_claims = _safe_str_list(normalized.get("access_restricted_claims"))
    poison_quarantined_claims = _safe_str_list(normalized.get("poison_quarantined_claims"))
    citation_ready_claims = _safe_str_list(normalized.get("citation_ready_claims"))
    citation_blocked_claims = _safe_str_list(normalized.get("citation_blocked_claims"))
    claim_nodes = _safe_str_list(normalized.get("claim_nodes"))

    runtime_authority = _safe_flag(normalized.get("runtime_authority"))
    writes_state = _safe_flag(normalized.get("writes_state"))
    model_provider_used = _safe_flag(normalized.get("model_provider_used"))
    public_claim_allowed = _safe_flag(normalized.get("public_claim_allowed"))
    proof_claim_allowed = _safe_flag(normalized.get("proof_claim_allowed"))
    learning_claimed = _safe_flag(normalized.get("learning_claimed"))
    public_claim_readiness = _safe_flag(normalized.get("public_claim_readiness"))

    if runtime_authority:
        raise ValidationError("runtime_authority_must_be_false")
    if writes_state:
        raise ValidationError("writes_state_must_be_false")
    if model_provider_used:
        raise ValidationError("model_provider_used_must_be_false")
    if public_claim_allowed:
        raise ValidationError("public_claim_allowed_must_be_false")
    if proof_claim_allowed:
        raise ValidationError("proof_claim_allowed_must_be_false")
    if learning_claimed:
        raise ValidationError("learning_claimed_must_be_false")
    if public_claim_readiness and not public_claim_allowed:
        raise ValidationError("public_claim_readiness_requires_public_claim_allowed")

    if citation_readiness == "citation_ready" and not source_evidence_refs:
        raise ValidationError("answer_with_citations_requires_source_evidence_refs")
    if recommended_action == "answer_with_citations" and not source_evidence_refs:
        raise ValidationError("answer_with_citations_requires_source_evidence_refs")

    if citation_readiness == "citation_ready" and unsupported_claims:
        raise ValidationError("citation_ready_cannot_have_unsupported_claims")
    if citation_readiness == "citation_ready_with_caveat" and unsupported_claims:
        raise ValidationError("citation_ready_cannot_have_unsupported_claims")
    if citation_readiness == "citation_ready" and access_restricted_claims:
        raise ValidationError("citation_ready_cannot_use_access_restricted_source")
    if citation_readiness == "citation_ready_with_caveat" and access_restricted_claims:
        raise ValidationError("citation_ready_cannot_use_access_restricted_source")
    if citation_readiness == "citation_ready" and poison_quarantined_claims:
        raise ValidationError("citation_ready_cannot_use_poison_quarantined_source")
    if citation_readiness == "citation_ready_with_caveat" and poison_quarantined_claims:
        raise ValidationError("citation_ready_cannot_use_poison_quarantined_source")

    if contradicted_claims and recommended_action != "disclose_contradiction":
        raise ValidationError("contradicted_claim_requires_disclosure")
    if stale_supported_claims and recommended_action not in {"answer_with_caveats", "downgrade_confidence"}:
        raise ValidationError("stale_support_requires_caveat_or_downgrade")
    if unsupported_claims and recommended_action not in {"remove_unsupported_claim", "ask_for_source", "ask_clarifying_question", "block_answer"}:
        raise ValidationError("unsupported_claim_requires_removal_or_uncertainty")
    if access_restricted_claims and recommended_action not in {"block_answer", "refuse_public_claim"}:
        raise ValidationError("access_restricted_claim_requires_blocking_action")
    if poison_quarantined_claims and recommended_action not in {"block_answer", "refuse_public_claim"}:
        raise ValidationError("poison_quarantined_claim_requires_blocking_action")

    if claim_grounding_status == "grounded" and not grounded_claims and not claim_nodes:
        raise ValidationError("grounded_status_requires_grounded_claims")
    if claim_grounding_status == "contradicted" and not contradicted_claims:
        raise ValidationError("contradicted_status_requires_contradicted_claims")
    if claim_grounding_status == "unsupported" and not unsupported_claims:
        raise ValidationError("unsupported_status_requires_unsupported_claims")
    if claim_grounding_status == "stale_support" and not stale_supported_claims:
        raise ValidationError("stale_status_requires_stale_supported_claims")

    if citation_readiness == "citation_not_required" and recommended_action == "answer_with_citations" and not source_evidence_refs:
        raise ValidationError("citation_not_required_answer_with_citations_requires_source_evidence_refs")

    if claim_grounding_status == "citation_not_ready" and citation_readiness == "citation_ready":
        raise ValidationError("citation_ready_requires_ready_grounding")

    # Claim markers and normalized list presence are retained for metadata-only checks.
    _ = citation_blocked_claims
    _ = claim_nodes

    return True



def summarize_claim_grounding_packet_v1(packet: Any) -> dict[str, Any]:
    validate_claim_grounding_packet_v1(packet)
    normalized = to_claim_grounding_json_safe_v1(packet)
    mapping = dict(normalized)
    grounded_claims = _safe_str_list(mapping.get("grounded_claims"))
    unsupported_claims = _safe_str_list(mapping.get("unsupported_claims"))
    contradicted_claims = _safe_str_list(mapping.get("contradicted_claims"))
    stale_supported_claims = _safe_str_list(mapping.get("stale_supported_claims"))
    access_restricted_claims = _safe_str_list(mapping.get("access_restricted_claims"))
    poison_quarantined_claims = _safe_str_list(mapping.get("poison_quarantined_claims"))
    citation_ready_claims = _safe_str_list(mapping.get("citation_ready_claims"))
    citation_blocked_claims = _safe_str_list(mapping.get("citation_blocked_claims"))
    return {
        "summary_type": SUMMARY_TYPE_V1,
        "claim_grounding_packet_id": _safe_text(mapping.get("claim_grounding_packet_id")),
        "answer_candidate_id": _safe_text(mapping.get("answer_candidate_id")),
        "claim_count": len(_safe_str_list(mapping.get("claim_nodes"))),
        "source_evidence_ref_count": len(_safe_str_list(mapping.get("source_evidence_refs"))),
        "citation_ref_count": len(_safe_str_list(mapping.get("citation_refs"))),
        "grounded_claim_count": len(grounded_claims),
        "unsupported_claim_count": len(unsupported_claims),
        "contradicted_claim_count": len(contradicted_claims),
        "stale_supported_claim_count": len(stale_supported_claims),
        "access_restricted_claim_count": len(access_restricted_claims),
        "poison_quarantined_claim_count": len(poison_quarantined_claims),
        "citation_ready_claim_count": len(citation_ready_claims),
        "citation_blocked_claim_count": len(citation_blocked_claims),
        "claim_grounding_status": _safe_text(mapping.get("claim_grounding_status")),
        "citation_readiness": _safe_text(mapping.get("citation_readiness")),
        "public_claim_readiness": _safe_flag(mapping.get("public_claim_readiness")),
        "recommended_answer_action": _safe_text(mapping.get("recommended_answer_action")),
        "recommended_next_check": _safe_text(mapping.get("recommended_next_check")),
        "safe_metadata": _json_safe(mapping.get("safe_metadata", DEFAULT_SAFE_METADATA_V1)),
    }


# ---------------------------------------------------------------------------
# Initial examples
# ---------------------------------------------------------------------------


def build_initial_claim_grounding_examples_v1() -> list[dict[str, Any]]:
    examples = [
        build_claim_grounding_packet_v1(
            claim_grounding_packet_id="simple_grounded_claim_citation_ready",
            answer_candidate_id="answer_1",
            claim_nodes=["claim:a"],
            source_evidence_refs=["source:1"],
            citation_refs=["cite:1"],
            grounded_claims=["claim:a"],
            citation_ready_claims=["claim:a"],
            claim_grounding_status="grounded",
            citation_readiness="citation_ready",
            public_claim_readiness=False,
            recommended_answer_action="answer_with_citations",
            recommended_next_check="none",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
            safe_metadata={"example_name": "simple_grounded_claim_citation_ready"},
        ),
        build_claim_grounding_packet_v1(
            claim_grounding_packet_id="stale_source_requires_caveat",
            answer_candidate_id="answer_2",
            claim_nodes=["claim:b"],
            source_evidence_refs=["source:2"],
            citation_refs=["cite:2"],
            grounded_claims=["claim:b"],
            stale_supported_claims=["claim:b"],
            citation_ready_claims=["claim:b"],
            claim_grounding_status="stale_support",
            citation_readiness="citation_ready_with_caveat",
            public_claim_readiness=False,
            recommended_answer_action="answer_with_caveats",
            recommended_next_check="recheck_source_freshness",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
            safe_metadata={"example_name": "stale_source_requires_caveat"},
        ),
        build_claim_grounding_packet_v1(
            claim_grounding_packet_id="contradicted_claim_requires_disclosure",
            answer_candidate_id="answer_3",
            claim_nodes=["claim:c"],
            source_evidence_refs=["source:3", "source:4"],
            citation_refs=["cite:3", "cite:4"],
            contradicted_claims=["claim:c"],
            citation_blocked_claims=["claim:c"],
            claim_grounding_status="contradicted",
            citation_readiness="citation_blocked_contradicted",
            public_claim_readiness=False,
            recommended_answer_action="disclose_contradiction",
            recommended_next_check="surface_conflict",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
            safe_metadata={"example_name": "contradicted_claim_requires_disclosure"},
        ),
        build_claim_grounding_packet_v1(
            claim_grounding_packet_id="unsupported_claim_removed",
            answer_candidate_id="answer_4",
            claim_nodes=["claim:d"],
            unsupported_claims=["claim:d"],
            citation_blocked_claims=["claim:d"],
            claim_grounding_status="unsupported",
            citation_readiness="citation_blocked_unsupported",
            public_claim_readiness=False,
            recommended_answer_action="remove_unsupported_claim",
            recommended_next_check="ask_for_source",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
            safe_metadata={"example_name": "unsupported_claim_removed"},
        ),
        build_claim_grounding_packet_v1(
            claim_grounding_packet_id="access_restricted_source_blocks_public_citation",
            answer_candidate_id="answer_5",
            claim_nodes=["claim:e"],
            access_restricted_claims=["claim:e"],
            citation_blocked_claims=["claim:e"],
            claim_grounding_status="access_restricted",
            citation_readiness="citation_blocked_access",
            public_claim_readiness=False,
            recommended_answer_action="block_answer",
            recommended_next_check="request_authorized_source",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
            safe_metadata={"example_name": "access_restricted_source_blocks_public_citation"},
        ),
        build_claim_grounding_packet_v1(
            claim_grounding_packet_id="poison_quarantined_source_blocks_citation",
            answer_candidate_id="answer_6",
            claim_nodes=["claim:f"],
            poison_quarantined_claims=["claim:f"],
            citation_blocked_claims=["claim:f"],
            claim_grounding_status="poison_quarantined",
            citation_readiness="citation_blocked_poison",
            public_claim_readiness=False,
            recommended_answer_action="block_answer",
            recommended_next_check="quarantine_source",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
            safe_metadata={"example_name": "poison_quarantined_source_blocks_citation"},
        ),
        build_claim_grounding_packet_v1(
            claim_grounding_packet_id="energy_recommendation_downgraded_due_stale_signal",
            answer_candidate_id="answer_7",
            claim_nodes=["claim:g"],
            source_evidence_refs=["signal:1"],
            citation_refs=["cite:7"],
            grounded_claims=["claim:g"],
            stale_supported_claims=["claim:g"],
            citation_ready_claims=["claim:g"],
            claim_grounding_status="stale_support",
            citation_readiness="citation_ready_with_caveat",
            public_claim_readiness=False,
            recommended_answer_action="downgrade_confidence",
            recommended_next_check="refresh_signal_metadata",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
            safe_metadata={"example_name": "energy_recommendation_downgraded_due_stale_signal"},
        ),
        build_claim_grounding_packet_v1(
            claim_grounding_packet_id="llm_candidate_rejected_no_source_edge",
            answer_candidate_id="answer_8",
            claim_nodes=["claim:h"],
            unsupported_claims=["claim:h"],
            claim_grounding_status="unsupported",
            citation_readiness="citation_blocked_unsupported",
            public_claim_readiness=False,
            recommended_answer_action="remove_unsupported_claim",
            recommended_next_check="ask_for_source",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
            safe_metadata={"example_name": "llm_candidate_rejected_no_source_edge"},
        ),
        build_claim_grounding_packet_v1(
            claim_grounding_packet_id="public_website_claim_blocked_not_public_safe",
            answer_candidate_id="answer_9",
            claim_nodes=["claim:i"],
            access_restricted_claims=["claim:i"],
            citation_blocked_claims=["claim:i"],
            claim_grounding_status="access_restricted",
            citation_readiness="citation_blocked_access",
            public_claim_readiness=False,
            recommended_answer_action="refuse_public_claim",
            recommended_next_check="request_public_safe_source",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
            safe_metadata={"example_name": "public_website_claim_blocked_not_public_safe"},
        ),
        build_claim_grounding_packet_v1(
            claim_grounding_packet_id="general_reasoning_answer_allowed_citation_not_required",
            answer_candidate_id="answer_10",
            claim_nodes=["claim:j"],
            grounded_claims=["claim:j"],
            claim_grounding_status="grounded",
            citation_readiness="citation_not_required",
            public_claim_readiness=False,
            recommended_answer_action="answer_with_caveats",
            recommended_next_check="none",
            public_claim_allowed=False,
            proof_claim_allowed=False,
            learning_claimed=False,
            safe_metadata={"example_name": "general_reasoning_answer_allowed_citation_not_required"},
        ),
    ]
    return examples


__all__ = [
    "HELPER_TYPE_V1",
    "PACKET_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "ValidationError",
    "ALLOWED_GROUNDING_STATUSES_V1",
    "ALLOWED_CITATION_READINESS_V1",
    "ALLOWED_RECOMMENDED_ACTIONS_V1",
    "build_claim_grounding_packet_v1",
    "evaluate_claim_grounding_v1",
    "evaluate_citation_readiness_v1",
    "validate_claim_grounding_packet_v1",
    "summarize_claim_grounding_packet_v1",
    "to_claim_grounding_json_safe_v1",
    "build_initial_claim_grounding_examples_v1",
]
