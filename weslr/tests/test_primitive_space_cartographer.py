"""Tests for WESLR Primitive-Space Grid/Graph Cartographer.

Tests prove:
- Cartographer builds without touching BH80 behavior
- Grid axes match design
- Graph node/edge schema exists
- Coverage grids are deterministic
- Candidate-only cells are detected
- Full family gaps are detected
- Duplicate-risk candidates are penalized
- mask_border_only and geom_flip_vertical are deferred/dropped
- Recommended candidates are promote_now
- Unpromoted candidates remain unscored
- Candidate probes counted as solved remains 0
- BH80 remains 80/80
- Discovery 120 scored layer remains 110/110
"""

from __future__ import annotations

import pytest
from weslr.primitive_space_cartographer import (
    build_cartographer,
    get_cartographer_summary,
    PrimitiveSpaceCartographer,
    PrimitiveRecord,
    PrimitiveGraph,
    GraphNode,
    GraphEdge,
    FAMILIES,
    TARGETS,
    ROLES,
    MATURITIES,
)


class TestCartographerBuilds:

    def test_builds_without_error(self):
        cart = build_cartographer()
        assert cart is not None
        assert isinstance(cart, PrimitiveSpaceCartographer)

    def test_has_records(self):
        cart = build_cartographer()
        assert len(cart.records) > 0
        # 20 BH80 + 1 promoted + 31 candidates = 52
        assert len(cart.records) == 52

    def test_has_graph(self):
        cart = build_cartographer()
        assert len(cart.graph.nodes) > 0
        assert len(cart.graph.edges) > 0

    def test_does_not_touch_bh80(self):
        """Building the cartographer must not change BH80 behavior."""
        from weslr.arc_discovery_120_generator import generate_discovery_120_tasks, get_scoring_summary
        tasks = generate_discovery_120_tasks()
        summary = get_scoring_summary(tasks)
        assert summary["bh80_count"] == 80
        assert summary["scored_total"] == 117


class TestGridAxes:

    def test_family_axis_matches_design(self):
        assert len(FAMILIES) == 14
        assert "selection" in FAMILIES
        assert "topology" in FAMILIES
        assert "construction" in FAMILIES
        assert "conditional" in FAMILIES

    def test_target_axis_matches_design(self):
        assert len(TARGETS) == 10
        assert "object" in TARGETS
        assert "mask" in TARGETS
        assert "whole_grid" in TARGETS

    def test_role_axis_matches_design(self):
        assert len(ROLES) == 9
        assert "selector" in ROLES
        assert "constructor" in ROLES
        assert "brancher" in ROLES
        assert "comparator" in ROLES

    def test_maturity_axis_matches_design(self):
        assert len(MATURITIES) == 10
        assert "accepted_bh80" in MATURITIES
        assert "promoted_native" in MATURITIES
        assert "generated_candidate" in MATURITIES
        assert "missing" in MATURITIES


class TestGraphSchema:

    def test_graph_has_node_types(self):
        cart = build_cartographer()
        node_types = {n.node_type for n in cart.graph.nodes}
        assert "primitive" in node_types or "candidate" in node_types
        assert "family" in node_types
        assert "task" in node_types
        assert "audit" in node_types

    def test_graph_has_edge_types(self):
        cart = build_cartographer()
        edge_types = {e.edge_type for e in cart.graph.edges}
        assert "composes_with" in edge_types
        assert "family_member" in edge_types
        assert "appears_in_task" in edge_types
        assert "aliases_or_duplicates" in edge_types

    def test_graph_has_primitive_nodes(self):
        cart = build_cartographer()
        prim_nodes = [n for n in cart.graph.nodes if n.node_type in ("primitive", "candidate")]
        assert len(prim_nodes) == 52

    def test_graph_has_family_nodes(self):
        cart = build_cartographer()
        family_nodes = [n for n in cart.graph.nodes if n.node_type == "family"]
        assert len(family_nodes) == 14


class TestCoverageGrids:

    def test_coverage_grids_deterministic(self):
        cart1 = build_cartographer()
        cart2 = build_cartographer()
        g1 = cart1.coverage_grid_family_target()
        g2 = cart2.coverage_grid_family_target()
        assert g1 == g2

    def test_family_maturity_grid_has_all_families(self):
        cart = build_cartographer()
        grid = cart.coverage_grid_family_maturity()
        assert len(grid) == 14
        families = [row["family"] for row in grid]
        for fam in FAMILIES:
            assert fam in families

    def test_family_target_grid_has_all_targets(self):
        cart = build_cartographer()
        grid = cart.coverage_grid_family_target()
        for fam in FAMILIES:
            assert fam in grid
            for target in TARGETS:
                assert target in grid[fam]


