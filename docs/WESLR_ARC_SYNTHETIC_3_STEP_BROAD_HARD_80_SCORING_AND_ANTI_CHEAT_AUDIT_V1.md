# ARC Synthetic 3‑Step – Broad Hard‑80 Scoring and Anti‑Cheat Audit (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `AUDIT_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_SCORING_AND_ANTI_CHEAT_V1`
**Start HEAD**: `8e0caaea`

---

## Executive Summary

The Broad‑Hard‑80 pilot reported 80/80 exact (100%). **This audit finds that the 80/80 result is a structural dispatch pass, not a semantic exact solving result.** The scoring code classifies a task as `exact` when all 3 primitives return `supported=True`, with no comparison to any independent reference output. Multiple anti‑cheat checks confirm the scoring is too weak to distinguish correct from incorrect solving.

---

## 1. Scoring Semantics Audit

**Scoring code location**: `weslr/arc_synthetic_3_step_real_dispatch.py`, function `_process_task()`

**Scoring logic**:
```
for each step 1, 2, 3:
    supported, grid, trace = run_primitive(prim_name, grid, params)
    if not supported:
        return "unsupported"
return "exact"
```

**Finding**: `exact` means **(B) all primitives supported / no error**. It does **not** mean (A) final output equals independent reference output. There is no reference output, no output comparison, and no output validation of any kind.

**Classification**: The 80/80 result is a **structural execution pass**, not a semantic exact pass.

---

## 2. Independent Reference‑Output Audit

| Check | Finding |
|-------|---------|
| Independent oracle exists? | **No** ❌ |
| Expected outputs generated separately from solver? | **No** ❌ |
| Scorer and solver share same execution path? | **Yes** — both use `run_primitive()` ❌ |

**Self‑grading risk: YES.** The scorer and solver are the same code path. There is no separation between "solving" and "checking."

---

## 3. Solver Input‑Boundary Audit

`_process_task()` accesses only:
- `task["primitive_sequence"]` — used for dispatch ✅
- `task["allowed_dynamic_parameters"]` — used for params ✅
- `task["leakage_flags"]` — used for assertion only ✅

It does **not** access:
- `task_id`, `family_id`, `difficulty`, `hardness_axes`, `shortcut_defeated`, `expected_failure_categories`, `expected_trace_requirements`, `expected_test_output`

**Metadata leakage risk: NO.** The solver does not shortcut on metadata.

---

## 4. Metadata Shuffle Audit

| Check | Result |
|-------|--------|
| Task IDs randomized | Results unchanged ✅ |
| Family labels shuffled | No effect (solver ignores them) ✅ |
| Difficulty labels shuffled | No effect (solver ignores them) ✅ |
| Hardness axes removed | No effect (solver ignores them) ✅ |
| Shortcut strings removed | No effect (solver ignores them) ✅ |

**Metadata leakage risk: NO.** Results are invariant to metadata shuffling because the solver does not use metadata.

---

## 5. Primitive‑Order Negative Controls

Tested 10 order‑sensitive tasks (axes 1+5 active) with reversed and swapped orders:

| Perturbation | Tasks | Still exact |
|-------------|-------|-------------|
| Reversed order | 10 | 10/10 ❌ |
| Swapped step 1↔3 | 10 | 10/10 ❌ |

**All perturbed orders still score exact.** The scoring cannot distinguish primitive order — it only checks whether each primitive is individually supported. This confirms scoring is structural, not semantic.

**Primitive‑order sensitivity: NOT DETECTED by scoring ❌**

---

## 6. No‑Op Shadow Controls

Replaced each step (1, 2, 3) with `pattern_output` (identity/no‑op) for 12 tasks:

| Check | Result |
|-------|--------|
| 36 no‑op replacements (12 tasks × 3 steps) | 36/36 still exact ❌ |

**No‑op overcredit risk: YES.** Replacing any step with a no‑op still scores exact. The scoring cannot detect whether a primitive actually contributes to solving.

---

## 7. Alias‑Wrapper Audit

| Alias | Maps to | Grid changed? | Pass‑through? |
|-------|---------|--------------|---------------|
| `remove_noise` | `remove_background_noise` adapter | Yes | No ✅ |
| `extract_object` | `extract_largest_object` adapter | Yes | No ✅ |
| `crop_object` | `crop_to_non_background_bbox` adapter | No | **Yes** ❌ |
| `recolor_boundary` | wraps `recolor` adapter | No | **Yes** ❌ |
| `count` | `count_objects` (metadata only) | No | By design (count primitive) |
| `count_or_pattern` | `count_objects` (metadata only) | No | By design (count primitive) |
| `extract_changed_region` | bbox of largest, grid unchanged | No | By design (metadata primitive) |
| `fill_region` | fill grid with 1 | Yes | No ✅ |

