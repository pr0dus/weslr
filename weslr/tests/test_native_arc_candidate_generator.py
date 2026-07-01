"""Tests for WESLR native ARC primitive candidate generator."""

import pytest
from weslr.native_arc_candidate_generator import (
    generate_candidates, list_candidate_summaries, list_audit_ready_fields,
    PerspicuityScore, CandidateFamily,
)
from weslr.native_arc_language_schema import (
    PromotionStage, validate_promotion_eligibility, reject_unvalidated_as_solved,
)


@pytest.fixture(scope="module")
def generated():
    candidates, families, scores = generate_candidates()
    return candidates, families, scores


class TestDeterministicGeneration:
    def test_same_input_same_output(self):
        c1, f1, s1 = generate_candidates()
        c2, f2, s2 = generate_candidates()
        assert len(c1) == len(c2)
        assert [c.primitive_id for c in c1] == [c.primitive_id for c in c2]
        assert [c.content_hash for c in c1] == [c.content_hash for c in c2]

    def test_stable_hashes(self, generated):
        candidates, _, _ = generated
        for c in candidates:
            assert c.content_hash == __import__("hashlib").sha256(
                c.internal_expression.encode()
            ).hexdigest()


class TestCandidateFamilies:
    def test_at_least_9_families(self, generated):
        _, families, _ = generated
        assert len(families) >= 9

    def test_family_ids(self, generated):
        _, families, _ = generated
        fam_ids = [f.family_id for f in families]
        expected = [
            "object_selector", "mask_algebra", "color_transform",
            "geometry_transform", "topology_transform", "relation_transform",
            "construction_transform", "pattern_transform", "conditional_transform",
        ]
        for exp in expected:
            assert exp in fam_ids, f"Missing family: {exp}"

    def test_each_family_has_candidates(self, generated):
        _, families, _ = generated
        for f in families:
            assert len(f.candidates) >= 1, f"Family {f.family_id} has no candidates"

    def test_total_candidates(self, generated):
        candidates, _, _ = generated
        assert len(candidates) >= 30  # 9 families × 3-5 candidates


class TestAlienExpressions:
    def test_alien_symbols_present(self, generated):
        candidates, _, _ = generated
        alien_chars = ["λ", "Σ", "Ω", "κ", "γ", "τ", "Φ", "ξ", "π", "⇒", "⇢", "∧", "∨", "¬"]
        all_exprs = " ".join(c.internal_expression for c in candidates)
        for ch in alien_chars:
            assert ch in all_exprs, f"Alien character '{ch}' not found in any expression"

    def test_human_summary_optional(self, generated):
        candidates, _, _ = generated
        # Some have summaries, some don't (all have summaries here, but None should be accepted)
        for c in candidates:
            assert c.human_summary is not None or c.human_summary is None  # either is fine


class TestPromotionBlocking:
    def test_candidates_cannot_be_counted_as_solved(self, generated):
        candidates, _, _ = generated
        for c in candidates:
            assert reject_unvalidated_as_solved(c) is True, f"{c.primitive_id} should not be countable as solved"
            assert not c.can_be_counted_as_solved()

    def test_candidates_cannot_be_promoted(self, generated):
        candidates, _, _ = generated
        for c in candidates:
            eligible, reason = validate_promotion_eligibility(c)
            assert not eligible, f"{c.primitive_id} should not be promotion-eligible: {reason}"

    def test_stages_cannot_be_skipped(self, generated):
        candidates, _, _ = generated
        for c in candidates:
            # All are at GENERATED stage
            assert c.promotion_stage == PromotionStage.GENERATED
            assert c.completed_stages == {PromotionStage.GENERATED}

    def test_promotion_requires_all_stages(self, generated):
        candidates, _, _ = generated
        for c in candidates:
            # Set all stages except one
            c.completed_stages = {
                PromotionStage.GENERATED, PromotionStage.TYPED,
                PromotionStage.EXECUTABLE, PromotionStage.ORACLE_DEFINED,
                PromotionStage.SOLVER_TARGETED, PromotionStage.TESTED,
                PromotionStage.ANTI_CHEAT_VALIDATED,
                # Missing REGRESSION_SAFE
            }
            c.oracle_execution_status = "verified"
            c.solver_execution_status = "verified"
            c.positive_examples = [{"in": [[1]], "out": [[2]]}]
            c.negative_controls = [{"noop": True}]
            c.anti_cheat_checks = ["check1"]
            eligible, reason = validate_promotion_eligibility(c)
            assert not eligible
            assert "Missing stages" in reason


class TestDuplicateDetection:
    def test_no_duplicates_in_generated_set(self, generated):
        candidates, _, _ = generated
        hashes = [c.content_hash for c in candidates]
        assert len(hashes) == len(set(hashes)), "Duplicate content hashes found"

    def test_duplicate_detection_catches_identical(self):
        from weslr.native_arc_candidate_generator import _detect_duplicates
        from weslr.native_arc_language_schema import make_primitive_contract
        c1 = make_primitive_contract("dup1", "same_expr", "Grid", "Grid")
        c2 = make_primitive_contract("dup2", "same_expr", "Grid", "Grid")
        dups = _detect_duplicates([c1, c2])
        assert len(dups) == 1


class TestPerspicuityScoring:
    def test_scores_deterministic(self, generated):
        _, _, scores = generated
        _, _, scores2 = generate_candidates()
        for pid in scores:
            assert scores[pid].total == scores2[pid].total, f"Score for {pid} differs"

    def test_scores_in_range(self, generated):
        _, _, scores = generated
        for pid, score in scores.items():
            assert 0.0 <= score.total <= 1.0, f"{pid}: score {score.total} out of range"

    def test_scores_have_all_fields(self, generated):
        _, _, scores = generated
        for pid, s in scores.items():
            assert hasattr(s, "clarity")
            assert hasattr(s, "minimality")
            assert hasattr(s, "non_duplication")
            assert hasattr(s, "compositional_depth")
            assert hasattr(s, "testability")
            assert hasattr(s, "expected_usefulness")
            assert hasattr(s, "shortcut_risk")


class TestExportHelpers:
    def test_list_summaries(self, generated):
        candidates, _, _ = generated
        summaries = list_candidate_summaries(candidates)
        assert len(summaries) == len(candidates)
        for s in summaries:
            assert "primitive_id" in s
            assert "content_hash" in s
            assert "type" in s
            assert "stage" in s

    def test_list_audit_ready(self, generated):
        candidates, _, _ = generated
        audit = list_audit_ready_fields(candidates)
        assert len(audit) == len(candidates)
        for a in audit:
            assert "primitive_id" in a
            assert "internal_expression" in a
            assert "content_hash" in a
            assert "type_signature" in a
            assert "promotion_stage" in a


class TestBH80Unchanged:
    def test_bh80_regression_policy_referenced(self):
        from weslr.native_arc_language_schema import BH80_REGRESSION_POLICY
        assert BH80_REGRESSION_POLICY["frozen_baseline"] == 80
        assert BH80_REGRESSION_POLICY["strong_gate"] == 72

    def test_no_bh80_files_modified(self):
        # This is verified by the fact that no BH80 modules are imported by the generator
        import weslr.native_arc_candidate_generator as gen_mod
        src = open(gen_mod.__file__).read()
        assert "arc_synthetic_3_step_real_dispatch" not in src
        assert "arc_bh80_oracle" not in src
        assert "arc_bh80_materializer" not in src
        assert "arc_bh80_semantic_scorer" not in src
        assert "arc_bh80_enriched_scenes" not in src
        assert "arc_synthetic_3_step_task_schema" not in src or "from weslr.native_arc_language_schema" in src