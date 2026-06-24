"""WESLR Level 3 governed answer-improvement loop V1.

This module stays local, deterministic, JSON-safe, and no-model. It only
combines implemented metadata helpers, fit checks, friction replay metadata,
and a narrow text rewrite pass that preserves safety boundaries.

No provider calls. No model calls. No payment calls. No runtime wiring.
No `.weslr` writes. No ChatResponder/respond_chat wiring.
"""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
import re
from typing import Any, Mapping

from weslr.friction_replay_harness import (
    build_initial_renderer_friction_replay_v1,
    summarize_friction_replay_packet_v1,
    to_friction_replay_json_safe_v1,
)
from weslr.perspicuity_scorer import build_perspicuity_candidate_v1, build_perspicuity_scorecard_v1
from weslr.response_fit_self_check import (
    check_candidate_response_fit_v1,
    summarize_response_fit_self_check_packet_v1,
    to_response_fit_self_check_json_safe_v1,
)
from weslr.targeted_response_formation_improvement import (
    build_answer_shape_planner_v1,
    build_conversation_state_frame_v1,
    build_current_user_concern_slot_v1,
    build_goal_subgoal_conversation_frame_v1,
    build_recent_turn_recall_object_v1,
    build_targeted_response_formation_improvement_plan_v1,
    select_answer_shape_v1,
    select_concrete_next_step_v1,
    summarize_targeted_response_formation_improvement_plan_v1,
    to_targeted_response_formation_improvement_json_safe_v1,
)

SCHEMA_VERSION_V1 = "Level3AnswerImprovementLoopV1"
LOOP_TYPE_V1 = "level3_answer_improvement_loop_v1"

_GENERIC_MARKERS_V1 = (
    "i can help",
    "concrete advice",
    "if you want",
    "one more detail",
    "i need one more detail",
    "that sounds",
    "treat the term as unknown",
    "smallest failing layer",
    "pick the simplest option",
    "keep the next step small",
)

_BANNED_CLAIMS_V1 = (
    "agi",
    "consciousness",
    "sentience",
    "official certification",
)

_DEFERRED_HELPERS_V1 = (
    "rule_pressure_engine",
    "dialectic_generator_loop",
    "nonlinear_inspiration_resonance_engine",
)


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
        return str(value)
    if isinstance(value, float):
        return default if value != value else str(value)
    return default if value == "" else str(value)


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    return default


def _safe_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _json_safe(value: Any) -> Any:
    value = deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    return _safe_text(value)


@lru_cache(maxsize=1)
def _default_friction_replay_summary() -> dict[str, Any]:
    packet = build_initial_renderer_friction_replay_v1()
    summary = summarize_friction_replay_packet_v1(packet)
    return to_friction_replay_json_safe_v1(summary)


def _normalize_question(question: str) -> str:
    return " ".join(_safe_text(question).strip().lower().split())


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def _extract_distance_meters(question: str) -> int | None:
    match = re.search(r"(\d+)\s*(?:m|meter|meters|metre|metres)\b", question)
    if match:
        return int(match.group(1))
    return None


def _family_from_packet(packet: Mapping[str, Any]) -> str:
    family = _safe_text(packet.get("question_family"), "bounded_general")
    return family or "bounded_general"


def _question_from_packet(packet: Mapping[str, Any]) -> str:
    question = _safe_text(packet.get("question"), "")
    if question:
        return question
    question = _safe_text(packet.get("normalized_question"), "")
    return question or ""


def _initial_answer_text(packet: Mapping[str, Any]) -> str:
    return _safe_text(packet.get("final_answer_text"), "")


