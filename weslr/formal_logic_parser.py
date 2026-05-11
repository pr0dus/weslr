from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ParsedStatement:
    statement_id: str = ""
    raw_text_runtime_only: str = ""
    text_fingerprint: str = ""
    normalized_text: str = ""
    role: str = ""
    logical_form: str = ""
    confidence: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class LogicalOperatorRecord:
    record_id: str = ""
    operator_type: str = ""
    source_statement_ids: list[str] = field(default_factory=list)
    normalized_form: str = ""
    confidence: str = ""
    human_translation: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class QuantifierRecord:
    record_id: str = ""
    quantifier_type: str = ""
    source_statement_ids: list[str] = field(default_factory=list)
    normalized_form: str = ""
    confidence: str = ""
    human_translation: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class ConditionalRecord:
    record_id: str = ""
    antecedent: str = ""
    consequent: str = ""
    conditional_type: str = ""
    source_statement_ids: list[str] = field(default_factory=list)
    normalized_form: str = ""
    confidence: str = ""
    human_translation: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class NegationRecord:
    record_id: str = ""
    negation_type: str = ""
    source_statement_ids: list[str] = field(default_factory=list)
    normalized_form: str = ""
    confidence: str = ""
    human_translation: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class DisjunctionRecord:
    record_id: str = ""
    alternatives: list[str] = field(default_factory=list)
    exhaustive: bool = False
    exclusive: bool = False
    source_statement_ids: list[str] = field(default_factory=list)
    normalized_form: str = ""
    confidence: str = ""
    human_translation: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class ConjunctionRecord:
    record_id: str = ""
    conjunction_type: str = ""
    source_statement_ids: list[str] = field(default_factory=list)
    normalized_form: str = ""
    confidence: str = ""
    human_translation: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class ParserWarningRecord:
    record_id: str = ""
    warning_type: str = ""
    source_statement_ids: list[str] = field(default_factory=list)
    normalized_form: str = ""
    confidence: str = ""
    human_translation: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class UnsupportedFragmentRecord:
    record_id: str = ""
    fragment_type: str = ""
    source_statement_ids: list[str] = field(default_factory=list)
    normalized_form: str = ""
    confidence: str = ""
    human_translation: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class ParserAntiGamingRecord:
    uses_answer_key: bool = False
    uses_item_id: bool = False
    uses_answer_position_bias: bool = False
    stores_raw_text_by_default: bool = False
    official_score_claimed: bool = False
    benchmark_specific_rule_used: bool = False


@dataclass
class ParserLegibilityRecord:
    symbolic_forms_translated: bool = True
    unsupported_fragments_visible: bool = True
    private_symbolic_authority_used: bool = False
    human_translation_available: bool = True


@dataclass
class LogicalFormParse:
    parse_id: str
    source_task_id: str
    statements: list[ParsedStatement] = field(default_factory=list)
    premises: list[str] = field(default_factory=list)
    candidate_conclusions: list[str] = field(default_factory=list)
    operators: list[LogicalOperatorRecord] = field(default_factory=list)
    quantifiers: list[QuantifierRecord] = field(default_factory=list)
    conditionals: list[ConditionalRecord] = field(default_factory=list)
    negations: list[NegationRecord] = field(default_factory=list)
    disjunctions: list[DisjunctionRecord] = field(default_factory=list)
    conjunctions: list[ConjunctionRecord] = field(default_factory=list)
    exceptions: list[str] = field(default_factory=list)
    modality: list[str] = field(default_factory=list)
    normalized_terms: list[str] = field(default_factory=list)
    parse_confidence: str = ""
    parse_warnings: list[ParserWarningRecord] = field(default_factory=list)
    unsupported_fragments: list[UnsupportedFragmentRecord] = field(default_factory=list)
    human_translation: str = ""
    anti_gaming: ParserAntiGamingRecord = field(default_factory=ParserAntiGamingRecord)
    legibility: ParserLegibilityRecord = field(default_factory=ParserLegibilityRecord)


