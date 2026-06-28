"""
Tests for ARC Synthetic Smoke V5 Helper Stack Diagnostic

Verifies V5 implementation:
- 48 tasks across 8 groups
- Baseline vs helper-stack comparison
- Task-level metrics
- Helper-usage metrics
- Frontier metrics
- Interpretation fields
- Safety boundaries preserved
"""

import pytest
from weslr.arc_synthetic_smoke_v5_helper_stack_diagnostic import (
    build_v5_helper_stack_diagnostic_tasks_v1,
    run_v5_helper_stack_diagnostic_v1,
    summarize_v5_helper_stack_diagnostic_v1,
    TASK_GROUPS,
    RUNTIME_WIRING_AVAILABLE,
    PUBLIC_CLAIMS_ALLOWED,
    INTERNAL_120_ENABLED,
    HELPER_INTEGRATION_ENABLED,
)


class TestTaskSuite:
    """Test task suite generation."""
    
    def test_exactly_48_tasks(self):
        """Exactly 48 tasks are generated."""
        tasks = build_v5_helper_stack_diagnostic_tasks_v1()
        assert len(tasks) == 48
    
    def test_exactly_8_groups(self):
        """Exactly 8 groups exist."""
        tasks = build_v5_helper_stack_diagnostic_tasks_v1()
        groups = set(t["group_id"] for t in tasks)
        assert len(groups) == 8
    
    def test_each_group_has_6_tasks(self):
        """Each group has exactly 6 tasks."""
        tasks = build_v5_helper_stack_diagnostic_tasks_v1()
        for group_id in TASK_GROUPS:
            group_tasks = [t for t in tasks if t["group_id"] == group_id]
            assert len(group_tasks) == 6


class TestTaskModel:
    """Test task model fields."""
    
    def test_task_model_fields(self):
        """All required task model fields exist."""
        tasks = build_v5_helper_stack_diagnostic_tasks_v1()
        required_fields = [
            "task_id", "group_id", "train_examples", "test_input_descriptor",
            "baseline_solver_status", "expected_frontier_failure",
            "candidate_grammars", "candidate_invariants", "candidate_correspondences",
            "candidate_mdl_signals", "expected_helper_stack_behavior",
            "expected_ledger_status", "expected_safety_behavior"
        ]
        
        for task in tasks:
            for field in required_fields:
                assert field in task, f"Missing field {field} in task {task['task_id']}"


class TestMetrics:
    """Test metrics exist."""
    
    def test_task_level_metrics(self):
        """All 10 task-level metrics exist."""
        result = run_v5_helper_stack_diagnostic_v1()
        task_metrics = result.get("task_metrics", {})
        
        required = [
            "attempted_tasks", "task_exact_count", "task_exact_rate",
            "task_partial_count", "task_unsupported_count", "task_failed_count",
            "safe_failure_count", "overconfident_wrong_count",
            "deserved_answer_count", "undeserved_answer_blocked_count"
        ]
        
        for metric in required:
            assert metric in task_metrics, f"Missing task metric: {metric}"
    
    def test_helper_usage_metrics(self):
        """All 8 helper-usage metrics exist."""
        result = run_v5_helper_stack_diagnostic_v1()
        helper_metrics = result.get("helper_usage_metrics", {})
        
        required = [
            "constraint_helper_used_count", "divergence_helper_used_count",
            "invariant_symmetry_helper_used_count", "mdl_helper_used_count",
            "object_graph_helper_used_count", "retry_loop_used_count",
            "relation_first_helper_used_count", "promotion_gate_used_count"
        ]
        
        for metric in required:
            assert metric in helper_metrics, f"Missing helper metric: {metric}"
    
    def test_frontier_metrics(self):
        """All 8 frontier metrics exist."""
        result = run_v5_helper_stack_diagnostic_v1()
        frontier_metrics = result.get("frontier_metrics", {})
        
        required = [
            "rival_grammar_resolved_count", "rival_grammar_preserved_count",
            "beautiful_wrong_rule_blocked_count", "helper_trap_blocked_count",
            "object_mapping_ambiguity_detected_count", "invariant_ambiguity_detected_count",
            "mdl_simpler_but_not_forced_count", "safe_failure_recommended_count"
        ]
        
        for metric in required:
            assert metric in frontier_metrics, f"Missing frontier metric: {metric}"


