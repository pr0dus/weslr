from __future__ import annotations

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
    "create_empty_logical_form_parse",
    "logical_form_parse_to_dict",
    "logical_form_parse_from_dict",
    "validate_logical_form_parse",
    "add_parsed_statement",
    "add_unsupported_fragment",
    "add_parser_warning",
]
