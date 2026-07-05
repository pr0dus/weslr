from __future__ import annotations

from types import SimpleNamespace

import weslr.arc_synthetic_discovery_eval_v1 as eval_module
from weslr.arc_synthetic_discovery_task_generator_v1 import build_arc_synthetic_discovery_task_v1, build_arc_synthetic_solver_packet_v1


def _stub_result(output_1: object, output_2: object, *, exact_two_output: bool = True, family_1: str = "object_bbox", family_2: str = "fallback") -> SimpleNamespace:
    attempt_1 = SimpleNamespace(family_name=family_1, output=output_1)
    attempt_2 = SimpleNamespace(family_name=family_2, output=output_2)
    return SimpleNamespace(attempt_1=attempt_1, attempt_2=attempt_2, exact_two_output=exact_two_output, selected_family_names=[family_1], trace={"selected_composition_families": [], "executed_composition_families": []})


def test_evaluator_does_not_pass_expected_output_to_runner(monkeypatch) -> None:
    task = build_arc_synthetic_discovery_task_v1("crop_foreground_bbox", seed=31)

    def fake_packet(task_dict):
        packet = build_arc_synthetic_solver_packet_v1(task_dict)
        packet["expected_output"] = task_dict["expected_output"]
        return packet

    seen = {}

    def fake_runner(train_pairs, test_input):
        seen["train_pairs_keys"] = set(train_pairs[0])
        seen["test_input"] = test_input
        return _stub_result(task["expected_output"], [[0]])

    monkeypatch.setattr(eval_module, "build_arc_synthetic_solver_packet_v1", fake_packet)
    result = eval_module.evaluate_arc_synthetic_discovery_tasks_v1([task], runner=fake_runner)
    assert seen["train_pairs_keys"] == {"input", "output"}
    assert seen["test_input"] == task["test_input"]
    assert result.report["solved_by_attempt_1"] == 1
    assert result.report["exact_two_output_pass"] is True


def test_evaluator_exact_match_counts_attempts_and_per_family(monkeypatch) -> None:
    task_1 = build_arc_synthetic_discovery_task_v1("crop_foreground_bbox", seed=41)
    task_2 = build_arc_synthetic_discovery_task_v1("crop_foreground_bbox", seed=42, variant="alt")
    outputs = [task_1["expected_output"], task_2["expected_output"]]

    def fake_runner(train_pairs, test_input):
        expected = outputs.pop(0)
        return _stub_result([[0]], expected)

    result = eval_module.evaluate_arc_synthetic_discovery_tasks_v1([task_1, task_2], runner=fake_runner)
    report = result.report
    assert report["total_tasks"] == 2
    assert report["solved_by_attempt_1"] == 0
    assert report["solved_by_attempt_2"] == 2
    assert report["per_family_generated"]["crop_foreground_bbox"] == 2
    assert report["per_family_solved"]["crop_foreground_bbox"] == 2
    assert report["per_family_failed"].get("crop_foreground_bbox", 0) == 0


def test_evaluator_malformed_and_adversarial_rejection_are_counted() -> None:
    normal = build_arc_synthetic_discovery_task_v1("crop_foreground_bbox", seed=51)
    adversarial = build_arc_synthetic_discovery_task_v1("inconsistent_train_examples", seed=52)

    def fake_runner(train_pairs, test_input):
        if len(train_pairs) == 1 and train_pairs[0]["output"] == normal["train_pairs"][0]["output"]:
            return SimpleNamespace(
                attempt_1=SimpleNamespace(family_name="object_bbox", output="not-a-grid"),
                attempt_2=SimpleNamespace(family_name="fallback", output=[[0]]),
                exact_two_output=True,
                selected_family_names=["object_bbox"],
                trace={"selected_composition_families": [], "executed_composition_families": []},
            )
        return SimpleNamespace(
            attempt_1=SimpleNamespace(family_name="fallback", output=[[0]]),
            attempt_2=SimpleNamespace(family_name="fallback", output=[[0]]),
            exact_two_output=True,
            selected_family_names=["fallback"],
            trace={"selected_composition_families": [], "executed_composition_families": []},
        )

    result = eval_module.evaluate_arc_synthetic_discovery_tasks_v1([normal, adversarial], runner=fake_runner)
    report = result.report
    assert report["malformed"] >= 1
    assert report["fallback_only"] == 1
    assert report["adversarial_rejection_pass"] == 1
    assert report["failure_categories"].get("wrong_family_selected", 0) == 1
    assert report["failure_categories"].get("ambiguous_expected_rejection", 0) == 1


def test_deterministic_replay_status_helper() -> None:
    first = [build_arc_synthetic_discovery_task_v1("tile_grid", seed=61), build_arc_synthetic_discovery_task_v1("rotate_object_180", seed=62)]
    second = [build_arc_synthetic_discovery_task_v1("tile_grid", seed=61), build_arc_synthetic_discovery_task_v1("rotate_object_180", seed=62)]
    assert first == second
