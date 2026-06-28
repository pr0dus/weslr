"""
Tests for ARC Ledger-Guided Micro-Theory Retry Loop

Verifies the bounded retry loop implementation:
- 12 rejection reason codes supported
- Rejection reason treated as constraint, not evidence
- Max 1 retry round
- Final ledger gate preserved
- Anti-laundering laws enforced
- No runtime solver wiring
- No helper integration
- No auto-improvement
"""

import pytest
from weslr.arc_ledger_guided_micro_theory_retry_loop import (
    build_ledger_rejection_reason_v1,
    build_retry_constraint_from_rejection_v1,
    run_ledger_guided_micro_theory_retry_loop_v1,
    REJECTION_REASON_CODES,
    ALLOWED_RETRY_CONSTRAINTS,
    FORBIDDEN_RETRY_BEHAVIORS,
    TERMINATION_STATES,
    ANTI_LAUNDERING_LAWS,
    MAX_RETRY_ROUNDS,
    SOLVER_BEHAVIOR_CHANGED,
    HELPER_INTEGRATED,
    AUTO_IMPROVEMENT_SEPARATED,
)


class TestRejectionReasonSupport:
    """Test all 12 rejection reason codes are supported."""
    
    def test_all_12_reason_codes_supported(self):
        """All 12 rejection reason codes are defined."""
        expected_codes = [
            "target_uncertain",
            "action_uncertain",
            "representation_uncertain",
            "rival_grammar_alive",
            "train_evidence_underdetermined",
            "beautiful_wrong_rule_not_eliminated",
            "probe_divergence_detected",
            "negative_evidence_not_accounted_for",
            "helper_trap_detected",
            "unsafe_hidden_assumption",
            "coincidence_risk",
            "insufficient_forced_output",
        ]
        assert set(REJECTION_REASON_CODES) == set(expected_codes)
    
    def test_rejection_reason_includes_required_fields(self):
        """Rejection reason includes all required fields."""
        reason = build_ledger_rejection_reason_v1(
            reason_code="target_uncertain",
            affected_candidate_grammar="grammar_A",
            rival_grammar="grammar_B",
            train_example_reference="train_1",
            explanation="Target not forced",
        )
        
        required_fields = [
            "reason_code",
            "explanation",
            "affected_candidate_grammar",
            "rival_grammar",
            "train_example_reference",
            "retry_allowed",
            "retry_constraint",
            "final_abstention_required",
            "treated_as_evidence",
        ]
        
        for field in required_fields:
            assert field in reason, f"Missing field: {field}"
    
    def test_rejection_reason_not_treated_as_evidence(self):
        """Rejection reason is NOT treated as evidence."""
        reason = build_ledger_rejection_reason_v1(
            reason_code="rival_grammar_alive",
            affected_candidate_grammar="grammar_A",
        )
        
        assert reason["treated_as_evidence"] is False
    
    def test_target_uncertain_retry_allowed(self):
        """target_uncertain allows retry."""
        reason = build_ledger_rejection_reason_v1(
            reason_code="target_uncertain",
            affected_candidate_grammar="grammar_A",
        )
        assert reason["retry_allowed"] is True
        assert reason["final_abstention_required"] is False
    
    def test_probe_divergence_no_retry(self):
        """probe_divergence_detected does NOT allow retry."""
        reason = build_ledger_rejection_reason_v1(
            reason_code="probe_divergence_detected",
            affected_candidate_grammar="grammar_A",
        )
        assert reason["retry_allowed"] is False
        assert reason["final_abstention_required"] is True
    
    def test_helper_trap_no_retry(self):
        """helper_trap_detected does NOT allow retry."""
        reason = build_ledger_rejection_reason_v1(
            reason_code="helper_trap_detected",
            affected_candidate_grammar="grammar_A",
        )
        assert reason["retry_allowed"] is False
        assert reason["final_abstention_required"] is True
    
    def test_unsafe_hidden_assumption_no_retry(self):
        """unsafe_hidden_assumption does NOT allow retry."""
        reason = build_ledger_rejection_reason_v1(
            reason_code="unsafe_hidden_assumption",
            affected_candidate_grammar="grammar_A",
        )
        assert reason["retry_allowed"] is False
        assert reason["final_abstention_required"] is True


