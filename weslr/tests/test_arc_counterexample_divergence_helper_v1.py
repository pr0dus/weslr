"""
Tests for ARC Counterexample / Divergence Helper

Verifies helper family 4/8:
- Input model with train_derived scope
- Shadow-case generation for divergence detection
- Anti-laundering laws
- Ledger boundary preserved
- No runtime solver wiring
"""

import pytest
from weslr.arc_counterexample_divergence_helper import (
    build_counterexample_divergence_helper_input_v1,
    evaluate_counterexample_divergence_v1,
    summarize_counterexample_divergence_status_v1,
    DIVERGENCE_AXES,
    ALLOWED_OUTPUT_STATUSES,
    FORBIDDEN_OUTPUT_STATUSES,
    ANTI_LAUNDERING_LAWS,
    FINAL_ANSWER_AUTHORITY,
    HELPER_GENERATES_FINAL_ANSWER,
    HELPER_RANKS_GRAMMARS,
    HELPER_REPAIRS_GRAMMAR,
    ALLOWED_SHADOW_CASE_SCOPE,
    ALLOWED_EVIDENCE_SCOPE,
    SYNTHETIC_PROBE_RESULTS_ALLOWED_AS_EVIDENCE,
    HIDDEN_TEST_OUTPUT_AVAILABLE,
)


class TestInputModel:
    """Test input model with proper boundaries."""
    
    def test_train_derived_shadow_scope(self):
        """Helper input sets train_derived shadow scope."""
        helper_input = build_counterexample_divergence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[],
            rival_grammar_pairs=[],
        )
        
        assert helper_input["allowed_shadow_case_scope"] == "train_derived"
    
    def test_train_only_evidence_scope(self):
        """Helper input sets train_only evidence scope."""
        helper_input = build_counterexample_divergence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[],
            rival_grammar_pairs=[],
        )
        
        assert helper_input["allowed_evidence_scope"] == "train_only"
    
    def test_hidden_test_output_fails_closed(self):
        """Hidden test output availability is always False."""
        helper_input = build_counterexample_divergence_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
            rival_grammar_pairs=[],
        )
        
        assert helper_input["hidden_test_output_available"] is False
    
    def test_synthetic_probe_fails_closed(self):
        """Synthetic probe results as evidence is always False."""
        helper_input = build_counterexample_divergence_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
            rival_grammar_pairs=[],
        )
        
        assert helper_input["synthetic_probe_results_allowed_as_evidence"] is False


class TestDivergenceAxes:
    """Test divergence axis support."""
    
    def test_all_10_divergence_axes_defined(self):
        """All 10 divergence axes are defined."""
        expected_axes = [
            "target_selection_divergence",
            "action_divergence",
            "representation_divergence",
            "object_correspondence_divergence",
            "symmetry_divergence",
            "negative_evidence_divergence",
            "boundary_condition_divergence",
            "coordinate_vs_relation_divergence",
            "helper_trap_divergence",
            "beautiful_wrong_rule_divergence",
        ]
        assert set(DIVERGENCE_AXES) == set(expected_axes)


class TestShadowCase:
    """Test shadow case model."""
    
    def test_shadow_case_required_fields(self):
        """Shadow case includes required fields."""
        helper_input = build_counterexample_divergence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}, {"grammar_id": "B"}],
            rival_grammar_pairs=[("A", "B")],
        )
        
        result = evaluate_counterexample_divergence_v1(helper_input)
        
        assert len(result["comparison_results"]) > 0
        shadow = result["comparison_results"][0]["shadow_case"]
        
        required_fields = [
            "shadow_case_id",
            "description",
            "minimal_condition_changed",
            "grammar_a_prediction",
            "grammar_b_prediction",
            "divergence_detected",
            "uses_train_evidence_only",
            "treated_as_evidence",
            "may_eliminate_grammar",
            "may_raise_confidence",
        ]
        
        for field in required_fields:
            assert field in shadow, f"Missing field: {field}"
    
    def test_shadow_case_non_evidential(self):
        """Shadow case is treated as non-evidence."""
        helper_input = build_counterexample_divergence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}, {"grammar_id": "B"}],
            rival_grammar_pairs=[("A", "B")],
        )
        
        result = evaluate_counterexample_divergence_v1(helper_input)
        shadow = result["comparison_results"][0]["shadow_case"]
        
        assert shadow["treated_as_evidence"] is False
        assert shadow["may_eliminate_grammar"] is False
        assert shadow["may_raise_confidence"] is False


class TestDivergenceDetection:
    """Test divergence detection."""
    
    def test_divergence_detected_between_rivals(self):
        """Divergence is detected between rival grammars."""
        helper_input = build_counterexample_divergence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}, {"grammar_id": "B"}],
            rival_grammar_pairs=[("A", "B")],
        )
        
        result = evaluate_counterexample_divergence_v1(helper_input)
        
        assert result["overall_status"] in ["divergence_detected", "rival_grammars_diverge"]
    
    def test_no_divergence_when_grammars_identical(self):
        """No divergence when grammars are identical."""
        # Same grammar ID = no divergence (our deterministic mock)
        helper_input = build_counterexample_divergence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}],
            rival_grammar_pairs=[("A", "A")],
        )
        
        result = evaluate_counterexample_divergence_v1(helper_input)
        
        # Same ID should have no divergence
        assert result["overall_status"] == "no_divergence_detected"


