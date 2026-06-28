"""
Tests for ARC Synthetic Smoke V3 Diagnostic

Verifies the V3 diagnostic implementation:
- Task builder returns 36 tasks
- All 6 groups exist
- Each group has exactly 6 tasks
- Task IDs are unique
- Helper eligibility is counted
- Helper is not applied
- Public/kaggle/benchmark flags are fail-closed
- Run function returns correct metrics
- V1/V2 comparison reference exists
- Relation-first helper is not called/applied
- Solver-freeze flags preserved
"""

import pytest
from weslr.arc_synthetic_smoke_v3_diagnostic import (
    build_arc_synthetic_smoke_v3_tasks_v1,
    run_arc_synthetic_smoke_v3_diagnostic_v1,
    GROUPS,
    HELPER_ELIGIBLE_GROUPS,
    SAFE_FAILURE_GROUPS,
    SOLVER_BEHAVIOR_CHANGED,
    SOLVER_PRIMITIVES_ADDED,
    BENCHMARK_CLAIM_SAFE,
    SYNTHETIC_ONLY,
    PUBLIC_ARC_USED,
    KAGGLE_USED,
)


class TestTaskBuilder:
    """Test task builder returns correct structure."""
    
    def test_returns_36_tasks(self):
        """Task builder returns 36 tasks."""
        tasks = build_arc_synthetic_smoke_v3_tasks_v1()
        assert len(tasks) == 36
    
    def test_all_6_groups_exist(self):
        """All 6 groups are present."""
        tasks = build_arc_synthetic_smoke_v3_tasks_v1()
        groups_present = set(task["group_id"] for task in tasks)
        assert groups_present == set(GROUPS)
    
    def test_each_group_has_6_tasks(self):
        """Each group has exactly 6 tasks."""
        tasks = build_arc_synthetic_smoke_v3_tasks_v1()
        for group in GROUPS:
            group_tasks = [t for t in tasks if t["group_id"] == group]
            assert len(group_tasks) == 6, f"Group {group} has {len(group_tasks)} tasks"
    
    def test_task_ids_unique(self):
        """All task IDs are unique."""
        tasks = build_arc_synthetic_smoke_v3_tasks_v1()
        task_ids = [t["task_id"] for t in tasks]
        assert len(task_ids) == len(set(task_ids)), "Duplicate task IDs found"
    
    def test_helper_eligibility_counted(self):
        """Helper eligibility is correctly counted."""
        tasks = build_arc_synthetic_smoke_v3_tasks_v1()
        eligible = [t for t in tasks if t["helper_eligible"]]
        # 3 groups × 6 tasks = 18 helper-eligible tasks
        assert len(eligible) == 18
    
    def test_helper_not_applied(self):
        """Helper is NOT applied in any task."""
        tasks = build_arc_synthetic_smoke_v3_tasks_v1()
        applied = [t for t in tasks if t.get("helper_applied", False)]
        assert len(applied) == 0, "Helper was applied to some tasks"
    
    def test_boundary_flags_fail_closed(self):
        """Public/kaggle/benchmark flags are fail-closed."""
        tasks = build_arc_synthetic_smoke_v3_tasks_v1()
        for task in tasks:
            assert task["synthetic_only"] is True
            assert task["public_arc_used"] is False
            assert task["kaggle_used"] is False
            assert task["benchmark_claim_safe"] is False


