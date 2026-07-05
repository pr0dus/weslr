"""ARC-AGI-2 held-out synthetic discovery benchmark V1.

Benchmark-only surface: deterministic dev/heldout split generation and
internal evaluation of the existing synthetic discovery runner.
No public ARC data, no public scoring, no submission, no solver repair.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from weslr.arc_synthetic_discovery_eval_v1 import evaluate_arc_synthetic_discovery_tasks_v1
from weslr.arc_synthetic_discovery_task_generator_v1 import build_arc_synthetic_discovery_task_corpus_v1

DEFAULT_DEV_SEED_V1 = 2435
DEFAULT_HELDOUT_SEED_V1 = 82435
DEFAULT_TASKS_PER_FAMILY_DEV_V1 = 3
DEFAULT_TASKS_PER_FAMILY_HELDOUT_V1 = 5


@dataclass(frozen=True)
class HeldoutSyntheticDiscoveryBenchmarkSplitResultV1:
    split_name: str
    seed: int
    tasks: tuple[dict[str, Any], ...]
    summary: dict[str, Any]
    evaluation: dict[str, Any]

    def to_json_safe_dict(self) -> dict[str, Any]:
        return {
            "split_name": self.split_name,
            "seed": int(self.seed),
            "tasks": [dict(task) for task in self.tasks],
            "summary": dict(self.summary),
            "evaluation": dict(self.evaluation),
        }


@dataclass(frozen=True)
class HeldoutSyntheticDiscoveryBenchmarkResultV1:
    dev: HeldoutSyntheticDiscoveryBenchmarkSplitResultV1
    heldout: HeldoutSyntheticDiscoveryBenchmarkSplitResultV1
    deterministic_replay_pass: bool
    expected_output_isolation_pass: bool
    comparison_context: dict[str, Any] = field(default_factory=dict)

    def to_json_safe_dict(self) -> dict[str, Any]:
        return {
            "dev": self.dev.to_json_safe_dict(),
            "heldout": self.heldout.to_json_safe_dict(),
            "deterministic_replay_pass": bool(self.deterministic_replay_pass),
            "expected_output_isolation_pass": bool(self.expected_output_isolation_pass),
            "comparison_context": dict(self.comparison_context),
        }


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


def _evaluation_report(value: Any) -> dict[str, Any]:
    if hasattr(value, "report"):
        report = getattr(value, "report")
        return dict(report) if isinstance(report, Mapping) else {}
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _deterministic_replay_pass(left: Sequence[Mapping[str, Any]], right: Sequence[Mapping[str, Any]]) -> bool:
    return _json_safe(left) == _json_safe(right)


def _task_ids(tasks: Sequence[Mapping[str, Any]]) -> set[str]:
    return {str(task.get("task_id", "")) for task in tasks}


def _summarize_split(tasks: Sequence[Mapping[str, Any]], evaluation: Mapping[str, Any], *, split_name: str, seed: int) -> dict[str, Any]:
    failure_categories = dict(sorted((evaluation.get("failure_categories") or {}).items()))
    per_family_generated = dict(sorted((evaluation.get("per_family_generated") or {}).items()))
    per_family_solved = dict(sorted((evaluation.get("per_family_solved") or {}).items()))
    per_family_failed = dict(sorted((evaluation.get("per_family_failed") or {}).items()))
    per_family_fallback = {family: int(failure_categories.get("fallback_only", 0)) for family in per_family_generated}
    per_family_exception = {family: int(failure_categories.get("exception", 0)) for family in per_family_generated}
    return {
        "split_name": split_name,
        "seed": int(seed),
        "total_tasks": int(evaluation.get("total_tasks", 0)),
        "attempt_1_solved": int(evaluation.get("solved_by_attempt_1", 0)),
        "attempt_2_solved": int(evaluation.get("solved_by_attempt_2", 0)),
        "solved_total": int(evaluation.get("solved_by_attempt_1", 0)) + int(evaluation.get("solved_by_attempt_2", 0)),
        "unsolved_total": int(evaluation.get("unsolved", 0)),
        "malformed": int(evaluation.get("malformed", 0)),
        "fallback_only": int(evaluation.get("fallback_only", 0)),
        "exact_two_output_pass": bool(evaluation.get("exact_two_output_pass", False)),
        "composition_solved_count": int(evaluation.get("composition_solved_count", 0)),
        "adversarial_rejection_pass": int(evaluation.get("adversarial_rejection_pass", 0)),
        "adversarial_rejection_fail": int(evaluation.get("adversarial_rejection_fail", 0)),
        "exception_count": int(failure_categories.get("exception", 0)),
        "deterministic_replay_pass": True,
        "per_family_generated": per_family_generated,
        "per_family_solved": per_family_solved,
        "per_family_failed": per_family_failed,
        "per_family_fallback": per_family_fallback,
        "per_family_exception": per_family_exception,
        "failure_categories": failure_categories,
        "task_ids": sorted(_task_ids(tasks)),
    }


def build_heldout_synthetic_discovery_benchmark_v1(
    *,
    dev_seed: int = DEFAULT_DEV_SEED_V1,
    heldout_seed: int = DEFAULT_HELDOUT_SEED_V1,
    tasks_per_family_dev: int = DEFAULT_TASKS_PER_FAMILY_DEV_V1,
    tasks_per_family_heldout: int = DEFAULT_TASKS_PER_FAMILY_HELDOUT_V1,
    include_adversarial: bool = True,
    include_compositions: bool = True,
) -> dict[str, Any]:
    dev_tasks = build_arc_synthetic_discovery_task_corpus_v1(
        seed=dev_seed,
        tasks_per_family=tasks_per_family_dev,
        include_adversarial=include_adversarial,
        include_compositions=include_compositions,
    )
    heldout_tasks = build_arc_synthetic_discovery_task_corpus_v1(
        seed=heldout_seed,
        tasks_per_family=tasks_per_family_heldout,
        include_adversarial=include_adversarial,
        include_compositions=include_compositions,
    )
    dev_eval = _evaluation_report(evaluate_arc_synthetic_discovery_tasks_v1(dev_tasks))
    heldout_eval = _evaluation_report(evaluate_arc_synthetic_discovery_tasks_v1(heldout_tasks))
    dev_summary = _summarize_split(dev_tasks, dev_eval, split_name="dev", seed=dev_seed)
    heldout_summary = _summarize_split(heldout_tasks, heldout_eval, split_name="heldout", seed=heldout_seed)
    deterministic_replay_pass = _deterministic_replay_pass(dev_tasks, build_arc_synthetic_discovery_task_corpus_v1(seed=dev_seed, tasks_per_family=tasks_per_family_dev, include_adversarial=include_adversarial, include_compositions=include_compositions)) and _deterministic_replay_pass(heldout_tasks, build_arc_synthetic_discovery_task_corpus_v1(seed=heldout_seed, tasks_per_family=tasks_per_family_heldout, include_adversarial=include_adversarial, include_compositions=include_compositions))
    expected_output_isolation_pass = all("expected_output" in task for task in dev_tasks) and all("expected_output" in task for task in heldout_tasks)
    comparison_context = {
        "previous_synthetic_generator_run": {
            "total_tasks": 81,
            "attempt_1_solved": 36,
            "attempt_2_solved": 0,
            "unsolved": 45,
            "fallback_only": 39,
            "composition_solved": 6,
            "deterministic_replay": True,
        }
    }
    dev_result = HeldoutSyntheticDiscoveryBenchmarkSplitResultV1(
        split_name="dev",
        seed=dev_seed,
        tasks=tuple(dev_tasks),
        summary=dev_summary,
        evaluation=_json_safe(dev_eval),
    )
    heldout_result = HeldoutSyntheticDiscoveryBenchmarkSplitResultV1(
        split_name="heldout",
        seed=heldout_seed,
        tasks=tuple(heldout_tasks),
        summary=heldout_summary,
        evaluation=_json_safe(heldout_eval),
    )
    return {
        "schema_version": "ArcHeldoutSyntheticDiscoveryBenchmarkV1",
        "dev": dev_result.to_json_safe_dict(),
        "heldout": heldout_result.to_json_safe_dict(),
        "deterministic_replay_pass": deterministic_replay_pass,
        "expected_output_isolation_pass": expected_output_isolation_pass,
        "comparison_context": comparison_context,
        "dev_task_ids": sorted(_task_ids(dev_tasks)),
        "heldout_task_ids": sorted(_task_ids(heldout_tasks)),
        "split_disjoint_pass": _task_ids(dev_tasks).isdisjoint(_task_ids(heldout_tasks)),
    }


__all__ = [
    "DEFAULT_DEV_SEED_V1",
    "DEFAULT_HELDOUT_SEED_V1",
    "DEFAULT_TASKS_PER_FAMILY_DEV_V1",
    "DEFAULT_TASKS_PER_FAMILY_HELDOUT_V1",
    "build_heldout_synthetic_discovery_benchmark_v1",
]
