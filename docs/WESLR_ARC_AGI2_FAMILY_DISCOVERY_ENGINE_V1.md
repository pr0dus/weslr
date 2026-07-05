# WESLR ARC-AGI2 Family Discovery Engine V1

## Repo / branch
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`

## Start / end state
- Expected start HEAD: `6db595b100d459da2129f2cf34e12805acb1d37f`
- Actual preflight HEAD: `6db595b100d459da2129f2cf34e12805acb1d37f`
- End HEAD: `06e6148cccb9218813c0cd09d8bcfc6d83ded130`
- Commit status: committed (`Implement ARC-AGI2 Family Discovery Engine V1`)

## Files added/changed
- Added: `weslr/arc_family_discovery_engine_v1.py`
- Added: `weslr/tests/test_arc_family_discovery_engine_v1.py`
- Added: `docs/WESLR_ARC_AGI2_FAMILY_DISCOVERY_ENGINE_V1.md`

## Family discovery summary
- Converts primitive discovery hints into bounded family hypotheses.
- Uses the task feature signature extractor plus primitive discovery output.
- Supports single-step family hypotheses and a fixed set of two-step composition templates.
- Returns JSON-safe accepted / rejected / uncertain partitions.
- Does not emit final ARC answers or public-data outputs.

## Family hypothesis schema
- `family_name`
- `primitive_chain`
- `status`
- `confidence`
- `reason`
- `parameters`
- `train_fit`
- `rejection_reason`
- `source_primitive_hints`
- `trace`

## Primitive discovery integration behavior
- Builds primitive discovery automatically when not supplied.
- Accepts an injected primitive result when supplied.
- Ignores unknown primitive hints safely.
- Uses registry-backed primitive names only.

## Single-step family behavior
- `object_bbox`
- `shape_geometry`
- `color_role`
- `resize_tile`
- `count_quantity`
- Each family is validated against synthetic train fixtures with exact-fit helpers where available.

## Two-step composition behavior
Allowed templates:
- `crop_then_recolor`
- `crop_then_rotate_or_reflect`
- `crop_then_tile`
- `recolor_then_border`
- `select_then_recolor`

Each template is bounded to chain length 2 and rejects unsupported or contradictory cases.

## Train-consistency / rejection behavior
- Rejects when required primitives are rejected.
- Rejects when composition consistency fails.
- Rejects chains above the V1 depth limit.
- Rejects unsupported chains outside the allowed template list.
- Deduplicates repeated family-output signatures.

## Ranking behavior
- Accepted before uncertain before rejected.
- Higher confidence first.
- Shorter primitive chains first.
- Stable family priority and primitive ordering.

## Test summary
- `python -m py_compile weslr/arc_family_discovery_engine_v1.py` ✅
- `python -m pytest -q weslr/tests/test_arc_family_discovery_engine_v1.py` ✅ (7 passed)
- `git diff --check` ✅
- `python weslr/tests/release_gate_v1.py` ✅
- `./scripts/weslr_release_check.sh` ✅
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo` ✅
  - Health result: PASS `6/0/3/0` with optional probe warnings only

## Limitations
- Synthetic-only lane.
- No public ARC data was read, scored, or submitted.
- Family discovery is bounded and template-based, not universal.
- Final answer generation remains outside this lane.

## Next recommended lane
- Universal family runner lane, using the accepted family hypotheses as the bounded execution layer.
