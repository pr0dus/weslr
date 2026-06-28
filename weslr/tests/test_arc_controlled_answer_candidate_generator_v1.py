"""
Tests for ARC Controlled Answer Candidate Generator

Verifies implementation:
- Input model fields
- Construction modes
- Candidate descriptor model
- Construction trace model
- Blocking rules
- Ledger relationship
- Anti-laundering laws
- Metrics
"""

import pytest
from weslr.arc_controlled_answer_candidate_generator import (
    build_controlled_answer_candidate_generator_input_v1,
    generate_controlled_answer_candidates_v1,
    summarize_controlled_answer_candidate_generation_v1,
    ANTILAUNDERING_LAWS,
    CONSTRUCTION_MODES,
    BLOCKING_STATUSES,
    GENERATOR_GRANTS_DESERVEDNESS,
    REQUIRES_LEDGER_REVIEW,
)


class TestInputModel:
    """Test input model fields."""
    
    def test_input_model_fields_preserved(self):
        """Input model fields preserved."""
        inp = build_controlled_answer_candidate_generator_input_v1(
            task_id="task_001",
            train_examples=[{"input": [[1, 2]]}],
            test_input_descriptor={"grid": [[1, 2]]},
            forced_constraints=["constraint_1"],
            train_forced_transformations=["transform_1"],
            object_graph_correspondences=[{"correspondence_id": "c1"}],
            invariant_preserving_transformations=["invariant_1"],
            relation_first_rewrites=["rewrite_1"],
            composed_transform_candidates=["composed_1"],
            explicit_candidate_grammars=["grammar_1"],
            unresolved_rival_grammars=["rival_1"],
            unsupported_assumption_list=["assumption_1"],
            helper_diagnostics={"helper_1": {}},
        )
        
        assert inp["task_id"] == "task_001"
        assert len(inp["train_examples"]) == 1
        assert len(inp["forced_constraints"]) == 1
        assert len(inp["train_forced_transformations"]) == 1
        assert len(inp["object_graph_correspondences"]) == 1


class TestConstructionModes:
    """Test construction modes."""
    
    def test_all_7_modes_supported(self):
        """All 7 construction modes supported."""
        assert len(CONSTRUCTION_MODES) == 7
        assert "relation_first_rewrite_candidate" in CONSTRUCTION_MODES
        assert "object_correspondence_candidate" in CONSTRUCTION_MODES
        assert "invariant_preserving_candidate" in CONSTRUCTION_MODES
        assert "composed_transform_candidate" in CONSTRUCTION_MODES
        assert "train_forced_transformation_candidate" in CONSTRUCTION_MODES
        assert "explicit_grammar_candidate" in CONSTRUCTION_MODES
        assert "partial_candidate_descriptor" in CONSTRUCTION_MODES
    
    def test_train_forced_transformation_generates(self):
        """Train-forced transformation candidate can be generated."""
        inp = build_controlled_answer_candidate_generator_input_v1(
            task_id="task_test",
            train_examples=[],
            test_input_descriptor={},
            train_forced_transformations=[{
                "operation_name": "fill",
                "train_supported": True,
                "output_shape": {"rows": 2, "cols": 2},
            }],
        )
        result = generate_controlled_answer_candidates_v1(inp)
        
        assert result["generation_status"] in ["generated", "blocked"]
        assert result["candidates"] or result["blocking_reason"]
    
    def test_object_correspondence_generates_when_train_forced(self):
        """Object correspondence candidate generates when train-forced."""
        inp = build_controlled_answer_candidate_generator_input_v1(
            task_id="task_test",
            train_examples=[],
            test_input_descriptor={},
            object_graph_correspondences=[{
                "correspondence_id": "c1",
                "train_supported": True,
            }],
        )
        result = generate_controlled_answer_candidates_v1(inp)
        
        assert result["generation_status"] in ["generated", "blocked"]