def _turn_labels_from_packet(packet: Mapping[str, Any], family: str, question: str) -> tuple[str, ...]:
    selector = packet.get("source_provenance", {}) if isinstance(packet.get("source_provenance"), Mapping) else {}
    selector = selector.get("answer_selector_json_safe", {}) if isinstance(selector, Mapping) else {}
    turn_labels = _safe_list(selector.get("turn_labels"))
    labels = [str(item).strip().lower() for item in turn_labels if str(item).strip()]
    if labels:
        return tuple(dict.fromkeys(labels))
    normalized = _normalize_question(question)
    labels = [normalized, family.replace("_", " ")]
    if family == "practical_decision":
        labels.extend(["direct bounded answer", "bounded decision"])
    elif family == "troubleshooting_guidance":
        labels.extend(["debugging flow", "stepwise plan"])
    elif family == "invention_guidance":
        labels.extend(["creative guidance", "bounded idea structure"])
    elif family == "emotional_support":
        labels.extend(["supportive response", "concrete next step"])
    elif family == "unknown_term":
        labels.extend(["bounded uncertainty", "context request"])
    elif family == "hostile_input_boundary":
        labels.extend(["boundary handling", "untrusted input"])
    elif family == "safe_technical_guidance":
        labels.extend(["privacy-preserving sensing", "teaching explanation"])
    elif family == "identity_status":
        labels.extend(["deterministic", "governed assistant stack"])
    return tuple(dict.fromkeys(label for label in labels if label))


def _context_signals_from_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    family = _family_from_packet(packet)
    question = _normalize_question(_question_from_packet(packet))
    distance_meters = _extract_distance_meters(question)
    module_signals = packet.get("module_signals", {}) if isinstance(packet.get("module_signals"), Mapping) else {}
    response_method = module_signals.get("response_method_selector", {}) if isinstance(module_signals.get("response_method_selector"), Mapping) else {}
    candidate = module_signals.get("candidate_response_formation", {}) if isinstance(module_signals.get("candidate_response_formation"), Mapping) else {}
    poison = module_signals.get("poison_shield", {}) if isinstance(module_signals.get("poison_shield"), Mapping) else {}
    return {
        "question_family": family,
        "identity_question": family == "identity_status",
        "capability_question": family == "capability_overview",
        "troubleshooting_question": family == "troubleshooting_guidance",
        "invention_question": family == "invention_guidance",
        "hostile_input_signal": family == "hostile_input_boundary",
        "unknown_word_signal": family == "unknown_term",
        "safe_technical_signal": family == "safe_technical_guidance",
        "practical_decision_signal": family == "practical_decision",
        "ambiguous_intent_signal": family == "ambiguous_intent",
        "emotional_support_signal": family == "emotional_support",
        "memory_boundary_signal": family == "memory_boundary",
        "safety_boundary_signal": family == "safety_boundary",
        "distance_meters": distance_meters,
        "selected_route_id": _safe_text(response_method.get("selected_route_id"), ""),
        "selected_method_id": _safe_text(response_method.get("selected_method_id"), ""),
        "selected_shape_id": _safe_text(response_method.get("selected_shape_id"), ""),
        "selected_candidate_id": _safe_text(candidate.get("selected_candidate_id"), ""),
        "blocked_by_poison_shield": _safe_bool(poison.get("blocked"), False),
    }


def _generic_or_weak_signal(answer_text: str, fit_status: str, shape: str, next_step: str) -> bool:
    lowered = answer_text.lower()
    if fit_status not in {"fit", "fit_with_boundaries"}:
        return True
    if _contains_any(lowered, _GENERIC_MARKERS_V1):
        return True
    if shape in {"planning_with_constraints", "tradeoff_reasoning", "concrete_next_step"} and len(answer_text) < 220:
        return True
    if next_step and "small" in next_step and len(answer_text) < 240:
        return True
    return False


