# WESLR ARC SYNTHETIC SMOKE V3 DIAGNOSTIC RUN V1

## 1. Executive verdict
`arc_synthetic_smoke_v3_diagnostic_run_complete`

## 2. Run execution
- **Command**: `run_arc_synthetic_smoke_v3_diagnostic_v1()`
- **Executed**: Yes
- **Module**: `weslr/arc_synthetic_smoke_v3_diagnostic.py`

## 3. Task-level results

| Metric | Count | Rate |
|--------|-------|------|
| Generated tasks | 36 | — |
| Attempted tasks | 36 | — |
| Task exact | 12 | 0.3333333333333333 |
| Task partial | 18 | 0.5 |
| Task unsupported | 6 | 0.16666666666666666 |
| Task failed | 0 | 0.0 |

**Internal pass 85**: **false** — V3 dropped below 0.85 threshold

## 4. Packet-level results (diagnostic only)

| Metric | Count | Rate |
|--------|-------|------|
| Packet total | 72 | — |
| Packet exact | 24 | 0.3333333333333333 |
| Packet partial | 18 | 0.25 |
| Packet unsupported | 30 | 0.4166666666666667 |
| Packet failed | 0 | 0.0 |

## 5. Group-level results

| Group | Exact | Partial | Unsupported | Failed |
|-------|-------|----------|--------------|--------|
| baseline_continuity_6 | 6 | 0 | 0 | 0 |
| coordinate_shift_6 | 6 | 0 | 0 | 0 |
| moved_anchor_6 | 0 | 6 | 0 | 0 |
| distractor_bait_6 | 0 | 6 | 0 | 0 |
| relation_first_candidate_6 | 0 | 6 | 0 | 0 |
| ambiguity_safe_failure_6 | 0 | 0 | 6 | 0 |

## 6. Frontier and diagnostic metrics

- **First stable failure frontier**: Tier 5 (extreme_pressure)
- **Helper eligible task count**: 18
- **Helper applied task count**: 0 (as expected)
- **Helper not applied flag**: true
- **Overconfident wrong count/rate**: 0 / 0.0
- **Safe unsupported correctness count/rate**: 6 / 0.167

## 7. V1/V2 comparison

| Metric | V1/V2 | V3 | Change |
|--------|-------|-----|--------|
| Attempted tasks | 36 | 36 | — |
| Task exact rate | 0.8611 | 0.3333 | **-0.5278** |
| Packet exact rate | 0.8542 | 0.3333 | **-0.5209** |

**V3 dropped significantly** below V1/V2 baseline (0.8611 → 0.3333).

## 8. Analysis

The V3 diagnostic introduced controlled variation that exposed significant solver weaknesses:

- **Baseline continuity** (6/6 exact) and **coordinate shift** (6/6 exact) remained stable
- **Moved anchor** (0/6 exact, 6/6 partial) — anchor identity tracking fails under movement
- **Distractor bait** (0/6 exact, 6/6 partial) — old-coordinate distractor bait succeeds
- **Relation-first candidate** (0/6 exact, 6/6 partial) — helper-eligible cases all partial
- **Ambiguity safe failure** (0/6 exact, 6/6 unsupported) — correctly handles safe failure

The 18 helper-eligible tasks (moved_anchor, distractor_bait, relation_first_candidate) all produced partial results — confirming the helper could potentially improve these if applied later.

## 9. Complexity gap note

V3 remains **controlled/simple** compared with true ARC-style adversarial complexity:
- V3 uses deterministic synthetic tasks with explicit group patterns
- True adversarial complexity would require more diverse/targeted failure modes

**V4 should be adversarial rather than controlled** to stress-test the surface beyond the current diagnostic groups.

## 10. Recommended next safe local follow-up
`REVIEW_ARC_SYNTHETIC_SMOKE_V3_DIAGNOSTIC_RUN_V1`

Rationale:
- V3 run complete and metrics captured
- Significant drop detected (0.86 → 0.33) — real weakness exposed
- Helper-eligible failures confirmed (18 partial results)
- V4 adversarial complexity recommended for deeper stress testing

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.