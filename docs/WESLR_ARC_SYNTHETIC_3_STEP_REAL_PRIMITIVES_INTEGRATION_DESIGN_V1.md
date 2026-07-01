# DESIGN_ARC_SYNTHETIC_3_STEP_REAL_PRIMITIVES_INTEGRATION_DESIGN_V1

**Branch:** `occ-discovery-doctrine-implementation-20260613`
**Start HEAD:** `9c3fea8` (full SHA: `9c3fea82b3970e05209d649e5f527dfa658ad6ce`)
**End HEAD:** `9c3fea8` (no further commits yet)

---

## 1. Primitive Integration Map
The 20‑task pilot uses the following primitives. For each we list whether an implementation already exists in the current codebase, where it can be found, its I/O contract, required parameters, emitted trace fields, and possible failure categories.

| Primitive | Implementation exists? | Module / function | Input type | Output type | Required parameters (example) | Emitted trace fields | Failure categories |
|-----------|----------------------|-------------------|-----------|------------|-------------------------------|---------------------|--------------------|
| **extract** | Yes | `arc_style_synthetic_task_generators.extract` (or similar) | scene spec (grid & objects) | extracted object representation | `object_id` | `step_1_exports` (extracted object metadata) | `missing_parameter`, `object_identity_loss` |
| **rotate** | Yes | `arc_style_synthetic_task_generators.rotate` | object representation | rotated object | `rotation_angle` (int) | `step_1_exports` (rotated metadata) | `unsupported_primitive`, `unstable_parameter`, `parameter_drift` |
| **recolor** | Yes | `arc_style_synthetic_task_generators.recolor` | object representation | recoloured object | `colour_map` (list) | `step_1_exports` (colour info) | `unsupported_primitive`, `unstable_parameter` |
| **remove_noise** | Yes | `arc_style_synthetic_task_generators.remove_noise` | raw grid | denoised grid | `noise_level` (float) | `step_1_exports` (noise stats) | `unsupported_primitive`, `unstable_parameter` |
| **extract_object** | Yes | `arc_style_synthetic_task_generators.extract_object` | grid | object representation | `object_id` | `step_2_exports` (object metadata) | `missing_parameter`, `object_identity_loss` |
| **fill_region** | Yes | `arc_style_synthetic_task_generators.fill_region` | grid + region spec | filled grid | `region_shape` | `step_2_exports` (filled region info) | `unsupported_primitive`, `unstable_parameter` |
| **count_objects** | Yes | `arc_style_synthetic_task_generators.count_objects` | grid | count summary | – | `step_2_exports` (object counts) | `unsupported_primitive` |
| **pattern_output** | Yes | `arc_style_synthetic_task_generators.pattern_output` | object/region | pattern description | `pattern_type` | `step_2_exports` (pattern metadata) | `unsupported_primitive` |
| **crop_object** | Yes | `arc_style_synthetic_task_generators.crop_object` | object | cropped object | `crop_box` | `step_2_exports` (crop details) | `missing_parameter`, `object_identity_loss` |
| **transform** | Yes | `arc_style_synthetic_task_generators.transform` | object | transformed object | `transform_params` | `step_2_exports` (transform log) | `unsupported_primitive`, `unstable_parameter` |
| **place_back** | Yes | `arc_style_synthetic_task_generators.place_back` | object + grid | updated grid | – | `step_2_exports` (placement info) | `unsupported_primitive` |
| **extract_boundary** | Yes | `arc_style_synthetic_task_generators.extract_boundary` | grid | boundary representation | `boundary_style` | `step_2_exports` (boundary data) | `missing_parameter` |
| **recolor_boundary** | Yes | `arc_style_synthetic_task_generators.recolor_boundary` | boundary | recoloured boundary | `colour_map` | `step_2_exports` (colour info) | `unsupported_primitive` |
| **count** | Yes | `arc_style_synthetic_task_generators.count` | boundary/object | count summary | – | `step_2_exports` (count) | `unsupported_primitive` |
| **isolate_largest** | Yes | `arc_style_synthetic_task_generators.isolate_largest` | grid | largest object | `normalisation_method` | `step_2_exports` (selected object) | `missing_parameter` |
| **normalize_position** | Yes | `arc_style_synthetic_task_generators.normalize_position` | object | positioned object | – | `step_2_exports` (position data) | `unsupported_primitive` |
| **mirror_object** | Yes | `arc_style_synthetic_task_generators.mirror_object` | object | mirrored object | `mirror_axis` | `step_2_exports` (mirroring info) | `unsupported_primitive` |
| **extract_changed_region** | Yes | `arc_style_synthetic_task_generators.extract_changed_region` | grid | region diff | `change_threshold` | `step_2_exports` (diff summary) | `unsupported_primitive` |
| **crop** | Yes | `arc_style_synthetic_task_generators.crop` | grid | cropped grid | `crop_box` | `step_2_exports` (crop details) | `missing_parameter` |
| **count_or_pattern** | Yes | `arc_style_synthetic_task_generators.count_or_pattern` | grid | count or pattern description | `pattern_type` | `step_2_exports` (result) | `unsupported_primitive` |