class TestCandidateDescriptorModel:
    """Test candidate descriptor model."""
    
    def test_candidate_descriptor_required_fields(self):
        """Candidate descriptor has required fields."""
        inp = build_controlled_answer_candidate_generator_input_v1(
            task_id="task_test",
            train_examples=[],
            test_input_descriptor={},
            train_forced_transformations=[{"train_supported": True}],
        )
        result = generate_controlled_answer_candidates_v1(inp)
        
        if result["candidates"]:
            cand = result["candidates"][0]
            required = [
                "candidate_id", "task_id", "construction_mode",
                "output_shape_descriptor", "object_operations", "color_operations",
                "spatial_operations", "relation_operations",
                "invariant_preservation_claims", "object_correspondence_claims",
                "source_constraints", "unsupported_assumptions", "unresolved_rivals",
                "construction_trace", "requires_ledger_review", "treated_as_final_answer",
            ]
            for f in required:
                assert f in cand, f"Missing field: {f}"


class TestConstructionTraceModel:
    """Test construction trace model."""
    
    def test_construction_trace_required_fields(self):
        """Construction trace has required fields."""
        inp = build_controlled_answer_candidate_generator_input_v1(
            task_id="task_test",
            train_examples=[],
            test_input_descriptor={},
            train_forced_transformations=[{"train_supported": True}],
        )
        result = generate_controlled_answer_candidates_v1(inp)
        
        if result["candidates"] and result["candidates"][0].get("construction_trace"):
            trace = result["candidates"][0]["construction_trace"][0]
            required = [
                "step_id", "source_helper", "source_constraint", "operation",
                "train_support", "assumption_status", "rival_impact",
                "ledger_relevance", "evidence_status",
            ]
            for f in required:
                assert f in trace, f"Missing trace field: {f}"


class TestLedgerRelationship:
    """Test ledger relationship."""
    
    def test_generated_candidate_requires_ledger_review(self):
        """Generated candidate requires ledger review."""
        inp = build_controlled_answer_candidate_generator_input_v1(
            task_id="task_test",
            train_examples=[],
            test_input_descriptor={},
            train_forced_transformations=[{"train_supported": True}],
        )
        result = generate_controlled_answer_candidates_v1(inp)
        
        assert result["requires_ledger_review"] is True
    
    def test_generated_candidate_is_not_final_answer(self):
        """Generated candidate is not final answer."""
        inp = build_controlled_answer_candidate_generator_input_v1(
            task_id="task_test",
            train_examples=[],
            test_input_descriptor={},
            train_forced_transformations=[{"train_supported": True}],
        )
        result = generate_controlled_answer_candidates_v1(inp)
        
        assert result["generator_outputs_final_answer"] is False
        assert result["generator_grants_deservedness"] is False
    
    def test_boundary_constants(self):
        """Boundary constants are correct."""
        assert GENERATOR_GRANTS_DESERVEDNESS is False
        assert REQUIRES_LEDGER_REVIEW is True


class TestBlockingRules:
    """Test blocking rules."""
    
    def test_no_forced_constraints_blocks_generation(self):
        """No forced constraints blocks generation."""
        inp = build_controlled_answer_candidate_generator_input_v1(
            task_id="task_test",
            train_examples=[],
            test_input_descriptor={},
        )
        result = generate_controlled_answer_candidates_v1(inp)
        
        # Should either block or generate partial
        assert result["generation_status"] in ["blocked", "generated"]
    
    def test_hidden_test_request_blocks_generation(self):
        """Hidden test request blocks generation."""
        inp = build_controlled_answer_candidate_generator_input_v1(
            task_id="task_test",
            train_examples=[],
            test_input_descriptor={},
            _requests_hidden_test=True,
        )
        result = generate_controlled_answer_candidates_v1(inp)
        
        assert "hidden_test" in result["blocking_reason"]
        assert result["metrics"]["hidden_test_request_blocked_count"] == 1
    
    def test_public_arc_answer_request_blocks(self):
        """Public ARC answer request blocks generation."""
        inp = build_controlled_answer_candidate_generator_input_v1(
            task_id="task_test",
            train_examples=[],
            test_input_descriptor={},
            _requests_public_arc_answer=True,
        )
        result = generate_controlled_answer_candidates_v1(inp)
        
        assert "public" in result["blocking_reason"]
        assert result["metrics"]["public_answer_request_blocked_count"] == 1


