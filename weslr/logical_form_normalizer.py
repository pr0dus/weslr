from __future__ import annotations

import hashlib
import re
import string
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class NormalizedTerm:
    term_id: str
    source_statement_ids: list[str] = field(default_factory=list)
    canonical_form: str = ""
    surface_fingerprints: list[str] = field(default_factory=list)
    term_type: str = ""
    confidence: str = "low"
    normalization_method: str = ""
    human_translation: str = ""


@dataclass
class NormalizedPredicate:
    predicate_id: str
    source_statement_ids: list[str] = field(default_factory=list)
    subject_term_id: str = ""
    relation: str = ""
    object_term_id: str = ""
    polarity: str = "positive"
    quantifier: str = ""
    modality: str = ""
    confidence: str = "low"
    human_translation: str = ""


@dataclass
class TermAlignmentRecord:
    alignment_id: str
    left_term_id: str
    right_term_id: str
    alignment_type: str = ""
    confidence: str = "low"
    evidence_fingerprints: list[str] = field(default_factory=list)
    human_explanation: str = ""


@dataclass
class NormalizationWarning:
    warning_id: str
    warning_type: str = ""
    severity: str = "low"
    source_statement_ids: list[str] = field(default_factory=list)
    human_explanation: str = ""


@dataclass
class NormalizationLegibilityRecord:
    human_explanation_available: bool = True
    normalization_warrants_available: bool = True
    unsupported_gaps_visible: bool = True
    private_symbolic_authority_used: bool = False


@dataclass
class NormalizationAntiGamingRecord:
    uses_answer_key: bool = False
    uses_item_id: bool = False
    uses_answer_position_bias: bool = False
    stores_raw_text_by_default: bool = False
    official_score_claimed: bool = False
    benchmark_specific_rule_used: bool = False


@dataclass
class AtomicTermCandidate:
    candidate_id: str = ""
    source_statement_id: str = ""
    source_statement_role: str = ""
    safe_origin_type: str = "unknown"
    token_fingerprints: list[str] = field(default_factory=list)
    canonical_hint: str = ""
    term_type_hint: str = ""
    confidence: str = "low"
    extraction_method: str = ""
    human_explanation: str = ""


@dataclass
class PredicateCandidate:
    predicate_candidate_id: str = ""
    source_statement_id: str = ""
    subject_candidate_id: str = ""
    relation_hint: str = ""
    object_candidate_id: str = ""
    polarity: str = "positive"
    quantifier_hint: str = ""
    modality_hint: str = ""
    confidence: str = "low"
    decomposition_method: str = ""
    human_explanation: str = ""


@dataclass
class RoleAwareTermIndex:
    index_id: str = ""
    source_parse_id: str = ""
    source_task_id: str = ""
    premise_term_candidate_ids: list[str] = field(default_factory=list)
    candidate_term_candidate_ids: list[str] = field(default_factory=list)
    background_term_candidate_ids: list[str] = field(default_factory=list)
    unsupported_term_candidate_ids: list[str] = field(default_factory=list)
    confidence: str = "low"
    human_explanation: str = ""


@dataclass
class AlignmentEvidenceRecord:
    evidence_id: str = ""
    left_candidate_id: str = ""
    right_candidate_id: str = ""
    evidence_type: str = ""
    evidence_fingerprints: list[str] = field(default_factory=list)
    confidence: str = "low"
    human_explanation: str = ""


@dataclass
class NormalizerDiagnosticSummary:
    summary_id: str = ""
    source_report_id: str = ""
    suite_count: int = 0
    item_count: int = 0
    atomic_term_candidate_count: int = 0
    predicate_candidate_count: int = 0
    role_index_count: int = 0
    alignment_evidence_count: int = 0
    unsupported_gap_count: int = 0
    items_with_alignment: int = 0
    anti_gaming_safe: bool = True
    legibility_safe: bool = True
    official_score_claimed: bool = False
    human_explanation: str = ""


