"""
Tests for ARC Sequential Statistical Promotion Gate Helper

Verifies helper family 7/8:
- Statistical improvement evaluation
- Holdout and regression checks
- Safety boundary preservation
- Anti-laundering laws
- Owner approval required
- No auto-merge
- No runtime behavior changes
"""

import pytest
from weslr.arc_sequential_statistical_promotion_gate_helper import (
    build_statistical_promotion_gate_input_v1,
    evaluate_statistical_promotion_gate_v1,
    summarize_statistical_promotion_gate_status_v1,
    ALLOWED_OUTPUT_STATUSES,
    FORBIDDEN_OUTPUT_STATUSES,
    ANTI_LAUNDERING_LAWS,
    OWNER_APPROVAL_REQUIRED,
    AUTO_MERGE_ALLOWED,
    RUNTIME_WIRING_ALLOWED,
    PUBLIC_CLAIM_ALLOWED,
    HELPER_CHANGES_RUNTIME_BEHAVIOR,
    HELPER_PROMOTES_AUTOMATICALLY,
    OFFICIAL_ARC_CLAIM_ALLOWED,
    SAFETY_GATE_WEAKENED,
    ALLOWED_EVIDENCE_SCOPE,
)


class TestInputModel:
    """Test input model with proper boundaries."""
    
    def test_owner_approval_required(self):
        """Helper input sets owner approval required."""
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=[],
            candidate_run_results=[],
        )
        
        assert helper_input["owner_approval_required"] is True
    
    def test_auto_merge_fails_closed(self):
        """Auto-merge is always False."""
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=[],
            candidate_run_results=[],
        )
        
        assert helper_input["auto_merge_allowed"] is False
    
    def test_runtime_wiring_fails_closed(self):
        """Runtime wiring is always False."""
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=[],
            candidate_run_results=[],
        )
        
        assert helper_input["runtime_wiring_allowed"] is False
    
    def test_public_claim_fails_closed(self):
        """Public claim is always False."""
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=[],
            candidate_run_results=[],
        )
        
        assert helper_input["public_claim_allowed"] is False
    
    def test_allowed_evidence_scope(self):
        """Evidence scope is local/approved only."""
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=[],
            candidate_run_results=[],
        )
        
        assert helper_input["allowed_evidence_scope"] == "local_synthetic_and_approved_private_only"


class TestPromotionPolicyFailClosed:
    """Test promotion policy fail-closed behavior."""
    
    def test_regression_not_allowed(self):
        """Regression is not allowed."""
        with pytest.raises(ValueError):
            build_statistical_promotion_gate_input_v1(
                candidate_change_id="change_1",
                baseline_run_results=[],
                candidate_run_results=[],
                promotion_policy={"regression_allowed": True},
            )
    
    def test_holdout_required(self):
        """Holdout is required."""
        with pytest.raises(ValueError):
            build_statistical_promotion_gate_input_v1(
                candidate_change_id="change_1",
                baseline_run_results=[],
                candidate_run_results=[],
                promotion_policy={"requires_holdout": False},
            )
    
    def test_owner_approval_required_policy(self):
        """Owner approval is required."""
        with pytest.raises(ValueError):
            build_statistical_promotion_gate_input_v1(
                candidate_change_id="change_1",
                baseline_run_results=[],
                candidate_run_results=[],
                promotion_policy={"requires_owner_approval": False},
            )
    
    def test_no_public_claim_policy(self):
        """No public claim is required."""
        with pytest.raises(ValueError):
            build_statistical_promotion_gate_input_v1(
                candidate_change_id="change_1",
                baseline_run_results=[],
                candidate_run_results=[],
                promotion_policy={"requires_no_public_claim": False},
            )


class TestStatisticalImprovement:
    """Test statistical improvement evaluation."""
    
    def test_statistical_improvement_observed(self):
        """Statistical improvement is observed."""
        baseline = [{"task_count": 100, "task_exact_count": 10}]
        candidate = [{"task_count": 100, "task_exact_count": 20}]
        
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=baseline,
            candidate_run_results=candidate,
            holdout_run_results=[{"task_count": 100, "task_exact_count": 15}],
        )
        
        result = evaluate_statistical_promotion_gate_v1(helper_input)
        
        assert result["task_exact_rate_delta"] > 0
    
    def test_insufficient_sample_size(self):
        """Insufficient sample size blocks promotion."""
        baseline = [{"task_count": 100, "task_exact_count": 10}]
        candidate = [{"task_count": 5, "task_exact_count": 1}]  # Small sample
        
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=baseline,
            candidate_run_results=candidate,
        )
        
        result = evaluate_statistical_promotion_gate_v1(helper_input)
        
        assert result["overall_status"] == "insufficient_evidence"
    
    def test_no_improvement(self):
        """No improvement blocks promotion."""
        baseline = [{"task_count": 100, "task_exact_count": 10}]
        candidate = [{"task_count": 100, "task_exact_count": 10}]  # Same
        
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=baseline,
            candidate_run_results=candidate,
        )
        
        result = evaluate_statistical_promotion_gate_v1(helper_input)
        
        assert result["overall_status"] == "promotion_blocked"


