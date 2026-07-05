"""Tests for ARC-AGI-2 symmetry/line completion capability V1."""

from __future__ import annotations

import json

import pytest

from weslr.arc_agi2_symmetry_line_candidate_adapter_v1 import (
    ADAPTER_NAME_V1,
    solve_symmetry_line_task,
    build_arc_agi2_symmetry_line_top2_attempt_packet_v1,
    _infer_horizontal_symmetry,
    _infer_vertical_symmetry,
    _infer_line_extension,
    _complete_horizontal_symmetry,
    _complete_vertical_symmetry,
    _extend_horizontal_line,
    _extend_vertical_line,
    _is_horizontal_line,
    _is_vertical_line,
)
from weslr.arc_synthetic_family_diversification_v1 import (
    build_diversified_family_task_v1,
    build_diversified_family_corpus_v1,
)
from weslr.arc_synthetic_discovery_task_generator_v1 import build_arc_synthetic_solver_packet_v1
from weslr.arc_universal_family_runner_v1 import run_universal_family_solver
from weslr.arc_synthetic_discovery_eval_v1 import evaluate_arc_synthetic_discovery_tasks_v1


class TestInference:
    def test_infer_horizontal_symmetry(self):
        task = build_diversified_family_task_v1("complete_horizontal_symmetry", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        direction = _infer_horizontal_symmetry(packet["train_pairs"])
        assert direction == "left_to_right"

    def test_infer_vertical_symmetry(self):
        task = build_diversified_family_task_v1("complete_vertical_symmetry", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        direction = _infer_vertical_symmetry(packet["train_pairs"])
        assert direction == "top_to_bottom"

    def test_infer_line_extension(self):
        task = build_diversified_family_task_v1("extend_line_to_boundary", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        direction = _infer_line_extension(packet["train_pairs"])
        assert direction == "horizontal"


class TestExecution:
    def test_complete_horizontal_symmetry_solves(self):
        task = build_diversified_family_task_v1("complete_horizontal_symmetry", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        candidates = solve_symmetry_line_task(packet["train_pairs"], packet["test_input"])
        assert len(candidates) >= 1
        assert candidates[0]["grid"] == task["expected_output"]

    def test_complete_vertical_symmetry_solves(self):
        task = build_diversified_family_task_v1("complete_vertical_symmetry", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        candidates = solve_symmetry_line_task(packet["train_pairs"], packet["test_input"])
        assert len(candidates) >= 1
        assert candidates[0]["grid"] == task["expected_output"]

    def test_extend_line_to_boundary_solves(self):
        task = build_diversified_family_task_v1("extend_line_to_boundary", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        candidates = solve_symmetry_line_task(packet["train_pairs"], packet["test_input"])
        assert len(candidates) >= 1
        assert candidates[0]["grid"] == task["expected_output"]

    def test_all_variants_solve(self):
        for family in ["complete_horizontal_symmetry", "complete_vertical_symmetry", "extend_line_to_boundary"]:
            for vi in range(3):
                task = build_diversified_family_task_v1(family, seed=42, variant=f"v{vi}")
                packet = build_arc_synthetic_solver_packet_v1(task)
                candidates = solve_symmetry_line_task(packet["train_pairs"], packet["test_input"])
                assert len(candidates) >= 1, f"{family} v{vi} has no candidates"
                assert candidates[0]["grid"] == task["expected_output"], f"{family} v{vi} output mismatch"


class TestFullPipeline:
    def test_universal_runner_solves_symmetry(self):
        for family in ["complete_horizontal_symmetry", "complete_vertical_symmetry", "extend_line_to_boundary"]:
            task = build_diversified_family_task_v1(family, seed=42, variant="v0")
            packet = build_arc_synthetic_solver_packet_v1(task)
            result = run_universal_family_solver(packet["train_pairs"], packet["test_input"])
            assert result.attempt_1.output == task["expected_output"], f"{family} not solved by universal runner"
            assert not result.fallback_used, f"{family} uses fallback"

    def test_evaluation_passes(self):
        tasks = []
        for family in ["complete_horizontal_symmetry", "complete_vertical_symmetry", "extend_line_to_boundary"]:
            for vi in range(3):
                tasks.append(build_diversified_family_task_v1(family, seed=42, variant=f"v{vi}"))
        eval_result = evaluate_arc_synthetic_discovery_tasks_v1(tasks)
        report = eval_result.to_json_safe_dict()
        assert report.get("exception_count", 0) == 0
        assert report.get("malformed", 0) == 0
        # All 9 tasks should be solved
        assert report.get("solved_by_attempt_1", 0) == 9


class TestNoLeakage:
    def test_expected_output_not_in_solver_packet(self):
        for family in ["complete_horizontal_symmetry", "complete_vertical_symmetry", "extend_line_to_boundary"]:
            task = build_diversified_family_task_v1(family, seed=42, variant="v0")
            packet = build_arc_synthetic_solver_packet_v1(task)
            assert "expected_output" not in packet


class TestDeterminism:
    def test_same_seed_same_result(self):
        t1 = build_diversified_family_task_v1("complete_horizontal_symmetry", seed=42, variant="v0")
        t2 = build_diversified_family_task_v1("complete_horizontal_symmetry", seed=42, variant="v0")
        assert json.dumps(t1, sort_keys=True) == json.dumps(t2, sort_keys=True)


class TestAdapterPacket:
    def test_adapter_produces_valid_packet(self):
        task = build_diversified_family_task_v1("complete_horizontal_symmetry", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        result = build_arc_agi2_symmetry_line_top2_attempt_packet_v1(
            packet["train_pairs"],
            packet["test_input"],
            task_id="test",
            test_input_index=0,
        )
        assert len(result.get("attempts", [])) == 2
        assert result["attempts"][0]["grid"] == task["expected_output"]