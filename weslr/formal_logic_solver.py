from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any

from weslr.reasoning_task import ReasoningTask
from weslr.reasoning_trace import WarrantRecord, add_conflict, add_inference_edge, add_inference_node
from weslr.solver_interface import (
    ReasoningSolverProtocol,
    SolverRunContext,
    SolverRunResult,
    validate_solver_run_context,
)


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


__all__ = ["FormalLogicSolver"]
