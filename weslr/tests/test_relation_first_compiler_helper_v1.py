"""
Tests for Relation-First Compiler Helper V1

Verifies the helper transforms candidate rules correctly without:
- Judging, scoring, vetoing, or generating final answers
- Mutating input
- Generating live timestamps
- Calling external systems
- Changing solver behavior
"""

import pytest
from weslr.relation_first_compiler_helper import (
    rewrite_moved_anchor_candidate_rule_v1,
    REWRITE_FULL,
    REWRITE_PARTIAL,
    REWRITE_IRREDUCIBLE,
    REWRITE_UNSAFE,
    REWRITE_NOT_APPLICABLE,
    SOLVER_BEHAVIOR_CHANGED,
    SOLVER_PRIMITIVES_ADDED,
    BENCHMARK_CLAIM_SAFE,
    SYNTHETIC_ONLY,
    PUBLIC_ARC_USED,
    KAGGLE_USED,
)


def _make_rule(
    rule_id="test_rule_1",
    family_id="anchor_translated_target_preserved",
    anchor_identity="anchor_A",
    distractor_at_old=False,
    ambiguity=False,
    boundary=False,
    anchor_absent=False,
):
    """Helper to create test candidate rules."""
    return {
        "rule_id": rule_id,
        "family_id": family_id,
        "anchor_coordinate": {"x": 2, "y": 2},
        "anchor_identity": anchor_identity,
        "target_offset": {"dx": 1, "dy": 0},
        "distractor_at_old_anchor": distractor_at_old,
        "ambiguity_signal": ambiguity,
        "boundary_signal": boundary,
        "anchor_absent": anchor_absent,
        "context": {"task_id": "test_task", "source": "test"},
    }


class TestFullRewrite:
    """Test cases for full relational rewrite."""
    
    def test_full_rewrite_translated_target(self):
        """Full rewrite for anchor_translated_target_preserved."""
        rule = _make_rule(family_id="anchor_translated_target_preserved")
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        assert result["rewrite_status"] == REWRITE_FULL
        assert result["relational_rule"] is not None
        assert result["helper_changed_candidate_rule"] is True
        assert result["downstream_candidate_rule"]["rule_type"] == "relational"
    
    def test_full_rewrite_offset_constant(self):
        """Full rewrite for anchor_moved_offset_constant."""
        rule = _make_rule(family_id="anchor_moved_offset_constant")
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        assert result["rewrite_status"] == REWRITE_FULL
        assert result["relational_rule"] is not None
    
    def test_full_rewrite_distractor_bait(self):
        """Full rewrite for anchor_moved_distractor_at_old_coord when identity available."""
        # This is the key distractor-bait test: identity available, should full rewrite
        rule = _make_rule(
            family_id="anchor_moved_distractor_at_old_coord",
            anchor_identity="anchor_A",
            distractor_at_old=True,  # Distractor present at old coordinate
        )
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        assert result["rewrite_status"] == REWRITE_FULL
        assert result["relational_rule"] is not None
        assert result["helper_changed_candidate_rule"] is True


class TestPartialRewrite:
    """Test cases for partial rewrite."""
    
    def test_partial_rewrite_multiple_anchors(self):
        """Partial rewrite for multiple_anchors_one_valid."""
        rule = _make_rule(
            family_id="multiple_anchors_one_valid",
            ambiguity=True,
        )
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        assert result["rewrite_status"] == REWRITE_PARTIAL
        assert result["residual_dependency"] == "ambiguity_residual"
        assert result["relational_rule"] is not None


class TestIrreducible:
    """Test cases for irreducible coordinate dependency."""
    
    def test_irreducible_boundary(self):
        """Irreducible for anchor_moved_near_boundary."""
        rule = _make_rule(family_id="anchor_moved_near_boundary", boundary=True)
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        assert result["rewrite_status"] == REWRITE_IRREDUCIBLE
        assert result["relational_rule"] is None
        assert result["fallback_rule"] is not None
    
    def test_irreducible_boundary_signal(self):
        """Irreducible when boundary_signal is true."""
        rule = _make_rule(family_id="anchor_translated_target_preserved", boundary=True)
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        assert result["rewrite_status"] == REWRITE_IRREDUCIBLE


