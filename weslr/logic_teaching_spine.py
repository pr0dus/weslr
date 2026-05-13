from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
import string
from typing import Any


SAFE_CONFIDENCE_VALUES = {"low", "medium", "high"}
SAFE_VALIDITY_TYPES = {"valid", "invalid", "ambiguous", "unsupported", "unknown"}
SAFE_SUPPORT_STATUSES = {"supported", "unsupported", "invalid", "ambiguous", "unknown"}
SAFE_TEACHING_MODES = {"beginner", "technical", "academic", "spock", "operator_audit", "unknown"}
SAFE_TEACHING_EXPLANATION_SUPPORT_STATUSES = {
    "supported", "contradicted", "counterexample_supported", "rule_application_supported",
    "template_completed", "ambiguous", "unsupported", "unknown"
}
SAFE_PROPOSITION_ROLES = {"premise", "choice_claim", "background", "unknown"}
SAFE_PROPOSITION_MERGE_ORIGINS = {"predicate_derived", "binding_derived", "merged", "unknown"}
SAFE_SIMPLE_INFERENCE_PATTERN_TYPES = {"shared-subject", "shared-object", "relation-overlap", "contradiction-candidate", "duplicate-support-candidate", "transitivity-candidate", "unsupported/no-pattern"}
SAFE_SIMPLE_INFERENCE_VALIDITY_STATUSES = {"candidate_only", "unsupported", "ambiguous", "unknown"}
SAFE_REASONING_CONTEXT_QUESTION_TARGET_TYPES = {"must_be_true", "must_be_false", "follows", "does_not_follow", "valid_argument", "invalid_argument", "counterexample", "completion", "unknown"}
SAFE_REASONING_CONTEXT_PREMISE_CONTEXT_TYPES = {"given_fact", "conditional_rule", "quantified_rule", "exclusion_rule", "definition_like", "background_context", "mixed_context", "unknown"}
SAFE_REASONING_CONTEXT_CHOICE_TARGET_ROLES = {"candidate_conclusion", "candidate_counterexample", "candidate_invalid_statement", "candidate_valid_statement", "candidate_restatement", "candidate_irrelevant", "fragment_needs_binding", "unknown"}
SAFE_REASONING_CONTEXT_EXPECTED_RELATIONS = {"support", "contradict", "instantiate_rule", "apply_condition", "test_validity", "provide_counterexample", "complete_template", "unknown"}
SAFE_REASONING_CONTEXT_CANDIDATE_SUPPORT_ROLES = {"supports_target", "contradicts_target", "tests_target", "restates_target", "irrelevant_to_target", "unknown"}
SAFE_PROOF_STEP_CANDIDATE_TYPES = {"support_step_candidate", "contradiction_step_candidate", "counterexample_step_candidate", "rule_application_candidate", "invalidity_test_candidate", "template_completion_candidate", "unsupported_step_candidate"}
SAFE_PROOF_STEP_CANDIDATE_SUPPORT_STATUSES = {"candidate_only", "insufficient_support", "ambiguous", "unsupported", "unknown"}
SAFE_PROOF_STEP_SUPPORT_STATUSES = {"supported", "contradicted", "counterexample_supported", "rule_application_supported", "template_completed", "ambiguous", "unsupported"}
SAFE_CONDITIONAL_FORM_LABELS = {"modus_ponens", "modus_tollens", "affirming_consequent", "denying_antecedent", "ambiguous_form", "unsupported_form"}
SAFE_CONDITIONAL_FORM_SUPPORT_ASSESSMENTS = {"supported_form", "fallacy_shaped", "insufficient_structure"}
_ALIGNMENT_STOPWORDS = {"the", "a", "an", "of", "to", "and", "or"}


@dataclass
class PropositionLegibilityRecord:
    human_translation_available: bool = True
    redacted_summary_only: bool = True
    stores_raw_benchmark_text: bool = False
    hides_unsupported_assumptions: bool = False
    private_symbolic_authority: bool = False
    human_explanation: str = "Human-legible translation is required for high-confidence propositions."


@dataclass
class PropositionAntiGamingRecord:
    uses_answer_key: bool = False
    uses_item_id_as_authority: bool = False
    uses_answer_position_bias: bool = False
    claims_official_score: bool = False
    benchmark_specific_tuning: bool = False
    uses_private_symbolic_authority: bool = False
    no_answer_selection: bool = True
    human_explanation: str = "Schema records are structural only and do not use benchmark authority or answer selection."


@dataclass
class PropositionCandidate:
    schema_version: str = "WESLR_LOGIC_TEACHING_SPINE_V1"
    proposition_id: str = ""
    source_predicate_ids: list[str] = field(default_factory=list)
    source_statement_ids: list[str] = field(default_factory=list)
    source_statement_roles: list[str] = field(default_factory=list)
    proposition_role: str = "unknown"
    proposition_type: str = "unknown"
    subject: str = ""
    relation: str = ""
    object: str = ""
    subject_canonical_hint: str = ""
    object_canonical_hint: str = ""
    relation_canonical_hint: str = ""
    subject_fingerprint: str = ""
    object_fingerprint: str = ""
    polarity: str = "positive"
    quantifier: str = ""
    modality: str = ""
    confidence: str = "low"
    human_translation: str = ""
    unsupported_gaps: list[str] = field(default_factory=list)
    legibility: PropositionLegibilityRecord = field(default_factory=PropositionLegibilityRecord)
    anti_gaming: PropositionAntiGamingRecord = field(default_factory=PropositionAntiGamingRecord)


@dataclass
class PropositionMergeCandidate:
    schema_version: str = "1.0"
    merge_id: str = ""
    structural_signature: str = ""
    source_proposition_ids: list[str] = field(default_factory=list)
    source_origins: list[str] = field(default_factory=list)
    proposition_role: str = "unknown"
    subject_canonical_hint: str = ""
    relation_canonical_hint: str = ""
    object_canonical_hint: str = ""
    confidence_summary: str = "low"
    duplicate_count: int = 0
    unsupported_gaps: list[str] = field(default_factory=list)
    human_explanation: str = ""
    legibility: PropositionLegibilityRecord = field(default_factory=PropositionLegibilityRecord)
    anti_gaming: PropositionAntiGamingRecord = field(default_factory=PropositionAntiGamingRecord)


@dataclass
class SimpleInferencePatternCandidate:
    schema_version: str = "1.0"
    candidate_id: str = ""
    pattern_type: str = "unsupported/no-pattern"
    source_merge_ids: list[str] = field(default_factory=list)
    source_proposition_ids: list[str] = field(default_factory=list)
    premise_role_count: int = 0
    choice_role_count: int = 0
    shared_subject: bool = False
    shared_object: bool = False
    relation_overlap: bool = False
    contradiction_signal: bool = False
    transitivity_signal: bool = False
    confidence: str = "low"
    validity_status: str = "unknown"
    unsupported_gaps: list[str] = field(default_factory=list)
    human_explanation: str = ""
    legibility: PropositionLegibilityRecord = field(default_factory=PropositionLegibilityRecord)
    anti_gaming: PropositionAntiGamingRecord = field(default_factory=PropositionAntiGamingRecord)


@dataclass
class ReasoningContextBindingCandidate:
    schema_version: str = "1.0"
    binding_id: str = ""
    source_premise_proposition_ids: list[str] = field(default_factory=list)
    source_question_instruction_ids: list[str] = field(default_factory=list)
    source_choice_proposition_ids: list[str] = field(default_factory=list)
    question_target_type: str = "unknown"
    premise_context_type: str = "unknown"
    choice_target_role: str = "unknown"
    expected_reasoning_relation: str = "unknown"
    candidate_support_role: str = "unknown"
    conditional_form_slots: dict[str, Any] = field(default_factory=dict)
    confidence: str = "low"
    unsupported_gaps: list[str] = field(default_factory=list)
    human_explanation: str = ""
    legibility: PropositionLegibilityRecord = field(default_factory=PropositionLegibilityRecord)
    anti_gaming: PropositionAntiGamingRecord = field(default_factory=PropositionAntiGamingRecord)


@dataclass
class ProofStepCandidate:
    schema_version: str = "1.0"
    candidate_id: str = ""
    source_context_binding_ids: list[str] = field(default_factory=list)
    source_premise_proposition_ids: list[str] = field(default_factory=list)
    source_choice_proposition_ids: list[str] = field(default_factory=list)
    candidate_type: str = "unsupported_step_candidate"
    expected_reasoning_relation: str = "unknown"
    inference_pattern_hint: str = ""
    support_status: str = "unknown"
    conditional_form_mapping: dict[str, Any] = field(default_factory=dict)
    conditional_form_mapping_origin: str = "insufficient_slot_evidence"
    confidence: str = "low"
    unsupported_gaps: list[str] = field(default_factory=list)
    human_explanation: str = ""
    legibility: PropositionLegibilityRecord = field(default_factory=PropositionLegibilityRecord)
    anti_gaming: PropositionAntiGamingRecord = field(default_factory=PropositionAntiGamingRecord)


@dataclass
class ConditionalFormMappingResult:
    schema_version: str = "1.0"
    form_label: str = "ambiguous_form"
    support_assessment: str = "insufficient_structure"
    conditional_direction: str = "unknown"
    asserted_literal: str = "unknown"
    conclusion_literal: str = "unknown"
    slot_binding_status: str = "unknown"
    fallacy_shaped: bool = False
    supported_form: bool = False
    unsupported_gaps: list[str] = field(default_factory=list)
    human_explanation: str = (
        "Helper-only conditional form mapping from structural slots; does not select answers, "
        "assert truth, claim soundness, or use benchmark authority."
    )


@dataclass
class InferencePattern:
    schema_version: str = "1.0"
    pattern_id: str = ""
    pattern_family: str = ""
    pattern_name: str = ""
    validity_type: str = "unknown"
    required_proposition_roles: list[str] = field(default_factory=list)
    supported_proposition_types: list[str] = field(default_factory=list)
    fallacy_name: str = ""
    description: str = ""
    human_explanation: str = ""
    counterexample_required: bool = False
    confidence: str = "low"
    legibility: PropositionLegibilityRecord = field(default_factory=PropositionLegibilityRecord)
    anti_gaming: PropositionAntiGamingRecord = field(default_factory=PropositionAntiGamingRecord)


@dataclass
class ProofStep:
    schema_version: str = "1.0"
    proof_step_id: str = ""
    source_candidate_id: str = ""
    source_context_binding_ids: list[str] = field(default_factory=list)
    source_premise_proposition_ids: list[str] = field(default_factory=list)
    source_choice_proposition_ids: list[str] = field(default_factory=list)
    reasoning_relation: str = "unknown"
    inference_pattern: str = ""
    support_status: str = "unsupported"
    source_proposition_ids: list[str] = field(default_factory=list)
    target_proposition_id: str = ""
    inference_pattern_id: str = ""
    warrant: str = ""
    validity_status: str = "unknown"
    conditional_form_mapping: dict[str, Any] = field(default_factory=dict)
    conditional_form_mapping_origin: str = "insufficient_slot_evidence"
    confidence: str = "low"
    human_explanation: str = ""
    unsupported_gaps: list[str] = field(default_factory=list)
    unsupported_assumptions: list[str] = field(default_factory=list)
    requires_counterexample: bool = False
    legibility: PropositionLegibilityRecord = field(default_factory=PropositionLegibilityRecord)
    anti_gaming: PropositionAntiGamingRecord = field(default_factory=PropositionAntiGamingRecord)


@dataclass
class CounterexampleCandidate:
    schema_version: str = "1.0"
    counterexample_id: str = ""
    challenged_proposition_id: str = ""
    challenged_proof_step_id: str = ""
    counterexample_type: str = ""
    possible_world_sketch: str = ""
    violated_assumption: str = ""
    fallacy_pattern_id: str = ""
    confidence: str = "low"
    human_explanation: str = ""
    unsupported_gaps: list[str] = field(default_factory=list)
    legibility: PropositionLegibilityRecord = field(default_factory=PropositionLegibilityRecord)
    anti_gaming: PropositionAntiGamingRecord = field(default_factory=PropositionAntiGamingRecord)


@dataclass
class TeachingExplanation:
    schema_version: str = "1.0"
    explanation_id: str = ""
    source_proposition_ids: list[str] = field(default_factory=list)
    source_proof_step_ids: list[str] = field(default_factory=list)
    source_context_binding_ids: list[str] = field(default_factory=list)
    source_counterexample_ids: list[str] = field(default_factory=list)
    conclusion: str = ""
    support_status: str = "unknown"
    core_claim: str = ""
    why_it_follows_or_fails: str = ""
    pattern_name: str = ""
    fallacy_name: str = ""
    counterexample_note: str = ""
    confidence: str = "low"
    common_fallacy: str = ""
    learner_level: str = "general"
    teaching_mode: str = "unknown"
    step_by_step_explanation: list[str] = field(default_factory=list)
    uncertainty_note: str = ""
    human_explanation: str = ""
    unsupported_gaps: list[str] = field(default_factory=list)
    legibility: PropositionLegibilityRecord = field(default_factory=PropositionLegibilityRecord)
    anti_gaming: PropositionAntiGamingRecord = field(default_factory=PropositionAntiGamingRecord)


def _validate_shared_safety(legibility: PropositionLegibilityRecord, anti_gaming: PropositionAntiGamingRecord) -> list[str]:
    messages: list[str] = []
    if anti_gaming.uses_answer_key:
        messages.append("answer-key use is forbidden")
    if anti_gaming.uses_item_id_as_authority:
        messages.append("item-id authority is forbidden")
    if anti_gaming.claims_official_score:
        messages.append("official-score claim is forbidden")
    if legibility.stores_raw_benchmark_text:
        messages.append("raw benchmark storage by default is forbidden")
    if legibility.private_symbolic_authority or anti_gaming.uses_private_symbolic_authority:
        messages.append("private symbolic authority is forbidden")
    if anti_gaming.uses_answer_position_bias:
        messages.append("answer-position bias is forbidden")
    if anti_gaming.benchmark_specific_tuning:
        messages.append("benchmark-specific tuning is forbidden")
    if not anti_gaming.no_answer_selection:
        messages.append("answer selection must remain disabled")
    if not legibility.redacted_summary_only:
        messages.append("redacted summaries are required")
    if legibility.hides_unsupported_assumptions:
        messages.append("unsupported assumptions must remain visible")
    return messages


def _legibility_safe(legibility: PropositionLegibilityRecord) -> bool:
    return not any(
        [
            legibility.stores_raw_benchmark_text,
            legibility.hides_unsupported_assumptions,
            legibility.private_symbolic_authority,
        ]
    )


def _anti_gaming_safe(anti_gaming: PropositionAntiGamingRecord) -> bool:
    return not any(
        [
            anti_gaming.uses_answer_key,
            anti_gaming.uses_item_id_as_authority,
            anti_gaming.uses_answer_position_bias,
            anti_gaming.claims_official_score,
            anti_gaming.benchmark_specific_tuning,
            anti_gaming.uses_private_symbolic_authority,
            not anti_gaming.no_answer_selection,
        ]
    )


def create_empty_proposition_candidate(
    *,
    proposition_id: str = "",
    source_predicate_ids: list[str] | None = None,
    source_statement_ids: list[str] | None = None,
    source_statement_roles: list[str] | None = None,
    proposition_role: str = "unknown",
    proposition_type: str = "unknown",
) -> PropositionCandidate:
    return PropositionCandidate(
        proposition_id=proposition_id,
        source_predicate_ids=list(source_predicate_ids or []),
        source_statement_ids=list(source_statement_ids or []),
        source_statement_roles=[normalize_proposition_role(role) for role in list(source_statement_roles or []) if str(role).strip()],
        proposition_role=normalize_proposition_role(proposition_role),
        proposition_type=proposition_type,
    )


def proposition_candidate_to_dict(candidate: PropositionCandidate) -> dict[str, Any]:
    return asdict(candidate)


def proposition_candidate_from_dict(data: dict[str, Any]) -> PropositionCandidate:
    legibility_data = data.get("legibility") or {}
    anti_gaming_data = data.get("anti_gaming") or {}
    return PropositionCandidate(
        schema_version=data.get("schema_version", "WESLR_LOGIC_TEACHING_SPINE_V1"),
        proposition_id=data.get("proposition_id", ""),
        source_predicate_ids=list(data.get("source_predicate_ids") or []),
        source_statement_ids=list(data.get("source_statement_ids") or []),
        source_statement_roles=[normalize_proposition_role(role) for role in list(data.get("source_statement_roles") or []) if str(role).strip()],
        proposition_role=normalize_proposition_role(data.get("proposition_role", "unknown")),
        proposition_type=data.get("proposition_type", "unknown"),
        subject=data.get("subject", ""),
        relation=data.get("relation", ""),
        object=data.get("object", ""),
        subject_canonical_hint=data.get("subject_canonical_hint", ""),
        object_canonical_hint=data.get("object_canonical_hint", ""),
        relation_canonical_hint=data.get("relation_canonical_hint", ""),
        subject_fingerprint=data.get("subject_fingerprint", ""),
        object_fingerprint=data.get("object_fingerprint", ""),
        polarity=data.get("polarity", "positive"),
        quantifier=data.get("quantifier", ""),
        modality=data.get("modality", ""),
        confidence=data.get("confidence", "low"),
        human_translation=data.get("human_translation", ""),
        unsupported_gaps=list(data.get("unsupported_gaps") or []),
        legibility=PropositionLegibilityRecord(**legibility_data),
        anti_gaming=PropositionAntiGamingRecord(**anti_gaming_data),
    )


def validate_proposition_candidate(candidate: PropositionCandidate) -> list[str]:
    messages: list[str] = []
    if not candidate.proposition_id:
        messages.append("missing proposition id")
    if candidate.confidence not in SAFE_CONFIDENCE_VALUES:
        messages.append("invalid confidence value")
    if candidate.confidence == "high" and not candidate.human_translation.strip():
        messages.append("missing human translation for high-confidence proposition")
    if candidate.proposition_role not in SAFE_PROPOSITION_ROLES:
        messages.append("invalid proposition role")
    messages.extend(_validate_shared_safety(candidate.legibility, candidate.anti_gaming))
    return messages


def summarize_proposition_candidate(candidate: PropositionCandidate) -> dict[str, Any]:
    return {
        "schema_version": candidate.schema_version,
        "proposition_id": candidate.proposition_id,
        "proposition_role": candidate.proposition_role,
        "proposition_type": candidate.proposition_type,
        "polarity": candidate.polarity,
        "quantifier": candidate.quantifier,
        "modality": candidate.modality,
        "confidence": candidate.confidence,
        "source_predicate_count": len(candidate.source_predicate_ids),
        "source_statement_count": len(candidate.source_statement_ids),
        "source_statement_role_count": len(candidate.source_statement_roles),
        "unsupported_gap_count": len(candidate.unsupported_gaps),
        "human_translation_available": bool(candidate.human_translation.strip()),
        "legibility_safe": _legibility_safe(candidate.legibility),
        "anti_gaming_safe": _anti_gaming_safe(candidate.anti_gaming),
    }



