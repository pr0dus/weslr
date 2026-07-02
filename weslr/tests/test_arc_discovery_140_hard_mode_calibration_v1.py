"""Tests for ARC Synthetic Discovery 140 Hard Mode Calibration V1."""

from __future__ import annotations

import pytest

from weslr.arc_bh80_materializer import materialize_scene
from weslr.arc_discovery_140_generator import generate_discovery_140_tasks, get_scoring_summary
from weslr.arc_discovery_140_hard_mode_calibration import (
    HARD_MODE_AXES,
    HARD_MODE_GATES,
    HARD_MODE_TASK_COUNT,
    SCORING_LAYER,
    generate_hard_mode_calibration_tasks,
    get_hard_mode_summary,
    run_hard_mode_semantic_pilot,
)
from weslr.arc_discovery_140_semantic_pilot import run_140_semantic_pilot


@pytest.fixture(scope="module")
def hard_mode_tasks():
    return generate_hard_mode_calibration_tasks()


@pytest.fixture(scope="module")
def hard_mode_pilot():
    return run_hard_mode_semantic_pilot()


class TestHardModeGenerator:
    def test_exact_count(self, hard_mode_tasks):
        assert len(hard_mode_tasks) == HARD_MODE_TASK_COUNT

    def test_scoring_layer_is_separate(self, hard_mode_tasks):
        assert all(t["scoring_layer"] == SCORING_LAYER for t in hard_mode_tasks)
        assert all(t.get("hard_mode") is True for t in hard_mode_tasks)
        assert all(t.get("train_pair_count") == 1 for t in hard_mode_tasks)
        assert all(t.get("test_input_count") == 1 for t in hard_mode_tasks)

    def test_tasks_materialize(self, hard_mode_tasks):
        for task in hard_mode_tasks:
            grid = materialize_scene(task["scene_spec"], task["task_id"])
            assert isinstance(grid, list)
            assert grid
            assert all(isinstance(row, list) for row in grid)
            assert all(isinstance(v, int) for row in grid for v in row)

    def test_axis_coverage(self, hard_mode_tasks):
        summary = get_hard_mode_summary(hard_mode_tasks)
        assert summary["hard_mode_total"] == HARD_MODE_TASK_COUNT
        assert summary["hard_mode_scored_total"] == HARD_MODE_TASK_COUNT
        assert summary["candidate_probe_total"] == 0
        assert len(summary["axis_counts"]) == len(HARD_MODE_AXES)
        assert summary["axis_counts"]["object_ambiguity"] >= 1
        assert summary["axis_counts"]["rival_grammar_ambiguity"] >= 1


class TestHardModePilot:
    def test_base_140_still_preserved(self):
        pilot140 = run_140_semantic_pilot()
        assert pilot140["scored_aggregate"]["scored_exact"] == 130
        assert pilot140["bh80_subset"]["semantic_exact"] == 80
        assert pilot140["previous_117_scored_base"]["semantic_exact"] == 117
        assert pilot140["candidate_probe_diagnostics"]["candidate_probe_counted_as_solved"] == 0

    def test_hard_mode_summary_structure(self, hard_mode_pilot):
        assert hard_mode_pilot["task_count"] == HARD_MODE_TASK_COUNT
        assert hard_mode_pilot["hard_mode_summary"]["hard_mode_denominator"] == HARD_MODE_TASK_COUNT
        assert hard_mode_pilot["hard_mode_summary"]["hard_mode_scored_total"] == HARD_MODE_TASK_COUNT
        assert hard_mode_pilot["base_140_reference"]["base_130_preserved"] is True
        assert hard_mode_pilot["base_140_reference"]["bh80_80_preserved"] is True
        assert hard_mode_pilot["base_140_reference"]["previous_117_preserved"] is True
        assert hard_mode_pilot["base_140_reference"]["candidate_probes_counted_as_solved_zero"] is True

    def test_gate_thresholds_present(self, hard_mode_pilot):
        gates = hard_mode_pilot["gate_results"]
        assert gates["base_130_preserved"] is True
        assert gates["bh80_80_preserved"] is True
        assert gates["previous_117_preserved"] is True
        assert gates["candidate_probes_counted_as_solved_zero"] is True
        assert {"hard_mode_clean", "hard_mode_preferred", "hard_mode_strong", "hard_mode_minimal"} <= set(gates)
        assert HARD_MODE_GATES["total"] == HARD_MODE_TASK_COUNT

    def test_reportable_result_fields_exist(self, hard_mode_pilot):
        aggregate = hard_mode_pilot["hard_mode_aggregate"]
        assert aggregate["hard_mode_total"] == HARD_MODE_TASK_COUNT
        assert "hard_mode_exact" in aggregate
        assert "hard_mode_failed" in aggregate
        assert "hard_mode_unsupported" in aggregate
        assert "hard_mode_exact_rate" in aggregate
        assert "hard_mode_band" in aggregate
        assert hard_mode_pilot["failure_category_counts"]


class TestGenerationCrossChecks:
    def test_existing_140_generation_still_has_clean_layout(self):
        tasks140 = generate_discovery_140_tasks()
        summary = get_scoring_summary(tasks140)
        assert summary["total_tasks"] == 140
        assert summary["scored_total"] == 130
        assert summary["candidate_probe_total"] == 10
        assert summary["candidate_probe_counted_as_solved"] == 0