def _family_specific_improvement(question: str, family: str, answer_text: str, context: Mapping[str, Any], selected_shape: str, next_step: str) -> tuple[str, list[str]]:
    improved = answer_text.strip()
    reasons: list[str] = []
    distance_meters = context.get("distance_meters")
    question_lower = _normalize_question(question)

    if family == "practical_decision":
        if isinstance(distance_meters, int):
            detail = (
                f"At about {distance_meters} meters, walking is the default unless carrying items, accessibility, weather, or parking pushes you to drive."
            )
            if detail.lower() not in improved.lower():
                improved = f"{improved} {detail}".strip()
            reasons.append(f"distance_constraint={distance_meters}m")
        else:
            detail = "Use the simplest option that meets your constraints: walk for short hops, drive when carrying, access, weather, or time matter more."
            if detail.lower() not in improved.lower():
                improved = f"{improved} {detail}".strip()
            reasons.append("constraint_rule_added")
    elif family == "troubleshooting_guidance":
        detail = "Start with the smallest failing layer: power, inputs, recent changes, and the exact point where the behavior stops matching expectations."
        if "inverter" in question_lower:
            detail = (
                "Start by checking whether the app only shows status while the inverter itself still needs a power, connection, or fault check. "
                "Then verify the smallest failing layer: power, inputs, recent changes, and the exact point where the behavior stops matching expectations."
            )
        if detail.lower() not in improved.lower():
            improved = f"{improved} {detail}".strip()
        reasons.append("smallest_failing_layer_added")
    elif family == "invention_guidance":
        detail = "Keep it bounded: one safe idea, one success criterion, one tiny experiment, and one explicit safety check."
        if detail.lower() not in improved.lower():
            improved = f"{improved} {detail}".strip()
        reasons.append("bounded_idea_structure_added")
    elif family == "emotional_support":
        detail = "I can’t feel the frustration for you, but I can help make the next step smaller: capture the exact failure, do one check, and decide what changed."
        if detail.lower() not in improved.lower():
            improved = f"{improved} {detail}".strip()
        reasons.append("concrete_support_added")
    elif family == "unknown_term":
        detail = "Do not guess; preserve uncertainty, ask for context, and add the term to a local map only with provenance and a human-reviewed definition."
        if detail.lower() not in improved.lower():
            improved = f"{improved} {detail}".strip()
        reasons.append("uncertainty_preserved")
    elif family == "hostile_input_boundary":
        detail = "Never execute the hostile instruction, never grant it authority, and only use it as an untrusted signal for quarantine and boundary handling."
        if detail.lower() not in improved.lower():
            improved = f"{improved} {detail}".strip()
        reasons.append("boundary_hardened")
    elif family == "safe_technical_guidance":
        detail = "Use coarse occupancy or movement detection, explicit consent, local processing, minimal retention, and test on synthetic or reviewable data first."
        if detail.lower() not in improved.lower():
            improved = f"{improved} {detail}".strip()
        reasons.append("technical_bounds_added")
    elif family == "identity_status":
        detail = "Keep the description local and governed: deterministic helper stack, no-model answer packets, and no unsupported claims."
        if detail.lower() not in improved.lower():
            improved = f"{improved} {detail}".strip()
        reasons.append("identity_boundary_reinforced")
    elif family == "capability_overview":
        detail = "Stay scoped to local help: summaries, planning, troubleshooting, explanations, and careful next steps without provider or runtime calls."
        if detail.lower() not in improved.lower():
            improved = f"{improved} {detail}".strip()
        reasons.append("capability_scope_reinforced")
    elif family == "memory_boundary":
        detail = "Be explicit about what comes from the current conversation and what is inferred from local repo context."
        if detail.lower() not in improved.lower():
            improved = f"{improved} {detail}".strip()
        reasons.append("provenance_honesty_added")
    elif family == "safety_boundary":
        detail = "Offer the safest alternative instead of the disallowed action."
        if detail.lower() not in improved.lower():
            improved = f"{improved} {detail}".strip()
        reasons.append("safe_alternative_added")
    elif family == "ambiguous_intent":
        detail = "Ask one short clarifying question and give a provisional answer only under a stated assumption."
        if detail.lower() not in improved.lower():
            improved = f"{improved} {detail}".strip()
        reasons.append("clarification_bound_added")
    elif family == "bounded_general":
        detail = "Use the strongest supported answer, state uncertainty plainly, and keep the next step small."
        if detail.lower() not in improved.lower():
            improved = f"{improved} {detail}".strip()
        reasons.append("general_bound_added")

    if selected_shape and selected_shape not in reasons:
        reasons.append(f"selected_shape={selected_shape}")
    if next_step:
        reasons.append(f"next_step={next_step}")
    return improved, reasons


