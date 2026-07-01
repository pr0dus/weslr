# ARC Synthetic 3‑Step – BH80 Independent Oracle Design (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_ARC_SYNTHETIC_3_STEP_BH80_INDEPENDENT_ORACLE_V1`
**Start HEAD**: `dfedcc60`

---

## 1. Semantic Solving Definition

A task is **semantically solved** if and only if:

1. A real input grid is materialized from the task's `scene_spec`.
2. The solver receives the input grid and the declared primitive sequence.
3. The solver executes the 3‑step pipeline on the input grid, producing a final output grid.
4. An independent oracle — using its own reference primitive semantics, not the solver's dispatch path — produces a reference output grid from the same input grid and primitive sequence.
5. The scorer compares the solver's final grid to the oracle's final grid.
6. **`exact`** = solver final grid equals oracle final grid (element‑wise, dimension‑wise).
7. **`structural_pass`** = all primitives were supported (the old definition) — reported separately, never conflated with `exact`.

### Why the structural 80/80 is insufficient

The anti‑cheat audit (`structural_pass_only_semantic_scoring_missing`) found:
- `exact` meant "all primitives supported," not output equality.
- No independent oracle existed.
- Scorer and solver shared the same `run_primitive()` code path.
- `scene_spec` was never read — the solver operated on `[[1]]` defaults.
- No‑op replacements still scored exact (36/36).
- Primitive‑order negative controls still scored exact (20/20).
- Output diversity was 2 unique outputs across 80 tasks.
- Alias wrappers `crop_object` and `recolor_boundary` were pass‑through.

The 80/80 figure proves dispatch support. It does not prove solving.

---

## 2. Oracle / Solver / Scorer Separation

### Architecture

```
scene_spec ──→ [Materializer] ──→ input_grid
                                        │
                          ┌─────────────┼─────────────┐
                          ▼                           ▼
                    [Solver]                    [Oracle]
                  (run_primitive              (reference_primitives
                   dispatch path)              own semantics)
                          │                           │
                          ▼                           ▼
                    solver_grid              oracle_grid
                          │                           │
                          └─────────┬─────────────────┘
                                    ▼
                              [Scorer]
                          (grid equality check)
                                    │
                                    ▼
                            exact / partial /
                          unsupported / failed
```

### Separation rules

| Component | May call | May not call |
|-----------|----------|---------------|
| **Solver** | `run_primitive()` (dispatch path) | Oracle, scorer, scene materializer |
| **Oracle** | `reference_primitive()` (own path) | `run_primitive()`, solver, scorer |
| **Scorer** | Grid comparison only | Solver, oracle, `run_primitive()`, `reference_primitive()` |
| **Materializer** | Scene spec → grid only | Solver, oracle, scorer |

The oracle and solver must not share any execution code. The oracle has its own independent implementation of every primitive's semantics.

---

## 3. Scene Materialization

### 3.1 Current problem

The current `_make_scene_spec()` produces a trivial 10×10 grid with a single red object at `[0,0]`. The solver never reads it and defaults to `[[1]]`.

### 3.2 Materialization design

The materializer reads `scene_spec` and produces a concrete integer grid:

```python
def materialize_scene(scene_spec: dict) -> list[list[int]]:
    """Convert scene_spec into a concrete integer grid."""
```

### 3.3 Scene spec schema (enriched)

```json
{
  "grid_size": [W, H],
  "background": 0,
  "initial_objects": [
    {
      "object_id": "obj_001",
      "type": "rectangle|l_shape|cross|donut|disconnected",
      "color": 1,
      "position": [row, col],
      "size": [h, w],
      "holes": false,
      "disconnected_parts": false
    }
  ],
  "distractors": [
    {
      "object_id": "distractor_001",
      "type": "rectangle",
      "color": 1,
      "position": [row, col],
      "size": [h, w]
    }
  ],
  "noise_pixels": 0
}
```

### 3.4 Materialization rules

1. **Grid initialization**: Create a `grid_size[1] × grid_size[0]` grid filled with `background` value (default 0).
2. **Object placement**: For each object in `initial_objects`, draw its shape at its position using its color.
   - `rectangle`: fill `size` rows × `size` cols with color
   - `l_shape`: L‑shaped fill (3×3 minus one corner)
   - `cross`: plus‑sign fill
   - `donut`: rectangle with a hole (inner area set to background)
   - `disconnected`: two separate rectangles with a gap
