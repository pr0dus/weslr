# ARC Synthetic 3‑Step – BH80 Oracle Implementation Review and Enrichment Plan (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `REVIEW_AND_PREPARE_BH80_SEMANTIC_SCENE_ENRICHMENT_V1`
**Start HEAD**: `aba41b0c`

---

## 1. Preflight

| Check | Result |
|-------|--------|
| `pwd` | `/data/data/com.termux/files/home/weslr-pr47-clean` ✅ |
| `git status` | clean ✅ |
| `git branch --show-current` | `occ-discovery-doctrine-implementation-20260613` ✅ |
| `git rev-parse --short HEAD` | `aba41b0c` ✅ |
| Metadata reconciled | yes — matches expected `aba41b0c` ✅ |

---

## 2. Review Results

### 2.1 Materializer exists and reads scene_spec
- `materialize_scene(scene_spec, task_id)` in `weslr/arc_bh80_materializer.py` ✅
- Reads grid_size, background, objects, distractors, noise_pixels ✅
- Does not return `[[1]]` defaults ✅
- Test proof: different specs produce different grids ✅

### 2.2 Independent oracle does not call solver dispatch
- Static check: oracle module does not import `arc_synthetic_3_step_real_dispatch` ✅
- Dynamic check: monkey‑patching `run_primitive` to raise does not break oracle ✅
- Oracle has own connected‑components, bounding‑box, centroid implementations ✅

### 2.3 Semantic scorer uses grid equality for `semantic_exact`
- `grids_equal(a, b)` — element‑wise and dimension‑wise ✅
- `score_task` classifies as `semantic_exact` only when `solver_grid == oracle_grid` ✅
- `exact` does NOT mean "all primitives supported" ✅

### 2.4 Solver adapter receives materialized input grids
- `solver_run_with_input(input_grid, primitive_sequence)` passes real grid to `run_primitive()` ✅
- Solver output is NOT `[[1]]` when given a real grid ✅

### 2.5 `structural_pass` separate from `semantic_exact`
- `structural_pass` is a boolean field in the score report ✅
- `result` field is one of `semantic_exact`, `unsupported`, `failed` ✅
- Never conflated ✅

### 2.6 No‑op controls pass
- Replacing primitives with `pattern_output` chain changes oracle output ✅

### 2.7 Primitive‑order negative controls pass
- Reversed order produces different oracle output ✅

### 2.8 Unsupported sentinel passes
- `fake_primitive` returns `unsupported` from both solver and oracle ✅

### 2.9 Output diversity test exists
- 6 representative tasks produce ≥ 3 unique oracle outputs ✅

### 2.10 Full BH80 semantic run is not yet ready
- 68 of 80 scene specs need enrichment ✅
- Full semantic benchmark blocked until enrichment is complete ✅

---

## 3. Oracle Implementation Verdict

**`accepted`** — the oracle implementation is accepted as the foundation for semantic BH80 scoring.

---

## 4. Known Blockers

### 4.1 Scene enrichment gap (68/80 tasks)
12 of 80 tasks have enriched scene specs. The remaining 68 use a default non‑trivial spec (3×3 rectangle at center). While this is better than `[[1]]`, it does not provide the diversity needed to test the full hardness‑axis model.

### 4.2 `place_back` oracle semantics
The oracle's `place_back` currently returns the grid unchanged (identity). Full semantics require knowledge of the original pre‑crop canvas size, which is not passed through the 3‑step pipeline. This may cause semantic mismatches for tasks using `place_back` after `crop` or `crop_object`.

**Plan**: Add a pipeline‑level context object that carries the original canvas size through the 3 steps. The oracle and solver adapter must both support this context.

### 4.3 Solver `pattern_output` and `transform` wrappers are identity/no‑op
The solver dispatch's `pattern_output` wrapper returns the grid unchanged ("identity (no change)"). The `transform` wrapper also returns the grid unchanged ("identity transformation"). The oracle implements these as real transformations (row‑index alternating colors for `pattern_output`, vertical flip for `transform`).

**Plan**: Modify the solver dispatch wrappers for `pattern_output` and `transform` to match the oracle's reference semantics, OR document the semantic gap and exclude affected tasks from the first semantic run. Recommended: modify the solver wrappers to match oracle semantics (narrow, behavioral change only, no metadata shortcuts).

---

## 5. Remaining 68 Tasks Needing Enrichment

