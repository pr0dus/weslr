# WESLR ARC SEQUENTIAL STATISTICAL PROMOTION GATE HELPER DESIGN V1

## 1. Executive verdict
`arc_sequential_statistical_promotion_gate_helper_design_ready`

## 2. Purpose and mathematical grounding

### Purpose
Design a pure helper that evaluates whether a proposed solver/helper improvement deserves promotion across repeated controlled runs.

### Mathematical Grounding
- **Sequential hypothesis testing**: Sequential probability ratio tests for staged validation
- **Confidence intervals**: Statistical bounds around improvement estimates
- **Binomial proportion tests**: For exact rate comparisons
- **Sequential probability ratio testing (SPRT)**: Early stopping with bounds
- **Multi-armed bandit caution**: Exploration vs exploitation tradeoffs
- **PAC-style validation intuition**: Probably Approximately Correct validation
- **Regression testing and holdout validation**: Traditional software testing concepts
- **False discovery control**: Multiple comparison corrections

## 3. Helper roadmap position

| # | Helper | Status |
|---|--------|--------|
| 1 | Relation-First Compiler Helper | Complete |
| 2 | Ledger-Guided Micro-Theory Retry Loop Helper | Complete (functional) |
| 3 | Constraint Satisfaction / Rival Grammar Helper | Complete (functional + repair) |
| 4 | Counterexample / Divergence Helper | Complete (functional + repair) |
| 5 | Invariant / Symmetry Helper | Complete (functional + repair) |
| 6 | Minimum Description Length / Compression Helper | Complete (functional) |
| 7 | **Sequential Statistical Promotion Gate Helper** | **Current lane** |
| 8 | Object Graph Correspondence Helper | Not yet |

## 4. Input model

```python
helper_input = {
    "candidate_change_id": str,
    "baseline_run_results": list[dict],
    "candidate_run_results": list[dict],
    "holdout_run_results": list[dict],
    "regression_suite_results": list[dict],
    "safety_metrics": dict,
    "variant_family_metadata": dict,
    "promotion_policy": dict,
    "owner_approval_required": True,  # Fixed
    "auto_merge_allowed": False,  # Fixed
    "runtime_wiring_allowed": False,  # Fixed
    "public_claim_allowed": False,  # Fixed
    "allowed_evidence_scope": "local_synthetic_and_approved_private_only",  # Fixed
}
```

## 5. Run result model

```python
run_result = {
    "run_id": str,
    "suite_id": str,
    "variant_family": str,
    "task_count": int,
    "task_exact_count": int,
    "task_exact_rate": float,
    "packet_exact_count": int,
    "packet_exact_rate": float,
    "unsupported_count": int,
    "overconfident_wrong_count": int,
    "safe_unsupported_count": int,
    "unsafe_count": int,
    "failed_count": int,
    "seed": int,
    "fresh_variant": bool,
    "is_holdout": bool,
}
```

## 6. Promotion policy model

```python
promotion_policy = {
    "min_task_count": int,
    "min_holdout_count": int,
    "min_exact_rate_delta": float,
    "max_overconfident_wrong_delta": float,
    "min_safe_unsupported_preservation": float,
    "max_unsafe_count": int,
    "max_failed_count": int,
    "regression_allowed": False,  # Fixed
    "requires_holdout": True,  # Fixed
    "requires_owner_approval": True,  # Fixed
    "requires_no_public_claim": True,  # Fixed
}
```

## 7. Statistical checks

| Check | Description |
|-------|-------------|
| exact-rate_improvement | Compare baseline vs candidate exact rates |
| confidence_interval | Calculate CI around improvement |
| holdout_improvement | Check holdout performance |
| fresh_variant_improvement | Check performance on new variants |
| regression_suite_preservation | Check regression suite passes |
| overconfident_wrong_delta | Check overconfident wrong change |
| safe_unsupported_preservation | Check safe unsupported preservation |
| unsafe_count_check | Check unsafe count threshold |
| failed_count_check | Check failed count threshold |
| same_suite_overfit_warning | Warn if only same suite improves |
| insufficient_sample_size | Block on small samples |

## 8. Decision logic

| Condition | Output |
|-----------|--------|
| Improvement positive but sample too small | insufficient_evidence |
| Improvement only on same suite | promotion_quarantined |
| Exact improves but overconfident wrong rises | overconfident_wrong_increased |
| Exact improves but safe unsupported damaged | safe_unsupported_damaged |
| Holdout fails | holdout_failed |
| Regression detected | regression_detected |
| All gates pass | promotion_candidate + owner_approval_required |
| Safety preserved | holdout_passed |

