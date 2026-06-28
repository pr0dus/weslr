# WESLR ARC SEQUENTIAL STATISTICAL PROMOTION GATE HELPER FUNCTIONAL RUN V1

## 1. Executive summary
`arc_sequential_statistical_promotion_gate_helper_functional_run_complete`

Functional run of helper family 7/8 passed all 10 test cases.

## 2. Functional cases run

| Case | Description | Status |
|------|-------------|--------|
| 1 | insufficient_sample_blocks_promotion | PASS |
| 2 | same_suite_improvement_quarantined | PASS |
| 3 | overconfident_wrong_blocks_promotion | PASS |
| 4 | safe_unsupported_damage_blocks_promotion | PASS |
| 5 | holdout_failure_blocks_promotion | PASS |
| 6 | regression_blocks_promotion | PASS |
| 7 | all_gates_pass_promotion_candidate_owner_required | PASS |
| 8 | auto_merge_attempt_fails_closed | PASS |
| 9 | public_claim_attempt_fails_closed | PASS |
| 10 | runtime_wiring_attempt_fails_closed | PASS |

## 3. Detailed results

### Case 1: insufficient_sample_blocks_promotion
- **Input**: Sample size = 5 (< min_task_count)
- **Expected**: insufficient_evidence
- **Result**: overall_status = insufficient_evidence ✓

### Case 2: same_suite_improvement_quarantined
- **Input**: Same variant family for baseline, candidate, holdout
- **Expected**: promotion_quarantined
- **Result**: overall_status = promotion_quarantined ✓

### Case 3: overconfident_wrong_blocks_promotion
- **Input**: exact improves but overconfident_wrong_count rises from 0 to 5
- **Expected**: overconfident_wrong_increased
- **Result**: overall_status = overconfident_wrong_increased ✓

### Case 4: safe_unsupported_damage_blocks_promotion
- **Input**: exact improves but safe_unsupported_count drops from 10 to 1
- **Expected**: safe_unsupported_damaged
- **Result**: overall_status = safe_unsupported_damaged ✓

### Case 5: holdout_failure_blocks_promotion
- **Input**: Candidate improves baseline but holdout fails (5 vs baseline 10)
- **Expected**: holdout_failed
- **Result**: overall_status = holdout_failed ✓

### Case 6: regression_blocks_promotion
- **Input**: Candidate improves but regression_suite has failed_count=10
- **Expected**: regression_detected
- **Result**: overall_status = regression_detected ✓

### Case 7: all_gates_pass_promotion_candidate_owner_required
- **Input**: All gates pass - improvement, holdout, fresh variants, no safety regression
- **Expected**: promotion_candidate + owner_approval_required
- **Result**: overall_status = promotion_candidate, owner_approval_required = True, auto_merge_allowed = False, runtime_wiring_allowed = False, public_claim_allowed = False ✓

### Case 8: auto_merge_attempt_fails_closed
- **Input**: promotion_policy={'auto_merge_allowed': True}
- **Expected**: ValueError raised
- **Result**: ValueError: auto_merge_allowed must be False ✓

### Case 9: public_claim_attempt_fails_closed
- **Input**: promotion_policy={'requires_no_public_claim': False}
- **Expected**: ValueError raised
- **Result**: ValueError: requires_no_public_claim must be True ✓

### Case 10: runtime_wiring_attempt_fails_closed
- **Input**: Default input check
- **Expected**: runtime_wiring_allowed = False
- **Result**: runtime_wiring_allowed = False, helper_changes_runtime_behavior = False ✓

## 4. Summary metrics

| Metric | Value |
|--------|-------|
| Functional cases run | 10 |
| Functional cases passed | 10 |
| Functional cases failed | 0 |
| Baseline task exact rate | 0.1 |
| Candidate task exact rate | 0.2 |
| Task exact rate delta | +0.1 |
| Holdout task exact rate | 0.18 |
| Holdout delta | +0.08 |
| Owner approval required | Yes |
| Auto-merge blocked | Yes |
| Runtime behavior unchanged | Yes |
| Public/official ARC claims forbidden | Yes |
| Anti-laundering laws preserved | Yes |
| Helper roadmap count | 7/8 |

## 5. Boundary checks

- **Improvement alone not enough**: Yes ✓
- **Holdout required**: Yes ✓
- **Overconfident wrong increase blocks**: Yes ✓
- **Safe unsupported damage blocks**: Yes ✓
- **Same-suite-only quarantines**: Yes ✓
- **Insufficient sample blocks**: Yes ✓
- **Regression blocks**: Yes ✓
- **All gates pass = promotion candidate**: Yes ✓
- **Promotion candidate requires owner approval**: Yes ✓
- **Auto-merge remains blocked**: Yes ✓
- **Runtime behavior unchanged**: Yes ✓
- **Public/official claims forbidden**: Yes ✓

---
Functional run executed: yes
Functional cases run: 10
Functional cases passed: 10
Functional cases failed: 0
Statuses observed: insufficient_evidence, promotion_quarantined, overconfident_wrong_increased, safe_unsupported_damaged, holdout_failed, regression_detected, promotion_candidate
Owner approval required: yes
Auto-merge blocked: yes
Runtime behavior unchanged: yes
Public/official ARC claims forbidden: yes
Anti-laundering laws preserved: yes
Helper roadmap count: 7/8
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_sequential_statistical_promotion_gate_helper_functional_run_v1_complete