class TestRetryConstraintBuilder:
    """Test retry constraint builder."""
    
    def test_retry_constraint_generated_from_rejection(self):
        """Retry constraint is generated from rejection reason."""
        rejection = build_ledger_rejection_reason_v1(
            reason_code="target_uncertain",
            affected_candidate_grammar="grammar_A",
        )
        
        constraint = build_retry_constraint_from_rejection_v1(rejection)
        
        assert constraint["constraint_type"] == "retry_with_constraint"
        assert "train evidence" in constraint["constraint"].lower()
        assert constraint["treated_as_evidence"] is False
    
    def test_final_abstention_constraint(self):
        """Final abstention constraint for non-retry cases."""
        rejection = build_ledger_rejection_reason_v1(
            reason_code="probe_divergence_detected",
            affected_candidate_grammar="grammar_A",
        )
        
        constraint = build_retry_constraint_from_rejection_v1(rejection)
        
        assert constraint["constraint_type"] == "final_abstention"
        assert constraint["treated_as_evidence"] is False
    
    def test_train_only_proof_language(self):
        """Retry constraint uses train-only proof language."""
        rejection = build_ledger_rejection_reason_v1(
            reason_code="beautiful_wrong_rule_not_eliminated",
            affected_candidate_grammar="grammar_A",
        )
        
        constraint = build_retry_constraint_from_rejection_v1(rejection)
        
        assert "train" in constraint["constraint"].lower()


class TestRetryLoopBehavior:
    """Test retry loop behavior."""
    
    def test_max_retry_rounds_is_1(self):
        """Max retry rounds is 1."""
        assert MAX_RETRY_ROUNDS == 1
    
    def test_deserved_initial_answer_terminates(self):
        """Deserved initial answer terminates without retry."""
        candidates = [{"grammar": "A"}, {"grammar": "B"}]
        ledgers = [
            {"decision": "deserved", "confidence": 0.9, "answer_was_wrong": False},
        ]
        
        result = run_ledger_guided_micro_theory_retry_loop_v1(candidates, ledgers)
        
        assert result["termination_state"] == "answer_deserved"
        assert result["retry_attempt_count"] == 0
    
    def test_rejected_initial_creates_retry(self):
        """Rejected initial candidate creates one retry."""
        candidates = [{"grammar": "A"}, {"grammar": "A_retry"}]
        ledgers = [
            {"decision": "rejected", "rejection_reason": build_ledger_rejection_reason_v1(
                reason_code="target_uncertain",
                affected_candidate_grammar="grammar_A",
            )},
            {"decision": "deserved", "confidence": 0.8, "answer_was_wrong": False},
        ]
        
        result = run_ledger_guided_micro_theory_retry_loop_v1(candidates, ledgers)
        
        assert result["retry_attempt_count"] == 1
        assert result["retry_success_count"] == 1
        assert result["termination_state"] == "answer_deserved"
    
    def test_failed_retry_terminates_unsupported(self):
        """Failed retry terminates as unsupported."""
        candidates = [{"grammar": "A"}, {"grammar": "A_retry"}]
        ledgers = [
            {"decision": "rejected", "rejection_reason": build_ledger_rejection_reason_v1(
                reason_code="target_uncertain",
                affected_candidate_grammar="grammar_A",
            )},
            {"decision": "rejected", "rejection_reason": build_ledger_rejection_reason_v1(
                reason_code="target_uncertain",
                affected_candidate_grammar="grammar_A_retry",
            ), "safe_unsupported_correct": True},
        ]
        
        result = run_ledger_guided_micro_theory_retry_loop_v1(candidates, ledgers)
        
        assert result["retry_attempt_count"] == 1
        assert result["retry_success_count"] == 0
        assert result["termination_state"] in ["unsupported", "retry_budget_exhausted"]
    
    def test_unresolved_rival_grammar_blocks_answer(self):
        """Unresolved rival grammar blocks answer."""
        candidates = [{"grammar": "A"}, {"grammar": "B"}]
        ledgers = [
            {"decision": "rejected", "rejection_reason": build_ledger_rejection_reason_v1(
                reason_code="rival_grammar_alive",
                affected_candidate_grammar="grammar_A",
                rival_grammar="grammar_B",
            )},
            {"decision": "rejected", "rejection_reason": build_ledger_rejection_reason_v1(
                reason_code="rival_grammar_alive",
                affected_candidate_grammar="grammar_B",
                rival_grammar="grammar_A",
            )},
        ]
        
        result = run_ledger_guided_micro_theory_retry_loop_v1(candidates, ledgers)
        
        assert result["rival_grammar_preserved_count"] > 0
        assert result["termination_state"] in ["rival_grammars_remain", "unsupported"]
    
    def test_final_ledger_gate_preserved(self):
        """Final ledger gate is preserved - answer requires deservedness."""
        candidates = [{"grammar": "A"}, {"grammar": "B"}]
        ledgers = [
            {"decision": "rejected", "rejection_reason": build_ledger_rejection_reason_v1(
                reason_code="target_uncertain",
                affected_candidate_grammar="grammar_A",
            )},
            {"decision": "rejected", "rejection_reason": build_ledger_rejection_reason_v1(
                reason_code="target_uncertain",
                affected_candidate_grammar="grammar_B",
            )},
        ]
        
        result = run_ledger_guided_micro_theory_retry_loop_v1(candidates, ledgers)
        
        assert result["final_ledger_gate_preserved"] is True


