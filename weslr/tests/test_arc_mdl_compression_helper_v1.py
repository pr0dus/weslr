"""
Tests for ARC Minimum Description Length / Compression Helper

Verifies helper family 6/8:
- Description length estimation
- Exception/assumption penalties
- Overfit/underfit detection
- Compression comparison rules
- Anti-laundering laws
- Ledger boundary preserved
- No runtime solver wiring
"""

import pytest
from weslr.arc_mdl_compression_helper import (
    build_mdl_compression_helper_input_v1,
    evaluate_mdl_compression_v1,
    summarize_mdl_compression_status_v1,
    ALLOWED_OUTPUT_STATUSES,
    FORBIDDEN_OUTPUT_STATUSES,
    ANTI_LAUNDERING_LAWS,
    FINAL_ANSWER_AUTHORITY,
    HELPER_GENERATES_FINAL_ANSWER,
    HELPER_RANKS_FOR_FINAL_ANSWER,
    ALLOWED_EVIDENCE_SCOPE,
    HIDDEN_TEST_OUTPUT_AVAILABLE,
    SYNTHETIC_PROBE_RESULTS_ALLOWED_AS_EVIDENCE,
)


class TestInputModel:
    """Test input model with proper boundaries."""
    
    def test_train_only_evidence_scope(self):
        """Helper input sets train_only evidence scope."""
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[],
        )
        
        assert helper_input["allowed_evidence_scope"] == "train_only"
    
    def test_hidden_test_output_fails_closed(self):
        """Hidden test output availability is always False."""
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
        )
        
        assert helper_input["hidden_test_output_available"] is False
    
    def test_synthetic_probe_fails_closed(self):
        """Synthetic probe results as evidence is always False."""
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
        )
        
        assert helper_input["synthetic_probe_results_allowed_as_evidence"] is False


class TestDescriptionLengthEstimation:
    """Test description length estimation."""
    
    def test_grammar_with_few_rules(self):
        """Grammar with fewer rules has shorter description."""
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[
                {"grammar_id": "A", "rule_count": 1, "primitive_count": 1},
                {"grammar_id": "B", "rule_count": 5, "primitive_count": 5},
            ],
        )
        
        result = evaluate_mdl_compression_v1(helper_input)
        
        results = result["compression_results"]
        a_length = next(r for r in results if r["grammar_id"] == "A")["description_length_estimate"]
        b_length = next(r for r in results if r["grammar_id"] == "B")["description_length_estimate"]
        
        assert a_length < b_length
    
    def test_exception_penalty_applied(self):
        """Grammar with many exceptions gets penalty."""
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[
                {"grammar_id": "A", "rule_count": 2, "exception_count": 5},
            ],
        )
        
        result = evaluate_mdl_compression_v1(helper_input)
        
        assert result["exception_penalty_count"] == 1
    
    def test_assumption_penalty_applied(self):
        """Grammar with many assumptions gets penalty."""
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[
                {"grammar_id": "A", "rule_count": 2, "assumption_count": 5},
            ],
        )
        
        result = evaluate_mdl_compression_v1(helper_input)
        
        assert result["assumption_penalty_count"] == 1


class TestCompressionComparison:
    """Test compression comparison rules."""
    
    def test_compression_tie(self):
        """Similar description lengths produce tie."""
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[
                {"grammar_id": "A", "rule_count": 2, "primitive_count": 2},
                {"grammar_id": "B", "rule_count": 2, "primitive_count": 2},
            ],
        )
        
        result = evaluate_mdl_compression_v1(helper_input)
        
        assert result["overall_status"] == "compression_tie"
    
    def test_simpler_not_forced(self):
        """Simpler grammar but rivals alive."""
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[
                {"grammar_id": "A", "rule_count": 1},
            ],
            constraint_helper_status={"overall_status": "rival_grammar_alive"},
        )
        
        result = evaluate_mdl_compression_v1(helper_input)
        
        assert result["candidate_simpler_but_not_forced_count"] == 1
    
    def test_overfit_risk(self):
        """Grammar with overfit markers detected."""
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[
                {"grammar_id": "A", "rule_count": 1, "overfit_markers": ["marker1"]},
            ],
        )
        
        result = evaluate_mdl_compression_v1(helper_input)
        
        assert result["overfit_risk_count"] == 1
    
    def test_underfit_risk(self):
        """Grammar with underfit markers detected."""
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[
                {"grammar_id": "A", "rule_count": 1, "underfit_markers": ["marker1"]},
            ],
        )
        
        result = evaluate_mdl_compression_v1(helper_input)
        
        assert result["underfit_risk_count"] == 1