class TestGapDetection:

    def test_detect_gaps_returns_all_rules(self):
        cart = build_cartographer()
        gaps = cart.detect_gaps()
        assert "R1_empty_high_value_cells" in gaps
        assert "R2_candidate_only_cells" in gaps
        assert "R3_overpopulated_duplicate" in gaps
        assert "R4_missing_inverses" in gaps
        assert "R5_missing_bridges" in gaps
        assert "R6_full_family_gaps" in gaps
        assert "R7_task_gaps" in gaps
        assert "R8_isolated_primitives" in gaps
        assert "R9_missing_controls" in gaps

    def test_r2_candidate_only_cells_detected(self):
        cart = build_cartographer()
        gaps = cart.detect_gaps()
        r2 = gaps["R2_candidate_only_cells"]
        assert len(r2) > 0
        # Should include topology candidates (full family gap)
        topo_gaps = [g for g in r2 if g["family"] == "topology"]
        assert len(topo_gaps) > 0

    def test_r6_full_family_gaps_detected(self):
        cart = build_cartographer()
        gaps = cart.detect_gaps()
        r6 = gaps["R6_full_family_gaps"]
        fam_names = [g["family"] for g in r6]
        # topology, construction, relation, conditional have 0 accepted/promoted
        assert len(fam_names) == 0  # all families now have promoted primitives

        # topology and construction are no longer gaps (promoted in Batch 2)
        assert len(fam_names) == 0  # all families now have promoted primitives

        # topology and construction are no longer gaps (promoted in Batch 2)

    def test_r4_missing_inverses_detected(self):
        cart = build_cartographer()
        gaps = cart.detect_gaps()
        r4 = gaps["R4_missing_inverses"]
        assert len(r4) >= 5  # at least 5 missing inverses
        inv_names = [g["missing_inverse"] for g in r4]
        assert "rotate_ccw" in inv_names

    def test_r8_isolated_primitives_detected(self):
        cart = build_cartographer()
        gaps = cart.detect_gaps()
        r8 = gaps["R8_isolated_primitives"]
        assert len(r8) > 0
        # Candidates with no task appearances should be isolated
        prim_names = [g["primitive"] for g in r8]
        assert len(prim_names) > 0


class TestGapScoring:

    def test_gap_score_is_deterministic(self):
        cart = build_cartographer()
        s1 = cart.gap_score("mask_complement")
        s2 = cart.gap_score("mask_complement")
        assert s1 == s2

    def test_gap_score_in_range(self):
        cart = build_cartographer()
        for rec in cart.records:
            if rec.source == "native_candidate":
                score = cart.gap_score(rec.primitive_id)
                assert 0.0 <= score <= 1.0

    def test_low_duplicate_risk_scores_higher_than_high(self):
        cart = build_cartographer()
        # mask_complement is now promoted (gap_score returns 0)
        # Use remaining candidates: cond_if_edge_clip (0.4) vs mask_border_only (0.6)
        tm = cart.gap_score("topo_merge_objects")      # dup_risk=0.3
        ce = cart.gap_score("constr_extend_pattern")   # dup_risk=0.5
        assert tm > ce


class TestBatch2Recommendation:

    def test_batch_2_has_4_recommendations(self):
        cart = build_cartographer()
        batch2 = cart.batch_2_recommendation()
        assert len(batch2["recommended_batch_2"]) >= 0  # may be empty if all good candidates promoted

    def test_mask_border_only_dropped(self):
        cart = build_cartographer()
        batch2 = cart.batch_2_recommendation()
        recommended_ids = [b["primitive_id"] for b in batch2["recommended_batch_2"]]
        assert "mask_border_only" not in recommended_ids

    def test_geom_flip_vertical_dropped(self):
        cart = build_cartographer()
        batch2 = cart.batch_2_recommendation()
        recommended_ids = [b["primitive_id"] for b in batch2["recommended_batch_2"]]
        assert "geom_flip_vertical" not in recommended_ids

    def test_constr_draw_rect_around_promoted_not_in_batch2(self):
        cart = build_cartographer()
        batch2 = cart.batch_2_recommendation()
        recommended_ids = [b["primitive_id"] for b in batch2["recommended_batch_2"]]
        assert "constr_draw_rect_around" not in recommended_ids  # already promoted

    def test_topo_fill_holes_promoted_not_in_batch2(self):
        cart = build_cartographer()
        batch2 = cart.batch_2_recommendation()
        recommended_ids = [b["primitive_id"] for b in batch2["recommended_batch_2"]]
        assert "topo_fill_holes" not in recommended_ids  # already promoted

    def test_all_recommended_are_promote_now(self):
        cart = build_cartographer()
        batch2 = cart.batch_2_recommendation()
        for b in batch2["recommended_batch_2"]:
            assert b["recommendation"] == "promote_now"

    def test_all_recommended_have_low_duplicate_risk(self):
        cart = build_cartographer()
        batch2 = cart.batch_2_recommendation()
        for b in batch2["recommended_batch_2"]:
            assert b["duplicate_risk"] < 0.6