## 9. Relationship to helpers 1–6

| Helper | Primary Function | Helper 7 Relationship |
|--------|------------------|----------------------|
| 1 | Relation-First Compilation | May propose changes |
| 2 | Retry Loop | May propose changes |
| 3 | Constraint Satisfaction | May propose changes |
| 4 | Divergence Detection | May propose changes |
| 5 | Invariant/Symmetry | May propose changes |
| 6 | MDL Compression | May propose changes |
| 7 | **Statistical Promotion Gate** | Evaluates all proposals |

**Flow**:
1. Helpers 1–6 may propose or diagnose improvements
2. Helper 7 evaluates whether improvement deserves promotion consideration
3. Helper 7 does NOT change solver behavior
4. Helper 7 does NOT promote automatically
5. Helper 7 protects WESLR from overfitting, score-chasing, safety regression
6. Final promotion requires owner approval

## 10. Ledger / safety boundary

### May say (diagnostic)
- "candidate improvement is statistically credible on local synthetic variants"
- "holdout passed"
- "safety regression detected"
- "promotion candidate, owner approval required"
- "quarantine due to overfit risk"
- "insufficient evidence for promotion"
- "regression detected"

### May NOT say (automatic authority)
- "merge automatically"
- "modify solver"
- "publicly claim capability"
- "official ARC score improved"
- "safety gate can be weakened"
- "auto_promote"
- "runtime_behavior_changed"

Final promotion authority remains with owner.

## 11. Anti-laundering laws

1. **Same-suite improvement is not generalization** — Fresh variants required
2. **Exact improvement is not enough if safety regresses** — Both must improve
3. **Holdout is required for promotion consideration** — No holdout = no promotion
4. **Overconfident wrong increase blocks promotion** — Safety first
5. **Safe unsupported damage blocks promotion** — Unsupported behavior protected
6. **Small sample size blocks promotion** — Statistical credibility required
7. **Statistical gate cannot auto-merge** — No automatic merging
8. **Owner approval remains required** — Human in the loop
9. **Public claims remain forbidden** — No public ARC/Kaggle claims
10. **Official ARC/Kaggle claims remain forbidden** — Local only
11. **Runtime solver behavior remains unchanged** — No runtime modification
12. **Promotion evidence must be local/approved and auditable** — No external data

## 12. Metrics design

| Metric | Description |
|--------|-------------|
| baseline_task_exact_rate | Baseline exact rate |
| candidate_task_exact_rate | Candidate exact rate |
| task_exact_rate_delta | Improvement delta |
| holdout_task_exact_rate | Holdout exact rate |
| holdout_delta | Holdout improvement |
| confidence_interval_low | CI lower bound |
| confidence_interval_high | CI upper bound |
| sample_size_total | Total tasks evaluated |
| fresh_variant_count | Fresh variants evaluated |
| same_suite_repeat_count | Same-suite repeats |
| overconfident_wrong_delta | Overconfident wrong change |
| safe_unsupported_delta | Safe unsupported change |
| unsafe_count_delta | Unsafe count change |
| failed_count_delta | Failed count change |
| regression_detected_count | Regression detections |
| holdout_pass_count | Holdout passes |
| holdout_fail_count | Holdout failures |
| promotion_candidate_count | Promotion candidates |
| promotion_blocked_count | Blocked promotions |
| promotion_quarantined_count | Quarantined candidates |
| owner_approval_required_count | Owner approval required |

## 13. Recommended next safe local follow-up
`IMPLEMENT_ARC_SEQUENTIAL_STATISTICAL_PROMOTION_GATE_HELPER_V1`

Rationale:
- Design is clean and bounded
- Mathematical grounding is explicit (sequential testing, confidence intervals)
- Relationship to helpers 1–6 is clear
- Anti-laundering laws prevent automatic promotion
- Owner approval required — human in the loop preserved
- Metrics design is comprehensive

---
Helper roadmap count: 7/8
Mathematical grounding included: yes (sequential hypothesis testing, confidence intervals, SPRT)
Input model defined: yes
Run result model defined: yes
Promotion policy model defined: yes
Statistical checks defined: yes (11 checks)
Decision logic defined: yes (8 rules)
Owner approval required: yes
Auto-merge blocked: yes
Runtime behavior unchanged: yes
Anti-laundering laws included: yes (12 laws)
Metrics defined: yes (20 metrics)
Relationship to helpers 1–6 preserved: yes
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_sequential_statistical_promotion_gate_helper_design_ready