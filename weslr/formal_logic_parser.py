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
    r"\b(if|unless|either|or|and|not|no|none|never|all|every|some|therefore|so|hence|follows|must be true|which follows|could be true|can be inferred|logically follows|follows from|valid conclusion|best supported)\b",
    re.I,
)

_INSTRUCTION_MARKERS = [
    "which of the following",
    "which one",
    "which statement",
    "must be true",
    "could be true",
    "can be inferred",
    "logically follows",
    "follows from",
    "based on the statements",
    "from the information above",
    "valid conclusion",
    "best supported",
    "select",
    "which follows",
]

_SAFE_CHOICE_LABEL_RE = re.compile(r"^[A-Za-z0-9]{1,4}$")
_DECLARATIVE_VERB_RE = re.compile(r"\b(is|are|was|were|has|have|had|belongs|owns|supports|opposes|requires|permits|prevents|implies|entails|excludes|causes)\b", re.I)
_SYMBOLIC_RELATION_RE = re.compile(r"\b([A-Za-z]|[A-Za-z][A-Za-z0-9_]*)\b\s+(is|are|implies|entails|requires|supports|opposes|prevents)\s+\b([A-Za-z]|[A-Za-z][A-Za-z0-9_]*)\b", re.I)
_BACKGROUND_SHELL_RE = re.compile(r"^(question|statements above|the statements above|information above|above)$", re.I)


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
    if any(marker in lowered for marker in _INSTRUCTION_MARKERS):
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


def _looks_declarative_premise(fragment: str) -> bool:
    normalized = normalize_logical_text(fragment)
    if not normalized or re.search(r"\?$", fragment.strip()):
        return False
    if _LOGICAL_MARKER_RE.search(normalized):
        return True
    if _DECLARATIVE_VERB_RE.search(normalized):
        return True
    if _SYMBOLIC_RELATION_RE.search(fragment):
        return True
    tokens = re.findall(r"[A-Za-z0-9_]+", fragment)
    if len(tokens) >= 2 and all(len(token) <= 3 for token in tokens) and any(token.isalpha() for token in tokens):
        return True
    return False


def classify_question_fragment(fragment: str, *, position: int, total: int) -> str:
    lowered = normalize_logical_text(fragment)
    if not lowered:
        return "background"
    if any(marker in lowered for marker in _INSTRUCTION_MARKERS):
        return "question_instruction"
    if lowered.startswith(("which", "what", "determine", "identify", "select", "based on")):
        return "question_instruction"
    if "based on the statements above" in lowered or "based on" in lowered or "from the information above" in lowered:
        return "question_instruction"
    if re.search(r"\?$", fragment.strip()):
        return "question_instruction"
    if _looks_declarative_premise(fragment):
        return "premise"
    if position < total and not fragment.strip().endswith("?"):
        return "background"
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


def _extract_if_then_parts(normalized: str) -> tuple[str, str] | None:
    match = re.search(r"^if\s+(.*?)\s+then\s+(.*?)$", normalized)
    if not match:
        return None
    antecedent = match.group(1).strip(" ?")
    consequent = match.group(2).strip(" ?")
    if not antecedent or not consequent:
        return None
    return antecedent, consequent


def _contains_obvious_logical_marker(normalized: str) -> bool:
    return bool(_LOGICAL_MARKER_RE.search(normalized))


def _append_unique_terms(parse: LogicalFormParse, normalized: str) -> None:
    parse.normalized_terms.extend([token for token in re.findall(r"[a-z0-9]+", normalized) if token not in parse.normalized_terms])


def _add_structural_records(parse: LogicalFormParse, *, idx: str, statement_id: str, normalized: str) -> None:
    if normalized.startswith("if ") and " then " in normalized:
        parts = _extract_if_then_parts(normalized)
        if parts:
            antecedent, consequent = parts
            parse.conditionals.append(
                ConditionalRecord(
                    record_id=f"cond_{idx}",
                    antecedent=antecedent,
                    consequent=consequent,
                    conditional_type="direct_conditional",
                    source_statement_ids=[statement_id],
                    normalized_form=normalized,
                    confidence="medium",
                    human_translation="Conditional structure detected from if-then phrasing.",
                )
            )
            parse.operators.append(
                LogicalOperatorRecord(
                    record_id=f"op_cond_{idx}",
                    operator_type="conditional",
                    source_statement_ids=[statement_id],
                    normalized_form=normalized,
                    confidence="medium",
                    human_translation="Conditional structure detected from ordinary language.",
                )
            )

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


def _should_mark_unsupported(*, role: str, has_marker: bool, normalized: str) -> bool:
    if has_marker:
        return False
    if role in {"question_instruction", "choice_claim", "premise"}:
        return False
    if _BACKGROUND_SHELL_RE.fullmatch(normalized):
        return False
    return len(re.findall(r"[a-z0-9]+", normalized)) >= 3


