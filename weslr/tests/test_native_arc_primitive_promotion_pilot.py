"""Tests for WESLR native primitive promotion pilot — color_invert."""

import pytest
from weslr.native_arc_oracle import run_native_oracle, oracle_color_invert
from weslr.native_arc_solver import run_native_solver, solver_color_invert
from weslr.native_arc_promotion_pilot import (
    create_initial_candidate, run_promotion_pilot, produce_audit_bundle,
    POSITIVE_EXAMPLES, NEGATIVE_CONTROLS,
)
from weslr.native_arc_language_schema import PromotionStage, reject_unvalidated_as_solved
from weslr.arc_bh80_semantic_scorer import grids_equal


class TestOracleColorInvert:
    def test_simple(self):
        sup, out, _ = oracle_color_invert([[0, 1, 0], [0, 0, 0], [0, 2, 0]])
        assert sup
        assert out == [[0, 9, 0], [0, 0, 0], [0, 8, 0]]

    def test_background_unchanged(self):
        sup, out, _ = oracle_color_invert([[0, 0, 0], [0, 0, 0]])
        assert out == [[0, 0, 0], [0, 0, 0]]  # all bg stays unchanged

    def test_multi_color(self):
        sup, out, _ = oracle_color_invert([[1, 2, 3], [0, 4, 5]])
        assert out == [[9, 8, 7], [0, 6, 5]]

    def test_empty_grid(self):
        sup, out, _ = oracle_color_invert([])
        assert sup
        assert out == []

    def test_color_9_edge(self):
        sup, out, _ = oracle_color_invert([[9, 0], [0, 1]])
        assert out == [[1, 0], [0, 9]]

    def test_deterministic(self):
        grid = [[1, 2], [3, 0]]
        _, out1, _ = oracle_color_invert(grid)
        _, out2, _ = oracle_color_invert(grid)
        assert out1 == out2


class TestSolverColorInvert:
    def test_matches_oracle(self):
        for example in POSITIVE_EXAMPLES:
            _, o_out, _ = run_native_oracle("color_invert", example["input"])
            _, s_out, _ = run_native_solver("color_invert", example["input"], {})
            assert grids_equal(s_out, o_out), f"Mismatch on {example['name']}"

    def test_unsupported(self):
        sup, _, _ = run_native_solver("nonexistent", [[1]], {})
        assert not sup


class TestOracleSolverSeparation:
    def test_oracle_does_not_import_solver(self):
        import weslr.native_arc_oracle as om
        src = open(om.__file__).read()
        assert "import weslr.native_arc_solver" not in src
        assert "from weslr.native_arc_solver" not in src
        assert "import weslr.arc_synthetic_3_step_real_dispatch" not in src
        assert "from weslr.arc_synthetic_3_step_real_dispatch" not in src

    def test_solver_does_not_import_oracle(self):
        import weslr.native_arc_solver as sm
        src = open(sm.__file__).read()
        assert "import weslr.native_arc_oracle" not in src
        assert "from weslr.native_arc_oracle" not in src


class TestPromotionPilot:
    def test_candidate_cannot_be_solved_before_promotion(self):
        c = create_initial_candidate()
        assert not c.can_be_counted_as_solved()
        assert reject_unvalidated_as_solved(c)

    def test_full_promotion_succeeds(self):
        c, audit, summary = run_promotion_pilot()
        assert c.promotion_stage == PromotionStage.PROMOTED
        assert c.can_be_counted_as_solved()
        assert not reject_unvalidated_as_solved(c)

    def test_all_stages_completed(self):
        c, _, _ = run_promotion_pilot()
        required = {
            PromotionStage.GENERATED, PromotionStage.TYPED,
            PromotionStage.EXECUTABLE, PromotionStage.ORACLE_DEFINED,
            PromotionStage.SOLVER_TARGETED, PromotionStage.TESTED,
            PromotionStage.ANTI_CHEAT_VALIDATED, PromotionStage.REGRESSION_SAFE,
            PromotionStage.PROMOTED,
        }
        assert required.issubset(c.completed_stages)

    def test_oracle_verified(self):
        c, _, _ = run_promotion_pilot()
        assert c.oracle_execution_status == "verified"

    def test_solver_verified(self):
        c, _, _ = run_promotion_pilot()
        assert c.solver_execution_status == "verified"


class TestAuditArtifacts:
    def test_audit_bundle_complete(self):
        c, audit, _ = run_promotion_pilot()
        audit.validate_completeness()  # should not raise

    def test_audit_has_all_12_artifacts(self):
        c, audit, _ = run_promotion_pilot()
        assert audit.serialized_internal_expression
        assert audit.content_hash
        assert audit.type_signature
        assert len(audit.deterministic_execution_trace) >= 3
        assert len(audit.input_output_examples) >= 3
        assert len(audit.oracle_output) >= 3
        assert len(audit.solver_output) >= 3
        assert len(audit.grid_equality_result) >= 3
        assert len(audit.invariant_checks) >= 1
        assert len(audit.negative_control_results) >= 1
        assert audit.regression_impact_summary
        # human_summary is optional but we provide one
        assert audit.human_summary is not None

    def test_all_grids_equal(self):
        c, audit, _ = run_promotion_pilot()
        for result in audit.grid_equality_result:
            assert result["grids_equal"] is True, f"Grid equality failed for {result.get('example', '?')}"


class TestAntiCheat:
    def test_noop_differs(self):
        test_input = [[0, 1, 0], [0, 0, 0]]
        _, real_out, _ = run_native_oracle("color_invert", test_input)
        noop_out = [row[:] for row in test_input]
        assert not grids_equal(real_out, noop_out)

    def test_unsupported_sentinel(self):
        o_sup, _, _ = run_native_oracle("fake_prim", [[1]])
        s_sup, _, _ = run_native_solver("fake_prim", [[1]], {})
        assert not o_sup
        assert not s_sup

    def test_output_diversity(self):
        outputs = set()
        for example in POSITIVE_EXAMPLES:
            _, out, _ = run_native_oracle("color_invert", example["input"])
            outputs.add(str(out))
        assert len(outputs) >= 3


class TestBH80Unchanged:
    def test_bh80_remains_80_80(self):
        from weslr.arc_synthetic_3_step_task_schema import generate_broad_hard_80_tasks
        from weslr.arc_bh80_enriched_scenes import get_enriched_scene_spec
        from weslr.arc_bh80_materializer import materialize_scene
        from weslr.arc_bh80_oracle import run_oracle_pipeline
        from weslr.arc_bh80_solver_adapter import solver_run_with_input

        tasks = generate_broad_hard_80_tasks()
        se = 0
        for t in tasks:
            t["scene_spec"] = get_enriched_scene_spec(t["task_id"])
            ig = materialize_scene(t["scene_spec"], t["task_id"])
            _, og, _ = run_oracle_pipeline(t["primitive_sequence"], ig)
            ss, sg = solver_run_with_input(ig, t["primitive_sequence"])
            if ss and grids_equal(sg, og):
                se += 1
        assert se == 80, f"BH80 regression: expected 80, got {se}"