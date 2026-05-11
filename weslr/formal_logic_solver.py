from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from weslr.formal_logic_parser import LogicalFormParse, logical_form_parse_from_dict
from weslr.reasoning_task import ReasoningTask
from weslr.reasoning_trace import WarrantRecord, add_conflict, add_inference_edge, add_inference_node
from weslr.solver_interface import (
    ReasoningSolverProtocol,
    SolverRunContext,
    SolverRunResult,
    validate_solver_run_context,
)


@dataclass
class CandidateEvaluation:
    candidate_id: str
    support_score: int = 0
    contradiction_score: int = 0
    matched_premise_count: int = 0
    matched_operator_count: int = 0
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence: str = "low"


@dataclass
class CategoricalFacts:
    universal_affirmatives: list[tuple[str, str]] = field(default_factory=list)
    universal_negatives: list[tuple[str, str]] = field(default_factory=list)
    entity_affirmatives: list[tuple[str, str]] = field(default_factory=list)
    entity_negatives: list[tuple[str, str]] = field(default_factory=list)
    direct_facts: set[str] = field(default_factory=set)
    negated_facts: set[str] = field(default_factory=set)


class FormalLogicSolver(ReasoningSolverProtocol):
    solver_id = "formal_logic_solver"
    solver_family = "symbolic_reasoning"

    _DOMAINS = {"formal_logic", "reasoning_logic"}
    _SKILLS = {"ordinary_reasoning", "formal_logic_reasoning"}
    _TASK_TYPES = {"multiple_choice_reasoning", "structured_reasoning"}

    def can_handle(self, task: ReasoningTask) -> bool:
        return (
            task.parsed.task_type in self._TASK_TYPES
            and (task.domain in self._DOMAINS or task.required_skill in self._SKILLS)
        )

    def run(self, context: SolverRunContext) -> SolverRunResult:
        validation = validate_solver_run_context(context)
        if validation.errors:
            return SolverRunResult(
                solver_id=self.solver_id,
                solver_family=self.solver_family,
                status="invalid_context",
                warnings=list(validation.warnings),
                errors=list(validation.errors),
                anti_gaming_passed=False,
                legibility_passed=False,
            )

        task = context.task
        trace = context.trace
        warnings = list(validation.warnings)
        nodes_created: list[str] = []
        edges_created: list[str] = []
        conflicts_created: list[str] = []
        logical_form_parse = _coerce_logical_form_parse(context.metadata.get("logical_form_parse"))

        if logical_form_parse is not None:
            parser_claims = _extract_parser_claims(logical_form_parse)
            evaluations = _evaluate_parser_candidates(parser_claims)
            selection = _select_parser_candidate(parser_claims, evaluations)
            warnings.extend(selection["warnings"])

            if context.allow_trace_mutation:
                _add_parser_trace_nodes(
                    trace,
                    parser_claims=parser_claims,
                    evaluations=evaluations,
                    nodes_created=nodes_created,
                    edges_created=edges_created,
                    source=self.solver_id,
                )
                if selection["conflict_ids"]:
                    for idx, candidate_id in enumerate(selection["conflict_ids"], start=1):
                        conflict_id = f"{self.solver_id}_parser_conflict_{idx}"
                        add_conflict(
                            trace,
                            conflict_id=conflict_id,
                            conflict_type="candidate_contradiction",
                            node_ids=[],
                            explanation=f"candidate conflict detected for {candidate_id}",
                            severity="medium",
                            resolved=False,
                        )
                        conflicts_created.append(conflict_id)

            return SolverRunResult(
                solver_id=self.solver_id,
                solver_family=self.solver_family,
                status=selection["status"],
                proposed_answer=selection["proposed_answer"],
                confidence=selection["confidence"],
                explanation=selection["explanation"],
                nodes_created=nodes_created,
                edges_created=edges_created,
                conflicts_created=conflicts_created,
                warnings=warnings,
                anti_gaming_passed=True,
                legibility_passed=True,
                official_score_claimed=False,
            )

        if not context.allow_raw_question_access or not task.input.question_text:
            warnings.append("raw question access was not available")
            return SolverRunResult(
                solver_id=self.solver_id,
                solver_family=self.solver_family,
                status="insufficient_input",
                warnings=warnings,
                nodes_created=nodes_created,
                edges_created=edges_created,
                conflicts_created=conflicts_created,
            )

        if not task.input.choices or any("text" not in choice for choice in task.input.choices):
            warnings.append("raw choice text was not available")
            return SolverRunResult(
                solver_id=self.solver_id,
                solver_family=self.solver_family,
                status="insufficient_input",
                warnings=warnings,
                nodes_created=nodes_created,
                edges_created=edges_created,
                conflicts_created=conflicts_created,
            )

        analysis = _analyze_formal_logic(task.input.question_text)
        warnings.extend(analysis["warnings"])

        if context.allow_trace_mutation:
            premise_ids = []
            for idx, premise in enumerate(analysis["premises"], start=1):
                node_id = f"{self.solver_id}_premise_{idx}"
                add_inference_node(
                    trace,
                    node_id=node_id,
                    node_type="premise",
                    content=premise,
                    confidence="high",
                    source=self.solver_id,
                )
                nodes_created.append(node_id)
                premise_ids.append(node_id)

            if analysis["derived"]:
                derived_id = f"{self.solver_id}_derived_1"
                add_inference_node(
                    trace,
                    node_id=derived_id,
                    node_type="derived_conclusion",
                    content=analysis["derived"],
                    confidence=analysis["confidence"],
                    source=self.solver_id,
                )
                nodes_created.append(derived_id)
                for idx, premise_id in enumerate(premise_ids, start=1):
                    edge_id = f"{self.solver_id}_edge_{idx}"
                    add_inference_edge(
                        trace,
                        edge_id=edge_id,
                        from_node=premise_id,
                        to_node=derived_id,
                        relation_type="supports",
                        warrant=WarrantRecord(
                            warrant_type=analysis["pattern"] or "formal_rule",
                            source=self.solver_id,
                            explanation=analysis["warrant_explanation"] or "human-teachable formal logic step",
                            confidence=analysis["confidence"],
                            deterministic=True,
                            human_teachable=True,
                        ),
                        confidence=analysis["confidence"],
                    )
                    edges_created.append(edge_id)

            for idx, conflict in enumerate(analysis["conflicts"], start=1):
                conflict_id = f"{self.solver_id}_conflict_{idx}"
                add_conflict(
                    trace,
                    conflict_id=conflict_id,
                    conflict_type=conflict["type"],
                    node_ids=[],
                    explanation=conflict["explanation"],
                    severity=conflict["severity"],
                    resolved=False,
                )
                conflicts_created.append(conflict_id)

        if analysis["conflicts"]:
            return SolverRunResult(
                solver_id=self.solver_id,
                solver_family=self.solver_family,
                status="conflict_detected",
                warnings=warnings,
                nodes_created=nodes_created,
                edges_created=edges_created,
                conflicts_created=conflicts_created,
                confidence=analysis["confidence"],
            )

        if not analysis["derived"]:
            return SolverRunResult(
                solver_id=self.solver_id,
                solver_family=self.solver_family,
                status="no_supported_pattern",
                warnings=warnings,
                nodes_created=nodes_created,
                edges_created=edges_created,
                conflicts_created=conflicts_created,
                confidence="low",
            )

        matches = []
        derived_norm = _normalize_logic_text(analysis["derived"])
        for choice in task.input.choices:
            choice_text = str(choice.get("text", ""))
            if not choice_text:
                continue
            if _normalize_logic_text(choice_text) == derived_norm:
                matches.append(choice)

        if len(matches) != 1:
            status = "ambiguous_choice_match" if len(matches) > 1 else "no_unique_supported_choice"
            return SolverRunResult(
                solver_id=self.solver_id,
                solver_family=self.solver_family,
                status=status,
                warnings=warnings,
                nodes_created=nodes_created,
                edges_created=edges_created,
                conflicts_created=conflicts_created,
                confidence=analysis["confidence"],
            )

        chosen = matches[0]
        explanation = (
            f"Derived '{analysis['derived']}' using a human-teachable {analysis['pattern']} pattern; "
            f"exactly one choice matched that conclusion."
        )
        return SolverRunResult(
            solver_id=self.solver_id,
            solver_family=self.solver_family,
            status="ok",
            proposed_answer=str(chosen.get("label", "")),
            confidence=analysis["confidence"],
            explanation=explanation,
            nodes_created=nodes_created,
            edges_created=edges_created,
            conflicts_created=conflicts_created,
            warnings=warnings,
            anti_gaming_passed=True,
            legibility_passed=True,
            official_score_claimed=False,
        )