def create_empty_proposition_merge_candidate(
    *,
    merge_id: str = "",
    structural_signature: str = "",
    source_proposition_ids: list[str] | None = None,
    source_origins: list[str] | None = None,
    proposition_role: str = "unknown",
) -> PropositionMergeCandidate:
    return PropositionMergeCandidate(
        merge_id=merge_id,
        structural_signature=structural_signature,
        source_proposition_ids=list(source_proposition_ids or []),
        source_origins=list(source_origins or []),
        proposition_role=normalize_proposition_role(proposition_role),
    )


def proposition_merge_candidate_to_dict(candidate: PropositionMergeCandidate) -> dict[str, Any]:
    return asdict(candidate)


def proposition_merge_candidate_from_dict(data: dict[str, Any]) -> PropositionMergeCandidate:
    legibility_data = data.get("legibility") or {}
    anti_gaming_data = data.get("anti_gaming") or {}
    return PropositionMergeCandidate(
        schema_version=data.get("schema_version", "1.0"),
        merge_id=data.get("merge_id", ""),
        structural_signature=data.get("structural_signature", ""),
        source_proposition_ids=list(data.get("source_proposition_ids") or []),
        source_origins=list(data.get("source_origins") or []),
        proposition_role=normalize_proposition_role(data.get("proposition_role", "unknown")),
        subject_canonical_hint=data.get("subject_canonical_hint", ""),
        relation_canonical_hint=data.get("relation_canonical_hint", ""),
        object_canonical_hint=data.get("object_canonical_hint", ""),
        confidence_summary=data.get("confidence_summary", "low"),
        duplicate_count=int(data.get("duplicate_count", 0) or 0),
        unsupported_gaps=list(data.get("unsupported_gaps") or []),
        human_explanation=data.get("human_explanation", ""),
        legibility=PropositionLegibilityRecord(**legibility_data),
        anti_gaming=PropositionAntiGamingRecord(**anti_gaming_data),
    )


def validate_proposition_merge_candidate(candidate: PropositionMergeCandidate) -> list[str]:
    messages: list[str] = []
    if not candidate.merge_id:
        messages.append("missing merge id")
    if not candidate.structural_signature:
        messages.append("missing structural signature")
    if candidate.confidence_summary not in SAFE_CONFIDENCE_VALUES:
        messages.append("invalid confidence summary")
    if candidate.proposition_role not in SAFE_PROPOSITION_ROLES:
        messages.append("invalid proposition role")
    invalid_origins = [origin for origin in candidate.source_origins if origin not in SAFE_PROPOSITION_MERGE_ORIGINS]
    if invalid_origins:
        messages.append("invalid source origin")
    if candidate.confidence_summary == "high" and not candidate.source_proposition_ids:
        messages.append("empty source proposition ids for high-confidence merge candidate")
    if candidate.confidence_summary == "high" and not candidate.human_explanation.strip():
        messages.append("missing human explanation for high-confidence merge candidate")
    messages.extend(_validate_shared_safety(candidate.legibility, candidate.anti_gaming))
    return messages


def summarize_proposition_merge_candidate(candidate: PropositionMergeCandidate) -> dict[str, Any]:
    return {
        "schema_version": candidate.schema_version,
        "merge_id": candidate.merge_id,
        "has_structural_signature": bool(candidate.structural_signature.strip()),
        "source_proposition_count": len(candidate.source_proposition_ids),
        "source_origins": sorted(set(candidate.source_origins)),
        "proposition_role": candidate.proposition_role,
        "confidence_summary": candidate.confidence_summary,
        "duplicate_count": candidate.duplicate_count,
        "unsupported_gap_count": len(candidate.unsupported_gaps),
        "human_explanation_available": bool(candidate.human_explanation.strip()),
        "legibility_safe": _legibility_safe(candidate.legibility),
        "anti_gaming_safe": _anti_gaming_safe(candidate.anti_gaming),
    }



def _safe_proposition_list_value(proposition: object, field_name: str) -> list[str]:
    value = _safe_predicate_value(proposition, field_name)
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    if str(value).strip():
        return [str(value).strip()]
    return []


def _source_origins_from_proposition(proposition: object) -> list[str]:
    explicit = _safe_proposition_list_value(proposition, "source_origins")
    if not explicit:
        explicit = _safe_proposition_list_value(proposition, "source_origin") or _safe_proposition_list_value(proposition, "origin")
    origins = [origin for origin in explicit if origin in SAFE_PROPOSITION_MERGE_ORIGINS]
    if origins:
        return list(dict.fromkeys(origins))

    proposition_type = str(_safe_predicate_value(proposition, "proposition_type") or "")
    if proposition_type.startswith("binding_"):
        return ["binding_derived"]
    if _safe_proposition_list_value(proposition, "source_predicate_ids"):
        return ["predicate_derived"]
    return ["unknown"]


def proposition_structural_signature(proposition: object) -> str:
    """Return a redacted structural signature for proposition merge grouping."""
    role = normalize_proposition_role(str(_safe_predicate_value(proposition, "proposition_role") or "unknown"))
    subject = term_alignment_key(str(_safe_predicate_value(proposition, "subject_canonical_hint") or ""))
    relation = term_alignment_key(str(_safe_predicate_value(proposition, "relation_canonical_hint") or ""))
    obj = term_alignment_key(str(_safe_predicate_value(proposition, "object_canonical_hint") or ""))
    polarity = str(_safe_predicate_value(proposition, "polarity") or "positive").strip().lower() or "positive"
    quantifier = term_alignment_key(str(_safe_predicate_value(proposition, "quantifier") or ""))
    modality = term_alignment_key(str(_safe_predicate_value(proposition, "modality") or ""))
    return "|".join(
        [
            f"role={role}",
            f"subject={subject}",
            f"relation={relation}",
            f"object={obj}",
            f"polarity={polarity}",
            f"quantifier={quantifier}",
            f"modality={modality}",
        ]
    )


def _confidence_summary_for_merge_group(propositions: list[object]) -> str:
    confidences = [str(_safe_predicate_value(proposition, "confidence") or "low") for proposition in propositions]
    unsupported_gap_count = sum(len(_safe_proposition_list_value(proposition, "unsupported_gaps")) for proposition in propositions)
    if confidences and all(confidence == "high" for confidence in confidences):
        return "high"
    if unsupported_gap_count == 0 and any(confidence == "medium" for confidence in confidences):
        return "medium"
    return "low"


def create_proposition_merge_candidates(propositions: list[PropositionCandidate]) -> list[PropositionMergeCandidate]:
    """Create helper-only merge candidates for duplicate structural signatures."""
    groups: dict[str, list[object]] = {}
    for proposition in propositions:
        signature = proposition_structural_signature(proposition)
        if not signature.strip():
            continue
        groups.setdefault(signature, []).append(proposition)

    candidates: list[PropositionMergeCandidate] = []
    for index, (signature, group) in enumerate(groups.items(), start=1):
        if len(group) < 2:
            continue
        first = group[0]
        source_ids: list[str] = []
        source_origins: list[str] = []
        unsupported_gaps: list[str] = []
        for proposition in group:
            proposition_id = str(_safe_predicate_value(proposition, "proposition_id") or "").strip()
            if proposition_id:
                source_ids.append(proposition_id)
            source_origins.extend(_source_origins_from_proposition(proposition))
            unsupported_gaps.extend(_safe_proposition_list_value(proposition, "unsupported_gaps"))

        candidate = PropositionMergeCandidate(
            merge_id=f"merge:{index}",
            structural_signature=signature,
            source_proposition_ids=list(dict.fromkeys(source_ids)),
            source_origins=source_origins or ["unknown"],
            proposition_role=normalize_proposition_role(str(_safe_predicate_value(first, "proposition_role") or "unknown")),
            subject_canonical_hint=str(_safe_predicate_value(first, "subject_canonical_hint") or "").strip(),
            relation_canonical_hint=str(_safe_predicate_value(first, "relation_canonical_hint") or "").strip(),
            object_canonical_hint=str(_safe_predicate_value(first, "object_canonical_hint") or "").strip(),
            confidence_summary=_confidence_summary_for_merge_group(group),
            duplicate_count=len(group),
            unsupported_gaps=list(dict.fromkeys(unsupported_gaps)),
            human_explanation="Redacted helper-only proposition merge candidate created from duplicate structural signatures; not a truth claim, proof step, or answer selection.",
        )
        candidates.append(candidate)
    return candidates


def summarize_proposition_merge_diagnostics(merge_candidates: list[PropositionMergeCandidate]) -> dict[str, Any]:
    predicate_count = 0
    binding_count = 0
    unknown_count = 0
    low_count = 0
    medium_count = 0
    high_count = 0
    unsupported_gap_count = 0
    merged_source_count = 0
    anti_gaming_safe = True
    legibility_safe = True

    for candidate in merge_candidates:
        merged_source_count += len(candidate.source_proposition_ids)
        predicate_count += sum(1 for origin in candidate.source_origins if origin == "predicate_derived")
        binding_count += sum(1 for origin in candidate.source_origins if origin == "binding_derived")
        unknown_count += sum(1 for origin in candidate.source_origins if origin == "unknown")
        low_count += int(candidate.confidence_summary == "low")
        medium_count += int(candidate.confidence_summary == "medium")
        high_count += int(candidate.confidence_summary == "high")
        unsupported_gap_count += len(candidate.unsupported_gaps)
        anti_gaming_safe = anti_gaming_safe and _anti_gaming_safe(candidate.anti_gaming)
        legibility_safe = legibility_safe and _legibility_safe(candidate.legibility)

    return {
        "merge_candidate_count": len(merge_candidates),
        "merged_source_proposition_count": merged_source_count,
        "predicate_derived_source_count": predicate_count,
        "binding_derived_source_count": binding_count,
        "unknown_source_count": unknown_count,
        "low_confidence_count": low_count,
        "medium_confidence_count": medium_count,
        "high_confidence_count": high_count,
        "unsupported_gap_count": unsupported_gap_count,
        "anti_gaming_safe": anti_gaming_safe,
        "legibility_safe": legibility_safe,
    }



def create_empty_simple_inference_pattern_candidate(
    *,
    candidate_id: str = "",
    pattern_type: str = "unsupported/no-pattern",
    source_merge_ids: list[str] | None = None,
    source_proposition_ids: list[str] | None = None,
) -> SimpleInferencePatternCandidate:
    return SimpleInferencePatternCandidate(
        candidate_id=candidate_id,
        pattern_type=pattern_type,
        source_merge_ids=list(source_merge_ids or []),
        source_proposition_ids=list(source_proposition_ids or []),
    )


def simple_inference_pattern_candidate_to_dict(candidate: SimpleInferencePatternCandidate) -> dict[str, Any]:
    return asdict(candidate)


def simple_inference_pattern_candidate_from_dict(data: dict[str, Any]) -> SimpleInferencePatternCandidate:
    legibility_data = data.get("legibility") or {}
    anti_gaming_data = data.get("anti_gaming") or {}
    return SimpleInferencePatternCandidate(
        schema_version=data.get("schema_version", "1.0"),
        candidate_id=data.get("candidate_id", ""),
        pattern_type=data.get("pattern_type", "unsupported/no-pattern"),
        source_merge_ids=list(data.get("source_merge_ids") or []),
        source_proposition_ids=list(data.get("source_proposition_ids") or []),
        premise_role_count=int(data.get("premise_role_count", 0) or 0),
        choice_role_count=int(data.get("choice_role_count", 0) or 0),
        shared_subject=bool(data.get("shared_subject", False)),
        shared_object=bool(data.get("shared_object", False)),
        relation_overlap=bool(data.get("relation_overlap", False)),
        contradiction_signal=bool(data.get("contradiction_signal", False)),
        transitivity_signal=bool(data.get("transitivity_signal", False)),
        confidence=data.get("confidence", "low"),
        validity_status=data.get("validity_status", "unknown"),
        unsupported_gaps=list(data.get("unsupported_gaps") or []),
        human_explanation=data.get("human_explanation", ""),
        legibility=PropositionLegibilityRecord(**legibility_data),
        anti_gaming=PropositionAntiGamingRecord(**anti_gaming_data),
    )


def validate_simple_inference_pattern_candidate(candidate: SimpleInferencePatternCandidate) -> list[str]:
    messages: list[str] = []
    if not candidate.candidate_id:
        messages.append("missing candidate id")
    if candidate.pattern_type not in SAFE_SIMPLE_INFERENCE_PATTERN_TYPES:
        messages.append("invalid pattern type")
    if candidate.confidence not in SAFE_CONFIDENCE_VALUES:
        messages.append("invalid confidence")
    if candidate.validity_status not in SAFE_SIMPLE_INFERENCE_VALIDITY_STATUSES:
        messages.append("invalid validity status")
    if candidate.confidence == "high" and not (candidate.source_merge_ids or candidate.source_proposition_ids):
        messages.append("missing source ids for high-confidence simple inference candidate")
    if candidate.confidence == "high" and not candidate.human_explanation.strip():
        messages.append("missing human explanation for high-confidence simple inference candidate")
    messages.extend(_validate_shared_safety(candidate.legibility, candidate.anti_gaming))
    return messages


def summarize_simple_inference_pattern_candidate(candidate: SimpleInferencePatternCandidate) -> dict[str, Any]:
    return {
        "schema_version": candidate.schema_version,
        "candidate_id": candidate.candidate_id,
        "pattern_type": candidate.pattern_type,
        "source_merge_count": len(candidate.source_merge_ids),
        "source_proposition_count": len(candidate.source_proposition_ids),
        "premise_role_count": candidate.premise_role_count,
        "choice_role_count": candidate.choice_role_count,
        "shared_subject": candidate.shared_subject,
        "shared_object": candidate.shared_object,
        "relation_overlap": candidate.relation_overlap,
        "contradiction_signal": candidate.contradiction_signal,
        "transitivity_signal": candidate.transitivity_signal,
        "confidence": candidate.confidence,
        "validity_status": candidate.validity_status,
        "unsupported_gap_count": len(candidate.unsupported_gaps),
        "human_explanation_available": bool(candidate.human_explanation.strip()),
        "legibility_safe": _legibility_safe(candidate.legibility),
        "anti_gaming_safe": _anti_gaming_safe(candidate.anti_gaming),
    }



def create_empty_reasoning_context_binding_candidate(
    *,
    binding_id: str = "",
    source_premise_proposition_ids: list[str] | None = None,
    source_question_instruction_ids: list[str] | None = None,
    source_choice_proposition_ids: list[str] | None = None,
    question_target_type: str = "unknown",
    premise_context_type: str = "unknown",
    choice_target_role: str = "unknown",
    expected_reasoning_relation: str = "unknown",
    candidate_support_role: str = "unknown",
    conditional_form_slots: dict[str, Any] | None = None,
) -> ReasoningContextBindingCandidate:
    return ReasoningContextBindingCandidate(
        binding_id=binding_id,
        source_premise_proposition_ids=list(source_premise_proposition_ids or []),
        source_question_instruction_ids=list(source_question_instruction_ids or []),
        source_choice_proposition_ids=list(source_choice_proposition_ids or []),
        question_target_type=question_target_type,
        premise_context_type=premise_context_type,
        choice_target_role=choice_target_role,
        expected_reasoning_relation=expected_reasoning_relation,
        candidate_support_role=candidate_support_role,
        conditional_form_slots=dict(conditional_form_slots or {}),
    )


def reasoning_context_binding_candidate_to_dict(candidate: ReasoningContextBindingCandidate) -> dict[str, Any]:
    return asdict(candidate)


def reasoning_context_binding_candidate_from_dict(data: dict[str, Any]) -> ReasoningContextBindingCandidate:
    legibility_data = data.get("legibility") or {}
    anti_gaming_data = data.get("anti_gaming") or {}
    return ReasoningContextBindingCandidate(
        schema_version=data.get("schema_version", "1.0"),
        binding_id=data.get("binding_id", ""),
        source_premise_proposition_ids=list(data.get("source_premise_proposition_ids") or []),
        source_question_instruction_ids=list(data.get("source_question_instruction_ids") or []),
        source_choice_proposition_ids=list(data.get("source_choice_proposition_ids") or []),
        question_target_type=data.get("question_target_type", "unknown"),
        premise_context_type=data.get("premise_context_type", "unknown"),
        choice_target_role=data.get("choice_target_role", "unknown"),
        expected_reasoning_relation=data.get("expected_reasoning_relation", "unknown"),
        candidate_support_role=data.get("candidate_support_role", "unknown"),
        conditional_form_slots=dict(data.get("conditional_form_slots") or {}),
        confidence=data.get("confidence", "low"),
        unsupported_gaps=list(data.get("unsupported_gaps") or []),
        human_explanation=data.get("human_explanation", ""),
        legibility=PropositionLegibilityRecord(**legibility_data),
        anti_gaming=PropositionAntiGamingRecord(**anti_gaming_data),
    )


def validate_reasoning_context_binding_candidate(candidate: ReasoningContextBindingCandidate) -> list[str]:
    messages: list[str] = []
    if not candidate.binding_id:
        messages.append("missing binding id")
    if candidate.question_target_type not in SAFE_REASONING_CONTEXT_QUESTION_TARGET_TYPES:
        messages.append("invalid question target type")
    if candidate.premise_context_type not in SAFE_REASONING_CONTEXT_PREMISE_CONTEXT_TYPES:
        messages.append("invalid premise context type")
    if candidate.choice_target_role not in SAFE_REASONING_CONTEXT_CHOICE_TARGET_ROLES:
        messages.append("invalid choice target role")
    if candidate.expected_reasoning_relation not in SAFE_REASONING_CONTEXT_EXPECTED_RELATIONS:
        messages.append("invalid expected reasoning relation")
    if candidate.candidate_support_role not in SAFE_REASONING_CONTEXT_CANDIDATE_SUPPORT_ROLES:
        messages.append("invalid candidate support role")
    if candidate.confidence not in SAFE_CONFIDENCE_VALUES:
        messages.append("invalid confidence")
    if candidate.confidence == "high" and not candidate.source_premise_proposition_ids:
        messages.append("missing premise source ids for high-confidence context binding")
    if candidate.confidence == "high" and not candidate.source_question_instruction_ids:
        messages.append("missing question instruction source ids for high-confidence context binding")
    if candidate.confidence == "high" and not candidate.source_choice_proposition_ids:
        messages.append("missing choice source ids for high-confidence context binding")
    if candidate.confidence == "high" and not candidate.human_explanation.strip():
        messages.append("missing human explanation for high-confidence context binding")
    messages.extend(_validate_shared_safety(candidate.legibility, candidate.anti_gaming))
    return messages


def summarize_reasoning_context_binding_candidate(candidate: ReasoningContextBindingCandidate) -> dict[str, Any]:
    return {
        "schema_version": candidate.schema_version,
        "binding_id": candidate.binding_id,
        "premise_source_count": len(candidate.source_premise_proposition_ids),
        "instruction_source_count": len(candidate.source_question_instruction_ids),
        "candidate_source_count": len(candidate.source_choice_proposition_ids),
        "target_type": candidate.question_target_type,
        "context_type": candidate.premise_context_type,
        "target_role": candidate.choice_target_role,
        "expected_relation": candidate.expected_reasoning_relation,
        "support_role": candidate.candidate_support_role,
        "conditional_slot_evidence_available": bool(candidate.conditional_form_slots),
        "confidence": candidate.confidence,
        "unsupported_gap_count": len(candidate.unsupported_gaps),
        "human_explanation_available": bool(candidate.human_explanation.strip()),
        "legibility_safe": _legibility_safe(candidate.legibility),
        "anti_gaming_safe": _anti_gaming_safe(candidate.anti_gaming),
    }


