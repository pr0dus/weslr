# IMPLEMENT_ARC_SYNTHETIC_3_STEP_PRIMITIVE_COVERAGE_BATCH_4_CONTRACTS_V1

**Repo:** `weslr-pr47-clean`
**Branch:** `occ-discovery-doctrine-implementation-20260613`
**Start HEAD:** `ca9b26e8`

---

## Remaining unsupported primitives (from Batch 3)
| Primitive | Exact input type | Exact output type | Required parameters | Trace fields produced | Success criteria | Failure criteria | Safe local helper exists? | Implementation risk | Expected task‑gain |
|----------|------------------|-------------------|--------------------|----------------------|-------------------|------------------|--------------------------|-------------------|-------------------|
| `normalize_position` | Object coordinates (`x: int|float`, `y: int|float`) and optional canvas size (`canvas_width: int`, `canvas_height: int`) | Normalized coordinates (`norm_x: float`, `norm_y: float` in `[0,1]`) | `canvas_width` (optional, defaults to the grid width), `canvas_height` (optional) | `primitive_id`, `norm_x`, `norm_y` | Returned values are proportional to the original coordinates and lie within `[0,1]`. | Missing canvas dimensions, division‑by‑zero, or values outside `[0,1]`. | No – pure arithmetic wrapper needed. | **Low** – deterministic, bounded arithmetic. | **+2** exact tasks (`F006_1`, `F006_2`). |
| `place_back` | Source object grid (`List[List[Any]]`) + target canvas specs (`canvas_height: int`, `canvas_width: int`, `anchor_row: int`, `anchor_column: int`) | New canvas grid with the object placed at the specified anchor. | `canvas_height`, `canvas_width`, `anchor_row`, `anchor_column`, optional `object_value` (defaults to first non‑background cell). | `primitive_id`, `placement_anchor`, `canvas_dimensions`, `object_id` | Object appears on the new canvas exactly at the requested anchor, canvas dimensions match specs, and background is preserved. | Out‑of‑bounds anchor, mismatched dimensions, or object not placed. | Helper `place_object_on_new_canvas` exists (places a single object onto a fresh canvas) – needs a thin wrapper for parameter validation and anchor handling. | **Low** – wrapper around existing primitive. | **+2** exact tasks (`F004_2`, `F004_3`). |
| `count_objects` | Grid (`List[List[Any]]`) | Integer count (`int`) and optional pattern grid (`List[List[Any]]`) | Optional `background_value` to ignore. | `primitive_id`, `count`, `pattern_grid` (if generated) | Returned count equals the number of distinct non‑background connected components in the grid. | Count mismatch, or helper returns `None`. | No direct helper; closest is `object_count_to_pattern` which only produces a pattern grid, not a reliable count. | **Medium** – requires deterministic component counting logic. | **+3** exact tasks (`F003_1`, `F003_2`, `F003_3`). |
| `extract_boundary` | Grid (`List[List[Any]]`) | Boundary description (`dict` with `top`, `left`, `bottom`, `right`) and optional extracted boundary grid. | Optional `background_value`. | `primitive_id`, `boundary_coords`, `extracted_boundary_grid` | Boundary coordinates correctly enclose the minimal non‑background region; extracted grid matches that region. | No non‑background cells found, or coordinates exceed grid limits. | No existing helper; closest is `crop_to_non_background_bbox` (returns cropped grid but not coordinates). | **Medium** – need to compute bounding box and optionally crop. | **+2** exact tasks (`F005_1`, `F005_2`). |
| `mirror_object` | Grid (`List[List[Any]]`) | Mirrored grid (`List[List[Any]]`) | `axis` (`"horizontal"` or `"vertical"`) | `primitive_id`, `axis`, `mirrored_grid` | Grid is correctly reflected across the specified axis. | Invalid axis value, or failure to preserve background cells. | No helper; Phase‑2 adapter defines a `reflect` primitive but `is_executable_now=False`. | **Medium** – enable existing primitive or implement a thin reflector. | **+2** exact tasks (`F007_1`, `F007_2`). |
| object‑level `crop` | Grid (`List[List[Any]]`) + bounding box (`top`, `left`, `height`, `width`) | Cropped object grid (`List[List[Any]]`) | `bounding_box` dict, optional `background_value` | `primitive_id`, `crop_box`, `cropped_grid` | Cropped grid exactly matches the region defined by the bounding box and contains a single connected component (the object). | Bounding box out of bounds, or resulting grid empty/multiple components when a single object is expected. | Primitive `crop` exists but only provides generic rectangular cropping; ARC tasks require assurance of a *single* object crop. | **Medium** – wrapper adds validation of single‑object content. | **+2** exact tasks (`F008_1`, `F008_2`). |

## Prioritized implementation order (maximizing exact gain while keeping risk low)
1. `normalize_position` – low risk, pure arithmetic, resolves `F006_1` & `F006_2` (+2 exact).
2. `place_back` – thin wrapper around existing `place_object_on_new_canvas`, resolves `F004_2` & `F004_3` (+2 exact).
3. `count_objects` – medium risk component counting, resolves `F003_1‑3` (+3 exact).
4. `extract_boundary` – medium risk bounding‑box extraction, resolves `F005_1‑2` (+2 exact).
5. `mirror_object` – enable/implement reflector, resolves `F007_1‑2` (+2 exact).
6. object‑level `crop` – wrapper adding single‑object validation, resolves `F008_1‑2` (+2 exact).

**Expected maximum exact gain** if all six are implemented: **+13** exact tasks, raising exact count from 7 to **20** (100 % exact). Realistically, completing the first three priorities would raise exact count to **14** (70 % exact), meeting the immediate target.

---

### Safety & Governance
- All leakage flags remain **false** for every task.
- Diagnostic metadata (`diagnostic_expected_failure_categories`) stays separate from solver outcome fields.
- No changes to existing solver scaffolds or tests (except a potential release‑gate allowance for the new contracts file, which is a documentation‑only change).
- No external/provider calls, ARC‑AGI claims, or `.weslr` writes.

---

**Short receipt**
- **Start HEAD:** `ca9b26e8` → **End HEAD:** `ca9b26e8` (no code changes).
- **Report path:** `docs/WESLR_ARC_SYNTHETIC_3_STEP_PRIMITIVE_COVERAGE_BATCH_4_CONTRACTS_V1.md`.
- **Contracts created:** ✅
- **Primitive contracts covered:** all six remaining blockers.
- **Recommended implementation order:** `normalize_position → place_back → count_objects → extract_boundary → mirror_object → crop`.
- **Expected max exact gain:** **+13** (up to 100 % exact).
- **Validation:** PASS (git diff clean, release gate passes, health check passes).
- **Push avoided:** ✅
- **Recommended next lane:** `IMPLEMENT_ARC_SYNTHETIC_3_STEP_PRIMITIVE_COVERAGE_BATCH_4_V1` (actual code implementation).