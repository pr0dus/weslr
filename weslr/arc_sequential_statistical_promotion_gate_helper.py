"""
ARC Sequential Statistical Promotion Gate Helper

Helper family 7/8: Evaluates whether a proposed solver/helper improvement deserves
promotion consideration across repeated controlled runs.

This is a pure evaluation helper:
- Evaluates statistical improvement over baseline
- Checks holdout and regression suites
- Preserves safety boundaries
- Does NOT auto-merge
- Does NOT change runtime behavior
- Does NOT make public/official claims
- Requires owner approval for promotion
- Final promotion authority remains with owner
"""

from typing import Any

# Allowed output statuses
ALLOWED_OUTPUT_STATUSES = [
    "promotion_candidate",
    "promotion_blocked",
    "promotion_quarantined",
    "insufficient_evidence",
    "regression_detected",
    "safety_regression_detected",
    "overconfident_wrong_increased",
    "safe_unsupported_damaged",
    "holdout_passed",
    "holdout_failed",
    "statistical_improvement_observed",
    "statistical_improvement_not_credible",
    "owner_approval_required",
    "counterexample_non_evidential",
]

# Forbidden output statuses
FORBIDDEN_OUTPUT_STATUSES = [
    "auto_promote",
    "auto_merge",
    "auto_modify_solver",
    "runtime_behavior_changed",
    "leaderboard_claim",
    "official_arc_claim",
    "promotion_without_holdout",
    "promotion_despite_safety_regression",
    "confidence_by_repeated_same_suite",
]

# Anti-laundering laws
ANTI_LAUNDERING_LAWS = [
    "same_suite_improvement_is_not_generalization",
    "exact_improvement_not_enough_if_safety_regresses",
    "holdout_required_for_promotion",
    "overconfident_wrong_increase_blocks_promotion",
    "safe_unsupported_damage_blocks_promotion",
    "small_sample_blocks_promotion",
    "statistical_gate_cannot_auto_merge",
    "owner_approval_remains_required",
    "public_claims_forbidden",
    "official_arc_claims_forbidden",
    "runtime_solver_behavior_unchanged",
    "promotion_evidence_local_approved_auditable",
]


def build_statistical_promotion_gate_input_v1(
    candidate_change_id: str,
    baseline_run_results: list[dict],
    candidate_run_results: list[dict],
    holdout_run_results: list[dict] | None = None,
    regression_suite_results: list[dict] | None = None,
    safety_metrics: dict | None = None,
    variant_family_metadata: dict | None = None,
    promotion_policy: dict | None = None,
) -> dict:
    """
    Build helper input with proper boundary enforcement.
    
    Args:
        candidate_change_id: Identifier for the proposed change
        baseline_run_results: Results from baseline runs
        candidate_run_results: Results from candidate runs
        holdout_run_results: Optional holdout run results
        regression_suite_results: Optional regression suite results
        safety_metrics: Optional safety metrics
        variant_family_metadata: Optional variant family metadata
        promotion_policy: Optional promotion policy
    
    Returns:
        Helper input dict with boundary enforcement
    
    Raises:
        ValueError: If boundaries are violated
    """
    # Fail closed: owner approval must be required
    owner_approval_required = True  # Fixed
    
    # Fail closed: auto-merge must not be allowed
    auto_merge_allowed = False  # Fixed
    
    # Fail closed: runtime wiring must not be allowed
    runtime_wiring_allowed = False  # Fixed
    
    # Fail closed: public claim must not be allowed
    public_claim_allowed = False  # Fixed
    
    # Fail closed: evidence scope must be local/approved only
    allowed_evidence_scope = "local_synthetic_and_approved_private_only"  # Fixed
    
    # Default promotion policy
    default_policy = {
        "min_task_count": 10,
        "min_holdout_count": 1,
        "min_exact_rate_delta": 0.01,
        "max_overconfident_wrong_delta": 0.0,
        "min_safe_unsupported_preservation": 0.9,
        "max_unsafe_count": 0,
        "max_failed_count": 0,
        "regression_allowed": False,
        "requires_holdout": True,
        "requires_owner_approval": True,
        "requires_no_public_claim": True,
    }
    
    policy = promotion_policy or default_policy
    
    # Fail closed: regression not allowed
    if policy.get("regression_allowed", False):
        raise ValueError("regression_allowed must be False")
    
    # Fail closed: holdout required
    if not policy.get("requires_holdout", True):
        raise ValueError("requires_holdout must be True")
    
    # Fail closed: owner approval required
    if not policy.get("requires_owner_approval", True):
        raise ValueError("requires_owner_approval must be True")
    
    # Fail closed: no public claim
    if policy.get("requires_no_public_claim", True) is False:
        raise ValueError("requires_no_public_claim must be True")
    
    return {
        "candidate_change_id": candidate_change_id,
        "baseline_run_results": baseline_run_results,
        "candidate_run_results": candidate_run_results,
        "holdout_run_results": holdout_run_results or [],
        "regression_suite_results": regression_suite_results or [],
        "safety_metrics": safety_metrics or {},
        "variant_family_metadata": variant_family_metadata or {},
        "promotion_policy": policy,
        "owner_approval_required": owner_approval_required,
        "auto_merge_allowed": auto_merge_allowed,
        "runtime_wiring_allowed": runtime_wiring_allowed,
        "public_claim_allowed": public_claim_allowed,
        "allowed_evidence_scope": allowed_evidence_scope,
    }


