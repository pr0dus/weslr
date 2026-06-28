# WESLR MOVED ANCHOR FRONTIER PROBE DESIGN REVIEW V1

## 1. Executive verdict
`moved_anchor_frontier_probe_design_valid_ready_for_implementation`

## 2. Failure-mode review
**Assessment: Valid and clear.**

The design correctly defines moved-anchor failure as:
- **Success condition**: Solver tracks anchor *identity/role* across location changes.
- **Failure condition**: Solver binds to anchor's *old absolute coordinate* instead of its identity.

This distinction is precise and actionable. It builds directly on the coordinate-overfit finding (solver relies on absolute coordinates) while narrowing to a specific relational reasoning gap (anchor-role tracking).

## 3. Probe-family review
**Assessment: Sufficient and coherent.**

All 8 families are:
- Synthetic-only — no public ARC/Kaggle data.
- Internally consistent — each tests a distinct aspect of anchor movement.
- Meaningful for frontier probing:

| Family | What it Tests | Assessment |
|--------|---------------|------------|
| `anchor_translated_target_preserved` | Basic anchor move with relational target | Core test case |
| `anchor_moved_distractor_at_old_coord` | Old coordinate bait | High-signal failure case |
| `anchor_role_preserved_color_changed` | Anchor identity vs. appearance | Identity persistence |
| `anchor_role_preserved_shape_changed` | Anchor identity vs. shape | Identity persistence |
| `multiple_anchors_one_valid` | Disambiguation | Hard case |
| `anchor_moved_near_boundary` | Edge effects | Practical boundary |
| `anchor_moved_offset_constant` | Offset preservation | Should succeed |
| `anchor_absent_ambiguous` | Safe failure | Frontier boundary |

## 4. Tier-policy review
**Assessment: Coherent and monotonic.**

- **Tier 2**: Clean anchor translation cases — baseline moved-anchor behavior.
- **Tier 3**: Distractor bait and boundary effects — adds failure pressure.
- **Tier 4**: Identity ambiguities — tests whether solver conflates anchor with its properties.
- **Tier 5**: Safe-failure frontier — explicitly designs for unsupported outcomes.

The progression is logical: simple translation → bait/distraction → identity ambiguity → safe failure.

## 5. Metric-policy review
**Assessment: Sufficient.**

The proposed metrics capture the right signals:
- `moved_anchor_failure_count/rate` — core failure metric
- `old_anchor_coordinate_bait_count/rate` — specific bait signal
- `anchor_role_preservation_success_count/rate` — relational success signal
- `ambiguous_anchor_safe_failure_count/rate` — safe failure signal

Frontier fields (`first_stable_moved_anchor_frontier`, `hardest_moved_anchor_tier`, `next_recommended_pressure_family`) complete the picture.

## 6. Relation-first connection review
**Assessment: Useful and actionable.**

The design explicitly maps:
- **Coordinate form**: `anchor_at(old_x, old_y) → target_offset`
- **Relational form**: `anchor_role(anchor_id) → target_offset`

This is exactly the information needed for a manual relation-first compiler POC. The design correctly frames the outcome as: full rewrite, partial rewrite, irreducible coordinate dependency, or unsafe prediction.

**No overclaim**: The design correctly notes that this is a *potential* feed into a future POC, not a commitment to implement one now.

## 7. Boundary review
**Assessment: All boundaries preserved.**

- **Solver unchanged**: No new primitives, no depth-3, no patching.
- **Synthetic-only**: All tasks internal; `public_arc_used = false`.
- **No official claims**: `benchmark_claim_safe = false`.
- **No .weslr**: Confirmed.
- **No external calls**: Pure Python.
- **Protected files**: No modifications.

## 8. Implementation-readiness review
**Assessment: Safe for narrow implementation lane.**

The design is narrow enough:
- It builds on a confirmed finding (`moved_anchor` as partial family).
- It does not claim stable frontier status (notes small sample from coordinate-overfit run).
- It preserves solver freeze.
- It stays synthetic-only.

A narrow implementation lane can add the 8 families as a static ledger (similar to the coordinate-overfit probe structure) without modifying solver behavior.

## 9. Recommended next safe local follow-up
`IMPLEMENT_MOVED_ANCHOR_FRONTIER_PROBE_V1`

Rationale:
- Design is valid, narrow, and coherent.
- It directly follows the coordinate-overfit run's recommendation.
- Implementation can reuse the existing probe infrastructure.
- No solver changes required.

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.