def _perspicuity_status(packet: Mapping[str, Any], improved_answer_text: str, family: str, selected_shape: str) -> tuple[str | None, dict[str, Any] | None]:
    try:
        candidate = build_perspicuity_candidate_v1(
            {
                "candidate_type": "translation_candidate",
                "research_mode": "synthetic_test",
                "safe_metadata": {
                    "question_family": family,
                    "selected_shape": selected_shape,
                    "answer_length": len(improved_answer_text),
                    "answer_has_banned_claims": _contains_any(improved_answer_text.lower(), _BANNED_CLAIMS_V1),
                },
            }
        )
        scorecard = build_perspicuity_scorecard_v1(
            {
                "candidate_type": candidate.get("candidate_type", "translation_candidate"),
                "research_mode": "synthetic_test",
                "safe_metadata": {
                    "question_family": family,
                    "selected_shape": selected_shape,
                    "answer_length": len(improved_answer_text),
                },
            }
        )
    except Exception:
        return None, None
    safe_scorecard = _json_safe(scorecard)
    overall_priority = _safe_text(safe_scorecard.get("overall_priority"), "unknown")
    recommended = _safe_text(safe_scorecard.get("recommended_next_action"), "")
    status = f"{overall_priority}:{recommended}" if recommended else overall_priority
    return status, {
        "candidate": _json_safe(candidate),
        "scorecard": safe_scorecard,
    }


