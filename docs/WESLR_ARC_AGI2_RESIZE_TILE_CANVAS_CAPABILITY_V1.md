# WESLR ARC-AGI2 Resize / Tile / Canvas Pattern Capability V1

## Start HEAD
- `fa40da0a4426fd5adeef89250e297e32e68749de`

## Scope
Implemented a synthetic-only resize/tile/canvas reasoning lane with:
- crop-by-foreground-bbox
- whole-input tiling
- integer cell scaling
- border padding
- crop-then-tile

Integrated the new capability into the ARC-AGI-2 top-2 candidate aggregator.

## Files
- `weslr/arc_resize_tile_canvas_v1.py`
- `weslr/arc_agi2_resize_tile_candidate_adapter_v1.py`
- `weslr/arc_agi2_capability_candidate_aggregator_v1.py`
- `weslr/tests/test_arc_resize_tile_canvas_v1.py`
- `weslr/tests/test_arc_agi2_resize_tile_candidate_adapter_v1.py`
- `weslr/tests/test_arc_agi2_capability_candidate_aggregator_v1.py`

## Validation
- `python -m py_compile ...` ✅
- focused pytest across resize/tile + existing bbox/shape/color lanes ✅
- `git diff --check` ✅
- `python weslr/tests/release_gate_v1.py` ✅
- `./scripts/weslr_release_check.sh` ✅

## Notes
- Synthetic-only.
- No public ARC ingestion.
- No Kaggle writes.
- No claim of public ARC readiness.
