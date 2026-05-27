"""WESLR targeted response formation improvement helpers V1.

Pure helper code for deterministic, metadata-only, JSON-safe response-formation
planning. This module does not wire into runtime chat, does not call providers,
models, search, or advisors, does not read private data, does not touch
`.weslr`, and does not generate final answers.
"""

from __future__ import annotations

from copy import deepcopy
import json
import math
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "WeslrTargetedResponseFormationImprovementHelpersV1"
PLAN_SCHEMA_VERSION_V1 = "WeslrTargetedResponseFormationImprovementPlanV1"
CONVERSATION_STATE_SCHEMA_VERSION_V1 = "ConversationStateFrameV1"
CURRENT_USER_CONCERN_SCHEMA_VERSION_V1 = "CurrentUserConcernSlotV1"
RECENT_TURN_RECALL_SCHEMA_VERSION_V1 = "RecentTurnRecallObjectV1"
GOAL_SUBGOAL_SCHEMA_VERSION_V1 = "GoalSubgoalConversationFrameV1"
ANSWER_SHAPE_PLANNER_SCHEMA_VERSION_V1 = "AnswerShapePlannerV1"
CONCRETE_NEXT_STEP_SCHEMA_VERSION_V1 = "ConcreteNextStepSelectorV1"
NON_CANNEDNESS_SCHEMA_VERSION_V1 = "NonCannednessPressureV1"
RESPONSE_SHAPE_DIVERSITY_SCHEMA_VERSION_V1 = "ResponseShapeDiversityV1"
EMPATHY_CONCERN_SCHEMA_VERSION_V1 = "EmpathyConcernIntegrationV1"
RESPONSE_SELF_CHECK_SCHEMA_VERSION_V1 = "ResponseSelfCheckBeforeFinalAnswerV1"
DIRECTNESS_SCHEMA_VERSION_V1 = "DirectnessPressureV1"
AUTHORITY_CALIBRATION_SCHEMA_VERSION_V1 = "BoundarySpecificAuthorityCalibrationV1"
FALLBACK_GATING_SCHEMA_VERSION_V1 = "BoundarySpecificFallbackGatingV1"

ARTIFACT_TYPE_V1 = "WeslrTargetedResponseFormationImprovementPlanV1"

SOURCE_RUN_RESULT_PATH_V1 = "docs/WESLR_UNKNOWN_ENGINE_CONVERSATION_FRICTION_ASSIMILATION_RUN_RESULT_V1.md"
SOURCE_RUN_RESULT_COMMIT_V1 = "c72d1f7"
SOURCE_REVIEW_PATH_V1 = "docs/WESLR_UNKNOWN_ENGINE_CONVERSATION_FRICTION_ASSIMILATION_RUN_RESULT_REVIEW_V1.md"
SOURCE_REVIEW_COMMIT_V1 = "accc63e"

ALLOWED_TARGETED_RESPONSE_GAP_LABELS_V1: tuple[str, ...] = (
    "missing_answer_shape_planner",
    "missing_concrete_next_step_selection",
    "missing_conversation_state_frame",
    "missing_current_user_concern_slot",
    "missing_recent_turn_recall_object",
    "missing_goal_subgoal_cache_use",
    "missing_non_cannedness_pressure",
    "missing_response_shape_diversity",
    "missing_empathy_concern_integration",
    "missing_response_self_check_before_final_answer",
    "missing_directness_pressure",
    "missing_boundary_specific_authority_calibration",
    "missing_boundary_specific_fallback_gating",
)

ALLOWED_TARGETED_RESPONSE_HELPER_LABELS_V1: tuple[str, ...] = (
    "ConversationStateFrameV1",
    "CurrentUserConcernSlotV1",
    "RecentTurnRecallObjectV1",
    "GoalSubgoalConversationFrameV1",
    "AnswerShapePlannerV1",
    "ConcreteNextStepSelectorV1",
    "NonCannednessPressureV1",
    "ResponseShapeDiversityV1",
    "EmpathyConcernIntegrationV1",
    "ResponseSelfCheckBeforeFinalAnswerV1",
    "DirectnessPressureV1",
    "BoundarySpecificAuthorityCalibrationV1",
    "BoundarySpecificFallbackGatingV1",
)

HELPER_TO_GAP_V1: tuple[tuple[str, str], ...] = (
    ("ConversationStateFrameV1", "missing_conversation_state_frame"),
    ("CurrentUserConcernSlotV1", "missing_current_user_concern_slot"),
    ("RecentTurnRecallObjectV1", "missing_recent_turn_recall_object"),
    ("GoalSubgoalConversationFrameV1", "missing_goal_subgoal_cache_use"),
    ("AnswerShapePlannerV1", "missing_answer_shape_planner"),
    ("ConcreteNextStepSelectorV1", "missing_concrete_next_step_selection"),
    ("NonCannednessPressureV1", "missing_non_cannedness_pressure"),
    ("ResponseShapeDiversityV1", "missing_response_shape_diversity"),
    ("EmpathyConcernIntegrationV1", "missing_empathy_concern_integration"),
    ("ResponseSelfCheckBeforeFinalAnswerV1", "missing_response_self_check_before_final_answer"),
    ("DirectnessPressureV1", "missing_directness_pressure"),
    ("BoundarySpecificAuthorityCalibrationV1", "missing_boundary_specific_authority_calibration"),
    ("BoundarySpecificFallbackGatingV1", "missing_boundary_specific_fallback_gating"),
)

ALLOWED_ANSWER_SHAPES_V1: tuple[str, ...] = (
    "direct_answer_with_boundary",
    "tradeoff_reasoning",
    "concrete_next_step",
    "correction_repair",
    "refusal_with_useful_alternative",
    "reassurance_with_reasoning",
    "planning_with_constraints",
    "explanation_of_limits",
    "ask_one_clarifying_question_only_when_needed",
)

BLOCKED_ANSWER_SHAPES_V1: tuple[str, ...] = (
    "generic_checklist_when_judgment_requested",
    "safety_boundary_only_when_help_possible",
    "identity_answer_when_practical_step_requested",
    "memory_claim_without_local_evidence",
    "public_readiness_claim",
    "final_answer_authority_claim",
    "execution_claim",
)

DENIED_AUTHORITY_FIELDS_V1: tuple[str, ...] = (
    "permits_runtime_changes",
    "permits_chat_wiring",
    "permits_final_answer_generation",
    "permits_provider_calls",
    "permits_model_calls",
    "permits_search_calls",
    "permits_advisor_calls",
    "permits_raw_private_data",
    "permits_dot_weslr_io",
    "permits_continuity_raw_reads",
    "permits_memory_persistence",
    "permits_public_launch",
    "permits_product_readiness_claims",
    "permits_intelligence_claims",
    "permits_turing_claims",
    "permits_certification_claims",
    "permits_official_scoring",
    "permits_auto_implementation",
)

ALLOWED_USER_INTENT_TYPES_V1: tuple[str, ...] = (
    "planning",
    "judgment",
    "correction",
    "reassurance",
    "boundary_explanation",
    "practical_next_step",
    "tradeoff_reasoning",
    "unknown_or_blocked",
)

ALLOWED_RECALL_SCOPES_V1: tuple[str, ...] = (
    "local_recent_turn",
    "synthetic_observation",
)

ALLOWED_SHAPE_FAMILIES_V1: tuple[str, ...] = (
    "direct",
    "reasoning",
    "action",
    "repair",
    "refusal",
    "reassurance",
    "planning",
    "limits",
    "clarification",
)

_FORBIDDEN_MARKERS_V1 = (
    ".weslr",
    "continuity/",
    "review_queue.json",
    "pilot_signals/",
    "suggestion_box/",
    "raw prompt",
    "raw response",
    "hidden prompt",
    "protected item",
    "protected material",
    "private record",
    "private data",
    "provider call",
    "model call",
    "search call",
    "advisor call",
    "runtime change",
    "chat wiring",
    "final answer generation",
    "public readiness claim",
    "intelligence claim",
    "turing claim",
    "certification claim",
    "memory persistence",
)

_JSON_SAFE_SCALARS = (str, int, bool, type(None))