class TestInterpretationFields:
    """Test interpretation fields exist."""
    
    def test_interpretation_fields(self):
        """All interpretation fields exist."""
        result = run_v5_helper_stack_diagnostic_v1()
        
        required = [
            "discipline_improved", "exact_rate_improved_by_guessing",
            "safe_failure_preserved", "overconfident_wrong_preserved_or_reduced",
            "helper_outputs_treated_as_evidence", "ledger_authority_preserved",
            "runtime_wiring_avoided", "public_claims_avoided", "internal_120_blocked"
        ]
        
        for field in required:
            assert field in result, f"Missing interpretation field: {field}"


class TestSafetyBoundaries:
    """Test safety boundaries are preserved."""
    
    def test_runtime_wiring_avoided(self):
        """Runtime wiring is avoided."""
        result = run_v5_helper_stack_diagnostic_v1()
        assert result.get("runtime_wiring_avoided") is True
    
    def test_public_claims_avoided(self):
        """Public claims are avoided."""
        result = run_v5_helper_stack_diagnostic_v1()
        assert result.get("public_claims_avoided") is True
    
    def test_internal_120_blocked(self):
        """Internal 120 is blocked."""
        result = run_v5_helper_stack_diagnostic_v1()
        assert result.get("internal_120_blocked") is True
    
    def test_helper_outputs_not_evidence(self):
        """Helper outputs are not treated as evidence."""
        result = run_v5_helper_stack_diagnostic_v1()
        assert result.get("helper_outputs_treated_as_evidence") is False
    
    def test_ledger_authority_preserved(self):
        """Ledger authority is preserved."""
        result = run_v5_helper_stack_diagnostic_v1()
        assert result.get("ledger_authority_preserved") is True
    
    def test_boundary_constants(self):
        """Boundary constants are correct."""
        assert RUNTIME_WIRING_AVAILABLE is False
        assert PUBLIC_CLAIMS_ALLOWED is False
        assert INTERNAL_120_ENABLED is False
        assert HELPER_INTEGRATION_ENABLED is False


class TestGroupSpecificBehavior:
    """Test group-specific behavior."""
    
    def test_object_graph_ambiguity_detected(self):
        """Object graph ambiguity is detected."""
        result = run_v5_helper_stack_diagnostic_v1()
        frontier = result.get("frontier_metrics", {})
        assert frontier.get("object_mapping_ambiguity_detected_count", 0) > 0
    
    def test_invariant_ambiguity_detected(self):
        """Invariant ambiguity is detected."""
        result = run_v5_helper_stack_diagnostic_v1()
        frontier = result.get("frontier_metrics", {})
        assert frontier.get("invariant_ambiguity_detected_count", 0) > 0
    
    def test_mdl_simpler_not_forced(self):
        """MDL simplicity is not forced."""
        result = run_v5_helper_stack_diagnostic_v1()
        frontier = result.get("frontier_metrics", {})
        assert frontier.get("mdl_simpler_but_not_forced_count", 0) > 0
    
    def test_helper_trap_blocked(self):
        """Helper trap is blocked."""
        result = run_v5_helper_stack_diagnostic_v1()
        frontier = result.get("frontier_metrics", {})
        assert frontier.get("helper_trap_blocked_count", 0) > 0
    
    def test_beautiful_wrong_blocked(self):
        """Beautiful wrong rule is blocked."""
        result = run_v5_helper_stack_diagnostic_v1()
        frontier = result.get("frontier_metrics", {})
        assert frontier.get("beautiful_wrong_rule_blocked_count", 0) > 0
    
    def test_rival_grammar_preserved(self):
        """Rival grammar is preserved."""
        result = run_v5_helper_stack_diagnostic_v1()
        frontier = result.get("frontier_metrics", {})
        assert frontier.get("rival_grammar_preserved_count", 0) > 0
    
    def test_safe_failure_preserved(self):
        """Safe failure is preserved."""
        result = run_v5_helper_stack_diagnostic_v1()
        assert result.get("safe_failure_preserved") is True


class TestSummary:
    """Test summary function."""
    
    def test_summary_produced(self):
        """Summary is produced."""
        result = run_v5_helper_stack_diagnostic_v1()
        summary = summarize_v5_helper_stack_diagnostic_v1(result)
        
        assert "summary" in summary
        assert "result" in summary
        assert "V5 Helper Stack Diagnostic Summary" in summary["summary"]