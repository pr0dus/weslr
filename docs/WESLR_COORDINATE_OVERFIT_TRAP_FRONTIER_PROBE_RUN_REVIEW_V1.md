# WESLR COORDINATE OVERFIT TRAP FRONTIER PROBE RUN REVIEW V1

## 1. Executive verdict
`coordinate_overfit_trap_frontier_probe_run_valid_signal_but_not_stable_frontier`

The run confirms a coordinate-overfit signal (task exact rate drops from baseline 86% to 67%), but does not establish a stable frontier because no tier has ≥2 failures in the 6-task sample.

## 2. Run metric review
| Metric | Value | Interpretation |
|--------|-------|----------------|
| Task exact rate | 4/6 = 0.667 | below 85% baseline — signal confirmed |
| Coordinate-overfit suspected | 2/6 = 0.333 | ~1/3 of cases flag overfit |
| Coordinate bait failure | 1/6 = 0.167 | concrete bait case fails |
| Relation preservation success | 4/6 = 0.667 | ~2/3 cases succeed on relational logic |

The 33% suspected rate and 67% exact rate together confirm that the frozen solver has a genuine coordinate-overfit weakness, but the small sample prevents stable frontier formation.

## 3. Frontier review
- **First stable coordinate-overfit frontier = null**: Expected given only 6 tasks. No tier has ≥2 failures, so the tier-detection algorithm returns null.
- **Hardest coordinate-overfit tier = 2**: Tier 2 (`composed_two_pressure`) contains `moved_anchor` as a partial failure — this is meaningful because Tier 2 is supposed to be easier than Tier 3. The failure indicates the solver cannot handle anchor relocation even at the "composed two-pressure" level.
- **Moved-anchor trustworthiness**: `moved_anchor` appears as both a partial family and the next recommended pressure target. It is trustworthy as the next design focus because:
  1. It is the only partial family in the run.
  2. It directly tests anchor independence, a core relational capability.
  3. It aligns with the design's intent to probe absolute-coordinate bias.

## 4. Sample-size review
6 tasks is **not enough** to declare a stable frontier. However, it **is enough** to justify a focused next lane. The options are:

- **A. Expand coordinate-overfit cases** — would give statistical stability but delays actionable progress.
- **B. Moved-anchor focused probe** — narrows down the signal without expanding the full suite.
- **C. Manual relation-first compiler POC** — leverages the moved-anchor finding directly.

Given that `moved_anchor` is already identified as the pressure target, option **B** is the most efficient next step.

## 5. Architecture implication
Comparing the three paths:

| Option | Pros | Cons |
|--------|------|------|
| A. Expand coordinate-overfit cases | Better statistics | Delays action, may not change the signal |
| B. Design moved-anchor probe | Immediate focus, narrows the signal | Still synthetic-only |
| C. Manual relation-first POC | Directly addresses the finding | Requires manual rule authoring, higher risk |

**Recommendation**: Option **B** — design a moved-anchor focused probe. This builds on the confirmed signal without overcommitting to a full compiler POC.

## 6. Solver freeze and boundary review
- **Solver unchanged**: `solver_behavior_changed = false`, `solver_primitives_added = false`
- **Synthetic-only**: `synthetic_only = true`, `public_arc_used = false`
- **No official claims**: `benchmark_claim_safe = false`
- **No .weslr**: confirmed
- **No external calls**: confirmed

All boundaries preserved.

## 7. Recommended next safe local follow-up
`DESIGN_MOVED_ANCHOR_FRONTIER_PROBE_V1`

Rationale:
- The run confirmed coordinate-overfit signal.
- `moved_anchor` is identified as the next pressure target.
- A narrow moved-anchor probe can confirm whether the finding generalizes before expanding the full coordinate-overfit suite.
- This keeps the probe pipeline moving forward without committing to a full compiler POC.

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.