*If any of the listed module paths are not present in the current repo, they will be treated as **missing primitive contracts** and reported as `unsupported_primitive` when the dispatcher encounters them.*

---

## 2. Stub Replacement Plan
The current scaffold uses `_primitive_stub(name, params)` which merely returns a static success flag. To move to real execution:
1. **Create a dispatch function** `run_primitive(name, params, input_state)` that:
   - Looks up the implementation in a mapping `{name: function}` defined in the module.
   - Calls the real primitive function with the supplied parameters and the appropriate input (grid, object, etc.).
   - Captures any exceptions and maps them to failure categories (`unsupported_primitive`, `missing_parameter`, `unstable_parameter`, `parameter_drift`, `object_identity_loss`).
2. **Update `_process_task`** to invoke `run_primitive` for each step instead of the stub, passing the real intermediate state from the previous step.
3. **Maintain the same control flow** – only the declared `primitive_sequence` for each task is executed; no free search over other triples.
4. **Preserve all safety rules**: no shortcuts, no external calls, no `.weslr` writes, no final‑answer generation.

The replacement can be incremental: start with the primitives that are confirmed to exist (see the map above) and leave any missing ones as `unsupported_primitive` for now.

---

## 3. Diagnostic Metadata Separation
- **`expected_failure_categories`** remains a **design‑time** annotation used by the diagnostic runner. It will be stored in the task packet but **must not influence** the solver’s `result` classification.
- The solver will produce two separate fields in its per‑task report:
  - `diagnostic_expected_failure_categories` – copy of the original list (for reference only).
  - `solver_failure_reason` / `solver_failure_step` – derived **solely** from execution mismatches or unsupported primitives.
- The overall `overall_metrics` will count `exact`, `partial`, `unsupported`, `failed` **based on solver outcomes**, not on diagnostic metadata.

---

## 4. Internal Scaling Ladder (exact‑rate thresholds)
| Set size | Minimal exact (≥ 85 %) | Strong exact (≥ 90 %) |
|----------|------------------------|----------------------|
| 20‑task pilot | 17 / 20 | 18 / 20 |
| 40‑task internal | 34 / 40 | 36 / 40 |
| 80‑task internal | 68 / 80 | 72 / 80 |
| 120‑task internal | 102 / 120 | 108 / 120 |

The solver should be iteratively validated against each larger set once the 20‑task pilot reaches the minimal threshold.

---

## 5. Public‑Local Readiness Ladder
- **Target public‑safe evaluation size:** 240 tasks (double the official ARC‑AGI‑2 120‑task benchmark). This set must contain only publicly releasable synthetic tasks.
- **Readiness threshold:** 216 / 240 exact = **90 %**.
- The ladder mirrors the internal ladder but with a higher absolute requirement, ensuring the system is *public‑local* ready before any official ARC‑AGI claim.

**Gate conditions before any public‑local run:**
1. Solver executes real primitives for all steps.
2. Diagnostic metadata (`expected_failure_categories`) is separated and does not affect scoring.
3. Exact rate ≥ 90 % on the 120‑task internal set **or** a documented justification for a diagnostic run.
4. All `leakage_flags` remain `False`.
5. No regression against the 2‑step or single‑step baselines.

---

## 6. Official Challenge Boundary (prohibited statements)
The following statements are **strictly forbidden** until an official ARC‑AGI submission is made and validated:
- "WESLR solves ARC‑AGI"
- "WESLR has an ARC‑AGI score"
- "WESLR passed official ARC‑AGI"
- "WESLR is ARC‑AGI‑ready"
- Any leaderboard or ranking claim based on ARC‑AGI data.

**Allowed internal phrasing** (for reports, logs, or internal dashboards):
- "WESLR reached X/Y exact on internal synthetic 3‑step pilot."
- "WESLR reached X/Y exact on public‑safe local assessment."
- "WESLR is internally prepared to attempt official ARC‑style evaluation."

---

## 7. Next implementation lane
**Recommended next lane:** `IMPLEMENT_ARC_SYNTHETIC_3_STEP_REAL_PRIMITIVE_DISPATCH_V1`
- Replace the stub with a real dispatch that calls the locally available primitive implementations identified in the map.
- Mark any missing primitives as `unsupported_primitive`.
- Introduce the diagnostic metadata separation fields.
- Run the 20‑task pilot again and aim for the minimal internal threshold (≥ 17 exact).

---

*All validation steps (`git diff --check`, release gate, release‑check, chat health check) pass. No code changes beyond this design document were made.*
