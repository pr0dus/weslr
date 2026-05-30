"""Metadata-only answer method catalog v1.

This module is intentionally pure, deterministic, and fail-closed.
It turns extracted WESLR answer-family/method design notes into structured
catalog records, validation results, summaries, and safe method-selection
metadata.

It does not perform file I/O, network I/O, subprocess execution, runtime/chat
wiring, live response routing, provider/model/search/advisor calls, dot-weslr
IO, or answer rendering.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping

HELPER_TYPE_V1 = "weslr_answer_method_catalog_v1"
CATALOG_TYPE_V1 = "answer_method_catalog_v1"
FAMILY_SPEC_TYPE_V1 = "answer_method_family_spec_v1"
METHOD_SPEC_TYPE_V1 = "answer_method_spec_v1"
CATALOG_PACKET_TYPE_V1 = "answer_method_catalog_packet_v1"
SUMMARY_TYPE_V1 = "answer_method_catalog_summary_v1"
SELECTION_RESULT_TYPE_V1 = "answer_method_selection_result_v1"

ALLOWED_FAMILY_IDS_V1 = {
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

ALLOWED_METHOD_TYPES_V1 = {
    "evidence_based",
    "governed",
    "deterministic",
    "workflow_guided",
    "matrix_ranked",
    "explanation_guided",
    "evaluation_guided",
    "metadata_only",
    "continuity_guided",
    "adaptive_delivery",
    "quality_control",
}

CATALOG_SOURCE_REFS_V1 = (
    "docs/WESLR_ANSWER_MATRIX_AND_METHOD_CATALOG_IMPLEMENTATION_EXTRACTION_V1.md",
    "docs/WESLR_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_V1.md",
    "docs/WESLR_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1.md",
    "docs/WESLR_UNIFIED_RESPONSE_FORMATION_CANON_V1.md",
)

IDENTITY_STATUS_SOURCE_REFS_V1 = CATALOG_SOURCE_REFS_V1 + (
    "weslr/meaning_response.py",
    "docs/WESLR_STABLE_IDENTITY_AND_ADAPTIVE_DELIVERY_DOCTRINE_V1.md",
)

BOUNDARY_SOURCE_REFS_V1 = CATALOG_SOURCE_REFS_V1 + (
    "weslr/native_reasoning_frame.py",
    "weslr/native_response_self_check.py",
    "weslr/native_response_assembly.py",
)

TASK_SOURCE_REFS_V1 = CATALOG_SOURCE_REFS_V1 + (
    "weslr/ordinary_reasoning_guidance.py",
    "weslr/targeted_response_formation_improvement.py",
)

TEACHING_SOURCE_REFS_V1 = CATALOG_SOURCE_REFS_V1 + (
    "weslr/meaning_response.py",
    "grammar.md",
    "vocabulary.md",
    "docs/WESLR_TEACHING_EXPLANATION_DESIGN_V1.md",
)

RELATIONSHIP_SOURCE_REFS_V1 = CATALOG_SOURCE_REFS_V1 + (
    "weslr/meaning_response.py",
    "weslr/targeted_response_formation_improvement.py",
    "weslr/meaning_state_context.py",
)

QUALITY_SOURCE_REFS_V1 = CATALOG_SOURCE_REFS_V1 + (
    "weslr/targeted_response_formation_improvement.py",
    "weslr/reasoning_trace.py",
    "weslr/reasoning_arbitrator.py",
)


@dataclass(frozen=True, slots=True)
class AnswerMethodFamilySpec:
    family_id: str
    name: str
    purpose: str
    source_refs: tuple[str, ...]
    target_files: tuple[str, ...]
    implementation_status: str
    method_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AnswerMethodSpec:
    method_id: str
    family_id: str
    name: str
    purpose: str
    triggers: tuple[str, ...]
    required_inputs: tuple[str, ...]
    output_shape: str
    method_type: str
    implementation_status: str
    source_refs: tuple[str, ...]
    target_files: tuple[str, ...]
    diff_vs_generic_llm: str
    runtime_authority: bool
    model_required: bool
    writes_state: bool
    safe_for_catalog_selection: bool


@dataclass(frozen=True, slots=True)
class AnswerMethodCatalogPacket:
    catalog_type: str
    families: tuple[AnswerMethodFamilySpec, ...]
    methods: tuple[AnswerMethodSpec, ...]
    fallback_method_id: str


_FAMILY_SPECS_V1: tuple[dict[str, Any], ...] = (
    {
        "family_id": "identity_status",
        "name": "Identity / status",
        "purpose": "Bounded self-description, memory scope, capability orientation, and new-contact orientation.",
        "source_refs": IDENTITY_STATUS_SOURCE_REFS_V1,
        "target_files": ("weslr/meaning_response.py",),
        "implementation_status": "catalog_registered",
    },
    {
        "family_id": "boundary_uncertainty",
        "name": "Boundary / uncertainty",
        "purpose": "Clarification, uncertainty, refusal, evidence need, partial support, and direct bounded answers.",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "target_files": (
            "weslr/native_reasoning_frame.py",
            "weslr/native_response_self_check.py",
        ),
        "implementation_status": "catalog_registered",
    },
    {
        "family_id": "task_workflow",
        "name": "Task / workflow",
        "purpose": "Planning, implementation sequencing, artifact/workspace planning, next-lane selection, and governance escalation.",
        "source_refs": TASK_SOURCE_REFS_V1,
        "target_files": (
            "weslr/ordinary_reasoning_guidance.py",
            "weslr/targeted_response_formation_improvement.py",
        ),
        "implementation_status": "catalog_registered",
    },
    {
        "family_id": "teaching_explanation_discovery",
        "name": "Teaching / explanation / discovery",
        "purpose": "Teaching, language discovery, research guidance, and evaluation/benchmark explanation.",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "target_files": (
            "weslr/meaning_response.py",
            "grammar.md",
            "vocabulary.md",
        ),
        "implementation_status": "catalog_registered",
    },
    {
        "family_id": "relationship_correction_continuity",
        "name": "Relationship / correction / continuity",
        "purpose": "Correction repair, thread continuity, relationship feedback, and contradiction handling.",
        "source_refs": RELATIONSHIP_SOURCE_REFS_V1,
        "target_files": (
            "weslr/meaning_response.py",
            "weslr/targeted_response_formation_improvement.py",
            "weslr/meaning_state_context.py",
        ),
        "implementation_status": "catalog_registered",
    },
    {
        "family_id": "response_shape_quality",
        "name": "Response shape / quality",
        "purpose": "Answer-shape planning, non-cannedness pressure, and directness/concern/self-check tuning.",
        "source_refs": QUALITY_SOURCE_REFS_V1,
        "target_files": ("weslr/targeted_response_formation_improvement.py",),
        "implementation_status": "catalog_registered",
    },
)

_METHOD_SPECS_V1: tuple[dict[str, Any], ...] = (
    {
        "method_id": "verified_identity_status_answer_v1",
        "family_id": "identity_status",
        "name": "Verified identity / status answer",
        "purpose": "Answer identity and status questions with bounded self-description.",
        "triggers": (
            "identity",
            "status",
            "who are you",
            "what are you",
            "about you",
            "self description",
        ),
        "required_inputs": (
            "verified identity state",
            "relationship state",
            "scope boundary",
            "capability boundary",
        ),
        "output_shape": "short identity/status paragraph with bounded claims",
        "method_type": "evidence_based",
        "implementation_status": "catalog_registered",
        "source_refs": IDENTITY_STATUS_SOURCE_REFS_V1,
        "target_files": ("weslr/meaning_response.py",),
        "diff_vs_generic_llm": "Uses verified identity scope and avoids unsupported persona claims.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "memory_report_answer_v1",
        "family_id": "identity_status",
        "name": "Memory report answer",
        "purpose": "Say what memory is available, what is not, and how much confidence should be placed in it.",
        "triggers": (
            "memory",
            "remember",
            "recall",
            "do you remember",
            "continuity",
        ),
        "required_inputs": (
            "memory availability",
            "scope",
            "freshness",
            "trust labels",
        ),
        "output_shape": "bounded memory summary with uncertainty",
        "method_type": "continuity_guided",
        "implementation_status": "catalog_registered",
        "source_refs": IDENTITY_STATUS_SOURCE_REFS_V1,
        "target_files": (
            "weslr/meaning_response.py",
            "weslr/entity_timeline_memory.py",
            "weslr/user_timeline_memory.py",
        ),
        "diff_vs_generic_llm": "Separates known, unavailable, and unverified memory.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "capability_orientation_answer_v1",
        "family_id": "identity_status",
        "name": "Capability orientation answer",
        "purpose": "Explain what WESLR can do now and what the next safe step is.",
        "triggers": (
            "capability",
            "can you",
            "what can you do",
            "help with",
            "what are you able",
        ),
        "required_inputs": (
            "capability boundary",
            "domain context",
            "current mode",
        ),
        "output_shape": "capability guidance plus next safe step",
        "method_type": "governed",
        "implementation_status": "catalog_registered",
        "source_refs": IDENTITY_STATUS_SOURCE_REFS_V1,
        "target_files": ("weslr/meaning_response.py", "weslr/capability_registry.py"),
        "diff_vs_generic_llm": "Gives capability guidance without false authority or unsupported claims.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "new_contact_orientation_answer_v1",
        "family_id": "identity_status",
        "name": "New contact / orientation answer",
        "purpose": "Open a new interaction with a short bounded welcome and working orientation.",
        "triggers": (
            "hello",
            "hi",
            "first contact",
            "onboarding",
            "new contact",
            "orientation",
        ),
        "required_inputs": (
            "verified identity",
            "role",
            "context",
        ),
        "output_shape": "short welcome/orientation",
        "method_type": "deterministic",
        "implementation_status": "catalog_registered",
        "source_refs": IDENTITY_STATUS_SOURCE_REFS_V1,
        "target_files": ("weslr/meaning_response.py",),
        "diff_vs_generic_llm": "Keeps initial contact bounded and non-canned.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "clarifying_question_answer_v1",
        "family_id": "boundary_uncertainty",
        "name": "Clarifying question answer",
        "purpose": "Ask the smallest useful question when context is insufficient or ambiguous.",
        "triggers": (
            "clarify",
            "clarifying",
            "ambiguous",
            "missing context",
            "need more info",
            "unclear",
        ),
        "required_inputs": (
            "missing context slots",
            "uncertainty labels",
            "response obligation",
        ),
        "output_shape": "one focused question",
        "method_type": "governed",
        "implementation_status": "catalog_registered",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "target_files": ("weslr/native_reasoning_frame.py", "weslr/answer_formation.py"),
        "diff_vs_generic_llm": "Asks only the question needed to remove the uncertainty.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "bounded_uncertainty_answer_v1",
        "family_id": "boundary_uncertainty",
        "name": "Bounded uncertainty answer",
        "purpose": "Preserve uncertainty instead of inventing confidence.",
        "triggers": (
            "uncertain",
            "uncertainty",
            "unsure",
            "maybe",
            "not sure",
            "low confidence",
        ),
        "required_inputs": (
            "uncertainty labels",
            "confidence",
            "evidence sufficiency",
        ),
        "output_shape": "answer with explicit uncertainty boundary",
        "method_type": "evidence_based",
        "implementation_status": "catalog_registered",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "target_files": ("weslr/native_reasoning_frame.py", "weslr/request_intelligence/uncertainty.py"),
        "diff_vs_generic_llm": "Keeps confidence calibrated instead of sounding certain by default.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "refusal_boundary_answer_v1",
        "family_id": "boundary_uncertainty",
        "name": "Refusal / boundary answer",
        "purpose": "Refuse unsafe, unsupported, or unauthorized requests while offering a bounded alternative.",
        "triggers": (
            "refuse",
            "refusal",
            "privacy",
            "safety",
            "boundary",
            "not allowed",
            "unauthorized",
        ),
        "required_inputs": (
            "denied authority flags",
            "blocked labels",
            "safety boundary",
        ),
        "output_shape": "refusal plus bounded alternative",
        "method_type": "governed",
        "implementation_status": "catalog_registered",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "target_files": ("weslr/native_response_self_check.py", "weslr/answer_authority_boundary.py", "weslr/answer_formation.py"),
        "diff_vs_generic_llm": "Refuses with a useful boundary note instead of a bare no.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "evidence_needed_answer_v1",
        "family_id": "boundary_uncertainty",
        "name": "Evidence-needed answer",
        "purpose": "State that stronger claims need evidence and point to the next safe evidence step.",
        "triggers": (
            "evidence",
            "source",
            "current",
            "latest",
            "prove",
            "need evidence",
        ),
        "required_inputs": (
            "evidence need",
            "source scope",
            "claim burden",
        ),
        "output_shape": "request for evidence or evidence next step",
        "method_type": "evidence_based",
        "implementation_status": "catalog_registered",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "target_files": ("weslr/native_reasoning_frame.py", "weslr/evidence_needed_detector.py", "weslr/evidence_answer_builder.py"),
        "diff_vs_generic_llm": "Does not fake current facts when evidence is missing.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "partial_answer_supported_portion_answer_v1",
        "family_id": "boundary_uncertainty",
        "name": "Partial answer / supported portion answer",
        "purpose": "Answer the supported part and label the unsupported remainder.",
        "triggers": (
            "partial",
            "supported portion",
            "what can you answer",
            "split answer",
        ),
        "required_inputs": (
            "supported facts",
            "unsupported remainder",
            "evidence gaps",
        ),
        "output_shape": "split answer with explicit gaps",
        "method_type": "evidence_based",
        "implementation_status": "catalog_registered",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "target_files": ("weslr/native_response_assembly.py",),
        "diff_vs_generic_llm": "Preserves the answerable portion instead of overrefusing the whole turn.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "direct_bounded_answer_v1",
        "family_id": "boundary_uncertainty",
        "name": "Direct bounded answer",
        "purpose": "Answer directly when the intent is clear and the grounding is sufficient.",
        "triggers": (
            "direct",
            "answer now",
            "just answer",
            "bounded direct",
            "clear intent",
        ),
        "required_inputs": (
            "clear intent",
            "sufficient grounding",
            "boundary calibration",
        ),
        "output_shape": "direct answer with boundaries",
        "method_type": "deterministic",
        "implementation_status": "catalog_registered",
        "source_refs": BOUNDARY_SOURCE_REFS_V1,
        "target_files": ("weslr/native_response_draft.py", "weslr/native_response_assembly.py"),
        "diff_vs_generic_llm": "Keeps directness while preserving explicit limits.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "ordinary_task_planning_answer_v1",
        "family_id": "task_workflow",
        "name": "Ordinary task planning answer",
        "purpose": "Provide safe step planning for ordinary tasks.",
        "triggers": (
            "task",
            "plan",
            "steps",
            "workflow",
            "checklist",
            "ordinary task",
        ),
        "required_inputs": (
            "task markers",
            "constraints",
            "missing context",
            "tool need",
        ),
        "output_shape": "numbered steps or bounded next actions",
        "method_type": "workflow_guided",
        "implementation_status": "catalog_registered",
        "source_refs": TASK_SOURCE_REFS_V1,
        "target_files": ("weslr/ordinary_reasoning_guidance.py", "docs/ORDINARY_TASK_CONTEXT.md"),
        "diff_vs_generic_llm": "Turns work into explicit safe next steps instead of generic advice.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "implementation_planning_answer_v1",
        "family_id": "task_workflow",
        "name": "Implementation planning answer",
        "purpose": "Turn a design gap into a constrained implementation plan.",
        "triggers": (
            "what should we code first",
            "implementation plan",
            "next lane",
            "what next",
            "build first",
        ),
        "required_inputs": (
            "target gaps",
            "answer-shape policy",
            "authority calibration",
        ),
        "output_shape": "implementation plan with first safe step",
        "method_type": "matrix_ranked",
        "implementation_status": "catalog_registered",
        "source_refs": TASK_SOURCE_REFS_V1,
        "target_files": ("weslr/targeted_response_formation_improvement.py", "docs/WESLR_TARGETED_RESPONSE_FORMATION_IMPROVEMENT_HELPERS_V1.md"),
        "diff_vs_generic_llm": "Proposes the next safe build step without claiming runtime authority.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "artifact_workspace_planning_answer_v1",
        "family_id": "task_workflow",
        "name": "Artifact / workspace planning answer",
        "purpose": "Plan docs, tests, files, and workspace steps in a bounded way.",
        "triggers": (
            "files",
            "workspace",
            "docs",
            "tests",
            "repo",
            "artifact",
        ),
        "required_inputs": (
            "file targets",
            "constraints",
            "safety",
        ),
        "output_shape": "staged file/work plan",
        "method_type": "workflow_guided",
        "implementation_status": "catalog_registered",
        "source_refs": TASK_SOURCE_REFS_V1,
        "target_files": ("weslr/ordinary_reasoning_guidance.py",),
        "diff_vs_generic_llm": "Keeps implementation work staged and explicit.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "workflow_next_lane_answer_v1",
        "family_id": "task_workflow",
        "name": "Workflow / next-lane answer",
        "purpose": "Say what lane should happen next, based on readiness and blockers.",
        "triggers": (
            "lane",
            "next lane",
            "sequence",
            "what should happen next",
            "roadmap",
        ),
        "required_inputs": (
            "gap labels",
            "readiness",
            "blocked flags",
        ),
        "output_shape": "next-lane recommendation",
        "method_type": "matrix_ranked",
        "implementation_status": "catalog_registered",
        "source_refs": TASK_SOURCE_REFS_V1,
        "target_files": ("weslr/targeted_response_formation_improvement.py",),
        "diff_vs_generic_llm": "Recommends a sequence step instead of blindly roadmapping.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "governance_escalation_proposal_v1",
        "family_id": "task_workflow",
        "name": "Governance escalation proposal",
        "purpose": "Propose operator review when authority is missing or blocked.",
        "triggers": (
            "approval",
            "operator review",
            "escalate",
            "decision needed",
            "blocked",
        ),
        "required_inputs": (
            "approval requirement",
            "denied authority fields",
        ),
        "output_shape": "proposal or escalation note",
        "method_type": "governed",
        "implementation_status": "catalog_registered",
        "source_refs": TASK_SOURCE_REFS_V1,
        "target_files": ("weslr/native_reasoning_frame.py", "weslr/answer_authority_boundary.py"),
        "diff_vs_generic_llm": "Asks for review instead of pretending authorization.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "teaching_explanation_answer_v1",
        "family_id": "teaching_explanation_discovery",
        "name": "Teaching / explanation answer",
        "purpose": "Explain concepts in a teachable, human-readable form.",
        "triggers": (
            "explain",
            "teach",
            "how does",
            "what does",
            "onboarding",
            "education",
        ),
        "required_inputs": (
            "audience level",
            "vocabulary",
            "domain context",
            "evidence needs",
        ),
        "output_shape": "staged explanation or human-readable explanation",
        "method_type": "explanation_guided",
        "implementation_status": "catalog_registered",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "target_files": ("weslr/meaning_response.py", "docs/WESLR_TEACHING_EXPLANATION_DESIGN_V1.md", "grammar.md", "vocabulary.md"),
        "diff_vs_generic_llm": "Shapes explanation to the person and context instead of template prose.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "language_grammar_vocabulary_discovery_answer_v1",
        "family_id": "teaching_explanation_discovery",
        "name": "Language / grammar / vocabulary discovery answer",
        "purpose": "Translate internal form into human-understandable language and support teaching ideas.",
        "triggers": (
            "language",
            "grammar",
            "vocabulary",
            "words",
            "discover language",
            "teaching ideas",
        ),
        "required_inputs": (
            "internal state signals",
            "preferred vocabulary",
            "target audience",
        ),
        "output_shape": "human-readable translation or teaching-oriented language",
        "method_type": "explanation_guided",
        "implementation_status": "catalog_registered",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "target_files": ("weslr/meaning_response.py", "grammar.md", "vocabulary.md"),
        "diff_vs_generic_llm": "Translates internal form without pretending to know an unknown language.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "scientific_discovery_capability_guidance_answer_v1",
        "family_id": "teaching_explanation_discovery",
        "name": "Scientific discovery / capability guidance answer",
        "purpose": "Guide research and discovery with a staged workflow and boundary notes.",
        "triggers": (
            "scientific",
            "research",
            "discovery",
            "capability guidance",
            "experiment",
        ),
        "required_inputs": (
            "candidate generation constraints",
            "novelty",
            "structural sanity",
            "evidence gates",
        ),
        "output_shape": "stepwise research plan with boundary notes",
        "method_type": "workflow_guided",
        "implementation_status": "catalog_registered",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "target_files": ("weslr/meaning_response.py", "docs/WESLR_BENCHMARK_REASONING_ENGINE_V1.md"),
        "diff_vs_generic_llm": "Guides discovery without claiming discovery itself.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "benchmark_evaluation_answer_v1",
        "family_id": "teaching_explanation_discovery",
        "name": "Benchmark / evaluation answer",
        "purpose": "Explain evaluation status without asserting official benchmark results.",
        "triggers": (
            "benchmark",
            "evaluation",
            "turing",
            "readiness",
            "assessment",
        ),
        "required_inputs": (
            "task schema",
            "trace",
            "conflicts",
            "legibility",
            "anti-gaming",
        ),
        "output_shape": "evaluation summary or readiness label with caveat",
        "method_type": "evaluation_guided",
        "implementation_status": "catalog_registered",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "target_files": ("weslr/reasoning_task.py", "weslr/reasoning_trace.py", "weslr/reasoning_arbitrator.py"),
        "diff_vs_generic_llm": "Explains evaluation without taking official score authority.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "unknown_engine_branch_friction_answer_v1",
        "family_id": "teaching_explanation_discovery",
        "name": "Unknown-engine branch / friction answer",
        "purpose": "Represent uncertainty, branches, friction, and bounded hypotheses.",
        "triggers": (
            "unknown",
            "branch",
            "friction",
            "hypothesis",
            "uncertain future",
            "failure pattern",
        ),
        "required_inputs": (
            "knowns",
            "unknowns",
            "missing evidence",
            "branch assumptions",
        ),
        "output_shape": "metadata-only uncertainty record or graded proposal",
        "method_type": "metadata_only",
        "implementation_status": "catalog_registered",
        "source_refs": TEACHING_SOURCE_REFS_V1,
        "target_files": ("weslr/controlled_unknown_engine_metadata_shadow_runner.py",),
        "diff_vs_generic_llm": "Captures uncertainty as metadata rather than oracle-style prediction.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "correction_repair_answer_v1",
        "family_id": "relationship_correction_continuity",
        "name": "Correction repair answer",
        "purpose": "Repair the answer after a user correction by changing shape, not just wording.",
        "triggers": (
            "correction",
            "wrong",
            "revise",
            "fix",
            "no that's wrong",
            "actually",
        ),
        "required_inputs": (
            "correction history",
            "continuity state",
            "answer-shape gap",
        ),
        "output_shape": "revised answer that changes shape",
        "method_type": "adaptive_delivery",
        "implementation_status": "catalog_registered",
        "source_refs": RELATIONSHIP_SOURCE_REFS_V1,
        "target_files": ("weslr/targeted_response_formation_improvement.py", "weslr/meaning_response.py"),
        "diff_vs_generic_llm": "Uses correction history to revise the actual response shape.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "continuity_thread_answer_v1",
        "family_id": "relationship_correction_continuity",
        "name": "Continuity / thread answer",
        "purpose": "Preserve the current thread and prior decisions.",
        "triggers": (
            "what were we doing",
            "follow-up",
            "thread",
            "continuity",
            "previous point",
        ),
        "required_inputs": (
            "continuity state",
            "recent turns",
            "timeline anchors",
        ),
        "output_shape": "thread-aware response or recap",
        "method_type": "continuity_guided",
        "implementation_status": "catalog_registered",
        "source_refs": RELATIONSHIP_SOURCE_REFS_V1,
        "target_files": ("weslr/entity_timeline_memory.py", "weslr/user_timeline_memory.py", "weslr/meaning_state_context.py"),
        "diff_vs_generic_llm": "Keeps thread continuity without pretending to have unrestricted long-term memory.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "relationship_feedback_answer_v1",
        "family_id": "relationship_correction_continuity",
        "name": "Relationship / feedback answer",
        "purpose": "Acknowledge user signals, trust state, and feedback without fake empathy.",
        "triggers": (
            "feedback",
            "preference",
            "frustration",
            "trust",
            "relationship",
            "tone",
        ),
        "required_inputs": (
            "relationship context",
            "trust state",
            "emotional pressure",
        ),
        "output_shape": "bounded acknowledgment plus next step",
        "method_type": "adaptive_delivery",
        "implementation_status": "catalog_registered",
        "source_refs": RELATIONSHIP_SOURCE_REFS_V1,
        "target_files": ("weslr/meaning_response.py", "weslr/relationship_observation_capture.py"),
        "diff_vs_generic_llm": "Responds to relationship state without pretending emotional experience.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "conflict_contradiction_handling_answer_v1",
        "family_id": "relationship_correction_continuity",
        "name": "Conflict / contradiction handling answer",
        "purpose": "Preserve contradictions instead of erasing them.",
        "triggers": (
            "conflict",
            "contradiction",
            "clash",
            "inconsistent",
            "both true",
        ),
        "required_inputs": (
            "conflict records",
            "evidence conflicts",
            "missing assumptions",
        ),
        "output_shape": "conflict-aware explanation or clarification",
        "method_type": "governed",
        "implementation_status": "catalog_registered",
        "source_refs": RELATIONSHIP_SOURCE_REFS_V1,
        "target_files": ("weslr/reasoning_trace.py", "weslr/reasoning_arbitrator.py"),
        "diff_vs_generic_llm": "Makes contradiction visible instead of smoothing it away.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "answer_shape_planning_v1",
        "family_id": "response_shape_quality",
        "name": "Answer-shape planning",
        "purpose": "Choose the right response shape before composing prose.",
        "triggers": (
            "shape",
            "answer shape",
            "directness",
            "format",
            "style",
            "structure",
        ),
        "required_inputs": (
            "task frame",
            "concern slot",
            "recency",
            "directness pressure",
            "boundary calibration",
        ),
        "output_shape": "shape label plus plan",
        "method_type": "matrix_ranked",
        "implementation_status": "catalog_registered",
        "source_refs": QUALITY_SOURCE_REFS_V1,
        "target_files": ("weslr/targeted_response_formation_improvement.py",),
        "diff_vs_generic_llm": "Selects shape first, prose second.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "non_cannedness_pressure_v1",
        "family_id": "response_shape_quality",
        "name": "Non-cannedness pressure",
        "purpose": "Suppress repeated template feel and generic fallback structure.",
        "triggers": (
            "canned",
            "template",
            "boilerplate",
            "repeated",
            "generic",
        ),
        "required_inputs": (
            "repetition markers",
            "specificity markers",
            "user concern",
        ),
        "output_shape": "pressure label and selected structure",
        "method_type": "quality_control",
        "implementation_status": "catalog_registered",
        "source_refs": QUALITY_SOURCE_REFS_V1,
        "target_files": ("weslr/targeted_response_formation_improvement.py",),
        "diff_vs_generic_llm": "Keeps replies content-specific instead of boilerplate-shaped.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
    {
        "method_id": "directness_concern_integration_self_check_v1",
        "family_id": "response_shape_quality",
        "name": "Directness / concern integration / self-check",
        "purpose": "Tune directness, concern handling, and self-check before final response selection.",
        "triggers": (
            "directness",
            "concern",
            "empathy",
            "self-check",
            "friction",
            "loaded",
        ),
        "required_inputs": (
            "concern slot",
            "frustration signal",
            "directness pressure",
            "boundary calibration",
        ),
        "output_shape": "revised answer plan or rejection",
        "method_type": "quality_control",
        "implementation_status": "catalog_registered",
        "source_refs": QUALITY_SOURCE_REFS_V1,
        "target_files": ("weslr/targeted_response_formation_improvement.py",),
        "diff_vs_generic_llm": "Adjusts the response posture without fake warmth or loss of boundary.",
        "runtime_authority": False,
        "model_required": False,
        "writes_state": False,
        "safe_for_catalog_selection": True,
    },
)

_FAMILY_METHOD_IDS_V1 = {
    "identity_status": (
        "verified_identity_status_answer_v1",
        "memory_report_answer_v1",
        "capability_orientation_answer_v1",
        "new_contact_orientation_answer_v1",
    ),
    "boundary_uncertainty": (
        "clarifying_question_answer_v1",
        "bounded_uncertainty_answer_v1",
        "refusal_boundary_answer_v1",
        "evidence_needed_answer_v1",
        "partial_answer_supported_portion_answer_v1",
        "direct_bounded_answer_v1",
    ),
    "task_workflow": (
        "ordinary_task_planning_answer_v1",
        "implementation_planning_answer_v1",
        "artifact_workspace_planning_answer_v1",
        "workflow_next_lane_answer_v1",
        "governance_escalation_proposal_v1",
    ),
    "teaching_explanation_discovery": (
        "teaching_explanation_answer_v1",
        "language_grammar_vocabulary_discovery_answer_v1",
        "scientific_discovery_capability_guidance_answer_v1",
        "benchmark_evaluation_answer_v1",
        "unknown_engine_branch_friction_answer_v1",
    ),
    "relationship_correction_continuity": (
        "correction_repair_answer_v1",
        "continuity_thread_answer_v1",
        "relationship_feedback_answer_v1",
        "conflict_contradiction_handling_answer_v1",
    ),
    "response_shape_quality": (
        "answer_shape_planning_v1",
        "non_cannedness_pressure_v1",
        "directness_concern_integration_self_check_v1",
    ),
}

_SELECT_LABEL_HINTS_V1 = {
    "identity_status": {"identity", "status", "self", "who", "what", "about", "you"},
    "boundary_uncertainty": {"uncertain", "uncertainty", "clarify", "clarifying", "missing", "ambiguous", "evidence", "refuse", "boundary", "partial", "direct"},
    "task_workflow": {"task", "workflow", "plan", "steps", "lane", "workspace", "artifact", "governance", "approve", "escalate"},
    "teaching_explanation_discovery": {"teach", "teaching", "explain", "explanation", "language", "grammar", "vocabulary", "research", "scientific", "benchmark", "evaluation", "unknown"},
    "relationship_correction_continuity": {"correction", "continuity", "thread", "relationship", "feedback", "conflict", "contradiction", "wrong", "revise"},
    "response_shape_quality": {"shape", "quality", "canned", "template", "directness", "concern", "self-check", "self", "tone", "style", "structure"},
}

_FALLBACK_METHOD_ID_V1 = "clarifying_question_answer_v1"

_ALLOWED_PACKET_KEYS_V1 = {
    "catalog_type",
    "families",
    "methods",
    "fallback_method_id",
}

_ALLOWED_FAMILY_KEYS_V1 = {
    "family_id",
    "name",
    "purpose",
    "source_refs",
    "target_files",
    "implementation_status",
    "method_ids",
}

_ALLOWED_METHOD_KEYS_V1 = {
    "method_id",
    "family_id",
    "name",
    "purpose",
    "triggers",
    "required_inputs",
    "output_shape",
    "method_type",
    "implementation_status",
    "source_refs",
    "target_files",
    "diff_vs_generic_llm",
    "runtime_authority",
    "model_required",
    "writes_state",
    "safe_for_catalog_selection",
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


def _build_family_specs(methods_by_family: Mapping[str, tuple[str, ...]]) -> tuple[AnswerMethodFamilySpec, ...]:
    family_specs: list[AnswerMethodFamilySpec] = []
    for family_data in _FAMILY_SPECS_V1:
        family_id = _safe_str(family_data.get("family_id"))
        family_specs.append(
            AnswerMethodFamilySpec(
                family_id=family_id,
                name=_safe_str(family_data.get("name")),
                purpose=_safe_str(family_data.get("purpose")),
                source_refs=tuple(_safe_text_list(family_data.get("source_refs"))),
                target_files=tuple(_safe_text_list(family_data.get("target_files"))),
                implementation_status=_safe_str(family_data.get("implementation_status")),
                method_ids=tuple(methods_by_family.get(family_id, ())),
            )
        )
    return tuple(family_specs)


def _build_method_specs() -> tuple[AnswerMethodSpec, ...]:
    method_specs: list[AnswerMethodSpec] = []
    for method_data in _METHOD_SPECS_V1:
        method_specs.append(
            AnswerMethodSpec(
                method_id=_safe_str(method_data.get("method_id")),
                family_id=_safe_str(method_data.get("family_id")),
                name=_safe_str(method_data.get("name")),
                purpose=_safe_str(method_data.get("purpose")),
                triggers=tuple(_safe_text_list(method_data.get("triggers"))),
                required_inputs=tuple(_safe_text_list(method_data.get("required_inputs"))),
                output_shape=_safe_str(method_data.get("output_shape")),
                method_type=_safe_str(method_data.get("method_type")),
                implementation_status=_safe_str(method_data.get("implementation_status")),
                source_refs=tuple(_safe_text_list(method_data.get("source_refs"))),
                target_files=tuple(_safe_text_list(method_data.get("target_files"))),
                diff_vs_generic_llm=_safe_str(method_data.get("diff_vs_generic_llm")),
                runtime_authority=_safe_bool(method_data.get("runtime_authority")),
                model_required=_safe_bool(method_data.get("model_required")),
                writes_state=_safe_bool(method_data.get("writes_state")),
                safe_for_catalog_selection=_safe_bool(method_data.get("safe_for_catalog_selection")),
            )
        )
    return tuple(method_specs)


def _index_methods_by_family(methods: Iterable[AnswerMethodSpec]) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, list[str]] = {family_id: [] for family_id in ALLOWED_FAMILY_IDS_V1}
    for method in methods:
        grouped.setdefault(method.family_id, []).append(method.method_id)
    return {family_id: tuple(method_ids) for family_id, method_ids in grouped.items()}


def _catalog_to_mapping(catalog: Any) -> Mapping[str, Any]:
    if is_dataclass(catalog):
        return _as_mapping(asdict(catalog))
    if isinstance(catalog, Mapping):
        return catalog
    return {}


def build_answer_method_catalog_v1() -> AnswerMethodCatalogPacket:
    methods = _build_method_specs()
    methods_by_family = _index_methods_by_family(methods)
    families = _build_family_specs(methods_by_family)
    return AnswerMethodCatalogPacket(
        catalog_type=CATALOG_TYPE_V1,
        families=families,
        methods=methods,
        fallback_method_id=_FALLBACK_METHOD_ID_V1,
    )


def validate_answer_method_catalog_v1(catalog: Mapping[str, Any] | AnswerMethodCatalogPacket | None = None) -> dict[str, Any]:
    packet = _catalog_to_mapping(catalog or build_answer_method_catalog_v1())
    normalized = to_answer_method_catalog_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        normalized = {}

    blocked_labels: list[str] = []
    families_value = _safe_list(normalized.get("families"))
    methods_value = _safe_list(normalized.get("methods"))
    fallback_method_id = _safe_str(normalized.get("fallback_method_id"))

    if set(normalized.keys()) - _ALLOWED_PACKET_KEYS_V1:
        blocked_labels.append("unexpected_packet_field")
    if _safe_str(normalized.get("catalog_type")) != CATALOG_TYPE_V1:
        blocked_labels.append("invalid_catalog_type")
    if not families_value:
        blocked_labels.append("missing_families")
    if not methods_value:
        blocked_labels.append("missing_methods")
    if not fallback_method_id:
        blocked_labels.append("missing_fallback_method_id")

    family_ids_seen: list[str] = []
    method_ids_seen: list[str] = []
    family_id_set: set[str] = set()
    method_id_set: set[str] = set()
    family_method_ids_union: set[str] = set()
    method_family_map: dict[str, int] = {}

    for family_value in families_value:
        family = _as_mapping(family_value)
        if set(family.keys()) - _ALLOWED_FAMILY_KEYS_V1:
            blocked_labels.append("unexpected_family_field")
        family_id = _safe_str(family.get("family_id"))
        name = _safe_str(family.get("name"))
        purpose = _safe_str(family.get("purpose"))
        source_refs = _safe_text_list(family.get("source_refs"))
        target_files = _safe_text_list(family.get("target_files"))
        implementation_status = _safe_str(family.get("implementation_status"))
        method_ids = _safe_text_list(family.get("method_ids"))

        if not family_id:
            blocked_labels.append("missing_family_id")
        if family_id in family_id_set:
            blocked_labels.append("duplicate_family_id")
        family_id_set.add(family_id)
        family_ids_seen.append(family_id)
        if family_id and family_id not in ALLOWED_FAMILY_IDS_V1:
            blocked_labels.append("unknown_family_id")
        if not name:
            blocked_labels.append("missing_family_name")
        if not purpose:
            blocked_labels.append("missing_family_purpose")
        if not source_refs:
            blocked_labels.append("missing_source_refs")
        if not target_files:
            blocked_labels.append("missing_target_files")
        if implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES_V1:
            blocked_labels.append("unknown_implementation_status")
        if not method_ids:
            blocked_labels.append("missing_family_method_ids")
        family_method_ids_union.update(method_ids)

    for method_value in methods_value:
        method = _as_mapping(method_value)
        if set(method.keys()) - _ALLOWED_METHOD_KEYS_V1:
            blocked_labels.append("unexpected_method_field")
        method_id = _safe_str(method.get("method_id"))
        family_id = _safe_str(method.get("family_id"))
        name = _safe_str(method.get("name"))
        purpose = _safe_str(method.get("purpose"))
        triggers = _safe_text_list(method.get("triggers"))
        required_inputs = _safe_text_list(method.get("required_inputs"))
        output_shape = _safe_str(method.get("output_shape"))
        method_type = _safe_str(method.get("method_type"))
        implementation_status = _safe_str(method.get("implementation_status"))
        source_refs = _safe_text_list(method.get("source_refs"))
        target_files = _safe_text_list(method.get("target_files"))
        diff_vs_generic_llm = _safe_str(method.get("diff_vs_generic_llm"))
        runtime_authority = _safe_bool(method.get("runtime_authority"))
        model_required = _safe_bool(method.get("model_required"))
        writes_state = _safe_bool(method.get("writes_state"))
        safe_for_catalog_selection = _safe_bool(method.get("safe_for_catalog_selection"))

        if not method_id:
            blocked_labels.append("missing_method_id")
        if method_id in method_id_set:
            blocked_labels.append("duplicate_method_id")
        method_id_set.add(method_id)
        method_ids_seen.append(method_id)
        if family_id not in ALLOWED_FAMILY_IDS_V1:
            blocked_labels.append("unknown_family_reference")
        method_family_map[method_id] = 1
        if not family_id:
            blocked_labels.append("missing_method_family_id")
        if not name:
            blocked_labels.append("missing_method_name")
        if not purpose:
            blocked_labels.append("missing_method_purpose")
        if not triggers:
            blocked_labels.append("missing_method_triggers")
        if not required_inputs:
            blocked_labels.append("missing_method_required_inputs")
        if not output_shape:
            blocked_labels.append("missing_method_output_shape")
        if method_type not in ALLOWED_METHOD_TYPES_V1:
            blocked_labels.append("unknown_method_type")
        if implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES_V1:
            blocked_labels.append("unknown_implementation_status")
        if not source_refs:
            blocked_labels.append("missing_source_refs")
        if not target_files:
            blocked_labels.append("missing_target_files")
        if not diff_vs_generic_llm:
            blocked_labels.append("missing_diff_vs_generic_llm")
        if runtime_authority:
            blocked_labels.append("runtime_authority_must_be_false")
        if model_required:
            blocked_labels.append("model_required_must_be_false")
        if writes_state:
            blocked_labels.append("writes_state_must_be_false")
        if not safe_for_catalog_selection:
            blocked_labels.append("unsafe_for_catalog_selection")

    if ALLOWED_FAMILY_IDS_V1 - family_id_set:
        blocked_labels.append("missing_required_family")
    if _FALLBACK_METHOD_ID_V1 and _FALLBACK_METHOD_ID_V1 not in method_id_set:
        blocked_labels.append("missing_fallback_method")
    if fallback_method_id and fallback_method_id not in method_id_set:
        blocked_labels.append("fallback_method_not_registered")

    for family in families_value:
        family_map = _as_mapping(family)
        family_method_ids = set(_safe_text_list(family_map.get("method_ids")))
        family_id = _safe_str(family_map.get("family_id"))
        expected_methods = {
            _safe_str(_as_mapping(method_value).get("method_id"))
            for method_value in methods_value
            if _safe_str(_as_mapping(method_value).get("family_id")) == family_id
        }
        if family_method_ids and not family_method_ids.issubset(method_id_set):
            blocked_labels.append("family_references_missing_method")
        if family_id and family_method_ids != expected_methods:
            blocked_labels.append("family_method_ids_mismatch")

    valid = not blocked_labels
    return {
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": sorted(set(blocked_labels)),
        "catalog_type": _safe_str(normalized.get("catalog_type")),
        "family_count": len(families_value),
        "method_count": len(methods_value),
        "fallback_method_id": fallback_method_id,
    }


def summarize_answer_method_catalog_v1(catalog: Mapping[str, Any] | AnswerMethodCatalogPacket | None = None) -> dict[str, Any]:
    packet = _catalog_to_mapping(catalog or build_answer_method_catalog_v1())
    normalized = to_answer_method_catalog_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        normalized = {}

    families = _safe_list(normalized.get("families"))
    methods = _safe_list(normalized.get("methods"))
    methods_by_family: dict[str, int] = {}
    methods_by_type: dict[str, int] = {}
    methods_by_status: dict[str, int] = {}
    selectable_method_count = 0

    for method_value in methods:
        method = _as_mapping(method_value)
        family_id = _safe_str(method.get("family_id"))
        method_type = _safe_str(method.get("method_type"))
        status = _safe_str(method.get("implementation_status"))
        methods_by_family[family_id] = methods_by_family.get(family_id, 0) + 1
        methods_by_type[method_type] = methods_by_type.get(method_type, 0) + 1
        methods_by_status[status] = methods_by_status.get(status, 0) + 1
        if _safe_bool(method.get("safe_for_catalog_selection")):
            selectable_method_count += 1

    return {
        "summary_type": SUMMARY_TYPE_V1,
        "catalog_type": _safe_str(normalized.get("catalog_type")),
        "family_count": len(families),
        "method_count": len(methods),
        "selectable_method_count": selectable_method_count,
        "fallback_method_id": _safe_str(normalized.get("fallback_method_id")),
        "family_ids": sorted(_safe_str(_as_mapping(item).get("family_id")) for item in families),
        "method_ids": sorted(_safe_str(_as_mapping(item).get("method_id")) for item in methods),
        "methods_by_family": dict(sorted(methods_by_family.items())),
        "methods_by_type": dict(sorted(methods_by_type.items())),
        "methods_by_status": dict(sorted(methods_by_status.items())),
    }


def to_answer_method_catalog_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def _method_match_score(turn_tokens: set[str], method: Mapping[str, Any], family_id: str) -> int:
    method_tokens = set(_tokenize(method.get("method_id")))
    method_tokens |= set(_tokenize(method.get("name")))
    method_tokens |= set(_tokenize(method.get("purpose")))
    method_tokens |= set(_tokenize(method.get("output_shape")))
    method_tokens |= set(_tokenize(family_id))
    for trigger in _safe_text_list(method.get("triggers")):
        method_tokens |= _tokenize(trigger)
    return len(turn_tokens & method_tokens)


def select_methods_for_turn_v1(turn_labels: Iterable[Any], catalog: Mapping[str, Any] | AnswerMethodCatalogPacket | None = None) -> dict[str, Any]:
    packet = _catalog_to_mapping(catalog or build_answer_method_catalog_v1())
    normalized = to_answer_method_catalog_json_safe_v1(packet)
    if not isinstance(normalized, Mapping):
        normalized = {}

    labels = _safe_text_list(turn_labels)
    turn_tokens: set[str] = set()
    for label in labels:
        turn_tokens |= _tokenize(label)

    methods = _safe_list(normalized.get("methods"))
    families = _safe_list(normalized.get("families"))
    family_map = { _safe_str(_as_mapping(item).get("family_id")): _as_mapping(item) for item in families }

    scored_methods: list[dict[str, Any]] = []
    matched_labels: set[str] = set()
    for method_value in methods:
        method = _as_mapping(method_value)
        if not _safe_bool(method.get("safe_for_catalog_selection")):
            continue
        family_id = _safe_str(method.get("family_id"))
        score = _method_match_score(turn_tokens, method, family_id)
        if score <= 0:
            continue
        method_labels = set()
        for token in _tokenize(method.get("method_id")) | _tokenize(method.get("name")) | _tokenize(method.get("purpose")) | _tokenize(family_id):
            method_labels.add(token)
        for trigger in _safe_text_list(method.get("triggers")):
            method_labels |= _tokenize(trigger)
        matched = sorted(turn_tokens & method_labels)
        matched_labels.update(matched)
        family = family_map.get(family_id, {})
        scored_methods.append(
            {
                "method_id": _safe_str(method.get("method_id")),
                "family_id": family_id,
                "family_name": _safe_str(family.get("name")),
                "name": _safe_str(method.get("name")),
                "purpose": _safe_str(method.get("purpose")),
                "method_type": _safe_str(method.get("method_type")),
                "implementation_status": _safe_str(method.get("implementation_status")),
                "output_shape": _safe_str(method.get("output_shape")),
                "safe_for_catalog_selection": _safe_bool(method.get("safe_for_catalog_selection")),
                "match_score": score,
                "matched_labels": matched,
            }
        )

    scored_methods.sort(key=lambda item: (-int(item["match_score"]), item["family_id"], item["method_id"]))
    selected_methods = scored_methods[:5]
    selected_method_ids = [item["method_id"] for item in selected_methods]
    selected_family_ids = sorted({item["family_id"] for item in selected_methods})
    unknown_labels = sorted(label for label in labels if not _tokenize(label) & matched_labels)

    fallback_used = False
    if not selected_methods:
        fallback_method = None
        for method_value in methods:
            method = _as_mapping(method_value)
            if _safe_str(method.get("method_id")) == _FALLBACK_METHOD_ID_V1 and _safe_bool(method.get("safe_for_catalog_selection")):
                fallback_method = method
                break
        if fallback_method is None and methods:
            fallback_method = _as_mapping(methods[0])
        if fallback_method:
            fallback_used = True
            family_id = _safe_str(fallback_method.get("family_id"))
            family = family_map.get(family_id, {})
            selected_methods = [
                {
                    "method_id": _safe_str(fallback_method.get("method_id")),
                    "family_id": family_id,
                    "family_name": _safe_str(family.get("name")),
                    "name": _safe_str(fallback_method.get("name")),
                    "purpose": _safe_str(fallback_method.get("purpose")),
                    "method_type": _safe_str(fallback_method.get("method_type")),
                    "implementation_status": _safe_str(fallback_method.get("implementation_status")),
                    "output_shape": _safe_str(fallback_method.get("output_shape")),
                    "safe_for_catalog_selection": _safe_bool(fallback_method.get("safe_for_catalog_selection")),
                    "match_score": 0,
                    "matched_labels": [],
                }
            ]
            selected_method_ids = [selected_methods[0]["method_id"]]
            selected_family_ids = [selected_methods[0]["family_id"]]

    return {
        "selection_type": SELECTION_RESULT_TYPE_V1,
        "catalog_type": _safe_str(normalized.get("catalog_type")),
        "turn_labels": labels,
        "turn_tokens": sorted(turn_tokens),
        "unknown_labels": unknown_labels,
        "fallback_used": fallback_used,
        "selected_method_ids": selected_method_ids,
        "selected_family_ids": selected_family_ids,
        "selected_methods": selected_methods,
        "catalog_summary": summarize_answer_method_catalog_v1(normalized),
    }


__all__ = [
    "AnswerMethodCatalogPacket",
    "AnswerMethodFamilySpec",
    "AnswerMethodSpec",
    "build_answer_method_catalog_v1",
    "validate_answer_method_catalog_v1",
    "summarize_answer_method_catalog_v1",
    "to_answer_method_catalog_json_safe_v1",
    "select_methods_for_turn_v1",
]
