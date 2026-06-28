# WESLR ARC SYNTHETIC SMOKE V4 ADVERSARIAL COMPLEXITY DESIGN V1

## 1. Executive verdict
`arc_synthetic_smoke_v4_adversarial_complexity_design_ready`

## 2. V3 lesson summary

V3 exposed a real complexity gap:
- V1/V2 baseline: 31/36 = 0.8611 (too friendly/complicit)
- V3 result: 12/36 = 0.3333 (diagnostic groups introduced real pressure)
- Key insight: The current synthetic surface is too complicit — it doesn't test adversarial scenarios

V3 conclusively blocks internal 120 because:
1. Significant unresolved architectural weakness exposed
2. We don't know if scaling would help or mask the problem
3. Adversarial complexity must come before scaling

## 3. Anti-complicity definition

### Complicit synthetic task
A synthetic task that is too easy because:
- One clean obvious rule
- Same family repeated with shallow variation
- Task created around what the solver already handles
- No rival grammar
- No misleading cue
- No negative evidence
- No need to reject a beautiful wrong hypothesis
- No penalty for partial but wrong reasoning

### Adversarial synthetic task
A synthetic task that challenges solver assumptions:
- Multiple plausible grammars fit train evidence
- One beautiful wrong grammar is tempting
- False coordinate cue, old-anchor bait
- Role shift, symmetry trap, object-count trap
- Color-as-noise vs color-as-rule conflict
- Absence/non-change matters
- Train evidence underdetermines the test
- Safe unsupported is sometimes correct
- Relation-first helper should sometimes help and sometimes be blocked

## 4. V4 task composition

**Task count**: 36 tasks (6 groups × 6 tasks) — maintains V1/V2 comparability

| Group | Tasks | Purpose |
|-------|-------|---------|
| rival_grammar_6 | 6 | Multiple grammars fit, must not crown one prematurely |
| beautiful_wrong_rule_6 | 6 | Tempting wrong grammar, solver must reject |
| composed_transform_6 | 6 | Multi-step composition, not single rule |
| negative_evidence_absence_6 | 6 | Non-change/absence is meaningful signal |
| helper_trap_6 | 6 | Helper can help but also be trapped/wrong |
| safe_failure_underdetermined_6 | 6 | Train underdetermines test, safe unsupported correct |

## 5. Adversarial complexity dimensions

V4 must cover these pressure axes:

| Dimension | Description |
|-----------|-------------|
| **Composition depth** | Multi-step transforms, not single-rule |
| **Rival grammar count** | >1 grammar fits train evidence |
| **Misleading cue strength** | Strong false cues that look like rules |
| **Object role instability** | Same object has different roles across contexts |
| **Target uncertainty** | Multiple valid targets, none clearly correct |
| **Action uncertainty** | Multiple valid actions possible |
| **Representation uncertainty** | Different representations possible for same input |
| **Negative evidence** | Absence/non-change signals something |
| **Train/test shift** | Train doesn't uniquely determine test answer |
| **Safe-failure requirement** | Sometimes unsupported is correct |
| **Overconfident wrong risk** | Solver must not assert wrong answer confidently |
| **Helper-trap risk** | Helper eligibility doesn't guarantee improvement |

## 6. Rival grammar and underdetermination policy

V4 must include tasks where:
- **More than one grammar fits train evidence**: Rival grammars must be preserved
- **Solver should NOT crown one grammar** unless train evidence forces it
- **UNKNOWN ENGINE** style pressure may expose divergence but must not become evidence
- **Unresolved rivalry** should produce unsafe/underdetermined when appropriate

This is critical: V4 tests whether WESLR can handle grammar uncertainty without becoming overconfident.

## 7. Helper boundary policy

The relation-first helper remains **unwired** in V4.

V4 may count:
- Helper-eligible tasks
- Helper-trap tasks (where applying helper would make things worse)

V4 must NOT:
- Apply helper
- Let helper transform candidate rules
- Use helper survival as confidence metric

## 8. Metrics design

### Task-level metrics
- generated_task_count: 36
- attempted_task_count: 36
- task_exact/partial/unsupported/failed counts and rates

### Packet-level metrics (diagnostic only)
- packet_total: 72
- packet_exact/partial/unsupported/failed counts and rates

### Group-level metrics
- Per-group task breakdown

### Adversarial-specific metrics
- rival_grammar_count: Number of tasks with >1 grammar
- unresolved_rival_grammar_count/rate: Tasks where grammar remained ambiguous
- beautiful_wrong_rule_trigger_count/rate: Tempting wrong rule cases
- overconfident_wrong_count/rate: Wrong answers with high confidence potential
- safe_unsupported_correctness_count/rate: Correct safe failures
- helper_eligible_task_count: Tasks where helper could apply
- helper_blocked_task_count: Tasks where helper should NOT apply
- helper_trap_task_count: Tasks where applying helper would fail

### Train/test metrics
- train_evidence_underdetermined_count/rate: Train doesn't uniquely determine test

### Frontier metrics
- first_stable_failure_frontier: Tier where first stable failure occurs
- internal_pass_85: Based only on task_exact_rate

## 9. Decision policy after V4

| V4 Result | Next Lane |
|-----------|-----------|
| Low score (adversarial pressure) | SELECT_FRONTIER_AND_REPAIR_ARCHITECTURE |
| Rival grammar/underdetermined weakness exposed | DESIGN_UNKNOWN_ENGINE_REPAIR_MOCK |
| Helper-eligible failures + helper traps | DESIGN_HELPER_ASSISTED_COMPARISON (not wiring) |
| Stays ≥ 0.85 without overconfident wrong | DESIGN_INTERNAL_SYNTHETIC_120_EVAL_V1 |
| Many overconfident wrong answers | PRIORITIZE_LEDGER_REPAIR_OVER_SOLVER_EXPANSION |
| Inconclusive | DESIGN_V5 or REPAIR_TASK_TAXONOMY |

## 10. Recommended next safe local follow-up
`REVIEW_ARC_SYNTHETIC_SMOKE_V4_ADVERSARIAL_COMPLEXITY_DESIGN_V1`

Rationale:
- V3 conclusively blocked internal 120
- Anti-complicity definition clarifies the gap
- 6 adversarial groups target real weaknesses
- Helper remains unwired — counted but not applied
- Metrics cover rival grammar, underdetermination, overconfidence
- Decision policy is clear and bounded

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.