class TestHoldoutValidation:
    """Test holdout validation."""
    
    def test_holdout_passed(self):
        """Holdout passes."""
        baseline = [{"task_count": 100, "task_exact_count": 10, "variant_family": "baseline_family"}]
        candidate = [{"task_count": 100, "task_exact_count": 20, "variant_family": "candidate_family"}]
        holdout = [{"task_count": 100, "task_exact_count": 18, "variant_family": "holdout_family"}]
        
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=baseline,
            candidate_run_results=candidate,
            holdout_run_results=holdout,
        )
        
        result = evaluate_statistical_promotion_gate_v1(helper_input)
        
        assert result["holdout_status"] == "holdout_passed"
    
    def test_holdout_failed(self):
        """Holdout fails."""
        baseline = [{"task_count": 100, "task_exact_count": 10, "variant_family": "baseline_family"}]
        candidate = [{"task_count": 100, "task_exact_count": 20, "variant_family": "candidate_family"}]
        holdout = [{"task_count": 100, "task_exact_count": 5, "variant_family": "holdout_family"}]  # Worse than baseline
        
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=baseline,
            candidate_run_results=candidate,
            holdout_run_results=holdout,
        )
        
        result = evaluate_statistical_promotion_gate_v1(helper_input)
        
        assert result["overall_status"] == "holdout_failed"


class TestSafetyRegression:
    """Test safety regression detection."""
    
    def test_overconfident_wrong_increase(self):
        """Overconfident wrong increase blocks promotion."""
        baseline = [
            {"task_count": 100, "task_exact_count": 10, "overconfident_wrong_count": 0}
        ]
        candidate = [
            {"task_count": 100, "task_exact_count": 20, "overconfident_wrong_count": 5}
        ]
        
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=baseline,
            candidate_run_results=candidate,
        )
        
        result = evaluate_statistical_promotion_gate_v1(helper_input)
        
        assert result["overall_status"] == "overconfident_wrong_increased"
    
    def test_safe_unsupported_damaged(self):
        """Safe unsupported damage blocks promotion."""
        baseline = [
            {"task_count": 100, "task_exact_count": 10, "safe_unsupported_count": 10}
        ]
        candidate = [
            {"task_count": 100, "task_exact_count": 20, "safe_unsupported_count": 1}
        ]
        
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=baseline,
            candidate_run_results=candidate,
        )
        
        result = evaluate_statistical_promotion_gate_v1(helper_input)
        
        assert result["overall_status"] == "safe_unsupported_damaged"


class TestSameSuiteOverfit:
    """Test same-suite overfit detection."""
    
    def test_same_suite_quarantined(self):
        """Same suite improvement quarantines."""
        baseline = [
            {"task_count": 100, "task_exact_count": 10, "variant_family": "family_a"}
        ]
        candidate = [
            {"task_count": 100, "task_exact_count": 20, "variant_family": "family_a"}
        ]
        
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=baseline,
            candidate_run_results=candidate,
            holdout_run_results=[{"task_count": 100, "task_exact_count": 15, "variant_family": "family_a"}],
        )
        
        result = evaluate_statistical_promotion_gate_v1(helper_input)
        
        assert result["overall_status"] == "promotion_quarantined"


