"""Metadata-only answer shape catalog v1.

This module is intentionally pure, deterministic, and fail-closed.
It separates answer-shape selection from answer-method selection and final
prose generation.

It does not perform file I/O, network I/O, subprocess execution, runtime/chat
wiring, live response routing, provider/model/search/advisor calls, dot-weslr
IO, or answer rendering.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping

from weslr.answer_method_catalog import (
    AnswerMethodCatalogPacket,
    build_answer_method_catalog_v1,
    select_methods_for_turn_v1,
)

HELPER_TYPE_V1 = "weslr_answer_shape_catalog_v1"
CATALOG_TYPE_V1 = "answer_shape_catalog_v1"
SHAPE_SPEC_TYPE_V1 = "answer_shape_spec_v1"
SHAPE_SELECTION_TYPE_V1 = "answer_shape_selection_v1"
SUMMARY_TYPE_V1 = "answer_shape_catalog_summary_v1"

ALLOWED_METHOD_FAMILIES_V1 = {
    "identity_status",
    "boundary_uncertainty",
    "task_workflow",
    "teaching_explanation_discovery",
    "relationship_correction_continuity",
    "response_shape_quality",
}

ALLOWED_IMPLEMENTATION_STATUSES_V1 = {
    "catalog_registered",
}

ALLOWED_SHAPE_IDS_V1 = {
    "direct_bounded_answer",
    "clarifying_question",
    "bounded_uncertainty_answer",
    "refusal_boundary_answer",
    "evidence_needed_answer",
    "partial_supported_answer",
    "stepwise_plan_answer",
    "implementation_plan_answer",
    "workflow_next_lane_answer",
    "governance_escalation_answer",
    "teaching_explanation_answer",
    "language_discovery_explanation_answer",
    "scientific_discovery_guidance_answer",
    "benchmark_evaluation_summary_answer",
    "unknown_friction_branch_answer",
    "memory_honesty_answer",
    "continuity_thread_recap_answer",
    "relationship_feedback_answer",
    "correction_repair_answer",
    "conflict_contradiction_answer",
    "non_canned_specific_answer",
    "directness_concern_integrated_answer",
}

SOURCE_REFS_COMMON_V1 = (
    "docs/WESLR_ANSWER_MATRIX_AND_METHOD_CATALOG_IMPLEMENTATION_EXTRACTION_V1.md",
    "weslr/answer_method_catalog.py",
    "docs/WESLR_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_V1.md",
    "docs/WESLR_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1.md",
    "docs/WESLR_UNIFIED_RESPONSE_FORMATION_CANON_V1.md",
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


@dataclass(frozen=True, slots=True)
class AnswerShapeCompatibility:
    shape_id: str
    compatible_method_families: tuple[str, ...]
    compatible_method_ids: tuple[str, ...]
    blocked_if: tuple[str, ...]
    safe_for_shape_selection: bool


@dataclass(frozen=True, slots=True)
class AnswerShapeSpec:
    shape_id: str
    name: str
    purpose: str
    use_when: str
    avoid_when: str
    required_inputs: tuple[str, ...]
    compatible_method_families: tuple[str, ...]
    compatible_method_ids: tuple[str, ...]
    blocked_if: tuple[str, ...]
    output_contract: str
    risk_notes: str
    source_refs: tuple[str, ...]
    runtime_authority: bool
    model_required: bool
    writes_state: bool
    generates_final_text: bool
    safe_for_shape_selection: bool
    implementation_status: str = "catalog_registered"


@dataclass(frozen=True, slots=True)
class AnswerShapeCatalogPacket:
    catalog_type: str
    shapes: tuple[AnswerShapeSpec, ...]
    fallback_shape_id: str


@dataclass(frozen=True, slots=True)
class AnswerShapeSelection:
    selection_type: str
    catalog_type: str
    turn_labels: tuple[str, ...]
    unknown_labels: tuple[str, ...]
    fallback_used: bool
    selected_shape_ids: tuple[str, ...]
    selected_shapes: tuple[dict[str, Any], ...]
    rejected_shape_ids: tuple[str, ...]
    method_candidate_summary: dict[str, Any]
    catalog_summary: dict[str, Any]


_SHAPE_SPECS_V1: tuple[dict[str, Any], ...] = (
    {
        "shape_id": "direct_bounded_answer",
        "name": "Direct bounded answer",
        "purpose": "Answer directly when the intent is clear and the grounding is sufficient.",
        "use_when": "A turn can be answered directly without hiding uncertainty or authority limits.",
        "avoid_when": "The request is ambiguous, blocked, or needs clarification or evidence.",
        "required_inputs": ("clear intent", "sufficient grounding", "boundary calibration"),
        "compatible_method_families": ("identity_status", "boundary_uncertainty", "relationship_correction_continuity"),
        "compatible_method_ids": (
            "verified_identity_status_answer_v1",
            "direct_bounded_answer_v1",
            "memory_report_answer_v1",
            "continuity_thread_answer_v1",
            "relationship_feedback_answer_v1",
        ),
        "blocked_if": ("unknown intent", "missing grounding", "safety boundary", "authority boundary"),
        "output_contract": "Direct answer with explicit bounds and no unsupported claims.",
        "risk_notes": "Can become overconfident if used without grounding.",
        "source_refs": IDENTITY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "clarifying_question",
        "name": "Clarifying question",
        "purpose": "Ask the smallest useful question to remove ambiguity.",
        "use_when": "The turn is underspecified and one precise question would unblock progress.",
        "avoid_when": "The answer can be given safely without further input.",
        "required_inputs": ("missing context slots", "uncertainty labels", "response obligation"),
        "compatible_method_families": ("boundary_uncertainty", "task_workflow"),
        "compatible_method_ids": ("clarifying_question_answer_v1", "governance_escalation_proposal_v1"),
        "blocked_if": ("sufficient context", "already answered", "final prose required"),
        "output_contract": "Single focused question plus bounded reason if needed.",
        "risk_notes": "Should not expand into a checklist of questions.",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "bounded_uncertainty_answer",
        "name": "Bounded uncertainty answer",
        "purpose": "Preserve uncertainty instead of inventing confidence.",
        "use_when": "Evidence is incomplete or confidence is low.",
        "avoid_when": "A direct supported answer is available.",
        "required_inputs": ("uncertainty labels", "confidence", "evidence sufficiency"),
        "compatible_method_families": ("boundary_uncertainty", "teaching_explanation_discovery"),
        "compatible_method_ids": ("bounded_uncertainty_answer_v1", "evidence_needed_answer_v1", "unknown_engine_branch_friction_answer_v1"),
        "blocked_if": ("evidence sufficient", "certainty overstated", "runtime authority"),
        "output_contract": "Answer with explicit uncertainty boundary and no fake certainty.",
        "risk_notes": "Can become evasive if overused.",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "refusal_boundary_answer",
        "name": "Refusal / boundary answer",
        "purpose": "Refuse unsupported, unsafe, or unauthorized requests while staying useful.",
        "use_when": "A request crosses privacy, authority, or safety boundaries.",
        "avoid_when": "The request is safe and answerable.",
        "required_inputs": ("denied authority flags", "blocked labels", "safety boundary"),
        "compatible_method_families": ("boundary_uncertainty", "task_workflow"),
        "compatible_method_ids": ("refusal_boundary_answer_v1", "governance_escalation_proposal_v1"),
        "blocked_if": ("no boundary issue", "must produce final answer prose"),
        "output_contract": "Refusal plus a bounded alternative or next safe step.",
        "risk_notes": "Should not become a wall of policy text.",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "evidence_needed_answer",
        "name": "Evidence-needed answer",
        "purpose": "Say stronger claims need evidence and point to the next safe evidence step.",
        "use_when": "The turn asks for current facts, sources, or claims that need grounding.",
        "avoid_when": "Evidence is already sufficient.",
        "required_inputs": ("evidence need", "source scope", "claim burden"),
        "compatible_method_families": ("boundary_uncertainty", "teaching_explanation_discovery"),
        "compatible_method_ids": ("evidence_needed_answer_v1", "scientific_discovery_capability_guidance_answer_v1", "benchmark_evaluation_answer_v1"),
        "blocked_if": ("evidence sufficient", "unsupported certainty", "raw transcript requested"),
        "output_contract": "Evidence request or evidence next-step plan.",
        "risk_notes": "Can over-refuse if not paired with a concrete next step.",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "partial_supported_answer",
        "name": "Partial supported answer",
        "purpose": "Answer the supported part and label the unsupported remainder.",
        "use_when": "Some parts of the request are safe and answerable while others are not.",
        "avoid_when": "Nothing can be safely answered.",
        "required_inputs": ("supported facts", "unsupported remainder", "evidence gaps"),
        "compatible_method_families": ("boundary_uncertainty", "relationship_correction_continuity"),
        "compatible_method_ids": ("partial_answer_supported_portion_answer_v1", "direct_bounded_answer_v1", "conflict_contradiction_handling_answer_v1"),
        "blocked_if": ("all-or-nothing refusal only", "final prose required", "no supported portion exists"),
        "output_contract": "Split answer with explicit gaps.",
        "risk_notes": "Can become patchy if support boundaries are not explicit.",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "stepwise_plan_answer",
        "name": "Stepwise plan answer",
        "purpose": "Provide a safe step-by-step plan for ordinary tasks.",
        "use_when": "The user wants procedural guidance or a work plan.",
        "avoid_when": "The turn needs a direct bounded answer or clarification first.",
        "required_inputs": ("task markers", "constraints", "missing context", "tool need"),
        "compatible_method_families": ("task_workflow",),
        "compatible_method_ids": ("ordinary_task_planning_answer_v1", "artifact_workspace_planning_answer_v1"),
        "blocked_if": ("no task framing", "unsafe action", "needs operator approval"),
        "output_contract": "Numbered steps or bounded next actions.",
        "risk_notes": "Should remain concrete and not drift into generic advice.",
        "source_refs": TASK_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "implementation_plan_answer",
        "name": "Implementation plan answer",
        "purpose": "Turn a design gap into a constrained implementation plan.",
        "use_when": "The question is about what to build first or how to structure a lane.",
        "avoid_when": "The user asked for a direct answer or explanation.",
        "required_inputs": ("target gaps", "answer-shape policy", "authority calibration"),
        "compatible_method_families": ("task_workflow",),
        "compatible_method_ids": ("implementation_planning_answer_v1",),
        "blocked_if": ("no design gap", "final prose required", "runtime authority"),
        "output_contract": "Implementation plan with a first safe step.",
        "risk_notes": "Should not silently become a live roadmap engine.",
        "source_refs": TASK_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "workflow_next_lane_answer",
        "name": "Workflow next-lane answer",
        "purpose": "Say what lane should happen next, based on readiness and blockers.",
        "use_when": "A sequencing decision is needed.",
        "avoid_when": "The answer should be a direct result, not a plan.",
        "required_inputs": ("gap labels", "readiness", "blocked flags"),
        "compatible_method_families": ("task_workflow",),
        "compatible_method_ids": ("workflow_next_lane_answer_v1",),
        "blocked_if": ("no sequencing context", "single-turn direct answer fit"),
        "output_contract": "Next-lane recommendation only.",
        "risk_notes": "Can overemphasize sequencing over resolution.",
        "source_refs": TASK_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "governance_escalation_answer",
        "name": "Governance escalation answer",
        "purpose": "Propose operator review when authority is missing or blocked.",
        "use_when": "A decision needs approval or is blocked by policy.",
        "avoid_when": "No approval or escalation is required.",
        "required_inputs": ("approval requirement", "denied authority fields"),
        "compatible_method_families": ("task_workflow", "boundary_uncertainty"),
        "compatible_method_ids": ("governance_escalation_proposal_v1", "clarifying_question_answer_v1"),
        "blocked_if": ("no approval needed", "runtime authorization implied"),
        "output_contract": "Escalation note or review proposal.",
        "risk_notes": "Must not pretend to authorize itself.",
        "source_refs": TASK_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "teaching_explanation_answer",
        "name": "Teaching explanation answer",
        "purpose": "Explain concepts in a teachable, human-readable form.",
        "use_when": "The user asks to explain or teach a concept.",
        "avoid_when": "The turn is a direct factual lookup or a boundary refusal.",
        "required_inputs": ("audience level", "vocabulary", "domain context", "evidence needs"),
        "compatible_method_families": ("teaching_explanation_discovery",),
        "compatible_method_ids": ("teaching_explanation_answer_v1",),
        "blocked_if": ("no teaching intent", "final prose required by another path"),
        "output_contract": "Staged explanation or teachable summary.",
        "risk_notes": "Should stay teachable, not encyclopedic.",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "language_discovery_explanation_answer",
        "name": "Language discovery explanation answer",
        "purpose": "Translate internal form into human-understandable language.",
        "use_when": "The turn is about grammar, vocabulary, or language discovery.",
        "avoid_when": "A generic explanation is enough.",
        "required_inputs": ("internal signals", "preferred vocabulary", "target audience"),
        "compatible_method_families": ("teaching_explanation_discovery",),
        "compatible_method_ids": ("language_grammar_vocabulary_discovery_answer_v1",),
        "blocked_if": ("translation theater", "unknown language claims", "runtime authority"),
        "output_contract": "Human-readable translation or teaching-oriented language.",
        "risk_notes": "Must not pretend to discover an unknown language by magic.",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "scientific_discovery_guidance_answer",
        "name": "Scientific discovery guidance answer",
        "purpose": "Guide research and discovery with a staged workflow and boundary notes.",
        "use_when": "The turn asks for research, discovery, or experiment guidance.",
        "avoid_when": "The turn needs direct answer or refusal.",
        "required_inputs": ("candidate generation constraints", "novelty", "structural sanity", "evidence gates"),
        "compatible_method_families": ("teaching_explanation_discovery",),
        "compatible_method_ids": ("scientific_discovery_capability_guidance_answer_v1",),
        "blocked_if": ("no research framing", "official discovery claim"),
        "output_contract": "Stepwise research plan with boundary notes.",
        "risk_notes": "Can overpromise discovery if not bounded.",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "benchmark_evaluation_summary_answer",
        "name": "Benchmark evaluation summary answer",
        "purpose": "Explain evaluation status without asserting official benchmark results.",
        "use_when": "The turn is about evaluation, benchmarking, or readiness summaries.",
        "avoid_when": "The answer must be a live or official score claim.",
        "required_inputs": ("task schema", "trace", "conflicts", "legibility", "anti-gaming"),
        "compatible_method_families": ("teaching_explanation_discovery",),
        "compatible_method_ids": ("benchmark_evaluation_answer_v1",),
        "blocked_if": ("official scoring claim", "certification claim", "runtime authority"),
        "output_contract": "Evaluation summary or readiness label with caveat.",
        "risk_notes": "Must remain non-official and metadata-only.",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "unknown_friction_branch_answer",
        "name": "Unknown / friction branch answer",
        "purpose": "Represent uncertainty, branches, friction, and bounded hypotheses.",
        "use_when": "The turn is about unknowns, friction, or repeated failure patterns.",
        "avoid_when": "A direct supported answer exists.",
        "required_inputs": ("knowns", "unknowns", "missing evidence", "branch assumptions"),
        "compatible_method_families": ("teaching_explanation_discovery", "boundary_uncertainty"),
        "compatible_method_ids": ("unknown_engine_branch_friction_answer_v1", "bounded_uncertainty_answer_v1"),
        "blocked_if": ("future certainty", "oracle framing", "official claim"),
        "output_contract": "Metadata-only uncertainty record or graded proposal.",
        "risk_notes": "Should not become a prediction oracle.",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "memory_honesty_answer",
        "name": "Memory honesty answer",
        "purpose": "State what memory is available and what is not.",
        "use_when": "The turn asks what is remembered or known from continuity.",
        "avoid_when": "No memory claim is involved.",
        "required_inputs": ("memory availability", "scope", "freshness", "trust labels"),
        "compatible_method_families": ("identity_status", "relationship_correction_continuity"),
        "compatible_method_ids": ("memory_report_answer_v1", "continuity_thread_answer_v1"),
        "blocked_if": ("raw private memory requested", "unchecked continuity", "fake memory claims"),
        "output_contract": "Bounded memory summary with uncertainty.",
        "risk_notes": "Should not imply total recall.",
        "source_refs": IDENTITY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "continuity_thread_recap_answer",
        "name": "Continuity thread recap answer",
        "purpose": "Preserve the current thread and prior decisions.",
        "use_when": "The user asks what we were doing or needs a thread recap.",
        "avoid_when": "The turn should be answered directly without recap.",
        "required_inputs": ("continuity state", "recent turns", "timeline anchors"),
        "compatible_method_families": ("relationship_correction_continuity", "identity_status"),
        "compatible_method_ids": ("continuity_thread_answer_v1", "memory_report_answer_v1"),
        "blocked_if": ("thread unavailable", "new topic without continuity need"),
        "output_contract": "Thread-aware recap or continuation cue.",
        "risk_notes": "Can become overly chatty if not bounded.",
        "source_refs": RELATIONSHIP_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "relationship_feedback_answer",
        "name": "Relationship feedback answer",
        "purpose": "Acknowledge user signals, trust state, and feedback without fake empathy.",
        "use_when": "The user is correcting tone, expressing preference, or giving feedback.",
        "avoid_when": "The turn is purely factual or procedural.",
        "required_inputs": ("relationship context", "trust state", "emotional pressure"),
        "compatible_method_families": ("relationship_correction_continuity",),
        "compatible_method_ids": ("relationship_feedback_answer_v1",),
        "blocked_if": ("fake empathy", "relationship roleplay", "tone reset without context"),
        "output_contract": "Bounded acknowledgment plus next step.",
        "risk_notes": "Should not mimic emotional intimacy.",
        "source_refs": RELATIONSHIP_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "correction_repair_answer",
        "name": "Correction repair answer",
        "purpose": "Repair the answer after a user correction by changing shape, not just wording.",
        "use_when": "A prior answer was corrected or found wrong.",
        "avoid_when": "No correction has occurred.",
        "required_inputs": ("correction history", "continuity state", "answer-shape gap"),
        "compatible_method_families": ("relationship_correction_continuity", "response_shape_quality"),
        "compatible_method_ids": ("correction_repair_answer_v1", "directness_concern_integrated_self_check_v1"),
        "blocked_if": ("no correction history", "no shape change needed"),
        "output_contract": "Revised answer plan that changes shape.",
        "risk_notes": "Can drift into apology theater if not grounded.",
        "source_refs": RELATIONSHIP_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "conflict_contradiction_answer",
        "name": "Conflict / contradiction answer",
        "purpose": "Preserve contradictions instead of erasing them.",
        "use_when": "Evidence, goals, or constraints conflict.",
        "avoid_when": "There is no contradiction to preserve.",
        "required_inputs": ("conflict records", "evidence conflicts", "missing assumptions"),
        "compatible_method_families": ("relationship_correction_continuity", "boundary_uncertainty"),
        "compatible_method_ids": ("conflict_contradiction_handling_answer_v1", "partial_answer_supported_portion_answer_v1"),
        "blocked_if": ("no contradiction", "final prose required"),
        "output_contract": "Conflict-aware explanation or clarification.",
        "risk_notes": "Should not smooth over real tension.",
        "source_refs": RELATIONSHIP_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "non_canned_specific_answer",
        "name": "Non-canned specific answer",
        "purpose": "Choose a response shape that stays specific and avoids template feel.",
        "use_when": "The answer risks becoming boilerplate or generic.",
        "avoid_when": "A canned structure is acceptable and safer.",
        "required_inputs": ("repetition markers", "specificity markers", "user concern"),
        "compatible_method_families": ("response_shape_quality",),
        "compatible_method_ids": ("non_cannedness_pressure_v1",),
        "blocked_if": ("generic fallback only", "template locked"),
        "output_contract": "Specific structure and non-cannedness pressure metadata.",
        "risk_notes": "Not a style guide; a quality guard.",
        "source_refs": QUALITY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
    {
        "shape_id": "directness_concern_integrated_answer",
        "name": "Directness / concern integrated answer",
        "purpose": "Tune directness, concern handling, and self-check before final response choice.",
        "use_when": "The turn needs a careful balance of directness and concern handling.",
        "avoid_when": "A simpler direct or refusal shape is enough.",
        "required_inputs": ("concern slot", "frustration signal", "directness pressure", "boundary calibration"),
        "compatible_method_families": ("response_shape_quality", "relationship_correction_continuity", "boundary_uncertainty"),
        "compatible_method_ids": ("directness_concern_integrated_self_check_v1", "relationship_feedback_answer_v1", "bounded_uncertainty_answer_v1"),
        "blocked_if": ("no directness tension", "fake empathy", "runtime authority"),
        "output_contract": "Revised answer plan or rejection metadata.",
        "risk_notes": "Should stay grounded and not become performative empathy.",
        "source_refs": QUALITY_SOURCE_REFS_V1,
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "generates_final_text": False,
        "safe_for_shape_selection": True,
    },
)

_REQUIRED_SHAPE_IDS_V1 = ALLOWED_SHAPE_IDS_V1
_FALLBACK_SHAPE_ID_V1 = "clarifying_question"

_ALLOWED_PACKET_KEYS_V1 = {
    "catalog_type",
    "shapes",
    "fallback_shape_id",
}

_ALLOWED_SHAPE_KEYS_V1 = {
    "shape_id",
    "name",
    "purpose",
    "use_when",
    "avoid_when",
    "required_inputs",
    "compatible_method_families",
    "compatible_method_ids",
    "blocked_if",
    "output_contract",
    "risk_notes",
    "source_refs",
    "runtime_authority",
    "model_required",
    "writes_state",
    "generates_final_text",
    "safe_for_shape_selection",
    "implementation_status",
}

_LABEL_HINTS_V1 = {
    "direct_bounded_answer": {"direct", "answer", "simple", "bounded", "clear", "status", "identity", "memory"},
    "clarifying_question": {"clarify", "clarification", "unclear", "ambiguous", "question", "missing", "need more"},
    "bounded_uncertainty_answer": {"uncertain", "uncertainty", "maybe", "unsure", "not sure", "low confidence"},
    "refusal_boundary_answer": {"refuse", "refusal", "boundary", "unsafe", "unauthorized", "not allowed", "privacy"},
    "evidence_needed_answer": {"evidence", "source", "prove", "current", "latest", "need evidence"},
    "partial_supported_answer": {"partial", "supported", "portion", "split", "some parts"},
    "stepwise_plan_answer": {"plan", "steps", "workflow", "task", "checklist", "ordinary"},
    "implementation_plan_answer": {"implementation", "lane", "build", "code", "what should we code"},
    "workflow_next_lane_answer": {"next lane", "sequence", "roadmap", "what next", "lane"},
    "governance_escalation_answer": {"approval", "escalate", "operator review", "decision needed", "blocked"},
    "teaching_explanation_answer": {"teach", "teaching", "explain", "explanation", "onboarding", "education"},
    "language_discovery_explanation_answer": {"language", "grammar", "vocabulary", "discover language", "words"},
    "scientific_discovery_guidance_answer": {"scientific", "research", "discovery", "experiment", "capability guidance"},
    "benchmark_evaluation_summary_answer": {"benchmark", "evaluation", "turing", "readiness", "assessment"},
    "unknown_friction_branch_answer": {"unknown", "branch", "friction", "hypothesis", "failure pattern"},
    "memory_honesty_answer": {"memory", "remember", "recall", "continuity", "do you remember"},
    "continuity_thread_recap_answer": {"continuity", "thread", "follow-up", "what were we doing", "previous point"},
    "relationship_feedback_answer": {"feedback", "preference", "frustration", "trust", "tone"},
    "correction_repair_answer": {"correction", "wrong", "revise", "fix", "actually"},
    "conflict_contradiction_answer": {"conflict", "contradiction", "clash", "inconsistent", "both true"},
    "non_canned_specific_answer": {"canned", "template", "boilerplate", "generic", "repeated"},
    "directness_concern_integrated_answer": {"directness", "concern", "self-check", "empathy", "friction", "loaded"},
}

_FALLBACK_SHAPE_SELECTION_ORDER_V1 = (
    "clarifying_question",
    "bounded_uncertainty_answer",
    "direct_bounded_answer",
)


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


def _shape_spec_to_dataclass(shape_data: Mapping[str, Any]) -> AnswerShapeSpec:
    return AnswerShapeSpec(
        shape_id=_safe_str(shape_data.get("shape_id")),
        name=_safe_str(shape_data.get("name")),
        purpose=_safe_str(shape_data.get("purpose")),
        use_when=_safe_str(shape_data.get("use_when")),
        avoid_when=_safe_str(shape_data.get("avoid_when")),
        required_inputs=tuple(_safe_text_list(shape_data.get("required_inputs"))),
        compatible_method_families=tuple(_safe_text_list(shape_data.get("compatible_method_families"))),
        compatible_method_ids=tuple(_safe_text_list(shape_data.get("compatible_method_ids"))),
        blocked_if=tuple(_safe_text_list(shape_data.get("blocked_if"))),
        output_contract=_safe_str(shape_data.get("output_contract")),
        risk_notes=_safe_str(shape_data.get("risk_notes")),
        source_refs=tuple(_safe_text_list(shape_data.get("source_refs"))),
        runtime_authority=_safe_bool(shape_data.get("runtime_authority")),
        model_required=_safe_bool(shape_data.get("model_required")),
        writes_state=_safe_bool(shape_data.get("writes_state")),
        generates_final_text=_safe_bool(shape_data.get("generates_final_text")),
        safe_for_shape_selection=_safe_bool(shape_data.get("safe_for_shape_selection")),
        implementation_status=_safe_str(shape_data.get("implementation_status") or "catalog_registered"),
    )


def _build_shapes() -> tuple[AnswerShapeSpec, ...]:
    return tuple(_shape_spec_to_dataclass(shape_data) for shape_data in _SHAPE_SPECS_V1)


def build_answer_shape_catalog_v1() -> AnswerShapeCatalogPacket:
    return AnswerShapeCatalogPacket(
        catalog_type=CATALOG_TYPE_V1,
        shapes=_build_shapes(),
        fallback_shape_id=_FALLBACK_SHAPE_ID_V1,
    )


def _catalog_to_mapping(catalog: Any) -> Mapping[str, Any]:
    if is_dataclass(catalog):
        return _as_mapping(asdict(catalog))
    if isinstance(catalog, Mapping):
        return catalog
    return {}


def validate_answer_shape_catalog_v1(catalog: Mapping[str, Any] | AnswerShapeCatalogPacket | None = None) -> dict[str, Any]:
    packet = _catalog_to_mapping(catalog or build_answer_shape_catalog_v1())
    normalized = to_answer_shape_catalog_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        normalized = {}

    blocked_labels: list[str] = []
    shapes_value = _safe_list(normalized.get("shapes"))
    fallback_shape_id = _safe_str(normalized.get("fallback_shape_id"))

    if set(normalized.keys()) - _ALLOWED_PACKET_KEYS_V1:
        blocked_labels.append("unexpected_packet_field")
    if _safe_str(normalized.get("catalog_type")) != CATALOG_TYPE_V1:
        blocked_labels.append("invalid_catalog_type")
    if not shapes_value:
        blocked_labels.append("missing_shapes")
    if not fallback_shape_id:
        blocked_labels.append("missing_fallback_shape_id")

    shape_ids_seen: set[str] = set()
    shape_ids_in_order: list[str] = []
    family_usage: dict[str, int] = {family_id: 0 for family_id in ALLOWED_METHOD_FAMILIES_V1}

    for shape_value in shapes_value:
        shape = _as_mapping(shape_value)
        if set(shape.keys()) - _ALLOWED_SHAPE_KEYS_V1:
            blocked_labels.append("unexpected_shape_field")
        shape_id = _safe_str(shape.get("shape_id"))
        name = _safe_str(shape.get("name"))
        purpose = _safe_str(shape.get("purpose"))
        use_when = _safe_str(shape.get("use_when"))
        avoid_when = _safe_str(shape.get("avoid_when"))
        required_inputs = _safe_text_list(shape.get("required_inputs"))
        compatible_method_families = _safe_text_list(shape.get("compatible_method_families"))
        compatible_method_ids = _safe_text_list(shape.get("compatible_method_ids"))
        blocked_if = _safe_text_list(shape.get("blocked_if"))
        output_contract = _safe_str(shape.get("output_contract"))
        risk_notes = _safe_str(shape.get("risk_notes"))
        source_refs = _safe_text_list(shape.get("source_refs"))
        runtime_authority = _safe_bool(shape.get("runtime_authority"))
        model_required = _safe_bool(shape.get("model_required"))
        writes_state = _safe_bool(shape.get("writes_state"))
        generates_final_text = _safe_bool(shape.get("generates_final_text"))
        safe_for_shape_selection = _safe_bool(shape.get("safe_for_shape_selection"))
        implementation_status = _safe_str(shape.get("implementation_status"))

        if not shape_id:
            blocked_labels.append("missing_shape_id")
        if shape_id in shape_ids_seen:
            blocked_labels.append("duplicate_shape_id")
        shape_ids_seen.add(shape_id)
        shape_ids_in_order.append(shape_id)
        if shape_id and shape_id not in _REQUIRED_SHAPE_IDS_V1:
            blocked_labels.append("unknown_shape_id")
        if not name:
            blocked_labels.append("missing_shape_name")
        if not purpose:
            blocked_labels.append("missing_shape_purpose")
        if not use_when:
            blocked_labels.append("missing_shape_use_when")
        if not avoid_when:
            blocked_labels.append("missing_shape_avoid_when")
        if not required_inputs:
            blocked_labels.append("missing_shape_required_inputs")
        if not compatible_method_families:
            blocked_labels.append("missing_compatible_method_families")
        if not compatible_method_ids:
            blocked_labels.append("missing_compatible_method_ids")
        if not blocked_if:
            blocked_labels.append("missing_shape_blocked_if")
        if not output_contract:
            blocked_labels.append("missing_shape_output_contract")
        if not risk_notes:
            blocked_labels.append("missing_shape_risk_notes")
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
        if not safe_for_shape_selection:
            blocked_labels.append("unsafe_for_shape_selection")
        unknown_families = [family_id for family_id in compatible_method_families if family_id not in ALLOWED_METHOD_FAMILIES_V1]
        if unknown_families:
            blocked_labels.append("unknown_compatible_method_family")
        for family_id in compatible_method_families:
            if family_id in family_usage:
                family_usage[family_id] += 1

    if _REQUIRED_SHAPE_IDS_V1 - shape_ids_seen:
        blocked_labels.append("missing_required_shape")
    if fallback_shape_id and fallback_shape_id not in shape_ids_seen:
        blocked_labels.append("fallback_shape_not_registered")

    valid = not blocked_labels
    return {
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": sorted(set(blocked_labels)),
        "catalog_type": _safe_str(normalized.get("catalog_type")),
        "shape_count": len(shapes_value),
        "fallback_shape_id": fallback_shape_id,
        "compatibility_summary": {
            "families_covered": sorted(family for family, count in family_usage.items() if count > 0),
            "family_usage": dict(sorted(family_usage.items())),
            "selectable_shape_count": sum(1 for shape_value in shapes_value if _safe_bool(_as_mapping(shape_value).get("safe_for_shape_selection"))),
        },
    }


def summarize_answer_shape_catalog_v1(catalog: Mapping[str, Any] | AnswerShapeCatalogPacket | None = None) -> dict[str, Any]:
    packet = _catalog_to_mapping(catalog or build_answer_shape_catalog_v1())
    normalized = to_answer_shape_catalog_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        normalized = {}

    shapes = _safe_list(normalized.get("shapes"))
    family_usage: dict[str, int] = {}
    compatible_method_count = 0
    selectable_shape_count = 0
    for shape_value in shapes:
        shape = _as_mapping(shape_value)
        for family_id in _safe_text_list(shape.get("compatible_method_families")):
            family_usage[family_id] = family_usage.get(family_id, 0) + 1
        compatible_method_count += len(_safe_text_list(shape.get("compatible_method_ids")))
        if _safe_bool(shape.get("safe_for_shape_selection")):
            selectable_shape_count += 1

    return {
        "summary_type": SUMMARY_TYPE_V1,
        "catalog_type": _safe_str(normalized.get("catalog_type")),
        "shape_count": len(shapes),
        "selectable_shape_count": selectable_shape_count,
        "fallback_shape_id": _safe_str(normalized.get("fallback_shape_id")),
        "compatibility_summary": {
            "family_usage": dict(sorted(family_usage.items())),
            "compatible_method_id_count": compatible_method_count,
            "shape_ids": sorted(_safe_str(_as_mapping(item).get("shape_id")) for item in shapes),
        },
    }


def to_answer_shape_catalog_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def _shape_tokens(shape: Mapping[str, Any]) -> set[str]:
    tokens = set()
    for key in ("shape_id", "name", "purpose", "use_when", "avoid_when", "output_contract", "risk_notes"):
        tokens |= _tokenize(shape.get(key))
    for entry in _safe_text_list(shape.get("blocked_if")):
        tokens |= _tokenize(entry)
    return tokens


def _shape_label_hint_score(shape_id: str, turn_text: str, turn_tokens: set[str]) -> int:
    score = 0
    for hint in _LABEL_HINTS_V1.get(shape_id, set()):
        normalized_hint = hint.lower().strip()
        if not normalized_hint:
            continue
        if " " in normalized_hint:
            if normalized_hint in turn_text:
                score += 5
        elif normalized_hint in turn_tokens:
            score += 3
    return score


def _method_candidate_list(method_candidates: Any) -> list[dict[str, Any]]:
    if method_candidates is None:
        return []
    if isinstance(method_candidates, Mapping) and "selected_methods" in method_candidates:
        raw = method_candidates.get("selected_methods")
    elif isinstance(method_candidates, Mapping) and "methods" in method_candidates:
        raw = method_candidates.get("methods")
    else:
        raw = method_candidates
    candidates: list[dict[str, Any]] = []
    for item in _safe_list(raw):
        if isinstance(item, Mapping):
            candidates.append(dict(item))
    return candidates


def _shape_is_compatible_with_method(shape: Mapping[str, Any], method: Mapping[str, Any]) -> bool:
    family_id = _safe_str(method.get("family_id"))
    method_id = _safe_str(method.get("method_id"))
    families = set(_safe_text_list(shape.get("compatible_method_families")))
    method_ids = set(_safe_text_list(shape.get("compatible_method_ids")))
    if family_id and family_id in families:
        return True
    if method_id and method_id in method_ids:
        return True
    return False


def _score_shape(turn_text: str, turn_tokens: set[str], shape: Mapping[str, Any], method_candidates: list[dict[str, Any]]) -> tuple[int, int]:
    shape_id = _safe_str(shape.get("shape_id"))
    explicit_score = _shape_label_hint_score(shape_id, turn_text, turn_tokens)
    fuzzy_score = len(turn_tokens & _shape_tokens(shape))
    label_score = (explicit_score * 100) + fuzzy_score
    compatibility_score = 0
    if method_candidates:
        for candidate in method_candidates:
            if _shape_is_compatible_with_method(shape, candidate):
                compatibility_score += 1
    else:
        compatibility_score = 1
    return label_score, compatibility_score


def select_answer_shapes_v1(
    turn_labels: Iterable[Any],
    method_candidates: Any = None,
    catalog: Mapping[str, Any] | AnswerShapeCatalogPacket | None = None,
) -> dict[str, Any]:
    packet = _catalog_to_mapping(catalog or build_answer_shape_catalog_v1())
    normalized = to_answer_shape_catalog_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        normalized = {}

    labels = _safe_text_list(turn_labels)
    turn_text = " ".join(labels).lower()
    turn_tokens: set[str] = set()
    for label in labels:
        turn_tokens |= _tokenize(label)

    candidate_methods = _method_candidate_list(method_candidates)
    candidate_summary = {
        "candidate_count": len(candidate_methods),
        "candidate_method_ids": sorted({_safe_str(candidate.get("method_id")) for candidate in candidate_methods if _safe_str(candidate.get("method_id"))}),
        "candidate_family_ids": sorted({_safe_str(candidate.get("family_id")) for candidate in candidate_methods if _safe_str(candidate.get("family_id"))}),
    }

    shapes = _safe_list(normalized.get("shapes"))
    selected: list[dict[str, Any]] = []
    rejected: list[str] = []
    matched_labels: set[str] = set()

    for shape_value in shapes:
        shape = _as_mapping(shape_value)
        shape_id = _safe_str(shape.get("shape_id"))
        if not _safe_bool(shape.get("safe_for_shape_selection")):
            rejected.append(shape_id)
            continue
        label_score, compatibility_score = _score_shape(turn_text, turn_tokens, shape, candidate_methods)
        compatible_with_candidates = compatibility_score > 0
        if candidate_methods and not compatible_with_candidates:
            rejected.append(shape_id)
            continue
        if label_score <= 0 and not candidate_methods:
            continue
        matched = sorted(turn_tokens & _shape_tokens(shape))
        matched_labels.update(matched)
        selected.append(
            {
                "shape_id": shape_id,
                "name": _safe_str(shape.get("name")),
                "purpose": _safe_str(shape.get("purpose")),
                "use_when": _safe_str(shape.get("use_when")),
                "avoid_when": _safe_str(shape.get("avoid_when")),
                "required_inputs": _safe_text_list(shape.get("required_inputs")),
                "compatible_method_families": _safe_text_list(shape.get("compatible_method_families")),
                "compatible_method_ids": _safe_text_list(shape.get("compatible_method_ids")),
                "blocked_if": _safe_text_list(shape.get("blocked_if")),
                "output_contract": _safe_str(shape.get("output_contract")),
                "risk_notes": _safe_str(shape.get("risk_notes")),
                "source_refs": _safe_text_list(shape.get("source_refs")),
                "safe_for_shape_selection": _safe_bool(shape.get("safe_for_shape_selection")),
                "implementation_status": _safe_str(shape.get("implementation_status")),
                "label_score": label_score,
                "compatibility_score": compatibility_score,
                "matched_labels": matched,
            }
        )

    selected.sort(key=lambda item: (-int(item["label_score"]), -int(item["compatibility_score"]), item["shape_id"]))
    unknown_labels = sorted(label for label in labels if not _tokenize(label) & matched_labels)
    fallback_used = False

    if selected:
        selected = [selected[0]]
        selected_ids = [selected[0]["shape_id"]]
    else:
        selected_ids = []
        for fallback_shape_id in _FALLBACK_SHAPE_SELECTION_ORDER_V1:
            fallback = next((shape for shape in shapes if _safe_str(_as_mapping(shape).get("shape_id")) == fallback_shape_id), None)
            if fallback is None:
                continue
            fallback_map = _as_mapping(fallback)
            if candidate_methods and not any(_shape_is_compatible_with_method(fallback_map, candidate) for candidate in candidate_methods):
                continue
            fallback_used = True
            selected = [
                {
                    "shape_id": _safe_str(fallback_map.get("shape_id")),
                    "name": _safe_str(fallback_map.get("name")),
                    "purpose": _safe_str(fallback_map.get("purpose")),
                    "use_when": _safe_str(fallback_map.get("use_when")),
                    "avoid_when": _safe_str(fallback_map.get("avoid_when")),
                    "required_inputs": _safe_text_list(fallback_map.get("required_inputs")),
                    "compatible_method_families": _safe_text_list(fallback_map.get("compatible_method_families")),
                    "compatible_method_ids": _safe_text_list(fallback_map.get("compatible_method_ids")),
                    "blocked_if": _safe_text_list(fallback_map.get("blocked_if")),
                    "output_contract": _safe_str(fallback_map.get("output_contract")),
                    "risk_notes": _safe_str(fallback_map.get("risk_notes")),
                    "source_refs": _safe_text_list(fallback_map.get("source_refs")),
                    "safe_for_shape_selection": _safe_bool(fallback_map.get("safe_for_shape_selection")),
                    "implementation_status": _safe_str(fallback_map.get("implementation_status")),
                    "label_score": 0,
                    "compatibility_score": 1 if not candidate_methods else max(1, sum(1 for candidate in candidate_methods if _shape_is_compatible_with_method(fallback_map, candidate))),
                    "matched_labels": [],
                }
            ]
            selected_ids = [selected[0]["shape_id"]]
            break

    rejected = sorted(set(rejected) | ({shape_id for shape_id in [item["shape_id"] for item in selected[1:]]} if len(selected) > 1 else set()))
    if candidate_methods:
        rejected = sorted(set(rejected) - set(selected_ids))

    selected_family_ids = sorted({
        _safe_str(candidate.get("family_id"))
        for candidate in candidate_methods
        if selected_ids and any(_shape_is_compatible_with_method(_as_mapping(shape), candidate) and _safe_str(_as_mapping(shape).get("shape_id")) in selected_ids for shape in shapes)
    })

    return {
        "selection_type": SHAPE_SELECTION_TYPE_V1,
        "catalog_type": _safe_str(normalized.get("catalog_type")),
        "turn_labels": labels,
        "turn_tokens": sorted(turn_tokens),
        "unknown_labels": unknown_labels,
        "fallback_used": fallback_used,
        "selected_shape_ids": selected_ids,
        "selected_shapes": selected,
        "rejected_shape_ids": rejected,
        "selected_method_candidate_family_ids": selected_family_ids,
        "method_candidate_summary": candidate_summary,
        "catalog_summary": summarize_answer_shape_catalog_v1(normalized),
    }


__all__ = [
    "AnswerShapeCompatibility",
    "AnswerShapeCatalogPacket",
    "AnswerShapeSelection",
    "AnswerShapeSpec",
    "build_answer_shape_catalog_v1",
    "validate_answer_shape_catalog_v1",
    "summarize_answer_shape_catalog_v1",
    "to_answer_shape_catalog_json_safe_v1",
    "select_answer_shapes_v1",
]
