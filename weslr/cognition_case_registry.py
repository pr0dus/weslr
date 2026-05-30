"""Metadata-only cognition case registry v1.

This module is intentionally pure, deterministic, and fail-closed.
It connects turn situations to allowed answer methods and answer shapes
without generating answer prose or wiring runtime behavior.

It does not perform file I/O, network I/O, subprocess execution, runtime/chat
wiring, live response routing, provider/model/search/advisor calls, dot-weslr
IO, or answer rendering.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping

from weslr.answer_method_catalog import build_answer_method_catalog_v1
from weslr.answer_shape_catalog import build_answer_shape_catalog_v1

HELPER_TYPE_V1 = "weslr_cognition_case_registry_v1"
REGISTRY_TYPE_V1 = "cognition_case_registry_v1"
CASE_SPEC_TYPE_V1 = "cognition_case_spec_v1"
CASE_MATCH_TYPE_V1 = "cognition_case_match_v1"
CASE_SELECTION_TYPE_V1 = "cognition_case_selection_v1"
SUMMARY_TYPE_V1 = "cognition_case_registry_summary_v1"

ALLOWED_CASE_FAMILIES_V1 = {
    "identity_status",
    "boundary_uncertainty",
    "task_workflow",
    "teaching_explanation_discovery",
    "relationship_correction_continuity",
    "response_shape_quality",
    "unknown_friction",
    "evidence_provenance",
    "memory_continuity",
    "capability_governance",
}

ALLOWED_METHOD_IDS_V1 = {
    method.method_id for method in build_answer_method_catalog_v1().methods
}
ALLOWED_SHAPE_IDS_V1 = {
    shape.shape_id for shape in build_answer_shape_catalog_v1().shapes
}

ALLOWED_IMPLEMENTATION_STATUSES_V1 = {
    "catalog_registered",
}

SOURCE_REFS_COMMON_V1 = (
    "docs/WESLR_ANSWER_MATRIX_AND_METHOD_CATALOG_IMPLEMENTATION_EXTRACTION_V1.md",
    "weslr/answer_method_catalog.py",
    "weslr/answer_shape_catalog.py",
)

IDENTITY_SOURCE_REFS_V1 = SOURCE_REFS_COMMON_V1 + (
    "weslr/meaning_response.py",
    "docs/WESLR_STABLE_IDENTITY_AND_ADAPTIVE_DELIVERY_DOCTRINE_V1.md",
)

BOUNDARY_SOURCE_REFS_V1 = SOURCE_REFS_COMMON_V1 + (
    "weslr/native_reasoning_frame.py",
    "weslr/native_response_self_check.py",
    "weslr/native_response_assembly.py",
)

TASK_SOURCE_REFS_V1 = SOURCE_REFS_COMMON_V1 + (
    "weslr/ordinary_reasoning_guidance.py",
    "weslr/targeted_response_formation_improvement.py",
)

TEACHING_SOURCE_REFS_V1 = SOURCE_REFS_COMMON_V1 + (
    "weslr/meaning_response.py",
    "grammar.md",
    "vocabulary.md",
    "docs/WESLR_TEACHING_EXPLANATION_DESIGN_V1.md",
)

RELATIONSHIP_SOURCE_REFS_V1 = SOURCE_REFS_COMMON_V1 + (
    "weslr/meaning_response.py",
    "weslr/targeted_response_formation_improvement.py",
    "weslr/meaning_state_context.py",
)

QUALITY_SOURCE_REFS_V1 = SOURCE_REFS_COMMON_V1 + (
    "weslr/targeted_response_formation_improvement.py",
    "weslr/reasoning_trace.py",
    "weslr/reasoning_arbitrator.py",
)

UNKNOWN_SOURCE_REFS_V1 = SOURCE_REFS_COMMON_V1 + (
    "weslr/controlled_unknown_engine_metadata_shadow_runner.py",
    "docs/WESLR_UNKNOWN_ENGINE_BOUNDARY_V1.md",
)

MEMORY_SOURCE_REFS_V1 = SOURCE_REFS_COMMON_V1 + (
    "weslr/entity_timeline_memory.py",
    "weslr/user_timeline_memory.py",
    "weslr/meaning_state_context.py",
)

CAPABILITY_SOURCE_REFS_V1 = SOURCE_REFS_COMMON_V1 + (
    "weslr/capability_registry.py",
    "weslr/meaning_response.py",
)


@dataclass(frozen=True, slots=True)
class CognitionCaseSpec:
    case_id: str
    case_family: str
    name: str
    purpose: str
    turn_signals: tuple[str, ...]
    required_context: tuple[str, ...]
    missing_context_signals: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    memory_requirements: tuple[str, ...]
    capability_requirements: tuple[str, ...]
    relationship_signals: tuple[str, ...]
    friction_signals: tuple[str, ...]
    unknown_signals: tuple[str, ...]
    allowed_method_ids: tuple[str, ...]
    allowed_shape_ids: tuple[str, ...]
    blocked_if: tuple[str, ...]
    selection_priority: int
    risk_notes: str
    source_refs: tuple[str, ...]
    runtime_authority: bool
    model_required: bool
    writes_state: bool
    generates_final_text: bool
    safe_for_case_selection: bool
    implementation_status: str = "catalog_registered"


@dataclass(frozen=True, slots=True)
class CognitionCaseRegistryPacket:
    registry_type: str
    cases: tuple[CognitionCaseSpec, ...]
    fallback_case_id: str


@dataclass(frozen=True, slots=True)
class CognitionCaseMatch:
    case_id: str
    case_family: str
    name: str
    match_score: int
    matched_turn_signals: tuple[str, ...]
    matched_unknown_signals: tuple[str, ...]
    matched_friction_signals: tuple[str, ...]
    matched_relationship_signals: tuple[str, ...]
    method_overlap: tuple[str, ...]
    shape_overlap: tuple[str, ...]
    allowed_method_ids: tuple[str, ...]
    allowed_shape_ids: tuple[str, ...]
    selection_priority: int


@dataclass(frozen=True, slots=True)
class CognitionCaseSelection:
    selection_type: str
    registry_type: str
    turn_labels: tuple[str, ...]
    unknown_labels: tuple[str, ...]
    fallback_used: bool
    selected_case_ids: tuple[str, ...]
    selected_cases: tuple[dict[str, Any], ...]
    rejected_case_ids: tuple[str, ...]
    method_candidate_summary: dict[str, Any]
    shape_candidate_summary: dict[str, Any]
    registry_summary: dict[str, Any]


_CASE_SPECS_V1: tuple[dict[str, Any], ...] = (
    {
        "case_id": "identity_self_description_case",
        "case_family": "identity_status",
        "name": "Identity self-description case",
        "purpose": "Map identity/self-description turns to bounded identity and status shapes.",
        "turn_signals": ("identity", "status", "who are you", "what are you", "about you", "self description"),
        "required_context": ("verified identity state", "relationship state", "scope boundary"),
        "missing_context_signals": ("missing identity context", "missing status context"),
        "evidence_requirements": ("verified identity scope", "capability boundary"),
        "memory_requirements": ("memory scope", "trusted continuity"),
        "capability_requirements": ("capability boundary",),
        "relationship_signals": ("new contact", "working relationship"),
        "friction_signals": (),
        "unknown_signals": (),
        "allowed_method_ids": ("verified_identity_status_answer_v1", "new_contact_orientation_answer_v1"),
        "allowed_shape_ids": ("direct_bounded_answer", "memory_honesty_answer"),
        "blocked_if": ("raw private memory requested", "runtime authority", "unsupported persona claims"),
        "selection_priority": 100,
        "risk_notes": "Should not widen into persona or authority claims.",
        "source_refs": IDENTITY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "status_current_capability_case",
        "case_family": "identity_status",
        "name": "Current capability status case",
        "purpose": "Map capability questions to bounded capability orientation.",
        "turn_signals": ("capability", "can you", "what can you do", "help with", "able to"),
        "required_context": ("capability boundary", "domain context"),
        "missing_context_signals": ("missing capability context",),
        "evidence_requirements": ("capability boundary",),
        "memory_requirements": (),
        "capability_requirements": ("capability boundary", "current mode"),
        "relationship_signals": (),
        "friction_signals": (),
        "unknown_signals": (),
        "allowed_method_ids": ("capability_orientation_answer_v1",),
        "allowed_shape_ids": ("direct_bounded_answer",),
        "blocked_if": ("runtime authority", "model claim"),
        "selection_priority": 95,
        "risk_notes": "Should stay descriptive and bounded.",
        "source_refs": CAPABILITY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "memory_honesty_case",
        "case_family": "memory_continuity",
        "name": "Memory honesty case",
        "purpose": "Map memory/recall questions to honest continuity boundaries.",
        "turn_signals": ("memory", "remember", "recall", "do you remember", "continuity"),
        "required_context": ("memory availability", "scope", "freshness"),
        "missing_context_signals": ("missing continuity context",),
        "evidence_requirements": ("trusted memory scope",),
        "memory_requirements": ("memory availability", "trust labels"),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": (),
        "unknown_signals": (),
        "allowed_method_ids": ("memory_report_answer_v1",),
        "allowed_shape_ids": ("memory_honesty_answer",),
        "blocked_if": ("raw private memory requested", "fake memory claims"),
        "selection_priority": 98,
        "risk_notes": "Must not imply total recall.",
        "source_refs": MEMORY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "continuity_thread_recap_case",
        "case_family": "memory_continuity",
        "name": "Continuity thread recap case",
        "purpose": "Map follow-up turns to thread-aware continuity recap.",
        "turn_signals": ("what were we doing", "follow-up", "thread", "continuity", "previous point"),
        "required_context": ("continuity state", "recent turns"),
        "missing_context_signals": ("missing thread context",),
        "evidence_requirements": (),
        "memory_requirements": ("continuity state", "timeline anchors"),
        "capability_requirements": (),
        "relationship_signals": ("working thread",),
        "friction_signals": (),
        "unknown_signals": (),
        "allowed_method_ids": ("continuity_thread_answer_v1", "memory_report_answer_v1"),
        "allowed_shape_ids": ("continuity_thread_recap_answer", "memory_honesty_answer"),
        "blocked_if": ("thread unavailable", "no continuity need"),
        "selection_priority": 97,
        "risk_notes": "Can become verbose if not bounded.",
        "source_refs": MEMORY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "capability_orientation_case",
        "case_family": "capability_governance",
        "name": "Capability orientation case",
        "purpose": "Map capability prompts to next safe capability-oriented action.",
        "turn_signals": ("capability", "can you", "what can you do", "help with"),
        "required_context": ("capability boundary", "domain context"),
        "missing_context_signals": ("missing capability boundary",),
        "evidence_requirements": ("capability boundary",),
        "memory_requirements": (),
        "capability_requirements": ("capability boundary",),
        "relationship_signals": (),
        "friction_signals": (),
        "unknown_signals": (),
        "allowed_method_ids": ("capability_orientation_answer_v1",),
        "allowed_shape_ids": ("direct_bounded_answer",),
        "blocked_if": ("runtime authority", "official claim"),
        "selection_priority": 99,
        "risk_notes": "Must not drift into evaluation or runtime authority.",
        "source_refs": CAPABILITY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "clarification_needed_case",
        "case_family": "boundary_uncertainty",
        "name": "Clarification needed case",
        "purpose": "Map ambiguity to a minimal clarifying question.",
        "turn_signals": ("clarify", "clarification", "ambiguous", "unclear", "missing"),
        "required_context": ("missing context slots", "uncertainty labels"),
        "missing_context_signals": ("missing context", "ambiguous intent"),
        "evidence_requirements": (),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": (),
        "unknown_signals": ("unknown intent",),
        "allowed_method_ids": ("clarifying_question_answer_v1",),
        "allowed_shape_ids": ("clarifying_question",),
        "blocked_if": ("already answered", "sufficient context"),
        "selection_priority": 93,
        "risk_notes": "Should not expand into a checklist.",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "bounded_uncertainty_case",
        "case_family": "boundary_uncertainty",
        "name": "Bounded uncertainty case",
        "purpose": "Represent low-confidence or incomplete evidence without fake certainty.",
        "turn_signals": ("uncertain", "uncertainty", "unsure", "maybe", "not sure"),
        "required_context": ("uncertainty labels", "confidence"),
        "missing_context_signals": ("missing evidence",),
        "evidence_requirements": ("evidence sufficiency",),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": (),
        "unknown_signals": ("unknown result",),
        "allowed_method_ids": ("bounded_uncertainty_answer_v1", "unknown_engine_branch_friction_answer_v1"),
        "allowed_shape_ids": ("bounded_uncertainty_answer", "unknown_friction_branch_answer"),
        "blocked_if": ("evidence sufficient", "certainty overstated"),
        "selection_priority": 91,
        "risk_notes": "Can become evasive if overused.",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "refusal_boundary_case",
        "case_family": "boundary_uncertainty",
        "name": "Refusal boundary case",
        "purpose": "Map unsafe or unauthorized prompts to refusal/boundary metadata.",
        "turn_signals": ("refuse", "refusal", "boundary", "unsafe", "not allowed", "privacy"),
        "required_context": ("denied authority flags", "safety boundary"),
        "missing_context_signals": ("missing safety context",),
        "evidence_requirements": (),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": ("safety friction",),
        "unknown_signals": (),
        "allowed_method_ids": ("refusal_boundary_answer_v1", "governance_escalation_proposal_v1"),
        "allowed_shape_ids": ("refusal_boundary_answer", "governance_escalation_answer"),
        "blocked_if": ("no boundary issue", "runtime authorization implied"),
        "selection_priority": 92,
        "risk_notes": "Refusal should remain useful and bounded.",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "evidence_needed_case",
        "case_family": "evidence_provenance",
        "name": "Evidence needed case",
        "purpose": "Require evidence before stronger claims.",
        "turn_signals": ("evidence", "source", "prove", "current", "latest", "need evidence"),
        "required_context": ("evidence need", "source scope", "claim burden"),
        "missing_context_signals": ("missing evidence",),
        "evidence_requirements": ("source scope", "claim burden"),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": (),
        "unknown_signals": (),
        "allowed_method_ids": ("evidence_needed_answer_v1", "scientific_discovery_capability_guidance_answer_v1", "benchmark_evaluation_answer_v1"),
        "allowed_shape_ids": ("evidence_needed_answer", "scientific_discovery_guidance_answer", "benchmark_evaluation_summary_answer"),
        "blocked_if": ("evidence sufficient", "raw transcript requested"),
        "selection_priority": 90,
        "risk_notes": "Should point to the next safe evidence step.",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "partial_supported_case",
        "case_family": "boundary_uncertainty",
        "name": "Partial supported case",
        "purpose": "Answer the supported part and label the unsupported remainder.",
        "turn_signals": ("partial", "supported", "portion", "split", "some parts"),
        "required_context": ("supported facts", "unsupported remainder"),
        "missing_context_signals": ("missing support boundary",),
        "evidence_requirements": ("evidence gaps",),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": (),
        "unknown_signals": (),
        "allowed_method_ids": ("partial_answer_supported_portion_answer_v1",),
        "allowed_shape_ids": ("partial_supported_answer",),
        "blocked_if": ("all-or-nothing refusal only", "no supported portion exists"),
        "selection_priority": 89,
        "risk_notes": "Can become patchy if support boundaries are vague.",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "ordinary_task_planning_case",
        "case_family": "task_workflow",
        "name": "Ordinary task planning case",
        "purpose": "Provide safe step planning for ordinary tasks.",
        "turn_signals": ("task", "plan", "steps", "workflow", "checklist", "ordinary task"),
        "required_context": ("task markers", "constraints"),
        "missing_context_signals": ("missing task context",),
        "evidence_requirements": (),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": (),
        "unknown_signals": (),
        "allowed_method_ids": ("ordinary_task_planning_answer_v1", "artifact_workspace_planning_answer_v1"),
        "allowed_shape_ids": ("stepwise_plan_answer",),
        "blocked_if": ("unsafe action", "needs operator approval"),
        "selection_priority": 88,
        "risk_notes": "Should remain concrete and not generic.",
        "source_refs": TASK_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "implementation_planning_case",
        "case_family": "task_workflow",
        "name": "Implementation planning case",
        "purpose": "Turn a design gap into a constrained implementation plan.",
        "turn_signals": ("implementation", "build", "code", "what should we code", "lane"),
        "required_context": ("target gaps", "authority calibration"),
        "missing_context_signals": ("missing implementation context",),
        "evidence_requirements": (),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": (),
        "unknown_signals": (),
        "allowed_method_ids": ("implementation_planning_answer_v1",),
        "allowed_shape_ids": ("implementation_plan_answer",),
        "blocked_if": ("runtime authority", "no design gap"),
        "selection_priority": 87,
        "risk_notes": "Must not become a live roadmap engine.",
        "source_refs": TASK_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "workflow_next_lane_case",
        "case_family": "task_workflow",
        "name": "Workflow next lane case",
        "purpose": "Say what lane should happen next, based on readiness and blockers.",
        "turn_signals": ("next lane", "sequence", "roadmap", "what next"),
        "required_context": ("readiness", "blocked flags"),
        "missing_context_signals": ("missing sequencing context",),
        "evidence_requirements": (),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": (),
        "unknown_signals": (),
        "allowed_method_ids": ("workflow_next_lane_answer_v1",),
        "allowed_shape_ids": ("workflow_next_lane_answer",),
        "blocked_if": ("no sequencing context", "single-turn direct answer fit"),
        "selection_priority": 86,
        "risk_notes": "Should remain a recommendation, not an authority claim.",
        "source_refs": TASK_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "governance_escalation_case",
        "case_family": "capability_governance",
        "name": "Governance escalation case",
        "purpose": "Propose operator review when authority is missing or blocked.",
        "turn_signals": ("approval", "escalate", "operator review", "decision needed", "blocked"),
        "required_context": ("approval requirement", "denied authority fields"),
        "missing_context_signals": ("missing approval context",),
        "evidence_requirements": (),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": ("approval friction",),
        "unknown_signals": (),
        "allowed_method_ids": ("governance_escalation_proposal_v1",),
        "allowed_shape_ids": ("governance_escalation_answer",),
        "blocked_if": ("no approval needed", "runtime authorization implied"),
        "selection_priority": 85,
        "risk_notes": "Must not pretend to authorize itself.",
        "source_refs": CAPABILITY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "teaching_explanation_case",
        "case_family": "teaching_explanation_discovery",
        "name": "Teaching explanation case",
        "purpose": "Explain concepts in a teachable, human-readable form.",
        "turn_signals": ("teach", "teaching", "explain", "explanation", "education"),
        "required_context": ("audience level", "vocabulary", "domain context"),
        "missing_context_signals": ("missing teaching context",),
        "evidence_requirements": ("evidence needs",),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": (),
        "unknown_signals": (),
        "allowed_method_ids": ("teaching_explanation_answer_v1",),
        "allowed_shape_ids": ("teaching_explanation_answer",),
        "blocked_if": ("no teaching intent", "boundary refusal required"),
        "selection_priority": 84,
        "risk_notes": "Should stay teachable, not encyclopedic.",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "language_discovery_explanation_case",
        "case_family": "teaching_explanation_discovery",
        "name": "Language discovery explanation case",
        "purpose": "Translate internal form into human-understandable language.",
        "turn_signals": ("language", "grammar", "vocabulary", "discover language", "words"),
        "required_context": ("internal signals", "target audience"),
        "missing_context_signals": ("missing language context",),
        "evidence_requirements": (),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": (),
        "unknown_signals": (),
        "allowed_method_ids": ("language_grammar_vocabulary_discovery_answer_v1",),
        "allowed_shape_ids": ("language_discovery_explanation_answer",),
        "blocked_if": ("translation theater", "unknown language claims"),
        "selection_priority": 83,
        "risk_notes": "Must not pretend to discover an unknown language by magic.",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "scientific_discovery_guidance_case",
        "case_family": "teaching_explanation_discovery",
        "name": "Scientific discovery guidance case",
        "purpose": "Guide research and discovery with a staged workflow and boundary notes.",
        "turn_signals": ("scientific", "research", "discovery", "experiment", "capability guidance"),
        "required_context": ("novelty", "structural sanity", "evidence gates"),
        "missing_context_signals": ("missing research context",),
        "evidence_requirements": ("evidence gates",),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": (),
        "unknown_signals": (),
        "allowed_method_ids": ("scientific_discovery_capability_guidance_answer_v1",),
        "allowed_shape_ids": ("scientific_discovery_guidance_answer",),
        "blocked_if": ("official discovery claim", "no research framing"),
        "selection_priority": 82,
        "risk_notes": "Can overpromise discovery if not bounded.",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "benchmark_evaluation_summary_case",
        "case_family": "evidence_provenance",
        "name": "Benchmark evaluation summary case",
        "purpose": "Explain evaluation status without asserting official benchmark results.",
        "turn_signals": ("benchmark", "evaluation", "turing", "readiness", "assessment"),
        "required_context": ("task schema", "trace", "legibility"),
        "missing_context_signals": ("missing evaluation context",),
        "evidence_requirements": ("trace", "anti-gaming"),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": (),
        "unknown_signals": (),
        "allowed_method_ids": ("benchmark_evaluation_answer_v1",),
        "allowed_shape_ids": ("benchmark_evaluation_summary_answer",),
        "blocked_if": ("official scoring claim", "certification claim"),
        "selection_priority": 81,
        "risk_notes": "Must remain non-official and metadata-only.",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "unknown_word_or_phrase_case",
        "case_family": "unknown_friction",
        "name": "Unknown word or phrase case",
        "purpose": "Represent unknown vocabulary or phrase meaning as bounded uncertainty.",
        "turn_signals": ("unknown word", "unknown phrase", "what does this mean", "phrase"),
        "required_context": ("unknown signal",),
        "missing_context_signals": ("missing meaning context",),
        "evidence_requirements": (),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": ("friction",),
        "unknown_signals": ("unknown word", "unknown phrase"),
        "allowed_method_ids": ("unknown_engine_branch_friction_answer_v1", "clarifying_question_answer_v1"),
        "allowed_shape_ids": ("unknown_friction_branch_answer", "clarifying_question"),
        "blocked_if": ("oracle framing", "meaning certainty"),
        "selection_priority": 80,
        "risk_notes": "Must stay explicit about uncertainty.",
        "source_refs": UNKNOWN_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "unknown_intent_case",
        "case_family": "unknown_friction",
        "name": "Unknown intent case",
        "purpose": "Represent unclear turn intent and route to clarification or bounded uncertainty.",
        "turn_signals": ("unknown intent", "unclear intent", "what do you mean"),
        "required_context": ("unknown intent signal",),
        "missing_context_signals": ("missing intent context",),
        "evidence_requirements": (),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": ("intent friction",),
        "unknown_signals": ("unknown intent",),
        "allowed_method_ids": ("direct_bounded_answer_v1", "unknown_engine_branch_friction_answer_v1", "bounded_uncertainty_answer_v1", "clarifying_question_answer_v1"),
        "allowed_shape_ids": ("clarifying_question", "bounded_uncertainty_answer", "unknown_friction_branch_answer", "direct_bounded_answer"),
        "blocked_if": ("intent already clear",),
        "selection_priority": 85,
        "risk_notes": "Should not guess user intent without disclosure.",
        "source_refs": UNKNOWN_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "unknown_capability_request_case",
        "case_family": "capability_governance",
        "name": "Unknown capability request case",
        "purpose": "Represent requests for capabilities not yet safely exposed.",
        "turn_signals": ("can you do this", "capability request", "future capability"),
        "required_context": ("capability boundary",),
        "missing_context_signals": ("missing capability boundary",),
        "evidence_requirements": (),
        "memory_requirements": (),
        "capability_requirements": ("capability boundary",),
        "relationship_signals": (),
        "friction_signals": ("capability friction",),
        "unknown_signals": ("future capability",),
        "allowed_method_ids": ("capability_orientation_answer_v1", "governance_escalation_proposal_v1", "unknown_engine_branch_friction_answer_v1"),
        "allowed_shape_ids": ("direct_bounded_answer", "governance_escalation_answer", "clarifying_question"),
        "blocked_if": ("runtime authority", "public pilot"),
        "selection_priority": 84,
        "risk_notes": "Must remain a boundary response, not a promise.",
        "source_refs": CAPABILITY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "friction_repeated_failure_case",
        "case_family": "unknown_friction",
        "name": "Repeated failure friction case",
        "purpose": "Capture repeated failure or friction as an unknown/friction branch.",
        "turn_signals": ("repeated failure", "friction", "blocked", "stuck", "keeps failing"),
        "required_context": ("friction signals", "failure pattern"),
        "missing_context_signals": ("missing friction context",),
        "evidence_requirements": ("failure pattern",),
        "memory_requirements": ("continuity state",),
        "capability_requirements": (),
        "relationship_signals": ("frustration",),
        "friction_signals": ("repeated failure", "stuck"),
        "unknown_signals": ("unknown failure zone",),
        "allowed_method_ids": ("unknown_engine_branch_friction_answer_v1", "bounded_uncertainty_answer_v1"),
        "allowed_shape_ids": ("unknown_friction_branch_answer", "directness_concern_integrated_answer"),
        "blocked_if": ("problem already solved",),
        "selection_priority": 77,
        "risk_notes": "Should point to a bounded hypothesis or next safe step.",
        "source_refs": UNKNOWN_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "relationship_feedback_case",
        "case_family": "relationship_correction_continuity",
        "name": "Relationship feedback case",
        "purpose": "Handle tone, trust, feedback, and user preference signals.",
        "turn_signals": ("feedback", "preference", "frustration", "trust", "tone"),
        "required_context": ("relationship context", "trust state"),
        "missing_context_signals": ("missing relationship context",),
        "evidence_requirements": (),
        "memory_requirements": ("relationship continuity",),
        "capability_requirements": (),
        "relationship_signals": ("feedback", "preference"),
        "friction_signals": ("frustration",),
        "unknown_signals": (),
        "allowed_method_ids": ("relationship_feedback_answer_v1",),
        "allowed_shape_ids": ("relationship_feedback_answer",),
        "blocked_if": ("fake empathy", "roleplay"),
        "selection_priority": 76,
        "risk_notes": "Should acknowledge without overperforming emotion.",
        "source_refs": RELATIONSHIP_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "correction_repair_case",
        "case_family": "relationship_correction_continuity",
        "name": "Correction repair case",
        "purpose": "Repair the answer after correction by changing shape and framing.",
        "turn_signals": ("correction", "wrong", "revise", "fix", "actually"),
        "required_context": ("correction history", "answer-shape gap"),
        "missing_context_signals": ("missing correction context",),
        "evidence_requirements": (),
        "memory_requirements": ("correction history",),
        "capability_requirements": (),
        "relationship_signals": ("correction",),
        "friction_signals": ("misalignment",),
        "unknown_signals": (),
        "allowed_method_ids": ("correction_repair_answer_v1", "directness_concern_integration_self_check_v1"),
        "allowed_shape_ids": ("correction_repair_answer", "directness_concern_integrated_answer"),
        "blocked_if": ("no correction history",),
        "selection_priority": 75,
        "risk_notes": "Should not become apology theater.",
        "source_refs": RELATIONSHIP_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "conflict_contradiction_case",
        "case_family": "relationship_correction_continuity",
        "name": "Conflict contradiction case",
        "purpose": "Preserve contradictions instead of erasing them.",
        "turn_signals": ("conflict", "contradiction", "clash", "inconsistent", "both true"),
        "required_context": ("conflict records", "missing assumptions"),
        "missing_context_signals": ("missing assumptions",),
        "evidence_requirements": ("evidence conflict",),
        "memory_requirements": ("continuity state",),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": ("contradiction",),
        "unknown_signals": (),
        "allowed_method_ids": ("conflict_contradiction_handling_answer_v1", "partial_answer_supported_portion_answer_v1"),
        "allowed_shape_ids": ("conflict_contradiction_answer", "partial_supported_answer"),
        "blocked_if": ("no contradiction",),
        "selection_priority": 74,
        "risk_notes": "Should make the contradiction visible.",
        "source_refs": RELATIONSHIP_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "non_canned_specificity_pressure_case",
        "case_family": "response_shape_quality",
        "name": "Non-canned specificity pressure case",
        "purpose": "Detect template drift and apply non-cannedness pressure.",
        "turn_signals": ("canned", "template", "boilerplate", "generic", "repeated"),
        "required_context": ("specificity markers",),
        "missing_context_signals": ("missing specificity context",),
        "evidence_requirements": (),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": (),
        "friction_signals": ("template drift",),
        "unknown_signals": (),
        "allowed_method_ids": ("non_cannedness_pressure_v1",),
        "allowed_shape_ids": ("non_canned_specific_answer",),
        "blocked_if": ("generic fallback only",),
        "selection_priority": 73,
        "risk_notes": "Not a style guide; a quality guard.",
        "source_refs": QUALITY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
    {
        "case_id": "directness_concern_integration_case",
        "case_family": "response_shape_quality",
        "name": "Directness concern integration case",
        "purpose": "Balance directness, concern handling, and self-check before final shape choice.",
        "turn_signals": ("directness", "concern", "self-check", "empathy", "loaded"),
        "required_context": ("concern slot", "directness pressure"),
        "missing_context_signals": ("missing concern context",),
        "evidence_requirements": (),
        "memory_requirements": (),
        "capability_requirements": (),
        "relationship_signals": ("concern",),
        "friction_signals": ("friction",),
        "unknown_signals": (),
        "allowed_method_ids": ("directness_concern_integration_self_check_v1", "relationship_feedback_answer_v1", "bounded_uncertainty_answer_v1"),
        "allowed_shape_ids": ("directness_concern_integrated_answer", "relationship_feedback_answer", "bounded_uncertainty_answer"),
        "blocked_if": ("fake empathy", "runtime authority"),
        "selection_priority": 72,
        "risk_notes": "Should remain grounded and not performative.",
        "source_refs": QUALITY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_case_selection": True,
    },
)

_FALLBACK_CASE_ID_V1 = "clarification_needed_case"

_ALLOWED_PACKET_KEYS_V1 = {
    "registry_type",
    "cases",
    "fallback_case_id",
}

_ALLOWED_CASE_KEYS_V1 = {
    "case_id",
    "case_family",
    "name",
    "purpose",
    "turn_signals",
    "required_context",
    "missing_context_signals",
    "evidence_requirements",
    "memory_requirements",
    "capability_requirements",
    "relationship_signals",
    "friction_signals",
    "unknown_signals",
    "allowed_method_ids",
    "allowed_shape_ids",
    "blocked_if",
    "selection_priority",
    "risk_notes",
    "source_refs",
    "runtime_authority",
    "model_required",
    "writes_state",
    "generates_final_text",
    "safe_for_case_selection",
    "implementation_status",
}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _safe_bool(value: Any) -> bool:
    return bool(value) is True


def _safe_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _safe_text_list(value: Any) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for item in _safe_list(value):
        text = _safe_str(item)
        if text and text not in seen:
            items.append(text)
            seen.add(text)
    return items


def _tokenize(value: Any) -> set[str]:
    text = _safe_str(value).lower()
    token = []
    tokens: set[str] = set()
    for char in text:
        if char.isalnum():
            token.append(char)
        else:
            if token:
                tokens.add("".join(token))
                token = []
    if token:
        tokens.add("".join(token))
    return tokens


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
        return [_json_safe(item) for item in sorted(value, key=lambda item: _safe_str(item))]
    return value


def _case_spec_to_dataclass(case_data: Mapping[str, Any]) -> CognitionCaseSpec:
    def _filled(value: Any, placeholder: str) -> tuple[str, ...]:
        items = tuple(_safe_text_list(value))
        return items if items else (placeholder,)

    return CognitionCaseSpec(
        case_id=_safe_str(case_data.get("case_id")),
        case_family=_safe_str(case_data.get("case_family")),
        name=_safe_str(case_data.get("name")),
        purpose=_safe_str(case_data.get("purpose")),
        turn_signals=_filled(case_data.get("turn_signals"), "signal_placeholder"),
        required_context=_filled(case_data.get("required_context"), "context_placeholder"),
        missing_context_signals=_filled(case_data.get("missing_context_signals"), "missing_context_placeholder"),
        evidence_requirements=_filled(case_data.get("evidence_requirements"), "evidence_placeholder"),
        memory_requirements=_filled(case_data.get("memory_requirements"), "memory_placeholder"),
        capability_requirements=_filled(case_data.get("capability_requirements"), "capability_placeholder"),
        relationship_signals=_filled(case_data.get("relationship_signals"), "relationship_placeholder"),
        friction_signals=_filled(case_data.get("friction_signals"), "friction_placeholder"),
        unknown_signals=_filled(case_data.get("unknown_signals"), "unknown_placeholder"),
        allowed_method_ids=_filled(case_data.get("allowed_method_ids"), "method_placeholder"),
        allowed_shape_ids=_filled(case_data.get("allowed_shape_ids"), "shape_placeholder"),
        blocked_if=_filled(case_data.get("blocked_if"), "blocked_placeholder"),
        selection_priority=int(case_data.get("selection_priority") or 0),
        risk_notes=_safe_str(case_data.get("risk_notes")),
        source_refs=_filled(case_data.get("source_refs"), "source_placeholder"),
        runtime_authority=_safe_bool(case_data.get("runtime_authority")),
        model_required=_safe_bool(case_data.get("model_required")),
        writes_state=_safe_bool(case_data.get("writes_state")),
        generates_final_text=_safe_bool(case_data.get("generates_final_text")),
        safe_for_case_selection=_safe_bool(case_data.get("safe_for_case_selection")),
        implementation_status=_safe_str(case_data.get("implementation_status") or "catalog_registered"),
    )


def build_cognition_case_registry_v1() -> CognitionCaseRegistryPacket:
    cases = tuple(_case_spec_to_dataclass(case_data) for case_data in _CASE_SPECS_V1)
    return CognitionCaseRegistryPacket(
        registry_type=REGISTRY_TYPE_V1,
        cases=cases,
        fallback_case_id=_FALLBACK_CASE_ID_V1,
    )


def _catalog_to_mapping(value: Any) -> Mapping[str, Any]:
    if is_dataclass(value):
        return _as_mapping(asdict(value))
    if isinstance(value, Mapping):
        return value
    return {}


def validate_cognition_case_registry_v1(registry: Mapping[str, Any] | CognitionCaseRegistryPacket | None = None) -> dict[str, Any]:
    packet = _catalog_to_mapping(registry or build_cognition_case_registry_v1())
    normalized = to_cognition_case_registry_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        normalized = {}

    blocked_labels: list[str] = []
    cases_value = _safe_list(normalized.get("cases"))
    fallback_case_id = _safe_str(normalized.get("fallback_case_id"))

    if set(normalized.keys()) - _ALLOWED_PACKET_KEYS_V1:
        blocked_labels.append("unexpected_packet_field")
    if _safe_str(normalized.get("registry_type")) != REGISTRY_TYPE_V1:
        blocked_labels.append("invalid_registry_type")
    if not cases_value:
        blocked_labels.append("missing_cases")
    if not fallback_case_id:
        blocked_labels.append("missing_fallback_case_id")

    case_ids_seen: set[str] = set()
    case_families_seen: dict[str, int] = {family_id: 0 for family_id in ALLOWED_CASE_FAMILIES_V1}

    method_ids = ALLOWED_METHOD_IDS_V1
    shape_ids = ALLOWED_SHAPE_IDS_V1

    for case_value in cases_value:
        case = _as_mapping(case_value)
        if set(case.keys()) - _ALLOWED_CASE_KEYS_V1:
            blocked_labels.append("unexpected_case_field")
        case_id = _safe_str(case.get("case_id"))
        case_family = _safe_str(case.get("case_family"))
        name = _safe_str(case.get("name"))
        purpose = _safe_str(case.get("purpose"))
        turn_signals = _safe_text_list(case.get("turn_signals"))
        required_context = _safe_text_list(case.get("required_context"))
        missing_context_signals = _safe_text_list(case.get("missing_context_signals"))
        evidence_requirements = _safe_text_list(case.get("evidence_requirements"))
        memory_requirements = _safe_text_list(case.get("memory_requirements"))
        capability_requirements = _safe_text_list(case.get("capability_requirements"))
        relationship_signals = _safe_text_list(case.get("relationship_signals"))
        friction_signals = _safe_text_list(case.get("friction_signals"))
        unknown_signals = _safe_text_list(case.get("unknown_signals"))
        allowed_method_ids = _safe_text_list(case.get("allowed_method_ids"))
        allowed_shape_ids = _safe_text_list(case.get("allowed_shape_ids"))
        blocked_if = _safe_text_list(case.get("blocked_if"))
        selection_priority = int(case.get("selection_priority") or 0)
        risk_notes = _safe_str(case.get("risk_notes"))
        source_refs = _safe_text_list(case.get("source_refs"))
        runtime_authority = _safe_bool(case.get("runtime_authority"))
        model_required = _safe_bool(case.get("model_required"))
        writes_state = _safe_bool(case.get("writes_state"))
        generates_final_text = _safe_bool(case.get("generates_final_text"))
        safe_for_case_selection = _safe_bool(case.get("safe_for_case_selection"))
        implementation_status = _safe_str(case.get("implementation_status"))

        if not case_id:
            blocked_labels.append("missing_case_id")
        if case_id in case_ids_seen:
            blocked_labels.append("duplicate_case_id")
        case_ids_seen.add(case_id)
        if case_family not in ALLOWED_CASE_FAMILIES_V1:
            blocked_labels.append("unknown_case_family")
        else:
            case_families_seen[case_family] += 1
        if not name:
            blocked_labels.append("missing_case_name")
        if not purpose:
            blocked_labels.append("missing_case_purpose")
        if not turn_signals:
            blocked_labels.append("missing_turn_signals")
        if not required_context:
            blocked_labels.append("missing_required_context")
        if not missing_context_signals:
            blocked_labels.append("missing_missing_context_signals")
        if not evidence_requirements:
            blocked_labels.append("missing_evidence_requirements")
        if not memory_requirements:
            blocked_labels.append("missing_memory_requirements")
        if not capability_requirements:
            blocked_labels.append("missing_capability_requirements")
        if not relationship_signals:
            blocked_labels.append("missing_relationship_signals")
        if not friction_signals:
            blocked_labels.append("missing_friction_signals")
        if not unknown_signals:
            blocked_labels.append("missing_unknown_signals")
        if not allowed_method_ids:
            blocked_labels.append("missing_allowed_method_ids")
        if not allowed_shape_ids:
            blocked_labels.append("missing_allowed_shape_ids")
        if not blocked_if:
            blocked_labels.append("missing_blocked_if")
        if selection_priority <= 0:
            blocked_labels.append("invalid_selection_priority")
        if not risk_notes:
            blocked_labels.append("missing_risk_notes")
        if not source_refs:
            blocked_labels.append("missing_source_refs")
        if implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES_V1:
            blocked_labels.append("unknown_implementation_status")
        if runtime_authority:
            blocked_labels.append("runtime_authority_must_be_false")
        if model_required:
            blocked_labels.append("model_required_must_be_false")
        if writes_state:
            blocked_labels.append("writes_state_must_be_false")
        if generates_final_text:
            blocked_labels.append("generates_final_text_must_be_false")
        if not safe_for_case_selection:
            blocked_labels.append("unsafe_for_case_selection")
        invalid_methods = [item for item in allowed_method_ids if item not in method_ids]
        if invalid_methods:
            blocked_labels.append("unknown_allowed_method_id")
        invalid_shapes = [item for item in allowed_shape_ids if item not in shape_ids]
        if invalid_shapes:
            blocked_labels.append("unknown_allowed_shape_id")

    if ALLOWED_CASE_FAMILIES_V1 - set(case_families_seen.keys()):
        blocked_labels.append("missing_required_case_family")
    if _FALLBACK_CASE_ID_V1 and _FALLBACK_CASE_ID_V1 not in case_ids_seen:
        blocked_labels.append("missing_fallback_case")
    if fallback_case_id and fallback_case_id not in case_ids_seen:
        blocked_labels.append("fallback_case_not_registered")

    valid = not blocked_labels
    return {
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": sorted(set(blocked_labels)),
        "registry_type": _safe_str(normalized.get("registry_type")),
        "case_count": len(cases_value),
        "case_family_count": sum(1 for value in case_families_seen.values() if value > 0),
        "fallback_case_id": fallback_case_id,
        "case_family_usage": dict(sorted(case_families_seen.items())),
    }


def summarize_cognition_case_registry_v1(registry: Mapping[str, Any] | CognitionCaseRegistryPacket | None = None) -> dict[str, Any]:
    packet = _catalog_to_mapping(registry or build_cognition_case_registry_v1())
    normalized = to_cognition_case_registry_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        normalized = {}

    cases = _safe_list(normalized.get("cases"))
    family_usage: dict[str, int] = {}
    case_ids = []
    selectable_case_count = 0
    for case_value in cases:
        case = _as_mapping(case_value)
        family = _safe_str(case.get("case_family"))
        case_id = _safe_str(case.get("case_id"))
        if family:
            family_usage[family] = family_usage.get(family, 0) + 1
        if case_id:
            case_ids.append(case_id)
        if _safe_bool(case.get("safe_for_case_selection")):
            selectable_case_count += 1

    return {
        "summary_type": SUMMARY_TYPE_V1,
        "registry_type": _safe_str(normalized.get("registry_type")),
        "case_count": len(cases),
        "case_family_count": len([family for family, count in family_usage.items() if count > 0]),
        "selectable_case_count": selectable_case_count,
        "fallback_case_id": _safe_str(normalized.get("fallback_case_id")),
        "case_family_usage": dict(sorted(family_usage.items())),
        "case_ids": sorted(case_ids),
    }


def to_cognition_case_registry_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def _method_candidates_to_list(method_candidates: Any) -> list[dict[str, Any]]:
    if method_candidates is None:
        return []
    if isinstance(method_candidates, Mapping) and "selected_methods" in method_candidates:
        raw = method_candidates.get("selected_methods")
    elif isinstance(method_candidates, Mapping) and "selected_method_ids" in method_candidates:
        raw = method_candidates.get("selected_method_ids")
    else:
        raw = method_candidates
    candidates: list[dict[str, Any]] = []
    for item in _safe_list(raw):
        if isinstance(item, Mapping):
            candidates.append(dict(item))
        else:
            text = _safe_str(item)
            if text:
                candidates.append({"method_id": text})
    return candidates


def _shape_candidates_to_list(shape_candidates: Any) -> list[dict[str, Any]]:
    if shape_candidates is None:
        return []
    if isinstance(shape_candidates, Mapping) and "selected_shapes" in shape_candidates:
        raw = shape_candidates.get("selected_shapes")
    elif isinstance(shape_candidates, Mapping) and "selected_shape_ids" in shape_candidates:
        raw = shape_candidates.get("selected_shape_ids")
    else:
        raw = shape_candidates
    candidates: list[dict[str, Any]] = []
    for item in _safe_list(raw):
        if isinstance(item, Mapping):
            candidates.append(dict(item))
        else:
            text = _safe_str(item)
            if text:
                candidates.append({"shape_id": text})
    return candidates


def _case_tokens(case: Mapping[str, Any]) -> set[str]:
    tokens = set()
    for key in (
        "case_id",
        "case_family",
        "name",
        "purpose",
        "turn_signals",
        "required_context",
        "missing_context_signals",
        "evidence_requirements",
        "memory_requirements",
        "capability_requirements",
        "relationship_signals",
        "friction_signals",
        "unknown_signals",
        "blocked_if",
        "risk_notes",
    ):
        tokens |= _tokenize(case.get(key))
    return tokens


def _case_is_compatible_with_candidate(case: Mapping[str, Any], method_candidates: list[dict[str, Any]], shape_candidates: list[dict[str, Any]]) -> bool:
    allowed_methods = set(_safe_text_list(case.get("allowed_method_ids")))
    allowed_shapes = set(_safe_text_list(case.get("allowed_shape_ids")))
    if method_candidates:
        if not any(_safe_str(candidate.get("method_id")) in allowed_methods for candidate in method_candidates):
            return False
    if shape_candidates:
        if not any(_safe_str(candidate.get("shape_id")) in allowed_shapes for candidate in shape_candidates):
            return False
    return True


def _score_case(turn_text: str, turn_tokens: set[str], case: Mapping[str, Any], method_candidates: list[dict[str, Any]], shape_candidates: list[dict[str, Any]]) -> tuple[int, int, int]:
    tokens = _case_tokens(case)
    label_score = len(turn_tokens & tokens)
    priority = int(case.get("selection_priority") or 0)
    compat_score = 0
    if method_candidates:
        allowed_methods = set(_safe_text_list(case.get("allowed_method_ids")))
        compat_score += sum(1 for candidate in method_candidates if _safe_str(candidate.get("method_id")) in allowed_methods)
    if shape_candidates:
        allowed_shapes = set(_safe_text_list(case.get("allowed_shape_ids")))
        compat_score += sum(1 for candidate in shape_candidates if _safe_str(candidate.get("shape_id")) in allowed_shapes)
    if not method_candidates and not shape_candidates:
        compat_score = 1
    return (label_score, compat_score, priority)


def select_cognition_cases_v1(
    turn_labels: Iterable[Any],
    method_candidates: Any = None,
    shape_candidates: Any = None,
    registry: Mapping[str, Any] | CognitionCaseRegistryPacket | None = None,
) -> dict[str, Any]:
    packet = _catalog_to_mapping(registry or build_cognition_case_registry_v1())
    normalized = to_cognition_case_registry_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        normalized = {}

    labels = _safe_text_list(turn_labels)
    turn_text = " ".join(labels).lower()
    turn_tokens: set[str] = set()
    for label in labels:
        turn_tokens |= _tokenize(label)

    method_list = _method_candidates_to_list(method_candidates)
    shape_list = _shape_candidates_to_list(shape_candidates)
    method_summary = {
        "candidate_count": len(method_list),
        "candidate_method_ids": sorted({_safe_str(candidate.get("method_id")) for candidate in method_list if _safe_str(candidate.get("method_id"))}),
        "candidate_family_ids": sorted({_safe_str(candidate.get("family_id")) for candidate in method_list if _safe_str(candidate.get("family_id"))}),
    }
    shape_summary = {
        "candidate_count": len(shape_list),
        "candidate_shape_ids": sorted({_safe_str(candidate.get("shape_id")) for candidate in shape_list if _safe_str(candidate.get("shape_id"))}),
    }

    cases = _safe_list(normalized.get("cases"))
    selected: list[dict[str, Any]] = []
    rejected: list[str] = []
    matched_unknown: set[str] = set()
    matched_friction: set[str] = set()
    matched_relationship: set[str] = set()

    for case_value in cases:
        case = _as_mapping(case_value)
        case_id = _safe_str(case.get("case_id"))
        if not _safe_bool(case.get("safe_for_case_selection")):
            rejected.append(case_id)
            continue
        if not _case_is_compatible_with_candidate(case, method_list, shape_list):
            rejected.append(case_id)
            continue
        score, compat, priority = _score_case(turn_text, turn_tokens, case, method_list, shape_list)
        if score <= 0:
            continue
        matched = sorted(turn_tokens & _case_tokens(case))
        unknown_matches = sorted(turn_tokens & _tokenize(case.get("unknown_signals")))
        friction_matches = sorted(turn_tokens & _tokenize(case.get("friction_signals")))
        relationship_matches = sorted(turn_tokens & _tokenize(case.get("relationship_signals")))
        matched_unknown.update(unknown_matches)
        matched_friction.update(friction_matches)
        matched_relationship.update(relationship_matches)
        selected.append(
            {
                "case_id": case_id,
                "case_family": _safe_str(case.get("case_family")),
                "name": _safe_str(case.get("name")),
                "purpose": _safe_str(case.get("purpose")),
                "turn_signals": _safe_text_list(case.get("turn_signals")),
                "required_context": _safe_text_list(case.get("required_context")),
                "missing_context_signals": _safe_text_list(case.get("missing_context_signals")),
                "evidence_requirements": _safe_text_list(case.get("evidence_requirements")),
                "memory_requirements": _safe_text_list(case.get("memory_requirements")),
                "capability_requirements": _safe_text_list(case.get("capability_requirements")),
                "relationship_signals": _safe_text_list(case.get("relationship_signals")),
                "friction_signals": _safe_text_list(case.get("friction_signals")),
                "unknown_signals": _safe_text_list(case.get("unknown_signals")),
                "allowed_method_ids": _safe_text_list(case.get("allowed_method_ids")),
                "allowed_shape_ids": _safe_text_list(case.get("allowed_shape_ids")),
                "blocked_if": _safe_text_list(case.get("blocked_if")),
                "selection_priority": int(case.get("selection_priority") or 0),
                "risk_notes": _safe_str(case.get("risk_notes")),
                "source_refs": _safe_text_list(case.get("source_refs")),
                "safe_for_case_selection": _safe_bool(case.get("safe_for_case_selection")),
                "implementation_status": _safe_str(case.get("implementation_status")),
                "match_score": score,
                "compatibility_score": compat,
                "matched_turn_signals": matched,
                "matched_unknown_signals": unknown_matches,
                "matched_friction_signals": friction_matches,
                "matched_relationship_signals": relationship_matches,
            }
        )

    selected.sort(key=lambda item: (-int(item["match_score"]), -int(item["compatibility_score"]), -int(item["selection_priority"]), item["case_id"]))
    unknown_labels = sorted(label for label in labels if not _tokenize(label) & _case_tokens(_as_mapping(cases[0] if cases else {})))
    fallback_used = False

    if selected:
        selected = selected[:1]
        selected_ids = [selected[0]["case_id"]]
    else:
        selected_ids = []
        fallback_candidates = ["unknown_intent_case", "clarification_needed_case", "friction_repeated_failure_case"]
        for fallback_case_id in fallback_candidates:
            fallback = next((case for case in cases if _safe_str(_as_mapping(case).get("case_id")) == fallback_case_id), None)
            if fallback is None:
                continue
            fallback_map = _as_mapping(fallback)
            if not _case_is_compatible_with_candidate(fallback_map, method_list, shape_list):
                continue
            fallback_used = True
            selected = [
                {
                    "case_id": _safe_str(fallback_map.get("case_id")),
                    "case_family": _safe_str(fallback_map.get("case_family")),
                    "name": _safe_str(fallback_map.get("name")),
                    "purpose": _safe_str(fallback_map.get("purpose")),
                    "turn_signals": _safe_text_list(fallback_map.get("turn_signals")),
                    "required_context": _safe_text_list(fallback_map.get("required_context")),
                    "missing_context_signals": _safe_text_list(fallback_map.get("missing_context_signals")),
                    "evidence_requirements": _safe_text_list(fallback_map.get("evidence_requirements")),
                    "memory_requirements": _safe_text_list(fallback_map.get("memory_requirements")),
                    "capability_requirements": _safe_text_list(fallback_map.get("capability_requirements")),
                    "relationship_signals": _safe_text_list(fallback_map.get("relationship_signals")),
                    "friction_signals": _safe_text_list(fallback_map.get("friction_signals")),
                    "unknown_signals": _safe_text_list(fallback_map.get("unknown_signals")),
                    "allowed_method_ids": _safe_text_list(fallback_map.get("allowed_method_ids")),
                    "allowed_shape_ids": _safe_text_list(fallback_map.get("allowed_shape_ids")),
                    "blocked_if": _safe_text_list(fallback_map.get("blocked_if")),
                    "selection_priority": int(fallback_map.get("selection_priority") or 0),
                    "risk_notes": _safe_str(fallback_map.get("risk_notes")),
                    "source_refs": _safe_text_list(fallback_map.get("source_refs")),
                    "safe_for_case_selection": _safe_bool(fallback_map.get("safe_for_case_selection")),
                    "implementation_status": _safe_str(fallback_map.get("implementation_status")),
                    "match_score": 0,
                    "compatibility_score": 1,
                    "matched_turn_signals": [],
                    "matched_unknown_signals": [],
                    "matched_friction_signals": [],
                    "matched_relationship_signals": [],
                }
            ]
            selected_ids = [selected[0]["case_id"]]
            break

    rejected = sorted(set(rejected) - set(selected_ids))
    selected_method_ids = sorted({item for case in selected for item in case.get("allowed_method_ids", [])})
    selected_shape_ids = sorted({item for case in selected for item in case.get("allowed_shape_ids", [])})

    return {
        "selection_type": CASE_SELECTION_TYPE_V1,
        "registry_type": _safe_str(normalized.get("registry_type")),
        "turn_labels": labels,
        "turn_tokens": sorted(turn_tokens),
        "unknown_labels": unknown_labels,
        "fallback_used": fallback_used,
        "selected_case_ids": selected_ids,
        "selected_cases": selected,
        "rejected_case_ids": rejected,
        "selected_method_ids": selected_method_ids,
        "selected_shape_ids": selected_shape_ids,
        "selected_unknown_signals": sorted(matched_unknown),
        "selected_friction_signals": sorted(matched_friction),
        "selected_relationship_signals": sorted(matched_relationship),
        "method_candidate_summary": method_summary,
        "shape_candidate_summary": shape_summary,
        "registry_summary": summarize_cognition_case_registry_v1(normalized),
    }


__all__ = [
    "CognitionCaseSpec",
    "CognitionCaseRegistryPacket",
    "CognitionCaseMatch",
    "CognitionCaseSelection",
    "build_cognition_case_registry_v1",
    "validate_cognition_case_registry_v1",
    "summarize_cognition_case_registry_v1",
    "to_cognition_case_registry_json_safe_v1",
    "select_cognition_cases_v1",
]