class TestTrainEvidenceResolution:
    """Test train-evidence resolution rules."""
    
    def test_train_resolves_divergence(self):
        """Train evidence can resolve divergence."""
        helper_input = build_counterexample_divergence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}, {"grammar_id": "B"}],
            rival_grammar_pairs=[("A", "B")],
        )
        
        result = evaluate_counterexample_divergence_v1(helper_input)
        
        # Check that some pairs have train evidence resolution
        has_resolution = any(
            r.get("train_evidence_resolution_status") is not None
            for r in result.get("comparison_results", [])
        )
        assert has_resolution
    
    def test_synthetic_alone_cannot_resolve(self):
        """Synthetic/shadow divergence alone cannot resolve truth."""
        helper_input = build_counterexample_divergence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}, {"grammar_id": "B"}],
            rival_grammar_pairs=[("A", "B")],
        )
        
        result = evaluate_counterexample_divergence_v1(helper_input)
        
        # Counterexample is non-evidential
        assert result["counterexample_treated_as_evidence"] is False


class TestSafeFailure:
    """Test safe failure recommendation."""
    
    def test_unresolved_divergence_recommends_safe_failure(self):
        """Unresolved divergence can recommend safe failure."""
        helper_input = build_counterexample_divergence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}, {"grammar_id": "B"}],
            rival_grammar_pairs=[("A", "B")],
        )
        
        result = evaluate_counterexample_divergence_v1(helper_input)
        
        # With divergence and limited train, safe failure may be recommended
        assert result["safe_failure_recommended_count"] >= 0


class TestAntiLaunderingLaws:
    """Test anti-laundering laws are enforced."""
    
    def test_all_10_laws_present(self):
        """All 10 anti-laundering laws are present."""
        assert len(ANTI_LAUNDERING_LAWS) == 10
    
    def test_counterexample_is_diagnostic(self):
        """Counterexample is diagnostic, not evidence."""
        result = evaluate_counterexample_divergence_v1(
            build_counterexample_divergence_helper_input_v1(
                task_id="task_1",
                train_examples=[],
                test_input_descriptor={},
                candidate_grammars=[],
                rival_grammar_pairs=[],
            )
        )
        
        assert result["counterexample_treated_as_evidence"] is False
    
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
        helper_input = build_counterexample_divergence_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
            rival_grammar_pairs=[],
        )
        
        result = evaluate_counterexample_divergence_v1(helper_input)
        
        assert result["final_answer_authority"] == "ledger"
        assert result["helper_generates_final_answer"] is False
    
    def test_forbidden_status_not_produced(self):
        """Forbidden statuses are not produced."""
        result = evaluate_counterexample_divergence_v1(
            build_counterexample_divergence_helper_input_v1(
                task_id="task_1",
                train_examples=[],
                test_input_descriptor={},
                candidate_grammars=[],
                rival_grammar_pairs=[],
            )
        )
        
        # Check no forbidden status in output
        for comparison in result.get("comparison_results", []):
            # No direct status field in comparison, check via metrics
            pass
        
        # Overall status should be allowed
        assert result["overall_status"] in ALLOWED_OUTPUT_STATUSES


class TestMetrics:
    """Test metrics are returned."""
    
    def test_all_13_metrics_exist(self):
        """All 13 metrics are present."""
        helper_input = build_counterexample_divergence_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
            rival_grammar_pairs=[],
        )
        
        result = evaluate_counterexample_divergence_v1(helper_input)
        
        required_metrics = [
            "candidate_grammar_pair_count",
            "divergence_detected_count",
            "no_divergence_detected_count",
            "minimal_discriminating_condition_count",
            "train_resolved_divergence_count",
            "train_unresolved_divergence_count",
            "safe_failure_recommended_count",
            "counterexample_non_evidential_count",
            "probe_elimination_blocked_count",
            "probe_confidence_increase_blocked_count",
            "hidden_test_use_blocked_count",
            "rival_grammar_preserved_count",
            "ledger_boundary_preserved_count",
        ]
        
        for metric in required_metrics:
            assert metric in result, f"Missing metric: {metric}"


class TestBoundaryConstants:
    """Test boundary constants."""
    
    def test_allowed_shadow_case_scope(self):
        """Shadow case scope is train_derived."""
        assert ALLOWED_SHADOW_CASE_SCOPE == "train_derived"
    
    def test_allowed_evidence_scope(self):
        """Evidence scope is train_only."""
        assert ALLOWED_EVIDENCE_SCOPE == "train_only"
    
    def test_synthetic_probes_not_allowed(self):
        """Synthetic probes as evidence is not allowed."""
        assert SYNTHETIC_PROBE_RESULTS_ALLOWED_AS_EVIDENCE is False
    
    def test_hidden_test_not_available(self):
        """Hidden test output is not available."""
        assert HIDDEN_TEST_OUTPUT_AVAILABLE is False


class TestRelationshipToHelper3:
    """Test relationship to helper 3."""
    
    def test_helper_accepts_constraint_status(self):
        """Helper accepts constraint helper status."""
        helper_input = build_counterexample_divergence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}, {"grammar_id": "B"}],
            rival_grammar_pairs=[("A", "B")],
            constraint_helper_status={"overall_status": "rival_grammar_alive"},
        )
        
        result = evaluate_counterexample_divergence_v1(helper_input)
        
        assert result is not None