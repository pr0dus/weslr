"""Schema and helper-only choice-stem binding records for WESLR.

Choice-stem binding is a pre-proposition normalization aid, not a separate
reasoning path. This module defines structural records that may support later
projection into PropositionCandidate without bypassing the existing teaching
spine.

This module intentionally does not implement proposition projection, inference
matching, proof steps, answer selection, or scoring.
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

_CONCLUSION_MARKERS = frozenset({"conclusion", "follows", "follow", "infer", "inferred", "entailed", "entails"})
_SUBJECT_MARKERS = frozenset({"who", "which", "object", "thing", "one", "entity", "has", "property"})
_OBJECT_MARKERS = frozenset({"what", "which", "object", "property", "value"})
_PREDICATE_FRAME_MARKERS = frozenset({"true", "false", "valid", "invalid", "property", "has", "is", "are"})
_BINDING_TYPE_ALIASES = {
    "choice_completes_question_predicate": "completes_predicate",
    "choice_supplies_subject": "supplies_subject",
    "choice_supplies_object": "supplies_object",
    "choice_supplies_conclusion": "supplies_conclusion",
    "choice_is_full_claim": "full_claim",
    "choice_is_fragment_unknown": "fragment_unknown",
    "unsupported_binding": "unsupported",
}


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
    legibility: ChoiceStemBindingLegibilityRecord = field(default_factory=ChoiceStemBindingLegibilityRecord)
    anti_gaming: ChoiceStemBindingAntiGamingRecord = field(default_factory=ChoiceStemBindingAntiGamingRecord)


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


def choice_stem_binding_candidate_to_dict(candidate: ChoiceStemBindingCandidate) -> dict[str, Any]:
    """Serialize a choice-stem binding candidate to a plain dictionary."""
    return asdict(candidate)


def choice_stem_binding_candidate_from_dict(data: dict[str, Any]) -> ChoiceStemBindingCandidate:
    """Deserialize a choice-stem binding candidate from a plain dictionary."""
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
        legibility=ChoiceStemBindingLegibilityRecord(**(data.get("legibility", {}) or {})),
        anti_gaming=ChoiceStemBindingAntiGamingRecord(**(data.get("anti_gaming", {}) or {})),
    )


def validate_choice_stem_binding_candidate(candidate: ChoiceStemBindingCandidate) -> list[str]:
    """Return schema and safety validation findings for a candidate."""
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


def summarize_choice_stem_binding_candidate(candidate: ChoiceStemBindingCandidate) -> dict[str, Any]:
    """Return a redacted count/metadata-only summary for one candidate."""
    return {
        "schema_version": candidate.schema_version,
        "binding_id_present": bool(candidate.binding_id.strip()),
        "source_instruction_ref_present": bool(candidate.source_question_instruction_id.strip()),
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


def _normalized_marker_set(markers: list[str] | None) -> set[str]:
    return {str(marker).strip().lower() for marker in (markers or []) if str(marker).strip()}


def _record_value(record: object, key: str, default: str = "") -> str:
    if isinstance(record, dict):
        return str(record.get(key, default) or "")
    return str(getattr(record, key, default) or "")


def _record_statement_id(record: object) -> str:
    return _record_value(record, "statement_id") or _record_value(record, "id")


def _record_role(record: object) -> str:
    return _record_value(record, "role")


def _markers_from_record(record: object) -> list[str]:
    surface = " ".join(
        part
        for part in [_record_value(record, "normalized_text"), _record_value(record, "logical_form")]
        if part
    ).lower()
    if not surface:
        return []
    cleaned = "".join(char if char.isalnum() or char == "_" else " " for char in surface)
    return [token for token in cleaned.split() if token]


def _record_has_relation_hint(record: object) -> bool:
    markers = _normalized_marker_set(_markers_from_record(record))
    relation_markers = {
        "is", "are", "was", "were", "support", "supports", "oppose", "opposes",
        "require", "requires", "prevent", "prevents", "permit", "permits", "allow",
        "allows", "imply", "implies", "if", "then",
    }
    return bool(markers & relation_markers)


def _record_is_noun_phrase_like(record: object) -> bool:
    markers = _normalized_marker_set(_markers_from_record(record))
    return bool(markers) and not _record_has_relation_hint(record) and len(markers) <= 5


def _record_is_full_claim_like(record: object) -> bool:
    markers = _normalized_marker_set(_markers_from_record(record))
    return _record_has_relation_hint(record) or bool(
        markers & {"if", "then", "all", "some", "no", "not", "is", "are", "was", "were", "implies", "imply"}
    )


def classify_choice_stem_binding_type(
    *,
    question_instruction_markers: list[str] | None = None,
    choice_markers: list[str] | None = None,
    choice_has_relation_hint: bool = False,
    choice_is_noun_phrase_like: bool = False,
    choice_is_full_claim_like: bool = False,
) -> str:
    """Classify a structural binding type without solving or selecting."""
    instruction = _normalized_marker_set(question_instruction_markers)
    selected = _normalized_marker_set(choice_markers)
    if choice_is_full_claim_like or choice_has_relation_hint:
        return "choice_is_full_claim"
    is_fragment = choice_is_noun_phrase_like or bool(selected)
    if is_fragment and instruction & _CONCLUSION_MARKERS:
        return "choice_supplies_conclusion"
    if is_fragment and instruction & {"which", "object", "thing", "one"} and instruction & {"has", "property"}:
        return "choice_supplies_subject"
    if is_fragment and instruction & _OBJECT_MARKERS and not instruction & _PREDICATE_FRAME_MARKERS:
        return "choice_supplies_object"
    if is_fragment and instruction & _SUBJECT_MARKERS and instruction & {"has", "property"}:
        return "choice_supplies_subject"
    if is_fragment and instruction & _PREDICATE_FRAME_MARKERS:
        return "choice_completes_question_predicate"
    if is_fragment:
        return "choice_is_fragment_unknown"
    return "unsupported_binding"


def create_choice_stem_binding_candidate(
    *,
    binding_id: str,
    source_question_instruction_id: str = "",
    source_choice_statement_id: str = "",
    choice_role: str = "choice_claim",
    question_instruction_markers: list[str] | None = None,
    choice_markers: list[str] | None = None,
    choice_has_relation_hint: bool = False,
    choice_is_noun_phrase_like: bool = False,
    choice_is_full_claim_like: bool = False,
    implied_relation_hint: str = "",
    bound_subject_hint: str = "",
    bound_object_hint: str = "",
    confidence: str = "low",
) -> ChoiceStemBindingCandidate:
    """Create one helper-only binding candidate from redacted structure."""
    stem_binding_type = classify_choice_stem_binding_type(
        question_instruction_markers=question_instruction_markers,
        choice_markers=choice_markers,
        choice_has_relation_hint=choice_has_relation_hint,
        choice_is_noun_phrase_like=choice_is_noun_phrase_like,
        choice_is_full_claim_like=choice_is_full_claim_like,
    )
    unsupported_gaps: list[str] = []
    if stem_binding_type in {"choice_is_fragment_unknown", "unsupported_binding"}:
        unsupported_gaps.append("binding_not_explicit")
    if not source_question_instruction_id:
        unsupported_gaps.append("missing_question_instruction_ref")
    if not source_choice_statement_id:
        unsupported_gaps.append("missing_choice_statement_ref")
    if stem_binding_type != "choice_is_full_claim" and not implied_relation_hint:
        unsupported_gaps.append("relation_not_explicit")
    return ChoiceStemBindingCandidate(
        binding_id=binding_id,
        source_question_instruction_id=source_question_instruction_id,
        source_choice_statement_id=source_choice_statement_id,
        choice_role=choice_role,
        stem_binding_type=stem_binding_type,
        implied_relation_hint=implied_relation_hint,
        bound_subject_hint=bound_subject_hint,
        bound_object_hint=bound_object_hint,
        confidence=confidence,
        unsupported_gaps=list(dict.fromkeys(unsupported_gaps)),
        human_explanation=(
            "Choice-stem binding candidate created from parsed statement references, "
            "redacted markers, and structural shape flags only; it does not select "
            "answers, use answer keys, or generate propositions."
        ),
        legibility=ChoiceStemBindingLegibilityRecord(),
        anti_gaming=ChoiceStemBindingAntiGamingRecord(),
    )


def create_choice_stem_bindings_for_item(
    *,
    question_instruction_records: list[object] | None = None,
    choice_claim_records: list[object] | None = None,
    item_ref: str = "item",
) -> list[ChoiceStemBindingCandidate]:
    """Create candidates for safe parsed instruction/claim record pairs."""
    questions = [record for record in (question_instruction_records or []) if _record_statement_id(record)]
    choices = [record for record in (choice_claim_records or []) if _record_statement_id(record)]
    if not questions or not choices:
        return []
    created: list[ChoiceStemBindingCandidate] = []
    for q_index, question in enumerate(questions, start=1):
        q_id = _record_statement_id(question)
        q_markers = _markers_from_record(question)
        implied_relation_hint = next((marker for marker in q_markers if marker in _PREDICATE_FRAME_MARKERS), "")
        for c_index, claim in enumerate(choices, start=1):
            c_id = _record_statement_id(claim)
            if not q_id or not c_id:
                continue
            candidate = create_choice_stem_binding_candidate(
                binding_id=f"binding:{item_ref}:{q_index}:{c_index}",
                source_question_instruction_id=q_id,
                source_choice_statement_id=c_id,
                choice_role=_record_role(claim) or "choice_claim",
                question_instruction_markers=q_markers,
                choice_markers=_markers_from_record(claim),
                choice_has_relation_hint=_record_has_relation_hint(claim),
                choice_is_noun_phrase_like=_record_is_noun_phrase_like(claim),
                choice_is_full_claim_like=_record_is_full_claim_like(claim),
                implied_relation_hint=implied_relation_hint,
                confidence="medium" if _record_is_full_claim_like(claim) else "low",
            )
            if candidate.stem_binding_type != "unsupported_binding":
                created.append(candidate)
    return created


def summarize_choice_stem_binding_diagnostics(candidates: list[ChoiceStemBindingCandidate]) -> dict[str, Any]:
    """Summarize binding candidates with redacted counts only."""
    type_counts = {alias: 0 for alias in _BINDING_TYPE_ALIASES.values()}
    confidence_counts = {"low": 0, "medium": 0, "high": 0}
    unsupported_gap_count = 0
    anti_gaming_safe = True
    legibility_safe = True
    for candidate in candidates:
        type_counts[_BINDING_TYPE_ALIASES.get(candidate.stem_binding_type, "unsupported")] += 1
        if candidate.confidence in confidence_counts:
            confidence_counts[candidate.confidence] += 1
        unsupported_gap_count += len(candidate.unsupported_gaps)
        findings = validate_choice_stem_binding_candidate(candidate)
        anti_gaming_safe = anti_gaming_safe and not any(
            finding in findings
            for finding in [
                "answer_key_use", "item_id_authority", "answer_position_bias",
                "raw_benchmark_text_storage_by_default", "benchmark_specific_tuning",
                "answer_selection_enabled", "official_score_claim",
            ]
        )
        legibility_safe = legibility_safe and not any(
            finding in findings for finding in ["hidden_unsupported_gaps", "private_symbolic_authority"]
        )
    return {
        "binding_candidate_count": len(candidates),
        "type_counts": type_counts,
        "low_confidence_count": confidence_counts["low"],
        "medium_confidence_count": confidence_counts["medium"],
        "high_confidence_count": confidence_counts["high"],
        "unsupported_gap_count": unsupported_gap_count,
        "anti_gaming_safe": anti_gaming_safe,
        "legibility_safe": legibility_safe,
    }
