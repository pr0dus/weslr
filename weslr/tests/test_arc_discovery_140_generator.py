"""Tests for ARC Synthetic Discovery 140 Generator and Semantic Pilot.

Validates:
- Exactly 140 tasks generated
- 130 scored / 10 candidate-probe
- 117 scored base preserved
- 13 new scored tasks added
- 3 old probes remain unscored
- 7 new probes are unscored
- Candidate probes counted as solved stays 0
- All 8 promoted natives appear in at least 2 new scored tasks
- No default [[1]] scenes
- Scene specs exist and materialize
- Canonical probe reconciliation matches section 7.2
- Anti-cheat controls 14–18 pass
- BH80 remains 80/80
- Previous 117 base remains 117/117 in the pilot
- The 130 scored pilot is clean if the current implementation supports it
"""

from __future__ import annotations

import pytest

from weslr.arc_discovery_120_generator import generate_discovery_120_tasks
from weslr.arc_discovery_140_generator import (
    CANONICAL_NEW_PROBE_TABLE,
    PROMOTED_NATIVE_PRIMITIVES,
    generate_discovery_140_tasks,
    get_scored_tasks,
    get_candidate_probe_tasks,
    get_scoring_summary,
    get_gate_definitions,
    check_no_default_ones,
    check_candidate_probe_separation,
    check_unpromoted_blocked,
    check_all_three_steps,
    check_duplicate_risk_probe_separation,
    check_promoted_native_generalization_coverage,
    check_cc_divergence_sentinel,
    check_native_chain_order_sensitivity,
    anti_cheat_readiness,
    SCORED,
    CANDIDATE_PROBE,
)
from weslr.arc_discovery_140_semantic_pilot import run_140_semantic_pilot
from weslr.arc_bh80_materializer import materialize_scene
from weslr.arc_synthetic_3_step_task_schema import generate_broad_hard_80_tasks


@pytest.fixture(scope="module")
def tasks140():
    return generate_discovery_140_tasks()


@pytest.fixture(scope="module")
def base120_tasks():
    return generate_discovery_120_tasks()


@pytest.fixture(scope="module")
def bh80_tasks():
    return generate_broad_hard_80_tasks()


@pytest.fixture(scope="module")
def pilot140():
    return run_140_semantic_pilot()


class TestTotalCounts:
    def test_exactly_140_tasks(self, tasks140):
        assert len(tasks140) == 140

    def test_scoring_totals(self, tasks140):
        summary = get_scoring_summary(tasks140)
        assert summary["total_tasks"] == 140
        assert summary["scored_total"] == 130
        assert summary["candidate_probe_total"] == 10
        assert summary["previous_scored_base_total"] == 117
        assert summary["new_scored_expansion_total"] == 13
        assert summary["old_probe_total"] == 3
        assert summary["new_probe_total"] == 7

    def test_task_id_layout(self, tasks140):
        ids = [t["task_id"] for t in tasks140]
        assert ids[:120] == [t["task_id"] for t in generate_discovery_120_tasks()]
        assert ids[120:133] == [f"T140_{i}" for i in range(121, 134)]
        assert ids[133:] == [f"T140_{i}" for i in range(134, 141)]


class TestScoringLayers:
    def test_scored_and_probe_counts(self, tasks140):
        assert len(get_scored_tasks(tasks140)) == 130
        assert len(get_candidate_probe_tasks(tasks140)) == 10

    def test_previous_base_is_still_117_scored(self, tasks140):
        prev = [t for t in tasks140 if not t["task_id"].startswith("T140_") and t["scoring_layer"] == SCORED]
        assert len(prev) == 117

    def test_new_expansion_is_13_scored(self, tasks140):
        new = [t for t in tasks140 if t["task_id"].startswith("T140_") and 121 <= int(t["task_id"].split("_")[1]) <= 133]
        assert len(new) == 13
        assert all(t["scoring_layer"] == SCORED for t in new)

    def test_old_probes_remain_unscored(self, tasks140):
        for tid in ["T120_101", "T120_102", "T120_107"]:
            t = next(task for task in tasks140 if task["task_id"] == tid)
            assert t["scoring_layer"] == CANDIDATE_PROBE
            meta = t.get("candidate_probe", {})
            assert meta.get("candidate_probe") is True
            assert meta.get("unpromoted") is True
            assert meta.get("can_be_counted_as_solved") is False

    def test_new_probes_remain_unscored(self, tasks140):
        for tid in [f"T140_{i}" for i in range(134, 141)]:
            t = next(task for task in tasks140 if task["task_id"] == tid)
            assert t["scoring_layer"] == CANDIDATE_PROBE
            meta = t.get("candidate_probe", {})
            assert meta.get("candidate_probe") is True
            assert meta.get("unpromoted") is True
            assert meta.get("can_be_counted_as_solved") is False
            assert meta.get("duplicate_risk", 1.0) < 0.50


class TestCanonicalProbeReconciliation:
    def test_canonical_probe_table(self):
        assert CANONICAL_NEW_PROBE_TABLE == [
            ("T140_134", "geom_scale_2x"),
            ("T140_135", "topo_merge_objects"),
            ("T140_136", "constr_connect_line"),
            ("T140_137", "constr_copy_to_pos"),
            ("T140_138", "pat_color_cycle"),
            ("T140_139", "cond_if_edge_clip"),
            ("T140_140", "topo_split_at_gap"),
        ]

    def test_canonical_probe_ids_and_primitives(self, tasks140):
        for tid, primitive in CANONICAL_NEW_PROBE_TABLE:
            t = next(task for task in tasks140 if task["task_id"] == tid)
            meta = t.get("candidate_probe", {})
            assert meta.get("candidate_primitive_id") == primitive
            assert primitive in t["primitive_sequence"]


