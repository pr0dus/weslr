"""Tests for ARC-AGI-2 marker-copy capability V1."""

from __future__ import annotations

import json

import pytest

from weslr.arc_marker_copy_v1 import (
    solve_marker_copy_task,
    build_arc_agi2_marker_copy_top2_attempt_packet_v1,
    _infer_marker_copy_pattern,
    _find_connected_objects,
    _find_source_object,
    _find_marker,
    _copy_object_to_marker,
)
from weslr.arc_synthetic_family_diversification_v1 import (
    build_diversified_family_task_v1,
)
from weslr.arc_synthetic_discovery_task_generator_v1 import build_arc_synthetic_solver_packet_v1
from weslr.arc_universal_family_runner_v1 import run_universal_family_solver
from weslr.arc_synthetic_discovery_eval_v1 import evaluate_arc_synthetic_discovery_tasks_v1


class TestInference:
    def test_infer_marker_copy_pattern(self):
        task = build_diversified_family_task_v1("copy_object_to_marker", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        pattern = _infer_marker_copy_pattern(packet["train_pairs"])
        assert pattern is not None
        assert pattern["source_color"] == 1
        assert pattern["marker_color"] == 5
        assert pattern["source_height"] == 2
        assert pattern["source_width"] == 2
        assert pattern["placement"] == "top_right"

    def test_find_connected_objects(self):
        grid = [[1, 1, 0, 0, 0], [1, 1, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 5], [0, 0, 0, 0, 0]]
        objects = _find_connected_objects(grid)
        assert len(objects) == 2
        colors = sorted(o["color"] for o in objects)
        assert colors == [1, 5]

    def test_find_source_object(self):
        grid = [[1, 1, 0, 0, 0], [1, 1, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 5], [0, 0, 0, 0, 0]]
        source = _find_source_object(grid, 1)
        assert source is not None
        assert source["height"] == 2
        assert source["width"] == 2

    def test_find_marker(self):
        grid = [[1, 1, 0, 0, 0], [1, 1, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 5], [0, 0, 0, 0, 0]]
        marker = _find_marker(grid, 5)
        assert marker == (3, 4)


class TestExecution:
    def test_copy_object_to_marker_solves(self):
        task = build_diversified_family_task_v1("copy_object_to_marker", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        candidates = solve_marker_copy_task(packet["train_pairs"], packet["test_input"])
        assert len(candidates) >= 1
        assert candidates[0]["grid"] == task["expected_output"]

    def test_all_variants_solve(self):
        for vi in range(3):
            task = build_diversified_family_task_v1("copy_object_to_marker", seed=42, variant=f"v{vi}")
            packet = build_arc_synthetic_solver_packet_v1(task)
            candidates = solve_marker_copy_task(packet["train_pairs"], packet["test_input"])
            assert len(candidates) >= 1, f"v{vi} has no candidates"
            assert candidates[0]["grid"] == task["expected_output"], f"v{vi} output mismatch"

    def test_different_seeds_solve(self):
        for seed in [42, 43, 44, 100, 200]:
            task = build_diversified_family_task_v1("copy_object_to_marker", seed=seed, variant="v0")
            packet = build_arc_synthetic_solver_packet_v1(task)
            candidates = solve_marker_copy_task(packet["train_pairs"], packet["test_input"])
            assert len(candidates) >= 1, f"seed={seed} has no candidates"
            assert candidates[0]["grid"] == task["expected_output"], f"seed={seed} output mismatch"


class TestFullPipeline:
    def test_universal_runner_solves(self):
        task = build_diversified_family_task_v1("copy_object_to_marker", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        result = run_universal_family_solver(packet["train_pairs"], packet["test_input"])
        assert result.attempt_1.output == task["expected_output"]
        assert not result.fallback_used

    def test_evaluation_passes(self):
        tasks = []
        for vi in range(3):
            tasks.append(build_diversified_family_task_v1("copy_object_to_marker", seed=42, variant=f"v{vi}"))
        eval_result = evaluate_arc_synthetic_discovery_tasks_v1(tasks)
        report = eval_result.to_json_safe_dict()
        assert report.get("exception_count", 0) == 0
        assert report.get("malformed", 0) == 0
        assert report.get("solved_by_attempt_1", 0) == 3


class TestNoLeakage:
    def test_expected_output_not_in_solver_packet(self):
        task = build_diversified_family_task_v1("copy_object_to_marker", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        assert "expected_output" not in packet


class TestDeterminism:
    def test_same_seed_same_result(self):
        t1 = build_diversified_family_task_v1("copy_object_to_marker", seed=42, variant="v0")
        t2 = build_diversified_family_task_v1("copy_object_to_marker", seed=42, variant="v0")
        assert json.dumps(t1, sort_keys=True) == json.dumps(t2, sort_keys=True)


class TestAdapterPacket:
    def test_adapter_produces_valid_packet(self):
        task = build_diversified_family_task_v1("copy_object_to_marker", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        result = build_arc_agi2_marker_copy_top2_attempt_packet_v1(
            packet["train_pairs"],
            packet["test_input"],
            task_id="test",
            test_input_index=0,
        )
        assert len(result.get("attempts", [])) == 2
        assert result["attempts"][0]["grid"] == task["expected_output"]