3. **Distractor placement**: Same as object placement, but distractors are visually similar to test target‑selection.
4. **Noise pixels**: Randomly place `noise_pixels` non‑background values. Must be deterministic — use a fixed seed derived from `task_id` hash.
5. **Edge‑touching**: If an object's position causes it to touch or exceed the canvas edge, it is clipped to the canvas boundary. The materializer must record the clipped region.
6. **Overlapping objects**: Later objects overwrite earlier ones at overlapping cells.
7. **Color encoding**: Colors are integers 1–9. Background is 0.

### 3.5 Enriched scene_spec generation

The current generator's scene_specs are trivially uniform. A follow‑up implementation lane must:
- Enrich each BH80 task's scene_spec to match its hardness‑axis description
- Add distractors where axis 3 (distractor pressure) is active
- Add edge‑touching positions where axis 7 is active
- Add holes/disconnected shapes where axis 9 is active
- Add multiple objects where axis 8 (multi‑object relational) is active
- Vary grid sizes where mutation tasks call for canvas resizing

This enrichment is part of the implementation lane, not this design lane.

---

## 4. Oracle Primitive Semantics

The oracle implements its own reference semantics for every primitive. It must not call `run_primitive()` or any dispatch wrapper.

### 4.1 Core primitives

| Primitive | Oracle reference semantics |
|-----------|---------------------------|
| `extract` | Find the largest connected component (by cell count). Return a grid containing only that component, cropped to its bounding box. All other cells set to background. |
| `extract_largest_object` | Same as `extract`. |
| `isolate_largest` | Find the largest connected component. Return the original grid with only that component's cells preserved; all other non‑background cells set to background. Grid dimensions unchanged. |
| `extract_boundary` | Find the largest connected component. Compute its bounding box `[min_r, min_c, max_r, max_c]`. Return the original grid with only the bounding‑box border cells highlighted (set to color 1). Grid dimensions unchanged. |
| `crop` | Find the largest connected component. Crop the grid to its bounding box. Return the cropped grid. |
| `mirror_object` | Reflect the grid horizontally (reverse each row). Return the reflected grid. Grid dimensions unchanged. |
| `rotate` | Rotate the grid 90° clockwise. Return the rotated grid. Dimensions swap (H×W → W×H). |
| `recolor` | Replace all non‑background values with value 2. Return the recolored grid. |
| `normalize_position` | Find the largest connected component. Compute its centroid. Translate the entire grid so the centroid is at the center of the grid. Return the translated grid. Grid dimensions unchanged. |
| `place_back` | Create a new canvas of the same size as the original (pre‑crop) grid. Place the current grid's content at the center of the new canvas. Return the new canvas. |
| `count_objects` | Count connected components. Return the original grid unchanged (count is metadata, grid is unchanged). |
| `pattern_output` | Replace all non‑background cells with a repeating pattern based on their row index (e.g., alternating colors 1, 2, 1, 2, ...). Return the patterned grid. |
| `transform` | Apply a deterministic shape transform: flip vertically (reverse row order). Return the transformed grid. Grid dimensions unchanged. |

### 4.2 Alias primitives

| Alias | Oracle reference semantics |
|-------|---------------------------|
| `remove_noise` | Remove isolated single pixels (cells with no same‑color neighbor). Return the cleaned grid. |
| `extract_object` | Same as `extract` (largest connected component, cropped to bounding box). |
| `crop_object` | Same as `crop` (crop to bounding box of largest component). |
| `recolor_boundary` | Find the largest connected component's bounding box. Recolor only the border cells of the bounding box to color 2. Leave interior unchanged. Return the grid. |
| `count` | Same as `count_objects`. |
| `count_or_pattern` | If the grid has exactly 1 connected component, return the grid unchanged (count mode). Otherwise, apply `pattern_output` semantics. |
| `extract_changed_region` | Compute the bounding box of the largest connected component. Return the sub‑grid cropped to that bounding box (same as `crop`). |
| `fill_region` | Fill the entire grid with value 1. Return the filled grid. Grid dimensions unchanged. |

### 4.3 Oracle trace

The oracle must produce a trace with:
- Step 1 output grid
- Step 2 output grid
- Step 3 output grid (final reference)
- Per‑step primitive_id
- Per‑step metadata (bounding box, count, centroid, etc.)

The oracle trace is **not** given to the solver. It is used by the scorer for diagnostic comparison.

---

## 5. Solver Input Boundary