class TestPromotedCoverage:
    def test_all_promoted_natives_present(self):
        assert PROMOTED_NATIVE_PRIMITIVES == {
            "color_invert",
            "constr_draw_rect_around",
            "mask_complement",
            "topo_fill_holes",
            "sel_leftmost",
            "cond_if_holes_fill",
            "rel_swap_positions",
            "color_swap_1_2",
        }

    def test_each_promoted_native_appears_at_least_twice_in_new_scored(self, tasks140):
        new_scored = [t for t in tasks140 if t["task_id"].startswith("T140_") and 121 <= int(t["task_id"].split("_")[1]) <= 133]
        counts = {p: 0 for p in PROMOTED_NATIVE_PRIMITIVES}
        for t in new_scored:
            seq = t["primitive_sequence"]
            for p in PROMOTED_NATIVE_PRIMITIVES:
                if p in seq:
                    counts[p] += 1
        assert all(v >= 2 for v in counts.values()), counts


class TestSceneSpecs:
    def test_no_default_ones(self, tasks140):
        assert check_no_default_ones(tasks140)

    def test_all_tasks_have_scene_specs(self, tasks140):
        for t in tasks140:
            spec = t.get("scene_spec")
            assert spec is not None
            assert isinstance(spec, dict)
            assert "grid_size" in spec
            assert "initial_objects" in spec

    def test_all_scene_specs_materialize(self, tasks140):
        for t in tasks140:
            grid = materialize_scene(t["scene_spec"], t["task_id"])
            assert isinstance(grid, list)
            assert grid
            assert all(isinstance(row, list) for row in grid)
            assert all(isinstance(v, int) for row in grid for v in row)

    def test_scene_diversity(self, tasks140):
        sizes = {(t["scene_spec"]["grid_size"][0], t["scene_spec"]["grid_size"][1]) for t in tasks140 if t["task_id"].startswith("T140_")}
        assert len(sizes) >= 3


class TestAntiCheatControls:
    def test_base_controls(self, tasks140):
        assert check_candidate_probe_separation(tasks140)
        assert check_unpromoted_blocked(tasks140)
        assert check_all_three_steps(tasks140)

    def test_expansion_controls(self, tasks140):
        assert check_duplicate_risk_probe_separation(tasks140)
        assert check_promoted_native_generalization_coverage(tasks140)
        assert check_cc_divergence_sentinel(tasks140)
        assert check_native_chain_order_sensitivity(tasks140)

    def test_full_anti_cheat_readiness(self, tasks140):
        checks = anti_cheat_readiness(tasks140)
        assert checks["duplicate_risk_probe_separation"] is True
        assert checks["promoted_native_generalization_coverage"] is True
        assert checks["cc_divergence_sentinel"] is True
        assert checks["native_chain_order_sensitivity"] is True
        assert checks["candidate_probe_non_counting_proof"] is True
        assert checks["all_controls_pass"] is True


class TestBH80Preservation:
    def test_bh80_subset_preserved(self, tasks140, bh80_tasks):
        bh80 = [t for t in tasks140 if t["task_id"].startswith("BH80_")]
        assert len(bh80) == 80
        for i in range(80):
            assert bh80[i]["task_id"] == bh80_tasks[i]["task_id"]
            assert bh80[i]["family_id"] == bh80_tasks[i]["family_id"]
            assert bh80[i]["primitive_sequence"] == bh80_tasks[i]["primitive_sequence"]
            assert bh80[i]["scene_spec"] == bh80_tasks[i]["scene_spec"]


class TestPilotResults:
    def test_pilot_result_structure(self, pilot140):
        assert pilot140["summary"]["total_tasks"] == 140
        assert pilot140["summary"]["scored_total"] == 130
        assert pilot140["summary"]["candidate_probe_total"] == 10

    def test_pilot_subset_results(self, pilot140):
        assert pilot140["bh80_subset"]["semantic_exact"] == 80
        assert pilot140["previous_117_scored_base"]["semantic_exact"] == 117
        assert pilot140["new_13_scored_expansion"]["semantic_exact"] == 13

    def test_candidate_probe_diagnostics(self, pilot140):
        cpd = pilot140["candidate_probe_diagnostics"]
        assert cpd["candidate_probe_total"] == 10
        assert cpd["candidate_probe_executed"] == 10
        assert cpd["candidate_probe_counted_as_solved"] == 0
        assert cpd["candidate_probe_oracle_solver_agree"] == 0

    def test_pilot_clean_if_supported(self, pilot140):
        sa = pilot140["scored_aggregate"]
        gr = pilot140["gate_results"]
        assert sa["scored_total"] == 130
        assert sa["scored_exact"] == 130
        assert sa["failed"] == 0
        assert sa["unsupported"] == 0
        assert gr["scored_clean"] is True
        assert gr["scored_preferred"] is True
        assert gr["scored_strong"] is True
        assert gr["scored_minimal"] is True
        assert gr["bh80_clean"] is True
        assert gr["previous_117_scored_base_clean"] is True
        assert gr["new_13_scored_expansion_clean"] is True
        assert gr["candidate_probe_counted_as_solved_zero"] is True

    def test_pilot_anti_cheat_controls(self, pilot140):
        ac = pilot140["anti_cheat"]
        assert ac["all_controls_pass"] is True
        assert ac["candidate_probe_non_counting_proof"] is True
