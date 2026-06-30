# WESLR ARC 2‑Step Extract→Recolor Memory Contract Design V1

- **Dispatch**: `DESIGN_EXTRACT_RECOLOR_MEMORY_CONTRACT_V1`
- **Repo**: `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch**: `occ-discovery-doctrine-implementation-20260613`
- **Start HEAD (full)**: `2a302aeef760d2411ec1e615b5484d9180df488b`

## 1. Export contract for `extract_largest_object`

The primitive `extract_largest_object` will export a **structured object description** (`extracted_object`) containing the minimal set of information that can be safely consumed by downstream primitives without leaking task‑specific knowledge.

| Export field | Type | Meaning | Provenance label |
|--------------|------|---------|------------------|
| `extracted_object_handle` | `int` (object id) | A deterministic identifier for the extracted object (derived from its dominant non‑background colour). | `carried_from_step_1` |
| `extracted_object_value` | `int` | The colour/value of the extracted object (dominant non‑background colour in the intermediate grid). | `carried_from_step_1` |
| `extracted_object_background` | `int` | The background colour/value that was used to isolate the object (the `background_value` parameter passed to the primitive). | `carried_from_step_1` |
| `extracted_object_bbox` | `tuple[int,int,int,int]` | Bounding‑box `(row0, col0, row1, col1)` of the extracted region (inclusive). Useful for role‑based reasoning but optional for recolor. | `stable_train_inference` |
| `original_background_value` | `int` | The background colour/value of the *input* grid (same as `background_value` param). | `stable_train_inference` |
| `non_extracted_values` | `list[int]` | Sorted list of all non‑background colours **excluding** the extracted object value. Allows downstream primitives to reason about “other colours”. | `stable_train_inference` |

**Rationale** – The above fields give the downstream primitive everything it needs to decide:
- which colour to replace (`from_value`)
- which colour to paint with (`to_value`)
- whether the recolor should affect the background or a specific object.
All fields are derivable *only* from the input grid and the intermediate grid produced by `extract_largest_object`; no test‑output information is required.

## 2. Import contract for `recolor_symbol`

`recolor_symbol` will declare the *required* imports it can accept. The primitive expects a **colour‑pair contract** consisting of:

| Import field | Type | Meaning |
|--------------|------|---------|
| `background_value` | `int` | Background colour of the current grid (must match the exported background). |
| `from_value` | `int` | Colour to be recolored – to be resolved from either the exported `extracted_object_value` (object‑centric) or the `original_background_value` (background‑centric). |
| `to_value` | `int` | Target colour – inferred from *train‑pair deltas* (see section 3). |

The primitive will **reject** any candidate where any of the above imports are missing or cannot be inferred.

## 3. Inferring `to_value` without test output

The contract must be **train‑pair‑derived** only. The inference pipeline works as follows:

1. **Collect train pairs** for the same primitive pair (`extract_largest_object → recolor_symbol`). Each pair consists of:
   - Input grid `I`
   - Intermediate grid after extraction `E`
   - Final grid after recolor `F`

2. **Identify the extracted colour** in `E` using the `extracted_object_value` export.

3. **Compute colour deltas** between `E` and `F`:
   - `delta = {c_out for c_out in F if c_out not in E}` (non‑background colours that appear only after recolor).
   - If `delta` contains exactly **one colour**, that colour is a **candidate `to_value`**.
   - If `delta` is empty or contains >1 colour, the pair is **inconclusive**.

4. **Aggregate across all train pairs**:
   - If **all conclusive pairs agree on a single `to_value`**, the contract declares that value as *stable* and labels the provenance `stable_train_inference`.
   - If the set of candidate `to_value`s varies, the contract marks the import as **unstable** and the row will be rejected (`rejection_reason = "unstable_to_value_across_train_pairs"`).
   - If **no pair is conclusive**, the contract falls back to `dynamic_recomputed_from_current_input` (the `to_value` must be supplied by an external hint – which is disallowed, so the row will be rejected).

**No test‑output** is consulted; only the deterministic transformation from `E`→`F` is examined.

## 4. Handling inconsistent train‑pair exports

When `extract_largest_object` yields **different `extracted_object_value`s** across train pairs, the contract treats the export as **dynamic**:
- `from_value` is resolved **per‑pair** from the exported `extracted_object_value`.
- The provenance label for `from_value` becomes `dynamic_recomputed_from_current_input`.
- The contract still requires a *stable* `to_value` as defined in §3; otherwise the candidate is rejected (`rejection_reason = "unstable_to_value"`).

If the variation is *systematic* (e.g., always two possible colours), the design may later allow a **role‑based mapping** (`object_role = "largest_object"`) but this is outside the scope of the current bounded lane.

## 5. Provenance labels

The contract will attach **one of the following provenance tags** to each imported key:
- `carried_from_step_1` – directly taken from an exported field of `extract_largest_object`.
- `stable_train_inference` – inferred deterministically from a *consistent* set of train‑pair deltas.
- `dynamic_recomputed_from_current_input` – recomputed from the current grid (e.g., `background_value` derived from current background).
- `inferred_from_train_output_delta` – derived from the colour delta between `E` and `F`.
- `rejected_unstable` – used when the inference cannot produce a unique value.

These tags are stored in the `parameter_origin_by_key` dictionary of the blackboard trace.

## 6. Leakage‑boundary enforcement

The contract explicitly **forbids** any of the following during candidate generation:
- Access to **test‑output** or any `target_color` metadata that is not present in the training pairs.
- Use of **task‑id shortcuts** (e.g., `task_id -> target_color`).
- Use of **generator notes** as a source of colour values.
- Any **hard‑coded colour constants** not derivable from the train pair delta.

All inference must be performed within the **synthetic‑only** leakage flag set (`synthetic_only = true`).

## 7. Diagnostic trace extensions

To make the contract observable, the blackboard trace for each candidate will include the following additional fields:
- `extract_exports` – the full export dict from `extract_largest_object`.
- `recolor_import_requirements` – the set of keys the recolor primitive expects.
- `import_resolution` – mapping of each required key to the source (`carried_from_step_1`, `stable_train_inference`, etc.).
- `unresolved_imports` – list of keys that could not be resolved (causing rejection).
- `output_delta_inference` – the colour delta set computed between `E` and `F` for the train pair.
- `from_value_resolution` – how `from_value` was obtained.
- `to_value_resolution` – how `to_value` was inferred.
- `contract_status` – `accepted` or `rejected`.
- `rejection_reason` – human‑readable reason when rejected (e.g., `unstable_to_value_across_train_pairs`).

These fields enable downstream lanes to detect exactly why a candidate succeeded or failed.

## 8. Smallest safe implementation lane after this design

**Implementation lane**: `IMPLEMENT_EXTRACT_RECOLOR_MEMORY_CONTRACT_V1`

- **Files touched** (exact‑path allowances will be added):
  1. `weslr/arc_style_synthetic_2_step_pilot_runner.py` – modify `_build_carryover_trace` to emit the new export fields and provenance tags.
  2. `weslr/tests/test_arc_style_synthetic_2_step_pilot_runner_v1.py` – add a focused test `test_extract_recolor_memory_contract` that:
     - Runs the 80‑runner.
     - Locates the target row `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1`.
     - Asserts that `parameter_origin_by_key` now contains entries for `from_value` (`carried_from_step_1` or `dynamic_recomputed_from_current_input`) and `to_value` (`stable_train_inference`).
     - Verifies that `contract_status` is `accepted` **iff** the train‑pair delta is stable; otherwise it verifies the correct rejection reason.

- **Expected result**: After the implementation the target row should become `exact` *if* the `to_value` inference is stable; otherwise it becomes `partial` with a deterministic `rejection_reason`.

- **Rollback criteria**: If any of the new fields introduce unexpected failures in existing 40/80 tests, revert the changes and mark the contract as *unimplemented*.

---

**Design summary**: The contract defines a structured export from `extract_largest_object` and a deterministic, train‑pair‑derived import for `recolor_symbol`. It enforces strict leakage boundaries, provides provenance tags, and adds diagnostic trace fields to make the reasoning transparent. The next lane will implement the export/import logic and add focused tests.
