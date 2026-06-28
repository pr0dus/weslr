"""
Tests for ARC Constraint Satisfaction / Rival Grammar Helper

Verifies helper family 3/8:
- Input model with train-only scope
- Candidate grammar evaluation
- Rival grammar preservation
- Anti-laundering laws
- Ledger boundary preserved
- No runtime solver wiring
"""

import pytest
from weslr.arc_constraint_satisfaction_rival_grammar_helper import (
    build_constraint_helper_input_v1,
    evaluate_candidate_grammar_constraints_v1,
    summarize_rival_grammar_constraint_status_v1,
    ALLOWED_OUTPUT_STATUSES,
    FORBIDDEN_OUTPUT_STATUSES,
    ANTI_LAUNDERING_LAWS,
    FINAL_ANSWER_AUTHORITY,
    HELPER_GENERATES_FINAL_ANSWER,
    HELPER_RANKS_GRAMMARS,
    HELPER_REPAIRS_GRAMMAR,
    ALLOWED_EVIDENCE_SCOPE,
    HIDDEN_TEST_OUTPUT_AVAILABLE,
    SYNTHETIC_PROBE_RESULTS_ALLOWED,
)


class TestInputModel:
    """Test input model with proper boundaries."""
    
    def test_train_only_evidence_scope(self):
        """Helper input sets train_only evidence scope."""
        helper_input = build_constraint_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1, 2], "output": [3]}],
            test_input_descriptor={"input": [1, 2]},
            candidate_grammars=[{"grammar_id": "A"}],
            candidate_predictions=[{"output": [3]}],
        )
        
        assert helper_input["allowed_evidence_scope"] == "train_only"
    
    def test_hidden_test_output_fails_closed(self):
        """Hidden test output availability fails closed."""
        with pytest.raises(ValueError, match="hidden_test_output_available"):
            build_constraint_helper_input_v1(
                task_id="task_1",
                train_examples=[],
                test_input_descriptor={},
                candidate_grammars=[],
                candidate_predictions=[],
                ledger_rejection_context={"hidden_test_output_available": True},
            )
    
    def test_synthetic_probe_fails_closed(self):
        """Synthetic probe results allowed fails closed."""
        with pytest.raises(ValueError, match="synthetic_probe_results_allowed"):
            build_constraint_helper_input_v1(
                task_id="task_1",
                train_examples=[],
                test_input_descriptor={},
                candidate_grammars=[],
                candidate_predictions=[],
                ledger_rejection_context={"synthetic_probe_results_used": True},
            )


class TestCandidateGrammarModel:
    """Test candidate grammar required fields."""
    
    def test_grammar_required_fields(self):
        """Candidate grammar supports required fields."""
        grammar = {
            "grammar_id": "A",
            "private_language": "private_A",
            "target_selection_rule": "rule_1",
            "action_rule": "action_1",
            "representation_rule": "rep_1",
            "claimed_train_support": ["train_0"],
            "predicted_test_output_descriptor": {"output": [1, 2]},
            "known_rivals": ["B"],
            "assumptions": [],
        }
        
        helper_input = build_constraint_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[grammar],
            candidate_predictions=[{"output": [2]}],
        )
        
        result = evaluate_candidate_grammar_constraints_v1(helper_input)
        
        assert len(result["grammar_results"]) == 1
        assert result["grammar_results"][0]["grammar_id"] == "A"


class TestConstraintChecks:
    """Test constraint check implementation."""
    
    def test_one_unique_forced_grammar(self):
        """One unique forced grammar produces candidate_deserved_if_unique_and_forced."""
        helper_input = build_constraint_helper_input_v1(
            task_id="task_1",
            train_examples=[
                {"input": [1], "output": [2]},
            ],
            test_input_descriptor={},
            candidate_grammars=[
                {"grammar_id": "A"},
            ],
            candidate_predictions=[
                {"output": [2]},  # A matches train
            ],
        )
        
        result = evaluate_candidate_grammar_constraints_v1(helper_input)
        
        # Exactly one grammar consistent = candidate_deserved_if_unique_and_forced
        assert result["overall_status"] == "candidate_deserved_if_unique_and_forced"
    
    def test_multiple_consistent_grammars(self):
        """Multiple consistent grammars produce rival_grammar_alive."""
        helper_input = build_constraint_helper_input_v1(
            task_id="task_1",
            train_examples=[
                {"input": [1], "output": [2]},
            ],
            test_input_descriptor={},
            candidate_grammars=[
                {"grammar_id": "A"},
                {"grammar_id": "B"},
            ],
            candidate_predictions=[
                {"output": [2]},  # Both match
                {"output": [2]},
            ],
        )
        
        result = evaluate_candidate_grammar_constraints_v1(helper_input)
        
        assert result["overall_status"] == "rival_grammar_alive"
    
    def test_all_inconsistent_grammars(self):
        """All inconsistent grammars produce all_grammars_eliminated."""
        helper_input = build_constraint_helper_input_v1(
            task_id="task_1",
            train_examples=[
                {"input": [1], "output": [2]},
            ],
            test_input_descriptor={},
            candidate_grammars=[
                {"grammar_id": "A"},
            ],
            candidate_predictions=[
                {"output": [99]},  # Doesn't match
            ],
        )
        
        result = evaluate_candidate_grammar_constraints_v1(helper_input)
        
        assert result["overall_status"] == "all_grammars_eliminated"
    
    def test_unsupported_assumption(self):
        """Unsupported assumption produces candidate_not_deserved."""
        helper_input = build_constraint_helper_input_v1(
            task_id="task_1",
            train_examples=[
                {"input": [1], "output": [2]},
            ],
            test_input_descriptor={},
            candidate_grammars=[
                {
                    "grammar_id": "A",
                    "assumptions": [{"name": "hidden", "supported_by_train": False}],
                },
            ],
            candidate_predictions=[
                {"output": [2]},  # Matches but has unsupported assumption
            ],
        )
        
        result = evaluate_candidate_grammar_constraints_v1(helper_input)
        
        assert result["grammar_results"][0]["status"] == "candidate_not_deserved"
    
    def test_train_contradiction_eliminates(self):
        """Train contradiction eliminates grammar."""
        helper_input = build_constraint_helper_input_v1(
            task_id="task_1",
            train_examples=[
                {"input": [1], "output": [2]},
                {"input": [2], "output": [3]},
            ],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}],
            candidate_predictions=[
                {"output": [2]},  # Matches first but not second
            ],
        )
        
        result = evaluate_candidate_grammar_constraints_v1(helper_input)
        
        assert result["grammar_results"][0]["status"] == "grammar_eliminated_by_train_evidence"