### What the solver may see

| Input | Allowed |
|-------|---------|
| Materialized input grid | ✅ |
| Declared primitive sequence (for this synthetic 3‑step lane only) | ✅ |
| `allowed_dynamic_parameters` (parameter names only, not values) | ✅ |

### What the solver may not see

| Input | Forbidden |
|-------|-----------|
| Expected output grid | ❌ |
| Oracle output grid | ❌ |
| Oracle trace | ❌ |
| `hardness_axes` | ❌ |
| `hardness_reason` | ❌ |
| `shortcut_defeated` | ❌ |
| `difficulty` | ❌ |
| `family_id` | ❌ (unless explicitly needed by a future lane) |
| `task_id` (as a shortcut — may be used for labeling only) | ❌ |
| Generator notes | ❌ |
| `expected_failure_categories` | ❌ |
| `expected_trace_requirements` | ❌ |
| `expected_test_output` | ❌ |

### Solver modification requirements

The solver must be modified to:
1. Accept the materialized input grid (not `[]` or `[[1]]` defaults)
2. Read `scene_spec` through the materializer (or receive the materialized grid directly)
3. Execute primitives on the real grid
4. Return the final output grid

The solver must not:
- Default empty grids to `[[1]]`
- Ignore the input grid
- Use metadata fields as solving shortcuts

---

## 6. Scoring Policy

### Result categories

| Category | Definition |
|----------|------------|
| **`semantic_exact`** | Solver final grid equals oracle final grid (all cells, all dimensions) |
| **`semantic_partial`** | Disabled for now — would require structural near‑match definition. May be added in a later lane. |
| **`unsupported`** | Solver lacks dispatch support for a primitive in the sequence |
| **`failed`** | Solver or oracle raises a runtime error |
| **`structural_pass`** | All primitives were supported (the old definition). Reported **separately** from `semantic_exact`. Never conflated. |

### Scoring algorithm

```python
def score_task(solver_grid, oracle_grid, solver_supported):
    if not solver_supported:
        return "unsupported"
    if solver_grid is None:
        return "failed"
    if grids_equal(solver_grid, oracle_grid):
        return "semantic_exact"
    return "failed"  # or "semantic_partial" if partial scoring is enabled
```

### Gate definitions (semantic)

| Gate | Requirement |
|------|-------------|
| **Semantic Minimal** | ≥ 68/80 semantic_exact (85%) |
| **Semantic Strong** | ≥ 72/80 semantic_exact (90%) |
| **Semantic Clean** | 80/80 semantic_exact (100%) |

These gates replace the structural gates for all future reporting. Structural pass remains as a secondary metric.

---

## 7. Anti‑Cheat Controls

### 7.1 Task ID randomization
- Shuffle task order before scoring
- Verify results are invariant to task ordering (solver must not use task_id)

### 7.2 Metadata removal
- Strip `family_id`, `difficulty`, `hardness_axes`, `shortcut_defeated`, `expected_failure_categories` from the task packet before passing to solver
- Verify results are unchanged

### 7.3 Primitive‑order negative controls
- For a sample of order‑sensitive tasks (axes 1+5), reverse the primitive order
- The semantic result should differ from the correct order (oracle produces different output)
- If most reversed orders still score `semantic_exact`, the oracle is too weak

### 7.4 No‑op shadow controls
- Replace each step with `pattern_output` (identity in current dispatch)
- The semantic result should differ (oracle produces different output than no‑op chain)
- If no‑op chains still score `semantic_exact`, the oracle is too weak

### 7.5 Unsupported primitive sentinel
- Add a task with `fake_primitive` → should score `unsupported`

### 7.6 Impossible‑selection sentinel
- Add a task with an empty grid (no objects) and `isolate_largest` → should score `failed` or produce a defined degenerate output

### 7.7 Output diversity audit
- After semantic scoring, count unique solver output grids and unique oracle output grids
- Both must be substantially diverse (target: ≥ 20 unique oracle outputs across 80 tasks)
- If diversity is too low, scene_specs are too uniform

### 7.8 Trace intermediate‑grid audit
- For a sample of tasks, compare solver intermediate grids to oracle intermediate grids
- Flag tasks where solver and oracle diverge at step 1 or 2 but converge at step 3 (possible accidental equality)

### 7.9 Solver/oracle code separation audit
- Static analysis: confirm oracle does not import or call `run_primitive()`, `_process_task()`, or any dispatch function
- Confirm scorer does not import solver or oracle execution functions