class TestHelperRelationships:
    """Test relationships to other helpers."""
    
    def test_accepts_constraint_status(self):
        """Helper accepts constraint helper status."""
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}],
            constraint_helper_status={"overall_status": "rival_grammar_alive"},
        )
        
        result = evaluate_mdl_compression_v1(helper_input)
        
        assert result is not None
    
    def test_accepts_divergence_status(self):
        """Helper accepts divergence helper status."""
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}],
            divergence_helper_status={"overall_status": "divergence_detected"},
        )
        
        result = evaluate_mdl_compression_v1(helper_input)
        
        assert result is not None
    
    def test_accepts_invariant_symmetry_status(self):
        """Helper accepts invariant/symmetry helper status."""
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}],
            invariant_symmetry_helper_status={"overall_status": "invariant_preserved"},
        )
        
        result = evaluate_mdl_compression_v1(helper_input)
        
        assert result is not None


class TestAntiLaunderingLaws:
    """Test anti-laundering laws are enforced."""
    
    def test_all_10_laws_present(self):
        """All 10 anti-laundering laws are present."""
        assert len(ANTI_LAUNDERING_LAWS) == 10
    
    def test_compression_is_diagnostic(self):
        """Compression is diagnostic, not evidence."""
        result = evaluate_mdl_compression_v1(
            build_mdl_compression_helper_input_v1(
                task_id="task_1",
                train_examples=[],
                test_input_descriptor={},
                candidate_grammars=[],
            )
        )
        
        assert result["compression_treated_as_evidence"] is False
    
    def test_helper_does_not_rank(self):
        """Helper does not rank for final answer."""
        assert HELPER_RANKS_FOR_FINAL_ANSWER is False
    
    def test_helper_does_not_generate_final_answer(self):
        """Helper does not generate final answers."""
        assert HELPER_GENERATES_FINAL_ANSWER is False


class TestLedgerBoundary:
    """Test ledger boundary is preserved."""
    
    def test_final_answer_authority_is_ledger(self):
        """Final answer authority remains with ledger."""
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
        )
        
        result = evaluate_mdl_compression_v1(helper_input)
        
        assert result["final_answer_authority"] == "ledger"
        assert result["helper_generates_final_answer"] is False
    
    def test_forbidden_status_not_produced(self):
        """Forbidden statuses are not produced."""
        result = evaluate_mdl_compression_v1(
            build_mdl_compression_helper_input_v1(
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
        helper_input = build_mdl_compression_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
        )
        
        result = evaluate_mdl_compression_v1(helper_input)
        
        required_metrics = [
            "candidate_grammar_count",
            "description_length_estimated_count",
            "compression_preference_count",
            "compression_tie_count",
            "exception_penalty_count",
            "assumption_penalty_count",
            "special_case_penalty_count",
            "overfit_risk_count",
            "underfit_risk_count",
            "candidate_simpler_but_not_forced_count",
            "train_consistent_rival_preserved_count",
            "compression_confidence_increase_blocked_count",
            "hidden_test_compression_blocked_count",
            "synthetic_probe_compression_blocked_count",
            "safe_failure_recommended_count",
            "ledger_boundary_preserved_count",
        ]
        
        for metric in required_metrics:
            assert metric in result, f"Missing metric: {metric}"


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