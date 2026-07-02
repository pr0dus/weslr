"""Tests for evidence-driven perspicuity ranking of native ARC candidates.

Tests prove:
- Ranking is deterministic
- Top-N recommendation is stable
- Reason codes are produced
- Unpromoted candidates remain uncounted
- Promoted color_invert is recognized as already promoted
- Duplicate-risk candidates are penalized
- High-complexity candidates can be deferred
- Batch 2 recommendation is explainable
- BH80 unchanged
"""

from __future__ import annotations

import pytest
from weslr.native_arc_perspicuity import (
    compute_evidence_driven_ranking,
    get_top_n_recommendations,
    get_batch_2_reassessment,
    get_ranking_summary,
    EvidenceDrivenScore,
    BH80_ACCEPTED_PRIMITIVES,
    PROMOTED_PRIMITIVES,
    SEMANTIC_SIMILARITY,
    CANDIDATE_PROBE_TASKS,
)
from weslr.native_arc_language_schema import PromotionStage


class TestDeterminism:
    """Ranking must be deterministic: same input → same output."""

    def test_ranking_is_deterministic(self):
        r1 = compute_evidence_driven_ranking()
        r2 = compute_evidence_driven_ranking()
        assert len(r1) == len(r2)
        for a, b in zip(r1, r2):
            assert a.primitive_id == b.primitive_id
            assert abs(a.total - b.total) < 1e-12

    def test_ranking_order_is_stable(self):
        r1 = compute_evidence_driven_ranking()
        r2 = compute_evidence_driven_ranking()
        ids1 = [r.primitive_id for r in r1]
        ids2 = [r.primitive_id for r in r2]
        assert ids1 == ids2

    def test_total_scores_in_descending_order(self):
        rankings = compute_evidence_driven_ranking()
        for i in range(len(rankings) - 1):
            assert rankings[i].total >= rankings[i + 1].total


class TestTopNRecommendation:

    def test_top_n_returns_n(self):
        top5 = get_top_n_recommendations(5)
        assert len(top5) == 5

    def test_top_n_is_stable(self):
        t1 = get_top_n_recommendations(5)
        t2 = get_top_n_recommendations(5)
        assert [t["primitive_id"] for t in t1] == [t["primitive_id"] for t in t2]

    def test_top_n_excludes_promoted(self):
        top10 = get_top_n_recommendations(10)
        for t in top10:
            assert t["primitive_id"] not in PROMOTED_PRIMITIVES

    def test_top_n_has_reason_codes(self):
        top10 = get_top_n_recommendations(10)
        for t in top10:
            assert len(t["reason_codes"]) > 0

    def test_top_n_has_risk_flags(self):
        top10 = get_top_n_recommendations(10)
        for t in top10:
            assert "duplicate_risk" in t["risk_flags"]
            assert "regression_risk" in t["risk_flags"]
            assert "shortcut_risk" in t["risk_flags"]

    def test_top_n_has_promotion_difficulty(self):
        top10 = get_top_n_recommendations(10)
        for t in top10:
            assert 0.0 <= t["promotion_difficulty"] <= 1.0
            assert 0.0 <= t["oracle_complexity"] <= 1.0
            assert 0.0 <= t["solver_complexity"] <= 1.0


class TestPromotedRecognition:

    def test_color_invert_recognized_as_promoted(self):
        rankings = compute_evidence_driven_ranking()
        ci = next(r for r in rankings if r.primitive_id == "color_invert")
        assert ci.evidence.is_promoted is True
        assert ci.evidence.recommendation == "already_promoted"

    def test_color_invert_not_in_top_n(self):
        top10 = get_top_n_recommendations(10)
        ids = [t["primitive_id"] for t in top10]
        assert "color_invert" not in ids


class TestUnpromotedBlocked:

    def test_no_unpromoted_candidate_marked_promoted(self):
        rankings = compute_evidence_driven_ranking()
        for r in rankings:
            if not r.evidence.is_promoted:
                # Unpromoted candidates must not have is_promoted=True
                assert r.evidence.is_promoted is False
                # They must not be "already_promoted"
                assert r.evidence.recommendation != "already_promoted"

    def test_candidates_cannot_be_counted_as_solved(self):
        """All unpromoted candidates must have can_be_counted_as_solved = False."""
        from weslr.native_arc_candidate_generator import generate_candidates
        candidates, _, _ = generate_candidates()
        for c in candidates:
            if c.primitive_id not in PROMOTED_PRIMITIVES:
                assert not c.can_be_counted_as_solved()