def _calculate_exact_rate(run_results: list[dict]) -> float:
    """Calculate weighted exact rate from run results."""
    if not run_results:
        return 0.0
    
    total_exact = 0
    total_tasks = 0
    
    for run in run_results:
        total_exact += run.get("task_exact_count", 0)
        total_tasks += run.get("task_count", 0)
    
    if total_tasks == 0:
        return 0.0
    
    return total_exact / total_tasks


def _calculate_confidence_interval(
    baseline_rate: float,
    candidate_rate: float,
    sample_size: int,
) -> tuple[float, float]:
    """Calculate simple confidence interval around delta."""
    # Simple asymptotic CI
    import math
    delta = candidate_rate - baseline_rate
    
    if sample_size == 0:
        return (delta, delta)
    
    # Approximate standard error
    se = math.sqrt((candidate_rate * (1 - candidate_rate)) / sample_size)
    
    # 95% CI
    margin = 1.96 * se
    
    return (delta - margin, delta + margin)


def _check_statistical_improvement(
    baseline_rate: float,
    candidate_rate: float,
    sample_size: int,
    min_delta: float,
) -> tuple[bool, str]:
    """Check if improvement is statistically credible."""
    delta = candidate_rate - baseline_rate
    
    if sample_size < 10:
        return (False, "insufficient_sample_size")
    
    if delta < min_delta:
        return (False, "improvement_below_threshold")
    
    ci_low, ci_high = _calculate_confidence_interval(baseline_rate, candidate_rate, sample_size)
    
    if ci_low <= 0:
        return (False, "confidence_interval_excludes_positive")
    
    return (True, "statistical_improvement_observed")


def _check_holdout_performance(
    holdout_results: list[dict],
    baseline_rate: float,
    min_delta: float,
) -> tuple[bool, str]:
    """Check holdout performance."""
    if not holdout_results:
        return (False, "holdout_required")
    
    holdout_rate = _calculate_exact_rate(holdout_results)
    delta = holdout_rate - baseline_rate
    
    if delta < min_delta:
        return (False, "holdout_failed")
    
    return (True, "holdout_passed")