def _coerce_logical_form_parse(value: Any) -> LogicalFormParse | None:
    if value is None:
        return None
    if isinstance(value, LogicalFormParse):
        return value
    if isinstance(value, dict):
        return logical_form_parse_from_dict(value)
    return None


def _extract_parser_claims(logical_form_parse: LogicalFormParse) -> dict[str, Any]:
    statements_by_id = {statement.statement_id: statement for statement in logical_form_parse.statements}
    premises = [statements_by_id[statement_id] for statement_id in logical_form_parse.premises if statement_id in statements_by_id]
    candidate_conclusions = [
        statements_by_id[statement_id]
        for statement_id in logical_form_parse.candidate_conclusions
        if statement_id in statements_by_id
    ]
    return {
        "premises": premises,
        "candidate_conclusions": candidate_conclusions,
        "conditionals": list(logical_form_parse.conditionals),
        "quantifiers": list(logical_form_parse.quantifiers),
        "negations": list(logical_form_parse.negations),
        "disjunctions": list(logical_form_parse.disjunctions),
        "conjunctions": list(logical_form_parse.conjunctions),
        "unsupported_count": len(logical_form_parse.unsupported_fragments),
        "parse_confidence": logical_form_parse.parse_confidence,
    }


def _add_parser_trace_nodes(
    trace,
    *,
    parser_claims: dict[str, Any],
    evaluations: list[CandidateEvaluation],
    nodes_created: list[str],
    edges_created: list[str],
    source: str,
) -> None:
    summary_id = f"{source}_parser_summary"
    summary_content = (
        f"parser summary: premises={len(parser_claims['premises'])}, "
        f"candidate_conclusions={len(parser_claims['candidate_conclusions'])}, "
        f"unsupported_fragments={parser_claims['unsupported_count']}, "
        f"parse_confidence={parser_claims['parse_confidence'] or 'low'}"
    )
    add_inference_node(
        trace,
        node_id=summary_id,
        node_type="parser_summary",
        content=summary_content,
        confidence=parser_claims["parse_confidence"] or "low",
        source=source,
    )
    nodes_created.append(summary_id)

    premise_node_ids: dict[str, str] = {}
    for idx, statement in enumerate(parser_claims["premises"], start=1):
        node_id = f"{source}_parsed_premise_{idx}"
        add_inference_node(
            trace,
            node_id=node_id,
            node_type="parsed_premise",
            content=statement.logical_form or statement.normalized_text,
            confidence=statement.confidence or parser_claims["parse_confidence"] or "low",
            source=source,
        )
        nodes_created.append(node_id)
        premise_node_ids[statement.statement_id] = node_id
        edge_id = f"{source}_parser_premise_edge_{idx}"
        add_inference_edge(
            trace,
            edge_id=edge_id,
            from_node=summary_id,
            to_node=node_id,
            relation_type="supports",
            warrant=WarrantRecord(
                warrant_type="parser logical-form extraction",
                source=source,
                explanation="Parser extracted a structured premise without exposing raw text.",
                confidence=statement.confidence or parser_claims["parse_confidence"] or "low",
                deterministic=False,
                human_teachable=True,
            ),
            confidence=statement.confidence or parser_claims["parse_confidence"] or "low",
        )
        edges_created.append(edge_id)

    candidate_node_ids: dict[str, str] = {}
    for idx, statement in enumerate(parser_claims["candidate_conclusions"], start=1):
        node_id = f"{source}_{statement.statement_id}"
        node_type = "choice_claim" if statement.role == "choice_claim" else "candidate_conclusion"
        add_inference_node(
            trace,
            node_id=node_id,
            node_type=node_type,
            content=statement.statement_id,
            confidence=statement.confidence or parser_claims["parse_confidence"] or "low",
            source=source,
        )
        nodes_created.append(node_id)
        candidate_node_ids[statement.statement_id] = node_id
        edge_id = f"{source}_parser_choice_edge_{idx}"
        add_inference_edge(
            trace,
            edge_id=edge_id,
            from_node=summary_id,
            to_node=node_id,
            relation_type="supports",
            warrant=WarrantRecord(
                warrant_type="parser candidate-conclusion extraction",
                source=source,
                explanation="Parser extracted a candidate identifier from structured MCQ text without exposing raw text.",
                confidence=statement.confidence or parser_claims["parse_confidence"] or "low",
                deterministic=False,
                human_teachable=True,
            ),
            confidence=statement.confidence or parser_claims["parse_confidence"] or "low",
        )
        edges_created.append(edge_id)

    for idx, evaluation in enumerate(evaluations, start=1):
        node_type = "candidate_ambiguous"
        if evaluation.contradiction_score > 0:
            node_type = "candidate_contradicted"
        elif evaluation.support_score > 0 and evaluation.contradiction_score == 0:
            node_type = "candidate_supported"
        node_id = f"{source}_candidate_evaluation_{idx}"
        add_inference_node(
            trace,
            node_id=node_id,
            node_type=node_type,
            content=(
                f"candidate={evaluation.candidate_id}; support={evaluation.support_score}; "
                f"contradiction={evaluation.contradiction_score}; matched_premises={evaluation.matched_premise_count}; "
                f"matched_operators={evaluation.matched_operator_count}; confidence={evaluation.confidence}"
            ),
            confidence=evaluation.confidence,
            source=source,
        )
        nodes_created.append(node_id)

        candidate_node_id = candidate_node_ids.get(evaluation.candidate_id, summary_id)
        support_edge_id = f"{source}_candidate_eval_edge_{idx}"
        warrant_type = "parser candidate evaluation"
        explanation = "Candidate identifiers were evaluated against parser-visible premises and operators."
        if any(reason in evaluation.reasons for reason in {"universal_syllogism", "negative_universal_syllogism", "class_transitivity"}):
            warrant_type = "categorical syllogism"
            explanation = "Categorical premises supported this candidate through a teachable syllogistic step."
        elif any(reason in evaluation.reasons for reason in {"direct_fact_match", "direct_negation_conflict"}):
            warrant_type = "simple entailment check"
            explanation = "Direct entailment and contradiction checks compared the candidate against parsed premises."
        add_inference_edge(
            trace,
            edge_id=support_edge_id,
            from_node=candidate_node_id,
            to_node=node_id,
            relation_type="evaluates",
            warrant=WarrantRecord(
                warrant_type=warrant_type,
                source=source,
                explanation=explanation,
                confidence=evaluation.confidence,
                deterministic=False,
                human_teachable=True,
            ),
            confidence=evaluation.confidence,
        )
        edges_created.append(support_edge_id)

        if evaluation.contradiction_score > 0:
            contradiction_edge_id = f"{source}_candidate_contradiction_edge_{idx}"
            add_inference_edge(
                trace,
                edge_id=contradiction_edge_id,
                from_node=summary_id,
                to_node=node_id,
                relation_type="blocks",
                warrant=WarrantRecord(
                    warrant_type="contradiction check",
                    source=source,
                    explanation="Contradiction checks blocked confident candidate selection.",
                    confidence=evaluation.confidence,
                    deterministic=False,
                    human_teachable=True,
                ),
                confidence=evaluation.confidence,
            )
            edges_created.append(contradiction_edge_id)

    summary_eval_id = f"{source}_candidate_evaluation_summary"
    supported = sum(1 for evaluation in evaluations if evaluation.support_score > 0 and evaluation.contradiction_score == 0)
    contradicted = sum(1 for evaluation in evaluations if evaluation.contradiction_score > 0)
    add_inference_node(
        trace,
        node_id=summary_eval_id,
        node_type="candidate_evaluation_summary",
        content=(
            f"candidate evaluations: total={len(evaluations)}; supported={supported}; "
            f"contradicted={contradicted}; unsupported_fragments={parser_claims['unsupported_count']}"
        ),
        confidence=parser_claims["parse_confidence"] or "low",
        source=source,
    )
    nodes_created.append(summary_eval_id)
    summary_edge_id = f"{source}_candidate_evaluation_summary_edge"
    add_inference_edge(
        trace,
        edge_id=summary_edge_id,
        from_node=summary_id,
        to_node=summary_eval_id,
        relation_type="supports",
        warrant=WarrantRecord(
            warrant_type="parser candidate evaluation",
            source=source,
            explanation="Evaluation summary records how parser-visible candidates were compared without using answer keys.",
            confidence=parser_claims["parse_confidence"] or "low",
            deterministic=False,
            human_teachable=True,
        ),
        confidence=parser_claims["parse_confidence"] or "low",
    )
    edges_created.append(summary_edge_id)

    if parser_claims["unsupported_count"]:
        node_id = f"{source}_unsupported_fragment_summary"
        add_inference_node(
            trace,
            node_id=node_id,
            node_type="unsupported_fragment_summary",
            content=f"unsupported fragment summary: count={parser_claims['unsupported_count']}",
            confidence="low",
            source=source,
        )
        nodes_created.append(node_id)
        edge_id = f"{source}_unsupported_summary_edge"
        add_inference_edge(
            trace,
            edge_id=edge_id,
            from_node=summary_id,
            to_node=node_id,
            relation_type="supports",
            warrant=WarrantRecord(
                warrant_type="parser logical-form extraction",
                source=source,
                explanation="Parser exposed unsupported fragment count instead of hiding unresolved structure.",
                confidence="low",
                deterministic=False,
                human_teachable=True,
            ),
            confidence="low",
        )
        edges_created.append(edge_id)


