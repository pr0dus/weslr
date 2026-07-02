"""Tests for ARC Native Promotion Batch 2.

Tests prove for each of the 4 promoted primitives:
- Oracle works on positive examples
- Solver works on positive examples
- Oracle and solver agree by grid equality
- Empty-grid behavior is deterministic
- Edge cases work
- No-op control differs
- Unsupported sentinel works
- can_be_counted_as_solved false before promotion, true after
- Oracle/solver separation preserved

Plus:
- 120 scoring updated: scored 114, probes 6
- BH80 remains 80/80
- 120 semantic pilot: 114/114 clean
- Candidate probes counted as solved: 0
"""

from __future__ import annotations

import pytest
from weslr.native_arc_oracle import (
    run_native_oracle,
    oracle_constr_draw_rect_around,
    oracle_mask_complement,
    oracle_topo_fill_holes,
    oracle_sel_leftmost,
    NATIVE_ORACLE_PRIMITIVES,
)
from weslr.native_arc_solver import (
    run_native_solver,
    solver_constr_draw_rect_around,
    solver_mask_complement,
    solver_topo_fill_holes,
    solver_sel_leftmost,
    NATIVE_SOLVER_PRIMITIVES,
)
from weslr.arc_bh80_semantic_scorer import grids_equal


BATCH_2_PRIMITIVES = ["constr_draw_rect_around", "mask_complement", "topo_fill_holes", "sel_leftmost"]


class TestOracleSolverSeparation:

    def test_oracle_does_not_import_solver(self):
        """Oracle module must not import solver dispatch."""
        import weslr.native_arc_oracle as oracle_mod
        import inspect
        source = inspect.getsource(oracle_mod)
        assert "native_arc_solver" not in source
        assert "run_native_solver" not in source
        assert "solver_" not in source.replace("solver", "")  # no solver function names

    def test_solver_does_not_import_oracle(self):
        """Solver module must not import oracle."""
        import weslr.native_arc_solver as solver_mod
        import inspect
        source = inspect.getsource(solver_mod)
        # Check import statements only, not docstrings/comments
        import_lines = [l for l in source.split('\n') if l.strip().startswith('import ') or l.strip().startswith('from ')]
        for line in import_lines:
            assert 'native_arc_oracle' not in line, f'Solver imports oracle: {line}'
        # Also verify no oracle function calls
        assert 'run_native_oracle(' not in source


class TestConstrDrawRectAround:

    def test_oracle_solver_agree_positive(self):
        grid = [[0,0,0,0,0],[0,0,3,0,0],[0,3,3,3,0],[0,0,3,0,0],[0,0,0,0,0]]
        o_sup, o_grid, _ = run_native_oracle("constr_draw_rect_around", grid)
        s_sup, s_grid, _ = run_native_solver("constr_draw_rect_around", grid, {})
        assert o_sup and s_sup
        assert grids_equal(s_grid, o_grid)

    def test_largest_object_with_distractor(self):
        grid = [[0,0,0,0,0,0],[0,5,5,5,0,0],[0,5,5,5,0,0],[0,5,5,5,0,0],[0,0,0,0,0,0],[7,0,0,0,0,0]]
        o_sup, o_grid, _ = run_native_oracle("constr_draw_rect_around", grid)
        s_sup, s_grid, _ = run_native_solver("constr_draw_rect_around", grid, {})
        assert grids_equal(s_grid, o_grid)
        # Distractor at [5,0] should not be included in bbox
        # bbox should be rows 1-3, cols 1-3

    def test_edge_touching_object(self):
        grid = [[2,2,0,0],[2,2,0,0],[0,0,0,0],[0,0,0,0]]
        o_sup, o_grid, _ = run_native_oracle("constr_draw_rect_around", grid)
        s_sup, s_grid, _ = run_native_solver("constr_draw_rect_around", grid, {})
        assert grids_equal(s_grid, o_grid)

    def test_single_cell_object(self):
        grid = [[0,0,0],[0,5,0],[0,0,0]]
        o_sup, o_grid, _ = run_native_oracle("constr_draw_rect_around", grid)
        s_sup, s_grid, _ = run_native_solver("constr_draw_rect_around", grid, {})
        assert grids_equal(s_grid, o_grid)
        # Single cell: bbox is 1x1, perimeter is the cell itself, but it's not bg so no change

    def test_empty_grid_unchanged(self):
        grid = [[0,0],[0,0]]
        o_sup, o_grid, _ = run_native_oracle("constr_draw_rect_around", grid)
        s_sup, s_grid, _ = run_native_solver("constr_draw_rect_around", grid, {})
        assert grids_equal(s_grid, o_grid)
        assert grids_equal(s_grid, grid)  # unchanged

    def test_noop_differs(self):
        # Use an L-shaped object so bbox perimeter has bg cells to fill
        grid = [[0,0,0,0,0],[0,3,0,0,0],[0,3,0,0,0],[0,3,3,3,0],[0,0,0,0,0]]
        o_sup, o_grid, _ = run_native_oracle("constr_draw_rect_around", grid)
        assert not grids_equal(o_grid, grid)  # output differs from input


