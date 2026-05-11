from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SAFE_CONFIDENCE_VALUES = {"low", "medium", "high"}
SAFE_VALIDITY_TYPES = {"valid", "invalid", "ambiguous", "unsupported", "unknown"}
SAFE_SUPPORT_STATUSES = {"supported", "unsupported", "invalid", "ambiguous", "unknown"}
SAFE_TEACHING_MODES = {"beginner", "academic", "proof_only", "counterexample_first", "socratic_hint", "spock", "standard"}
SAFE_PROPOSITION_ROLES = {"premise", "choice_claim", "background", "unknown"}


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
    source_proposition_ids: list[str] = field(default_factory=list)
    target_proposition_id: str = ""
    inference_pattern_id: str = ""
    warrant: str = ""
    validity_status: str = "unknown"
    confidence: str = "low"
    human_explanation: str = ""
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
    source_counterexample_ids: list[str] = field(default_factory=list)
    conclusion: str = ""
    support_status: str = "unknown"
    common_fallacy: str = ""
    learner_level: str = "general"
    teaching_mode: str = "standard"
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
        validity_status=validity_status,
    )


def proof_step_to_dict(proof_step: ProofStep) -> dict[str, Any]:
    return asdict(proof_step)


def proof_step_from_dict(data: dict[str, Any]) -> ProofStep:
    legibility_data = data.get("legibility") or {}
    anti_gaming_data = data.get("anti_gaming") or {}
    return ProofStep(
        schema_version=data.get("schema_version", "1.0"),
        proof_step_id=data.get("proof_step_id", ""),
        source_proposition_ids=list(data.get("source_proposition_ids") or []),
        target_proposition_id=data.get("target_proposition_id", ""),
        inference_pattern_id=data.get("inference_pattern_id", ""),
        warrant=data.get("warrant", ""),
        validity_status=data.get("validity_status", "unknown"),
        confidence=data.get("confidence", "low"),
        human_explanation=data.get("human_explanation", ""),
        unsupported_assumptions=list(data.get("unsupported_assumptions") or []),
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
        "source_proposition_count": len(proof_step.source_proposition_ids),
        "has_target_proposition": bool(proof_step.target_proposition_id),
        "has_inference_pattern": bool(proof_step.inference_pattern_id),
        "validity_status": proof_step.validity_status,
        "confidence": proof_step.confidence,
        "has_warrant": bool(proof_step.warrant.strip()),
        "human_explanation_available": bool(proof_step.human_explanation.strip()),
        "unsupported_assumption_count": len(proof_step.unsupported_assumptions),
        "requires_counterexample": proof_step.requires_counterexample,
        "legibility_safe": _legibility_safe(proof_step.legibility),
        "anti_gaming_safe": _anti_gaming_safe(proof_step.anti_gaming),
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
    support_status: str = "unknown",
    teaching_mode: str = "standard",
    learner_level: str = "general",
) -> TeachingExplanation:
    return TeachingExplanation(
        explanation_id=explanation_id,
        support_status=support_status,
        teaching_mode=teaching_mode,
        learner_level=learner_level,
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
        source_counterexample_ids=list(data.get("source_counterexample_ids") or []),
        conclusion=data.get("conclusion", ""),
        support_status=data.get("support_status", "unknown"),
        common_fallacy=data.get("common_fallacy", ""),
        learner_level=data.get("learner_level", "general"),
        teaching_mode=data.get("teaching_mode", "standard"),
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
    if explanation.support_status not in SAFE_SUPPORT_STATUSES:
        messages.append("invalid support status")
    if explanation.teaching_mode not in SAFE_TEACHING_MODES:
        messages.append("invalid teaching mode")
    if explanation.legibility.human_translation_available and not explanation.human_explanation.strip():
        messages.append("missing human explanation when legibility requires it")
    if explanation.support_status != "unknown" and not explanation.step_by_step_explanation:
        messages.append("empty step-by-step explanation is not allowed when support status is known")
    messages.extend(_validate_shared_safety(explanation.legibility, explanation.anti_gaming))
    return messages


def summarize_teaching_explanation(explanation: TeachingExplanation) -> dict[str, Any]:
    return {
        "schema_version": explanation.schema_version,
        "explanation_id": explanation.explanation_id,
        "source_proposition_count": len(explanation.source_proposition_ids),
        "source_proof_step_count": len(explanation.source_proof_step_ids),
        "source_counterexample_count": len(explanation.source_counterexample_ids),
        "has_conclusion": bool(explanation.conclusion.strip()),
        "support_status": explanation.support_status,
        "common_fallacy": explanation.common_fallacy,
        "learner_level": explanation.learner_level,
        "teaching_mode": explanation.teaching_mode,
        "step_count": len(explanation.step_by_step_explanation),
        "has_uncertainty_note": bool(explanation.uncertainty_note.strip()),
        "human_explanation_available": bool(explanation.human_explanation.strip()),
        "unsupported_gap_count": len(explanation.unsupported_gaps),
        "legibility_safe": _legibility_safe(explanation.legibility),
        "anti_gaming_safe": _anti_gaming_safe(explanation.anti_gaming),
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
