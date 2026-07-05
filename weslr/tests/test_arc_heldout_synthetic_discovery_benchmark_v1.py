from __future__ import annotations

from types import SimpleNamespace

import weslr.arc_heldout_synthetic_discovery_benchmark_v1 as benchmark_module
from weslr.arc_synthetic_discovery_eval_v1 import evaluate_arc_synthetic_discovery_tasks_v1
from weslr.arc_synthetic_discovery_task_generator_v1 import build_arc_synthetic_discovery_task_corpus_v1
from weslr.arc_universal_family_runner_v1 import run_universal_family_solver


def _fake_report(**overrides):
    base = {
        "total_tasks": 2,
        "solved_by_attempt_1": 1,
        "solved_by_attempt_2": 1,
        "unsolved": 0,
        "malformed": 0,
        "fallback_only": 0,
        "exact_two_output_pass": True,
        "per_family_generated": {"crop_foreground_bbox": 2},
        "per_family_solved": {"crop_foreground_bbox": 2},
        "per_family_failed": {"crop_foreground_bbox": 0},
        "composition_solved_count": 1,
        "adversarial_rejection_pass": 1,
        "adversarial_rejection_fail": 0,
        "ambiguous_case_behavior": {},
        "failure_categories": {"candidate_wrong_output": 1},
        "task_summaries": [],
    }
    base.update(overrides)
    return base


def test_same_seed_same_benchmark_and_different_seed_changes_ids() -> None:
    first = benchmark_module.build_heldout_synthetic_discovery_benchmark_v1()
    second = benchmark_module.build_heldout_synthetic_discovery_benchmark_v1()
    third = benchmark_module.build_heldout_synthetic_discovery_benchmark_v1(dev_seed=2436, heldout_seed=82436)
    assert first == second
    assert first["dev_task_ids"] != third["dev_task_ids"]
    assert first["heldout_task_ids"] != third["heldout_task_ids"]


def test_dev_and_heldout_splits_are_disjoint_and_expected_output_isolation_holds(monkeypatch) -> None:
    captured = {"task_keys": []}

    def fake_eval(tasks, *, runner=None):
        captured["task_keys"].append(sorted(tasks[0].keys()))
        return SimpleNamespace(report=_fake_report())

    monkeypatch.setattr(benchmark_module, "evaluate_arc_synthetic_discovery_tasks_v1", fake_eval)
    payload = benchmark_module.build_heldout_synthetic_discovery_benchmark_v1()
    assert payload["split_disjoint_pass"] is True
    assert payload["expected_output_isolation_pass"] is True
    assert captured["task_keys"]
    assert "expected_output" in captured["task_keys"][0]


def test_benchmark_reports_exact_two_and_failure_categories(monkeypatch) -> None:
    monkeypatch.setattr(
        benchmark_module,
        "evaluate_arc_synthetic_discovery_tasks_v1",
        lambda tasks, runner=None: SimpleNamespace(report=_fake_report(failure_categories={"fallback_only": 1, "exception": 1})),
    )
    payload = benchmark_module.build_heldout_synthetic_discovery_benchmark_v1(tasks_per_family_dev=1, tasks_per_family_heldout=1)
    assert payload["dev"]["evaluation"]["exact_two_output_pass"] is True
    assert payload["heldout"]["evaluation"]["exact_two_output_pass"] is True
    assert payload["dev"]["summary"]["failure_categories"]["fallback_only"] == 1
    assert payload["heldout"]["summary"]["failure_categories"]["exception"] == 1


def test_per_family_aggregation_and_deterministic_replay(monkeypatch) -> None:
    monkeypatch.setattr(
        benchmark_module,
        "evaluate_arc_synthetic_discovery_tasks_v1",
        lambda tasks, runner=None: SimpleNamespace(report=_fake_report()),
    )
    payload = benchmark_module.build_heldout_synthetic_discovery_benchmark_v1()
    assert payload["deterministic_replay_pass"] is True
    assert payload["dev"]["summary"]["per_family_generated"]
    assert payload["dev"]["summary"]["per_family_solved"]
    assert payload["dev"]["summary"]["per_family_failed"]


def test_no_public_arc_path_is_referenced_in_module_source() -> None:
    from pathlib import Path

    text = Path(benchmark_module.__file__).read_text().lower()
    assert "kaggle" not in text
    assert "/kaggle/" not in text
    assert "arc-prize" not in text


def test_crop_largest_and_select_largest_do_not_raise_and_fail_cleanly() -> None:
    tasks = build_arc_synthetic_discovery_task_corpus_v1(seed=82435, tasks_per_family=5, include_adversarial=True, include_compositions=True)
    for family in ("crop_largest_object", "select_largest_object"):
        family_tasks = [task for task in tasks if task["family_label"] == family]
        result = evaluate_arc_synthetic_discovery_tasks_v1(family_tasks)
        assert result.report["failure_categories"].get("exception", 0) == 0
        assert result.report["total_tasks"] == len(family_tasks)
        assert result.report["unsolved"] >= 0


def test_primary_fallback_cluster_tasks_solve_without_fallback_when_valid() -> None:
    tasks = build_arc_synthetic_discovery_task_corpus_v1(seed=82435, tasks_per_family=5, include_adversarial=True, include_compositions=True)
    for family in (
        "translate_single_object",
        "swap_two_colors",
        "rotate_object_180",
        "reflect_object_horizontal",
        "reflect_object_vertical",
    ):
        family_tasks = [task for task in tasks if task["family_label"] == family]
        assert family_tasks
        result = evaluate_arc_synthetic_discovery_tasks_v1(family_tasks)
        assert result.report["failure_categories"].get("exception", 0) == 0
        assert result.report["fallback_only"] == 0
        assert result.report["exact_two_output_pass"] is True
        assert result.report["per_family_solved"].get(family, 0) >= 1
        runner_result = run_universal_family_solver(family_tasks[0]["train_pairs"], family_tasks[0]["test_input"])
        assert runner_result.fallback_used is False
        assert runner_result.exact_two_output is True
        assert runner_result.selected_family_names