@dataclass
class NormalizedLogicalForm:
    schema_version: str = "1.0"
    normalization_id: str = ""
    source_parse_id: str = ""
    source_task_id: str = ""
    normalized_terms: list[NormalizedTerm] = field(default_factory=list)
    normalized_predicates: list[NormalizedPredicate] = field(default_factory=list)
    term_alignments: list[TermAlignmentRecord] = field(default_factory=list)
    warnings: list[NormalizationWarning] = field(default_factory=list)
    unsupported_normalization_gaps: list[NormalizationWarning] = field(default_factory=list)
    atomic_term_candidates: list[AtomicTermCandidate] = field(default_factory=list)
    predicate_candidates: list[PredicateCandidate] = field(default_factory=list)
    role_aware_indexes: list[RoleAwareTermIndex] = field(default_factory=list)
    alignment_evidence: list[AlignmentEvidenceRecord] = field(default_factory=list)
    diagnostic_summaries: list[NormalizerDiagnosticSummary] = field(default_factory=list)
    legibility: NormalizationLegibilityRecord = field(default_factory=NormalizationLegibilityRecord)
    anti_gaming: NormalizationAntiGamingRecord = field(default_factory=NormalizationAntiGamingRecord)
    confidence: str = "low"


def create_empty_normalized_logical_form(
    *,
    normalization_id: str = "",
    source_parse_id: str = "",
    source_task_id: str = "",
    schema_version: str = "1.0",
) -> NormalizedLogicalForm:
    return NormalizedLogicalForm(
        schema_version=schema_version,
        normalization_id=normalization_id,
        source_parse_id=source_parse_id,
        source_task_id=source_task_id,
    )


def normalized_logical_form_to_dict(form: NormalizedLogicalForm) -> dict[str, Any]:
    return asdict(form)


def normalized_logical_form_from_dict(data: dict[str, Any]) -> NormalizedLogicalForm:
    return NormalizedLogicalForm(
        schema_version=data.get("schema_version", "1.0"),
        normalization_id=data.get("normalization_id", ""),
        source_parse_id=data.get("source_parse_id", ""),
        source_task_id=data.get("source_task_id", ""),
        normalized_terms=[NormalizedTerm(**item) for item in data.get("normalized_terms", [])],
        normalized_predicates=[NormalizedPredicate(**item) for item in data.get("normalized_predicates", [])],
        term_alignments=[TermAlignmentRecord(**item) for item in data.get("term_alignments", [])],
        warnings=[NormalizationWarning(**item) for item in data.get("warnings", [])],
        unsupported_normalization_gaps=[NormalizationWarning(**item) for item in data.get("unsupported_normalization_gaps", [])],
        atomic_term_candidates=[AtomicTermCandidate(**item) for item in data.get("atomic_term_candidates", [])],
        predicate_candidates=[PredicateCandidate(**item) for item in data.get("predicate_candidates", [])],
        role_aware_indexes=[RoleAwareTermIndex(**item) for item in data.get("role_aware_indexes", [])],
        alignment_evidence=[AlignmentEvidenceRecord(**item) for item in data.get("alignment_evidence", [])],
        diagnostic_summaries=[NormalizerDiagnosticSummary(**item) for item in data.get("diagnostic_summaries", [])],
        legibility=NormalizationLegibilityRecord(**data.get("legibility", {})),
        anti_gaming=NormalizationAntiGamingRecord(**data.get("anti_gaming", {})),
        confidence=data.get("confidence", "low"),
    )