class TestAntiLaunderingLaws:
    """Test anti-laundering laws are enforced."""
    
    def test_all_8_laws_present(self):
        """All 8 anti-laundering laws are present."""
        assert len(ANTI_LAUNDERING_LAWS) == 8
    
    def test_train_only_elimination(self):
        """Train evidence only eliminates grammars."""
        helper_input = build_constraint_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}],
            candidate_predictions=[{"output": [99]}],
        )
        
        result = evaluate_candidate_grammar_constraints_v1(helper_input)
        
        assert result["train_only_elimination_count"] == 1
    
    def test_synthetic_probe_cannot_eliminate(self):
        """Synthetic probe cannot eliminate grammar."""
        # Note: This is enforced by design - no synthetic probes in input
        assert SYNTHETIC_PROBE_RESULTS_ALLOWED is False
    
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
        helper_input = build_constraint_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
            candidate_predictions=[],
        )
        
        result = evaluate_candidate_grammar_constraints_v1(helper_input)
        
        assert result["final_answer_authority"] == "ledger"
        assert result["helper_generates_final_answer"] is False
    
    def test_forbidden_status_not_produced(self):
        """Forbidden statuses are not produced."""
        result = evaluate_candidate_grammar_constraints_v1(
            build_constraint_helper_input_v1(
                task_id="task_1",
                train_examples=[],
                test_input_descriptor={},
                candidate_grammars=[],
                candidate_predictions=[],
            )
        )
        
        # Check no forbidden status in output
        for grammar_result in result.get("grammar_results", []):
            status = grammar_result.get("status")
            assert status not in FORBIDDEN_OUTPUT_STATUSES


class TestMetrics:
    """Test metrics are returned."""
    
    def test_all_13_metrics_exist(self):
        """All 13 metrics are present."""
        helper_input = build_constraint_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
            candidate_predictions=[],
        )
        
        result = evaluate_candidate_grammar_constraints_v1(helper_input)
        
        required_metrics = [
            "candidate_grammar_count",
            "grammar_consistent_count",
            "grammar_eliminated_count",
            "rival_grammar_alive_count",
            "underdetermined_count",
            "all_eliminated_count",
            "forced_unique_candidate_count",
            "unsupported_assumption_count",
            "contradiction_count",
            "train_only_elimination_count",
            "synthetic_probe_elimination_attempt_blocked_count",
            "deserved_candidate_count",
            "candidate_not_deserved_count",
        ]
        
        for metric in required_metrics:
            assert metric in result, f"Missing metric: {metric}"


class TestRelationshipToHelper2:
    """Test relationship to helper 2 (Ledger-Guided Retry Loop)."""
    
    def test_helper_input_accepts_ledger_context(self):
        """Helper input accepts ledger rejection context."""
        helper_input = build_constraint_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
            candidate_grammars=[],
            candidate_predictions=[],
            ledger_rejection_context={"reason_code": "target_uncertain"},
        )
        
        assert helper_input["ledger_rejection_context"] is not None
    
    def test_ledger_boundary_preserved(self):
        """Ledger boundary is preserved - helper is diagnostic only."""
        helper_input = build_constraint_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_grammars=[{"grammar_id": "A"}],
            candidate_predictions=[{"output": [2]}],
        )
        
        result = evaluate_candidate_grammar_constraints_v1(helper_input)
        summary = summarize_rival_grammar_constraint_status_v1(result)
        
        # Summary is diagnostic, not final answer
        assert "final_answer_authority" in summary
        assert summary["final_answer_authority"] == "ledger"


class TestBoundaryConstants:
    """Test boundary constants."""
    
    def test_allowed_evidence_scope(self):
        """Evidence scope is train_only."""
        assert ALLOWED_EVIDENCE_SCOPE == "train_only"
    
    def test_hidden_test_output_not_available(self):
        """Hidden test output is not available."""
        assert HIDDEN_TEST_OUTPUT_AVAILABLE is False
    
    def test_synthetic_probes_not_allowed(self):
        """Synthetic probes are not allowed."""
        assert SYNTHETIC_PROBE_RESULTS_ALLOWED is False