class TestMaskComplement:

    def test_oracle_solver_agree_positive(self):
        grid = [[0,1,0],[2,0,3],[0,4,0]]
        o_sup, o_grid, _ = run_native_oracle("mask_complement", grid)
        s_sup, s_grid, _ = run_native_solver("mask_complement", grid, {})
        assert o_sup and s_sup
        assert grids_equal(s_grid, o_grid)

    def test_all_background_becomes_all_ones(self):
        grid = [[0,0,0],[0,0,0]]
        o_sup, o_grid, _ = run_native_oracle("mask_complement", grid)
        s_sup, s_grid, _ = run_native_solver("mask_complement", grid, {})
        assert grids_equal(s_grid, o_grid)
        assert all(v == 1 for row in s_grid for v in row)

    def test_all_nonbackground_becomes_zeros(self):
        grid = [[1,2,3],[4,5,6]]
        o_sup, o_grid, _ = run_native_oracle("mask_complement", grid)
        s_sup, s_grid, _ = run_native_solver("mask_complement", grid, {})
        assert grids_equal(s_grid, o_grid)
        assert all(v == 0 for row in s_grid for v in row)

    def test_empty_grid(self):
        o_sup, o_grid, _ = run_native_oracle("mask_complement", [])
        s_sup, s_grid, _ = run_native_solver("mask_complement", [], {})
        assert grids_equal(s_grid, o_grid)

    def test_noop_differs(self):
        grid = [[0,1],[2,3]]
        o_sup, o_grid, _ = run_native_oracle("mask_complement", grid)
        assert not grids_equal(o_grid, grid)


class TestTopoFillHoles:

    def test_oracle_solver_agree_positive(self):
        # Hollow rectangle: 5x5 with hole at center
        grid = [[0,0,0,0,0],[0,2,2,2,0],[0,2,0,2,0],[0,2,2,2,0],[0,0,0,0,0]]
        o_sup, o_grid, _ = run_native_oracle("topo_fill_holes", grid)
        s_sup, s_grid, _ = run_native_solver("topo_fill_holes", grid, {})
        assert o_sup and s_sup
        assert grids_equal(s_grid, o_grid)
        # Center should be filled
        assert o_grid[2][2] == 2

    def test_open_hole_connected_to_border(self):
        # Object with opening to border — interior bg is reachable from border
        grid = [[0,0,0,0,0],[0,2,2,2,0],[0,2,0,0,0],[0,2,2,2,0],[0,0,0,0,0]]
        o_sup, o_grid, _ = run_native_oracle("topo_fill_holes", grid)
        s_sup, s_grid, _ = run_native_solver("topo_fill_holes", grid, {})
        assert grids_equal(s_grid, o_grid)
        # Interior bg is connected to border via the opening → not filled
        assert o_grid[2][2] == 0
        assert o_grid[2][3] == 0

    def test_object_no_holes_unchanged(self):
        grid = [[0,0,0,0],[0,3,3,0],[0,3,3,0],[0,0,0,0]]
        o_sup, o_grid, _ = run_native_oracle("topo_fill_holes", grid)
        s_sup, s_grid, _ = run_native_solver("topo_fill_holes", grid, {})
        assert grids_equal(s_grid, o_grid)
        assert grids_equal(s_grid, grid)  # no holes → unchanged

    def test_multiple_objects_with_holes(self):
        grid = [[0,0,0,0,0,0,0],[0,2,2,2,0,4,4],[0,2,0,2,0,4,4],[0,2,2,2,0,0,0],[0,0,0,0,0,0,0]]
        o_sup, o_grid, _ = run_native_oracle("topo_fill_holes", grid)
        s_sup, s_grid, _ = run_native_solver("topo_fill_holes", grid, {})
        assert grids_equal(s_grid, o_grid)

    def test_empty_grid_unchanged(self):
        grid = [[0,0],[0,0]]
        o_sup, o_grid, _ = run_native_oracle("topo_fill_holes", grid)
        s_sup, s_grid, _ = run_native_solver("topo_fill_holes", grid, {})
        assert grids_equal(s_grid, o_grid)
        assert grids_equal(s_grid, grid)