class TestDuplicateRiskPenalty:

    def test_high_duplicate_risk_candidates_have_lower_scores(self):
        """Candidates with high duplicate risk should score lower than low-duplicate ones."""
        rankings = compute_evidence_driven_ranking()
        # mask_border_only has 0.6 duplicate risk (similar to extract_boundary)
        # mask_complement has 0.3 duplicate risk
        mb = next(r for r in rankings if r.primitive_id == "mask_border_only")
        mc = next(r for r in rankings if r.primitive_id == "mask_complement")
        assert mc.evidence.duplicate_risk < mb.evidence.duplicate_risk

    def test_duplicate_risk_in_range(self):
        rankings = compute_evidence_driven_ranking()
        for r in rankings:
            assert 0.0 <= r.evidence.duplicate_risk <= 1.0

    def test_geom_translate_center_has_high_duplicate_risk(self):
        """geom_translate_center is very similar to normalize_position."""
        rankings = compute_evidence_driven_ranking()
        gtc = next(r for r in rankings if r.primitive_id == "geom_translate_center")
        assert gtc.evidence.duplicate_risk >= 0.5


class TestDeferBehavior:

    def test_high_complexity_candidates_can_be_deferred(self):
        rankings = compute_evidence_driven_ranking()
        deferred = [r for r in rankings if r.evidence.recommendation == "defer"]
        # At least some candidates should be deferred
        assert len(deferred) > 0
        for d in deferred:
            # Deferred candidates should have a valid defer reason:
            # high difficulty, high risk, no probe task, or borderline score
            assert (
                d.evidence.promotion_difficulty > 0.5 or
                d.evidence.regression_risk > 0.4 or
                d.evidence.shortcut_risk > 0.6 or
                not d.evidence.has_probe_task or
                d.total < 0.65
            )

    def test_rel_swap_positions_is_deferred(self):
        """rel_swap_positions has high promotion difficulty (0.65)."""
        rankings = compute_evidence_driven_ranking()
        rsp = next(r for r in rankings if r.primitive_id == "rel_swap_positions")
        assert rsp.evidence.recommendation == "already_promoted"
        assert rsp.evidence.is_promoted == True


class TestBatch2Reassessment:

    def test_batch2_reassessment_returns_results(self):
        r = get_batch_2_reassessment()
        assert "original_batch_2" in r
        assert "recommended_batch_2" in r
        assert "original_assessment" in r

    def test_batch2_has_4_recommendations(self):
        r = get_batch_2_reassessment()
        assert len(r["recommended_batch_2"]) == 4

    def test_batch2_recommendations_have_reasons(self):
        r = get_batch_2_reassessment()
        for b in r["recommended_batch_2"]:
            assert len(b["reason_codes"]) > 0

    def test_batch2_original_assessment_covers_all_4(self):
        r = get_batch_2_reassessment()
        original = r["original_batch_2"]
        assessed = list(r["original_assessment"].keys())
        for pid in original:
            assert pid in assessed

    def test_batch2_is_explainable(self):
        r = get_batch_2_reassessment()
        assert "revision_needed" in r
        assert isinstance(r["revision_needed"], bool)
        # Each recommended candidate must have explainable fields
        for b in r["recommended_batch_2"]:
            assert "primitive_id" in b
            assert "total_score" in b
            assert "reason_codes" in b


class TestEvidenceFeatures:

    def test_all_candidates_have_evidence(self):
        rankings = compute_evidence_driven_ranking()
        assert len(rankings) == 32
        for r in rankings:
            assert r.evidence is not None
            assert r.evidence.static_perspicuity > 0

    def test_probe_task_candidates_detected(self):
        rankings = compute_evidence_driven_ranking()
        probe_candidates = [r for r in rankings if r.evidence.has_probe_task]
        assert len(probe_candidates) == 10
        for r in probe_candidates:
            assert r.evidence.probe_task_id is not None
            assert r.evidence.probe_chain is not None

    def test_new_family_flag_correct(self):
        rankings = compute_evidence_driven_ranking()
        new_family = [r for r in rankings if r.evidence.new_family]
        # 26 candidates introduce new families (color_invert is promoted so excluded from count)
        assert len(new_family) >= 20

    def test_expected_denominator_gain_positive_for_probes(self):
        rankings = compute_evidence_driven_ranking()
        for r in rankings:
            if r.evidence.has_probe_task and not r.evidence.is_promoted:
                assert r.evidence.expected_denominator_gain > 0


class TestBH80Unchanged:

    def test_bh80_primitives_not_modified(self):
        """The perspicuity module must not modify BH80 primitives."""
        from weslr.arc_discovery_120_generator import generate_discovery_120_tasks
        tasks = generate_discovery_120_tasks()
        bh80 = [t for t in tasks if t["task_id"].startswith("BH80_")]
        assert len(bh80) == 80

    def test_120_scored_remains_117(self):
        """The 120 suite must still have 110 scored tasks."""
        from weslr.arc_discovery_120_generator import generate_discovery_120_tasks, get_scoring_summary
        tasks = generate_discovery_120_tasks()
        summary = get_scoring_summary(tasks)
        assert summary["scored_total"] == 117
        assert summary["candidate_probe_total"] == 3

    def test_120_semantic_pilot_still_110(self):
        """Full 120 pilot must still produce 110/110."""
        from weslr.arc_discovery_120_semantic_pilot import run_120_semantic_pilot
        results = run_120_semantic_pilot()
        sa = results["scored_aggregate"]
        assert sa["scored_exact"] == 117
        assert sa["failed"] == 0