def create_empty_proof_step_candidate(
    *,
    candidate_id: str = "",
    source_context_binding_ids: list[str] | None = None,
    source_premise_proposition_ids: list[str] | None = None,
    source_choice_proposition_ids: list[str] | None = None,
    candidate_type: str = "unsupported_step_candidate",
    expected_reasoning_relation: str = "unknown",
    inference_pattern_hint: str = "",
    support_status: str = "unknown",
    conditional_form_mapping: dict[str, Any] | None = None,
    conditional_form_mapping_origin: str = "insufficient_slot_evidence",
) -> ProofStepCandidate:
    return ProofStepCandidate(
        candidate_id=candidate_id,
        source_context_binding_ids=list(source_context_binding_ids or []),
        source_premise_proposition_ids=list(source_premise_proposition_ids or []),
        source_choice_proposition_ids=list(source_choice_proposition_ids or []),
        candidate_type=candidate_type,
        expected_reasoning_relation=expected_reasoning_relation,
        inference_pattern_hint=inference_pattern_hint,
        support_status=support_status,
        conditional_form_mapping=dict(conditional_form_mapping or {}),
        conditional_form_mapping_origin=conditional_form_mapping_origin,
    )


def proof_step_candidate_to_dict(candidate: ProofStepCandidate) -> dict[str, Any]:
    return asdict(candidate)


def proof_step_candidate_from_dict(data: dict[str, Any]) -> ProofStepCandidate:
    legibility_data = data.get("legibility") or {}
    anti_gaming_data = data.get("anti_gaming") or {}
    return ProofStepCandidate(
        schema_version=data.get("schema_version", "1.0"),
        candidate_id=data.get("candidate_id", ""),
        source_context_binding_ids=list(data.get("source_context_binding_ids") or []),
        source_premise_proposition_ids=list(data.get("source_premise_proposition_ids") or []),
        source_choice_proposition_ids=list(data.get("source_choice_proposition_ids") or []),
        candidate_type=data.get("candidate_type", "unsupported_step_candidate"),
        expected_reasoning_relation=data.get("expected_reasoning_relation", "unknown"),
        inference_pattern_hint=data.get("inference_pattern_hint", ""),
        support_status=data.get("support_status", "unknown"),
        conditional_form_mapping=dict(data.get("conditional_form_mapping") or {}),
        conditional_form_mapping_origin=data.get("conditional_form_mapping_origin", "insufficient_slot_evidence"),
        confidence=data.get("confidence", "low"),
        unsupported_gaps=list(data.get("unsupported_gaps") or []),
        human_explanation=data.get("human_explanation", ""),
        legibility=PropositionLegibilityRecord(**legibility_data),
        anti_gaming=PropositionAntiGamingRecord(**anti_gaming_data),
    )


def validate_proof_step_candidate(candidate: ProofStepCandidate) -> list[str]:
    messages: list[str] = []
    if not candidate.candidate_id:
        messages.append("missing candidate id")
    if candidate.candidate_type not in SAFE_PROOF_STEP_CANDIDATE_TYPES:
        messages.append("invalid candidate type")
    if candidate.support_status not in SAFE_PROOF_STEP_CANDIDATE_SUPPORT_STATUSES:
        messages.append("invalid support status")
    if candidate.confidence not in SAFE_CONFIDENCE_VALUES:
        messages.append("invalid confidence")
    if candidate.confidence == "high" and not candidate.source_context_binding_ids:
        messages.append("missing context binding ids for high-confidence proof step candidate")
    if candidate.confidence == "high" and not (candidate.source_premise_proposition_ids and candidate.source_choice_proposition_ids):
        messages.append("missing premise/choice proposition ids for high-confidence proof step candidate")
    if candidate.confidence == "high" and not candidate.human_explanation.strip():
        messages.append("missing human explanation for high-confidence proof step candidate")
    messages.extend(_validate_shared_safety(candidate.legibility, candidate.anti_gaming))
    return messages


def summarize_proof_step_candidate(candidate: ProofStepCandidate) -> dict[str, Any]:
    return {
        "schema_version": candidate.schema_version,
        "candidate_id": candidate.candidate_id,
        "context_binding_source_count": len(candidate.source_context_binding_ids),
        "premise_proposition_source_count": len(candidate.source_premise_proposition_ids),
        "target_proposition_source_count": len(candidate.source_choice_proposition_ids),
        "candidate_type": candidate.candidate_type,
        "expected_reasoning_relation": candidate.expected_reasoning_relation,
        "inference_pattern_hint_available": bool(candidate.inference_pattern_hint.strip()),
        "support_status": candidate.support_status,
        "conditional_form_mapping_origin": candidate.conditional_form_mapping_origin,
        "conditional_form_mapping_available": bool(candidate.conditional_form_mapping),
        "confidence": candidate.confidence,
        "unsupported_gap_count": len(candidate.unsupported_gaps),
        "human_explanation_available": bool(candidate.human_explanation.strip()),
        "legibility_safe": _legibility_safe(candidate.legibility),
        "anti_gaming_safe": _anti_gaming_safe(candidate.anti_gaming),
    }



def _safe_record_value(record: object, field_name: str, default: Any = "") -> Any:
    if isinstance(record, dict):
        return record.get(field_name, default)
    return getattr(record, field_name, default)


def _safe_record_list_value(record: object, field_name: str) -> list[str]:
    value = _safe_record_value(record, field_name, [])
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    if str(value).strip():
        return [str(value).strip()]
    return []


def _record_markers(*records: object) -> set[str]:
    parts: list[str] = []
    for record in records:
        if record is None:
            continue
        for field_name in [
            "normalized_text", "logical_form", "human_translation", "human_explanation",
            "question_instruction_template", "expected_structural_pattern",
            "expected_context_binding_type", "expected_teaching_focus", "proposition_type",
            "proposition_role", "subject", "relation", "object", "subject_canonical_hint",
            "relation_canonical_hint", "object_canonical_hint", "pattern_type",
            "choice_target_role", "expected_reasoning_relation",
        ]:
            value = _safe_record_value(record, field_name, "")
            if value:
                parts.append(str(value))
        for field_name in [
            "source_statement_roles", "unsupported_gaps", "source_proposition_ids",
            "question_instruction_markers", "question_markers", "target_markers",
        ]:
            parts.extend(_safe_record_list_value(record, field_name))
    surface = " ".join(parts).lower()
    cleaned = "".join(char if char.isalnum() or char == "_" else " " for char in surface)
    tokens = {token for token in cleaned.split() if token}
    compact_markers = {part.strip().lower().replace(" ", "_") for part in parts if str(part).strip()}
    return tokens | compact_markers


def _has_any_marker(markers: set[str], *groups: set[str]) -> bool:
    return any(markers & group for group in groups)


def classify_question_target_type(question_instruction: object | None = None, *, markers: list[str] | None = None) -> str:
    marker_records = [question_instruction] if question_instruction is not None else []
    selected = _record_markers(*marker_records)
    for marker in markers or []:
        marker_text = str(marker).strip().lower()
        if marker_text:
            selected.add(marker_text.replace(" ", "_"))
            selected.update(_record_markers({"normalized_text": marker_text}))
    phrase_markers = " ".join(sorted(selected))
    if _has_any_marker(selected, {"counterexample", "counterexamples", "counter_example", "refutes"}) or ({"shows", "false"} <= selected):
        return "counterexample"
    if _has_any_marker(selected, {"does_not_follow", "not_follow", "not_follows", "not_entailed", "cannot_be_concluded"}) or ({"does", "not", "follow"} <= selected):
        return "does_not_follow"
    if _has_any_marker(selected, {"invalid_argument", "invalid_inference", "invalid", "invalidity", "fallacy", "fallacy_shaped"}):
        return "invalid_argument"
    if _has_any_marker(selected, {"valid_argument", "valid_inference", "validity"}) or ({"valid", "argument"} <= selected) or ({"valid", "inference"} <= selected):
        return "valid_argument"
    if _has_any_marker(selected, {"must_be_false", "must_false", "cannot_be_true"}) or ({"must", "be", "false"} <= selected):
        return "must_be_false"
    if _has_any_marker(selected, {"must_be_true", "must_true", "necessarily_true", "has_to_be_true"}) or ({"must", "be", "true"} <= selected):
        return "must_be_true"
    if _has_any_marker(selected, {"follows", "follow", "conclusion", "candidate_conclusion", "can_be_concluded", "valid_conclusion", "entailed"}):
        return "follows"
    if _has_any_marker(
        selected,
        {"complete", "completion", "completes", "supplies", "bind", "binding", "fragment", "template", "fills_the_blank", "which_object", "which_property", "which_statement_completes"},
        {"noun_phrase_choice_binding", "noun", "phrase"},
    ):
        return "completion"
    if _has_any_marker(selected, {"modus_ponens", "modus_tollens", "universal_syllogism", "quantifier_reasoning", "disjunction_reasoning", "negation_reasoning"}):
        return "follows"
    if _has_any_marker(selected, {"contradiction"}):
        return "must_be_false"
    if "necessary sufficient confusion" in phrase_markers or _has_any_marker(selected, {"necessary_sufficient_confusion"}):
        return "invalid_argument"
    return "unknown"


def classify_premise_context_type(premise_propositions: list[object] | object | None = None) -> str:
    records = premise_propositions if isinstance(premise_propositions, list) else [premise_propositions]
    markers = _record_markers(*[record for record in records if record is not None])
    detected: set[str] = set()
    if _has_any_marker(markers, {"if", "then", "conditional", "condition", "implies", "imply", "sufficient", "necessary", "modus_ponens", "modus_tollens"}):
        detected.add("conditional_rule")
    if _has_any_marker(markers, {"all", "every", "some", "no", "quantifier", "quantified", "universal", "existential", "group", "class"}):
        detected.add("quantified_rule")
    if _has_any_marker(markers, {"not", "no", "excludes", "exclusion", "lacks", "without", "contradiction", "negation"}):
        detected.add("exclusion_rule")
    if _has_any_marker(markers, {"definition", "defines", "defined", "means", "identical", "necessary_sufficient"}):
        detected.add("definition_like")
    if _has_any_marker(markers, {"background", "context"}):
        detected.add("background_context")
    if len(detected) > 1:
        return "mixed_context"
    if detected:
        return next(iter(detected))
    if records and any(record is not None for record in records):
        return "given_fact"
    return "unknown"

def classify_choice_target_role(choice_proposition: object | None = None, question_instruction: object | None = None) -> str:
    markers = _record_markers(choice_proposition, question_instruction)
    if markers & {"counterexample", "counterexamples", "lacks", "outside"}:
        return "candidate_counterexample"
    if markers & {"invalid", "fallacy", "unsupported"}:
        return "candidate_invalid_statement"
    if markers & {"valid", "validity"}:
        return "candidate_valid_statement"
    if markers & {"irrelevant", "unrelated"}:
        return "candidate_irrelevant"
    if markers & {"restate", "restatement", "duplicate"}:
        return "candidate_restatement"
    prop_type = str(_safe_record_value(choice_proposition, "proposition_type", "") or "")
    relation = str(_safe_record_value(choice_proposition, "relation", "") or _safe_record_value(choice_proposition, "relation_canonical_hint", "") or "")
    if prop_type == "binding_projection_weak_or_unsupported" or not relation.strip():
        if markers & {"fragment", "noun", "phrase", "binding", "bind"}:
            return "fragment_needs_binding"
    role = str(_safe_record_value(choice_proposition, "proposition_role", "") or "")
    if role == "choice_claim" or prop_type:
        return "candidate_conclusion"
    return "unknown"


def _context_expected_relation(question_target_type: str, premise_context_type: str, choice_target_role: str) -> str:
    if choice_target_role == "candidate_counterexample" or question_target_type == "counterexample":
        return "provide_counterexample"
    if question_target_type in {"valid_argument", "invalid_argument"} or choice_target_role in {"candidate_valid_statement", "candidate_invalid_statement"}:
        return "test_validity"
    if question_target_type == "completion" or choice_target_role == "fragment_needs_binding":
        return "complete_template"
    if premise_context_type == "conditional_rule":
        return "apply_condition"
    if premise_context_type == "quantified_rule":
        return "instantiate_rule"
    if question_target_type == "must_be_false":
        return "contradict"
    if question_target_type in {"must_be_true", "follows"} or choice_target_role == "candidate_conclusion":
        return "support"
    return "unknown"


def _context_support_role(expected_relation: str, choice_target_role: str) -> str:
    if expected_relation in {"support", "apply_condition", "instantiate_rule", "complete_template"}:
        return "supports_target"
    if expected_relation == "contradict":
        return "contradicts_target"
    if expected_relation in {"test_validity", "provide_counterexample"}:
        return "tests_target"
    if choice_target_role == "candidate_restatement":
        return "restates_target"
    if choice_target_role == "candidate_irrelevant":
        return "irrelevant_to_target"
    return "unknown"


def _derive_conditional_form_slots_from_structural_markers(markers: set[str]) -> dict[str, Any]:
    pattern_aliases = {
        "modus_ponens": ("P", "Q"),
        "modus_tollens": ("¬Q", "¬P"),
        "affirming_consequent": ("Q", "P"),
        "necessary_sufficient_confusion": ("Q", "P"),
        "denying_antecedent": ("¬P", "¬Q"),
    }
    matched = [pattern for pattern in pattern_aliases if pattern in markers]
    if len(matched) != 1:
        return {}
    asserted, conclusion = pattern_aliases[matched[0]]
    return {
        "conditional": "P -> Q",
        "asserted_literal": asserted,
        "conclusion_literal": conclusion,
        "conditional_count": 1,
        "conditional_direction": "P_to_Q",
        "negation_scope_status": "clear",
        "slot_binding_status": "complete",
        "conclusion_binding_count": 1,
        "requires_semantic_bridge": False,
        "source_structural_pattern": matched[0],
    }


def create_reasoning_context_binding_candidate_from_structures(
    *,
    binding_id: str = "",
    premise_propositions: list[object] | None = None,
    question_instruction_records: list[object] | None = None,
    choice_propositions: list[object] | None = None,
    simple_inference_candidates: list[object] | None = None,
) -> ReasoningContextBindingCandidate:
    premises = list(premise_propositions or [])
    questions = list(question_instruction_records or [])
    choices = list(choice_propositions or [])
    simple_candidates = list(simple_inference_candidates or [])

    premise_ids = []
    for proposition in premises:
        premise_ids.extend(_safe_record_list_value(proposition, "source_proposition_ids"))
        value = str(_safe_record_value(proposition, "proposition_id", "") or "").strip()
        if value:
            premise_ids.append(value)
            continue
        statement_ref = str(
            _safe_record_value(proposition, "statement_id", "")
            or _safe_record_value(proposition, "source_statement_id", "")
            or ""
        ).strip()
        if statement_ref:
            premise_ids.append(f"premise_statement:{statement_ref}")
    question_ids = []
    for question in questions:
        value = str(_safe_record_value(question, "statement_id", "") or _safe_record_value(question, "id", "") or "").strip()
        if value:
            question_ids.append(value)
    choice_ids = []
    for proposition in choices:
        choice_ids.extend(_safe_record_list_value(proposition, "source_proposition_ids"))
        value = str(_safe_record_value(proposition, "proposition_id", "") or "").strip()
        if value:
            choice_ids.append(value)

    question_marker_sources: list[str] = []
    for record in [*questions, *premises, *choices, *simple_candidates]:
        for field_name in [
            "question_instruction_markers", "question_markers", "target_markers",
            "expected_context_binding_type", "expected_structural_pattern",
            "question_instruction_template", "relation", "relation_canonical_hint",
            "pattern_type", "choice_target_role", "expected_reasoning_relation",
        ]:
            value = _safe_record_value(record, field_name, "")
            if value:
                question_marker_sources.append(str(value))
        for field_name in ["question_instruction_markers", "question_markers", "target_markers"]:
            question_marker_sources.extend(_safe_record_list_value(record, field_name))
    question_target_type = classify_question_target_type(questions[0] if questions else None, markers=question_marker_sources)
    premise_context_type = classify_premise_context_type(premises)
    choice_target_role = classify_choice_target_role(choices[0] if choices else None, questions[0] if questions else None)
    structural_markers = _record_markers(*premises, *questions, *choices, *simple_candidates)
    conditional_form_slots = _derive_conditional_form_slots_from_structural_markers(structural_markers)
    expected_relation = _context_expected_relation(question_target_type, premise_context_type, choice_target_role)
    if conditional_form_slots and expected_relation in {"support", "unknown"}:
        expected_relation = "apply_condition"
    support_role = _context_support_role(expected_relation, choice_target_role)
    unsupported_gaps: list[str] = []
    if not premise_ids:
        unsupported_gaps.append("missing_premise_proposition_refs")
    if not question_ids:
        unsupported_gaps.append("missing_question_instruction_refs")
    if not choice_ids:
        unsupported_gaps.append("missing_choice_proposition_refs")
    if question_target_type == "unknown":
        unsupported_gaps.append("question_target_type_unknown")
    if premise_context_type == "unknown":
        unsupported_gaps.append("premise_context_type_unknown")
    if choice_target_role == "unknown":
        unsupported_gaps.append("choice_target_role_unknown")
    if expected_relation == "unknown":
        unsupported_gaps.append("expected_reasoning_relation_unknown")
    for record in [*premises, *choices, *simple_candidates]:
        unsupported_gaps.extend(_safe_record_list_value(record, "unsupported_gaps"))

    confidence = "medium" if premise_ids and question_ids and choice_ids and expected_relation != "unknown" else "low"
    if any(str(_safe_record_value(candidate, "confidence", "") or "") == "high" for candidate in simple_candidates):
        confidence = "medium"

    return ReasoningContextBindingCandidate(
        binding_id=binding_id or "reasoning_context_binding:synthetic:unknown",
        source_premise_proposition_ids=list(dict.fromkeys(premise_ids)),
        source_question_instruction_ids=list(dict.fromkeys(question_ids)),
        source_choice_proposition_ids=list(dict.fromkeys(choice_ids)),
        question_target_type=question_target_type,
        premise_context_type=premise_context_type,
        choice_target_role=choice_target_role,
        expected_reasoning_relation=expected_relation,
        candidate_support_role=support_role,
        conditional_form_slots=conditional_form_slots,
        confidence=confidence,
        unsupported_gaps=list(dict.fromkeys(unsupported_gaps)),
        human_explanation=(
            "Helper-only reasoning context binding from redacted structural records; "
            "does not select answers, assert correctness, generate proof steps, or use answer keys."
        ),
        legibility=PropositionLegibilityRecord(),
        anti_gaming=PropositionAntiGamingRecord(),
    )