class TestAntiLaunderingLaws:
    """Test anti-laundering laws are enforced."""
    
    def test_all_7_anti_laundering_laws_present(self):
        """All 7 anti-laundering laws are present."""
        assert len(ANTI_LAUNDERING_LAWS) == 7
    
    def test_rejection_reason_not_evidence(self):
        """Rejection reason is not evidence."""
        reason = build_ledger_rejection_reason_v1(
            reason_code="target_uncertain",
            affected_candidate_grammar="grammar_A",
        )
        assert reason["treated_as_evidence"] is False
    
    def test_retry_does_not_accumulate_confidence(self):
        """Retry does not accumulate confidence."""
        result = run_ledger_guided_micro_theory_retry_loop_v1(
            [{"grammar": "A"}, {"grammar": "B"}],
            [
                {"decision": "rejected", "rejection_reason": build_ledger_rejection_reason_v1(
                    reason_code="target_uncertain",
                    affected_candidate_grammar="grammar_A",
                )},
                {"decision": "deserved"},
            ]
        )
        
        # No confidence accumulation field - each retry is independent
        assert "confidence_accumulated" not in result or result.get("confidence_accumulated") is None


class TestBoundaryFlags:
    """Test boundary flags are correct."""
    
    def test_solver_behavior_unchanged(self):
        """Solver behavior flag is false."""
        assert SOLVER_BEHAVIOR_CHANGED is False
    
    def test_helper_not_integrated(self):
        """Helper is not integrated into solver."""
        assert HELPER_INTEGRATED is False
    
    def test_auto_improvement_separated(self):
        """Auto-improvement is separated."""
        assert AUTO_IMPROVEMENT_SEPARATED is True
    
    def test_no_runtime_solver_wiring(self):
        """No runtime solver wiring in output."""
        result = run_ledger_guided_micro_theory_retry_loop_v1(
            [{"grammar": "A"}],
            [{"decision": "deserved"}]
        )
        
        # No solver modification flags
        assert result.get("solver_modified") is None or result.get("solver_modified") is False


class TestMetricsReturned:
    """Test metrics are returned."""
    
    def test_metrics_returned(self):
        """All metrics are returned."""
        result = run_ledger_guided_micro_theory_retry_loop_v1(
            [{"grammar": "A"}],
            [{"decision": "deserved"}]
        )
        
        required_metrics = [
            "initial_candidate_count",
            "ledger_rejection_count",
            "retry_attempt_count",
            "retry_success_count",
            "retry_abstain_count",
            "retry_unsafe_count",
            "rival_grammar_preserved_count",
            "overconfident_wrong_before_retry",
            "overconfident_wrong_after_retry",
            "safe_unsupported_preserved_count",
            "rejection_reason_distribution",
            "retry_constraint_distribution",
        ]
        
        for metric in required_metrics:
            assert metric in result, f"Missing metric: {metric}"


class TestHelperTrapAndProbe:
    """Test helper trap and probe divergence do not become evidence."""
    
    def test_helper_trap_no_wire(self):
        """Helper trap does not wire helper."""
        reason = build_ledger_rejection_reason_v1(
            reason_code="helper_trap_detected",
            affected_candidate_grammar="grammar_A",
        )
        
        assert reason["retry_allowed"] is False
        assert reason["final_abstention_required"] is True
        assert reason["treated_as_evidence"] is False
    
    def test_probe_divergence_no_evidence(self):
        """Probe divergence does not become evidence."""
        reason = build_ledger_rejection_reason_v1(
            reason_code="probe_divergence_detected",
            affected_candidate_grammar="grammar_A",
        )
        
        assert reason["retry_allowed"] is False
        assert reason["treated_as_evidence"] is False


class TestNoAutonomousSelfModification:
    """Test no autonomous self-modification."""
    
    def test_no_self_modification(self):
        """Result shows no autonomous self-modification."""
        result = run_ledger_guided_micro_theory_retry_loop_v1(
            [{"grammar": "A"}],
            [{"decision": "deserved"}]
        )
        
        # No modification flags
        assert result.get("solver_modified") is None or result.get("solver_modified") is False
        assert result.get("grammar_promoted") is None or result.get("grammar_promoted") is False