"""Metadata-only broad topic domain intake helper v1.

This module classifies safe topic descriptors and metadata labels into broad
research/domain intake categories before any later response planning.

It is pure, deterministic, import-safe, and fail-closed.
No model/provider/search/advisor calls. No network. No I/O. No state writes.
No chat routing. No runtime behavior changes.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping, Sequence

from weslr.behavior_pack_registry import (
    PACK_BOUNDARY,
    PACK_IDENTITY,
    PACK_OWNER,
    PACK_UNKNOWN,
)
from weslr.broad_topic_ontology import build_broad_topic_ontology_packet_v1, to_broad_topic_ontology_json_safe_v1

HELPER_TYPE_V1 = "broad_topic_domain_intake_helper_v1"
INTAKE_TYPE_V1 = "broad_topic_domain_intake_v1"
CLASSIFICATION_TYPE_V1 = "broad_topic_domain_classification_v1"
SUMMARY_TYPE_V1 = "broad_topic_domain_intake_summary_v1"

ALLOWED_DOMAIN_FAMILIES_V1 = {
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
    "ai_systems",
    "agentic_systems",
    "ai_safety_governance",
    "cognitive_architecture",
    "theory_of_mind",
    "philosophy_of_mind",
    "cognitive_science",
    "psychology",
    "neuroscience",
    "medicine_health_research",
    "biology_life_sciences",
    "physics",
    "chemistry",
    "unknown_domain",
}

ALLOWED_NOVELTY_LEVELS_V1 = {
    "known_existing_pack",
    "adjacent_to_existing_pack",
    "unfamiliar_but_researchable",
    "high_uncertainty",
    "blocked_or_sensitive",
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

ALLOWED_EVIDENCE_NEED_LEVELS_V1 = {
    "low",
    "medium",
    "high",
    "must_collect_before_claims",
}

ALLOWED_RISK_LEVELS_V1 = {"low", "medium", "high", "blocked"}

ALLOWED_NEXT_STAGES_V1 = {
    "direct_bounded_overview",
    "research_conversation_plan",
    "prototype_path_high_level",
    "evidence_mapping",
    "privacy_safety_legal_boundary_review",
    "clarifying_question",
    "refusal_boundary",
    "behavior_pack_candidate_seed",
    "conceptual_theory_path",
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

PRIVACY_SENSITIVE_TECH_TOKENS_V1 = {
    "wifi",
    "wi-fi",
    "rf",
    "radio frequency",
    "sensing",
    "human sensing",
    "presence",
    "location",
    "tracking",
    "track people",
    "track persons",
    "surveillance",
    "biometric",
    "biometrics",
    "covert",
    "monitoring",
    "home monitoring",
    "workplace monitoring",
    "minors",
    "vulnerable people",
}

CONSENT_LAWFULNESS_TOKENS_V1 = {
    "consent",
    "consented",
    "lawful",
    "lawfully",
    "authorized",
    "authorization",
    "permission",
    "permitted",
    "ethically",
    "ethical",
    "approved",
    "opt in",
    "opt-in",
}

SAFETY_SENSITIVE_TOKENS_V1 = {
    "safety",
    "hazard",
    "risk",
    "power",
    "battery",
    "inverter",
    "grid",
    "high voltage",
    "control",
    "controls",
    "hardware",
    "equipment",
    "robot",
    "robotics",
    "actuator",
    "motor",
}

LEGAL_PRIVACY_TOKENS_V1 = {
    "legal",
    "privacy",
    "consent",
    "policy",
    "compliance",
    "gdpr",
    "law",
    "regulatory",
    "terms",
    "surveillance",
}

INDUSTRIAL_AUTOMATION_TOKENS_V1 = {
    "industrial",
    "automation",
    "plc",
    "scada",
    "control system",
    "control",
    "equipment",
    "operational technology",
    "ot system",
    "factory",
    "manufacturing",
}

MATERIALS_DISCOVERY_TOKENS_V1 = {
    "materials",
    "material",
    "alloy",
    "compound",
    "chemistry",
    "catalyst",
    "crystal",
    "polymer",
    "discovery",
    "synthesis",
}

ENERGY_SYSTEM_TOKENS_V1 = {
    "energy",
    "battery",
    "grid",
    "solar",
    "power",
    "inverter",
    "storage",
    "microgrid",
    "electrical",
}

ROBOTICS_TOKENS_V1 = {
    "robot",
    "robotics",
    "manipulator",
    "autonomous",
    "ros",
    "motion",
    "actuator",
    "navigation",
    "perception",
}

SOFTWARE_PRODUCT_TOKENS_V1 = {
    "software",
    "product",
    "app",
    "saas",
    "api",
    "backend",
    "frontend",
    "platform",
    "feature",
    "architecture",
    "engineering",
    "devtool",
}

WEBSITE_PUBLIC_LAUNCH_TOKENS_V1 = {
    "website",
    "public launch",
    "launch",
    "landing page",
    "homepage",
    "seo",
    "marketing site",
    "public site",
    "checkout",
}

LANGUAGE_VOCABULARY_TOKENS_V1 = {
    "language",
    "vocabulary",
    "vocab",
    "word",
    "words",
    "term",
    "definition",
    "meaning",
    "semantics",
    "translation",
    "synonym",
}

OWNER_WORKFLOW_TOKENS_V1 = {
    "owner workflow",
    "workflow",
    "weslr",
    "behavior pack",
    "behavior pack registry",
    "replay",
    "friction",
    "proof",
    "governance",
    "router",
    "selector",
    "response fit",
    "prompt handling",
    "internal process",
}

TECHNICAL_RESEARCH_TOKENS_V1 = {
    "technical",
    "research",
    "engineering",
    "system",
    "protocol",
    "algorithm",
    "architecture",
    "signal",
    "sensor",
    "simulation",
    "network",
    "database",
    "model",
    "firmware",
    "electronics",
}

KNOWN_OWNER_INTENT_TOKENS_V1 = {
    "learn_explain": {"learn", "explain", "understand", "what is", "what are", "overview", "teach"},
    "research": {"research", "study", "investigate", "explore", "analyze", "analysis", "literature"},
    "build_prototype": {"build", "prototype", "implement", "make", "develop", "create", "poc"},
    "evaluate_feasibility": {"feasibility", "viable", "possible", "can this work", "evaluate", "assess"},
    "safety_legal_privacy_review": {"safety", "legal", "privacy", "compliance", "risk review", "boundary review"},
    "commercial_product_strategy": {"commercial", "product", "strategy", "launch", "market", "pricing", "business"},
    "troubleshooting": {"troubleshoot", "debug", "fix", "broken", "issue", "problem", "error", "bug"},
}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class BroadTopicDomainClassification:
    domain_family: str
    novelty_level: str
    owner_intent: str
    evidence_need_level: str
    risk_level: str
    risk_labels: tuple[str, ...]
    recommended_next_stage: str
    candidate_behavior_pack_labels: tuple[str, ...]
    boundary_review_required: bool
    evidence_mapping_required: bool
    research_planning_required: bool
    prototype_planning_allowed: bool
    privacy_sensitive: bool
    safety_sensitive: bool
    legal_sensitive: bool
    public_claim_allowed: bool
    iss_internal_reference_allowed: bool
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_metadata: dict[str, Any] | None = None
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


@dataclass(frozen=True, slots=True)
class BroadTopicDomainIntake:
    intake_id: str
    safe_topic_descriptor: str
    domain_family: str
    novelty_level: str
    owner_intent: str
    evidence_need_level: str
    risk_level: str
    risk_labels: tuple[str, ...]
    recommended_next_stage: str
    candidate_behavior_pack_labels: tuple[str, ...]
    boundary_review_required: bool
    evidence_mapping_required: bool
    research_planning_required: bool
    prototype_planning_allowed: bool
    privacy_sensitive: bool
    safety_sensitive: bool
    legal_sensitive: bool
    public_claim_allowed: bool
    iss_internal_reference_allowed: bool
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_metadata: dict[str, Any] | None = None
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


@dataclass(frozen=True, slots=True)
class BroadTopicDomainIntakeSummary:
    summary_type: str
    intake_id: str
    domain_family: str
    novelty_level: str
    owner_intent: str
    evidence_need_level: str
    risk_level: str
    recommended_next_stage: str
    boundary_review_required: bool
    evidence_mapping_required: bool
    research_planning_required: bool
    prototype_planning_allowed: bool
    risk_label_count: int


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



def _dedupe_preserve(items: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        text = _normalize_text(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return tuple(out)


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



def _split_tokens(text: str) -> tuple[str, ...]:
    blob = _normalize_text(text)
    if not blob:
        return ()
    token_blob = blob.replace("/", " ").replace("-", " ").replace("_", " ")
    return tuple(tok for tok in token_blob.split() if tok)



def _slugify(text: str, *, fallback: str = "topic") -> str:
    tokens = _split_tokens(text)
    if not tokens:
        return fallback
    return "_".join(tokens[:12])



def _contains_any_text(blob: str, phrases: Iterable[str]) -> bool:
    haystack = _normalize_text(blob)
    return any(_normalize_text(phrase) in haystack for phrase in phrases)



def _contains_any_label(labels: Sequence[str], phrases: Iterable[str]) -> bool:
    return _contains_any_text(" ".join(labels), phrases)



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
        if has_base and has_qualifier:
            return True
        return False
    return False



def _as_bool(value: Any) -> bool:
    return type(value) is bool and value is True



def _matches(labels: Sequence[str], phrases: Iterable[str]) -> bool:
    return _contains_any_label(labels, phrases)



def _domain_family_from_labels(labels: Sequence[str], descriptor: str) -> str:
    blob = " ".join((descriptor, " ".join(labels)))
    if _matches(labels, PRIVACY_SENSITIVE_TECH_TOKENS_V1) or _contains_any_text(blob, PRIVACY_SENSITIVE_TECH_TOKENS_V1):
        return "privacy_sensitive_technology"
    if _matches(labels, LEGAL_PRIVACY_TOKENS_V1):
        return "legal_privacy"
    if _matches(labels, INDUSTRIAL_AUTOMATION_TOKENS_V1):
        return "industrial_automation"
    if _matches(labels, MATERIALS_DISCOVERY_TOKENS_V1):
        return "materials_discovery"
    if _matches(labels, ENERGY_SYSTEM_TOKENS_V1):
        return "energy_systems"
    if _matches(labels, ROBOTICS_TOKENS_V1):
        return "robotics"
    if _contains_any_text(blob, WEBSITE_PUBLIC_LAUNCH_TOKENS_V1):
        return "website_public_launch"
    if _matches(labels, SOFTWARE_PRODUCT_TOKENS_V1):
        return "software_product"
    if _matches(labels, LANGUAGE_VOCABULARY_TOKENS_V1):
        return "language_vocabulary"
    if _matches(labels, OWNER_WORKFLOW_TOKENS_V1):
        return "owner_workflow"
    if _matches(labels, TECHNICAL_RESEARCH_TOKENS_V1) or _contains_any_text(blob, TECHNICAL_RESEARCH_TOKENS_V1):
        return "technical_research"
    return "unknown_domain"



def _intent_from_labels(labels: Sequence[str], descriptor: str) -> str:
    blob = " ".join((descriptor, " ".join(labels)))
    for intent, phrases in KNOWN_OWNER_INTENT_TOKENS_V1.items():
        if _contains_any_text(blob, phrases):
            return intent
    if not labels and not _normalize_text(descriptor):
        return "unknown_intent"
    return "unknown_intent"



def _novelty_from_hints(labels: Sequence[str], known_unknown_hints: Sequence[str], domain_family: str) -> str:
    blob = " ".join((" ".join(labels), " ".join(known_unknown_hints)))
    if _contains_any_text(blob, {"blocked", "sensitive", "unsafe", "covert", "surveillance"}):
        return "blocked_or_sensitive"
    if _contains_any_text(blob, {"known existing pack", "existing pack", "known pack", "already known"}):
        return "known_existing_pack"
    if _contains_any_text(blob, {"adjacent", "nearby", "similar to existing", "related pack"}):
        return "adjacent_to_existing_pack"
    if _contains_any_text(blob, {"high uncertainty", "uncertain", "unknown", "unfamiliar"}):
        return "high_uncertainty" if domain_family == "unknown_domain" else "unfamiliar_but_researchable"
    if domain_family == "unknown_domain":
        return "high_uncertainty"
    return "unfamiliar_but_researchable"



def _risk_level_from_family(domain_family: str, risk_hints: Sequence[str], labels: Sequence[str]) -> str:
    blob = " ".join((" ".join(risk_hints), " ".join(labels)))
    if _contains_any_text(blob, {"blocked", "unsafe", "surveillance", "illegal", "weapon", "harm"}):
        return "blocked"
    if domain_family in {"privacy_sensitive_technology", "legal_privacy", "medicine_health_research"}:
        return "high"
    if domain_family in {"industrial_automation", "robotics", "energy_systems"} and _contains_any_text(blob, SAFETY_SENSITIVE_TOKENS_V1):
        return "high"
    if domain_family in {"materials_discovery"}:
        return "high" if _contains_any_text(blob, {"hazard", "unsafe", "toxic"}) else "medium"
    if domain_family in {"software_product", "website_public_launch", "owner_workflow", "language_vocabulary", "technical_research"}:
        return "medium"
    if domain_family == "unknown_domain":
        return "high"
    return "medium"



def _evidence_need_from_inputs(domain_family: str, novelty_level: str, owner_intent: str, risk_level: str, labels: Sequence[str]) -> str:
    blob = " ".join(labels)
    if risk_level == "blocked" or novelty_level == "blocked_or_sensitive":
        return "must_collect_before_claims"
    if domain_family in {"privacy_sensitive_technology", "legal_privacy", "medicine_health_research"}:
        return "must_collect_before_claims"
    if domain_family == "materials_discovery":
        return "high"
    if domain_family in {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"}:
        return "high" if owner_intent in {"research", "evaluate_feasibility", "build_prototype"} else "medium"
    if domain_family in {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"}:
        return "high" if novelty_level == "high_uncertainty" else "medium"
    if domain_family == "energy_systems":
        return "high" if _contains_any_text(blob, SAFETY_SENSITIVE_TOKENS_V1) or owner_intent == "build_prototype" else "medium"
    if domain_family == "robotics":
        return "high" if owner_intent in {"build_prototype", "evaluate_feasibility"} else "medium"
    if domain_family in {"software_product", "website_public_launch"}:
        return "medium"
    if domain_family == "language_vocabulary":
        return "low" if owner_intent == "learn_explain" else "medium"
    if domain_family == "owner_workflow":
        return "medium"
    if domain_family == "unknown_domain" or novelty_level == "high_uncertainty":
        return "must_collect_before_claims"
    return "high" if owner_intent == "research" else "medium"



def _has_consent_lawfulness_signals(labels: Sequence[str], descriptor: str) -> bool:
    blob = " ".join((descriptor, " ".join(labels)))
    return _contains_any_text(blob, CONSENT_LAWFULNESS_TOKENS_V1)



def _has_privacy_signals(labels: Sequence[str], descriptor: str) -> bool:
    blob = " ".join((descriptor, " ".join(labels)))
    return _contains_any_text(blob, PRIVACY_SENSITIVE_TECH_TOKENS_V1)



def _has_safety_signals(labels: Sequence[str], descriptor: str) -> bool:
    blob = " ".join((descriptor, " ".join(labels)))
    return _contains_any_text(blob, SAFETY_SENSITIVE_TOKENS_V1)



def _has_legal_signals(labels: Sequence[str], descriptor: str) -> bool:
    blob = " ".join((descriptor, " ".join(labels)))
    return _contains_any_text(blob, LEGAL_PRIVACY_TOKENS_V1)



def _candidate_behavior_pack_labels(domain_family: str, novelty_level: str, owner_intent: str, risk_level: str) -> tuple[str, ...]:
    labels: list[str] = []
    if domain_family == "privacy_sensitive_technology":
        labels.extend(("privacy_sensitive_technology_candidate_pack", "safety_boundary_candidate_pack"))
    elif domain_family == "industrial_automation":
        labels.append("industrial_automation_candidate_pack")
    elif domain_family == "legal_privacy":
        labels.extend(("legal_privacy_candidate_pack", "boundary_review_candidate_pack"))
    elif domain_family == "materials_discovery":
        labels.append("materials_discovery_candidate_pack")
    elif domain_family == "energy_systems":
        labels.append("energy_systems_candidate_pack")
    elif domain_family == "robotics":
        labels.append("robotics_candidate_pack")
    elif domain_family == "software_product":
        labels.append("software_product_candidate_pack")
    elif domain_family == "website_public_launch":
        labels.append("website_public_launch_candidate_pack")
    elif domain_family == "language_vocabulary":
        labels.append("language_vocabulary_discovery_candidate_pack")
    elif domain_family == "owner_workflow":
        labels.extend(("owner_workflow_pack", "owner_workflow_candidate_pack"))
    elif domain_family == "technical_research":
        labels.append("technical_research_candidate_pack")
    elif domain_family in {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"}:
        labels.extend(("ai_systems_candidate_pack", "cognitive_architecture_candidate_pack"))
    elif domain_family in {"theory_of_mind", "philosophy_of_mind", "cognitive_science", "psychology", "neuroscience"}:
        labels.extend(("mind_intelligence_candidate_pack", "conceptual_reasoning_candidate_pack"))
    elif domain_family == "medicine_health_research":
        labels.extend(("medicine_health_candidate_pack", "regulatory_boundary_candidate_pack"))
    else:
        labels.append("unknown_domain_candidate_pack")

    if owner_intent in {"research", "evaluate_feasibility", "build_prototype"}:
        labels.append("research_planning_candidate_pack")
    if owner_intent == "build_prototype":
        labels.append("prototype_planning_candidate_pack")
    if novelty_level in {"high_uncertainty", "blocked_or_sensitive"} or risk_level in {"high", "blocked"}:
        labels.append("boundary_review_candidate_pack")
    if domain_family in {"privacy_sensitive_technology", "legal_privacy"}:
        labels.append("evidence_mapping_candidate_pack")
    return tuple(_dedupe_preserve(labels))



def _recommended_next_stage(
    domain_family: str,
    novelty_level: str,
    owner_intent: str,
    risk_level: str,
    labels: Sequence[str],
    descriptor: str,
) -> str:
    consented = _has_consent_lawfulness_signals(labels, descriptor)
    if novelty_level == "blocked_or_sensitive" or risk_level == "blocked":
        return "refusal_boundary"
    if domain_family == "privacy_sensitive_technology":
        if consented and owner_intent in {"research", "build_prototype", "evaluate_feasibility"}:
            return "research_conversation_plan"
        return "privacy_safety_legal_boundary_review"
    if domain_family == "industrial_automation":
        return "research_conversation_plan" if owner_intent != "troubleshooting" else "direct_bounded_overview"
    if domain_family == "legal_privacy":
        return "evidence_mapping" if owner_intent != "safety_legal_privacy_review" else "privacy_safety_legal_boundary_review"
    if domain_family == "materials_discovery":
        return "evidence_mapping" if owner_intent == "evaluate_feasibility" else "research_conversation_plan"
    if domain_family in {"ai_systems", "agentic_systems", "ai_safety_governance", "cognitive_architecture"}:
        return "research_conversation_plan"
    if domain_family == "theory_of_mind" or domain_family == "philosophy_of_mind" or domain_family == "cognitive_science":
        return "conceptual_theory_path" if owner_intent == "learn_explain" else "research_conversation_plan"
    if domain_family in {"psychology", "neuroscience", "medicine_health_research", "biology_life_sciences"}:
        return "privacy_safety_legal_boundary_review" if domain_family == "medicine_health_research" else "research_conversation_plan"
    if domain_family == "energy_systems":
        return "prototype_path_high_level" if owner_intent == "build_prototype" else "research_conversation_plan"
    if domain_family == "robotics":
        return "prototype_path_high_level" if owner_intent == "build_prototype" else "research_conversation_plan"
    if domain_family == "software_product":
        if owner_intent == "commercial_product_strategy":
            return "research_conversation_plan"
        if owner_intent == "build_prototype":
            return "prototype_path_high_level"
        return "direct_bounded_overview" if owner_intent == "learn_explain" else "research_conversation_plan"
    if domain_family == "website_public_launch":
        return "prototype_path_high_level" if owner_intent == "build_prototype" else "research_conversation_plan"
    if domain_family == "language_vocabulary":
        return "direct_bounded_overview" if owner_intent == "learn_explain" else "research_conversation_plan"
    if domain_family == "owner_workflow":
        return "behavior_pack_candidate_seed" if _contains_any_text(" ".join(labels), {"friction", "repeat", "repeated", "regression", "candidate pack", "pattern miner"}) else "research_conversation_plan"
    if domain_family == "technical_research":
        return "research_conversation_plan" if owner_intent != "build_prototype" else "prototype_path_high_level"
    if domain_family == "unknown_domain":
        return "clarifying_question" if risk_level == "low" else "evidence_mapping"
    return "clarifying_question"



def _boundary_flags(domain_family: str, novelty_level: str, risk_level: str) -> tuple[bool, bool, bool]:
    privacy_sensitive = domain_family == "privacy_sensitive_technology"
    safety_sensitive = domain_family in {"industrial_automation", "energy_systems", "robotics"}
    legal_sensitive = domain_family == "legal_privacy"
    if novelty_level == "blocked_or_sensitive":
        privacy_sensitive = True
        safety_sensitive = True
        legal_sensitive = True
    return privacy_sensitive, safety_sensitive, legal_sensitive



def _prototype_allowed(
    domain_family: str,
    novelty_level: str,
    risk_level: str,
    labels: Sequence[str],
    descriptor: str,
) -> bool:
    if risk_level == "blocked" or novelty_level == "blocked_or_sensitive":
        return False
    if domain_family == "privacy_sensitive_technology":
        return _has_consent_lawfulness_signals(labels, descriptor)
    if domain_family in {"legal_privacy", "unknown_domain"}:
        return False
    if domain_family == "language_vocabulary":
        return False
    if domain_family in {"software_product", "website_public_launch", "industrial_automation", "materials_discovery", "energy_systems", "robotics", "technical_research", "owner_workflow"}:
        return True
    return False



def _build_safe_metadata(
    descriptor: str,
    prompt_labels: Sequence[str],
    owner_intent_labels: Sequence[str],
    risk_hints: Sequence[str],
    known_unknown_hints: Sequence[str],
    existing_behavior_pack_refs: Sequence[str],
    classification: BroadTopicDomainClassification,
) -> dict[str, Any]:
    return {
        "source": "broad_topic_domain_intake_v1",
        "safe_topic_descriptor": descriptor,
        "prompt_labels": list(prompt_labels),
        "owner_intent_labels": list(owner_intent_labels),
        "risk_hints": list(risk_hints),
        "known_unknown_hints": list(known_unknown_hints),
        "existing_behavior_pack_refs": list(existing_behavior_pack_refs),
        "ontology": _json_safe(classification.safe_metadata.get("ontology", {})),
        "classification": _json_safe(classification),
    }



def _deterministic_intake_id(descriptor: str, domain_family: str, novelty_level: str) -> str:
    slug = _slugify(f"{descriptor} {domain_family} {novelty_level}", fallback="broad_topic")
    return f"broad_topic_domain_intake_{slug}"



def _normalize_pack_refs(existing_behavior_pack_refs: Sequence[Any] | None) -> tuple[str, ...]:
    return _normalize_sequence(existing_behavior_pack_refs)


def _ontology_payload_from_inputs(
    *,
    descriptor: str,
    prompt_labels: Sequence[str],
    owner_intent_labels: Sequence[str],
    risk_hints: Sequence[str],
    known_unknown_hints: Sequence[str],
    existing_behavior_pack_refs: Sequence[str],
):
    return build_broad_topic_ontology_packet_v1(
        safe_topic_descriptor=descriptor,
        prompt_labels=prompt_labels,
        owner_intent_labels=owner_intent_labels,
        risk_hints=risk_hints,
        evidence_hints=(),
        known_unknown_hints=known_unknown_hints,
        existing_behavior_pack_refs=existing_behavior_pack_refs,
    )


def _prefer_ontology_domain_family(flat_domain_family: str, ontology_domain_families: Sequence[str]) -> str:
    ontology_primary = next((family for family in ontology_domain_families if family != "unknown_domain"), "unknown_domain")
    if not ontology_primary or ontology_primary == flat_domain_family:
        return flat_domain_family
    if flat_domain_family in {"technical_research", "unknown_domain", "software_product"} and ontology_primary in {
        "ai_systems",
        "agentic_systems",
        "ai_safety_governance",
        "cognitive_architecture",
        "theory_of_mind",
        "philosophy_of_mind",
        "cognitive_science",
    }:
        return ontology_primary
    return flat_domain_family


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def classify_broad_topic_domain_v1(
    *,
    safe_topic_descriptor: str,
    prompt_labels: Sequence[Any] | None = None,
    owner_intent_labels: Sequence[Any] | None = None,
    risk_hints: Sequence[Any] | None = None,
    known_unknown_hints: Sequence[Any] | None = None,
    existing_behavior_pack_refs: Sequence[Any] | None = None,
) -> BroadTopicDomainClassification:
    descriptor = _safe_text(safe_topic_descriptor)
    if not descriptor:
        raise ValidationError("safe_topic_descriptor_required")

    prompt_labels_n = _normalize_sequence(prompt_labels)
    owner_intent_labels_n = _normalize_sequence(owner_intent_labels)
    risk_hints_n = _normalize_sequence(risk_hints)
    known_unknown_hints_n = _normalize_sequence(known_unknown_hints)
    existing_refs_n = _normalize_pack_refs(existing_behavior_pack_refs)

    ontology = _ontology_payload_from_inputs(
        descriptor=descriptor,
        prompt_labels=prompt_labels_n,
        owner_intent_labels=owner_intent_labels_n,
        risk_hints=risk_hints_n,
        known_unknown_hints=known_unknown_hints_n,
        existing_behavior_pack_refs=existing_refs_n,
    )

    domain_family = _domain_family_from_labels(prompt_labels_n, descriptor)
    ontology_domain_family = _prefer_ontology_domain_family(domain_family, ontology.domain_families)
    if _contains_any_text(" ".join((descriptor, " ".join(prompt_labels_n), " ".join(known_unknown_hints_n))), {"privacy", "surveillance", "tracking", "biometric", "human sensing"}) and ontology_domain_family in {"technical_research", "unknown_domain"}:
        ontology_domain_family = "privacy_sensitive_technology"
    domain_family = ontology_domain_family

    owner_intent = _intent_from_labels(owner_intent_labels_n, descriptor)
    if owner_intent == "unknown_intent":
        owner_intent = _intent_from_labels(prompt_labels_n, descriptor)

    novelty_level = _novelty_from_hints(prompt_labels_n + owner_intent_labels_n, known_unknown_hints_n, domain_family)
    risk_level = _risk_level_from_family(domain_family, risk_hints_n, prompt_labels_n + owner_intent_labels_n)
    if novelty_level == "blocked_or_sensitive":
        risk_level = "blocked"
    evidence_need_level = _evidence_need_from_inputs(domain_family, novelty_level, owner_intent, risk_level, prompt_labels_n + risk_hints_n + known_unknown_hints_n)
    boundary_review_required = domain_family in {"privacy_sensitive_technology", "legal_privacy"} or risk_level in {"high", "blocked"} or evidence_need_level == "must_collect_before_claims"
    evidence_mapping_required = evidence_need_level in {"high", "must_collect_before_claims"} or domain_family in {"materials_discovery", "unknown_domain"}
    research_planning_required = True if domain_family != "unknown_domain" or owner_intent != "unknown_intent" else True
    prototype_planning_allowed = _prototype_allowed(domain_family, novelty_level, risk_level, prompt_labels_n + owner_intent_labels_n, descriptor)
    privacy_sensitive, safety_sensitive, legal_sensitive = _boundary_flags(domain_family, novelty_level, risk_level)
    if domain_family == "privacy_sensitive_technology":
        privacy_sensitive = True
        legal_sensitive = True
        boundary_review_required = True
        evidence_mapping_required = True
    if domain_family == "legal_privacy":
        legal_sensitive = True
        boundary_review_required = True
        evidence_mapping_required = True
    if domain_family == "medicine_health_research":
        safety_sensitive = True
        legal_sensitive = True
        boundary_review_required = True
        evidence_mapping_required = True
    if domain_family == "energy_systems" and _has_safety_signals(prompt_labels_n + owner_intent_labels_n + risk_hints_n, descriptor):
        safety_sensitive = True
    if domain_family == "industrial_automation" and _has_safety_signals(prompt_labels_n + owner_intent_labels_n + risk_hints_n, descriptor):
        safety_sensitive = True
    if domain_family == "software_product" and _contains_any_text(" ".join((descriptor, " ".join(prompt_labels_n), " ".join(risk_hints_n))), {"medical", "health", "clinical", "therapy", "treatment", "self-care", "wellness"}):
        safety_sensitive = True
        legal_sensitive = True
        boundary_review_required = True
        evidence_mapping_required = True
        risk_level = "high"
    if domain_family == "robotics":
        safety_sensitive = True
    recommended_next_stage = _recommended_next_stage(domain_family, novelty_level, owner_intent, risk_level, prompt_labels_n + owner_intent_labels_n + risk_hints_n + known_unknown_hints_n, descriptor)
    if domain_family == "privacy_sensitive_technology" and not _has_consent_lawfulness_signals(prompt_labels_n + owner_intent_labels_n + risk_hints_n, descriptor):
        prototype_planning_allowed = False
        if recommended_next_stage == "research_conversation_plan":
            recommended_next_stage = "privacy_safety_legal_boundary_review"
    if domain_family in {"unknown_domain", "legal_privacy"}:
        prototype_planning_allowed = False
    if domain_family == "materials_discovery" and owner_intent == "evaluate_feasibility":
        recommended_next_stage = "evidence_mapping"
    if domain_family == "owner_workflow" and _contains_any_text(" ".join(prompt_labels_n + owner_intent_labels_n + risk_hints_n + known_unknown_hints_n), {"friction", "repeat", "repeated", "regression", "candidate pack", "pattern miner"}):
        recommended_next_stage = "behavior_pack_candidate_seed"
    if owner_intent == "safety_legal_privacy_review":
        recommended_next_stage = "privacy_safety_legal_boundary_review"
    if domain_family == "software_product" and safety_sensitive:
        recommended_next_stage = "privacy_safety_legal_boundary_review" if owner_intent in {"evaluate_feasibility", "research"} else "evidence_mapping"
    if domain_family == "unknown_domain" and novelty_level == "high_uncertainty":
        recommended_next_stage = "clarifying_question"
    if risk_level == "blocked":
        recommended_next_stage = "refusal_boundary"
        prototype_planning_allowed = False

    candidate_behavior_pack_labels = _candidate_behavior_pack_labels(domain_family, novelty_level, owner_intent, risk_level)

    classification = BroadTopicDomainClassification(
        domain_family=domain_family,
        novelty_level=novelty_level,
        owner_intent=owner_intent,
        evidence_need_level=evidence_need_level,
        risk_level=risk_level,
        risk_labels=_build_risk_labels(domain_family, novelty_level, owner_intent, risk_level, prompt_labels_n, risk_hints_n, known_unknown_hints_n),
        recommended_next_stage=recommended_next_stage,
        candidate_behavior_pack_labels=candidate_behavior_pack_labels,
        boundary_review_required=boundary_review_required,
        evidence_mapping_required=evidence_mapping_required,
        research_planning_required=research_planning_required,
        prototype_planning_allowed=prototype_planning_allowed,
        privacy_sensitive=privacy_sensitive,
        safety_sensitive=safety_sensitive,
        legal_sensitive=legal_sensitive,
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={"ontology": _json_safe(ontology)},
        ontology_packet_id=ontology.ontology_id,
        ontology_meta_domains=tuple(ontology.meta_domains),
        ontology_domain_families=tuple(ontology.domain_families),
        ontology_subdomain_traits=tuple(ontology.subdomain_traits),
        ontology_objects_of_study=tuple(ontology.objects_of_study),
        ontology_evidence_classes=tuple(ontology.evidence_classes),
        ontology_risk_classes=tuple(ontology.risk_classes),
        ontology_sensitivity_classes=tuple(ontology.sensitivity_classes),
        ontology_response_route_family=ontology.response_route_family,
        ontology_behavior_pack_candidate_labels=tuple(ontology.behavior_pack_candidate_labels),
    )
    return BroadTopicDomainClassification(**{**asdict(classification), "safe_metadata": _build_safe_metadata(descriptor, prompt_labels_n, owner_intent_labels_n, risk_hints_n, known_unknown_hints_n, existing_refs_n, classification)})



def _build_risk_labels(
    domain_family: str,
    novelty_level: str,
    owner_intent: str,
    risk_level: str,
    prompt_labels: Sequence[str],
    risk_hints: Sequence[str],
    known_unknown_hints: Sequence[str],
) -> tuple[str, ...]:
    labels: list[str] = []
    blob = " ".join((" ".join(prompt_labels), " ".join(risk_hints), " ".join(known_unknown_hints)))
    if domain_family == "privacy_sensitive_technology":
        labels.extend(("privacy_sensitive", "consent_required", "lawfulness_required", "boundary_review_required"))
        if _contains_any_text(blob, {"tracking", "location", "human sensing", "surveillance"}):
            labels.append("tracking_or_surveillance_risk")
    if domain_family == "legal_privacy":
        labels.extend(("legal_review_required", "privacy_review_required"))
    if domain_family == "industrial_automation":
        labels.append("control_system_risk")
        if _contains_any_text(blob, SAFETY_SENSITIVE_TOKENS_V1):
            labels.append("equipment_safety_risk")
    if domain_family == "materials_discovery":
        labels.extend(("evidence_depth_required", "research_uncertainty"))
    if domain_family == "energy_systems":
        labels.append("electrical_safety_risk")
        if _contains_any_text(blob, {"battery", "grid", "inverter", "power"}):
            labels.append("high_energy_system_risk")
    if domain_family == "robotics":
        labels.extend(("physical_safety_risk", "prototype_limitations"))
    if domain_family == "software_product":
        labels.append("product_scope_uncertainty")
    if domain_family == "website_public_launch":
        labels.extend(("public_launch_scope", "product_marketing_risk"))
    if domain_family == "language_vocabulary":
        labels.append("low_domain_risk")
    if domain_family == "owner_workflow":
        labels.append("governance_workflow_risk")
    if domain_family == "unknown_domain":
        labels.extend(("novel_domain", "clarification_needed"))
    if novelty_level in {"high_uncertainty", "blocked_or_sensitive"}:
        labels.append("novelty_risk")
    if owner_intent == "build_prototype":
        labels.append("prototype_requested")
    if risk_level == "blocked":
        labels.append("blocked")
    elif risk_level == "high":
        labels.append("high_risk")
    elif risk_level == "medium":
        labels.append("moderate_risk")
    else:
        labels.append("low_risk")
    return tuple(_dedupe_preserve(labels))



def build_broad_topic_domain_intake_v1(
    *,
    safe_topic_descriptor: str,
    prompt_labels: Sequence[Any] | None = None,
    owner_intent_labels: Sequence[Any] | None = None,
    risk_hints: Sequence[Any] | None = None,
    known_unknown_hints: Sequence[Any] | None = None,
    existing_behavior_pack_refs: Sequence[Any] | None = None,
) -> BroadTopicDomainIntake:
    classification = classify_broad_topic_domain_v1(
        safe_topic_descriptor=safe_topic_descriptor,
        prompt_labels=prompt_labels,
        owner_intent_labels=owner_intent_labels,
        risk_hints=risk_hints,
        known_unknown_hints=known_unknown_hints,
        existing_behavior_pack_refs=existing_behavior_pack_refs,
    )
    descriptor = _safe_text(safe_topic_descriptor)
    if not descriptor:
        raise ValidationError("safe_topic_descriptor_required")
    intake = BroadTopicDomainIntake(
        intake_id=_deterministic_intake_id(descriptor, classification.domain_family, classification.novelty_level),
        safe_topic_descriptor=descriptor,
        domain_family=classification.domain_family,
        novelty_level=classification.novelty_level,
        owner_intent=classification.owner_intent,
        evidence_need_level=classification.evidence_need_level,
        risk_level=classification.risk_level,
        risk_labels=classification.risk_labels,
        recommended_next_stage=classification.recommended_next_stage,
        candidate_behavior_pack_labels=classification.candidate_behavior_pack_labels,
        boundary_review_required=classification.boundary_review_required,
        evidence_mapping_required=classification.evidence_mapping_required,
        research_planning_required=classification.research_planning_required,
        prototype_planning_allowed=classification.prototype_planning_allowed,
        privacy_sensitive=classification.privacy_sensitive,
        safety_sensitive=classification.safety_sensitive,
        legal_sensitive=classification.legal_sensitive,
        public_claim_allowed=classification.public_claim_allowed,
        iss_internal_reference_allowed=classification.iss_internal_reference_allowed,
        learning_claimed=classification.learning_claimed,
        runtime_authority=classification.runtime_authority,
        writes_state=classification.writes_state,
        model_provider_used=classification.model_provider_used,
        safe_metadata=classification.safe_metadata,
        ontology_packet_id=classification.ontology_packet_id,
        ontology_meta_domains=classification.ontology_meta_domains,
        ontology_domain_families=classification.ontology_domain_families,
        ontology_subdomain_traits=classification.ontology_subdomain_traits,
        ontology_objects_of_study=classification.ontology_objects_of_study,
        ontology_evidence_classes=classification.ontology_evidence_classes,
        ontology_risk_classes=classification.ontology_risk_classes,
        ontology_sensitivity_classes=classification.ontology_sensitivity_classes,
        ontology_response_route_family=classification.ontology_response_route_family,
        ontology_behavior_pack_candidate_labels=classification.ontology_behavior_pack_candidate_labels,
    )
    validate_broad_topic_domain_intake_v1(intake)
    return intake


# ---------------------------------------------------------------------------
# Validation and summaries
# ---------------------------------------------------------------------------


def validate_broad_topic_domain_intake_v1(intake: Any) -> bool:
    if _collect_forbidden_fields(intake):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_claim_marker(intake):
        raise ValidationError("forbidden_public_or_claim_language_present")

    if is_dataclass(intake):
        normalized = intake
    elif isinstance(intake, Mapping):
        allowed = {field.name for field in BroadTopicDomainIntake.__dataclass_fields__.values()}
        extra_keys = set(str(key) for key in intake.keys()) - allowed
        if extra_keys:
            raise ValidationError("unknown_fields_present")
        normalized = BroadTopicDomainIntake(
            intake_id=_safe_text(intake.get("intake_id")),
            safe_topic_descriptor=_safe_text(intake.get("safe_topic_descriptor")),
            domain_family=_safe_text(intake.get("domain_family")),
            novelty_level=_safe_text(intake.get("novelty_level")),
            owner_intent=_safe_text(intake.get("owner_intent")),
            evidence_need_level=_safe_text(intake.get("evidence_need_level")),
            risk_level=_safe_text(intake.get("risk_level")),
            risk_labels=tuple(_normalize_sequence(intake.get("risk_labels"))),
            recommended_next_stage=_safe_text(intake.get("recommended_next_stage")),
            candidate_behavior_pack_labels=tuple(_normalize_sequence(intake.get("candidate_behavior_pack_labels"))),
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
            safe_metadata=dict(intake.get("safe_metadata") or {}),
            ontology_packet_id=_safe_text(intake.get("ontology_packet_id")),
            ontology_meta_domains=tuple(_normalize_sequence(intake.get("ontology_meta_domains"))),
            ontology_domain_families=tuple(_normalize_sequence(intake.get("ontology_domain_families"))),
            ontology_subdomain_traits=tuple(_normalize_sequence(intake.get("ontology_subdomain_traits"))),
            ontology_objects_of_study=tuple(_normalize_sequence(intake.get("ontology_objects_of_study"))),
            ontology_evidence_classes=tuple(_normalize_sequence(intake.get("ontology_evidence_classes"))),
            ontology_risk_classes=tuple(_normalize_sequence(intake.get("ontology_risk_classes"))),
            ontology_sensitivity_classes=tuple(_normalize_sequence(intake.get("ontology_sensitivity_classes"))),
            ontology_response_route_family=_safe_text(intake.get("ontology_response_route_family")),
            ontology_behavior_pack_candidate_labels=tuple(_normalize_sequence(intake.get("ontology_behavior_pack_candidate_labels"))),
        )
    else:
        raise ValidationError("intake_must_be_dataclass_or_mapping")

    if not normalized.intake_id:
        raise ValidationError("intake_id_required")
    if not normalized.safe_topic_descriptor:
        raise ValidationError("safe_topic_descriptor_required")
    if normalized.domain_family not in ALLOWED_DOMAIN_FAMILIES_V1:
        raise ValidationError("unknown_domain_family")
    if normalized.novelty_level not in ALLOWED_NOVELTY_LEVELS_V1:
        raise ValidationError("unknown_novelty_level")
    if normalized.owner_intent not in ALLOWED_OWNER_INTENTS_V1:
        raise ValidationError("unknown_owner_intent")
    if normalized.evidence_need_level not in ALLOWED_EVIDENCE_NEED_LEVELS_V1:
        raise ValidationError("unknown_evidence_need_level")
    if normalized.risk_level not in ALLOWED_RISK_LEVELS_V1:
        raise ValidationError("unknown_risk_level")
    if normalized.recommended_next_stage not in ALLOWED_NEXT_STAGES_V1:
        raise ValidationError("unknown_recommended_next_stage")
    if not normalized.risk_labels:
        raise ValidationError("risk_labels_required")
    if not normalized.candidate_behavior_pack_labels:
        raise ValidationError("candidate_behavior_pack_labels_required")
    for field_name in (
        "boundary_review_required",
        "evidence_mapping_required",
        "research_planning_required",
        "prototype_planning_allowed",
        "privacy_sensitive",
        "safety_sensitive",
        "legal_sensitive",
        "public_claim_allowed",
        "iss_internal_reference_allowed",
        "learning_claimed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
    ):
        if type(getattr(normalized, field_name)) is not bool:
            raise ValidationError(f"{field_name}_must_be_bool")

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

    if normalized.domain_family == "privacy_sensitive_technology" and normalized.risk_level == "blocked":
        raise ValidationError("privacy_sensitive_domain_cannot_be_blocked_without_boundary_reason")
    return True



def summarize_broad_topic_domain_intake_v1(intake: Any) -> BroadTopicDomainIntakeSummary:
    valid = intake if isinstance(intake, BroadTopicDomainIntake) else None
    if valid is None:
        validate_broad_topic_domain_intake_v1(intake)
        if isinstance(intake, Mapping):
            valid = BroadTopicDomainIntake(
                intake_id=_safe_text(intake.get("intake_id")),
                safe_topic_descriptor=_safe_text(intake.get("safe_topic_descriptor")),
                domain_family=_safe_text(intake.get("domain_family")),
                novelty_level=_safe_text(intake.get("novelty_level")),
                owner_intent=_safe_text(intake.get("owner_intent")),
                evidence_need_level=_safe_text(intake.get("evidence_need_level")),
                risk_level=_safe_text(intake.get("risk_level")),
                risk_labels=tuple(_normalize_sequence(intake.get("risk_labels"))),
                recommended_next_stage=_safe_text(intake.get("recommended_next_stage")),
                candidate_behavior_pack_labels=tuple(_normalize_sequence(intake.get("candidate_behavior_pack_labels"))),
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
                safe_metadata=dict(intake.get("safe_metadata") or {}),
                ontology_packet_id=_safe_text(intake.get("ontology_packet_id")),
                ontology_meta_domains=tuple(_normalize_sequence(intake.get("ontology_meta_domains"))),
                ontology_domain_families=tuple(_normalize_sequence(intake.get("ontology_domain_families"))),
                ontology_subdomain_traits=tuple(_normalize_sequence(intake.get("ontology_subdomain_traits"))),
                ontology_objects_of_study=tuple(_normalize_sequence(intake.get("ontology_objects_of_study"))),
                ontology_evidence_classes=tuple(_normalize_sequence(intake.get("ontology_evidence_classes"))),
                ontology_risk_classes=tuple(_normalize_sequence(intake.get("ontology_risk_classes"))),
                ontology_sensitivity_classes=tuple(_normalize_sequence(intake.get("ontology_sensitivity_classes"))),
                ontology_response_route_family=_safe_text(intake.get("ontology_response_route_family")),
                ontology_behavior_pack_candidate_labels=tuple(_normalize_sequence(intake.get("ontology_behavior_pack_candidate_labels"))),
            )
        else:
            valid = intake
    return BroadTopicDomainIntakeSummary(
        summary_type=SUMMARY_TYPE_V1,
        intake_id=valid.intake_id,
        domain_family=valid.domain_family,
        novelty_level=valid.novelty_level,
        owner_intent=valid.owner_intent,
        evidence_need_level=valid.evidence_need_level,
        risk_level=valid.risk_level,
        recommended_next_stage=valid.recommended_next_stage,
        boundary_review_required=valid.boundary_review_required,
        evidence_mapping_required=valid.evidence_mapping_required,
        research_planning_required=valid.research_planning_required,
        prototype_planning_allowed=valid.prototype_planning_allowed,
        risk_label_count=len(valid.risk_labels),
    )



def to_broad_topic_domain_intake_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


# ---------------------------------------------------------------------------
# Seed examples
# ---------------------------------------------------------------------------


def build_initial_broad_topic_domain_intake_examples_v1() -> tuple[BroadTopicDomainIntake, ...]:
    return (
        build_broad_topic_domain_intake_v1(
            safe_topic_descriptor="WiFi/RF sensing for human presence and location in a house",
            prompt_labels=("wifi sensing", "human tracking", "privacy", "consent required"),
            owner_intent_labels=("research",),
            risk_hints=("high risk", "privacy-sensitive", "consent required", "lawful only"),
            known_unknown_hints=("unfamiliar", "researchable"),
            existing_behavior_pack_refs=(PACK_OWNER,),
        ),
        build_broad_topic_domain_intake_v1(
            safe_topic_descriptor="Industrial automation troubleshooting for a control system",
            prompt_labels=("industrial automation", "troubleshooting", "PLC", "equipment"),
            owner_intent_labels=("troubleshooting",),
            risk_hints=("equipment safety",),
            known_unknown_hints=("adjacent",),
            existing_behavior_pack_refs=(PACK_BOUNDARY,),
        ),
        build_broad_topic_domain_intake_v1(
            safe_topic_descriptor="Materials discovery feasibility planning",
            prompt_labels=("materials discovery", "feasibility", "research"),
            owner_intent_labels=("evaluate feasibility",),
            risk_hints=("high evidence need",),
            known_unknown_hints=("unfamiliar",),
            existing_behavior_pack_refs=(PACK_UNKNOWN,),
        ),
        build_broad_topic_domain_intake_v1(
            safe_topic_descriptor="Legal/privacy policy review for a new workflow",
            prompt_labels=("legal privacy", "policy review", "compliance"),
            owner_intent_labels=("safety legal privacy review",),
            risk_hints=("legal", "privacy"),
            known_unknown_hints=("unfamiliar",),
            existing_behavior_pack_refs=(PACK_UNKNOWN,),
        ),
        build_broad_topic_domain_intake_v1(
            safe_topic_descriptor="Energy system prototype planning",
            prompt_labels=("energy systems", "prototype", "battery", "power"),
            owner_intent_labels=("build prototype",),
            risk_hints=("safety sensitive",),
            known_unknown_hints=("adjacent",),
            existing_behavior_pack_refs=(PACK_BOUNDARY,),
        ),
        build_broad_topic_domain_intake_v1(
            safe_topic_descriptor="Software product planning for an owner-facing feature",
            prompt_labels=("software product", "product strategy", "feature planning"),
            owner_intent_labels=("commercial product strategy",),
            risk_hints=("medium uncertainty",),
            known_unknown_hints=("known existing pack",),
            existing_behavior_pack_refs=(PACK_OWNER,),
        ),
        build_broad_topic_domain_intake_v1(
            safe_topic_descriptor="Language and vocabulary discovery for a new term",
            prompt_labels=("language", "vocabulary", "definition"),
            owner_intent_labels=("learn explain",),
            risk_hints=("low risk",),
            known_unknown_hints=("known existing pack",),
            existing_behavior_pack_refs=(PACK_UNKNOWN,),
        ),
        build_broad_topic_domain_intake_v1(
            safe_topic_descriptor="Unknown domain with unclear goal and no prior pack",
            prompt_labels=("unknown", "novel"),
            owner_intent_labels=("unknown",),
            risk_hints=("high uncertainty",),
            known_unknown_hints=("high uncertainty",),
            existing_behavior_pack_refs=(),
        ),
    )


# Backwards-compatible alias names for downstream callers that prefer concise names.
build_broad_topic_domain_intake = build_broad_topic_domain_intake_v1
classify_broad_topic_domain = classify_broad_topic_domain_v1
validate_broad_topic_domain_intake = validate_broad_topic_domain_intake_v1
summarize_broad_topic_domain_intake = summarize_broad_topic_domain_intake_v1
to_broad_topic_domain_intake_json_safe = to_broad_topic_domain_intake_json_safe_v1
build_initial_broad_topic_domain_intake_examples = build_initial_broad_topic_domain_intake_examples_v1
