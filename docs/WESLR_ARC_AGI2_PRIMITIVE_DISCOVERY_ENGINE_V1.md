# WESLR ARC-AGI2 Primitive Discovery Engine V1

## Repo / branch
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`

## Start / end state
- Expected start HEAD: `577bb94f7fe8ed1be38044022ba1d0e42bf7416a`
- Actual preflight HEAD: `577bb94f7fe8ed1be38044022ba1d0e42bf7416a`
- End HEAD: `577bb94f7fe8ed1be38044022ba1d0e42bf7416a` before commit, then committed in this lane
- Commit status: committed (`Implement ARC-AGI2 Primitive Discovery Engine V1`)

## Files added
- `weslr/arc_primitive_discovery_engine_v1.py`
- `weslr/tests/test_arc_primitive_discovery_engine_v1.py`
- `docs/WESLR_ARC_AGI2_PRIMITIVE_DISCOVERY_ENGINE_V1.md`

## Engine behavior
- Builds a task feature signature via `weslr/arc_task_feature_signature_v1.py`.
- Loads the built-in primitive registry when none is supplied.
- Produces JSON-safe `PrimitiveDiscoveryHint` records with:
  - `primitive_name`
  - `family`
  - `status`
  - `confidence`
  - `reason`
  - `inferred_parameters`
  - `source_feature_labels`
  - `trace`
- Produces JSON-safe `PrimitiveDiscoveryResult` records with accepted/rejected/uncertain partitions and compact trace only.
- Does not emit raw grids, expected outputs, solution labels, or final ARC answers.

## Discovery behavior
- Crop hints:
  - accepts exact crop-like matches
  - rejects crop primitives when size/evidence contradicts cropping
- Translation hints:
  - accepts shape-preserving object translation with stable palette/count structure
  - rejects when size or shape evidence is incompatible
- Geometry hints:
  - accepts exact rotate/reflect matches
  - rejects color-only changes that do not alter geometry
- Color-role hints:
  - accepts recolor-like same-size palette-change tasks
  - rejects palette-stable tasks
- Resize/tile/border hints:
  - accepts exact integer scale, tile, border, and crop-then-tile matches
  - rejects incompatible size relations
- Count/quantity hints:
  - accepts count-to-line / count-to-square style tasks
  - rejects inconsistent count evidence

## Test summary
- `python -m py_compile weslr/arc_primitive_discovery_engine_v1.py` ✅
- `python -m pytest -q weslr/tests/test_arc_primitive_discovery_engine_v1.py` ✅ (7 passed)
- `git diff --check` ✅
- `python weslr/tests/release_gate_v1.py` ✅
- `./scripts/weslr_release_check.sh` ✅
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo` ✅
  - Health result: PASS `6/0/3/0` with optional probe warnings only

## Limitations
- Synthetic-only lane.
- No public ARC data was read, scored, or submitted.
- Discovery is applicability-focused; it does not run full family hypothesis search or emit final answers.
- Some primitives may remain uncertain when task evidence is insufficient.

## Next recommended lane
- ARC family hypothesis discovery lane using the primitive discovery hints as the input signal.