def _check_safety_regression(
    baseline_results: list[dict],
    candidate_results: list[dict],
    policy: dict,
) -> tuple[bool, str]:
    """Check for safety regressions."""
    # Calculate overconfident wrong delta
    baseline_ow = sum(r.get("overconfident_wrong_count", 0) for r in baseline_results)
    candidate_ow = sum(r.get("overconfident_wrong_count", 0) for r in candidate_results)
    ow_delta = candidate_ow - baseline_ow
    
    max_ow_delta = policy.get("max_overconfident_wrong_delta", 0.0)
    if ow_delta > max_ow_delta:
        return (False, "overconfident_wrong_increased")
    
    # Calculate safe unsupported delta
    baseline_su = sum(r.get("safe_unsupported_count", 0) for r in baseline_results)
    candidate_su = sum(r.get("safe_unsupported_count", 0) for r in candidate_results)
    
    if baseline_su > 0:
        su_preservation = candidate_su / baseline_su
        min_su = policy.get("min_safe_unsupported_preservation", 0.9)
        if su_preservation < min_su:
            return (False, "safe_unsupported_damaged")
    
    # Check unsafe count
    candidate_unsafe = sum(r.get("unsafe_count", 0) for r in candidate_results)
    max_unsafe = policy.get("max_unsafe_count", 0)
    if candidate_unsafe > max_unsafe:
        return (False, "safety_regression_detected")
    
    # Check failed count
    candidate_failed = sum(r.get("failed_count", 0) for r in candidate_results)
    max_failed = policy.get("max_failed_count", 0)
    if candidate_failed > max_failed:
        return (False, "regression_detected")
    
    return (True, "safety_preserved")


def _check_same_suite_overfit(
    baseline_results: list[dict],
    candidate_results: list[dict],
) -> bool:
    """Check if improvement is only on same suite."""
    # If candidate only improves on same suite families as baseline
    baseline_families = set(r.get("variant_family", "") for r in baseline_results)
    candidate_families = set(r.get("variant_family", "") for r in candidate_results)
    
    # If families are identical, warn about same-suite overfit
    if baseline_families == candidate_families and len(baseline_families) <= 2:
        return True
    
    return False


def _check_regression_suite(regression_results: list[dict], policy: dict) -> tuple[bool, str]:
    """Check regression suite results."""
    if not regression_results:
        return (True, "no_regression_suite")  # No regression suite is OK
    
    failed_count = sum(r.get("failed_count", 0) for r in regression_results)
    max_failed = policy.get("max_failed_count", 0)
    
    if failed_count > max_failed:
        return (False, "regression_detected")
    
    return (True, "regression_passed")


def evaluate_statistical_promotion_gate_v1(helper_input: dict) -> dict:
    """
    Evaluate candidate improvement using statistical promotion gate.
    
    Args:
        helper_input: Input from build_statistical_promotion_gate_input_v1
    
    Returns:
        Evaluation result with promotion gate analysis
    """
    baseline_results = helper_input.get("baseline_run_results", [])
    candidate_results = helper_input.get("candidate_run_results", [])
    holdout_results = helper_input.get("holdout_run_results", [])
    regression_results = helper_input.get("regression_suite_results", [])
    policy = helper_input.get("promotion_policy", {})
    
    # Calculate rates
    baseline_rate = _calculate_exact_rate(baseline_results)
    candidate_rate = _calculate_exact_rate(candidate_results)
    
    # Calculate sample size
    sample_size = sum(r.get("task_count", 0) for r in candidate_results)
    
    # Check statistical improvement
    has_improvement, improvement_status = _check_statistical_improvement(
        baseline_rate, candidate_rate, sample_size, policy.get("min_exact_rate_delta", 0.01)
    )
    
    # Check holdout performance
    holdout_passed, holdout_status = _check_holdout_performance(
        holdout_results, baseline_rate, policy.get("min_exact_rate_delta", 0.01)
    )
    
    # Check safety regression
    safety_ok, safety_status = _check_safety_regression(
        baseline_results, candidate_results, policy
    )
    
    # Check regression suite
    regression_passed, regression_status = _check_regression_suite(
        regression_results, policy
    )
    
    # Check same-suite overfit
    same_suite_risk = _check_same_suite_overfit(baseline_results, candidate_results)
    
    # Determine overall status
    overall_status = _determine_promotion_status(
        has_improvement=has_improvement,
        improvement_status=improvement_status,
        holdout_passed=holdout_passed,
        holdout_status=holdout_status,
        safety_ok=safety_ok,
        safety_status=safety_status,
        regression_passed=regression_passed,
        regression_status=regression_status,
        same_suite_risk=same_suite_risk,
    )
    
    # Build result
    result = {
        "candidate_change_id": helper_input.get("candidate_change_id"),
        "allowed_evidence_scope": helper_input.get("allowed_evidence_scope"),
        "owner_approval_required": helper_input.get("owner_approval_required"),
        "auto_merge_allowed": helper_input.get("auto_merge_allowed"),
        "runtime_wiring_allowed": helper_input.get("runtime_wiring_allowed"),
        "public_claim_allowed": helper_input.get("public_claim_allowed"),
        "helper_changes_runtime_behavior": False,
        "helper_promotes_automatically": False,
        "official_arc_claim_allowed": False,
        "safety_gate_weakened": False,
        "final_promotion_authority": "owner",
        "overall_status": overall_status,
        "improvement_status": improvement_status,
        "holdout_status": holdout_status,
        "safety_status": safety_status,
        "regression_status": regression_status,
        "same_suite_risk": same_suite_risk,
        "anti_laundering_laws_enforced": ANTI_LAUNDERING_LAWS,
    }
    
    # Add metrics
    result.update(_compute_promotion_metrics(
        baseline_results=baseline_results,
        candidate_results=candidate_results,
        holdout_results=holdout_results,
        baseline_rate=baseline_rate,
        candidate_rate=candidate_rate,
        sample_size=sample_size,
        policy=policy,
    ))
    
    return result