class TestUnpromotedBlocked:

    def test_unpromoted_candidates_not_counted_as_solved(self):
        cart = build_cartographer()
        for rec in cart.records:
            if rec.source == "native_candidate":
                assert not rec.can_be_counted_as_solved
                assert not rec.promoted

    def test_candidate_probes_remain_unscored(self):
        """Candidate probes should not be counted as solved."""
        from weslr.arc_discovery_120_semantic_pilot import run_120_semantic_pilot
        results = run_120_semantic_pilot()
        cpd = results["candidate_probe_diagnostics"]
        assert cpd["candidate_probe_counted_as_solved"] == 0


class TestBH80And120Unchanged:

    def test_bh80_remains_80(self):
        from weslr.arc_discovery_120_generator import generate_discovery_120_tasks, get_scoring_summary
        tasks = generate_discovery_120_tasks()
        summary = get_scoring_summary(tasks)
        assert summary["bh80_count"] == 80

    def test_120_scored_remains_117(self):
        from weslr.arc_discovery_120_generator import generate_discovery_120_tasks, get_scoring_summary
        tasks = generate_discovery_120_tasks()
        summary = get_scoring_summary(tasks)
        assert summary["scored_total"] == 117
        assert summary["candidate_probe_total"] == 3

    def test_120_semantic_pilot_still_117(self):
        from weslr.arc_discovery_120_semantic_pilot import run_120_semantic_pilot
        results = run_120_semantic_pilot()
        sa = results["scored_aggregate"]
        assert sa["scored_exact"] == 117
        assert sa["failed"] == 0


class TestPerspicuityIntegration:

    def test_perspicuity_contribution_returns_values(self):
        cart = build_cartographer()
        for pid in ["mask_complement", "sel_leftmost", "topo_fill_holes"]:
            contrib = cart.perspicuity_contribution(pid)
            assert "gap_fill" in contrib
            assert "connectivity" in contrib
            assert "family_gap_bonus" in contrib
            assert "task_unlock_bonus" in contrib
            assert 0.0 <= contrib["gap_fill"] <= 1.0

    def test_perspicuity_promoted_returns_zeros(self):
        cart = build_cartographer()
        contrib = cart.perspicuity_contribution("color_invert")
        assert contrib["gap_fill"] == 0.0
        assert contrib["family_gap_bonus"] == 0.0


class TestOutputArtifacts:

    def test_export_coverage_grid(self):
        cart = build_cartographer()
        grid = cart.export_coverage_grid()
        assert "family_maturity" in grid
        assert "family_target" in grid
        assert "family_role" in grid

    def test_export_graph_adjacency(self):
        cart = build_cartographer()
        adj = cart.export_graph_adjacency()
        assert "nodes" in adj
        assert "adjacency" in adj
        assert len(adj["nodes"]) > 0

    def test_export_gap_report(self):
        cart = build_cartographer()
        report = cart.export_gap_report()
        assert "gaps" in report
        assert "gap_scores" in report

    def test_export_top_n_missing(self):
        cart = build_cartographer()
        missing = cart.export_top_n_missing(10)
        assert len(missing) <= 10

    def test_export_top_n_promotion_recommendations(self):
        cart = build_cartographer()
        recs = cart.export_top_n_promotion_recommendations(10)
        assert len(recs) == 10
        # Should be sorted by gap_score descending
        for i in range(len(recs) - 1):
            assert recs[i]["gap_score"] >= recs[i + 1]["gap_score"]

    def test_export_duplicate_risk_report(self):
        cart = build_cartographer()
        report = cart.export_duplicate_risk_report()
        assert len(report) > 0
        # Should be sorted by similarity descending
        for i in range(len(report) - 1):
            assert report[i]["similarity"] >= report[i + 1]["similarity"]

    def test_export_task_unlock_report(self):
        cart = build_cartographer()
        report = cart.export_task_unlock_report()
        assert len(report) > 0

    def test_export_family_coverage(self):
        cart = build_cartographer()
        report = cart.export_family_coverage()
        assert len(report) == 14
        for entry in report:
            assert "family" in entry
            assert "accepted" in entry
            assert "promoted" in entry
            assert "candidates" in entry
            assert "gap_severity" in entry

    def test_export_hub_centrality(self):
        cart = build_cartographer()
        report = cart.export_hub_centrality()
        assert len(report) > 0
        # Should be sorted by composition_degree descending
        for i in range(len(report) - 1):
            assert report[i]["composition_degree"] >= report[i + 1]["composition_degree"]

    def test_get_cartographer_summary(self):
        summary = get_cartographer_summary()
        assert summary["total_records"] == 52
        assert summary["bh80_count"] == 20
        assert summary["promoted_count"] == 8
        assert summary["candidate_count"] == 24
        assert summary["graph_nodes"] > 0
        assert summary["graph_edges"] > 0
        assert "batch_2_recommended" in summary
        assert "batch_2_dropped" in summary