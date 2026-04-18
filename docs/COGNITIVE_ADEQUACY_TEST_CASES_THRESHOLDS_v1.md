# COGNITIVE_ADEQUACY_TEST_CASES_THRESHOLDS_v1

**Scope:** Doctrine-first mapping of adequacy scenarios to concrete test cases and thresholds. No implementation.

## SECTION 1 — TEST CASE MAPPING
- Repetitive shallow proposals:
  - Case: Same task class/source_loop emits ≥N similar proposals with minimal deltas in content/actionability.
- Repeated rejects/ignores:
  - Case: For a task class, reject/ignore rate exceeds R over W proposals.
- Repeated low-confidence streaks:
  - Case: Confidence < C_low across S consecutive proposals in a loop/task class.
- Same-fix loops:
  - Case: Same fix text/category proposed ≥N times without acceptance/status change.
- No improvement after multiple cycles:
  - Case: Confidence and/or acceptance rate fails to improve over T windows (e.g., rolling windows of size W).
- Evidence-to-action failure:
  - Case: Proposals cite evidence but lack actionable steps ≥F times within a window.

## SECTION 2 — THRESHOLD RULES (INITIAL DOCTRINE VALUES)
- Repetition count (N): 3 consecutive similar proposals.
- Reject/ignore ratio (R): ≥60% rejects/ignores over window W=5 proposals for the task class.
- Low-confidence streak (C_low, S): confidence < 0.4 for S=3 consecutive proposals in the loop/task class.
- Same-fix loops (N): same fix/category appears ≥3 times without an accepted/applied status.
- No improvement (T, W): no measurable increase in confidence or acceptance over T=2 consecutive windows, each window W=4 proposals.
- Evidence-to-action failure (F): ≥2 occurrences in a window W=4 proposals where evidence is cited but no actionable steps are present.
- Minimum sample floor before triggering: require at least 3 proposals in scope for any trigger.

## SECTION 3 — EXPECTED DECISIONS (PER CASE)
- Adequacy score: should decrease when thresholds hit; remain neutral if under thresholds/guards.
- Inadequacy reason: scenario-specific (repetition, low usefulness, low confidence, same-fix, no improvement, evidence-to-action failure).
- Cognitive-improvement proposal: emit when threshold crossed and no false-positive guard applies.
- False-positive guard: suppress emission when guard conditions are met (see below).

## SECTION 4 — FALSE-POSITIVE THRESHOLDS
- Operator-requested repetition: explicit flag suppresses triggers for repetition/same-fix when present.
- Low sample count: if total proposals in scope < 3, do not trigger.
- Exploratory budget / improving trend: if within exploratory window (first 3 proposals) and confidence is improving (+0.05 or more per step), do not trigger low-confidence or no-improvement cases.

## SECTION 5 — NEXT STEP
- Build test fixtures and harness cases using these thresholds; seek approval before implementation.