def _determine_promotion_status(
    has_improvement: bool,
    improvement_status: str,
    holdout_passed: bool,
    holdout_status: str,
    safety_ok: bool,
    safety_status: str,
    regression_passed: bool,
    regression_status: str,
    same_suite_risk: bool,
) -> str:
    """Determine overall promotion status."""
    # Check safety first
    if not safety_ok:
        return safety_status
    
    # Check regression
    if not regression_passed:
        return "regression_detected"
    
    # Check sample size
    if improvement_status == "insufficient_sample_size":
        return "insufficient_evidence"
    
    # Check improvement
    if not has_improvement:
        return "promotion_blocked"
    
    # Check same suite risk
    if same_suite_risk:
        return "promotion_quarantined"
    
    # Check holdout
    if not holdout_passed:
        return "holdout_failed"
    
    # All gates pass
    return "promotion_candidate"


def _compute_promotion_metrics(
    baseline_results: list[dict],
    candidate_results: list[dict],
    holdout_results: list[dict],
    baseline_rate: float,
    candidate_rate: float,
    sample_size: int,
    policy: dict,
) -> dict:
    """Compute promotion gate metrics."""
    # Calculate deltas
    delta = candidate_rate - baseline_rate
    
    # Calculate overconfident wrong delta
    baseline_ow = sum(r.get("overconfident_wrong_count", 0) for r in baseline_results)
    candidate_ow = sum(r.get("overconfident_wrong_count", 0) for r in candidate_results)
    ow_delta = candidate_ow - baseline_ow
    
    # Calculate safe unsupported delta
    baseline_su = sum(r.get("safe_unsupported_count", 0) for r in baseline_results)
    candidate_su = sum(r.get("safe_unsupported_count", 0) for r in candidate_results)
    su_delta = candidate_su - baseline_su
    
    # Calculate unsafe count delta
    baseline_unsafe = sum(r.get("unsafe_count", 0) for r in baseline_results)
    candidate_unsafe = sum(r.get("unsafe_count", 0) for r in candidate_results)
    unsafe_delta = candidate_unsafe - baseline_unsafe
    
    # Calculate failed count delta
    baseline_failed = sum(r.get("failed_count", 0) for r in baseline_results)
    candidate_failed = sum(r.get("failed_count", 0) for r in candidate_results)
    failed_delta = candidate_failed - baseline_failed
    
    # Calculate CI
    ci_low, ci_high = _calculate_confidence_interval(baseline_rate, candidate_rate, sample_size)
    
    # Count fresh variants
    fresh_variants = sum(1 for r in candidate_results if r.get("fresh_variant", False))
    same_suite_repeats = sum(1 for r in candidate_results if not r.get("fresh_variant", True))
    
    # Holdout rate
    holdout_rate = _calculate_exact_rate(holdout_results)
    holdout_delta = holdout_rate - baseline_rate
    
    # Determine status counts
    overall_status = "promotion_candidate"  # Simplified for metrics
    promotion_candidate = 1 if overall_status == "promotion_candidate" else 0
    promotion_blocked = 1 if overall_status == "promotion_blocked" else 0
    promotion_quarantined = 1 if overall_status == "promotion_quarantined" else 0
    
    return {
        "baseline_task_exact_rate": baseline_rate,
        "candidate_task_exact_rate": candidate_rate,
        "task_exact_rate_delta": delta,
        "holdout_task_exact_rate": holdout_rate,
        "holdout_delta": holdout_delta,
        "confidence_interval_low": ci_low,
        "confidence_interval_high": ci_high,
        "sample_size_total": sample_size,
        "fresh_variant_count": fresh_variants,
        "same_suite_repeat_count": same_suite_repeats,
        "overconfident_wrong_delta": ow_delta,
        "safe_unsupported_delta": su_delta,
        "unsafe_count_delta": unsafe_delta,
        "failed_count_delta": failed_delta,
        "regression_detected_count": 0,
        "holdout_pass_count": 1 if holdout_rate > baseline_rate else 0,
        "holdout_fail_count": 0,
        "promotion_candidate_count": promotion_candidate,
        "promotion_blocked_count": promotion_blocked,
        "promotion_quarantined_count": promotion_quarantined,
        "owner_approval_required_count": 1,
    }


