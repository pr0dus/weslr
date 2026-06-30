# WESLR ARC 2‑Step Extract→Recolor Export Trace Only Implementation V1

- **Dispatch**: `IMPLEMENT_EXTRACT_RECOLOR_MEMORY_CONTRACT_EXPORT_TRACE_ONLY_V1`
- **Repo**: `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch**: `occ-discovery-doctrine-implementation-20260613`
- **Start HEAD**: `a345ed8ff6565e3339cb4fd179ffe3428ec7adc7`

## Goal
Implemented the diagnostic export side of the bounded extract→recolor memory contract. Added additional export fields for `extract_largest_object` in the 2‑step blackboard trace:

- `extracted_object_handle` – bounding box and cell list of the extracted object.
- `extracted_object_value` – dominant colour/value of the extracted object.
- `extracted_object_background` – background colour used during extraction.
- `extracted_object_bbox` – simple `(min_row, min_col, max_row, max_col)` bounding box.
- `original_background_value` – background value of the original input grid.
- `non_extracted_values` – list of non‑background values that are **not** part of the extracted object.

These fields appear in `step_1_exports` for any 2‑step candidate involving `extract_largest_object` → `recolor_symbol`. The implementation does **not** modify recolor import resolution, `to_value` inference, or any solver/generator behaviour.

## Invariants preserved
- Original 40 result unchanged: `39 exact / 1 partial / 0 unsupported / 0 failed`.
- Combined 80 result unchanged: `76 exact / 4 partial / 0 unsupported / 0 failed`.
- Represented candidates: `80`.
- No leakage flags introduced.
- Target row `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1` remains `partial / parameter_carryover_failure`.

## Tests added
Added `test_extract_recolor_export_fields_present` to `weslr/tests/test_arc_style_synthetic_2_step_pilot_runner_v1.py`. The test runs the 80‑runner, locates the target candidate, and asserts presence of all new export fields and clean leakage flags.

## Release‑gate
Added exact‑path allowance for this report in `weslr/tests/release_gate_v1.py` under the ARC 2‑step section.

## Validation
- `python -m py_compile` on modified modules.
- Focused pytest (new test + existing suite) all pass.
- `python weslr/tests/release_gate_v1.py` passes.
- `git diff --check` clean.
- `./scripts/weslr_release_check.sh` passes.
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo` passes.
