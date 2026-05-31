"""Metadata-only research conversation planner v1.

This module turns a broad-topic domain intake packet into a safe research /
development conversation plan.

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
    build_broad_topic_domain_intake_v1,
    build_initial_broad_topic_domain_intake_examples_v1,
    classify_broad_topic_domain_v1,
    validate_broad_topic_domain_intake_v1,
)
from weslr.broad_topic_ontology import build_broad_topic_ontology_packet_v1

HELPER_TYPE_V1 = "research_conversation_planner_helper_v1"
PLAN_TYPE_V1 = "research_conversation_plan_v1"
SUMMARY_TYPE_V1 = "research_conversation_plan_summary_v1"

ALLOWED_PLAN_TYPES_V1 = {
    "explain_topic",
    "map_research_questions",
    "feasibility_review",
    "prototype_path_high_level",
    "evidence_collection_plan",
    "risk_boundary_review",
    "product_development_plan",
    "troubleshooting_plan",
    "behavior_pack_seed_plan",
    "clarifying_intake_plan",
}

ALLOWED_RESPONSE_MODES_V1 = {
    "direct_bounded_overview",
    "research_plan",
    "prototype_path_high_level",
    "evidence_request",
    "clarifying_question",
    "refusal_boundary",
    "behavior_pack_candidate",
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
    "unsafe deployment",
    "covert tracking",
    "covert deployment",
)

CLAIM_BASE_TERMS_V1 = {"agi", "consciousness", "sentience", "turing", "certification"}
CLAIM_QUALIFIERS_V1 = {"claim", "claims", "claimed", "official", "certification", "certified", "public", "readiness"}
UNSAFE_DEPLOYMENT_TERMS_V1 = {"covert", "deploy", "deployment", "track", "tracking", "evade", "bypass", "surveillance"}
CONSENT_TERMS_V1 = {"consent", "consented", "lawful", "lawfully", "authorized", "permission", "ethical", "ethically", "approved", "opt in", "opt-in"}
PRIVACY_BOUNDARY_TERMS_V1 = {"privacy", "surveillance", "tracking", "biometric", "location", "monitoring", "human sensing", "rf", "wifi"}
SAFETY_BOUNDARY_TERMS_V1 = {"safety", "electrical", "grid", "battery", "power", "control", "hardware", "equipment", "robot", "robotics", "fault"}
ONTOLOGY_PLAN_FIELD_NAMES_V1 = (
    "ontology_packet_id",
    "ontology_meta_domains",
    "ontology_domain_families",
    "ontology_subdomain_traits",
    "ontology_objects_of_study",
    "ontology_evidence_classes",
    "ontology_risk_classes",
    "ontology_sensitivity_classes",
    "ontology_response_route_family",
    "ontology_behavior_pack_candidate_labels",
)

class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ResearchConversationPlan:
    plan_id: str
    source_intake_id: str
    domain_family: str
    novelty_level: str
    owner_intent: str
    plan_type: str
    knowns: tuple[str, ...]
    unknowns: tuple[str, ...]
    assumptions: tuple[str, ...]
    evidence_needed: tuple[str, ...]
    safe_next_steps: tuple[str, ...]
    owner_questions: tuple[str, ...]
    boundary_warnings: tuple[str, ...]
    prototype_phase_outline: tuple[str, ...]
    friction_capture_triggers: tuple[str, ...]
    recommended_response_mode: str
    requires_boundary_review: bool
    requires_evidence_mapping: bool
    prototype_planning_allowed: bool
    behavior_pack_seed_candidate: bool
    public_claim_allowed: bool
    iss_internal_reference_allowed: bool
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    ontology_packet_id: str = ""
    ontology_meta_domains: tuple[str, ...] = ()
    ontology_domain_families: tuple[str, ...] = ()
    ontology_subdomain_traits: tuple[str, ...] = ()
    ontology_objects_of_study: tuple[str, ...] = ()
    ontology_evidence_classes: tuple[str, ...] = ()
    ontology_risk_classes: tuple[str, ...] = ()
    ontology_sensitivity_classes: tuple[str, ...] = ()
    ontology_response_route_family: str = ""
    ontology_behavior_pack_candidate_labels: tuple[str, ...] = ()
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ResearchConversationPlanSummary:
    summary_type: str
    plan_id: str
    domain_family: str
    plan_type: str
    novelty_level: str
    owner_intent: str
    recommended_response_mode: str
    requires_boundary_review: bool
    requires_evidence_mapping: bool
    prototype_planning_allowed: bool
    boundary_warning_count: int
    evidence_item_count: int


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



def _normalize_sequence(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
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



def _intake_ontology_snapshot(intake: Any) -> dict[str, Any]:
    def _seq(name: str) -> tuple[str, ...]:
        return _normalize_sequence(getattr(intake, name, ()))

    snapshot = {
        "ontology_packet_id": _safe_text(getattr(intake, "ontology_packet_id", "")),
        "ontology_meta_domains": _seq("ontology_meta_domains"),
        "ontology_domain_families": _seq("ontology_domain_families"),
        "ontology_subdomain_traits": _seq("ontology_subdomain_traits"),
        "ontology_objects_of_study": _seq("ontology_objects_of_study"),
        "ontology_evidence_classes": _seq("ontology_evidence_classes"),
        "ontology_risk_classes": _seq("ontology_risk_classes"),
        "ontology_sensitivity_classes": _seq("ontology_sensitivity_classes"),
        "ontology_response_route_family": _safe_text(getattr(intake, "ontology_response_route_family", "")),
        "ontology_behavior_pack_candidate_labels": _seq("ontology_behavior_pack_candidate_labels"),
    }
    if snapshot["ontology_packet_id"] or any(snapshot[name] for name in ONTOLOGY_PLAN_FIELD_NAMES_V1 if name != "ontology_packet_id"):
        return snapshot

    safe_metadata = getattr(intake, "safe_metadata", None)
    if isinstance(safe_metadata, Mapping):
        ontology = safe_metadata.get("ontology")
        packet = ontology.get("packet") if isinstance(ontology, Mapping) else None
        source = ontology if isinstance(ontology, Mapping) else packet if isinstance(packet, Mapping) else None
        if isinstance(source, Mapping):
            snapshot = {
                "ontology_packet_id": _safe_text(source.get("ontology_id") or source.get("ontology_packet_id")),
                "ontology_meta_domains": _normalize_sequence(source.get("meta_domains")),
                "ontology_domain_families": _normalize_sequence(source.get("domain_families")),
                "ontology_subdomain_traits": _normalize_sequence(source.get("subdomain_traits")),
                "ontology_objects_of_study": _normalize_sequence(source.get("objects_of_study")),
                "ontology_evidence_classes": _normalize_sequence(source.get("evidence_classes")),
                "ontology_risk_classes": _normalize_sequence(source.get("risk_classes")),
                "ontology_sensitivity_classes": _normalize_sequence(source.get("sensitivity_classes")),
                "ontology_response_route_family": _safe_text(source.get("response_route_family")),
                "ontology_behavior_pack_candidate_labels": _normalize_sequence(source.get("behavior_pack_candidate_labels")),
            }
    return snapshot



def _collect_forbidden_fields(value: Any, path: str = "") -> list[str]:
    blocked: list[str] = []
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _safe_text(key).lower()
            next_path = f"{path}.{key_text}" if path else key_text
            if key_text in FORBIDDEN_FIELD_NAMES_V1:
                blocked.append(next_path)
            blocked.extend(_collect_forbidden_fields(item, next_path))
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            blocked.extend(_collect_forbidden_fields(item, f"{path}[{index}]"))
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
        if has_base and has_qualifier:
            return True
        return False
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



def _contains_unsafe_deployment_marker_in_guidance(plan: Any) -> bool:
    if is_dataclass(plan):
        source = asdict(plan)
    elif isinstance(plan, Mapping):
        source = dict(plan)
    else:
        return _contains_unsafe_deployment_marker(plan)
    guidance_keys = (
        "safe_next_steps",
        "prototype_phase_outline",
        "owner_questions",
        "boundary_warnings",
        "evidence_needed",
        "assumptions",
        "knowns",
        "unknowns",
        "friction_capture_triggers",
        "recommended_response_mode",
        "plan_type",
    )
    return any(_contains_unsafe_deployment_marker(source.get(key)) for key in guidance_keys)



def _has_token(blob: str, terms: Iterable[str]) -> bool:
    text = _normalize_text(blob)
    return any(_normalize_text(term) in text for term in terms)



def _plan_id(source_intake_id: str, plan_type: str, domain_family: str) -> str:
    slug = _normalize_text(f"{source_intake_id} {plan_type} {domain_family}").replace("/", " ").replace("-", " ")
    slug = "_".join(tok for tok in slug.split() if tok)[:96]
    return f"research_conversation_plan_{slug or 'plan'}"



def _safe_metadata(
    intake: BroadTopicDomainIntake,
    plan_type: str,
    response_mode: str,
    behavior_pack_seed_candidate: bool,
) -> dict[str, Any]:
    return {
        "source": "research_conversation_planner_v1",
        "source_intake_id": intake.intake_id,
        "domain_family": intake.domain_family,
        "novelty_level": intake.novelty_level,
        "owner_intent": intake.owner_intent,
        "plan_type": plan_type,
        "recommended_response_mode": response_mode,
        "behavior_pack_seed_candidate": behavior_pack_seed_candidate,
    }


# ---------------------------------------------------------------------------
# Ontology helpers
# ---------------------------------------------------------------------------


def _ontology_context(intake: BroadTopicDomainIntake) -> dict[str, Any]:
    return {
        "ontology_packet_id": _safe_text(getattr(intake, "ontology_packet_id", "")),
        "ontology_meta_domains": _normalize_sequence(getattr(intake, "ontology_meta_domains", ())),
        "ontology_domain_families": _normalize_sequence(getattr(intake, "ontology_domain_families", ())),
        "ontology_subdomain_traits": _normalize_sequence(getattr(intake, "ontology_subdomain_traits", ())),
        "ontology_objects_of_study": _normalize_sequence(getattr(intake, "ontology_objects_of_study", ())),
        "ontology_evidence_classes": _normalize_sequence(getattr(intake, "ontology_evidence_classes", ())),
        "ontology_risk_classes": _normalize_sequence(getattr(intake, "ontology_risk_classes", ())),
        "ontology_sensitivity_classes": _normalize_sequence(getattr(intake, "ontology_sensitivity_classes", ())),
        "ontology_response_route_family": _safe_text(getattr(intake, "ontology_response_route_family", "")),
        "ontology_behavior_pack_candidate_labels": _normalize_sequence(getattr(intake, "ontology_behavior_pack_candidate_labels", ())),
    }


# ---------------------------------------------------------------------------
# Domain-specific content
# ---------------------------------------------------------------------------


def _build_knowns_unknowns_assumptions(intake: BroadTopicDomainIntake) -> tuple[list[str], list[str], list[str]]:
    domain = intake.domain_family
    novelty = intake.novelty_level
    intent = intake.owner_intent
    ontology = _ontology_context(intake)
    ontology_families = set(ontology["ontology_domain_families"])

    if ontology_families & {"metamaterials", "materials_discovery", "physics", "chemistry"} or domain in {"metamaterials", "materials_discovery", "physics", "chemistry"}:
        knowns = (
            "topic is frontier materials or metamaterials research",
            "technical literature and validation criteria matter",
        )
        unknowns = (
            "target property or material class",
            "evidence gaps",
            "validation criteria and uncertainty bounds",
        )
        assumptions = (
            "high evidence need is appropriate",
            "feasibility is not established until validated",
        )
    elif ontology_families & {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"} or domain in {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"}:
        knowns = (
            "topic is theory of mind and conceptual mind and intelligence research",
            "definitions and distinctions matter",
        )
        unknowns = (
            "which conceptual distinction matters most",
            "how philosophy, cognitive science, neuroscience, and AI theory differ here",
            "which evidence gap should anchor the plan",
        )
        assumptions = (
            "strong claims should be avoided",
            "conceptual clarity comes before stronger conclusions",
        )
    elif ontology_families & {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"} or domain in {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"}:
        knowns = (
            "topic is AI or agent architecture work",
            "governance and evaluation context matter",
        )
        unknowns = (
            "system architecture",
            "safety and governance questions",
            "evaluation criteria and operational constraints",
        )
        assumptions = (
            "architecture should stay evidence-based",
            "external certainty should stay bounded",
        )
    elif ontology_families & {"medicine_health_research", "biology_life_sciences"} or domain == "medicine_health_research":
        knowns = (
            "topic is health or clinical-adjacent research",
            "validation and regulatory context matter",
        )
        unknowns = (
            "intended use boundary",
            "clinical and regulatory evidence needs",
            "safety constraints and misuse risk",
        )
        assumptions = (
            "diagnostic or treatment authority should not be implied",
            "boundary review comes first",
        )
    elif domain == "privacy_sensitive_technology":
        knowns = (
            "topic is privacy-sensitive technology research",
            "boundary review is required before any stronger claim",
        )
        unknowns = (
            "whether use is consent-based and lawful",
            "what evidence exists for the sensing approach",
            "whether the use case is research only or real-world oriented",
        )
        assumptions = (
            "current knowledge is insufficient for certainty",
            "non-consensual sensing is not an acceptable default",
        )
    elif domain == "industrial_automation":
        knowns = (
            "topic is industrial automation",
            "device, control, and fault context matter",
        )
        unknowns = (
            "device specs and configuration",
            "current fault state or symptom",
            "operator constraints and safety context",
        )
        assumptions = (
            "equipment behavior should be treated as safety-sensitive when control or hardware labels appear",
            "troubleshooting should start from the current observable state",
        )
    elif domain == "legal_privacy":
        knowns = (
            "topic involves legal or privacy review",
            "certainty should stay bounded",
        )
        unknowns = (
            "jurisdiction, policy scope, and compliance context",
            "whether the question is informational or decision-critical",
        )
        assumptions = (
            "no legal certainty should be implied",
            "sources and jurisdiction matter before stronger conclusions",
        )
    elif domain == "energy_systems":
        knowns = (
            "topic is energy systems",
            "safety and electrical context may matter",
        )
        unknowns = (
            "battery, inverter, grid, or power constraints",
            "prototype scope or feasibility target",
            "safety envelope and failure modes",
        )
        assumptions = (
            "prototype planning must remain high-level when risk is unclear",
            "safety review may be required before deeper steps",
        )
    elif domain == "robotics":
        knowns = (
            "topic is robotics",
            "physical safety and prototype limits matter",
        )
        unknowns = (
            "actuation, sensing, and motion constraints",
            "validation environment",
            "risk envelope",
        )
        assumptions = (
            "prototype guidance should stay high-level unless context is clear",
            "safety review may be needed before implementation detail",
        )
    elif domain in {"software_product", "website_public_launch"}:
        knowns = (
            "topic is software or product planning",
            "owner goals and launch state matter",
        )
        unknowns = (
            "target audience",
            "constraints and launch stage",
            "scope and success criteria",
        )
        assumptions = (
            "product planning should stay grounded in evidence and goals",
            "prototype scope should be constrained",
        )
    elif domain == "language_vocabulary":
        knowns = (
            "topic is language or vocabulary exploration",
            "bounded explanation is often sufficient",
        )
        unknowns = (
            "exact term usage context",
            "whether a deeper research path is needed",
        )
        assumptions = (
            "a direct bounded overview is usually safe",
            "a research question path is only needed if the term is unclear or novel",
        )
    elif domain == "owner_workflow":
        knowns = (
            "topic concerns owner workflow or WESLR process",
            "metadata-only planning is appropriate",
        )
        unknowns = (
            "which workflow bottleneck is being addressed",
            "whether repeated friction is present",
            "what pack candidate or proof gap exists",
        )
        assumptions = (
            "behavior-pack candidate formation may be relevant",
            "no external wording or runtime authority should be implied",
        )
    else:
        knowns = ("topic family is unknown",)
        unknowns = (
            "what domain the topic belongs to",
            "what the owner wants to achieve",
            "what evidence or constraints matter",
        )
        assumptions = (
            "clarification is required before stronger planning",
            "no domain expertise should be pretended",
        )

    if novelty == "high_uncertainty":
        unknowns = unknowns + ("novelty is high and should be treated as an intake problem",)
    if intent == "unknown_intent":
        unknowns = unknowns + ("owner intent needs clarification",)
    return list(knowns), _dedupe_preserve(unknowns), list(assumptions)

def _boundary_warnings(intake: BroadTopicDomainIntake) -> list[str]:
    warnings: list[str] = []
    ontology = _ontology_context(intake)
    ontology_families = set(ontology["ontology_domain_families"])
    ontology_traits = set(ontology["ontology_subdomain_traits"])
    ontology_risks = set(ontology["ontology_risk_classes"])
    ontology_sensitivity = set(ontology["ontology_sensitivity_classes"])
    blob = " ".join((intake.safe_topic_descriptor, intake.domain_family, intake.owner_intent, intake.novelty_level, " ".join(intake.risk_labels), intake.recommended_next_stage, " ".join(ontology_families), " ".join(ontology_traits), " ".join(ontology_risks), " ".join(ontology_sensitivity)))
    if ontology_families & {"privacy_sensitive_technology"} or intake.domain_family == "privacy_sensitive_technology":
        warnings.extend(("privacy review required", "privacy misuse risk", "non-consensual rollout guidance is forbidden", "consent and lawfulness must be clarified before deeper steps"))
    if ontology_families & {"legal_privacy", "policy_governance"} or intake.domain_family == "legal_privacy":
        warnings.extend(("no legal certainty claim", "jurisdiction and policy context matter", "evidence mapping is required before stronger conclusions"))
    if ontology_families & {"industrial_automation"} or intake.domain_family == "industrial_automation":
        warnings.append("equipment, control, and hardware context may be safety-sensitive")
    if ontology_families & {"metamaterials", "materials_discovery", "physics", "chemistry"} or intake.domain_family == "materials_discovery":
        warnings.append("validation criteria and uncertainty gaps must be explicit")
    if ontology_families & {"energy_systems"} or intake.domain_family == "energy_systems":
        warnings.append("battery, grid, power, and electrical safety context may be relevant")
    if ontology_families & {"robotics"} or intake.domain_family == "robotics":
        warnings.append("physical safety and failure modes should stay explicit")
    if ontology_families & {"software_product", "website_public_launch"} or intake.domain_family in {"software_product", "website_public_launch"}:
        warnings.append("product or launch scope should remain evidence grounded")
    if ontology_families & {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"}:
        warnings.append("keep distinctions between philosophy, cognitive science, neuroscience, and AI explicit")
    if ontology_families & {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"}:
        warnings.append("architecture and governance should stay bounded by evidence and evaluation")
    if ontology_families & {"medicine_health_research", "biology_life_sciences"} or intake.domain_family == "medicine_health_research":
        warnings.append("clinical and regulatory boundaries must be explicit")
    if ontology_families & {"unknown_domain"} or intake.domain_family == "unknown_domain":
        warnings.append("domain knowledge is insufficient for strong conclusions")
    if "blocked" in intake.risk_level or intake.novelty_level == "blocked_or_sensitive":
        warnings.append("boundary review is mandatory")
    if _has_token(blob, {"human sensing", "rf", "wifi"}) and intake.domain_family != "privacy_sensitive_technology":
        warnings.append("privacy review may still be required")
    if not warnings:
        warnings.append("keep the plan bounded and evidence-oriented")
    return _dedupe_preserve(warnings)

def _evidence_needed(intake: BroadTopicDomainIntake) -> list[str]:
    domain = intake.domain_family
    ontology = _ontology_context(intake)
    ontology_families = set(ontology["ontology_domain_families"])
    ontology_evidence = set(ontology["ontology_evidence_classes"])
    ontology_traits = set(ontology["ontology_subdomain_traits"])
    items: list[str] = []
    if ontology_families & {"privacy_sensitive_technology"} or domain == "privacy_sensitive_technology":
        items.extend(("consent and lawfulness context", "privacy boundary analysis", "technical literature or terminology", "prototype validation criteria"))
    elif ontology_families & {"industrial_automation"} or domain == "industrial_automation":
        items.extend(("device specs and configuration", "current fault or symptom context", "control or hardware boundaries", "safety constraints"))
    elif ontology_families & {"legal_privacy", "policy_governance"} or domain == "legal_privacy":
        items.extend(("jurisdiction or policy scope", "legal or privacy sources", "specific compliance question", "uncertainty gaps"))
    elif ontology_families & {"metamaterials", "materials_discovery", "physics", "chemistry"} or domain == "materials_discovery":
        items.extend(("technical literature", "experimental validation criteria", "uncertainty gaps", "definitions and terminology"))
    elif ontology_families & {"energy_systems"} or domain == "energy_systems":
        items.extend(("system constraints", "safety constraints", "hardware or software requirements", "validation criteria"))
    elif ontology_families & {"robotics"} or domain == "robotics":
        items.extend(("mechanical and control constraints", "safety constraints", "prototype validation criteria"))
    elif ontology_families & {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"}:
        items.extend(("system architecture questions", "evaluation criteria", "safety or governance boundaries", "implementation constraints"))
    elif ontology_families & {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"}:
        items.extend(("definitions and distinctions", "conceptual contrasts", "evidence gaps", "scope of the question"))
    elif ontology_families & {"medicine_health_research", "biology_life_sciences"} or domain == "medicine_health_research":
        items.extend(("clinical or regulatory scope", "safety constraints", "validation criteria", "intended use boundary"))
    elif ontology_families & {"software_product", "website_public_launch"} or domain in {"software_product", "website_public_launch"}:
        items.extend(("owner goals", "audience and launch state", "constraints", "prototype validation criteria"))
    elif domain == "language_vocabulary":
        items.extend(("term context", "definitions or terminology", "related usage examples"))
    elif domain == "owner_workflow":
        items.extend(("workflow bottleneck", "friction evidence", "pack references", "proof requirements"))
    else:
        items.extend(("domain definition", "unknowns", "evidence gaps"))
    if intake.evidence_need_level == "must_collect_before_claims" or "experimental_validation_needed" in ontology_evidence or "high_uncertainty" in ontology_traits:
        items.append("evidence must be collected before stronger conclusions")
    return _dedupe_preserve(items)

def _safe_next_steps(intake: BroadTopicDomainIntake, plan_type: str, response_mode: str) -> list[str]:
    domain = intake.domain_family
    ontology = _ontology_context(intake)
    ontology_families = set(ontology["ontology_domain_families"])
    ontology_traits = set(ontology["ontology_subdomain_traits"])
    ontology_route = ontology["ontology_response_route_family"]
    steps: list[str] = []
    if ontology_families & {"privacy_sensitive_technology"} or domain == "privacy_sensitive_technology":
        steps.extend(("confirm whether the use case is consent-based and lawful", "separate research exploration from rollout planning", "map privacy boundaries", "collect evidence before stronger conclusions"))
    elif ontology_families & {"industrial_automation"} or domain == "industrial_automation":
        steps.extend(("describe the current fault or operating symptom", "list device specs and control context", "separate troubleshooting from safety validation"))
    elif ontology_families & {"legal_privacy", "policy_governance"} or domain == "legal_privacy":
        steps.extend(("define the jurisdiction or policy scope", "collect legal or privacy sources", "separate informational review from decision-making"))
    elif ontology_families & {"metamaterials", "materials_discovery", "physics", "chemistry"} or domain == "materials_discovery":
        steps.extend(("define the target property or material class", "list evidence gaps", "set validation criteria", "choose a research question path"))
    elif ontology_families & {"energy_systems"} or domain == "energy_systems":
        steps.extend(("define the use case and constraints", "review safety and electrical boundaries", "choose a high-level feasibility path"))
    elif ontology_families & {"robotics"} or domain == "robotics":
        steps.extend(("define the robot task and environment", "review safety and motion constraints", "keep prototype guidance high-level"))
    elif ontology_families & {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"}:
        steps.extend(("map architecture and evaluation questions", "define governance constraints", "keep the plan evidence-oriented"))
    elif ontology_families & {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"}:
        steps.extend(("define the theory of mind conceptual question", "separate philosophy, science, and AI angles", "identify evidence gaps and terminology"))
    elif ontology_families & {"medicine_health_research", "biology_life_sciences"} or domain == "medicine_health_research":
        steps.extend(("define the intended use boundary", "review regulatory and safety evidence needs", "keep health conclusions non-authoritative"))
    elif ontology_families & {"software_product", "website_public_launch"} or domain in {"software_product", "website_public_launch"}:
        steps.extend(("define the owner goal and audience", "capture constraints and launch state", "choose a product or prototype path"))
    elif domain == "language_vocabulary":
        steps.extend(("give a bounded explanation", "ask for the exact term or context if needed"))
    elif domain == "owner_workflow":
        steps.extend(("identify the workflow friction point", "capture repeated failure evidence", "seed a behavior-pack candidate if the issue repeats"))
    else:
        steps.extend(("ask for one focused clarification", "capture the unknowns explicitly", "avoid pretending domain certainty"))

    if plan_type == "clarifying_intake_plan" or response_mode == "clarifying_question":
        steps.insert(0, "ask one focused intake question")
    if response_mode == "behavior_pack_candidate":
        steps.append("preserve metadata for candidate pack review")
    if response_mode == "evidence_request":
        steps.append("ask for evidence before stronger conclusions")
    if response_mode == "prototype_path_high_level" and not intake.prototype_planning_allowed:
        steps.append("keep prototype discussion high-level only")
    if ontology_route == "conceptual_theory_path":
        steps.append("keep the explanation conceptual and bounded")
    if ontology_route == "privacy_safety_legal_boundary_review":
        steps.append("treat boundary review as a prerequisite before deeper planning")
    return _dedupe_preserve(steps)

def _owner_questions(intake: BroadTopicDomainIntake) -> list[str]:
    domain = intake.domain_family
    ontology = _ontology_context(intake)
    ontology_families = set(ontology["ontology_domain_families"])
    if ontology_families & {"privacy_sensitive_technology"} or domain == "privacy_sensitive_technology":
        return [
            "Is the sensing use case consent-based and lawful?",
            "Is this research only, or are you considering rollout?",
        ]
    if ontology_families & {"industrial_automation"} or domain == "industrial_automation":
        return [
            "What device, controller, or control system is involved?",
            "What symptom, fault, or configuration detail should we anchor on?",
        ]
    if ontology_families & {"legal_privacy", "policy_governance"} or domain == "legal_privacy":
        return [
            "What jurisdiction or policy scope applies?",
            "Is this informational review or a decision-critical legal or privacy question?",
        ]
    if ontology_families & {"metamaterials", "materials_discovery", "physics", "chemistry"} or domain == "materials_discovery":
        return [
            "What material class or target property are you exploring?",
            "What validation criterion would count as success?",
        ]
    if ontology_families & {"energy_systems"} or domain == "energy_systems":
        return [
            "What system boundary matters most—battery, grid, inverter, or power path?",
            "Is the goal feasibility review or a high-level prototype path?",
        ]
    if ontology_families & {"robotics"} or domain == "robotics":
        return [
            "What task and environment is the robot supposed to handle?",
            "What safety constraint matters most?",
        ]
    if ontology_families & {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"}:
        return [
            "What architecture question or system boundary matters most?",
            "What evaluation or governance constraint should shape the plan?",
        ]
    if ontology_families & {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"}:
        return [
            "Which conceptual distinction or research question matters most?",
            "Do you want a conceptual overview or a research-question map?",
        ]
    if ontology_families & {"medicine_health_research", "biology_life_sciences"} or domain == "medicine_health_research":
        return [
            "What intended use boundary should we respect?",
            "What validation or regulatory evidence matters most?",
        ]
    if ontology_families & {"software_product", "website_public_launch"} or domain in {"software_product", "website_public_launch"}:
        return [
            "What is the owner goal and target audience?",
            "What constraints or launch state should we plan around?",
        ]
    if domain == "language_vocabulary":
        return [
            "What is the exact term or phrase?",
            "Do you want a direct explanation or a deeper research path?",
        ]
    if domain == "owner_workflow":
        return [
            "Which workflow friction point should we solve first?",
            "Is this a repeated issue that should seed a behavior-pack candidate?",
        ]
    return ["What domain are we in, and what outcome do you want?"]

def _prototype_outline(intake: BroadTopicDomainIntake, allowed: bool, plan_type: str) -> list[str]:
    if not allowed:
        return ["prototype detail is deferred until intake allows it"]
    domain = intake.domain_family
    ontology = _ontology_context(intake)
    ontology_families = set(ontology["ontology_domain_families"])
    if ontology_families & {"privacy_sensitive_technology"} or domain == "privacy_sensitive_technology":
        return [
            "define a lawful and consent-based use case",
            "collect evidence and boundary constraints",
            "choose a toy or synthetic test environment",
            "validate limitations and failure modes",
        ]
    if ontology_families & {"industrial_automation", "energy_systems", "robotics"} or domain in {"industrial_automation", "energy_systems", "robotics"}:
        return [
            "define the scope and constraints",
            "choose a safe high-level prototype environment",
            "validate failure modes and safety limits",
            "review whether to continue",
        ]
    if ontology_families & {"software_product", "website_public_launch"} or domain in {"software_product", "website_public_launch"}:
        return [
            "define user goal and scope",
            "pick a small prototype slice",
            "validate launch constraints and evidence needs",
            "decide whether to continue",
        ]
    if ontology_families & {"metamaterials", "materials_discovery", "physics", "chemistry"} or domain == "materials_discovery":
        return [
            "define the material target or property",
            "select literature and validation criteria",
            "keep prototype discussion at feasibility level",
            "test uncertainty bounds before implementation detail",
        ]
    if ontology_families & {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"}:
        return [
            "define the architecture scope",
            "map evaluation and governance constraints",
            "keep prototype detail high level",
            "review safety limits before implementation detail",
        ]
    if ontology_families & {"medicine_health_research", "biology_life_sciences"} or domain == "medicine_health_research":
        return [
            "define the intended use boundary",
            "keep health review high level",
            "validate regulatory and safety constraints before detail",
            "avoid diagnosis or treatment authority",
        ]
    return ()

def _friction_triggers(intake: BroadTopicDomainIntake) -> list[str]:
    triggers = [
        "novel domain or unfamiliar terms",
        "missing evidence or unclear conclusions",
        "boundary ambiguity",
        "prototype detail requested without sufficient context",
    ]
    ontology = _ontology_context(intake)
    ontology_families = set(ontology["ontology_domain_families"])
    ontology_traits = set(ontology["ontology_subdomain_traits"])
    if ontology_families & {"privacy_sensitive_technology"} or intake.domain_family == "privacy_sensitive_technology":
        triggers.append("consent or lawfulness not yet established")
    if ontology_families & {"industrial_automation"} or intake.domain_family == "industrial_automation":
        triggers.append("device specs or current fault context missing")
    if ontology_families & {"legal_privacy", "policy_governance"} or intake.domain_family == "legal_privacy":
        triggers.append("jurisdiction or policy scope missing")
    if ontology_families & {"metamaterials", "materials_discovery", "physics", "chemistry"} or intake.domain_family == "materials_discovery":
        triggers.append("validation criteria or uncertainty gaps missing")
    if ontology_families & {"energy_systems"} or intake.domain_family == "energy_systems":
        triggers.append("safety or electrical constraints missing")
    if ontology_families & {"robotics"} or intake.domain_family == "robotics":
        triggers.append("motion or failure-mode safety missing")
    if ontology_families & {"software_product", "website_public_launch"} or intake.domain_family in {"software_product", "website_public_launch"}:
        triggers.append("audience, launch state, or scope missing")
    if ontology_families & {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"}:
        triggers.append("architecture or evaluation constraints missing")
    if ontology_families & {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"}:
        triggers.append("conceptual distinctions or evidence gaps missing")
    if ontology_families & {"medicine_health_research", "biology_life_sciences"} or intake.domain_family == "medicine_health_research":
        triggers.append("regulatory or safety evidence missing")
    if ontology_families & {"unknown_domain"} or intake.domain_family == "unknown_domain" or "high_uncertainty" in ontology_traits:
        triggers.append("clarification or evidence mapping needed")
    if intake.domain_family == "owner_workflow":
        triggers.append("repeated friction or pack-candidate evidence present")
    return _dedupe_preserve(triggers)

def _plan_type_and_mode(intake: BroadTopicDomainIntake) -> tuple[str, str, bool, bool, bool, bool]:
    family = intake.domain_family
    intent = intake.owner_intent
    novelty = intake.novelty_level
    allowed_proto = intake.prototype_planning_allowed
    ontology = _ontology_context(intake)
    ontology_families = set(ontology["ontology_domain_families"])
    ontology_traits = set(ontology["ontology_subdomain_traits"])
    ontology_evidence = set(ontology["ontology_evidence_classes"])
    ontology_risk = set(ontology["ontology_risk_classes"])
    ontology_sensitivity = set(ontology["ontology_sensitivity_classes"])
    ontology_route = ontology["ontology_response_route_family"]
    has_consent = _has_token(intake.safe_topic_descriptor, CONSENT_TERMS_V1) or any(_has_token(label, CONSENT_TERMS_V1) for label in intake.candidate_behavior_pack_labels)

    if ontology_families & {"medicine_health_research", "biology_life_sciences"} or family == "medicine_health_research":
        plan_type = "risk_boundary_review" if intent in {"evaluate_feasibility", "research", "build_prototype"} or "medical_or_health_sensitive" in ontology_sensitivity else "evidence_collection_plan"
        mode = "evidence_request"
        return plan_type, mode, True, True, False, False

    if ontology_families & {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"} or family in {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"}:
        plan_type = "explain_topic" if intent == "learn_explain" else "map_research_questions"
        mode = "direct_bounded_overview" if plan_type == "explain_topic" else "research_plan"
        requires_boundary_review = "public_claim_sensitive" in ontology_risk or "public_claim_sensitive" in ontology_sensitivity
        return plan_type, mode, requires_boundary_review, True, False, False

    if ontology_families & {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"} or family in {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"}:
        plan_type = "feasibility_review" if intent in {"build_prototype", "evaluate_feasibility"} else "map_research_questions"
        return plan_type, "research_plan", True, True, allowed_proto, False

    if ontology_families & {"metamaterials", "materials_discovery", "physics", "chemistry"} or family in {"metamaterials", "materials_discovery", "physics", "chemistry"}:
        plan_type = "feasibility_review" if intent == "evaluate_feasibility" or "experimental_validation_needed" in ontology_evidence or "frontier_research" in ontology_traits else "map_research_questions"
        mode = "evidence_request" if "experimental_validation_needed" in ontology_evidence or novelty in {"high_uncertainty", "adjacent_to_existing_pack"} else "research_plan"
        requires_boundary_review = novelty in {"high_uncertainty", "blocked_or_sensitive"} or "unknown_risk" in ontology_risk
        return plan_type, mode, requires_boundary_review, True, allowed_proto and plan_type == "feasibility_review", False

    if ontology_families & {"privacy_sensitive_technology"} or family == "privacy_sensitive_technology":
        plan_type = "risk_boundary_review" if novelty in {"high_uncertainty", "blocked_or_sensitive"} or intake.boundary_review_required else "map_research_questions"
        if has_consent and allowed_proto and intent in {"research", "build_prototype", "evaluate_feasibility"}:
            plan_type = "map_research_questions"
        mode = "refusal_boundary" if not has_consent else "research_plan"
        return plan_type, mode, True, True, allowed_proto and has_consent, False

    if ontology_families & {"industrial_automation"} or family == "industrial_automation":
        plan_type = "troubleshooting_plan" if intent == "troubleshooting" else "feasibility_review"
        return plan_type, "research_plan", False, True, allowed_proto, False

    if ontology_families & {"legal_privacy", "policy_governance"} or family == "legal_privacy":
        plan_type = "risk_boundary_review" if intent == "safety_legal_privacy_review" else "evidence_collection_plan"
        mode = "evidence_request" if plan_type == "evidence_collection_plan" else "refusal_boundary"
        return plan_type, mode, True, True, False, False

    if ontology_families & {"energy_systems"} or family == "energy_systems":
        plan_type = "prototype_path_high_level" if intent == "build_prototype" and allowed_proto else "feasibility_review"
        mode = "prototype_path_high_level" if plan_type == "prototype_path_high_level" else "research_plan"
        return plan_type, mode, False, True, allowed_proto, False

    if ontology_families & {"robotics"} or family == "robotics":
        plan_type = "prototype_path_high_level" if intent == "build_prototype" and allowed_proto else "feasibility_review"
        mode = "prototype_path_high_level" if plan_type == "prototype_path_high_level" else "research_plan"
        return plan_type, mode, False, True, allowed_proto, False

    if ontology_families & {"software_product", "website_public_launch", "economics_business_strategy"} or family in {"software_product", "website_public_launch"}:
        if "medicine_health_research" in ontology_families:
            return "risk_boundary_review", "evidence_request", True, True, False, False
        if "ai_systems" in ontology_families or "agentic_systems" in ontology_families:
            return "map_research_questions", "research_plan", True, True, allowed_proto, False
        plan_type = "product_development_plan" if intent == "commercial_product_strategy" else "prototype_path_high_level"
        mode = "research_plan" if plan_type == "product_development_plan" else "prototype_path_high_level"
        return plan_type, mode, False, True, allowed_proto, False

    if ontology_families & {"language_vocabulary", "education_learning", "creative_design"} or family == "language_vocabulary":
        plan_type = "explain_topic" if intent == "learn_explain" else "map_research_questions"
        mode = "direct_bounded_overview" if plan_type == "explain_topic" else "research_plan"
        return plan_type, mode, False, False, False, False

    if ontology_families & {"owner_workflow"} or family == "owner_workflow":
        behavior_pack_seed_candidate = bool(intake.candidate_behavior_pack_labels or ontology["ontology_behavior_pack_candidate_labels"])
        plan_type = "behavior_pack_seed_plan" if behavior_pack_seed_candidate else "clarifying_intake_plan"
        mode = "behavior_pack_candidate" if plan_type == "behavior_pack_seed_plan" else "clarifying_question"
        return plan_type, mode, False, True, False, behavior_pack_seed_candidate

    if ontology_families & {"unknown_domain"} or family == "unknown_domain":
        plan_type = "clarifying_intake_plan" if novelty == "high_uncertainty" else "evidence_collection_plan"
        mode = "clarifying_question" if plan_type == "clarifying_intake_plan" else "evidence_request"
        return plan_type, mode, True, True, False, False

    plan_type = "clarifying_intake_plan" if novelty == "high_uncertainty" else "evidence_collection_plan"
    mode = "clarifying_question" if plan_type == "clarifying_intake_plan" else "evidence_request"
    return plan_type, mode, True, True, False, False


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_research_conversation_plan_v1(*, domain_intake: BroadTopicDomainIntake | Mapping[str, Any]) -> ResearchConversationPlan:
    intake = domain_intake if isinstance(domain_intake, BroadTopicDomainIntake) else domain_intake
    if not isinstance(intake, BroadTopicDomainIntake):
        intake = BroadTopicDomainIntake(
            intake_id=_safe_text(intake.get("intake_id")),
            safe_topic_descriptor=_safe_text(intake.get("safe_topic_descriptor")),
            domain_family=_safe_text(intake.get("domain_family")),
            novelty_level=_safe_text(intake.get("novelty_level")),
            owner_intent=_safe_text(intake.get("owner_intent")),
            evidence_need_level=_safe_text(intake.get("evidence_need_level")),
            risk_level=_safe_text(intake.get("risk_level")),
            risk_labels=_normalize_sequence(intake.get("risk_labels")),
            recommended_next_stage=_safe_text(intake.get("recommended_next_stage")),
            candidate_behavior_pack_labels=_normalize_sequence(intake.get("candidate_behavior_pack_labels")),
            boundary_review_required=bool(intake.get("boundary_review_required")),
            evidence_mapping_required=bool(intake.get("evidence_mapping_required")),
            research_planning_required=bool(intake.get("research_planning_required")),
            prototype_planning_allowed=bool(intake.get("prototype_planning_allowed")),
            privacy_sensitive=bool(intake.get("privacy_sensitive")),
            safety_sensitive=bool(intake.get("safety_sensitive")),
            legal_sensitive=bool(intake.get("legal_sensitive")),
            public_claim_allowed=bool(intake.get("public_claim_allowed")),
            iss_internal_reference_allowed=bool(intake.get("iss_internal_reference_allowed")),
            learning_claimed=bool(intake.get("learning_claimed")),
            runtime_authority=bool(intake.get("runtime_authority")),
            writes_state=bool(intake.get("writes_state")),
            model_provider_used=bool(intake.get("model_provider_used")),
            ontology_packet_id=_safe_text(intake.get("ontology_packet_id")),
            ontology_meta_domains=_normalize_sequence(intake.get("ontology_meta_domains")),
            ontology_domain_families=_normalize_sequence(intake.get("ontology_domain_families")),
            ontology_subdomain_traits=_normalize_sequence(intake.get("ontology_subdomain_traits")),
            ontology_objects_of_study=_normalize_sequence(intake.get("ontology_objects_of_study")),
            ontology_evidence_classes=_normalize_sequence(intake.get("ontology_evidence_classes")),
            ontology_risk_classes=_normalize_sequence(intake.get("ontology_risk_classes")),
            ontology_sensitivity_classes=_normalize_sequence(intake.get("ontology_sensitivity_classes")),
            ontology_response_route_family=_safe_text(intake.get("ontology_response_route_family")),
            ontology_behavior_pack_candidate_labels=_normalize_sequence(intake.get("ontology_behavior_pack_candidate_labels")),
            safe_metadata=dict(intake.get("safe_metadata") or {}),
        )
    validate_broad_topic_domain_intake_v1(intake)
    plan_type, response_mode, requires_boundary_review, requires_evidence_mapping, prototype_allowed, behavior_pack_seed_candidate = _plan_type_and_mode(intake)
    knowns, unknowns, assumptions = _build_knowns_unknowns_assumptions(intake)
    evidence_needed = _evidence_needed(intake)
    boundary_warnings = _boundary_warnings(intake)
    safe_next_steps = _safe_next_steps(intake, plan_type, response_mode)
    owner_questions = _owner_questions(intake)
    prototype_phase_outline = _prototype_outline(intake, prototype_allowed, plan_type)
    friction_capture_triggers = _friction_triggers(intake)
    if response_mode == "behavior_pack_candidate":
        behavior_pack_seed_candidate = True
    if intake.domain_family == "privacy_sensitive_technology" and not _has_token(intake.safe_topic_descriptor, CONSENT_TERMS_V1):
        requires_boundary_review = True
    if intake.boundary_review_required:
        requires_boundary_review = True
    if intake.evidence_mapping_required:
        requires_evidence_mapping = True
    ontology = _intake_ontology_snapshot(intake)
    plan = ResearchConversationPlan(
        plan_id=_plan_id(intake.intake_id, plan_type, intake.domain_family),
        source_intake_id=intake.intake_id,
        domain_family=intake.domain_family,
        novelty_level=intake.novelty_level,
        owner_intent=intake.owner_intent,
        plan_type=plan_type,
        knowns=knowns,
        unknowns=unknowns,
        assumptions=assumptions,
        evidence_needed=evidence_needed,
        safe_next_steps=safe_next_steps,
        owner_questions=owner_questions,
        boundary_warnings=boundary_warnings,
        prototype_phase_outline=prototype_phase_outline,
        friction_capture_triggers=friction_capture_triggers,
        recommended_response_mode=response_mode,
        requires_boundary_review=requires_boundary_review,
        requires_evidence_mapping=requires_evidence_mapping,
        prototype_planning_allowed=prototype_allowed,
        behavior_pack_seed_candidate=behavior_pack_seed_candidate,
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        ontology_packet_id=ontology["ontology_packet_id"],
        ontology_meta_domains=tuple(ontology["ontology_meta_domains"]),
        ontology_domain_families=tuple(ontology["ontology_domain_families"]),
        ontology_subdomain_traits=tuple(ontology["ontology_subdomain_traits"]),
        ontology_objects_of_study=tuple(ontology["ontology_objects_of_study"]),
        ontology_evidence_classes=tuple(ontology["ontology_evidence_classes"]),
        ontology_risk_classes=tuple(ontology["ontology_risk_classes"]),
        ontology_sensitivity_classes=tuple(ontology["ontology_sensitivity_classes"]),
        ontology_response_route_family=ontology["ontology_response_route_family"],
        ontology_behavior_pack_candidate_labels=tuple(ontology["ontology_behavior_pack_candidate_labels"]),
        safe_metadata={**_safe_metadata(intake, plan_type, response_mode, behavior_pack_seed_candidate), "ontology": ontology},
    )
    validate_research_conversation_plan_v1(plan)
    return plan



def plan_research_conversation_v1(domain_intake: BroadTopicDomainIntake | Mapping[str, Any]) -> ResearchConversationPlan:
    return build_research_conversation_plan_v1(domain_intake=domain_intake)


# ---------------------------------------------------------------------------
# Validation and summaries
# ---------------------------------------------------------------------------


def validate_research_conversation_plan_v1(plan: Any) -> bool:
    if _collect_forbidden_fields(plan):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_claim_marker(plan):
        raise ValidationError("forbidden_public_or_claim_language_present")
    if _contains_unsafe_deployment_marker_in_guidance(plan):
        raise ValidationError("unsafe_deployment_marker_present")

    if is_dataclass(plan):
        normalized = plan
    elif isinstance(plan, Mapping):
        allowed = {field.name for field in ResearchConversationPlan.__dataclass_fields__.values()}
        extra = set(str(key) for key in plan.keys()) - allowed
        if extra:
            raise ValidationError("unknown_fields_present")
        normalized = ResearchConversationPlan(
            plan_id=_safe_text(plan.get("plan_id")),
            source_intake_id=_safe_text(plan.get("source_intake_id")),
            domain_family=_safe_text(plan.get("domain_family")),
            novelty_level=_safe_text(plan.get("novelty_level")),
            owner_intent=_safe_text(plan.get("owner_intent")),
            plan_type=_safe_text(plan.get("plan_type")),
            knowns=_normalize_sequence(plan.get("knowns")),
            unknowns=_normalize_sequence(plan.get("unknowns")),
            assumptions=_normalize_sequence(plan.get("assumptions")),
            evidence_needed=_normalize_sequence(plan.get("evidence_needed")),
            safe_next_steps=_normalize_sequence(plan.get("safe_next_steps")),
            owner_questions=_normalize_sequence(plan.get("owner_questions")),
            boundary_warnings=_normalize_sequence(plan.get("boundary_warnings")),
            prototype_phase_outline=_normalize_sequence(plan.get("prototype_phase_outline")),
            friction_capture_triggers=_normalize_sequence(plan.get("friction_capture_triggers")),
            recommended_response_mode=_safe_text(plan.get("recommended_response_mode")),
            requires_boundary_review=bool(plan.get("requires_boundary_review")),
            requires_evidence_mapping=bool(plan.get("requires_evidence_mapping")),
            prototype_planning_allowed=bool(plan.get("prototype_planning_allowed")),
            behavior_pack_seed_candidate=bool(plan.get("behavior_pack_seed_candidate")),
            public_claim_allowed=bool(plan.get("public_claim_allowed")),
            iss_internal_reference_allowed=bool(plan.get("iss_internal_reference_allowed")),
            learning_claimed=bool(plan.get("learning_claimed")),
            runtime_authority=bool(plan.get("runtime_authority")),
            writes_state=bool(plan.get("writes_state")),
            model_provider_used=bool(plan.get("model_provider_used")),
            ontology_packet_id=_safe_text(plan.get("ontology_packet_id")),
            ontology_meta_domains=_normalize_sequence(plan.get("ontology_meta_domains")),
            ontology_domain_families=_normalize_sequence(plan.get("ontology_domain_families")),
            ontology_subdomain_traits=_normalize_sequence(plan.get("ontology_subdomain_traits")),
            ontology_objects_of_study=_normalize_sequence(plan.get("ontology_objects_of_study")),
            ontology_evidence_classes=_normalize_sequence(plan.get("ontology_evidence_classes")),
            ontology_risk_classes=_normalize_sequence(plan.get("ontology_risk_classes")),
            ontology_sensitivity_classes=_normalize_sequence(plan.get("ontology_sensitivity_classes")),
            ontology_response_route_family=_safe_text(plan.get("ontology_response_route_family")),
            ontology_behavior_pack_candidate_labels=_normalize_sequence(plan.get("ontology_behavior_pack_candidate_labels")),
            safe_metadata=dict(plan.get("safe_metadata") or {}),
        )
    else:
        raise ValidationError("plan_must_be_dataclass_or_mapping")

    if not normalized.plan_id:
        raise ValidationError("plan_id_required")
    if not normalized.source_intake_id:
        raise ValidationError("source_intake_id_required")
    if normalized.domain_family not in {
        "technical_research",
        "privacy_sensitive_technology",
        "industrial_automation",
        "legal_privacy",
        "materials_discovery",
        "energy_systems",
        "robotics",
        "software_product",
        "website_public_launch",
        "language_vocabulary",
        "owner_workflow",
        "metamaterials",
        "theory_of_mind",
        "philosophy_of_mind",
        "cognitive_science",
        "psychology",
        "neuroscience",
        "ai_systems",
        "agentic_systems",
        "ai_safety_governance",
        "cognitive_architecture",
        "medicine_health_research",
        "biology_life_sciences",
        "physics",
        "chemistry",
        "unknown_domain",
    }:
        raise ValidationError("unknown_domain_family")
    if normalized.novelty_level not in {"known_existing_pack", "adjacent_to_existing_pack", "unfamiliar_but_researchable", "high_uncertainty", "blocked_or_sensitive"}:
        raise ValidationError("unknown_novelty_level")
    if normalized.owner_intent not in {"learn_explain", "research", "build_prototype", "evaluate_feasibility", "safety_legal_privacy_review", "commercial_product_strategy", "troubleshooting", "unknown_intent"}:
        raise ValidationError("unknown_owner_intent")
    if normalized.plan_type not in ALLOWED_PLAN_TYPES_V1:
        raise ValidationError("unknown_plan_type")
    if normalized.recommended_response_mode not in ALLOWED_RESPONSE_MODES_V1:
        raise ValidationError("unknown_recommended_response_mode")

    for field_name in (
        "requires_boundary_review",
        "requires_evidence_mapping",
        "prototype_planning_allowed",
        "behavior_pack_seed_candidate",
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

    for field_name in (
        "knowns",
        "unknowns",
        "assumptions",
        "evidence_needed",
        "safe_next_steps",
        "owner_questions",
        "boundary_warnings",
        "prototype_phase_outline",
        "friction_capture_triggers",
    ):
        if not isinstance(getattr(normalized, field_name), list):
            raise ValidationError(f"{field_name}_must_be_list")
        if not getattr(normalized, field_name):
            raise ValidationError(f"{field_name}_required")

    if normalized.public_claim_allowed is not False:
        raise ValidationError("public_claim_allowed_must_be_false")
    if normalized.learning_claimed is not False:
        raise ValidationError("learning_claimed_must_be_false")
    if normalized.runtime_authority is not False:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state is not False:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used is not False:
        raise ValidationError("model_provider_used_must_be_false")

    if normalized.domain_family == "privacy_sensitive_technology":
        warning_blob = " ".join(normalized.boundary_warnings)
        questions_blob = " ".join(normalized.owner_questions)
        if not _has_token(warning_blob, PRIVACY_BOUNDARY_TERMS_V1):
            raise ValidationError("privacy_sensitive_plan_requires_boundary_warning")
        if not _has_token(questions_blob, CONSENT_TERMS_V1):
            raise ValidationError("privacy_sensitive_plan_requires_consent_question")
        if normalized.prototype_planning_allowed and not _has_token(" ".join(normalized.safe_next_steps + normalized.prototype_phase_outline), {"consent", "lawful", "lawfulness"}):
            raise ValidationError("privacy_sensitive_prototype_requires_consent_language")
    return True



def summarize_research_conversation_plan_v1(plan: Any) -> ResearchConversationPlanSummary:
    if not isinstance(plan, ResearchConversationPlan):
        validate_research_conversation_plan_v1(plan)
        if isinstance(plan, Mapping):
            plan = ResearchConversationPlan(
                plan_id=_safe_text(plan.get("plan_id")),
                source_intake_id=_safe_text(plan.get("source_intake_id")),
                domain_family=_safe_text(plan.get("domain_family")),
                novelty_level=_safe_text(plan.get("novelty_level")),
                owner_intent=_safe_text(plan.get("owner_intent")),
                plan_type=_safe_text(plan.get("plan_type")),
                knowns=_normalize_sequence(plan.get("knowns")),
                unknowns=_normalize_sequence(plan.get("unknowns")),
                assumptions=_normalize_sequence(plan.get("assumptions")),
                evidence_needed=_normalize_sequence(plan.get("evidence_needed")),
                safe_next_steps=_normalize_sequence(plan.get("safe_next_steps")),
                owner_questions=_normalize_sequence(plan.get("owner_questions")),
                boundary_warnings=_normalize_sequence(plan.get("boundary_warnings")),
                prototype_phase_outline=_normalize_sequence(plan.get("prototype_phase_outline")),
                friction_capture_triggers=_normalize_sequence(plan.get("friction_capture_triggers")),
                recommended_response_mode=_safe_text(plan.get("recommended_response_mode")),
                requires_boundary_review=bool(plan.get("requires_boundary_review")),
                requires_evidence_mapping=bool(plan.get("requires_evidence_mapping")),
                prototype_planning_allowed=bool(plan.get("prototype_planning_allowed")),
                behavior_pack_seed_candidate=bool(plan.get("behavior_pack_seed_candidate")),
                public_claim_allowed=bool(plan.get("public_claim_allowed")),
                iss_internal_reference_allowed=bool(plan.get("iss_internal_reference_allowed")),
                learning_claimed=bool(plan.get("learning_claimed")),
                runtime_authority=bool(plan.get("runtime_authority")),
                writes_state=bool(plan.get("writes_state")),
                model_provider_used=bool(plan.get("model_provider_used")),
                ontology_packet_id=_safe_text(plan.get("ontology_packet_id")),
                ontology_meta_domains=_normalize_sequence(plan.get("ontology_meta_domains")),
                ontology_domain_families=_normalize_sequence(plan.get("ontology_domain_families")),
                ontology_subdomain_traits=_normalize_sequence(plan.get("ontology_subdomain_traits")),
                ontology_objects_of_study=_normalize_sequence(plan.get("ontology_objects_of_study")),
                ontology_evidence_classes=_normalize_sequence(plan.get("ontology_evidence_classes")),
                ontology_risk_classes=_normalize_sequence(plan.get("ontology_risk_classes")),
                ontology_sensitivity_classes=_normalize_sequence(plan.get("ontology_sensitivity_classes")),
                ontology_response_route_family=_safe_text(plan.get("ontology_response_route_family")),
                ontology_behavior_pack_candidate_labels=_normalize_sequence(plan.get("ontology_behavior_pack_candidate_labels")),
                safe_metadata=dict(plan.get("safe_metadata") or {}),
            )
    return ResearchConversationPlanSummary(
        summary_type=SUMMARY_TYPE_V1,
        plan_id=plan.plan_id,
        domain_family=plan.domain_family,
        plan_type=plan.plan_type,
        novelty_level=plan.novelty_level,
        owner_intent=plan.owner_intent,
        recommended_response_mode=plan.recommended_response_mode,
        requires_boundary_review=plan.requires_boundary_review,
        requires_evidence_mapping=plan.requires_evidence_mapping,
        prototype_planning_allowed=plan.prototype_planning_allowed,
        boundary_warning_count=len(plan.boundary_warnings),
        evidence_item_count=len(plan.evidence_needed),
    )



def to_research_conversation_plan_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


# ---------------------------------------------------------------------------
# Seed examples
# ---------------------------------------------------------------------------


def build_initial_research_conversation_plan_examples_v1() -> tuple[ResearchConversationPlan, ...]:
    example_specs = [
        {
            "safe_topic_descriptor": "WiFi/RF sensing for consent-based research in a home setting",
            "prompt_labels": ("wifi sensing", "research only", "privacy"),
            "owner_intent_labels": ("research",),
            "risk_hints": ("consent required", "lawful only"),
            "known_unknown_hints": ("researchable",),
        },
        {
            "safe_topic_descriptor": "Industrial automation troubleshooting for a control system",
            "prompt_labels": ("industrial automation", "troubleshooting", "PLC", "equipment"),
            "owner_intent_labels": ("troubleshooting",),
            "risk_hints": ("equipment safety",),
            "known_unknown_hints": ("adjacent",),
        },
        {
            "safe_topic_descriptor": "Materials discovery feasibility planning",
            "prompt_labels": ("materials discovery", "feasibility", "research"),
            "owner_intent_labels": ("evaluate feasibility",),
            "risk_hints": ("high evidence need",),
            "known_unknown_hints": ("unfamiliar",),
        },
        {
            "safe_topic_descriptor": "Metamaterials frontier research",
            "prompt_labels": ("metamaterials", "materials discovery", "frontier research", "experimental validation"),
            "owner_intent_labels": ("evaluate feasibility",),
            "risk_hints": ("high uncertainty",),
            "known_unknown_hints": ("frontier", "high uncertainty"),
        },
        {
            "safe_topic_descriptor": "Theory of mind conceptual research",
            "prompt_labels": ("theory of mind", "philosophy of mind", "cognitive science"),
            "owner_intent_labels": ("learn explain",),
            "risk_hints": ("high uncertainty",),
            "known_unknown_hints": ("high uncertainty",),
        },
        {
            "safe_topic_descriptor": "AI agent architecture and governance",
            "prompt_labels": ("ai systems", "agentic systems", "cognitive architecture", "ai safety governance"),
            "owner_intent_labels": ("research",),
            "risk_hints": ("public-facing sensitivity", "safety critical"),
            "known_unknown_hints": ("adjacent",),
        },
        {
            "safe_topic_descriptor": "Medical software regulated path",
            "prompt_labels": ("medicine health research", "software product", "clinical validation"),
            "owner_intent_labels": ("evaluate feasibility",),
            "risk_hints": ("medical sensitive", "regulated domain"),
            "known_unknown_hints": ("unfamiliar",),
        },
        {
            "safe_topic_descriptor": "Legal/privacy policy review for a new workflow",
            "prompt_labels": ("legal privacy", "policy review", "compliance"),
            "owner_intent_labels": ("safety legal privacy review",),
            "risk_hints": ("legal", "privacy"),
            "known_unknown_hints": ("unfamiliar",),
        },
        {
            "safe_topic_descriptor": "Energy system prototype planning",
            "prompt_labels": ("energy systems", "prototype", "battery", "power"),
            "owner_intent_labels": ("build prototype",),
            "risk_hints": ("safety sensitive",),
            "known_unknown_hints": ("adjacent",),
        },
        {
            "safe_topic_descriptor": "Software product planning for an owner-facing feature",
            "prompt_labels": ("software product", "product strategy", "feature planning"),
            "owner_intent_labels": ("commercial product strategy",),
            "risk_hints": ("medium uncertainty",),
            "known_unknown_hints": ("known existing pack",),
        },
        {
            "safe_topic_descriptor": "Language and vocabulary discovery for a new term",
            "prompt_labels": ("language", "vocabulary", "definition"),
            "owner_intent_labels": ("learn explain",),
            "risk_hints": ("low risk",),
            "known_unknown_hints": ("known existing pack",),
        },
        {
            "safe_topic_descriptor": "Unknown future topic",
            "prompt_labels": ("unknown", "novel"),
            "owner_intent_labels": ("unknown",),
            "risk_hints": ("high uncertainty",),
            "known_unknown_hints": ("high uncertainty",),
        },
    ]

    plans: list[ResearchConversationPlan] = []
    for spec in example_specs:
        intake = build_broad_topic_domain_intake_v1(
            safe_topic_descriptor=spec["safe_topic_descriptor"],
            prompt_labels=spec["prompt_labels"],
            owner_intent_labels=spec["owner_intent_labels"],
            risk_hints=spec["risk_hints"],
            known_unknown_hints=spec["known_unknown_hints"],
            existing_behavior_pack_refs=(),
        )
        plans.append(build_research_conversation_plan_v1(domain_intake=intake))
    return tuple(plans)


# Backwards-compatible aliases.
build_research_conversation_plan = build_research_conversation_plan_v1
plan_research_conversation = plan_research_conversation_v1
validate_research_conversation_plan = validate_research_conversation_plan_v1
summarize_research_conversation_plan = summarize_research_conversation_plan_v1
to_research_conversation_plan_json_safe = to_research_conversation_plan_json_safe_v1
build_initial_research_conversation_plan_examples = build_initial_research_conversation_plan_examples_v1