def validate_normalized_logical_form(form: NormalizedLogicalForm) -> list[str]:
    messages: list[str] = []
    anti = form.anti_gaming
    legibility = form.legibility

    if anti.official_score_claimed:
        messages.append("official_score_claimed must remain False")
    if anti.uses_answer_key:
        messages.append("uses_answer_key must remain False")
    if anti.uses_item_id:
        messages.append("uses_item_id must remain False")
    if anti.uses_answer_position_bias:
        messages.append("uses_answer_position_bias must remain False")
    if anti.stores_raw_text_by_default:
        messages.append("stores_raw_text_by_default must remain False")
    if anti.benchmark_specific_rule_used:
        messages.append("benchmark_specific_rule_used must remain False")
    if legibility.private_symbolic_authority_used:
        messages.append("private_symbolic_authority_used must remain False")
    if not legibility.human_explanation_available:
        messages.append("human_explanation_available must remain True")
    if not legibility.normalization_warrants_available:
        messages.append("normalization_warrants_available must remain True")
    if not legibility.unsupported_gaps_visible:
        messages.append("unsupported_gaps_visible must remain True")
    if not form.normalization_id:
        messages.append("normalization_id is required")
    if not form.source_task_id:
        messages.append("source_task_id is required")
    if not form.source_parse_id:
        messages.append("source_parse_id is required")

    term_ids = {term.term_id for term in form.normalized_terms}
    for predicate in form.normalized_predicates:
        if predicate.subject_term_id not in term_ids:
            messages.append(
                f"predicate {predicate.predicate_id} references missing subject_term_id {predicate.subject_term_id}"
            )
        if predicate.object_term_id not in term_ids:
            messages.append(
                f"predicate {predicate.predicate_id} references missing object_term_id {predicate.object_term_id}"
            )
    for alignment in form.term_alignments:
        if alignment.left_term_id not in term_ids:
            messages.append(
                f"alignment {alignment.alignment_id} references missing left_term_id {alignment.left_term_id}"
            )
        if alignment.right_term_id not in term_ids:
            messages.append(
                f"alignment {alignment.alignment_id} references missing right_term_id {alignment.right_term_id}"
            )
    for warning in [*form.warnings, *form.unsupported_normalization_gaps]:
        if not warning.human_explanation:
            messages.append(f"warning {warning.warning_id} must include human_explanation")

    atomic_candidate_ids = {candidate.candidate_id for candidate in form.atomic_term_candidates if candidate.candidate_id}
    for candidate in form.atomic_term_candidates:
        if not candidate.candidate_id:
            messages.append("AtomicTermCandidate missing candidate_id")
        if not candidate.human_explanation:
            messages.append(f"AtomicTermCandidate {candidate.candidate_id or '<missing>'} must include human_explanation")
    for candidate in form.predicate_candidates:
        if not candidate.predicate_candidate_id:
            messages.append("PredicateCandidate missing predicate_candidate_id")
        if candidate.subject_candidate_id and candidate.subject_candidate_id not in atomic_candidate_ids:
            messages.append(
                f"PredicateCandidate {candidate.predicate_candidate_id or '<missing>'} references missing subject_candidate_id {candidate.subject_candidate_id}"
            )
        if candidate.object_candidate_id and candidate.object_candidate_id not in atomic_candidate_ids:
            messages.append(
                f"PredicateCandidate {candidate.predicate_candidate_id or '<missing>'} references missing object_candidate_id {candidate.object_candidate_id}"
            )
    for index in form.role_aware_indexes:
        for candidate_id in [
            *index.premise_term_candidate_ids,
            *index.candidate_term_candidate_ids,
            *index.background_term_candidate_ids,
            *index.unsupported_term_candidate_ids,
        ]:
            if candidate_id not in atomic_candidate_ids:
                messages.append(
                    f"RoleAwareTermIndex {index.index_id or '<missing>'} references missing atomic term candidate {candidate_id}"
                )
    for evidence in form.alignment_evidence:
        if evidence.left_candidate_id and evidence.left_candidate_id not in atomic_candidate_ids:
            messages.append(
                f"AlignmentEvidenceRecord {evidence.evidence_id or '<missing>'} references missing left_candidate_id {evidence.left_candidate_id}"
            )
        if evidence.right_candidate_id and evidence.right_candidate_id not in atomic_candidate_ids:
            messages.append(
                f"AlignmentEvidenceRecord {evidence.evidence_id or '<missing>'} references missing right_candidate_id {evidence.right_candidate_id}"
            )
        if not evidence.human_explanation:
            messages.append(f"AlignmentEvidenceRecord {evidence.evidence_id or '<missing>'} must include human_explanation")
    for summary in form.diagnostic_summaries:
        if summary.official_score_claimed:
            messages.append(f"NormalizerDiagnosticSummary {summary.summary_id or '<missing>'} official_score_claimed must remain False")
        if not summary.human_explanation:
            messages.append(f"NormalizerDiagnosticSummary {summary.summary_id or '<missing>'} must include human_explanation")

    return messages


def add_normalized_term(
    form: NormalizedLogicalForm,
    *,
    term_id: str,
    source_statement_ids: list[str] | None = None,
    canonical_form: str = "",
    surface_fingerprints: list[str] | None = None,
    term_type: str = "",
    confidence: str = "low",
    normalization_method: str = "",
    human_translation: str = "",
) -> NormalizedTerm:
    term = NormalizedTerm(
        term_id=term_id,
        source_statement_ids=list(source_statement_ids or []),
        canonical_form=canonical_form,
        surface_fingerprints=list(surface_fingerprints or []),
        term_type=term_type,
        confidence=confidence,
        normalization_method=normalization_method,
        human_translation=human_translation,
    )
    form.normalized_terms.append(term)
    return term


