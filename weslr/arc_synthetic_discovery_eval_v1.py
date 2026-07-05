"""ARC-AGI-2 synthetic discovery evaluation V1.

Runs the universal family runner on synthetic tasks and summarizes exact-match,
family-selection, fallback, and adversarial rejection behavior.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from weslr.arc_synthetic_discovery_task_generator_v1 import build_arc_synthetic_solver_packet_v1
from weslr.arc_universal_family_runner_v1 import UniversalRunnerResult, run_universal_family_solver

RunnerFn = Callable[[Sequence[Mapping[str, Any]], Any], UniversalRunnerResult]


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    return str(value)


def _grid_like(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    width = None
    for row in value:
        if not isinstance(row, list) or not row:
            return False
        if width is None:
            width = len(row)
        elif len(row) != width:
            return False
        for cell in row:
            if not isinstance(cell, int) or isinstance(cell, bool):
                return False
    return True


def _grids_equal(left: Any, right: Any) -> bool:
    return _json_safe(left) == _json_safe(right)


def _task_kind(task: Mapping[str, Any]) -> str:
    metadata = task.get("metadata") if isinstance(task.get("metadata"), Mapping) else {}
    return str(metadata.get("kind", ""))


def _task_expected_behavior(task: Mapping[str, Any]) -> str:
    metadata = task.get("metadata") if isinstance(task.get("metadata"), Mapping) else {}
    return str(metadata.get("expected_behavior", "solve"))


def _is_fallback_only(result: Any) -> bool:
    try:
        attempts = [result.attempt_1, result.attempt_2]
    except Exception:
        return False
    return all(getattr(attempt, "family_name", "") == "fallback" for attempt in attempts)


def _selected_families(result: Any) -> list[str]:
    try:
        families = result.selected_family_names
    except Exception:
        return []
    return [str(item) for item in families]


def _failure_category(task: Mapping[str, Any], result: Any, *, exact_match: bool, fallback_only: bool, solved_by_attempt_1: bool, solved_by_attempt_2: bool) -> str | None:
    if exact_match:
        return None
    kind = _task_kind(task)
    families = _selected_families(result)
    trace = getattr(result, "trace", {}) if hasattr(result, "trace") else {}
    selected_compositions = trace.get("selected_composition_families", []) if isinstance(trace, Mapping) else []
    executed_compositions = trace.get("executed_composition_families", []) if isinstance(trace, Mapping) else []
    family_label = str(task.get("family_label", ""))
    if kind == "adversarial":
        return "ambiguous_expected_rejection"
    if fallback_only:
        return "fallback_only"
    if family_label in selected_compositions and family_label not in executed_compositions:
        return "family_discovered_not_executed"
    if families and family_label not in families:
        return "wrong_family_selected"
    if not families:
        return "discovery_missed_family"
    if solved_by_attempt_1 or solved_by_attempt_2:
        return "candidate_wrong_output"
    return "candidate_wrong_output"


@dataclass(frozen=True)
class SyntheticDiscoveryEvaluationResultV1:
    report: dict[str, Any] = field(default_factory=dict)

    def to_json_safe_dict(self) -> dict[str, Any]:
        return _json_safe(self.report)


def evaluate_arc_synthetic_discovery_tasks_v1(tasks: Sequence[Mapping[str, Any]], *, runner: RunnerFn = run_universal_family_solver) -> SyntheticDiscoveryEvaluationResultV1:
    total_tasks = len(tasks)
    solved_by_attempt_1 = 0
    solved_by_attempt_2 = 0
    unsolved = 0
    malformed = 0
    fallback_only = 0
    exact_two_output_pass = True
    adversarial_rejection_pass = 0
    adversarial_rejection_fail = 0
    failure_categories: Counter[str] = Counter()
    per_family_generated: Counter[str] = Counter()
    per_family_solved: Counter[str] = Counter()
    per_family_failed: Counter[str] = Counter()
    composition_solved_count = 0
    ambiguous_case_behavior = Counter()
    task_summaries: list[dict[str, Any]] = []

    for task in tasks:
        family_label = str(task.get("family_label", ""))
        per_family_generated[family_label] += 1
        try:
            packet = build_arc_synthetic_solver_packet_v1(task)
            result = runner(packet["train_pairs"], packet["test_input"])
            exact_two = bool(getattr(result, "exact_two_output", False))
            exact_two_output_pass = exact_two_output_pass and exact_two
            attempt_1 = getattr(result, "attempt_1", None)
            attempt_2 = getattr(result, "attempt_2", None)
            expected_output = task.get("expected_output")
            attempt_1_match = bool(attempt_1 is not None and _grids_equal(getattr(attempt_1, "output", None), expected_output))
            attempt_2_match = bool(attempt_2 is not None and _grids_equal(getattr(attempt_2, "output", None), expected_output))
            exact_match = attempt_1_match or attempt_2_match
            if attempt_1_match:
                solved_by_attempt_1 += 1
                per_family_solved[family_label] += 1
            if attempt_2_match:
                solved_by_attempt_2 += 1
                per_family_solved[family_label] += 1
            if not exact_match:
                unsolved += 1
                per_family_failed[family_label] += 1
            if _is_fallback_only(result):
                fallback_only += 1
            if str(_task_kind(task)) == "composition" and exact_match:
                composition_solved_count += 1
            if str(_task_kind(task)) == "adversarial":
                if exact_match:
                    adversarial_rejection_fail += 1
                else:
                    adversarial_rejection_pass += 1
            if _grid_like(getattr(attempt_1, "output", None)) is False and getattr(attempt_1, "output", None) is not None:
                malformed += 1
            if _grid_like(getattr(attempt_2, "output", None)) is False and getattr(attempt_2, "output", None) is not None:
                malformed += 1
            category = _failure_category(task, result, exact_match=exact_match, fallback_only=_is_fallback_only(result), solved_by_attempt_1=attempt_1_match, solved_by_attempt_2=attempt_2_match)
            if category is not None:
                failure_categories[category] += 1
            if str(_task_kind(task)) == "adversarial":
                ambiguous_case_behavior["rejected"] += 1 if not exact_match else 0
                ambiguous_case_behavior["solved"] += 1 if exact_match else 0
            task_summaries.append(
                {
                    "task_id": str(task.get("task_id", "")),
                    "family_label": family_label,
                    "exact_match": exact_match,
                    "solved_by_attempt_1": attempt_1_match,
                    "solved_by_attempt_2": attempt_2_match,
                    "fallback_only": _is_fallback_only(result),
                    "selected_families": _selected_families(result),
                    "failure_category": category,
                }
            )
        except Exception:
            unsolved += 1
            per_family_failed[family_label] += 1
            failure_categories["exception"] += 1
            task_summaries.append(
                {
                    "task_id": str(task.get("task_id", "")),
                    "family_label": family_label,
                    "exact_match": False,
                    "solved_by_attempt_1": False,
                    "solved_by_attempt_2": False,
                    "fallback_only": False,
                    "selected_families": [],
                    "failure_category": "exception",
                }
            )

    report = {
        "schema_version": "ArcSyntheticDiscoveryEvalV1",
        "total_tasks": total_tasks,
        "solved_by_attempt_1": solved_by_attempt_1,
        "solved_by_attempt_2": solved_by_attempt_2,
        "unsolved": unsolved,
        "malformed": malformed,
        "fallback_only": fallback_only,
        "exact_two_output_pass": exact_two_output_pass,
        "per_family_generated": dict(sorted(per_family_generated.items())),
        "per_family_solved": dict(sorted(per_family_solved.items())),
        "per_family_failed": dict(sorted(per_family_failed.items())),
        "composition_solved_count": composition_solved_count,
        "adversarial_rejection_pass": adversarial_rejection_pass,
        "adversarial_rejection_fail": adversarial_rejection_fail,
        "ambiguous_case_behavior": dict(sorted(ambiguous_case_behavior.items())),
        "failure_categories": dict(sorted(failure_categories.items())),
        "task_summaries": task_summaries,
    }
    return SyntheticDiscoveryEvaluationResultV1(report=report)


__all__ = [
    "SyntheticDiscoveryEvaluationResultV1",
    "evaluate_arc_synthetic_discovery_tasks_v1",
]
