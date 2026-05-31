"""Metadata-only no-model bounded renderer v1.

This layer turns the selected response path plus fit/self-check metadata into
safe bounded text. It is pure, deterministic, import-safe, and fail-closed.

No model/provider calls. No runtime wiring. No state writes. No public pilot.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from weslr.answer_method_catalog import build_answer_method_catalog_v1
from weslr.answer_shape_catalog import build_answer_shape_catalog_v1
from weslr.cognition_case_registry import build_cognition_case_registry_v1
from weslr.response_fit_self_check import (
    check_candidate_response_fit_v1,
    summarize_response_fit_self_check_packet_v1,
    to_response_fit_self_check_json_safe_v1,
    validate_response_fit_self_check_packet_v1,
)

PACKET_TYPE_V1 = "no_model_bounded_renderer_v1"
SUMMARY_TYPE_V1 = "no_model_bounded_render_summary_v1"
TRACE_TYPE_V1 = "no_model_bounded_render_trace_v1"
RENDERED_ANSWER_TYPE_V1 = "no_model_rendered_answer_v1"

ALLOWED_RENDER_MODES_V1 = {
    "direct_bounded",
    "clarifying_question",
    "bounded_uncertainty",
    "refusal_boundary",
    "evidence_needed",
    "partial_supported",
    "stepwise_plan",
    "implementation_plan",
    "workflow_next_lane",
    "governance_escalation",
    "teaching_explanation",
    "language_discovery_explanation",
    "scientific_discovery_guidance",
    "benchmark_evaluation_summary",
    "unknown_friction",
    "memory_honesty",
    "continuity_recap",
    "relationship_feedback",
    "correction_repair",
    "conflict_contradiction",
    "non_canned_specificity",
    "directness_concern",
}

RESPONSE_POLICY_BY_MODE_V1 = {
    "direct_bounded": "bounded_direct_answer",
    "clarifying_question": "clarify_before_answering",
    "bounded_uncertainty": "bounded_uncertainty",
    "refusal_boundary": "refuse_with_boundary",
    "evidence_needed": "request_evidence",
    "partial_supported": "give_partial_supported_answer",
    "stepwise_plan": "answer_with_stepwise_plan",
    "implementation_plan": "answer_with_implementation_plan",
    "workflow_next_lane": "answer_with_next_lane_plan",
    "governance_escalation": "escalate_to_owner_review",
    "teaching_explanation": "answer_with_teaching_explanation",
    "language_discovery_explanation": "route_language_discovery_explanation",
    "scientific_discovery_guidance": "answer_with_scientific_guidance",
    "benchmark_evaluation_summary": "answer_with_evaluation_summary",
    "unknown_friction": "route_unknown_friction",
    "memory_honesty": "route_memory_honesty",
    "continuity_recap": "route_continuity_recap",
    "relationship_feedback": "route_relationship_feedback",
    "correction_repair": "route_correction_repair",
    "conflict_contradiction": "route_conflict_contradiction",
    "non_canned_specificity": "answer_with_non_canned_specificity",
    "directness_concern": "answer_with_directness_concern",
}

MODE_BY_CANDIDATE_TYPE_V1 = {
    "direct_bounded_candidate": "direct_bounded",
    "clarification_candidate": "clarifying_question",
    "bounded_uncertainty_candidate": "bounded_uncertainty",
    "refusal_boundary_candidate": "refusal_boundary",
    "evidence_needed_candidate": "evidence_needed",
    "partial_supported_candidate": "partial_supported",
    "stepwise_plan_candidate": "stepwise_plan",
    "implementation_plan_candidate": "implementation_plan",
    "workflow_next_lane_candidate": "workflow_next_lane",
    "governance_escalation_candidate": "governance_escalation",
    "teaching_explanation_candidate": "teaching_explanation",
    "language_discovery_candidate": "language_discovery_explanation",
    "scientific_discovery_guidance_candidate": "scientific_discovery_guidance",
    "benchmark_evaluation_candidate": "benchmark_evaluation_summary",
    "unknown_friction_candidate": "unknown_friction",
    "memory_honesty_candidate": "memory_honesty",
    "continuity_recap_candidate": "continuity_recap",
    "relationship_feedback_candidate": "relationship_feedback",
    "correction_repair_candidate": "correction_repair",
    "conflict_contradiction_candidate": "conflict_contradiction",
    "non_canned_specificity_candidate": "non_canned_specificity",
    "directness_concern_candidate": "directness_concern",
}

MODE_BY_SHAPE_ID_V1 = {
    "direct_bounded_answer": "direct_bounded",
    "clarifying_question": "clarifying_question",
    "bounded_uncertainty_answer": "bounded_uncertainty",
    "refusal_boundary_answer": "refusal_boundary",
    "evidence_needed_answer": "evidence_needed",
    "partial_supported_answer": "partial_supported",
    "stepwise_plan_answer": "stepwise_plan",
    "implementation_plan_answer": "implementation_plan",
    "workflow_next_lane_answer": "workflow_next_lane",
    "governance_escalation_answer": "governance_escalation",
    "teaching_explanation_answer": "teaching_explanation",
    "language_discovery_explanation_answer": "language_discovery_explanation",
    "scientific_discovery_guidance_answer": "scientific_discovery_guidance",
    "benchmark_evaluation_summary_answer": "benchmark_evaluation_summary",
    "unknown_friction_branch_answer": "unknown_friction",
    "memory_honesty_answer": "memory_honesty",
    "continuity_thread_recap_answer": "continuity_recap",
    "relationship_feedback_answer": "relationship_feedback",
    "correction_repair_answer": "correction_repair",
    "conflict_contradiction_answer": "conflict_contradiction",
    "non_canned_specific_answer": "non_canned_specificity",
    "directness_concern_integrated_answer": "directness_concern",
}

RENDER_RECORD_IDS_BY_ROUTE_V1 = {
    "identity_status_route": ("verified_identity_status_answer_v1", "direct_bounded_answer", "identity_self_description_case"),
    "capability_orientation_route": ("capability_orientation_answer_v1", "direct_bounded_answer", "capability_orientation_case"),
    "memory_honesty_route": ("memory_report_answer_v1", "memory_honesty_answer", "memory_honesty_case"),
    "continuity_route": ("continuity_thread_answer_v1", "continuity_thread_recap_answer", "continuity_thread_recap_case"),
    "clarification_route": ("clarifying_question_answer_v1", "clarifying_question", "clarification_needed_case"),
    "uncertainty_route": ("bounded_uncertainty_answer_v1", "bounded_uncertainty_answer", "bounded_uncertainty_case"),
    "refusal_boundary_route": ("refusal_boundary_answer_v1", "refusal_boundary_answer", "refusal_boundary_case"),
    "evidence_needed_route": ("evidence_needed_answer_v1", "evidence_needed_answer", "evidence_needed_case"),
    "partial_supported_route": ("partial_answer_supported_portion_answer_v1", "partial_supported_answer", "partial_supported_case"),
    "ordinary_task_route": ("ordinary_task_planning_answer_v1", "stepwise_plan_answer", "ordinary_task_planning_case"),
    "implementation_planning_route": ("implementation_planning_answer_v1", "implementation_plan_answer", "implementation_planning_case"),
    "workflow_next_lane_route": ("workflow_next_lane_answer_v1", "workflow_next_lane_answer", "workflow_next_lane_case"),
    "governance_escalation_route": ("governance_escalation_proposal_v1", "governance_escalation_answer", "governance_escalation_case"),
    "teaching_explanation_route": ("teaching_explanation_answer_v1", "teaching_explanation_answer", "teaching_explanation_case"),
    "language_discovery_route": ("language_grammar_vocabulary_discovery_answer_v1", "language_discovery_explanation_answer", "language_discovery_explanation_case"),
    "scientific_discovery_route": ("scientific_discovery_capability_guidance_answer_v1", "scientific_discovery_guidance_answer", "scientific_discovery_guidance_case"),
    "benchmark_evaluation_route": ("benchmark_evaluation_answer_v1", "benchmark_evaluation_summary_answer", "benchmark_evaluation_summary_case"),
    "unknown_word_phrase_route": ("unknown_engine_branch_friction_answer_v1", "unknown_friction_branch_answer", "unknown_word_or_phrase_case"),
    "unknown_intent_route": ("unknown_engine_branch_friction_answer_v1", "unknown_friction_branch_answer", "unknown_intent_case"),
    "unknown_capability_route": ("unknown_engine_branch_friction_answer_v1", "unknown_friction_branch_answer", "unknown_capability_request_case"),
    "friction_repeated_failure_route": ("unknown_engine_branch_friction_answer_v1", "unknown_friction_branch_answer", "friction_repeated_failure_case"),
    "relationship_feedback_route": ("relationship_feedback_answer_v1", "relationship_feedback_answer", "relationship_feedback_case"),
    "correction_repair_route": ("correction_repair_answer_v1", "correction_repair_answer", "correction_repair_case"),
    "conflict_contradiction_route": ("conflict_contradiction_handling_answer_v1", "conflict_contradiction_answer", "conflict_contradiction_case"),
    "non_canned_specificity_route": ("non_cannedness_pressure_v1", "non_canned_specific_answer", "non_canned_specificity_pressure_case"),
    "directness_concern_route": ("directness_concern_integration_self_check_v1", "directness_concern_integrated_answer", "directness_concern_integration_case"),
}

RAW_LEAK_MARKERS_V1 = (
    "raw_prompt_text",
    "prompt_text",
    "raw_response_text",
    "response_text",
    "final_answer_text",
    "final_answer_prose",
    "answer_draft_text",
    "composed_reply_text",
    "live_dialogue_transcript",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "private_content",
    "hidden_prompt",
)

NON_OFFICIAL_MARKERS_V1 = (
    "as an ai",
    "language model",
    "conscious",
    "sentient",
    "agi",
    "turing",
    "certified",
    "official benchmark",
    "public ready",
    "benchmark ready",
)

METHODS = {item.method_id: item for item in build_answer_method_catalog_v1().methods}
SHAPES = {item.shape_id: item for item in build_answer_shape_catalog_v1().shapes}
CASES = {item.case_id: item for item in build_cognition_case_registry_v1().cases}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class NoModelRenderTrace:
    trace_id: str
    selected_candidate_type: str
    selected_route_id: str
    render_mode: str
    response_policy: str
    fit_status: str
    steps: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class NoModelRenderedAnswer:
    response_text: str
    render_mode: str
    response_policy: str
    selected_candidate_id: str
    selected_method_id: str
    selected_shape_id: str
    selected_case_id: str
    selected_route_id: str


@dataclass(frozen=True, slots=True)
class NoModelRenderSummary:
    packet_type: str
    render_mode: str
    response_policy: str
    selected_candidate_id: str
    selected_method_id: str
    selected_shape_id: str
    selected_case_id: str
    selected_route_id: str
    fit_status: str
    blocked: bool
    response_length: int


@dataclass(frozen=True, slots=True)
class NoModelBoundedRenderPacket:
    packet_type: str
    turn_labels: list[str]
    safe_context_signal_keys: list[str]
    fit_summary: dict[str, Any]
    selected_candidate_id: str
    selected_method_id: str
    selected_shape_id: str
    selected_case_id: str
    selected_route_id: str
    response_policy: str
    render_mode: str
    response_text: str
    render_trace: NoModelRenderTrace
    boundary_notes: list[str]
    missing_inputs: list[str]
    evidence_notes: list[str]
    memory_notes: list[str]
    capability_notes: list[str]
    governance_notes: list[str]
    needs_clarification: bool
    needs_evidence: bool
    needs_owner_approval: bool
    blocked: bool
    blocked_labels: list[str]
    safe_metadata: dict[str, Any]
    runtime_authority: bool = False
    model_provider_used: bool = False
    writes_state: bool = False
    chat_wired: bool = False
    public_ready: bool = False



def _dedupe_preserve(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out



def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return _json_safe({name: getattr(value, name) for name in value.__dataclass_fields__})
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)



def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())



def _normalize_labels(turn_labels: Any) -> list[str]:
    if turn_labels is None:
        return []
    if isinstance(turn_labels, str):
        values = [turn_labels]
    elif isinstance(turn_labels, Mapping):
        values = [str(v) for v in turn_labels.values()]
    else:
        try:
            values = [str(v) for v in turn_labels]
        except TypeError:
            values = [str(turn_labels)]
    out: list[str] = []
    for value in values:
        text = _safe_text(value).lower().replace("/", " ").replace("_", " ").replace("-", " ")
        if text:
            out.append(" ".join(text.split()))
    return _dedupe_preserve(out)



def _normalize_context_signals(context_signals: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    if not context_signals or not isinstance(context_signals, Mapping):
        return {}
    return {str(key): value for key, value in context_signals.items()}



def _contains_any(blob: str, phrases: Sequence[str]) -> bool:
    return any(phrase in blob for phrase in phrases)



def _truthy(value: Any) -> bool:
    return bool(value is True or value == 1 or str(value).strip().lower() in {"true", "yes", "1", "on"})



def _safe_context_signal_keys(context_signals: Mapping[str, Any]) -> list[str]:
    return _dedupe_preserve(sorted(key for key in context_signals.keys() if key not in RAW_LEAK_MARKERS_V1))



def _turn_blob(turn_labels: Sequence[str], context_signals: Mapping[str, Any]) -> str:
    return " ".join([*turn_labels, *(_safe_text(v).lower() for v in context_signals.values())])



def _candidate_lookup(packet: Mapping[str, Any], candidate_id: str) -> dict[str, Any] | None:
    for item in packet.get("candidate_fit_results", []):
        if item.get("candidate_id") == candidate_id:
            return item
    return None



def _find_candidate_by_type(packet: Mapping[str, Any], candidate_type: str) -> dict[str, Any] | None:
    for item in packet.get("candidate_fit_results", []):
        if item.get("candidate_type") == candidate_type:
            return item
    return None



def _select_render_candidate(fit_packet: Mapping[str, Any]) -> dict[str, Any]:
    fit_status = str(fit_packet.get("fit_status", "blocked"))
    blocked = bool(fit_packet.get("blocked", False))
    if blocked:
        candidate = _find_candidate_by_type(fit_packet, "refusal_boundary_candidate")
        if candidate is not None:
            return candidate
        return {
            "candidate_type": "refusal_boundary_candidate",
            "candidate_id": "refusal_boundary_candidate:refusal_boundary_route",
            "route_id": "refusal_boundary_route",
            "method_id": "refusal_boundary_answer_v1",
            "shape_id": "refusal_boundary_answer",
            "case_id": "refusal_boundary_case",
        }
    if fit_status in {"needs_clarification", "needs_evidence", "needs_owner_approval", "unknown_friction"}:
        candidate_id = str(fit_packet.get("final_candidate_id") or fit_packet.get("selected_candidate_id") or "")
        candidate = _candidate_lookup(fit_packet, candidate_id) if candidate_id else None
        if candidate is not None:
            return candidate
    candidate_id = str(fit_packet.get("final_candidate_id") or fit_packet.get("selected_candidate_id") or "")
    candidate = _candidate_lookup(fit_packet, candidate_id) if candidate_id else None
    if candidate is not None:
        return candidate
    candidate = _candidate_lookup(fit_packet, str(fit_packet.get("selected_candidate_id") or ""))
    if candidate is not None:
        return candidate
    return _find_candidate_by_type(fit_packet, "clarification_candidate") or {
        "candidate_type": "clarification_candidate",
        "candidate_id": "clarification_candidate:clarification_route",
        "route_id": "clarification_route",
        "method_id": "clarifying_question_answer_v1",
        "shape_id": "clarifying_question",
        "case_id": "clarification_needed_case",
    }



def _mode_for_candidate(candidate_type: str) -> str:
    return MODE_BY_CANDIDATE_TYPE_V1.get(candidate_type, "direct_bounded")



def _response_policy_for_mode(mode: str) -> str:
    return RESPONSE_POLICY_BY_MODE_V1.get(mode, "bounded_direct_answer")



def _method_shape_case(candidate: Mapping[str, Any]) -> tuple[Any, Any, Any]:
    route_id = str(candidate.get("route_id", ""))
    method_id, shape_id, case_id = RENDER_RECORD_IDS_BY_ROUTE_V1.get(route_id, (str(candidate.get("method_id", "")), str(candidate.get("shape_id", "")), str(candidate.get("case_id", ""))))
    method = METHODS.get(method_id)
    shape = SHAPES.get(shape_id)
    case = CASES.get(case_id)
    if method is None or shape is None or case is None:
        raise ValidationError("selected method/shape/case must exist")
    return method, shape, case



def _next_step_phrase(mode: str, case: Any, missing_inputs: Sequence[str]) -> str:
    if mode == "clarifying_question":
        return f"What should I ground this in: {', '.join(missing_inputs[:2]) or 'scope'}?"
    if mode == "evidence_needed":
        return "Share the smallest relevant excerpt or source pointer, and I’ll continue from there."
    if mode == "unknown_friction":
        return "If you want, give me one clearer target or the exact sticking point and I’ll narrow it down."
    if mode == "memory_honesty":
        return "If you want continuity, give me the specific note or detail you want me to anchor to."
    if mode == "continuity_recap":
        return "The next safe step is to keep the thread bounded and continue from the last verified point."
    if mode == "correction_repair":
        return "Please point to the part that needs correction, and I’ll repair the shape rather than just the wording."
    if mode == "relationship_feedback":
        return "If you want, I’ll keep the tone tighter and adjust the next reply shape."
    if mode == "language_discovery_explanation":
        return "If you want, I can reframe it with simpler grammar or vocabulary."
    if mode == "scientific_discovery_guidance":
        return "If you want, I can turn this into a minimal research checklist without claiming results."
    if mode == "benchmark_evaluation_summary":
        return "I can summarize the evaluation shape without making a score claim."
    if mode == "governance_escalation":
        return "This needs owner review before I can take the next step."
    if mode == "refusal_boundary":
        return "I can still help with a safe alternative or a bounded next step."
    if mode == "implementation_plan":
        return "I can turn this into a constrained implementation sequence next."
    if mode == "workflow_next_lane":
        return "I can keep the next lane bounded and move one step at a time."
    return "If you want, I can narrow this further without overclaiming."



def _boundary_notes(fit_status: str, blocked_labels: Sequence[str], shape: Any, case: Any) -> list[str]:
    notes = [f"fit_status:{fit_status}"]
    notes.extend(_safe_text(note) for note in getattr(shape, "blocked_if", ()) if _safe_text(note))
    notes.extend(_safe_text(note) for note in getattr(case, "blocked_if", ()) if _safe_text(note))
    notes.extend(f"blocked:{label}" for label in blocked_labels)
    return _dedupe_preserve([note for note in notes if note])



def _notes_from_requirements(title: str, items: Sequence[str]) -> list[str]:
    out = [f"{title}:{_safe_text(item)}" for item in items if _safe_text(item)]
    return _dedupe_preserve(out)



def _build_response_text(
    mode: str,
    method: Any,
    shape: Any,
    case: Any,
    fit_summary: Mapping[str, Any],
    turn_labels: Sequence[str],
    context_signals: Mapping[str, Any],
    missing_inputs: Sequence[str],
) -> str:
    blob = _turn_blob(turn_labels, context_signals)
    next_step = _next_step_phrase(mode, case, missing_inputs)
    method_name = _safe_text(getattr(method, "name", ""))
    shape_name = _safe_text(getattr(shape, "name", ""))
    case_name = _safe_text(getattr(case, "name", ""))
    case_purpose = _safe_text(getattr(case, "purpose", ""))
    shape_contract = _safe_text(getattr(shape, "output_contract", ""))
    method_purpose = _safe_text(getattr(method, "purpose", ""))

    if mode == "clarifying_question":
        focus = ", ".join(missing_inputs[:2] or ["scope"])
        return f"What should I focus on first: {focus}?"
    if mode == "bounded_uncertainty":
        return f"I’m not fully sure yet. The safe read is that {method_purpose or shape_contract or case_purpose} applies, but I’d rather not overstate beyond the current context. {next_step}"
    if mode == "refusal_boundary":
        return f"I can’t help with that as stated. {shape_contract or case_purpose or method_purpose} keeps the reply bounded, and I can still help with a safe alternative. {next_step}"
    if mode == "evidence_needed":
        return f"I need a small piece of evidence or source context before I can answer that safely. {shape_contract or case_purpose or method_purpose} fits here, but not without an anchor. {next_step}"
    if mode == "partial_supported":
        supported = case_purpose or method_purpose or shape_contract or "the supported part"
        return f"I can cover the supported part now: {supported}. The unsupported part still needs context or evidence. {next_step}"
    if mode == "stepwise_plan":
        return (
            f"1. Confirm the task and success criteria for {case_name or shape_name}.\n"
            f"2. Collect any missing context from the current turn: {', '.join(missing_inputs[:2] or ['scope'])}.\n"
            f"3. Execute the smallest safe next step using {method_name or method_purpose}."
        )
    if mode == "implementation_plan":
        return (
            f"1. Pin down the target gap for {case_name or shape_name}.\n"
            f"2. Map a bounded implementation path from {method_purpose or shape_contract}.\n"
            f"3. Stop before any runtime wiring or unsupported claim."
        )
    if mode == "workflow_next_lane":
        return (
            f"Next lane: {case_name or shape_name}.\n"
            f"1. Keep the step bounded to the current metadata.\n"
            f"2. Carry the next safe action forward without overreach."
        )
    if mode == "governance_escalation":
        return f"This needs owner review before I can proceed. {case_purpose or method_purpose or shape_contract} makes the boundary explicit. {next_step}"
    if mode == "teaching_explanation":
        return f"Here’s the short version: {method_purpose or case_purpose or shape_contract}. I’m keeping it teachable, bounded, and specific. {next_step}"
    if mode == "language_discovery_explanation":
        return f"If you mean the wording, grammar, or vocabulary itself, I’d treat it as a language-discovery problem. {method_purpose or case_purpose or shape_contract} applies here. {next_step}"
    if mode == "scientific_discovery_guidance":
        return f"For research or discovery, I’d stay at guidance level only: {method_purpose or case_purpose or shape_contract}. {next_step}"
    if mode == "benchmark_evaluation_summary":
        return f"I can summarize the evaluation shape without making a score claim. {next_step}"
    if mode == "unknown_friction":
        lead = "This looks like an unknown capability, intent, or friction-heavy path rather than a clean direct answer."
        return f"{lead} {method_purpose or case_purpose or shape_contract}. {next_step}"
    if mode == "memory_honesty":
        return f"I don’t have verified memory for this here. {method_purpose or case_purpose or shape_contract}. {next_step}"
    if mode == "continuity_recap":
        return f"We were on {case_name or case_purpose or shape_name}. {method_purpose or shape_contract}. {next_step}"
    if mode == "relationship_feedback":
        return f"I hear the feedback, and I’ll keep the next reply tighter and more grounded. {method_purpose or case_purpose or shape_contract}. {next_step}"
    if mode == "correction_repair":
        return f"You’re right to correct that. I’ll repair the shape, not just the wording. {method_purpose or case_purpose or shape_contract}. {next_step}"
    if mode == "conflict_contradiction":
        return f"I see a contradiction, and I’ll preserve both sides instead of flattening them. {method_purpose or case_purpose or shape_contract}. {next_step}"
    if mode == "non_canned_specificity":
        detail = case_purpose or method_purpose or shape_contract or "the specific shape here"
        return f"I’ll keep this specific and avoid generic filler. {detail}. {next_step}"
    if mode == "directness_concern":
        return f"Directly: {method_purpose or case_purpose or shape_contract}. I’m keeping the reply clear, bounded, and not performative. {next_step}"
    # direct_bounded
    return f"I can help with that in a bounded way. {method_name or method_purpose}. {shape_contract or case_purpose}. {next_step}"



def _trace_id(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"nmbrrv1_{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"



def build_no_model_bounded_render_packet_v1(turn_labels: Any, context_signals: Mapping[str, Any] | None = None) -> NoModelBoundedRenderPacket:
    normalized_labels = _normalize_labels(turn_labels)
    normalized_context_signals = _normalize_context_signals(context_signals)
    safe_context_signal_keys = _safe_context_signal_keys(normalized_context_signals)

    fit_packet_obj = check_candidate_response_fit_v1(normalized_labels, context_signals=normalized_context_signals)
    fit_packet = to_response_fit_self_check_json_safe_v1(fit_packet_obj)
    fit_summary_obj = summarize_response_fit_self_check_packet_v1(fit_packet_obj)
    fit_summary = _json_safe(fit_summary_obj)

    render_candidate = _select_render_candidate(fit_packet)
    method, shape, case = _method_shape_case(render_candidate)
    mode = _mode_for_candidate(str(render_candidate.get("candidate_type", "direct_bounded_candidate")))
    if bool(fit_packet.get("blocked", False)):
        mode = "refusal_boundary"
    elif str(fit_packet.get("fit_status", "")) == "needs_clarification":
        mode = "clarifying_question"
    elif str(fit_packet.get("fit_status", "")) == "needs_evidence":
        mode = "evidence_needed"
    elif str(fit_packet.get("fit_status", "")) == "needs_owner_approval":
        mode = "governance_escalation"
    elif str(fit_packet.get("fit_status", "")) == "unknown_friction":
        mode = "unknown_friction"

    response_policy = _response_policy_for_mode(mode)
    selected_candidate_id = str(render_candidate.get("candidate_id", ""))
    selected_method_id = str(getattr(method, "method_id", ""))
    selected_shape_id = str(getattr(shape, "shape_id", ""))
    selected_case_id = str(getattr(case, "case_id", ""))
    selected_route_id = str(render_candidate.get("route_id", ""))

    missing_inputs = _dedupe_preserve([str(item) for item in render_candidate.get("missing_inputs", []) if _safe_text(item)])
    if not missing_inputs:
        missing_inputs = _dedupe_preserve(
            [str(item) for item in getattr(case, "required_context", ()) if _safe_text(item)]
            + [str(item) for item in getattr(case, "evidence_requirements", ()) if _safe_text(item)]
            + [str(item) for item in getattr(case, "memory_requirements", ()) if _safe_text(item)]
            + [str(item) for item in getattr(case, "capability_requirements", ()) if _safe_text(item)]
            + [str(item) for item in getattr(case, "relationship_signals", ()) if _safe_text(item)]
        )

    boundary_notes = _boundary_notes(str(fit_packet.get("fit_status", "blocked")), list(fit_packet.get("blocked_labels", [])), shape, case)
    evidence_notes = _notes_from_requirements("evidence", getattr(case, "evidence_requirements", ()))
    memory_notes = _notes_from_requirements("memory", getattr(case, "memory_requirements", ()))
    capability_notes = _notes_from_requirements("capability", getattr(case, "capability_requirements", ()))
    governance_notes = _notes_from_requirements("governance", tuple(getattr(case, "blocked_if", ())))

    if mode == "evidence_needed" and not evidence_notes:
        evidence_notes.append("evidence:share_the_smallest_relevant_excerpt")
    if mode == "memory_honesty" and not memory_notes:
        memory_notes.append("memory:memory_not_verified_here")
    if mode in {"governance_escalation", "refusal_boundary"} and not governance_notes:
        governance_notes.append("governance:owner_review_or_boundary")
    if mode in {"direct_bounded", "bounded_uncertainty"} and not capability_notes:
        capability_notes.append("capability:keep_claims_bounded")

    response_text = _build_response_text(mode, method, shape, case, fit_packet, normalized_labels, normalized_context_signals, missing_inputs)
    trace = NoModelRenderTrace(
        trace_id=_trace_id(
            {
                "labels": normalized_labels,
                "fit_status": fit_packet.get("fit_status"),
                "render_mode": mode,
                "selected_candidate_id": selected_candidate_id,
                "selected_method_id": selected_method_id,
                "selected_shape_id": selected_shape_id,
                "selected_case_id": selected_case_id,
            }
        ),
        selected_candidate_type=str(render_candidate.get("candidate_type", "")),
        selected_route_id=selected_route_id,
        render_mode=mode,
        response_policy=response_policy,
        fit_status=str(fit_packet.get("fit_status", "blocked")),
        steps=(
            {
                "stage": "fit_check",
                "fit_status": fit_packet.get("fit_status"),
                "blocked": fit_packet.get("blocked"),
                "final_candidate_id": fit_packet.get("final_candidate_id"),
            },
            {
                "stage": "selection",
                "render_mode": mode,
                "response_policy": response_policy,
                "selected_candidate_type": render_candidate.get("candidate_type"),
            },
            {
                "stage": "notes",
                "boundary_note_count": len(boundary_notes),
                "missing_input_count": len(missing_inputs),
            },
        ),
        notes=(
            f"method:{_safe_text(getattr(method, 'name', ''))}",
            f"shape:{_safe_text(getattr(shape, 'name', ''))}",
            f"case:{_safe_text(getattr(case, 'name', ''))}",
        ),
    )

    packet = NoModelBoundedRenderPacket(
        packet_type=PACKET_TYPE_V1,
        turn_labels=normalized_labels,
        safe_context_signal_keys=safe_context_signal_keys,
        fit_summary=fit_summary,
        selected_candidate_id=selected_candidate_id,
        selected_method_id=selected_method_id,
        selected_shape_id=selected_shape_id,
        selected_case_id=selected_case_id,
        selected_route_id=selected_route_id,
        response_policy=response_policy,
        render_mode=mode,
        response_text=response_text,
        render_trace=trace,
        boundary_notes=boundary_notes,
        missing_inputs=missing_inputs,
        evidence_notes=evidence_notes,
        memory_notes=memory_notes,
        capability_notes=capability_notes,
        governance_notes=governance_notes,
        needs_clarification=str(fit_packet.get("fit_status", "")) == "needs_clarification",
        needs_evidence=str(fit_packet.get("fit_status", "")) == "needs_evidence",
        needs_owner_approval=str(fit_packet.get("fit_status", "")) == "needs_owner_approval",
        blocked=bool(fit_packet.get("blocked", False)) or mode == "refusal_boundary",
        blocked_labels=list(fit_packet.get("blocked_labels", [])),
        safe_metadata={
            "fit_packet": fit_packet,
            "fit_summary": fit_summary,
            "render_trace": _json_safe(trace),
            "selected_candidate_type": render_candidate.get("candidate_type"),
            "selected_method_name": _safe_text(getattr(method, "name", "")),
            "selected_shape_name": _safe_text(getattr(shape, "name", "")),
            "selected_case_name": _safe_text(getattr(case, "name", "")),
            "selected_method_family": _safe_text(getattr(method, "family_id", "")),
            "selected_shape_contract": _safe_text(getattr(shape, "output_contract", "")),
            "selected_case_purpose": _safe_text(getattr(case, "purpose", "")),
            "response_policy": response_policy,
            "render_mode": mode,
            "blocked_reason": "blocked_by_fit" if bool(fit_packet.get("blocked", False)) else "",
            "unsafe_context_signal_keys": [key for key in normalized_context_signals.keys() if key not in safe_context_signal_keys],
            "context_flags_detected": {
                key: _truthy(normalized_context_signals.get(key))
                for key in ("runtime_authority", "model_provider_used", "writes_state", "chat_wired", "public_ready")
            },
        },
        runtime_authority=False,
        model_provider_used=False,
        writes_state=False,
        chat_wired=False,
        public_ready=False,
    )
    return packet



def render_no_model_bounded_answer_v1(turn_labels: Any, context_signals: Mapping[str, Any] | None = None) -> NoModelBoundedRenderPacket:
    return build_no_model_bounded_render_packet_v1(turn_labels, context_signals=context_signals)



def to_no_model_bounded_render_json_safe_v1(packet: Any) -> dict[str, Any]:
    return _json_safe(packet)



def validate_no_model_bounded_render_packet_v1(packet: Any) -> bool:
    data = to_no_model_bounded_render_json_safe_v1(packet) if is_dataclass(packet) else dict(packet) if isinstance(packet, Mapping) else None
    if data is None:
        raise ValidationError("packet must be a mapping or dataclass")

    required = [
        "packet_type",
        "turn_labels",
        "safe_context_signal_keys",
        "fit_summary",
        "selected_candidate_id",
        "selected_method_id",
        "selected_shape_id",
        "selected_case_id",
        "selected_route_id",
        "response_policy",
        "render_mode",
        "response_text",
        "render_trace",
        "boundary_notes",
        "missing_inputs",
        "evidence_notes",
        "memory_notes",
        "capability_notes",
        "governance_notes",
        "needs_clarification",
        "needs_evidence",
        "needs_owner_approval",
        "blocked",
        "blocked_labels",
        "safe_metadata",
        "runtime_authority",
        "model_provider_used",
        "writes_state",
        "chat_wired",
        "public_ready",
    ]
    for field_name in required:
        if field_name not in data:
            raise ValidationError(f"missing required field: {field_name}")

    if data["packet_type"] != PACKET_TYPE_V1:
        raise ValidationError("packet_type mismatch")
    if data["render_mode"] not in ALLOWED_RENDER_MODES_V1:
        raise ValidationError("unknown render_mode")
    if data["response_policy"] not in RESPONSE_POLICY_BY_MODE_V1.values():
        raise ValidationError("unknown response_policy")
    if not isinstance(data["response_text"], str) or not data["response_text"].strip():
        raise ValidationError("response_text must be non-empty")

    for field_name in ("runtime_authority", "model_provider_used", "writes_state", "chat_wired", "public_ready"):
        if data[field_name] is not False:
            raise ValidationError(f"{field_name} must be false")

    if not isinstance(data["turn_labels"], list) or not isinstance(data["safe_context_signal_keys"], list):
        raise ValidationError("labels must be lists")
    if not isinstance(data["fit_summary"], dict):
        raise ValidationError("fit_summary must be a dict")
    if not isinstance(data["render_trace"], dict):
        raise ValidationError("render_trace must be a dict")
    for field_name in ("boundary_notes", "missing_inputs", "evidence_notes", "memory_notes", "capability_notes", "governance_notes", "blocked_labels"):
        if not isinstance(data[field_name], list):
            raise ValidationError(f"{field_name} must be a list")
    if not isinstance(data["safe_metadata"], dict):
        raise ValidationError("safe_metadata must be a dict")

    if not data["selected_candidate_id"] or not data["selected_method_id"] or not data["selected_shape_id"] or not data["selected_case_id"] or not data["selected_route_id"]:
        raise ValidationError("selected identifiers must be non-empty")

    if any(marker in data["response_text"].lower() for marker in RAW_LEAK_MARKERS_V1):
        raise ValidationError("raw prompt leakage detected")
    unsafe_context_signal_keys = data["safe_metadata"].get("unsafe_context_signal_keys", [])
    if unsafe_context_signal_keys:
        raise ValidationError("raw prompt leakage detected")
    if any(marker in data["response_text"].lower() for marker in NON_OFFICIAL_MARKERS_V1):
        raise ValidationError("official or identity claim detected")
    if any(token in data["response_text"] for token in ("chat_responder.py", "main.py", "dialogue.py", "chat_ui.py")):
        raise ValidationError("forbidden module reference detected")

    if data["blocked"] and data["render_mode"] != "refusal_boundary":
        raise ValidationError("blocked outputs must use refusal_boundary mode")
    if data["needs_clarification"] and data["render_mode"] != "clarifying_question":
        raise ValidationError("clarification outputs must use clarifying_question mode")
    if data["needs_evidence"] and data["render_mode"] != "evidence_needed":
        raise ValidationError("evidence outputs must use evidence_needed mode")
    if data["needs_owner_approval"] and data["render_mode"] != "governance_escalation":
        raise ValidationError("owner approval outputs must use governance_escalation mode")
    if data["fit_summary"].get("fit_status") == "unknown_friction" and data["render_mode"] != "unknown_friction":
        raise ValidationError("unknown friction outputs must use unknown_friction mode")

    method = METHODS.get(data["selected_method_id"])
    shape = SHAPES.get(data["selected_shape_id"])
    case = CASES.get(data["selected_case_id"])
    if method is None or shape is None or case is None:
        raise ValidationError("selected method/shape/case must exist")

    expected_mode = MODE_BY_SHAPE_ID_V1.get(data["selected_shape_id"])
    if expected_mode is None:
        raise ValidationError("unknown selected shape for render mode validation")
    if expected_mode != data["render_mode"]:
        raise ValidationError("render mode must match selected shape")

    if data["selected_shape_id"] not in getattr(method, "compatible_shape_ids", ()) and data["selected_method_id"] not in getattr(shape, "compatible_method_ids", ()):
        raise ValidationError("selected method and shape are incompatible")
    if data["selected_method_id"] not in getattr(case, "allowed_method_ids", ()) or data["selected_shape_id"] not in getattr(case, "allowed_shape_ids", ()):
        raise ValidationError("selected case is incompatible with method or shape")

    fit_summary = data["fit_summary"]
    if fit_summary.get("packet_type") != "response_fit_self_check_v1":
        raise ValidationError("fit_summary packet_type mismatch")
    if fit_summary.get("selected_candidate_id") == "" and not data["blocked"]:
        raise ValidationError("fit summary must include selected candidate when not blocked")

    if any(flag for flag in (data["runtime_authority"], data["model_provider_used"], data["writes_state"], data["chat_wired"], data["public_ready"])):
        raise ValidationError("authority drift detected")
    if data["safe_metadata"].get("blocked_reason") == "blocked_by_fit" and not data["blocked"]:
        raise ValidationError("blocked_reason mismatch")
    if data["safe_metadata"].get("render_mode") != data["render_mode"]:
        raise ValidationError("render mode metadata mismatch")
    context_flags = data["safe_metadata"].get("context_flags_detected", {})
    if any(_truthy(context_flags.get(key)) for key in ("runtime_authority", "model_provider_used", "writes_state", "chat_wired", "public_ready")):
        raise ValidationError("authority drift detected")
    fit_blocked_labels = data["fit_summary"].get("fit_packet", {}).get("blocked_labels", [])
    if any(label in {"runtime_authority_requested", "model_provider_output_requested", "raw_persistence_requested", "final_answer_authority_requested", "official_claim_requested", "turing_claim_requested", "intelligence_claim_requested", "certification_claim_requested", "search_call_authority_requested", "advisor_call_authority_requested", "automatic_lesson_promotion_requested", "raw_prompt_provided", "raw_response_text_provided", "raw_transcript_provided", "raw_context_provided", "private_memory_requested", "hidden_material_requested", "benchmark_material_requested"} for label in fit_blocked_labels):
        raise ValidationError("authority drift detected")

    return True


@dataclass(frozen=True, slots=True)
class NoModelRenderSummary:
    packet_type: str
    render_mode: str
    response_policy: str
    selected_candidate_id: str
    selected_method_id: str
    selected_shape_id: str
    selected_case_id: str
    selected_route_id: str
    fit_status: str
    blocked: bool
    response_length: int



def summarize_no_model_bounded_render_packet_v1(packet: Any) -> NoModelRenderSummary:
    data = to_no_model_bounded_render_json_safe_v1(packet)
    return NoModelRenderSummary(
        packet_type=str(data.get("packet_type", PACKET_TYPE_V1)),
        render_mode=str(data.get("render_mode", "direct_bounded")),
        response_policy=str(data.get("response_policy", "bounded_direct_answer")),
        selected_candidate_id=str(data.get("selected_candidate_id", "")),
        selected_method_id=str(data.get("selected_method_id", "")),
        selected_shape_id=str(data.get("selected_shape_id", "")),
        selected_case_id=str(data.get("selected_case_id", "")),
        selected_route_id=str(data.get("selected_route_id", "")),
        fit_status=str(data.get("fit_summary", {}).get("fit_status", "blocked")),
        blocked=bool(data.get("blocked", False)),
        response_length=len(str(data.get("response_text", ""))),
    )


__all__ = [
    "PACKET_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "TRACE_TYPE_V1",
    "RENDERED_ANSWER_TYPE_V1",
    "NoModelRenderTrace",
    "NoModelRenderedAnswer",
    "NoModelRenderSummary",
    "NoModelBoundedRenderPacket",
    "build_no_model_bounded_render_packet_v1",
    "render_no_model_bounded_answer_v1",
    "validate_no_model_bounded_render_packet_v1",
    "summarize_no_model_bounded_render_packet_v1",
    "to_no_model_bounded_render_json_safe_v1",
]
