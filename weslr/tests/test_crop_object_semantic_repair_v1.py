"""Focused tests for crop_object oracle/solver semantic alignment repair.

Tests that crop_object:
1. Crops to largest connected component bbox (not all non-bg bbox)
2. Handles distractor presence correctly
3. Matches oracle semantics on T120_084-style chains
4. Matches oracle semantics on T120_093-style chains
5. BH80 regression: tasks with crop_object remain exact
6. 120 scored result is 110/110
7. Candidate probes remain unscored (0 counted as solved)
"""

from __future__ import annotations

import pytest
from weslr.arc_bh80_oracle import reference_primitive, run_oracle_pipeline
from weslr.arc_synthetic_3_step_real_dispatch import run_primitive
from weslr.arc_bh80_materializer import materialize_scene
from weslr.arc_bh80_semantic_scorer import grids_equal
from weslr.arc_discovery_120_generator import generate_discovery_120_tasks
from weslr.arc_discovery_120_semantic_pilot import (
    combined_oracle_pipeline,
    combined_solver_pipeline,
    run_120_semantic_pilot,
)


class TestCropObjectLargestComponentBbox:
    """Test that crop_object crops to the largest connected component bbox."""

    def test_crop_object_single_object_no_distractors(self):
        """With one object, crop_object should crop to that object's bbox."""
        grid = [
            [0, 0, 0, 0, 0],
            [0, 2, 2, 0, 0],
            [0, 2, 2, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
        o_sup, o_grid, _ = reference_primitive("crop_object", grid, {})
        s_sup, s_grid, _ = run_primitive("crop_object", grid, {})
        assert s_sup and o_sup
        assert grids_equal(s_grid, o_grid)
        assert len(o_grid) == 2 and len(o_grid[0]) == 2

    def test_crop_object_with_distractor_crops_to_largest(self):
        """With a distractor, crop_object should crop to the largest component only."""
        grid = [
            [0, 0, 0, 0, 0, 0],
            [0, 3, 3, 3, 0, 0],
            [0, 3, 3, 3, 0, 0],
            [0, 3, 3, 3, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [8, 0, 0, 0, 0, 0],
        ]
        o_sup, o_grid, _ = reference_primitive("crop_object", grid, {})
        s_sup, s_grid, _ = run_primitive("crop_object", grid, {})
        assert s_sup and o_sup
        assert grids_equal(s_grid, o_grid), f"Oracle: {o_grid}, Solver: {s_grid}"
        # Should be 3x3 (largest component), not 6x6 or 5x4 (all non-bg)
        assert len(o_grid) == 3 and len(o_grid[0]) == 3

    def test_crop_object_distractor_at_edge(self):
        """Distractor at grid edge should not expand the crop bbox."""
        grid = [
            [0, 0, 0, 0, 0],
            [0, 4, 4, 4, 0],
            [0, 4, 4, 4, 0],
            [0, 4, 4, 4, 0],
            [0, 0, 0, 0, 7],
        ]
        o_sup, o_grid, _ = reference_primitive("crop_object", grid, {})
        s_sup, s_grid, _ = run_primitive("crop_object", grid, {})
        assert s_sup and o_sup
        assert grids_equal(s_grid, o_grid), f"Oracle: {o_grid}, Solver: {s_grid}"
        assert len(o_grid) == 3 and len(o_grid[0]) == 3

    def test_crop_object_empty_grid(self):
        """Empty grid (all background) should be handled gracefully."""
        grid = [[0, 0], [0, 0]]
        o_sup, o_grid, _ = reference_primitive("crop_object", grid, {})
        s_sup, s_grid, _ = run_primitive("crop_object", grid, {})
        assert s_sup and o_sup
        assert grids_equal(s_grid, o_grid)

    def test_crop_object_multiple_equal_components(self):
        """Multiple equal-sized components: largest is still well-defined."""
        grid = [
            [0, 0, 0, 0, 0],
            [0, 1, 1, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 2, 2],
            [0, 0, 0, 0, 0],
        ]
        o_sup, o_grid, _ = reference_primitive("crop_object", grid, {})
        s_sup, s_grid, _ = run_primitive("crop_object", grid, {})
        assert s_sup and o_sup
        assert grids_equal(s_grid, o_grid), f"Oracle: {o_grid}, Solver: {s_grid}"


class TestT120Chains:

    def test_t120_084_chain_crop_color_invert_place_back(self):
        """T120_084: crop_object → color_invert → place_back should match oracle."""
        tasks = generate_discovery_120_tasks()
        task = next(t for t in tasks if t["task_id"] == "T120_084")
        grid = materialize_scene(task["scene_spec"], "T120_084")
        prims = task["primitive_sequence"]

        o_sup, o_grid, _ = combined_oracle_pipeline(prims, grid)
        s_sup, s_grid = combined_solver_pipeline(grid, prims)

        assert o_sup and s_sup
        assert grids_equal(s_grid, o_grid), f"Oracle: {o_grid}, Solver: {s_grid}"

    def test_t120_093_chain_crop_mirror_recolor_boundary(self):
        """T120_093: crop_object → mirror_object → recolor_boundary should match oracle."""
        tasks = generate_discovery_120_tasks()
        task = next(t for t in tasks if t["task_id"] == "T120_093")
        grid = materialize_scene(task["scene_spec"], "T120_093")
        prims = task["primitive_sequence"]

        o_sup, o_grid, _ = combined_oracle_pipeline(prims, grid)
        s_sup, s_grid = combined_solver_pipeline(grid, prims)

        assert o_sup and s_sup
        assert grids_equal(s_grid, o_grid), f"Oracle: {o_grid}, Solver: {s_grid}"


class TestBH80Regression:

    def test_bh80_crop_object_tasks_remain_exact(self):
        """All BH80 tasks using crop_object must remain semantic_exact."""
        tasks = generate_discovery_120_tasks()
        crop_tasks = [
            t for t in tasks
            if "crop_object" in t["primitive_sequence"]
            and t["task_id"].startswith("BH80_")
        ]
        assert len(crop_tasks) == 5, f"Expected 5 BH80 crop_object tasks, got {len(crop_tasks)}"

        for task in crop_tasks:
            grid = materialize_scene(task["scene_spec"], task["task_id"])
            prims = task["primitive_sequence"]
            o_sup, o_grid, _ = combined_oracle_pipeline(prims, grid)
            s_sup, s_grid = combined_solver_pipeline(grid, prims)
            assert o_sup and s_sup, f"{task['task_id']}: oracle/solver unsupported"
            assert grids_equal(s_grid, o_grid), f"{task['task_id']}: grid mismatch"

    def test_bh80_full_80_remain_80(self):
        """Full BH80 subset must remain 80/80 semantic_exact."""
        tasks = generate_discovery_120_tasks()
        bh80_tasks = [t for t in tasks if t["task_id"].startswith("BH80_")]
        assert len(bh80_tasks) == 80

        exact = 0
        for task in bh80_tasks:
            grid = materialize_scene(task["scene_spec"], task["task_id"])
            prims = task["primitive_sequence"]
            o_sup, o_grid, _ = combined_oracle_pipeline(prims, grid)
            s_sup, s_grid = combined_solver_pipeline(grid, prims)
            if o_sup and s_sup and grids_equal(s_grid, o_grid):
                exact += 1

        assert exact == 80, f"BH80 regression: {exact}/80 (expected 80)"


class Test120ScoredResult:

    def test_120_scored_exact_is_110(self):
        """Full 120 semantic pilot must produce 110/110 scored_exact."""
        results = run_120_semantic_pilot()
        sa = results["scored_aggregate"]
        assert sa["scored_exact"] == 110, f"Expected 110/110, got {sa['scored_exact']}/110"
        assert sa["failed"] == 0
        assert sa["unsupported"] == 0

    def test_120_candidate_probes_not_counted_as_solved(self):
        """Candidate probes must not be counted as solved."""
        results = run_120_semantic_pilot()
        cpd = results["candidate_probe_diagnostics"]
        assert cpd["candidate_probe_counted_as_solved"] == 0

    def test_120_all_anti_cheat_controls_pass(self):
        """All 13 anti-cheat controls must pass."""
        results = run_120_semantic_pilot()
        ac = results["anti_cheat"]
        assert ac["all_controls_pass"], f"Anti-cheat failed: {ac}"

    def test_120_gate_clean_reached(self):
        """Scored clean gate (110/110) must be reached."""
        results = run_120_semantic_pilot()
        gr = results["gate_results"]
        assert gr["scored_clean"], "Scored clean gate not reached"
        assert gr["bh80_clean"], "BH80 clean gate not reached"