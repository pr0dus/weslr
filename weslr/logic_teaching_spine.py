from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SAFE_CONFIDENCE_VALUES = {"low", "medium", "high"}
REDACTED_SUMMARY_KEYS = {
    "schema_version",
    "proposition_id",
    "proposition_type",
    "polarity",
    "quantifier",
    "modality",
    "confidence",
    "source_predicate_count",
    "unsupported_gap_count",
    "human_translation_available",
    "legibility_safe",
    "anti_gaming_safe",
}


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
    human_explanation: str = "Proposition schema is structural only and does not use benchmark authority or answer selection."


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
    if candidate.anti_gaming.uses_answer_key:
        messages.append("answer-key use is forbidden")
    if candidate.anti_gaming.uses_item_id_as_authority:
        messages.append("item-id authority is forbidden")
    if candidate.anti_gaming.claims_official_score:
        messages.append("official-score claim is forbidden")
    if candidate.legibility.stores_raw_benchmark_text:
        messages.append("raw benchmark storage by default is forbidden")
    if candidate.legibility.private_symbolic_authority or candidate.anti_gaming.uses_private_symbolic_authority:
        messages.append("private symbolic authority is forbidden")
    if candidate.anti_gaming.uses_answer_position_bias:
        messages.append("answer-position bias is forbidden")
    if candidate.anti_gaming.benchmark_specific_tuning:
        messages.append("benchmark-specific tuning is forbidden")
    if not candidate.anti_gaming.no_answer_selection:
        messages.append("answer selection must remain disabled")
    if not candidate.legibility.redacted_summary_only:
        messages.append("redacted summaries are required")
    if candidate.legibility.hides_unsupported_assumptions:
        messages.append("unsupported assumptions must remain visible")

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
        "legibility_safe": not any(
            [
                candidate.legibility.stores_raw_benchmark_text,
                candidate.legibility.hides_unsupported_assumptions,
                candidate.legibility.private_symbolic_authority,
            ]
        ),
        "anti_gaming_safe": not any(
            [
                candidate.anti_gaming.uses_answer_key,
                candidate.anti_gaming.uses_item_id_as_authority,
                candidate.anti_gaming.uses_answer_position_bias,
                candidate.anti_gaming.claims_official_score,
                candidate.anti_gaming.benchmark_specific_tuning,
                candidate.anti_gaming.uses_private_symbolic_authority,
                not candidate.anti_gaming.no_answer_selection,
            ]
        ),
    }
