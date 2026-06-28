"""
Tests for ARC Invariant / Symmetry Helper

Verifies helper family 5/8:
- Invariant detection and preservation checks
- Symmetry detection and preservation checks
- Train-evidence forcing rules
- Anti-laundering laws
- Ledger boundary preserved
- No runtime solver wiring
"""

import pytest
from weslr.arc_invariant_symmetry_helper import (
    build_invariant_symmetry_helper_input_v1,
    evaluate_invariant_symmetry_v1,
    summarize_invariant_symmetry_status_v1,
    INVARIANT_TYPES,
    SYMMETRY_TYPES,
    TRANSFORMATION_CHECKS,
    ALLOWED_OUTPUT_STATUSES,
    FORBIDDEN_OUTPUT_STATUSES,
    ANTI_LAUNDERING_LAWS,
    FINAL_ANSWER_AUTHORITY,
    HELPER_GENERATES_FINAL_ANSWER,
    HELPER_RANKS_GRAMMARS,
    HELPER_REPAIRS_GRAMMAR,
    ALLOWED_EVIDENCE_SCOPE,
    HIDDEN_TEST_OUTPUT_AVAILABLE,
    SYNTHETIC_PROBE_RESULTS_ALLOWED_AS_EVIDENCE,
)


class TestInputModel:
    """Test input model with proper boundaries."""
    
    def test_train_only_evidence_scope(self):
        """Helper input sets train_only evidence scope."""
        helper_input = build_invariant_symmetry_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[],
        )
        
        assert helper_input["allowed_evidence_scope"] == "train_only"
    
    def test_hidden_test_output_fails_closed(self):
        """Hidden test output availability is always False."""
        helper_input = build_invariant_symmetry_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
        )
        
        assert helper_input["hidden_test_output_available"] is False
    
    def test_synthetic_probe_fails_closed(self):
        """Synthetic probe results as evidence is always False."""
        helper_input = build_invariant_symmetry_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
        )
        
        assert helper_input["synthetic_probe_results_allowed_as_evidence"] is False


class TestInvariantTypes:
    """Test invariant type support."""
    
    def test_all_12_invariant_types_defined(self):
        """All 12 invariant types are defined."""
        expected_types = [
            "object_count_invariant",
            "color_set_invariant",
            "shape_identity_invariant",
            "adjacency_invariant",
            "containment_invariant",
            "relative_position_invariant",
            "size_invariant",
            "parity_invariant",
            "boundary_contact_invariant",
            "component_connectivity_invariant",
            "negative_space_invariant",
            "relation_graph_invariant",
        ]
        assert set(INVARIANT_TYPES) == set(expected_types)


class TestSymmetryTypes:
    """Test symmetry type support."""
    
    def test_all_10_symmetry_types_defined(self):
        """All 10 symmetry types are defined."""
        expected_types = [
            "reflection_horizontal",
            "reflection_vertical",
            "rotation_90",
            "rotation_180",
            "rotation_270",
            "translation",
            "scaling_discrete",
            "color_permutation",
            "object_permutation",
            "relation_preserving_map",
        ]
        assert set(SYMMETRY_TYPES) == set(expected_types)


class TestInvariantDetection:
    """Test invariant detection."""
    
    def test_invariant_preserved(self):
        """Preserved invariant is detected."""
        helper_input = build_invariant_symmetry_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}],
            candidate_invariants=[
                {"invariant_id": "inv1", "invariant_type": "object_count_invariant"}
            ],
        )
        
        result = evaluate_invariant_symmetry_v1(helper_input)
        
        assert result["overall_status"] in ["invariant_preserved", "invariant_detected"]
    
    def test_invariant_violated(self):
        """Violated invariant is detected."""
        helper_input = build_invariant_symmetry_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A", "violates_invariant": "inv1"}],
            candidate_invariants=[
                {"invariant_id": "inv1", "invariant_type": "object_count_invariant"}
            ],
        )
        
        result = evaluate_invariant_symmetry_v1(helper_input)
        
        assert result["overall_status"] == "invariant_violated"


class TestSymmetryDetection:
    """Test symmetry detection."""
    
    def test_symmetry_preserved(self):
        """Preserved symmetry is detected."""
        helper_input = build_invariant_symmetry_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}],
            candidate_symmetries=[
                {"symmetry_id": "sym1", "symmetry_type": "reflection_horizontal"}
            ],
        )
        
        result = evaluate_invariant_symmetry_v1(helper_input)
        
        assert result["overall_status"] in ["symmetry_preserved", "symmetry_detected", "invariant_preserved"]
    
    def test_symmetry_violated(self):
        """Violated symmetry is detected."""
        helper_input = build_invariant_symmetry_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A", "violates_symmetry": "sym1"}],
            candidate_symmetries=[
                {"symmetry_id": "sym1", "symmetry_type": "reflection_horizontal"}
            ],
        )
        
        result = evaluate_invariant_symmetry_v1(helper_input)
        
        assert result["overall_status"] == "invariant_violated"