def summarize_reasoning_context_binding_diagnostics(candidates: list[ReasoningContextBindingCandidate]) -> dict[str, Any]:
    question_counts = {value: 0 for value in SAFE_REASONING_CONTEXT_QUESTION_TARGET_TYPES}
    premise_counts = {value: 0 for value in SAFE_REASONING_CONTEXT_PREMISE_CONTEXT_TYPES}
    choice_counts = {value: 0 for value in SAFE_REASONING_CONTEXT_CHOICE_TARGET_ROLES}
    relation_counts = {value: 0 for value in SAFE_REASONING_CONTEXT_EXPECTED_RELATIONS}
    confidence_counts = {"low": 0, "medium": 0, "high": 0}
    unsupported_gap_count = 0
    anti_gaming_safe = True
    legibility_safe = True
    for candidate in candidates:
        question_counts[candidate.question_target_type] = question_counts.get(candidate.question_target_type, 0) + 1
        premise_counts[candidate.premise_context_type] = premise_counts.get(candidate.premise_context_type, 0) + 1
        choice_counts[candidate.choice_target_role] = choice_counts.get(candidate.choice_target_role, 0) + 1
        relation_counts[candidate.expected_reasoning_relation] = relation_counts.get(candidate.expected_reasoning_relation, 0) + 1
        if candidate.confidence in confidence_counts:
            confidence_counts[candidate.confidence] += 1
        unsupported_gap_count += len(candidate.unsupported_gaps)
        findings = validate_reasoning_context_binding_candidate(candidate)
        anti_gaming_safe = anti_gaming_safe and not any(
            finding in findings
            for finding in [
                "answer-key use is forbidden",
                "item-id authority is forbidden",
                "answer-position bias is forbidden",
                "official-score claim is forbidden",
                "benchmark-specific tuning is forbidden",
                "answer selection must remain disabled",
            ]
        )
        legibility_safe = legibility_safe and not any(
            finding in findings
            for finding in [
                "raw benchmark storage by default is forbidden",
                "private symbolic authority is forbidden",
                "unsupported assumptions must remain visible",
            ]
        )
    return {
        "context_binding_count": len(candidates),
        "question_target_type_counts": dict(sorted(question_counts.items())),
        "premise_context_type_counts": dict(sorted(premise_counts.items())),
        "choice_target_role_counts": dict(sorted(choice_counts.items())),
        "expected_reasoning_relation_counts": dict(sorted(relation_counts.items())),
        "low_confidence_count": confidence_counts["low"],
        "medium_confidence_count": confidence_counts["medium"],
        "high_confidence_count": confidence_counts["high"],
        "unsupported_gap_count": unsupported_gap_count,
        "anti_gaming_safe": anti_gaming_safe,
        "legibility_safe": legibility_safe,
    }

def _normalize_conditional_literal(value: object) -> str:
    text = str(value or "").strip().lower()
    text = text.replace(" ", "")
    text = text.replace("¬", "not_").replace("~", "not_").replace("!", "not_")
    text = text.replace("not", "not_") if text in {"notp", "notq"} else text
    aliases = {
        "p": "P",
        "antecedent": "P",
        "asserted_antecedent": "P",
        "q": "Q",
        "consequent": "Q",
        "asserted_consequent": "Q",
        "not_p": "¬P",
        "not__p": "¬P",
        "negated_antecedent": "¬P",
        "denied_antecedent": "¬P",
        "not_q": "¬Q",
        "not__q": "¬Q",
        "negated_consequent": "¬Q",
        "denied_consequent": "¬Q",
    }
    return aliases.get(text, "unknown")


def _normalize_conditional_direction(value: object) -> str:
    text = str(value or "").strip().lower().replace(" ", "_")
    if text in {"p_to_q", "p→q", "p->q", "if_p_then_q", "clear", "locked", "direction_locked"}:
        return "P_to_Q"
    if text in {"unknown", "unclear", "ambiguous", "", "multi", "multiple"}:
        return "unknown"
    return "unknown"


def _safe_bool_value(record: object, field_name: str, default: bool = False) -> bool:
    value = _safe_record_value(record, field_name, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "required", "semantic_bridge_required"}
    return bool(value)


