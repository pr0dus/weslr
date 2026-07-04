# WESLR ARC-AGI2 Capability Candidate Aggregator V1

## Repo / branch
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`

## Heads
- Actual preflight HEAD: `f2d490224845f18f9b9e54c562a45f18bdbb011a`
- Start HEAD: `f2d490224845f18f9b9e54c562a45f18bdbb011a`
- End HEAD: `1f7f5ec5d52b2e9daeabe90fbbeba7818a3c1a17`
- Commit status: committed

## Files added / changed
- `weslr/arc_agi2_capability_candidate_aggregator_v1.py`
- `weslr/tests/test_arc_agi2_capability_candidate_aggregator_v1.py`
- `docs/WESLR_ARC_AGI2_CAPABILITY_CANDIDATE_AGGREGATOR_V1.md`

## Aggregator summary
- Added a thin synthetic-only capability coordinator.
- It combines object/bbox and shape-geometry capability adapters.
- It deduplicates identical outputs before final top-2 emission.
- It uses deterministic fallback packets when no capability candidate survives.
- It preserves the existing ARC-AGI-2 top-2 attempt contract.

## Candidate source families
- `object_bbox`
- `shape_geometry`
- `fallback`

## Ranking behavior
- Train-fit candidates are preferred first.
- Higher candidate score is preferred next.
- Family priority is stable: object_bbox → shape_geometry → fallback.
- Trace labels remain compact and deterministic.
- Source adapter / source candidate ordering stays stable.

## Deduplication behavior
- Identical output grids are collapsed to a single kept candidate.
- Duplicate family/source labels are recorded in metadata.
- If a duplicate collapses the pool below two unique outputs, fallback fills the gap.

## Fallback behavior
- When no capability candidate matches, two safe deterministic fallback attempts are emitted.
- Fallback attempts remain metadata-safe and synthetic-only.
- Fallback behavior also fills missing slots when only one unique candidate exists.

## Exact-two-output status
- Passed.
- The aggregator always emits exactly two attempts.

## Synthetic test summary
- Object/bbox wins case: passed
- Shape geometry wins case: passed
- Dedupe case: passed
- Fallback case: passed
- Ranking stability: passed
- Enabled family switch: passed
- Trace safety: passed
- Contract compatibility: passed

## Limitations
- Synthetic-only lane.
- No public ARC ingestion.
- No Kaggle submission writes.
- No scoring claims.
- No large orchestration layer yet.
- No new mini-run script was added; the mini-suite helper inside the aggregator file was sufficient.

## Validation run
- `python -m py_compile` on changed Python files: passed
- Focused pytest for object/bbox, shape geometry, and aggregator: passed
- `git diff --check`: passed
- `python weslr/tests/release_gate_v1.py`: passed
- `./scripts/weslr_release_check.sh`: passed
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`: passed

## Readiness verdict
- `capability_candidate_aggregator_passed_ready_for_color_role_capability_lane`

## Next recommended lane
- Color-role capability lane, or another narrow family that can plug into the same aggregator spine.
