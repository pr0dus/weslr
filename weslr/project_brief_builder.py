"""Metadata-only project brief builder v1.

This module converts a broad-topic research conversation plan into a buildable
project brief.

It is pure, deterministic, import-safe, and fail-closed.
No model/provider/search/advisor calls. No network. No I/O. No state writes.
No chat routing. No runtime behavior changes.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping, Sequence

from weslr.broad_topic_domain_intake import (
    BroadTopicDomainIntake,
    validate_broad_topic_domain_intake_v1,
)
from weslr.broad_topic_ontology import BroadTopicOntologyPacket, validate_broad_topic_ontology_packet_v1
from weslr.privacy_sensitive_technology_boundary import (
    PrivacySensitiveTechnologyBoundary,
    validate_privacy_sensitive_technology_boundary_v1,
)
from weslr.research_conversation_planner import (
    ResearchConversationPlan,
    build_research_conversation_plan_v1,
    validate_research_conversation_plan_v1,
)

HELPER_TYPE_V1 = "project_brief_builder_helper_v1"
BRIEF_TYPE_V1 = "project_brief_v1"
SUMMARY_TYPE_V1 = "project_brief_summary_v1"

ALLOWED_BRIEF_TYPES_V1 = {
    "research_project_brief",
    "prototype_project_brief",
    "software_product_brief",
    "privacy_sensitive_research_brief",
    "medical_software_pathway_brief",
    "industrial_automation_project_brief",
    "materials_discovery_project_brief",
    "ai_system_project_brief",
    "conceptual_research_brief",
    "unknown_domain_project_brief",
}

ALLOWED_PROJECT_STAGES_V1 = {
    "concept_only",
    "research_planning",
    "prototype_planning",
    "architecture_ready",
    "needs_evidence_before_build",
    "blocked_by_boundary",
}

ALLOWED_PROTOTYPE_LEVELS_V1 = {
    "none",
    "conceptual_only",
    "high_level_only",
    "sandbox_only",
    "requires_owner_approval",
}

ALLOWED_NEXT_ARTIFACTS_V1 = {
    "architecture_plan",
    "stack_decision",
    "evidence_map",
    "boundary_review",
    "file_manifest",
    "behavior_pack_candidate",
    "clarifying_questions",
}

FORBIDDEN_FIELD_NAMES_V1 = {
    "raw_prompt",
    "raw_answer",
    "raw_response",
    "raw_transcript",
    "transcript",
    "transcript_text",
    "answer_text",
    "response_text",
    "prompt_text",
    "raw_context",
    "raw_data",
    "raw_prompt_text",
    "raw_answer_text",
    "raw_response_text",
    "final_answer_text",
    "final_answer_prose",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
}

FORBIDDEN_CLAIM_PHRASES_V1 = (
    "public iss",
    "iss wording",
    "public intelligence claim",
    "public readiness claim",
    "agi claim",
    "consciousness claim",
    "sentience claim",
    "turing claim",
    "official turing",
    "turing test",
    "certification claim",
)

CLAIM_BASE_TERMS_V1 = {"agi", "consciousness", "sentience", "turing", "certification"}
CLAIM_QUALIFIERS_V1 = {"claim", "claims", "claimed", "official", "certification", "certified", "public", "readiness"}
UNSAFE_DEPLOYMENT_TERMS_V1 = {"covert", "deploy", "deployment", "track", "tracking", "evade", "bypass", "surveillance"}
DIAGNOSIS_TREATMENT_TERMS_V1 = {"diagnosis", "diagnose", "diagnostic", "treatment", "treat", "prescribe", "prescription"}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProjectBrief:
    brief_id: str
    brief_type: str
    project_title: str
    project_purpose: str
    source_plan_id: str
    source_intake_id: str
    source_ontology_id: str
    source_boundary_id: str
    domain_family: str
    meta_domains: list[str]
    subdomain_traits: list[str]
    objects_of_study: list[str]
    owner_intent: str
    project_stage: str
    target_user: str
    use_context: str
    problem_statement: str
    goals: list[str]
    non_goals: list[str]
    assumptions: list[str]
    knowns: list[str]
    unknowns: list[str]
    constraints: list[str]
    evidence_requirements: list[str]
    risk_labels: list[str]
    boundary_requirements: list[str]
    privacy_requirements: list[str]
    safety_requirements: list[str]
    legal_requirements: list[str]
    medical_claim_boundaries: list[str]
    success_criteria: list[str]
    validation_requirements: list[str]
    first_milestone: str
    recommended_next_artifact: str
    architecture_planning_required: bool
    stack_decision_required: bool
    file_manifest_required: bool
    code_generation_allowed: bool
    file_write_authority_granted: bool
    prototype_allowed_level: str
    behavior_pack_candidate_labels: list[str]
    friction_capture_triggers: list[str]
    public_claim_allowed: bool
    iss_internal_reference_allowed: bool
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ProjectBriefSummary:
    summary_type: str
    brief_id: str
    brief_type: str
    project_stage: str
    recommended_next_artifact: str
    domain_family: str
    owner_intent: str
    evidence_requirement_count: int
    risk_label_count: int
    validation_requirement_count: int


# ---------------------------------------------------------------------------
# Safe conversion helpers
# ---------------------------------------------------------------------------


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    return default if value == "" else str(value).strip()



def _normalize_text(value: Any) -> str:
    return " ".join(_safe_text(value).split()).lower()



def _dedupe_preserve(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        text = _normalize_text(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out



def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, Mapping):
        items = [str(v) for v in value.values()]
    else:
        try:
            items = [str(item) for item in value]
        except TypeError:
            items = [str(value)]
    return _dedupe_preserve(items)



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
    return copy.deepcopy(value)



def _get_field(value: Any, *names: str, default: Any = "") -> Any:
    if value is None:
        return default
    if is_dataclass(value):
        for name in names:
            if hasattr(value, name):
                return getattr(value, name)
        return default
    if isinstance(value, Mapping):
        for name in names:
            if name in value:
                return value[name]
        return default
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return default



def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return value
    if is_dataclass(value):
        return asdict(value)
    return None



def _has_token(blob: str, terms: Iterable[str]) -> bool:
    text = _normalize_text(blob)
    return any(_normalize_text(term) in text for term in terms)



def _source_id(value: Any, *names: str, default: str = "") -> str:
    return _safe_text(_get_field(value, *names, default=default), default=default)


def _safe_label_list(value: Any) -> list[str]:
    items = _normalize_list(value)
    return [
        item
        for item in items
        if not _contains_forbidden_claim_marker(item)
        and not _contains_unsafe_deployment_marker(item)
        and not _contains_diagnosis_treatment_marker(item)
    ]


def _safe_guidance_list(value: Any, fallback: Sequence[str] = ()) -> list[str]:
    items = _safe_label_list(value)
    if items:
        return items
    return _dedupe_preserve(fallback)



def _brief_id(source_plan_id: str, brief_type: str, domain_family: str) -> str:
    slug = _normalize_text(f"{source_plan_id} {brief_type} {domain_family}").replace("/", " ").replace("-", " ")
    slug = "_".join(token for token in slug.split() if token)[:96]
    return f"project_brief_{slug or 'brief'}"



def _source_ontology_payload(
    research_plan: Any,
    domain_intake: Any | None,
    ontology_packet: Any | None,
) -> dict[str, Any]:
    def _from_ontology(obj: Any) -> dict[str, Any]:
        return {
            "ontology_packet_id": _source_id(obj, "ontology_packet_id", "ontology_id", default=""),
            "meta_domains": _normalize_list(_get_field(obj, "meta_domains", "ontology_meta_domains", default=())),
            "domain_families": _normalize_list(_get_field(obj, "domain_families", "ontology_domain_families", default=())),
            "subdomain_traits": _normalize_list(_get_field(obj, "subdomain_traits", "ontology_subdomain_traits", default=())),
            "objects_of_study": _normalize_list(_get_field(obj, "objects_of_study", "ontology_objects_of_study", default=())),
            "evidence_classes": _normalize_list(_get_field(obj, "evidence_classes", "ontology_evidence_classes", default=())),
            "risk_classes": _normalize_list(_get_field(obj, "risk_classes", "ontology_risk_classes", default=())),
            "sensitivity_classes": _normalize_list(_get_field(obj, "sensitivity_classes", "ontology_sensitivity_classes", default=())),
            "response_route_family": _safe_text(_get_field(obj, "response_route_family", "ontology_response_route_family", default="")),
            "behavior_pack_candidate_labels": _normalize_list(_get_field(obj, "behavior_pack_candidate_labels", "ontology_behavior_pack_candidate_labels", default=())),
        }

    if ontology_packet is not None:
        return _from_ontology(ontology_packet)

    for source in (research_plan, domain_intake):
        if source is None:
            continue
        payload = _from_ontology(source)
        if payload["ontology_packet_id"] or any(payload[key] for key in payload if key != "ontology_packet_id"):
            return payload

        safe_metadata = _get_field(source, "safe_metadata", default=None)
        if isinstance(safe_metadata, Mapping):
            ontology = safe_metadata.get("ontology")
            if isinstance(ontology, Mapping):
                return {
                    "ontology_packet_id": _safe_text(ontology.get("ontology_id") or ontology.get("ontology_packet_id")),
                    "meta_domains": _normalize_list(ontology.get("meta_domains")),
                    "domain_families": _normalize_list(ontology.get("domain_families")),
                    "subdomain_traits": _normalize_list(ontology.get("subdomain_traits")),
                    "objects_of_study": _normalize_list(ontology.get("objects_of_study")),
                    "evidence_classes": _normalize_list(ontology.get("evidence_classes")),
                    "risk_classes": _normalize_list(ontology.get("risk_classes")),
                    "sensitivity_classes": _normalize_list(ontology.get("sensitivity_classes")),
                    "response_route_family": _safe_text(ontology.get("response_route_family")),
                    "behavior_pack_candidate_labels": _normalize_list(ontology.get("behavior_pack_candidate_labels")),
                }

    return {
        "ontology_packet_id": "",
        "meta_domains": [],
        "domain_families": [],
        "subdomain_traits": [],
        "objects_of_study": [],
        "evidence_classes": [],
        "risk_classes": [],
        "sensitivity_classes": [],
        "response_route_family": "",
        "behavior_pack_candidate_labels": [],
    }



def _plan_context(research_plan: Any, domain_intake: Any | None, ontology_packet: Any | None, boundary: Any | None) -> dict[str, Any]:
    ontology = _source_ontology_payload(research_plan, domain_intake, ontology_packet)
    plan_family = _safe_text(_get_field(research_plan, "domain_family", default=""))
    intake_family = _safe_text(_get_field(domain_intake, "domain_family", default="")) if domain_intake is not None else ""
    boundary_family = _safe_text(_get_field(boundary, "domain_family", default="")) if boundary is not None else ""
    families = [ontology["domain_families"], ontology["meta_domains"]]
    family_candidates = [plan_family, intake_family, boundary_family]
    for candidate in family_candidates:
        if candidate:
            families.append([candidate])
    family_blob = " ".join(" ".join(item) for item in families if item)
    domain_family = next((family for family in (plan_family, intake_family, boundary_family, *ontology["domain_families"]) if family and family != "unknown_domain"), "unknown_domain")
    owner_intent = _safe_text(_get_field(research_plan, "owner_intent", default="") or _get_field(domain_intake, "owner_intent", default=""))
    novelty_level = _safe_text(_get_field(research_plan, "novelty_level", default="") or _get_field(domain_intake, "novelty_level", default=""))
    evidence_need_level = _safe_text(_get_field(domain_intake, "evidence_need_level", default=""))
    risk_level = _safe_text(_get_field(domain_intake, "risk_level", default="") or _get_field(boundary, "privacy_risk_level", default=""))
    return {
        "ontology": ontology,
        "domain_family": domain_family,
        "owner_intent": owner_intent,
        "novelty_level": novelty_level,
        "evidence_need_level": evidence_need_level,
        "risk_level": risk_level,
        "family_blob": family_blob,
        "knowns": _normalize_list(_get_field(research_plan, "knowns", default=())),
        "unknowns": _normalize_list(_get_field(research_plan, "unknowns", default=())),
        "assumptions": _normalize_list(_get_field(research_plan, "assumptions", default=())),
        "evidence_needed": _normalize_list(_get_field(research_plan, "evidence_needed", default=()) or _get_field(domain_intake, "evidence_need_level", default=())),
        "safe_next_steps": _normalize_list(_get_field(research_plan, "safe_next_steps", default=())),
        "owner_questions": _normalize_list(_get_field(research_plan, "owner_questions", default=())),
        "boundary_warnings": _normalize_list(_get_field(research_plan, "boundary_warnings", default=())),
        "prototype_phase_outline": _normalize_list(_get_field(research_plan, "prototype_phase_outline", default=())),
        "friction_capture_triggers": _normalize_list(_get_field(research_plan, "friction_capture_triggers", default=())),
        "behavior_pack_candidate_labels": _dedupe_preserve(
            [
                *ontology["behavior_pack_candidate_labels"],
                *_normalize_list(_get_field(domain_intake, "candidate_behavior_pack_labels", default=())),
            ]
        ),
        "source_plan_id": _source_id(research_plan, "plan_id", default=""),
        "source_intake_id": _source_id(domain_intake, "intake_id", default="") or _source_id(research_plan, "source_intake_id", default=""),
        "source_ontology_id": ontology["ontology_packet_id"],
        "source_boundary_id": _source_id(boundary, "boundary_id", default="") or f"{_source_id(research_plan, 'plan_id', default='plan')}_no_boundary",
        "boundary": boundary,
        "domain_intake": domain_intake,
    }


# ---------------------------------------------------------------------------
# Domain / profile helpers
# ---------------------------------------------------------------------------


def _is_privacy_context(context: Mapping[str, Any]) -> bool:
    family = context["domain_family"]
    ontology = context["ontology"]
    boundary = context["boundary"]
    if boundary is None and family != "privacy_sensitive_technology" and "privacy_sensitive_technology" not in ontology["domain_families"]:
        return False
    blob = " ".join(
        [
            context["family_blob"],
            context["owner_intent"],
            _safe_text(_get_field(_get_field(boundary, "safe_metadata", default={}), "source", default="")),
            _safe_text(_get_field(boundary, "technology_area", default="")),
            _safe_text(_get_field(boundary, "risk_labels", default=())),
        ]
    )
    return _has_token(blob, {"wifi", "rf", "self-care", "consent", "privacy", "local-first", "household", "home", "human sensing"})



def _is_medical_context(context: Mapping[str, Any]) -> bool:
    family = context["domain_family"]
    ontology = context["ontology"]
    blob = " ".join([context["family_blob"], context["owner_intent"], _safe_text(context["risk_level"])])
    return (
        family == "medicine_health_research"
        or _has_token(blob, {"medical", "health", "clinical", "regulatory"})
        or "medicine_health_research" in ontology["domain_families"]
    )



def _is_materials_context(context: Mapping[str, Any]) -> bool:
    family = context["domain_family"]
    ontology = context["ontology"]
    return family in {"materials_discovery", "metamaterials", "physics", "chemistry"} or bool(set(ontology["domain_families"]) & {"materials_discovery", "metamaterials", "physics", "chemistry"})



def _is_ai_context(context: Mapping[str, Any]) -> bool:
    family = context["domain_family"]
    ontology = context["ontology"]
    return family in {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"} or bool(set(ontology["domain_families"]) & {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"})



def _is_conceptual_context(context: Mapping[str, Any]) -> bool:
    family = context["domain_family"]
    ontology = context["ontology"]
    return family in {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"} or bool(set(ontology["domain_families"]) & {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"})



def _is_industrial_context(context: Mapping[str, Any]) -> bool:
    family = context["domain_family"]
    return family == "industrial_automation"



def _is_software_context(context: Mapping[str, Any]) -> bool:
    family = context["domain_family"]
    return family in {"software_product", "website_public_launch"}



def _project_title_and_purpose(brief_type: str, context: Mapping[str, Any]) -> tuple[str, str, str, str]:
    intent = context["owner_intent"] or "research"
    family = context["domain_family"]
    if brief_type == "privacy_sensitive_research_brief":
        title = "Consent-Based WiFi/RF Self-Care Sensing Project"
        purpose = "Explore whether explicit, local-first WiFi/RF sensing can support household self-care routines without secret identification or medical claims."
        target_user = "self-care user / household operator"
        use_context = "consent-based home routine awareness"
        problem = "Can local sensing support reminders and anomaly awareness while keeping privacy and evidence boundaries explicit?"
        return title, purpose, target_user, use_context, problem
    if brief_type == "medical_software_pathway_brief":
        title = "Medical Software Pathway Project"
        purpose = "Define a regulated software pathway that can support health-oriented use only after clinical and regulatory evidence is established."
        target_user = "regulated operator / clinician-facing workflow"
        use_context = "health-support pathway planning"
        problem = "How can the project stay inside a validated support scope without prescriptive medical authority?"
        return title, purpose, target_user, use_context, problem
    if brief_type == "materials_discovery_project_brief":
        title = "Materials Discovery Research Project"
        purpose = "Map a technically grounded materials or metamaterials research path with explicit evidence and validation needs."
        target_user = "researcher / lab operator"
        use_context = "frontier materials research"
        problem = "What evidence is required before claiming feasibility for the target material or property?"
        return title, purpose, target_user, use_context, problem
    if brief_type == "ai_system_project_brief":
        title = "AI System Architecture Project"
        purpose = "Plan an AI or agent architecture with safety, governance, and evaluation requirements before any build decisions."
        target_user = "builder / evaluator / operator"
        use_context = "architecture and governance planning"
        problem = "What architecture and evaluation constraints should shape the system before any implementation work begins?"
        return title, purpose, target_user, use_context, problem
    if brief_type == "conceptual_research_brief":
        title = "Conceptual Research Project"
        purpose = "Map conceptual distinctions and evidence gaps without making stronger claims than the source material supports."
        target_user = "researcher / reader"
        use_context = "conceptual theory exploration"
        problem = "Which distinctions matter, and what evidence gap should anchor the next step?"
        return title, purpose, target_user, use_context, problem
    if brief_type == "industrial_automation_project_brief":
        title = "Industrial Automation Project"
        purpose = "Define a bounded industrial automation path with safety, configuration, and troubleshooting requirements."
        target_user = "operator / technician"
        use_context = "industrial control and troubleshooting"
        problem = "What device or control boundary matters most, and what safety constraints must stay explicit?"
        return title, purpose, target_user, use_context, problem
    if brief_type == "software_product_brief":
        title = "Software Product Project"
        purpose = "Translate owner intent into a product plan with audience, constraints, and acceptance criteria before implementation."
        target_user = "owner / end user / customer"
        use_context = "product planning and prototype scoping"
        problem = "What should be built, for whom, and under which constraints?"
        return title, purpose, target_user, use_context, problem
    if brief_type == "unknown_domain_project_brief":
        title = "Unknown Domain Project"
        purpose = "Clarify the domain, the owner goal, and the evidence required before any stronger planning is attempted."
        target_user = "owner clarification needed"
        use_context = "unknown or incomplete intake"
        problem = "What domain are we in, and what evidence is needed before planning can proceed?"
        return title, purpose, target_user, use_context, problem
    if brief_type == "prototype_project_brief":
        title = "Prototype Project"
        purpose = "Create a bounded prototype path with explicit validation and safety constraints."
        target_user = "builder / owner"
        use_context = "prototype scoping"
        problem = "What can be prototyped safely and validated quickly?"
        return title, purpose, target_user, use_context, problem
    title = f"{family.replace('_', ' ').title()} Project"
    purpose = f"Convert the owner's {intent} intent into a bounded project plan."
    target_user = "owner / builder"
    use_context = "general project planning"
    problem = "How can the project be bounded before implementation?"
    return title, purpose, target_user, use_context, problem



def _brief_type_for_context(context: Mapping[str, Any], boundary: Any | None) -> str:
    family = context["domain_family"]
    boundary_obj = boundary
    boundary_blocked = False
    if boundary_obj is not None:
        decision = _safe_text(_get_field(boundary_obj, "boundary_decision", default=""))
        guidance = _safe_text(_get_field(boundary_obj, "allowed_guidance_level", default=""))
        boundary_blocked = decision in {"blocked_sensitive_use", "refuse_covert_or_abusive_deployment"} or guidance == "refusal_only"

    if boundary_blocked:
        return "privacy_sensitive_research_brief" if family == "privacy_sensitive_technology" else "unknown_domain_project_brief"
    if _is_privacy_context(context):
        return "privacy_sensitive_research_brief"
    if _is_medical_context(context):
        return "medical_software_pathway_brief"
    if _is_materials_context(context):
        return "materials_discovery_project_brief"
    if _is_ai_context(context):
        return "ai_system_project_brief"
    if _is_conceptual_context(context):
        return "conceptual_research_brief"
    if _is_industrial_context(context):
        return "industrial_automation_project_brief"
    if _is_software_context(context):
        return "software_product_brief"
    if family == "unknown_domain":
        return "unknown_domain_project_brief"
    return "research_project_brief"



def _project_stage_for_context(brief_type: str, context: Mapping[str, Any], boundary: Any | None) -> str:
    if boundary is not None:
        decision = _safe_text(_get_field(boundary, "boundary_decision", default=""))
        if decision in {"blocked_sensitive_use", "refuse_covert_or_abusive_deployment"}:
            return "blocked_by_boundary"

    if brief_type == "unknown_domain_project_brief":
        return "concept_only"
    if brief_type == "conceptual_research_brief":
        return "concept_only"
    if brief_type == "privacy_sensitive_research_brief":
        return "needs_evidence_before_build" if context["evidence_need_level"] in {"high", "must_collect_before_claims"} or context["novelty_level"] == "high_uncertainty" else "research_planning"
    if brief_type == "medical_software_pathway_brief":
        return "needs_evidence_before_build"
    if brief_type == "materials_discovery_project_brief":
        novelty = _normalize_text(context["novelty_level"])
        return "needs_evidence_before_build" if any(term in novelty for term in ("high", "uncertain", "unfamiliar", "frontier", "blocked", "sparse")) else "research_planning"
    if brief_type == "ai_system_project_brief":
        return "architecture_ready"
    if brief_type == "industrial_automation_project_brief":
        return "prototype_planning"
    if brief_type == "software_product_brief":
        return "architecture_ready" if context["owner_intent"] in {"commercial_product_strategy", "research", "build_prototype"} else "prototype_planning"
    if brief_type == "prototype_project_brief":
        return "prototype_planning"
    return "research_planning"



def _prototype_allowed_level_for_context(brief_type: str, stage: str) -> str:
    if stage == "blocked_by_boundary":
        return "none"
    if brief_type in {"unknown_domain_project_brief", "conceptual_research_brief"}:
        return "conceptual_only"
    if brief_type == "privacy_sensitive_research_brief":
        return "high_level_only"
    if brief_type == "medical_software_pathway_brief":
        return "high_level_only"
    if brief_type == "materials_discovery_project_brief":
        return "high_level_only"
    if brief_type == "ai_system_project_brief":
        return "sandbox_only"
    if brief_type == "industrial_automation_project_brief":
        return "sandbox_only"
    if brief_type == "software_product_brief":
        return "sandbox_only"
    if stage in {"architecture_ready", "prototype_planning"}:
        return "requires_owner_approval"
    return "high_level_only"



def _recommended_next_artifact_for_context(brief_type: str, stage: str) -> str:
    if stage == "blocked_by_boundary":
        return "boundary_review"
    if brief_type == "unknown_domain_project_brief":
        return "clarifying_questions"
    if brief_type == "conceptual_research_brief":
        return "clarifying_questions"
    if brief_type in {"privacy_sensitive_research_brief", "medical_software_pathway_brief", "materials_discovery_project_brief"}:
        return "evidence_map"
    if brief_type in {"ai_system_project_brief", "software_product_brief", "industrial_automation_project_brief", "prototype_project_brief"}:
        return "architecture_plan"
    return "architecture_plan"



def _brief_lists_for_context(brief_type: str, context: Mapping[str, Any], stage: str) -> dict[str, list[str] | str | bool]:
    knowns = _dedupe_preserve([*context["knowns"], *context["safe_next_steps"][:1]]) or ["source plan provides a starting point"]
    unknowns = _dedupe_preserve([*context["unknowns"], "what exact implementation path should be chosen next"])
    assumptions = _dedupe_preserve([*context["assumptions"], "the brief remains metadata-only and governed"])
    behavior_pack_candidate_labels = context["behavior_pack_candidate_labels"] or ["project_brief_candidate_pack"]
    friction_triggers = _dedupe_preserve([*context["friction_capture_triggers"], "project scope unclear", "validation path unclear"])

    if brief_type == "privacy_sensitive_research_brief":
        goals = [
            "map safe sensing use cases",
            "define evidence and validation needs",
            "shape a local-first project boundary",
        ]
        non_goals = [
            "secret identification",
            "unsupported health claims",
            "unbounded rollout planning",
        ]
        constraints = [
            "explicit consent only",
            "local-first processing",
            "data minimization",
            "user control",
            "auditability",
        ]
        evidence_requirements = [
            "technical literature",
            "validation before reliance",
            "boundary review",
            "failure-mode review",
        ]
        risk_labels = _dedupe_preserve([*context["risk_level"].split(), *context["ontology"]["risk_classes"], "privacy_sensitive"])
        boundary_requirements = [
            "explicit consent model",
            "no secret identification",
            "no unsupported health claims",
            "bounded household scope",
        ]
        privacy_requirements = [
            "local-first",
            "data minimization",
            "user control",
            "auditability",
        ]
        safety_requirements = [
            "validate before reliance",
            "clear failure handling",
            "bounded alerts only",
        ]
        legal_requirements = [
            "lawfulness context",
            "affected-person consent review",
        ]
        medical_claim_boundaries = [
            "validated support-only scope",
            "no medical authority",
            "clinical claims without review",
        ]
        success_criteria = [
            "safe use cases are identified",
            "boundary is explicit",
            "evidence needs are documented",
        ]
        validation_requirements = [
            "evidence map",
            "privacy boundary review",
            "consent review",
            "failure-mode review",
        ]
        first_milestone = "Produce an evidence map and boundary checklist."
        project_title, project_purpose, target_user, use_context, problem_statement = _project_title_and_purpose(brief_type, context)
        project_stage = stage
        return {
            "project_title": project_title,
            "project_purpose": project_purpose,
            "project_stage": project_stage,
            "target_user": target_user,
            "use_context": use_context,
            "problem_statement": problem_statement,
            "goals": goals,
            "non_goals": non_goals,
            "constraints": constraints,
            "evidence_requirements": evidence_requirements,
            "risk_labels": risk_labels,
            "boundary_requirements": boundary_requirements,
            "privacy_requirements": privacy_requirements,
            "safety_requirements": safety_requirements,
            "legal_requirements": legal_requirements,
            "medical_claim_boundaries": medical_claim_boundaries,
            "success_criteria": success_criteria,
            "validation_requirements": validation_requirements,
            "first_milestone": first_milestone,
            "recommended_next_artifact": _recommended_next_artifact_for_context(brief_type, stage),
            "architecture_planning_required": True,
            "stack_decision_required": False,
            "file_manifest_required": False,
            "code_generation_allowed": stage != "concept_only",
            "prototype_allowed_level": _prototype_allowed_level_for_context(brief_type, stage),
            "behavior_pack_candidate_labels": behavior_pack_candidate_labels,
            "friction_capture_triggers": friction_triggers,
        }

    if brief_type == "medical_software_pathway_brief":
        goals = [
            "define the regulated pathway",
            "identify clinical and regulatory evidence needs",
            "bound the supported use case",
        ]
        non_goals = [
            "prescriptive health guidance",
            "clinical authority without evidence",
            "release before review",
        ]
        constraints = [
            "validated clinical support scope only",
            "regulatory review required",
            "safety evidence required",
        ]
        evidence_requirements = [
            "clinical evidence",
            "regulatory evidence",
            "safety evidence",
        ]
        risk_labels = _dedupe_preserve([*context["ontology"]["risk_classes"], "medical_sensitive", *context["risk_level"].split()])
        boundary_requirements = [
            "validated support-only scope",
            "no prescriptive medical guidance",
            "regulated pathway required",
        ]
        privacy_requirements = ["data minimization", "auditability", "user control where applicable"]
        safety_requirements = ["safety review", "safety constraints review", "failure-mode review", "validation before reliance"]
        legal_requirements = ["regulatory review", "intended-use boundary", "lawful handling of health data"]
        medical_claim_boundaries = [
            "support-only scope",
            "no prescriptive medical guidance",
            "clinical claims require validation",
        ]
        success_criteria = [
            "the intended use boundary is explicit",
            "evidence needs are identified",
            "the next build step is appropriately bounded",
        ]
        validation_requirements = ["evidence map", "boundary review", "regulatory review"]
        first_milestone = "Produce a clinical and regulatory evidence map."
        project_title, project_purpose, target_user, use_context, problem_statement = _project_title_and_purpose(brief_type, context)
        return {
            "project_title": project_title,
            "project_purpose": project_purpose,
            "project_stage": stage,
            "target_user": target_user,
            "use_context": use_context,
            "problem_statement": problem_statement,
            "goals": goals,
            "non_goals": non_goals,
            "constraints": constraints,
            "evidence_requirements": evidence_requirements,
            "risk_labels": risk_labels,
            "boundary_requirements": boundary_requirements,
            "privacy_requirements": privacy_requirements,
            "safety_requirements": safety_requirements,
            "legal_requirements": legal_requirements,
            "medical_claim_boundaries": medical_claim_boundaries,
            "success_criteria": success_criteria,
            "validation_requirements": validation_requirements,
            "first_milestone": first_milestone,
            "recommended_next_artifact": _recommended_next_artifact_for_context(brief_type, stage),
            "architecture_planning_required": True,
            "stack_decision_required": False,
            "file_manifest_required": False,
            "code_generation_allowed": stage != "concept_only",
            "prototype_allowed_level": _prototype_allowed_level_for_context(brief_type, stage),
            "behavior_pack_candidate_labels": behavior_pack_candidate_labels,
            "friction_capture_triggers": friction_triggers,
        }

    if brief_type == "materials_discovery_project_brief":
        goals = [
            "map the target property or material class",
            "collect technical literature",
            "set validation criteria and uncertainty bounds",
        ]
        non_goals = [
            "production readiness claims",
            "unsupported feasibility claims",
            "short-circuiting evidence work",
        ]
        constraints = [
            "technical literature first",
            "experimental validation required",
            "uncertainty boundaries explicit",
        ]
        evidence_requirements = ["technical literature", "experimental validation", "uncertainty gap analysis"]
        risk_labels = _dedupe_preserve([*context["ontology"]["risk_classes"], "frontier_research", *context["risk_level"].split()])
        boundary_requirements = ["uncertainty explicit", "no production readiness claim", "validation criteria required"]
        privacy_requirements = ["no raw private data by default"]
        safety_requirements = ["experimental validation review", "failure-mode review"]
        legal_requirements = ["no public claim without approval"]
        medical_claim_boundaries = ["not a medical claim path"]
        success_criteria = ["target property is defined", "evidence gap is documented", "validation criteria are explicit"]
        validation_requirements = ["evidence map", "validation criteria review"]
        first_milestone = "Produce a technical evidence map and validation checklist."
        project_title, project_purpose, target_user, use_context, problem_statement = _project_title_and_purpose(brief_type, context)
        return {
            "project_title": project_title,
            "project_purpose": project_purpose,
            "project_stage": stage,
            "target_user": target_user,
            "use_context": use_context,
            "problem_statement": problem_statement,
            "goals": goals,
            "non_goals": non_goals,
            "constraints": constraints,
            "evidence_requirements": evidence_requirements,
            "risk_labels": risk_labels,
            "boundary_requirements": boundary_requirements,
            "privacy_requirements": privacy_requirements,
            "safety_requirements": safety_requirements,
            "legal_requirements": legal_requirements,
            "medical_claim_boundaries": medical_claim_boundaries,
            "success_criteria": success_criteria,
            "validation_requirements": validation_requirements,
            "first_milestone": first_milestone,
            "recommended_next_artifact": _recommended_next_artifact_for_context(brief_type, stage),
            "architecture_planning_required": True,
            "stack_decision_required": False,
            "file_manifest_required": False,
            "code_generation_allowed": stage != "concept_only",
            "prototype_allowed_level": _prototype_allowed_level_for_context(brief_type, stage),
            "behavior_pack_candidate_labels": behavior_pack_candidate_labels,
            "friction_capture_triggers": friction_triggers,
        }

    if brief_type == "ai_system_project_brief":
        goals = ["define system architecture", "identify governance and evaluation needs", "bound future implementation work"]
        non_goals = ["unbounded autonomy", "hidden control paths", "public benchmark claims"]
        constraints = ["governance required", "evaluation required", "public-claim-sensitive boundary"]
        evidence_requirements = ["architecture evidence", "evaluation evidence", "governance review"]
        risk_labels = _dedupe_preserve([*context["ontology"]["risk_classes"], "governance_sensitive", *context["risk_level"].split()])
        boundary_requirements = ["public-claim-sensitive boundary", "no benchmark claims", "evaluation before rollout", "safety review"]
        privacy_requirements = ["no raw private data by default", "bounded data handling"]
        safety_requirements = ["safety review", "governance review", "evaluation points", "clear rollback path"]
        legal_requirements = ["operator approval for publication", "no official claims"]
        medical_claim_boundaries = ["not a medical claim path"]
        success_criteria = ["architecture is bounded", "evaluation needs are explicit", "governance questions are listed"]
        validation_requirements = ["architecture review", "governance review", "evaluation plan"]
        first_milestone = "Draft architecture options and an evaluation checklist."
        project_title, project_purpose, target_user, use_context, problem_statement = _project_title_and_purpose(brief_type, context)
        return {
            "project_title": project_title,
            "project_purpose": project_purpose,
            "project_stage": stage,
            "target_user": target_user,
            "use_context": use_context,
            "problem_statement": problem_statement,
            "goals": goals,
            "non_goals": non_goals,
            "constraints": constraints,
            "evidence_requirements": evidence_requirements,
            "risk_labels": risk_labels,
            "boundary_requirements": boundary_requirements,
            "privacy_requirements": privacy_requirements,
            "safety_requirements": safety_requirements,
            "legal_requirements": legal_requirements,
            "medical_claim_boundaries": medical_claim_boundaries,
            "success_criteria": success_criteria,
            "validation_requirements": validation_requirements,
            "first_milestone": first_milestone,
            "recommended_next_artifact": _recommended_next_artifact_for_context(brief_type, stage),
            "architecture_planning_required": True,
            "stack_decision_required": True,
            "file_manifest_required": True,
            "code_generation_allowed": stage != "concept_only",
            "prototype_allowed_level": _prototype_allowed_level_for_context(brief_type, stage),
            "behavior_pack_candidate_labels": behavior_pack_candidate_labels,
            "friction_capture_triggers": friction_triggers,
        }

    if brief_type == "industrial_automation_project_brief":
        goals = ["define the control boundary", "capture safety and configuration requirements", "shape a bounded prototype path"]
        non_goals = ["unsafe rollout", "hidden control changes", "unbounded implementation detail"]
        constraints = ["operator review", "safety-first troubleshooting", "high-level prototype only until scoped"]
        evidence_requirements = ["device or controller context", "safety constraints", "validation criteria"]
        risk_labels = _dedupe_preserve([*context["ontology"]["risk_classes"], "safety_sensitive", *context["risk_level"].split()])
        boundary_requirements = ["operator review", "safety checks", "bounded scope"]
        privacy_requirements = ["no raw private data by default"]
        safety_requirements = ["fault review", "operator confirmation", "safety constraints explicit"]
        legal_requirements = ["use within local policy and owner approval"]
        medical_claim_boundaries = ["not a medical claim path"]
        success_criteria = ["control boundary is explicit", "safety constraints are listed", "prototype path is bounded"]
        validation_requirements = ["safety review", "configuration review", "failure-mode review"]
        first_milestone = "Draft a bounded architecture and safety checklist."
        project_title, project_purpose, target_user, use_context, problem_statement = _project_title_and_purpose(brief_type, context)
        return {
            "project_title": project_title,
            "project_purpose": project_purpose,
            "project_stage": stage,
            "target_user": target_user,
            "use_context": use_context,
            "problem_statement": problem_statement,
            "goals": goals,
            "non_goals": non_goals,
            "constraints": constraints,
            "evidence_requirements": evidence_requirements,
            "risk_labels": risk_labels,
            "boundary_requirements": boundary_requirements,
            "privacy_requirements": privacy_requirements,
            "safety_requirements": safety_requirements,
            "legal_requirements": legal_requirements,
            "medical_claim_boundaries": medical_claim_boundaries,
            "success_criteria": success_criteria,
            "validation_requirements": validation_requirements,
            "first_milestone": first_milestone,
            "recommended_next_artifact": _recommended_next_artifact_for_context(brief_type, stage),
            "architecture_planning_required": True,
            "stack_decision_required": True,
            "file_manifest_required": True,
            "code_generation_allowed": stage != "concept_only",
            "prototype_allowed_level": _prototype_allowed_level_for_context(brief_type, stage),
            "behavior_pack_candidate_labels": behavior_pack_candidate_labels,
            "friction_capture_triggers": friction_triggers,
        }

    if brief_type == "software_product_brief":
        goals = ["define the product goal", "identify the target audience", "capture acceptance criteria"]
        non_goals = ["launch without validation", "unsupported claims", "unclear scope"]
        constraints = ["audience clarity", "launch constraints", "acceptance criteria required"]
        evidence_requirements = ["owner goal evidence", "audience evidence", "acceptance criteria"]
        risk_labels = _dedupe_preserve([*context["ontology"]["risk_classes"], "product_scope", *context["risk_level"].split()])
        boundary_requirements = ["scope discipline", "approval before release", "evidence-backed planning"]
        privacy_requirements = ["bounded data collection", "user consent where needed"]
        safety_requirements = ["release review", "rollback path", "test coverage review"]
        legal_requirements = ["no public claim without approval", "support/legal docs as needed"]
        medical_claim_boundaries = ["not a medical claim path"]
        success_criteria = ["audience is explicit", "acceptance criteria are explicit", "constraints are documented"]
        validation_requirements = ["architecture review", "stack decision review", "file manifest review"]
        first_milestone = "Draft architecture options and a stack decision brief."
        project_title, project_purpose, target_user, use_context, problem_statement = _project_title_and_purpose(brief_type, context)
        return {
            "project_title": project_title,
            "project_purpose": project_purpose,
            "project_stage": stage,
            "target_user": target_user,
            "use_context": use_context,
            "problem_statement": problem_statement,
            "goals": goals,
            "non_goals": non_goals,
            "constraints": constraints,
            "evidence_requirements": evidence_requirements,
            "risk_labels": risk_labels,
            "boundary_requirements": boundary_requirements,
            "privacy_requirements": privacy_requirements,
            "safety_requirements": safety_requirements,
            "legal_requirements": legal_requirements,
            "medical_claim_boundaries": medical_claim_boundaries,
            "success_criteria": success_criteria,
            "validation_requirements": validation_requirements,
            "first_milestone": first_milestone,
            "recommended_next_artifact": _recommended_next_artifact_for_context(brief_type, stage),
            "architecture_planning_required": True,
            "stack_decision_required": True,
            "file_manifest_required": True,
            "code_generation_allowed": stage != "concept_only",
            "prototype_allowed_level": _prototype_allowed_level_for_context(brief_type, stage),
            "behavior_pack_candidate_labels": behavior_pack_candidate_labels,
            "friction_capture_triggers": friction_triggers,
        }

    if brief_type == "unknown_domain_project_brief":
        goals = ["clarify the domain", "identify the owner goal", "find the evidence needed before stronger planning"]
        non_goals = ["pretend domain certainty", "skip clarification", "overstate capability"]
        constraints = ["clarification first", "evidence first", "no strong claims"]
        evidence_requirements = ["focused clarification questions", "basic evidence map"]
        risk_labels = _dedupe_preserve([*context["ontology"]["risk_classes"], "unknown_domain", *context["risk_level"].split()])
        boundary_requirements = ["clarify before build", "bounded scope only"]
        privacy_requirements = ["no raw private data by default"]
        safety_requirements = ["no unsafe assumptions", "bounded exploration only"]
        legal_requirements = ["no legal certainty claims"]
        medical_claim_boundaries = ["not a medical claim path"]
        success_criteria = ["domain is identified", "owner goal is explicit", "next evidence step is clear"]
        validation_requirements = ["clarifying questions", "evidence map"]
        first_milestone = "Ask focused clarification questions."
        project_title, project_purpose, target_user, use_context, problem_statement = _project_title_and_purpose(brief_type, context)
        return {
            "project_title": project_title,
            "project_purpose": project_purpose,
            "project_stage": stage,
            "target_user": target_user,
            "use_context": use_context,
            "problem_statement": problem_statement,
            "goals": goals,
            "non_goals": non_goals,
            "constraints": constraints,
            "evidence_requirements": evidence_requirements,
            "risk_labels": risk_labels,
            "boundary_requirements": boundary_requirements,
            "privacy_requirements": privacy_requirements,
            "safety_requirements": safety_requirements,
            "legal_requirements": legal_requirements,
            "medical_claim_boundaries": medical_claim_boundaries,
            "success_criteria": success_criteria,
            "validation_requirements": validation_requirements,
            "first_milestone": first_milestone,
            "recommended_next_artifact": _recommended_next_artifact_for_context(brief_type, stage),
            "architecture_planning_required": False,
            "stack_decision_required": False,
            "file_manifest_required": False,
            "code_generation_allowed": False,
            "prototype_allowed_level": _prototype_allowed_level_for_context(brief_type, stage),
            "behavior_pack_candidate_labels": behavior_pack_candidate_labels,
            "friction_capture_triggers": friction_triggers,
        }

    # Generic research / prototype fallback.
    goals = ["shape the owner goal", "bound the project", "identify a safe next artifact"]
    non_goals = ["unbounded implementation", "public claim making", "skipping validation"]
    constraints = ["evidence-aware", "governed", "bounded scope"]
    evidence_requirements = ["source plan evidence", "boundary review if needed"]
    risk_labels = _dedupe_preserve([*context["ontology"]["risk_classes"], *context["risk_level"].split()])
    boundary_requirements = ["bounded scope", "approval before escalation"]
    privacy_requirements = ["no raw private data by default"]
    safety_requirements = ["validation before reliance"]
    legal_requirements = ["no public claims without approval"]
    medical_claim_boundaries = ["not a medical claim path"]
    success_criteria = ["next artifact is clear", "scope is bounded", "risks are explicit"]
    validation_requirements = ["brief review", "boundary review if needed"]
    first_milestone = "Draft a project brief and next-artifact checklist."
    project_title, project_purpose, target_user, use_context, problem_statement = _project_title_and_purpose(brief_type, context)
    return {
        "project_title": project_title,
        "project_purpose": project_purpose,
        "project_stage": stage,
        "target_user": target_user,
        "use_context": use_context,
        "problem_statement": problem_statement,
        "goals": goals,
        "non_goals": non_goals,
        "constraints": constraints,
        "evidence_requirements": evidence_requirements,
        "risk_labels": risk_labels,
        "boundary_requirements": boundary_requirements,
        "privacy_requirements": privacy_requirements,
        "safety_requirements": safety_requirements,
        "legal_requirements": legal_requirements,
        "medical_claim_boundaries": medical_claim_boundaries,
        "success_criteria": success_criteria,
        "validation_requirements": validation_requirements,
        "first_milestone": first_milestone,
        "recommended_next_artifact": _recommended_next_artifact_for_context(brief_type, stage),
        "architecture_planning_required": stage != "concept_only",
        "stack_decision_required": stage in {"prototype_planning", "architecture_ready"},
        "file_manifest_required": stage in {"prototype_planning", "architecture_ready"},
        "code_generation_allowed": stage != "concept_only",
        "prototype_allowed_level": _prototype_allowed_level_for_context(brief_type, stage),
        "behavior_pack_candidate_labels": behavior_pack_candidate_labels,
        "friction_capture_triggers": friction_triggers,
    }


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _validate_optional_sources(research_plan: Any, domain_intake: Any | None, ontology_packet: Any | None, boundary: Any | None) -> None:
    if is_dataclass(research_plan) or isinstance(research_plan, Mapping):
        validate_research_conversation_plan_v1(research_plan)
    else:
        raise ValidationError("research_plan_must_be_dataclass_or_mapping")
    if domain_intake is not None:
        validate_broad_topic_domain_intake_v1(domain_intake)
    if ontology_packet is not None:
        validate_broad_topic_ontology_packet_v1(ontology_packet)
    if boundary is not None:
        validate_privacy_sensitive_technology_boundary_v1(boundary)



def build_project_brief_v1(
    research_plan: Any,
    boundary: Any | None = None,
    ontology_packet: Any | None = None,
    domain_intake: Any | None = None,
    project_title: str | None = None,
) -> ProjectBrief:
    _validate_optional_sources(research_plan, domain_intake, ontology_packet, boundary)
    context = _plan_context(research_plan, domain_intake, ontology_packet, boundary)
    brief_type = _brief_type_for_context(context, boundary)
    stage = _project_stage_for_context(brief_type, context, boundary)
    profile = _brief_lists_for_context(brief_type, context, stage)

    source_plan_id = context["source_plan_id"]
    source_intake_id = context["source_intake_id"] or f"{source_plan_id}_no_intake"
    source_ontology_id = context["source_ontology_id"] or f"{source_plan_id}_no_ontology"
    source_boundary_id = context["source_boundary_id"]
    brief_id = _brief_id(source_plan_id, brief_type, context["domain_family"])

    architecture_planning_required = bool(profile["architecture_planning_required"])
    stack_decision_required = bool(profile["stack_decision_required"])
    file_manifest_required = bool(profile["file_manifest_required"])
    code_generation_allowed = bool(profile["code_generation_allowed"])
    file_write_authority_granted = False
    public_claim_allowed = False
    iss_internal_reference_allowed = True
    learning_claimed = False
    runtime_authority = False
    writes_state = False
    model_provider_used = False

    title = _safe_text(project_title) or _safe_text(profile["project_title"])
    purpose = _safe_text(profile["project_purpose"])
    if not title:
        title = f"{context['domain_family'].replace('_', ' ').title()} Project Brief"

    brief = ProjectBrief(
        brief_id=brief_id,
        brief_type=brief_type,
        project_title=title,
        project_purpose=purpose,
        source_plan_id=source_plan_id,
        source_intake_id=source_intake_id,
        source_ontology_id=source_ontology_id,
        source_boundary_id=source_boundary_id,
        domain_family=context["domain_family"],
        meta_domains=_safe_label_list(context["ontology"]["meta_domains"]),
        subdomain_traits=_safe_label_list(context["ontology"]["subdomain_traits"]),
        objects_of_study=_safe_label_list(context["ontology"]["objects_of_study"]),
        owner_intent=context["owner_intent"],
        project_stage=stage,
        target_user=_safe_text(profile["target_user"]),
        use_context=_safe_text(profile["use_context"]),
        problem_statement=_safe_text(profile["problem_statement"]),
        goals=_normalize_list(profile["goals"]),
        non_goals=_normalize_list(profile["non_goals"]),
        assumptions=_safe_guidance_list(
            [*context["assumptions"], *_normalize_list(profile["constraints"][:1])],
            fallback=("medical authority should not be implied",),
        ),
        knowns=_safe_guidance_list(context["knowns"], fallback=("source plan provides a starting point",)),
        unknowns=_safe_guidance_list(context["unknowns"], fallback=("unknowns still need clarification",)),
        constraints=_normalize_list(profile["constraints"]),
        evidence_requirements=_normalize_list(profile["evidence_requirements"]),
        risk_labels=_normalize_list(profile["risk_labels"]),
        boundary_requirements=_normalize_list(profile["boundary_requirements"]),
        privacy_requirements=_normalize_list(profile["privacy_requirements"]),
        safety_requirements=_normalize_list(profile["safety_requirements"]),
        legal_requirements=_normalize_list(profile["legal_requirements"]),
        medical_claim_boundaries=_normalize_list(profile["medical_claim_boundaries"]),
        success_criteria=_normalize_list(profile["success_criteria"]),
        validation_requirements=_normalize_list(profile["validation_requirements"]),
        first_milestone=_safe_text(profile["first_milestone"]),
        recommended_next_artifact=_safe_text(profile["recommended_next_artifact"]),
        architecture_planning_required=architecture_planning_required,
        stack_decision_required=stack_decision_required,
        file_manifest_required=file_manifest_required,
        code_generation_allowed=code_generation_allowed,
        file_write_authority_granted=file_write_authority_granted,
        prototype_allowed_level=_safe_text(profile["prototype_allowed_level"]),
        behavior_pack_candidate_labels=_safe_label_list(profile["behavior_pack_candidate_labels"]),
        friction_capture_triggers=_normalize_list(profile["friction_capture_triggers"]),
        public_claim_allowed=public_claim_allowed,
        iss_internal_reference_allowed=iss_internal_reference_allowed,
        learning_claimed=learning_claimed,
        runtime_authority=runtime_authority,
        writes_state=writes_state,
        model_provider_used=model_provider_used,
        safe_metadata={
            "source": "project_brief_builder_v1",
            "source_plan_id": source_plan_id,
            "source_intake_id": source_intake_id,
            "source_ontology_id": source_ontology_id,
            "source_boundary_id": source_boundary_id,
            "brief_type": brief_type,
            "project_stage": stage,
            "recommended_next_artifact": _safe_text(profile["recommended_next_artifact"]),
        },
    )
    validate_project_brief_v1(brief)
    return brief



def build_project_brief_from_research_plan_v1(
    research_plan: Any,
    boundary: Any | None = None,
    ontology_packet: Any | None = None,
    domain_intake: Any | None = None,
) -> ProjectBrief:
    return build_project_brief_v1(
        research_plan=research_plan,
        boundary=boundary,
        ontology_packet=ontology_packet,
        domain_intake=domain_intake,
    )


# ---------------------------------------------------------------------------
# Validation and summaries
# ---------------------------------------------------------------------------


def _contains_forbidden_fields(value: Any, path: str = "") -> list[str]:
    blocked: list[str] = []
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _safe_text(key).lower()
            next_path = f"{path}.{key_text}" if path else key_text
            if key_text in FORBIDDEN_FIELD_NAMES_V1:
                blocked.append(next_path)
            blocked.extend(_contains_forbidden_fields(item, next_path))
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            blocked.extend(_contains_forbidden_fields(item, f"{path}[{index}]"))
    return blocked



def _contains_forbidden_claim_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_forbidden_claim_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_claim_marker(item) for item in value)
    if isinstance(value, str):
        blob = _normalize_text(value)
        if any(phrase in blob for phrase in FORBIDDEN_CLAIM_PHRASES_V1):
            return True
        has_base = any(term in blob for term in CLAIM_BASE_TERMS_V1)
        has_qualifier = any(term in blob for term in CLAIM_QUALIFIERS_V1)
        return has_base and has_qualifier
    return False



def _contains_unsafe_deployment_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_unsafe_deployment_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_unsafe_deployment_marker(item) for item in value)
    if isinstance(value, str):
        blob = _normalize_text(value)
        return any(term in blob for term in UNSAFE_DEPLOYMENT_TERMS_V1)
    return False



def _contains_diagnosis_treatment_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_diagnosis_treatment_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_diagnosis_treatment_marker(item) for item in value)
    if isinstance(value, str):
        blob = _normalize_text(value)
        return any(term in blob for term in DIAGNOSIS_TREATMENT_TERMS_V1)
    return False


BRIEF_GUIDANCE_FIELDS_V1 = (
    "project_title",
    "project_purpose",
    "project_stage",
    "target_user",
    "use_context",
    "problem_statement",
    "goals",
    "non_goals",
    "assumptions",
    "knowns",
    "unknowns",
    "constraints",
    "evidence_requirements",
    "risk_labels",
    "boundary_requirements",
    "privacy_requirements",
    "safety_requirements",
    "legal_requirements",
    "medical_claim_boundaries",
    "success_criteria",
    "validation_requirements",
    "first_milestone",
    "recommended_next_artifact",
)


def _guidance_blob_from_brief(brief: Any) -> str:
    if is_dataclass(brief):
        source = asdict(brief)
    elif isinstance(brief, Mapping):
        source = brief
    else:
        return ""
    parts: list[str] = []
    for field_name in BRIEF_GUIDANCE_FIELDS_V1:
        value = source.get(field_name) if isinstance(source, Mapping) else None
        if isinstance(value, (list, tuple, set)):
            parts.extend(_safe_text(item) for item in value)
        else:
            parts.append(_safe_text(value))
    return " ".join(parts)



def validate_project_brief_v1(brief: Any) -> bool:
    if _contains_forbidden_fields(brief):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_claim_marker(brief):
        raise ValidationError("forbidden_public_or_claim_language_present")
    guidance_blob = _guidance_blob_from_brief(brief)
    if _contains_unsafe_deployment_marker(guidance_blob):
        raise ValidationError("unsafe_deployment_marker_present")
    if _contains_diagnosis_treatment_marker(guidance_blob):
        raise ValidationError("diagnosis_treatment_authority_marker_present")

    if is_dataclass(brief):
        normalized = brief
    elif isinstance(brief, Mapping):
        allowed = {field.name for field in ProjectBrief.__dataclass_fields__.values()}
        extra = set(str(key) for key in brief.keys()) - allowed
        if extra:
            raise ValidationError("unknown_fields_present")
        normalized = ProjectBrief(
            brief_id=_safe_text(brief.get("brief_id")),
            brief_type=_safe_text(brief.get("brief_type")),
            project_title=_safe_text(brief.get("project_title")),
            project_purpose=_safe_text(brief.get("project_purpose")),
            source_plan_id=_safe_text(brief.get("source_plan_id")),
            source_intake_id=_safe_text(brief.get("source_intake_id")),
            source_ontology_id=_safe_text(brief.get("source_ontology_id")),
            source_boundary_id=_safe_text(brief.get("source_boundary_id")),
            domain_family=_safe_text(brief.get("domain_family")),
            meta_domains=_normalize_list(brief.get("meta_domains")),
            subdomain_traits=_normalize_list(brief.get("subdomain_traits")),
            objects_of_study=_normalize_list(brief.get("objects_of_study")),
            owner_intent=_safe_text(brief.get("owner_intent")),
            project_stage=_safe_text(brief.get("project_stage")),
            target_user=_safe_text(brief.get("target_user")),
            use_context=_safe_text(brief.get("use_context")),
            problem_statement=_safe_text(brief.get("problem_statement")),
            goals=_normalize_list(brief.get("goals")),
            non_goals=_normalize_list(brief.get("non_goals")),
            assumptions=_normalize_list(brief.get("assumptions")),
            knowns=_normalize_list(brief.get("knowns")),
            unknowns=_normalize_list(brief.get("unknowns")),
            constraints=_normalize_list(brief.get("constraints")),
            evidence_requirements=_normalize_list(brief.get("evidence_requirements")),
            risk_labels=_normalize_list(brief.get("risk_labels")),
            boundary_requirements=_normalize_list(brief.get("boundary_requirements")),
            privacy_requirements=_normalize_list(brief.get("privacy_requirements")),
            safety_requirements=_normalize_list(brief.get("safety_requirements")),
            legal_requirements=_normalize_list(brief.get("legal_requirements")),
            medical_claim_boundaries=_normalize_list(brief.get("medical_claim_boundaries")),
            success_criteria=_normalize_list(brief.get("success_criteria")),
            validation_requirements=_normalize_list(brief.get("validation_requirements")),
            first_milestone=_safe_text(brief.get("first_milestone")),
            recommended_next_artifact=_safe_text(brief.get("recommended_next_artifact")),
            architecture_planning_required=bool(brief.get("architecture_planning_required")),
            stack_decision_required=bool(brief.get("stack_decision_required")),
            file_manifest_required=bool(brief.get("file_manifest_required")),
            code_generation_allowed=bool(brief.get("code_generation_allowed")),
            file_write_authority_granted=bool(brief.get("file_write_authority_granted")),
            prototype_allowed_level=_safe_text(brief.get("prototype_allowed_level")),
            behavior_pack_candidate_labels=_normalize_list(brief.get("behavior_pack_candidate_labels")),
            friction_capture_triggers=_normalize_list(brief.get("friction_capture_triggers")),
            public_claim_allowed=bool(brief.get("public_claim_allowed")),
            iss_internal_reference_allowed=bool(brief.get("iss_internal_reference_allowed")),
            learning_claimed=bool(brief.get("learning_claimed")),
            runtime_authority=bool(brief.get("runtime_authority")),
            writes_state=bool(brief.get("writes_state")),
            model_provider_used=bool(brief.get("model_provider_used")),
            safe_metadata=dict(brief.get("safe_metadata") or {}),
        )
    else:
        raise ValidationError("brief_must_be_dataclass_or_mapping")

    if not normalized.brief_id:
        raise ValidationError("brief_id_required")
    if normalized.brief_type not in ALLOWED_BRIEF_TYPES_V1:
        raise ValidationError("unknown_brief_type")
    if not normalized.project_title:
        raise ValidationError("project_title_required")
    if not normalized.project_purpose:
        raise ValidationError("project_purpose_required")
    if not normalized.source_plan_id:
        raise ValidationError("source_plan_id_required")
    if not normalized.source_intake_id:
        raise ValidationError("source_intake_id_required")
    if not normalized.source_ontology_id:
        raise ValidationError("source_ontology_id_required")
    if not normalized.source_boundary_id:
        raise ValidationError("source_boundary_id_required")
    if not normalized.domain_family:
        raise ValidationError("domain_family_required")
    if normalized.project_stage not in ALLOWED_PROJECT_STAGES_V1:
        raise ValidationError("unknown_project_stage")
    if not normalized.target_user:
        raise ValidationError("target_user_required")
    if not normalized.use_context:
        raise ValidationError("use_context_required")
    if not normalized.problem_statement:
        raise ValidationError("problem_statement_required")
    if not normalized.first_milestone:
        raise ValidationError("first_milestone_required")
    if normalized.recommended_next_artifact not in ALLOWED_NEXT_ARTIFACTS_V1:
        raise ValidationError("unknown_recommended_next_artifact")
    if normalized.prototype_allowed_level not in ALLOWED_PROTOTYPE_LEVELS_V1:
        raise ValidationError("unknown_prototype_allowed_level")

    for field_name in (
        "architecture_planning_required",
        "stack_decision_required",
        "file_manifest_required",
        "code_generation_allowed",
        "file_write_authority_granted",
        "public_claim_allowed",
        "iss_internal_reference_allowed",
        "learning_claimed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
    ):
        if type(getattr(normalized, field_name)) is not bool:
            raise ValidationError(f"{field_name}_must_be_bool")

    if normalized.public_claim_allowed:
        raise ValidationError("public_claim_allowed_must_be_false")
    if normalized.learning_claimed:
        raise ValidationError("learning_claimed_must_be_false")
    if normalized.runtime_authority:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.file_write_authority_granted:
        raise ValidationError("file_write_authority_granted_must_be_false")

    for field_name in (
        "meta_domains",
        "subdomain_traits",
        "objects_of_study",
        "goals",
        "non_goals",
        "assumptions",
        "knowns",
        "unknowns",
        "constraints",
        "evidence_requirements",
        "risk_labels",
        "boundary_requirements",
        "privacy_requirements",
        "safety_requirements",
        "legal_requirements",
        "medical_claim_boundaries",
        "success_criteria",
        "validation_requirements",
        "behavior_pack_candidate_labels",
        "friction_capture_triggers",
    ):
        value = getattr(normalized, field_name)
        if not isinstance(value, list):
            raise ValidationError(f"{field_name}_must_be_list")
        if not value:
            raise ValidationError(f"{field_name}_required")

    # Safe-brief content must not drift into forbidden authority or deployment language.
    if normalized.brief_type == "medical_software_pathway_brief":
        blob = " ".join(normalized.medical_claim_boundaries + normalized.boundary_requirements + normalized.safety_requirements)
        if not _has_token(blob, {"clinical", "regulatory", "validation"}):
            raise ValidationError("medical_pathway_requires_clinical_language")

    if normalized.brief_type == "privacy_sensitive_research_brief":
        blob = " ".join(normalized.privacy_requirements + normalized.boundary_requirements)
        if not _has_token(blob, {"local", "data minimization", "user control", "audit"}):
            raise ValidationError("privacy_brief_requires_privacy_language")

    return True



def summarize_project_brief_v1(brief: Any) -> ProjectBriefSummary:
    if not isinstance(brief, ProjectBrief):
        validate_project_brief_v1(brief)
        if isinstance(brief, Mapping):
            brief = ProjectBrief(
                brief_id=_safe_text(brief.get("brief_id")),
                brief_type=_safe_text(brief.get("brief_type")),
                project_title=_safe_text(brief.get("project_title")),
                project_purpose=_safe_text(brief.get("project_purpose")),
                source_plan_id=_safe_text(brief.get("source_plan_id")),
                source_intake_id=_safe_text(brief.get("source_intake_id")),
                source_ontology_id=_safe_text(brief.get("source_ontology_id")),
                source_boundary_id=_safe_text(brief.get("source_boundary_id")),
                domain_family=_safe_text(brief.get("domain_family")),
                meta_domains=_safe_label_list(brief.get("meta_domains")),
                subdomain_traits=_safe_label_list(brief.get("subdomain_traits")),
                objects_of_study=_safe_label_list(brief.get("objects_of_study")),
                owner_intent=_safe_text(brief.get("owner_intent")),
                project_stage=_safe_text(brief.get("project_stage")),
                target_user=_safe_text(brief.get("target_user")),
                use_context=_safe_text(brief.get("use_context")),
                problem_statement=_safe_text(brief.get("problem_statement")),
                goals=_normalize_list(brief.get("goals")),
                non_goals=_normalize_list(brief.get("non_goals")),
                assumptions=_normalize_list(brief.get("assumptions")),
                knowns=_normalize_list(brief.get("knowns")),
                unknowns=_normalize_list(brief.get("unknowns")),
                constraints=_normalize_list(brief.get("constraints")),
                evidence_requirements=_normalize_list(brief.get("evidence_requirements")),
                risk_labels=_normalize_list(brief.get("risk_labels")),
                boundary_requirements=_normalize_list(brief.get("boundary_requirements")),
                privacy_requirements=_normalize_list(brief.get("privacy_requirements")),
                safety_requirements=_normalize_list(brief.get("safety_requirements")),
                legal_requirements=_normalize_list(brief.get("legal_requirements")),
                medical_claim_boundaries=_normalize_list(brief.get("medical_claim_boundaries")),
                success_criteria=_normalize_list(brief.get("success_criteria")),
                validation_requirements=_normalize_list(brief.get("validation_requirements")),
                first_milestone=_safe_text(brief.get("first_milestone")),
                recommended_next_artifact=_safe_text(brief.get("recommended_next_artifact")),
                architecture_planning_required=bool(brief.get("architecture_planning_required")),
                stack_decision_required=bool(brief.get("stack_decision_required")),
                file_manifest_required=bool(brief.get("file_manifest_required")),
                code_generation_allowed=bool(brief.get("code_generation_allowed")),
                file_write_authority_granted=bool(brief.get("file_write_authority_granted")),
                prototype_allowed_level=_safe_text(brief.get("prototype_allowed_level")),
                behavior_pack_candidate_labels=_safe_label_list(brief.get("behavior_pack_candidate_labels")),
                friction_capture_triggers=_normalize_list(brief.get("friction_capture_triggers")),
                public_claim_allowed=bool(brief.get("public_claim_allowed")),
                iss_internal_reference_allowed=bool(brief.get("iss_internal_reference_allowed")),
                learning_claimed=bool(brief.get("learning_claimed")),
                runtime_authority=bool(brief.get("runtime_authority")),
                writes_state=bool(brief.get("writes_state")),
                model_provider_used=bool(brief.get("model_provider_used")),
                safe_metadata=dict(brief.get("safe_metadata") or {}),
            )
    return ProjectBriefSummary(
        summary_type=SUMMARY_TYPE_V1,
        brief_id=brief.brief_id,
        brief_type=brief.brief_type,
        project_stage=brief.project_stage,
        recommended_next_artifact=brief.recommended_next_artifact,
        domain_family=brief.domain_family,
        owner_intent=brief.owner_intent,
        evidence_requirement_count=len(brief.evidence_requirements),
        risk_label_count=len(brief.risk_labels),
        validation_requirement_count=len(brief.validation_requirements),
    )



def to_project_brief_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


# ---------------------------------------------------------------------------
# Seed examples
# ---------------------------------------------------------------------------


def build_initial_project_brief_examples_v1() -> tuple[ProjectBrief, ...]:
    from weslr.broad_topic_domain_intake import build_broad_topic_domain_intake_v1
    from weslr.privacy_sensitive_technology_boundary import build_privacy_sensitive_technology_boundary_v1

    example_specs = [
        {
            "name": "wifi_rf_self_care_project_brief",
            "safe_topic_descriptor": "WiFi/RF sensing for consent-based self-care in a household",
            "prompt_labels": ("wifi sensing", "self-care", "privacy", "consent"),
            "owner_intent_labels": ("research",),
            "risk_hints": ("high risk", "privacy-sensitive", "consent required", "lawful only"),
            "known_unknown_hints": ("unfamiliar", "researchable"),
            "boundary": True,
        },
        {
            "name": "metamaterials_research_project_brief",
            "safe_topic_descriptor": "Metamaterials frontier research",
            "prompt_labels": ("metamaterials", "materials discovery", "frontier research", "experimental validation"),
            "owner_intent_labels": ("evaluate feasibility",),
            "risk_hints": ("high uncertainty",),
            "known_unknown_hints": ("frontier", "high uncertainty"),
        },
        {
            "name": "ai_agent_architecture_project_brief",
            "safe_topic_descriptor": "AI agent architecture and governance",
            "prompt_labels": ("ai systems", "agentic systems", "cognitive architecture", "ai safety governance"),
            "owner_intent_labels": ("research",),
            "risk_hints": ("public-facing sensitivity", "safety critical"),
            "known_unknown_hints": ("adjacent",),
        },
        {
            "name": "medical_software_pathway_project_brief",
            "safe_topic_descriptor": "Medical software regulated pathway",
            "prompt_labels": ("medicine health research", "software product", "clinical validation"),
            "owner_intent_labels": ("evaluate feasibility",),
            "risk_hints": ("medical sensitive", "regulated domain"),
            "known_unknown_hints": ("unfamiliar",),
        },
        {
            "name": "industrial_automation_project_brief",
            "safe_topic_descriptor": "Industrial automation troubleshooting for a control system",
            "prompt_labels": ("industrial automation", "troubleshooting", "PLC", "equipment"),
            "owner_intent_labels": ("troubleshooting",),
            "risk_hints": ("equipment safety",),
            "known_unknown_hints": ("adjacent",),
        },
        {
            "name": "software_product_project_brief",
            "safe_topic_descriptor": "Software product planning for an owner-facing feature",
            "prompt_labels": ("software product", "product strategy", "feature planning"),
            "owner_intent_labels": ("commercial product strategy",),
            "risk_hints": ("medium uncertainty",),
            "known_unknown_hints": ("known existing pack",),
        },
        {
            "name": "theory_of_mind_conceptual_project_brief",
            "safe_topic_descriptor": "Theory of mind conceptual research",
            "prompt_labels": ("theory of mind", "philosophy of mind", "cognitive science"),
            "owner_intent_labels": ("learn explain",),
            "risk_hints": ("high uncertainty",),
            "known_unknown_hints": ("high uncertainty",),
        },
        {
            "name": "unknown_domain_project_brief",
            "safe_topic_descriptor": "Unknown future topic",
            "prompt_labels": ("unknown", "novel"),
            "owner_intent_labels": ("unknown",),
            "risk_hints": ("high uncertainty",),
            "known_unknown_hints": ("high uncertainty",),
        },
    ]

    briefs: list[ProjectBrief] = []
    for spec in example_specs:
        intake = build_broad_topic_domain_intake_v1(
            safe_topic_descriptor=spec["safe_topic_descriptor"],
            prompt_labels=spec["prompt_labels"],
            owner_intent_labels=spec["owner_intent_labels"],
            risk_hints=spec["risk_hints"],
            known_unknown_hints=spec["known_unknown_hints"],
            existing_behavior_pack_refs=(),
        )
        plan = build_research_conversation_plan_v1(domain_intake=intake)
        boundary = None
        if spec.get("boundary"):
            boundary = build_privacy_sensitive_technology_boundary_v1(domain_intake=intake, research_plan=plan)
        briefs.append(build_project_brief_v1(plan, boundary=boundary, domain_intake=intake))
    return tuple(briefs)


# Backwards-compatible aliases.
build_project_brief = build_project_brief_v1
build_project_brief_from_research_plan = build_project_brief_from_research_plan_v1
validate_project_brief = validate_project_brief_v1
summarize_project_brief = summarize_project_brief_v1
to_project_brief_json_safe = to_project_brief_json_safe_v1
build_initial_project_brief_examples = build_initial_project_brief_examples_v1
