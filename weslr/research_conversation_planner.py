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
    build_initial_broad_topic_domain_intake_examples_v1,
    classify_broad_topic_domain_v1,
    validate_broad_topic_domain_intake_v1,
)

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
# Domain-specific content
# ---------------------------------------------------------------------------


def _build_knowns_unknowns_assumptions(intake: BroadTopicDomainIntake) -> tuple[list[str], list[str], list[str]]:
    domain = intake.domain_family
    novelty = intake.novelty_level
    intent = intake.owner_intent

    if domain == "privacy_sensitive_technology":
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
            "equipment behavior should be treated as safety-sensitive when control/hardware labels appear",
            "troubleshooting should start from the current observable state",
        )
    elif domain == "legal_privacy":
        knowns = (
            "topic involves legal/privacy review",
            "certainty should stay bounded",
        )
        unknowns = (
            "jurisdiction, policy scope, and compliance context",
            "whether the question is informational or decision-critical",
        )
        assumptions = (
            "no legal certainty should be implied",
            "sources and jurisdiction matter before claims",
        )
    elif domain == "materials_discovery":
        knowns = (
            "topic is materials discovery research",
            "feasibility depends on evidence and validation criteria",
        )
        unknowns = (
            "candidate material class or target property",
            "evidence gaps",
            "validation criteria and uncertainty bounds",
        )
        assumptions = (
            "high evidence need is appropriate",
            "feasibility is not established until validated",
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
            "topic is software/product planning",
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
            "governed metadata-only planning is appropriate",
        )
        unknowns = (
            "which workflow bottleneck is being addressed",
            "whether repeated friction is present",
            "what pack candidate or proof gap exists",
        )
        assumptions = (
            "behavior-pack candidate formation may be relevant",
            "no public wording or runtime authority should be implied",
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
    blob = " ".join((intake.safe_topic_descriptor, intake.domain_family, intake.owner_intent, intake.novelty_level, " ".join(intake.risk_labels), intake.recommended_next_stage))
    if intake.domain_family == "privacy_sensitive_technology":
        warnings.extend(("privacy review required", "privacy misuse risk", "non-consensual rollout guidance is forbidden", "consent and lawfulness must be clarified before deeper steps"))
    if intake.domain_family == "legal_privacy":
        warnings.extend(("no legal certainty claim", "jurisdiction and policy context matter", "evidence mapping is required before claims"))
    if intake.domain_family == "industrial_automation":
        warnings.append("equipment, control, and hardware context may be safety-sensitive")
    if intake.domain_family == "materials_discovery":
        warnings.append("validation criteria and uncertainty gaps must be explicit")
    if intake.domain_family == "energy_systems":
        warnings.append("battery, grid, power, and electrical safety context may be relevant")
    if intake.domain_family == "robotics":
        warnings.append("physical safety and failure modes should stay explicit")
    if intake.domain_family in {"software_product", "website_public_launch"}:
        warnings.append("launch and product scope should remain evidence grounded")
    if intake.domain_family == "unknown_domain":
        warnings.append("domain knowledge is insufficient for strong claims")
    if "blocked" in intake.risk_level or intake.novelty_level == "blocked_or_sensitive":
        warnings.append("boundary review is mandatory")
    if _has_token(blob, {"human sensing", "rf", "wifi"}) and intake.domain_family != "privacy_sensitive_technology":
        warnings.append("privacy review may still be required")
    if not warnings:
        warnings.append("keep the plan bounded and evidence-oriented")
    return _dedupe_preserve(warnings)



def _evidence_needed(intake: BroadTopicDomainIntake) -> list[str]:
    domain = intake.domain_family
    items: list[str] = []
    if domain == "privacy_sensitive_technology":
        items.extend(("consent and lawfulness context", "privacy boundary analysis", "technical literature or terminology", "prototype validation criteria"))
    elif domain == "industrial_automation":
        items.extend(("device specs and configuration", "current fault or symptom context", "control/hardware boundaries", "safety constraints"))
    elif domain == "legal_privacy":
        items.extend(("jurisdiction or policy scope", "legal/privacy sources", "specific compliance question", "uncertainty gaps"))
    elif domain == "materials_discovery":
        items.extend(("definitions and terminology", "technical literature", "validation criteria", "uncertainty gaps"))
    elif domain == "energy_systems":
        items.extend(("system constraints", "safety constraints", "hardware/software requirements", "validation criteria"))
    elif domain == "robotics":
        items.extend(("mechanical and control constraints", "safety constraints", "prototype validation criteria"))
    elif domain in {"software_product", "website_public_launch"}:
        items.extend(("owner goals", "audience and launch state", "constraints", "prototype validation criteria"))
    elif domain == "language_vocabulary":
        items.extend(("term context", "definitions/terminology", "related usage examples"))
    elif domain == "owner_workflow":
        items.extend(("workflow bottleneck", "friction evidence", "pack references", "proof requirements"))
    else:
        items.extend(("domain definition", "unknowns", "evidence gaps"))
    if intake.evidence_need_level == "must_collect_before_claims":
        items.append("evidence must be collected before stronger claims")
    return _dedupe_preserve(items)



def _safe_next_steps(intake: BroadTopicDomainIntake, plan_type: str, response_mode: str) -> list[str]:
    domain = intake.domain_family
    steps: list[str] = []
    if domain == "privacy_sensitive_technology":
        steps.extend(("confirm whether the use case is consent-based and lawful", "separate research exploration from real-world rollout", "map privacy boundaries", "collect evidence before stronger claims"))
    elif domain == "industrial_automation":
        steps.extend(("describe the current fault or operating symptom", "list device specs and control context", "separate troubleshooting from safety validation"))
    elif domain == "legal_privacy":
        steps.extend(("define the jurisdiction or policy scope", "collect legal/privacy sources", "separate informational review from decision-making"))
    elif domain == "materials_discovery":
        steps.extend(("define the target property or material class", "list evidence gaps", "set validation criteria", "choose a research question path"))
    elif domain == "energy_systems":
        steps.extend(("define the use case and constraints", "review safety and electrical boundaries", "choose a high-level feasibility path"))
    elif domain == "robotics":
        steps.extend(("define the robot task and environment", "review safety and motion constraints", "keep prototype guidance high-level"))
    elif domain in {"software_product", "website_public_launch"}:
        steps.extend(("define the owner goal and audience", "capture constraints and launch state", "choose a product/prototype path"))
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
        steps.append("ask for evidence before stronger claims")
    if response_mode == "prototype_path_high_level" and not intake.prototype_planning_allowed:
        steps.append("keep prototype discussion high-level only")
    return _dedupe_preserve(steps)



def _owner_questions(intake: BroadTopicDomainIntake) -> list[str]:
    domain = intake.domain_family
    if domain == "privacy_sensitive_technology":
        return [
            "Is the sensing use case consent-based and lawful?",
            "Is this research only, or are you considering real-world rollout?",
        ]
    if domain == "industrial_automation":
        return [
            "What device, controller, or control system is involved?",
            "What symptom, fault, or configuration detail should we anchor on?",
        ]
    if domain == "legal_privacy":
        return [
            "What jurisdiction or policy scope applies?",
            "Is this informational review or a decision-critical legal/privacy question?",
        ]
    if domain == "materials_discovery":
        return [
            "What material class or target property are you exploring?",
            "What validation criterion would count as success?",
        ]
    if domain == "energy_systems":
        return [
            "What system boundary matters most—battery, grid, inverter, or power path?",
            "Is the goal feasibility review or a high-level prototype path?",
        ]
    if domain == "robotics":
        return [
            "What task and environment is the robot supposed to handle?",
            "What safety constraint matters most?",
        ]
    if domain in {"software_product", "website_public_launch"}:
        return [
            "What is the owner goal and target audience?",
            "What constraints or launch state should we plan around?",
        ]
    if domain == "language_vocabulary":
        return [
            "What is the exact term or phrase?",
            "Do you want a direct explanation or a deeper research question path?",
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
    if domain == "privacy_sensitive_technology":
        return [
            "define a lawful and consent-based use case",
            "collect evidence and boundary constraints",
            "choose a toy or synthetic test environment",
            "validate limitations and failure modes",
        ]
    if domain in {"industrial_automation", "energy_systems", "robotics"}:
        return [
            "define the scope and constraints",
            "choose a safe high-level prototype environment",
            "validate failure modes and safety limits",
            "review whether to continue",
        ]
    if domain in {"software_product", "website_public_launch"}:
        return [
            "define user goal and scope",
            "pick a small prototype slice",
            "validate launch constraints and evidence needs",
            "decide whether to continue",
        ]
    return ()



def _friction_triggers(intake: BroadTopicDomainIntake) -> list[str]:
    triggers = [
        "novel domain or unfamiliar terms",
        "missing evidence or unclear claims",
        "boundary ambiguity",
        "prototype detail requested without sufficient context",
    ]
    if intake.domain_family == "privacy_sensitive_technology":
        triggers.append("consent or lawfulness not yet established")
    if intake.domain_family == "industrial_automation":
        triggers.append("device specs or current fault context missing")
    if intake.domain_family == "legal_privacy":
        triggers.append("jurisdiction or policy scope missing")
    if intake.domain_family == "materials_discovery":
        triggers.append("validation criteria or uncertainty gaps missing")
    if intake.domain_family == "energy_systems":
        triggers.append("safety or electrical constraints missing")
    if intake.domain_family == "robotics":
        triggers.append("motion or failure-mode safety missing")
    if intake.domain_family in {"software_product", "website_public_launch"}:
        triggers.append("audience, launch state, or scope missing")
    if intake.domain_family == "owner_workflow":
        triggers.append("repeated friction or pack-candidate evidence present")
    return _dedupe_preserve(triggers)



def _plan_type_and_mode(intake: BroadTopicDomainIntake) -> tuple[str, str, bool, bool, bool, bool]:
    family = intake.domain_family
    intent = intake.owner_intent
    novelty = intake.novelty_level
    allowed_proto = intake.prototype_planning_allowed
    has_consent = _has_token(intake.safe_topic_descriptor, CONSENT_TERMS_V1) or any(_has_token(label, CONSENT_TERMS_V1) for label in intake.candidate_behavior_pack_labels)

    if family == "privacy_sensitive_technology":
        plan_type = "risk_boundary_review" if novelty in {"high_uncertainty", "blocked_or_sensitive"} or intake.boundary_review_required else "map_research_questions"
        if has_consent and allowed_proto and intent in {"research", "build_prototype", "evaluate_feasibility"}:
            plan_type = "map_research_questions"
        mode = "refusal_boundary" if not has_consent else "research_plan"
        return plan_type, mode, True, True, allowed_proto and has_consent, False

    if family == "industrial_automation":
        plan_type = "troubleshooting_plan" if intent == "troubleshooting" else "feasibility_review"
        mode = "research_plan"
        return plan_type, mode, False, True, allowed_proto, False

    if family == "legal_privacy":
        plan_type = "risk_boundary_review" if intent == "safety_legal_privacy_review" else "evidence_collection_plan"
        mode = "evidence_request" if plan_type == "evidence_collection_plan" else "refusal_boundary"
        return plan_type, mode, True, True, False, False

    if family == "materials_discovery":
        plan_type = "feasibility_review" if intent == "evaluate_feasibility" else "map_research_questions"
        return plan_type, "research_plan", False, True, False, False

    if family == "energy_systems":
        plan_type = "prototype_path_high_level" if intent == "build_prototype" and allowed_proto else "feasibility_review"
        mode = "prototype_path_high_level" if plan_type == "prototype_path_high_level" else "research_plan"
        return plan_type, mode, False, True, allowed_proto, False

    if family == "robotics":
        plan_type = "prototype_path_high_level" if intent == "build_prototype" and allowed_proto else "feasibility_review"
        mode = "prototype_path_high_level" if plan_type == "prototype_path_high_level" else "research_plan"
        return plan_type, mode, False, True, allowed_proto, False

    if family == "software_product":
        plan_type = "product_development_plan" if intent == "commercial_product_strategy" else "prototype_path_high_level"
        mode = "research_plan" if plan_type == "product_development_plan" else "prototype_path_high_level"
        return plan_type, mode, False, True, allowed_proto, False

    if family == "website_public_launch":
        plan_type = "product_development_plan" if intent == "commercial_product_strategy" else "prototype_path_high_level"
        mode = "research_plan" if plan_type == "product_development_plan" else "prototype_path_high_level"
        return plan_type, mode, False, True, allowed_proto, False

    if family == "language_vocabulary":
        plan_type = "explain_topic" if intent == "learn_explain" else "map_research_questions"
        mode = "direct_bounded_overview" if plan_type == "explain_topic" else "research_plan"
        return plan_type, mode, False, False, False, False

    if family == "owner_workflow":
        plan_type = "behavior_pack_seed_plan" if intake.behavior_pack_seed_candidate else "clarifying_intake_plan"
        mode = "behavior_pack_candidate" if plan_type == "behavior_pack_seed_plan" else "clarifying_question"
        return plan_type, mode, False, True, False, True

    # unknown_domain
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
        safe_metadata=_safe_metadata(intake, plan_type, response_mode, behavior_pack_seed_candidate),
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
    if _contains_unsafe_deployment_marker(plan):
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
    from weslr.broad_topic_domain_intake import build_initial_broad_topic_domain_intake_examples_v1

    return tuple(build_research_conversation_plan_v1(domain_intake=intake) for intake in build_initial_broad_topic_domain_intake_examples_v1())


# Backwards-compatible aliases.
build_research_conversation_plan = build_research_conversation_plan_v1
plan_research_conversation = plan_research_conversation_v1
validate_research_conversation_plan = validate_research_conversation_plan_v1
summarize_research_conversation_plan = summarize_research_conversation_plan_v1
to_research_conversation_plan_json_safe = to_research_conversation_plan_json_safe_v1
build_initial_research_conversation_plan_examples = build_initial_research_conversation_plan_examples_v1
