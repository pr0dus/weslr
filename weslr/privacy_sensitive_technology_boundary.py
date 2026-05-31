"""Metadata-only privacy-sensitive technology boundary helper v1.

This module evaluates privacy-sensitive technology topics using broad-topic
intake plus research-conversation plan metadata and returns a boundary
decision.

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
from weslr.research_conversation_planner import (
    ResearchConversationPlan,
    build_research_conversation_plan_v1,
    validate_research_conversation_plan_v1,
)

HELPER_TYPE_V1 = "privacy_sensitive_technology_boundary_helper_v1"
BOUNDARY_TYPE_V1 = "privacy_sensitive_technology_boundary_v1"
SUMMARY_TYPE_V1 = "privacy_sensitive_technology_boundary_summary_v1"

ALLOWED_BOUNDARY_DECISIONS_V1 = {
    "allow_bounded_research",
    "allow_consent_based_assistive_research",
    "allow_privacy_by_design_prototype_plan",
    "allow_high_level_prototype_only",
    "require_consent_and_lawfulness_context",
    "require_affected_person_consent_context",
    "require_medical_claim_boundary",
    "require_boundary_clarification",
    "require_evidence_before_prototype",
    "refuse_covert_or_abusive_deployment",
    "blocked_sensitive_use",
}

ALLOWED_GUIDANCE_LEVELS_V1 = {
    "conceptual_only",
    "research_questions_only",
    "privacy_by_design_plan",
    "assistive_product_design",
    "high_level_prototype_only",
    "evidence_first",
    "medical_claim_boundary_only",
    "refusal_only",
}

ALLOWED_RISK_LEVELS_V1 = {"low", "medium", "high", "blocked"}
ALLOWED_RESPONSE_MODES_V1 = {
    "bounded_research_plan",
    "assistive_safety_research_plan",
    "privacy_by_design_plan",
    "evidence_request",
    "boundary_clarification",
    "medical_claim_boundary",
    "high_level_prototype_path",
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
UNSAFE_DEPLOYMENT_TERMS_V1 = {"covert", "deploy", "deployment", "track", "tracking", "evade", "bypass", "surveillance", "hidden"}
CONSENT_TERMS_V1 = {"consent", "consented", "lawful", "lawfully", "authorized", "permission", "ethical", "ethically", "approved", "opt in", "opt-in"}

PRIVACY_SENSITIVE_TOKENS_V1 = {
    "wifi",
    "wi-fi",
    "rf",
    "radio frequency",
    "sensing",
    "human sensing",
    "presence",
    "location",
    "person",
    "people",
    "someone",
    "someone else",
    "home",
    "house",
    "workplace",
    "minor",
    "vulnerable",
    "biometric",
    "identity",
    "face",
    "voice",
    "gait",
    "breathing",
    "heart",
    "medication",
    "meal",
    "routine",
    "elder",
    "caregiver",
    "safety",
    "security",
    "health",
}

ASSISTIVE_CONTEXT_TOKENS_V1 = {
    "self care",
    "self-care",
    "medication",
    "meds",
    "missed meals",
    "breathing",
    "routine",
    "reminder",
    "elder care",
    "elder-care",
    "caregiver",
    "assistive",
    "support",
    "future self",
    "forgetful",
    "sick",
    "wellness",
    "home safety",
    "home security",
    "anomaly awareness",
}

EMERGENCY_CONTEXT_TOKENS_V1 = {
    "emergency",
    "urgent",
    "alert",
    "escalation",
    "critical",
}

WORKPLACE_CONTEXT_TOKENS_V1 = {"workplace", "employee", "staff", "monitoring"}
MINOR_CONTEXT_TOKENS_V1 = {"minor", "children", "child", "kids", "student", "vulnerable"}
BIOMETRIC_CONTEXT_TOKENS_V1 = {"biometric", "identity", "face", "voice", "gait", "fingerprint"}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PrivacySensitiveTechnologyBoundary:
    boundary_id: str
    source_intake_id: str
    source_plan_id: str
    domain_family: str
    technology_area: str
    authenticated_user_context: bool
    terms_acceptance_context: bool
    responsible_use_context: bool
    affected_person_consent_required: bool
    affected_person_consent_present: bool
    consent_context_present: bool
    lawfulness_context_present: bool
    lawfulness_required: bool
    beneficial_use_detected: bool
    assistive_health_support_intent: bool
    self_care_context: bool
    caregiver_context_present: bool
    security_safety_context_present: bool
    routine_support_context_present: bool
    medical_claim_boundary_required: bool
    medical_diagnosis_claim_blocked: bool
    treatment_recommendation_blocked: bool
    validation_required_before_reliance: bool
    regulatory_review_required_for_health_product: bool
    local_processing_recommended: bool
    data_minimization_required: bool
    user_control_required: bool
    auditability_recommended: bool
    raw_signal_retention_discouraged: bool
    emergency_escalation_requires_explicit_permission: bool
    privacy_risk_level: str
    safety_risk_level: str
    legal_risk_level: str
    abuse_risk_level: str
    boundary_decision: str
    allowed_guidance_level: str
    deployment_guidance_allowed: bool
    covert_use_blocked: bool
    person_tracking_sensitive: bool
    minor_or_vulnerable_person_sensitive: bool
    workplace_monitoring_sensitive: bool
    home_monitoring_sensitive: bool
    risk_labels: tuple[str, ...]
    required_owner_questions: tuple[str, ...]
    allowed_next_steps: tuple[str, ...]
    forbidden_guidance: tuple[str, ...]
    friction_capture_triggers: tuple[str, ...]
    recommended_response_mode: str
    public_claim_allowed: bool
    iss_internal_reference_allowed: bool
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class PrivacySensitiveTechnologyBoundarySummary:
    summary_type: str
    boundary_id: str
    boundary_decision: str
    domain_family: str
    technology_area: str
    privacy_risk_level: str
    safety_risk_level: str
    legal_risk_level: str
    abuse_risk_level: str
    allowed_guidance_level: str
    beneficial_use_detected: bool
    covert_use_blocked: bool
    deployment_guidance_allowed: bool
    medical_claim_boundary_required: bool


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



def _contains_unsafe_marker(value: Any, *, ignore_keys: set[str] | None = None) -> bool:
    if ignore_keys is None:
        ignore_keys = {"boundary_decision", "risk_labels"}
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _safe_text(key).lower() in ignore_keys:
                continue
            if _contains_unsafe_marker(item, ignore_keys=ignore_keys):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_unsafe_marker(item, ignore_keys=ignore_keys) for item in value)
    if isinstance(value, str):
        blob = _normalize_text(value)
        return any(term in blob for term in UNSAFE_DEPLOYMENT_TERMS_V1)
    return False



def _has_token(text: Any, terms: Iterable[str]) -> bool:
    blob = _normalize_text(text)
    return any(_normalize_text(term) in blob for term in terms)



def _context_from_mapping(mapping: Mapping[str, Any] | None, key: str, default: bool = False) -> bool:
    if not mapping:
        return default
    value = mapping.get(key)
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return bool(value)



def _extract_ontology_metadata(
    intake: BroadTopicDomainIntake,
    research_plan: ResearchConversationPlan | None,
    overrides: Mapping[str, Any] | None,
) -> dict[str, Any]:
    merged: dict[str, Any] = {}

    def _merge(source: Any) -> None:
        if isinstance(source, Mapping):
            for key, value in source.items():
                if key == "safe_metadata" and isinstance(value, Mapping):
                    _merge(value)
                else:
                    merged[str(key)] = value

    if intake.safe_metadata:
        _merge(intake.safe_metadata.get("ontology"))
        classification = intake.safe_metadata.get("classification")
        if isinstance(classification, Mapping):
            _merge(classification.get("safe_metadata"))
    if research_plan and research_plan.safe_metadata:
        _merge(research_plan.safe_metadata.get("ontology"))
    if overrides:
        _merge(overrides.get("ontology"))
    return merged



def _safe_slug(text: str, *, fallback: str = "boundary") -> str:
    tokens = _normalize_text(text).replace("/", " ").replace("-", " ").replace("_", " ").split()
    if not tokens:
        return fallback
    return "_".join(tokens[:12])



def _boundary_id(intake_id: str, plan_id: str, boundary_decision: str) -> str:
    decision_slug_map = {
        "allow_bounded_research": "bounded_research",
        "allow_consent_based_assistive_research": "consent_assistive_research",
        "allow_privacy_by_design_prototype_plan": "privacy_by_design_plan",
        "allow_high_level_prototype_only": "high_level_prototype",
        "require_consent_and_lawfulness_context": "require_consent_lawfulness",
        "require_affected_person_consent_context": "require_affected_person_consent",
        "require_medical_claim_boundary": "require_medical_boundary",
        "require_boundary_clarification": "boundary_clarification",
        "require_evidence_before_prototype": "evidence_before_prototype",
        "refuse_covert_or_abusive_deployment": "refuse_abusive_use",
        "blocked_sensitive_use": "blocked_sensitive_use",
    }
    decision_slug = decision_slug_map.get(boundary_decision, "boundary")
    base = "_".join(part for part in (_safe_slug(intake_id), _safe_slug(plan_id), decision_slug) if part)
    return f"privacy_sensitive_technology_boundary_{base}"


# ---------------------------------------------------------------------------
# Coercion and classification
# ---------------------------------------------------------------------------


def _coerce_intake(domain_intake: BroadTopicDomainIntake | Mapping[str, Any] | None, research_plan: ResearchConversationPlan | Mapping[str, Any] | None) -> BroadTopicDomainIntake:
    if domain_intake is not None:
        if isinstance(domain_intake, BroadTopicDomainIntake):
            validate_broad_topic_domain_intake_v1(domain_intake)
            return domain_intake
        if isinstance(domain_intake, Mapping):
            intake = BroadTopicDomainIntake(
                intake_id=_safe_text(domain_intake.get("intake_id")),
                safe_topic_descriptor=_safe_text(domain_intake.get("safe_topic_descriptor")),
                domain_family=_safe_text(domain_intake.get("domain_family")),
                novelty_level=_safe_text(domain_intake.get("novelty_level")),
                owner_intent=_safe_text(domain_intake.get("owner_intent")),
                evidence_need_level=_safe_text(domain_intake.get("evidence_need_level")),
                risk_level=_safe_text(domain_intake.get("risk_level")),
                risk_labels=_normalize_sequence(domain_intake.get("risk_labels")),
                recommended_next_stage=_safe_text(domain_intake.get("recommended_next_stage")),
                candidate_behavior_pack_labels=_normalize_sequence(domain_intake.get("candidate_behavior_pack_labels")),
                boundary_review_required=bool(domain_intake.get("boundary_review_required")),
                evidence_mapping_required=bool(domain_intake.get("evidence_mapping_required")),
                research_planning_required=bool(domain_intake.get("research_planning_required")),
                prototype_planning_allowed=bool(domain_intake.get("prototype_planning_allowed")),
                privacy_sensitive=bool(domain_intake.get("privacy_sensitive")),
                safety_sensitive=bool(domain_intake.get("safety_sensitive")),
                legal_sensitive=bool(domain_intake.get("legal_sensitive")),
                public_claim_allowed=bool(domain_intake.get("public_claim_allowed")),
                iss_internal_reference_allowed=bool(domain_intake.get("iss_internal_reference_allowed")),
                learning_claimed=bool(domain_intake.get("learning_claimed")),
                runtime_authority=bool(domain_intake.get("runtime_authority")),
                writes_state=bool(domain_intake.get("writes_state")),
                model_provider_used=bool(domain_intake.get("model_provider_used")),
                safe_metadata=dict(domain_intake.get("safe_metadata") or {}),
            )
            validate_broad_topic_domain_intake_v1(intake)
            return intake
    if research_plan is not None:
        plan = research_plan if isinstance(research_plan, ResearchConversationPlan) else None
        if plan is None and isinstance(research_plan, Mapping):
            allowed = {field.name for field in ResearchConversationPlan.__dataclass_fields__.values()}
            extra = set(str(key) for key in research_plan.keys()) - allowed
            if extra:
                raise ValidationError("unknown_plan_fields_present")
            plan = ResearchConversationPlan(
                plan_id=_safe_text(research_plan.get("plan_id")),
                source_intake_id=_safe_text(research_plan.get("source_intake_id")),
                domain_family=_safe_text(research_plan.get("domain_family")),
                novelty_level=_safe_text(research_plan.get("novelty_level")),
                owner_intent=_safe_text(research_plan.get("owner_intent")),
                plan_type=_safe_text(research_plan.get("plan_type")),
                knowns=_normalize_sequence(research_plan.get("knowns")),
                unknowns=_normalize_sequence(research_plan.get("unknowns")),
                assumptions=_normalize_sequence(research_plan.get("assumptions")),
                evidence_needed=_normalize_sequence(research_plan.get("evidence_needed")),
                safe_next_steps=_normalize_sequence(research_plan.get("safe_next_steps")),
                owner_questions=_normalize_sequence(research_plan.get("owner_questions")),
                boundary_warnings=_normalize_sequence(research_plan.get("boundary_warnings")),
                prototype_phase_outline=_normalize_sequence(research_plan.get("prototype_phase_outline")),
                friction_capture_triggers=_normalize_sequence(research_plan.get("friction_capture_triggers")),
                recommended_response_mode=_safe_text(research_plan.get("recommended_response_mode")),
                requires_boundary_review=bool(research_plan.get("requires_boundary_review")),
                requires_evidence_mapping=bool(research_plan.get("requires_evidence_mapping")),
                prototype_planning_allowed=bool(research_plan.get("prototype_planning_allowed")),
                behavior_pack_seed_candidate=bool(research_plan.get("behavior_pack_seed_candidate")),
                public_claim_allowed=bool(research_plan.get("public_claim_allowed")),
                iss_internal_reference_allowed=bool(research_plan.get("iss_internal_reference_allowed")),
                learning_claimed=bool(research_plan.get("learning_claimed")),
                runtime_authority=bool(research_plan.get("runtime_authority")),
                writes_state=bool(research_plan.get("writes_state")),
                model_provider_used=bool(research_plan.get("model_provider_used")),
                safe_metadata=dict(research_plan.get("safe_metadata") or {}),
            )
        if plan is not None:
            validate_research_conversation_plan_v1(plan)
            source_meta = plan.safe_metadata or {}
            descriptor = _safe_text(source_meta.get("technology_area") or plan.plan_type or plan.domain_family or "privacy_sensitive_technology")
            domain_family = plan.domain_family if plan.domain_family in {
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
            } else "privacy_sensitive_technology"
            novelty_level = plan.novelty_level if plan.novelty_level in {
                "known_existing_pack",
                "adjacent_to_existing_pack",
                "unfamiliar_but_researchable",
                "high_uncertainty",
                "blocked_or_sensitive",
            } else "high_uncertainty"
            owner_intent = plan.owner_intent if plan.owner_intent in {
                "learn_explain",
                "research",
                "build_prototype",
                "evaluate_feasibility",
                "safety_legal_privacy_review",
                "commercial_product_strategy",
                "troubleshooting",
                "unknown_intent",
            } else "research"
            evidence_need_level = "must_collect_before_claims" if domain_family in {"privacy_sensitive_technology", "legal_privacy"} else "high"
            risk_level = "high" if domain_family in {"privacy_sensitive_technology", "legal_privacy"} else "medium"
            return BroadTopicDomainIntake(
                intake_id=_safe_text(source_meta.get("source_intake_id") or plan.source_intake_id or "unknown_intake"),
                safe_topic_descriptor=descriptor,
                domain_family=domain_family,
                novelty_level=novelty_level,
                owner_intent=owner_intent,
                evidence_need_level=evidence_need_level,
                risk_level=risk_level,
                risk_labels=_normalize_sequence(source_meta.get("risk_labels") or ("privacy_sensitive",)),
                recommended_next_stage="research_conversation_plan",
                candidate_behavior_pack_labels=_normalize_sequence(source_meta.get("candidate_behavior_pack_labels") or ()),
                boundary_review_required=True,
                evidence_mapping_required=True,
                research_planning_required=True,
                prototype_planning_allowed=bool(source_meta.get("prototype_planning_allowed", False)),
                privacy_sensitive=True,
                safety_sensitive=bool(source_meta.get("safety_sensitive", True)),
                legal_sensitive=bool(source_meta.get("legal_sensitive", True)),
                public_claim_allowed=False,
                iss_internal_reference_allowed=True,
                learning_claimed=False,
                runtime_authority=False,
                writes_state=False,
                model_provider_used=False,
                safe_metadata={},
            )
    raise ValidationError("domain_intake_or_research_plan_required")



def _context_flags(intake: BroadTopicDomainIntake, research_plan: ResearchConversationPlan | None, overrides: Mapping[str, Any] | None) -> dict[str, bool]:
    meta = {}
    if intake.safe_metadata:
        meta.update(intake.safe_metadata)
    if research_plan and research_plan.safe_metadata:
        meta.update(research_plan.safe_metadata)
    if overrides:
        meta.update(overrides)

    ontology = _extract_ontology_metadata(intake, research_plan, overrides)
    ontology_domain_families = set(_normalize_sequence(ontology.get("domain_families")))
    ontology_subdomain_traits = set(_normalize_sequence(ontology.get("subdomain_traits")))
    ontology_evidence_classes = set(_normalize_sequence(ontology.get("evidence_classes")))
    ontology_risk_classes = set(_normalize_sequence(ontology.get("risk_classes")))
    ontology_sensitivity_classes = set(_normalize_sequence(ontology.get("sensitivity_classes")))
    ontology_privacy_sensitive = bool(ontology.get("privacy_sensitive")) or "privacy_sensitive" in ontology_subdomain_traits or "privacy_sensitive" in ontology_sensitivity_classes or "privacy_sensitive_technology" in ontology_domain_families
    ontology_human_subject_involved = bool(ontology.get("human_subject_involved")) or "human_subject_involved" in ontology_subdomain_traits or ontology_privacy_sensitive
    ontology_beneficial_assistive_use = bool(ontology.get("beneficial_assistive_use")) or "beneficial_assistive_use" in ontology_subdomain_traits
    ontology_medical_sensitive = bool(ontology.get("medical_sensitive")) or "medical_or_health_sensitive" in ontology_sensitivity_classes or "medicine_health_research" in ontology_domain_families
    ontology_safety_critical = bool(ontology.get("safety_sensitive")) or "safety_critical" in ontology_sensitivity_classes or "safety_critical" in ontology_risk_classes

    descriptor = intake.safe_topic_descriptor
    plan_blob = " ".join((research_plan.plan_type if research_plan else "", research_plan.recommended_response_mode if research_plan else "", " ".join(research_plan.safe_next_steps) if research_plan else "", " ".join(research_plan.boundary_warnings) if research_plan else ""))
    blob = " ".join((descriptor, intake.domain_family, intake.owner_intent, intake.novelty_level, intake.risk_level, intake.recommended_next_stage, plan_blob, " ".join(intake.risk_labels), " ".join(intake.candidate_behavior_pack_labels)))

    authenticated_user_context = _context_from_mapping(meta, "authenticated_user_context", True)
    terms_acceptance_context = _context_from_mapping(meta, "terms_acceptance_context", True)
    responsible_use_context = _context_from_mapping(meta, "responsible_use_context", True)

    consent_context_present = authenticated_user_context and terms_acceptance_context and responsible_use_context and _has_token(blob, CONSENT_TERMS_V1)
    lawfulness_context_present = _has_token(blob, {"lawful", "lawfully", "authorized", "permission", "approved", "responsible"}) or consent_context_present
    self_care_context = _has_token(blob, {"self care", "self-care", "future self", "forgetful"})
    caregiver_context_present = _has_token(blob, {"caregiver", "elder care", "elder-care", "care support"})
    routine_support_context_present = _has_token(blob, {"medication", "meds", "missed meals", "routine", "reminder", "schedule"})
    security_safety_context_present = _has_token(blob, {"home safety", "home security", "safety", "security"}) or ontology_safety_critical
    assistive_health_support_intent = self_care_context or caregiver_context_present or routine_support_context_present or _has_token(blob, {"breathing", "wellness", "health"}) or ontology_beneficial_assistive_use
    beneficial_use_detected = assistive_health_support_intent or security_safety_context_present

    person_tracking_sensitive = _has_token(blob, {"wifi", "wi-fi", "rf", "radio frequency", "sensing", "human sensing", "presence", "location", "person", "people", "someone", "home", "house", "workplace", "minor", "vulnerable", "biometric", "identity", "face", "voice", "gait"}) or ontology_privacy_sensitive or ontology_human_subject_involved
    home_monitoring_sensitive = _has_token(blob, {"home", "house"}) and person_tracking_sensitive
    workplace_monitoring_sensitive = _has_token(blob, WORKPLACE_CONTEXT_TOKENS_V1) or _has_token(blob, {"employee", "staff"})
    minor_or_vulnerable_person_sensitive = _has_token(blob, MINOR_CONTEXT_TOKENS_V1)

    affected_person_consent_required = person_tracking_sensitive or workplace_monitoring_sensitive or minor_or_vulnerable_person_sensitive or _has_token(blob, BIOMETRIC_CONTEXT_TOKENS_V1)
    affected_person_consent_present = _context_from_mapping(meta, "affected_person_consent_present", False) or (_has_token(blob, {"consent", "consented", "authorized", "permission"}) and not _has_token(blob, {"covert", "hidden"}))

    medical_claim_boundary_required = assistive_health_support_intent or _has_token(blob, {"medical", "medication", "breathing", "health", "wellness", "clinical", "therapy", "treatment"}) or ontology_medical_sensitive or ("medical_claim_adjacent" in ontology_subdomain_traits)
    validation_required_before_reliance = medical_claim_boundary_required or beneficial_use_detected or person_tracking_sensitive
    regulatory_review_required_for_health_product = medical_claim_boundary_required and bool(_context_from_mapping(meta, "regulatory_review_required_for_health_product", False) or _has_token(blob, {"product", "launch", "prototype", "app", "service"}) or ontology_medical_sensitive)

    emergency_escalation_requires_explicit_permission = _has_token(blob, EMERGENCY_CONTEXT_TOKENS_V1) or bool(_context_from_mapping(meta, "emergency_escalation_requires_explicit_permission", False))

    lawfulness_required = person_tracking_sensitive or workplace_monitoring_sensitive or minor_or_vulnerable_person_sensitive or medical_claim_boundary_required or security_safety_context_present or ontology_medical_sensitive or ontology_privacy_sensitive

    privacy_risk_level = "high" if person_tracking_sensitive or workplace_monitoring_sensitive or minor_or_vulnerable_person_sensitive or _has_token(blob, BIOMETRIC_CONTEXT_TOKENS_V1) or ontology_privacy_sensitive else ("medium" if beneficial_use_detected else "low")
    safety_risk_level = "high" if minor_or_vulnerable_person_sensitive or emergency_escalation_requires_explicit_permission or medical_claim_boundary_required or ontology_safety_critical else ("medium" if security_safety_context_present else "low")
    legal_risk_level = "blocked" if _has_token(blob, {"covert", "hidden"}) else ("high" if lawfulness_required else "medium")
    abuse_risk_level = "blocked" if _has_token(blob, {"covert", "hidden"}) else ("high" if person_tracking_sensitive or workplace_monitoring_sensitive or minor_or_vulnerable_person_sensitive or ontology_privacy_sensitive else "medium")

    return {
        "authenticated_user_context": authenticated_user_context,
        "terms_acceptance_context": terms_acceptance_context,
        "responsible_use_context": responsible_use_context,
        "consent_context_present": consent_context_present,
        "lawfulness_context_present": lawfulness_context_present,
        "self_care_context": self_care_context,
        "caregiver_context_present": caregiver_context_present,
        "routine_support_context_present": routine_support_context_present,
        "security_safety_context_present": security_safety_context_present,
        "beneficial_use_detected": beneficial_use_detected,
        "assistive_health_support_intent": assistive_health_support_intent,
        "person_tracking_sensitive": person_tracking_sensitive,
        "home_monitoring_sensitive": home_monitoring_sensitive,
        "workplace_monitoring_sensitive": workplace_monitoring_sensitive,
        "minor_or_vulnerable_person_sensitive": minor_or_vulnerable_person_sensitive,
        "affected_person_consent_required": affected_person_consent_required,
        "affected_person_consent_present": affected_person_consent_present,
        "medical_claim_boundary_required": medical_claim_boundary_required,
        "validation_required_before_reliance": validation_required_before_reliance,
        "regulatory_review_required_for_health_product": regulatory_review_required_for_health_product,
        "emergency_escalation_requires_explicit_permission": emergency_escalation_requires_explicit_permission,
        "lawfulness_required": lawfulness_required,
        "privacy_risk_level": privacy_risk_level,
        "safety_risk_level": safety_risk_level,
        "legal_risk_level": legal_risk_level,
        "abuse_risk_level": abuse_risk_level,
    }



def _boundary_decision_and_guidance(intake: BroadTopicDomainIntake, plan: ResearchConversationPlan | None, flags: Mapping[str, bool]) -> tuple[str, str, bool, bool, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    person_sensitive = flags["person_tracking_sensitive"]
    beneficial_use = flags["beneficial_use_detected"]
    medical = flags["medical_claim_boundary_required"]
    emergency = flags["emergency_escalation_requires_explicit_permission"]
    consent_present = flags["consent_context_present"] and flags["lawfulness_context_present"] and flags["affected_person_consent_present"]
    consent_required = flags["affected_person_consent_required"] or medical or person_sensitive
    high_risk_sensitive = person_sensitive or flags["workplace_monitoring_sensitive"] or flags["minor_or_vulnerable_person_sensitive"] or medical
    covert_marker = _contains_unsafe_marker(intake.safe_topic_descriptor) or _contains_unsafe_marker(intake.candidate_behavior_pack_labels)

    if covert_marker or _has_token(intake.safe_topic_descriptor, {"covert", "hidden", "surveillance", "evade", "bypass"}) or _has_token(intake.risk_labels, {"covert", "hidden"}):
        decision = "refuse_covert_or_abusive_deployment"
        guidance = "refusal_only"
        deployment_allowed = False
        covert_blocked = True
        risk_labels = _dedupe_preserve(("secret_use_blocked", "abusive_use_blocked", "refusal_only"))
        allowed_next = (
            "clarify lawful, consent-based boundaries",
            "remove any concealed or abusive sensing intent",
            "restart with a bounded research question",
        )
        forbidden = (
            "concealed sensing or secret use",
            "identity inference without consent",
            "invasive rollout advice",
        )
        return decision, guidance, deployment_allowed, covert_blocked, risk_labels, allowed_next, forbidden

    if high_risk_sensitive and not consent_present:
        if medical:
            decision = "require_medical_claim_boundary"
            guidance = "medical_claim_boundary_only"
        elif flags["minor_or_vulnerable_person_sensitive"] or flags["workplace_monitoring_sensitive"]:
            decision = "require_affected_person_consent_context"
            guidance = "research_questions_only"
        else:
            decision = "require_consent_and_lawfulness_context"
            guidance = "evidence_first"
        deployment_allowed = False
        covert_blocked = True
        risk_labels = _dedupe_preserve(("consent_required", "lawfulness_required", "high_risk_sensitive_use"))
        allowed_next = (
            "collect consent and lawfulness context",
            "identify all affected people and permissions",
            "map privacy and safety boundaries before any prototype",
        )
        forbidden = (
            "concealed sensing",
            "secret monitoring",
            "medical diagnosis claims",
            "treatment recommendations",
        )
        return decision, guidance, deployment_allowed, covert_blocked, risk_labels, allowed_next, forbidden

    if beneficial_use and consent_present:
        if medical:
            decision = "allow_consent_based_assistive_research"
            guidance = "assistive_product_design"
            if flags["validation_required_before_reliance"]:
                guidance = "privacy_by_design_plan"
            if plan and plan.prototype_planning_allowed:
                decision = "allow_privacy_by_design_prototype_plan"
                guidance = "privacy_by_design_plan"
        elif person_sensitive:
            decision = "allow_privacy_by_design_prototype_plan"
            guidance = "privacy_by_design_plan"
        else:
            decision = "allow_bounded_research"
            guidance = "conceptual_only"
        if emergency:
            guidance = "high_level_prototype_only"
        deployment_allowed = False
        covert_blocked = True
        risk_labels = _dedupe_preserve(("beneficial_use", "consent_based", "privacy_by_design_required"))
        allowed_next = (
            "define user-configured permissions and controls",
            "keep processing local where possible",
            "test with synthetic or opt-in data before reliance",
        )
        forbidden = (
            "concealed sensing",
            "diagnosis claims",
            "treatment recommendations",
            "invasive rollout advice",
        )
        return decision, guidance, deployment_allowed, covert_blocked, risk_labels, allowed_next, forbidden

    if consent_present and person_sensitive:
        decision = "allow_high_level_prototype_only"
        guidance = "high_level_prototype_only"
        deployment_allowed = False
        covert_blocked = True
        risk_labels = _dedupe_preserve(("consent_present", "person_sensitive", "prototype_only"))
        allowed_next = (
            "keep the prototype high-level and non-invasive",
            "map consent, lawfulness, and affected-person boundaries",
            "collect evidence before any wider rollout",
        )
        forbidden = (
            "concealed sensing",
            "secret monitoring",
            "rollout instructions",
        )
        return decision, guidance, deployment_allowed, covert_blocked, risk_labels, allowed_next, forbidden

    if not person_sensitive:
        decision = "allow_bounded_research"
        guidance = "research_questions_only" if intake.domain_family == "unknown_domain" else "conceptual_only"
        deployment_allowed = True if intake.domain_family in {"technical_research", "materials_discovery"} else False
        covert_blocked = False
        risk_labels = _dedupe_preserve(("bounded_research", "no_person_sensitive_labels"))
        allowed_next = (
            "state the sensing setup in high-level terms",
            "keep the question evidence-oriented",
            "avoid rollout detail unless a later boundary review allows it",
        )
        forbidden = (
            "identity inference without consent",
            "diagnosis claims",
            "invasive rollout advice",
        )
        return decision, guidance, deployment_allowed, covert_blocked, risk_labels, allowed_next, forbidden

    decision = "require_boundary_clarification"
    guidance = "research_questions_only"
    deployment_allowed = False
    covert_blocked = True
    risk_labels = _dedupe_preserve(("boundary_clarification_needed", "sensitive_context"))
    allowed_next = (
        "clarify consent, lawfulness, and affected-person context",
        "identify whether this is assistive, security, or health support",
        "gather evidence before prototype planning",
    )
    forbidden = (
        "concealed sensing",
        "identity inference without consent",
        "medical diagnosis claims",
    )
    return decision, guidance, deployment_allowed, covert_blocked, risk_labels, allowed_next, forbidden


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_privacy_sensitive_technology_boundary_v1(
    *,
    domain_intake: BroadTopicDomainIntake | Mapping[str, Any] | None = None,
    research_plan: ResearchConversationPlan | Mapping[str, Any] | None = None,
    safe_metadata: Mapping[str, Any] | None = None,
    **context_overrides: Any,
) -> PrivacySensitiveTechnologyBoundary:
    intake = _coerce_intake(domain_intake, research_plan)
    plan = None
    if research_plan is not None:
        plan = research_plan if isinstance(research_plan, ResearchConversationPlan) else None
        if plan is None and isinstance(research_plan, Mapping):
            plan = ResearchConversationPlan(
                plan_id=_safe_text(research_plan.get("plan_id")),
                source_intake_id=_safe_text(research_plan.get("source_intake_id")),
                domain_family=_safe_text(research_plan.get("domain_family")),
                novelty_level=_safe_text(research_plan.get("novelty_level")),
                owner_intent=_safe_text(research_plan.get("owner_intent")),
                plan_type=_safe_text(research_plan.get("plan_type")),
                knowns=_normalize_sequence(research_plan.get("knowns")),
                unknowns=_normalize_sequence(research_plan.get("unknowns")),
                assumptions=_normalize_sequence(research_plan.get("assumptions")),
                evidence_needed=_normalize_sequence(research_plan.get("evidence_needed")),
                safe_next_steps=_normalize_sequence(research_plan.get("safe_next_steps")),
                owner_questions=_normalize_sequence(research_plan.get("owner_questions")),
                boundary_warnings=_normalize_sequence(research_plan.get("boundary_warnings")),
                prototype_phase_outline=_normalize_sequence(research_plan.get("prototype_phase_outline")),
                friction_capture_triggers=_normalize_sequence(research_plan.get("friction_capture_triggers")),
                recommended_response_mode=_safe_text(research_plan.get("recommended_response_mode")),
                requires_boundary_review=bool(research_plan.get("requires_boundary_review")),
                requires_evidence_mapping=bool(research_plan.get("requires_evidence_mapping")),
                prototype_planning_allowed=bool(research_plan.get("prototype_planning_allowed")),
                behavior_pack_seed_candidate=bool(research_plan.get("behavior_pack_seed_candidate")),
                public_claim_allowed=bool(research_plan.get("public_claim_allowed")),
                iss_internal_reference_allowed=bool(research_plan.get("iss_internal_reference_allowed")),
                learning_claimed=bool(research_plan.get("learning_claimed")),
                runtime_authority=bool(research_plan.get("runtime_authority")),
                writes_state=bool(research_plan.get("writes_state")),
                model_provider_used=bool(research_plan.get("model_provider_used")),
                safe_metadata=dict(research_plan.get("safe_metadata") or {}),
            )
        if plan is not None:
            validate_research_conversation_plan_v1(plan)

    ctx = _context_flags(intake, plan, safe_metadata)
    ctx.update({k: bool(v) for k, v in context_overrides.items() if k in {
        "authenticated_user_context",
        "terms_acceptance_context",
        "responsible_use_context",
        "affected_person_consent_present",
        "consent_context_present",
        "lawfulness_context_present",
        "emergency_escalation_requires_explicit_permission",
        "regulatory_review_required_for_health_product",
    }})

    decision, guidance, deployment_allowed, covert_blocked, decision_labels, allowed_next, forbidden = _boundary_decision_and_guidance(intake, plan, ctx)
    beneficial_use = ctx["beneficial_use_detected"]
    medical = ctx["medical_claim_boundary_required"]

    if decision in {"allow_consent_based_assistive_research", "allow_privacy_by_design_prototype_plan"}:
        local_processing = True
        minimization = True
        user_control = True
        auditability = True
        raw_retention = False
    elif decision == "allow_high_level_prototype_only":
        local_processing = True
        minimization = True
        user_control = True
        auditability = True
        raw_retention = True
    elif decision == "allow_bounded_research":
        local_processing = False
        minimization = True
        user_control = False
        auditability = False
        raw_retention = False
    else:
        local_processing = True if ctx["person_tracking_sensitive"] or medical else False
        minimization = True
        user_control = True
        auditability = ctx["person_tracking_sensitive"] or medical
        raw_retention = False

    if ctx["emergency_escalation_requires_explicit_permission"]:
        allowed_next = allowed_next + ("require explicit user-configured permission before any escalation logic",)
        forbidden = forbidden + ("automatic escalation without explicit permission",)

    technology_area = _safe_text(
        (ctx.get("technology_area") if isinstance(ctx, Mapping) else None)
        or (plan.safe_metadata.get("technology_area") if plan and plan.safe_metadata else None)
        or intake.safe_topic_descriptor
        or intake.domain_family,
        default="privacy_sensitive_technology",
    )
    if not technology_area:
        technology_area = intake.domain_family

    boundary = PrivacySensitiveTechnologyBoundary(
        boundary_id=_boundary_id(intake.intake_id, plan.plan_id if plan else intake.intake_id, decision),
        source_intake_id=intake.intake_id,
        source_plan_id=plan.plan_id if plan else "",
        domain_family=intake.domain_family,
        technology_area=technology_area,
        authenticated_user_context=ctx["authenticated_user_context"],
        terms_acceptance_context=ctx["terms_acceptance_context"],
        responsible_use_context=ctx["responsible_use_context"],
        affected_person_consent_required=ctx["affected_person_consent_required"],
        affected_person_consent_present=ctx["affected_person_consent_present"],
        consent_context_present=ctx["consent_context_present"],
        lawfulness_context_present=ctx["lawfulness_context_present"],
        lawfulness_required=ctx["lawfulness_required"],
        beneficial_use_detected=beneficial_use,
        assistive_health_support_intent=ctx["assistive_health_support_intent"],
        self_care_context=ctx["self_care_context"],
        caregiver_context_present=ctx["caregiver_context_present"],
        security_safety_context_present=ctx["security_safety_context_present"],
        routine_support_context_present=ctx["routine_support_context_present"],
        medical_claim_boundary_required=medical,
        medical_diagnosis_claim_blocked=medical,
        treatment_recommendation_blocked=medical,
        validation_required_before_reliance=ctx["validation_required_before_reliance"],
        regulatory_review_required_for_health_product=ctx["regulatory_review_required_for_health_product"],
        local_processing_recommended=local_processing,
        data_minimization_required=minimization,
        user_control_required=user_control,
        auditability_recommended=auditability,
        raw_signal_retention_discouraged=raw_retention,
        emergency_escalation_requires_explicit_permission=ctx["emergency_escalation_requires_explicit_permission"],
        privacy_risk_level=ctx["privacy_risk_level"],
        safety_risk_level=ctx["safety_risk_level"],
        legal_risk_level=ctx["legal_risk_level"],
        abuse_risk_level=ctx["abuse_risk_level"],
        boundary_decision=decision,
        allowed_guidance_level=guidance,
        deployment_guidance_allowed=deployment_allowed,
        covert_use_blocked=covert_blocked,
        person_tracking_sensitive=ctx["person_tracking_sensitive"],
        minor_or_vulnerable_person_sensitive=ctx["minor_or_vulnerable_person_sensitive"],
        workplace_monitoring_sensitive=ctx["workplace_monitoring_sensitive"],
        home_monitoring_sensitive=ctx["home_monitoring_sensitive"],
        risk_labels=decision_labels,
        required_owner_questions=_required_owner_questions(intake, ctx, decision),
        allowed_next_steps=_dedupe_preserve(allowed_next),
        forbidden_guidance=_dedupe_preserve(forbidden),
        friction_capture_triggers=_friction_capture_triggers(intake, ctx, decision),
        recommended_response_mode=_recommended_response_mode(decision, guidance),
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata=_safe_metadata(intake, plan, ctx, decision, guidance),
    )
    validate_privacy_sensitive_technology_boundary_v1(boundary)
    return boundary



def evaluate_privacy_sensitive_technology_boundary_v1(
    domain_intake: BroadTopicDomainIntake | Mapping[str, Any] | None = None,
    research_plan: ResearchConversationPlan | Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> PrivacySensitiveTechnologyBoundary:
    return build_privacy_sensitive_technology_boundary_v1(domain_intake=domain_intake, research_plan=research_plan, **kwargs)


# ---------------------------------------------------------------------------
# Internal detail builders
# ---------------------------------------------------------------------------


def _safe_metadata(
    intake: BroadTopicDomainIntake,
    plan: ResearchConversationPlan | None,
    ctx: Mapping[str, bool],
    decision: str,
    guidance: str,
) -> dict[str, Any]:
    return {
        "source": "privacy_sensitive_technology_boundary_v1",
        "source_intake_id": intake.intake_id,
        "source_plan_id": plan.plan_id if plan else "",
        "domain_family": intake.domain_family,
        "technology_area": intake.safe_topic_descriptor,
        "allowed_guidance_level": guidance,
        "context_tags": _dedupe_preserve(
            tag for tag in (
                "authenticated_context" if ctx["authenticated_user_context"] else "",
                "terms_accepted" if ctx["terms_acceptance_context"] else "",
                "responsible_use" if ctx["responsible_use_context"] else "",
                "beneficial_use" if ctx["beneficial_use_detected"] else "",
                "assistive_health" if ctx["assistive_health_support_intent"] else "",
                "person_sensitive" if ctx["person_tracking_sensitive"] else "",
                "home_context" if ctx["home_monitoring_sensitive"] else "",
                "workplace_context" if ctx["workplace_monitoring_sensitive"] else "",
                "minor_or_vulnerable_context" if ctx["minor_or_vulnerable_person_sensitive"] else "",
                "medical_boundary" if ctx["medical_claim_boundary_required"] else "",
            ) if tag
        ),
    }



def _required_owner_questions(intake: BroadTopicDomainIntake, ctx: Mapping[str, bool], decision: str) -> tuple[str, ...]:
    questions: list[str] = []
    if ctx["person_tracking_sensitive"]:
        questions.append("Which people may be affected, and what consent or authorization applies to each of them?")
    if ctx["beneficial_use_detected"]:
        questions.append("Is the intent assistive support, safety support, or a general research question?")
    if ctx["assistive_health_support_intent"]:
        questions.append("Is this wellness or routine support only, or are you asking for diagnosis or treatment claims?")
    if ctx["medical_claim_boundary_required"]:
        questions.append("What validation and review are in place before anyone relies on health-related outputs?")
    if ctx["emergency_escalation_requires_explicit_permission"]:
        questions.append("What explicit permission model and dismissal/override path will control any escalation?")
    if ctx["workplace_monitoring_sensitive"]:
        questions.append("What lawful context and affected-person consent exist for any workplace setting?")
    if ctx["minor_or_vulnerable_person_sensitive"]:
        questions.append("What stricter lawful and consent context applies because minors or vulnerable people may be affected?")
    if not questions:
        questions.append("What exact sensing or support scenario are you evaluating, and what evidence do you want first?")
    return _dedupe_preserve(questions)



def _friction_capture_triggers(intake: BroadTopicDomainIntake, ctx: Mapping[str, bool], decision: str) -> tuple[str, ...]:
    triggers = [
        "consent or lawfulness context still unclear",
        "affected-person permissions need mapping",
    ]
    if ctx["person_tracking_sensitive"]:
        triggers.append("person-sensitive sensing requires strict boundary review")
    if ctx["beneficial_use_detected"]:
        triggers.append("assistive intent should stay bounded and non-invasive")
    if ctx["medical_claim_boundary_required"]:
        triggers.append("health claim boundary and validation evidence missing")
    if ctx["emergency_escalation_requires_explicit_permission"]:
        triggers.append("explicit permission and override path need definition")
    if ctx["workplace_monitoring_sensitive"]:
        triggers.append("workplace lawful context and employee rights need review")
    if ctx["minor_or_vulnerable_person_sensitive"]:
        triggers.append("minor or vulnerable-person context needs stricter review")
    if decision in {"require_boundary_clarification", "require_consent_and_lawfulness_context"}:
        triggers.append("boundary clarification should precede any prototype detail")
    return _dedupe_preserve(triggers)



def _recommended_response_mode(decision: str, guidance: str) -> str:
    if decision in {"refuse_covert_or_abusive_deployment", "blocked_sensitive_use"}:
        return "refusal_boundary"
    if decision == "require_medical_claim_boundary":
        return "medical_claim_boundary"
    if decision == "allow_privacy_by_design_prototype_plan":
        return "privacy_by_design_plan"
    if decision == "allow_consent_based_assistive_research":
        return "assistive_safety_research_plan"
    if decision == "allow_high_level_prototype_only":
        return "high_level_prototype_path"
    if decision == "require_consent_and_lawfulness_context" or decision == "require_affected_person_consent_context":
        return "boundary_clarification"
    if decision == "require_evidence_before_prototype":
        return "evidence_request"
    if decision == "allow_bounded_research":
        return "bounded_research_plan" if guidance != "research_questions_only" else "evidence_request"
    return "boundary_clarification"


# ---------------------------------------------------------------------------
# Validation and summaries
# ---------------------------------------------------------------------------


def validate_privacy_sensitive_technology_boundary_v1(boundary: Any) -> bool:
    if _collect_forbidden_fields(boundary):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_claim_marker(boundary):
        raise ValidationError("forbidden_public_or_claim_language_present")
    if _contains_unsafe_marker(boundary):
        raise ValidationError("unsafe_marker_present")

    if is_dataclass(boundary):
        normalized = boundary
    elif isinstance(boundary, Mapping):
        allowed = {field.name for field in PrivacySensitiveTechnologyBoundary.__dataclass_fields__.values()}
        extra = set(str(key) for key in boundary.keys()) - allowed
        if extra:
            raise ValidationError("unknown_fields_present")
        normalized = PrivacySensitiveTechnologyBoundary(
            boundary_id=_safe_text(boundary.get("boundary_id")),
            source_intake_id=_safe_text(boundary.get("source_intake_id")),
            source_plan_id=_safe_text(boundary.get("source_plan_id")),
            domain_family=_safe_text(boundary.get("domain_family")),
            technology_area=_safe_text(boundary.get("technology_area")),
            authenticated_user_context=bool(boundary.get("authenticated_user_context")),
            terms_acceptance_context=bool(boundary.get("terms_acceptance_context")),
            responsible_use_context=bool(boundary.get("responsible_use_context")),
            affected_person_consent_required=bool(boundary.get("affected_person_consent_required")),
            affected_person_consent_present=bool(boundary.get("affected_person_consent_present")),
            consent_context_present=bool(boundary.get("consent_context_present")),
            lawfulness_context_present=bool(boundary.get("lawfulness_context_present")),
            lawfulness_required=bool(boundary.get("lawfulness_required")),
            beneficial_use_detected=bool(boundary.get("beneficial_use_detected")),
            assistive_health_support_intent=bool(boundary.get("assistive_health_support_intent")),
            self_care_context=bool(boundary.get("self_care_context")),
            caregiver_context_present=bool(boundary.get("caregiver_context_present")),
            security_safety_context_present=bool(boundary.get("security_safety_context_present")),
            routine_support_context_present=bool(boundary.get("routine_support_context_present")),
            medical_claim_boundary_required=bool(boundary.get("medical_claim_boundary_required")),
            medical_diagnosis_claim_blocked=bool(boundary.get("medical_diagnosis_claim_blocked")),
            treatment_recommendation_blocked=bool(boundary.get("treatment_recommendation_blocked")),
            validation_required_before_reliance=bool(boundary.get("validation_required_before_reliance")),
            regulatory_review_required_for_health_product=bool(boundary.get("regulatory_review_required_for_health_product")),
            local_processing_recommended=bool(boundary.get("local_processing_recommended")),
            data_minimization_required=bool(boundary.get("data_minimization_required")),
            user_control_required=bool(boundary.get("user_control_required")),
            auditability_recommended=bool(boundary.get("auditability_recommended")),
            raw_signal_retention_discouraged=bool(boundary.get("raw_signal_retention_discouraged")),
            emergency_escalation_requires_explicit_permission=bool(boundary.get("emergency_escalation_requires_explicit_permission")),
            privacy_risk_level=_safe_text(boundary.get("privacy_risk_level")),
            safety_risk_level=_safe_text(boundary.get("safety_risk_level")),
            legal_risk_level=_safe_text(boundary.get("legal_risk_level")),
            abuse_risk_level=_safe_text(boundary.get("abuse_risk_level")),
            boundary_decision=_safe_text(boundary.get("boundary_decision")),
            allowed_guidance_level=_safe_text(boundary.get("allowed_guidance_level")),
            deployment_guidance_allowed=bool(boundary.get("deployment_guidance_allowed")),
            covert_use_blocked=bool(boundary.get("covert_use_blocked")),
            person_tracking_sensitive=bool(boundary.get("person_tracking_sensitive")),
            minor_or_vulnerable_person_sensitive=bool(boundary.get("minor_or_vulnerable_person_sensitive")),
            workplace_monitoring_sensitive=bool(boundary.get("workplace_monitoring_sensitive")),
            home_monitoring_sensitive=bool(boundary.get("home_monitoring_sensitive")),
            risk_labels=_normalize_sequence(boundary.get("risk_labels")),
            required_owner_questions=_normalize_sequence(boundary.get("required_owner_questions")),
            allowed_next_steps=_normalize_sequence(boundary.get("allowed_next_steps")),
            forbidden_guidance=_normalize_sequence(boundary.get("forbidden_guidance")),
            friction_capture_triggers=_normalize_sequence(boundary.get("friction_capture_triggers")),
            recommended_response_mode=_safe_text(boundary.get("recommended_response_mode")),
            public_claim_allowed=bool(boundary.get("public_claim_allowed")),
            iss_internal_reference_allowed=bool(boundary.get("iss_internal_reference_allowed")),
            learning_claimed=bool(boundary.get("learning_claimed")),
            runtime_authority=bool(boundary.get("runtime_authority")),
            writes_state=bool(boundary.get("writes_state")),
            model_provider_used=bool(boundary.get("model_provider_used")),
            safe_metadata=dict(boundary.get("safe_metadata") or {}),
        )
    else:
        raise ValidationError("boundary_must_be_dataclass_or_mapping")

    if not normalized.boundary_id:
        raise ValidationError("boundary_id_required")
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
    if not normalized.technology_area:
        raise ValidationError("technology_area_required")
    if normalized.boundary_decision not in ALLOWED_BOUNDARY_DECISIONS_V1:
        raise ValidationError("unknown_boundary_decision")
    if normalized.allowed_guidance_level not in ALLOWED_GUIDANCE_LEVELS_V1:
        raise ValidationError("unknown_allowed_guidance_level")
    if normalized.privacy_risk_level not in ALLOWED_RISK_LEVELS_V1:
        raise ValidationError("unknown_privacy_risk_level")
    if normalized.safety_risk_level not in ALLOWED_RISK_LEVELS_V1:
        raise ValidationError("unknown_safety_risk_level")
    if normalized.legal_risk_level not in ALLOWED_RISK_LEVELS_V1:
        raise ValidationError("unknown_legal_risk_level")
    if normalized.abuse_risk_level not in ALLOWED_RISK_LEVELS_V1:
        raise ValidationError("unknown_abuse_risk_level")
    if normalized.recommended_response_mode not in ALLOWED_RESPONSE_MODES_V1:
        raise ValidationError("unknown_recommended_response_mode")

    for field_name in (
        "authenticated_user_context",
        "terms_acceptance_context",
        "responsible_use_context",
        "affected_person_consent_required",
        "affected_person_consent_present",
        "consent_context_present",
        "lawfulness_context_present",
        "lawfulness_required",
        "beneficial_use_detected",
        "assistive_health_support_intent",
        "self_care_context",
        "caregiver_context_present",
        "security_safety_context_present",
        "routine_support_context_present",
        "medical_claim_boundary_required",
        "medical_diagnosis_claim_blocked",
        "treatment_recommendation_blocked",
        "validation_required_before_reliance",
        "regulatory_review_required_for_health_product",
        "local_processing_recommended",
        "data_minimization_required",
        "user_control_required",
        "auditability_recommended",
        "raw_signal_retention_discouraged",
        "emergency_escalation_requires_explicit_permission",
        "deployment_guidance_allowed",
        "covert_use_blocked",
        "person_tracking_sensitive",
        "minor_or_vulnerable_person_sensitive",
        "workplace_monitoring_sensitive",
        "home_monitoring_sensitive",
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
    if normalized.allowed_guidance_level == "refusal_only" and normalized.boundary_decision not in {"refuse_covert_or_abusive_deployment", "blocked_sensitive_use", "require_boundary_clarification", "require_consent_and_lawfulness_context", "require_affected_person_consent_context", "require_medical_claim_boundary"}:
        raise ValidationError("refusal_only_mismatch")
    if normalized.person_tracking_sensitive and normalized.deployment_guidance_allowed:
        raise ValidationError("deployment_guidance_allowed_for_high_risk_person_tracking")
    if (normalized.covert_use_blocked is False) and (normalized.person_tracking_sensitive or normalized.privacy_risk_level == "high" or normalized.abuse_risk_level in {"high", "blocked"}):
        raise ValidationError("covert_use_blocked_required_for_sensitive_use")
    if normalized.medical_claim_boundary_required and (not normalized.medical_diagnosis_claim_blocked or not normalized.treatment_recommendation_blocked):
        raise ValidationError("medical_claim_boundaries_required")
    if normalized.emergency_escalation_requires_explicit_permission and not normalized.affected_person_consent_required and normalized.boundary_decision not in {"allow_bounded_research", "allow_high_level_prototype_only", "allow_privacy_by_design_prototype_plan", "allow_consent_based_assistive_research"}:
        raise ValidationError("emergency_escalation_requires_explicit_permission_mismatch")

    for field_name in (
        "risk_labels",
        "required_owner_questions",
        "allowed_next_steps",
        "forbidden_guidance",
        "friction_capture_triggers",
    ):
        if not isinstance(getattr(normalized, field_name), tuple):
            raise ValidationError(f"{field_name}_must_be_tuple")
        if not getattr(normalized, field_name):
            raise ValidationError(f"{field_name}_required")

    if normalized.boundary_decision in {"allow_consent_based_assistive_research", "allow_privacy_by_design_prototype_plan", "allow_high_level_prototype_only"} and not normalized.lawfulness_context_present:
        raise ValidationError("lawfulness_context_required_for_sensitive_allowance")
    if normalized.person_tracking_sensitive and not normalized.affected_person_consent_required:
        raise ValidationError("affected_person_consent_required_for_person_sensitive_use")
    if normalized.person_tracking_sensitive and not normalized.lawfulness_required:
        raise ValidationError("lawfulness_required_for_person_sensitive_use")
    emergency_context = _has_token(normalized.required_owner_questions, EMERGENCY_CONTEXT_TOKENS_V1) or _has_token(normalized.allowed_next_steps, EMERGENCY_CONTEXT_TOKENS_V1) or _has_token(normalized.forbidden_guidance, EMERGENCY_CONTEXT_TOKENS_V1)
    if emergency_context and not normalized.emergency_escalation_requires_explicit_permission:
        raise ValidationError("emergency_escalation_requires_explicit_permission_required")
    if normalized.boundary_decision in {"allow_consent_based_assistive_research", "allow_privacy_by_design_prototype_plan"} and not normalized.medical_claim_boundary_required and normalized.assistive_health_support_intent:
        raise ValidationError("medical_claim_boundary_required_for_health_support")

    return True



def summarize_privacy_sensitive_technology_boundary_v1(boundary: PrivacySensitiveTechnologyBoundary | Mapping[str, Any]) -> PrivacySensitiveTechnologyBoundarySummary:
    validate_privacy_sensitive_technology_boundary_v1(boundary)
    normalized = boundary if is_dataclass(boundary) else PrivacySensitiveTechnologyBoundary(**boundary)  # type: ignore[arg-type]
    return PrivacySensitiveTechnologyBoundarySummary(
        summary_type=SUMMARY_TYPE_V1,
        boundary_id=normalized.boundary_id,
        boundary_decision=normalized.boundary_decision,
        domain_family=normalized.domain_family,
        technology_area=normalized.technology_area,
        privacy_risk_level=normalized.privacy_risk_level,
        safety_risk_level=normalized.safety_risk_level,
        legal_risk_level=normalized.legal_risk_level,
        abuse_risk_level=normalized.abuse_risk_level,
        allowed_guidance_level=normalized.allowed_guidance_level,
        beneficial_use_detected=normalized.beneficial_use_detected,
        covert_use_blocked=normalized.covert_use_blocked,
        deployment_guidance_allowed=normalized.deployment_guidance_allowed,
        medical_claim_boundary_required=normalized.medical_claim_boundary_required,
    )



def to_privacy_sensitive_technology_boundary_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


# ---------------------------------------------------------------------------
# Initial examples
# ---------------------------------------------------------------------------


def build_initial_privacy_sensitive_technology_boundary_examples_v1() -> tuple[PrivacySensitiveTechnologyBoundary, ...]:
    examples: list[PrivacySensitiveTechnologyBoundary] = []

    def _add(
        descriptor: str,
        prompt_labels: Sequence[str],
        owner_intent_labels: Sequence[str],
        risk_hints: Sequence[str],
        known_unknown_hints: Sequence[str],
        *,
        context_overrides: Mapping[str, Any] | None = None,
    ) -> None:
        intake = build_broad_topic_domain_intake_v1(
            safe_topic_descriptor=descriptor,
            prompt_labels=prompt_labels,
            owner_intent_labels=owner_intent_labels,
            risk_hints=risk_hints,
            known_unknown_hints=known_unknown_hints,
            existing_behavior_pack_refs=(),
        )
        plan = build_research_conversation_plan_v1(domain_intake=intake)
        examples.append(build_privacy_sensitive_technology_boundary_v1(domain_intake=intake, research_plan=plan, **(dict(context_overrides or {}))))

    _add(
        "WiFi/RF sensing for human presence and location in a house",
        ("wifi sensing", "human presence", "location", "privacy"),
        ("research",),
        ("high risk", "privacy-sensitive", "consent required", "lawful only"),
        ("unfamiliar", "researchable"),
        context_overrides={"authenticated_user_context": True, "terms_acceptance_context": True, "responsible_use_context": True},
    )
    _add(
        "WiFi/RF sensing for medication reminders and routine support",
        ("wifi sensing", "medication reminder", "routine support", "self care"),
        ("research",),
        ("consent required", "health support", "privacy-sensitive"),
        ("unfamiliar",),
        context_overrides={"authenticated_user_context": True, "terms_acceptance_context": True, "responsible_use_context": True, "consent_context_present": True, "lawfulness_context_present": True, "affected_person_consent_present": True},
    )
    _add(
        "WiFi/RF sensing for consent-based research in a home setting",
        ("wifi sensing", "research only", "privacy"),
        ("research",),
        ("consent required", "lawful only"),
        ("researchable",),
        context_overrides={"authenticated_user_context": True, "terms_acceptance_context": True, "responsible_use_context": True, "consent_context_present": True, "lawfulness_context_present": True},
    )
    _add(
        "Medication routine reminder with user-configured safety support",
        ("medication reminder", "routine", "support"),
        ("learn explain",),
        ("health support", "wellness"),
        ("known existing pack",),
        context_overrides={"authenticated_user_context": True, "terms_acceptance_context": True, "responsible_use_context": True, "consent_context_present": True, "lawfulness_context_present": True, "affected_person_consent_present": True},
    )
    _add(
        "Breathing anomaly awareness with consent for home support",
        ("breathing", "anomaly awareness", "home support"),
        ("research",),
        ("health support", "privacy-sensitive"),
        ("unfamiliar",),
        context_overrides={"authenticated_user_context": True, "terms_acceptance_context": True, "responsible_use_context": True, "consent_context_present": True, "lawfulness_context_present": True, "affected_person_consent_present": True},
    )
    _add(
        "Emergency escalation design with explicit permission and override controls",
        ("emergency escalation", "override", "permission"),
        ("research",),
        ("safety critical",),
        ("unfamiliar",),
        context_overrides={"authenticated_user_context": True, "terms_acceptance_context": True, "responsible_use_context": True, "consent_context_present": True, "lawfulness_context_present": True, "emergency_escalation_requires_explicit_permission": True},
    )
    _add(
        "Workplace monitoring boundary review for a lawful employee-safety program",
        ("workplace", "employee safety", "monitoring"),
        ("safety legal privacy review",),
        ("workplace context", "privacy-sensitive"),
        ("unfamiliar",),
        context_overrides={"authenticated_user_context": True, "terms_acceptance_context": True, "responsible_use_context": True},
    )
    _add(
        "Minor-sensitive sensing boundary review",
        ("minors", "vulnerable people", "home safety"),
        ("safety legal privacy review",),
        ("high risk", "minor context"),
        ("unfamiliar",),
        context_overrides={"authenticated_user_context": True, "terms_acceptance_context": True, "responsible_use_context": True},
    )
    _add(
        "Generic sensor research for a lab prototype",
        ("sensor research", "lab prototype"),
        ("research",),
        ("low risk",),
        ("known existing pack",),
        context_overrides={"authenticated_user_context": True, "terms_acceptance_context": True, "responsible_use_context": True},
    )
    _add(
        "Biometric identity inference boundary review",
        ("biometric", "identity", "face", "voice"),
        ("research",),
        ("high privacy risk", "legal review required"),
        ("unfamiliar",),
        context_overrides={"authenticated_user_context": True, "terms_acceptance_context": True, "responsible_use_context": True},
    )

    return tuple(examples)


# Backwards-compatible alias names.
build_privacy_sensitive_technology_boundary = build_privacy_sensitive_technology_boundary_v1
evaluate_privacy_sensitive_technology_boundary = evaluate_privacy_sensitive_technology_boundary_v1
validate_privacy_sensitive_technology_boundary = validate_privacy_sensitive_technology_boundary_v1
summarize_privacy_sensitive_technology_boundary = summarize_privacy_sensitive_technology_boundary_v1
to_privacy_sensitive_technology_boundary_json_safe = to_privacy_sensitive_technology_boundary_json_safe_v1
build_initial_privacy_sensitive_technology_boundary_examples = build_initial_privacy_sensitive_technology_boundary_examples_v1
