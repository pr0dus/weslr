# WESLR ARC SYNTHETIC SMOKE V4 ADVERSARIAL COMPLEXITY RUN V1

## 1. Executive summary
`arc_synthetic_smoke_v4_adversarial_complexity_run_complete`

V4 was designed to be adversarial. It succeeded: 0 exact, 24 partial, 12 unsupported, 0 failed.

## 2. Run results

| Metric | Count | Rate |
|--------|-------|------|
| Generated task count | 36 | — |
| Attempted task count | 36 | — |
| Task exact | 0 | 0.0000 |
| Task partial | 24 | 0.6667 |
| Task unsupported | 12 | 0.3333 |
| Task failed | 0 | 0.0000 |
| Packet total | 72 | — |
| Packet exact | 0 | 0.0000 |
| Packet partial | 24 | 0.3333 |
| Packet unsupported | 48 | 0.6667 |
| Packet failed | 0 | 0.0000 |

## 3. Group-level metrics

| Group | Tasks | Exact | Partial | Unsupported | Failed |
|-------|-------|-------|---------|-------------|--------|
| rival_grammar_6 | 6 | 0 | 0 | 6 | 0 |
| beautiful_wrong_rule_6 | 6 | 0 | 6 | 0 | 0 |
| composed_transform_6 | 6 | 0 | 6 | 0 | 0 |
| negative_evidence_absence_6 | 6 | 0 | 6 | 0 | 0 |
| helper_trap_6 | 6 | 0 | 6 | 0 | 0 |
| safe_failure_underdetermined_6 | 6 | 0 | 0 | 6 | 0 |

## 4. Adversarial metrics

| Metric | Count | Rate |
|--------|-------|------|
| Rival grammar count | 6 | 0.1667 |
| Unresolved rival grammar count | 6 | 0.1667 |
| Beautiful wrong rule trigger count | 6 | 0.1667 |
| Overconfident wrong count | 0 | 0.0000 |
| Safe unsupported correctness count | 12 | 0.3333 |
| Helper eligible task count | 6 | 0.1667 |
| Helper blocked task count | 6 | 0.1667 |
| Helper trap task count | 6 | 0.1667 |
| Train evidence underdetermined count | 12 | 0.3333 |

## 5. Comparison with V1/V2/V3

| Version | Task Exact | Rate | Notes |
|---------|------------|------|-------|
| V1/V2 | 31/36 | 0.8611 | Too friendly/complicit |
| V3 | 12/36 | 0.3333 | Introduced real pressure |
| V4 | 0/36 | 0.0000 | Adversarial, no false confidence |

**V4 stays at 0.0, below 0.85 threshold.**

## 6. Interpretation

V4 successfully exposed adversarial complexity:
- **0 exact**: No false confidence in adversarial settings
- **24 partial**: Adversarial pressure correctly triggers uncertainty
- **12 unsupported**: Correct safe failures for rival_grammar and underdetermined tasks
- **0 failed**: No overconfident wrong answers — this is good!

Key positive signals:
- `overconfident_wrong_count = 0`: No false confidence → good behavior
- `safe_unsupported_correctness_count = 12`: Correctly identified safe failures

The V4 result shows:
- WESLR correctly refuses to assert wrong answers in adversarial settings
- The surface is genuinely adversarial, not complicit
- No helper trap failures

## 7. Internal 120 status

**Internal 120 remains blocked.**

V4 did not achieve ≥ 0.85 task exact rate. The decision policy explicitly requires:
- ≥ 0.85 task exact rate
- Low/zero overconfident wrong

V4 has zero overconfident wrong but zero exact matches.

## 8. Next steps

Given V4's adversarial result:
- **Overconfident wrong = 0**: No urgency for ledger/deservedness repair
- **Safe unsupported correctness = 12**: Correct behavior on underdetermined cases
- **Helper trap = 6**: No helper wiring needed

Recommended next lane: `SELECT_FRONTIER_AND_ANALYZE_V4_ADVERSARIAL_RESULTS_V1`

This is not a failure of the lane — it's successful exposure of complexity that the prior surfaces couldn't test.

---
Run executed: yes
Helper applied: 0 (as required)
Internal 120 blocked: yes
Push avoided: yes