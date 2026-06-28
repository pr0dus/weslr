# WESLR ARC SYNTHETIC SMOKE V3 DIAGNOSTIC DESIGN V1

## 1. Executive verdict
`arc_synthetic_smoke_v3_diagnostic_design_ready`

## 2. Purpose and context

The V1/V2 smoke runs produced stable identical metrics (31/36 = 0.8611). This V3 diagnostic is designed to stress-test that stable surface by introducing controlled variation while maintaining comparability.

**V3 Goals:**
- Preserve V1/V2 comparability (same 36-task structure)
- Introduce diagnostic variation (harder task families)
- Keep small enough to run before internal 120
- Separate task-level from packet-level metrics
- Use task_exact_rate as primary gate
- Treat packet metrics as diagnostic only

## 3. V3 composition (36 tasks total)

| Group | Tasks | Purpose | Expected Pressure |
|-------|-------|---------|-------------------|
| baseline_continuity_6 | 6 | Core ARC tasks that V1/V2 solved correctly | Should remain exact |
| coordinate_shift_6 | 6 | Coordinate binding with translation | Tests coordinate sensitivity |
| moved_anchor_6 | 6 | Anchor moved after rule formation | Tests anchor identity tracking |
| distractor_bait_6 | 6 | Distractor at old anchor coordinate | Tests bait resistance |
| relation_first_candidate_6 | 6 | Tasks that helper could rewrite | Identifies helper-eligible failures |
| ambiguity_safe_failure_6 | 6 | Ambiguous/absent anchor cases | Tests safe failure boundaries |

## 4. Group-level design

### baseline_continuity_6
- **Purpose**: Verify core stability — tasks similar to V1/V2 baseline
- **Expected behavior**: ~5-6 exact, 0-1 partial, 0 unsupported
- **Helper eligible**: No — baseline continuity

### coordinate_shift_6
- **Purpose**: Test coordinate binding under translation
- **Expected behavior**: ~4-5 exact, 1-2 partial, 0 unsupported
- **Helper eligible**: No — coordinate behavior, not relational

### moved_anchor_6
- **Purpose**: Test anchor identity tracking across movement
- **Expected behavior**: ~3-4 exact, 2-3 partial, 0-1 unsupported
- **Helper eligible**: Yes — relation-first helper could rewrite coordinate to relational
- **Note**: This is key for helper-eligible failure counting

### distractor_bait_6
- **Purpose**: Test resistance to old-coordinate distractor bait
- **Expected behavior**: ~3-4 exact, 2-3 partial, 0-1 unsupported
- **Helper eligible**: Yes — helper could ignore distractor
- **Note**: Another key group for helper eligibility

### relation_first_candidate_6
- **Purpose**: Explicitly designed for relation-first rewrite potential
- **Expected behavior**: ~3-4 exact, 1-2 partial, 1-2 unsupported
- **Helper eligible**: Yes — primary helper-eligible group

### ambiguity_safe_failure_6
- **Purpose**: Test safe-failure boundaries with ambiguous anchors
- **Expected behavior**: ~2-3 exact, 1-2 partial, 2-3 unsupported
- **Helper eligible**: No — no valid relational form exists
- **Note**: Unsupported here is acceptable/correct

## 5. Required V3 metrics

### Task-level metrics
- generated_task_count: 36
- attempted_task_count: 36
- task_exact_count: ?
- task_exact_rate: ?
- task_partial_count: ?
- task_partial_rate: ?
- task_unsupported_count: ?
- task_unsupported_rate: ?
- task_failed_count: ?
- task_failed_rate: ?

### Packet-level metrics (diagnostic only)
- packet_total: 72 (36 × 2)
- packet_exact_count: ?
- packet_exact_rate: ?
- packet_partial_count: ?
- packet_partial_rate: ?
- packet_unsupported_count: ?
- packet_unsupported_rate: ?
- packet_failed_count: ?
- packet_failed_rate: ?

### Group-level metrics
- For each group: task_exact_count, task_partial_count, task_unsupported_count

### Frontier fields
- first_stable_failure_frontier: ?
- helper_eligible_task_count: ?
- helper_not_applied_flag: true (V3 does NOT apply helper yet)
- overconfident_wrong_count/rate: ?
- safe_unsupported_correctness_count/rate: ?

### Threshold gate
- internal_threshold: 0.85
- threshold_basis: task_exact_rate
- internal_pass_85: true/false

## 6. Comparison policy

V3 compares against:
- **V1/V2 baseline**: 31/36 = 0.8611
- **Difficulty probe**: 4/8 = 0.50
- **Coordinate-overfit probe**: 9 tests passed
- **Moved-anchor probe**: 4/8 = 0.50, 4/8 failure = 0.50

**Do NOT mix their scores into V3 metrics.** V3 is standalone.

## 7. Decision policy after V3 run

| V3 Result | Next Lane |
|-----------|-----------|
| V3 stays ≥ 0.85 (stable) | DESIGN_INTERNAL_SYNTHETIC_120_EVAL_V1 |
| V3 drops < 0.85 (real weakness exposed) | REVIEW_V3_DIAGNOSTIC_RUN_AND_SELECT_FRONTIER |
| V3 reveals helper-eligible failures | DESIGN_HELPER_ASSISTED_COMPARISON_LATER (not immediate wiring) |
| V3 inconclusive | DESIGN_ARC_SYNTHETIC_SMOKE_V4_DIAGNOSTIC |

## 8. Important V3 constraints

- **Do NOT apply relation-first helper** — helper code exists but is NOT wired in V3
- **Helper eligibility** is counted but NOT applied
- **Do NOT modify solver behavior**
- **Do NOT create new solver primitives**
- **Do NOT make public ARC/Kaggle claims**
- **Synthetic-only**: all tasks generated internally
- **No .weslr**: confirmed

## 9. Boundary review
- **Solver unchanged**: No behavior changes
- **Synthetic-only**: All tasks internal
- **No public data**: No ARC/Kaggle
- **No official claims**: No benchmark scoring
- **No helper integration**: Helper exists but not wired
- **Protected files**: No modifications

## 10. Recommended next safe local follow-up
`REVIEW_ARC_SYNTHETIC_SMOKE_V3_DIAGNOSTIC_DESIGN_V1`

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.