class TestUnsafe:
    """Test cases for unsafe to predict."""
    
    def test_unsafe_absent_ambiguous(self):
        """Unsafe for anchor_absent_ambiguous."""
        rule = _make_rule(family_id="anchor_absent_ambiguous", anchor_absent=True)
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        assert result["rewrite_status"] == REWRITE_UNSAFE
        assert result["relational_rule"] is None
        assert result["downstream_candidate_rule"] is None
    
    def test_unsafe_identity_missing(self):
        """Unsafe when anchor identity is missing for moved-anchor family."""
        rule = _make_rule(family_id="anchor_translated_target_preserved", anchor_identity=None)
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        assert result["rewrite_status"] == REWRITE_UNSAFE


class TestNotApplicable:
    """Test cases for not applicable."""
    
    def test_not_applicable_non_moved_anchor(self):
        """Not applicable for non-moved-anchor family."""
        rule = _make_rule(family_id="some_other_family")
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        assert result["rewrite_status"] == REWRITE_NOT_APPLICABLE
    
    def test_not_applicable_missing_field(self):
        """Not applicable when required field is missing."""
        rule = _make_rule()
        del rule["rule_id"]
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        assert result["rewrite_status"] == REWRITE_NOT_APPLICABLE


class TestMutationAndDeterminism:
    """Test for immutability and determinism."""
    
    def test_no_input_mutation(self):
        """Verify input is not mutated."""
        original = _make_rule()
        original_copy = dict(original)
        
        result = rewrite_moved_anchor_candidate_rule_v1(original)
        
        # Original should be preserved
        assert original == original_copy
        # Result should have original preserved separately
        assert result["original_coordinate_rule"] == original_copy
    
    def test_deterministic_output(self):
        """Verify deterministic output for identical input."""
        rule = _make_rule()
        
        result1 = rewrite_moved_anchor_candidate_rule_v1(rule)
        result2 = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        # Results should be identical (except object identity)
        assert result1["rewrite_status"] == result2["rewrite_status"]
        assert result1["helper_changed_candidate_rule"] == result2["helper_changed_candidate_rule"]
        assert result1["transform_metadata"]["rewrite_timestamp"] is None
        assert result2["transform_metadata"]["rewrite_timestamp"] is None
    
    def test_no_live_timestamp(self):
        """Verify no live timestamp is generated."""
        rule = _make_rule()
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        assert result["transform_metadata"]["rewrite_timestamp"] is None


class TestOutputStructure:
    """Test output structure separation."""
    
    def test_original_preserved(self):
        """Verify original coordinate rule is preserved in output."""
        rule = _make_rule()
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        assert "original_coordinate_rule" in result
        assert result["original_coordinate_rule"] is not None
    
    def test_downstream_separated(self):
        """Verify downstream candidate rule is separate."""
        rule = _make_rule()
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        assert "downstream_candidate_rule" in result
        # For full rewrite, downstream should be relational
        if result["rewrite_status"] == REWRITE_FULL:
            assert result["downstream_candidate_rule"]["rule_type"] == "relational"


class TestSolverFreeze:
    """Test solver-freeze constants."""
    
    def test_solver_behavior_unchanged(self):
        """Verify solver behavior flag is false."""
        assert SOLVER_BEHAVIOR_CHANGED is False
    
    def test_solver_primitives_unchanged(self):
        """Verify solver primitives flag is false."""
        assert SOLVER_PRIMITIVES_ADDED is False
    
    def test_benchmark_claim_safe(self):
        """Verify benchmark claim safe flag is false."""
        assert BENCHMARK_CLAIM_SAFE is False
    
    def test_synthetic_only(self):
        """Verify synthetic-only flag is true."""
        assert SYNTHETIC_ONLY is True
    
    def test_no_public_arc(self):
        """Verify public ARC flag is false."""
        assert PUBLIC_ARC_USED is False
    
    def test_no_kaggle(self):
        """Verify Kaggle flag is false."""
        assert KAGGLE_USED is False


class TestReturnType:
    """Test return type."""
    
    def test_returns_dict(self):
        """Verify function returns a dictionary."""
        rule = _make_rule()
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        assert isinstance(result, dict)
    
    def test_has_required_fields(self):
        """Verify output has all required fields."""
        rule = _make_rule()
        result = rewrite_moved_anchor_candidate_rule_v1(rule)
        
        required = [
            "rewrite_status",
            "original_coordinate_rule",
            "relational_rule",
            "residual_dependency",
            "fallback_rule",
            "downstream_candidate_rule",
            "helper_changed_candidate_rule",
            "safety_reason",
            "transform_metadata",
        ]
        for field in required:
            assert field in result, f"Missing field: {field}"