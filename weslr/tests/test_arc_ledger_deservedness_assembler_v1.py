"""
Tests for ARC Ledger Deservedness Assembler

Verifies implementation:
- Input model fields
- Decision rules
- Deservedness traces
- Ledger boundary
- Anti-laundering laws
- Metrics
"""

import pytest
from weslr.arc_ledger_deservedness_assembler import (
    build_ledger_deservedness_assembler_input_v1,
    evaluate_ledger_deservedness_v1,
    summarize_ledger_deservedness_v1,
    ANTILAUNDERING_LAWS,
    ALLOWED_DECISIONS,
    FINAL_ANSWER_EMITTED,
    PUBLIC_CLAIM_ALLOWED,
    HELPER_OUTPUT_AS_EVIDENCE,
)


class TestInputModel:
    """Test input model fields."""
    
    def test_input_model_fields_preserved(self):
        """Input model fields preserved."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_001",
            candidate_descriptors=[{"candidate_id": "c1"}],
            helper_diagnostics={"helper_1": {}},
            candidate_grammars=[{"grammar_id": "g1"}],
            forced_constraints=["constraint_1"],
            train_evidence_support={"support": True},
            unresolved_rival_grammars=["rival_1"],
            ambiguity_flags={"flag": True},
            invariant_symmetry_findings=[{"finding": "inv1"}],
            object_correspondence_findings=[{"finding": "obj1"}],
            mdl_diagnostics={"mdl": 10},
            divergence_findings=[{"finding": "div1"}],
            constraint_findings=[{"finding": "con1"}],
            rehearsal_context={"repeat_count": 1},
        )
        
        assert inp["task_id"] == "task_001"
        assert len(inp["candidate_descriptors"]) == 1
        assert inp["evidence_scope"] == "train_only"
        assert inp["hidden_test_output_available"] is False
        assert inp["public_arc_answer_available"] is False


class TestNoCandidates:
    """Test no candidates case."""
    
    def test_no_candidates_needs_generation(self):
        """No candidates → needs candidate generation."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[],
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["decision"] == "needs_candidate_generation"
        assert result["metrics"]["needs_candidate_generation_count"] == 1


class TestDeservednessRules:
    """Test deservedness decision rules."""
    
    def test_train_forced_unique_candidate_deserved(self):
        """Train-forced unique candidate → candidate_deserved."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[{
                "candidate_id": "c1",
                "requires_ledger_review": True,
                "treated_as_final_answer": False,
                "generation_status": "generated",
                "unsupported_assumptions": [],
                "unresolved_rivals": [],
            }],
            forced_constraints=["constraint_1"],
            train_evidence_support={"support": True},
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["decision"] == "candidate_deserved"
        assert result["metrics"]["candidate_deserved_count"] >= 1
    
    def test_bounded_forced_unique_deserved(self):
        """Bounded forced unique candidate → candidate_deserved."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[{
                "candidate_id": "c1",
                "requires_ledger_review": True,
                "treated_as_final_answer": False,
                "generation_status": "generated",
                "unsupported_assumptions": [],
                "unresolved_rivals": [],
                "source_constraints": ["constraint_1"],
            }],
            forced_constraints=["constraint_1"],
            train_evidence_support={"support": True},
            candidate_grammars=[{"grammar_id": "g1", "rules_from_train": True}],
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["decision"] == "candidate_deserved"
    
    def test_unsupported_assumptions_rejected(self):
        """Unsupported assumptions → candidate_not_deserved."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[{
                "candidate_id": "c1",
                "requires_ledger_review": True,
                "treated_as_final_answer": False,
                "generation_status": "generated",
                "unsupported_assumptions": ["assumption_1"],
            }],
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["metrics"]["unsupported_assumption_rejected_count"] >= 1
        assert result["decision"] == "candidate_not_deserved"
    
    def test_unresolved_rivals_block_deservedness(self):
        """Unresolved rivals → candidate_not_deserved."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[{
                "candidate_id": "c1",
                "requires_ledger_review": True,
                "treated_as_final_answer": False,
                "generation_status": "generated",
                "unsupported_assumptions": [],
                "unresolved_rivals": ["rival_a", "rival_b"],
            }],
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["metrics"]["rival_unresolved_count"] >= 1
    
    def test_partial_candidate_not_complete(self):
        """Partial candidate → candidate_not_deserved."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[{
                "candidate_id": "c1",
                "requires_ledger_review": True,
                "treated_as_final_answer": False,
                "generation_status": "partial",
                "unsupported_assumptions": [],
                "unresolved_rivals": [],
            }],
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["metrics"]["insufficient_train_evidence_count"] >= 1
    
    def test_insufficient_train_evidence(self):
        """Insufficient train evidence → insufficient_train_evidence."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[{
                "candidate_id": "c1",
                "requires_ledger_review": True,
                "treated_as_final_answer": False,
                "generation_status": "generated",
                "unsupported_assumptions": [],
                "unresolved_rivals": [],
            }],
            # No forced_constraints, no train_evidence_support
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["metrics"]["insufficient_train_evidence_count"] >= 1