def _safe_int_value(record: object, field_name: str, default: int = 0) -> int:
    value = _safe_record_value(record, field_name, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _conditional_slot_value(context_binding: object | None, field_name: str, default: Any = "") -> Any:
    if context_binding is None:
        return default
    slot_payload = _safe_record_value(context_binding, "conditional_form_slots", None) or _safe_record_value(context_binding, "conditional_mapping", None)
    if isinstance(slot_payload, dict) and field_name in slot_payload:
        return slot_payload.get(field_name, default)
    return _safe_record_value(context_binding, field_name, default)


def classify_conditional_form_mapping(
    *,
    conditional: object = "P -> Q",
    asserted_literal: object = "",
    conclusion_literal: object = "",
    conditional_count: int = 1,
    conditional_direction: object = "P_to_Q",
    negation_scope_status: object = "clear",
    slot_binding_status: object = "complete",
    conclusion_binding_count: int = 1,
    requires_semantic_bridge: bool = False,
    fallacy_shaped: bool | None = None,
    context_binding: object | None = None,
) -> ConditionalFormMappingResult:
    """Classify a completed conditional slot pattern without truth or answer selection.

    The helper accepts only structural slots.  Any caller-provided fallacy flag is ignored;
    fallacy-shaped status is derived only when the slots exactly match a known invalid form.
    """
    if context_binding is not None:
        conditional = _conditional_slot_value(context_binding, "conditional", conditional)
        asserted_literal = _conditional_slot_value(context_binding, "asserted_literal", asserted_literal)
        conclusion_literal = _conditional_slot_value(context_binding, "conclusion_literal", conclusion_literal)
        conditional_count = _safe_int_value(context_binding, "conditional_count", conditional_count)
        conditional_direction = _conditional_slot_value(context_binding, "conditional_direction", conditional_direction)
        negation_scope_status = _conditional_slot_value(context_binding, "negation_scope_status", negation_scope_status)
        slot_binding_status = _conditional_slot_value(context_binding, "slot_binding_status", slot_binding_status)
        conclusion_binding_count = _safe_int_value(context_binding, "conclusion_binding_count", conclusion_binding_count)
        requires_semantic_bridge = _safe_bool_value(context_binding, "requires_semantic_bridge", requires_semantic_bridge)

    gaps: list[str] = []
    conditional_text = str(conditional or "").strip().lower().replace(" ", "")
    direction = _normalize_conditional_direction(conditional_direction)
    asserted = _normalize_conditional_literal(asserted_literal)
    conclusion = _normalize_conditional_literal(conclusion_literal)
    slot_status = str(slot_binding_status or "unknown").strip().lower() or "unknown"
    negation_scope = str(negation_scope_status or "unknown").strip().lower() or "unknown"

    if conditional_count != 1:
        gaps.append("conditional_count_not_one")
    if not any(marker in conditional_text for marker in ["p->q", "p→q", "p=>q", "ifpthenq"]):
        gaps.append("conditional_pattern_not_locked")
    if direction != "P_to_Q":
        gaps.append("conditional_direction_unclear")
    if asserted == "unknown":
        gaps.append("asserted_literal_unbound")
    if conclusion == "unknown":
        gaps.append("conclusion_literal_unbound")
    if conclusion_binding_count != 1:
        gaps.append("conclusion_not_single_bound")
    if negation_scope not in {"clear", "locked", "whole_literal", "unambiguous"}:
        gaps.append("negation_scope_unclear")
    if slot_status not in {"complete", "exact", "locked"}:
        gaps.append("slot_binding_incomplete")
    if requires_semantic_bridge:
        gaps.append("semantic_bridge_required")

    if gaps:
        return ConditionalFormMappingResult(
            form_label="ambiguous_form",
            support_assessment="insufficient_structure",
            conditional_direction=direction,
            asserted_literal=asserted,
            conclusion_literal=conclusion,
            slot_binding_status=slot_status,
            fallacy_shaped=False,
            supported_form=False,
            unsupported_gaps=list(dict.fromkeys(gaps)),
        )

    mapping = {
        ("P", "Q"): ("modus_ponens", "supported_form"),
        ("¬Q", "¬P"): ("modus_tollens", "supported_form"),
        ("Q", "P"): ("affirming_consequent", "fallacy_shaped"),
        ("¬P", "¬Q"): ("denying_antecedent", "fallacy_shaped"),
    }
    form_label, support_assessment = mapping.get((asserted, conclusion), ("unsupported_form", "insufficient_structure"))
    return ConditionalFormMappingResult(
        form_label=form_label,
        support_assessment=support_assessment,
        conditional_direction=direction,
        asserted_literal=asserted,
        conclusion_literal=conclusion,
        slot_binding_status=slot_status,
        fallacy_shaped=support_assessment == "fallacy_shaped",
        supported_form=support_assessment == "supported_form",
        unsupported_gaps=[] if support_assessment != "insufficient_structure" else ["unrecognized_conditional_form_mapping"],
    )


def summarize_conditional_form_mapping_diagnostics(results: list[ConditionalFormMappingResult]) -> dict[str, Any]:
    form_counts = {value: 0 for value in SAFE_CONDITIONAL_FORM_LABELS}
    support_counts = {value: 0 for value in SAFE_CONDITIONAL_FORM_SUPPORT_ASSESSMENTS}
    unsupported_gap_count = 0
    for result in results:
        form_counts[result.form_label] = form_counts.get(result.form_label, 0) + 1
        support_counts[result.support_assessment] = support_counts.get(result.support_assessment, 0) + 1
        unsupported_gap_count += len(result.unsupported_gaps)
    return {
        "conditional_form_mapping_count": len(results),
        "conditional_form_mapping_counts": dict(sorted(form_counts.items())),
        "conditional_support_assessment_counts": dict(sorted(support_counts.items())),
        "fallacy_shaped_count": sum(1 for result in results if result.fallacy_shaped),
        "supported_form_count": sum(1 for result in results if result.supported_form),
        "unsupported_or_insufficient_structure_count": sum(1 for result in results if result.support_assessment == "insufficient_structure"),
        "unsupported_gap_count": unsupported_gap_count,
        "answer_selection_enabled": False,
        "truth_claim_made": False,
        "official_score_claimed": False,
        "anti_gaming_safe": True,
        "legibility_safe": True,
    }


def classify_proof_step_candidate_type(context_binding: object) -> str:
    relation = str(_safe_record_value(context_binding, "expected_reasoning_relation", "unknown") or "unknown").strip()
    if relation == "support":
        return "support_step_candidate"
    if relation == "contradict":
        return "contradiction_step_candidate"
    if relation == "provide_counterexample":
        return "counterexample_step_candidate"
    if relation in {"apply_condition", "instantiate_rule"}:
        return "rule_application_candidate"
    if relation == "test_validity":
        return "invalidity_test_candidate"
    if relation == "complete_template":
        return "template_completion_candidate"
    return "unsupported_step_candidate"


def _proof_step_candidate_support_status(context_binding: object, candidate_type: str) -> str:
    premise_ids = _safe_record_list_value(context_binding, "source_premise_proposition_ids")
    choice_ids = _safe_record_list_value(context_binding, "source_choice_proposition_ids")
    context_id = str(_safe_record_value(context_binding, "binding_id", "") or "").strip()
    relation = str(_safe_record_value(context_binding, "expected_reasoning_relation", "unknown") or "unknown").strip()
    support_role = str(_safe_record_value(context_binding, "candidate_support_role", "unknown") or "unknown").strip()
    choice_role = str(_safe_record_value(context_binding, "choice_target_role", "unknown") or "unknown").strip()
    if not (context_id and premise_ids and choice_ids):
        return "insufficient_support"
    if relation == "unknown" or candidate_type == "unsupported_step_candidate":
        return "unsupported"
    if support_role == "unknown" or choice_role == "unknown":
        return "ambiguous"
    return "candidate_only"


def _has_conditional_form_slots(context_binding: object) -> bool:
    slot_payload = _safe_record_value(context_binding, "conditional_form_slots", None) or _safe_record_value(context_binding, "conditional_mapping", None)
    if isinstance(slot_payload, dict) and slot_payload:
        return True
    return any(
        _safe_record_value(context_binding, field_name, None) is not None
        for field_name in [
            "conditional",
            "asserted_literal",
            "conclusion_literal",
            "conditional_count",
            "conditional_direction",
            "negation_scope_status",
            "slot_binding_status",
            "conclusion_binding_count",
            "requires_semantic_bridge",
        ]
    )


def _conditional_form_mapping_to_provenance(
    result: ConditionalFormMappingResult,
    *,
    source_context_binding_ids: list[str],
    source_candidate_id: str = "",
    source_premise_proposition_ids: list[str] | None = None,
    source_choice_proposition_ids: list[str] | None = None,
    expected_reasoning_relation: str = "unknown",
    inference_pattern_hint: str = "",
    origin: str = "pipeline_derived_mapping",
) -> dict[str, Any]:
    return {
        "schema_version": result.schema_version,
        "origin": origin,
        "form_label": result.form_label,
        "support_assessment": result.support_assessment,
        "conditional_direction": result.conditional_direction,
        "asserted_literal": result.asserted_literal,
        "conclusion_literal": result.conclusion_literal,
        "slot_binding_status": result.slot_binding_status,
        "fallacy_shaped": result.fallacy_shaped,
        "supported_form": result.supported_form,
        "unsupported_gaps": list(result.unsupported_gaps),
        "source_context_binding_ids": list(source_context_binding_ids),
        "source_candidate_id": source_candidate_id,
        "source_premise_proposition_ids": list(source_premise_proposition_ids or []),
        "source_choice_proposition_ids": list(source_choice_proposition_ids or []),
        "expected_reasoning_relation": expected_reasoning_relation,
        "inference_pattern_hint": inference_pattern_hint or result.form_label,
    }


def derive_conditional_form_mapping_from_context_binding(context_binding: object) -> dict[str, Any]:
    binding_id = str(_safe_record_value(context_binding, "binding_id", "") or "").strip()
    premise_ids = _safe_record_list_value(context_binding, "source_premise_proposition_ids")
    choice_ids = _safe_record_list_value(context_binding, "source_choice_proposition_ids")
    expected_relation = str(_safe_record_value(context_binding, "expected_reasoning_relation", "unknown") or "unknown").strip() or "unknown"
    if not _has_conditional_form_slots(context_binding):
        return {
            "origin": "insufficient_slot_evidence",
            "form_label": "ambiguous_form",
            "support_assessment": "insufficient_structure",
            "slot_binding_status": "missing",
            "fallacy_shaped": False,
            "supported_form": False,
            "unsupported_gaps": ["conditional_slot_evidence_unavailable"],
            "source_context_binding_ids": [binding_id] if binding_id else [],
            "source_candidate_id": "",
            "source_premise_proposition_ids": list(dict.fromkeys(premise_ids)),
            "source_choice_proposition_ids": list(dict.fromkeys(choice_ids)),
            "expected_reasoning_relation": expected_relation,
            "inference_pattern_hint": "",
        }
    result = classify_conditional_form_mapping(context_binding=context_binding)
    return _conditional_form_mapping_to_provenance(
        result,
        source_context_binding_ids=[binding_id] if binding_id else [],
        source_premise_proposition_ids=list(dict.fromkeys(premise_ids)),
        source_choice_proposition_ids=list(dict.fromkeys(choice_ids)),
        expected_reasoning_relation=expected_relation,
        inference_pattern_hint=result.form_label,
        origin="pipeline_derived_mapping",
    )


def derive_conditional_form_mapping_from_proof_step_candidate(candidate: object) -> dict[str, Any]:
    mapping = _safe_record_value(candidate, "conditional_form_mapping", {})
    if isinstance(mapping, dict) and mapping:
        result = dict(mapping)
        result["source_candidate_id"] = str(_safe_record_value(candidate, "candidate_id", result.get("source_candidate_id", "")) or "")
        result["source_context_binding_ids"] = _safe_record_list_value(candidate, "source_context_binding_ids") or list(result.get("source_context_binding_ids") or [])
        result["source_premise_proposition_ids"] = _safe_record_list_value(candidate, "source_premise_proposition_ids") or list(result.get("source_premise_proposition_ids") or [])
        result["source_choice_proposition_ids"] = _safe_record_list_value(candidate, "source_choice_proposition_ids") or list(result.get("source_choice_proposition_ids") or [])
        result["expected_reasoning_relation"] = str(_safe_record_value(candidate, "expected_reasoning_relation", result.get("expected_reasoning_relation", "unknown")) or "unknown")
        result["inference_pattern_hint"] = str(_safe_record_value(candidate, "inference_pattern_hint", result.get("inference_pattern_hint", "")) or "")
        return result
    return {
        "origin": "insufficient_slot_evidence",
        "form_label": "ambiguous_form",
        "support_assessment": "insufficient_structure",
        "slot_binding_status": "missing",
        "fallacy_shaped": False,
        "supported_form": False,
        "unsupported_gaps": ["conditional_slot_evidence_unavailable"],
        "source_context_binding_ids": _safe_record_list_value(candidate, "source_context_binding_ids"),
        "source_candidate_id": str(_safe_record_value(candidate, "candidate_id", "") or ""),
        "source_premise_proposition_ids": _safe_record_list_value(candidate, "source_premise_proposition_ids"),
        "source_choice_proposition_ids": _safe_record_list_value(candidate, "source_choice_proposition_ids"),
        "expected_reasoning_relation": str(_safe_record_value(candidate, "expected_reasoning_relation", "unknown") or "unknown"),
        "inference_pattern_hint": str(_safe_record_value(candidate, "inference_pattern_hint", "") or ""),
    }


def create_proof_step_candidate_from_context_binding(context_binding: object) -> ProofStepCandidate:
    binding_id = str(_safe_record_value(context_binding, "binding_id", "") or "").strip()
    premise_ids = _safe_record_list_value(context_binding, "source_premise_proposition_ids")
    choice_ids = _safe_record_list_value(context_binding, "source_choice_proposition_ids")
    unsupported_gaps = _safe_record_list_value(context_binding, "unsupported_gaps")
    expected_relation = str(_safe_record_value(context_binding, "expected_reasoning_relation", "unknown") or "unknown").strip() or "unknown"
    candidate_type = classify_proof_step_candidate_type(context_binding)
    support_status = _proof_step_candidate_support_status(context_binding, candidate_type)
    inference_pattern_hint = str(_safe_record_value(context_binding, "candidate_support_role", "") or "")
    conditional_mapping: dict[str, Any] = {}
    conditional_mapping_origin = "insufficient_slot_evidence"
    if _has_conditional_form_slots(context_binding):
        conditional_mapping = derive_conditional_form_mapping_from_context_binding(context_binding)
        conditional_mapping_origin = str(conditional_mapping.get("origin", "insufficient_slot_evidence"))
        inference_pattern_hint = str(conditional_mapping.get("form_label", "") or inference_pattern_hint)
        unsupported_gaps.extend(list(conditional_mapping.get("unsupported_gaps") or []))
        support_assessment = str(conditional_mapping.get("support_assessment", "") or "")
        if support_assessment == "fallacy_shaped":
            support_status = "unsupported"
            unsupported_gaps.append("recognized_fallacy_shaped_pattern")
        elif support_assessment == "insufficient_structure":
            support_status = "ambiguous" if support_status == "candidate_only" else support_status
            unsupported_gaps.append("conditional_form_mapping_insufficient_structure")
    source_context_binding_ids = [binding_id] if binding_id else []
    confidence = "medium" if support_status == "candidate_only" else "low"
    if not source_context_binding_ids:
        unsupported_gaps.append("missing_context_binding_ref")
    if not premise_ids:
        unsupported_gaps.append("missing_premise_proposition_refs")
    if not choice_ids:
        unsupported_gaps.append("missing_choice_proposition_refs")
    if expected_relation == "unknown":
        unsupported_gaps.append("expected_reasoning_relation_unknown")
    return ProofStepCandidate(
        candidate_id=f"proof_step_candidate:{binding_id}" if binding_id else "",
        source_context_binding_ids=source_context_binding_ids,
        source_premise_proposition_ids=list(dict.fromkeys(premise_ids)),
        source_choice_proposition_ids=list(dict.fromkeys(choice_ids)),
        candidate_type=candidate_type,
        expected_reasoning_relation=expected_relation,
        inference_pattern_hint=inference_pattern_hint,
        support_status=support_status,
        conditional_form_mapping=conditional_mapping,
        conditional_form_mapping_origin=conditional_mapping_origin,
        confidence=confidence,
        unsupported_gaps=list(dict.fromkeys(unsupported_gaps)),
        human_explanation=str(_safe_record_value(context_binding, "human_explanation", "") or "").strip()
        or "Helper-only proof-step candidate hypothesis from redacted context binding; not proof and not answer selection.",
        legibility=PropositionLegibilityRecord(),
        anti_gaming=PropositionAntiGamingRecord(),
    )


def create_proof_step_candidates_from_context_bindings(context_bindings: list[object]) -> list[ProofStepCandidate]:
    return [create_proof_step_candidate_from_context_binding(binding) for binding in list(context_bindings or [])]


def summarize_proof_step_candidate_diagnostics(candidates: list[ProofStepCandidate]) -> dict[str, Any]:
    type_counts = {value: 0 for value in SAFE_PROOF_STEP_CANDIDATE_TYPES}
    support_counts = {value: 0 for value in SAFE_PROOF_STEP_CANDIDATE_SUPPORT_STATUSES}
    confidence_counts = {"low": 0, "medium": 0, "high": 0}
    unsupported_gap_count = 0
    candidates_with_premise_refs = 0
    candidates_with_choice_refs = 0
    candidates_with_context_refs = 0
    pipeline_conditional_mapping_count = 0
    ad_hoc_conditional_mapping_count = 0
    insufficient_slot_evidence_count = 0
    conditional_with_context_refs = 0
    conditional_with_premise_refs = 0
    conditional_with_choice_refs = 0
    conditional_with_unsupported_gaps = 0
    conditional_form_counts = {value: 0 for value in SAFE_CONDITIONAL_FORM_LABELS}
    conditional_support_counts = {value: 0 for value in SAFE_CONDITIONAL_FORM_SUPPORT_ASSESSMENTS}
    anti_gaming_safe = True
    legibility_safe = True
    for candidate in candidates:
        type_counts[candidate.candidate_type] = type_counts.get(candidate.candidate_type, 0) + 1
        support_counts[candidate.support_status] = support_counts.get(candidate.support_status, 0) + 1
        if candidate.confidence in confidence_counts:
            confidence_counts[candidate.confidence] += 1
        unsupported_gap_count += len(candidate.unsupported_gaps)
        candidates_with_premise_refs += int(bool(candidate.source_premise_proposition_ids))
        candidates_with_choice_refs += int(bool(candidate.source_choice_proposition_ids))
        candidates_with_context_refs += int(bool(candidate.source_context_binding_ids))
        mapping = candidate.conditional_form_mapping if isinstance(candidate.conditional_form_mapping, dict) else {}
        origin = candidate.conditional_form_mapping_origin
        if origin == "pipeline_derived_mapping" and mapping:
            pipeline_conditional_mapping_count += 1
            form_label = str(mapping.get("form_label", "ambiguous_form") or "ambiguous_form")
            support_assessment = str(mapping.get("support_assessment", "insufficient_structure") or "insufficient_structure")
            conditional_form_counts[form_label] = conditional_form_counts.get(form_label, 0) + 1
            conditional_support_counts[support_assessment] = conditional_support_counts.get(support_assessment, 0) + 1
            conditional_with_context_refs += int(bool(mapping.get("source_context_binding_ids")))
            conditional_with_premise_refs += int(bool(mapping.get("source_premise_proposition_ids")))
            conditional_with_choice_refs += int(bool(mapping.get("source_choice_proposition_ids")))
            conditional_with_unsupported_gaps += int(bool(mapping.get("unsupported_gaps")))
        elif origin == "ad_hoc_test_mapping" and mapping:
            ad_hoc_conditional_mapping_count += 1
        else:
            insufficient_slot_evidence_count += 1
        findings = validate_proof_step_candidate(candidate)
        anti_gaming_safe = anti_gaming_safe and not any(
            finding in findings
            for finding in [
                "answer-key use is forbidden",
                "item-id authority is forbidden",
                "answer-position bias is forbidden",
                "official-score claim is forbidden",
                "benchmark-specific tuning is forbidden",
                "answer selection must remain disabled",
            ]
        )
        legibility_safe = legibility_safe and not any(
            finding in findings
            for finding in [
                "raw benchmark storage by default is forbidden",
                "private symbolic authority is forbidden",
                "unsupported assumptions must remain visible",
            ]
        )
    return {
        "proof_step_candidate_count": len(candidates),
        "candidate_type_counts": dict(sorted(type_counts.items())),
        "support_status_counts": dict(sorted(support_counts.items())),
        "low_confidence_count": confidence_counts["low"],
        "medium_confidence_count": confidence_counts["medium"],
        "high_confidence_count": confidence_counts["high"],
        "unsupported_gap_count": unsupported_gap_count,
        "candidates_with_premise_refs": candidates_with_premise_refs,
        "candidates_with_choice_refs": candidates_with_choice_refs,
        "candidates_with_context_refs": candidates_with_context_refs,
        "pipeline_conditional_form_mapping_count": pipeline_conditional_mapping_count,
        "ad_hoc_conditional_form_mapping_count": ad_hoc_conditional_mapping_count,
        "insufficient_slot_evidence_count": insufficient_slot_evidence_count,
        "conditional_form_mapping_counts": dict(sorted(conditional_form_counts.items())),
        "conditional_support_assessment_counts": dict(sorted(conditional_support_counts.items())),
        "conditional_mappings_with_context_refs": conditional_with_context_refs,
        "conditional_mappings_with_premise_refs": conditional_with_premise_refs,
        "conditional_mappings_with_choice_refs": conditional_with_choice_refs,
        "conditional_mappings_with_unsupported_gaps": conditional_with_unsupported_gaps,
        "fallacy_shaped_count": conditional_support_counts.get("fallacy_shaped", 0),
        "supported_form_count": conditional_support_counts.get("supported_form", 0),
        "proof_behavior_generated": False,
        "answer_selection_enabled": False,
        "anti_gaming_safe": anti_gaming_safe,
        "legibility_safe": legibility_safe,
    }


def _merge_value(merge: object, field_name: str, default: Any = "") -> Any:
    if isinstance(merge, dict):
        return merge.get(field_name, default)
    return getattr(merge, field_name, default)


def _merge_list_value(merge: object, field_name: str) -> list[str]:
    value = _merge_value(merge, field_name, [])
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    if str(value).strip():
        return [str(value).strip()]
    return []


def _merge_id(merge: object) -> str:
    return str(_merge_value(merge, "merge_id", "") or "").strip()


def _merge_confidence(merge: object) -> str:
    confidence = str(_merge_value(merge, "confidence_summary", "low") or "low").strip()
    return confidence if confidence in SAFE_CONFIDENCE_VALUES else "low"


def _simple_candidate_confidence(left: object, right: object | None = None) -> str:
    confidences = [_merge_confidence(left)]
    if right is not None:
        confidences.append(_merge_confidence(right))
    if confidences and all(confidence == "high" for confidence in confidences):
        return "high"
    if any(confidence == "medium" for confidence in confidences):
        return "medium"
    return "low"


def _make_simple_inference_candidate(
    *,
    candidate_id: str,
    pattern_type: str,
    merges: list[object],
    shared_subject: bool = False,
    shared_object: bool = False,
    relation_overlap: bool = False,
    contradiction_signal: bool = False,
    transitivity_signal: bool = False,
) -> SimpleInferencePatternCandidate:
    source_merge_ids: list[str] = []
    source_proposition_ids: list[str] = []
    unsupported_gaps: list[str] = []
    premise_role_count = 0
    choice_role_count = 0
    for merge in merges:
        merge_id = _merge_id(merge)
        if merge_id:
            source_merge_ids.append(merge_id)
        source_proposition_ids.extend(_merge_list_value(merge, "source_proposition_ids"))
        unsupported_gaps.extend(_merge_list_value(merge, "unsupported_gaps"))
        role = normalize_proposition_role(str(_merge_value(merge, "proposition_role", "unknown") or "unknown"))
        premise_role_count += int(role == "premise")
        choice_role_count += int(role == "choice_claim")
    confidence = _simple_candidate_confidence(merges[0], merges[1] if len(merges) > 1 else None)
    return SimpleInferencePatternCandidate(
        candidate_id=candidate_id,
        pattern_type=pattern_type,
        source_merge_ids=list(dict.fromkeys(source_merge_ids)),
        source_proposition_ids=list(dict.fromkeys(source_proposition_ids)),
        premise_role_count=premise_role_count,
        choice_role_count=choice_role_count,
        shared_subject=shared_subject,
        shared_object=shared_object,
        relation_overlap=relation_overlap,
        contradiction_signal=contradiction_signal,
        transitivity_signal=transitivity_signal,
        confidence=confidence,
        validity_status="candidate_only",
        unsupported_gaps=list(dict.fromkeys(unsupported_gaps)),
        human_explanation="Redacted helper-only simple inference pattern opportunity; not a proof step, truth claim, or answer selection.",
    )


def _opposite_polarity(left: object, right: object) -> bool:
    left_polarity = str(_merge_value(left, "polarity", "") or "").strip().lower()
    right_polarity = str(_merge_value(right, "polarity", "") or "").strip().lower()
    if not left_polarity or not right_polarity:
        left_sig = str(_merge_value(left, "structural_signature", "") or "").lower()
        right_sig = str(_merge_value(right, "structural_signature", "") or "").lower()
        left_polarity = "negative" if "polarity=negative" in left_sig else "positive" if "polarity=positive" in left_sig else ""
        right_polarity = "negative" if "polarity=negative" in right_sig else "positive" if "polarity=positive" in right_sig else ""
    return bool({left_polarity, right_polarity} == {"positive", "negative"})


def create_simple_inference_pattern_candidates_from_merges(
    merges: list[PropositionMergeCandidate],
) -> list[SimpleInferencePatternCandidate]:
    """Create helper-only simple inference opportunity candidates from merge records."""
    candidates: list[SimpleInferencePatternCandidate] = []
    next_index = 1

    for merge in merges:
        if int(_merge_value(merge, "duplicate_count", 0) or 0) >= 2:
            candidates.append(
                _make_simple_inference_candidate(
                    candidate_id=f"simple:{next_index}",
                    pattern_type="duplicate-support-candidate",
                    merges=[merge],
                )
            )
            next_index += 1

    for left_index, left in enumerate(merges):
        for right in merges[left_index + 1:]:
            left_subject = term_alignment_key(str(_merge_value(left, "subject_canonical_hint", "") or ""))
            right_subject = term_alignment_key(str(_merge_value(right, "subject_canonical_hint", "") or ""))
            left_object = term_alignment_key(str(_merge_value(left, "object_canonical_hint", "") or ""))
            right_object = term_alignment_key(str(_merge_value(right, "object_canonical_hint", "") or ""))
            left_relation = term_alignment_key(str(_merge_value(left, "relation_canonical_hint", "") or ""))
            right_relation = term_alignment_key(str(_merge_value(right, "relation_canonical_hint", "") or ""))

            shared_subject = bool(left_subject and right_subject and left_subject == right_subject)
            shared_object = bool(left_object and right_object and left_object == right_object)
            relation_overlap = bool(left_relation and right_relation and left_relation == right_relation)
            same_terms = shared_subject and shared_object and relation_overlap
            opposite_polarity = same_terms and _opposite_polarity(left, right)
            transitivity_signal = bool(left_object and right_subject and left_object == right_subject and left_relation and right_relation)

            pattern_specs = []
            if shared_subject:
                pattern_specs.append(("shared-subject", {"shared_subject": True}))
            if shared_object:
                pattern_specs.append(("shared-object", {"shared_object": True}))
            if relation_overlap:
                pattern_specs.append(("relation-overlap", {"relation_overlap": True}))
            if opposite_polarity:
                pattern_specs.append(("contradiction-candidate", {"contradiction_signal": True}))
            if transitivity_signal:
                pattern_specs.append(("transitivity-candidate", {"transitivity_signal": True}))

            for pattern_type, flags in pattern_specs:
                candidates.append(
                    _make_simple_inference_candidate(
                        candidate_id=f"simple:{next_index}",
                        pattern_type=pattern_type,
                        merges=[left, right],
                        **flags,
                    )
                )
                next_index += 1

    return candidates


def summarize_simple_inference_candidate_diagnostics(
    candidates: list[SimpleInferencePatternCandidate],
) -> dict[str, Any]:
    return {
        "candidate_count": len(candidates),
        "shared_subject_count": sum(1 for candidate in candidates if candidate.pattern_type == "shared-subject"),
        "shared_object_count": sum(1 for candidate in candidates if candidate.pattern_type == "shared-object"),
        "relation_overlap_count": sum(1 for candidate in candidates if candidate.pattern_type == "relation-overlap"),
        "duplicate_support_count": sum(1 for candidate in candidates if candidate.pattern_type == "duplicate-support-candidate"),
        "contradiction_candidate_count": sum(1 for candidate in candidates if candidate.pattern_type == "contradiction-candidate"),
        "transitivity_candidate_count": sum(1 for candidate in candidates if candidate.pattern_type == "transitivity-candidate"),
        "unsupported_no_pattern_count": sum(1 for candidate in candidates if candidate.pattern_type == "unsupported/no-pattern"),
        "low_confidence_count": sum(1 for candidate in candidates if candidate.confidence == "low"),
        "medium_confidence_count": sum(1 for candidate in candidates if candidate.confidence == "medium"),
        "high_confidence_count": sum(1 for candidate in candidates if candidate.confidence == "high"),
        "anti_gaming_safe": all(_anti_gaming_safe(candidate.anti_gaming) for candidate in candidates),
        "legibility_safe": all(_legibility_safe(candidate.legibility) for candidate in candidates),
    }


def normalize_proposition_role(role: str) -> str:
    normalized = str(role or "").strip().lower()
    if normalized in {"premise", "parsed_premise", "premise_term"}:
        return "premise"
    if normalized in {"choice_claim", "candidate", "candidate_term"}:
        return "choice_claim"
    if normalized in {"background", "question_instruction"}:
        return "background"
    return "unknown"


def _conservative_proposition_translation(subject: str, relation: str, object: str, polarity: str = "positive") -> str:
    parts = [part.strip() for part in (subject, relation, object) if part and part.strip()]
    if not parts:
        return "Conservative structural proposition with unsupported content."
    translation = " ".join(parts)
    if polarity.strip().lower() == "negative":
        return f"It is not the case that {translation}."
    return translation


def create_proposition_candidate_from_predicate(
    *,
    predicate_id: str,
    subject: str = "",
    relation: str = "",
    object: str = "",
    subject_canonical_hint: str = "",
    object_canonical_hint: str = "",
    relation_canonical_hint: str = "",
    subject_fingerprint: str = "",
    object_fingerprint: str = "",
    polarity: str = "positive",
    quantifier: str = "",
    modality: str = "",
    confidence: str = "low",
    human_translation: str = "",
    unsupported_gaps: list[str] | None = None,
    source_statement_id: str = "",
    source_statement_role: str = "",
    proposition_role: str = "",
) -> PropositionCandidate:
    gaps = list(unsupported_gaps or [])
    if not subject:
        gaps.append("missing_subject")
    if not relation:
        gaps.append("missing_relation")
    if not object:
        gaps.append("missing_object")
    proposition_type = "binary_relation" if subject and relation and object else "incomplete_relation"
    translation = human_translation.strip() or _conservative_proposition_translation(subject, relation, object, polarity)
    normalized_role = normalize_proposition_role(proposition_role or source_statement_role)
    statement_id = str(source_statement_id or "").strip()
    raw_statement_role = str(source_statement_role or proposition_role or "").strip()
    return PropositionCandidate(
        proposition_id=f"proposition:{predicate_id}",
        source_predicate_ids=[predicate_id],
        source_statement_ids=[statement_id] if statement_id else [],
        source_statement_roles=[normalized_role] if raw_statement_role else [],
        proposition_role=normalized_role,
        proposition_type=proposition_type,
        subject=subject,
        relation=relation,
        object=object,
        subject_canonical_hint=str(subject_canonical_hint or "").strip(),
        object_canonical_hint=str(object_canonical_hint or "").strip(),
        relation_canonical_hint=str(relation_canonical_hint or relation or "").strip(),
        subject_fingerprint=str(subject_fingerprint or "").strip(),
        object_fingerprint=str(object_fingerprint or "").strip(),
        polarity=polarity,
        quantifier=quantifier,
        modality=modality,
        confidence=confidence,
        human_translation=translation,
        unsupported_gaps=list(dict.fromkeys(gaps)),
    )


def _safe_predicate_value(predicate: object, field_name: str) -> Any:
    if isinstance(predicate, dict):
        return predicate.get(field_name)
    return getattr(predicate, field_name, None)


def normalize_term_for_alignment(term: str) -> str:
    text = str(term or "").strip().lower()
    if not text:
        return ""
    text = re.sub(r"[_\-/]+", " ", text)
    text = re.sub(rf"[{re.escape(string.punctuation)}]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""

    normalized_tokens: list[str] = []
    for token in text.split(" "):
        token = token.strip()
        if not token or token in _ALIGNMENT_STOPWORDS:
            continue
        if token.endswith("ies") and len(token) > 3:
            token = token[:-3] + "y"
        elif len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]
        if token:
            normalized_tokens.append(token)
    return " ".join(normalized_tokens)


def term_alignment_key(term: str) -> str:
    normalized = normalize_term_for_alignment(term)
    return normalized if normalized else ""


def compare_proposition_terms_for_alignment(left: object, right: object) -> dict[str, Any]:
    left_subject = term_alignment_key(str(_safe_predicate_value(left, "subject_canonical_hint") or ""))
    right_subject = term_alignment_key(str(_safe_predicate_value(right, "subject_canonical_hint") or ""))
    left_object = term_alignment_key(str(_safe_predicate_value(left, "object_canonical_hint") or ""))
    right_object = term_alignment_key(str(_safe_predicate_value(right, "object_canonical_hint") or ""))
    left_relation = term_alignment_key(str(_safe_predicate_value(left, "relation_canonical_hint") or ""))
    right_relation = term_alignment_key(str(_safe_predicate_value(right, "relation_canonical_hint") or ""))

    subject_match = bool(left_subject and right_subject and left_subject == right_subject)
    object_match = bool(left_object and right_object and left_object == right_object)
    relation_match = bool(left_relation and right_relation and left_relation == right_relation)
    any_term_match = subject_match or object_match or relation_match
    if subject_match and object_match and relation_match:
        match_type = "exact_normalized"
    elif subject_match:
        match_type = "subject_only"
    elif object_match:
        match_type = "object_only"
    elif relation_match:
        match_type = "relation_only"
    else:
        match_type = "none"
    return {
        "subject_match": subject_match,
        "object_match": object_match,
        "relation_match": relation_match,
        "any_term_match": any_term_match,
        "match_type": match_type,
    }


def summarize_term_alignment_candidates(propositions: list[PropositionCandidate]) -> dict[str, Any]:
    premise_props = [proposition for proposition in propositions if proposition.proposition_role == "premise"]
    choice_props = [proposition for proposition in propositions if proposition.proposition_role == "choice_claim"]
    comparison_count = 0
    subject_match_count = 0
    object_match_count = 0
    relation_match_count = 0
    any_term_match_count = 0
    no_match_count = 0

    for premise in premise_props:
        for choice in choice_props:
            comparison_count += 1
            match = compare_proposition_terms_for_alignment(premise, choice)
            subject_match_count += int(match["subject_match"])
            object_match_count += int(match["object_match"])
            relation_match_count += int(match["relation_match"])
            any_term_match_count += int(match["any_term_match"])
            no_match_count += int(not match["any_term_match"])

    return {
        "premise_proposition_count": len(premise_props),
        "choice_claim_proposition_count": len(choice_props),
        "comparison_count": comparison_count,
        "subject_match_count": subject_match_count,
        "object_match_count": object_match_count,
        "relation_match_count": relation_match_count,
        "any_term_match_count": any_term_match_count,
        "no_match_count": no_match_count,
        "anti_gaming_safe": all(_anti_gaming_safe(proposition.anti_gaming) for proposition in propositions),
        "legibility_safe": all(_legibility_safe(proposition.legibility) for proposition in propositions),
    }


def create_proposition_candidates_from_predicates(predicates: list[object]) -> list[PropositionCandidate]:
    created: list[PropositionCandidate] = []
    for predicate in predicates:
        predicate_id = str(_safe_predicate_value(predicate, "predicate_candidate_id") or "").strip()
        if not predicate_id:
            continue
        source_statement_role = str(
            _safe_predicate_value(predicate, "source_statement_role")
            or _safe_predicate_value(predicate, "statement_role")
            or _safe_predicate_value(predicate, "role")
            or ""
        )
        proposition_role = str(
            _safe_predicate_value(predicate, "role")
            or _safe_predicate_value(predicate, "statement_role")
            or _safe_predicate_value(predicate, "source_statement_role")
            or ""
        )
        subject_canonical_hint = str(
            _safe_predicate_value(predicate, "subject_canonical_hint")
            or _safe_predicate_value(predicate, "subject_hint")
            or _safe_predicate_value(predicate, "canonical_subject")
            or ""
        ).strip()
        object_canonical_hint = str(
            _safe_predicate_value(predicate, "object_canonical_hint")
            or _safe_predicate_value(predicate, "object_hint")
            or _safe_predicate_value(predicate, "canonical_object")
            or ""
        ).strip()
        relation_canonical_hint = str(
            _safe_predicate_value(predicate, "relation_canonical_hint")
            or _safe_predicate_value(predicate, "relation_hint")
            or ""
        ).strip()
        created.append(
            create_proposition_candidate_from_predicate(
                predicate_id=predicate_id,
                subject=str(_safe_predicate_value(predicate, "subject_candidate_id") or ""),
                relation=str(_safe_predicate_value(predicate, "relation_hint") or ""),
                object=str(_safe_predicate_value(predicate, "object_candidate_id") or ""),
                subject_canonical_hint=subject_canonical_hint,
                object_canonical_hint=object_canonical_hint,
                relation_canonical_hint=relation_canonical_hint,
                subject_fingerprint=str(_safe_predicate_value(predicate, "subject_fingerprint") or "").strip(),
                object_fingerprint=str(_safe_predicate_value(predicate, "object_fingerprint") or "").strip(),
                polarity=str(_safe_predicate_value(predicate, "polarity") or "positive"),
                quantifier=str(_safe_predicate_value(predicate, "quantifier_hint") or ""),
                modality=str(_safe_predicate_value(predicate, "modality_hint") or ""),
                confidence=str(_safe_predicate_value(predicate, "confidence") or "low"),
                source_statement_id=str(_safe_predicate_value(predicate, "source_statement_id") or ""),
                source_statement_role=source_statement_role,
                proposition_role=proposition_role,
            )
        )
    return created


def summarize_proposition_projection_diagnostics(propositions: list[PropositionCandidate]) -> dict[str, Any]:
    return {
        "proposition_candidate_count": len(propositions),
        "source_predicate_link_count": sum(len(proposition.source_predicate_ids) for proposition in propositions),
        "source_statement_link_count": sum(len(proposition.source_statement_ids) for proposition in propositions),
        "premise_proposition_count": sum(1 for proposition in propositions if proposition.proposition_role == "premise"),
        "choice_claim_proposition_count": sum(1 for proposition in propositions if proposition.proposition_role == "choice_claim"),
        "background_proposition_count": sum(1 for proposition in propositions if proposition.proposition_role == "background"),
        "unknown_role_proposition_count": sum(1 for proposition in propositions if proposition.proposition_role == "unknown"),
        "subject_canonical_hint_count": sum(1 for proposition in propositions if proposition.subject_canonical_hint.strip()),
        "object_canonical_hint_count": sum(1 for proposition in propositions if proposition.object_canonical_hint.strip()),
        "relation_canonical_hint_count": sum(1 for proposition in propositions if proposition.relation_canonical_hint.strip()),
        "subject_fingerprint_count": sum(1 for proposition in propositions if proposition.subject_fingerprint.strip()),
        "object_fingerprint_count": sum(1 for proposition in propositions if proposition.object_fingerprint.strip()),
        "high_confidence_count": sum(1 for proposition in propositions if proposition.confidence == "high"),
        "medium_confidence_count": sum(1 for proposition in propositions if proposition.confidence == "medium"),
        "low_confidence_count": sum(1 for proposition in propositions if proposition.confidence == "low"),
        "unsupported_gap_count": sum(len(proposition.unsupported_gaps) for proposition in propositions),
        "anti_gaming_safe": all(_anti_gaming_safe(proposition.anti_gaming) for proposition in propositions),
        "legibility_safe": all(_legibility_safe(proposition.legibility) for proposition in propositions),
    }



def _binding_value(binding: object, field_name: str) -> Any:
    if isinstance(binding, dict):
        return binding.get(field_name)
    return getattr(binding, field_name, None)


def _binding_anti_gaming_safe(binding: object) -> bool:
    anti = _binding_value(binding, "anti_gaming")
    if anti is None:
        return True
    unsafe_fields = [
        "uses_answer_key",
        "uses_item_id_as_authority",
        "uses_answer_position_bias",
        "stores_raw_benchmark_text_by_default",
        "benchmark_specific_tuning_used",
        "answer_selection_enabled",
        "official_score_claimed",
    ]
    return not any(bool(_binding_value(anti, field)) for field in unsafe_fields)


def _binding_legibility_safe(binding: object) -> bool:
    legibility = _binding_value(binding, "legibility")
    if legibility is None:
        return True
    return not any(
        [
            bool(_binding_value(legibility, "private_symbolic_authority_used")),
            not bool(_binding_value(legibility, "unsupported_gaps_visible") if _binding_value(legibility, "unsupported_gaps_visible") is not None else True),
        ]
    )


def _choice_stem_binding_projection_ready(binding: object) -> bool:
    binding_type = str(_binding_value(binding, "stem_binding_type") or "")
    if binding_type in {"", "unsupported_binding", "choice_is_fragment_unknown"}:
        return False
    if not str(_binding_value(binding, "source_choice_statement_id") or "").strip():
        return False
    if not str(_binding_value(binding, "human_explanation") or "").strip():
        return False
    if not _binding_anti_gaming_safe(binding) or not _binding_legibility_safe(binding):
        return False
    has_safe_structure = any(
        str(_binding_value(binding, field) or "").strip()
        for field in ["implied_relation_hint", "bound_subject_hint", "bound_object_hint"]
    ) or binding_type == "choice_is_full_claim"
    return bool(has_safe_structure)


def create_proposition_candidate_from_choice_stem_binding(binding: object) -> PropositionCandidate:
    """Project one ChoiceStemBindingCandidate-like record into PropositionCandidate.

    This helper uses only structural binding fields. It does not use raw text,
    answer keys, item ids as authority, answer positions, or correctness labels.
    """

    binding_id = str(_binding_value(binding, "binding_id") or "").strip()
    source_choice_statement_id = str(_binding_value(binding, "source_choice_statement_id") or "").strip()
    stem_binding_type = str(_binding_value(binding, "stem_binding_type") or "unsupported_binding").strip()
    relation_hint = str(_binding_value(binding, "implied_relation_hint") or "").strip()
    subject_hint = str(_binding_value(binding, "bound_subject_hint") or "").strip()
    object_hint = str(_binding_value(binding, "bound_object_hint") or "").strip()
    confidence = str(_binding_value(binding, "confidence") or "low").strip() or "low"
    unsupported_gaps = [str(gap) for gap in (_binding_value(binding, "unsupported_gaps") or [])]
    explanation = str(_binding_value(binding, "human_explanation") or "").strip()

    if not binding_id:
        unsupported_gaps.append("missing_binding_id")
    if stem_binding_type in {"unsupported_binding", "choice_is_fragment_unknown"}:
        unsupported_gaps.append(stem_binding_type)
    if not source_choice_statement_id:
        unsupported_gaps.append("missing_choice_statement_ref")
    if not _binding_anti_gaming_safe(binding):
        unsupported_gaps.append("binding_anti_gaming_violation")
    if not _binding_legibility_safe(binding):
        unsupported_gaps.append("binding_legibility_violation")

    proposition_type = "binding_projected_choice_claim" if _choice_stem_binding_projection_ready(binding) else "binding_projection_weak_or_unsupported"
    translation_parts = []
    if subject_hint:
        translation_parts.append("subject-hint present")
    if relation_hint:
        translation_parts.append("relation-hint present")
    if object_hint:
        translation_parts.append("object-hint present")
    if stem_binding_type == "choice_is_full_claim":
        translation_parts.append("full-claim choice structure")
    human_translation = "; ".join(translation_parts) or "Conservative binding-derived proposition with unsupported structure."
    if explanation:
        human_translation = f"{human_translation}. Binding explanation available."

    return PropositionCandidate(
        proposition_id=f"proposition:binding:{binding_id}" if binding_id else "proposition:binding:missing",
        source_predicate_ids=[f"binding:{binding_id}"] if binding_id else [],
        source_statement_ids=[source_choice_statement_id] if source_choice_statement_id else [],
        source_statement_roles=["choice_claim"] if source_choice_statement_id else [],
        proposition_role="choice_claim",
        proposition_type=proposition_type,
        subject=subject_hint,
        relation=relation_hint,
        object=object_hint,
        subject_canonical_hint=subject_hint,
        object_canonical_hint=object_hint,
        relation_canonical_hint=relation_hint,
        confidence=confidence if confidence in SAFE_CONFIDENCE_VALUES else "low",
        human_translation=human_translation,
        unsupported_gaps=list(dict.fromkeys(unsupported_gaps)),
        legibility=PropositionLegibilityRecord(
            human_translation_available=True,
            redacted_summary_only=True,
            stores_raw_benchmark_text=False,
            hides_unsupported_assumptions=False,
            private_symbolic_authority=False,
            human_explanation="Binding-derived proposition is redacted and structural only.",
        ),
        anti_gaming=PropositionAntiGamingRecord(
            uses_answer_key=False,
            uses_item_id_as_authority=False,
            uses_answer_position_bias=False,
            claims_official_score=False,
            benchmark_specific_tuning=False,
            uses_private_symbolic_authority=False,
            no_answer_selection=True,
            human_explanation="Binding-derived projection does not select answers or use benchmark authority.",
        ),
    )


def summarize_binding_to_proposition_projection_diagnostics(
    bindings: list[object],
    propositions: list[PropositionCandidate] | None = None,
) -> dict[str, Any]:
    """Return redacted counts for binding-derived proposition projection."""

    projected = list(propositions) if propositions is not None else [
        create_proposition_candidate_from_choice_stem_binding(binding)
        for binding in bindings
        if _choice_stem_binding_projection_ready(binding)
    ]
    confidence_counts = {"low": 0, "medium": 0, "high": 0}
    for proposition in projected:
        if proposition.confidence in confidence_counts:
            confidence_counts[proposition.confidence] += 1
    return {
        "binding_count": len(bindings),
        "projection_ready_binding_count": sum(1 for binding in bindings if _choice_stem_binding_projection_ready(binding)),
        "proposition_candidate_count": len(projected),
        "low_confidence_count": confidence_counts["low"],
        "medium_confidence_count": confidence_counts["medium"],
        "high_confidence_count": confidence_counts["high"],
        "unsupported_gap_count": sum(len(proposition.unsupported_gaps) for proposition in projected),
        "anti_gaming_safe": all(_binding_anti_gaming_safe(binding) for binding in bindings) and all(_anti_gaming_safe(proposition.anti_gaming) for proposition in projected),
        "legibility_safe": all(_binding_legibility_safe(binding) for binding in bindings) and all(_legibility_safe(proposition.legibility) for proposition in projected),
    }

def create_empty_inference_pattern(
    *,
    pattern_id: str = "",
    pattern_family: str = "",
    pattern_name: str = "",
    validity_type: str = "unknown",
) -> InferencePattern:
    return InferencePattern(
        pattern_id=pattern_id,
        pattern_family=pattern_family,
        pattern_name=pattern_name,
        validity_type=validity_type,
    )


def inference_pattern_to_dict(pattern: InferencePattern) -> dict[str, Any]:
    return asdict(pattern)


def inference_pattern_from_dict(data: dict[str, Any]) -> InferencePattern:
    legibility_data = data.get("legibility") or {}
    anti_gaming_data = data.get("anti_gaming") or {}
    return InferencePattern(
        schema_version=data.get("schema_version", "1.0"),
        pattern_id=data.get("pattern_id", ""),
        pattern_family=data.get("pattern_family", ""),
        pattern_name=data.get("pattern_name", ""),
        validity_type=data.get("validity_type", "unknown"),
        required_proposition_roles=list(data.get("required_proposition_roles") or []),
        supported_proposition_types=list(data.get("supported_proposition_types") or []),
        fallacy_name=data.get("fallacy_name", ""),
        description=data.get("description", ""),
        human_explanation=data.get("human_explanation", ""),
        counterexample_required=bool(data.get("counterexample_required", False)),
        confidence=data.get("confidence", "low"),
        legibility=PropositionLegibilityRecord(**legibility_data),
        anti_gaming=PropositionAntiGamingRecord(**anti_gaming_data),
    )


def validate_inference_pattern(pattern: InferencePattern) -> list[str]:
    messages: list[str] = []
    if not pattern.pattern_id:
        messages.append("missing pattern id")
    if not pattern.pattern_name:
        messages.append("missing pattern name")
    if pattern.validity_type not in SAFE_VALIDITY_TYPES:
        messages.append("invalid validity type")
    if pattern.confidence not in SAFE_CONFIDENCE_VALUES:
        messages.append("invalid confidence value")
    if pattern.confidence == "high" and not pattern.human_explanation.strip():
        messages.append("missing human explanation for high-confidence inference pattern")
    messages.extend(_validate_shared_safety(pattern.legibility, pattern.anti_gaming))
    return messages


def summarize_inference_pattern(pattern: InferencePattern) -> dict[str, Any]:
    return {
        "schema_version": pattern.schema_version,
        "pattern_id": pattern.pattern_id,
        "pattern_family": pattern.pattern_family,
        "pattern_name": pattern.pattern_name,
        "validity_type": pattern.validity_type,
        "required_proposition_role_count": len(pattern.required_proposition_roles),
        "supported_proposition_type_count": len(pattern.supported_proposition_types),
        "fallacy_name": pattern.fallacy_name,
        "counterexample_required": pattern.counterexample_required,
        "confidence": pattern.confidence,
        "human_explanation_available": bool(pattern.human_explanation.strip()),
        "legibility_safe": _legibility_safe(pattern.legibility),
        "anti_gaming_safe": _anti_gaming_safe(pattern.anti_gaming),
    }


def create_empty_proof_step(
    *,
    proof_step_id: str = "",
    source_proposition_ids: list[str] | None = None,
    target_proposition_id: str = "",
    inference_pattern_id: str = "",
    validity_status: str = "unknown",
) -> ProofStep:
    return ProofStep(
        proof_step_id=proof_step_id,
        source_proposition_ids=list(source_proposition_ids or []),
        target_proposition_id=target_proposition_id,
        inference_pattern_id=inference_pattern_id,
        inference_pattern=inference_pattern_id,
        validity_status=validity_status,
        support_status="unsupported" if validity_status == "unknown" else "supported",
    )


def proof_step_to_dict(proof_step: ProofStep) -> dict[str, Any]:
    return asdict(proof_step)


def proof_step_from_dict(data: dict[str, Any]) -> ProofStep:
    legibility_data = data.get("legibility") or {}
    anti_gaming_data = data.get("anti_gaming") or {}
    unsupported_gaps = list(data.get("unsupported_gaps") or data.get("unsupported_assumptions") or [])
    return ProofStep(
        schema_version=data.get("schema_version", "1.0"),
        proof_step_id=data.get("proof_step_id", ""),
        source_candidate_id=data.get("source_candidate_id", ""),
        source_context_binding_ids=list(data.get("source_context_binding_ids") or []),
        source_premise_proposition_ids=list(data.get("source_premise_proposition_ids") or []),
        source_choice_proposition_ids=list(data.get("source_choice_proposition_ids") or []),
        reasoning_relation=data.get("reasoning_relation", "unknown"),
        inference_pattern=data.get("inference_pattern", data.get("inference_pattern_id", "")),
        support_status=data.get("support_status", "unsupported"),
        source_proposition_ids=list(data.get("source_proposition_ids") or []),
        target_proposition_id=data.get("target_proposition_id", ""),
        inference_pattern_id=data.get("inference_pattern_id", data.get("inference_pattern", "")),
        warrant=data.get("warrant", ""),
        validity_status=data.get("validity_status", "unknown"),
        conditional_form_mapping=dict(data.get("conditional_form_mapping") or {}),
        conditional_form_mapping_origin=data.get("conditional_form_mapping_origin", "insufficient_slot_evidence"),
        confidence=data.get("confidence", "low"),
        human_explanation=data.get("human_explanation", ""),
        unsupported_gaps=unsupported_gaps,
        unsupported_assumptions=list(data.get("unsupported_assumptions") or unsupported_gaps),
        requires_counterexample=bool(data.get("requires_counterexample", False)),
        legibility=PropositionLegibilityRecord(**legibility_data),
        anti_gaming=PropositionAntiGamingRecord(**anti_gaming_data),
    )


def validate_proof_step(proof_step: ProofStep) -> list[str]:
    messages: list[str] = []
    if not proof_step.proof_step_id:
        messages.append("missing proof step id")
    if proof_step.validity_status not in SAFE_VALIDITY_TYPES:
        messages.append("invalid validity status")
    if proof_step.support_status not in SAFE_PROOF_STEP_SUPPORT_STATUSES:
        messages.append("invalid proof step support status")
    if proof_step.confidence not in SAFE_CONFIDENCE_VALUES:
        messages.append("invalid confidence value")
    if proof_step.confidence == "high" and not proof_step.warrant.strip():
        messages.append("missing warrant for high-confidence proof step")
    if proof_step.confidence == "high" and not proof_step.human_explanation.strip():
        messages.append("missing human explanation for high-confidence proof step")
    messages.extend(_validate_shared_safety(proof_step.legibility, proof_step.anti_gaming))
    return messages


def summarize_proof_step(proof_step: ProofStep) -> dict[str, Any]:
    return {
        "schema_version": proof_step.schema_version,
        "proof_step_id": proof_step.proof_step_id,
        "has_source_candidate": bool(proof_step.source_candidate_id),
        "context_binding_source_count": len(proof_step.source_context_binding_ids),
        "premise_proposition_source_count": len(proof_step.source_premise_proposition_ids),
        "choice_proposition_source_count": len(proof_step.source_choice_proposition_ids),
        "source_proposition_count": len(proof_step.source_proposition_ids),
        "has_target_proposition": bool(proof_step.target_proposition_id),
        "reasoning_relation": proof_step.reasoning_relation,
        "has_inference_pattern": bool(proof_step.inference_pattern.strip() or proof_step.inference_pattern_id.strip()),
        "support_status": proof_step.support_status,
        "validity_status": proof_step.validity_status,
        "conditional_form_mapping_origin": proof_step.conditional_form_mapping_origin,
        "conditional_form_mapping_available": bool(proof_step.conditional_form_mapping),
        "confidence": proof_step.confidence,
        "has_warrant": bool(proof_step.warrant.strip()),
        "human_explanation_available": bool(proof_step.human_explanation.strip()),
        "unsupported_gap_count": len(proof_step.unsupported_gaps),
        "unsupported_assumption_count": len(proof_step.unsupported_assumptions),
        "requires_counterexample": proof_step.requires_counterexample,
        "legibility_safe": _legibility_safe(proof_step.legibility),
        "anti_gaming_safe": _anti_gaming_safe(proof_step.anti_gaming),
    }


_PROOF_STEP_CANDIDATE_STATUS_MAP = {
    "support_step_candidate": "supported",
    "contradiction_step_candidate": "contradicted",
    "counterexample_step_candidate": "counterexample_supported",
    "rule_application_candidate": "rule_application_supported",
    "invalidity_test_candidate": "rule_application_supported",
    "template_completion_candidate": "template_completed",
}


def _proof_step_support_status_from_candidate(candidate: object) -> str:
    candidate_type = str(_safe_record_value(candidate, "candidate_type", "unsupported_step_candidate") or "unsupported_step_candidate")
    candidate_status = str(_safe_record_value(candidate, "support_status", "unknown") or "unknown")
    if candidate_type not in _PROOF_STEP_CANDIDATE_STATUS_MAP:
        return "ambiguous" if candidate_status == "ambiguous" else "unsupported"
    if candidate_status in {"unsupported", "insufficient_support", "unknown"}:
        return "unsupported"
    if candidate_status == "ambiguous":
        return "ambiguous"
    return _PROOF_STEP_CANDIDATE_STATUS_MAP[candidate_type]


def _proof_step_validity_status(support_status: str) -> str:
    if support_status in {"supported", "rule_application_supported", "template_completed"}:
        return "valid"
    if support_status in {"contradicted", "counterexample_supported"}:
        return "invalid"
    if support_status == "ambiguous":
        return "ambiguous"
    return "unsupported"


def create_proof_step_from_candidate(candidate: object) -> ProofStep:
    if isinstance(candidate, dict):
        candidate = proof_step_candidate_from_dict(candidate)
    candidate_id = str(_safe_record_value(candidate, "candidate_id", "") or "").strip()
    context_ids = _safe_record_list_value(candidate, "source_context_binding_ids")
    premise_ids = _safe_record_list_value(candidate, "source_premise_proposition_ids")
    choice_ids = _safe_record_list_value(candidate, "source_choice_proposition_ids")
    relation = str(_safe_record_value(candidate, "expected_reasoning_relation", "unknown") or "unknown").strip() or "unknown"
    inference_pattern = str(_safe_record_value(candidate, "inference_pattern_hint", "") or "").strip()
    confidence = str(_safe_record_value(candidate, "confidence", "low") or "low").strip()
    if confidence not in SAFE_CONFIDENCE_VALUES:
        confidence = "low"
    unsupported_gaps = _safe_record_list_value(candidate, "unsupported_gaps")
    conditional_mapping = derive_conditional_form_mapping_from_proof_step_candidate(candidate)
    conditional_mapping_origin = str(conditional_mapping.get("origin", "insufficient_slot_evidence") or "insufficient_slot_evidence")
    support_status = _proof_step_support_status_from_candidate(candidate)
    if not candidate_id:
        unsupported_gaps.append("missing_source_candidate_id")
    if not context_ids:
        unsupported_gaps.append("missing_context_binding_ref")
    if not premise_ids:
        unsupported_gaps.append("missing_premise_proposition_refs")
    if not choice_ids:
        unsupported_gaps.append("missing_choice_proposition_refs")
    if relation == "unknown":
        unsupported_gaps.append("expected_reasoning_relation_unknown")
    if not inference_pattern:
        unsupported_gaps.append("inference_pattern_hint_unknown")
    structural_gap_markers = ("missing_", "_unknown", "unknown_")
    has_structural_gap = any(str(gap).startswith("missing_") or any(marker in str(gap) for marker in structural_gap_markers[1:]) for gap in unsupported_gaps)
    if has_structural_gap and support_status not in {"ambiguous", "unsupported"}:
        support_status = "ambiguous"
    unique_gaps = list(dict.fromkeys(unsupported_gaps))
    return ProofStep(
        proof_step_id=f"proof_step:{candidate_id}" if candidate_id else "",
        source_candidate_id=candidate_id,
        source_context_binding_ids=context_ids,
        source_premise_proposition_ids=premise_ids,
        source_choice_proposition_ids=choice_ids,
        reasoning_relation=relation,
        inference_pattern=inference_pattern,
        support_status=support_status,
        source_proposition_ids=list(dict.fromkeys(premise_ids)),
        target_proposition_id=choice_ids[0] if choice_ids else "",
        inference_pattern_id=inference_pattern,
        warrant="Helper-only structural warrant from safe ProofStepCandidate; not answer selection and not a benchmark truth claim.",
        validity_status=_proof_step_validity_status(support_status),
        conditional_form_mapping=conditional_mapping if conditional_mapping_origin == "pipeline_derived_mapping" else {},
        conditional_form_mapping_origin=conditional_mapping_origin,
        confidence=confidence,
        human_explanation=str(_safe_record_value(candidate, "human_explanation", "") or "").strip()
        or "Helper-only proof step from redacted synthetic candidate; no teaching explanation generated.",
        unsupported_gaps=unique_gaps,
        unsupported_assumptions=unique_gaps,
        requires_counterexample=support_status == "counterexample_supported",
        legibility=PropositionLegibilityRecord(),
        anti_gaming=PropositionAntiGamingRecord(),
    )


def create_proof_steps_from_candidates(candidates: list[object]) -> list[ProofStep]:
    return [create_proof_step_from_candidate(candidate) for candidate in list(candidates or [])]


def summarize_proof_step_generation_diagnostics(proof_steps: list[ProofStep]) -> dict[str, Any]:
    support_counts = {value: 0 for value in SAFE_PROOF_STEP_SUPPORT_STATUSES}
    relation_counts: dict[str, int] = {}
    pattern_counts: dict[str, int] = {}
    confidence_counts = {"low": 0, "medium": 0, "high": 0}
    unsupported_gap_count = 0
    pipeline_conditional_mapping_count = 0
    ad_hoc_conditional_mapping_count = 0
    insufficient_slot_evidence_count = 0
    conditional_with_context_refs = 0
    conditional_with_premise_refs = 0
    conditional_with_choice_refs = 0
    conditional_with_visible_warrant = 0
    conditional_with_unsupported_gaps = 0
    conditional_form_counts = {value: 0 for value in SAFE_CONDITIONAL_FORM_LABELS}
    conditional_support_counts = {value: 0 for value in SAFE_CONDITIONAL_FORM_SUPPORT_ASSESSMENTS}
    anti_gaming_safe = True
    legibility_safe = True
    for proof_step in proof_steps:
        support_counts[proof_step.support_status] = support_counts.get(proof_step.support_status, 0) + 1
        relation_counts[proof_step.reasoning_relation] = relation_counts.get(proof_step.reasoning_relation, 0) + 1
        pattern_key = proof_step.inference_pattern or "unknown"
        pattern_counts[pattern_key] = pattern_counts.get(pattern_key, 0) + 1
        if proof_step.confidence in confidence_counts:
            confidence_counts[proof_step.confidence] += 1
        unsupported_gap_count += len(proof_step.unsupported_gaps)
        mapping = proof_step.conditional_form_mapping if isinstance(proof_step.conditional_form_mapping, dict) else {}
        origin = proof_step.conditional_form_mapping_origin
        if origin == "pipeline_derived_mapping" and mapping:
            pipeline_conditional_mapping_count += 1
            form_label = str(mapping.get("form_label", "ambiguous_form") or "ambiguous_form")
            support_assessment = str(mapping.get("support_assessment", "insufficient_structure") or "insufficient_structure")
            conditional_form_counts[form_label] = conditional_form_counts.get(form_label, 0) + 1
            conditional_support_counts[support_assessment] = conditional_support_counts.get(support_assessment, 0) + 1
            conditional_with_context_refs += int(bool(mapping.get("source_context_binding_ids")))
            conditional_with_premise_refs += int(bool(mapping.get("source_premise_proposition_ids")))
            conditional_with_choice_refs += int(bool(mapping.get("source_choice_proposition_ids")))
            conditional_with_visible_warrant += int(bool(proof_step.warrant))
            conditional_with_unsupported_gaps += int(bool(mapping.get("unsupported_gaps")))
        elif origin == "ad_hoc_test_mapping" and mapping:
            ad_hoc_conditional_mapping_count += 1
        else:
            insufficient_slot_evidence_count += 1
        findings = validate_proof_step(proof_step)
        anti_gaming_safe = anti_gaming_safe and not any(
            finding in findings
            for finding in [
                "answer-key use is forbidden",
                "item-id authority is forbidden",
                "answer-position bias is forbidden",
                "official-score claim is forbidden",
                "benchmark-specific tuning is forbidden",
                "answer selection must remain disabled",
            ]
        )
        legibility_safe = legibility_safe and not any(
            finding in findings
            for finding in [
                "raw benchmark storage by default is forbidden",
                "private symbolic authority is forbidden",
                "unsupported assumptions must remain visible",
            ]
        )
    return {
        "proof_step_count": len(proof_steps),
        "support_status_counts": dict(sorted(support_counts.items())),
        "reasoning_relation_counts": dict(sorted(relation_counts.items())),
        "inference_pattern_counts": dict(sorted(pattern_counts.items())),
        "low_confidence_count": confidence_counts["low"],
        "medium_confidence_count": confidence_counts["medium"],
        "high_confidence_count": confidence_counts["high"],
        "unsupported_gap_count": unsupported_gap_count,
        "pipeline_conditional_form_mapping_count": pipeline_conditional_mapping_count,
        "ad_hoc_conditional_form_mapping_count": ad_hoc_conditional_mapping_count,
        "insufficient_slot_evidence_count": insufficient_slot_evidence_count,
        "conditional_form_mapping_counts": dict(sorted(conditional_form_counts.items())),
        "conditional_support_assessment_counts": dict(sorted(conditional_support_counts.items())),
        "conditional_mappings_with_context_refs": conditional_with_context_refs,
        "conditional_mappings_with_premise_refs": conditional_with_premise_refs,
        "conditional_mappings_with_choice_refs": conditional_with_choice_refs,
        "conditional_mappings_with_visible_warrant": conditional_with_visible_warrant,
        "conditional_mappings_with_unsupported_gaps": conditional_with_unsupported_gaps,
        "fallacy_shaped_count": conditional_support_counts.get("fallacy_shaped", 0),
        "supported_form_count": conditional_support_counts.get("supported_form", 0),
        "proof_chain_generated": False,
        "teaching_explanation_generated": False,
        "answer_selection_enabled": False,
        "truth_claim_made": False,
        "official_score_claimed": False,
        "anti_gaming_safe": anti_gaming_safe,
        "legibility_safe": legibility_safe,
    }


def create_empty_counterexample_candidate(
    *,
    counterexample_id: str = "",
    challenged_proposition_id: str = "",
    challenged_proof_step_id: str = "",
    counterexample_type: str = "",
) -> CounterexampleCandidate:
    return CounterexampleCandidate(
        counterexample_id=counterexample_id,
        challenged_proposition_id=challenged_proposition_id,
        challenged_proof_step_id=challenged_proof_step_id,
        counterexample_type=counterexample_type,
    )


def counterexample_candidate_to_dict(counterexample: CounterexampleCandidate) -> dict[str, Any]:
    return asdict(counterexample)


def counterexample_candidate_from_dict(data: dict[str, Any]) -> CounterexampleCandidate:
    legibility_data = data.get("legibility") or {}
    anti_gaming_data = data.get("anti_gaming") or {}
    return CounterexampleCandidate(
        schema_version=data.get("schema_version", "1.0"),
        counterexample_id=data.get("counterexample_id", ""),
        challenged_proposition_id=data.get("challenged_proposition_id", ""),
        challenged_proof_step_id=data.get("challenged_proof_step_id", ""),
        counterexample_type=data.get("counterexample_type", ""),
        possible_world_sketch=data.get("possible_world_sketch", ""),
        violated_assumption=data.get("violated_assumption", ""),
        fallacy_pattern_id=data.get("fallacy_pattern_id", ""),
        confidence=data.get("confidence", "low"),
        human_explanation=data.get("human_explanation", ""),
        unsupported_gaps=list(data.get("unsupported_gaps") or []),
        legibility=PropositionLegibilityRecord(**legibility_data),
        anti_gaming=PropositionAntiGamingRecord(**anti_gaming_data),
    )


def validate_counterexample_candidate(counterexample: CounterexampleCandidate) -> list[str]:
    messages: list[str] = []
    if not counterexample.counterexample_id:
        messages.append("missing counterexample id")
    if counterexample.confidence not in SAFE_CONFIDENCE_VALUES:
        messages.append("invalid confidence value")
    if counterexample.confidence == "high" and not (
        counterexample.challenged_proposition_id.strip() or counterexample.challenged_proof_step_id.strip()
    ):
        messages.append("missing challenged target for high-confidence counterexample")
    if counterexample.confidence == "high" and not counterexample.human_explanation.strip():
        messages.append("missing human explanation for high-confidence counterexample")
    messages.extend(_validate_shared_safety(counterexample.legibility, counterexample.anti_gaming))
    return messages


def summarize_counterexample_candidate(counterexample: CounterexampleCandidate) -> dict[str, Any]:
    return {
        "schema_version": counterexample.schema_version,
        "counterexample_id": counterexample.counterexample_id,
        "has_challenged_proposition": bool(counterexample.challenged_proposition_id),
        "has_challenged_proof_step": bool(counterexample.challenged_proof_step_id),
        "counterexample_type": counterexample.counterexample_type,
        "has_possible_world_sketch": bool(counterexample.possible_world_sketch.strip()),
        "has_violated_assumption": bool(counterexample.violated_assumption.strip()),
        "has_fallacy_pattern": bool(counterexample.fallacy_pattern_id),
        "confidence": counterexample.confidence,
        "human_explanation_available": bool(counterexample.human_explanation.strip()),
        "unsupported_gap_count": len(counterexample.unsupported_gaps),
        "legibility_safe": _legibility_safe(counterexample.legibility),
        "anti_gaming_safe": _anti_gaming_safe(counterexample.anti_gaming),
    }


def create_empty_teaching_explanation(
    *,
    explanation_id: str = "",
    source_proof_step_ids: list[str] | None = None,
    source_context_binding_ids: list[str] | None = None,
    source_proposition_ids: list[str] | None = None,
    support_status: str = "unknown",
    teaching_mode: str = "unknown",
    learner_level: str = "general",
    core_claim: str = "",
    why_it_follows_or_fails: str = "",
    pattern_name: str = "",
    fallacy_name: str = "",
    counterexample_note: str = "",
    confidence: str = "low",
) -> TeachingExplanation:
    return TeachingExplanation(
        explanation_id=explanation_id,
        source_proof_step_ids=list(source_proof_step_ids or []),
        source_context_binding_ids=list(source_context_binding_ids or []),
        source_proposition_ids=list(source_proposition_ids or []),
        support_status=support_status,
        teaching_mode=teaching_mode,
        learner_level=learner_level,
        core_claim=core_claim,
        why_it_follows_or_fails=why_it_follows_or_fails,
        pattern_name=pattern_name,
        fallacy_name=fallacy_name,
        counterexample_note=counterexample_note,
        confidence=confidence,
    )


def teaching_explanation_to_dict(explanation: TeachingExplanation) -> dict[str, Any]:
    return asdict(explanation)


def teaching_explanation_from_dict(data: dict[str, Any]) -> TeachingExplanation:
    legibility_data = data.get("legibility") or {}
    anti_gaming_data = data.get("anti_gaming") or {}
    return TeachingExplanation(
        schema_version=data.get("schema_version", "1.0"),
        explanation_id=data.get("explanation_id", ""),
        source_proposition_ids=list(data.get("source_proposition_ids") or []),
        source_proof_step_ids=list(data.get("source_proof_step_ids") or []),
        source_context_binding_ids=list(data.get("source_context_binding_ids") or []),
        source_counterexample_ids=list(data.get("source_counterexample_ids") or []),
        conclusion=data.get("conclusion", ""),
        support_status=data.get("support_status", "unknown"),
        core_claim=data.get("core_claim", ""),
        why_it_follows_or_fails=data.get("why_it_follows_or_fails", ""),
        pattern_name=data.get("pattern_name", ""),
        fallacy_name=data.get("fallacy_name", ""),
        counterexample_note=data.get("counterexample_note", ""),
        confidence=data.get("confidence", "low"),
        common_fallacy=data.get("common_fallacy", ""),
        learner_level=data.get("learner_level", "general"),
        teaching_mode=data.get("teaching_mode", "unknown"),
        step_by_step_explanation=list(data.get("step_by_step_explanation") or []),
        uncertainty_note=data.get("uncertainty_note", ""),
        human_explanation=data.get("human_explanation", ""),
        unsupported_gaps=list(data.get("unsupported_gaps") or []),
        legibility=PropositionLegibilityRecord(**legibility_data),
        anti_gaming=PropositionAntiGamingRecord(**anti_gaming_data),
    )


def validate_teaching_explanation(explanation: TeachingExplanation) -> list[str]:
    messages: list[str] = []
    if not explanation.explanation_id:
        messages.append("missing explanation id")
    if explanation.support_status not in SAFE_TEACHING_EXPLANATION_SUPPORT_STATUSES:
        messages.append("invalid support status")
    if explanation.teaching_mode not in SAFE_TEACHING_MODES:
        messages.append("invalid teaching mode")
    if explanation.confidence not in SAFE_CONFIDENCE_VALUES:
        messages.append("invalid confidence")
    if explanation.confidence == "high" and not explanation.source_proof_step_ids:
        messages.append("missing proof step refs for high-confidence teaching explanation")
    if explanation.confidence == "high" and not explanation.human_explanation.strip():
        messages.append("missing human explanation for high-confidence teaching explanation")
    if explanation.legibility.hides_unsupported_assumptions:
        messages.append("unsupported gaps must remain visible")
    messages.extend(_validate_shared_safety(explanation.legibility, explanation.anti_gaming))
    return messages


def summarize_teaching_explanation(explanation: TeachingExplanation) -> dict[str, Any]:
    return {
        "schema_version": explanation.schema_version,
        "explanation_id": explanation.explanation_id,
        "source_proposition_count": len(explanation.source_proposition_ids),
        "source_proof_step_count": len(explanation.source_proof_step_ids),
        "source_context_binding_count": len(explanation.source_context_binding_ids),
        "source_counterexample_count": len(explanation.source_counterexample_ids),
        "has_conclusion": bool(explanation.conclusion.strip()),
        "support_status": explanation.support_status,
        "has_core_claim": bool(explanation.core_claim.strip()),
        "has_why_it_follows_or_fails": bool(explanation.why_it_follows_or_fails.strip()),
        "has_pattern_name": bool(explanation.pattern_name.strip()),
        "has_fallacy_name": bool(explanation.fallacy_name.strip() or explanation.common_fallacy.strip()),
        "has_counterexample_note": bool(explanation.counterexample_note.strip()),
        "confidence": explanation.confidence,
        "learner_level": explanation.learner_level,
        "teaching_mode": explanation.teaching_mode,
        "step_count": len(explanation.step_by_step_explanation),
        "has_uncertainty_note": bool(explanation.uncertainty_note.strip()),
        "human_explanation_available": bool(explanation.human_explanation.strip()),
        "unsupported_gap_count": len(explanation.unsupported_gaps),
        "legibility_safe": _legibility_safe(explanation.legibility),
        "anti_gaming_safe": _anti_gaming_safe(explanation.anti_gaming),
    }


def _teaching_proof_step_value(proof_step: object, field_name: str, default: Any = "") -> Any:
    if isinstance(proof_step, dict):
        return proof_step.get(field_name, default)
    return getattr(proof_step, field_name, default)


def _teaching_proof_step_list_value(proof_step: object, field_name: str) -> list[str]:
    value = _teaching_proof_step_value(proof_step, field_name, [])
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    if str(value).strip():
        return [str(value).strip()]
    return []



def _teaching_source_legibility(proof_step: object) -> PropositionLegibilityRecord:
    source = _teaching_proof_step_value(proof_step, "legibility", None)
    if isinstance(source, PropositionLegibilityRecord):
        return PropositionLegibilityRecord(**asdict(source))
    if isinstance(source, dict):
        return PropositionLegibilityRecord(**source)
    return PropositionLegibilityRecord()


def _teaching_source_anti_gaming(proof_step: object) -> PropositionAntiGamingRecord:
    source = _teaching_proof_step_value(proof_step, "anti_gaming", None)
    if isinstance(source, PropositionAntiGamingRecord):
        return PropositionAntiGamingRecord(**asdict(source))
    if isinstance(source, dict):
        return PropositionAntiGamingRecord(**source)
    return PropositionAntiGamingRecord()

def _teaching_pattern_name_from_proof_step(proof_step: object) -> str:
    mapping = _teaching_proof_step_value(proof_step, "conditional_form_mapping", {})
    mapping = mapping if isinstance(mapping, dict) else {}
    pattern = str(mapping.get("form_label", "") or "").strip()
    if not pattern:
        pattern = str(_teaching_proof_step_value(proof_step, "inference_pattern", "") or "").strip()
    if not pattern:
        pattern = str(_teaching_proof_step_value(proof_step, "inference_pattern_id", "") or "").strip()
    return pattern or "unknown_pattern"


def _teaching_fallacy_name_from_proof_step(proof_step: object, pattern_name: str) -> str:
    mapping = _teaching_proof_step_value(proof_step, "conditional_form_mapping", {})
    mapping = mapping if isinstance(mapping, dict) else {}
    support_assessment = str(mapping.get("support_assessment", "") or "").strip()
    fallacy_shaped = bool(mapping.get("fallacy_shaped", False)) or support_assessment == "fallacy_shaped"
    if fallacy_shaped and pattern_name in {"affirming_consequent", "affirming the consequent"}:
        return "affirming the consequent"
    if fallacy_shaped and pattern_name in {"denying_antecedent", "denying the antecedent"}:
        return "denying the antecedent"
    return ""



def _classify_teaching_unsupported_gap(gap: str, *, fallacy_name: str = "") -> str:
    normalized = str(gap or "").strip()
    if fallacy_name and normalized == "recognized_fallacy_shaped_pattern":
        return "redundant_structural_note"
    if fallacy_name and normalized == "fallacy label may be exposed without choosing a response":
        return "safety_caution"
    if normalized in {"helper_only_synthetic_fixture", "diagnostic_only"}:
        return "diagnostic_note"
    return "actual_uncertainty"


def _teaching_actual_uncertainty_gaps(gaps: list[str], *, fallacy_name: str = "") -> list[str]:
    return list(
        dict.fromkeys(
            gap
            for gap in gaps
            if _classify_teaching_unsupported_gap(gap, fallacy_name=fallacy_name) == "actual_uncertainty"
        )
    )

def _teaching_counterexample_note(proof_step: object, support_status: str) -> str:
    requires_counterexample = bool(_teaching_proof_step_value(proof_step, "requires_counterexample", False))
    if support_status == "counterexample_supported" or requires_counterexample:
        return "A counterexample-shaped structural note is available; this is not a benchmark truth claim."
    return ""


def _teaching_mode_text(mode: str, support_status: str, pattern_name: str, fallacy_name: str, gap_count: int) -> tuple[str, str, list[str]]:
    pattern_label = pattern_name.replace("_", " ") if pattern_name else "unknown pattern"
    if support_status in {"ambiguous", "unsupported", "unknown"}:
        why = "The proof step is not treated as established because required structural support is missing or ambiguous."
    elif fallacy_name:
        why = "The proof step is fallacy-shaped, so the helper explains the structural failure rather than certifying the conclusion."
    elif support_status == "counterexample_supported":
        why = "The proof step carries counterexample-shaped support and is explained as a structural challenge only."
    else:
        why = "The proof step has structural support under its recorded pattern, without selecting an answer or asserting benchmark truth."

    if mode == "beginner":
        core = "This explains the proof step in plain structural terms."
        steps = ["Look at the recorded premises and target.", why]
    elif mode == "technical":
        core = f"Structural explanation using pattern: {pattern_label}."
        steps = [f"Pattern field: {pattern_label}.", f"Support status: {support_status}.", why]
    elif mode == "academic":
        core = "Conservative formal explanation of the recorded inference structure."
        steps = ["Identify the recorded inference form.", "Check whether the support status licenses only a structural explanation.", why]
    elif mode == "spock":
        core = "Logical structure noted; certainty is not inferred."
        steps = [f"Form: {pattern_label}.", f"Status: {support_status}."]
    elif mode == "operator_audit":
        core = "Audit-only teaching explanation with provenance and gap visibility."
        steps = ["Proof-step refs are preserved when available.", f"Unsupported gap count: {gap_count}.", "Safety flags remain non-authoritative."]
    else:
        core = "Conservative structural teaching explanation."
        steps = [why]
    return core, why, steps


def create_teaching_explanation_from_proof_step(proof_step: object, *, teaching_mode: str = "beginner") -> TeachingExplanation:
    """Create a helper-only TeachingExplanation from a safe synthetic ProofStep-like record.

    This helper is structural only. It does not select answers, assert truth or soundness,
    claim official scores, use answer keys, use item ids as authority, or tune to a benchmark.
    """

    mode = teaching_mode if teaching_mode in SAFE_TEACHING_MODES else "unknown"
    proof_step_id = str(_teaching_proof_step_value(proof_step, "proof_step_id", "") or "").strip()
    support_status = str(_teaching_proof_step_value(proof_step, "support_status", "unknown") or "unknown").strip()
    if support_status not in SAFE_TEACHING_EXPLANATION_SUPPORT_STATUSES:
        support_status = "unknown"
    confidence = str(_teaching_proof_step_value(proof_step, "confidence", "low") or "low").strip()
    if confidence not in SAFE_CONFIDENCE_VALUES:
        confidence = "low"
    legibility = _teaching_source_legibility(proof_step)
    anti_gaming = _teaching_source_anti_gaming(proof_step)
    context_ids = _teaching_proof_step_list_value(proof_step, "source_context_binding_ids")
    premise_ids = _teaching_proof_step_list_value(proof_step, "source_premise_proposition_ids")
    choice_ids = _teaching_proof_step_list_value(proof_step, "source_choice_proposition_ids")
    source_ids = _teaching_proof_step_list_value(proof_step, "source_proposition_ids")
    target_id = str(_teaching_proof_step_value(proof_step, "target_proposition_id", "") or "").strip()
    proposition_ids = list(dict.fromkeys(source_ids + premise_ids + choice_ids + ([target_id] if target_id else [])))
    unsupported_gaps = _teaching_proof_step_list_value(proof_step, "unsupported_gaps")
    if support_status in {"ambiguous", "unsupported", "unknown"} and not unsupported_gaps:
        unsupported_gaps.append("structural_support_missing_or_ambiguous")
    pattern_name = _teaching_pattern_name_from_proof_step(proof_step)
    fallacy_name = _teaching_fallacy_name_from_proof_step(proof_step, pattern_name)
    unsupported_gaps = _teaching_actual_uncertainty_gaps(unsupported_gaps, fallacy_name=fallacy_name)
    if fallacy_name or support_status in {"ambiguous", "unsupported", "unknown"}:
        confidence = "low"
    counterexample_note = _teaching_counterexample_note(proof_step, support_status)
    core_claim, why, steps = _teaching_mode_text(mode, support_status, pattern_name, fallacy_name, len(unsupported_gaps))
    if fallacy_name == "affirming the consequent":
        steps.append("This has the structure of affirming the consequent.")
    elif fallacy_name == "denying the antecedent":
        steps.append("This has the structure of denying the antecedent.")
    if counterexample_note:
        steps.append("Counterexample support is recorded structurally.")
    if unsupported_gaps:
        steps.append("Unsupported or ambiguous gaps remain visible.")
    explanation = TeachingExplanation(
        explanation_id=f"teaching:{proof_step_id}" if proof_step_id else "",
        source_proof_step_ids=[proof_step_id] if proof_step_id else [],
        source_context_binding_ids=context_ids,
        source_proposition_ids=proposition_ids,
        conclusion="Redacted structural conclusion reference only." if target_id else "",
        support_status=support_status,
        core_claim=core_claim,
        why_it_follows_or_fails=why,
        pattern_name=pattern_name,
        fallacy_name=fallacy_name,
        counterexample_note=counterexample_note,
        confidence=confidence,
        common_fallacy=fallacy_name,
        learner_level="general",
        teaching_mode=mode,
        step_by_step_explanation=steps,
        uncertainty_note="Unsupported or ambiguous structure is not upgraded to certainty." if support_status in {"ambiguous", "unsupported", "unknown"} else "No truth, soundness, answer, or score claim is made.",
        human_explanation="Redacted helper-only teaching explanation from synthetic proof-step structure.",
        unsupported_gaps=list(dict.fromkeys(unsupported_gaps)),
        legibility=legibility,
        anti_gaming=anti_gaming,
    )
    return explanation


def create_teaching_explanations_from_proof_steps(proof_steps: list[object], *, teaching_mode: str = "beginner") -> list[TeachingExplanation]:
    return [create_teaching_explanation_from_proof_step(proof_step, teaching_mode=teaching_mode) for proof_step in list(proof_steps or [])]


def summarize_teaching_explanation_generation_diagnostics(explanations: list[TeachingExplanation]) -> dict[str, Any]:
    mode_counts = {mode: 0 for mode in SAFE_TEACHING_MODES}
    support_counts = {status: 0 for status in SAFE_TEACHING_EXPLANATION_SUPPORT_STATUSES}
    pattern_counts: dict[str, int] = {}
    fallacy_count = 0
    counterexample_note_count = 0
    unsupported_gap_count = 0
    explanation_text_present_count = 0
    proof_step_refs_present_count = 0
    anti_gaming_safe = True
    legibility_safe = True
    for explanation in explanations:
        mode_counts[explanation.teaching_mode] = mode_counts.get(explanation.teaching_mode, 0) + 1
        support_counts[explanation.support_status] = support_counts.get(explanation.support_status, 0) + 1
        pattern_key = explanation.pattern_name or "unknown"
        pattern_counts[pattern_key] = pattern_counts.get(pattern_key, 0) + 1
        fallacy_count += int(bool(explanation.fallacy_name or explanation.common_fallacy))
        counterexample_note_count += int(bool(explanation.counterexample_note.strip()))
        unsupported_gap_count += len(explanation.unsupported_gaps)
        explanation_text_present_count += int(bool(explanation.human_explanation.strip() or explanation.core_claim.strip() or explanation.why_it_follows_or_fails.strip()))
        proof_step_refs_present_count += int(bool(explanation.source_proof_step_ids))
        anti_gaming_safe = anti_gaming_safe and _anti_gaming_safe(explanation.anti_gaming)
        legibility_safe = legibility_safe and _legibility_safe(explanation.legibility)
    return {
        "teaching_explanation_count": len(explanations),
        "teaching_mode_counts": dict(sorted(mode_counts.items())),
        "support_status_counts": dict(sorted(support_counts.items())),
        "pattern_counts": dict(sorted(pattern_counts.items())),
        "fallacy_count": fallacy_count,
        "counterexample_note_count": counterexample_note_count,
        "unsupported_gap_count": unsupported_gap_count,
        "explanation_text_present_count": explanation_text_present_count,
        "proof_step_refs_present_count": proof_step_refs_present_count,
        "answer_selection_enabled": False,
        "truth_claim_made": False,
        "official_score_claimed": False,
        "anti_gaming_safe": anti_gaming_safe,
        "legibility_safe": legibility_safe,
    }


def make_modus_ponens_pattern() -> InferencePattern:
    return InferencePattern(
        pattern_id="pattern:modus_ponens",
        pattern_family="conditional_inference",
        pattern_name="modus ponens",
        validity_type="valid",
        required_proposition_roles=["conditional_premise", "antecedent_premise", "derived_conclusion"],
        supported_proposition_types=["conditional", "atomic_claim"],
        description="If a conditional premise and its antecedent are both accepted, the consequent is supported.",
        human_explanation="This pattern describes the valid move from 'if P then Q' and 'P' to 'Q'.",
        confidence="low",
    )


def make_modus_tollens_pattern() -> InferencePattern:
    return InferencePattern(
        pattern_id="pattern:modus_tollens",
        pattern_family="conditional_inference",
        pattern_name="modus tollens",
        validity_type="valid",
        required_proposition_roles=["conditional_premise", "negated_consequent_premise", "derived_negated_antecedent"],
        supported_proposition_types=["conditional", "negated_claim"],
        description="If a conditional premise holds and the consequent is false, the antecedent is ruled out.",
        human_explanation="This pattern describes the valid move from 'if P then Q' and 'not Q' to 'not P'.",
        confidence="low",
        counterexample_required=False,
    )


def make_universal_syllogism_pattern() -> InferencePattern:
    return InferencePattern(
        pattern_id="pattern:universal_syllogism",
        pattern_family="syllogism",
        pattern_name="universal syllogism",
        validity_type="valid",
        required_proposition_roles=["universal_premise", "instance_premise", "derived_conclusion"],
        supported_proposition_types=["universal_claim", "instance_claim"],
        description="A universal rule and a matching instance can support a specific conclusion.",
        human_explanation="This pattern describes the valid move from a universal statement and a matching case to a specific result.",
        confidence="low",
    )


def make_affirming_consequent_fallacy_pattern() -> InferencePattern:
    return InferencePattern(
        pattern_id="pattern:affirming_consequent",
        pattern_family="conditional_fallacy",
        pattern_name="affirming the consequent",
        validity_type="invalid",
        required_proposition_roles=["conditional_premise", "consequent_premise", "invalid_conclusion"],
        supported_proposition_types=["conditional", "atomic_claim"],
        fallacy_name="affirming the consequent",
        description="From 'if P then Q' and 'Q', concluding 'P' is invalid.",
        human_explanation="This pattern is invalid because the consequent may be true for reasons unrelated to the antecedent.",
        counterexample_required=True,
        confidence="low",
    )


def make_denying_antecedent_fallacy_pattern() -> InferencePattern:
    return InferencePattern(
        pattern_id="pattern:denying_antecedent",
        pattern_family="conditional_fallacy",
        pattern_name="denying the antecedent",
        validity_type="invalid",
        required_proposition_roles=["conditional_premise", "negated_antecedent_premise", "invalid_conclusion"],
        supported_proposition_types=["conditional", "negated_claim"],
        fallacy_name="denying the antecedent",
        description="From 'if P then Q' and 'not P', concluding 'not Q' is invalid.",
        human_explanation="This pattern is invalid because the consequent may still hold even when the antecedent does not.",
        counterexample_required=True,
        confidence="low",
    )


def make_necessary_sufficient_confusion_pattern() -> InferencePattern:
    return InferencePattern(
        pattern_id="pattern:necessary_sufficient_confusion",
        pattern_family="condition_confusion",
        pattern_name="necessary/sufficient confusion",
        validity_type="invalid",
        required_proposition_roles=["conditional_premise", "misread_condition", "invalid_conclusion"],
        supported_proposition_types=["conditional", "condition_claim"],
        fallacy_name="necessary/sufficient confusion",
        description="A necessary condition is mistaken for a sufficient one, or the reverse.",
        human_explanation="This pattern is invalid because it swaps the direction or force of a conditional requirement.",
        counterexample_required=True,
        confidence="low",
    )