**Alias‑wrapper risk: YES.** `crop_object` and `recolor_boundary` are pass‑through (grid unchanged on test input). While `count`/`count_or_pattern`/`extract_changed_region` are metadata‑only by design, `crop_object` and `recolor_boundary` should change the grid and do not.

---

## 8. Intermediate‑Grid Trace Audit

Audited 12 tasks (3 known, 3 hybrid, 3 mutation, 3 unknown, 6 adversarial).

**Finding**: All 12 tasks start with an empty grid `[]`. The first primitive defaults empty grids to `[[1]]` (a 1×1 grid with value 1). All subsequent steps operate on this trivial 1×1 grid, producing `[[1]]` at every step. The only exception is `fill_region`, which creates a 3×3 grid of 1s.

| Task ID | Family | Diff. | Step 1 | Step 2 | Step 3 | All same grid? |
|---------|--------|-------|--------|--------|--------|----------------|
| BH80_001 | F001 | medium | `[[1]]` | `[[1]]` | `[[1]]` | Yes ⚠️ |
| BH80_012 | F006 | hard | `[[1]]` | `[[1]]` | `[[1]]` | Yes ⚠️ |
| BH80_017 | F003 | adv | `[[1,1,1],[1,1,1],[1,1,1]]` | same | same | Yes ⚠️ |
| BH80_023 | BH‑A | adv | `[[1]]` | `[[1]]` | `[[1]]` | Yes ⚠️ |
| BH80_025 | BH‑A | adv | `[[1]]` | `[[1]]` | `[[1]]` | Yes ⚠️ |
| BH80_026 | BH‑A | adv | `[[1]]` | `[[1]]` | `[[1]]` | Yes ⚠️ |
| BH80_048 | BH‑C | adv | `[[1]]` | `[[1]]` | `[[1]]` | Yes ⚠️ |
| BH80_049 | BH‑C | adv | `[[1]]` | `[[1]]` | `[[1]]` | Yes ⚠️ |
| BH80_050 | BH‑C | adv | `[[1,1,1],[1,1,1],[1,1,1]]` | same | same | Yes ⚠️ |
| BH80_061 | BH‑E | adv | `[[1]]` | `[[1]]` | `[[1]]` | Yes ⚠️ |
| BH80_069 | BH‑F | adv | `[[1]]` | `[[1]]` | `[[1]]` | Yes ⚠️ |
| BH80_080 | BH‑G | adv | `[[1]]` | `[[1]]` | `[[1]]` | Yes ⚠️ |

**All 12 audited tasks produce unchanged grids across all 3 steps.** The primitives operate on a trivial default grid, not on the scene_spec's described objects, positions, or colors.

**Root cause**: The solver starts with `grid = []` (empty). `run_primitive()` defaults empty grids to `[[1]]`. The `scene_spec` in the task packet (which describes objects, colors, positions) is **never read by the solver**. The primitives operate on a synthetic default grid, not the task's actual scene.

---

## 9. Output Diversity Audit

| Check | Result |
|-------|--------|
| Total final outputs | 80 |
| Unique final outputs | **2** ❌ |
| Output values | `[[1]]` (78 tasks) and `[[1,1,1],[1,1,1],[1,1,1]]` (2 tasks with `fill_region`) |
| Unique output dimensions | 2: `(1,1)` and `(3,3)` |

**Output diversity: SEVERELY INSUFFICIENT ❌.** 78 of 80 tasks produce `[[1]]`. The primitives produce no meaningful differentiation because they operate on a trivial default grid.

---

## 10. Sentinel Task Audit

| Sentinel | Expected | Actual | Pass? |
|----------|----------|--------|-------|
| Unsupported primitive (`fake_primitive`) | unsupported | unsupported | ✅ |
| Wrong‑order (`recolor → crop → extract`) | should differ from correct order | exact (same as correct) | ❌ confirms weakness |
| All‑noop (`pattern_output × 3`) | should fail or differ | **exact** | ❌ overcredit |
| Identity‑chain (`pattern_output → transform → count_or_pattern`) | should fail or differ | **exact** | ❌ overcredit |

**Sentinel results confirm scoring is invalid for semantic evaluation.**

---

## 11. Perturbation Audit Design

A follow‑up blind perturbation suite should test:

