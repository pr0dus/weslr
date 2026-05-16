"""Safe meaning/obligation/state reuse helpers for native response inputs V1.

This module only builds compact, JSON-safe, in-memory payloads. It does not
wire runtime chat, call models, rank answers, execute solvers, or persist state.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping


FORBIDDEN_KEY_NAMES_V1 = {
    "raw_text",
    "normalized_text",
    "tokens",
    "hidden_prompt",
    "hidden_prompts",
    "answer_key",
    "answer_keys",
    "protected_material",
    "protected_test_item",
    "protected_test_items",
}

FORBIDDEN_TEXT_MARKERS_V1 = {
    "hidden_prompt": ["hidden prompt", "system prompt secret"],
    "answer_key": ["answer key", "protected answer key"],
    "protected_material": ["protected material", "protected test item", "protected benchmark item"],
    "official_claim": ["official iq", "certified iq", "official benchmark", "officially certified"],
    "fake_consciousness_claim": ["officially conscious", "i am sentient", "i have a soul", "soul proof"],
    "model_or_advisor_authorization": ["model_calls: true", "advisor_calls: true", "web_search: true", "search_calls: true"],
    "solver_or_arbitration": ["solver_execution: true", "answer-selection arbitration", "answer_selection_arbitration: true"],
    "persistence_or_state": ["write .weslr", "created .weslr", "persistence: true", "writes_performed: true"],
}


def to_meaning_response_reuse_json_safe_v1(obj: Any) -> Any:
    """Return a deep JSON-safe copy without writes or side effects."""
    value = copy.deepcopy(obj)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return to_meaning_response_reuse_json_safe_v1(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(k): to_meaning_response_reuse_json_safe_v1(v)
            for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple, set)):
        return [to_meaning_response_reuse_json_safe_v1(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_meaning_response_reuse_json_safe_v1(value.to_dict())
    if hasattr(value, "__dict__"):
        return to_meaning_response_reuse_json_safe_v1(vars(value))
    return repr(value)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_score_map(value: Any) -> Dict[str, float]:
    if not isinstance(value, Mapping):
        return {}
    return {str(k): _safe_float(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}


def _active_labels(score_map: Any) -> List[str]:
    if not isinstance(score_map, Mapping):
        return []
    labels = [str(k) for k, v in score_map.items() if _safe_float(v) > 0.0]
    return sorted(labels)


def _safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return to_meaning_response_reuse_json_safe_v1(value)
    if isinstance(value, tuple):
        return to_meaning_response_reuse_json_safe_v1(list(value))
    if isinstance(value, set):
        return to_meaning_response_reuse_json_safe_v1(sorted(value, key=repr))
    return [to_meaning_response_reuse_json_safe_v1(value)]


def _safe_structural_evidence(value: Any) -> List[Any]:
    """Keep structural evidence only; drop string-only private text fragments."""
    result: List[Any] = []
    for item in _safe_list(value):
        if isinstance(item, Mapping):
            compact = {
                str(k): v
                for k, v in item.items()
                if str(k) not in FORBIDDEN_KEY_NAMES_V1 and not isinstance(v, str)
            }
            if compact:
                result.append(to_meaning_response_reuse_json_safe_v1(compact))
        elif isinstance(item, (int, float, bool)):
            result.append(item)
    return result


def build_compact_meaning_payload_v1(meaning: Any) -> Dict[str, Any]:
    """Build a raw-text-free payload from a MeaningVector."""
    return {
        "payload_type": "compact_meaning_payload_v1",
        "primary_speech_act": getattr(meaning, "primary_speech_act", None),
        "primary_relational_frame": getattr(meaning, "primary_relational_frame", None),
        "primary_state_query": getattr(meaning, "primary_state_query", None),
        "required_state": _safe_list(getattr(meaning, "required_state", [])),
        "confidence": _safe_float(getattr(meaning, "confidence", 0.0)),
        "ambiguity": _safe_float(getattr(meaning, "ambiguity", 1.0), default=1.0),
        "speech_act_scores": _safe_score_map(getattr(meaning, "speech_act_scores", {})),
        "relational_scores": _safe_score_map(getattr(meaning, "relational_scores", {})),
        "state_query_scores": _safe_score_map(getattr(meaning, "state_query_scores", {})),
        "safety_scores": _safe_score_map(getattr(meaning, "safety_scores", {})),
        "affect_scores": _safe_score_map(getattr(meaning, "affect_scores", {})),
        "human_context_labels": _active_labels(getattr(meaning, "human_context_scores", {})),
        "creative_conversation_labels": _active_labels(getattr(meaning, "creative_conversation_scores", {})),
        "raw_text_included": False,
        "normalized_text_included": False,
    }


def build_compact_response_obligation_payload_v1(obligation: Any) -> Dict[str, Any]:
    """Build a compact native-frame-safe payload from a ResponseObligation."""
    return {
        "payload_type": "compact_response_obligation_payload_v1",
        "obligation_type": getattr(obligation, "obligation_type", None),
        "required_state": _safe_list(getattr(obligation, "required_state", [])),
        "disclosure_level": getattr(obligation, "disclosure_level", None),
        "identity_verification_required": bool(getattr(obligation, "identity_verification_required", False)),
        "memory_evidence_required": bool(getattr(obligation, "memory_evidence_required", False)),
        "should_answer_bounded": bool(getattr(obligation, "should_answer_bounded", False)),
        "should_ask_clarifying": bool(getattr(obligation, "should_ask_clarifying", False)),
        "confidence": _safe_float(getattr(obligation, "confidence", 0.0)),
        "reason": getattr(obligation, "reason", None),
        "evidence": _safe_structural_evidence(getattr(obligation, "evidence", [])),
    }


def build_compact_meaning_state_context_bundle_v1(state_context: Any) -> Dict[str, Any]:
    """Build a compact, non-writing context bundle from MeaningStateContext."""
    identity_evidence = _safe_list(getattr(state_context, "identity_evidence", []))
    return {
        "payload_type": "compact_meaning_state_context_bundle_v1",
        "known_user_status": getattr(state_context, "known_user_status", "unknown"),
        "sender_confidence": _safe_float(getattr(state_context, "sender_confidence", 0.0)),
        "identity_evidence_count": len(identity_evidence),
        "relationship_depth": _safe_float(getattr(state_context, "relationship_depth", 0.0)),
        "relationship_stage": getattr(state_context, "relationship_stage", None),
        "relationship_confidence": _safe_float(getattr(state_context, "relationship_confidence", 0.0)),
        "relationship_limitations": _safe_list(getattr(state_context, "relationship_limitations", [])),
        "memory_available": bool(getattr(state_context, "memory_available", False)),
        "memory_sources_checked": _safe_list(getattr(state_context, "memory_sources_checked", [])),
        "memory_scope_used": getattr(state_context, "memory_scope_used", None),
        "entity_memory_available": getattr(state_context, "entity_memory_available", None),
        "entity_relationships_used": _safe_list(getattr(state_context, "entity_relationships_used", [])),
        "memory_access_limitations": _safe_list(getattr(state_context, "memory_access_limitations", [])),
        "self_model_summary": getattr(state_context, "self_model_summary", None),
        "capability_summary": getattr(state_context, "capability_summary", None),
        "continuity_summary": getattr(state_context, "continuity_summary", None),
        "timeline_summary": getattr(state_context, "timeline_summary", None),
        "sources_used": _safe_list(getattr(state_context, "sources_used", [])),
        "sources_failed": to_meaning_response_reuse_json_safe_v1(getattr(state_context, "sources_failed", [])),
        "state_confidence": _safe_float(getattr(state_context, "state_confidence", 0.0)),
        "raw_text_included": False,
        "raw_private_text_stored": False,
        "writes_performed": False,
    }


def derive_known_and_missing_context_from_meaning_state_v1(
    compact_meaning: Mapping[str, Any],
    compact_obligation: Mapping[str, Any],
    compact_state: Mapping[str, Any],
) -> Dict[str, Any]:
    """Derive normalized non-private native-frame context hints."""
    known_context: List[Dict[str, Any]] = []
    missing_context: List[str] = []
    provenance_refs: List[str] = []

    required = set(_safe_list(compact_obligation.get("required_state"))) | set(_safe_list(compact_meaning.get("required_state")))
    known_user_status = compact_state.get("known_user_status") or "unknown"

    if compact_obligation.get("identity_verification_required") and known_user_status in {"unknown", "claimed", "onboarded_unverified"}:
        missing_context.append("verified identity context")
    elif known_user_status != "unknown":
        known_context.append({"kind": "identity_status", "status": known_user_status})

    if compact_obligation.get("memory_evidence_required") and not compact_state.get("memory_available"):
        missing_context.append("verified memory context")
    elif compact_state.get("memory_available"):
        known_context.append({"kind": "memory_status", "available": True, "scope": compact_state.get("memory_scope_used")})

    if "capability_model" in required and compact_state.get("capability_summary"):
        known_context.append({"kind": "capability_summary", "summary": compact_state.get("capability_summary")})
    elif "capability_model" in required:
        missing_context.append("capability model summary")

    if "self_model" in required and compact_state.get("self_model_summary"):
        known_context.append({"kind": "self_model_summary", "summary": compact_state.get("self_model_summary")})
    elif "self_model" in required:
        missing_context.append("self-model summary")

    for source in _safe_list(compact_state.get("sources_used")):
        if isinstance(source, str) and source:
            provenance_refs.append(source)

    return {
        "known_context": known_context,
        "missing_context": sorted(set(missing_context)),
        "memory_context_hints": {
            "memory_available": bool(compact_state.get("memory_available")),
            "memory_sources_checked": _safe_list(compact_state.get("memory_sources_checked")),
            "memory_access_limitations": _safe_list(compact_state.get("memory_access_limitations")),
        },
        "identity_status": {
            "known_user_status": known_user_status,
            "sender_confidence": _safe_float(compact_state.get("sender_confidence")),
            "identity_verification_required": bool(compact_obligation.get("identity_verification_required")),
        },
        "capability_boundary_hint": {
            "capability_summary_supplied": bool(compact_state.get("capability_summary")),
            "requires_tool": False,
            "requires_external_evidence": False,
            "requires_approval": False,
        },
        "provenance_refs": sorted(set(provenance_refs)),
        "raw_text_stored": False,
    }


def build_native_frame_inputs_from_meaning_reuse_v1(meaning: Any, obligation: Any, state_context: Any) -> Dict[str, Any]:
    """Build compact inputs for native frame construction without calling it."""
    compact_meaning = build_compact_meaning_payload_v1(meaning)
    compact_obligation = build_compact_response_obligation_payload_v1(obligation)
    compact_state = build_compact_meaning_state_context_bundle_v1(state_context)
    derived = derive_known_and_missing_context_from_meaning_state_v1(compact_meaning, compact_obligation, compact_state)

    return {
        "meaning_vector_result": compact_meaning,
        "response_obligation_result": compact_obligation,
        "selected_context_bundle": compact_state,
        "known_context": derived["known_context"],
        "missing_context": derived["missing_context"],
        "memory_context_hints": derived["memory_context_hints"],
        "self_model_or_identity_status": derived["identity_status"],
        "capability_boundary_result": derived["capability_boundary_hint"],
        "provenance_refs": derived["provenance_refs"],
        "raw_text_stored": False,
        "model_calls": False,
        "advisor_calls": False,
        "solver_execution": False,
        "safe_to_wire_runtime": False,
    }


def _walk(obj: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    yield path, obj
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            yield from _walk(value, child)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _walk(value, f"{path}[{index}]")


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def validate_meaning_response_reuse_payload_v1(payload: Any) -> Dict[str, Any]:
    """Validate a reuse payload and return structured results."""
    safe = to_meaning_response_reuse_json_safe_v1(payload)
    violations: List[Dict[str, str]] = []

    def add(category: str, path: str, message: str) -> None:
        violations.append({"category": category, "path": path or "$", "message": message})

    for path, value in _walk(safe):
        key = path.split(".")[-1].split("[")[0] if path else ""
        if key in FORBIDDEN_KEY_NAMES_V1:
            add("forbidden_key", path, f"{key} must not appear in reuse payloads")

        if key in {"model_calls", "advisor_calls", "search_calls", "web_search", "solver_execution", "answer_selection_arbitration", "safe_to_wire_runtime", "persistence", "writes_performed", "weslr_state_created"} and value is True:
            add("forbidden_authorization_or_side_effect", path, f"{key}=true is not allowed")

        if isinstance(value, str):
            for category, markers in FORBIDDEN_TEXT_MARKERS_V1.items():
                if _contains_any(value, markers):
                    add(category, path, "forbidden text marker present")

    return {
        "schema_version": "meaning_response_reuse_payload_validation_v1",
        "valid": not violations,
        "violations": violations,
    }


__all__ = [
    "build_compact_meaning_payload_v1",
    "build_compact_response_obligation_payload_v1",
    "build_compact_meaning_state_context_bundle_v1",
    "derive_known_and_missing_context_from_meaning_state_v1",
    "build_native_frame_inputs_from_meaning_reuse_v1",
    "validate_meaning_response_reuse_payload_v1",
    "to_meaning_response_reuse_json_safe_v1",
]
