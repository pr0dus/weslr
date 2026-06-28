# WESLR MOVED ANCHOR FRONTIER PROBE RUN REVIEW V1

## 1. Executive verdict
`moved_anchor_frontier_probe_run_valid_ready_for_relation_first_manual_poc`

## 2. Run metric review
| Metric | Value | Assessment |
|--------|-------|-------------|
| Task exact rate | 4/8 = 0.5 | Strong signal — well below 85% baseline |
| Task partial rate | 3/8 = 0.375 | Meaningful partial breakdown |
| Task unsupported rate | 1/8 = 0.125 | Safe failure expected for ambiguous case |
| Moved-anchor failure rate | 4/8 = 0.5 | **Core signal confirmed** |
| Old-anchor coordinate bait rate | 1/8 = 0.125 | Concrete bait failure confirmed |
| Anchor-role preservation success rate | 4/8 = 0.5 | ~50% relational reasoning works |
| Ambiguous-anchor safe failure rate | 1/8 = 0.125 | Safe failure correctly identified |

**Conclusion**: The 50% moved-anchor failure rate is a strong, actionable signal. The 12.5% coordinate bait confirms a specific failure sub-mode.

## 3. Frontier review
- **First stable moved-anchor frontier**: Tier 3 — contains two partial failures (`anchor_moved_distractor_at_old_coord`, `anchor_moved_near_boundary`). This is trustworthy because Tier 3 represents adversarial/distractor-heavy pressure, which aligns with the moved-anchor failure mode.
- **Hardest moved-anchor tier**: 5 — contains the `anchor_absent_ambiguous` case, which is explicitly designed as a safe-failure boundary. This is expected behavior, not a failure of the probe.
- **Assessment**: Tier 3 is the meaningful frontier; Tier 5 is the safe-failure boundary.

## 4. Relation-first POC review
- **relation_first_poc_candidate = true** is confirmed by:
  - 50% moved-anchor failure rate (strong signal)
  - 12.5% old anchor coordinate bait (specific sub-mode)
  - 50% anchor-role preservation success (half the cases work relationally, confirming the solver can do it when not confused)
- The metadata fields `coordinate_form_example` and `relational_form_example` provide the exact input/output forms needed for a manual POC design.
- **This run justifies designing a manual relation-first compiler POC.**

The probe has done its job: it identified a specific, actionable failure mode (anchor role vs. anchor coordinate) and confirmed that the failure rate is high enough to warrant manual intervention design.

## 5. Boundary review
- **Solver unchanged**: `solver_behavior_changed = false`, `solver_primitives_added = false`
- **Synthetic-only**: All tasks internal; `public_arc_used = false`
- **No official claims**: `benchmark_claim_safe = false`
- **No .weslr**: confirmed
- **No external calls**: pure Python execution
- **Protected files**: No modifications

All boundaries preserved.

## 6. Recommended next safe local follow-up
`DESIGN_RELATION_FIRST_COMPILER_MANUAL_POC_V1`

Rationale:
- The moved-anchor run confirmed a strong, specific frontier signal.
- Tier 3 provides a stable first frontier.
- The relation-first metadata (coordinate_form vs. relational_form) is ready for manual POC design.
- No case expansion needed — the signal is already actionable.
- This does not patch the solver — it designs a manual relational rewrite strategy that can be evaluated separately.

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.