```
BH80_003, BH80_004, BH80_007, BH80_008, BH80_009, BH80_010, BH80_011,
BH80_013, BH80_014, BH80_015, BH80_016, BH80_017, BH80_018, BH80_019,
BH80_020, BH80_021, BH80_022, BH80_024, BH80_026, BH80_027, BH80_028,
BH80_029, BH80_030, BH80_031, BH80_032, BH80_033, BH80_034, BH80_035,
BH80_036, BH80_037, BH80_038, BH80_039, BH80_040, BH80_041, BH80_042,
BH80_043, BH80_044, BH80_045, BH80_046, BH80_047, BH80_049, BH80_051,
BH80_052, BH80_053, BH80_054, BH80_055, BH80_056, BH80_057, BH80_058,
BH80_059, BH80_060, BH80_062, BH80_063, BH80_064, BH80_065, BH80_066,
BH80_067, BH80_068, BH80_070, BH80_071, BH80_072, BH80_073, BH80_074,
BH80_075, BH80_076, BH80_077, BH80_078, BH80_079
```

---

## 6. Enrichment Plan

### Phase 1: Enrich remaining 68 scene specs
For each task, the enriched scene_spec must align with its hardness‑axis description:
- **Axis 3 (distractor pressure)**: Add 1–2 distractor objects with same color/shape as target
- **Axis 7 (edge/boundary pressure)**: Position main object touching or near canvas edge
- **Axis 8 (multi‑object relational)**: Add 2–3 objects with varying sizes/positions
- **Axis 9 (shape identity)**: Use `donut`, `l_shape`, `disconnected`, or `cross` shapes
- **Canvas size variation**: Vary grid_size across tasks (8×8, 10×10, 12×12, 6×8, etc.)
- **Color variation**: Use colors 1–5 across tasks, not just color 1

### Phase 2: Repair `place_back` oracle semantics
- Add a `PipelineContext` object that carries original canvas size
- Oracle's `place_back` reads canvas size from context and places current grid centered on it
- Solver adapter also passes context through

### Phase 3: Align solver `pattern_output` and `transform`
- Modify `pattern_output` wrapper in dispatch to match oracle: row‑index alternating colors (1, 2, 1, 2, ...)
- Modify `transform` wrapper in dispatch to match oracle: vertical flip (reverse row order)
- These are narrow behavioral changes, not metadata shortcuts

### Phase 4: Run full semantic BH80 benchmark
- Only after phases 1–3 are complete
- Run all 80 tasks through semantic scorer
- Record `semantic_exact` / `unsupported` / `failed` per task
- Report separately from `structural_pass`

---

## 7. Risks Before Full Semantic Run

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Insufficient scene diversity | Low semantic differentiation | Phase 1 enrichment with varied shapes, sizes, colors |
| `place_back` semantic gap | False `failed` for crop+place_back tasks | Phase 2 context object |
| `pattern_output`/`transform` identity in solver | False `failed` for tasks using these primitives | Phase 3 alignment |
| Oracle primitive edge cases | Unexpected oracle output | Test oracle on edge cases (empty grid, single cell, full grid) |
| Solver wrapper differences (`crop_object` pass‑through) | Semantic mismatch on `crop_object` tasks | Audit all alias wrappers against oracle semantics |

---

## 8. Validation

| Check | Result |
|-------|--------|
| `git diff --check` | clean ✅ |
| `python weslr/tests/release_gate_v1.py` | `WESLR_RELEASE_GATE_V1_OK` ✅ |
| `./scripts/weslr_release_check.sh` | `WESLR_RELEASE_CHECK_OK` ✅ |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | PASS=6 FAIL=0 ✅ |

---

## Receipt

| Field | Value |
|-------|-------|
| **Start HEAD** | `aba41b0c` |
| **End HEAD** | `aba41b0c` (review‑only, no code changes) |
| **Commit** | none (review report only — will commit the report) |
| **Actual preflight HEAD** | `aba41b0c` ✅ |
| **Metadata reconciled** | yes ✅ |
| **Oracle implementation accepted** | yes ✅ |
| **Full BH80 semantic run ready** | no — 68/80 scenes need enrichment ❌ |
| **68 remaining scene specs listed** | yes ✅ |
| **`place_back` blocker recorded** | yes ✅ |
| **`pattern_output`/`transform` blocker recorded** | yes ✅ |
| **Validation** | PASS ✅ |
| **Push avoided** | yes ✅ |
| **Recommended next lane** | `ENRICH_BH80_SCENE_SPECS_FOR_SEMANTIC_RUN_V1` |