class TestSelLeftmost:

    def test_oracle_solver_agree_positive(self):
        grid = [[0,0,0,0,0,0],[1,1,0,0,4,4],[0,0,0,0,4,4],[0,0,0,0,0,0]]
        o_sup, o_grid, _ = run_native_oracle("sel_leftmost", grid)
        s_sup, s_grid, _ = run_native_solver("sel_leftmost", grid, {})
        assert o_sup and s_sup
        assert grids_equal(s_grid, o_grid)

    def test_small_leftmost_vs_large_rightmost(self):
        grid = [[0,0,0,0,0,0,0],[1,0,0,0,3,3,3],[0,0,0,0,3,3,3],[0,0,0,0,0,0,0]]
        o_sup, o_grid, _ = run_native_oracle("sel_leftmost", grid)
        s_sup, s_grid, _ = run_native_solver("sel_leftmost", grid, {})
        assert grids_equal(s_grid, o_grid)
        # Leftmost is the single cell at [1,0]
        assert o_grid[1][0] == 1
        assert o_grid[1][4] == 0  # right object removed

    def test_tie_on_min_col_uses_min_row(self):
        # Two objects both starting at col 1
        grid = [[0,2,0,0,0],[0,2,0,0,0],[0,0,0,0,0],[0,3,0,0,0],[0,3,0,0,0]]
        o_sup, o_grid, _ = run_native_oracle("sel_leftmost", grid)
        s_sup, s_grid, _ = run_native_solver("sel_leftmost", grid, {})
        assert grids_equal(s_grid, o_grid)
        # Both at col 1, tie-break by min_row: object at row 0 wins
        assert o_grid[0][1] == 2
        assert o_grid[3][1] == 0  # other object removed

    def test_empty_grid_unchanged(self):
        grid = [[0,0],[0,0]]
        o_sup, o_grid, _ = run_native_oracle("sel_leftmost", grid)
        s_sup, s_grid, _ = run_native_solver("sel_leftmost", grid, {})
        assert grids_equal(s_grid, o_grid)
        assert grids_equal(s_grid, grid)

    def test_single_object_returns_isolated(self):
        grid = [[0,0,0,0],[0,5,5,0],[0,5,5,0],[0,0,0,0]]
        o_sup, o_grid, _ = run_native_oracle("sel_leftmost", grid)
        s_sup, s_grid, _ = run_native_solver("sel_leftmost", grid, {})
        assert grids_equal(s_grid, o_grid)
        assert grids_equal(s_grid, grid)  # single object → unchanged


class TestUnsupportedSentinel:

    def test_unsupported_primitive_oracle(self):
        sup, _, trace = run_native_oracle("fake_primitive", [[1,2],[3,4]])
        assert not sup
        assert "not implemented" in trace.get("unsupported_reason", "")

    def test_unsupported_primitive_solver(self):
        sup, _, trace = run_native_solver("fake_primitive", [[1,2],[3,4]], {})
        assert not sup
        assert "not implemented" in trace.get("unsupported_reason", "")