def add_normalized_predicate(
    form: NormalizedLogicalForm,
    *,
    predicate_id: str,
    source_statement_ids: list[str] | None = None,
    subject_term_id: str,
    relation: str = "",
    object_term_id: str,
    polarity: str = "positive",
    quantifier: str = "",
    modality: str = "",
    confidence: str = "low",
    human_translation: str = "",
) -> NormalizedPredicate:
    predicate = NormalizedPredicate(
        predicate_id=predicate_id,
        source_statement_ids=list(source_statement_ids or []),
        subject_term_id=subject_term_id,
        relation=relation,
        object_term_id=object_term_id,
        polarity=polarity,
        quantifier=quantifier,
        modality=modality,
        confidence=confidence,
        human_translation=human_translation,
    )
    form.normalized_predicates.append(predicate)
    return predicate


def add_term_alignment(
    form: NormalizedLogicalForm,
    *,
    alignment_id: str,
    left_term_id: str,
    right_term_id: str,
    alignment_type: str = "",
    confidence: str = "low",
    evidence_fingerprints: list[str] | None = None,
    human_explanation: str = "",
) -> TermAlignmentRecord:
    alignment = TermAlignmentRecord(
        alignment_id=alignment_id,
        left_term_id=left_term_id,
        right_term_id=right_term_id,
        alignment_type=alignment_type,
        confidence=confidence,
        evidence_fingerprints=list(evidence_fingerprints or []),
        human_explanation=human_explanation,
    )
    form.term_alignments.append(alignment)
    return alignment


def add_normalization_warning(
    form: NormalizedLogicalForm,
    *,
    warning_id: str,
    warning_type: str = "",
    severity: str = "low",
    source_statement_ids: list[str] | None = None,
    human_explanation: str = "",
    unsupported_gap: bool = False,
) -> NormalizationWarning:
    warning = NormalizationWarning(
        warning_id=warning_id,
        warning_type=warning_type,
        severity=severity,
        source_statement_ids=list(source_statement_ids or []),
        human_explanation=human_explanation,
    )
    if unsupported_gap:
        form.unsupported_normalization_gaps.append(warning)
    else:
        form.warnings.append(warning)
    return warning


def add_atomic_term_candidate(
    form: NormalizedLogicalForm,
    *,
    candidate_id: str,
    source_statement_id: str = "",
    source_statement_role: str = "",
    safe_origin_type: str = "unknown",
    token_fingerprints: list[str] | None = None,
    canonical_hint: str = "",
    term_type_hint: str = "",
    confidence: str = "low",
    extraction_method: str = "",
    human_explanation: str = "",
) -> AtomicTermCandidate:
    candidate = AtomicTermCandidate(
        candidate_id=candidate_id,
        source_statement_id=source_statement_id,
        source_statement_role=source_statement_role,
        safe_origin_type=safe_origin_type,
        token_fingerprints=list(token_fingerprints or []),
        canonical_hint=canonical_hint,
        term_type_hint=term_type_hint,
        confidence=confidence,
        extraction_method=extraction_method,
        human_explanation=human_explanation,
    )
    form.atomic_term_candidates.append(candidate)
    return candidate


def add_predicate_candidate(
    form: NormalizedLogicalForm,
    *,
    predicate_candidate_id: str,
    source_statement_id: str = "",
    subject_candidate_id: str = "",
    relation_hint: str = "",
    object_candidate_id: str = "",
    polarity: str = "positive",
    quantifier_hint: str = "",
    modality_hint: str = "",
    confidence: str = "low",
    decomposition_method: str = "",
    human_explanation: str = "",
) -> PredicateCandidate:
    candidate = PredicateCandidate(
        predicate_candidate_id=predicate_candidate_id,
        source_statement_id=source_statement_id,
        subject_candidate_id=subject_candidate_id,
        relation_hint=relation_hint,
        object_candidate_id=object_candidate_id,
        polarity=polarity,
        quantifier_hint=quantifier_hint,
        modality_hint=modality_hint,
        confidence=confidence,
        decomposition_method=decomposition_method,
        human_explanation=human_explanation,
    )
    form.predicate_candidates.append(candidate)
    return candidate


