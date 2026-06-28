# WESLR COORDINATE OVERFIT TRAP FRONTIER PROBE DESIGN V1

## 1. Executive verdict
`coordinate_overfit_trap_frontier_probe_design_ready`

## 2. Why this probe is needed
The previous difficulty‑probe run identified **Tier 3 (adversarial‑distractor‑heavy)** as the first stable failure frontier and highlighted the **"coordinate_overfit_trap"** family as the next recommended pressure target.  The frozen solver appears to rely on absolute‑position cues in several test families, which is a classic over‑fit failure mode for ARC‑style relational reasoning.  A dedicated probe that isolates absolute‑coordinate bias will tell us whether the solver truly lacks relational inference or simply needs more varied pressure.

## 3. Coordinate‑overfit definition
*Coordinate‑overfit* occurs when the solver makes decisions based on **fixed absolute grid coordinates** (row = X, column = Y) instead of **relative relationships** such as adjacency, distance, symmetry, or shared object properties.  Evidence of this failure mode includes:
- Correct predictions only when the test object remains at the exact location seen in the training examples.
- Systematic errors when the same relational pattern is presented with a uniform shift, translation, or mirroring of all objects.
- Sensitivity to “distractor” objects placed at specific absolute cells that were absent in training examples.

The probe aims to expose these symptoms without altering the frozen solver or the baseline synthetic generator.

## 4. Probe families (synthetic only)
Each family consists of a small, well‑defined set of generated ARC‑style tasks.  All families share the same relational rule; only the **coordinate configuration** varies.

| Family ID | Description | What is Tested |
|-----------|-------------|----------------|
| `shifted_same_relation` | Training examples show a relation (e.g., “object A is above object B”). Test example shifts the whole scene by a uniform offset (dx, dy). | Solver’s ability to apply the rule under absolute‑position shift. |
| `moved_anchor` | One anchor object (reference point) is moved to a new absolute location while the relational rule remains unchanged for other objects. | Whether the solver binds the rule to the anchor’s absolute cell instead of its role. |
| `translated_pair` | Two objects forming a pair are translated together while preserving their relative offset. | Sensitivity to absolute coordinates vs. relative offset. |
| `same_shape_diff_coord` | Same shape appears in a different absolute cell; relational rule involves shape identity, not position. | Distinguishes shape‑based reasoning from coordinate‑based reasoning. |
| `coordinate_bait_distractor` | Distractor objects placed at fixed “bait” coordinates that appear in training but are irrelevant to the rule. Test moves the target objects while keeping distractors fixed. | Checks if solver incorrectly keys on distractor absolute positions. |
| `relative_adjacency_preserve` | Training examples encode adjacency (objects touch). Test translates the whole configuration but preserves adjacency. | Verifies relational adjacency reasoning independent of absolute cell numbers. |
| *Optional* `reflection_center_shift` | Objects are reflected about a center that itself is shifted. | Tests interaction of reflection with absolute‑center bias. |
| *Optional* `bbox_relative_placement` | Rule defined by objects being in the same bounding‑box quadrant. Test moves the entire bounding box. | Checks relational quadrant reasoning vs. absolute quadrant numbers. |

## 5. Tier mapping (difficulty progression)
- **Tier 2 – Clean coordinate‑shift checks**: `shifted_same_relation`, `translated_pair`.
- **Tier 3 – Distractor‑heavy / bait cases**: `coordinate_bait_distractor`.
- **Tier 4 – Ambiguous rival grammar**: `relative_adjacency_preserve`, `same_shape_diff_coord` (introduces competing relational interpretations).
- **Tier 5 – Compound frontier cases**: `reflection_center_shift`, `bbox_relative_placement` (combine multiple pressures and potential over‑fit traps).

## 6. Expected solver outcomes per family
| Family | Expected exact | Expected partial | Expected unsupported | Expected blocker | Coordinate‑overfit suspected |
|--------|----------------|----------------|----------------------|------------------|------------------------------|
| `shifted_same_relation` | exact (if relational) or partial if solver over‑fits | – | – | – | **yes** when exact drops and partial appears. |
| `moved_anchor` | partial (anchor absolute) or unsupported | – | – | **yes** when fails completely. |
| `translated_pair` | exact or partial | – | – | – | **yes** when exact rate falls sharply. |
| `same_shape_diff_coord` | exact (shape‑based) or partial | – | – | – | **no** – serves as control. |
| `coordinate_bait_distractor` | unsupported or blocker | – | – | **yes** – if distractor coordinates dominate. |
| `relative_adjacency_preserve` | exact or partial | – | – | – | **no** – tests relational reasoning. |
| `reflection_center_shift` | unsupported or blocker | – | – | **yes** |
| `bbox_relative_placement` | partial or unsupported | – | – | **yes** |

## 7. Metric policy
The probe will be measured with the same baseline metric schema plus two new fields specific to coordinate‑overfit detection:
- `coordinate_overfit_suspected_count` / `rate`
- `coordinate_bait_failure_count` / `rate`
All other task‑level and packet‑level metrics remain unchanged (exact, partial, unsupported, failed, rates).
Additional frontier fields:
- `first_stable_coordinate_overfit_frontier`
- `hardest_coordinate_overfit_tier`
- `next_recommended_pressure_family` (still `coordinate_overfit_trap` unless a deeper frontier emerges).

## 8. Interpretation policy
- **Exact ≥ 85 %** – coordinate‑overfit not yet exposed; increase difficulty (add harder families). 
- **70 % ≤ Exact < 85 %** – useful frontier zone; record as first over‑fit signal. 
- **40 % ≤ Exact < 70 %** – strong coordinate‑overfit exposure; focus design on Tier 4‑5 families. 
- **Exact < 40 %** – probe may be too hard or dominated by unsupported cases; inspect `coordinate_overfit_suspected_rate` and adjust family balance.
- **Coordinate‑overfit suspected > 0** – flag for future design; do **not** patch solver.

## 9. Solver freeze and boundary review
- **Solver unchanged** – no new primitives, no depth‑3, no retry‑fill, no patching.
- **Synthetic‑only** – all tasks generated internally; `public_arc_used = false`, `kaggle_used = false`.
- **No .weslr writes** – pure in‑memory dictionaries.
- **No external calls** – deterministic Python execution.
- **No official claims** – `benchmark_claim_safe = false`.
All boundaries are fully respected.

## 10. Future implementation plan (next lane)
A narrow implementation lane should:
1. Add the above families as concrete synthetic cases in a new module (e.g., `weslr/arc_coordinate_overfit_probe.py`).
2. Re‑use the existing `run_arc_unknown_engine_level_ladder_difficulty_probe_v1` surface to report the new metrics under a separate mode (`coordinate_overfit_probe_v1`).
3. Ensure baseline reference remains untouched.
4. Run tests analogous to `test_arc_unknown_engine_level_ladder_difficulty_probe_v1.py` to validate metric collection.

## 11. Recommended next safe local follow‑up
`REVIEW_COORDINATE_OVERFIT_TRAP_FRONTIER_PROBE_DESIGN_V1`

---
All release‑gate checks pass; no protected files touched; `.weslr` untouched; push avoided.
