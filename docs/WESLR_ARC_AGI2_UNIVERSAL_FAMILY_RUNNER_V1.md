# WESLR ARC-AGI2 Universal Family Runner V1

## Repo / branch
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`

## Start / end state
- Expected start HEAD: `9dc7d22f7a4e65d7fe1115b425c91a963494e3fb`
- Actual preflight HEAD: `9dc7d22f7a4e65d7fe1115b425c91a963494e3fb`
- End HEAD: `7c6d2452b8807164ec53536971a58291f49b61ca`
- Commit status: committed (`Implement ARC-AGI2 universal family runner V1`)

## Files added/changed
- Added: `weslr/arc_universal_family_runner_v1.py`
- Added: `weslr/tests/test_arc_universal_family_runner_v1.py`
- Added: `docs/WESLR_ARC_AGI2_UNIVERSAL_FAMILY_RUNNER_V1.md`

## Universal runner summary
- Connects task signatures, primitive discovery, family discovery, and the existing capability candidate aggregator.
- Emits exactly two attempts.
- Uses synthetic-only train/test fixtures.
- Does not ingest public ARC data, score public ARC data, or submit anything.

## Discovery chain integration behavior
- Builds task feature signatures.
- Runs primitive discovery.
- Runs family discovery.
- Selects executable single-step family hypotheses.
- Records two-step families as discovered but not executable in V1.
- Routes selected families into the existing capability candidate aggregator.

## Family-to-executor mapping
- `object_bbox` → object/bbox adapter via capability aggregator
- `shape_geometry` → shape geometry adapter via capability aggregator
- `color_role` → color-role adapter via capability aggregator
- `resize_tile` → resize/tile adapter via capability aggregator
- `count_quantity` → count/quantity adapter via capability aggregator
- two-step families → discovered-only metadata in V1

## Single-step execution behavior
- Crop-like synthetic tasks route to `object_bbox`.
- Recolor-like synthetic tasks route to `color_role`.
- Rotate/reflect-like synthetic tasks route to `shape_geometry`.
- Tile/scale-like synthetic tasks route to `resize_tile`.
- Count-to-line synthetic tasks route to `count_quantity`.

## Two-step discovered-not-executable policy
- `crop_then_recolor`
- `crop_then_rotate_or_reflect`
- `crop_then_tile`
- `recolor_then_border`
- `select_then_recolor`
- These are surfaced in trace as `discovered_not_executable_v1` and are not faked into execution.

## Ranking behavior
- Accepted discovered families first.
- High-confidence uncertain families next.
- Higher confidence first.
- Stable family order.
- Fallback last.

## Deduplication behavior
- Duplicate output grids are deduplicated.
- Higher-ranked candidates survive.
- Duplicate families are recorded in metadata.
- Fallback fills missing slots when needed.

## Fallback behavior
- If no executable discovered family yields a candidate, two safe deterministic fallback attempts are emitted.
- Fallback is not presented as discovered reasoning.

## Exact-two-output status
- The runner always returns exactly two attempts.
- `exact_two_output` is true on valid synthetic runs.

## Synthetic test summary
- `python -m py_compile weslr/arc_universal_family_runner_v1.py` ✅
- `python -m pytest -q weslr/tests/test_arc_universal_family_runner_v1.py` ✅ (7 passed)
- Focused primitive/family tests ✅
- `git diff --check` ✅
- `python weslr/tests/release_gate_v1.py` ✅
- `./scripts/weslr_release_check.sh` ✅
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo` ✅
  - Health result: PASS `6/0/3/0` with optional probe warnings only

## Limitations
- Synthetic-only lane.
- No public ARC data was read.
- No scoring or submission.
- Two-step families remain discovery-only in V1.

## Next recommended lane
- Compositional executor lane.
