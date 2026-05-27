"""WESLR UNKNOWN ENGINE conversation friction assimilation helpers V1.

Metadata-only, helper-only, deterministic in-memory helpers for turning safe
synthetic conversation-observation metadata into friction items, cognition-gap
hypotheses, failed-path references, improvement targets, and a safe assimilation
artifact. This module does not execute runtime behavior, does not wire into chat,
does not call providers/models/search/advisors, does not read private data,
does not touch `.weslr`, and does not grant any authority.
"""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "WeslrUnknownEngineConversationFrictionAssimilationV1"
ARTIFACT_TYPE_V1 = "WeslrUnknownEngineConversationFrictionAssimilationV1"
ITEM_SCHEMA_VERSION_V1 = "WeslrUnknownEngineConversationFrictionItemV1"
GAP_HYPOTHESIS_SCHEMA_VERSION_V1 = "WeslrUnknownEngineCognitionGapHypothesisV1"
FAILED_PATH_REFERENCE_SCHEMA_VERSION_V1 = "WeslrUnknownEngineFailedPathReferenceV1"
IMPROVEMENT_TARGET_SCHEMA_VERSION_V1 = "WeslrUnknownEngineImprovementTargetV1"
RECOMMENDED_NEXT_LANE_V1 = "REVIEW_UNKNOWN_ENGINE_CONVERSATION_FRICTION_ARTIFACT_HELPERS_V1"
DEFAULT_SOURCE_OBSERVATION_PATH_V1 = "docs/WESLR_CONTROLLED_LOCAL_REAL_CONVERSATION_OBSERVATION_V1.md"
DEFAULT_OBSERVATION_COMMIT_V1 = "unknown"
DEFAULT_TRANSCRIPT_SCOPE_V1 = "synthetic"
DEFAULT_SAFE_REFERENCE_ID_V1 = "synthetic_observation_reference_v1"
DEFAULT_SOURCE_TURN_ID_V1 = "synthetic_turn_v1"
DEFAULT_FAILURE_LABEL_V1 = "cannedness"
DEFAULT_GAP_LABEL_V1 = "missing_non_cannedness_pressure"
DEFAULT_TARGET_ID_V1 = "synthetic_improvement_target_v1"
DEFAULT_FAILURE_PATH_ID_V1 = "synthetic_failed_path_reference_v1"
DEFAULT_GAP_HYPOTHESIS_ID_V1 = "synthetic_gap_hypothesis_v1"

ALLOWED_UNKNOWN_ENGINE_CONVERSATION_FRICTION_LABELS_V1: tuple[str, ...] = (
    "cannedness",
    "missed_local_context",
    "shallow_continuity",
    "over_safety",
    "under_answering",
    "vague_language",
    "weak_tradeoff_reasoning",
    "weak_human_concern_tracking",
    "weak_followup_memory",
    "boundary_overgeneralization",
    "fallback_to_checklist",
    "insufficient_self_correction",
    "unsafe_authority_claim",
    "public_readiness_overclaim",
    "provider_model_fallback_risk",
)

ALLOWED_UNKNOWN_ENGINE_CONVERSATION_GAP_LABELS_V1: tuple[str, ...] = (
    "missing_conversation_state_frame",
    "missing_current_user_concern_slot",
    "missing_recent_turn_recall_object",
    "missing_goal_subgoal_cache_use",
    "missing_answer_shape_planner",
    "missing_non_cannedness_pressure",
    "missing_tradeoff_reasoning_frame",
    "missing_empathy_concern_integration",
    "missing_boundary_specific_authority_calibration",
    "missing_response_self_check_before_final_answer",
    "missing_failed_path_registry_connection",
    "missing_concrete_next_step_selection",
    "missing_directness_pressure",
    "missing_response_shape_diversity",
    "missing_boundary_specific_fallback_gating",
    "missing_validation_gate",
)

FRICTION_TO_GAP_LABELS_V1: dict[str, tuple[str, ...]] = {
    "cannedness": ("missing_non_cannedness_pressure", "missing_answer_shape_planner"),
    "missed_local_context": ("missing_conversation_state_frame", "missing_current_user_concern_slot"),
    "shallow_continuity": ("missing_recent_turn_recall_object", "missing_goal_subgoal_cache_use"),
    "over_safety": ("missing_boundary_specific_authority_calibration", "missing_answer_shape_planner"),
    "under_answering": ("missing_answer_shape_planner", "missing_concrete_next_step_selection"),
    "vague_language": ("missing_response_self_check_before_final_answer", "missing_directness_pressure"),
    "weak_tradeoff_reasoning": ("missing_tradeoff_reasoning_frame",),
    "weak_human_concern_tracking": ("missing_empathy_concern_integration",),
    "weak_followup_memory": ("missing_recent_turn_recall_object", "missing_current_user_concern_slot"),
    "boundary_overgeneralization": ("missing_boundary_specific_authority_calibration",),
    "fallback_to_checklist": ("missing_non_cannedness_pressure", "missing_response_shape_diversity"),
    "insufficient_self_correction": ("missing_response_self_check_before_final_answer",),
    "unsafe_authority_claim": ("missing_boundary_specific_authority_calibration",),
    "public_readiness_overclaim": ("missing_failed_path_registry_connection", "missing_validation_gate"),
    "provider_model_fallback_risk": ("missing_boundary_specific_fallback_gating", "missing_boundary_specific_authority_calibration"),
}

BLOCKED_AUTHORITY_FIELDS_V1: tuple[str, ...] = (
    "permits_runtime_changes",
    "permits_chat_wiring",
    "permits_final_answer_generation",
    "permits_provider_calls",
    "permits_model_calls",
    "permits_search_calls",
    "permits_advisor_calls",
    "permits_raw_private_data",
    "permits_dot_weslr_io",
    "permits_memory_claims",
    "permits_public_launch",
    "permits_product_readiness_claims",
    "permits_intelligence_claims",
    "permits_turing_claims",
    "permits_certification_claims",
    "permits_official_scoring",
    "permits_auto_implementation",
)

_FORBIDDEN_KEY_FRAGMENTS_V1 = (
    "raw_prompt",
    "raw_response",
    "private",
    "provider",
    "model",
    "search",
    "advisor",
    "runtime",
    "chat",
    "final_answer",
    "answer_draft",
    "reply_output",
    "preview_output",
    "user_facing",
    "official_score",
    "benchmark",
    "intelligence",
    "turing",
    "certification",
    "product_readiness",
    "dot_weslr",
    ".weslr",
    "continuity",
    "review_queue",
    "pilot_signals",
    "suggestion_box",
    "hidden_prompt",
    "protected_item",
    "protected_material",
)

_ALLOWED_METADATA_KEYS_V1 = {
    "schema_version",
    "artifact_type",
    "item_type",
    "source_observation_path",
    "observation_commit",
    "transcript_scope",
    "synthetic_only",
    "raw_private_data_included",
    "provider_model_calls_allowed",
    "runtime_wiring_allowed",
    "official_score_allowed",
    "friction_items",
    "cognition_gap_hypotheses",
    "failed_path_references",
    "improvement_targets",
    "blocked_authority",
    "recommended_next_lane",
    "validation_status",
    "blocked_reason_labels",
    "blocked",
    "source_turn_id",
    "failure_label",
    "mapped_gap_labels",
    "safe_reference_id",
    "observation_note",
    "friction_label",
    "gap_labels",
    "gap_label",
    "target_id",
    "recommended_helper_name",
    "recommended_lane",
    "bounded",
}

