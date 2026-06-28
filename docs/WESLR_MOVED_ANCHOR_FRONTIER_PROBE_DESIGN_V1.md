# WESLR MOVED ANCHOR FRONTIER PROBE DESIGN V1

## 1. Executive verdict
`moved_anchor_frontier_probe_design_ready`

## 2. Why moved-anchor focus
The coordinate-overfit run identified `moved_anchor` as the single partial family and the next recommended pressure target. This is a natural narrowing of the frontier:

- **Coordinate-overfit** is a broad failure mode (solver relies on absolute coordinates).
- **Moved-anchor** is a specific, actionable instance: the solver can handle uniform shifts (in `shifted_same_relation`) but breaks when an anchor object's identity/role must be tracked across location changes.

A narrow moved-anchor probe can confirm whether the frozen solver truly lacks anchor-role inference.

## 3. Moved-anchor failure mode definition
The failure occurs when the solver **binds to the anchor's old absolute coordinate** instead of **tracking the anchor's identity or role**.

Example scenario:
- **Training**: Object A is the anchor at coordinate (2,2). Object B is positioned relative to A (e.g., "above A").
- **Test**: The anchor A moves to a new coordinate (5,5). Object B remains in the same relative position to A.
- **Correct behavior**: Solver should recognize A as the anchor and predict B's new position based on relative rule.
- **Failure behavior**: Solver predicts based on the old anchor coordinate (2,2), producing an incorrect result.

Key distinction: The solver must track **anchor identity/role**, not anchor **location**.

## 4. Synthetic moved-anchor probe families
| Family ID | Description | Expected Outcome |
|-----------|-------------|------------------|
| `anchor_translated_target_preserved` | Anchor moves, target object maintains relative position | exact (relational reasoning) |
| `anchor_moved_distractor_at_old_coord` | Anchor moves, distractor placed at old anchor coordinate | partial / blocker (distractor bait) |
| `anchor_role_preserved_color_changed` | Anchor object changes color but keeps position/role | exact |
| `anchor_role_preserved_shape_changed` | Anchor object changes shape but keeps position/role | exact |
| `multiple_anchors_one_valid` | Multiple candidate anchors, only one is the true relational anchor | partial / unsupported |
| `anchor_moved_near_boundary` | Anchor moved close to grid boundary, possible edge effects | exact / partial |
| `anchor_moved_offset_constant` | Anchor moves, but offset between anchor and target remains constant | exact (should work if relational) |
| `anchor_absent_ambiguous` | No clear anchor, ambiguous case requiring safe failure | unsupported (safe failure expected) |

## 5. Tier policy
| Tier | Families | Rationale |
|------|----------|-----------|
| **2** | `anchor_translated_target_preserved`, `anchor_moved_offset_constant` | Clean moved-anchor checks without distractors |
| **3** | `anchor_moved_distractor_at_old_coord`, `anchor_moved_near_boundary` | Old-coordinate bait and edge effects |
| **4** | `anchor_role_preserved_color_changed`, `anchor_role_preserved_shape_changed`, `multiple_anchors_one_valid` | Anchor identity vs. appearance ambiguities |
| **5** | `anchor_absent_ambiguous` | Safe-failure frontier case |

## 6. Metrics
### Standard metrics
- Attempted task count
- Task exact / partial / unsupported / failed counts and rates
- Packet exact / partial / unsupported / failed counts and rates
- Frontier fields (hardest exact/partial tier, first stable frontier, etc.)

### Moved-anchor specific metrics
- `moved_anchor_failure_count` / `rate` — cases where anchor moved and solver failed
- `old_anchor_coordinate_bait_count` / `rate` — failures due to old anchor coordinate bait
- `anchor_role_preservation_success_count` / `rate` — cases where relational anchor reasoning succeeded
- `ambiguous_anchor_safe_failure_count` / `rate` — cases where ambiguous anchor caused safe unsupported failure

### Frontier fields
- `first_stable_moved_anchor_frontier` — first tier with ≥2 failures
- `hardest_moved_anchor_tier` — highest tier with failures
- `next_recommended_pressure_family` — next target after moved-anchor

## 7. Relation-first connection
The moved-anchor probe directly feeds the **relation-first compiler POC** concept from the run review:

| Form | Description |
|------|-------------|
| **Coordinate form** | `anchor_at(old_x, old_y) → target_offset` |
| **Relational form** | `anchor_role(anchor_id) → target_offset` |
| **Structural outcome** | full rewrite (if relational works), partial rewrite (if mixed), irreducible (if coordinate-only), unsafe (if overconfident) |

A successful moved-anchor probe (low failure rate) would indicate the solver can handle relational anchor reasoning. A high failure rate would confirm the need for a manual relation-first compiler.

## 8. Boundary review
- **Solver unchanged**: No new primitives, no depth-3, no patching.
- **Synthetic-only**: All tasks generated internally; `public_arc_used = false`.
- **No official claims**: `benchmark_claim_safe = false`.
- **No .weslr**: Confirmed.
- **No external calls**: Pure Python execution.
- **Protected files**: No modifications.

## 9. Recommended next safe local follow-up
`REVIEW_MOVED_ANCHOR_FRONTIER_PROBE_DESIGN_V1`

---
All release-gate checks pass; protected files unchanged; `.weslr` untouched; push avoided.