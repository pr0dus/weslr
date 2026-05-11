from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SAFE_CONFIDENCE_VALUES = {"low", "medium", "high"}
SAFE_VALIDITY_TYPES = {"valid", "invalid", "ambiguous", "unsupported", "unknown"}


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
    proposition_type: str = "unknown"
    subject: str = ""
    relation: str = ""
    object: str = ""
    polarity: str = "positive"
    quantifier: str = ""
    modality: str = ""
    confidence: str = "low"
    human_translation: str = ""
    unsupported_gaps: list[str] = field(default_factory=list)
    legibility: PropositionLegibilityRecord = field(default_factory=PropositionLegibilityRecord)
    anti_gaming: PropositionAntiGamingRecord = field(default_factory=PropositionAntiGamingRecord)


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
    proposition_type: str = "unknown",
) -> PropositionCandidate:
    return PropositionCandidate(
        proposition_id=proposition_id,
        source_predicate_ids=list(source_predicate_ids or []),
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
        proposition_type=data.get("proposition_type", "unknown"),
        subject=data.get("subject", ""),
        relation=data.get("relation", ""),
        object=data.get("object", ""),
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
    messages.extend(_validate_shared_safety(candidate.legibility, candidate.anti_gaming))
    return messages


def summarize_proposition_candidate(candidate: PropositionCandidate) -> dict[str, Any]:
    return {
        "schema_version": candidate.schema_version,
        "proposition_id": candidate.proposition_id,
        "proposition_type": candidate.proposition_type,
        "polarity": candidate.polarity,
        "quantifier": candidate.quantifier,
        "modality": candidate.modality,
        "confidence": candidate.confidence,
        "source_predicate_count": len(candidate.source_predicate_ids),
        "unsupported_gap_count": len(candidate.unsupported_gaps),
        "human_translation_available": bool(candidate.human_translation.strip()),
        "legibility_safe": _legibility_safe(candidate.legibility),
        "anti_gaming_safe": _anti_gaming_safe(candidate.anti_gaming),
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