class TestPromotionCandidate:
    """Test promotion candidate detection."""
    
    def test_promotion_candidate(self):
        """All gates pass = promotion candidate."""
        baseline = [{"task_count": 100, "task_exact_count": 10, "variant_family": "baseline_family"}]
        candidate = [{"task_count": 100, "task_exact_count": 20, "variant_family": "candidate_family"}]
        holdout = [{"task_count": 100, "task_exact_count": 18, "variant_family": "holdout_family"}]
        
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=baseline,
            candidate_run_results=candidate,
            holdout_run_results=holdout,
        )
        
        result = evaluate_statistical_promotion_gate_v1(helper_input)
        
        assert result["overall_status"] == "promotion_candidate"
        assert result["owner_approval_required"] is True
    
    def test_promotion_candidate_requires_owner_approval(self):
        """Promotion candidate still requires owner approval."""
        baseline = [{"task_count": 100, "task_exact_count": 10, "variant_family": "baseline_family"}]
        candidate = [{"task_count": 100, "task_exact_count": 20, "variant_family": "candidate_family"}]
        holdout = [{"task_count": 100, "task_exact_count": 18, "variant_family": "holdout_family"}]
        
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=baseline,
            candidate_run_results=candidate,
            holdout_run_results=holdout,
        )
        
        result = evaluate_statistical_promotion_gate_v1(helper_input)
        
        assert result["owner_approval_required"] is True
        assert result["final_promotion_authority"] == "owner"


class TestBoundaryConstants:
    """Test boundary constants."""
    
    def test_owner_approval_required_constant(self):
        """Owner approval required is True."""
        assert OWNER_APPROVAL_REQUIRED is True
    
    def test_auto_merge_allowed_constant(self):
        """Auto-merge allowed is False."""
        assert AUTO_MERGE_ALLOWED is False
    
    def test_runtime_wiring_allowed_constant(self):
        """Runtime wiring allowed is False."""
        assert RUNTIME_WIRING_ALLOWED is False
    
    def test_public_claim_allowed_constant(self):
        """Public claim allowed is False."""
        assert PUBLIC_CLAIM_ALLOWED is False
    
    def test_helper_changes_runtime_behavior_constant(self):
        """Helper changes runtime behavior is False."""
        assert HELPER_CHANGES_RUNTIME_BEHAVIOR is False
    
    def test_helper_promotes_automatically_constant(self):
        """Helper promotes automatically is False."""
        assert HELPER_PROMOTES_AUTOMATICALLY is False
    
    def test_official_arc_claim_allowed_constant(self):
        """Official ARC claim allowed is False."""
        assert OFFICIAL_ARC_CLAIM_ALLOWED is False
    
    def test_safety_gate_weakened_constant(self):
        """Safety gate weakened is False."""
        assert SAFETY_GATE_WEAKENED is False


class TestAntiLaunderingLaws:
    """Test anti-laundering laws are enforced."""
    
    def test_all_12_laws_present(self):
        """All 12 anti-laundering laws are present."""
        assert len(ANTI_LAUNDERING_LAWS) == 12
    
    def test_helper_does_not_auto_merge(self):
        """Helper does not auto-merge."""
        assert AUTO_MERGE_ALLOWED is False
    
    def test_helper_does_not_change_runtime(self):
        """Helper does not change runtime behavior."""
        assert HELPER_CHANGES_RUNTIME_BEHAVIOR is False


class TestForbiddenStatuses:
    """Test forbidden statuses are not produced."""
    
    def test_forbidden_status_not_produced(self):
        """Forbidden statuses are not produced."""
        baseline = [{"task_count": 100, "task_exact_count": 10}]
        candidate = [{"task_count": 100, "task_exact_count": 20}]
        
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=baseline,
            candidate_run_results=candidate,
            holdout_run_results=[{"task_count": 100, "task_exact_count": 15}],
        )
        
        result = evaluate_statistical_promotion_gate_v1(helper_input)
        
        # Overall status should be allowed
        assert result["overall_status"] in ALLOWED_OUTPUT_STATUSES


class TestMetrics:
    """Test metrics are returned."""
    
    def test_all_21_metrics_exist(self):
        """All 21 metrics are present."""
        helper_input = build_statistical_promotion_gate_input_v1(
            candidate_change_id="change_1",
            baseline_run_results=[],
            candidate_run_results=[],
        )
        
        result = evaluate_statistical_promotion_gate_v1(helper_input)
        
        required_metrics = [
            "baseline_task_exact_rate",
            "candidate_task_exact_rate",
            "task_exact_rate_delta",
            "holdout_task_exact_rate",
            "holdout_delta",
            "confidence_interval_low",
            "confidence_interval_high",
            "sample_size_total",
            "fresh_variant_count",
            "same_suite_repeat_count",
            "overconfident_wrong_delta",
            "safe_unsupported_delta",
            "unsafe_count_delta",
            "failed_count_delta",
            "regression_detected_count",
            "holdout_pass_count",
            "holdout_fail_count",
            "promotion_candidate_count",
            "promotion_blocked_count",
            "promotion_quarantined_count",
            "owner_approval_required_count",
        ]
        
        for metric in required_metrics:
            assert metric in result, f"Missing metric: {metric}"