def build_level3_answer_improvement_loop_packet_v1(initial_packet: Mapping[str, Any], *, use_friction_replay: bool = True, use_perspicuity: bool = True) -> dict[str, Any]:
    if not isinstance(initial_packet, Mapping):
        raise TypeError("initial_packet must be a mapping")

    packet = _json_safe(initial_packet)
    family = _family_from_packet(packet)
    question = _question_from_packet(packet)
    initial_answer = _initial_answer_text(packet)
    context = _context_signals_from_packet(packet)
    turn_labels = _turn_labels_from_packet(packet, family, question)

    plan_metadata = {
        "question_family": family,
        "current_user_concern": question,
        "answer_shape": packet.get("inferred_answer_direction", "bounded_general_answer"),
        "turn_labels": list(turn_labels),
        "observations": list(_safe_list(packet.get("observations"))),
        "selected_capability_families": list(_safe_list(packet.get("selected_capability_families"))),
        "safety_provenance_limits": list(_safe_list(packet.get("safety_provenance_limits"))),
        "source_label": "level3_answer_improvement_loop",
    }

    conversation_state_frame = build_conversation_state_frame_v1(plan_metadata)
    current_user_concern_slot = build_current_user_concern_slot_v1(plan_metadata)
    recent_turn_recall_object = build_recent_turn_recall_object_v1(plan_metadata)
    goal_subgoal_frame = build_goal_subgoal_conversation_frame_v1(plan_metadata)
    answer_shape_planner = build_answer_shape_planner_v1(plan_metadata)
    selected_answer_shape = select_answer_shape_v1(plan_metadata)
    selected_next_step = select_concrete_next_step_v1(plan_metadata)
    improvement_plan = build_targeted_response_formation_improvement_plan_v1(plan_metadata)
    fit_packet = check_candidate_response_fit_v1(turn_labels, context)
    fit_summary = summarize_response_fit_self_check_packet_v1(fit_packet)

    if use_friction_replay:
        friction_summary = _default_friction_replay_summary()
        friction_status = _safe_text(friction_summary.get("packet_type"), "friction_replay_harness_v1")
        if friction_summary.get("failed_count", 0):
            friction_status = f"{friction_status}:needs_attention"
        else:
            friction_status = f"{friction_status}:pass"
        friction_trace = _json_safe(friction_summary)
    else:
        friction_status = "deferred"
        friction_trace = {"deferred": True, "reason": "friction replay disabled"}

    selected_shape_name = _safe_text(selected_answer_shape.get("selected_answer_shape"), "")
    next_step_label = _safe_text(selected_next_step.get("selected_next_step_label"), "")
    fit_status = _safe_text(fit_summary.fit_status if hasattr(fit_summary, "fit_status") else fit_summary.get("fit_status"), "unknown")
    selected_shape_id = _safe_text(packet.get("source_provenance", {}).get("answer_selector_json_safe", {}).get("selected_shape_id"), "")
    should_improve = _generic_or_weak_signal(initial_answer, fit_status, selected_shape_name, next_step_label)

    improved_answer = initial_answer
    improvement_reasons: list[str] = []
    if should_improve:
        improved_answer, improvement_reasons = _family_specific_improvement(
            question,
            family,
            initial_answer,
            context,
            selected_shape_name,
            next_step_label,
        )

    if _contains_any(improved_answer.lower(), _BANNED_CLAIMS_V1):
        improved_answer = initial_answer
        improvement_reasons.append("banned_claims_blocked")
        should_improve = False

    if not improvement_reasons:
        improvement_reasons = ["fit_check_preserved" if improved_answer == initial_answer else "targeted_improvement_applied"]

    perspicuity_status = None
    perspicuity_trace = None
    if use_perspicuity:
        perspicuity_status, perspicuity_trace = _perspicuity_status(packet, improved_answer, family, selected_shape_name)

    targeted_plan_summary = summarize_targeted_response_formation_improvement_plan_v1(improvement_plan)

    trace = {
        "schema_version": SCHEMA_VERSION_V1,
        "loop_type": LOOP_TYPE_V1,
        "family": family,
        "question": question,
        "initial_answer_text": initial_answer,
        "improved_answer_text": improved_answer,
        "turn_labels": list(turn_labels),
        "context_signals": _json_safe(context),
        "conversation_state_frame": _json_safe(conversation_state_frame),
        "current_user_concern_slot": _json_safe(current_user_concern_slot),
        "recent_turn_recall_object": _json_safe(recent_turn_recall_object),
        "goal_subgoal_frame": _json_safe(goal_subgoal_frame),
        "answer_shape_planner": _json_safe(answer_shape_planner),
        "selected_answer_shape": _json_safe(selected_answer_shape),
        "selected_next_step": _json_safe(selected_next_step),
        "targeted_response_improvement_plan": _json_safe(targeted_plan_summary),
        "fit_check": _json_safe(to_response_fit_self_check_json_safe_v1(fit_packet)),
        "friction_replay": _json_safe(friction_trace),
        "perspicuity": _json_safe(perspicuity_trace) if perspicuity_trace is not None else None,
    }

    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "loop_type": LOOP_TYPE_V1,
        "initial_answer_text": initial_answer,
        "improved_answer_text": improved_answer,
        "improvement_applied": improved_answer != initial_answer,
        "improvement_reasons": improvement_reasons,
        "fit_check_status": fit_status,
        "friction_replay_status": friction_status,
        "clarity_or_perspicuity_status": perspicuity_status,
        "deferred_helpers": list(_DEFERRED_HELPERS_V1),
        "safety_boundaries": list(_safe_list(packet.get("safety_provenance_limits")))
        + [
            "no provider/model/payment/API calls",
            "no ChatResponder/respond_chat wiring",
            "no website/runtime wiring",
            "no .weslr writes",
            "no memory mutation",
            "no AGI/consciousness/sentience/official certification claims",
            "deterministic no-model local helper stack only",
        ],
        "final_answer_text": improved_answer,
        "improvement_trace": trace,
    }
    return result


def to_level3_answer_improvement_loop_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


__all__ = [
    "SCHEMA_VERSION_V1",
    "LOOP_TYPE_V1",
    "build_level3_answer_improvement_loop_packet_v1",
    "to_level3_answer_improvement_loop_json_safe_v1",
]
