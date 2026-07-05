"""Tests for ARC-AGI-2 hole filling and row/column extraction capability V1."""

from __future__ import annotations

import json

import pytest

from weslr.arc_hole_row_column_v1 import (
    solve_hole_row_column_task,
    build_arc_agi2_hole_row_column_top2_attempt_packet_v1,
    _infer_fill_color,
    _infer_marker_pattern,
    _fill_enclosed_holes,
    _extract_row_by_marker,
    _extract_column_by_marker,
    _is_enclosed_hole,
)
from weslr.arc_synthetic_family_diversification_v1 import (
    build_diversified_family_task_v1,
)
from weslr.arc_synthetic_discovery_task_generator_v1 import build_arc_synthetic_solver_packet_v1
from weslr.arc_universal_family_runner_v1 import run_universal_family_solver
from weslr.arc_synthetic_discovery_eval_v1 import evaluate_arc_synthetic_discovery_tasks_v1


class TestInference:
    def test_infer_fill_color(self):
        task = build_diversified_family_task_v1("fill_enclosed_hole", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        color = _infer_fill_color(packet["train_pairs"], packet["test_input"])
        assert color == 3  # test border color

    def test_infer_marker_pattern_row(self):
        task = build_diversified_family_task_v1("extract_row_or_column_by_marker", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        pattern = _infer_marker_pattern(packet["train_pairs"])
        assert pattern is not None
        assert pattern["mode"] == "row"

    def test_is_enclosed_hole(self):
        grid = [[3, 3, 3, 3, 3], [3, 0, 0, 0, 3], [3, 0, 0, 0, 3], [3, 0, 0, 0, 3], [3, 3, 3, 3, 3]]
        assert _is_enclosed_hole(grid, 1, 1)
        assert not _is_enclosed_hole(grid, 0, 0)  # boundary cell


class TestExecution:
    def test_fill_enclosed_hole_solves(self):
        task = build_diversified_family_task_v1("fill_enclosed_hole", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        candidates = solve_hole_row_column_task(packet["train_pairs"], packet["test_input"])
        assert len(candidates) >= 1
        assert candidates[0]["grid"] == task["expected_output"]

    def test_extract_row_by_marker_solves(self):
        task = build_diversified_family_task_v1("extract_row_or_column_by_marker", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        candidates = solve_hole_row_column_task(packet["train_pairs"], packet["test_input"])
        assert len(candidates) >= 1
        assert candidates[0]["grid"] == task["expected_output"]

    def test_all_variants_solve(self):
        for family in ["fill_enclosed_hole", "extract_row_or_column_by_marker"]:
            for vi in range(3):
                task = build_diversified_family_task_v1(family, seed=42, variant=f"v{vi}")
                packet = build_arc_synthetic_solver_packet_v1(task)
                candidates = solve_hole_row_column_task(packet["train_pairs"], packet["test_input"])
                assert len(candidates) >= 1, f"{family} v{vi} has no candidates"
                assert candidates[0]["grid"] == task["expected_output"], f"{family} v{vi} output mismatch"


class TestFullPipeline:
    def test_universal_runner_solves(self):
        for family in ["fill_enclosed_hole", "extract_row_or_column_by_marker"]:
            task = build_diversified_family_task_v1(family, seed=42, variant="v0")
            packet = build_arc_synthetic_solver_packet_v1(task)
            result = run_universal_family_solver(packet["train_pairs"], packet["test_input"])
            assert result.attempt_1.output == task["expected_output"], f"{family} not solved by universal runner"
            assert not result.fallback_used, f"{family} uses fallback"

    def test_evaluation_passes(self):
        tasks = []
        for family in ["fill_enclosed_hole", "extract_row_or_column_by_marker"]:
            for vi in range(3):
                tasks.append(build_diversified_family_task_v1(family, seed=42, variant=f"v{vi}"))
        eval_result = evaluate_arc_synthetic_discovery_tasks_v1(tasks)
        report = eval_result.to_json_safe_dict()
        assert report.get("exception_count", 0) == 0
        assert report.get("malformed", 0) == 0
        # All 6 tasks should be solved
        assert report.get("solved_by_attempt_1", 0) == 6


class TestNoLeakage:
    def test_expected_output_not_in_solver_packet(self):
        for family in ["fill_enclosed_hole", "extract_row_or_column_by_marker"]:
            task = build_diversified_family_task_v1(family, seed=42, variant="v0")
            packet = build_arc_synthetic_solver_packet_v1(task)
            assert "expected_output" not in packet


class TestDeterminism:
    def test_same_seed_same_result(self):
        t1 = build_diversified_family_task_v1("fill_enclosed_hole", seed=42, variant="v0")
        t2 = build_diversified_family_task_v1("fill_enclosed_hole", seed=42, variant="v0")
        assert json.dumps(t1, sort_keys=True) == json.dumps(t2, sort_keys=True)


class TestAdapterPacket:
    def test_adapter_produces_valid_packet(self):
        task = build_diversified_family_task_v1("fill_enclosed_hole", seed=42, variant="v0")
        packet = build_arc_synthetic_solver_packet_v1(task)
        result = build_arc_agi2_hole_row_column_top2_attempt_packet_v1(
            packet["train_pairs"],
            packet["test_input"],
            task_id="test",
            test_input_index=0,
        )
        assert len(result.get("attempts", [])) == 2
        assert result["attempts"][0]["grid"] == task["expected_output"]
