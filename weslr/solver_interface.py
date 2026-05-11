from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol, runtime_checkable

from weslr.reasoning_task import ReasoningTask
from weslr.reasoning_trace import ReasoningTrace, SolverOutput
from weslr.solver_registry import SolverDescriptor


@dataclass
class SolverRunContext:
    task: ReasoningTask | None = None
    trace: ReasoningTrace | None = None
    solver_descriptor: SolverDescriptor | None = None
    dry_run: bool = True
    allow_answer_selection: bool = False
    allow_trace_mutation: bool = True
    allow_raw_question_access: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SolverRunResult:
    solver_id: str = ""
    solver_family: str = ""
    status: str = ""
    proposed_answer: str = ""
    confidence: str = ""
    explanation: str = ""
    nodes_created: list[str] = field(default_factory=list)
    edges_created: list[str] = field(default_factory=list)
    conflicts_created: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    anti_gaming_passed: bool = True
    legibility_passed: bool = True
    official_score_claimed: bool = False


@dataclass
class SolverValidationResult:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@runtime_checkable
class ReasoningSolverProtocol(Protocol):
    solver_id: str
    solver_family: str

    def can_handle(self, task: ReasoningTask) -> bool: ...
    def run(self, context: SolverRunContext) -> SolverRunResult: ...


def validate_solver_run_context(context: SolverRunContext) -> SolverValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if context.task is None:
        errors.append("context.task is required")
    if context.trace is None:
        errors.append("context.trace is required")
    if context.solver_descriptor is None:
        errors.append("context.solver_descriptor is required")

    descriptor = context.solver_descriptor
    task = context.task

    if context.allow_raw_question_access and task is not None and not task.input.question_text:
        errors.append("allow_raw_question_access true but task.input.question_text is empty")

    if descriptor is not None:
        can_select = any(cap.can_select_answer for cap in descriptor.capabilities)
        if context.allow_answer_selection and not can_select:
            errors.append("allow_answer_selection true but solver descriptor cannot select answers")

        safety = descriptor.safety_profile
        if safety.uses_answer_key:
            errors.append("solver descriptor safety profile uses answer key")
        if safety.uses_item_id:
            errors.append("solver descriptor safety profile uses item id")
        if safety.official_score_claimed:
            errors.append("solver descriptor safety profile claims official score")
        if safety.private_authority_used:
            errors.append("solver descriptor safety profile uses private authority")
        if safety.opaque_output_allowed:
            errors.append("solver descriptor safety profile allows opaque output")

        if not descriptor.enabled:
            warnings.append("solver descriptor is disabled")

    return SolverValidationResult(valid=not errors, errors=errors, warnings=warnings)


def validate_solver_run_result(result: SolverRunResult) -> SolverValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not result.solver_id:
        errors.append("solver_id is required")
    if result.official_score_claimed:
        errors.append("official_score_claimed true is not allowed")
    if not result.anti_gaming_passed:
        errors.append("anti_gaming_passed false is not allowed")
    if not result.legibility_passed:
        errors.append("legibility_passed false is not allowed")
    if result.proposed_answer and not result.explanation:
        errors.append("proposed_answer requires explanation")
    if result.proposed_answer and not result.confidence:
        errors.append("proposed_answer requires confidence")
    if result.errors:
        errors.append("solver run result contains errors")

    return SolverValidationResult(valid=not errors, errors=errors, warnings=warnings)


def solver_run_result_to_solver_output(result: SolverRunResult) -> SolverOutput:
    return SolverOutput(
        solver_id=result.solver_id,
        solver_family=result.solver_family,
        proposed_answer=result.proposed_answer,
        confidence=result.confidence,
        explanation=result.explanation,
        nodes_created=list(result.nodes_created),
        conflicts_created=list(result.conflicts_created),
        status=result.status,
    )


def solver_run_result_to_dict(result: SolverRunResult) -> dict[str, Any]:
    return asdict(result)


__all__ = [
    "SolverRunContext",
    "SolverRunResult",
    "SolverValidationResult",
    "ReasoningSolverProtocol",
    "validate_solver_run_context",
    "validate_solver_run_result",
    "solver_run_result_to_solver_output",
    "solver_run_result_to_dict",
]
