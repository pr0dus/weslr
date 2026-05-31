"""Metadata-only candidate response formation v1.

This module is intentionally pure, deterministic, and fail-closed.
It forms bounded candidate response plans from the selector / friction stack
without generating final prose, wiring runtime behavior, or calling models.

No file I/O, network I/O, subprocess execution, provider/search/advisor calls,
chat/runtime wiring, or state writes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping

from weslr.answer_method_catalog import build_answer_method_catalog_v1
from weslr.answer_shape_catalog import build_answer_shape_catalog_v1
from weslr.cognition_case_registry import build_cognition_case_registry_v1
from weslr.response_method_selector import (
    select_response_route_v1,
    summarize_response_selection_packet_v1,
    to_response_selection_json_safe_v1,
    validate_response_selection_packet_v1,
)
from weslr.unknown_prompt_friction_router import (
    route_unknown_prompt_friction_v1,
    summarize_unknown_prompt_friction_packet_v1,
    to_unknown_prompt_friction_json_safe_v1,
    validate_unknown_prompt_friction_packet_v1,
)

PACKET_TYPE_V1 = "candidate_response_formation_v1"
SUMMARY_TYPE_V1 = "candidate_response_formation_summary_v1"
CANDIDATE_TYPE_V1 = "candidate_response_path_v1"
REJECTION_TYPE_V1 = "candidate_response_rejection_v1"

_ALLOWED_CANDIDATE_TYPES_V1 = {
    "direct_bounded_candidate",
    "clarification_candidate",
    "bounded_uncertainty_candidate",
    "refusal_boundary_candidate",
    "evidence_needed_candidate",
    "partial_supported_candidate",
    "stepwise_plan_candidate",
    "implementation_plan_candidate",
    "workflow_next_lane_candidate",
    "governance_escalation_candidate",
    "teaching_explanation_candidate",
    "language_discovery_candidate",
    "scientific_discovery_guidance_candidate",
    "benchmark_evaluation_candidate",
    "unknown_friction_candidate",
    "memory_honesty_candidate",
    "continuity_recap_candidate",
    "relationship_feedback_candidate",
    "correction_repair_candidate",
    "conflict_contradiction_candidate",
    "non_canned_specificity_candidate",
    "directness_concern_candidate",
}

_ALLOWED_ROUTE_IDS_V1 = {
    "identity_status_route",
    "capability_orientation_route",
    "memory_honesty_route",
    "continuity_route",
    "clarification_route",
    "uncertainty_route",
    "refusal_boundary_route",
    "evidence_needed_route",
    "partial_supported_route",
    "ordinary_task_route",
    "implementation_planning_route",
    "workflow_next_lane_route",
    "governance_escalation_route",
    "teaching_explanation_route",
    "language_discovery_route",
    "scientific_discovery_route",
    "benchmark_evaluation_route",
    "unknown_word_phrase_route",
    "unknown_intent_route",
    "unknown_capability_route",
    "friction_repeated_failure_route",
    "relationship_feedback_route",
    "correction_repair_route",
    "conflict_contradiction_route",
    "non_canned_specificity_route",
    "directness_concern_route",
}

_SELECTOR_IDS_BY_ROUTE_V1 = {
    "identity_status_route": ("method_identity_status", "shape_identity_status", "case_identity_status"),
    "capability_orientation_route": ("method_capability_orientation", "shape_capability_orientation", "case_capability_orientation"),
    "memory_honesty_route": ("method_memory_honesty", "shape_memory_honesty", "case_memory_honesty"),
    "continuity_route": ("method_continuity", "shape_continuity", "case_continuity"),
    "clarification_route": ("method_clarification", "shape_clarification", "case_clarification"),
    "uncertainty_route": ("method_uncertainty", "shape_uncertainty", "case_uncertainty"),
    "refusal_boundary_route": ("method_refusal_boundary", "shape_refusal_boundary", "case_refusal_boundary"),
    "evidence_needed_route": ("method_evidence_needed", "shape_evidence_needed", "case_evidence_needed"),
    "partial_supported_route": ("method_partial_supported", "shape_partial_supported", "case_partial_supported"),
    "ordinary_task_route": ("method_ordinary_task", "shape_ordinary_task", "case_ordinary_task"),
    "implementation_planning_route": ("method_implementation_planning", "shape_implementation_planning", "case_implementation_planning"),
    "workflow_next_lane_route": ("method_workflow_next_lane", "shape_workflow_next_lane", "case_workflow_next_lane"),
    "governance_escalation_route": ("method_governance_escalation", "shape_governance_escalation", "case_governance_escalation"),
    "teaching_explanation_route": ("method_teaching_explanation", "shape_teaching_explanation", "case_teaching_explanation"),
    "language_discovery_route": ("method_language_discovery", "shape_language_discovery", "case_language_discovery"),
    "scientific_discovery_route": ("method_scientific_discovery", "shape_scientific_discovery", "case_scientific_discovery"),
    "benchmark_evaluation_route": ("method_benchmark_evaluation", "shape_benchmark_evaluation", "case_benchmark_evaluation"),
    "unknown_word_phrase_route": ("method_unknown_word_phrase", "shape_unknown_word_phrase", "case_unknown_word_phrase"),
    "unknown_intent_route": ("method_unknown_intent", "shape_unknown_intent", "case_unknown_intent"),
    "unknown_capability_route": ("method_unknown_capability", "shape_unknown_capability", "case_unknown_capability"),
    "friction_repeated_failure_route": ("method_friction_repeated_failure", "shape_friction_repeated_failure", "case_friction_repeated_failure"),
    "relationship_feedback_route": ("method_relationship_feedback", "shape_relationship_feedback", "case_relationship_feedback"),
    "correction_repair_route": ("method_correction_repair", "shape_correction_repair", "case_correction_repair"),
    "conflict_contradiction_route": ("method_conflict_contradiction", "shape_conflict_contradiction", "case_conflict_contradiction"),
    "non_canned_specificity_route": ("method_non_canned_specificity", "shape_non_canned_specificity", "case_non_canned_specificity"),
    "directness_concern_route": ("method_directness_concern", "shape_directness_concern", "case_directness_concern"),
}

_ALLOWED_SELECTOR_METHOD_IDS_V1 = {method_id for method_id, _, _ in _SELECTOR_IDS_BY_ROUTE_V1.values()}
_ALLOWED_SELECTOR_SHAPE_IDS_V1 = {shape_id for _, shape_id, _ in _SELECTOR_IDS_BY_ROUTE_V1.values()}
_ALLOWED_SELECTOR_CASE_IDS_V1 = {case_id for _, _, case_id in _SELECTOR_IDS_BY_ROUTE_V1.values()}

_FORBIDDEN_KEYS_V1 = {
    "raw_prompt_text",
    "raw_response_text",
    "prompt_text",
    "response_text",
    "final_answer_text",
    "final_answer_prose",
    "answer_draft_text",
    "composed_reply_text",
    "live_dialogue_transcript",
    "live_dialogue_transcript_content",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "answer_key",
    "private_content",
    "hidden_prompt",
}


@dataclass(frozen=True, slots=True)
class CandidateResponsePath:
    candidate_id: str
    candidate_type: str
    method_id: str
    shape_id: str
    case_id: str
    route_id: str
    purpose: str
    answer_policy: str
    why_candidate_exists: str
    required_inputs: tuple[str, ...]
    missing_inputs: tuple[str, ...]
    acceptance_conditions: tuple[str, ...]
    rejection_conditions: tuple[str, ...]
    risk_labels: tuple[str, ...]
    quality_pressure_labels: tuple[str, ...]
    provenance_requirements: tuple[str, ...]
    selection_score: float
    selected: bool
    rejected: bool
    rejection_reason: str
    generates_final_text: bool = False


@dataclass(frozen=True, slots=True)
class CandidateResponseRejection:
    candidate_id: str
    candidate_type: str
    route_id: str
    method_id: str
    shape_id: str
    case_id: str
    rejection_reason: str
    blocked_labels: tuple[str, ...]
    selection_score: float


@dataclass(frozen=True, slots=True)
class CandidateResponseFormationPacket:
    packet_type: str
    turn_labels: tuple[str, ...]
    safe_context_signal_keys: tuple[str, ...]
    friction_summary: dict[str, Any]
    selector_summary: dict[str, Any]
    candidate_count: int
    candidates: tuple[CandidateResponsePath, ...]
    rejected_candidates: tuple[CandidateResponseRejection, ...]
    selected_candidate_id: str
    candidate_family: str
    answer_obligation: str
    required_inputs: tuple[str, ...]
    missing_inputs: tuple[str, ...]
    boundary_labels: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    memory_requirements: tuple[str, ...]
    capability_requirements: tuple[str, ...]
    relationship_requirements: tuple[str, ...]
    proposed_answer_policy: str
    needs_clarification: bool
    needs_evidence: bool
    needs_owner_approval: bool
    blocked: bool
    blocked_labels: tuple[str, ...]
    safe_metadata: dict[str, Any]
    runtime_authority: bool = False
    model_provider_used: bool = False
    generates_final_text: bool = False
    writes_state: bool = False


@dataclass(frozen=True, slots=True)
class CandidateResponseFormationSummary:
    packet_type: str
    candidate_count: int
    selected_candidate_id: str
    selected_candidate_type: str
    candidate_family: str
    route_id: str
    method_id: str
    shape_id: str
    case_id: str
    blocked: bool
    needs_clarification: bool
    needs_evidence: bool
    needs_owner_approval: bool
    proposed_answer_policy: str
    blocked_labels: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _CandidateVariant:
    candidate_type: str
    route_id: str
    method_id: str
    shape_id: str
    case_id: str
    purpose: str
    answer_policy: str
    why_candidate_exists: str
    trigger_labels: tuple[str, ...]
    acceptance_conditions: tuple[str, ...]
    rejection_conditions: tuple[str, ...]
    risk_labels: tuple[str, ...]
    quality_pressure_labels: tuple[str, ...]
    candidate_family: str
    route_family_hint: str


_METHODS = {method.method_id: method for method in build_answer_method_catalog_v1().methods}
_SHAPES = {shape.shape_id: shape for shape in build_answer_shape_catalog_v1().shapes}
_CASES = {case.case_id: case for case in build_cognition_case_registry_v1().cases}


def _dedupe_preserve(items: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _normalize_labels(turn_labels: Any) -> tuple[str, ...]:
    if turn_labels is None:
        return ()
    if isinstance(turn_labels, str):
        values = [turn_labels]
    elif isinstance(turn_labels, Mapping):
        values = [str(v) for v in turn_labels.values()]
    else:
        try:
            values = [str(v) for v in turn_labels]
        except TypeError:
            values = [str(turn_labels)]
    normalized: list[str] = []
    for value in values:
        text = _safe_text(value).lower().replace("_", " ").replace("/", " ").replace("-", " ")
        if text:
            normalized.append(" ".join(text.split()))
    return _dedupe_preserve(normalized)


def _normalize_context_signals(context_signals: Any) -> dict[str, Any]:
    if not context_signals or not isinstance(context_signals, Mapping):
        return {}
    return {str(key): value for key, value in context_signals.items()}


def _is_truthy(value: Any) -> bool:
    return bool(value is True or value == 1 or str(value).strip().lower() in {"true", "yes", "1", "on"})


def _contains_any(blob: str, phrases: Iterable[str]) -> bool:
    return any(phrase in blob for phrase in phrases)


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=_safe_text)]
    return value


def _safe_context_signal_keys(context_signals: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(_dedupe_preserve(context_signals.keys())))


def _augment_turn_labels_for_selection(normalized_labels: tuple[str, ...]) -> tuple[str, ...]:
    labels = list(normalized_labels)
    blob = " ".join(normalized_labels)
    if _contains_any(blob, ("unsafe", "privacy", "not allowed", "forbidden", "boundary")):
        labels.extend(["safety boundary", "refusal"])
    if _contains_any(blob, ("template", "generic", "boilerplate", "canned")):
        labels.extend(["non canned specificity", "specific", "tailored"])
    return _dedupe_preserve(labels)


def _get_record_by_route(route_id: str) -> tuple[Any, Any, Any]:
    if route_id == "identity_status_route":
        return _METHODS["verified_identity_status_answer_v1"], _SHAPES["direct_bounded_answer"], _CASES["identity_self_description_case"]
    if route_id == "capability_orientation_route":
        return _METHODS["capability_orientation_answer_v1"], _SHAPES["direct_bounded_answer"], _CASES["capability_orientation_case"]
    if route_id == "memory_honesty_route":
        return _METHODS["memory_report_answer_v1"], _SHAPES["memory_honesty_answer"], _CASES["memory_honesty_case"]
    if route_id == "continuity_route":
        return _METHODS["continuity_thread_answer_v1"], _SHAPES["continuity_thread_recap_answer"], _CASES["continuity_thread_recap_case"]
    if route_id == "clarification_route":
        return _METHODS["clarifying_question_answer_v1"], _SHAPES["clarifying_question"], _CASES["clarification_needed_case"]
    if route_id == "uncertainty_route":
        return _METHODS["bounded_uncertainty_answer_v1"], _SHAPES["bounded_uncertainty_answer"], _CASES["bounded_uncertainty_case"]
    if route_id == "refusal_boundary_route":
        return _METHODS["refusal_boundary_answer_v1"], _SHAPES["refusal_boundary_answer"], _CASES["refusal_boundary_case"]
    if route_id == "evidence_needed_route":
        return _METHODS["evidence_needed_answer_v1"], _SHAPES["evidence_needed_answer"], _CASES["evidence_needed_case"]
    if route_id == "partial_supported_route":
        return _METHODS["partial_answer_supported_portion_answer_v1"], _SHAPES["partial_supported_answer"], _CASES["partial_supported_case"]
    if route_id == "ordinary_task_route":
        return _METHODS["ordinary_task_planning_answer_v1"], _SHAPES["stepwise_plan_answer"], _CASES["ordinary_task_planning_case"]
    if route_id == "implementation_planning_route":
        return _METHODS["implementation_planning_answer_v1"], _SHAPES["implementation_plan_answer"], _CASES["implementation_planning_case"]
    if route_id == "workflow_next_lane_route":
        return _METHODS["workflow_next_lane_answer_v1"], _SHAPES["workflow_next_lane_answer"], _CASES["workflow_next_lane_case"]
    if route_id == "governance_escalation_route":
        return _METHODS["governance_escalation_proposal_v1"], _SHAPES["governance_escalation_answer"], _CASES["governance_escalation_case"]
    if route_id == "teaching_explanation_route":
        return _METHODS["teaching_explanation_answer_v1"], _SHAPES["teaching_explanation_answer"], _CASES["teaching_explanation_case"]
    if route_id == "language_discovery_route":
        return _METHODS["language_grammar_vocabulary_discovery_answer_v1"], _SHAPES["language_discovery_explanation_answer"], _CASES["language_discovery_explanation_case"]
    if route_id == "scientific_discovery_route":
        return _METHODS["scientific_discovery_capability_guidance_answer_v1"], _SHAPES["scientific_discovery_guidance_answer"], _CASES["scientific_discovery_guidance_case"]
    if route_id == "benchmark_evaluation_route":
        return _METHODS["benchmark_evaluation_answer_v1"], _SHAPES["benchmark_evaluation_summary_answer"], _CASES["benchmark_evaluation_summary_case"]
    if route_id == "unknown_word_phrase_route":
        return _METHODS["unknown_engine_branch_friction_answer_v1"], _SHAPES["unknown_friction_branch_answer"], _CASES["unknown_word_or_phrase_case"]
    if route_id == "unknown_intent_route":
        return _METHODS["unknown_engine_branch_friction_answer_v1"], _SHAPES["unknown_friction_branch_answer"], _CASES["unknown_intent_case"]
    if route_id == "unknown_capability_route":
        return _METHODS["unknown_engine_branch_friction_answer_v1"], _SHAPES["unknown_friction_branch_answer"], _CASES["unknown_capability_request_case"]
    if route_id == "friction_repeated_failure_route":
        return _METHODS["unknown_engine_branch_friction_answer_v1"], _SHAPES["unknown_friction_branch_answer"], _CASES["friction_repeated_failure_case"]
    if route_id == "relationship_feedback_route":
        return _METHODS["relationship_feedback_answer_v1"], _SHAPES["relationship_feedback_answer"], _CASES["relationship_feedback_case"]
    if route_id == "correction_repair_route":
        return _METHODS["correction_repair_answer_v1"], _SHAPES["correction_repair_answer"], _CASES["correction_repair_case"]
    if route_id == "conflict_contradiction_route":
        return _METHODS["conflict_contradiction_handling_answer_v1"], _SHAPES["conflict_contradiction_answer"], _CASES["conflict_contradiction_case"]
    if route_id == "non_canned_specificity_route":
        return _METHODS["non_cannedness_pressure_v1"], _SHAPES["non_canned_specific_answer"], _CASES["non_canned_specificity_pressure_case"]
    if route_id == "directness_concern_route":
        return _METHODS["directness_concern_integration_self_check_v1"], _SHAPES["directness_concern_integrated_answer"], _CASES["directness_concern_integration_case"]
    raise ValueError(f"unknown route_id: {route_id}")


_CANDIDATE_VARIANTS_V1: tuple[_CandidateVariant, ...] = (
    _CandidateVariant(
        "direct_bounded_candidate",
        "identity_status_route",
        "verified_identity_status_answer_v1",
        "direct_bounded_answer",
        "identity_self_description_case",
        "direct bounded answer",
        "answer_directly_bounded",
        "direct clear labels and bounded identity/status claims",
        ("identity", "status", "who are you", "what are you", "about you"),
        ("clear intent", "sufficient grounding"),
        ("missing context", "unsafe boundary", "evidence gap"),
        ("low overclaim risk", "bounded directness"),
        ("keep claims scoped",),
        "identity_status",
        "identity_status",
    ),
    _CandidateVariant(
        "clarification_candidate",
        "clarification_route",
        "clarifying_question_answer_v1",
        "clarifying_question",
        "clarification_needed_case",
        "clarify before answering",
        "ask_clarifying_question",
        "remove ambiguity with the smallest useful question",
        ("clarify", "clarification", "ambiguous", "unclear", "missing"),
        ("missing context slots", "uncertainty labels"),
        ("sufficient context", "already answered"),
        ("ambiguity pressure",),
        ("keep the question small",),
        "boundary_uncertainty",
        "clarification",
    ),
    _CandidateVariant(
        "bounded_uncertainty_candidate",
        "uncertainty_route",
        "bounded_uncertainty_answer_v1",
        "bounded_uncertainty_answer",
        "bounded_uncertainty_case",
        "state bounded uncertainty",
        "state_bounded_uncertainty",
        "preserve uncertainty instead of inventing confidence",
        ("uncertain", "uncertainty", "unsure", "maybe", "not sure"),
        ("uncertainty labels", "confidence", "evidence sufficiency"),
        ("evidence sufficient", "confidence overstated"),
        ("calibration pressure",),
        ("avoid fake certainty",),
        "boundary_uncertainty",
        "uncertainty",
    ),
    _CandidateVariant(
        "refusal_boundary_candidate",
        "refusal_boundary_route",
        "refusal_boundary_answer_v1",
        "refusal_boundary_answer",
        "refusal_boundary_case",
        "refuse with boundary",
        "refuse_with_boundary",
        "refuse unsafe or unauthorized requests while staying useful",
        ("refuse", "refusal", "privacy", "safety", "boundary", "not allowed"),
        ("denied authority flags", "blocked labels", "safety boundary"),
        ("no boundary issue", "runtime authorization implied"),
        ("boundary pressure",),
        ("keep the refusal useful",),
        "boundary_uncertainty",
        "refusal",
    ),
    _CandidateVariant(
        "evidence_needed_candidate",
        "evidence_needed_route",
        "evidence_needed_answer_v1",
        "evidence_needed_answer",
        "evidence_needed_case",
        "request evidence",
        "request_evidence",
        "stronger claims need evidence before proceeding",
        ("evidence", "source", "prove", "current", "latest"),
        ("evidence need", "source scope", "claim burden"),
        ("evidence sufficient", "raw transcript requested"),
        ("evidence pressure",),
        ("point to the next safe evidence step",),
        "boundary_uncertainty",
        "evidence",
    ),
    _CandidateVariant(
        "partial_supported_candidate",
        "partial_supported_route",
        "partial_answer_supported_portion_answer_v1",
        "partial_supported_answer",
        "partial_supported_case",
        "answer the supported part",
        "give_partial_supported_answer",
        "answer the supported part and label the unsupported remainder",
        ("partial", "supported", "portion", "split", "some parts"),
        ("supported facts", "unsupported remainder", "evidence gaps"),
        ("all-or-nothing refusal only", "no supported portion exists"),
        ("support boundary pressure",),
        ("split supported from unsupported",),
        "boundary_uncertainty",
        "partial_support",
    ),
    _CandidateVariant(
        "stepwise_plan_candidate",
        "ordinary_task_route",
        "ordinary_task_planning_answer_v1",
        "stepwise_plan_answer",
        "ordinary_task_planning_case",
        "stepwise task plan",
        "answer_with_stepwise_plan",
        "provide safe step planning for ordinary tasks",
        ("task", "plan", "steps", "workflow", "checklist"),
        ("task markers", "constraints", "missing context", "tool need"),
        ("unsafe action", "needs operator approval"),
        ("task pressure",),
        ("keep steps concrete",),
        "task_workflow",
        "task",
    ),
    _CandidateVariant(
        "implementation_plan_candidate",
        "implementation_planning_route",
        "implementation_planning_answer_v1",
        "implementation_plan_answer",
        "implementation_planning_case",
        "implementation plan",
        "answer_with_implementation_plan",
        "turn a design gap into a constrained implementation plan",
        ("implementation", "build", "code", "lane", "next lane"),
        ("target gaps", "answer-shape policy", "authority calibration"),
        ("runtime authority", "no design gap"),
        ("implementation pressure",),
        ("do not become a live roadmap engine",),
        "task_workflow",
        "implementation",
    ),
    _CandidateVariant(
        "workflow_next_lane_candidate",
        "workflow_next_lane_route",
        "workflow_next_lane_answer_v1",
        "workflow_next_lane_answer",
        "workflow_next_lane_case",
        "workflow next lane",
        "answer_with_next_lane_plan",
        "recommend the next lane based on readiness and blockers",
        ("next lane", "sequence", "roadmap", "what next", "lane"),
        ("gap labels", "readiness", "blocked flags"),
        ("no sequencing context", "single-turn direct answer fit"),
        ("sequencing pressure",),
        ("recommend a lane, not an authority claim",),
        "task_workflow",
        "next_lane",
    ),
    _CandidateVariant(
        "governance_escalation_candidate",
        "governance_escalation_route",
        "governance_escalation_proposal_v1",
        "governance_escalation_answer",
        "governance_escalation_case",
        "governance escalation",
        "escalate_to_owner_review",
        "propose operator review when authority is missing or blocked",
        ("approval", "escalate", "operator review", "decision needed", "blocked"),
        ("approval requirement", "denied authority fields"),
        ("no approval needed", "runtime authorization implied"),
        ("approval pressure",),
        ("do not self-authorize",),
        "task_workflow",
        "governance",
    ),
    _CandidateVariant(
        "teaching_explanation_candidate",
        "teaching_explanation_route",
        "teaching_explanation_answer_v1",
        "teaching_explanation_answer",
        "teaching_explanation_case",
        "teaching explanation",
        "route_language_discovery_explanation",
        "explain concepts in a teachable, human-readable form",
        ("teach", "teaching", "explain", "explanation", "education"),
        ("audience level", "vocabulary", "domain context", "evidence needs"),
        ("no teaching intent", "boundary refusal required"),
        ("explanation pressure",),
        ("stay teachable, not encyclopedic",),
        "teaching_explanation_discovery",
        "teaching",
    ),
    _CandidateVariant(
        "language_discovery_candidate",
        "language_discovery_route",
        "language_grammar_vocabulary_discovery_answer_v1",
        "language_discovery_explanation_answer",
        "language_discovery_explanation_case",
        "language discovery",
        "route_language_discovery_explanation",
        "translate internal form into human-understandable language",
        ("language", "grammar", "vocabulary", "translation", "words"),
        ("internal signals", "preferred vocabulary", "target audience"),
        ("translation theater", "unknown language claims", "runtime authority"),
        ("language pressure",),
        ("do not pretend to magically discover a language",),
        "teaching_explanation_discovery",
        "language",
    ),
    _CandidateVariant(
        "scientific_discovery_guidance_candidate",
        "scientific_discovery_route",
        "scientific_discovery_capability_guidance_answer_v1",
        "scientific_discovery_guidance_answer",
        "scientific_discovery_guidance_case",
        "scientific discovery guidance",
        "route_capability_orientation",
        "guide research and discovery with a staged workflow and boundary notes",
        ("scientific", "research", "discovery", "experiment", "capability guidance"),
        ("candidate generation constraints", "novelty", "structural sanity", "evidence gates"),
        ("official discovery claim", "no research framing"),
        ("research pressure",),
        ("guide discovery without claiming discovery",),
        "teaching_explanation_discovery",
        "scientific",
    ),
    _CandidateVariant(
        "benchmark_evaluation_candidate",
        "benchmark_evaluation_route",
        "benchmark_evaluation_answer_v1",
        "benchmark_evaluation_summary_answer",
        "benchmark_evaluation_summary_case",
        "benchmark evaluation",
        "answer_with_evaluation_summary",
        "explain evaluation status without asserting official benchmark results",
        ("benchmark", "evaluation", "turing", "readiness", "assessment"),
        ("task schema", "trace", "conflicts", "legibility", "anti-gaming"),
        ("official scoring claim", "certification claim"),
        ("evaluation pressure",),
        ("stay non-official and metadata-only",),
        "teaching_explanation_discovery",
        "evaluation",
    ),
    _CandidateVariant(
        "unknown_friction_candidate",
        "unknown_intent_route",
        "unknown_engine_branch_friction_answer_v1",
        "unknown_friction_branch_answer",
        "unknown_intent_case",
        "unknown friction",
        "route_unknown_friction",
        "represent unknowns and repeated friction as bounded metadata",
        ("unknown", "unclear", "ambiguous", "stuck", "friction", "failed"),
        ("unknown signal",),
        ("oracle framing", "meaning certainty"),
        ("friction pressure",),
        ("stay explicit about uncertainty and friction",),
        "unknown_friction",
        "unknown",
    ),
    _CandidateVariant(
        "memory_honesty_candidate",
        "memory_honesty_route",
        "memory_report_answer_v1",
        "memory_honesty_answer",
        "memory_honesty_case",
        "memory honesty",
        "route_memory_honesty",
        "state what memory is available and what is not",
        ("memory", "remember", "recall", "continuity", "do you remember"),
        ("memory availability", "scope", "freshness", "trust labels"),
        ("raw private memory requested", "fake memory claims"),
        ("memory pressure",),
        ("do not imply total recall",),
        "memory_continuity",
        "memory",
    ),
    _CandidateVariant(
        "continuity_recap_candidate",
        "continuity_route",
        "continuity_thread_answer_v1",
        "continuity_thread_recap_answer",
        "continuity_thread_recap_case",
        "continuity recap",
        "route_continuity_recap",
        "preserve the current thread and prior decisions",
        ("continuity", "thread", "follow up", "previous point", "what were we doing"),
        ("continuity state", "recent turns", "timeline anchors"),
        ("thread unavailable", "new topic without continuity need"),
        ("continuity pressure",),
        ("stay thread-aware and bounded",),
        "memory_continuity",
        "continuity",
    ),
    _CandidateVariant(
        "relationship_feedback_candidate",
        "relationship_feedback_route",
        "relationship_feedback_answer_v1",
        "relationship_feedback_answer",
        "relationship_feedback_case",
        "relationship feedback",
        "route_relationship_feedback",
        "acknowledge user signals without fake empathy",
        ("relationship", "feedback", "tone", "trust", "preference"),
        ("relationship context", "trust state", "emotional pressure"),
        ("fake empathy", "relationship roleplay", "tone reset without context"),
        ("relationship pressure",),
        ("acknowledge, do not perform",),
        "relationship_correction_continuity",
        "relationship",
    ),
    _CandidateVariant(
        "correction_repair_candidate",
        "correction_repair_route",
        "correction_repair_answer_v1",
        "correction_repair_answer",
        "correction_repair_case",
        "correction repair",
        "route_correction_repair",
        "repair the answer after a user correction by changing shape",
        ("correction", "wrong", "revise", "fix", "actually"),
        ("correction history", "continuity state", "answer-shape gap"),
        ("no correction history", "no shape change needed"),
        ("correction pressure",),
        ("change shape, not only wording",),
        "relationship_correction_continuity",
        "correction",
    ),
    _CandidateVariant(
        "conflict_contradiction_candidate",
        "conflict_contradiction_route",
        "conflict_contradiction_handling_answer_v1",
        "conflict_contradiction_answer",
        "conflict_contradiction_case",
        "conflict contradiction",
        "route_conflict_contradiction",
        "preserve contradictions instead of erasing them",
        ("conflict", "contradiction", "inconsistent", "both true", "clash"),
        ("conflict records", "evidence conflicts", "missing assumptions"),
        ("no contradiction", "final prose required"),
        ("conflict pressure",),
        ("do not smooth over real tension",),
        "relationship_correction_continuity",
        "conflict",
    ),
    _CandidateVariant(
        "non_canned_specificity_candidate",
        "non_canned_specificity_route",
        "non_cannedness_pressure_v1",
        "non_canned_specific_answer",
        "non_canned_specificity_pressure_case",
        "non-canned specificity",
        "answer_with_non_canned_specificity",
        "choose a response shape that stays specific and avoids template feel",
        ("canned", "template", "boilerplate", "generic", "repeated"),
        ("repetition markers", "specificity markers", "user concern"),
        ("generic fallback only", "template locked"),
        ("specificity pressure",),
        ("keep the response specific",),
        "response_shape_quality",
        "specificity",
    ),
    _CandidateVariant(
        "directness_concern_candidate",
        "directness_concern_route",
        "directness_concern_integrated_self_check_v1",
        "directness_concern_integrated_answer",
        "directness_concern_integration_case",
        "directness / concern integrated",
        "answer_with_directness_concern",
        "tune directness, concern handling, and self-check before final response choice",
        ("directness", "concern", "too direct", "friction", "loaded"),
        ("concern slot", "frustration signal", "directness pressure", "boundary calibration"),
        ("no directness tension", "fake empathy", "runtime authority"),
        ("directness pressure",),
        ("stay grounded and not performative",),
        "response_shape_quality",
        "directness",
    ),
)


def _candidate_id(candidate_type: str, route_id: str) -> str:
    return f"{candidate_type}:{route_id}"


def _variant_lookup() -> dict[str, _CandidateVariant]:
    return {variant.candidate_type: variant for variant in _CANDIDATE_VARIANTS_V1}


_VARIANTS_BY_TYPE = _variant_lookup()


def _candidate_source_refs(method: Any, shape: Any, case: Any) -> tuple[str, ...]:
    refs: list[str] = []
    for source in getattr(method, "source_refs", ()):
        refs.append(str(source))
    for source in getattr(shape, "source_refs", ()):
        refs.append(str(source))
    for source in getattr(case, "source_refs", ()):
        refs.append(str(source))
    return _dedupe_preserve(refs)


def _record_inputs(method: Any, shape: Any, case: Any) -> tuple[str, ...]:
    inputs: list[str] = []
    for item in getattr(method, "required_inputs", ()):
        inputs.append(str(item))
    for item in getattr(shape, "required_inputs", ()):
        inputs.append(str(item))
    for item in getattr(case, "required_context", ()):
        inputs.append(str(item))
    return _dedupe_preserve(inputs)


def _record_missing_inputs(route_id: str, friction_summary: Mapping[str, Any], selector_summary: Mapping[str, Any], labels_blob: str) -> tuple[str, ...]:
    missing: list[str] = []
    if friction_summary.get("needs_clarification") or selector_summary.get("needs_clarification"):
        missing.append("missing context")
    if friction_summary.get("needs_evidence") or selector_summary.get("needs_evidence"):
        missing.append("missing evidence")
    if friction_summary.get("needs_owner_approval") or selector_summary.get("needs_owner_approval"):
        missing.append("needs owner approval")
    if not labels_blob:
        missing.append("no usable turn labels")
    if route_id in {"unknown_word_phrase_route", "unknown_intent_route", "unknown_capability_route", "friction_repeated_failure_route"}:
        missing.append("unknown or friction path")
    return _dedupe_preserve(missing)


def _requirements_from_case(case: Any) -> tuple[str, str, str, str]:
    evidence_requirements = tuple(str(item) for item in getattr(case, "evidence_requirements", ()))
    memory_requirements = tuple(str(item) for item in getattr(case, "memory_requirements", ()))
    capability_requirements = tuple(str(item) for item in getattr(case, "capability_requirements", ()))
    relationship_requirements = tuple(str(item) for item in getattr(case, "relationship_signals", ()))
    return evidence_requirements, memory_requirements, capability_requirements, relationship_requirements


def _policy_to_obligation(policy: str) -> str:
    return {
        "answer_directly_bounded": "bounded_direct_answer",
        "ask_clarifying_question": "clarify_before_answering",
        "state_bounded_uncertainty": "bounded_uncertainty",
        "request_evidence": "evidence_first",
        "give_partial_supported_answer": "partial_supported_answer",
        "route_unknown_friction": "unknown_friction_handling",
        "route_language_discovery_explanation": "language_discovery_help",
        "route_capability_orientation": "capability_orientation",
        "route_memory_honesty": "memory_honesty",
        "route_continuity_recap": "continuity_recap",
        "route_correction_repair": "correction_repair",
        "route_relationship_feedback": "relationship_feedback",
        "route_conflict_contradiction": "conflict_preservation",
        "escalate_to_owner_review": "owner_review",
        "refuse_with_boundary": "boundary_refusal",
        "answer_with_stepwise_plan": "stepwise_plan",
        "answer_with_implementation_plan": "implementation_plan",
        "answer_with_next_lane_plan": "workflow_next_lane",
        "answer_with_teaching_explanation": "teaching_explanation",
        "answer_with_scientific_guidance": "scientific_discovery_guidance",
        "answer_with_evaluation_summary": "benchmark_evaluation_summary",
        "answer_with_non_canned_specificity": "non_canned_specificity",
        "answer_with_directness_concern": "directness_concern",
    }.get(policy, policy)


def _variant_active(variant: _CandidateVariant, labels_blob: str, friction_summary: Mapping[str, Any], selector_summary: Mapping[str, Any]) -> bool:
    route_id = selector_summary.get("route_id")
    if variant.candidate_type == "direct_bounded_candidate":
        return _contains_any(labels_blob, variant.trigger_labels) or route_id in {"identity_status_route", "capability_orientation_route"}
    if variant.candidate_type == "clarification_candidate":
        return bool(friction_summary.get("needs_clarification")) or _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "bounded_uncertainty_candidate":
        return bool(friction_summary.get("needs_clarification")) or _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "refusal_boundary_candidate":
        return bool(friction_summary.get("blocked")) or _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "evidence_needed_candidate":
        return bool(friction_summary.get("needs_evidence")) or _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "partial_supported_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "stepwise_plan_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "implementation_plan_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "workflow_next_lane_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "governance_escalation_candidate":
        return bool(friction_summary.get("needs_owner_approval")) or _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "teaching_explanation_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "language_discovery_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "scientific_discovery_guidance_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "benchmark_evaluation_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "unknown_friction_candidate":
        return bool(friction_summary.get("unknown_detected")) or bool(friction_summary.get("friction_detected")) or _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "memory_honesty_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "continuity_recap_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "relationship_feedback_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "correction_repair_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "conflict_contradiction_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "non_canned_specificity_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    if variant.candidate_type == "directness_concern_candidate":
        return _contains_any(labels_blob, variant.trigger_labels)
    return False


def _candidate_variant_for_selected_route(route_id: str, labels_blob: str, friction_summary: Mapping[str, Any]) -> _CandidateVariant:
    if route_id in {"identity_status_route", "capability_orientation_route"}:
        return _VARIANTS_BY_TYPE["direct_bounded_candidate"]
    if route_id == "memory_honesty_route":
        return _VARIANTS_BY_TYPE["memory_honesty_candidate"]
    if route_id == "continuity_route":
        return _VARIANTS_BY_TYPE["continuity_recap_candidate"]
    if route_id == "clarification_route":
        return _VARIANTS_BY_TYPE["clarification_candidate"]
    if route_id == "uncertainty_route":
        return _VARIANTS_BY_TYPE["bounded_uncertainty_candidate"]
    if route_id == "refusal_boundary_route":
        return _VARIANTS_BY_TYPE["refusal_boundary_candidate"]
    if route_id == "evidence_needed_route":
        return _VARIANTS_BY_TYPE["evidence_needed_candidate"]
    if route_id == "partial_supported_route":
        return _VARIANTS_BY_TYPE["partial_supported_candidate"]
    if route_id == "ordinary_task_route":
        return _VARIANTS_BY_TYPE["stepwise_plan_candidate"]
    if route_id == "implementation_planning_route":
        return _VARIANTS_BY_TYPE["implementation_plan_candidate"]
    if route_id == "workflow_next_lane_route":
        return _VARIANTS_BY_TYPE["workflow_next_lane_candidate"]
    if route_id == "governance_escalation_route":
        return _VARIANTS_BY_TYPE["governance_escalation_candidate"]
    if route_id == "teaching_explanation_route":
        return _VARIANTS_BY_TYPE["teaching_explanation_candidate"]
    if route_id == "language_discovery_route":
        return _VARIANTS_BY_TYPE["language_discovery_candidate"]
    if route_id == "scientific_discovery_route":
        return _VARIANTS_BY_TYPE["scientific_discovery_guidance_candidate"]
    if route_id == "benchmark_evaluation_route":
        return _VARIANTS_BY_TYPE["benchmark_evaluation_candidate"]
    if route_id in {"unknown_word_phrase_route", "unknown_intent_route", "unknown_capability_route", "friction_repeated_failure_route"}:
        return _VARIANTS_BY_TYPE["unknown_friction_candidate"]
    if route_id == "relationship_feedback_route":
        return _VARIANTS_BY_TYPE["relationship_feedback_candidate"]
    if route_id == "correction_repair_route":
        return _VARIANTS_BY_TYPE["correction_repair_candidate"]
    if route_id == "conflict_contradiction_route":
        return _VARIANTS_BY_TYPE["conflict_contradiction_candidate"]
    if route_id == "non_canned_specificity_route":
        return _VARIANTS_BY_TYPE["non_canned_specificity_candidate"]
    if route_id == "directness_concern_route":
        return _VARIANTS_BY_TYPE["directness_concern_candidate"]
    if bool(friction_summary.get("unknown_detected")) or bool(friction_summary.get("friction_detected")) or not labels_blob:
        return _VARIANTS_BY_TYPE["unknown_friction_candidate"]
    return _VARIANTS_BY_TYPE["clarification_candidate"]


def _candidate_route_choice(variant: _CandidateVariant, route_id: str, labels_blob: str, friction_summary: Mapping[str, Any]) -> str:
    if variant.candidate_type == "direct_bounded_candidate":
        return "capability_orientation_route" if route_id == "capability_orientation_route" else "identity_status_route"
    if variant.candidate_type == "unknown_friction_candidate":
        if route_id in {"unknown_word_phrase_route", "unknown_intent_route", "unknown_capability_route", "friction_repeated_failure_route"}:
            return route_id
        if _contains_any(labels_blob, ("unknown capability", "capability unknown", "what can you do", "can you do")):
            return "unknown_capability_route"
        if _contains_any(labels_blob, ("unknown word", "unknown phrase", "what does this mean", "word meaning", "phrase meaning")):
            return "unknown_word_phrase_route"
        if _contains_any(labels_blob, ("repeated failure", "friction", "stuck", "keeps failing", "blocked")):
            return "friction_repeated_failure_route"
        return "unknown_intent_route" if _contains_any(labels_blob, ("intent", "unclear", "ambiguous", "what do you mean")) else "unknown_intent_route"
    return variant.route_id


def _build_candidate(
    variant: _CandidateVariant,
    route_id: str,
    labels_blob: str,
    friction_summary: Mapping[str, Any],
    selector_summary: Mapping[str, Any],
    candidate_selected: bool,
    candidate_rejected: bool,
    rejection_reason: str,
    route_confidence: float,
) -> CandidateResponsePath:
    chosen_route_id = _candidate_route_choice(variant, route_id, labels_blob, friction_summary)
    selector_method_id, selector_shape_id, selector_case_id = _SELECTOR_IDS_BY_ROUTE_V1[chosen_route_id]
    method, shape, case = _get_record_by_route(chosen_route_id)
    required_inputs = _record_inputs(method, shape, case)
    missing_inputs = _record_missing_inputs(chosen_route_id, friction_summary, selector_summary, labels_blob)
    evidence_requirements, memory_requirements, capability_requirements, relationship_requirements = _requirements_from_case(case)
    acceptance_conditions = tuple(str(item) for item in getattr(shape, "use_when", "").split(";") if _safe_text(item)) or variant.acceptance_conditions
    rejection_conditions = tuple(str(item) for item in getattr(shape, "avoid_when", "").split(";") if _safe_text(item)) or variant.rejection_conditions
    provenance_requirements = _candidate_source_refs(method, shape, case)
    if candidate_selected:
        selection_score = min(1.0, max(0.0, route_confidence + 0.05))
    elif candidate_rejected:
        selection_score = min(1.0, max(0.0, route_confidence - 0.35))
    else:
        selection_score = min(1.0, max(0.0, route_confidence - 0.05))
    candidate_id = _candidate_id(variant.candidate_type, chosen_route_id)
    return CandidateResponsePath(
        candidate_id=candidate_id,
        candidate_type=variant.candidate_type,
        method_id=selector_method_id,
        shape_id=selector_shape_id,
        case_id=selector_case_id,
        route_id=chosen_route_id,
        purpose=variant.purpose,
        answer_policy=variant.answer_policy,
        why_candidate_exists=variant.why_candidate_exists,
        required_inputs=required_inputs,
        missing_inputs=missing_inputs,
        acceptance_conditions=tuple(_dedupe_preserve(list(acceptance_conditions))),
        rejection_conditions=tuple(_dedupe_preserve(list(rejection_conditions))),
        risk_labels=variant.risk_labels,
        quality_pressure_labels=variant.quality_pressure_labels,
        provenance_requirements=provenance_requirements,
        selection_score=selection_score,
        selected=candidate_selected,
        rejected=candidate_rejected,
        rejection_reason=rejection_reason,
        generates_final_text=False,
    )


def _blocked_labels_from_friction(friction_summary: Mapping[str, Any], selector_summary: Mapping[str, Any]) -> tuple[str, ...]:
    labels: list[str] = []
    labels.extend(str(item) for item in friction_summary.get("blocked_labels", []) if _safe_text(item))
    labels.extend(str(item) for item in selector_summary.get("blocked_labels", []) if _safe_text(item))
    if friction_summary.get("blocked"):
        labels.append("friction_blocked")
    if selector_summary.get("blocked"):
        labels.append("selector_blocked")
    if friction_summary.get("needs_clarification") or selector_summary.get("needs_clarification"):
        labels.append("needs_clarification")
    if friction_summary.get("needs_evidence") or selector_summary.get("needs_evidence"):
        labels.append("needs_evidence")
    if friction_summary.get("needs_owner_approval") or selector_summary.get("needs_owner_approval"):
        labels.append("needs_owner_approval")
    return _dedupe_preserve(labels)


def _selected_policy_from_route(route_id: str, friction_summary: Mapping[str, Any]) -> str:
    if route_id == "clarification_route":
        return "ask_clarifying_question"
    if route_id == "uncertainty_route":
        return "state_bounded_uncertainty"
    if route_id == "refusal_boundary_route":
        return "refuse_with_boundary"
    if route_id == "evidence_needed_route":
        return "request_evidence"
    if route_id == "partial_supported_route":
        return "give_partial_supported_answer"
    if route_id == "workflow_next_lane_route":
        return "answer_with_next_lane_plan"
    if route_id == "implementation_planning_route":
        return "answer_with_implementation_plan"
    if route_id == "ordinary_task_route":
        return "answer_with_stepwise_plan"
    if route_id == "governance_escalation_route":
        return "escalate_to_owner_review"
    if route_id == "teaching_explanation_route":
        return "route_language_discovery_explanation"
    if route_id == "language_discovery_route":
        return "route_language_discovery_explanation"
    if route_id == "scientific_discovery_route":
        return "route_capability_orientation"
    if route_id == "benchmark_evaluation_route":
        return "answer_with_evaluation_summary"
    if route_id in {"unknown_word_phrase_route", "unknown_intent_route", "unknown_capability_route", "friction_repeated_failure_route"}:
        return "route_unknown_friction"
    if route_id == "memory_honesty_route":
        return "route_memory_honesty"
    if route_id == "continuity_route":
        return "route_continuity_recap"
    if route_id == "relationship_feedback_route":
        return "route_relationship_feedback"
    if route_id == "correction_repair_route":
        return "route_correction_repair"
    if route_id == "conflict_contradiction_route":
        return "route_conflict_contradiction"
    if route_id == "non_canned_specificity_route":
        return "answer_with_non_canned_specificity"
    if route_id == "directness_concern_route":
        return "answer_with_directness_concern"
    if route_id == "capability_orientation_route":
        return "answer_directly_bounded"
    if bool(friction_summary.get("unknown_detected")) or bool(friction_summary.get("friction_detected")):
        return "route_unknown_friction"
    return "answer_directly_bounded"


def _candidate_family_from_route(route_id: str, variant: _CandidateVariant) -> str:
    if variant.candidate_type == "direct_bounded_candidate" and route_id == "capability_orientation_route":
        return "capability_orientation"
    return variant.candidate_family


def _build_packet(turn_labels: Any, context_signals: Any = None) -> CandidateResponseFormationPacket:
    normalized_labels = _normalize_labels(turn_labels)
    normalized_context_signals = _normalize_context_signals(context_signals)
    safe_keys = _safe_context_signal_keys(normalized_context_signals)
    labels_blob = " ".join(normalized_labels)

    selection_labels = _augment_turn_labels_for_selection(normalized_labels)
    friction_packet = route_unknown_prompt_friction_v1(selection_labels, context_signals=normalized_context_signals)
    selector_packet = select_response_route_v1(selection_labels, context_signals=normalized_context_signals)

    friction_json = to_unknown_prompt_friction_json_safe_v1(friction_packet)
    selector_json = to_response_selection_json_safe_v1(selector_packet)

    friction_summary = summarize_unknown_prompt_friction_packet_v1(friction_packet)
    selector_summary = summarize_response_selection_packet_v1(selector_packet)

    selected_route_id = str(selector_summary.get("route_id", "clarification_route"))
    if selected_route_id not in _ALLOWED_ROUTE_IDS_V1:
        selected_route_id = "clarification_route"

    selected_variant = _candidate_variant_for_selected_route(selected_route_id, labels_blob, friction_summary)
    selected_candidate_type = selected_variant.candidate_type
    selected_policy = _selected_policy_from_route(selected_route_id, friction_summary)
    selected_family = _candidate_family_from_route(selected_route_id, selected_variant)

    blocked_labels = _blocked_labels_from_friction(friction_summary, selector_summary)
    needs_clarification = bool(friction_summary.get("needs_clarification") or selector_summary.get("needs_clarification") or selected_route_id in {"clarification_route", "uncertainty_route", "unknown_word_phrase_route", "unknown_intent_route", "unknown_capability_route", "friction_repeated_failure_route"} or not normalized_labels)
    needs_evidence = bool(friction_summary.get("needs_evidence") or selector_summary.get("needs_evidence") or selected_route_id == "evidence_needed_route")
    needs_owner_approval = bool(friction_summary.get("needs_owner_approval") or selector_summary.get("needs_owner_approval") or selected_route_id == "governance_escalation_route")
    blocked = bool(friction_summary.get("blocked") or selector_summary.get("blocked") or needs_clarification or needs_evidence or needs_owner_approval)

    candidates: list[CandidateResponsePath] = []
    rejected_candidates: list[CandidateResponseRejection] = []
    route_confidence = float(selector_summary.get("route_confidence", 0.5))

    for variant in _CANDIDATE_VARIANTS_V1:
        active = _variant_active(variant, labels_blob, friction_summary, selector_summary)
        candidate_selected = variant.candidate_type == selected_candidate_type
        candidate_rejected = not active and not candidate_selected
        rejection_reason = ""
        if candidate_selected:
            rejection_reason = ""
        elif candidate_rejected:
            if variant.candidate_type == "unknown_friction_candidate" and not (bool(friction_summary.get("unknown_detected")) or bool(friction_summary.get("friction_detected"))):
                rejection_reason = "no unknown or friction signal"
            elif variant.candidate_type == "clarification_candidate" and not bool(friction_summary.get("needs_clarification")):
                rejection_reason = "no clarification need"
            elif variant.candidate_type == "bounded_uncertainty_candidate" and not _contains_any(labels_blob, variant.trigger_labels):
                rejection_reason = "no uncertainty signal"
            elif variant.candidate_type == "refusal_boundary_candidate" and not bool(friction_summary.get("blocked")):
                rejection_reason = "no refusal boundary"
            elif variant.candidate_type == "evidence_needed_candidate" and not bool(friction_summary.get("needs_evidence")):
                rejection_reason = "no evidence need"
            else:
                rejection_reason = "signal mismatch"
        candidate = _build_candidate(
            variant,
            selected_route_id if candidate_selected else _candidate_route_choice(variant, selected_route_id, labels_blob, friction_summary),
            labels_blob,
            friction_summary,
            selector_summary,
            candidate_selected,
            candidate_rejected,
            rejection_reason,
            route_confidence,
        )
        candidates.append(candidate)
        if candidate.rejected:
            rejected_candidates.append(
                CandidateResponseRejection(
                    candidate_id=candidate.candidate_id,
                    candidate_type=candidate.candidate_type,
                    route_id=candidate.route_id,
                    method_id=candidate.method_id,
                    shape_id=candidate.shape_id,
                    case_id=candidate.case_id,
                    rejection_reason=candidate.rejection_reason or "signal mismatch",
                    blocked_labels=blocked_labels,
                    selection_score=candidate.selection_score,
                )
            )

    selected_candidate = next(candidate for candidate in candidates if candidate.selected)
    required_inputs = selected_candidate.required_inputs
    missing_inputs = selected_candidate.missing_inputs
    _, _, selected_case_record = _get_record_by_route(selected_candidate.route_id)
    evidence_requirements, memory_requirements, capability_requirements, relationship_requirements = _requirements_from_case(selected_case_record)

    if selected_route_id in {"unknown_word_phrase_route", "unknown_intent_route", "unknown_capability_route", "friction_repeated_failure_route"}:
        blocked = True
        if "unknown_friction" not in blocked_labels:
            blocked_labels = _dedupe_preserve((*blocked_labels, "unknown_friction"))
    if needs_clarification and "needs_clarification" not in blocked_labels:
        blocked_labels = _dedupe_preserve((*blocked_labels, "needs_clarification"))
    if needs_evidence and "needs_evidence" not in blocked_labels:
        blocked_labels = _dedupe_preserve((*blocked_labels, "needs_evidence"))
    if needs_owner_approval and "needs_owner_approval" not in blocked_labels:
        blocked_labels = _dedupe_preserve((*blocked_labels, "needs_owner_approval"))

    answer_obligation = _policy_to_obligation(selected_policy)
    safe_metadata = {
        "normalized_turn_labels": normalized_labels,
        "safe_context_signal_keys": list(safe_keys),
        "selected_route_id": selected_route_id,
        "selected_candidate_type": selected_candidate_type,
        "selected_candidate_id": selected_candidate.candidate_id,
        "selected_candidate_family": selected_family,
        "friction_summary": friction_summary,
        "selector_summary": selector_summary,
        "friction_json_safe": friction_json,
        "selector_json_safe": selector_json,
        "active_candidate_ids": [candidate.candidate_id for candidate in candidates if not candidate.rejected],
        "rejected_candidate_ids": [item.candidate_id for item in rejected_candidates],
        "candidate_count": len(candidates),
    }

    return CandidateResponseFormationPacket(
        packet_type=PACKET_TYPE_V1,
        turn_labels=normalized_labels,
        safe_context_signal_keys=safe_keys,
        friction_summary=friction_summary,
        selector_summary=selector_summary,
        candidate_count=len(candidates),
        candidates=tuple(candidates),
        rejected_candidates=tuple(rejected_candidates),
        selected_candidate_id=selected_candidate.candidate_id,
        candidate_family=selected_family,
        answer_obligation=answer_obligation,
        required_inputs=required_inputs,
        missing_inputs=missing_inputs,
        boundary_labels=blocked_labels,
        evidence_requirements=evidence_requirements,
        memory_requirements=memory_requirements,
        capability_requirements=capability_requirements,
        relationship_requirements=relationship_requirements,
        proposed_answer_policy=selected_policy,
        needs_clarification=needs_clarification,
        needs_evidence=needs_evidence,
        needs_owner_approval=needs_owner_approval,
        blocked=blocked,
        blocked_labels=blocked_labels,
        safe_metadata=safe_metadata,
        runtime_authority=False,
        model_provider_used=False,
        generates_final_text=False,
        writes_state=False,
    )


def build_candidate_response_formation_packet_v1(turn_labels: Any, context_signals: Mapping[str, Any] | None = None) -> CandidateResponseFormationPacket:
    return _build_packet(turn_labels, context_signals=context_signals)


def form_candidate_responses_v1(turn_labels: Any, context_signals: Mapping[str, Any] | None = None) -> CandidateResponseFormationPacket:
    return _build_packet(turn_labels, context_signals=context_signals)


def to_candidate_response_formation_json_safe_v1(packet: Any) -> dict[str, Any]:
    return _json_safe(packet)


def validate_candidate_response_formation_packet_v1(packet: Any) -> bool:
    data = to_candidate_response_formation_json_safe_v1(packet) if is_dataclass(packet) else dict(packet) if isinstance(packet, Mapping) else None
    if data is None:
        raise ValueError("packet must be a mapping or dataclass")

    required = [
        "packet_type",
        "turn_labels",
        "safe_context_signal_keys",
        "friction_summary",
        "selector_summary",
        "candidate_count",
        "candidates",
        "rejected_candidates",
        "selected_candidate_id",
        "candidate_family",
        "answer_obligation",
        "required_inputs",
        "missing_inputs",
        "boundary_labels",
        "evidence_requirements",
        "memory_requirements",
        "capability_requirements",
        "relationship_requirements",
        "proposed_answer_policy",
        "needs_clarification",
        "needs_evidence",
        "needs_owner_approval",
        "blocked",
        "blocked_labels",
        "safe_metadata",
        "runtime_authority",
        "model_provider_used",
        "generates_final_text",
        "writes_state",
    ]
    for field_name in required:
        if field_name not in data:
            raise ValueError(f"missing required field: {field_name}")

    if data["packet_type"] != PACKET_TYPE_V1:
        raise ValueError("packet_type mismatch")
    if data["runtime_authority"] is not False:
        raise ValueError("runtime_authority must be false")
    if data["model_provider_used"] is not False:
        raise ValueError("model_provider_used must be false")
    if data["generates_final_text"] is not False:
        raise ValueError("generates_final_text must be false")
    if data["writes_state"] is not False:
        raise ValueError("writes_state must be false")

    if not isinstance(data["turn_labels"], list):
        raise ValueError("turn_labels must be a list")
    if not isinstance(data["safe_context_signal_keys"], list):
        raise ValueError("safe_context_signal_keys must be a list")
    if not isinstance(data["friction_summary"], dict):
        raise ValueError("friction_summary must be a dict")
    if not isinstance(data["selector_summary"], dict):
        raise ValueError("selector_summary must be a dict")
    if not isinstance(data["candidates"], list):
        raise ValueError("candidates must be a list")
    if not isinstance(data["rejected_candidates"], list):
        raise ValueError("rejected_candidates must be a list")
    if not isinstance(data["blocked_labels"], list):
        raise ValueError("blocked_labels must be a list")
    if not isinstance(data["safe_metadata"], dict):
        raise ValueError("safe_metadata must be a dict")

    if not data["selected_candidate_id"]:
        raise ValueError("selected_candidate_id must not be empty")
    if not data["candidate_family"]:
        raise ValueError("candidate_family must not be empty")
    if not data["answer_obligation"]:
        raise ValueError("answer_obligation must not be empty")
    if not data["proposed_answer_policy"]:
        raise ValueError("proposed_answer_policy must not be empty")
    if data["candidate_count"] != len(data["candidates"]):
        raise ValueError("candidate_count mismatch")
    if not data["candidates"]:
        raise ValueError("candidates must not be empty")

    if len(_dedupe_preserve(data["blocked_labels"])) != len(data["blocked_labels"]):
        raise ValueError("blocked_labels must not contain duplicates")
    if data["runtime_authority"] is not False or data["model_provider_used"] is not False or data["generates_final_text"] is not False or data["writes_state"] is not False:
        raise ValueError("authority drift detected")

    selected = next((candidate for candidate in data["candidates"] if candidate.get("candidate_id") == data["selected_candidate_id"]), None)
    if selected is None:
        raise ValueError("selected candidate must exist")
    if selected.get("selected") is not True:
        raise ValueError("selected candidate must be marked selected")
    if selected.get("rejected") is True:
        raise ValueError("selected candidate must not be rejected")
    if selected.get("generates_final_text") is not False:
        raise ValueError("selected candidate must not generate final text")

    candidate_ids: set[str] = set()
    for candidate in data["candidates"]:
        if set(candidate.keys()) & _FORBIDDEN_KEYS_V1:
            raise ValueError("raw prompt field detected in candidate")
        candidate_id = candidate.get("candidate_id")
        if not candidate_id:
            raise ValueError("candidate_id must not be empty")
        if candidate_id in candidate_ids:
            raise ValueError("duplicate candidate_id")
        candidate_ids.add(candidate_id)
        if candidate.get("candidate_type") not in _ALLOWED_CANDIDATE_TYPES_V1:
            raise ValueError("unknown candidate_type")
        if candidate.get("route_id") not in _ALLOWED_ROUTE_IDS_V1:
            raise ValueError("unknown route_id")
        if candidate.get("method_id") not in _ALLOWED_SELECTOR_METHOD_IDS_V1:
            raise ValueError("unknown method_id")
        if candidate.get("shape_id") not in _ALLOWED_SELECTOR_SHAPE_IDS_V1:
            raise ValueError("unknown shape_id")
        if candidate.get("case_id") not in _ALLOWED_SELECTOR_CASE_IDS_V1:
            raise ValueError("unknown case_id")
        if candidate.get("generates_final_text") is not False:
            raise ValueError("candidate must not generate final text")
        if not isinstance(candidate.get("selected"), bool):
            raise ValueError("selected must be bool")
        if not isinstance(candidate.get("rejected"), bool):
            raise ValueError("rejected must be bool")
        if candidate.get("selected") and candidate.get("rejected"):
            raise ValueError("candidate cannot be selected and rejected")
        if candidate.get("rejected") and not candidate.get("rejection_reason"):
            raise ValueError("rejected candidates must include rejection reasons")
        if candidate.get("selected"):
            if candidate.get("route_id") != data["selector_summary"].get("route_id"):
                raise ValueError("selected candidate must match selected route")
            if candidate.get("method_id") != data["selector_summary"].get("method_id"):
                raise ValueError("selected candidate must match selected method")
            if candidate.get("shape_id") != data["selector_summary"].get("shape_id"):
                raise ValueError("selected candidate must match selected shape")
            if candidate.get("case_id") != data["selector_summary"].get("case_id"):
                raise ValueError("selected candidate must match selected case")

    if selected.get("selected") is not True or selected.get("rejected") is True:
        raise ValueError("selected candidate invalid")

    if data["selected_candidate_id"] != selected.get("candidate_id"):
        raise ValueError("selected_candidate_id mismatch")

    if data["selected_candidate_id"] in {item.get("candidate_id") for item in data["rejected_candidates"]}:
        raise ValueError("selected candidate must not appear in rejected_candidates")

    if data["friction_summary"].get("blocked") is True and not data["blocked"]:
        raise ValueError("blocked packet required when friction is blocked")
    if data["blocked"] is True and not data["blocked_labels"]:
        raise ValueError("blocked packets must include blocked labels")

    if data["safe_metadata"].get("selected_candidate_id") != data["selected_candidate_id"]:
        raise ValueError("safe_metadata selected_candidate_id mismatch")
    if data["safe_metadata"].get("selected_route_id") != data["selector_summary"].get("route_id"):
        raise ValueError("safe_metadata selected_route_id mismatch")

    return True


def summarize_candidate_response_formation_packet_v1(packet: Any) -> CandidateResponseFormationSummary:
    data = to_candidate_response_formation_json_safe_v1(packet)
    selected = next(candidate for candidate in data.get("candidates", []) if candidate.get("candidate_id") == data.get("selected_candidate_id"))
    return CandidateResponseFormationSummary(
        packet_type=str(data.get("packet_type", PACKET_TYPE_V1)),
        candidate_count=int(data.get("candidate_count", 0)),
        selected_candidate_id=str(data.get("selected_candidate_id", "")),
        selected_candidate_type=str(selected.get("candidate_type", "")),
        candidate_family=str(data.get("candidate_family", "")),
        route_id=str(selected.get("route_id", "")),
        method_id=str(selected.get("method_id", "")),
        shape_id=str(selected.get("shape_id", "")),
        case_id=str(selected.get("case_id", "")),
        blocked=bool(data.get("blocked", False)),
        needs_clarification=bool(data.get("needs_clarification", False)),
        needs_evidence=bool(data.get("needs_evidence", False)),
        needs_owner_approval=bool(data.get("needs_owner_approval", False)),
        proposed_answer_policy=str(data.get("proposed_answer_policy", "")),
        blocked_labels=tuple(data.get("blocked_labels", [])),
    )


__all__ = [
    "CandidateResponsePath",
    "CandidateResponseRejection",
    "CandidateResponseFormationPacket",
    "CandidateResponseFormationSummary",
    "build_candidate_response_formation_packet_v1",
    "validate_candidate_response_formation_packet_v1",
    "summarize_candidate_response_formation_packet_v1",
    "to_candidate_response_formation_json_safe_v1",
    "form_candidate_responses_v1",
]