def _canonical_token(token: str) -> str:
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _normalize_logic_text(text: str) -> str:
    lowered = text.lower().strip()
    lowered = lowered.replace("therefore", "")
    lowered = lowered.replace("thus", "")
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    lowered = re.sub(r"\b(an|a|the)\b", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return " ".join(_canonical_token(token) for token in lowered.split())


def _tokenize_logic_text(text: str) -> set[str]:
    return {token for token in _normalize_logic_text(text).split() if token}


def _is_negated(text: str) -> bool:
    return _normalize_logic_text(text).startswith("not ")


def _strip_negation(text: str) -> str:
    normalized = _normalize_logic_text(text)
    return normalized[4:] if normalized.startswith("not ") else normalized


def _confidence_from_scores(*, support_score: int, contradiction_score: int, parse_confidence: str, unsupported_count: int) -> str:
    if contradiction_score > 0:
        return "low"
    if support_score >= 4 and parse_confidence == "medium" and unsupported_count == 0:
        return "medium"
    if support_score >= 2 and parse_confidence == "medium":
        return "low"
    return "low"


def _evaluate_parser_candidates(parser_claims: dict[str, Any]) -> list[CandidateEvaluation]:
    premise_texts = [statement.logical_form or statement.normalized_text for statement in parser_claims["premises"]]
    premise_norms = [_normalize_logic_text(text) for text in premise_texts if text]
    premise_tokens = [_tokenize_logic_text(text) for text in premise_texts if text]
    positive_premises = {_normalize_logic_text(text) for text in premise_texts if text and not _is_negated(text)}
    negative_premises = {_strip_negation(text) for text in premise_texts if text and _is_negated(text)}
    categorical_facts = _extract_categorical_facts(parser_claims)

    satisfied_conditionals: list[tuple[str, str]] = []
    for conditional in parser_claims["conditionals"]:
        antecedent = _normalize_logic_text(conditional.antecedent)
        consequent = _normalize_logic_text(conditional.consequent)
        if antecedent and consequent and antecedent in positive_premises:
            satisfied_conditionals.append((antecedent, consequent))
        if antecedent and consequent and f"not {consequent}" in {_normalize_logic_text(text) for text in premise_texts if text}:
            satisfied_conditionals.append((f"not {consequent}", f"not {antecedent}"))

    evaluations: list[CandidateEvaluation] = []
    unsupported_count = parser_claims["unsupported_count"]
    parse_confidence = parser_claims["parse_confidence"] or "low"

    for candidate in parser_claims["candidate_conclusions"]:
        candidate_text = candidate.logical_form or candidate.normalized_text
        candidate_norm = _normalize_logic_text(candidate_text)
        candidate_tokens = _tokenize_logic_text(candidate_text)
        evaluation = CandidateEvaluation(candidate_id=candidate.statement_id)

        if candidate_norm in positive_premises:
            evaluation.support_score += 3
            evaluation.matched_premise_count += 1
            evaluation.reasons.append("matched_direct_premise")
        if _is_negated(candidate_norm) and _strip_negation(candidate_norm) in negative_premises:
            evaluation.support_score += 3
            evaluation.matched_premise_count += 1
            evaluation.reasons.append("matched_direct_negated_premise")

        for tokens, premise_norm in zip(premise_tokens, premise_norms, strict=False):
            if not candidate_tokens or not tokens:
                continue
            overlap = candidate_tokens & tokens
            if len(overlap) >= 2 and candidate_tokens.issubset(tokens) and premise_norm != candidate_norm:
                evaluation.support_score += 1
                evaluation.matched_premise_count += 1
                evaluation.reasons.append("token_overlap")

        if _is_negated(candidate_norm) and _strip_negation(candidate_norm) in positive_premises:
            evaluation.contradiction_score += 3
            evaluation.warnings.append("explicit_negation_conflict")
        if not _is_negated(candidate_norm) and candidate_norm in negative_premises:
            evaluation.contradiction_score += 3
            evaluation.warnings.append("explicit_negation_conflict")

        for _, consequent in satisfied_conditionals:
            if candidate_norm == consequent:
                evaluation.support_score += 4
                evaluation.matched_operator_count += 1
                evaluation.reasons.append("supported_by_conditional")

        categorical_delta = _score_candidate_against_categorical_facts(candidate_norm, categorical_facts)
        evaluation.support_score += categorical_delta.support_score
        evaluation.contradiction_score += categorical_delta.contradiction_score
        evaluation.matched_premise_count += categorical_delta.matched_premise_count
        evaluation.matched_operator_count += categorical_delta.matched_operator_count
        for reason in categorical_delta.reasons:
            if reason not in evaluation.reasons:
                evaluation.reasons.append(reason)
        for warning in categorical_delta.warnings:
            if warning not in evaluation.warnings:
                evaluation.warnings.append(warning)

        for negation in parser_claims["negations"]:
            neg_norm = _normalize_logic_text(negation.normalized_form)
            if neg_norm and candidate_norm and _strip_negation(candidate_norm) == _strip_negation(neg_norm) and candidate_norm != neg_norm:
                evaluation.contradiction_score += 2
                evaluation.matched_operator_count += 1
                evaluation.warnings.append("negation_record_conflict")
                break

        if parser_claims["disjunctions"] and evaluation.support_score > 0:
            evaluation.warnings.append("disjunctions_require_conservative_selection")
        if unsupported_count:
            evaluation.warnings.append("unsupported_fragments_reduce_confidence")

        evaluation.confidence = _confidence_from_scores(
            support_score=evaluation.support_score,
            contradiction_score=evaluation.contradiction_score,
            parse_confidence=parse_confidence,
            unsupported_count=unsupported_count,
        )
        evaluations.append(evaluation)

    return evaluations


def _select_parser_candidate(parser_claims: dict[str, Any], evaluations: list[CandidateEvaluation]) -> dict[str, Any]:
    unsupported_count = parser_claims["unsupported_count"]
    parse_confidence = parser_claims["parse_confidence"] or "low"
    contradicted = [evaluation for evaluation in evaluations if evaluation.contradiction_score > 0]
    supportable = [
        evaluation
        for evaluation in evaluations
        if evaluation.support_score > 0 and evaluation.contradiction_score == 0
    ]

    explanation = (
        "Parser extracted structured premises and candidate conclusions, "
        "but no supported inference rule selected a unique answer in this phase."
    )
    warnings: list[str] = []
    if unsupported_count:
        warnings.append(
            f"parser reported {unsupported_count} unsupported fragment(s) still requiring broader logical-form coverage"
        )

    if contradicted and not supportable:
        return {
            "status": "parsed_candidate_blocked_by_conflict",
            "proposed_answer": "",
            "confidence": "low",
            "explanation": "Parser-mode candidate checks found contradiction signals, so selection remained blocked.",
            "warnings": warnings,
            "conflict_ids": [evaluation.candidate_id for evaluation in contradicted],
        }

    if parse_confidence == "low":
        warnings.append("low parse confidence blocked candidate selection")
        return {
            "status": "parsed_no_supported_inference",
            "proposed_answer": "",
            "confidence": "low",
            "explanation": explanation,
            "warnings": warnings,
            "conflict_ids": [evaluation.candidate_id for evaluation in contradicted],
        }

    if not supportable:
        return {
            "status": "parsed_no_supported_inference",
            "proposed_answer": "",
            "confidence": "low",
            "explanation": explanation,
            "warnings": warnings,
            "conflict_ids": [evaluation.candidate_id for evaluation in contradicted],
        }

    ranked = sorted(supportable, key=lambda evaluation: (evaluation.support_score, evaluation.matched_operator_count), reverse=True)
    best = ranked[0]
    if len(ranked) > 1 and ranked[1].support_score == best.support_score and ranked[1].matched_operator_count == best.matched_operator_count:
        warnings.append("candidate evaluations tied, so no answer was selected")
        return {
            "status": "parsed_ambiguous_candidates",
            "proposed_answer": "",
            "confidence": "low",
            "explanation": "Parser-mode candidate checks found multiple similarly supported candidates, so selection remained ambiguous.",
            "warnings": warnings,
            "conflict_ids": [evaluation.candidate_id for evaluation in contradicted],
        }

    if unsupported_count and best.support_score < 4:
        warnings.append("unsupported fragments lowered confidence below selection threshold")
        return {
            "status": "parsed_no_supported_inference",
            "proposed_answer": "",
            "confidence": "low",
            "explanation": explanation,
            "warnings": warnings,
            "conflict_ids": [evaluation.candidate_id for evaluation in contradicted],
        }

    if best.support_score < 4:
        return {
            "status": "parsed_no_supported_inference",
            "proposed_answer": "",
            "confidence": "low",
            "explanation": explanation,
            "warnings": warnings,
            "conflict_ids": [evaluation.candidate_id for evaluation in contradicted],
        }

    return {
        "status": "parsed_candidate_selected",
        "proposed_answer": best.candidate_id.replace("choice_", "", 1),
        "confidence": "medium" if best.confidence == "medium" else "low",
        "explanation": f"Parser-mode candidate evaluation selected {best.candidate_id} from structured support only.",
        "warnings": warnings,
        "conflict_ids": [evaluation.candidate_id for evaluation in contradicted],
    }


def _extract_categorical_facts(parser_claims: dict[str, Any]) -> CategoricalFacts:
    facts = CategoricalFacts()
    premise_texts = [statement.logical_form or statement.normalized_text for statement in parser_claims["premises"]]
    for premise_text in premise_texts:
        normalized = _normalize_logic_text(premise_text)
        if not normalized:
            continue
        facts.direct_facts.add(normalized)
        if normalized.startswith("not "):
            facts.negated_facts.add(_strip_negation(normalized))

        all_match = re.fullmatch(r"all\s+(.+?)\s+are\s+(.+)", normalized)
        if all_match:
            facts.universal_affirmatives.append((all_match.group(1).strip(), all_match.group(2).strip()))
            continue

        no_match = re.fullmatch(r"no\s+(.+?)\s+are\s+(.+)", normalized)
        if no_match:
            facts.universal_negatives.append((no_match.group(1).strip(), no_match.group(2).strip()))
            continue

        neg_entity_match = re.fullmatch(r"(.+?)\s+is\s+not\s+(.+)", normalized)
        if neg_entity_match:
            facts.entity_negatives.append((neg_entity_match.group(1).strip(), neg_entity_match.group(2).strip()))
            continue

        pos_entity_match = re.fullmatch(r"(.+?)\s+is\s+(.+)", normalized)
        if pos_entity_match:
            facts.entity_affirmatives.append((pos_entity_match.group(1).strip(), pos_entity_match.group(2).strip()))
            continue

        relation_neg_match = re.fullmatch(r"(.+?)\s+does\s+not\s+(.+)", normalized)
        if relation_neg_match:
            facts.negated_facts.add(f"{relation_neg_match.group(1).strip()} {relation_neg_match.group(2).strip()}")
            continue

    return facts


def _score_candidate_against_categorical_facts(candidate_norm: str, facts: CategoricalFacts) -> CandidateEvaluation:
    delta = CandidateEvaluation(candidate_id="")
    if not candidate_norm:
        return delta

    if candidate_norm in facts.direct_facts:
        delta.support_score += 4
        delta.matched_premise_count += 1
        delta.reasons.append("direct_fact_match")

    if candidate_norm in facts.negated_facts or _strip_negation(candidate_norm) in facts.negated_facts:
        if candidate_norm not in facts.direct_facts:
            delta.contradiction_score += 4
            delta.matched_premise_count += 1
            delta.reasons.append("direct_negation_conflict")

    entity_pos_match = re.fullmatch(r"(.+?)\s+is\s+(.+)", candidate_norm)
    entity_neg_match = re.fullmatch(r"(.+?)\s+is\s+not\s+(.+)", candidate_norm)
    universal_match = re.fullmatch(r"all\s+(.+?)\s+are\s+(.+)", candidate_norm)

    if entity_pos_match:
        entity, cls = entity_pos_match.group(1).strip(), entity_pos_match.group(2).strip()
        for fact_entity, fact_cls in facts.entity_affirmatives:
            if fact_entity == entity and fact_cls == cls:
                delta.support_score = max(delta.support_score, 4)
                delta.matched_premise_count += 1
                if "direct_fact_match" not in delta.reasons:
                    delta.reasons.append("direct_fact_match")
            for source_cls, target_cls in facts.universal_affirmatives:
                if fact_entity == entity and fact_cls == source_cls and target_cls == cls:
                    delta.support_score += 5
                    delta.matched_premise_count += 2
                    delta.matched_operator_count += 1
                    delta.reasons.append("universal_syllogism")
        for fact_entity, fact_cls in facts.entity_negatives:
            if fact_entity == entity and fact_cls == cls:
                delta.contradiction_score += 4
                delta.matched_premise_count += 1
                delta.reasons.append("direct_negation_conflict")

    if entity_neg_match:
        entity, cls = entity_neg_match.group(1).strip(), entity_neg_match.group(2).strip()
        for fact_entity, fact_cls in facts.entity_negatives:
            if fact_entity == entity and fact_cls == cls:
                delta.support_score += 4
                delta.matched_premise_count += 1
                delta.reasons.append("direct_fact_match")
        for fact_entity, fact_cls in facts.entity_affirmatives:
            if fact_entity == entity and fact_cls == cls:
                delta.contradiction_score += 4
                delta.matched_premise_count += 1
                delta.reasons.append("direct_negation_conflict")
            for source_cls, target_cls in facts.universal_negatives:
                if fact_entity == entity and fact_cls == source_cls and target_cls == cls:
                    delta.support_score += 5
                    delta.matched_premise_count += 2
                    delta.matched_operator_count += 1
                    delta.reasons.append("negative_universal_syllogism")

    if universal_match:
        source_cls, target_cls = universal_match.group(1).strip(), universal_match.group(2).strip()
        for left_cls, mid_cls in facts.universal_affirmatives:
            for mid2_cls, right_cls in facts.universal_affirmatives:
                if left_cls == source_cls and mid_cls == mid2_cls and right_cls == target_cls:
                    delta.support_score += 5
                    delta.matched_premise_count += 2
                    delta.matched_operator_count += 1
                    delta.reasons.append("class_transitivity")
                    break

    return delta


def _split_statements(text: str) -> list[str]:
    normalized = text.replace("?", ".").replace(";", ".").replace(":", ".")
    return [part.strip() for part in re.split(r"[\.!\n]+", normalized) if part.strip()]


def _extract_conditional(statement: str) -> tuple[str, str] | None:
    m = re.search(r"if\s+(.+?)\s+then\s+(.+)", statement, re.I)
    if not m:
        return None
    return _normalize_logic_text(m.group(1)), _normalize_logic_text(m.group(2))


def _extract_all_quantifier(statement: str) -> tuple[str, str] | None:
    m = re.search(r"all\s+(.+?)\s+are\s+(.+)", statement, re.I)
    if not m:
        return None
    return _normalize_logic_text(m.group(1)), _normalize_logic_text(m.group(2))


def _extract_no_quantifier(statement: str) -> tuple[str, str] | None:
    m = re.search(r"no\s+(.+?)\s+are\s+(.+)", statement, re.I)
    if not m:
        return None
    return _normalize_logic_text(m.group(1)), _normalize_logic_text(m.group(2))


def _extract_some_quantifier(statement: str) -> tuple[str, str] | None:
    m = re.search(r"some\s+(.+?)\s+are\s+(.+)", statement, re.I)
    if not m:
        return None
    return _normalize_logic_text(m.group(1)), _normalize_logic_text(m.group(2))


def _extract_membership(statement: str) -> tuple[str, str] | None:
    m = re.search(r"(.+?)\s+is\s+(?:an|a)?\s*(.+)", statement, re.I)
    if not m:
        return None
    return _normalize_logic_text(m.group(1)), _normalize_logic_text(m.group(2))


def _analyze_formal_logic(question_text: str) -> dict[str, Any]:
    statements = _split_statements(question_text)
    normalized = [_normalize_logic_text(s) for s in statements]
    premises = list(statements)
    warnings: list[str] = []
    conflicts: list[dict[str, str]] = []
    derived = ""
    pattern = ""
    warrant_explanation = ""
    confidence = "low"

    conditionals = []
    for statement in statements:
        extracted = _extract_conditional(statement)
        if extracted:
            conditionals.append(extracted)

    atomic = {s for s in normalized if s and not s.startswith("if ")}
    negated_atomic = {_normalize_logic_text(s[4:]) for s in normalized if s.startswith("not ")}

    for atom in atomic:
        if atom in negated_atomic:
            conflicts.append(
                {
                    "type": "contradiction",
                    "severity": "high",
                    "explanation": f"The premises contain both '{atom}' and 'not {atom}', which is a contradiction.",
                }
            )

    for antecedent, consequent in conditionals:
        if antecedent in atomic:
            derived = consequent
            pattern = "modus ponens"
            warrant_explanation = "From 'if P then Q' and 'P', it is valid to infer 'Q'."
            confidence = "high"
            break
        if f"not {consequent}" in atomic:
            derived = f"not {antecedent}"
            pattern = "modus tollens"
            warrant_explanation = "From 'if P then Q' and 'not Q', it is valid to infer 'not P'."
            confidence = "high"
            break
        if consequent in atomic:
            warnings.append("Detected an invalid converse pattern: if P then Q; Q; therefore P is not valid.")
            conflicts.append(
                {
                    "type": "invalid_converse",
                    "severity": "medium",
                    "explanation": "The premises match the invalid converse pattern, so no conclusion should be selected.",
                }
            )
        if f"not {antecedent}" in atomic:
            warnings.append("Detected an invalid inverse pattern: if P then Q; not P; therefore not Q is not valid.")
            conflicts.append(
                {
                    "type": "invalid_inverse",
                    "severity": "medium",
                    "explanation": "The premises match the invalid inverse pattern, so no conclusion should be selected.",
                }
            )

    if not conflicts and not derived:
        for statement in statements:
            all_q = _extract_all_quantifier(statement)
            if all_q:
                source_class, target_class = all_q
                for other in statements:
                    membership = _extract_membership(other)
                    if membership and membership[1] == source_class:
                        derived = f"{membership[0]} is {target_class}"
                        pattern = "universal instantiation"
                        warrant_explanation = "From 'All A are B' and 'x is A', it is valid to infer 'x is B'."
                        confidence = "medium"
                        break
            if derived:
                break

    if not conflicts and not derived:
        for statement in statements:
            no_q = _extract_no_quantifier(statement)
            if no_q:
                source_class, target_class = no_q
                for other in statements:
                    membership = _extract_membership(other)
                    if membership and membership[1] == source_class:
                        derived = f"{membership[0]} is not {target_class}"
                        pattern = "universal exclusion"
                        warrant_explanation = "From 'No A are B' and 'x is A', it is valid to infer 'x is not B'."
                        confidence = "medium"
                        break
            if derived:
                break

    if not conflicts and not derived:
        for statement in statements:
            some_q = _extract_some_quantifier(statement)
            if some_q:
                derived = f"some {some_q[0]} are {some_q[1]}"
                pattern = "existential restatement"
                warrant_explanation = "A 'some A are B' premise supports the same existential claim directly."
                confidence = "medium"
                break

    return {
        "premises": premises,
        "warnings": warnings,
        "conflicts": conflicts,
        "derived": derived,
        "pattern": pattern,
        "warrant_explanation": warrant_explanation,
        "confidence": confidence,
    }


__all__ = ["FormalLogicSolver", "CandidateEvaluation"]