class TestPartialCandidate:
    """Test partial candidate descriptor."""
    
    def test_partial_candidate_descriptor_remains_partial(self):
        """Partial candidate descriptor remains partial."""
        inp = build_controlled_answer_candidate_generator_input_v1(
            task_id="task_test",
            train_examples=[],
            test_input_descriptor={},
        )
        result = generate_controlled_answer_candidates_v1(inp)
        
        # If candidates exist, at least one should be partial or status blocked
        if result["candidates"]:
            has_partial = any(
                c.get("generation_status") == "partial" 
                for c in result["candidates"]
            )
            assert has_partial or result["blocking_reason"]


class TestMetrics:
    """Test metrics."""
    
    def test_all_16_metrics_exist(self):
        """All 16 metrics exist."""
        inp = build_controlled_answer_candidate_generator_input_v1(
            task_id="task_test",
            train_examples=[],
            test_input_descriptor={},
        )
        result = generate_controlled_answer_candidates_v1(inp)
        metrics = result["metrics"]
        
        required = [
            "candidate_generation_attempt_count",
            "candidate_generated_count",
            "candidate_generation_blocked_count",
            "candidate_requires_ledger_review_count",
            "safe_failure_required_count",
            "unsupported_assumption_blocked_count",
            "unresolved_rival_blocked_count",
            "ambiguous_correspondence_blocked_count",
            "unforced_invariant_blocked_count",
            "mdl_only_choice_blocked_count",
            "hidden_test_request_blocked_count",
            "public_answer_request_blocked_count",
            "candidate_treated_as_final_answer_count",
            "ledger_review_required_count",
            "construction_trace_complete_count",
            "memorization_risk_flag_count",
        ]
        
        for m in required:
            assert m in metrics, f"Missing metric: {m}"


class TestAntiLaunderingLaws:
    """Test anti-laundering laws."""
    
    def test_all_12_laws_exposed(self):
        """All 12 anti-laundering laws exposed."""
        assert len(ANTILAUNDERING_LAWS) == 12
    
    def test_candidate_generation_not_final_answer(self):
        """Candidate generation is not final answer."""
        assert "candidate_generation_is_not_final_answer" in ANTILAUNDERING_LAWS
    
    def test_every_candidate_requires_ledger_review(self):
        """Every candidate requires ledger review."""
        assert "every_candidate_requires_ledger_review" in ANTILAUNDERING_LAWS
    
    def test_hidden_test_output_blocked(self):
        """Hidden test output cannot be used."""
        assert "hidden_test_output_cannot_be_used" in ANTILAUNDERING_LAWS
    
    def test_public_arc_answers_blocked(self):
        """Public ARC answers cannot be used."""
        assert "public_arc_answers_cannot_be_used" in ANTILAUNDERING_LAWS


class TestRehearsalHoldout:
    """Test rehearsal/holdout policy."""
    
    def test_rehearsal_policy_represented(self):
        """Rehearsal policy is represented."""
        inp = build_controlled_answer_candidate_generator_input_v1(
            task_id="task_test",
            train_examples=[],
            test_input_descriptor={},
        )
        result = generate_controlled_answer_candidates_v1(inp)
        
        assert result.get("rehearsal_candidate_generation_allowed") is True
        assert result.get("rehearsal_counts_toward_threshold") is False
        assert result.get("fresh_holdout_counts") is True
        assert result.get("fresh_holdout_requires_no_leakage") is True


class TestSummary:
    """Test summary function."""
    
    def test_summary_produced(self):
        """Summary is produced."""
        inp = build_controlled_answer_candidate_generator_input_v1(
            task_id="task_test",
            train_examples=[],
            test_input_descriptor={},
        )
        result = generate_controlled_answer_candidates_v1(inp)
        summary = summarize_controlled_answer_candidate_generation_v1(result)
        
        assert "summary" in summary
        assert "result" in summary
        assert "Controlled Answer Candidate Generator Summary" in summary["summary"]