class TestRunFunction:
    """Test run function returns correct metrics."""
    
    def test_returns_dict(self):
        """Run function returns a dictionary."""
        result = run_arc_synthetic_smoke_v3_diagnostic_v1()
        assert isinstance(result, dict)
    
    def test_task_metrics_exist(self):
        """Task-level metrics exist."""
        result = run_arc_synthetic_smoke_v3_diagnostic_v1()
        required = [
            "attempted_task_count",
            "task_exact_count",
            "task_exact_rate",
            "task_partial_count",
            "task_partial_rate",
            "task_unsupported_count",
            "task_unsupported_rate",
            "task_failed_count",
            "task_failed_rate",
        ]
        for field in required:
            assert field in result, f"Missing: {field}"
    
    def test_packet_metrics_exist(self):
        """Packet-level metrics exist."""
        result = run_arc_synthetic_smoke_v3_diagnostic_v1()
        required = [
            "packet_total",
            "packet_exact_count",
            "packet_exact_rate",
            "packet_partial_count",
            "packet_partial_rate",
            "packet_unsupported_count",
            "packet_unsupported_rate",
            "packet_failed_count",
            "packet_failed_rate",
        ]
        for field in required:
            assert field in result, f"Missing: {field}"
    
    def test_packet_metrics_diagnostic_only(self):
        """Packet metrics are marked as diagnostic only."""
        result = run_arc_synthetic_smoke_v3_diagnostic_v1()
        assert result.get("packet_metrics_diagnostic_only") is True
    
    def test_group_metrics_exist(self):
        """Group-level metrics exist."""
        result = run_arc_synthetic_smoke_v3_diagnostic_v1()
        assert "group_metrics" in result
        for group in GROUPS:
            assert group in result["group_metrics"]
    
    def test_threshold_uses_task_exact_rate(self):
        """Threshold uses task_exact_rate only."""
        result = run_arc_synthetic_smoke_v3_diagnostic_v1()
        assert result.get("threshold_basis") == "task_exact_rate"
        assert result.get("internal_threshold") == 0.85
    
    def test_helper_flags_correct(self):
        """Helper flags are correct."""
        result = run_arc_synthetic_smoke_v3_diagnostic_v1()
        assert result.get("helper_not_applied_flag") is True
        assert result.get("helper_applied_task_count") == 0
    
    def test_v1_v2_comparison_reference_exists(self):
        """V1/V2 comparison reference exists."""
        result = run_arc_synthetic_smoke_v3_diagnostic_v1()
        assert result.get("v1_attempted_tasks") == 36
        assert result.get("v2_attempted_tasks") == 36
        assert result.get("v1_v2_task_exact_count") == 31
        assert result.get("v1_v2_task_exact_rate") == 0.8611111111111112
    
    def test_task_count_36(self):
        """Attempted task count is 36."""
        result = run_arc_synthetic_smoke_v3_diagnostic_v1()
        assert result.get("attempted_task_count") == 36


class TestHelperBoundary:
    """Test helper is not applied."""
    
    def test_helper_not_called(self):
        """Relation-first helper is not called."""
        result = run_arc_synthetic_smoke_v3_diagnostic_v1()
        assert result.get("helper_applied_task_count") == 0
        assert result.get("helper_not_applied_flag") is True


class TestSolverFreeze:
    """Test solver-freeze flags."""
    
    def test_solver_behavior_unchanged(self):
        """Solver behavior flag is false."""
        assert SOLVER_BEHAVIOR_CHANGED is False
    
    def test_solver_primitives_unchanged(self):
        """Solver primitives flag is false."""
        assert SOLVER_PRIMITIVES_ADDED is False
    
    def test_benchmark_claim_safe(self):
        """Benchmark claim safe flag is false."""
        assert BENCHMARK_CLAIM_SAFE is False
    
    def test_synthetic_only(self):
        """Synthetic-only flag is true."""
        assert SYNTHETIC_ONLY is True
    
    def test_no_public_arc(self):
        """Public ARC flag is false."""
        assert PUBLIC_ARC_USED is False
    
    def test_no_kaggle(self):
        """Kaggle flag is false."""
        assert KAGGLE_USED is False


class TestMetricValues:
    """Test metric values are reasonable."""
    
    def test_task_metrics_sum_to_36(self):
        """Task metrics sum to 36."""
        result = run_arc_synthetic_smoke_v3_diagnostic_v1()
        total = (
            result["task_exact_count"] +
            result["task_partial_count"] +
            result["task_unsupported_count"] +
            result["task_failed_count"]
        )
        assert total == 36
    
    def test_task_exact_rate_in_range(self):
        """Task exact rate is between 0 and 1."""
        result = run_arc_synthetic_smoke_v3_diagnostic_v1()
        assert 0 <= result["task_exact_rate"] <= 1
    
    def test_helper_eligible_count_18(self):
        """Helper eligible task count is 18."""
        result = run_arc_synthetic_smoke_v3_diagnostic_v1()
        assert result.get("helper_eligible_task_count") == 18
    
    def test_packet_total_72(self):
        """Packet total is 72 (36 × 2)."""
        result = run_arc_synthetic_smoke_v3_diagnostic_v1()
        assert result.get("packet_total") == 72