### 7.10 Scene_spec read audit
- Instrument the solver to confirm it reads the materialized input grid
- Verify the solver does not default to `[[1]]` when a real grid is provided

---

## 8. BH80 Semantic Regression Role

After the oracle is implemented, BH80 becomes the **BH80 semantic regression gate**:

- Any change to solver dispatch (`run_primitive`, wrappers, adapters) must be followed by a BH80 semantic run
- The semantic score must not decrease below the last recorded gate
- If the score decreases, the change is blocked until the regression is explained or reverted
- The gate prevents future solver changes from "faking success" by merely being structurally supported

### Regression gate levels

| Level | Gate | Usage |
|-------|------|-------|
| **Blocking** | Semantic Strong (72/80) | Changes that lower the score below this are blocked |
| **Target** | Semantic Clean (80/80) | Goal for full semantic correctness |
| **Minimum** | Semantic Minimal (68/80) | Absolute floor — below this means broken |

---

## 9. Conditions for Moving to 120 Tasks

The 120‑task expansion may only proceed after **all** of the following are verified:

1. ✅ BH80 oracle exists and is implemented
2. ✅ BH80 semantic scoring exists and is run
3. ✅ No‑op shadow controls fail as expected (no‑op chains do **not** score `semantic_exact`)
4. ✅ Primitive‑order negative controls fail as expected (reversed orders produce different outputs)
5. ✅ `scene_spec` is actually read by the solver (input grid is materialized, not `[[1]]`)
6. ✅ Output diversity is nontrivial (≥ 20 unique oracle outputs across 80 tasks)
7. ✅ At least one semantic BH80 run is recorded with results

Only after all conditions are met, recommend: `DESIGN_ARC_SYNTHETIC_3_STEP_SEMANTIC_120_V1`

---

## 10. Implementation Plan (for the next lane)

### Files to create

| File | Purpose |
|------|---------|
| `weslr/arc_bh80_oracle.py` | Independent oracle with reference primitive semantics |
| `weslr/arc_bh80_materializer.py` | Scene materializer (scene_spec → input grid) |
| `weslr/arc_bh80_semantic_scorer.py` | Semantic scorer (solver grid vs oracle grid comparison) |
| `weslr/tests/test_bh80_oracle.py` | Focused tests for oracle reference primitives |
| `weslr/tests/test_bh80_materializer.py` | Focused tests for scene materialization |
| `weslr/tests/test_bh80_semantic_scorer.py` | Focused tests for semantic scoring |

### Files to modify

| File | Change |
|------|--------|
| `weslr/arc_synthetic_3_step_task_schema.py` | Enrich scene_specs for all 80 tasks |
| `weslr/arc_synthetic_3_step_real_dispatch.py` | Modify solver to accept materialized input grid |

### Implementation order

1. Materializer (scene_spec → grid)
2. Oracle (reference primitives)
3. Semantic scorer
4. Enrich scene_specs
5. Modify solver to read materialized grids
6. Run anti‑cheat controls
7. Run first semantic BH80 pilot

---

## 11. Forbidden Claims

- No public ARC data used ✅
- No hidden/private ARC data used ✅
- No ARC‑AGI benchmark claims ✅
- No external provider API or model calls ✅
- No runtime/chat/UI/provider path changes ✅
- No `.weslr` IO ✅
- This design does not prove semantic solving — it designs the mechanism to test it ✅

---

## Receipt

| Field | Value |
|-------|-------|
| **Start HEAD** | `dfedcc60` |
| **End HEAD** | `7bb690c0` |
| **Commit** | yes (`7bb690c0`) |
| **Semantic solving defined** | yes ✅ |
| **Oracle/solver separation defined** | yes ✅ |
| **Scene_spec materialization defined** | yes ✅ |
| **Oracle primitive semantics defined** | yes (13 core + 8 aliases) ✅ |
| **Solver input boundary defined** | yes ✅ |
| **Scoring policy defined** | yes ✅ |
| **Anti‑cheat controls defined** | yes (10 controls) ✅ |
| **BH80 semantic regression role defined** | yes ✅ |
| **120 entry conditions defined** | yes (7 conditions) ✅ |
| **Validation** | PASS |
| **Push avoided** | yes ✅ |
| **Recommended next lane** | `IMPLEMENT_ARC_SYNTHETIC_3_STEP_BH80_INDEPENDENT_ORACLE_V1` |