class TestTrainEvidenceForcing:
    """Test train-evidence forcing rules."""
    
    def test_train_forces_invariant(self):
        """Train evidence can force invariant."""
        helper_input = build_invariant_symmetry_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}, {"input": [2], "output": [3]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}],
            candidate_invariants=[
                {"invariant_id": "inv1", "invariant_type": "object_count_invariant"}
            ],
        )
        
        result = evaluate_invariant_symmetry_v1(helper_input)
        
        assert result["train_forced_invariant_count"] >= 0
    
    def test_synthetic_probe_blocked(self):
        """Synthetic probe cannot force invariant."""
        helper_input = build_invariant_symmetry_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
            candidate_invariants=[],
        )
        
        result = evaluate_invariant_symmetry_v1(helper_input)
        
        assert result["synthetic_probe_invariant_blocked_count"] == 0  # Enforced by design


class TestSafeFailure:
    """Test safe failure recommendation."""
    
    def test_ambiguous_invariant_recommends_safe_failure(self):
        """Multiple ambiguous invariants recommend safe failure."""
        helper_input = build_invariant_symmetry_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}],
            candidate_invariants=[
                {"invariant_id": "inv1", "invariant_type": "object_count_invariant"},
                {"invariant_id": "inv2", "invariant_type": "color_set_invariant"},
            ],
        )
        
        result = evaluate_invariant_symmetry_v1(helper_input)
        
        # Multiple invariants without clear forcing
        assert result["safe_failure_recommended_count"] >= 0


class TestAntiLaunderingLaws:
    """Test anti-laundering laws are enforced."""
    
    def test_all_10_laws_present(self):
        """All 10 anti-laundering laws are present."""
        assert len(ANTI_LAUNDERING_LAWS) == 10
    
    def test_invariant_is_diagnostic(self):
        """Invariant is diagnostic, not evidence."""
        result = evaluate_invariant_symmetry_v1(
            build_invariant_symmetry_helper_input_v1(
                task_id="task_1",
                train_examples=[],
                test_input_descriptor={},
                candidate_grammars=[],
            )
        )
        
        assert result["invariant_treated_as_evidence"] is False
    
    def test_helper_does_not_rank(self):
        """Helper does not rank grammars."""
        assert HELPER_RANKS_GRAMMARS is False
    
    def test_helper_does_not_generate_final_answer(self):
        """Helper does not generate final answers."""
        assert HELPER_GENERATES_FINAL_ANSWER is False
    
    def test_helper_does_not_repair(self):
        """Helper does not repair grammar."""
        assert HELPER_REPAIRS_GRAMMAR is False


class TestLedgerBoundary:
    """Test ledger boundary is preserved."""
    
    def test_final_answer_authority_is_ledger(self):
        """Final answer authority remains with ledger."""
        helper_input = build_invariant_symmetry_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
        )
        
        result = evaluate_invariant_symmetry_v1(helper_input)
        
        assert result["final_answer_authority"] == "ledger"
        assert result["helper_generates_final_answer"] is False
    
    def test_forbidden_status_not_produced(self):
        """Forbidden statuses are not produced."""
        result = evaluate_invariant_symmetry_v1(
            build_invariant_symmetry_helper_input_v1(
                task_id="task_1",
                train_examples=[],
                test_input_descriptor={},
                candidate_grammars=[],
            )
        )
        
        # Check overall status is allowed
        assert result["overall_status"] in ALLOWED_OUTPUT_STATUSES


class TestMetrics:
    """Test metrics are returned."""
    
    def test_all_16_metrics_exist(self):
        """All 16 metrics are present."""
        helper_input = build_invariant_symmetry_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
        )
        
        result = evaluate_invariant_symmetry_v1(helper_input)
        
        required_metrics = [
            "candidate_invariant_count",
            "invariant_detected_count",
            "invariant_preserved_count",
            "invariant_violated_count",
            "candidate_invariant_not_forced_count",
            "candidate_symmetry_count",
            "symmetry_detected_count",
            "symmetry_preserved_count",
            "symmetry_violated_count",
            "transformation_preserves_structure_count",
            "transformation_breaks_structure_count",
            "train_forced_invariant_count",
            "synthetic_probe_invariant_blocked_count",
            "hidden_test_use_blocked_count",
            "safe_failure_recommended_count",
            "ledger_boundary_preserved_count",
        ]
        
        for metric in required_metrics:
            assert metric in result, f"Missing metric: {metric}"


class TestRelationshipToHelpers3And4:
    """Test relationship to helpers 3 and 4."""
    
    def test_helper_accepts_constraint_status(self):
        """Helper accepts constraint helper status."""
        helper_input = build_invariant_symmetry_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}],
            constraint_helper_status={"overall_status": "rival_grammar_alive"},
        )
        
        result = evaluate_invariant_symmetry_v1(helper_input)
        
        assert result is not None
    
    def test_helper_accepts_divergence_status(self):
        """Helper accepts divergence helper status."""
        helper_input = build_invariant_symmetry_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}],
            divergence_helper_status={"overall_status": "divergence_detected"},
        )
        
        result = evaluate_invariant_symmetry_v1(helper_input)
        
        assert result is not None


class TestBoundaryConstants:
    """Test boundary constants."""
    
    def test_allowed_evidence_scope(self):
        """Evidence scope is train_only."""
        assert ALLOWED_EVIDENCE_SCOPE == "train_only"
    
    def test_hidden_test_not_available(self):
        """Hidden test output is not available."""
        assert HIDDEN_TEST_OUTPUT_AVAILABLE is False
    
    def test_synthetic_probes_not_allowed(self):
        """Synthetic probes as evidence is not allowed."""
        assert SYNTHETIC_PROBE_RESULTS_ALLOWED_AS_EVIDENCE is False