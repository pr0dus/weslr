# WESLR ARC Primitive Sequence to Grid Reconstruction V1

## Implementation Summary

Added a narrow helper that materializes predicted output grids from primitive sequences for the synthetic ARC-style solver.

## Files Added

- `weslr/arc_primitive_sequence_grid_reconstruction.py` – helper module
- `weslr/tests/test_arc_primitive_sequence_grid_reconstruction_v1.py` – 17 focused tests
- Updated `weslr/tests/release_gate_v1.py` with exact-path allowances

## What Was Implemented

### Helper: `apply_primitive_sequence_to_grid_v1`

Takes:
- `input_grid`: 2D list of int/bool cells
- `primitive_sequence`: list of primitive dicts with `primitive_id` and `parameters`

Returns:
- `reconstructed_grid`: the materialized output grid, or `None` if failed
- `reconstruction_success`: bool
- `failure_reason`: str or `None`
- `provenance`: `"primitive_sequence_reconstruction"`
- `schema_version`: `"ArcPrimitiveSequenceGridReconstructionV1"`

### Supported Primitives

- `copy`, `recolor`, `move`, `fill`, `fill_region`
- `extract_largest_object`, `remove_background_noise`
- `line_completion`, `object_count_to_pattern`
- `rotate_object_90`, `reflect_object_horizontal_or_vertical`
- `complete_symmetry`, `border_frame`

### Failure Handling

- Unsupported primitives: fail closed with `failure_reason: "unsupported_primitive:{id}"`
- Empty sequence: fail closed
- Invalid input grid: fail closed with `"invalid_input_grid"`
- Primitive execution failure: fail closed with `"primitive_failed:{id}"`

## Test Results

- All 17 tests passed
- All 5 dry-run toy tasks reconstruct successfully
- Input grid is not mutated
- Expected outputs are not required or used
- No scoring, no candidate_output_surface building, no replay wiring

## Validation Results

- `python3 -m py_compile` → PASS
- `pytest test_arc_primitive_sequence_grid_reconstruction_v1.py` → 17 passed
- `python3 weslr/tests/release_gate_v1.py` → PASS
- `git diff --check` → PASS
- `bash scripts/weslr_release_check.sh` → PASS
- `bash scripts/chat_weslr_de_health_check.sh --mode source-repo` → PASS

## Hard Boundaries Preserved

- No expected-output access
- No scoring
- No candidate_output_surface construction
- No replay wiring
- No final-answer emission
- No provider/model/tool/retrieval calls
- `.weslr` untouched
- Protected runtime/chat files unchanged
- Push avoided (commit remains local)

## Provenance

The helper uses provenance `"primitive_sequence_reconstruction"` to distinguish from other surface sources.

## Next Step

With reconstruction proven, the next narrow step would be to wire the reconstructed grids into `candidate_output_surface` construction (for the dry-run tasks first), completing the path from solver → reconstruction → surface.