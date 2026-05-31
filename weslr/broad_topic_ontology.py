"""Metadata-only broad topic ontology helper v1.

This module classifies safe broad-topic descriptors into a layered ontology.
It is deterministic, import-safe, and fail-closed.

No model/provider/search/advisor calls. No network. No IO. No state writes.
No chat routing. No runtime behavior changes. No public claims.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Mapping, Sequence

HELPER_TYPE_V1 = "broad_topic_ontology_helper_v1"
ONTOLOGY_TYPE_V1 = "broad_topic_ontology_v1"
SUMMARY_TYPE_V1 = "broad_topic_ontology_summary_v1"

ALLOWED_META_DOMAINS_V1 = {
    "mind_intelligence_consciousness",
    "technical_engineering",
    "physical_sciences",
    "life_health",
    "society_law_governance",
    "formal_reasoning",
    "product_business",
    "language_communication",
    "creative_culture",
    "security_safety",
    "environment_energy",
    "unknown_open_domain",
}

ALLOWED_DOMAIN_FAMILIES_V1 = {
    "ai_systems",
    "machine_learning",
    "llm_systems",
    "agentic_systems",
    "ai_safety_governance",
    "cognitive_architecture",
    "theory_of_mind",
    "philosophy_of_mind",
    "cognitive_science",
    "psychology",
    "neuroscience",
    "technical_research",
    "materials_discovery",
    "metamaterials",
    "physics",
    "chemistry",
    "biology_life_sciences",
    "medicine_health_research",
    "robotics",
    "hardware_electronics",
    "privacy_sensitive_technology",
    "industrial_automation",
    "energy_systems",
    "legal_privacy",
    "policy_governance",
    "economics_business_strategy",
    "education_learning",
    "social_systems",
    "website_public_launch",
    "software_product",
    "language_vocabulary",
    "creative_design",
    "owner_workflow",
    "unknown_domain",
}

ALLOWED_SUBDOMAIN_TRAITS_V1 = {
    "frontier_research",
    "emerging_technology",
    "privacy_sensitive",
    "safety_critical",
    "medical_claim_adjacent",
    "human_subject_involved",
    "physical_world_deployment",
    "regulated_domain",
    "theoretical_concept",
    "experimental_validation_needed",
    "prototype_possible",
    "evidence_sparse",
    "high_uncertainty",
    "multi_domain",
    "abuse_potential",
    "beneficial_assistive_use",
    "conceptual_modeling",
    "system_architecture",
    "formal_reasoning_required",
    "public_claim_sensitive",
}

ALLOWED_OBJECTS_OF_STUDY_V1 = {
    "human_mind",
    "machine_intelligence",
    "materials",
    "signals_waves",
    "energy_power",
    "living_systems",
    "legal_rights",
    "social_behavior",
    "software_system",
    "physical_device",
    "business_process",
    "language_meaning",
    "unknown_object",
}

ALLOWED_OWNER_INTENTS_V1 = {
    "learn_explain",
    "research",
    "build_prototype",
    "evaluate_feasibility",
    "safety_legal_privacy_review",
    "commercial_product_strategy",
    "troubleshooting",
    "unknown_intent",
}

ALLOWED_NOVELTY_LEVELS_V1 = {
    "known_existing_pack",
    "adjacent_to_existing_pack",
    "unfamiliar_but_researchable",
    "high_uncertainty",
    "blocked_or_sensitive",
}

ALLOWED_EVIDENCE_CLASSES_V1 = {
    "conceptual_definition",
    "technical_literature_needed",
    "experimental_validation_needed",
    "legal_regulatory_sources_needed",
    "safety_validation_needed",
    "clinical_validation_needed",
    "market_validation_needed",
    "user_context_needed",
    "unknown_evidence_needed",
}

ALLOWED_RISK_CLASSES_V1 = {
    "low_risk_conceptual",
    "privacy_sensitive",
    "safety_critical",
    "medical_or_health_sensitive",
    "legal_regulatory_sensitive",
    "dual_use_or_abuse_potential",
    "public_claim_sensitive",
    "unknown_risk",
}

ALLOWED_RESPONSE_ROUTE_FAMILIES_V1 = {
    "direct_bounded_overview",
    "research_conversation_plan",
    "evidence_mapping",
    "privacy_safety_legal_boundary_review",
    "prototype_path_high_level",
    "formal_reasoning_path",
    "conceptual_theory_path",
    "behavior_pack_candidate_seed",
    "clarifying_question",
    "refusal_boundary",
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

BASE_CLAIM_TERMS_V1 = {"agi", "consciousness", "sentience", "turing", "certification"}
CLAIM_QUALIFIERS_V1 = {
    "claim",
    "claims",
    "claimed",
    "official",
    "certified",
    "certification",
    "public",
    "ready",
    "readiness",
    "proof",
    "proven",
}

META_DOMAIN_PRIORITIES_V1 = (
    "mind_intelligence_consciousness",
    "technical_engineering",
    "physical_sciences",
    "life_health",
    "society_law_governance",
    "formal_reasoning",
    "product_business",
    "language_communication",
    "creative_culture",
    "security_safety",
    "environment_energy",
    "unknown_open_domain",
)

OWNER_INTENT_PRIORITY_V1 = (
    "safety_legal_privacy_review",
    "build_prototype",
    "evaluate_feasibility",
    "commercial_product_strategy",
    "research",
    "learn_explain",
    "troubleshooting",
)

FAMILY_TO_META_DOMAINS_V1 = {
    "ai_systems": ("mind_intelligence_consciousness", "technical_engineering"),
    "machine_learning": ("mind_intelligence_consciousness", "technical_engineering"),
    "llm_systems": ("mind_intelligence_consciousness", "technical_engineering"),
    "agentic_systems": ("mind_intelligence_consciousness", "technical_engineering"),
    "ai_safety_governance": ("mind_intelligence_consciousness", "technical_engineering", "society_law_governance", "security_safety"),
    "cognitive_architecture": ("mind_intelligence_consciousness", "technical_engineering"),
    "theory_of_mind": ("mind_intelligence_consciousness", "formal_reasoning"),
    "philosophy_of_mind": ("mind_intelligence_consciousness", "formal_reasoning"),
    "cognitive_science": ("mind_intelligence_consciousness",),
    "psychology": ("mind_intelligence_consciousness", "life_health"),
    "neuroscience": ("mind_intelligence_consciousness", "life_health"),
    "technical_research": ("technical_engineering",),
    "materials_discovery": ("physical_sciences", "technical_engineering"),
    "metamaterials": ("physical_sciences", "technical_engineering"),
    "physics": ("physical_sciences", "formal_reasoning", "technical_engineering"),
    "chemistry": ("physical_sciences", "technical_engineering"),
    "biology_life_sciences": ("life_health", "physical_sciences"),
    "medicine_health_research": ("life_health", "technical_engineering", "society_law_governance"),
    "robotics": ("technical_engineering", "security_safety"),
    "hardware_electronics": ("technical_engineering",),
    "privacy_sensitive_technology": ("technical_engineering", "society_law_governance", "life_health"),
    "industrial_automation": ("technical_engineering", "security_safety"),
    "energy_systems": ("environment_energy", "technical_engineering"),
    "legal_privacy": ("society_law_governance",),
    "policy_governance": ("society_law_governance",),
    "economics_business_strategy": ("product_business", "society_law_governance"),
    "education_learning": ("language_communication", "society_law_governance"),
    "social_systems": ("society_law_governance",),
    "website_public_launch": ("product_business", "technical_engineering"),
    "software_product": ("product_business", "technical_engineering"),
    "language_vocabulary": ("language_communication",),
    "creative_design": ("creative_culture", "language_communication"),
    "owner_workflow": ("product_business", "technical_engineering"),
    "unknown_domain": ("unknown_open_domain",),
}

DOMAIN_TRAIT_HINTS_V1 = {
    "frontier_research": ("frontier", "new domain", "novel", "research frontier", "emerging"),
    "emerging_technology": ("emerging", "prototype", "new technology", "future technology", "agentic", "ai system", "metamaterial", "wifi sensing", "rf sensing"),
    "privacy_sensitive": ("privacy", "surveillance", "tracking", "biometric", "location", "human sensing", "consent", "lawful only"),
    "safety_critical": ("safety", "hazard", "control system", "industrial automation", "robot", "energy", "medical", "clinical", "security"),
    "medical_claim_adjacent": ("medical", "health", "self-care", "therapy", "treatment", "wellness", "clinical"),
    "human_subject_involved": ("human", "people", "person", "house", "home", "occupant", "self-care", "behavior", "mind"),
    "physical_world_deployment": ("device", "sensor", "hardware", "robot", "automation", "deployment", "physical"),
    "regulated_domain": ("legal", "privacy", "policy", "compliance", "regulated", "medical", "clinical"),
    "theoretical_concept": ("theory", "philosophy", "conceptual", "concept", "mind", "cognition", "formal"),
    "experimental_validation_needed": ("experimental", "experiment", "validation", "prototype", "proof of concept", "lab"),
    "prototype_possible": ("prototype", "build", "implement", "develop", "make", "create", "poc"),
    "evidence_sparse": ("unknown", "unfamiliar", "novel", "frontier", "sparse", "limited evidence"),
    "high_uncertainty": ("unknown", "unfamiliar", "uncertain", "high uncertainty", "novel", "frontier"),
    "multi_domain": ("and", "/", ",", "plus"),
    "abuse_potential": ("abuse", "dual use", "surveillance", "tracking", "exploit", "weapon", "bypass"),
    "beneficial_assistive_use": ("assistive", "self-care", "help", "support", "accessibility", "well-being", "education"),
    "conceptual_modeling": ("conceptual", "model", "mapping", "theory", "architecture", "ontology"),
    "system_architecture": ("architecture", "system", "stack", "pipeline", "agent", "workflow"),
    "formal_reasoning_required": ("formal", "reasoning", "logic", "proof", "philosophy", "theory of mind"),
    "public_claim_sensitive": ("public claim", "public readiness", "official", "certification", "turing", "consciousness", "sentience", "agi"),
}

OBJECT_HINTS_V1 = {
    "human_mind": ("mind", "theory of mind", "psychology", "cognition", "consciousness", "person", "human"),
    "machine_intelligence": ("ai", "machine learning", "llm", "agent", "model", "intelligence", "architecture"),
    "materials": ("material", "materials", "metamaterial", "alloy", "compound", "chemistry", "synthesis"),
    "signals_waves": ("wifi", "rf", "signal", "signals", "wave", "waves", "sensing", "radio frequency"),
    "energy_power": ("energy", "power", "battery", "grid", "inverter", "storage", "solar"),
    "living_systems": ("biology", "bio", "health", "medical", "clinical", "human body", "life"),
    "legal_rights": ("legal", "privacy", "rights", "policy", "regulatory", "compliance"),
    "social_behavior": ("social", "society", "behavior", "public", "community", "workplace"),
    "software_system": ("software", "app", "platform", "system", "api", "backend", "frontend", "agent"),
    "physical_device": ("device", "hardware", "sensor", "robot", "electronics", "controller"),
    "business_process": ("business", "product", "strategy", "workflow", "launch", "market", "pricing"),
    "language_meaning": ("language", "vocabulary", "meaning", "translation", "grammar", "term"),
    "unknown_object": (),
}

EVIDENCE_HINTS_V1 = {
    "conceptual_definition": ("conceptual", "definition", "philosophy", "theory of mind", "language", "meaning"),
    "technical_literature_needed": ("technical", "literature", "research", "paper", "papers", "engineering", "architecture"),
    "experimental_validation_needed": ("experimental", "experiment", "validation", "prototype", "lab", "proof of concept"),
    "legal_regulatory_sources_needed": ("legal", "privacy", "policy", "regulatory", "compliance", "law"),
    "safety_validation_needed": ("safety", "hazard", "risk", "robot", "industrial", "energy", "security"),
    "clinical_validation_needed": ("clinical", "medical", "health", "self-care", "care", "patient"),
    "market_validation_needed": ("market", "business", "product", "launch", "pricing", "customers"),
    "user_context_needed": ("user", "owner", "workflow", "context", "needs", "preference"),
    "unknown_evidence_needed": ("unknown", "unfamiliar", "high uncertainty", "novel", "frontier"),
}

RISK_HINTS_V1 = {
    "low_risk_conceptual": ("conceptual", "overview", "explain", "learn", "theory", "definition"),
    "privacy_sensitive": ("privacy", "surveillance", "tracking", "human sensing", "biometric", "consent", "location"),
    "safety_critical": ("safety", "industrial", "robot", "energy", "medical", "clinical", "hazard"),
    "medical_or_health_sensitive": ("medical", "health", "clinical", "self-care", "wellness", "treatment"),
    "legal_regulatory_sensitive": ("legal", "privacy", "policy", "compliance", "regulatory", "law"),
    "dual_use_or_abuse_potential": ("dual use", "abuse", "surveillance", "tracking", "exploit", "weapon", "bypass"),
    "public_claim_sensitive": ("public claim", "public readiness", "official", "certification", "turing", "consciousness", "sentience", "agi"),
    "unknown_risk": ("unknown", "uncertain", "novel", "frontier", "unfamiliar"),
}

RESPONSE_ROUTE_PRIORITY_V1 = (
    "refusal_boundary",
    "privacy_safety_legal_boundary_review",
    "conceptual_theory_path",
    "formal_reasoning_path",
    "evidence_mapping",
    "research_conversation_plan",
    "prototype_path_high_level",
    "behavior_pack_candidate_seed",
    "direct_bounded_overview",
    "clarifying_question",
)

DEFAULT_RECOMMENDED_HELPERS_V1 = (
    "research_conversation_planner",
    "new_domain_evidence_mapper",
    "prototype_path_planner",
    "domain_behavior_pack_candidate_builder",
)


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class BroadTopicOntologyPacket:
    ontology_id: str
    safe_topic_descriptor: str
    meta_domains: list[str]
    domain_families: list[str]
    subdomain_traits: list[str]
    objects_of_study: list[str]
    owner_intents: list[str]
    novelty_level: str
    evidence_classes: list[str]
    risk_classes: list[str]
    sensitivity_classes: list[str]
    response_route_family: str
    behavior_pack_candidate_labels: list[str]
    recommended_next_helpers: list[str]
    boundary_review_required: bool
    evidence_mapping_required: bool
    research_planning_required: bool
    prototype_planning_allowed: bool
    privacy_sensitive: bool
    safety_sensitive: bool
    legal_sensitive: bool
    medical_sensitive: bool
    public_claim_allowed: bool
    iss_internal_reference_allowed: bool
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class BroadTopicOntologySummary:
    summary_type: str
    ontology_id: str
    safe_topic_descriptor: str
    meta_domains: list[str]
    domain_families: list[str]
    evidence_classes: list[str]
    risk_classes: list[str]
    response_route_family: str
    boundary_review_required: bool
    evidence_mapping_required: bool
    research_planning_required: bool
    prototype_planning_allowed: bool
    behavior_pack_candidate_count: int


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



def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]



def _normalize_sequence(value: Any) -> list[str]:
    return _dedupe_preserve(_safe_text(item) for item in _as_list(value))



def _dedupe_preserve(items: Sequence[str] | Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        text = _normalize_text(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out



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



def _contains_any_text(blob: str, phrases: Sequence[str]) -> bool:
    haystack = _normalize_text(blob)
    token_set = set(_split_tokens(haystack))
    for phrase in phrases:
        needle = _normalize_text(phrase)
        if not needle:
            continue
        needle_tokens = _split_tokens(needle)
        if len(needle_tokens) == 1:
            if needle_tokens[0] in token_set:
                return True
            continue
        needle_joined = " ".join(needle_tokens)
        if needle_joined in haystack or needle in haystack:
            return True
    return False



def _contains_any_label(labels: Sequence[str], phrases: Sequence[str]) -> bool:
    return _contains_any_text(" ".join(labels), phrases)



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
        has_base = any(term in blob for term in BASE_CLAIM_TERMS_V1)
        has_qualifier = any(term in blob for term in CLAIM_QUALIFIERS_V1)
        return has_base and has_qualifier
    return False



def _ordered_unique(candidates: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in candidates:
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


def _has_any(blob: str, phrases: Sequence[str]) -> bool:
    return _contains_any_text(blob, phrases)



def _infer_owner_intent(labels: Sequence[str], descriptor: str) -> str:
    blob = " ".join((descriptor, " ".join(labels)))
    if _has_any(blob, ("safety", "legal", "privacy", "compliance", "risk review", "boundary review")):
        return "safety_legal_privacy_review"
    if _has_any(blob, ("build", "prototype", "implement", "create", "develop", "make", "design", "poc")):
        return "build_prototype"
    if _has_any(blob, ("feasibility", "viable", "possible", "assess", "evaluate", "can this work", "practical")):
        return "evaluate_feasibility"
    if _has_any(blob, ("commercial", "product", "strategy", "market", "launch", "pricing", "business")):
        return "commercial_product_strategy"
    if _has_any(blob, ("research", "study", "investigate", "explore", "analyze", "analysis", "literature")):
        return "research"
    if _has_any(blob, ("learn", "explain", "understand", "overview", "teach")):
        return "learn_explain"
    if _has_any(blob, ("troubleshoot", "debug", "fix", "issue", "problem", "error", "bug")):
        return "troubleshooting"
    return "unknown_intent"



def _infer_domain_families(labels: Sequence[str], descriptor: str, owner_intents: Sequence[str], evidence_hints: Sequence[str], risk_hints: Sequence[str], known_unknown_hints: Sequence[str]) -> list[str]:
    blob = " ".join((descriptor, " ".join(labels), " ".join(owner_intents), " ".join(risk_hints), " ".join(known_unknown_hints)))
    families: list[str] = []

    # Mind / cognition / AI
    if _has_any(blob, ("ai", "artificial intelligence", "machine learning", "llm", "language model", "agentic", "agents", "neural network")):
        families.append("ai_systems")
        if _has_any(blob, ("machine learning", "training", "dataset", "neural network", "learning")):
            families.append("machine_learning")
        if _has_any(blob, ("llm", "language model", "chat", "prompt", "token")):
            families.append("llm_systems")
        if _has_any(blob, ("agent", "agentic", "autonomous", "tool use", "planner")):
            families.append("agentic_systems")
        if _has_any(blob, ("safety", "governance", "alignment", "policy", "oversight")):
            families.append("ai_safety_governance")
        if _has_any(blob, ("cognitive architecture", "reasoning loop", "memory architecture", "world model", "agent architecture")):
            families.append("cognitive_architecture")

    if _has_any(blob, ("theory of mind", "tom", "mental state", "belief attribution")):
        families.extend(("theory_of_mind", "philosophy_of_mind", "cognitive_science"))
    if _has_any(blob, ("philosophy", "philosophy of mind", "mind", "consciousness", "intentionality", "epistemology", "ontology")):
        if "philosophy_of_mind" not in families:
            families.append("philosophy_of_mind")
        if _has_any(blob, ("cognition", "behavior", "theory")):
            families.append("cognitive_science")
    if _has_any(blob, ("psychology", "behavioral science")):
        families.extend(("psychology", "cognitive_science"))
    if _has_any(blob, ("neuroscience", "brain", "neuronal", "cortex")):
        families.append("neuroscience")

    # Science / engineering
    if _has_any(blob, ("metamaterial", "metamaterials")):
        families.extend(("metamaterials", "materials_discovery"))
    elif _has_any(blob, ("material", "materials", "alloy", "compound", "synthesis", "crystal", "chemistry")):
        families.append("materials_discovery")
    if _has_any(blob, ("physics", "wave", "waves", "quantum", "field", "optics")):
        families.append("physics")
    if _has_any(blob, ("chemistry", "chemical", "catalyst", "reaction")):
        families.append("chemistry")
    if _has_any(blob, ("biology", "life sciences", "biological", "organism")):
        families.append("biology_life_sciences")
    if _has_any(blob, ("medical", "medicine", "health", "clinical", "therapy", "care", "self-care", "wellness")):
        families.append("medicine_health_research")
    if _has_any(blob, ("robot", "robotics", "actuator", "manipulator", "autonomous machine")):
        families.append("robotics")
    if _has_any(blob, ("hardware", "electronics", "circuit", "embedded", "sensor", "device", "rf", "wifi", "radio frequency")):
        families.append("hardware_electronics")
    if _has_any(blob, ("privacy", "surveillance", "tracking", "biometric", "human sensing", "rf sensing", "wifi sensing", "location inference", "covert")):
        families.append("privacy_sensitive_technology")
    if _has_any(blob, ("industrial", "automation", "plc", "scada", "control system", "factory", "manufacturing", "ot")):
        families.append("industrial_automation")
    if _has_any(blob, ("energy", "battery", "storage", "power", "grid", "solar", "inverter", "microgrid")):
        families.append("energy_systems")

    # Society / law / business
    if _has_any(blob, ("legal", "privacy", "law", "rights", "regulatory", "compliance")):
        families.append("legal_privacy")
    if _has_any(blob, ("policy", "regulation", "regulatory", "compliance")):
        families.append("policy_governance")
    if _has_any(blob, ("economics", "business", "strategy", "pricing", "market", "commercial")):
        families.append("economics_business_strategy")
    if _has_any(blob, ("education", "learning", "curriculum", "teaching", "pedagogy")):
        families.append("education_learning")
    if _has_any(blob, ("social", "society", "community", "group", "behavior", "culture")):
        families.append("social_systems")
    if _has_any(blob, ("website", "public launch", "launch", "landing page", "seo", "checkout", "homepage")):
        families.append("website_public_launch")
    if _has_any(blob, ("software", "app", "platform", "feature", "product", "api", "backend", "frontend", "saas")):
        families.append("software_product")

    # General
    if _has_any(blob, ("language", "vocabulary", "word", "meaning", "translation", "grammar", "term", "lexicon")):
        families.append("language_vocabulary")
    if _has_any(blob, ("design", "art", "creative", "writing", "story", "culture", "aesthetic")):
        families.append("creative_design")
    if _has_any(blob, ("workflow", "owner", "weslr", "behavior pack", "replay", "friction")):
        families.append("owner_workflow")

    if not families:
        families.append("unknown_domain")

    if "privacy_sensitive_technology" in families:
        for extra in ("technical_research", "hardware_electronics"):
            if extra not in families:
                families.append(extra)

    return _ordered_unique(families)



def _infer_meta_domains(domain_families: Sequence[str], labels: Sequence[str], descriptor: str, owner_intents: Sequence[str], evidence_hints: Sequence[str], risk_hints: Sequence[str], known_unknown_hints: Sequence[str]) -> list[str]:
    meta_domains: list[str] = []
    blob = " ".join((descriptor, " ".join(labels), " ".join(owner_intents), " ".join(evidence_hints), " ".join(risk_hints), " ".join(known_unknown_hints)))

    for family in domain_families:
        for meta in FAMILY_TO_META_DOMAINS_V1.get(family, ()):
            if meta not in meta_domains:
                meta_domains.append(meta)

    if _has_any(blob, ("philosophy", "theory of mind", "cognition", "mind", "consciousness", "psychology", "neuroscience")):
        if "mind_intelligence_consciousness" not in meta_domains:
            meta_domains.insert(0, "mind_intelligence_consciousness")
    if _has_any(blob, ("rf", "wifi", "sensing", "device", "sensor", "hardware", "engineering", "automation")):
        if "technical_engineering" not in meta_domains:
            meta_domains.append("technical_engineering")
    if _has_any(blob, ("physics", "chemistry", "materials", "metamaterial", "signals", "waves")):
        if "physical_sciences" not in meta_domains:
            meta_domains.append("physical_sciences")
    if _has_any(blob, ("medical", "health", "clinical", "biology", "life science", "self-care")):
        if "life_health" not in meta_domains:
            meta_domains.append("life_health")
    if _has_any(blob, ("legal", "privacy", "policy", "governance", "regulatory", "compliance")):
        if "society_law_governance" not in meta_domains:
            meta_domains.append("society_law_governance")
    if _has_any(blob, ("formal", "logic", "proof", "reasoning", "philosophy")):
        if "formal_reasoning" not in meta_domains:
            meta_domains.append("formal_reasoning")
    if _has_any(blob, ("product", "business", "market", "launch", "pricing", "strategy")):
        if "product_business" not in meta_domains:
            meta_domains.append("product_business")
    if _has_any(blob, ("language", "vocabulary", "meaning", "translation", "teaching")):
        if "language_communication" not in meta_domains:
            meta_domains.append("language_communication")
    if _has_any(blob, ("design", "creative", "writing", "story", "culture")):
        if "creative_culture" not in meta_domains:
            meta_domains.append("creative_culture")
    if _has_any(blob, ("security", "cyber", "abuse", "dual use", "exploit", "threat")):
        if "security_safety" not in meta_domains:
            meta_domains.append("security_safety")
    if _has_any(blob, ("energy", "battery", "storage", "power", "grid", "solar", "inverter")):
        if "environment_energy" not in meta_domains:
            meta_domains.append("environment_energy")

    if not meta_domains:
        meta_domains.append("unknown_open_domain")
    if len(meta_domains) > 1 and "unknown_open_domain" in meta_domains:
        meta_domains = [item for item in meta_domains if item != "unknown_open_domain"]
    return _ordered_unique(meta_domains)



def _infer_traits(domain_families: Sequence[str], meta_domains: Sequence[str], labels: Sequence[str], descriptor: str, owner_intents: Sequence[str], evidence_hints: Sequence[str], risk_hints: Sequence[str], known_unknown_hints: Sequence[str]) -> list[str]:
    blob = " ".join((descriptor, " ".join(labels), " ".join(owner_intents), " ".join(evidence_hints), " ".join(risk_hints), " ".join(known_unknown_hints), " ".join(domain_families)))
    traits: list[str] = []

    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["frontier_research"]):
        traits.append("frontier_research")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["emerging_technology"]):
        traits.append("emerging_technology")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["privacy_sensitive"]):
        traits.append("privacy_sensitive")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["safety_critical"]):
        traits.append("safety_critical")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["medical_claim_adjacent"]):
        traits.append("medical_claim_adjacent")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["human_subject_involved"]):
        traits.append("human_subject_involved")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["physical_world_deployment"]):
        traits.append("physical_world_deployment")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["regulated_domain"]):
        traits.append("regulated_domain")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["theoretical_concept"]):
        traits.append("theoretical_concept")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["experimental_validation_needed"]):
        traits.append("experimental_validation_needed")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["prototype_possible"]):
        traits.append("prototype_possible")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["evidence_sparse"]):
        traits.append("evidence_sparse")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["high_uncertainty"]):
        traits.append("high_uncertainty")
    if len(meta_domains) > 1 or len(domain_families) > 1:
        traits.append("multi_domain")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["abuse_potential"]):
        traits.append("abuse_potential")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["beneficial_assistive_use"]):
        traits.append("beneficial_assistive_use")
    if any(family in {"privacy_sensitive_technology"} for family in domain_families) and _has_any(blob, ("self-care", "assistive", "help", "support", "accessibility", "well-being")):
        traits.append("beneficial_assistive_use")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["public_claim_sensitive"]):
        traits.append("public_claim_sensitive")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["conceptual_modeling"]):
        traits.append("conceptual_modeling")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["system_architecture"]):
        traits.append("system_architecture")
    if _has_any(blob, DOMAIN_TRAIT_HINTS_V1["formal_reasoning_required"]):
        traits.append("formal_reasoning_required")

    if any(family in {"ai_systems", "agentic_systems", "cognitive_architecture", "software_product", "industrial_automation", "website_public_launch"} for family in domain_families):
        if "system_architecture" not in traits:
            traits.append("system_architecture")
    if any(family in {"theory_of_mind", "philosophy_of_mind", "cognitive_science"} for family in domain_families):
        if "conceptual_modeling" not in traits:
            traits.append("conceptual_modeling")
        if "formal_reasoning_required" not in traits:
            traits.append("formal_reasoning_required")
    if any(family in {"privacy_sensitive_technology", "legal_privacy", "medicine_health_research"} for family in domain_families):
        if "regulated_domain" not in traits:
            traits.append("regulated_domain")
    if any(family in {"metamaterials", "materials_discovery", "physics", "chemistry"} for family in domain_families):
        if "frontier_research" not in traits:
            traits.append("frontier_research")
        if "experimental_validation_needed" not in traits:
            traits.append("experimental_validation_needed")
        if "prototype_possible" not in traits:
            traits.append("prototype_possible")
    if any(family in {"unknown_domain"} for family in domain_families):
        if "high_uncertainty" not in traits:
            traits.append("high_uncertainty")
        if "evidence_sparse" not in traits:
            traits.append("evidence_sparse")
    if any(family in {"industrial_automation", "energy_systems", "robotics", "medicine_health_research", "security_safety"} for family in domain_families):
        if "safety_critical" not in traits:
            traits.append("safety_critical")
    if any(family in {"privacy_sensitive_technology"} for family in domain_families):
        if "privacy_sensitive" not in traits:
            traits.append("privacy_sensitive")
        if "human_subject_involved" not in traits:
            traits.append("human_subject_involved")
    if any(family in {"language_vocabulary", "education_learning"} for family in domain_families):
        if "beneficial_assistive_use" not in traits:
            traits.append("beneficial_assistive_use")

    return _ordered_unique(traits)



def _infer_objects(domain_families: Sequence[str], meta_domains: Sequence[str], labels: Sequence[str], descriptor: str) -> list[str]:
    blob = " ".join((descriptor, " ".join(labels), " ".join(domain_families), " ".join(meta_domains)))
    objects: list[str] = []

    for obj, phrases in OBJECT_HINTS_V1.items():
        if obj == "unknown_object":
            continue
        if phrases and _has_any(blob, phrases):
            objects.append(obj)

    if any(family in {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"} for family in domain_families):
        for item in ("human_mind", "machine_intelligence"):
            if item not in objects:
                objects.append(item)
    if any(family in {"ai_systems", "machine_learning", "llm_systems", "agentic_systems", "cognitive_architecture", "ai_safety_governance"} for family in domain_families):
        for item in ("machine_intelligence", "software_system"):
            if item not in objects:
                objects.append(item)
    if any(family in {"metamaterials", "materials_discovery", "physics", "chemistry"} for family in domain_families):
        for item in ("materials", "signals_waves"):
            if item not in objects:
                objects.append(item)
    if any(family in {"privacy_sensitive_technology", "hardware_electronics", "industrial_automation", "robotics"} for family in domain_families):
        for item in ("signals_waves", "physical_device", "software_system"):
            if item not in objects:
                objects.append(item)
    if any(family in {"medicine_health_research", "biology_life_sciences"} for family in domain_families):
        for item in ("living_systems", "software_system"):
            if item not in objects:
                objects.append(item)
    if any(family in {"legal_privacy", "policy_governance"} for family in domain_families):
        for item in ("legal_rights", "social_behavior", "business_process"):
            if item not in objects:
                objects.append(item)
    if any(family in {"economics_business_strategy", "software_product", "website_public_launch", "owner_workflow"} for family in domain_families):
        for item in ("business_process", "software_system"):
            if item not in objects:
                objects.append(item)
    if any(family in {"language_vocabulary", "education_learning", "creative_design"} for family in domain_families):
        if "language_meaning" not in objects:
            objects.append("language_meaning")
    if any(family in {"energy_systems"} for family in domain_families):
        for item in ("energy_power", "physical_device"):
            if item not in objects:
                objects.append(item)

    if not objects:
        objects.append("unknown_object")
    return _ordered_unique(objects)



def _infer_evidence_classes(domain_families: Sequence[str], meta_domains: Sequence[str], traits: Sequence[str], labels: Sequence[str], descriptor: str, evidence_hints: Sequence[str], owner_intents: Sequence[str], risk_hints: Sequence[str], known_unknown_hints: Sequence[str]) -> list[str]:
    blob = " ".join((descriptor, " ".join(labels), " ".join(evidence_hints), " ".join(owner_intents), " ".join(risk_hints), " ".join(known_unknown_hints), " ".join(domain_families), " ".join(traits)))
    evidence: list[str] = []

    if _has_any(blob, EVIDENCE_HINTS_V1["conceptual_definition"]):
        evidence.append("conceptual_definition")
    if _has_any(blob, EVIDENCE_HINTS_V1["technical_literature_needed"]):
        evidence.append("technical_literature_needed")
    if _has_any(blob, EVIDENCE_HINTS_V1["experimental_validation_needed"]):
        evidence.append("experimental_validation_needed")
    if _has_any(blob, EVIDENCE_HINTS_V1["legal_regulatory_sources_needed"]):
        evidence.append("legal_regulatory_sources_needed")
    if _has_any(blob, EVIDENCE_HINTS_V1["safety_validation_needed"]):
        evidence.append("safety_validation_needed")
    if _has_any(blob, EVIDENCE_HINTS_V1["clinical_validation_needed"]):
        evidence.append("clinical_validation_needed")
    if _has_any(blob, EVIDENCE_HINTS_V1["market_validation_needed"]):
        evidence.append("market_validation_needed")
    if _has_any(blob, EVIDENCE_HINTS_V1["user_context_needed"]):
        evidence.append("user_context_needed")
    if _has_any(blob, EVIDENCE_HINTS_V1["unknown_evidence_needed"]):
        evidence.append("unknown_evidence_needed")

    if any(family in {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "language_vocabulary"} for family in domain_families):
        if "conceptual_definition" not in evidence:
            evidence.append("conceptual_definition")
        if any(family in {"cognitive_science"} for family in domain_families) and "technical_literature_needed" not in evidence:
            evidence.append("technical_literature_needed")
    if any(family in {"metamaterials", "materials_discovery", "physics", "chemistry"} for family in domain_families):
        for item in ("technical_literature_needed", "experimental_validation_needed"):
            if item not in evidence:
                evidence.append(item)
    if any(family in {"privacy_sensitive_technology", "legal_privacy", "policy_governance"} for family in domain_families):
        for item in ("legal_regulatory_sources_needed",):
            if item not in evidence:
                evidence.append(item)
        if "technical_literature_needed" not in evidence:
            evidence.append("technical_literature_needed")
    if any(family in {"medicine_health_research", "biology_life_sciences"} for family in domain_families):
        for item in ("clinical_validation_needed", "legal_regulatory_sources_needed", "safety_validation_needed"):
            if item not in evidence:
                evidence.append(item)
    if any(family in {"industrial_automation", "robotics", "energy_systems", "security_safety"} for family in domain_families):
        if "safety_validation_needed" not in evidence:
            evidence.append("safety_validation_needed")
        if "technical_literature_needed" not in evidence:
            evidence.append("technical_literature_needed")
    if any(family in {"economics_business_strategy", "software_product", "website_public_launch", "owner_workflow"} for family in domain_families):
        for item in ("market_validation_needed", "user_context_needed"):
            if item not in evidence:
                evidence.append(item)
    if any(family in {"unknown_domain"} for family in domain_families) and "unknown_evidence_needed" not in evidence:
        evidence.append("unknown_evidence_needed")
    if "high_uncertainty" in traits or "evidence_sparse" in traits:
        if "unknown_evidence_needed" not in evidence:
            evidence.append("unknown_evidence_needed")

    return _ordered_unique(evidence)



def _infer_novelty_level(domain_families: Sequence[str], traits: Sequence[str], labels: Sequence[str], evidence_hints: Sequence[str], known_unknown_hints: Sequence[str]) -> str:
    blob = " ".join((" ".join(domain_families), " ".join(traits), " ".join(labels), " ".join(evidence_hints), " ".join(known_unknown_hints)))
    if _has_any(blob, ("blocked", "unsafe", "illegal", "covert", "surveillance", "harm")):
        return "blocked_or_sensitive"
    if _has_any(blob, ("known existing pack", "existing pack", "known pack", "already known")):
        return "known_existing_pack"
    if _has_any(blob, ("adjacent", "nearby", "related", "similar to existing")):
        return "adjacent_to_existing_pack"
    if _has_any(blob, ("high uncertainty", "uncertain", "unknown", "unfamiliar", "frontier", "emerging")):
        return "high_uncertainty"
    if any(trait in {"frontier_research", "evidence_sparse"} for trait in traits):
        return "unfamiliar_but_researchable"
    return "unfamiliar_but_researchable"



def _infer_risk_classes(domain_families: Sequence[str], meta_domains: Sequence[str], traits: Sequence[str], labels: Sequence[str], descriptor: str, risk_hints: Sequence[str], evidence_hints: Sequence[str]) -> list[str]:
    blob = " ".join((descriptor, " ".join(labels), " ".join(risk_hints), " ".join(evidence_hints), " ".join(domain_families), " ".join(traits)))
    risks: list[str] = []

    if _has_any(blob, RISK_HINTS_V1["low_risk_conceptual"]):
        risks.append("low_risk_conceptual")
    if _has_any(blob, RISK_HINTS_V1["privacy_sensitive"]):
        risks.append("privacy_sensitive")
    if _has_any(blob, RISK_HINTS_V1["safety_critical"]):
        risks.append("safety_critical")
    if _has_any(blob, RISK_HINTS_V1["medical_or_health_sensitive"]):
        risks.append("medical_or_health_sensitive")
    if _has_any(blob, RISK_HINTS_V1["legal_regulatory_sensitive"]):
        risks.append("legal_regulatory_sensitive")
    if _has_any(blob, RISK_HINTS_V1["dual_use_or_abuse_potential"]):
        risks.append("dual_use_or_abuse_potential")
    if _has_any(blob, RISK_HINTS_V1["public_claim_sensitive"]):
        risks.append("public_claim_sensitive")
    if _has_any(blob, RISK_HINTS_V1["unknown_risk"]):
        risks.append("unknown_risk")

    if any(family in {"privacy_sensitive_technology", "legal_privacy"} for family in domain_families):
        for item in ("privacy_sensitive", "legal_regulatory_sensitive"):
            if item not in risks:
                risks.append(item)
    if any(family in {"medicine_health_research"} for family in domain_families):
        for item in ("medical_or_health_sensitive", "legal_regulatory_sensitive", "safety_critical"):
            if item not in risks:
                risks.append(item)
    if any(family in {"industrial_automation", "robotics", "energy_systems", "security_safety"} for family in domain_families):
        if "safety_critical" not in risks:
            risks.append("safety_critical")
    if any(family in {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture", "theory_of_mind", "philosophy_of_mind"} for family in domain_families):
        if "public_claim_sensitive" not in risks:
            risks.append("public_claim_sensitive")
    if any(family in {"materials_discovery", "metamaterials", "physics", "chemistry"} for family in domain_families):
        if "unknown_risk" not in risks and _has_any(blob, ("unknown", "frontier", "novel", "emerging")):
            risks.append("unknown_risk")
    if any(family in {"unknown_domain"} for family in domain_families):
        if "unknown_risk" not in risks:
            risks.append("unknown_risk")

    if not risks:
        risks.append("low_risk_conceptual")
    return _ordered_unique(risks)



def _infer_sensitivity_classes(domain_families: Sequence[str], meta_domains: Sequence[str], traits: Sequence[str], labels: Sequence[str], descriptor: str, risk_classes: Sequence[str], evidence_classes: Sequence[str]) -> list[str]:
    blob = " ".join((descriptor, " ".join(labels), " ".join(domain_families), " ".join(traits), " ".join(risk_classes), " ".join(evidence_classes)))
    sensitivity: list[str] = []

    if _has_any(blob, ("privacy", "surveillance", "tracking", "human sensing", "location", "biometric", "consent")):
        sensitivity.append("privacy_sensitive")
    if _has_any(blob, ("safety", "hazard", "industrial", "robot", "energy", "medical", "clinical", "security")):
        sensitivity.append("safety_critical")
    if _has_any(blob, ("medical", "health", "clinical", "self-care", "wellness", "treatment")):
        sensitivity.append("medical_or_health_sensitive")
    if _has_any(blob, ("legal", "privacy", "policy", "regulatory", "compliance", "law")):
        sensitivity.append("legal_regulatory_sensitive")
    if _has_any(blob, ("dual use", "abuse", "weapon", "exploit", "bypass", "surveillance", "tracking")):
        sensitivity.append("dual_use_or_abuse_potential")
    if _has_any(blob, ("public claim", "official", "readiness", "certification", "turing", "consciousness", "sentience", "agi")):
        sensitivity.append("public_claim_sensitive")
    if _has_any(blob, ("unknown", "unfamiliar", "novel", "frontier")) and not sensitivity:
        sensitivity.append("unknown_risk")
    if not sensitivity:
        sensitivity.append("low_risk_conceptual")

    return _ordered_unique(sensitivity)



def _infer_response_route_family(
    domain_families: Sequence[str],
    meta_domains: Sequence[str],
    traits: Sequence[str],
    novelty_level: str,
    evidence_classes: Sequence[str],
    risk_classes: Sequence[str],
    sensitivity_classes: Sequence[str],
    owner_intents: Sequence[str],
    labels: Sequence[str],
    descriptor: str,
) -> str:
    blob = " ".join((descriptor, " ".join(labels), " ".join(domain_families), " ".join(meta_domains), " ".join(traits), " ".join(evidence_classes), " ".join(risk_classes), " ".join(sensitivity_classes), " ".join(owner_intents)))

    if "privacy_sensitive" in sensitivity_classes or "legal_regulatory_sensitive" in sensitivity_classes or "medical_or_health_sensitive" in sensitivity_classes:
        return "privacy_safety_legal_boundary_review"
    if "conceptual_definition" in evidence_classes and any(family in {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "language_vocabulary"} for family in domain_families):
        if any(family in {"language_vocabulary"} for family in domain_families):
            return "direct_bounded_overview"
        return "conceptual_theory_path"
    if "formal_reasoning_required" in traits or any(meta in {"formal_reasoning"} for meta in meta_domains):
        if any(family in {"theory_of_mind", "philosophy_of_mind"} for family in domain_families):
            return "conceptual_theory_path"
        return "formal_reasoning_path"
    if "unknown_evidence_needed" in evidence_classes or novelty_level == "high_uncertainty" or "high_uncertainty" in traits:
        return "clarifying_question" if any(family in {"unknown_domain"} for family in domain_families) else "evidence_mapping"
    if any(family in {"metamaterials", "materials_discovery", "physics", "chemistry"} for family in domain_families):
        if "experimental_validation_needed" in evidence_classes or "frontier_research" in traits:
            return "evidence_mapping"
        return "research_conversation_plan"
    if any(family in {"ai_systems", "machine_learning", "llm_systems", "agentic_systems", "cognitive_architecture", "ai_safety_governance", "software_product", "website_public_launch", "economics_business_strategy", "energy_systems", "industrial_automation", "robotics", "hardware_electronics"} for family in domain_families):
        if any(family in {"industrial_automation", "robotics", "energy_systems", "hardware_electronics"} for family in domain_families) and "experimental_validation_needed" in evidence_classes:
            return "evidence_mapping"
        if any(intent in {"build_prototype", "evaluate_feasibility", "research", "commercial_product_strategy"} for intent in owner_intents):
            return "research_conversation_plan"
        if "prototype_possible" in traits:
            return "prototype_path_high_level"
        return "research_conversation_plan"
    if any(family in {"legal_privacy", "policy_governance"} for family in domain_families):
        return "privacy_safety_legal_boundary_review" if any(item in evidence_classes for item in ("legal_regulatory_sources_needed",)) else "evidence_mapping"
    if any(family in {"medicine_health_research", "biology_life_sciences"} for family in domain_families):
        return "privacy_safety_legal_boundary_review" if any(item in sensitivity_classes for item in ("medical_or_health_sensitive", "legal_regulatory_sensitive")) else "evidence_mapping"
    if any(family in {"language_vocabulary", "creative_design", "owner_workflow", "social_systems", "education_learning"} for family in domain_families):
        if "owner_workflow" in domain_families:
            return "behavior_pack_candidate_seed"
        return "direct_bounded_overview" if any(intent == "learn_explain" for intent in owner_intents) else "research_conversation_plan"
    if "market_validation_needed" in evidence_classes or any(meta in {"product_business"} for meta in meta_domains):
        return "research_conversation_plan"
    if novelty_level == "blocked_or_sensitive" or "unknown_risk" in risk_classes:
        return "refusal_boundary"
    if any(family in {"unknown_domain"} for family in domain_families):
        return "clarifying_question"
    return "direct_bounded_overview"



def _infer_behavior_pack_labels(
    domain_families: Sequence[str],
    meta_domains: Sequence[str],
    traits: Sequence[str],
    response_route_family: str,
    novelty_level: str,
    owner_intents: Sequence[str],
    risk_classes: Sequence[str],
    existing_behavior_pack_refs: Sequence[str],
) -> list[str]:
    labels: list[str] = []

    if "owner_workflow" in domain_families:
        labels.append("owner_workflow_pack")
    if any(family in {"privacy_sensitive_technology", "legal_privacy", "policy_governance"} for family in domain_families):
        labels.extend(("privacy_sensitive_technology_candidate_pack", "boundary_review_candidate_pack"))
    if any(family in {"metamaterials", "materials_discovery", "physics", "chemistry"} for family in domain_families):
        labels.append("scientific_research_candidate_pack")
    if any(family in {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"} for family in domain_families):
        labels.append("cognitive_concept_candidate_pack")
    if any(family in {"ai_systems", "machine_learning", "llm_systems", "agentic_systems", "cognitive_architecture", "ai_safety_governance"} for family in domain_families):
        labels.append("ai_system_candidate_pack")
    if any(family in {"medicine_health_research", "biology_life_sciences"} for family in domain_families):
        labels.append("health_research_candidate_pack")
    if any(family in {"industrial_automation", "robotics", "energy_systems", "hardware_electronics"} for family in domain_families):
        labels.append("technical_system_candidate_pack")
    if any(family in {"legal_privacy", "policy_governance"} for family in domain_families):
        labels.append("governance_candidate_pack")
    if any(family in {"software_product", "website_public_launch", "economics_business_strategy"} for family in domain_families):
        labels.append("product_strategy_candidate_pack")
    if any(family in {"language_vocabulary", "education_learning"} for family in domain_families):
        labels.append("language_discovery_candidate_pack")
    if any(family in {"creative_design"} for family in domain_families):
        labels.append("creative_response_candidate_pack")
    if any(family in {"unknown_domain"} for family in domain_families):
        labels.append("unknown_domain_candidate_pack")

    if response_route_family == "privacy_safety_legal_boundary_review":
        labels.append("boundary_review_candidate_pack")
    elif response_route_family == "evidence_mapping":
        labels.append("evidence_mapping_candidate_pack")
    elif response_route_family == "research_conversation_plan":
        labels.append("research_planning_candidate_pack")
    elif response_route_family == "prototype_path_high_level":
        labels.append("prototype_planning_candidate_pack")
    elif response_route_family == "conceptual_theory_path":
        labels.append("conceptual_theory_candidate_pack")
    elif response_route_family == "formal_reasoning_path":
        labels.append("formal_reasoning_candidate_pack")
    elif response_route_family == "behavior_pack_candidate_seed":
        labels.append("behavior_pack_candidate_seed_pack")
    elif response_route_family == "clarifying_question":
        labels.append("clarification_candidate_pack")
    elif response_route_family == "direct_bounded_overview":
        labels.append("bounded_overview_candidate_pack")

    if novelty_level in {"high_uncertainty", "blocked_or_sensitive"} or "unknown_risk" in risk_classes:
        labels.append("boundary_review_candidate_pack")
    if any(intent in {"build_prototype", "evaluate_feasibility"} for intent in owner_intents):
        labels.append("prototype_planning_candidate_pack")
    if any(meta in {"mind_intelligence_consciousness", "formal_reasoning"} for meta in meta_domains):
        labels.append("theory_candidate_pack")
    if existing_behavior_pack_refs:
        labels.extend(f"ref_{_normalize_text(ref).replace(' ', '_')}" for ref in existing_behavior_pack_refs)

    return _ordered_unique(labels)



def _infer_recommended_next_helpers(
    response_route_family: str,
    domain_families: Sequence[str],
    traits: Sequence[str],
    evidence_classes: Sequence[str],
    risk_classes: Sequence[str],
) -> list[str]:
    helpers = ["research_conversation_planner"]
    if response_route_family in {"privacy_safety_legal_boundary_review"} or any(item in risk_classes for item in ("privacy_sensitive", "legal_regulatory_sensitive", "medical_or_health_sensitive")):
        helpers.append("privacy_sensitive_technology_boundary")
    if response_route_family in {"evidence_mapping"} or any(item in evidence_classes for item in ("technical_literature_needed", "experimental_validation_needed", "clinical_validation_needed", "legal_regulatory_sources_needed")):
        helpers.append("new_domain_evidence_mapper")
    if response_route_family in {"prototype_path_high_level"} or "prototype_possible" in traits:
        helpers.append("prototype_path_planner")
    if response_route_family in {"behavior_pack_candidate_seed"} or "owner_workflow" in domain_families:
        helpers.append("domain_behavior_pack_candidate_builder")
    if any(family in {"unknown_domain"} for family in domain_families):
        helpers.append("broad_topic_domain_intake")
    return _ordered_unique(helpers)



def _infer_boundary_flags(risk_classes: Sequence[str], sensitivity_classes: Sequence[str], evidence_classes: Sequence[str]) -> tuple[bool, bool, bool, bool, bool]:
    boundary_review_required = any(item in risk_classes for item in ("privacy_sensitive", "medical_or_health_sensitive", "legal_regulatory_sensitive", "dual_use_or_abuse_potential", "unknown_risk")) or any(item in sensitivity_classes for item in ("privacy_sensitive", "medical_or_health_sensitive", "legal_regulatory_sensitive", "dual_use_or_abuse_potential"))
    evidence_mapping_required = any(item in evidence_classes for item in ("technical_literature_needed", "experimental_validation_needed", "legal_regulatory_sources_needed", "safety_validation_needed", "clinical_validation_needed", "market_validation_needed", "unknown_evidence_needed"))
    research_planning_required = True
    prototype_planning_allowed = not boundary_review_required and "unknown_evidence_needed" not in evidence_classes
    privacy_sensitive = "privacy_sensitive" in risk_classes or "privacy_sensitive" in sensitivity_classes
    safety_sensitive = "safety_critical" in risk_classes or "safety_critical" in sensitivity_classes
    return boundary_review_required, evidence_mapping_required, research_planning_required, prototype_planning_allowed, privacy_sensitive or safety_sensitive



def _safe_metadata(
    descriptor: str,
    prompt_labels: Sequence[str],
    owner_intent_labels: Sequence[str],
    risk_hints: Sequence[str],
    evidence_hints: Sequence[str],
    known_unknown_hints: Sequence[str],
    existing_behavior_pack_refs: Sequence[str],
    packet: BroadTopicOntologyPacket,
) -> dict[str, Any]:
    return {
        "source": "broad_topic_ontology_v1",
        "safe_topic_descriptor": descriptor,
        "prompt_labels": list(prompt_labels),
        "owner_intent_labels": list(owner_intent_labels),
        "risk_hints": list(risk_hints),
        "evidence_hints": list(evidence_hints),
        "known_unknown_hints": list(known_unknown_hints),
        "existing_behavior_pack_refs": list(existing_behavior_pack_refs),
        "packet": _json_safe(packet),
    }



def _deterministic_ontology_id(descriptor: str, domain_families: Sequence[str], novelty_level: str) -> str:
    slug = _slugify(f"{descriptor} {' '.join(domain_families)} {novelty_level}", fallback="broad_topic")
    return f"broad_topic_ontology_{slug}"



def _slugify(text: str, *, fallback: str = "topic") -> str:
    tokens = _split_tokens(text)
    if not tokens:
        return fallback
    return "_".join(tokens[:12])



def _split_tokens(text: str) -> list[str]:
    blob = _normalize_text(text)
    if not blob:
        return []
    token_blob = blob.replace("/", " ").replace("-", " ").replace("_", " ")
    return [tok for tok in token_blob.split() if tok]



def _contains_any_label_sequence(labels: Sequence[str], phrases: Sequence[str]) -> bool:
    return _contains_any_text(" ".join(labels), phrases)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def classify_broad_topic_ontology_v1(
    *,
    safe_topic_descriptor: str,
    prompt_labels: Sequence[Any] | None = None,
    owner_intent_labels: Sequence[Any] | None = None,
    risk_hints: Sequence[Any] | None = None,
    evidence_hints: Sequence[Any] | None = None,
    known_unknown_hints: Sequence[Any] | None = None,
    existing_behavior_pack_refs: Sequence[Any] | None = None,
) -> BroadTopicOntologyPacket:
    descriptor = _safe_text(safe_topic_descriptor)
    if not descriptor:
        raise ValidationError("safe_topic_descriptor_required")

    prompt_labels_n = _normalize_sequence(prompt_labels)
    owner_intent_labels_n = _normalize_sequence(owner_intent_labels)
    risk_hints_n = _normalize_sequence(risk_hints)
    evidence_hints_n = _normalize_sequence(evidence_hints)
    known_unknown_hints_n = _normalize_sequence(known_unknown_hints)
    existing_refs_n = _normalize_sequence(existing_behavior_pack_refs)

    owner_intent = _infer_owner_intent(owner_intent_labels_n, descriptor)
    domain_families = _infer_domain_families(prompt_labels_n, descriptor, owner_intent_labels_n, evidence_hints_n, risk_hints_n, known_unknown_hints_n)
    meta_domains = _infer_meta_domains(domain_families, prompt_labels_n, descriptor, owner_intent_labels_n, evidence_hints_n, risk_hints_n, known_unknown_hints_n)
    traits = _infer_traits(domain_families, meta_domains, prompt_labels_n, descriptor, owner_intent_labels_n, evidence_hints_n, risk_hints_n, known_unknown_hints_n)
    objects_of_study = _infer_objects(domain_families, meta_domains, prompt_labels_n, descriptor)
    evidence_classes = _infer_evidence_classes(domain_families, meta_domains, traits, prompt_labels_n, descriptor, evidence_hints_n, owner_intent_labels_n, risk_hints_n, known_unknown_hints_n)
    novelty_level = _infer_novelty_level(domain_families, traits, prompt_labels_n, evidence_hints_n, known_unknown_hints_n)
    risk_classes = _infer_risk_classes(domain_families, meta_domains, traits, prompt_labels_n, descriptor, risk_hints_n, evidence_hints_n)
    sensitivity_classes = _infer_sensitivity_classes(domain_families, meta_domains, traits, prompt_labels_n, descriptor, risk_classes, evidence_classes)
    response_route_family = _infer_response_route_family(domain_families, meta_domains, traits, novelty_level, evidence_classes, risk_classes, sensitivity_classes, owner_intent_labels_n or [owner_intent], prompt_labels_n, descriptor)
    behavior_pack_candidate_labels = _infer_behavior_pack_labels(domain_families, meta_domains, traits, response_route_family, novelty_level, owner_intent_labels_n or [owner_intent], risk_classes, existing_refs_n)
    recommended_next_helpers = _infer_recommended_next_helpers(response_route_family, domain_families, traits, evidence_classes, risk_classes)
    boundary_review_required, evidence_mapping_required, research_planning_required, prototype_planning_allowed, technical_boundary_flag = _infer_boundary_flags(risk_classes, sensitivity_classes, evidence_classes)
    privacy_sensitive = "privacy_sensitive" in risk_classes or "privacy_sensitive" in sensitivity_classes or "privacy_sensitive_technology" in domain_families
    safety_sensitive = "safety_critical" in risk_classes or "safety_critical" in sensitivity_classes or any(family in {"industrial_automation", "robotics", "energy_systems", "security_safety"} for family in domain_families)
    legal_sensitive = "legal_regulatory_sensitive" in risk_classes or "legal_regulatory_sensitive" in sensitivity_classes or any(family in {"legal_privacy", "policy_governance"} for family in domain_families)
    medical_sensitive = "medical_or_health_sensitive" in risk_classes or "medical_or_health_sensitive" in sensitivity_classes or any(family in {"medicine_health_research"} for family in domain_families)

    if response_route_family == "privacy_safety_legal_boundary_review":
        boundary_review_required = True
    if novelty_level == "blocked_or_sensitive":
        boundary_review_required = True
        prototype_planning_allowed = False
    if any(family in {"unknown_domain"} for family in domain_families):
        evidence_mapping_required = True
    if any(family in {"legal_privacy", "policy_governance", "medicine_health_research", "privacy_sensitive_technology"} for family in domain_families):
        boundary_review_required = True
        evidence_mapping_required = True
    if any(family in {"theory_of_mind", "philosophy_of_mind", "cognitive_science"} for family in domain_families) and "conceptual_definition" in evidence_classes:
        research_planning_required = True
    if any(family in {"metamaterials", "materials_discovery", "physics", "chemistry"} for family in domain_families) and "experimental_validation_needed" in evidence_classes:
        evidence_mapping_required = True
    if any(family in {"software_product", "website_public_launch", "economics_business_strategy"} for family in domain_families):
        research_planning_required = True

    packet = BroadTopicOntologyPacket(
        ontology_id="",
        safe_topic_descriptor=descriptor,
        meta_domains=meta_domains,
        domain_families=domain_families,
        subdomain_traits=traits,
        objects_of_study=objects_of_study,
        owner_intents=[owner_intent] if owner_intent != "unknown_intent" else ["unknown_intent"],
        novelty_level=novelty_level,
        evidence_classes=evidence_classes,
        risk_classes=risk_classes,
        sensitivity_classes=sensitivity_classes,
        response_route_family=response_route_family,
        behavior_pack_candidate_labels=behavior_pack_candidate_labels,
        recommended_next_helpers=recommended_next_helpers,
        boundary_review_required=boundary_review_required,
        evidence_mapping_required=evidence_mapping_required,
        research_planning_required=research_planning_required,
        prototype_planning_allowed=prototype_planning_allowed and not boundary_review_required,
        privacy_sensitive=privacy_sensitive,
        safety_sensitive=safety_sensitive or technical_boundary_flag,
        legal_sensitive=legal_sensitive,
        medical_sensitive=medical_sensitive,
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={},
    )
    ontology_id = _deterministic_ontology_id(descriptor, domain_families, novelty_level)
    return BroadTopicOntologyPacket(**{**asdict(packet), "ontology_id": ontology_id, "safe_metadata": _safe_metadata(descriptor, prompt_labels_n, owner_intent_labels_n, risk_hints_n, evidence_hints_n, known_unknown_hints_n, existing_refs_n, packet)})



def build_broad_topic_ontology_packet_v1(
    *,
    safe_topic_descriptor: str,
    prompt_labels: Sequence[Any] | None = None,
    owner_intent_labels: Sequence[Any] | None = None,
    risk_hints: Sequence[Any] | None = None,
    evidence_hints: Sequence[Any] | None = None,
    known_unknown_hints: Sequence[Any] | None = None,
    existing_behavior_pack_refs: Sequence[Any] | None = None,
) -> BroadTopicOntologyPacket:
    return classify_broad_topic_ontology_v1(
        safe_topic_descriptor=safe_topic_descriptor,
        prompt_labels=prompt_labels,
        owner_intent_labels=owner_intent_labels,
        risk_hints=risk_hints,
        evidence_hints=evidence_hints,
        known_unknown_hints=known_unknown_hints,
        existing_behavior_pack_refs=existing_behavior_pack_refs,
    )



def _validate_known_values(name: str, values: Sequence[str], allowed: set[str]) -> list[str]:
    errors: list[str] = []
    if not isinstance(values, list):
        errors.append(f"{name}_must_be_list")
        return errors
    if not values:
        errors.append(f"{name}_required")
        return errors
    for value in values:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{name}_invalid_value")
        elif value not in allowed:
            errors.append(f"unknown_{name.rstrip('s')}_{value}")
    return errors



def _validate_bool(name: str, value: Any) -> list[str]:
    return [] if type(value) is bool else [f"{name}_must_be_bool"]



def validate_broad_topic_ontology_packet_v1(packet: Mapping[str, Any] | BroadTopicOntologyPacket) -> bool:
    if is_dataclass(packet):
        packet = asdict(packet)
    if not isinstance(packet, Mapping):
        raise ValidationError("packet_must_be_mapping")

    required_keys = {
        "ontology_id",
        "safe_topic_descriptor",
        "meta_domains",
        "domain_families",
        "subdomain_traits",
        "objects_of_study",
        "owner_intents",
        "novelty_level",
        "evidence_classes",
        "risk_classes",
        "sensitivity_classes",
        "response_route_family",
        "behavior_pack_candidate_labels",
        "recommended_next_helpers",
        "boundary_review_required",
        "evidence_mapping_required",
        "research_planning_required",
        "prototype_planning_allowed",
        "privacy_sensitive",
        "safety_sensitive",
        "legal_sensitive",
        "medical_sensitive",
        "public_claim_allowed",
        "iss_internal_reference_allowed",
        "learning_claimed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "safe_metadata",
    }
    missing = [key for key in required_keys if key not in packet]
    if missing:
        raise ValidationError(f"missing_required_fields:{','.join(sorted(missing))}")

    errors: list[str] = []
    if not isinstance(packet.get("ontology_id"), str) or not packet["ontology_id"].strip():
        errors.append("ontology_id_required")
    if not isinstance(packet.get("safe_topic_descriptor"), str) or not packet["safe_topic_descriptor"].strip():
        errors.append("safe_topic_descriptor_required")

    errors.extend(_validate_known_values("meta_domains", packet.get("meta_domains", []), ALLOWED_META_DOMAINS_V1))
    errors.extend(_validate_known_values("domain_families", packet.get("domain_families", []), ALLOWED_DOMAIN_FAMILIES_V1))
    errors.extend(_validate_known_values("subdomain_traits", packet.get("subdomain_traits", []), ALLOWED_SUBDOMAIN_TRAITS_V1))
    errors.extend(_validate_known_values("objects_of_study", packet.get("objects_of_study", []), ALLOWED_OBJECTS_OF_STUDY_V1))
    errors.extend(_validate_known_values("owner_intents", packet.get("owner_intents", []), ALLOWED_OWNER_INTENTS_V1))
    errors.extend(_validate_known_values("evidence_classes", packet.get("evidence_classes", []), ALLOWED_EVIDENCE_CLASSES_V1))
    errors.extend(_validate_known_values("risk_classes", packet.get("risk_classes", []), ALLOWED_RISK_CLASSES_V1))
    errors.extend(_validate_known_values("sensitivity_classes", packet.get("sensitivity_classes", []), ALLOWED_RISK_CLASSES_V1))
    if packet.get("novelty_level") not in ALLOWED_NOVELTY_LEVELS_V1:
        errors.append(f"unknown_novelty_level_{packet.get('novelty_level')}")
    if packet.get("response_route_family") not in ALLOWED_RESPONSE_ROUTE_FAMILIES_V1:
        errors.append(f"unknown_response_route_{packet.get('response_route_family')}")

    for bool_name in (
        "boundary_review_required",
        "evidence_mapping_required",
        "research_planning_required",
        "prototype_planning_allowed",
        "privacy_sensitive",
        "safety_sensitive",
        "legal_sensitive",
        "medical_sensitive",
        "public_claim_allowed",
        "iss_internal_reference_allowed",
        "learning_claimed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
    ):
        errors.extend(_validate_bool(bool_name, packet.get(bool_name)))

    if packet.get("public_claim_allowed") is not False:
        errors.append("public_claim_must_be_false")
    if packet.get("learning_claimed") is not False:
        errors.append("learning_claim_must_be_false")
    if packet.get("runtime_authority") is not False:
        errors.append("runtime_authority_must_be_false")
    if packet.get("writes_state") is not False:
        errors.append("writes_state_must_be_false")
    if packet.get("model_provider_used") is not False:
        errors.append("model_provider_used_must_be_false")

    errors.extend(_collect_forbidden_fields(packet))
    if _contains_forbidden_claim_marker(packet):
        errors.append("forbidden_claim_marker_detected")

    if errors:
        raise ValidationError(";".join(_ordered_unique(errors)))
    return True



def summarize_broad_topic_ontology_packet_v1(packet: Mapping[str, Any] | BroadTopicOntologyPacket) -> BroadTopicOntologySummary:
    if is_dataclass(packet):
        packet = asdict(packet)
    validate_broad_topic_ontology_packet_v1(packet)
    return BroadTopicOntologySummary(
        summary_type=SUMMARY_TYPE_V1,
        ontology_id=_safe_text(packet["ontology_id"]),
        safe_topic_descriptor=_safe_text(packet["safe_topic_descriptor"]),
        meta_domains=list(packet["meta_domains"]),
        domain_families=list(packet["domain_families"]),
        evidence_classes=list(packet["evidence_classes"]),
        risk_classes=list(packet["risk_classes"]),
        response_route_family=_safe_text(packet["response_route_family"]),
        boundary_review_required=bool(packet["boundary_review_required"]),
        evidence_mapping_required=bool(packet["evidence_mapping_required"]),
        research_planning_required=bool(packet["research_planning_required"]),
        prototype_planning_allowed=bool(packet["prototype_planning_allowed"]),
        behavior_pack_candidate_count=len(packet["behavior_pack_candidate_labels"]),
    )



def to_broad_topic_ontology_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def build_initial_broad_topic_ontology_examples_v1() -> dict[str, BroadTopicOntologyPacket]:
    examples: dict[str, BroadTopicOntologyPacket] = {
        "metamaterials_frontier_research_ontology": build_broad_topic_ontology_packet_v1(
            safe_topic_descriptor="Metamaterials frontier research",
            prompt_labels=("metamaterials", "materials discovery", "frontier research", "experimental validation"),
            owner_intent_labels=("research",),
            evidence_hints=("technical literature", "experimental validation"),
            known_unknown_hints=("frontier", "high uncertainty"),
        ),
        "wifi_rf_self_care_sensing_ontology": build_broad_topic_ontology_packet_v1(
            safe_topic_descriptor="WiFi/RF sensing for self-care",
            prompt_labels=("wifi sensing", "rf sensing", "human sensing", "privacy", "consent", "self-care"),
            owner_intent_labels=("research",),
            risk_hints=("privacy sensitive", "medical adjacent", "lawful only"),
            evidence_hints=("technical literature", "legal/privacy", "safety validation"),
            known_unknown_hints=("unfamiliar", "researchable"),
        ),
        "theory_of_mind_conceptual_ontology": build_broad_topic_ontology_packet_v1(
            safe_topic_descriptor="Theory of mind conceptual research",
            prompt_labels=("theory of mind", "philosophy of mind", "cognitive science"),
            owner_intent_labels=("learn explain",),
            evidence_hints=("conceptual definition", "technical literature"),
            known_unknown_hints=("high uncertainty",),
        ),
        "ai_agent_architecture_ontology": build_broad_topic_ontology_packet_v1(
            safe_topic_descriptor="AI agent architecture and governance",
            prompt_labels=("ai systems", "agentic systems", "cognitive architecture", "ai safety governance"),
            owner_intent_labels=("research",),
            risk_hints=("public claim sensitive", "safety critical"),
            evidence_hints=("technical literature", "safety validation"),
            known_unknown_hints=("adjacent",),
        ),
        "medical_software_regulated_path_ontology": build_broad_topic_ontology_packet_v1(
            safe_topic_descriptor="Medical software regulated path",
            prompt_labels=("medicine health research", "software product", "clinical validation"),
            owner_intent_labels=("evaluate feasibility",),
            risk_hints=("medical sensitive", "regulated domain"),
            evidence_hints=("clinical validation", "legal/regulatory", "safety validation"),
            known_unknown_hints=("unfamiliar",),
        ),
        "philosophy_of_mind_ontology": build_broad_topic_ontology_packet_v1(
            safe_topic_descriptor="Philosophy of mind",
            prompt_labels=("philosophy of mind", "formal reasoning"),
            owner_intent_labels=("learn explain",),
            evidence_hints=("conceptual definition",),
            known_unknown_hints=("known existing pack",),
        ),
        "industrial_automation_control_ontology": build_broad_topic_ontology_packet_v1(
            safe_topic_descriptor="Industrial automation control system",
            prompt_labels=("industrial automation", "PLC", "control system", "equipment"),
            owner_intent_labels=("troubleshooting",),
            risk_hints=("safety critical",),
            evidence_hints=("technical literature", "safety validation"),
            known_unknown_hints=("adjacent",),
        ),
        "energy_storage_system_ontology": build_broad_topic_ontology_packet_v1(
            safe_topic_descriptor="Energy storage system planning",
            prompt_labels=("energy systems", "battery", "storage", "power"),
            owner_intent_labels=("build prototype",),
            risk_hints=("safety critical",),
            evidence_hints=("technical literature", "safety validation"),
            known_unknown_hints=("adjacent",),
        ),
        "legal_privacy_policy_ontology": build_broad_topic_ontology_packet_v1(
            safe_topic_descriptor="Legal/privacy policy review",
            prompt_labels=("legal privacy", "policy governance", "compliance"),
            owner_intent_labels=("safety legal privacy review",),
            risk_hints=("legal regulatory sensitive", "privacy sensitive"),
            evidence_hints=("legal/regulatory",),
            known_unknown_hints=("unfamiliar",),
        ),
        "language_vocabulary_discovery_ontology": build_broad_topic_ontology_packet_v1(
            safe_topic_descriptor="Language vocabulary discovery",
            prompt_labels=("language vocabulary", "meaning", "definition"),
            owner_intent_labels=("learn explain",),
            evidence_hints=("conceptual definition",),
            known_unknown_hints=("known existing pack",),
        ),
        "software_product_planning_ontology": build_broad_topic_ontology_packet_v1(
            safe_topic_descriptor="Software product planning",
            prompt_labels=("software product", "product strategy", "feature planning"),
            owner_intent_labels=("commercial product strategy",),
            risk_hints=("public claim sensitive",),
            evidence_hints=("market validation", "user context"),
            known_unknown_hints=("adjacent",),
        ),
        "unknown_future_topic_ontology": build_broad_topic_ontology_packet_v1(
            safe_topic_descriptor="Unknown future topic",
            prompt_labels=("unknown", "future topic"),
            owner_intent_labels=("unknown",),
            risk_hints=("high uncertainty",),
            evidence_hints=("unknown evidence"),
            known_unknown_hints=("high uncertainty",),
        ),
    }
    return examples


__all__ = [
    "ALLOWED_DOMAIN_FAMILIES_V1",
    "ALLOWED_EVIDENCE_CLASSES_V1",
    "ALLOWED_META_DOMAINS_V1",
    "ALLOWED_NOVELTY_LEVELS_V1",
    "ALLOWED_OBJECTS_OF_STUDY_V1",
    "ALLOWED_OWNER_INTENTS_V1",
    "ALLOWED_RESPONSE_ROUTE_FAMILIES_V1",
    "ALLOWED_RISK_CLASSES_V1",
    "ALLOWED_SUBDOMAIN_TRAITS_V1",
    "BroadTopicOntologyPacket",
    "BroadTopicOntologySummary",
    "HELPER_TYPE_V1",
    "ONTOLOGY_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "ValidationError",
    "build_broad_topic_ontology_packet_v1",
    "build_initial_broad_topic_ontology_examples_v1",
    "classify_broad_topic_ontology_v1",
    "summarize_broad_topic_ontology_packet_v1",
    "to_broad_topic_ontology_json_safe_v1",
    "validate_broad_topic_ontology_packet_v1",
]
