"""Safe meaning/obligation/state reuse helpers for native response inputs V1.

This module only builds compact, JSON-safe, in-memory payloads. It does not
wire runtime chat, call models, rank answers, execute solvers, or persist state.
``to_meaning_response_reuse_json_safe_v1`` is only a copier/coercer; it is not
a privacy sanitizer. Use the compact builders plus validator for safe reuse.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping


NATIVE_FRAME_KWARGS_V1 = {
    "meaning_vector_result",
    "response_obligation_result",
    "selected_context_bundle",
    "known_context",
    "missing_context",
    "memory_context_hints",
    "evidence_sufficiency_result",
    "capability_boundary_result",
    "uncertainty_result",
    "self_model_or_identity_status",
    "provenance_refs",
    "forbidden_claims",
}

REQUIRED_FALSE_HELPER_FLAGS_V1 = {
    "raw_text_stored",
    "model_calls",
    "advisor_calls",
    "solver_execution",
    "answer_selection_arbitration",
    "safe_to_wire_runtime",
    "live_runtime_output",
    "runtime_wiring",
}


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
    """Return a deep JSON-safe copy without writes or side effects.

    This is deliberately a copier/coercer, not a sanitizer: forbidden raw fields
    remain present so the validator can detect them. Do not pass raw/private
    objects through this helper and treat the result as privacy-safe.
    """
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




def _safe_source_label(value: Any) -> str | None:
    """Return a bounded non-authoritative source label, never a raw URL/text."""
    if value is None:
        return None
    if isinstance(value, Mapping):
        for key in ("source", "name", "label", "kind", "module", "path"):
            if value.get(key):
                return _safe_source_label(value.get(key))
        return "source_status_available"
    text = str(value).strip()
    if not text:
        return None
    lowered = text.lower()
    if "://" in lowered or lowered.startswith("www."):
        return "source_label_redacted"
    text = text.replace("\\", "/")
    if len(text) > 96:
        text = text[:93] + "..."
    return text


def _safe_source_labels(value: Any) -> List[str]:
    labels: List[str] = []
    for item in _safe_list(value):
        label = _safe_source_label(item)
        if label:
            labels.append(label)
    return sorted(set(labels))


def _safe_failed_source_labels(value: Any) -> List[str]:
    labels: List[str] = []
    for item in _safe_list(value):
        label = _safe_source_label(item)
        if label:
            labels.append(label)
    return sorted(set(labels))


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
    sources_used = _safe_source_labels(getattr(state_context, "sources_used", []))
    sources_failed = _safe_failed_source_labels(getattr(state_context, "sources_failed", []))
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
        "sources_used": sources_used,
        "sources_failed": sources_failed,
        "source_status": {
            "sources_used": sources_used,
            "sources_failed": sources_failed,
            "source_labels_only": True,
            "source_authority_elevated": False,
        },
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
    sources_used = _safe_source_labels(compact_state.get("sources_used"))
    sources_failed = _safe_failed_source_labels(compact_state.get("sources_failed"))

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

    relationship_stage = compact_state.get("relationship_stage")
    relationship_depth = _safe_float(compact_state.get("relationship_depth"))
    relationship_confidence = _safe_float(compact_state.get("relationship_confidence"))
    if relationship_stage or (relationship_depth > 0.0 and relationship_confidence > 0.0):
        known_context.append({
            "kind": "relationship_context_available",
            "stage": relationship_stage or "available",
            "depth_available": relationship_depth > 0.0,
            "confidence": relationship_confidence,
            "raw_relationship_text_included": False,
        })
    if _safe_list(compact_state.get("relationship_limitations")):
        missing_context.append("relationship_context_limitations")

    if compact_state.get("continuity_summary"):
        known_context.append({"kind": "continuity_summary_available", "summary_available": True})
    if compact_state.get("timeline_summary"):
        known_context.append({"kind": "timeline_summary_available", "summary_available": True})

    if compact_state.get("state_confidence") is not None:
        known_context.append({"kind": "state_confidence", "confidence": _safe_float(compact_state.get("state_confidence"))})

    if "capability_model" in required and compact_state.get("capability_summary"):
        known_context.append({"kind": "capability_summary", "summary": compact_state.get("capability_summary")})
    elif "capability_model" in required:
        missing_context.append("capability model summary")

    if "self_model" in required and compact_state.get("self_model_summary"):
        known_context.append({"kind": "self_model_summary", "summary": compact_state.get("self_model_summary")})
    elif "self_model" in required:
        missing_context.append("self-model summary")

    for source in sources_used:
        provenance_refs.append(source)
    for source in sources_failed:
        missing_context.append(f"state_source_unavailable:{source}")

    source_status = {
        "sources_used": sources_used,
        "sources_failed": sources_failed,
        "source_labels_only": True,
        "source_authority_elevated": False,
        "raw_source_text_included": False,
        "raw_urls_included": False,
    }
    if sources_used or sources_failed:
        known_context.append({"kind": "source_status", **source_status})

    evidence_sufficiency_hint = {
        "hint_only": True,
        "source_status_available": bool(sources_used or sources_failed),
        "sources_failed": sources_failed,
        "source_authority_elevated": False,
        "external_evidence_checked": False,
    }

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
            "hint_only": True,
            "capability_summary_supplied": bool(compact_state.get("capability_summary")),
            "requires_tool": False,
            "requires_external_action": False,
            "requires_external_evidence": False,
            "requires_approval": False,
            "authorization_granted": False,
        },
        "evidence_sufficiency_hint": evidence_sufficiency_hint,
        "uncertainty_hint": {
            "hint_only": True,
            "sources_failed": sources_failed,
            "state_confidence": _safe_float(compact_state.get("state_confidence")),
        },
        "source_status": source_status,
        "provenance_refs": sorted(set(provenance_refs)),
        "raw_text_stored": False,
    }


def build_native_frame_inputs_from_meaning_reuse_v1(meaning: Any, obligation: Any, state_context: Any) -> Dict[str, Any]:
    """Build separated compact native-frame kwargs and helper metadata.

    The returned ``native_frame_kwargs`` dict is directly splattable into
    ``build_native_reasoning_frame_v1``. Safety/side-effect flags live only in
    ``helper_metadata`` and must not be passed to native frame constructors.
    """
    compact_meaning = build_compact_meaning_payload_v1(meaning)
    compact_obligation = build_compact_response_obligation_payload_v1(obligation)
    compact_state = build_compact_meaning_state_context_bundle_v1(state_context)
    derived = derive_known_and_missing_context_from_meaning_state_v1(compact_meaning, compact_obligation, compact_state)

    native_frame_kwargs = {
        "meaning_vector_result": compact_meaning,
        "response_obligation_result": compact_obligation,
        "selected_context_bundle": compact_state,
        "known_context": derived["known_context"],
        "missing_context": derived["missing_context"],
        "memory_context_hints": derived["memory_context_hints"],
        "evidence_sufficiency_result": derived["evidence_sufficiency_hint"],
        "self_model_or_identity_status": derived["identity_status"],
        "capability_boundary_result": derived["capability_boundary_hint"],
        "uncertainty_result": derived["uncertainty_hint"],
        "provenance_refs": derived["provenance_refs"],
        "forbidden_claims": [],
    }
    helper_metadata = {
        "raw_text_stored": False,
        "model_calls": False,
        "advisor_calls": False,
        "solver_execution": False,
        "answer_selection_arbitration": False,
        "safe_to_wire_runtime": False,
        "live_runtime_output": False,
        "runtime_wiring": False,
    }
    return {
        "payload_type": "meaning_response_reuse_native_inputs_v1",
        "native_frame_kwargs": native_frame_kwargs,
        "helper_metadata": helper_metadata,
    }


def extract_native_frame_kwargs_from_meaning_reuse_v1(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Extract only fields accepted by build_native_reasoning_frame_v1."""
    if isinstance(payload, Mapping) and isinstance(payload.get("native_frame_kwargs"), Mapping):
        source = payload["native_frame_kwargs"]
    else:
        source = payload
    return {str(k): to_meaning_response_reuse_json_safe_v1(v) for k, v in source.items() if str(k) in NATIVE_FRAME_KWARGS_V1}


