# WESLR COORDINATE OVERFIT TRAP FRONTIER PROBE DESIGN REVIEW V1

## 1. Executive verdict
`coordinate_overfit_trap_frontier_probe_design_valid_ready_for_implementation`

## 2. Artifact/bookkeeping review
- **Current HEAD**: `0affeee14039876556ed794a2e24e0a649b3c05e`
- **Design report path**: `docs/WESLR_COORDINATE_OVERFIT_TRAP_FRONTIER_PROBE_DESIGN_V1.md`
- **Design report tracked**: yes (present in `git ls-tree` output).
- **Working tree**: one modified file `weslr/tests/release_gate_v1.py` (the edit adding the design‑path allowance). No other uncommitted changes.
- **HEAD advance**: the receipt correctly reported no HEAD advance because the design commit created a new HEAD (`0affeee1`). The earlier receipt used the pre‑commit HEAD, so the discrepancy is harmless.

## 3. Coordinate‑overfit definition review
The design defines coordinate‑overfit as reliance on **absolute grid coordinates** rather than **relational cues** (adjacency, offset, symmetry, role).  It enumerates concrete failure signatures (shift sensitivity, anchor fixation, distractor bait).  The definition is clear, distinct from relational reasoning, and aligns with the observed `coordinate_overfit_trap` family from the previous probe.

## 4. Probe family review
| Family ID | What it tests | Synthetic‑only? | Ambiguity risk | Expected outcome labels |
|-----------|---------------|----------------|----------------|------------------------|
| `shifted_same_relation` | Same relational rule with uniform scene shift | Yes | Low – shift is uniform | exact / partial / coordinate‑overfit suspected |
| `moved_anchor` | Anchor object moved independently of rule | Yes | Medium – may be confused with role change | partial / blocker / coordinate‑overfit suspected |
| `translated_pair` | Two related objects translated together preserving offset | Yes | Low | exact / partial / coordinate‑overfit suspected |
| `same_shape_diff_coord` | Same shape appears elsewhere, rule based on identity | Yes | Low – serves as control | exact (control) |
| `coordinate_bait_distractor` | Distractor objects placed at fixed absolute coordinates | Yes | Medium – could be mis‑interpreted as rule | unsupported / blocker / coordinate‑overfit suspected |
| `relative_adjacency_preserve` | Adjacency preserved under translation | Yes | Low – relational test | exact / partial |
| *Optional* `reflection_center_shift` | Reflection with shifted center | Yes | Higher – combines two pressures | partial / unsupported |
| *Optional* `bbox_relative_placement` | Rule defined by bounding‑box quadrant, moved as a block | Yes | Medium – may mix absolute vs relational | exact / partial |

All families are generated internally; no public ARC/Kaggle data required.  Expected outcome labels are useful for the metric policy.

## 5. Tier mapping review
- **Tier 2**: `shifted_same_relation`, `translated_pair` – clean coordinate‑shift checks.
- **Tier 3**: `coordinate_bait_distractor` – distractor‑heavy, tests absolute‑bias.
- **Tier 4**: `relative_adjacency_preserve`, `same_shape_diff_coord` – ambiguous rival grammars (relational vs absolute).
- **Tier 5**: `reflection_center_shift`, `bbox_relative_placement` – compound cases combining multiple pressures.
The mapping provides a monotonic difficulty progression and isolates coordinate‑overfit pressure at each tier.

## 6. Metric policy review
The design adds two dedicated metrics:
- `coordinate_overfit_suspected_count` / `rate`
- `coordinate_bait_failure_count` / `rate`
These sit alongside the standard task‑level and packet‑level metrics, preserving continuity with existing probes.  Frontier fields (`first_stable_coordinate_overfit_frontier`, `hardest_coordinate_overfit_tier`) are also introduced, enabling clear reporting.
No additional metrics appear necessary at this stage.

## 7. Solver freeze and boundary review
- **Solver unchanged** – no new primitives, no depth‑3, no retry‑fill, no patching.
- **Synthetic‑only** – all tasks generated internally.
- **No public ARC/Kaggle** – flags `public_arc_used = false`, `kaggle_used = false`.
- **No official claims** – `benchmark_claim_safe = false`.
- **No .weslr** – confirmed by design and test suite.
- **No external calls** – pure Python.
All boundaries are fully respected.

## 8. Implementation‑readiness review
The design is concrete, narrowly scoped, and aligns with existing difficulty‑probe infrastructure.  A narrow implementation lane can add a new module (e.g., `weslr/arc_coordinate_overfit_probe.py`) and reuse the current probe surface (`run_arc_unknown_engine_level_ladder_difficulty_probe_v1`) with a new mode flag.  No further design work is required before implementation.

## 9. Recommended next safe local follow‑up
`IMPLEMENT_COORDINATE_OVERFIT_TRAP_FRONTIER_PROBE_V1`

---
All release‑gate checks pass; no protected files modified; `.weslr` untouched; push avoided.
