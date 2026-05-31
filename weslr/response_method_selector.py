"""WESLR Response Method Selector v1.

Metadata-only route selector that combines answer methods, answer shapes,
and cognition cases into a single safe routing packet.

No final answer generation. No model/provider calls. No state writes.
"""

from __future__ import annotations

from dataclasses import dataclass, field, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


SELECTION_TYPE = "response_method_selection_v1"


class ValidationError(ValueError):
    pass


def _dedupe_preserve(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _as_bool(value: Any) -> bool:
    return bool(value is True or value == 1 or str(value).lower() in {"true", "yes", "1"})


def _normalize_labels(turn_labels: Any) -> List[str]:
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
    normalized: List[str] = []
    for value in values:
        text = value.strip().lower().replace("/", " ").replace("_", " ").replace("-", " ")
        if text:
            normalized.append(" ".join(text.split()))
    return _dedupe_preserve(normalized)


def _normalize_context_signals(context_signals: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if not context_signals:
        return {}
    return {str(k): v for k, v in context_signals.items()}


def _contains_any(blob: str, phrases: Sequence[str]) -> bool:
    return any(phrase in blob for phrase in phrases)


def _score_match(blob: str, phrases: Sequence[str]) -> float:
    if not phrases:
        return 0.0
    hits = sum(1 for phrase in phrases if phrase in blob)
    return hits / float(len(phrases))


@dataclass(frozen=True)
class ResponseMethodCandidate:
    method_id: str
    method_family: str
    route_id: str
    label: str
    confidence: float
    compatible_shape_ids: List[str] = field(default_factory=list)
    compatible_case_ids: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResponseShapeCandidate:
    shape_id: str
    shape_family: str
    route_id: str
    label: str
    confidence: float
    compatible_method_ids: List[str] = field(default_factory=list)
    compatible_case_ids: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CognitionCaseCandidate:
    case_id: str
    case_family: str
    route_id: str
    label: str
    confidence: float
    compatible_method_ids: List[str] = field(default_factory=list)
    compatible_shape_ids: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResponseMethodSelection:
    route_id: str
    selected_method_id: str
    route_confidence: float
    candidate_count: int
    reason: str
    candidates: List[ResponseMethodCandidate] = field(default_factory=list)


@dataclass(frozen=True)
class ResponseShapeSelection:
    route_id: str
    selected_shape_id: str
    route_confidence: float
    candidate_count: int
    reason: str
    candidates: List[ResponseShapeCandidate] = field(default_factory=list)


@dataclass(frozen=True)
class CognitionCaseSelection:
    route_id: str
    selected_case_id: str
    route_confidence: float
    candidate_count: int
    reason: str
    candidates: List[CognitionCaseCandidate] = field(default_factory=list)


@dataclass(frozen=True)
class ResponseSelectionTrace:
    trace_id: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResponseSelectionPacket:
    selection_type: str
    turn_labels: List[str]
    context_signals: Dict[str, Any]
    method_selection: ResponseMethodSelection
    shape_selection: ResponseShapeSelection
    case_selection: CognitionCaseSelection
    selected_route_id: str
    selected_method_id: str
    selected_shape_id: str
    selected_case_id: str
    route_confidence: float
    unknown_or_friction_detected: bool
    needs_clarification: bool
    needs_evidence: bool
    needs_owner_approval: bool
    blocked: bool
    blocked_labels: List[str]
    safe_metadata: Dict[str, Any]
    runtime_authority: bool = False
    model_provider_used: bool = False
    generates_final_text: bool = False
    writes_state: bool = False
    trace: Optional[ResponseSelectionTrace] = None


@dataclass(frozen=True)
class _RouteSpec:
    route_id: str
    method_id: str
    shape_id: str
    case_id: str
    keywords: List[str]
    family: str
    needs_clarification: bool = False
    needs_evidence: bool = False
    needs_owner_approval: bool = False
    blocked: bool = False
    unknown_or_friction: bool = False


_ROUTE_SPECS: List[_RouteSpec] = [
    _RouteSpec("identity_status_route", "method_identity_status", "shape_identity_status", "case_identity_status", ["identity status", "identity", "status", "who are you", "self"], "identity_status"),
    _RouteSpec("memory_honesty_route", "method_memory_honesty", "shape_memory_honesty", "case_memory_honesty", ["memory honesty", "memory", "remember", "forget", "honest memory"], "memory_honesty"),
    _RouteSpec("continuity_route", "method_continuity", "shape_continuity", "case_continuity", ["continuity", "resume", "where we left off", "context continuity", "follow up"], "continuity"),
    _RouteSpec("capability_orientation_route", "method_capability_orientation", "shape_capability_orientation", "case_capability_orientation", ["capability orientation", "capability", "what can you do", "can you", "ability"], "capability_orientation"),
    _RouteSpec("clarification_route", "method_clarification", "shape_clarification", "case_clarification", ["clarify", "clarification", "what do you mean", "ask clarify", "rephrase"], "clarification", needs_clarification=True, blocked=True),
    _RouteSpec("uncertainty_route", "method_uncertainty", "shape_uncertainty", "case_uncertainty", ["uncertainty", "uncertain", "not sure", "unknown", "unsure"], "uncertainty", needs_clarification=True, blocked=True, unknown_or_friction=True),
    _RouteSpec("refusal_boundary_route", "method_refusal_boundary", "shape_refusal_boundary", "case_refusal_boundary", ["refusal", "boundary", "cannot", "can't", "safety boundary"], "refusal_boundary", blocked=True),
    _RouteSpec("evidence_needed_route", "method_evidence_needed", "shape_evidence_needed", "case_evidence_needed", ["evidence", "source", "proof", "citation", "verify"], "evidence_needed", needs_evidence=True, blocked=True),
    _RouteSpec("partial_supported_route", "method_partial_supported", "shape_partial_supported", "case_partial_supported", ["partial", "limited support", "partially supported", "some support"], "partial_supported"),
    _RouteSpec("ordinary_task_route", "method_ordinary_task", "shape_ordinary_task", "case_ordinary_task", ["ordinary task", "task", "standard task", "normal work"], "ordinary_task"),
    _RouteSpec("implementation_planning_route", "method_implementation_planning", "shape_implementation_planning", "case_implementation_planning", ["implementation planning", "implementation", "plan", "prototype", "build"], "implementation_planning"),
    _RouteSpec("workflow_next_lane_route", "method_workflow_next_lane", "shape_workflow_next_lane", "case_workflow_next_lane", ["workflow next lane", "next lane", "next step", "handoff"], "workflow_next_lane"),
    _RouteSpec("governance_escalation_route", "method_governance_escalation", "shape_governance_escalation", "case_governance_escalation", ["governance escalation", "governance", "approval", "owner", "escalate"], "governance_escalation", needs_owner_approval=True, blocked=True),
    _RouteSpec("teaching_explanation_route", "method_teaching_explanation", "shape_teaching_explanation", "case_teaching_explanation", ["teaching explanation", "teach", "explain", "lesson", "why"], "teaching_explanation"),
    _RouteSpec("language_discovery_route", "method_language_discovery", "shape_language_discovery", "case_language_discovery", ["language discovery", "language", "translation", "phrase", "word"], "language_discovery"),
    _RouteSpec("scientific_discovery_route", "method_scientific_discovery", "shape_scientific_discovery", "case_scientific_discovery", ["scientific discovery", "scientific", "hypothesis", "experiment", "discovery"], "scientific_discovery"),
    _RouteSpec("benchmark_evaluation_route", "method_benchmark_evaluation", "shape_benchmark_evaluation", "case_benchmark_evaluation", ["benchmark evaluation", "benchmark", "evaluation", "score", "test"], "benchmark_evaluation"),
    _RouteSpec("unknown_word_phrase_route", "method_unknown_word_phrase", "shape_unknown_word_phrase", "case_unknown_word_phrase", ["unknown word phrase", "unknown word", "unknown phrase", "word meaning"], "unknown_word_phrase", needs_clarification=True, blocked=True, unknown_or_friction=True),
    _RouteSpec("unknown_intent_route", "method_unknown_intent", "shape_unknown_intent", "case_unknown_intent", ["unknown intent", "intent unknown"], "unknown_intent", needs_clarification=True, blocked=True, unknown_or_friction=True),
    _RouteSpec("unknown_capability_route", "method_unknown_capability", "shape_unknown_capability", "case_unknown_capability", ["unknown capability", "capability unknown", "can you do"], "unknown_capability", needs_clarification=True, blocked=True, unknown_or_friction=True),
    _RouteSpec("friction_repeated_failure_route", "method_friction_repeated_failure", "shape_friction_repeated_failure", "case_friction_repeated_failure", ["repeated failure", "friction", "stuck", "keeps failing"], "friction_repeated_failure", needs_clarification=True, blocked=True, unknown_or_friction=True),
    _RouteSpec("relationship_feedback_route", "method_relationship_feedback", "shape_relationship_feedback", "case_relationship_feedback", ["relationship feedback", "relationship", "rapport", "tone"], "relationship_feedback"),
    _RouteSpec("correction_repair_route", "method_correction_repair", "shape_correction_repair", "case_correction_repair", ["correction repair", "correction", "repair", "fix", "actually"], "correction_repair"),
    _RouteSpec("conflict_contradiction_route", "method_conflict_contradiction", "shape_conflict_contradiction", "case_conflict_contradiction", ["conflict contradiction", "conflict", "contradiction", "contradict", "inconsistent"], "conflict_contradiction", needs_clarification=True, blocked=True),
    _RouteSpec("non_canned_specificity_route", "method_non_canned_specificity", "shape_non_canned_specificity", "case_non_canned_specificity", ["non canned specificity", "specificity", "specific", "tailored", "non-canned"], "non_canned_specificity"),
    _RouteSpec("directness_concern_route", "method_directness_concern", "shape_directness_concern", "case_directness_concern", ["directness concern", "directness", "too direct", "concern"], "directness_concern"),
]

_ROUTE_LOOKUP = {spec.route_id: spec for spec in _ROUTE_SPECS}


def _clean_id_list(values: Any) -> List[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    try:
        return _dedupe_preserve(str(v) for v in values if str(v))
    except TypeError:
        return [str(values)]


def _fallback_method_catalog() -> List[ResponseMethodCandidate]:
    return [
        ResponseMethodCandidate("method_identity_status", "identity_status", "identity_status_route", "identity/status", 0.95, ["shape_identity_status"], ["case_identity_status"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_memory_honesty", "memory_honesty", "memory_honesty_route", "memory honesty", 0.95, ["shape_memory_honesty"], ["case_memory_honesty"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_continuity", "continuity", "continuity_route", "continuity", 0.95, ["shape_continuity"], ["case_continuity"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_capability_orientation", "capability_orientation", "capability_orientation_route", "capability orientation", 0.95, ["shape_capability_orientation"], ["case_capability_orientation"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_clarification", "clarification", "clarification_route", "clarification", 0.95, ["shape_clarification"], ["case_clarification"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_uncertainty", "uncertainty", "uncertainty_route", "uncertainty", 0.95, ["shape_uncertainty"], ["case_uncertainty"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_refusal_boundary", "refusal_boundary", "refusal_boundary_route", "refusal boundary", 0.95, ["shape_refusal_boundary"], ["case_refusal_boundary"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_evidence_needed", "evidence_needed", "evidence_needed_route", "evidence needed", 0.95, ["shape_evidence_needed"], ["case_evidence_needed"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_partial_supported", "partial_supported", "partial_supported_route", "partial supported", 0.90, ["shape_partial_supported"], ["case_partial_supported"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_ordinary_task", "ordinary_task", "ordinary_task_route", "ordinary task", 0.90, ["shape_ordinary_task"], ["case_ordinary_task"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_implementation_planning", "implementation_planning", "implementation_planning_route", "implementation planning", 0.90, ["shape_implementation_planning"], ["case_implementation_planning"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_workflow_next_lane", "workflow_next_lane", "workflow_next_lane_route", "workflow next lane", 0.90, ["shape_workflow_next_lane"], ["case_workflow_next_lane"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_governance_escalation", "governance_escalation", "governance_escalation_route", "governance escalation", 0.95, ["shape_governance_escalation"], ["case_governance_escalation"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_teaching_explanation", "teaching_explanation", "teaching_explanation_route", "teaching explanation", 0.90, ["shape_teaching_explanation"], ["case_teaching_explanation"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_language_discovery", "language_discovery", "language_discovery_route", "language discovery", 0.90, ["shape_language_discovery"], ["case_language_discovery"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_scientific_discovery", "scientific_discovery", "scientific_discovery_route", "scientific discovery", 0.90, ["shape_scientific_discovery"], ["case_scientific_discovery"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_benchmark_evaluation", "benchmark_evaluation", "benchmark_evaluation_route", "benchmark evaluation", 0.90, ["shape_benchmark_evaluation"], ["case_benchmark_evaluation"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_unknown_word_phrase", "unknown_word_phrase", "unknown_word_phrase_route", "unknown word/phrase", 0.90, ["shape_unknown_word_phrase"], ["case_unknown_word_phrase"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_unknown_intent", "unknown_intent", "unknown_intent_route", "unknown intent", 0.90, ["shape_unknown_intent"], ["case_unknown_intent"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_unknown_capability", "unknown_capability", "unknown_capability_route", "unknown capability", 0.90, ["shape_unknown_capability"], ["case_unknown_capability"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_friction_repeated_failure", "friction_repeated_failure", "friction_repeated_failure_route", "repeated failure/friction", 0.90, ["shape_friction_repeated_failure"], ["case_friction_repeated_failure"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_relationship_feedback", "relationship_feedback", "relationship_feedback_route", "relationship feedback", 0.90, ["shape_relationship_feedback"], ["case_relationship_feedback"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_correction_repair", "correction_repair", "correction_repair_route", "correction repair", 0.90, ["shape_correction_repair"], ["case_correction_repair"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_conflict_contradiction", "conflict_contradiction", "conflict_contradiction_route", "conflict contradiction", 0.90, ["shape_conflict_contradiction"], ["case_conflict_contradiction"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_non_canned_specificity", "non_canned_specificity", "non_canned_specificity_route", "non-canned specificity", 0.90, ["shape_non_canned_specificity"], ["case_non_canned_specificity"], ["catalog:fallback"]),
        ResponseMethodCandidate("method_directness_concern", "directness_concern", "directness_concern_route", "directness concern", 0.90, ["shape_directness_concern"], ["case_directness_concern"], ["catalog:fallback"]),
    ]


def _fallback_shape_catalog() -> List[ResponseShapeCandidate]:
    return [
        ResponseShapeCandidate("shape_identity_status", "identity_status", "identity_status_route", "identity/status", 0.95, ["method_identity_status"], ["case_identity_status"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_memory_honesty", "memory_honesty", "memory_honesty_route", "memory honesty", 0.95, ["method_memory_honesty"], ["case_memory_honesty"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_continuity", "continuity", "continuity_route", "continuity", 0.95, ["method_continuity"], ["case_continuity"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_capability_orientation", "capability_orientation", "capability_orientation_route", "capability orientation", 0.95, ["method_capability_orientation"], ["case_capability_orientation"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_clarification", "clarification", "clarification_route", "clarification", 0.95, ["method_clarification"], ["case_clarification"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_uncertainty", "uncertainty", "uncertainty_route", "uncertainty", 0.95, ["method_uncertainty"], ["case_uncertainty"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_refusal_boundary", "refusal_boundary", "refusal_boundary_route", "refusal boundary", 0.95, ["method_refusal_boundary"], ["case_refusal_boundary"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_evidence_needed", "evidence_needed", "evidence_needed_route", "evidence needed", 0.95, ["method_evidence_needed"], ["case_evidence_needed"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_partial_supported", "partial_supported", "partial_supported_route", "partial supported", 0.90, ["method_partial_supported"], ["case_partial_supported"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_ordinary_task", "ordinary_task", "ordinary_task_route", "ordinary task", 0.90, ["method_ordinary_task"], ["case_ordinary_task"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_implementation_planning", "implementation_planning", "implementation_planning_route", "implementation planning", 0.90, ["method_implementation_planning"], ["case_implementation_planning"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_workflow_next_lane", "workflow_next_lane", "workflow_next_lane_route", "workflow next lane", 0.90, ["method_workflow_next_lane"], ["case_workflow_next_lane"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_governance_escalation", "governance_escalation", "governance_escalation_route", "governance escalation", 0.95, ["method_governance_escalation"], ["case_governance_escalation"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_teaching_explanation", "teaching_explanation", "teaching_explanation_route", "teaching explanation", 0.90, ["method_teaching_explanation"], ["case_teaching_explanation"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_language_discovery", "language_discovery", "language_discovery_route", "language discovery", 0.90, ["method_language_discovery"], ["case_language_discovery"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_scientific_discovery", "scientific_discovery", "scientific_discovery_route", "scientific discovery", 0.90, ["method_scientific_discovery"], ["case_scientific_discovery"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_benchmark_evaluation", "benchmark_evaluation", "benchmark_evaluation_route", "benchmark evaluation", 0.90, ["method_benchmark_evaluation"], ["case_benchmark_evaluation"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_unknown_word_phrase", "unknown_word_phrase", "unknown_word_phrase_route", "unknown word/phrase", 0.90, ["method_unknown_word_phrase"], ["case_unknown_word_phrase"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_unknown_intent", "unknown_intent", "unknown_intent_route", "unknown intent", 0.90, ["method_unknown_intent"], ["case_unknown_intent"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_unknown_capability", "unknown_capability", "unknown_capability_route", "unknown capability", 0.90, ["method_unknown_capability"], ["case_unknown_capability"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_friction_repeated_failure", "friction_repeated_failure", "friction_repeated_failure_route", "repeated failure/friction", 0.90, ["method_friction_repeated_failure"], ["case_friction_repeated_failure"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_relationship_feedback", "relationship_feedback", "relationship_feedback_route", "relationship feedback", 0.90, ["method_relationship_feedback"], ["case_relationship_feedback"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_correction_repair", "correction_repair", "correction_repair_route", "correction repair", 0.90, ["method_correction_repair"], ["case_correction_repair"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_conflict_contradiction", "conflict_contradiction", "conflict_contradiction_route", "conflict contradiction", 0.90, ["method_conflict_contradiction"], ["case_conflict_contradiction"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_non_canned_specificity", "non_canned_specificity", "non_canned_specificity_route", "non-canned specificity", 0.90, ["method_non_canned_specificity"], ["case_non_canned_specificity"], ["catalog:fallback"]),
        ResponseShapeCandidate("shape_directness_concern", "directness_concern", "directness_concern_route", "directness concern", 0.90, ["method_directness_concern"], ["case_directness_concern"], ["catalog:fallback"]),
    ]


def _fallback_case_registry() -> List[CognitionCaseCandidate]:
    return [
        CognitionCaseCandidate("case_identity_status", "identity_status", "identity_status_route", "identity/status", 0.95, ["method_identity_status"], ["shape_identity_status"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_memory_honesty", "memory_honesty", "memory_honesty_route", "memory honesty", 0.95, ["method_memory_honesty"], ["shape_memory_honesty"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_continuity", "continuity", "continuity_route", "continuity", 0.95, ["method_continuity"], ["shape_continuity"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_capability_orientation", "capability_orientation", "capability_orientation_route", "capability orientation", 0.95, ["method_capability_orientation"], ["shape_capability_orientation"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_clarification", "clarification", "clarification_route", "clarification", 0.95, ["method_clarification"], ["shape_clarification"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_uncertainty", "uncertainty", "uncertainty_route", "uncertainty", 0.95, ["method_uncertainty"], ["shape_uncertainty"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_refusal_boundary", "refusal_boundary", "refusal_boundary_route", "refusal boundary", 0.95, ["method_refusal_boundary"], ["shape_refusal_boundary"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_evidence_needed", "evidence_needed", "evidence_needed_route", "evidence needed", 0.95, ["method_evidence_needed"], ["shape_evidence_needed"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_partial_supported", "partial_supported", "partial_supported_route", "partial supported", 0.90, ["method_partial_supported"], ["shape_partial_supported"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_ordinary_task", "ordinary_task", "ordinary_task_route", "ordinary task", 0.90, ["method_ordinary_task"], ["shape_ordinary_task"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_implementation_planning", "implementation_planning", "implementation_planning_route", "implementation planning", 0.90, ["method_implementation_planning"], ["shape_implementation_planning"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_workflow_next_lane", "workflow_next_lane", "workflow_next_lane_route", "workflow next lane", 0.90, ["method_workflow_next_lane"], ["shape_workflow_next_lane"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_governance_escalation", "governance_escalation", "governance_escalation_route", "governance escalation", 0.95, ["method_governance_escalation"], ["shape_governance_escalation"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_teaching_explanation", "teaching_explanation", "teaching_explanation_route", "teaching explanation", 0.90, ["method_teaching_explanation"], ["shape_teaching_explanation"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_language_discovery", "language_discovery", "language_discovery_route", "language discovery", 0.90, ["method_language_discovery"], ["shape_language_discovery"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_scientific_discovery", "scientific_discovery", "scientific_discovery_route", "scientific discovery", 0.90, ["method_scientific_discovery"], ["shape_scientific_discovery"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_benchmark_evaluation", "benchmark_evaluation", "benchmark_evaluation_route", "benchmark evaluation", 0.90, ["method_benchmark_evaluation"], ["shape_benchmark_evaluation"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_unknown_word_phrase", "unknown_word_phrase", "unknown_word_phrase_route", "unknown word/phrase", 0.90, ["method_unknown_word_phrase"], ["shape_unknown_word_phrase"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_unknown_intent", "unknown_intent", "unknown_intent_route", "unknown intent", 0.90, ["method_unknown_intent"], ["shape_unknown_intent"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_unknown_capability", "unknown_capability", "unknown_capability_route", "unknown capability", 0.90, ["method_unknown_capability"], ["shape_unknown_capability"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_friction_repeated_failure", "friction_repeated_failure", "friction_repeated_failure_route", "repeated failure/friction", 0.90, ["method_friction_repeated_failure"], ["shape_friction_repeated_failure"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_relationship_feedback", "relationship_feedback", "relationship_feedback_route", "relationship feedback", 0.90, ["method_relationship_feedback"], ["shape_relationship_feedback"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_correction_repair", "correction_repair", "correction_repair_route", "correction repair", 0.90, ["method_correction_repair"], ["shape_correction_repair"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_conflict_contradiction", "conflict_contradiction", "conflict_contradiction_route", "conflict contradiction", 0.90, ["method_conflict_contradiction"], ["shape_conflict_contradiction"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_non_canned_specificity", "non_canned_specificity", "non_canned_specificity_route", "non-canned specificity", 0.90, ["method_non_canned_specificity"], ["shape_non_canned_specificity"], ["catalog:fallback"]),
        CognitionCaseCandidate("case_directness_concern", "directness_concern", "directness_concern_route", "directness concern", 0.90, ["method_directness_concern"], ["shape_directness_concern"], ["catalog:fallback"]),
    ]


def _candidate_from_any(candidate: Any, cls: Any, fallback_route_id: str) -> Any:
    if isinstance(candidate, cls):
        return candidate
    if is_dataclass(candidate):
        data = candidate.__dict__
    elif isinstance(candidate, Mapping):
        data = dict(candidate)
    else:
        data = {
            key: getattr(candidate, key)
            for key in [
                "method_id",
                "method_family",
                "shape_id",
                "shape_family",
                "case_id",
                "case_family",
                "route_id",
                "label",
                "confidence",
                "compatible_shape_ids",
                "compatible_case_ids",
                "compatible_method_ids",
                "notes",
            ]
            if hasattr(candidate, key)
        }
    route_id = str(data.get("route_id", fallback_route_id))
    label = str(data.get("label", data.get("method_id", data.get("shape_id", data.get("case_id", route_id)))))
    confidence = float(data.get("confidence", 0.5))
    notes = list(data.get("notes", [])) if isinstance(data.get("notes", []), list) else [str(data.get("notes"))]
    if cls is ResponseMethodCandidate:
        return ResponseMethodCandidate(
            method_id=str(data.get("method_id", data.get("id", route_id))),
            method_family=str(data.get("method_family", data.get("family", route_id.replace("_route", "")))),
            route_id=route_id,
            label=label,
            confidence=confidence,
            compatible_shape_ids=_clean_id_list(data.get("compatible_shape_ids", [])),
            compatible_case_ids=_clean_id_list(data.get("compatible_case_ids", [])),
            notes=notes,
        )
    if cls is ResponseShapeCandidate:
        return ResponseShapeCandidate(
            shape_id=str(data.get("shape_id", data.get("id", route_id))),
            shape_family=str(data.get("shape_family", data.get("family", route_id.replace("_route", "")))),
            route_id=route_id,
            label=label,
            confidence=confidence,
            compatible_method_ids=_clean_id_list(data.get("compatible_method_ids", [])),
            compatible_case_ids=_clean_id_list(data.get("compatible_case_ids", [])),
            notes=notes,
        )
    return CognitionCaseCandidate(
        case_id=str(data.get("case_id", data.get("id", route_id))),
        case_family=str(data.get("case_family", data.get("family", route_id.replace("_route", "")))),
        route_id=route_id,
        label=label,
        confidence=confidence,
        compatible_method_ids=_clean_id_list(data.get("compatible_method_ids", [])),
        compatible_shape_ids=_clean_id_list(data.get("compatible_shape_ids", [])),
        notes=notes,
    )


def _normalize_catalog_result(result: Any, fallback_builder: Any) -> List[Any]:
    if result is None:
        return fallback_builder()
    if isinstance(result, list):
        return result
    if isinstance(result, tuple):
        return list(result)
    if isinstance(result, Mapping):
        for key in ("candidates", "methods", "shapes", "cases", "items", "catalog"):
            if key in result and isinstance(result[key], list):
                return result[key]
    if is_dataclass(result) and hasattr(result, "candidates"):
        candidates = getattr(result, "candidates")
        if isinstance(candidates, list):
            return candidates
    if hasattr(result, "candidates"):
        candidates = getattr(result, "candidates")
        if isinstance(candidates, list):
            return candidates
    return fallback_builder()


def _load_external_candidates(module_name: str, selector_name: str, fallback_builder: Any, turn_labels: Any, context_signals: Optional[Mapping[str, Any]]) -> List[Any]:
    try:
        module = __import__(module_name, fromlist=[selector_name])
    except Exception:
        return fallback_builder()
    selector = getattr(module, selector_name, None)
    if not callable(selector):
        return fallback_builder()
    try:
        result = selector(turn_labels=turn_labels, context_signals=context_signals)
    except TypeError:
        try:
            result = selector(turn_labels, context_signals)
        except TypeError:
            try:
                result = selector(turn_labels)
            except Exception:
                return fallback_builder()
    except Exception:
        return fallback_builder()
    return _normalize_catalog_result(result, fallback_builder)


def select_methods_for_turn_v1(turn_labels: Any, context_signals: Optional[Mapping[str, Any]] = None) -> List[ResponseMethodCandidate]:
    candidates = _load_external_candidates("weslr.answer_method_catalog", "select_methods_for_turn_v1", _fallback_method_catalog, turn_labels, context_signals)
    return [_candidate_from_any(candidate, ResponseMethodCandidate, "ordinary_task_route") for candidate in candidates]


def select_answer_shapes_v1(turn_labels: Any, context_signals: Optional[Mapping[str, Any]] = None) -> List[ResponseShapeCandidate]:
    candidates = _load_external_candidates("weslr.answer_shape_catalog", "select_answer_shapes_v1", _fallback_shape_catalog, turn_labels, context_signals)
    return [_candidate_from_any(candidate, ResponseShapeCandidate, "ordinary_task_route") for candidate in candidates]


def select_cognition_cases_v1(turn_labels: Any, context_signals: Optional[Mapping[str, Any]] = None) -> List[CognitionCaseCandidate]:
    candidates = _load_external_candidates("weslr.cognition_case_registry", "select_cognition_cases_v1", _fallback_case_registry, turn_labels, context_signals)
    return [_candidate_from_any(candidate, CognitionCaseCandidate, "ordinary_task_route") for candidate in candidates]


def _route_priority(labels_blob: str, normalized_labels: List[str], signals: Dict[str, Any]) -> List[Tuple[str, float]]:
    priorities: List[Tuple[str, float]] = []
    for spec in _ROUTE_SPECS:
        score = _score_match(labels_blob, spec.keywords)
        if score <= 0.0:
            continue
        if spec.route_id == "clarification_route" and _contains_any(labels_blob, ["clarify", "clarification"]):
            score += 0.2
        if spec.route_id == "evidence_needed_route" and _as_bool(signals.get("evidence_needed")):
            score += 0.2
        if spec.route_id == "governance_escalation_route" and _as_bool(signals.get("needs_owner_approval")):
            score += 0.3
        if spec.route_id == "continuity_route" and _as_bool(signals.get("continuity_signal")):
            score += 0.2
        if spec.route_id == "memory_honesty_route" and _as_bool(signals.get("memory_available")):
            score += 0.1
        if spec.route_id == "relationship_feedback_route" and _as_bool(signals.get("relationship_signal")):
            score += 0.2
        if spec.route_id == "correction_repair_route" and _as_bool(signals.get("correction_signal")):
            score += 0.2
        if spec.route_id == "friction_repeated_failure_route" and _as_bool(signals.get("friction_signal")):
            score += 0.25
        if spec.route_id == "unknown_intent_route" and _as_bool(signals.get("unknown_signal")):
            score += 0.25
        if spec.route_id == "unknown_capability_route" and _as_bool(signals.get("capability_known")) is False:
            score += 0.15
        priorities.append((spec.route_id, score))
    priorities.sort(key=lambda item: (-item[1], _ROUTE_SPECS.index(_ROUTE_LOOKUP[item[0]])))
    return priorities


def _default_route_from_signals(labels_blob: str, signals: Dict[str, Any]) -> _RouteSpec:
    if not labels_blob:
        return _ROUTE_LOOKUP["clarification_route"]
    if _as_bool(signals.get("needs_owner_approval")):
        return _ROUTE_LOOKUP["governance_escalation_route"]
    if _as_bool(signals.get("evidence_needed")):
        return _ROUTE_LOOKUP["evidence_needed_route"]
    if _as_bool(signals.get("friction_signal")):
        return _ROUTE_LOOKUP["friction_repeated_failure_route"]
    if _as_bool(signals.get("unknown_signal")):
        return _ROUTE_LOOKUP["uncertainty_route"]
    return _ROUTE_LOOKUP["clarification_route"]


def _select_route_spec(turn_labels: List[str], context_signals: Dict[str, Any]) -> Tuple[_RouteSpec, bool, List[str], bool, bool, bool]:
    labels_blob = " ".join(turn_labels)
    ordered = _route_priority(labels_blob, turn_labels, context_signals)
    if ordered:
        route_id = ordered[0][0]
        spec = _ROUTE_LOOKUP[route_id]
    else:
        spec = _default_route_from_signals(labels_blob, context_signals)
    unknown_or_friction = spec.unknown_or_friction or _as_bool(context_signals.get("unknown_signal")) or _as_bool(context_signals.get("friction_signal"))
    needs_clarification = spec.needs_clarification or unknown_or_friction or not turn_labels
    needs_evidence = spec.needs_evidence or _as_bool(context_signals.get("evidence_needed"))
    needs_owner_approval = spec.needs_owner_approval or _as_bool(context_signals.get("needs_owner_approval"))
    blocked_labels: List[str] = []
    if needs_clarification:
        blocked_labels.append("needs_clarification")
    if needs_evidence:
        blocked_labels.append("needs_evidence")
    if needs_owner_approval:
        blocked_labels.append("needs_owner_approval")
    if unknown_or_friction:
        blocked_labels.append("unknown_or_friction")
    if spec.blocked:
        blocked_labels.append("route_blocked")
    blocked = bool(blocked_labels)
    return spec, unknown_or_friction, _dedupe_preserve(blocked_labels), needs_clarification, needs_evidence, needs_owner_approval


def _candidate_matches_route(candidate: Any, route_id: str) -> bool:
    return getattr(candidate, "route_id", None) == route_id


def _compatibility_triplets(
    methods: List[ResponseMethodCandidate],
    shapes: List[ResponseShapeCandidate],
    cases: List[CognitionCaseCandidate],
    route_id: str,
) -> List[Tuple[ResponseMethodCandidate, ResponseShapeCandidate, CognitionCaseCandidate, float]]:
    compatible_methods = [m for m in methods if _candidate_matches_route(m, route_id)]
    compatible_shapes = [s for s in shapes if _candidate_matches_route(s, route_id)]
    compatible_cases = [c for c in cases if _candidate_matches_route(c, route_id)]
    combos: List[Tuple[ResponseMethodCandidate, ResponseShapeCandidate, CognitionCaseCandidate, float]] = []
    for method in compatible_methods:
        for shape in compatible_shapes:
            if shape.shape_id not in method.compatible_shape_ids and method.method_id not in shape.compatible_method_ids and route_id not in method.compatible_shape_ids and route_id not in shape.compatible_method_ids:
                continue
            for case in compatible_cases:
                if case.case_id not in method.compatible_case_ids and case.case_id not in shape.compatible_case_ids and method.method_id not in case.compatible_method_ids and shape.shape_id not in case.compatible_shape_ids:
                    continue
                score = method.confidence * 0.4 + shape.confidence * 0.3 + case.confidence * 0.3
                combos.append((method, shape, case, score))
    combos.sort(key=lambda item: (-item[3], item[0].method_id, item[1].shape_id, item[2].case_id))
    return combos


def _fallback_triplet_for_route(route_id: str, methods: List[ResponseMethodCandidate], shapes: List[ResponseShapeCandidate], cases: List[CognitionCaseCandidate]) -> Tuple[ResponseMethodCandidate, ResponseShapeCandidate, CognitionCaseCandidate, float]:
    spec = _ROUTE_LOOKUP[route_id]
    method = next((m for m in methods if m.method_id == spec.method_id), methods[0])
    shape = next((s for s in shapes if s.shape_id == spec.shape_id), shapes[0])
    case = next((c for c in cases if c.case_id == spec.case_id), cases[0])
    score = (method.confidence + shape.confidence + case.confidence) / 3.0
    return method, shape, case, score


def _route_from_selection(method: ResponseMethodCandidate, shape: ResponseShapeCandidate, case: CognitionCaseCandidate) -> str:
    if method.route_id == shape.route_id == case.route_id:
        return method.route_id
    return _ROUTE_LOOKUP["clarification_route"].route_id


def build_response_selection_packet_v1(turn_labels: Any, context_signals: Optional[Mapping[str, Any]] = None) -> ResponseSelectionPacket:
    normalized_labels = _normalize_labels(turn_labels)
    normalized_signals = _normalize_context_signals(context_signals)

    methods = select_methods_for_turn_v1(normalized_labels, normalized_signals)
    shapes = select_answer_shapes_v1(normalized_labels, normalized_signals)
    cases = select_cognition_cases_v1(normalized_labels, normalized_signals)

    spec, unknown_or_friction, blocked_labels, needs_clarification, needs_evidence, needs_owner_approval = _select_route_spec(normalized_labels, normalized_signals)

    triplets = _compatibility_triplets(methods, shapes, cases, spec.route_id)
    if triplets:
        method, shape, case, score = triplets[0]
        route_id = _route_from_selection(method, shape, case)
        if route_id != spec.route_id:
            blocked_labels = _dedupe_preserve(blocked_labels + ["incompatible_selection"])
            spec = _ROUTE_LOOKUP["clarification_route"]
            method, shape, case, score = _fallback_triplet_for_route(spec.route_id, methods, shapes, cases)
    else:
        blocked_labels = _dedupe_preserve(blocked_labels + ["incompatible_selection"])
        spec = _ROUTE_LOOKUP["clarification_route"] if not needs_owner_approval else _ROUTE_LOOKUP["governance_escalation_route"]
        method, shape, case, score = _fallback_triplet_for_route(spec.route_id, methods, shapes, cases)

    route_confidence = max(0.0, min(1.0, score))
    if unknown_or_friction:
        route_confidence = min(route_confidence, 0.55)
    if needs_evidence:
        route_confidence = min(route_confidence, 0.70)
    if needs_owner_approval:
        route_confidence = min(route_confidence, 0.65)
    if not normalized_labels:
        route_confidence = min(route_confidence, 0.50)

    selected_route_id = spec.route_id
    selected_method_id = method.method_id
    selected_shape_id = shape.shape_id
    selected_case_id = case.case_id
    blocked = bool(blocked_labels)

    method_selection = ResponseMethodSelection(
        route_id=selected_route_id,
        selected_method_id=selected_method_id,
        route_confidence=route_confidence,
        candidate_count=len(methods),
        reason=f"Selected {selected_method_id} for {selected_route_id}",
        candidates=methods,
    )
    shape_selection = ResponseShapeSelection(
        route_id=selected_route_id,
        selected_shape_id=selected_shape_id,
        route_confidence=route_confidence,
        candidate_count=len(shapes),
        reason=f"Selected {selected_shape_id} for {selected_route_id}",
        candidates=shapes,
    )
    case_selection = CognitionCaseSelection(
        route_id=selected_route_id,
        selected_case_id=selected_case_id,
        route_confidence=route_confidence,
        candidate_count=len(cases),
        reason=f"Selected {selected_case_id} for {selected_route_id}",
        candidates=cases,
    )

    trace = ResponseSelectionTrace(
        trace_id=f"trace_{selected_route_id}",
        steps=[
            {"step": "normalize_turn_labels", "value": normalized_labels},
            {"step": "normalize_context_signals", "value": sorted(normalized_signals.keys())},
            {"step": "route_spec", "value": selected_route_id},
            {"step": "method_selection", "value": selected_method_id},
            {"step": "shape_selection", "value": selected_shape_id},
            {"step": "case_selection", "value": selected_case_id},
        ],
        notes=["metadata-only", "no final text", "no model/provider usage"],
    )

    safe_metadata = {
        "normalized_turn_labels": normalized_labels,
        "normalized_context_signal_keys": sorted(normalized_signals.keys()),
        "route_family": spec.family,
        "catalog_counts": {
            "methods": len(methods),
            "shapes": len(shapes),
            "cases": len(cases),
        },
        "route_keywords": spec.keywords,
        "trace_id": trace.trace_id,
    }

    return ResponseSelectionPacket(
        selection_type=SELECTION_TYPE,
        turn_labels=normalized_labels,
        context_signals=normalized_signals,
        method_selection=method_selection,
        shape_selection=shape_selection,
        case_selection=case_selection,
        selected_route_id=selected_route_id,
        selected_method_id=selected_method_id,
        selected_shape_id=selected_shape_id,
        selected_case_id=selected_case_id,
        route_confidence=route_confidence,
        unknown_or_friction_detected=unknown_or_friction,
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
        trace=trace,
    )


def select_response_route_v1(turn_labels: Any, context_signals: Optional[Mapping[str, Any]] = None) -> ResponseSelectionPacket:
    return build_response_selection_packet_v1(turn_labels, context_signals=context_signals)


def _serialize_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_serialize_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _serialize_json_safe(item) for key, item in value.items()}
    if is_dataclass(value):
        return {field_name: _serialize_json_safe(getattr(value, field_name)) for field_name in value.__dataclass_fields__}
    if hasattr(value, "to_dict") and callable(getattr(value, "to_dict")):
        return _serialize_json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return {str(k): _serialize_json_safe(v) for k, v in value.__dict__.items() if not str(k).startswith("_")}
    return str(value)


def to_response_selection_json_safe_v1(packet: Any) -> Dict[str, Any]:
    return _serialize_json_safe(packet)


def validate_response_selection_packet_v1(packet: Any) -> bool:
    if isinstance(packet, Mapping):
        data = dict(packet)
    elif is_dataclass(packet):
        data = to_response_selection_json_safe_v1(packet)
    else:
        raise ValidationError("packet must be a ResponseSelectionPacket or mapping")

    required = [
        "selection_type",
        "turn_labels",
        "context_signals",
        "method_selection",
        "shape_selection",
        "case_selection",
        "selected_route_id",
        "selected_method_id",
        "selected_shape_id",
        "selected_case_id",
        "route_confidence",
        "unknown_or_friction_detected",
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
            raise ValidationError(f"missing field: {field_name}")

    if data["selection_type"] != SELECTION_TYPE:
        raise ValidationError("selection_type mismatch")
    if data["runtime_authority"] is not False:
        raise ValidationError("runtime_authority must be false")
    if data["model_provider_used"] is not False:
        raise ValidationError("model_provider_used must be false")
    if data["generates_final_text"] is not False:
        raise ValidationError("generates_final_text must be false")
    if data["writes_state"] is not False:
        raise ValidationError("writes_state must be false")

    if not isinstance(data["turn_labels"], list):
        raise ValidationError("turn_labels must be a list")
    if not isinstance(data["context_signals"], dict):
        raise ValidationError("context_signals must be a dict")
    if not isinstance(data["blocked_labels"], list):
        raise ValidationError("blocked_labels must be a list")
    if not isinstance(data["safe_metadata"], dict):
        raise ValidationError("safe_metadata must be a dict")

    if not isinstance(data["route_confidence"], (int, float)):
        raise ValidationError("route_confidence must be numeric")
    if data["route_confidence"] < 0 or data["route_confidence"] > 1:
        raise ValidationError("route_confidence must be between 0 and 1")

    route_id = data["selected_route_id"]
    if route_id not in _ROUTE_LOOKUP:
        raise ValidationError("selected_route_id unknown")
    spec = _ROUTE_LOOKUP[route_id]

    method_selection = data["method_selection"]
    shape_selection = data["shape_selection"]
    case_selection = data["case_selection"]

    method_id = data["selected_method_id"]
    shape_id = data["selected_shape_id"]
    case_id = data["selected_case_id"]

    method_candidates = method_selection["candidates"] if isinstance(method_selection, Mapping) else to_response_selection_json_safe_v1(method_selection)["candidates"]
    shape_candidates = shape_selection["candidates"] if isinstance(shape_selection, Mapping) else to_response_selection_json_safe_v1(shape_selection)["candidates"]
    case_candidates = case_selection["candidates"] if isinstance(case_selection, Mapping) else to_response_selection_json_safe_v1(case_selection)["candidates"]

    method_ids = {candidate["method_id"] for candidate in method_candidates}
    shape_ids = {candidate["shape_id"] for candidate in shape_candidates}
    case_ids = {candidate["case_id"] for candidate in case_candidates}

    if method_id not in method_ids:
        raise ValidationError("selected_method_id must exist in method catalog")
    if shape_id not in shape_ids:
        raise ValidationError("selected_shape_id must exist in shape catalog")
    if case_id not in case_ids:
        raise ValidationError("selected_case_id must exist in case registry")

    method = next(candidate for candidate in method_candidates if candidate["method_id"] == method_id)
    shape = next(candidate for candidate in shape_candidates if candidate["shape_id"] == shape_id)
    case = next(candidate for candidate in case_candidates if candidate["case_id"] == case_id)

    compatible = (
        (shape_id in method.get("compatible_shape_ids", []) or method_id in shape.get("compatible_method_ids", []) or route_id in method.get("compatible_shape_ids", []))
        and (case_id in method.get("compatible_case_ids", []) or case_id in shape.get("compatible_case_ids", []) or method_id in case.get("compatible_method_ids", []) or shape_id in case.get("compatible_shape_ids", []))
        and method.get("route_id") == shape.get("route_id") == case.get("route_id") == route_id
    )
    if not compatible:
        raise ValidationError("selected method/shape/case combination is incompatible")

    if len(_dedupe_preserve(data["blocked_labels"])) != len(data["blocked_labels"]):
        raise ValidationError("blocked_labels must not contain duplicates")
    if len(_ROUTE_LOOKUP) != len({spec.route_id for spec in _ROUTE_SPECS}):
        raise ValidationError("duplicate route IDs detected")

    for field_name in ["runtime_authority", "model_provider_used", "generates_final_text", "writes_state"]:
        if data[field_name] is not False:
            raise ValidationError(f"forbidden authority drift: {field_name}")

    return True


def summarize_response_selection_packet_v1(packet: Any) -> Dict[str, Any]:
    data = to_response_selection_json_safe_v1(packet)
    return {
        "selection_type": data.get("selection_type"),
        "route_id": data.get("selected_route_id"),
        "method_id": data.get("selected_method_id"),
        "shape_id": data.get("selected_shape_id"),
        "case_id": data.get("selected_case_id"),
        "blocked": data.get("blocked"),
        "blocked_labels": data.get("blocked_labels", []),
        "route_confidence": data.get("route_confidence"),
        "family": data.get("safe_metadata", {}).get("route_family"),
        "turn_labels": data.get("turn_labels", []),
    }


__all__ = [
    "ResponseMethodCandidate",
    "ResponseShapeCandidate",
    "CognitionCaseCandidate",
    "ResponseMethodSelection",
    "ResponseShapeSelection",
    "CognitionCaseSelection",
    "ResponseSelectionTrace",
    "ResponseSelectionPacket",
    "build_response_selection_packet_v1",
    "validate_response_selection_packet_v1",
    "summarize_response_selection_packet_v1",
    "to_response_selection_json_safe_v1",
    "select_response_route_v1",
    "select_methods_for_turn_v1",
    "select_answer_shapes_v1",
    "select_cognition_cases_v1",
]