def add_role_aware_term_index(
    form: NormalizedLogicalForm,
    *,
    index_id: str,
    source_parse_id: str = "",
    source_task_id: str = "",
    premise_term_candidate_ids: list[str] | None = None,
    candidate_term_candidate_ids: list[str] | None = None,
    background_term_candidate_ids: list[str] | None = None,
    unsupported_term_candidate_ids: list[str] | None = None,
    confidence: str = "low",
    human_explanation: str = "",
) -> RoleAwareTermIndex:
    index = RoleAwareTermIndex(
        index_id=index_id,
        source_parse_id=source_parse_id,
        source_task_id=source_task_id,
        premise_term_candidate_ids=list(premise_term_candidate_ids or []),
        candidate_term_candidate_ids=list(candidate_term_candidate_ids or []),
        background_term_candidate_ids=list(background_term_candidate_ids or []),
        unsupported_term_candidate_ids=list(unsupported_term_candidate_ids or []),
        confidence=confidence,
        human_explanation=human_explanation,
    )
    form.role_aware_indexes.append(index)
    return index


def add_alignment_evidence_record(
    form: NormalizedLogicalForm,
    *,
    evidence_id: str,
    left_candidate_id: str = "",
    right_candidate_id: str = "",
    evidence_type: str = "",
    evidence_fingerprints: list[str] | None = None,
    confidence: str = "low",
    human_explanation: str = "",
) -> AlignmentEvidenceRecord:
    evidence = AlignmentEvidenceRecord(
        evidence_id=evidence_id,
        left_candidate_id=left_candidate_id,
        right_candidate_id=right_candidate_id,
        evidence_type=evidence_type,
        evidence_fingerprints=list(evidence_fingerprints or []),
        confidence=confidence,
        human_explanation=human_explanation,
    )
    form.alignment_evidence.append(evidence)
    return evidence


def add_normalizer_diagnostic_summary(
    form: NormalizedLogicalForm,
    *,
    summary_id: str,
    source_report_id: str = "",
    suite_count: int = 0,
    item_count: int = 0,
    atomic_term_candidate_count: int = 0,
    predicate_candidate_count: int = 0,
    role_index_count: int = 0,
    alignment_evidence_count: int = 0,
    unsupported_gap_count: int = 0,
    items_with_alignment: int = 0,
    anti_gaming_safe: bool = True,
    legibility_safe: bool = True,
    official_score_claimed: bool = False,
    human_explanation: str = "",
) -> NormalizerDiagnosticSummary:
    summary = NormalizerDiagnosticSummary(
        summary_id=summary_id,
        source_report_id=source_report_id,
        suite_count=suite_count,
        item_count=item_count,
        atomic_term_candidate_count=atomic_term_candidate_count,
        predicate_candidate_count=predicate_candidate_count,
        role_index_count=role_index_count,
        alignment_evidence_count=alignment_evidence_count,
        unsupported_gap_count=unsupported_gap_count,
        items_with_alignment=items_with_alignment,
        anti_gaming_safe=anti_gaming_safe,
        legibility_safe=legibility_safe,
        official_score_claimed=official_score_claimed,
        human_explanation=human_explanation,
    )
    form.diagnostic_summaries.append(summary)
    return summary


