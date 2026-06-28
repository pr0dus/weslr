# WESLR ARC SOLVER FRONTIER SELECTION FROM V4 V1

## 1. Executive verdict
`arc_solver_frontier_selection_from_v4_complete`

## 2. V4 result summary

| Metric | Count | Rate |
|--------|-------|------|
| Attempted tasks | 36 | — |
| Task exact | 0 | 0.0000 |
| Task partial | 24 | 0.6667 |
| Task unsupported | 12 | 0.3333 |
| Overconfident wrong | 0 | 0.0000 |
| Safe unsupported correctness | 12 | 0.3333 |
| Rival grammar unresolved | 6 | 0.1667 |
| Helper trap | 6 | 0.1667 |
| Helper applied | 0 | 0.0000 |

Key insight: V4 shows 0 overconfident wrong + 12 correct safe unsupported = safe-failure discipline is working. The 0 exact is NOT a failure — it's the intended adversarial exposure.

## 3. Coordinate-overfit comparison

V4 failures are NOT the same as coordinate-overfit probe failures.

| Aspect | Coordinate-Overfit | V4 |
|--------|-------------------|-----|
| Primary failure | Coordinate pattern overfitting | Rival grammar / underdetermination |
| Overconfident wrong pattern | High | 0 |
| Resolution approach | Coordinate probing | Grammar/ledger handling |

V4 exposes a different failure mode: the solver doesn't know how to handle multiple grammars that fit train evidence equally well. This is a **rival grammar / deservedness frontier**, not a coordinate-overfit frontier.

## 4. Moved-anchor comparison

V4 failures are NOT primarily moved-anchor failures.

| Aspect | Moved-Anchor | V4 |
|--------|-------------|-----|
| Primary failure | Anchor pattern movement | Multi-grammar resolution |
| Anchor-related groups | 1/6 | 0/6 |
| Rival grammar groups | 2/6 | 6/6 |

V4's adversarial groups (rival_grammar, beautiful_wrong, helper_trap, safe_failure) are orthogonal to moved-anchor. The moved-anchor probe tested a specific pattern; V4 tests grammar/uncertainty handling.

## 5. Relation-first helper relevance

The relation-first helper is NOT the solution to V4 failures.

| Helper Aspect | Status |
|--------------|--------|
| Helper eligible | 6 (helper_trap_6 group) |
| Helper helpful | 0 |
| Helper trap | 6 |
| Helper applied | 0 (correct) |

V4 shows that helper eligibility doesn't mean helper helpfulness. The helper_trap_6 group proves that automatic helper promotion would fail. Helper should remain unwired.

## 6. V4 group classification table

| Group | Primary Failure | Secondary | Coord-Overfit | Moved-Anchor | Rival Grammar | Deservedness | Helper | Safe Unsupported | Solver Improvement |
|-------|----------------|-----------|---------------|--------------|---------------|--------------|--------|------------------|---------------------|
| rival_grammar_6 | Rival grammar resolution | None | No | No | Yes | Yes | No | Correct | Unsafe |
| beautiful_wrong_rule_6 | Hypothesis rejection | Beautiful wrong | No | No | Yes | No | No | N/A | Unsafe |
| composed_transform_6 | Multi-step composition | Micro-theory | No | No | No | No | No | N/A | Candidate |
| negative_evidence_absence_6 | Absence reasoning | Negative evidence | No | No | No | No | No | N/A | Candidate |
| helper_trap_6 | Helper trap avoidance | Eligibility trap | No | No | No | No | Yes | N/A | Unsafe |
| safe_failure_underdetermined_6 | Underdetermination | Safe failure | No | No | Yes | Yes | No | Correct | Unsafe |

**Key insight**: Most V4 groups are unsafe for direct solver improvement because:
1. Rival grammar requires grammar resolution (not simple patch)
2. Beautiful wrong requires philosophical rejection (not algorithmic)
3. Helper trap requires understanding eligibility vs helpfulness
4. Safe failure underdetermination requires ledger/deservedness

Only `composed_transform_6` and `negative_evidence_absence_6` are candidate frontiers for improvement, but they're not the primary weakness.

## 7. Primary frontier selected
**`rival_grammar_ledger_deservedness`**

Rationale:
- V4's most significant new failure mode is rival grammar / underdetermination
- This is different from coordinate-overfit and moved-anchor probes
- Overconfident wrong = 0 means the ledger/safe-failure layer works — but it may be too conservative
- The next improvement should focus on how the system handles grammar uncertainty

This is NOT about making the solver more confident. It's about understanding when multiple grammars are genuinely equivalent vs when one should be preferred based on parsimony or other criteria.

## 8. Recommended improvement type
**B. Ledger/deservedness repair design**

Rationale:
- The V4 shows safe-failure discipline works (0 overconfident wrong)
- But it may be too conservative — we can't tell if rival grammars are genuinely equivalent
- A ledger/deservedness repair would help track grammar confidence without asserting wrong answers
- This is different from solver improvement: it's about improving the confidence/uncertainty layer

## 9. Auto-improvement / mathematical promotion note

**Not yet. Future design only.**

If auto-improvement is ever considered:
- Must be pre-gated mathematically (not heuristics)
- Must use holdout variants for validation
- Must include regression gates
- Must include overconfident-wrong gates
- Must preserve safe-unsupported correctness
- Must include rollback/quarantine for failed promotions

**Current status**: No auto-improvement, no autonomous self-modification, no auto-merge. This is a design document only.

## 10. Internal 120 readiness
**Internal 120 remains blocked.**

V4 showed:
- 0 overconfident wrong (good!)
- But 0 exact matches

Internal 120 requires both ≥0.85 exact rate AND low overconfident wrong. Neither V3 nor V4 has achieved this. The frontier selection is about designing a controlled improvement — not starting internal 120.

## 11. Recommended next safe local follow-up
`DESIGN_ARC_LEDGER_DESERVEDNESS_REPAIR_FROM_V4_V1`

Rationale:
- Primary frontier selected: rival_grammar_ledger_deservedness
- V4 shows safe-failure works but may need calibration
- Ledger/deservedness repair is the correct next step
- This is design/report only, not implementation
- Will present proposal for operator review before any changes

---
V4 vs coordinate-overfit: Different failure modes (rival grammar vs coordinate pattern)
Primary frontier: rival_grammar_ledger_deservedness
Recommended improvement type: Ledger/deservedness repair design
Auto-improvement note included: yes (future design only)
Internal 120 blocked: yes
Helper remains unwired: yes
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_solver_frontier_selection_from_v4_complete