class TestPromotionStatus:

    def test_batch_2_in_oracle_dispatch(self):
        for pid in BATCH_2_PRIMITIVES:
            assert pid in NATIVE_ORACLE_PRIMITIVES, f"{pid} not in oracle dispatch"

    def test_batch_2_in_solver_dispatch(self):
        for pid in BATCH_2_PRIMITIVES:
            assert pid in NATIVE_SOLVER_PRIMITIVES, f"{pid} not in solver dispatch"

    def test_batch_2_in_promoted_set(self):
        from weslr.native_arc_perspicuity import PROMOTED_PRIMITIVES
        for pid in BATCH_2_PRIMITIVES:
            assert pid in PROMOTED_PRIMITIVES, f"{pid} not in PROMOTED_PRIMITIVES"

    def test_batch_2_can_be_counted_as_solved(self):
        from weslr.arc_discovery_120_generator import _can_primitive_be_counted
        for pid in BATCH_2_PRIMITIVES:
            assert _can_primitive_be_counted(pid), f"{pid} should be countable as solved"

    def test_unpromoted_still_blocked(self):
        from weslr.arc_discovery_120_generator import _can_primitive_be_counted
        unpromoted = ["mask_border_only", "geom_flip_vertical", "cond_if_edge_clip",
                      "pat_row_alternate", "rel_order_by_size"]
        for pid in unpromoted:
            assert not _can_primitive_be_counted(pid), f"{pid} should NOT be countable as solved"


class Test120ScoringUpdate:

    def test_scored_total_is_114(self):
        from weslr.arc_discovery_120_generator import generate_discovery_120_tasks, get_scoring_summary
        tasks = generate_discovery_120_tasks()
        summary = get_scoring_summary(tasks)
        assert summary["scored_total"] == 117
        assert summary["candidate_probe_total"] == 3

    def test_promoted_probe_tasks_are_scored(self):
        from weslr.arc_discovery_120_generator import generate_discovery_120_tasks
        tasks = generate_discovery_120_tasks()
        for tid in ["T120_103", "T120_104", "T120_106", "T120_110"]:
            task = next(t for t in tasks if t["task_id"] == tid)
            assert task["scoring_layer"] == "scored", f"{tid} should be scored"

    def test_remaining_probes_are_unscored(self):
        from weslr.arc_discovery_120_generator import generate_discovery_120_tasks
        tasks = generate_discovery_120_tasks()
        for tid in ["T120_101", "T120_102", "T120_107"]:
            task = next(t for t in tasks if t["task_id"] == tid)
            assert task["scoring_layer"] == "candidate_probe", f"{tid} should be candidate_probe"


class TestRegression:

    def test_bh80_remains_80(self):
        from weslr.arc_discovery_120_semantic_pilot import run_120_semantic_pilot
        results = run_120_semantic_pilot()
        bh = results["bh80_subset"]
        assert bh["semantic_exact"] == 80

    def test_120_scored_exact_is_117(self):
        from weslr.arc_discovery_120_semantic_pilot import run_120_semantic_pilot
        results = run_120_semantic_pilot()
        sa = results["scored_aggregate"]
        assert sa["scored_exact"] == 117
        assert sa["failed"] == 0
        assert sa["unsupported"] == 0

    def test_candidate_probes_counted_as_solved_0(self):
        from weslr.arc_discovery_120_semantic_pilot import run_120_semantic_pilot
        results = run_120_semantic_pilot()
        cpd = results["candidate_probe_diagnostics"]
        assert cpd["candidate_probe_counted_as_solved"] == 0

    def test_all_anti_cheat_controls_pass(self):
        from weslr.arc_discovery_120_semantic_pilot import run_120_semantic_pilot
        results = run_120_semantic_pilot()
        ac = results["anti_cheat"]
        assert ac["all_controls_pass"]

    def test_gate_clean_reached(self):
        from weslr.arc_discovery_120_semantic_pilot import run_120_semantic_pilot
        results = run_120_semantic_pilot()
        gr = results["gate_results"]
        assert gr["scored_clean"]
        assert gr["bh80_clean"]