def fingerprint_surface(text: str) -> str:
    normalized = " ".join((text or "").strip().lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def normalize_term_surface(text: str) -> str:
    normalized = (text or "").strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.strip(string.punctuation + " ")
    normalized = re.sub(rf"^[{re.escape(string.punctuation)}]+|[{re.escape(string.punctuation)}]+$", "", normalized)
    if len(normalized) > 3 and normalized.endswith("s") and not normalized.endswith("ss"):
        normalized = normalized[:-1]
    return normalized


def normalize_relation_surface(text: str) -> str:
    normalized = normalize_term_surface(text)
    mapping = {
        "is": "is",
        "are": "is",
        "was": "is",
        "were": "is",
        "support": "supports",
        "supports": "supports",
        "oppose": "opposes",
        "opposes": "opposes",
        "require": "requires",
        "requires": "requires",
        "prevent": "prevents",
        "prevents": "prevents",
        "permit": "permits",
        "permits": "permits",
        "allow": "permits",
        "allows": "permits",
    }
    return mapping.get(normalized, normalized)


def infer_polarity(text: str) -> str:
    normalized = f" {normalize_term_surface(text)} "
    markers = [" not ", " no ", " never ", " none ", " is not ", " are not "]
    return "negative" if any(marker in normalized for marker in markers) else "positive"


def safe_candidate_term_id(label: str, index: int = 0) -> str:
    normalized = (label or "").strip()
    if len(normalized) == 1 and normalized in string.ascii_uppercase:
        return f"choice_{normalized}"
    return f"choice_{index}"


def create_normalized_term_from_surface(
    form: NormalizedLogicalForm,
    *,
    source_statement_ids: list[str] | None = None,
    surface: str,
    term_id: str | None = None,
    term_type: str = "concept",
    confidence: str = "low",
    normalization_method: str = "surface_normalization",
) -> NormalizedTerm:
    canonical_form = normalize_term_surface(surface)
    safe_term_id = term_id or canonical_form or f"term_{len(form.normalized_terms)}"
    fingerprint = fingerprint_surface(surface)
    human_translation = canonical_form
    return add_normalized_term(
        form,
        term_id=safe_term_id,
        source_statement_ids=source_statement_ids,
        canonical_form=canonical_form,
        surface_fingerprints=[fingerprint],
        term_type=term_type,
        confidence=confidence,
        normalization_method=normalization_method,
        human_translation=human_translation,
    )


def align_terms_by_canonical_form(
    form: NormalizedLogicalForm,
    *,
    min_confidence: str = "low",
) -> list[TermAlignmentRecord]:
    created: list[TermAlignmentRecord] = []
    seen_pairs = {
        tuple(sorted((alignment.left_term_id, alignment.right_term_id)))
        for alignment in form.term_alignments
    }
    for i, left in enumerate(form.normalized_terms):
        for right in form.normalized_terms[i + 1 :]:
            if left.term_id == right.term_id:
                continue
            if not left.canonical_form or left.canonical_form != right.canonical_form:
                continue
            pair = tuple(sorted((left.term_id, right.term_id)))
            if pair in seen_pairs:
                continue
            evidence = list(dict.fromkeys([*left.surface_fingerprints, *right.surface_fingerprints]))
            alignment = add_term_alignment(
                form,
                alignment_id=f"align:{left.term_id}:{right.term_id}",
                left_term_id=left.term_id,
                right_term_id=right.term_id,
                alignment_type="canonical_match",
                confidence=min_confidence,
                evidence_fingerprints=evidence,
                human_explanation="Terms share identical canonical form after safe normalization.",
            )
            created.append(alignment)
            seen_pairs.add(pair)
    return created


def summarize_term_alignment_gaps(form: NormalizedLogicalForm) -> dict[str, Any]:
    canonical_counts: dict[str, int] = {}
    for term in form.normalized_terms:
        if term.canonical_form:
            canonical_counts[term.canonical_form] = canonical_counts.get(term.canonical_form, 0) + 1
    aligned_ids = {a.left_term_id for a in form.term_alignments} | {a.right_term_id for a in form.term_alignments}
    return {
        "term_count": len(form.normalized_terms),
        "unique_canonical_term_count": len(canonical_counts),
        "alignment_count": len(form.term_alignments),
        "unaligned_term_count": sum(1 for term in form.normalized_terms if term.term_id not in aligned_ids),
        "warning_count": len(form.warnings),
        "unsupported_gap_count": len(form.unsupported_normalization_gaps),
    }


def summarize_normalized_logical_form(form: NormalizedLogicalForm) -> dict[str, Any]:
    anti = form.anti_gaming
    legibility = form.legibility
    return {
        "schema_version": form.schema_version,
        "normalization_id": form.normalization_id,
        "source_parse_id": form.source_parse_id,
        "source_task_id": form.source_task_id,
        "term_count": len(form.normalized_terms),
        "predicate_count": len(form.normalized_predicates),
        "alignment_count": len(form.term_alignments),
        "warning_count": len(form.warnings),
        "unsupported_gap_count": len(form.unsupported_normalization_gaps),
        "atomic_term_candidate_count": len(form.atomic_term_candidates),
        "predicate_candidate_count": len(form.predicate_candidates),
        "role_index_count": len(form.role_aware_indexes),
        "alignment_evidence_count": len(form.alignment_evidence),
        "diagnostic_summary_count": len(form.diagnostic_summaries),
        "confidence": form.confidence,
        "anti_gaming_safe": not any(
            [
                anti.uses_answer_key,
                anti.uses_item_id,
                anti.uses_answer_position_bias,
                anti.stores_raw_text_by_default,
                anti.official_score_claimed,
                anti.benchmark_specific_rule_used,
            ]
        ),
        "legibility_safe": all(
            [
                legibility.human_explanation_available,
                legibility.normalization_warrants_available,
                legibility.unsupported_gaps_visible,
                not legibility.private_symbolic_authority_used,
            ]
        ),
    }
