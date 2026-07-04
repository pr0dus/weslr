# WESLR ARC-AGI2 Hypothesis Engine + Shape Geometry Capability V1

## Repo / branch
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`

## Heads
- Actual preflight HEAD: `ceeb3728a3d0cd74732b326c9ffd6fd37ea663dd`
- Start HEAD: `ceeb3728a3d0cd74732b326c9ffd6fd37ea663dd`
- End HEAD: pending commit of this report
- Commit status: validation passed; report pending commit

## Files added / changed
- `weslr/arc_hypothesis_engine_v1.py`
- `weslr/arc_shape_geometry_v1.py`
- `weslr/arc_agi2_shape_geometry_candidate_adapter_v1.py`
- `weslr/tests/test_arc_hypothesis_engine_v1.py`
- `weslr/tests/test_arc_shape_geometry_v1.py`
- `weslr/tests/test_arc_agi2_shape_geometry_candidate_adapter_v1.py`
- `docs/WESLR_ARC_AGI2_HYPOTHESIS_ENGINE_SHAPE_GEOMETRY_CAPABILITY_V1.md`

## Hypothesis engine summary
- Added a small reusable `HypothesisCandidate` structure.
- Added deterministic train-fit scoring via exact-match execution across train pairs.
- Added deterministic ranking with accepted-first behavior and stable ordering.
- Trace data stays compact and metadata-only.

## Train-consistency behavior
- Candidates are accepted only when every train pair matches exactly.
- Mismatched train outputs are rejected.
- Rejection is explicit and deterministic.

## Shape canonicalization behavior
- Object masks can be normalized to origin.
- Canonical shape signatures compare shape independent of position.
- Rigid shape identity checks remain separate from canvas placement.

## Rotation / reflection behavior
- Supports rotate 90 / 180 / 270.
- Supports horizontal and vertical reflection.
- Supports translation while preserving shape.
- Rejects ragged grids, bool cells, ambiguous multi-object grids, and shape-changing outputs.

## Adapter integration behavior
- The shape-geometry adapter emits exactly two attempts.
- Top-ranked geometry candidate becomes attempt 1.
- Safe deterministic fallback is used when no candidate exists.
- Trace metadata avoids expected-output leakage.

## Synthetic test summary
- Hypothesis engine tests: passed
- Shape geometry tests: passed
- Geometry adapter tests: passed
- Exact-two-output contract: passed

## Limitations
- Synthetic-only capability lane.
- No public ARC ingestion.
- No scoring claims.
- No Kaggle submission writes.
- No provider/model/payment calls.
- No broad orchestration layer.

## Aggregator
- Not added.
- Kept out to keep the lane small and low-risk.

## Next recommended lane
- Capability aggregator lane, or a color-role capability lane if the next synthetic family is narrower.

## Validation run
- `python -m py_compile` on changed Python files: passed
- Focused pytest: passed
- `git diff --check`: passed
- `python weslr/tests/release_gate_v1.py`: passed
- `./scripts/weslr_release_check.sh`: passed
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`: passed

## Readiness verdict
- `hypothesis_engine_shape_geometry_capability_passed_ready_for_capability_aggregator_or_color_role_lane`