def _populate_statement(
    parse: LogicalFormParse,
    *,
    idx: str,
    fragment: str,
    role: str,
    store_raw_text: bool,
    statement_id: str | None = None,
) -> tuple[ParsedStatement, bool]:
    normalized = normalize_logical_text(fragment)
    has_marker = _contains_obvious_logical_marker(normalized)
    statement = add_parsed_statement(
        parse,
        statement_id=statement_id or f"stmt_{idx}",
        raw_text_runtime_only=fragment if store_raw_text else "",
        text_fingerprint=fingerprint_text(fragment),
        normalized_text=normalized,
        role=role,
        logical_form=normalized,
        confidence="medium" if has_marker or role == "premise" else "low",
    )
    _append_unique_terms(parse, normalized)

    if role == "premise":
        parse.premises.append(statement.statement_id)
    elif role in {"conclusion_candidate", "choice_claim"}:
        parse.candidate_conclusions.append(statement.statement_id)

    _add_structural_records(parse, idx=idx, statement_id=statement.statement_id, normalized=normalized)

    if _should_mark_unsupported(role=role, has_marker=has_marker, normalized=normalized):
        add_unsupported_fragment(
            parse,
            record_id=f"unsupported_{idx}",
            fragment_type="natural_language_fragment",
            source_statement_ids=[statement.statement_id],
            normalized_form=normalized,
            confidence="low",
            human_translation="No obvious logical marker was detected, so this fragment remains visible as unsupported.",
        )

    return statement, has_marker


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
        role = detect_statement_role(fragment)
        _, has_marker = _populate_statement(parse, idx=str(idx), fragment=fragment, role=role, store_raw_text=store_raw_text)
        any_marker = any_marker or has_marker

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


def safe_choice_identifier(choice: Any, index: int) -> str:
    label = ""
    if hasattr(choice, "label"):
        label = str(getattr(choice, "label") or "")
    elif isinstance(choice, dict):
        label = str(choice.get("label", "") or "")

    label = label.strip()
    if _SAFE_CHOICE_LABEL_RE.fullmatch(label):
        return f"choice_{label}"
    return f"choice_{index}"


def parse_mcq_runtime_text_to_logical_form(
    question_text: str,
    choices: list[dict],
    *,
    parse_id: str,
    source_task_id: str,
    store_raw_text: bool = False,
) -> LogicalFormParse:
    parse = create_empty_logical_form_parse(parse_id=parse_id, source_task_id=source_task_id)
    any_marker = False

    question_fragments = split_candidate_statements(question_text)
    total_question_fragments = len(question_fragments)
    for idx, fragment in enumerate(question_fragments, start=1):
        role = classify_question_fragment(fragment, position=idx, total=total_question_fragments)
        _, has_marker = _populate_statement(parse, idx=f"q{idx}", fragment=fragment, role=role, store_raw_text=store_raw_text)
        any_marker = any_marker or has_marker or role == "premise"

    for idx, choice in enumerate(choices, start=1):
        text = str(choice.text if hasattr(choice, "text") else choice.get("text", ""))
        if not text.strip():
            continue
        # choice_claim is a non-answer-selecting candidate-conclusion role for parser-only MCQ structure awareness.
        _, has_marker = _populate_statement(
            parse,
            idx=f"c{idx}",
            statement_id=safe_choice_identifier(choice, idx),
            fragment=text,
            role="choice_claim",
            store_raw_text=store_raw_text,
        )
        any_marker = any_marker or has_marker

    parse.parse_confidence = "medium" if any_marker else "low"
    parse.human_translation = (
        "Preliminary MCQ-aware natural-language logical-form extraction only. "
        "Question instructions and choice claims are recorded without selecting or scoring answers."
    )
    parse.anti_gaming.uses_item_id = False
    parse.anti_gaming.uses_answer_key = False
    parse.anti_gaming.uses_answer_position_bias = False
    parse.anti_gaming.stores_raw_text_by_default = False
    parse.anti_gaming.official_score_claimed = False
    parse.anti_gaming.benchmark_specific_rule_used = False
    parse.legibility.symbolic_forms_translated = True
    parse.legibility.unsupported_fragments_visible = True
    parse.legibility.private_symbolic_authority_used = False
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
    question_instruction_count = sum(1 for statement in parse.statements if statement.role == "question_instruction")
    choice_claim_count = sum(1 for statement in parse.statements if statement.role == "choice_claim")
    return {
        "parse_id": parse.parse_id,
        "source_task_id": parse.source_task_id,
        "statement_count": len(parse.statements),
        "premise_count": len(parse.premises),
        "candidate_conclusion_count": len(parse.candidate_conclusions),
        "question_instruction_count": question_instruction_count,
        "choice_claim_count": choice_claim_count,
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
    "classify_question_fragment",
    "create_empty_logical_form_parse",
    "logical_form_parse_to_dict",
    "logical_form_parse_from_dict",
    "validate_logical_form_parse",
    "add_parsed_statement",
    "add_unsupported_fragment",
    "add_parser_warning",
    "parse_runtime_text_to_logical_form",
    "parse_mcq_runtime_text_to_logical_form",
    "safe_choice_identifier",
    "summarize_logical_form_parse",
]