_TEXT_MARKERS_V1 = {
    "raw_private_data_included": (
        "raw prompt:",
        "raw_prompt:",
        "raw response:",
        "raw_response:",
        "private content:",
        "confidential:",
        "secret:",
        "api key",
        "password:",
    ),
    "hidden_prompt_or_protected_item_included": (
        "hidden prompt",
        "protected item",
        "protected material",
        "system prompt:",
        "developer prompt:",
    ),
    "provider_model_search_advisor_call_implied": (
        "provider output:",
        "provider response:",
        "model output:",
        "llm output:",
        "search output:",
        "search result:",
        "advisor output:",
        "advisor response:",
    ),
    "runtime_chat_wiring_implied": (
        "chat responder",
        "respond_chat",
        "generate_chat",
        "runtime output:",
        "live dialogue",
        "live runtime",
    ),
    "final_answer_generation_implied": (
        "final answer:",
        "final_answer:",
        "answer draft:",
        "answer_draft:",
        "reply output:",
        "preview output:",
        "user-facing output:",
    ),
    "public_readiness_implied": (
        "public readiness",
        "public-ready",
        "ready for public launch",
        "launch now",
        "shipping-ready",
    ),
    "official_claim_implied": (
        "official score",
        "benchmark",
        "turing test",
        "certification",
        "intelligence claim",
        "product ready",
    ),
    "continuity_raw_data_implied": (
        "continuity/",
        "pilot_signals",
        "suggestion_box",
        "review_queue.json",
        "raw transcript",
        "raw conversation",
        "private record",
        "private records",
        "user data",
        "memory/",
    ),
    "dot_weslr_io_implied": (
        ".weslr",
        "dot weslr",
    ),
    "memory_claim_implied": (
        "i remember",
        "memory claim",
        "raw memory",
    ),
}


def _merge_metadata(metadata: Mapping[str, Any] | None, overrides: Mapping[str, Any]) -> dict[str, Any]:
    if metadata is None:
        merged: dict[str, Any] = {}
    elif isinstance(metadata, Mapping):
        merged = dict(metadata)
    else:
        return {"__invalid_metadata__": metadata, "__metadata_not_mapping__": True}
    merged.update(dict(overrides))
    return merged


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return list(deepcopy(value))
    if isinstance(value, set):
        return sorted(deepcopy(value), key=repr)
    return [deepcopy(value)]


def _append_unique(target: list[str], label: str) -> None:
    if label not in target:
        target.append(label)


def _safe_label(value: Any) -> str:
    return str(value).replace("`", "").replace("\n", " ").strip()[:240]


def _safe_labels(value: Any) -> list[str]:
    labels: list[str] = []
    for item in _as_list(value):
        _append_unique(labels, _safe_label(item))
    return labels


def _is_json_safe(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, bool)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_safe(item) for key, item in value.items())
    if isinstance(value, list):
        return all(_is_json_safe(item) for item in value)
    return False


def _json_safe(value: Any) -> Any:
    value = deepcopy(value)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else "non_json_safe_float_replaced"
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return "non_json_safe_value_replaced"


def _walk(value: Any, path: str = ""):
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_s = str(key)
            child = f"{path}.{key_s}" if path else key_s
            yield child, item
            yield from _walk(item, child)
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            child = f"{path}[{index}]"
            yield child, item
            yield from _walk(item, child)


def _blocked_authority_v1() -> dict[str, bool]:
    return {field: False for field in BLOCKED_AUTHORITY_FIELDS_V1}


def required_unknown_engine_blocked_authority_v1() -> dict[str, bool]:
    return _blocked_authority_v1()


def _safe_blocked_authority(value: Any) -> tuple[dict[str, bool], list[str]]:
    reasons: list[str] = []
    if not isinstance(value, Mapping):
        return _blocked_authority_v1(), ["blocked_authority_not_mapping"]
    result = _blocked_authority_v1()
    for field in BLOCKED_AUTHORITY_FIELDS_V1:
        if field not in value:
            _append_unique(reasons, f"missing_blocked_authority_field:{field}")
            continue
        if value.get(field) is not False:
            _append_unique(reasons, f"blocked_authority_field_not_false:{field}")
        result[field] = False
    return result, reasons


def _detect_unsafe_metadata(value: Any) -> list[str]:
    reasons: list[str] = []
    if not _is_json_safe(value):
        _append_unique(reasons, "non_json_safe_metadata")
        return reasons
    for path, item in _walk(value):
        normalized_parts = [part for part in path.replace("[", ".").replace("]", "").split(".") if part]
        if "blocked_authority" in normalized_parts:
            continue
        key = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
        if isinstance(item, str):
            lowered = item.lower()
            for label, markers in _TEXT_MARKERS_V1.items():
                if any(marker in lowered for marker in markers):
                    _append_unique(reasons, label)
        if key not in _ALLOWED_METADATA_KEYS_V1:
            for fragment in _FORBIDDEN_KEY_FRAGMENTS_V1:
                if fragment in key:
                    _append_unique(reasons, f"forbidden_key_fragment:{fragment}")
    return reasons


def _validate_label(label: Any, allowed: tuple[str, ...], *, kind: str) -> tuple[str | None, list[str]]:
    reasons: list[str] = []
    safe = _safe_label(label)
    if not safe:
        _append_unique(reasons, f"{kind}_label_empty")
        return None, reasons
    if safe not in allowed:
        _append_unique(reasons, f"unsupported_{kind}_label:{safe}")
        return None, reasons
    return safe, reasons


def _filter_allowed_labels(value: Any, allowed: tuple[str, ...], *, kind: str) -> tuple[list[str], list[str]]:
    labels: list[str] = []
    reasons: list[str] = []
    for raw in _as_list(value):
        safe, label_reasons = _validate_label(raw, allowed, kind=kind)
        for reason in label_reasons:
            _append_unique(reasons, reason)
        if safe is not None:
            _append_unique(labels, safe)
    return labels, reasons


def allowed_unknown_engine_conversation_friction_labels_v1() -> tuple[str, ...]:
    return ALLOWED_UNKNOWN_ENGINE_CONVERSATION_FRICTION_LABELS_V1


def allowed_unknown_engine_conversation_gap_labels_v1() -> tuple[str, ...]:
    return ALLOWED_UNKNOWN_ENGINE_CONVERSATION_GAP_LABELS_V1


def map_unknown_engine_friction_to_cognition_gaps_v1(
    friction_labels: Any = None,
    **overrides: Any,
) -> dict[str, Any]:
    source = _merge_metadata({"friction_labels": friction_labels} if friction_labels is not None else None, overrides)
    source_labels, label_reasons = _filter_allowed_labels(source.get("friction_labels"), ALLOWED_UNKNOWN_ENGINE_CONVERSATION_FRICTION_LABELS_V1, kind="friction")
    friction_to_gap_map: dict[str, list[str]] = {}
    gap_labels: list[str] = []
    for friction_label in source_labels:
        mapped = list(FRICTION_TO_GAP_LABELS_V1[friction_label])
        friction_to_gap_map[friction_label] = mapped
        for gap_label in mapped:
            _append_unique(gap_labels, gap_label)
    blocked = bool(label_reasons)
    validation_status = "blocked_invalid_or_unsafe_metadata_labels_only" if blocked else "validation_pass_metadata_only"
    return _json_safe(
        {
            "schema_version": SCHEMA_VERSION_V1,
            "artifact_type": "UnknownEngineFrictionToGapMappingV1",
            "friction_labels": source_labels,
            "friction_to_gap_map": friction_to_gap_map,
            "gap_labels": gap_labels,
            "blocked": blocked,
            "blocked_reason_labels": label_reasons,
            "validation_status": validation_status,
        }
    )