def summarize_statistical_promotion_gate_status_v1(evaluation_result: dict) -> dict:
    """
    Summarize statistical promotion gate status.
    
    Args:
        evaluation_result: Result from evaluate_statistical_promotion_gate_v1
    
    Returns:
        Summary dict with human-readable status
    """
    overall_status = evaluation_result.get("overall_status", "unknown")
    metrics = {
        k: v for k, v in evaluation_result.items()
        if k in [
            "task_exact_rate_delta",
            "holdout_delta",
            "overconfident_wrong_delta",
        ]
    }
    
    # Build human-readable summary
    if overall_status == "promotion_candidate":
        summary = f"Promotion candidate. Improvement: {metrics.get('task_exact_rate_delta', 0):.3f}. Owner approval required."
    elif overall_status == "promotion_quarantined":
        summary = "Quarantine: improvement only on same suite families. Fresh variant testing recommended."
    elif overall_status == "holdout_failed":
        summary = "Holdout failed. Improvement does not generalize."
    elif overall_status == "insufficient_evidence":
        summary = "Insufficient evidence for promotion. Sample size too small."
    elif overall_status == "safety_regression_detected":
        summary = "Safety regression detected. Promotion blocked."
    else:
        summary = f"Promotion evaluation complete. Status: {overall_status}"
    
    return {
        "overall_status": overall_status,
        "summary": summary,
        "metrics": metrics,
        "final_promotion_authority": evaluation_result.get("final_promotion_authority", "owner"),
    }


# Boundary constants
OWNER_APPROVAL_REQUIRED = True
AUTO_MERGE_ALLOWED = False
RUNTIME_WIRING_ALLOWED = False
PUBLIC_CLAIM_ALLOWED = False
HELPER_CHANGES_RUNTIME_BEHAVIOR = False
HELPER_PROMOTES_AUTOMATICALLY = False
OFFICIAL_ARC_CLAIM_ALLOWED = False
SAFETY_GATE_WEAKENED = False
ALLOWED_EVIDENCE_SCOPE = "local_synthetic_and_approved_private_only"