| Perturbation | What it tests |
|-------------|---------------|
| Color permutation | Whether solver depends on specific color values |
| Object translation | Whether solver depends on absolute positions |
| Canvas resizing | Whether solver depends on specific grid dimensions |
| Distractor insertion/removal | Whether solver is robust to scene modifications |
| Task ID randomization | Already tested — no effect (confirmed) |
| Family/difficulty removal | Already tested — no effect (confirmed) |

This should become a separate lane: `DESIGN_ARC_SYNTHETIC_3_STEP_BH80_PERTURBATION_SUITE_V1`

---

## 12. Summary of Findings

| Audit | Risk | Finding |
|-------|------|---------|
| 1. Scoring semantics | **Critical** | `exact` = all primitives supported, NOT output equality |
| 2. Self‑grading | **Critical** | Scorer and solver are the same code path |
| 3. Input boundary | No risk | Solver does not use metadata shortcuts |
| 4. Metadata shuffle | No risk | Results invariant to metadata changes |
| 5. Primitive‑order controls | **Critical** | All perturbed orders still score exact |
| 6. No‑op controls | **Critical** | All no‑op replacements still score exact |
| 7. Alias wrappers | **High** | `crop_object` and `recolor_boundary` are pass‑through |
| 8. Trace audit | **Critical** | All tasks operate on trivial `[[1]]` default grid, scene_spec never read |
| 9. Output diversity | **Critical** | Only 2 unique outputs across 80 tasks |
| 10. Sentinel tasks | **Critical** | No‑op and identity‑chain sentinels score exact |

---

## Reclassification

The pilot result of 80/80 exact must be reclassified as:

**80/80 structural dispatch support (not semantic exact solving)**

The 80/80 figure proves that all 80 task primitive sequences are individually mappable to dispatch wrappers. It does **not** prove that the solver produces correct outputs for any task.

---

## Verdict

**`structural_pass_only_semantic_scoring_missing`**

The Broad‑Hard‑80 pilot demonstrates that the dispatch layer can execute all 80 primitive sequences without errors. However:
- No independent oracle exists
- No output comparison occurs
- The solver operates on a trivial default grid (`[[1]]`), not the task's scene_spec
- Primitive order cannot be detected
- No‑op replacements cannot be detected
- Output diversity is effectively zero (2 unique outputs)

**The 80/80 result must not be reported as semantic solving.**

---

## Recommended Next Lanes

1. **`DESIGN_ARC_SYNTHETIC_3_STEP_BH80_INDEPENDENT_ORACLE_V1`** — design an independent oracle that generates expected outputs separately from the solver path, using the scene_spec to produce reference grids.

2. **`DESIGN_ARC_SYNTHETIC_3_STEP_BH80_REAL_SCENE_INPUT_V1`** — wire the scene_spec into the solver input so primitives operate on actual task scenes, not `[[1]]` defaults.

3. **`DESIGN_ARC_SYNTHETIC_3_STEP_BH80_PERTURBATION_SUITE_V1`** — design the blind perturbation suite (color, translation, canvas, distractor).

4. **`REPAIR_ARC_SYNTHETIC_3_STEP_ALIAS_PASS_THROUGH_V1`** — repair `crop_object` and `recolor_boundary` aliases that are pass‑through on default grids.

---

## Receipt

| Field | Value |
|-------|-------|
| **Start HEAD** | `8e0caaea` |
| **End HEAD** | `8e0caaea` (audit‑only, no code changes) |
| **Commit** | none (audit report only) |
| **Scoring semantics audited** | yes ✅ |
| **Exact means output equality** | **no** ❌ |
| **Independent oracle exists** | **no** ❌ |
| **Self‑grading risk** | **yes** ❌ |
| **Metadata leakage risk** | no ✅ |
| **No‑op shadow controls passed** | **no** — 36/36 still exact ❌ |
| **Primitive‑order negative controls passed** | **no** — 20/20 still exact ❌ |
| **Alias‑wrapper audit passed** | **no** — `crop_object` and `recolor_boundary` pass‑through ❌ |
| **Trace audit completed** | yes — all 12 tasks operate on `[[1]]` default ⚠️ |
| **Output diversity audit completed** | yes — only 2 unique outputs ❌ |
| **Verdict** | `structural_pass_only_semantic_scoring_missing` |
| **Validation** | PASS ✅ (no code changes) |
| **Push avoided** | yes ✅ |
| **Recommended next lane** | `DESIGN_ARC_SYNTHETIC_3_STEP_BH80_INDEPENDENT_ORACLE_V1` |