def build_unknown_engine_conversation_friction_item_v1(
    metadata: Mapping[str, Any] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    blocked_authority, authority_reasons = _safe_blocked_authority(source.get("blocked_authority", _blocked_authority_v1()))
    failure_label, failure_reasons = _validate_label(source.get("failure_label", DEFAULT_FAILURE_LABEL_V1), ALLOWED_UNKNOWN_ENGINE_CONVERSATION_FRICTION_LABELS_V1, kind="friction")
    source_turn_id = _safe_label(source.get("source_turn_id", DEFAULT_SOURCE_TURN_ID_V1))
    safe_reference_id = _safe_label(source.get("safe_reference_id", DEFAULT_SAFE_REFERENCE_ID_V1))
    transcript_scope = _safe_label(source.get("transcript_scope", DEFAULT_TRANSCRIPT_SCOPE_V1))
    synthetic_only = bool(source.get("synthetic_only", True))
    observation_commit = _safe_label(source.get("observation_commit", DEFAULT_OBSERVATION_COMMIT_V1))
    observation_note = _safe_label(source.get("observation_note", "synthetic friction item metadata only"))
    mapped = map_unknown_engine_friction_to_cognition_gaps_v1([failure_label] if failure_label else [])
    item = {
        "schema_version": ITEM_SCHEMA_VERSION_V1,
        "item_type": "WeslrUnknownEngineConversationFrictionItemV1",
        "source_turn_id": source_turn_id,
        "failure_label": failure_label,
        "mapped_gap_labels": mapped.get("gap_labels", []),
        "safe_reference_id": safe_reference_id,
        "transcript_scope": transcript_scope,
        "synthetic_only": synthetic_only,
        "observation_commit": observation_commit,
        "observation_note": observation_note,
        "blocked_authority": blocked_authority,
        "validation_status": "validation_pass_metadata_only",
        "blocked": False,
        "blocked_reason_labels": [],
    }
    item_reasons = authority_reasons + failure_reasons + _detect_unsafe_metadata(item)
    if not synthetic_only:
        _append_unique(item_reasons, "synthetic_only_false")
    if item_reasons:
        item["blocked"] = True
        item["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
        item["blocked_reason_labels"] = _safe_labels(item_reasons)
    return _json_safe(item)


def validate_unknown_engine_conversation_friction_item_v1(item: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_labels_only",
            "missing_required_fields": [
                "schema_version",
                "item_type",
                "source_turn_id",
                "failure_label",
                "mapped_gap_labels",
                "safe_reference_id",
                "transcript_scope",
                "synthetic_only",
                "observation_commit",
                "observation_note",
                "blocked_authority",
                "validation_status",
                "blocked",
                "blocked_reason_labels",
            ],
            "invalid_fields": ["item"],
            "blocked_reason_labels": ["item_not_mapping"],
            "json_safe": False,
        }
    missing = [
        field
        for field in (
            "schema_version",
            "item_type",
            "source_turn_id",
            "failure_label",
            "mapped_gap_labels",
            "safe_reference_id",
            "transcript_scope",
            "synthetic_only",
            "observation_commit",
            "observation_note",
            "blocked_authority",
            "validation_status",
            "blocked",
            "blocked_reason_labels",
        )
        if field not in item
    ]
    invalid_fields: list[str] = []
    blocked_reasons: list[str] = []
    if item.get("schema_version") != ITEM_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reasons, "schema_version_mismatch")
    if item.get("item_type") != "WeslrUnknownEngineConversationFrictionItemV1":
        _append_unique(invalid_fields, "item_type")
        _append_unique(blocked_reasons, "item_type_mismatch")
    failure_label, label_reasons = _validate_label(item.get("failure_label"), ALLOWED_UNKNOWN_ENGINE_CONVERSATION_FRICTION_LABELS_V1, kind="friction")
    for reason in label_reasons:
        _append_unique(blocked_reasons, reason)
    if failure_label is None:
        _append_unique(invalid_fields, "failure_label")
    mapped_gaps = _safe_labels(item.get("mapped_gap_labels"))
    if not mapped_gaps:
        _append_unique(invalid_fields, "mapped_gap_labels")
        _append_unique(blocked_reasons, "mapped_gap_labels_empty")
    elif any(gap not in ALLOWED_UNKNOWN_ENGINE_CONVERSATION_GAP_LABELS_V1 for gap in mapped_gaps):
        _append_unique(invalid_fields, "mapped_gap_labels")
        for gap in mapped_gaps:
            if gap not in ALLOWED_UNKNOWN_ENGINE_CONVERSATION_GAP_LABELS_V1:
                _append_unique(blocked_reasons, f"unsupported_gap_label:{gap}")
    if not isinstance(item.get("blocked_authority"), Mapping):
        _append_unique(invalid_fields, "blocked_authority")
        _append_unique(blocked_reasons, "blocked_authority_not_mapping")
        blocked_authority = {}
    else:
        blocked_authority = item.get("blocked_authority")
    authority, authority_reasons = _safe_blocked_authority(blocked_authority)
    for reason in authority_reasons:
        _append_unique(blocked_reasons, reason)
    if item.get("synthetic_only") is not True:
        _append_unique(invalid_fields, "synthetic_only")
        _append_unique(blocked_reasons, "synthetic_only_false")
    if not isinstance(item.get("blocked"), bool):
        _append_unique(invalid_fields, "blocked")
        _append_unique(blocked_reasons, "blocked_not_boolean")
    if item.get("blocked") is True:
        for reason in _safe_labels(item.get("blocked_reason_labels")):
            _append_unique(blocked_reasons, reason)
    if not isinstance(item.get("validation_status"), str):
        _append_unique(invalid_fields, "validation_status")
        _append_unique(blocked_reasons, "validation_status_not_string")
    if not isinstance(item.get("blocked_reason_labels"), list):
        _append_unique(invalid_fields, "blocked_reason_labels")
        _append_unique(blocked_reasons, "blocked_reason_labels_not_list")
    if _detect_unsafe_metadata(item):
        for reason in _detect_unsafe_metadata(item):
            _append_unique(blocked_reasons, reason)
    json_safe = _is_json_safe(item)
    if not json_safe:
        _append_unique(blocked_reasons, "non_json_safe_metadata")
    valid = not missing and not invalid_fields and not blocked_reasons and json_safe
    return _json_safe(
        {
            "valid": valid,
            "blocked": not valid,
            "validation_status": "validation_pass_metadata_only" if valid else "blocked_invalid_or_unsafe_metadata_labels_only",
            "missing_required_fields": missing,
            "invalid_fields": _safe_labels(invalid_fields),
            "blocked_reason_labels": _safe_labels(blocked_reasons),
            "json_safe": json_safe,
            "blocked_authority": authority,
        }
    )


def build_unknown_engine_cognition_gap_hypothesis_v1(
    metadata: Mapping[str, Any] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    blocked_authority, authority_reasons = _safe_blocked_authority(source.get("blocked_authority", _blocked_authority_v1()))
    friction_label, friction_reasons = _validate_label(source.get("friction_label", DEFAULT_FAILURE_LABEL_V1), ALLOWED_UNKNOWN_ENGINE_CONVERSATION_FRICTION_LABELS_V1, kind="friction")
    gap_labels, gap_reasons = _filter_allowed_labels(source.get("gap_labels", []), ALLOWED_UNKNOWN_ENGINE_CONVERSATION_GAP_LABELS_V1, kind="gap")
    if not gap_labels and friction_label in FRICTION_TO_GAP_LABELS_V1:
        gap_labels = list(FRICTION_TO_GAP_LABELS_V1[friction_label])
    if not gap_labels:
        _append_unique(gap_reasons, "gap_labels_empty")
    source_turn_id = _safe_label(source.get("source_turn_id", DEFAULT_SOURCE_TURN_ID_V1))
    safe_reference_id = _safe_label(source.get("safe_reference_id", DEFAULT_GAP_HYPOTHESIS_ID_V1))
    transcript_scope = _safe_label(source.get("transcript_scope", DEFAULT_TRANSCRIPT_SCOPE_V1))
    synthetic_only = bool(source.get("synthetic_only", True))
    hypothesis = {
        "schema_version": GAP_HYPOTHESIS_SCHEMA_VERSION_V1,
        "item_type": "WeslrUnknownEngineCognitionGapHypothesisV1",
        "source_turn_id": source_turn_id,
        "friction_label": friction_label,
        "gap_labels": gap_labels,
        "safe_reference_id": safe_reference_id,
        "transcript_scope": transcript_scope,
        "synthetic_only": synthetic_only,
        "blocked_authority": blocked_authority,
        "validation_status": "validation_pass_metadata_only",
        "blocked": False,
        "blocked_reason_labels": [],
    }
    hypothesis_reasons = authority_reasons + friction_reasons + gap_reasons + _detect_unsafe_metadata(hypothesis)
    if not synthetic_only:
        _append_unique(hypothesis_reasons, "synthetic_only_false")
    if hypothesis_reasons:
        hypothesis["blocked"] = True
        hypothesis["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
        hypothesis["blocked_reason_labels"] = _safe_labels(hypothesis_reasons)
    return _json_safe(hypothesis)


def validate_unknown_engine_cognition_gap_hypothesis_v1(hypothesis: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(hypothesis, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_labels_only",
            "missing_required_fields": ["schema_version", "item_type"],
            "invalid_fields": ["hypothesis"],
            "blocked_reason_labels": ["hypothesis_not_mapping"],
            "json_safe": False,
        }
    missing = [
        field
        for field in (
            "schema_version",
            "item_type",
            "source_turn_id",
            "friction_label",
            "gap_labels",
            "safe_reference_id",
            "transcript_scope",
            "synthetic_only",
            "blocked_authority",
            "validation_status",
            "blocked",
            "blocked_reason_labels",
        )
        if field not in hypothesis
    ]
    invalid_fields: list[str] = []
    blocked_reasons: list[str] = []
    if hypothesis.get("schema_version") != GAP_HYPOTHESIS_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reasons, "schema_version_mismatch")
    if hypothesis.get("item_type") != "WeslrUnknownEngineCognitionGapHypothesisV1":
        _append_unique(invalid_fields, "item_type")
        _append_unique(blocked_reasons, "item_type_mismatch")
    friction_label, friction_reasons = _validate_label(hypothesis.get("friction_label"), ALLOWED_UNKNOWN_ENGINE_CONVERSATION_FRICTION_LABELS_V1, kind="friction")
    for reason in friction_reasons:
        _append_unique(blocked_reasons, reason)
    if friction_label is None:
        _append_unique(invalid_fields, "friction_label")
    gap_labels, gap_reasons = _filter_allowed_labels(hypothesis.get("gap_labels"), ALLOWED_UNKNOWN_ENGINE_CONVERSATION_GAP_LABELS_V1, kind="gap")
    for reason in gap_reasons:
        _append_unique(blocked_reasons, reason)
    if not gap_labels:
        _append_unique(invalid_fields, "gap_labels")
        _append_unique(blocked_reasons, "gap_labels_empty")
    if not isinstance(hypothesis.get("blocked_authority"), Mapping):
        _append_unique(invalid_fields, "blocked_authority")
        _append_unique(blocked_reasons, "blocked_authority_not_mapping")
        blocked_authority = {}
    else:
        blocked_authority = hypothesis.get("blocked_authority")
    authority, authority_reasons = _safe_blocked_authority(blocked_authority)
    for reason in authority_reasons:
        _append_unique(blocked_reasons, reason)
    if hypothesis.get("synthetic_only") is not True:
        _append_unique(invalid_fields, "synthetic_only")
        _append_unique(blocked_reasons, "synthetic_only_false")
    if not isinstance(hypothesis.get("blocked"), bool):
        _append_unique(invalid_fields, "blocked")
        _append_unique(blocked_reasons, "blocked_not_boolean")
    if hypothesis.get("blocked") is True:
        for reason in _safe_labels(hypothesis.get("blocked_reason_labels")):
            _append_unique(blocked_reasons, reason)
    if not isinstance(hypothesis.get("validation_status"), str):
        _append_unique(invalid_fields, "validation_status")
        _append_unique(blocked_reasons, "validation_status_not_string")
    if not isinstance(hypothesis.get("blocked_reason_labels"), list):
        _append_unique(invalid_fields, "blocked_reason_labels")
        _append_unique(blocked_reasons, "blocked_reason_labels_not_list")
    for reason in _detect_unsafe_metadata(hypothesis):
        _append_unique(blocked_reasons, reason)
    json_safe = _is_json_safe(hypothesis)
    if not json_safe:
        _append_unique(blocked_reasons, "non_json_safe_metadata")
    valid = not missing and not invalid_fields and not blocked_reasons and json_safe
    return _json_safe(
        {
            "valid": valid,
            "blocked": not valid,
            "validation_status": "validation_pass_metadata_only" if valid else "blocked_invalid_or_unsafe_metadata_labels_only",
            "missing_required_fields": missing,
            "invalid_fields": _safe_labels(invalid_fields),
            "blocked_reason_labels": _safe_labels(blocked_reasons),
            "json_safe": json_safe,
            "blocked_authority": authority,
        }
    )


def build_unknown_engine_failed_path_reference_v1(
    metadata: Mapping[str, Any] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    blocked_authority, authority_reasons = _safe_blocked_authority(source.get("blocked_authority", _blocked_authority_v1()))
    failure_label, failure_reasons = _validate_label(source.get("failure_label", DEFAULT_FAILURE_LABEL_V1), ALLOWED_UNKNOWN_ENGINE_CONVERSATION_FRICTION_LABELS_V1, kind="friction")
    gap_label, gap_reasons = _validate_label(source.get("gap_label", DEFAULT_GAP_LABEL_V1), ALLOWED_UNKNOWN_ENGINE_CONVERSATION_GAP_LABELS_V1, kind="gap")
    source_turn_id = _safe_label(source.get("source_turn_id", DEFAULT_SOURCE_TURN_ID_V1))
    safe_reference_id = _safe_label(source.get("safe_reference_id", DEFAULT_FAILURE_PATH_ID_V1))
    transcript_scope = _safe_label(source.get("transcript_scope", DEFAULT_TRANSCRIPT_SCOPE_V1))
    synthetic_only = bool(source.get("synthetic_only", True))
    path = {
        "schema_version": FAILED_PATH_REFERENCE_SCHEMA_VERSION_V1,
        "item_type": "WeslrUnknownEngineFailedPathReferenceV1",
        "source_turn_id": source_turn_id,
        "failure_label": failure_label,
        "gap_label": gap_label,
        "safe_reference_id": safe_reference_id,
        "source_observation_path": _safe_label(source.get("source_observation_path", DEFAULT_SOURCE_OBSERVATION_PATH_V1)),
        "transcript_scope": transcript_scope,
        "synthetic_only": synthetic_only,
        "blocked_authority": blocked_authority,
        "validation_status": "validation_pass_metadata_only",
        "blocked": False,
        "blocked_reason_labels": [],
    }
    path_reasons = authority_reasons + failure_reasons + gap_reasons + _detect_unsafe_metadata(path)
    if not synthetic_only:
        _append_unique(path_reasons, "synthetic_only_false")
    if path_reasons:
        path["blocked"] = True
        path["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
        path["blocked_reason_labels"] = _safe_labels(path_reasons)
    return _json_safe(path)


def validate_unknown_engine_failed_path_reference_v1(reference: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(reference, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_labels_only",
            "missing_required_fields": ["schema_version", "item_type"],
            "invalid_fields": ["reference"],
            "blocked_reason_labels": ["reference_not_mapping"],
            "json_safe": False,
        }
    missing = [
        field
        for field in (
            "schema_version",
            "item_type",
            "source_turn_id",
            "failure_label",
            "gap_label",
            "safe_reference_id",
            "source_observation_path",
            "transcript_scope",
            "synthetic_only",
            "blocked_authority",
            "validation_status",
            "blocked",
            "blocked_reason_labels",
        )
        if field not in reference
    ]
    invalid_fields: list[str] = []
    blocked_reasons: list[str] = []
    if reference.get("schema_version") != FAILED_PATH_REFERENCE_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reasons, "schema_version_mismatch")
    if reference.get("item_type") != "WeslrUnknownEngineFailedPathReferenceV1":
        _append_unique(invalid_fields, "item_type")
        _append_unique(blocked_reasons, "item_type_mismatch")
    failure_label, failure_reasons = _validate_label(reference.get("failure_label"), ALLOWED_UNKNOWN_ENGINE_CONVERSATION_FRICTION_LABELS_V1, kind="friction")
    gap_label, gap_reasons = _validate_label(reference.get("gap_label"), ALLOWED_UNKNOWN_ENGINE_CONVERSATION_GAP_LABELS_V1, kind="gap")
    for reason in failure_reasons + gap_reasons:
        _append_unique(blocked_reasons, reason)
    if failure_label is None:
        _append_unique(invalid_fields, "failure_label")
    if gap_label is None:
        _append_unique(invalid_fields, "gap_label")
    if not isinstance(reference.get("blocked_authority"), Mapping):
        _append_unique(invalid_fields, "blocked_authority")
        _append_unique(blocked_reasons, "blocked_authority_not_mapping")
        blocked_authority = {}
    else:
        blocked_authority = reference.get("blocked_authority")
    authority, authority_reasons = _safe_blocked_authority(blocked_authority)
    for reason in authority_reasons:
        _append_unique(blocked_reasons, reason)
    if reference.get("synthetic_only") is not True:
        _append_unique(invalid_fields, "synthetic_only")
        _append_unique(blocked_reasons, "synthetic_only_false")
    if not isinstance(reference.get("blocked"), bool):
        _append_unique(invalid_fields, "blocked")
        _append_unique(blocked_reasons, "blocked_not_boolean")
    if reference.get("blocked") is True:
        for reason in _safe_labels(reference.get("blocked_reason_labels")):
            _append_unique(blocked_reasons, reason)
    if not isinstance(reference.get("validation_status"), str):
        _append_unique(invalid_fields, "validation_status")
        _append_unique(blocked_reasons, "validation_status_not_string")
    if not isinstance(reference.get("blocked_reason_labels"), list):
        _append_unique(invalid_fields, "blocked_reason_labels")
        _append_unique(blocked_reasons, "blocked_reason_labels_not_list")
    for reason in _detect_unsafe_metadata(reference):
        _append_unique(blocked_reasons, reason)
    json_safe = _is_json_safe(reference)
    if not json_safe:
        _append_unique(blocked_reasons, "non_json_safe_metadata")
    valid = not missing and not invalid_fields and not blocked_reasons and json_safe
    return _json_safe(
        {
            "valid": valid,
            "blocked": not valid,
            "validation_status": "validation_pass_metadata_only" if valid else "blocked_invalid_or_unsafe_metadata_labels_only",
            "missing_required_fields": missing,
            "invalid_fields": _safe_labels(invalid_fields),
            "blocked_reason_labels": _safe_labels(blocked_reasons),
            "json_safe": json_safe,
            "blocked_authority": authority,
        }
    )


def build_unknown_engine_improvement_target_v1(
    metadata: Mapping[str, Any] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    blocked_authority, authority_reasons = _safe_blocked_authority(source.get("blocked_authority", _blocked_authority_v1()))
    gap_label, gap_reasons = _validate_label(source.get("gap_label", DEFAULT_GAP_LABEL_V1), ALLOWED_UNKNOWN_ENGINE_CONVERSATION_GAP_LABELS_V1, kind="gap")
    recommended_helper_name = _safe_label(source.get("recommended_helper_name", f"add_{gap_label.replace('missing_', '') if gap_label else 'conversation_helper'}_helper"))
    if not recommended_helper_name.endswith("_helper") and not recommended_helper_name.endswith("_helper_v1"):
        recommended_helper_name = f"{recommended_helper_name}_helper"
    recommendation_lane = _safe_label(source.get("recommended_lane", "helper_design_lane_only"))
    target = {
        "schema_version": IMPROVEMENT_TARGET_SCHEMA_VERSION_V1,
        "item_type": "WeslrUnknownEngineImprovementTargetV1",
        "target_id": _safe_label(source.get("target_id", DEFAULT_TARGET_ID_V1)),
        "gap_label": gap_label,
        "recommended_helper_name": recommended_helper_name,
        "recommended_lane": recommendation_lane,
        "bounded": True,
        "synthetic_only": bool(source.get("synthetic_only", True)),
        "blocked_authority": blocked_authority,
        "validation_status": "validation_pass_metadata_only",
        "blocked": False,
        "blocked_reason_labels": [],
    }
    target_reasons = authority_reasons + gap_reasons + _detect_unsafe_metadata(target)
    if target["recommended_lane"] != "helper_design_lane_only" and "lane" not in target["recommended_lane"].lower():
        _append_unique(target_reasons, "recommended_lane_not_helper_design_lane")
    if not target["bounded"]:
        _append_unique(target_reasons, "target_not_bounded")
    if target["synthetic_only"] is not True:
        _append_unique(target_reasons, "synthetic_only_false")
    if target_reasons:
        target["blocked"] = True
        target["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
        target["blocked_reason_labels"] = _safe_labels(target_reasons)
    return _json_safe(target)


def validate_unknown_engine_improvement_target_v1(target: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(target, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_labels_only",
            "missing_required_fields": ["schema_version", "item_type"],
            "invalid_fields": ["target"],
            "blocked_reason_labels": ["target_not_mapping"],
            "json_safe": False,
        }
    missing = [
        field
        for field in (
            "schema_version",
            "item_type",
            "target_id",
            "gap_label",
            "recommended_helper_name",
            "recommended_lane",
            "bounded",
            "synthetic_only",
            "blocked_authority",
            "validation_status",
            "blocked",
            "blocked_reason_labels",
        )
        if field not in target
    ]
    invalid_fields: list[str] = []
    blocked_reasons: list[str] = []
    if target.get("schema_version") != IMPROVEMENT_TARGET_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reasons, "schema_version_mismatch")
    if target.get("item_type") != "WeslrUnknownEngineImprovementTargetV1":
        _append_unique(invalid_fields, "item_type")
        _append_unique(blocked_reasons, "item_type_mismatch")
    gap_label, gap_reasons = _validate_label(target.get("gap_label"), ALLOWED_UNKNOWN_ENGINE_CONVERSATION_GAP_LABELS_V1, kind="gap")
    for reason in gap_reasons:
        _append_unique(blocked_reasons, reason)
    if gap_label is None:
        _append_unique(invalid_fields, "gap_label")
    if not isinstance(target.get("blocked_authority"), Mapping):
        _append_unique(invalid_fields, "blocked_authority")
        _append_unique(blocked_reasons, "blocked_authority_not_mapping")
        blocked_authority = {}
    else:
        blocked_authority = target.get("blocked_authority")
    authority, authority_reasons = _safe_blocked_authority(blocked_authority)
    for reason in authority_reasons:
        _append_unique(blocked_reasons, reason)
    if target.get("bounded") is not True:
        _append_unique(invalid_fields, "bounded")
        _append_unique(blocked_reasons, "target_not_bounded")
    if target.get("synthetic_only") is not True:
        _append_unique(invalid_fields, "synthetic_only")
        _append_unique(blocked_reasons, "synthetic_only_false")
    if not isinstance(target.get("blocked"), bool):
        _append_unique(invalid_fields, "blocked")
        _append_unique(blocked_reasons, "blocked_not_boolean")
    if target.get("blocked") is True:
        for reason in _safe_labels(target.get("blocked_reason_labels")):
            _append_unique(blocked_reasons, reason)
    if not isinstance(target.get("validation_status"), str):
        _append_unique(invalid_fields, "validation_status")
        _append_unique(blocked_reasons, "validation_status_not_string")
    if not isinstance(target.get("blocked_reason_labels"), list):
        _append_unique(invalid_fields, "blocked_reason_labels")
        _append_unique(blocked_reasons, "blocked_reason_labels_not_list")
    if "helper" not in _safe_label(target.get("recommended_helper_name", "")).lower():
        _append_unique(blocked_reasons, "recommended_helper_name_not_helper_design")
    if "lane" not in _safe_label(target.get("recommended_lane", "")).lower():
        _append_unique(blocked_reasons, "recommended_lane_not_helper_design_lane")
    for reason in _detect_unsafe_metadata(target):
        _append_unique(blocked_reasons, reason)
    json_safe = _is_json_safe(target)
    if not json_safe:
        _append_unique(blocked_reasons, "non_json_safe_metadata")
    valid = not missing and not invalid_fields and not blocked_reasons and json_safe
    return _json_safe(
        {
            "valid": valid,
            "blocked": not valid,
            "validation_status": "validation_pass_metadata_only" if valid else "blocked_invalid_or_unsafe_metadata_labels_only",
            "missing_required_fields": missing,
            "invalid_fields": _safe_labels(invalid_fields),
            "blocked_reason_labels": _safe_labels(blocked_reasons),
            "json_safe": json_safe,
            "blocked_authority": authority,
        }
    )


def _normalize_friction_item(value: Any) -> tuple[dict[str, Any], list[str]]:
    if isinstance(value, Mapping):
        item = build_unknown_engine_conversation_friction_item_v1(value)
    else:
        item = build_unknown_engine_conversation_friction_item_v1(failure_label=value)
    validation = validate_unknown_engine_conversation_friction_item_v1(item)
    reasons = list(validation.get("blocked_reason_labels", []))
    return item, reasons


def _normalize_gap_hypothesis(value: Any) -> tuple[dict[str, Any], list[str]]:
    if isinstance(value, Mapping):
        hypothesis = build_unknown_engine_cognition_gap_hypothesis_v1(value)
    else:
        hypothesis = build_unknown_engine_cognition_gap_hypothesis_v1(friction_label=value)
    validation = validate_unknown_engine_cognition_gap_hypothesis_v1(hypothesis)
    reasons = list(validation.get("blocked_reason_labels", []))
    return hypothesis, reasons


def _normalize_failed_path_reference(value: Any) -> tuple[dict[str, Any], list[str]]:
    if isinstance(value, Mapping):
        reference = build_unknown_engine_failed_path_reference_v1(value)
    else:
        reference = build_unknown_engine_failed_path_reference_v1(failure_label=value)
    validation = validate_unknown_engine_failed_path_reference_v1(reference)
    reasons = list(validation.get("blocked_reason_labels", []))
    return reference, reasons


def _normalize_improvement_target(value: Any) -> tuple[dict[str, Any], list[str]]:
    if isinstance(value, Mapping):
        target = build_unknown_engine_improvement_target_v1(value)
    else:
        target = build_unknown_engine_improvement_target_v1(gap_label=value)
    validation = validate_unknown_engine_improvement_target_v1(target)
    reasons = list(validation.get("blocked_reason_labels", []))
    return target, reasons


def build_unknown_engine_conversation_friction_assimilation_v1(
    metadata: Mapping[str, Any] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    blocked_authority, authority_reasons = _safe_blocked_authority(source.get("blocked_authority", _blocked_authority_v1()))
    friction_items_source = source.get("friction_items")
    friction_labels_source = source.get("friction_labels")
    friction_items: list[dict[str, Any]] = []
    blocked_reasons: list[str] = []

    if friction_items_source is None and friction_labels_source is not None:
        friction_items_source = [{"failure_label": label} for label in _as_list(friction_labels_source)]

    for raw_item in _as_list(friction_items_source):
        item, item_reasons = _normalize_friction_item(raw_item)
        friction_items.append(item)
        for reason in item_reasons:
            _append_unique(blocked_reasons, reason)

    if not friction_items:
        default_item, item_reasons = _normalize_friction_item({"failure_label": DEFAULT_FAILURE_LABEL_V1})
        friction_items.append(default_item)
        for reason in item_reasons:
            _append_unique(blocked_reasons, reason)

    cognition_gap_hypotheses_source = source.get("cognition_gap_hypotheses")
    if cognition_gap_hypotheses_source is None:
        cognition_gap_hypotheses_source = []
        for item in friction_items:
            for gap_label in _safe_labels(item.get("mapped_gap_labels")):
                cognition_gap_hypotheses_source.append({
                    "source_turn_id": item.get("source_turn_id", DEFAULT_SOURCE_TURN_ID_V1),
                    "friction_label": item.get("failure_label"),
                    "gap_labels": [gap_label],
                    "safe_reference_id": f"{_safe_label(item.get('safe_reference_id', DEFAULT_SAFE_REFERENCE_ID_V1))}:{gap_label}",
                    "transcript_scope": item.get("transcript_scope", DEFAULT_TRANSCRIPT_SCOPE_V1),
                    "synthetic_only": item.get("synthetic_only", True),
                })
    cognition_gap_hypotheses: list[dict[str, Any]] = []
    for raw_hypothesis in _as_list(cognition_gap_hypotheses_source):
        hypothesis, hypothesis_reasons = _normalize_gap_hypothesis(raw_hypothesis)
        cognition_gap_hypotheses.append(hypothesis)
        for reason in hypothesis_reasons:
            _append_unique(blocked_reasons, reason)

    failed_path_references_source = source.get("failed_path_references")
    if failed_path_references_source is None:
        failed_path_references_source = [
            {
                "source_turn_id": item.get("source_turn_id", DEFAULT_SOURCE_TURN_ID_V1),
                "failure_label": item.get("failure_label"),
                "gap_label": gap_label,
                "safe_reference_id": f"{_safe_label(item.get('safe_reference_id', DEFAULT_SAFE_REFERENCE_ID_V1))}:{gap_label}:failed_path",
                "source_observation_path": source.get("source_observation_path", DEFAULT_SOURCE_OBSERVATION_PATH_V1),
                "transcript_scope": item.get("transcript_scope", DEFAULT_TRANSCRIPT_SCOPE_V1),
                "synthetic_only": item.get("synthetic_only", True),
            }
            for item in friction_items
            for gap_label in _safe_labels(item.get("mapped_gap_labels"))
        ]
    failed_path_references: list[dict[str, Any]] = []
    for raw_reference in _as_list(failed_path_references_source):
        reference, reference_reasons = _normalize_failed_path_reference(raw_reference)
        failed_path_references.append(reference)
        for reason in reference_reasons:
            _append_unique(blocked_reasons, reason)

    improvement_targets_source = source.get("improvement_targets")
    if improvement_targets_source is None:
        unique_gaps: list[str] = []
        for item in friction_items:
            for gap_label in _safe_labels(item.get("mapped_gap_labels")):
                _append_unique(unique_gaps, gap_label)
        improvement_targets_source = [
            {
                "target_id": f"{gap_label}:improvement_target",
                "gap_label": gap_label,
                "recommended_helper_name": f"add_{gap_label}_helper",
                "recommended_lane": "helper_design_lane_only",
                "synthetic_only": True,
            }
            for gap_label in unique_gaps
        ]
    improvement_targets: list[dict[str, Any]] = []
    for raw_target in _as_list(improvement_targets_source):
        target, target_reasons = _normalize_improvement_target(raw_target)
        improvement_targets.append(target)
        for reason in target_reasons:
            _append_unique(blocked_reasons, reason)

    source_observation_path = _safe_label(source.get("source_observation_path", DEFAULT_SOURCE_OBSERVATION_PATH_V1))
    observation_commit = _safe_label(source.get("observation_commit", DEFAULT_OBSERVATION_COMMIT_V1))
    transcript_scope = _safe_label(source.get("transcript_scope", DEFAULT_TRANSCRIPT_SCOPE_V1))
    synthetic_only = bool(source.get("synthetic_only", True))
    raw_private_data_included = bool(source.get("raw_private_data_included", False))
    provider_model_calls_allowed = bool(source.get("provider_model_calls_allowed", False))
    runtime_wiring_allowed = bool(source.get("runtime_wiring_allowed", False))
    official_score_allowed = bool(source.get("official_score_allowed", False))
    recommended_next_lane = _safe_label(source.get("recommended_next_lane", RECOMMENDED_NEXT_LANE_V1))
    if not recommended_next_lane:
        recommended_next_lane = RECOMMENDED_NEXT_LANE_V1

    artifact = {
        "schema_version": SCHEMA_VERSION_V1,
        "artifact_type": ARTIFACT_TYPE_V1,
        "source_observation_path": source_observation_path,
        "observation_commit": observation_commit,
        "transcript_scope": transcript_scope,
        "synthetic_only": synthetic_only,
        "raw_private_data_included": raw_private_data_included,
        "provider_model_calls_allowed": provider_model_calls_allowed,
        "runtime_wiring_allowed": runtime_wiring_allowed,
        "official_score_allowed": official_score_allowed,
        "friction_items": friction_items,
        "cognition_gap_hypotheses": cognition_gap_hypotheses,
        "failed_path_references": failed_path_references,
        "improvement_targets": improvement_targets,
        "blocked_authority": blocked_authority,
        "recommended_next_lane": recommended_next_lane,
        "validation_status": "validation_pass_metadata_only",
        "blocked_reason_labels": [],
    }

    if not synthetic_only:
        _append_unique(blocked_reasons, "synthetic_only_false")
    if raw_private_data_included:
        _append_unique(blocked_reasons, "raw_private_data_included_true")
    if provider_model_calls_allowed:
        _append_unique(blocked_reasons, "provider_model_calls_allowed_true")
    if runtime_wiring_allowed:
        _append_unique(blocked_reasons, "runtime_wiring_allowed_true")
    if official_score_allowed:
        _append_unique(blocked_reasons, "official_score_allowed_true")
    if recommended_next_lane != RECOMMENDED_NEXT_LANE_V1 and "helper" not in recommended_next_lane.lower():
        _append_unique(blocked_reasons, "recommended_next_lane_not_helper_lane")
    if not source_observation_path or ".weslr" in source_observation_path.lower():
        _append_unique(blocked_reasons, "dot_weslr_path_detected")
    for reason in authority_reasons:
        _append_unique(blocked_reasons, reason)
    for reason in _detect_unsafe_metadata(artifact):
        _append_unique(blocked_reasons, reason)

    artifact["blocked_reason_labels"] = _safe_labels(blocked_reasons)
    artifact["validation_status"] = "validation_pass_metadata_only" if not blocked_reasons else "blocked_invalid_or_unsafe_metadata_labels_only"
    artifact["blocked"] = bool(blocked_reasons)
    return _json_safe(artifact)


def validate_unknown_engine_conversation_friction_assimilation_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "schema_version",
        "artifact_type",
        "source_observation_path",
        "observation_commit",
        "transcript_scope",
        "synthetic_only",
        "raw_private_data_included",
        "provider_model_calls_allowed",
        "runtime_wiring_allowed",
        "official_score_allowed",
        "friction_items",
        "cognition_gap_hypotheses",
        "failed_path_references",
        "improvement_targets",
        "blocked_authority",
        "recommended_next_lane",
        "validation_status",
        "blocked_reason_labels",
    )
    if not isinstance(artifact, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_labels_only",
            "missing_required_fields": list(required_fields),
            "invalid_fields": ["artifact"],
            "blocked_reason_labels": ["artifact_not_mapping"],
            "json_safe": False,
        }
    missing = [field for field in required_fields if field not in artifact]
    invalid_fields: list[str] = []
    blocked_reasons: list[str] = []
    if artifact.get("schema_version") != SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reasons, "schema_version_mismatch")
    if artifact.get("artifact_type") != ARTIFACT_TYPE_V1:
        _append_unique(invalid_fields, "artifact_type")
        _append_unique(blocked_reasons, "artifact_type_mismatch")
    if not isinstance(artifact.get("source_observation_path"), str) or not artifact.get("source_observation_path"):
        _append_unique(invalid_fields, "source_observation_path")
        _append_unique(blocked_reasons, "source_observation_path_invalid")
    if ".weslr" in _safe_label(artifact.get("source_observation_path", "")).lower():
        _append_unique(blocked_reasons, "dot_weslr_path_detected")
    if not isinstance(artifact.get("observation_commit"), str) or not artifact.get("observation_commit"):
        _append_unique(invalid_fields, "observation_commit")
        _append_unique(blocked_reasons, "observation_commit_invalid")
    if not isinstance(artifact.get("transcript_scope"), str) or not artifact.get("transcript_scope"):
        _append_unique(invalid_fields, "transcript_scope")
        _append_unique(blocked_reasons, "transcript_scope_invalid")
    if artifact.get("synthetic_only") is not True:
        _append_unique(invalid_fields, "synthetic_only")
        _append_unique(blocked_reasons, "synthetic_only_false")
    if artifact.get("raw_private_data_included") is not False:
        _append_unique(invalid_fields, "raw_private_data_included")
        _append_unique(blocked_reasons, "raw_private_data_included_true")
    if artifact.get("provider_model_calls_allowed") is not False:
        _append_unique(invalid_fields, "provider_model_calls_allowed")
        _append_unique(blocked_reasons, "provider_model_calls_allowed_true")
    if artifact.get("runtime_wiring_allowed") is not False:
        _append_unique(invalid_fields, "runtime_wiring_allowed")
        _append_unique(blocked_reasons, "runtime_wiring_allowed_true")
    if artifact.get("official_score_allowed") is not False:
        _append_unique(invalid_fields, "official_score_allowed")
        _append_unique(blocked_reasons, "official_score_allowed_true")
    if not isinstance(artifact.get("recommended_next_lane"), str) or not artifact.get("recommended_next_lane"):
        _append_unique(invalid_fields, "recommended_next_lane")
        _append_unique(blocked_reasons, "recommended_next_lane_invalid")
    if "helper" not in _safe_label(artifact.get("recommended_next_lane", "")).lower():
        _append_unique(blocked_reasons, "recommended_next_lane_not_helper_lane")
    if not isinstance(artifact.get("blocked_authority"), Mapping):
        _append_unique(invalid_fields, "blocked_authority")
        _append_unique(blocked_reasons, "blocked_authority_not_mapping")
        blocked_authority = {}
    else:
        blocked_authority = artifact.get("blocked_authority")
    authority, authority_reasons = _safe_blocked_authority(blocked_authority)
    for reason in authority_reasons:
        _append_unique(blocked_reasons, reason)
    if not isinstance(artifact.get("friction_items"), list):
        _append_unique(invalid_fields, "friction_items")
        _append_unique(blocked_reasons, "friction_items_not_list")
    if not isinstance(artifact.get("cognition_gap_hypotheses"), list):
        _append_unique(invalid_fields, "cognition_gap_hypotheses")
        _append_unique(blocked_reasons, "cognition_gap_hypotheses_not_list")
    if not isinstance(artifact.get("failed_path_references"), list):
        _append_unique(invalid_fields, "failed_path_references")
        _append_unique(blocked_reasons, "failed_path_references_not_list")
    if not isinstance(artifact.get("improvement_targets"), list):
        _append_unique(invalid_fields, "improvement_targets")
        _append_unique(blocked_reasons, "improvement_targets_not_list")
    if not isinstance(artifact.get("validation_status"), str):
        _append_unique(invalid_fields, "validation_status")
        _append_unique(blocked_reasons, "validation_status_not_string")
    if not isinstance(artifact.get("blocked_reason_labels"), list):
        _append_unique(invalid_fields, "blocked_reason_labels")
        _append_unique(blocked_reasons, "blocked_reason_labels_not_list")

    if any(item.get("synthetic_only") is not True for item in _as_list(artifact.get("friction_items")) if isinstance(item, Mapping)):
        _append_unique(blocked_reasons, "friction_item_synthetic_only_false")
    if any(gap.get("synthetic_only") is not True for gap in _as_list(artifact.get("cognition_gap_hypotheses")) if isinstance(gap, Mapping)):
        _append_unique(blocked_reasons, "cognition_gap_hypothesis_synthetic_only_false")
    if any(reference.get("synthetic_only") is not True for reference in _as_list(artifact.get("failed_path_references")) if isinstance(reference, Mapping)):
        _append_unique(blocked_reasons, "failed_path_reference_synthetic_only_false")
    if any(target.get("synthetic_only") is not True for target in _as_list(artifact.get("improvement_targets")) if isinstance(target, Mapping)):
        _append_unique(blocked_reasons, "improvement_target_synthetic_only_false")

    for item in _as_list(artifact.get("friction_items")):
        if isinstance(item, Mapping):
            validation = validate_unknown_engine_conversation_friction_item_v1(item)
            if not validation.get("valid"):
                _append_unique(blocked_reasons, "friction_item_invalid")
                for reason in _safe_labels(validation.get("blocked_reason_labels")):
                    _append_unique(blocked_reasons, reason)
    for hypothesis in _as_list(artifact.get("cognition_gap_hypotheses")):
        if isinstance(hypothesis, Mapping):
            validation = validate_unknown_engine_cognition_gap_hypothesis_v1(hypothesis)
            if not validation.get("valid"):
                _append_unique(blocked_reasons, "cognition_gap_hypothesis_invalid")
                for reason in _safe_labels(validation.get("blocked_reason_labels")):
                    _append_unique(blocked_reasons, reason)
    for reference in _as_list(artifact.get("failed_path_references")):
        if isinstance(reference, Mapping):
            validation = validate_unknown_engine_failed_path_reference_v1(reference)
            if not validation.get("valid"):
                _append_unique(blocked_reasons, "failed_path_reference_invalid")
                for reason in _safe_labels(validation.get("blocked_reason_labels")):
                    _append_unique(blocked_reasons, reason)
    for target in _as_list(artifact.get("improvement_targets")):
        if isinstance(target, Mapping):
            validation = validate_unknown_engine_improvement_target_v1(target)
            if not validation.get("valid"):
                _append_unique(blocked_reasons, "improvement_target_invalid")
                for reason in _safe_labels(validation.get("blocked_reason_labels")):
                    _append_unique(blocked_reasons, reason)

    blocked_reason_labels = _safe_labels(artifact.get("blocked_reason_labels"))
    for reason in blocked_reason_labels:
        _append_unique(blocked_reasons, reason)
    for reason in _detect_unsafe_metadata(artifact):
        _append_unique(blocked_reasons, reason)
    json_safe = _is_json_safe(artifact)
    if not json_safe:
        _append_unique(blocked_reasons, "non_json_safe_metadata")

    valid = not missing and not invalid_fields and not blocked_reasons and json_safe
    return _json_safe(
        {
            "valid": valid,
            "blocked": not valid,
            "validation_status": "validation_pass_metadata_only" if valid else "blocked_invalid_or_unsafe_metadata_labels_only",
            "missing_required_fields": missing,
            "invalid_fields": _safe_labels(invalid_fields),
            "blocked_reason_labels": _safe_labels(blocked_reasons),
            "json_safe": json_safe,
            "blocked_authority": authority,
        }
    )


def summarize_unknown_engine_conversation_friction_assimilation_v1(
    artifact: Mapping[str, Any],
) -> dict[str, Any]:
    validation = validate_unknown_engine_conversation_friction_assimilation_v1(artifact)
    friction_labels: list[str] = []
    for item in _as_list(artifact.get("friction_items")) if isinstance(artifact, Mapping) else []:
        if isinstance(item, Mapping):
            _append_unique(friction_labels, _safe_label(item.get("failure_label")))
    gap_labels: list[str] = []
    for hypothesis in _as_list(artifact.get("cognition_gap_hypotheses")) if isinstance(artifact, Mapping) else []:
        if isinstance(hypothesis, Mapping):
            for gap_label in _safe_labels(hypothesis.get("gap_labels")):
                _append_unique(gap_labels, gap_label)
    summary = {
        "schema_version": SCHEMA_VERSION_V1,
        "artifact_type": ARTIFACT_TYPE_V1,
        "counts": {
            "friction_items": len(_as_list(artifact.get("friction_items")) if isinstance(artifact, Mapping) else []),
            "cognition_gap_hypotheses": len(_as_list(artifact.get("cognition_gap_hypotheses")) if isinstance(artifact, Mapping) else []),
            "failed_path_references": len(_as_list(artifact.get("failed_path_references")) if isinstance(artifact, Mapping) else []),
            "improvement_targets": len(_as_list(artifact.get("improvement_targets")) if isinstance(artifact, Mapping) else []),
        },
        "friction_labels": friction_labels,
        "gap_labels": gap_labels,
        "blocked": validation["blocked"],
        "blocked_reason_labels": validation["blocked_reason_labels"],
        "recommended_next_lane": artifact.get("recommended_next_lane", RECOMMENDED_NEXT_LANE_V1) if isinstance(artifact, Mapping) else RECOMMENDED_NEXT_LANE_V1,
        "validation_status": validation["validation_status"],
        "json_safe": validation["json_safe"],
    }
    return _json_safe(summary)


__all__ = (
    "allowed_unknown_engine_conversation_friction_labels_v1",
    "allowed_unknown_engine_conversation_gap_labels_v1",
    "required_unknown_engine_blocked_authority_v1",
    "build_unknown_engine_conversation_friction_item_v1",
    "validate_unknown_engine_conversation_friction_item_v1",
    "build_unknown_engine_cognition_gap_hypothesis_v1",
    "validate_unknown_engine_cognition_gap_hypothesis_v1",
    "build_unknown_engine_failed_path_reference_v1",
    "validate_unknown_engine_failed_path_reference_v1",
    "build_unknown_engine_improvement_target_v1",
    "validate_unknown_engine_improvement_target_v1",
    "build_unknown_engine_conversation_friction_assimilation_v1",
    "validate_unknown_engine_conversation_friction_assimilation_v1",
    "summarize_unknown_engine_conversation_friction_assimilation_v1",
    "map_unknown_engine_friction_to_cognition_gaps_v1",
)