_LOGICAL_MARKER_RE = re.compile(
    r"\b(unless|either|or|and|not|no|none|never|all|every|some|therefore|so|hence|follows|must be true|which follows)\b",
    re.I,
)


def fingerprint_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_candidate_statements(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    parts = re.split(r"[.;\n]+", normalized)
    return [part.strip() for part in parts if part.strip()]


def normalize_logical_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def detect_statement_role(statement: str) -> str:
    lowered = normalize_logical_text(statement)
    if not lowered:
        return "background"
    if "must be true" in lowered or "which follows" in lowered:
        return "question_instruction"
    if re.search(r"\?$", statement.strip()) or lowered.startswith(("which", "what", "determine", "identify", "select")):
        return "question_instruction"
    if any(marker in lowered for marker in ["therefore", "hence", " so ", "follows"]):
        if "which follows" in lowered or "follows that" in lowered or lowered.startswith("what follows"):
            return "question_instruction"
        return "conclusion_candidate"
    if _LOGICAL_MARKER_RE.search(lowered):
        return "premise"
    return "background"


def create_empty_logical_form_parse(*, parse_id: str = "", source_task_id: str = "") -> LogicalFormParse:
    return LogicalFormParse(parse_id=parse_id, source_task_id=source_task_id)


def logical_form_parse_to_dict(parse: LogicalFormParse) -> dict[str, Any]:
    return asdict(parse)


def logical_form_parse_from_dict(data: dict[str, Any]) -> LogicalFormParse:
    return LogicalFormParse(
        parse_id=data.get("parse_id", ""),
        source_task_id=data.get("source_task_id", ""),
        statements=[ParsedStatement(**item) for item in data.get("statements", [])],
        premises=list(data.get("premises", [])),
        candidate_conclusions=list(data.get("candidate_conclusions", [])),
        operators=[LogicalOperatorRecord(**item) for item in data.get("operators", [])],
        quantifiers=[QuantifierRecord(**item) for item in data.get("quantifiers", [])],
        conditionals=[ConditionalRecord(**item) for item in data.get("conditionals", [])],
        negations=[NegationRecord(**item) for item in data.get("negations", [])],
        disjunctions=[DisjunctionRecord(**item) for item in data.get("disjunctions", [])],
        conjunctions=[ConjunctionRecord(**item) for item in data.get("conjunctions", [])],
        exceptions=list(data.get("exceptions", [])),
        modality=list(data.get("modality", [])),
        normalized_terms=list(data.get("normalized_terms", [])),
        parse_confidence=data.get("parse_confidence", ""),
        parse_warnings=[ParserWarningRecord(**item) for item in data.get("parse_warnings", [])],
        unsupported_fragments=[UnsupportedFragmentRecord(**item) for item in data.get("unsupported_fragments", [])],
        human_translation=data.get("human_translation", ""),
        anti_gaming=ParserAntiGamingRecord(**data.get("anti_gaming", {})),
        legibility=ParserLegibilityRecord(**data.get("legibility", {})),
    )


def validate_logical_form_parse(parse: LogicalFormParse) -> list[str]:
    messages: list[str] = []
    anti = parse.anti_gaming
    legibility = parse.legibility

    if not parse.parse_id:
        messages.append("missing parse_id")
    if not parse.source_task_id:
        messages.append("missing source_task_id")

    if anti.official_score_claimed:
        messages.append("official_score_claimed true is not allowed")
    if anti.uses_answer_key:
        messages.append("uses_answer_key true is not allowed")
    if anti.uses_item_id:
        messages.append("uses_item_id true is not allowed")
    if anti.uses_answer_position_bias:
        messages.append("uses_answer_position_bias true is not allowed")
    if anti.stores_raw_text_by_default:
        messages.append("stores_raw_text_by_default true is not allowed")
    if anti.benchmark_specific_rule_used:
        messages.append("benchmark_specific_rule_used true is not allowed")

    if legibility.private_symbolic_authority_used:
        messages.append("private_symbolic_authority_used true is not allowed")
    if not legibility.symbolic_forms_translated:
        messages.append("symbolic_forms_translated false is not allowed")
    if not legibility.unsupported_fragments_visible:
        messages.append("unsupported_fragments_visible false is not allowed")

    if anti.stores_raw_text_by_default and any(statement.raw_text_runtime_only for statement in parse.statements):
        messages.append("raw_text_runtime_only populated while stores_raw_text_by_default true")

    if parse.parse_confidence == "high" and not parse.human_translation.strip():
        messages.append("high-confidence parse missing human_translation")

    return messages


def add_parsed_statement(
    parse: LogicalFormParse,
    *,
    statement_id: str,
    raw_text_runtime_only: str = "",
    text_fingerprint: str = "",
    normalized_text: str = "",
    role: str = "",
    logical_form: str = "",
    confidence: str = "",
    warnings: list[str] | None = None,
) -> ParsedStatement:
    statement = ParsedStatement(
        statement_id=statement_id,
        raw_text_runtime_only=raw_text_runtime_only,
        text_fingerprint=text_fingerprint,
        normalized_text=normalized_text,
        role=role,
        logical_form=logical_form,
        confidence=confidence,
        warnings=list(warnings or []),
    )
    parse.statements.append(statement)
    return statement


def add_unsupported_fragment(
    parse: LogicalFormParse,
    *,
    record_id: str,
    fragment_type: str,
    source_statement_ids: list[str] | None = None,
    normalized_form: str = "",
    confidence: str = "",
    human_translation: str = "",
    warnings: list[str] | None = None,
) -> UnsupportedFragmentRecord:
    fragment = UnsupportedFragmentRecord(
        record_id=record_id,
        fragment_type=fragment_type,
        source_statement_ids=list(source_statement_ids or []),
        normalized_form=normalized_form,
        confidence=confidence,
        human_translation=human_translation,
        warnings=list(warnings or []),
    )
    parse.unsupported_fragments.append(fragment)
    return fragment


def add_parser_warning(
    parse: LogicalFormParse,
    *,
    record_id: str,
    warning_type: str,
    source_statement_ids: list[str] | None = None,
    normalized_form: str = "",
    confidence: str = "",
    human_translation: str = "",
    warnings: list[str] | None = None,
) -> ParserWarningRecord:
    warning = ParserWarningRecord(
        record_id=record_id,
        warning_type=warning_type,
        source_statement_ids=list(source_statement_ids or []),
        normalized_form=normalized_form,
        confidence=confidence,
        human_translation=human_translation,
        warnings=list(warnings or []),
    )
    parse.parse_warnings.append(warning)
    return warning


def _extract_unless_parts(normalized: str) -> tuple[str, str] | None:
    match = re.search(r"^(.*?)\s+unless\s+(.*?)$", normalized)
    if not match:
        return None
    main = match.group(1).strip(" ?")
    exception = match.group(2).strip(" ?")
    if not main or not exception:
        return None
    return exception, main


def _contains_obvious_logical_marker(normalized: str) -> bool:
    return bool(_LOGICAL_MARKER_RE.search(normalized))


def parse_runtime_text_to_logical_form(
    text: str,
    *,
    parse_id: str,
    source_task_id: str,
    store_raw_text: bool = False,
) -> LogicalFormParse:
    parse = create_empty_logical_form_parse(parse_id=parse_id, source_task_id=source_task_id)
    fragments = split_candidate_statements(text)
    any_marker = False

    for idx, fragment in enumerate(fragments, start=1):
        normalized = normalize_logical_text(fragment)
        statement_id = f"stmt_{idx}"
        role = detect_statement_role(fragment)
        has_marker = _contains_obvious_logical_marker(normalized)
        if has_marker:
            any_marker = True

        statement = add_parsed_statement(
            parse,
            statement_id=statement_id,
            raw_text_runtime_only=fragment if store_raw_text else "",
            text_fingerprint=fingerprint_text(fragment),
            normalized_text=normalized,
            role=role,
            logical_form=normalized,
            confidence="medium" if has_marker else "low",
        )

        parse.normalized_terms.extend([token for token in re.findall(r"[a-z0-9]+", normalized) if token not in parse.normalized_terms])

        if role == "premise":
            parse.premises.append(statement.statement_id)
        elif role == "conclusion_candidate":
            parse.candidate_conclusions.append(statement.statement_id)

        if "unless" in normalized:
            parts = _extract_unless_parts(normalized)
            if parts:
                exception, main = parts
                normalized_form = f"if not {exception} then {main}"
                parse.conditionals.append(
                    ConditionalRecord(
                        record_id=f"cond_{idx}",
                        antecedent=f"not {exception}",
                        consequent=main,
                        conditional_type="unless_translation",
                        source_statement_ids=[statement_id],
                        normalized_form=normalized_form,
                        confidence="medium",
                        human_translation="Unless is translated conservatively as if the exception does not hold, the main claim holds.",
                    )
                )
                parse.operators.append(
                    LogicalOperatorRecord(
                        record_id=f"op_cond_{idx}",
                        operator_type="conditional",
                        source_statement_ids=[statement_id],
                        normalized_form=normalized_form,
                        confidence="medium",
                        human_translation="Conditional structure detected from unless phrasing.",
                    )
                )
                parse.exceptions.append(exception)

        if " or " in f" {normalized} ":
            alternatives = [part.strip() for part in re.split(r"\bor\b", normalized) if part.strip()]
            parse.disjunctions.append(
                DisjunctionRecord(
                    record_id=f"disj_{idx}",
                    alternatives=alternatives,
                    exhaustive="either" in normalized or "at least one" in normalized,
                    exclusive="either" in normalized,
                    source_statement_ids=[statement_id],
                    normalized_form=normalized,
                    confidence="medium",
                    human_translation="Disjunctive structure detected; case analysis may be required.",
                )
            )
            parse.operators.append(
                LogicalOperatorRecord(
                    record_id=f"op_disj_{idx}",
                    operator_type="disjunction",
                    source_statement_ids=[statement_id],
                    normalized_form=normalized,
                    confidence="medium",
                    human_translation="Disjunction detected from ordinary language.",
                )
            )

        if " and " in f" {normalized} ":
            parse.conjunctions.append(
                ConjunctionRecord(
                    record_id=f"conj_{idx}",
                    conjunction_type="and",
                    source_statement_ids=[statement_id],
                    normalized_form=normalized,
                    confidence="medium",
                    human_translation="Conjunctive structure detected from ordinary language.",
                )
            )
            parse.operators.append(
                LogicalOperatorRecord(
                    record_id=f"op_conj_{idx}",
                    operator_type="conjunction",
                    source_statement_ids=[statement_id],
                    normalized_form=normalized,
                    confidence="medium",
                    human_translation="Conjunction detected from ordinary language.",
                )
            )

        if re.search(r"\b(not|no|none|never)\b", normalized):
            parse.negations.append(
                NegationRecord(
                    record_id=f"neg_{idx}",
                    negation_type="explicit_negation",
                    source_statement_ids=[statement_id],
                    normalized_form=normalized,
                    confidence="medium",
                    human_translation="Explicit negation detected from ordinary language.",
                )
            )
            parse.operators.append(
                LogicalOperatorRecord(
                    record_id=f"op_neg_{idx}",
                    operator_type="negation",
                    source_statement_ids=[statement_id],
                    normalized_form=normalized,
                    confidence="medium",
                    human_translation="Negation detected from ordinary language.",
                )
            )

        quantifier_match = re.search(r"\b(all|every|some|no)\b", normalized)
        if quantifier_match:
            parse.quantifiers.append(
                QuantifierRecord(
                    record_id=f"quant_{idx}",
                    quantifier_type=quantifier_match.group(1),
                    source_statement_ids=[statement_id],
                    normalized_form=normalized,
                    confidence="medium",
                    human_translation="Quantifier detected from ordinary language.",
                )
            )
            parse.operators.append(
                LogicalOperatorRecord(
                    record_id=f"op_quant_{idx}",
                    operator_type="quantifier",
                    source_statement_ids=[statement_id],
                    normalized_form=normalized,
                    confidence="medium",
                    human_translation="Quantifier structure detected from ordinary language.",
                )
            )

        if not has_marker:
            add_unsupported_fragment(
                parse,
                record_id=f"unsupported_{idx}",
                fragment_type="natural_language_fragment",
                source_statement_ids=[statement_id],
                normalized_form=normalized,
                confidence="low",
                human_translation="No obvious logical marker was detected, so this fragment remains visible as unsupported.",
            )

    parse.parse_confidence = "medium" if any_marker else "low"
    parse.human_translation = (
        "Preliminary natural-language logical-form extraction only. "
        "This parse records visible structure without selecting answers or asserting truth."
    )
    parse.anti_gaming.stores_raw_text_by_default = False
    parse.anti_gaming.official_score_claimed = False
    parse.legibility.symbolic_forms_translated = True
    parse.legibility.unsupported_fragments_visible = True
    parse.legibility.human_translation_available = bool(parse.human_translation)
    return parse


def summarize_logical_form_parse(parse: LogicalFormParse) -> dict[str, Any]:
    validation_messages = validate_logical_form_parse(parse)
    anti_gaming_safe = not any(
        marker in validation_messages
        for marker in [
            "official_score_claimed true is not allowed",
            "uses_answer_key true is not allowed",
            "uses_item_id true is not allowed",
            "uses_answer_position_bias true is not allowed",
            "stores_raw_text_by_default true is not allowed",
            "benchmark_specific_rule_used true is not allowed",
        ]
    )
    legibility_safe = not any(
        marker in validation_messages
        for marker in [
            "private_symbolic_authority_used true is not allowed",
            "symbolic_forms_translated false is not allowed",
            "unsupported_fragments_visible false is not allowed",
        ]
    )
    return {
        "parse_id": parse.parse_id,
        "source_task_id": parse.source_task_id,
        "statement_count": len(parse.statements),
        "premise_count": len(parse.premises),
        "candidate_conclusion_count": len(parse.candidate_conclusions),
        "operator_count": len(parse.operators),
        "quantifier_count": len(parse.quantifiers),
        "conditional_count": len(parse.conditionals),
        "negation_count": len(parse.negations),
        "disjunction_count": len(parse.disjunctions),
        "conjunction_count": len(parse.conjunctions),
        "unsupported_fragment_count": len(parse.unsupported_fragments),
        "parse_confidence": parse.parse_confidence,
        "warning_count": len(parse.parse_warnings),
        "anti_gaming_safe": anti_gaming_safe,
        "legibility_safe": legibility_safe,
    }


__all__ = [
    "LogicalFormParse",
    "ParsedStatement",
    "LogicalOperatorRecord",
    "QuantifierRecord",
    "ConditionalRecord",
    "NegationRecord",
    "DisjunctionRecord",
    "ConjunctionRecord",
    "ParserWarningRecord",
    "UnsupportedFragmentRecord",
    "ParserAntiGamingRecord",
    "ParserLegibilityRecord",
    "fingerprint_text",
    "split_candidate_statements",
    "normalize_logical_text",
    "detect_statement_role",
    "create_empty_logical_form_parse",
    "logical_form_parse_to_dict",
    "logical_form_parse_from_dict",
    "validate_logical_form_parse",
    "add_parsed_statement",
    "add_unsupported_fragment",
    "add_parser_warning",
    "parse_runtime_text_to_logical_form",
    "summarize_logical_form_parse",
]