def _append_unique(values: list[str], value: Any) -> None:
    text = str(value)
    if text not in values:
        values.append(text)


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return default
        return str(value)
    return default if value == "" else str(value)


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    return default


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _merge_metadata(metadata: Mapping[str, Any] | None, overrides: Mapping[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(metadata, Mapping):
        merged.update(metadata)
    if isinstance(overrides, Mapping):
        merged.update(overrides)
    return merged


def _json_safe_copy(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe_copy(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, _JSON_SAFE_SCALARS):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError("non_json_safe_metadata")
        return value
    raise ValueError("non_json_safe_metadata")


def to_targeted_response_formation_improvement_json_safe_v1(value: Any) -> Any:
    """Return a JSON-safe deep copy or raise ValueError for unsafe metadata."""

    safe = _json_safe_copy(deepcopy(value))
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _detect_unsafe_metadata(value: Any) -> list[str]:
    reasons: list[str] = []
    try:
        to_targeted_response_formation_improvement_json_safe_v1(value)
    except Exception:
        _append_unique(reasons, "non_json_safe_metadata")
        return reasons

    def _walk(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                key_text = _safe_text(key).lower()
                for marker in _FORBIDDEN_MARKERS_V1:
                    if marker in key_text:
                        _append_unique(reasons, f"forbidden_marker:{marker}")
                _walk(child)
        elif isinstance(item, list):
            for child in item:
                _walk(child)
        elif isinstance(item, str):
            lowered = item.lower()
            for marker in _FORBIDDEN_MARKERS_V1:
                if marker in lowered:
                    _append_unique(reasons, f"forbidden_marker:{marker}")

    _walk(value)
    return reasons


def _validate_allowed_label_list(value: Any, allowed: tuple[str, ...], *, kind: str) -> tuple[list[str], list[str]]:
    labels: list[str] = []
    reasons: list[str] = []
    for raw in _as_list(value):
        safe = _safe_text(raw).strip()
        if not safe:
            _append_unique(reasons, f"{kind}_label_empty")
            continue
        if safe not in allowed:
            _append_unique(reasons, f"unsupported_{kind}_label:{safe}")
            continue
        if safe not in labels:
            labels.append(safe)
    return labels, reasons


def _safe_blocked_authority() -> dict[str, bool]:
    return {field: False for field in DENIED_AUTHORITY_FIELDS_V1}


def required_targeted_response_denied_authority_v1() -> dict[str, bool]:
    return _safe_blocked_authority()


def _validate_denied_authority(value: Any) -> tuple[dict[str, bool], list[str]]:
    reasons: list[str] = []
    if not isinstance(value, Mapping):
        return _safe_blocked_authority(), ["denied_authority_not_mapping"]
    result = _safe_blocked_authority()
    for field in DENIED_AUTHORITY_FIELDS_V1:
        if field not in value:
            _append_unique(reasons, f"missing_denied_authority_field:{field}")
            continue
        if value.get(field) is not False:
            _append_unique(reasons, f"denied_authority_field_not_false:{field}")
        result[field] = False
    for key, item in value.items():
        if key not in DENIED_AUTHORITY_FIELDS_V1 and item is not False:
            _append_unique(reasons, f"unexpected_denied_authority_field:{key}")
    return result, reasons


def allowed_targeted_response_gap_labels_v1() -> tuple[str, ...]:
    return ALLOWED_TARGETED_RESPONSE_GAP_LABELS_V1


def allowed_targeted_response_helper_labels_v1() -> tuple[str, ...]:
    return ALLOWED_TARGETED_RESPONSE_HELPER_LABELS_V1


def allowed_answer_shapes_v1() -> tuple[str, ...]:
    return ALLOWED_ANSWER_SHAPES_V1


def blocked_answer_shapes_v1() -> tuple[str, ...]:
    return BLOCKED_ANSWER_SHAPES_V1


def _intent_to_shape(metadata: Mapping[str, Any]) -> tuple[str, list[str]]:
    blocked_reasons: list[str] = []
    intent = _safe_text(metadata.get("user_intent_type", metadata.get("intent_type", "unknown_or_blocked"))).strip()
    if intent not in ALLOWED_USER_INTENT_TYPES_V1:
        _append_unique(blocked_reasons, f"unsupported_user_intent_type:{intent}")
        intent = "unknown_or_blocked"
    boundary_label = _safe_text(metadata.get("boundary_label", "")).strip()
    last_correction = _safe_text(metadata.get("last_correction_label", metadata.get("last_correction", ""))).strip()
    concern = _safe_text(metadata.get("current_user_concern_label", metadata.get("concern_label", ""))).strip()
    fallback_risk = _safe_bool(metadata.get("provider_model_fallback_risk", False)) or _safe_bool(metadata.get("fallback_risk_detected", False))
    practical_step_needed = _safe_bool(metadata.get("concrete_next_step_required", False)) or intent == "practical_next_step"
    tradeoff_needed = _safe_bool(metadata.get("tradeoff_needed", False)) or intent == "tradeoff_reasoning"
    correction_needed = _safe_bool(metadata.get("correction_needed", False)) or bool(last_correction)
    reassurance_needed = _safe_bool(metadata.get("reassurance_needed", False)) or intent == "reassurance"
    boundary_explanation_needed = _safe_bool(metadata.get("boundary_explanation_needed", False)) or intent == "boundary_explanation"
    planning_needed = _safe_bool(metadata.get("planning_needed", False)) or intent == "planning"
    judgment_requested = intent == "judgment"

    if correction_needed:
        return "correction_repair", blocked_reasons
    if tradeoff_needed:
        return "tradeoff_reasoning", blocked_reasons
    if practical_step_needed:
        return "concrete_next_step", blocked_reasons
    if reassurance_needed and concern:
        return "reassurance_with_reasoning", blocked_reasons
    if boundary_explanation_needed or boundary_label:
        if fallback_risk:
            return "explanation_of_limits", blocked_reasons
        return "direct_answer_with_boundary", blocked_reasons
    if planning_needed:
        return "planning_with_constraints", blocked_reasons
    if judgment_requested:
        if concern or fallback_risk:
            return "tradeoff_reasoning", blocked_reasons
        return "direct_answer_with_boundary", blocked_reasons
    if fallback_risk:
        return "refusal_with_useful_alternative", blocked_reasons
    if intent == "unknown_or_blocked":
        return "ask_one_clarifying_question_only_when_needed", blocked_reasons
    return "direct_answer_with_boundary", blocked_reasons


def select_answer_shape_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    selected_shape, blocked_reason_labels = _intent_to_shape(source)
    if selected_shape in BLOCKED_ANSWER_SHAPES_V1:
        _append_unique(blocked_reason_labels, f"blocked_answer_shape_selected:{selected_shape}")
    result = {
        "schema_version": ANSWER_SHAPE_PLANNER_SCHEMA_VERSION_V1,
        "selected_answer_shape": selected_shape,
        "requested_user_intent_type": _safe_text(source.get("user_intent_type", source.get("intent_type", "unknown_or_blocked"))).strip() or "unknown_or_blocked",
        "boundary_label": _safe_text(source.get("boundary_label", "")).strip(),
        "current_user_concern_label": _safe_text(source.get("current_user_concern_label", source.get("concern_label", ""))).strip(),
        "last_correction_label": _safe_text(source.get("last_correction_label", source.get("last_correction", ""))).strip(),
        "fallback_risk_label": "provider_model_fallback_risk" if _safe_bool(source.get("provider_model_fallback_risk", False)) or _safe_bool(source.get("fallback_risk_detected", False)) else "none",
        "blocked_reason_labels": blocked_reason_labels,
        "validation_status": "validation_pass_metadata_only" if selected_shape in ALLOWED_ANSWER_SHAPES_V1 else "blocked_invalid_or_unsafe_metadata_only",
    }
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def validate_answer_shape_plan_v1(plan: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "schema_version",
        "selected_answer_shape",
        "requested_user_intent_type",
        "boundary_label",
        "current_user_concern_label",
        "last_correction_label",
        "fallback_risk_label",
        "blocked_reason_labels",
        "validation_status",
    )
    if not isinstance(plan, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_only",
            "missing_required_fields": list(required_fields),
            "invalid_fields": ["plan"],
            "blocked_reason_labels": ["plan_not_mapping"],
            "json_safe": False,
        }
    missing = [field for field in required_fields if field not in plan]
    invalid_fields: list[str] = []
    blocked_reason_labels: list[str] = []
    if plan.get("schema_version") != ANSWER_SHAPE_PLANNER_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")
    selected_shape = _safe_text(plan.get("selected_answer_shape", "")).strip()
    if selected_shape not in ALLOWED_ANSWER_SHAPES_V1:
        _append_unique(invalid_fields, "selected_answer_shape")
        if selected_shape in BLOCKED_ANSWER_SHAPES_V1:
            _append_unique(blocked_reason_labels, f"blocked_answer_shape_selected:{selected_shape}")
        else:
            _append_unique(blocked_reason_labels, f"unsupported_answer_shape:{selected_shape}")
    if plan.get("requested_user_intent_type") not in ALLOWED_USER_INTENT_TYPES_V1:
        _append_unique(invalid_fields, "requested_user_intent_type")
        _append_unique(blocked_reason_labels, f"unsupported_user_intent_type:{_safe_text(plan.get('requested_user_intent_type'))}")
    if not isinstance(plan.get("blocked_reason_labels", []), (list, tuple)):
        _append_unique(invalid_fields, "blocked_reason_labels")
        _append_unique(blocked_reason_labels, "blocked_reason_labels_not_list")
    unsafe = _detect_unsafe_metadata(plan)
    for reason in unsafe:
        _append_unique(blocked_reason_labels, reason)
    blocked = bool(missing or invalid_fields or blocked_reason_labels)
    return {
        "valid": not blocked,
        "blocked": blocked,
        "validation_status": "validation_pass_metadata_only" if not blocked else "blocked_invalid_or_unsafe_metadata_only",
        "missing_required_fields": missing,
        "invalid_fields": invalid_fields,
        "blocked_reason_labels": blocked_reason_labels,
        "json_safe": not bool(unsafe),
    }


def build_conversation_state_frame_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    denied_authority, denied_reasons = _validate_denied_authority(source.get("denied_authority", required_targeted_response_denied_authority_v1()))
    local_context_only = _safe_bool(source.get("local_context_only", True), True)
    raw_private_data_included = _safe_bool(source.get("raw_private_data_included", False))
    memory_claim_made = _safe_bool(source.get("memory_claim_made", False)) or _safe_bool(source.get("memory_claim", False))
    emotional_signal_label = _safe_text(source.get("emotional_signal_label", "neutral")).strip() or "neutral"
    result = {
        "schema_version": CONVERSATION_STATE_SCHEMA_VERSION_V1,
        "artifact_type": CONVERSATION_STATE_SCHEMA_VERSION_V1,
        "active_topic": _safe_text(source.get("active_topic", "")).strip(),
        "current_user_concern": _safe_text(source.get("current_user_concern", "")).strip(),
        "active_objective": _safe_text(source.get("active_objective", "")).strip(),
        "unresolved_question": _safe_text(source.get("unresolved_question", "")).strip(),
        "last_correction": _safe_text(source.get("last_correction", "")).strip(),
        "emotional_signal_label": emotional_signal_label,
        "relevant_boundary": _safe_text(source.get("relevant_boundary", "")).strip(),
        "safe_next_step": _safe_text(source.get("safe_next_step", "")).strip(),
        "local_context_only": local_context_only,
        "raw_private_data_included": raw_private_data_included,
        "memory_claim_made": memory_claim_made,
        "denied_authority": denied_authority,
        "validation_status": "validation_pass_metadata_only",
        "blocked_reason_labels": [],
    }
    reasons = denied_reasons + _detect_unsafe_metadata(result)
    if memory_claim_made:
        _append_unique(reasons, "memory_claim_made_true")
    if not local_context_only:
        _append_unique(reasons, "local_context_only_false")
    if raw_private_data_included:
        _append_unique(reasons, "raw_private_data_included_true")
    if reasons:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
        result["blocked_reason_labels"] = reasons
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def validate_conversation_state_frame_v1(frame: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "schema_version",
        "artifact_type",
        "active_topic",
        "current_user_concern",
        "active_objective",
        "unresolved_question",
        "last_correction",
        "emotional_signal_label",
        "relevant_boundary",
        "safe_next_step",
        "local_context_only",
        "raw_private_data_included",
        "denied_authority",
        "validation_status",
        "blocked_reason_labels",
    )
    if not isinstance(frame, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_only",
            "missing_required_fields": list(required_fields),
            "invalid_fields": ["frame"],
            "blocked_reason_labels": ["frame_not_mapping"],
            "json_safe": False,
        }
    missing = [field for field in required_fields if field not in frame]
    invalid_fields: list[str] = []
    blocked_reason_labels: list[str] = []
    if frame.get("schema_version") != CONVERSATION_STATE_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")
    if frame.get("artifact_type") != CONVERSATION_STATE_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "artifact_type")
        _append_unique(blocked_reason_labels, "artifact_type_mismatch")
    if not _safe_bool(frame.get("local_context_only", False)):
        _append_unique(invalid_fields, "local_context_only")
        _append_unique(blocked_reason_labels, "local_context_only_false")
    if _safe_bool(frame.get("raw_private_data_included", True)):
        _append_unique(invalid_fields, "raw_private_data_included")
        _append_unique(blocked_reason_labels, "raw_private_data_included_true")
    if _safe_bool(frame.get("memory_claim_made", False)) or _safe_bool(frame.get("memory_claim", False)):
        _append_unique(invalid_fields, "memory_claim_made")
        _append_unique(blocked_reason_labels, "memory_claim_made_true")
    denied_authority, authority_reasons = _validate_denied_authority(frame.get("denied_authority"))
    for reason in authority_reasons:
        _append_unique(blocked_reason_labels, reason)
    if denied_authority != required_targeted_response_denied_authority_v1():
        _append_unique(invalid_fields, "denied_authority")
    unsafe = _detect_unsafe_metadata(frame)
    for reason in unsafe:
        _append_unique(blocked_reason_labels, reason)
    blocked = bool(missing or invalid_fields or blocked_reason_labels)
    return {
        "valid": not blocked,
        "blocked": blocked,
        "validation_status": "validation_pass_metadata_only" if not blocked else "blocked_invalid_or_unsafe_metadata_only",
        "missing_required_fields": missing,
        "invalid_fields": invalid_fields,
        "blocked_reason_labels": blocked_reason_labels,
        "json_safe": not bool(unsafe),
    }


def build_current_user_concern_slot_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    result = {
        "schema_version": CURRENT_USER_CONCERN_SCHEMA_VERSION_V1,
        "artifact_type": CURRENT_USER_CONCERN_SCHEMA_VERSION_V1,
        "stated_task_label": _safe_text(source.get("stated_task_label", source.get("active_topic", ""))).strip(),
        "inferred_current_concern_label": _safe_text(source.get("inferred_current_concern_label", source.get("current_user_concern", ""))).strip(),
        "concern_evidence_label": _safe_text(source.get("concern_evidence_label", source.get("evidence_label", ""))).strip(),
        "local_context_only": _safe_bool(source.get("local_context_only", True), True),
        "memory_claim_made": _safe_bool(source.get("memory_claim_made", False)),
        "raw_private_data_included": _safe_bool(source.get("raw_private_data_included", False)),
        "validation_status": "validation_pass_metadata_only",
        "blocked_reason_labels": [],
    }
    reasons = _detect_unsafe_metadata(result)
    if not result["local_context_only"]:
        _append_unique(reasons, "local_context_only_false")
    if result["memory_claim_made"]:
        _append_unique(reasons, "memory_claim_made_true")
    if result["raw_private_data_included"]:
        _append_unique(reasons, "raw_private_data_included_true")
    if reasons:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
        result["blocked_reason_labels"] = reasons
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def validate_current_user_concern_slot_v1(slot: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "schema_version",
        "artifact_type",
        "stated_task_label",
        "inferred_current_concern_label",
        "concern_evidence_label",
        "local_context_only",
        "memory_claim_made",
        "raw_private_data_included",
        "validation_status",
        "blocked_reason_labels",
    )
    if not isinstance(slot, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_only",
            "missing_required_fields": list(required_fields),
            "invalid_fields": ["slot"],
            "blocked_reason_labels": ["slot_not_mapping"],
            "json_safe": False,
        }
    missing = [field for field in required_fields if field not in slot]
    invalid_fields: list[str] = []
    blocked_reason_labels: list[str] = []
    if slot.get("schema_version") != CURRENT_USER_CONCERN_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")
    if not _safe_bool(slot.get("local_context_only", False)):
        _append_unique(invalid_fields, "local_context_only")
        _append_unique(blocked_reason_labels, "local_context_only_false")
    if _safe_bool(slot.get("memory_claim_made", True)):
        _append_unique(invalid_fields, "memory_claim_made")
        _append_unique(blocked_reason_labels, "memory_claim_made_true")
    if _safe_bool(slot.get("raw_private_data_included", True)):
        _append_unique(invalid_fields, "raw_private_data_included")
        _append_unique(blocked_reason_labels, "raw_private_data_included_true")
    unsafe = _detect_unsafe_metadata(slot)
    for reason in unsafe:
        _append_unique(blocked_reason_labels, reason)
    blocked = bool(missing or invalid_fields or blocked_reason_labels)
    return {
        "valid": not blocked,
        "blocked": blocked,
        "validation_status": "validation_pass_metadata_only" if not blocked else "blocked_invalid_or_unsafe_metadata_only",
        "missing_required_fields": missing,
        "invalid_fields": invalid_fields,
        "blocked_reason_labels": blocked_reason_labels,
        "json_safe": not bool(unsafe),
    }


def build_recent_turn_recall_object_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    result = {
        "schema_version": RECENT_TURN_RECALL_SCHEMA_VERSION_V1,
        "artifact_type": RECENT_TURN_RECALL_SCHEMA_VERSION_V1,
        "recent_turn_id": _safe_text(source.get("recent_turn_id", "")).strip(),
        "recalled_point_label": _safe_text(source.get("recalled_point_label", source.get("current_point_label", ""))).strip(),
        "recall_scope": _safe_text(source.get("recall_scope", "local_recent_turn")).strip() or "local_recent_turn",
        "local_or_synthetic_only": _safe_bool(source.get("local_or_synthetic_only", True), True),
        "long_term_memory_claim": _safe_bool(source.get("long_term_memory_claim", False)),
        "raw_private_data_included": _safe_bool(source.get("raw_private_data_included", False)),
        "validation_status": "validation_pass_metadata_only",
        "blocked_reason_labels": [],
    }
    reasons = _detect_unsafe_metadata(result)
    if result["recall_scope"] not in ALLOWED_RECALL_SCOPES_V1:
        _append_unique(reasons, f"unsupported_recall_scope:{result['recall_scope']}")
    if not result["local_or_synthetic_only"]:
        _append_unique(reasons, "local_or_synthetic_only_false")
    if result["long_term_memory_claim"]:
        _append_unique(reasons, "long_term_memory_claim_true")
    if result["raw_private_data_included"]:
        _append_unique(reasons, "raw_private_data_included_true")
    if reasons:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
        result["blocked_reason_labels"] = reasons
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def validate_recent_turn_recall_object_v1(recall: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "schema_version",
        "artifact_type",
        "recent_turn_id",
        "recalled_point_label",
        "recall_scope",
        "local_or_synthetic_only",
        "long_term_memory_claim",
        "raw_private_data_included",
        "validation_status",
        "blocked_reason_labels",
    )
    if not isinstance(recall, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_only",
            "missing_required_fields": list(required_fields),
            "invalid_fields": ["recall"],
            "blocked_reason_labels": ["recall_not_mapping"],
            "json_safe": False,
        }
    missing = [field for field in required_fields if field not in recall]
    invalid_fields: list[str] = []
    blocked_reason_labels: list[str] = []
    if recall.get("schema_version") != RECENT_TURN_RECALL_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")
    if _safe_text(recall.get("recall_scope", "")).strip() not in ALLOWED_RECALL_SCOPES_V1:
        _append_unique(invalid_fields, "recall_scope")
        _append_unique(blocked_reason_labels, f"unsupported_recall_scope:{_safe_text(recall.get('recall_scope'))}")
    if not _safe_bool(recall.get("local_or_synthetic_only", False)):
        _append_unique(invalid_fields, "local_or_synthetic_only")
        _append_unique(blocked_reason_labels, "local_or_synthetic_only_false")
    if _safe_bool(recall.get("long_term_memory_claim", True)):
        _append_unique(invalid_fields, "long_term_memory_claim")
        _append_unique(blocked_reason_labels, "long_term_memory_claim_true")
    if _safe_bool(recall.get("raw_private_data_included", True)):
        _append_unique(invalid_fields, "raw_private_data_included")
        _append_unique(blocked_reason_labels, "raw_private_data_included_true")
    unsafe = _detect_unsafe_metadata(recall)
    for reason in unsafe:
        _append_unique(blocked_reason_labels, reason)
    blocked = bool(missing or invalid_fields or blocked_reason_labels)
    return {
        "valid": not blocked,
        "blocked": blocked,
        "validation_status": "validation_pass_metadata_only" if not blocked else "blocked_invalid_or_unsafe_metadata_only",
        "missing_required_fields": missing,
        "invalid_fields": invalid_fields,
        "blocked_reason_labels": blocked_reason_labels,
        "json_safe": not bool(unsafe),
    }


def build_goal_subgoal_conversation_frame_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    intent = _safe_text(source.get("user_intent_type", "unknown_or_blocked")).strip() or "unknown_or_blocked"
    result = {
        "schema_version": GOAL_SUBGOAL_SCHEMA_VERSION_V1,
        "artifact_type": GOAL_SUBGOAL_SCHEMA_VERSION_V1,
        "active_goal_label": _safe_text(source.get("active_goal_label", source.get("active_objective", ""))).strip(),
        "active_subgoal_label": _safe_text(source.get("active_subgoal_label", source.get("safe_next_step", ""))).strip(),
        "user_intent_type": intent,
        "requested_response_mode": _safe_text(source.get("requested_response_mode", source.get("answer_shape_family", ""))).strip(),
        "safe_next_step": _safe_text(source.get("safe_next_step", "")).strip(),
        "generic_fallback_risk": _safe_bool(source.get("generic_fallback_risk", False)),
        "validation_status": "validation_pass_metadata_only",
        "blocked_reason_labels": [],
    }
    reasons = _detect_unsafe_metadata(result)
    if result["user_intent_type"] not in ALLOWED_USER_INTENT_TYPES_V1:
        _append_unique(reasons, f"unsupported_user_intent_type:{result['user_intent_type']}")
    if result["generic_fallback_risk"]:
        _append_unique(reasons, "generic_fallback_risk_true")
    if reasons:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
        result["blocked_reason_labels"] = reasons
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def validate_goal_subgoal_conversation_frame_v1(frame: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "schema_version",
        "artifact_type",
        "active_goal_label",
        "active_subgoal_label",
        "user_intent_type",
        "requested_response_mode",
        "safe_next_step",
        "generic_fallback_risk",
        "validation_status",
        "blocked_reason_labels",
    )
    if not isinstance(frame, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_only",
            "missing_required_fields": list(required_fields),
            "invalid_fields": ["frame"],
            "blocked_reason_labels": ["frame_not_mapping"],
            "json_safe": False,
        }
    missing = [field for field in required_fields if field not in frame]
    invalid_fields: list[str] = []
    blocked_reason_labels: list[str] = []
    if frame.get("schema_version") != GOAL_SUBGOAL_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")
    if _safe_text(frame.get("user_intent_type", "")).strip() not in ALLOWED_USER_INTENT_TYPES_V1:
        _append_unique(invalid_fields, "user_intent_type")
        _append_unique(blocked_reason_labels, f"unsupported_user_intent_type:{_safe_text(frame.get('user_intent_type'))}")
    if _safe_bool(frame.get("generic_fallback_risk", False)):
        _append_unique(invalid_fields, "generic_fallback_risk")
        _append_unique(blocked_reason_labels, "generic_fallback_risk_true")
    unsafe = _detect_unsafe_metadata(frame)
    for reason in unsafe:
        _append_unique(blocked_reason_labels, reason)
    blocked = bool(missing or invalid_fields or blocked_reason_labels)
    return {
        "valid": not blocked,
        "blocked": blocked,
        "validation_status": "validation_pass_metadata_only" if not blocked else "blocked_invalid_or_unsafe_metadata_only",
        "missing_required_fields": missing,
        "invalid_fields": invalid_fields,
        "blocked_reason_labels": blocked_reason_labels,
        "json_safe": not bool(unsafe),
    }


def build_answer_shape_planner_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    selected_shape, _ = _intent_to_shape(source)
    result = {
        "schema_version": ANSWER_SHAPE_PLANNER_SCHEMA_VERSION_V1,
        "artifact_type": ANSWER_SHAPE_PLANNER_SCHEMA_VERSION_V1,
        "user_intent_type": _safe_text(source.get("user_intent_type", source.get("intent_type", "unknown_or_blocked"))).strip() or "unknown_or_blocked",
        "requested_user_intent_type": _safe_text(source.get("requested_user_intent_type", source.get("user_intent_type", source.get("intent_type", "unknown_or_blocked")))).strip() or "unknown_or_blocked",
        "boundary_label": _safe_text(source.get("boundary_label", "")).strip(),
        "current_user_concern_label": _safe_text(source.get("current_user_concern_label", source.get("concern_label", ""))).strip(),
        "last_correction_label": _safe_text(source.get("last_correction_label", source.get("last_correction", ""))).strip(),
        "provider_model_fallback_risk": _safe_bool(source.get("provider_model_fallback_risk", False)) or _safe_bool(source.get("fallback_risk_detected", False)),
        "fallback_risk_label": "provider_model_fallback_risk" if _safe_bool(source.get("provider_model_fallback_risk", False)) or _safe_bool(source.get("fallback_risk_detected", False)) else "none",
        "selected_answer_shape": selected_shape,
        "allowed_answer_shapes": list(ALLOWED_ANSWER_SHAPES_V1),
        "blocked_answer_shapes": list(BLOCKED_ANSWER_SHAPES_V1),
        "blocked_reason_labels": [],
        "validation_status": "validation_pass_metadata_only",
    }
    if selected_shape in BLOCKED_ANSWER_SHAPES_V1:
        _append_unique(result["blocked_reason_labels"], f"blocked_answer_shape_selected:{selected_shape}")
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
    unsafe = _detect_unsafe_metadata(result)
    for reason in unsafe:
        _append_unique(result["blocked_reason_labels"], reason)
    if unsafe:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def validate_answer_shape_plan_v1(plan: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "schema_version",
        "selected_answer_shape",
        "requested_user_intent_type",
        "boundary_label",
        "current_user_concern_label",
        "last_correction_label",
        "fallback_risk_label",
        "blocked_reason_labels",
        "validation_status",
    )
    if not isinstance(plan, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_only",
            "missing_required_fields": list(required_fields),
            "invalid_fields": ["plan"],
            "blocked_reason_labels": ["plan_not_mapping"],
            "json_safe": False,
        }
    missing = [field for field in required_fields if field not in plan]
    invalid_fields: list[str] = []
    blocked_reason_labels: list[str] = []
    if plan.get("schema_version") != ANSWER_SHAPE_PLANNER_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")
    selected_shape = _safe_text(plan.get("selected_answer_shape", "")).strip()
    if selected_shape not in ALLOWED_ANSWER_SHAPES_V1:
        _append_unique(invalid_fields, "selected_answer_shape")
        if selected_shape in BLOCKED_ANSWER_SHAPES_V1:
            _append_unique(blocked_reason_labels, f"blocked_answer_shape_selected:{selected_shape}")
        else:
            _append_unique(blocked_reason_labels, f"unsupported_answer_shape:{selected_shape}")
    if plan.get("requested_user_intent_type") not in ALLOWED_USER_INTENT_TYPES_V1:
        _append_unique(invalid_fields, "requested_user_intent_type")
        _append_unique(blocked_reason_labels, f"unsupported_user_intent_type:{_safe_text(plan.get('requested_user_intent_type'))}")
    if not isinstance(plan.get("blocked_reason_labels", []), (list, tuple)):
        _append_unique(invalid_fields, "blocked_reason_labels")
        _append_unique(blocked_reason_labels, "blocked_reason_labels_not_list")
    unsafe = _detect_unsafe_metadata(plan)
    for reason in unsafe:
        _append_unique(blocked_reason_labels, reason)
    blocked = bool(missing or invalid_fields or blocked_reason_labels)
    return {
        "valid": not blocked,
        "blocked": blocked,
        "validation_status": "validation_pass_metadata_only" if not blocked else "blocked_invalid_or_unsafe_metadata_only",
        "missing_required_fields": missing,
        "invalid_fields": invalid_fields,
        "blocked_reason_labels": blocked_reason_labels,
        "json_safe": not bool(unsafe),
    }


def build_conversation_state_frame_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    denied_authority, denied_reasons = _validate_denied_authority(source.get("denied_authority", required_targeted_response_denied_authority_v1()))
    local_context_only = _safe_bool(source.get("local_context_only", True), True)
    raw_private_data_included = _safe_bool(source.get("raw_private_data_included", False))
    memory_claim_made = _safe_bool(source.get("memory_claim_made", False)) or _safe_bool(source.get("memory_claim", False))
    emotional_signal_label = _safe_text(source.get("emotional_signal_label", "neutral")).strip() or "neutral"
    result = {
        "schema_version": CONVERSATION_STATE_SCHEMA_VERSION_V1,
        "artifact_type": CONVERSATION_STATE_SCHEMA_VERSION_V1,
        "active_topic": _safe_text(source.get("active_topic", "")).strip(),
        "current_user_concern": _safe_text(source.get("current_user_concern", "")).strip(),
        "active_objective": _safe_text(source.get("active_objective", "")).strip(),
        "unresolved_question": _safe_text(source.get("unresolved_question", "")).strip(),
        "last_correction": _safe_text(source.get("last_correction", "")).strip(),
        "emotional_signal_label": emotional_signal_label,
        "relevant_boundary": _safe_text(source.get("relevant_boundary", "")).strip(),
        "safe_next_step": _safe_text(source.get("safe_next_step", "")).strip(),
        "local_context_only": local_context_only,
        "raw_private_data_included": raw_private_data_included,
        "memory_claim_made": memory_claim_made,
        "denied_authority": denied_authority,
        "validation_status": "validation_pass_metadata_only",
        "blocked_reason_labels": [],
    }
    reasons = denied_reasons + _detect_unsafe_metadata(result)
    if memory_claim_made:
        _append_unique(reasons, "memory_claim_made_true")
    if not local_context_only:
        _append_unique(reasons, "local_context_only_false")
    if raw_private_data_included:
        _append_unique(reasons, "raw_private_data_included_true")
    if reasons:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
        result["blocked_reason_labels"] = reasons
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def validate_conversation_state_frame_v1(frame: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "schema_version",
        "artifact_type",
        "active_topic",
        "current_user_concern",
        "active_objective",
        "unresolved_question",
        "last_correction",
        "emotional_signal_label",
        "relevant_boundary",
        "safe_next_step",
        "local_context_only",
        "raw_private_data_included",
        "denied_authority",
        "validation_status",
        "blocked_reason_labels",
    )
    if not isinstance(frame, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_only",
            "missing_required_fields": list(required_fields),
            "invalid_fields": ["frame"],
            "blocked_reason_labels": ["frame_not_mapping"],
            "json_safe": False,
        }
    missing = [field for field in required_fields if field not in frame]
    invalid_fields: list[str] = []
    blocked_reason_labels: list[str] = []
    if frame.get("schema_version") != CONVERSATION_STATE_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")
    if frame.get("artifact_type") != CONVERSATION_STATE_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "artifact_type")
        _append_unique(blocked_reason_labels, "artifact_type_mismatch")
    if not _safe_bool(frame.get("local_context_only", False)):
        _append_unique(invalid_fields, "local_context_only")
        _append_unique(blocked_reason_labels, "local_context_only_false")
    if _safe_bool(frame.get("raw_private_data_included", True)):
        _append_unique(invalid_fields, "raw_private_data_included")
        _append_unique(blocked_reason_labels, "raw_private_data_included_true")
    if _safe_bool(frame.get("memory_claim_made", False)) or _safe_bool(frame.get("memory_claim", False)):
        _append_unique(invalid_fields, "memory_claim_made")
        _append_unique(blocked_reason_labels, "memory_claim_made_true")
    denied_authority, authority_reasons = _validate_denied_authority(frame.get("denied_authority"))
    for reason in authority_reasons:
        _append_unique(blocked_reason_labels, reason)
    if denied_authority != required_targeted_response_denied_authority_v1():
        _append_unique(invalid_fields, "denied_authority")
    unsafe = _detect_unsafe_metadata(frame)
    for reason in unsafe:
        _append_unique(blocked_reason_labels, reason)
    blocked = bool(missing or invalid_fields or blocked_reason_labels)
    return {
        "valid": not blocked,
        "blocked": blocked,
        "validation_status": "validation_pass_metadata_only" if not blocked else "blocked_invalid_or_unsafe_metadata_only",
        "missing_required_fields": missing,
        "invalid_fields": invalid_fields,
        "blocked_reason_labels": blocked_reason_labels,
        "json_safe": not bool(unsafe),
    }


def build_current_user_concern_slot_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    result = {
        "schema_version": CURRENT_USER_CONCERN_SCHEMA_VERSION_V1,
        "artifact_type": CURRENT_USER_CONCERN_SCHEMA_VERSION_V1,
        "stated_task_label": _safe_text(source.get("stated_task_label", source.get("active_topic", ""))).strip(),
        "inferred_current_concern_label": _safe_text(source.get("inferred_current_concern_label", source.get("current_user_concern", ""))).strip(),
        "concern_evidence_label": _safe_text(source.get("concern_evidence_label", source.get("evidence_label", ""))).strip(),
        "local_context_only": _safe_bool(source.get("local_context_only", True), True),
        "memory_claim_made": _safe_bool(source.get("memory_claim_made", False)),
        "raw_private_data_included": _safe_bool(source.get("raw_private_data_included", False)),
        "validation_status": "validation_pass_metadata_only",
        "blocked_reason_labels": [],
    }
    reasons = _detect_unsafe_metadata(result)
    if not result["local_context_only"]:
        _append_unique(reasons, "local_context_only_false")
    if result["memory_claim_made"]:
        _append_unique(reasons, "memory_claim_made_true")
    if result["raw_private_data_included"]:
        _append_unique(reasons, "raw_private_data_included_true")
    if reasons:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
        result["blocked_reason_labels"] = reasons
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def validate_current_user_concern_slot_v1(slot: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "schema_version",
        "artifact_type",
        "stated_task_label",
        "inferred_current_concern_label",
        "concern_evidence_label",
        "local_context_only",
        "memory_claim_made",
        "raw_private_data_included",
        "validation_status",
        "blocked_reason_labels",
    )
    if not isinstance(slot, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_only",
            "missing_required_fields": list(required_fields),
            "invalid_fields": ["slot"],
            "blocked_reason_labels": ["slot_not_mapping"],
            "json_safe": False,
        }
    missing = [field for field in required_fields if field not in slot]
    invalid_fields: list[str] = []
    blocked_reason_labels: list[str] = []
    if slot.get("schema_version") != CURRENT_USER_CONCERN_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")
    if not _safe_bool(slot.get("local_context_only", False)):
        _append_unique(invalid_fields, "local_context_only")
        _append_unique(blocked_reason_labels, "local_context_only_false")
    if _safe_bool(slot.get("memory_claim_made", True)):
        _append_unique(invalid_fields, "memory_claim_made")
        _append_unique(blocked_reason_labels, "memory_claim_made_true")
    if _safe_bool(slot.get("raw_private_data_included", True)):
        _append_unique(invalid_fields, "raw_private_data_included")
        _append_unique(blocked_reason_labels, "raw_private_data_included_true")
    unsafe = _detect_unsafe_metadata(slot)
    for reason in unsafe:
        _append_unique(blocked_reason_labels, reason)
    blocked = bool(missing or invalid_fields or blocked_reason_labels)
    return {
        "valid": not blocked,
        "blocked": blocked,
        "validation_status": "validation_pass_metadata_only" if not blocked else "blocked_invalid_or_unsafe_metadata_only",
        "missing_required_fields": missing,
        "invalid_fields": invalid_fields,
        "blocked_reason_labels": blocked_reason_labels,
        "json_safe": not bool(unsafe),
    }


def build_recent_turn_recall_object_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    result = {
        "schema_version": RECENT_TURN_RECALL_SCHEMA_VERSION_V1,
        "artifact_type": RECENT_TURN_RECALL_SCHEMA_VERSION_V1,
        "recent_turn_id": _safe_text(source.get("recent_turn_id", "")).strip(),
        "recalled_point_label": _safe_text(source.get("recalled_point_label", source.get("current_point_label", ""))).strip(),
        "recall_scope": _safe_text(source.get("recall_scope", "local_recent_turn")).strip() or "local_recent_turn",
        "local_or_synthetic_only": _safe_bool(source.get("local_or_synthetic_only", True), True),
        "long_term_memory_claim": _safe_bool(source.get("long_term_memory_claim", False)),
        "raw_private_data_included": _safe_bool(source.get("raw_private_data_included", False)),
        "validation_status": "validation_pass_metadata_only",
        "blocked_reason_labels": [],
    }
    reasons = _detect_unsafe_metadata(result)
    if result["recall_scope"] not in ALLOWED_RECALL_SCOPES_V1:
        _append_unique(reasons, f"unsupported_recall_scope:{result['recall_scope']}")
    if not result["local_or_synthetic_only"]:
        _append_unique(reasons, "local_or_synthetic_only_false")
    if result["long_term_memory_claim"]:
        _append_unique(reasons, "long_term_memory_claim_true")
    if result["raw_private_data_included"]:
        _append_unique(reasons, "raw_private_data_included_true")
    if reasons:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
        result["blocked_reason_labels"] = reasons
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def validate_recent_turn_recall_object_v1(recall: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "schema_version",
        "artifact_type",
        "recent_turn_id",
        "recalled_point_label",
        "recall_scope",
        "local_or_synthetic_only",
        "long_term_memory_claim",
        "raw_private_data_included",
        "validation_status",
        "blocked_reason_labels",
    )
    if not isinstance(recall, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_only",
            "missing_required_fields": list(required_fields),
            "invalid_fields": ["recall"],
            "blocked_reason_labels": ["recall_not_mapping"],
            "json_safe": False,
        }
    missing = [field for field in required_fields if field not in recall]
    invalid_fields: list[str] = []
    blocked_reason_labels: list[str] = []
    if recall.get("schema_version") != RECENT_TURN_RECALL_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")
    if _safe_text(recall.get("recall_scope", "")).strip() not in ALLOWED_RECALL_SCOPES_V1:
        _append_unique(invalid_fields, "recall_scope")
        _append_unique(blocked_reason_labels, f"unsupported_recall_scope:{_safe_text(recall.get('recall_scope'))}")
    if not _safe_bool(recall.get("local_or_synthetic_only", False)):
        _append_unique(invalid_fields, "local_or_synthetic_only")
        _append_unique(blocked_reason_labels, "local_or_synthetic_only_false")
    if _safe_bool(recall.get("long_term_memory_claim", True)):
        _append_unique(invalid_fields, "long_term_memory_claim")
        _append_unique(blocked_reason_labels, "long_term_memory_claim_true")
    if _safe_bool(recall.get("raw_private_data_included", True)):
        _append_unique(invalid_fields, "raw_private_data_included")
        _append_unique(blocked_reason_labels, "raw_private_data_included_true")
    unsafe = _detect_unsafe_metadata(recall)
    for reason in unsafe:
        _append_unique(blocked_reason_labels, reason)
    blocked = bool(missing or invalid_fields or blocked_reason_labels)
    return {
        "valid": not blocked,
        "blocked": blocked,
        "validation_status": "validation_pass_metadata_only" if not blocked else "blocked_invalid_or_unsafe_metadata_only",
        "missing_required_fields": missing,
        "invalid_fields": invalid_fields,
        "blocked_reason_labels": blocked_reason_labels,
        "json_safe": not bool(unsafe),
    }


def build_goal_subgoal_conversation_frame_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    intent = _safe_text(source.get("user_intent_type", "unknown_or_blocked")).strip() or "unknown_or_blocked"
    result = {
        "schema_version": GOAL_SUBGOAL_SCHEMA_VERSION_V1,
        "artifact_type": GOAL_SUBGOAL_SCHEMA_VERSION_V1,
        "active_goal_label": _safe_text(source.get("active_goal_label", source.get("active_objective", ""))).strip(),
        "active_subgoal_label": _safe_text(source.get("active_subgoal_label", source.get("safe_next_step", ""))).strip(),
        "user_intent_type": intent,
        "requested_response_mode": _safe_text(source.get("requested_response_mode", source.get("answer_shape_family", ""))).strip(),
        "safe_next_step": _safe_text(source.get("safe_next_step", "")).strip(),
        "generic_fallback_risk": _safe_bool(source.get("generic_fallback_risk", False)),
        "validation_status": "validation_pass_metadata_only",
        "blocked_reason_labels": [],
    }
    reasons = _detect_unsafe_metadata(result)
    if result["user_intent_type"] not in ALLOWED_USER_INTENT_TYPES_V1:
        _append_unique(reasons, f"unsupported_user_intent_type:{result['user_intent_type']}")
    if result["generic_fallback_risk"]:
        _append_unique(reasons, "generic_fallback_risk_true")
    if reasons:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
        result["blocked_reason_labels"] = reasons
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def validate_goal_subgoal_conversation_frame_v1(frame: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "schema_version",
        "artifact_type",
        "active_goal_label",
        "active_subgoal_label",
        "user_intent_type",
        "requested_response_mode",
        "safe_next_step",
        "generic_fallback_risk",
        "validation_status",
        "blocked_reason_labels",
    )
    if not isinstance(frame, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_only",
            "missing_required_fields": list(required_fields),
            "invalid_fields": ["frame"],
            "blocked_reason_labels": ["frame_not_mapping"],
            "json_safe": False,
        }
    missing = [field for field in required_fields if field not in frame]
    invalid_fields: list[str] = []
    blocked_reason_labels: list[str] = []
    if frame.get("schema_version") != GOAL_SUBGOAL_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")
    if _safe_text(frame.get("user_intent_type", "")).strip() not in ALLOWED_USER_INTENT_TYPES_V1:
        _append_unique(invalid_fields, "user_intent_type")
        _append_unique(blocked_reason_labels, f"unsupported_user_intent_type:{_safe_text(frame.get('user_intent_type'))}")
    if _safe_bool(frame.get("generic_fallback_risk", False)):
        _append_unique(invalid_fields, "generic_fallback_risk")
        _append_unique(blocked_reason_labels, "generic_fallback_risk_true")
    unsafe = _detect_unsafe_metadata(frame)
    for reason in unsafe:
        _append_unique(blocked_reason_labels, reason)
    blocked = bool(missing or invalid_fields or blocked_reason_labels)
    return {
        "valid": not blocked,
        "blocked": blocked,
        "validation_status": "validation_pass_metadata_only" if not blocked else "blocked_invalid_or_unsafe_metadata_only",
        "missing_required_fields": missing,
        "invalid_fields": invalid_fields,
        "blocked_reason_labels": blocked_reason_labels,
        "json_safe": not bool(unsafe),
    }


def build_answer_shape_planner_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    selected_shape, _ = _intent_to_shape(source)
    result = {
        "schema_version": ANSWER_SHAPE_PLANNER_SCHEMA_VERSION_V1,
        "artifact_type": ANSWER_SHAPE_PLANNER_SCHEMA_VERSION_V1,
        "user_intent_type": _safe_text(source.get("user_intent_type", source.get("intent_type", "unknown_or_blocked"))).strip() or "unknown_or_blocked",
        "requested_user_intent_type": _safe_text(source.get("requested_user_intent_type", source.get("user_intent_type", source.get("intent_type", "unknown_or_blocked")))).strip() or "unknown_or_blocked",
        "boundary_label": _safe_text(source.get("boundary_label", "")).strip(),
        "current_user_concern_label": _safe_text(source.get("current_user_concern_label", source.get("concern_label", ""))).strip(),
        "last_correction_label": _safe_text(source.get("last_correction_label", source.get("last_correction", ""))).strip(),
        "provider_model_fallback_risk": _safe_bool(source.get("provider_model_fallback_risk", False)) or _safe_bool(source.get("fallback_risk_detected", False)),
        "fallback_risk_label": "provider_model_fallback_risk" if _safe_bool(source.get("provider_model_fallback_risk", False)) or _safe_bool(source.get("fallback_risk_detected", False)) else "none",
        "selected_answer_shape": selected_shape,
        "allowed_answer_shapes": list(ALLOWED_ANSWER_SHAPES_V1),
        "blocked_answer_shapes": list(BLOCKED_ANSWER_SHAPES_V1),
        "blocked_reason_labels": [],
        "validation_status": "validation_pass_metadata_only",
    }
    if selected_shape in BLOCKED_ANSWER_SHAPES_V1:
        _append_unique(result["blocked_reason_labels"], f"blocked_answer_shape_selected:{selected_shape}")
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
    unsafe = _detect_unsafe_metadata(result)
    for reason in unsafe:
        _append_unique(result["blocked_reason_labels"], reason)
    if unsafe:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def validate_answer_shape_plan_v1(plan: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "schema_version",
        "selected_answer_shape",
        "requested_user_intent_type",
        "boundary_label",
        "current_user_concern_label",
        "last_correction_label",
        "fallback_risk_label",
        "blocked_reason_labels",
        "validation_status",
    )
    if not isinstance(plan, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_only",
            "missing_required_fields": list(required_fields),
            "invalid_fields": ["plan"],
            "blocked_reason_labels": ["plan_not_mapping"],
            "json_safe": False,
        }
    missing = [field for field in required_fields if field not in plan]
    invalid_fields: list[str] = []
    blocked_reason_labels: list[str] = []
    if plan.get("schema_version") != ANSWER_SHAPE_PLANNER_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")
    selected_shape = _safe_text(plan.get("selected_answer_shape", "")).strip()
    if selected_shape not in ALLOWED_ANSWER_SHAPES_V1:
        _append_unique(invalid_fields, "selected_answer_shape")
        if selected_shape in BLOCKED_ANSWER_SHAPES_V1:
            _append_unique(blocked_reason_labels, f"blocked_answer_shape_selected:{selected_shape}")
        else:
            _append_unique(blocked_reason_labels, f"unsupported_answer_shape:{selected_shape}")
    if plan.get("requested_user_intent_type") not in ALLOWED_USER_INTENT_TYPES_V1:
        _append_unique(invalid_fields, "requested_user_intent_type")
        _append_unique(blocked_reason_labels, f"unsupported_user_intent_type:{_safe_text(plan.get('requested_user_intent_type'))}")
    if not isinstance(plan.get("blocked_reason_labels", []), (list, tuple)):
        _append_unique(invalid_fields, "blocked_reason_labels")
        _append_unique(blocked_reason_labels, "blocked_reason_labels_not_list")
    unsafe = _detect_unsafe_metadata(plan)
    for reason in unsafe:
        _append_unique(blocked_reason_labels, reason)
    blocked = bool(missing or invalid_fields or blocked_reason_labels)
    return {
        "valid": not blocked,
        "blocked": blocked,
        "validation_status": "validation_pass_metadata_only" if not blocked else "blocked_invalid_or_unsafe_metadata_only",
        "missing_required_fields": missing,
        "invalid_fields": invalid_fields,
        "blocked_reason_labels": blocked_reason_labels,
        "json_safe": not bool(unsafe),
    }


def select_concrete_next_step_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    safe_next_step = _safe_text(source.get("safe_next_step", source.get("selected_next_step_label", ""))).strip()
    boundary_preserved = True
    blocked_reason_labels: list[str] = []
    if not safe_next_step:
        boundary_preserved = False
        _append_unique(blocked_reason_labels, "safe_next_step_missing")
    if _safe_bool(source.get("execution_claim_made", False)):
        boundary_preserved = False
        _append_unique(blocked_reason_labels, "execution_claim_made_true")
    result = {
        "schema_version": CONCRETE_NEXT_STEP_SCHEMA_VERSION_V1,
        "artifact_type": CONCRETE_NEXT_STEP_SCHEMA_VERSION_V1,
        "selected_next_step_label": safe_next_step,
        "why_selected": _safe_text(source.get("why_selected", source.get("selection_rationale_label", ""))).strip(),
        "boundary_preserved": boundary_preserved,
        "execution_claim_made": False,
        "validation_status": "validation_pass_metadata_only" if boundary_preserved else "blocked_invalid_or_unsafe_metadata_only",
        "blocked_reason_labels": blocked_reason_labels,
    }
    unsafe = _detect_unsafe_metadata(result)
    for reason in unsafe:
        _append_unique(result["blocked_reason_labels"], reason)
    if unsafe:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def validate_concrete_next_step_selector_v1(selector: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "schema_version",
        "artifact_type",
        "selected_next_step_label",
        "why_selected",
        "boundary_preserved",
        "execution_claim_made",
        "validation_status",
        "blocked_reason_labels",
    )
    if not isinstance(selector, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_only",
            "missing_required_fields": list(required_fields),
            "invalid_fields": ["selector"],
            "blocked_reason_labels": ["selector_not_mapping"],
            "json_safe": False,
        }
    missing = [field for field in required_fields if field not in selector]
    invalid_fields: list[str] = []
    blocked_reason_labels: list[str] = []
    if selector.get("schema_version") != CONCRETE_NEXT_STEP_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")
    if _safe_bool(selector.get("execution_claim_made", True)):
        _append_unique(invalid_fields, "execution_claim_made")
        _append_unique(blocked_reason_labels, "execution_claim_made_true")
    if not _safe_bool(selector.get("boundary_preserved", False)):
        _append_unique(invalid_fields, "boundary_preserved")
        _append_unique(blocked_reason_labels, "boundary_not_preserved")
    unsafe = _detect_unsafe_metadata(selector)
    for reason in unsafe:
        _append_unique(blocked_reason_labels, reason)
    blocked = bool(missing or invalid_fields or blocked_reason_labels)
    return {
        "valid": not blocked,
        "blocked": blocked,
        "validation_status": "validation_pass_metadata_only" if not blocked else "blocked_invalid_or_unsafe_metadata_only",
        "missing_required_fields": missing,
        "invalid_fields": invalid_fields,
        "blocked_reason_labels": blocked_reason_labels,
        "json_safe": not bool(unsafe),
    }


def apply_non_cannedness_pressure_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    repeated_answer_skeleton_risk = _safe_bool(source.get("repeated_answer_skeleton_risk", False))
    generic_checklist_risk = _safe_bool(source.get("generic_checklist_risk", False))
    current_turn_specificity_required = _safe_bool(source.get("current_turn_specificity_required", True), True)
    user_concern_anchor_required = _safe_bool(source.get("user_concern_anchor_required", True), True)
    concrete_next_step_required = _safe_bool(source.get("concrete_next_step_required", False))
    pressure_applied = repeated_answer_skeleton_risk or generic_checklist_risk or current_turn_specificity_required or user_concern_anchor_required or concrete_next_step_required
    result = {
        "schema_version": NON_CANNEDNESS_SCHEMA_VERSION_V1,
        "artifact_type": NON_CANNEDNESS_SCHEMA_VERSION_V1,
        "repeated_answer_skeleton_risk": repeated_answer_skeleton_risk,
        "generic_checklist_risk": generic_checklist_risk,
        "current_turn_specificity_required": current_turn_specificity_required,
        "user_concern_anchor_required": user_concern_anchor_required,
        "concrete_next_step_required": concrete_next_step_required,
        "pressure_applied": pressure_applied,
        "validation_status": "validation_pass_metadata_only",
        "blocked_reason_labels": [],
    }
    if not pressure_applied:
        _append_unique(result["blocked_reason_labels"], "non_cannedness_pressure_not_applied")
    unsafe = _detect_unsafe_metadata(result)
    for reason in unsafe:
        _append_unique(result["blocked_reason_labels"], reason)
    if unsafe:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def select_response_shape_diversity_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    previous_family = _safe_text(source.get("previous_shape_family", "")).strip() or "none"
    selected_shape = _safe_text(source.get("allowed_shape", source.get("selected_answer_shape", "direct_answer_with_boundary"))).strip() or "direct_answer_with_boundary"
    if selected_shape not in ALLOWED_ANSWER_SHAPES_V1:
        selected_shape = "direct_answer_with_boundary"
    family_map = {
        "direct_answer_with_boundary": "direct",
        "tradeoff_reasoning": "reasoning",
        "concrete_next_step": "action",
        "correction_repair": "repair",
        "refusal_with_useful_alternative": "refusal",
        "reassurance_with_reasoning": "reassurance",
        "planning_with_constraints": "planning",
        "explanation_of_limits": "limits",
        "ask_one_clarifying_question_only_when_needed": "clarification",
    }
    selected_family = family_map[selected_shape]
    blocked_reason_labels: list[str] = []
    diversity_pressure_applied = selected_family == previous_family
    if diversity_pressure_applied:
        _append_unique(blocked_reason_labels, "repeat_shape_family_risk")
    result = {
        "schema_version": RESPONSE_SHAPE_DIVERSITY_SCHEMA_VERSION_V1,
        "artifact_type": RESPONSE_SHAPE_DIVERSITY_SCHEMA_VERSION_V1,
        "selected_shape_family": selected_family,
        "previous_shape_family": previous_family,
        "diversity_pressure_applied": diversity_pressure_applied,
        "allowed_shape": selected_shape,
        "blocked_reason_labels": blocked_reason_labels,
        "validation_status": "validation_pass_metadata_only" if not blocked_reason_labels else "blocked_invalid_or_unsafe_metadata_only",
    }
    unsafe = _detect_unsafe_metadata(result)
    for reason in unsafe:
        _append_unique(result["blocked_reason_labels"], reason)
    if unsafe:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def integrate_empathy_concern_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    concern_label = _safe_text(source.get("concern_label", source.get("current_user_concern_label", ""))).strip()
    emotional_signal_label = _safe_text(source.get("emotional_signal_label", "neutral")).strip() or "neutral"
    acknowledgement_strategy_label = _safe_text(source.get("acknowledgement_strategy_label", "acknowledge_concern_and_help")).strip() or "acknowledge_concern_and_help"
    fake_emotion_claim = _safe_bool(source.get("fake_emotion_claim", False))
    diagnosis_claim = _safe_bool(source.get("diagnosis_claim", False))
    over_personalization_risk = _safe_bool(source.get("over_personalization_risk", False)) or bool(concern_label and acknowledgement_strategy_label == "over_personalize")
    result = {
        "schema_version": EMPATHY_CONCERN_SCHEMA_VERSION_V1,
        "artifact_type": EMPATHY_CONCERN_SCHEMA_VERSION_V1,
        "concern_label": concern_label,
        "emotional_signal_label": emotional_signal_label,
        "acknowledgement_strategy_label": acknowledgement_strategy_label,
        "fake_emotion_claim": fake_emotion_claim,
        "diagnosis_claim": diagnosis_claim,
        "over_personalization_risk": over_personalization_risk,
        "validation_status": "validation_pass_metadata_only",
        "blocked_reason_labels": [],
    }
    if fake_emotion_claim:
        _append_unique(result["blocked_reason_labels"], "fake_emotion_claim_true")
    if diagnosis_claim:
        _append_unique(result["blocked_reason_labels"], "diagnosis_claim_true")
    if over_personalization_risk:
        _append_unique(result["blocked_reason_labels"], "over_personalization_risk_true")
    unsafe = _detect_unsafe_metadata(result)
    for reason in unsafe:
        _append_unique(result["blocked_reason_labels"], reason)
    if result["blocked_reason_labels"]:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def run_response_self_check_before_final_answer_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    answers_current_prompt = _safe_bool(source.get("answers_current_prompt", True), True)
    uses_relevant_local_context_when_needed = _safe_bool(source.get("uses_relevant_local_context_when_needed", True), True)
    too_vague = _safe_bool(source.get("too_vague", False))
    too_generic = _safe_bool(source.get("too_generic", False))
    too_safety_heavy = _safe_bool(source.get("too_safety_heavy", False))
    overclaims = _safe_bool(source.get("overclaims", False))
    memory_claim_without_evidence = _safe_bool(source.get("memory_claim_without_evidence", False))
    provider_fallback_risk = _safe_bool(source.get("provider_fallback_risk", False))
    recommended_repair_labels: list[str] = []
    if not answers_current_prompt:
        _append_unique(recommended_repair_labels, "answer_current_prompt")
    if not uses_relevant_local_context_when_needed:
        _append_unique(recommended_repair_labels, "use_relevant_local_context")
    if too_vague:
        _append_unique(recommended_repair_labels, "increase_specificity")
    if too_generic:
        _append_unique(recommended_repair_labels, "remove_generic_skeleton")
    if too_safety_heavy:
        _append_unique(recommended_repair_labels, "relax_safety_only_response")
    if overclaims:
        _append_unique(recommended_repair_labels, "remove_overclaim")
    if memory_claim_without_evidence:
        _append_unique(recommended_repair_labels, "remove_memory_claim")
    if provider_fallback_risk:
        _append_unique(recommended_repair_labels, "route_to_fallback_gate")
    final_answer_generated = False
    result = {
        "schema_version": RESPONSE_SELF_CHECK_SCHEMA_VERSION_V1,
        "artifact_type": RESPONSE_SELF_CHECK_SCHEMA_VERSION_V1,
        "answers_current_prompt": answers_current_prompt,
        "uses_relevant_local_context_when_needed": uses_relevant_local_context_when_needed,
        "too_vague": too_vague,
        "too_generic": too_generic,
        "too_safety_heavy": too_safety_heavy,
        "overclaims": overclaims,
        "memory_claim_without_evidence": memory_claim_without_evidence,
        "provider_fallback_risk": provider_fallback_risk,
        "recommended_repair_labels": recommended_repair_labels,
        "final_answer_generated": final_answer_generated,
        "validation_status": "validation_pass_metadata_only",
        "blocked_reason_labels": [],
    }
    if not answers_current_prompt:
        _append_unique(result["blocked_reason_labels"], "does_not_answer_current_prompt")
    if too_vague:
        _append_unique(result["blocked_reason_labels"], "too_vague")
    if too_generic:
        _append_unique(result["blocked_reason_labels"], "too_generic")
    if too_safety_heavy:
        _append_unique(result["blocked_reason_labels"], "too_safety_heavy")
    if overclaims:
        _append_unique(result["blocked_reason_labels"], "overclaims_true")
    if memory_claim_without_evidence:
        _append_unique(result["blocked_reason_labels"], "memory_claim_without_evidence_true")
    if provider_fallback_risk:
        _append_unique(result["blocked_reason_labels"], "provider_fallback_risk_true")
    if final_answer_generated:
        _append_unique(result["blocked_reason_labels"], "final_answer_generated_true")
    unsafe = _detect_unsafe_metadata(result)
    for reason in unsafe:
        _append_unique(result["blocked_reason_labels"], reason)
    if result["blocked_reason_labels"]:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def apply_directness_pressure_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    vague_language_detected = _safe_bool(source.get("vague_language_detected", False)) or _safe_text(source.get("response_language_label", "direct")).strip() != "direct"
    directness_needed = _safe_bool(source.get("directness_needed", True), True)
    directness_pressure_applied = directness_needed or vague_language_detected
    result = {
        "schema_version": DIRECTNESS_SCHEMA_VERSION_V1,
        "artifact_type": DIRECTNESS_SCHEMA_VERSION_V1,
        "directness_needed": directness_needed,
        "vague_language_detected": vague_language_detected,
        "directness_pressure_applied": directness_pressure_applied,
        "uncertainty_preserved": _safe_bool(source.get("uncertainty_preserved", True), True),
        "validation_status": "validation_pass_metadata_only",
        "blocked_reason_labels": [],
    }
    if vague_language_detected:
        _append_unique(result["blocked_reason_labels"], "vague_language_detected_true")
    unsafe = _detect_unsafe_metadata(result)
    for reason in unsafe:
        _append_unique(result["blocked_reason_labels"], reason)
    if unsafe:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def calibrate_boundary_specific_authority_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    boundary_label = _safe_text(source.get("boundary_label", "")).strip()
    can_explain = _safe_bool(source.get("can_explain", True), True)
    can_design = _safe_bool(source.get("can_design", True), True)
    can_execute = _safe_bool(source.get("can_execute", False))
    can_claim_real_memory = _safe_bool(source.get("can_claim_real_memory", False))
    can_claim_public_readiness = _safe_bool(source.get("can_claim_public_readiness", False))
    can_claim_deletion_completed = _safe_bool(source.get("can_claim_deletion_completed", False))
    safe_authority_phrase_label = _safe_text(source.get("safe_authority_phrase_label", "explain_and_design_only")).strip() or "explain_and_design_only"
    blocked_authority_labels: list[str] = []
    if can_execute:
        _append_unique(blocked_authority_labels, "can_execute_true")
    if can_claim_real_memory:
        _append_unique(blocked_authority_labels, "can_claim_real_memory_true")
    if can_claim_public_readiness:
        _append_unique(blocked_authority_labels, "can_claim_public_readiness_true")
    if can_claim_deletion_completed:
        _append_unique(blocked_authority_labels, "can_claim_deletion_completed_true")
    result = {
        "schema_version": AUTHORITY_CALIBRATION_SCHEMA_VERSION_V1,
        "artifact_type": AUTHORITY_CALIBRATION_SCHEMA_VERSION_V1,
        "boundary_label": boundary_label,
        "can_explain": can_explain,
        "can_design": can_design,
        "can_execute": can_execute,
        "can_claim_real_memory": can_claim_real_memory,
        "can_claim_public_readiness": can_claim_public_readiness,
        "can_claim_deletion_completed": can_claim_deletion_completed,
        "safe_authority_phrase_label": safe_authority_phrase_label,
        "blocked_authority_labels": blocked_authority_labels,
        "validation_status": "validation_pass_metadata_only",
    }
    unsafe = _detect_unsafe_metadata(result)
    for reason in unsafe:
        _append_unique(blocked_authority_labels, reason)
    if blocked_authority_labels:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def gate_boundary_specific_fallback_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    fallback_risk_label = _safe_text(source.get("fallback_risk_label", "none")).strip() or "none"
    provider_model_path_detected = _safe_bool(source.get("provider_model_path_detected", False))
    search_advisor_path_detected = _safe_bool(source.get("search_advisor_path_detected", False))
    local_safe_alternative_available = _safe_bool(source.get("local_safe_alternative_available", True), True)
    should_stop = not local_safe_alternative_available
    safe_next_lane_label = _safe_text(source.get("safe_next_lane_label", "AWAIT_OPERATOR_DECISION")).strip() or "AWAIT_OPERATOR_DECISION"
    blocked_reason_labels: list[str] = []
    if provider_model_path_detected:
        _append_unique(blocked_reason_labels, "provider_model_path_detected_true")
    if search_advisor_path_detected:
        _append_unique(blocked_reason_labels, "search_advisor_path_detected_true")
    if should_stop:
        _append_unique(blocked_reason_labels, "local_safe_alternative_unavailable")
    result = {
        "schema_version": FALLBACK_GATING_SCHEMA_VERSION_V1,
        "artifact_type": FALLBACK_GATING_SCHEMA_VERSION_V1,
        "fallback_risk_label": fallback_risk_label,
        "provider_model_path_detected": provider_model_path_detected,
        "search_advisor_path_detected": search_advisor_path_detected,
        "local_safe_alternative_available": local_safe_alternative_available,
        "should_stop": should_stop,
        "safe_next_lane_label": safe_next_lane_label,
        "validation_status": "validation_pass_metadata_only" if local_safe_alternative_available else "blocked_invalid_or_unsafe_metadata_only",
        "blocked_reason_labels": blocked_reason_labels,
    }
    unsafe = _detect_unsafe_metadata(result)
    for reason in unsafe:
        _append_unique(result["blocked_reason_labels"], reason)
    if unsafe:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def _default_helper_plans_v1() -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    for helper_label, gap_label in HELPER_TO_GAP_V1:
        plans.append(
            {
                "schema_version": PLAN_SCHEMA_VERSION_V1,
                "artifact_type": "WeslrTargetedResponseFormationHelperPlanV1",
                "helper_label": helper_label,
                "target_gap_labels": [gap_label],
                "purpose": f"close {gap_label}",
                "validation_status": "validation_pass_metadata_only",
                "blocked_reason_labels": [],
            }
        )
    return plans


def build_targeted_response_formation_improvement_plan_v1(
    metadata: Mapping[str, Any] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    source = _merge_metadata(metadata, overrides)
    target_gap_labels, gap_reasons = _validate_allowed_label_list(source.get("target_gap_labels", ALLOWED_TARGETED_RESPONSE_GAP_LABELS_V1), ALLOWED_TARGETED_RESPONSE_GAP_LABELS_V1, kind="gap")
    helper_labels, helper_reasons = _validate_allowed_label_list(source.get("helper_labels", ALLOWED_TARGETED_RESPONSE_HELPER_LABELS_V1), ALLOWED_TARGETED_RESPONSE_HELPER_LABELS_V1, kind="helper")
    helper_plans = source.get("helper_plans", _default_helper_plans_v1())
    result = {
        "schema_version": PLAN_SCHEMA_VERSION_V1,
        "artifact_type": ARTIFACT_TYPE_V1,
        "source_run_result_path": _safe_text(source.get("source_run_result_path", SOURCE_RUN_RESULT_PATH_V1)).strip(),
        "source_run_result_commit": _safe_text(source.get("source_run_result_commit", SOURCE_RUN_RESULT_COMMIT_V1)).strip(),
        "source_review_path": _safe_text(source.get("source_review_path", SOURCE_REVIEW_PATH_V1)).strip(),
        "source_review_commit": _safe_text(source.get("source_review_commit", SOURCE_REVIEW_COMMIT_V1)).strip(),
        "target_gap_labels": list(target_gap_labels),
        "helper_plans": helper_plans,
        "conversation_state_fields": [
            "active_topic",
            "current_user_concern",
            "active_objective",
            "unresolved_question",
            "last_correction",
            "emotional_signal_label",
            "relevant_boundary",
            "safe_next_step",
            "local_context_only",
        ],
        "answer_shape_policy": {
            "allowed_answer_shapes": list(ALLOWED_ANSWER_SHAPES_V1),
            "blocked_answer_shapes": list(BLOCKED_ANSWER_SHAPES_V1),
        },
        "non_cannedness_policy": {
            "pressure_required": True,
            "current_turn_specificity_required": True,
            "user_concern_anchor_required": True,
        },
        "authority_calibration_policy": {
            "can_explain": True,
            "can_design": True,
            "can_execute": False,
            "can_claim_real_memory": False,
            "can_claim_public_readiness": False,
            "can_claim_deletion_completed": False,
        },
        "fallback_gating_policy": {
            "provider_model_path_detected": False,
            "search_advisor_path_detected": False,
            "local_safe_alternative_available": True,
        },
        "denied_authority": _safe_blocked_authority(),
        "validation_status": "validation_pass_metadata_only",
        "blocked_reason_labels": [],
        "recommended_next_lane": _safe_text(source.get("recommended_next_lane", "AWAIT_OPERATOR_DECISION")).strip() or "AWAIT_OPERATOR_DECISION",
    }

    reasons = gap_reasons + helper_reasons + _detect_unsafe_metadata(result)
    if set(helper_labels) != set(ALLOWED_TARGETED_RESPONSE_HELPER_LABELS_V1):
        _append_unique(reasons, "helper_labels_incomplete_or_unsupported")
    if set(target_gap_labels) != set(ALLOWED_TARGETED_RESPONSE_GAP_LABELS_V1):
        _append_unique(reasons, "target_gap_labels_incomplete_or_unsupported")
    denied_authority, denied_reasons = _validate_denied_authority(result["denied_authority"])
    result["denied_authority"] = denied_authority
    for reason in denied_reasons:
        _append_unique(reasons, reason)
    if ".weslr" in result["source_run_result_path"] or ".weslr" in result["source_review_path"]:
        _append_unique(reasons, "dot_weslr_path_present")
    if "continuity" in result["source_run_result_path"].lower() or "continuity" in result["source_review_path"].lower():
        _append_unique(reasons, "continuity_raw_path_present")
    if any(not isinstance(plan, Mapping) for plan in _as_list(result["helper_plans"])):
        _append_unique(reasons, "helper_plans_not_mapping_list")
    if reasons:
        result["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
        result["blocked_reason_labels"] = reasons
    return to_targeted_response_formation_improvement_json_safe_v1(result)


def validate_targeted_response_formation_improvement_plan_v1(plan: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "schema_version",
        "artifact_type",
        "source_run_result_path",
        "source_run_result_commit",
        "source_review_path",
        "source_review_commit",
        "target_gap_labels",
        "helper_plans",
        "conversation_state_fields",
        "answer_shape_policy",
        "non_cannedness_policy",
        "authority_calibration_policy",
        "fallback_gating_policy",
        "denied_authority",
        "validation_status",
        "blocked_reason_labels",
        "recommended_next_lane",
    )
    if not isinstance(plan, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "validation_status": "blocked_invalid_or_unsafe_metadata_only",
            "missing_required_fields": list(required_fields),
            "invalid_fields": ["plan"],
            "blocked_reason_labels": ["plan_not_mapping"],
            "json_safe": False,
        }
    missing = [field for field in required_fields if field not in plan]
    invalid_fields: list[str] = []
    blocked_reason_labels: list[str] = []
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")
    if plan.get("artifact_type") != ARTIFACT_TYPE_V1:
        _append_unique(invalid_fields, "artifact_type")
        _append_unique(blocked_reason_labels, "artifact_type_mismatch")
    gaps, gap_reasons = _validate_allowed_label_list(plan.get("target_gap_labels"), ALLOWED_TARGETED_RESPONSE_GAP_LABELS_V1, kind="gap")
    helpers, helper_reasons = _validate_allowed_label_list([item.get("helper_label") for item in _as_list(plan.get("helper_plans")) if isinstance(item, Mapping)], ALLOWED_TARGETED_RESPONSE_HELPER_LABELS_V1, kind="helper")
    for reason in gap_reasons + helper_reasons:
        _append_unique(blocked_reason_labels, reason)
    if set(gaps) != set(ALLOWED_TARGETED_RESPONSE_GAP_LABELS_V1):
        _append_unique(invalid_fields, "target_gap_labels")
        _append_unique(blocked_reason_labels, "target_gap_labels_incomplete_or_unsupported")
    if set(helpers) != set(ALLOWED_TARGETED_RESPONSE_HELPER_LABELS_V1):
        _append_unique(invalid_fields, "helper_plans")
        _append_unique(blocked_reason_labels, "helper_labels_incomplete_or_unsupported")
    denied_authority, denied_reasons = _validate_denied_authority(plan.get("denied_authority"))
    for reason in denied_reasons:
        _append_unique(blocked_reason_labels, reason)
    if denied_authority != required_targeted_response_denied_authority_v1():
        _append_unique(invalid_fields, "denied_authority")
    if ".weslr" in _safe_text(plan.get("source_run_result_path", "")) or ".weslr" in _safe_text(plan.get("source_review_path", "")):
        _append_unique(invalid_fields, "source_run_result_path")
        _append_unique(blocked_reason_labels, "dot_weslr_path_present")
    if "continuity" in _safe_text(plan.get("source_run_result_path", "")).lower() or "continuity" in _safe_text(plan.get("source_review_path", "")).lower():
        _append_unique(invalid_fields, "source_run_result_path")
        _append_unique(blocked_reason_labels, "continuity_raw_path_present")
    if _safe_bool(plan.get("denied_authority", {}).get("permits_memory_persistence", False)):
        _append_unique(invalid_fields, "denied_authority")
        _append_unique(blocked_reason_labels, "memory_persistence_allowed")
    unsafe = _detect_unsafe_metadata(plan)
    for reason in unsafe:
        _append_unique(blocked_reason_labels, reason)
    blocked = bool(missing or invalid_fields or blocked_reason_labels)
    return {
        "valid": not blocked,
        "blocked": blocked,
        "validation_status": "validation_pass_metadata_only" if not blocked else "blocked_invalid_or_unsafe_metadata_only",
        "missing_required_fields": missing,
        "invalid_fields": invalid_fields,
        "blocked_reason_labels": blocked_reason_labels,
        "json_safe": not bool(unsafe),
    }


def summarize_targeted_response_formation_improvement_plan_v1(plan: Mapping[str, Any]) -> dict[str, Any]:
    summary = {
        "helper_count": len(_as_list(plan.get("helper_plans"))) if isinstance(plan, Mapping) else 0,
        "target_gap_count": len(_as_list(plan.get("target_gap_labels"))) if isinstance(plan, Mapping) else 0,
        "allowed_answer_shapes": list(ALLOWED_ANSWER_SHAPES_V1),
        "blocked_answer_shapes": list(BLOCKED_ANSWER_SHAPES_V1),
        "validation_status": "validation_pass_metadata_only" if isinstance(plan, Mapping) else "blocked_invalid_or_unsafe_metadata_only",
        "blocked_reason_labels": list(plan.get("blocked_reason_labels", [])) if isinstance(plan, Mapping) else ["plan_not_mapping"],
        "recommended_next_lane": _safe_text(plan.get("recommended_next_lane", "AWAIT_OPERATOR_DECISION")).strip() if isinstance(plan, Mapping) else "AWAIT_OPERATOR_DECISION",
    }
    unsafe = _detect_unsafe_metadata(summary)
    if unsafe:
        summary["validation_status"] = "blocked_invalid_or_unsafe_metadata_only"
        for reason in unsafe:
            _append_unique(summary["blocked_reason_labels"], reason)
    return to_targeted_response_formation_improvement_json_safe_v1(summary)


__all__ = [
    "allowed_answer_shapes_v1",
    "allowed_targeted_response_gap_labels_v1",
    "allowed_targeted_response_helper_labels_v1",
    "apply_directness_pressure_v1",
    "apply_non_cannedness_pressure_v1",
    "build_answer_shape_planner_v1",
    "build_conversation_state_frame_v1",
    "build_current_user_concern_slot_v1",
    "build_goal_subgoal_conversation_frame_v1",
    "build_recent_turn_recall_object_v1",
    "build_targeted_response_formation_improvement_plan_v1",
    "blocked_answer_shapes_v1",
    "calibrate_boundary_specific_authority_v1",
    "gate_boundary_specific_fallback_v1",
    "integrate_empathy_concern_v1",
    "required_targeted_response_denied_authority_v1",
    "run_response_self_check_before_final_answer_v1",
    "select_answer_shape_v1",
    "select_concrete_next_step_v1",
    "select_response_shape_diversity_v1",
    "summarize_targeted_response_formation_improvement_plan_v1",
    "to_targeted_response_formation_improvement_json_safe_v1",
    "validate_answer_shape_plan_v1",
    "validate_conversation_state_frame_v1",
    "validate_current_user_concern_slot_v1",
    "validate_goal_subgoal_conversation_frame_v1",
    "validate_recent_turn_recall_object_v1",
    "validate_targeted_response_formation_improvement_plan_v1",
]