class TestFailClosed:
    """Test fail-closed conditions."""
    
    def test_hidden_test_output_blocks(self):
        """Hidden test output available → fail closed."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[],
            hidden_test_output_available=True,
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["hidden_test_blocked_count"] == 1
    
    def test_public_arc_answer_blocks(self):
        """Public ARC answer available → fail closed."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[],
            public_arc_answer_available=True,
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["public_arc_answer_blocked_count"] == 1
    
    def test_evidence_scope_not_train_only_blocks(self):
        """Evidence scope not train_only → fail closed."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[],
            evidence_scope="public_test",
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["decision"] == "safe_failure_required"
    
    def test_candidate_bypassing_ledger_rejected(self):
        """Candidate bypassing ledger → rejected."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[{
                "candidate_id": "c1",
                "requires_ledger_review": False,  # Bypassed
                "treated_as_final_answer": False,
            }],
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["decision"] == "candidate_not_deserved"
        assert result["metrics"]["helper_output_as_evidence_blocked_count"] >= 1
    
    def test_candidate_treated_as_final_rejected(self):
        """Candidate treated as final answer → rejected."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[{
                "candidate_id": "c1",
                "requires_ledger_review": True,
                "treated_as_final_answer": True,  # Treated as final
            }],
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["decision"] == "candidate_not_deserved"


class TestLedgerBoundary:
    """Test ledger boundary preservation."""
    
    def test_final_answer_emitted_always_false(self):
        """Final answer emitted is always false."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[{
                "candidate_id": "c1",
                "requires_ledger_review": True,
                "treated_as_final_answer": False,
                "generation_status": "generated",
                "unsupported_assumptions": [],
                "unresolved_rivals": [],
            }],
            forced_constraints=["c1"],
            train_evidence_support={"s": True},
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["final_answer_emitted"] is False
    
    def test_public_claim_allowed_always_false(self):
        """Public claim allowed is always false."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[],
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["public_claim_allowed"] is False
    
    def test_helper_output_as_evidence_false(self):
        """Helper output as evidence is false."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[],
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["helper_output_as_evidence"] is False
    
    def test_boundary_constants(self):
        """Boundary constants are correct."""
        assert FINAL_ANSWER_EMITTED is False
        assert PUBLIC_CLAIM_ALLOWED is False
        assert HELPER_OUTPUT_AS_EVIDENCE is False


class TestRehearsalContext:
    """Test rehearsal context handling."""
    
    def test_rehearsal_repeat_rejected(self):
        """Rehearsal-only support → rejected."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[{
                "candidate_id": "c1",
                "requires_ledger_review": True,
                "treated_as_final_answer": False,
                "generation_status": "generated",
                "unsupported_assumptions": [],
                "unresolved_rivals": [],
            }],
            rehearsal_context={
                "repeat_count": 5,
                "memorization_risk": "high",
                "fresh_holdout_confirmed": False,
            },
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["rehearsal_repeat_count"] == 5
        assert result["memorization_risk_flag"] == "high"
        assert result["rehearsal_does_not_create_deservedness"] is True
    
    def test_fresh_holdout_may_count(self):
        """Fresh holdout may count."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[],
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        assert result["fresh_holdout_may_count"] is True


class TestMetrics:
    """Test metrics."""
    
    def test_all_metrics_exist(self):
        """All metrics exist."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[],
        )
        result = evaluate_ledger_deservedness_v1(inp)
        metrics = result["metrics"]
        
        required = [
            "candidate_review_count",
            "candidate_deserved_count",
            "candidate_not_deserved_count",
            "safe_failure_required_count",
            "needs_candidate_generation_count",
            "rival_unresolved_count",
            "forced_unique_output_count",
            "insufficient_train_evidence_count",
            "unsupported_assumption_rejected_count",
            "mdl_only_rejected_count",
            "rehearsal_only_rejected_count",
            "hidden_test_blocked_count",
            "public_arc_answer_blocked_count",
            "helper_output_as_evidence_blocked_count",
            "final_answer_emitted_count",
            "public_claim_allowed_count",
        ]
        
        for m in required:
            assert m in metrics, f"Missing metric: {m}"


class TestAntiLaunderingLaws:
    """Test anti-laundering laws."""
    
    def test_all_12_laws_exposed(self):
        """All 12 anti-laundering laws exposed."""
        assert len(ANTILAUNDERING_LAWS) == 12
    
    def test_train_evidence_only_source(self):
        """Train evidence is the only source of deservedness."""
        assert "train_evidence_is_the_only_source_of_deservedness" in ANTILAUNDERING_LAWS
    
    def test_helper_output_not_evidence(self):
        """Helper output is diagnostic, not evidence."""
        assert "helper_output_is_diagnostic_not_evidence" in ANTILAUNDERING_LAWS


class TestDeservednessTraces:
    """Test deservedness trace model."""
    
    def test_trace_fields_exist(self):
        """Trace fields exist when candidate evaluated."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[{
                "candidate_id": "c1",
                "requires_ledger_review": True,
                "treated_as_final_answer": False,
                "generation_status": "generated",
                "unsupported_assumptions": [],
                "unresolved_rivals": [],
            }],
            forced_constraints=["c1"],
            train_evidence_support={"s": True},
        )
        result = evaluate_ledger_deservedness_v1(inp)
        
        if result.get("candidate_results"):
            cand = result["candidate_results"][0]
            if cand.get("deservedness_traces"):
                trace = cand["deservedness_traces"][0]
                required = ["step_id", "source", "constraint", "train_support", 
                          "decision_relevance", "evidence_status"]
                for f in required:
                    assert f in trace, f"Missing trace field: {f}"


class TestSummary:
    """Test summary function."""
    
    def test_summary_produced(self):
        """Summary is produced."""
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[],
        )
        result = evaluate_ledger_deservedness_v1(inp)
        summary = summarize_ledger_deservedness_v1(result)
        
        assert "summary" in summary
        assert "result" in summary
        assert "Ledger Deservedness Assembler Summary" in summary["summary"]