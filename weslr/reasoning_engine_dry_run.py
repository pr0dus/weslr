from __future__ import annotations

from typing import Any

from weslr.formal_logic_solver import FormalLogicSolver
from weslr.reasoning_arbitrator import arbitrate_reasoning_trace
from weslr.reasoning_task import validate_reasoning_task
from weslr.reasoning_task_builder import build_reasoning_task_from_mcq_item
from weslr.reasoning_trace import create_empty_reasoning_trace
from weslr.solver_interface import (
    SolverRunContext,
    solver_run_result_to_solver_output,
    validate_solver_run_context,
    validate_solver_run_result,
)
from weslr.solver_registry import create_empty_solver_registry, get_solver


def _implemented_solver_instances() -> dict[str, Any]:
    return {
        "formal_logic_solver": FormalLogicSolver(),
    }


def run_reasoning_dry_run_for_mcq_item(
    item,
    suite_metadata=None,
    *,
    store_raw_question: bool = False,
    allow_solver_raw_access: bool = False,
    allow_answer_selection: bool = False,
) -> dict:
    task = build_reasoning_task_from_mcq_item(
        item,
        suite_metadata,
        store_raw_question=store_raw_question,
    )
    trace = create_empty_reasoning_trace(
        task_id=task.task_id,
        task_family=task.task_family,
        domain=task.domain,
        required_skill=task.required_skill,
    )
    registry = create_empty_solver_registry()

    candidate_solver_ids = list(task.solver_plan.candidate_solvers)
    implemented = _implemented_solver_instances()
    implemented_solvers_run: list[str] = []
    solver_statuses: dict[str, str] = {}
    validation_errors: list[str] = []
    validation_warnings: list[str] = []
    anti_gaming_warnings: list[str] = []

    for solver_id in candidate_solver_ids:
        solver = implemented.get(solver_id)
        if solver is None:
            continue
        descriptor = get_solver(registry, solver_id)
        if descriptor is None:
            validation_errors.append(f"missing solver descriptor: {solver_id}")
            continue
        descriptor.enabled = True
        context = SolverRunContext(
            task=task,
            trace=trace,
            solver_descriptor=descriptor,
            dry_run=True,
            allow_answer_selection=allow_answer_selection,
            allow_trace_mutation=True,
            allow_raw_question_access=allow_solver_raw_access,
        )
        context_validation = validate_solver_run_context(context)
        validation_errors.extend(context_validation.errors)
        validation_warnings.extend(context_validation.warnings)
        if not context_validation.valid:
            solver_statuses[solver_id] = "invalid_context"
            continue
        if not solver.can_handle(task):
            solver_statuses[solver_id] = "cannot_handle"
            continue
        implemented_solvers_run.append(solver_id)
        result = solver.run(context)
        result_validation = validate_solver_run_result(result)
        validation_errors.extend(result_validation.errors)
        validation_warnings.extend(result_validation.warnings)
        solver_statuses[solver_id] = result.status
        if not result.anti_gaming_passed:
            anti_gaming_warnings.append(f"{solver_id}: anti-gaming failed")
        if result.official_score_claimed:
            anti_gaming_warnings.append(f"{solver_id}: official score claimed")
        trace.solver_outputs.append(solver_run_result_to_solver_output(result))

    arbitrator_decision = arbitrate_reasoning_trace(trace)
    if not arbitrator_decision.anti_gaming_passed:
        anti_gaming_warnings.append("arbitrator anti-gaming blocked selection")
    if arbitrator_decision.official_score_claimed:
        anti_gaming_warnings.append("arbitrator reported official-score claim")

    return {
        "task_id": task.task_id,
        "domain": task.domain,
        "required_skill": task.required_skill,
        "question_text_stored": bool(task.input.question_text),
        "choice_text_stored": any(bool(choice.get("text")) for choice in task.input.choices),
        "candidate_solvers": candidate_solver_ids,
        "implemented_solvers_run": implemented_solvers_run,
        "solver_statuses": solver_statuses,
        "proposed_answer_present": any(bool(output.proposed_answer) for output in trace.solver_outputs),
        "arbitrator_selected_answer_present": bool(arbitrator_decision.selected_answer),
        "arbitrator_decision_status": arbitrator_decision.decision_status,
        "arbitrator_conflict_status": arbitrator_decision.conflict_status,
        "trace_node_count": len(trace.nodes),
        "trace_edge_count": len(trace.edges),
        "trace_conflict_count": len(trace.conflicts),
        "official_score_claimed": False,
        "anti_gaming_warnings": anti_gaming_warnings,
        "validation_errors": validation_errors + validate_reasoning_task(task),
        "validation_warnings": validation_warnings,
    }


__all__ = ["run_reasoning_dry_run_for_mcq_item"]