def extract_helper_metadata_from_meaning_reuse_v1(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Extract helper metadata, defaulting all helper-only side-effect flags false."""
    source = payload.get("helper_metadata", {}) if isinstance(payload, Mapping) else {}
    metadata = {key: False for key in sorted(REQUIRED_FALSE_HELPER_FLAGS_V1)}
    if isinstance(source, Mapping):
        for key, value in source.items():
            metadata[str(key)] = to_meaning_response_reuse_json_safe_v1(value)
    return metadata


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
    """Validate a reuse payload and return structured safety errors plus usefulness warnings."""
    safe = to_meaning_response_reuse_json_safe_v1(payload)
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    def add_error(category: str, path: str, message: str) -> None:
        errors.append({"category": category, "path": path or "$", "message": message})

    def add_warning(category: str, path: str, message: str) -> None:
        warnings.append({"category": category, "path": path or "$", "message": message})

    for path, value in _walk(safe):
        key = path.split(".")[-1].split("[")[0] if path else ""
        if key in FORBIDDEN_KEY_NAMES_V1:
            add_error("forbidden_key", path, f"{key} must not appear in reuse payloads")

        if key in {"model_calls", "advisor_calls", "search_calls", "web_search", "solver_execution", "answer_selection_arbitration", "safe_to_wire_runtime", "live_runtime_output", "runtime_wiring", "authorization_granted", "persistence", "writes_performed", "weslr_state_created"} and value is True:
            add_error("forbidden_authorization_or_side_effect", path, f"{key}=true is not allowed")

        if isinstance(value, str):
            for category, markers in FORBIDDEN_TEXT_MARKERS_V1.items():
                if _contains_any(value, markers):
                    add_error(category, path, "forbidden text marker present")
            lowered = value.lower()
            if "://" in lowered or lowered.startswith("www."):
                add_error("raw_source_url", path, "raw source URLs must not appear in reuse payloads")

    if isinstance(safe, Mapping):
        if safe.get("payload_type") == "meaning_response_reuse_native_inputs_v1":
            native_kwargs = safe.get("native_frame_kwargs")
            helper_metadata = safe.get("helper_metadata")
            if not isinstance(native_kwargs, Mapping):
                add_warning("native_frame_kwargs_missing", "native_frame_kwargs", "native_frame_kwargs/helper_metadata separation is missing")
                native_kwargs = {}
            if not isinstance(helper_metadata, Mapping):
                add_warning("helper_metadata_missing", "helper_metadata", "helper metadata is missing")
                helper_metadata = {}
            if not native_kwargs:
                add_warning("empty_native_frame_kwargs", "native_frame_kwargs", "native frame kwargs are empty")
            leaked = sorted(set(native_kwargs) & REQUIRED_FALSE_HELPER_FLAGS_V1)
            if leaked:
                add_warning("helper_metadata_not_separated", "native_frame_kwargs", f"helper metadata keys are present in native kwargs: {', '.join(leaked)}")
            for flag in sorted(REQUIRED_FALSE_HELPER_FLAGS_V1):
                if helper_metadata.get(flag) is not False:
                    add_warning("helper_metadata_false_flag_missing", f"helper_metadata.{flag}", f"{flag} should be present and false")
            cap_hint = native_kwargs.get("capability_boundary_result") if isinstance(native_kwargs, Mapping) else None
            if not isinstance(cap_hint, Mapping) or cap_hint.get("hint_only") is not True:
                add_warning("capability_hint_missing_hint_only", "native_frame_kwargs.capability_boundary_result", "capability hint must declare hint_only=true")
            known = native_kwargs.get("known_context", []) if isinstance(native_kwargs, Mapping) else []
            missing = native_kwargs.get("missing_context", []) if isinstance(native_kwargs, Mapping) else []
            if not known and not missing:
                add_warning("no_known_or_missing_context", "native_frame_kwargs", "payload has no known_context or missing_context")
            selected = native_kwargs.get("selected_context_bundle", {}) if isinstance(native_kwargs, Mapping) else {}
            rendered_signals = repr([known, missing, native_kwargs.get("memory_context_hints"), native_kwargs.get("capability_boundary_result"), native_kwargs.get("evidence_sufficiency_result"), native_kwargs.get("self_model_or_identity_status")])
            if not any(marker in rendered_signals for marker in ("identity", "memory", "capability", "source_status", "relationship", "continuity", "timeline", "provenance")):
                add_warning("missing_cognition_signals", "native_frame_kwargs", "no identity/memory/capability/evidence/relationship/continuity signals detected")
            if isinstance(selected, Mapping):
                if (selected.get("sources_used") or selected.get("sources_failed")) and not selected.get("source_status"):
                    add_warning("missing_source_status", "native_frame_kwargs.selected_context_bundle.source_status", "source_status missing while source labels are present")
                if (selected.get("relationship_stage") or selected.get("relationship_depth") or selected.get("relationship_limitations")) and "relationship" not in rendered_signals:
                    add_warning("missing_relationship_propagation", "native_frame_kwargs.known_context", "relationship fields are not propagated")
                if (selected.get("continuity_summary") or selected.get("timeline_summary")) and not any(x in rendered_signals for x in ("continuity", "timeline")):
                    add_warning("missing_continuity_propagation", "native_frame_kwargs.known_context", "continuity/timeline fields are not propagated")
        elif "native_frame_kwargs" not in safe and "helper_metadata" not in safe and any(key in safe for key in ("meaning_vector_result", "response_obligation_result", "selected_context_bundle")):
            add_warning("native_frame_kwargs_helper_metadata_not_separated", "$", "native frame kwargs and helper metadata should be separated")

    return {
        "schema_version": "meaning_response_reuse_payload_validation_v1",
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "violations": errors,
    }


__all__ = [
    "build_compact_meaning_payload_v1",
    "build_compact_response_obligation_payload_v1",
    "build_compact_meaning_state_context_bundle_v1",
    "derive_known_and_missing_context_from_meaning_state_v1",
    "build_native_frame_inputs_from_meaning_reuse_v1",
    "extract_native_frame_kwargs_from_meaning_reuse_v1",
    "extract_helper_metadata_from_meaning_reuse_v1",
    "validate_meaning_response_reuse_payload_v1",
    "to_meaning_response_reuse_json_safe_v1",
]
