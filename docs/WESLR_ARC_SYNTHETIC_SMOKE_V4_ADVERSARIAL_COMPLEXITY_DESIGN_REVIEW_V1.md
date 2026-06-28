# WESLR ARC SYNTHETIC SMOKE V4 ADVERSARIAL COMPLEXITY DESIGN REVIEW V1

## 1. Executive verdict
`arc_synthetic_smoke_v4_adversarial_complexity_design_valid_ready_for_implementation`

## 2. V3 lesson review
**Assessment: Correctly incorporated.**

V4 responds to the V3 complexity gap:
- V3 drop from 0.86 → 0.33 confirmed the prior surface was too complicit
- Internal 120 remains blocked until V4 proves the surface can handle adversarial pressure
- V4 is explicitly designed as adversarial to test what V1/V2/V3 couldn't

## 3. Anti-complicity review
**Assessment: Strong definitions.**

The complicit/adversarial definitions are clear and actionable:
- **Complicit**: One obvious rule, no rival grammars, no misleading cues, no need to reject wrong hypotheses
- **Adversarial**: Multiple grammars possible, beautiful wrong grammar tempting, false cues, train underdetermines test

This correctly defines the gap V4 must fill.

## 4. V4 group composition review
**Assessment: Meaningful and balanced.**

| Group | Purpose | Adversarial Pressure |
|-------|---------|---------------------|
| rival_grammar_6 | Multiple grammars fit train | Must not crown prematurely |
| beautiful_wrong_rule_6 | Tempting wrong grammar | Must reject when evidence doesn't support |
| composed_transform_6 | Multi-step composition | Not single-rule pattern matching |
| negative_evidence_absence_6 | Absence matters | Non-change signals something |
| helper_trap_6 | Helper eligibility trap | Applying helper would fail |
| safe_failure_underdetermined_6 | Train underdetermines test | Unsupported is correct |

All 6 groups target real solver weaknesses identified in V3.

## 5. Rival grammar and underdetermination review
**Assessment: Correctly bounded.**

- More than one grammar fits → keep rival grammars unresolved
- Solver should NOT crown one grammar unless train evidence eliminates alternatives
- UNKNOWN ENGINE pressure may expose divergence but must not become evidence
- Unresolved rivalry → safe/unsupported when appropriate

This is the critical guardrail against overconfidence.

## 6. Helper boundary review
**Assessment: Correctly bounded.**

- Helper remains unwired: helper_applied = 0, helper_not_applied_flag = true
- Helper trap metrics: distinguishes helper-eligible-from-helper-helpful
- Helper blocked metrics: prevents automatic helper promotion based on eligibility

No hidden confidence accumulation via helper.

## 7. Metrics review
**Assessment: Sufficient.**

All required metrics present:
- Task-level: exact, partial, unsupported, failed ✓
- Packet-level (diagnostic only) ✓
- Group-level ✓
- Adversarial: rival_grammar_count, unresolved_rival_grammar_count, beautiful_wrong_rule_trigger_count ✓
- Overconfident wrong count/rate ✓
- Safe unsupported correctness count/rate ✓
- Helper eligible/blocked/trap counts ✓
- Train evidence underdetermined count/rate ✓
- First stable failure frontier ✓
- Internal pass 85 (task_exact_rate only) ✓

## 8. Internal 120 readiness review
**Assessment: Blocked for now.**

The design explicitly keeps internal 120 blocked:
- V4 must show ≥ 0.85 WITHOUT overconfident wrong before 120 becomes allowed
- Decision policy maps different V4 outcomes to different next lanes
- No path to 120 until V4 proves the surface is genuinely strong

## 9. Solver freeze and benchmark boundary review
**Assessment: All boundaries preserved.**

- No solver changes: Confirmed
- No public ARC/Kaggle: Confirmed
- No official claims: Confirmed
- No .weslr: Confirmed
- No external calls: Confirmed

## 10. Recommended next safe local follow-up
`IMPLEMENT_ARC_SYNTHETIC_SMOKE_V4_ADVERSARIAL_COMPLEXITY_V1`

Rationale:
- Design is valid and responds correctly to V3 complexity gap
- Anti-complicity definitions are strong
- 6 adversarial groups are meaningful and balanced
- Rival grammar policy prevents premature grammar crowning
- Helper remains unwired with trap metrics
- Metrics are sufficient to detect overconfidence, underdetermination, and helper traps
- Internal 120 is correctly blocked until V4 proves the surface

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.