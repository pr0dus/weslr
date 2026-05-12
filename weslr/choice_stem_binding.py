"""Schema-only choice-stem binding records for WESLR.

Choice-stem binding is a pre-proposition normalization aid, not a separate
reasoning path. This module defines structural records that may support later
projection into PropositionCandidate without bypassing the existing teaching
spine.

This module intentionally does not implement binding behavior, proposition
projection, inference matching, proof steps, answer selection, or scoring.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ALLOWED_STEM_BINDING_TYPES = frozenset(
    {
        "choice_completes_question_predicate",
        "choice_supplies_subject",
        "choice_supplies_object",
        "choice_supplies_conclusion",
        "choice_is_full_claim",
        "choice_is_fragment_unknown",
        "unsupported_binding",
    }
)

ALLOWED_CONFIDENCE_VALUES = frozenset({"low", "medium", "high"})


@dataclass
class ChoiceStemBindingAntiGamingRecord:
    uses_answer_key: bool = False
    uses_item_id_as_authority: bool = False
    uses_answer_position_bias: bool = False
    stores_raw_benchmark_text_by_default: bool = False
    benchmark_specific_tuning_used: bool = False
    answer_selection_enabled: bool = False
    official_score_claimed: bool = False


@dataclass
class ChoiceStemBindingLegibilityRecord:
    human_explanation_available: bool = True
    unsupported_gaps_visible: bool = True
    binding_warrants_available: bool = True
    private_symbolic_authority_used: bool = False
    raw_text_required_for_review: bool = False


@dataclass
class ChoiceStemBindingCandidate:
    schema_version: str = "1.0"
    binding_id: str = ""
    source_question_instruction_id: str = ""
    source_choice_statement_id: str = ""
    choice_role: str = "choice_claim"
    stem_binding_type: str = "choice_is_fragment_unknown"
    implied_relation_hint: str = ""
    bound_subject_hint: str = ""
    bound_object_hint: str = ""
    confidence: str = "low"
    unsupported_gaps: list[str] = field(default_factory=list)
    human_explanation: str = ""
    legibility: ChoiceStemBindingLegibilityRecord = field(
        default_factory=ChoiceStemBindingLegibilityRecord
    )
    anti_gaming: ChoiceStemBindingAntiGamingRecord = field(
        default_factory=ChoiceStemBindingAntiGamingRecord
    )


def create_empty_choice_stem_binding_candidate(
    *,
    binding_id: str = "",
    source_question_instruction_id: str = "",
    source_choice_statement_id: str = "",
) -> ChoiceStemBindingCandidate:
    """Create an empty schema record with safe defaults."""

    return ChoiceStemBindingCandidate(
        binding_id=binding_id,
        source_question_instruction_id=source_question_instruction_id,
        source_choice_statement_id=source_choice_statement_id,
    )


def choice_stem_binding_candidate_to_dict(
    candidate: ChoiceStemBindingCandidate,
) -> dict[str, Any]:
    """Serialize a choice-stem binding candidate to a plain dictionary."""

    return asdict(candidate)


def choice_stem_binding_candidate_from_dict(
    data: dict[str, Any],
) -> ChoiceStemBindingCandidate:
    """Deserialize a choice-stem binding candidate from a plain dictionary."""

    legibility_data = data.get("legibility", {}) or {}
    anti_gaming_data = data.get("anti_gaming", {}) or {}

    return ChoiceStemBindingCandidate(
        schema_version=str(data.get("schema_version", "1.0")),
        binding_id=str(data.get("binding_id", "")),
        source_question_instruction_id=str(data.get("source_question_instruction_id", "")),
        source_choice_statement_id=str(data.get("source_choice_statement_id", "")),
        choice_role=str(data.get("choice_role", "choice_claim")),
        stem_binding_type=str(data.get("stem_binding_type", "choice_is_fragment_unknown")),
        implied_relation_hint=str(data.get("implied_relation_hint", "")),
        bound_subject_hint=str(data.get("bound_subject_hint", "")),
        bound_object_hint=str(data.get("bound_object_hint", "")),
        confidence=str(data.get("confidence", "low")),
        unsupported_gaps=[str(gap) for gap in data.get("unsupported_gaps", [])],
        human_explanation=str(data.get("human_explanation", "")),
        legibility=ChoiceStemBindingLegibilityRecord(**legibility_data),
        anti_gaming=ChoiceStemBindingAntiGamingRecord(**anti_gaming_data),
    )


def validate_choice_stem_binding_candidate(
    candidate: ChoiceStemBindingCandidate,
) -> list[str]:
    """Return schema and safety validation findings for a candidate.

    Findings are strings so diagnostics remain simple and dependency-free.
    Empty list means the schema record is valid for storage as a structural
    pre-proposition normalization aid.
    """

    findings: list[str] = []

    if not candidate.binding_id.strip():
        findings.append("missing_binding_id")

    if candidate.stem_binding_type not in ALLOWED_STEM_BINDING_TYPES:
        findings.append("invalid_stem_binding_type")

    if candidate.confidence not in ALLOWED_CONFIDENCE_VALUES:
        findings.append("invalid_confidence")

    if candidate.confidence == "high" and not candidate.source_choice_statement_id.strip():
        findings.append("high_confidence_missing_source_choice_statement_id")

    if candidate.confidence == "high" and not candidate.human_explanation.strip():
        findings.append("high_confidence_missing_human_explanation")

    if candidate.unsupported_gaps and not candidate.legibility.unsupported_gaps_visible:
        findings.append("hidden_unsupported_gaps")

    if candidate.legibility.private_symbolic_authority_used:
        findings.append("private_symbolic_authority")

    if candidate.anti_gaming.uses_answer_key:
        findings.append("answer_key_use")

    if candidate.anti_gaming.uses_item_id_as_authority:
        findings.append("item_id_authority")

    if candidate.anti_gaming.uses_answer_position_bias:
        findings.append("answer_position_bias")

    if candidate.anti_gaming.stores_raw_benchmark_text_by_default:
        findings.append("raw_benchmark_text_storage_by_default")

    if candidate.anti_gaming.benchmark_specific_tuning_used:
        findings.append("benchmark_specific_tuning")

    if candidate.anti_gaming.answer_selection_enabled:
        findings.append("answer_selection_enabled")

    if candidate.anti_gaming.official_score_claimed:
        findings.append("official_score_claim")

    return findings


def summarize_choice_stem_binding_candidate(
    candidate: ChoiceStemBindingCandidate,
) -> dict[str, Any]:
    """Return a redacted count/metadata-only summary.

    The summary intentionally excludes raw prompt text, option labels, key
    material, source strings, and binding type names. It is suitable for
    aggregate diagnostics without exposing benchmark content.
    """

    return {
        "schema_version": candidate.schema_version,
        "binding_id_present": bool(candidate.binding_id.strip()),
        "source_instruction_ref_present": bool(
            candidate.source_question_instruction_id.strip()
        ),
        "source_statement_ref_present": bool(candidate.source_choice_statement_id.strip()),
        "binding_type_known": candidate.stem_binding_type in ALLOWED_STEM_BINDING_TYPES,
        "confidence": candidate.confidence,
        "unsupported_gap_count": len(candidate.unsupported_gaps),
        "has_relation_hint": bool(candidate.implied_relation_hint.strip()),
        "has_subject_hint": bool(candidate.bound_subject_hint.strip()),
        "has_object_hint": bool(candidate.bound_object_hint.strip()),
        "has_human_explanation": bool(candidate.human_explanation.strip()),
        "legible": (
            candidate.legibility.human_explanation_available
            and candidate.legibility.unsupported_gaps_visible
            and candidate.legibility.binding_warrants_available
            and not candidate.legibility.private_symbolic_authority_used
        ),
        "safety_ok": not any(
            [
                candidate.anti_gaming.uses_answer_key,
                candidate.anti_gaming.uses_item_id_as_authority,
                candidate.anti_gaming.uses_answer_position_bias,
                candidate.anti_gaming.stores_raw_benchmark_text_by_default,
                candidate.anti_gaming.benchmark_specific_tuning_used,
                candidate.anti_gaming.answer_selection_enabled,
                candidate.anti_gaming.official_score_claimed,
            ]
        ),
        "finding_count": len(validate_choice_stem_binding_candidate(candidate)),
    }
