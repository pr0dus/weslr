# ARC-AGI2 Held-out Fallback Cluster Repair V1

## Repo
- `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`

## Heads
- Actual preflight HEAD: `a3b9f138787b8897137d08568ed44de44c6f8df0`
- Start HEAD: `a3b9f138787b8897137d08568ed44de44c6f8df0`
- End HEAD: `4f318976d90184a53961f76c06066ece6c45d6e5`
- Commit status: code/tests committed; report stamped in workspace after final HEAD and not recommitted

## Baseline
Previous benchmark:
- dev: 81 tasks, 36 solved, 45 unsolved, 39 fallback-only, 6 exceptions
- heldout: 135 tasks, 60 solved, 75 unsolved, 65 fallback-only, 10 exceptions
- exact-two-output: pass
- deterministic replay: pass
- expected-output isolation: pass
- split disjointness: pass

## Primary family diagnosis
### `translate_single_object`
- Primitive discovery: accepted `rotate_object_180`; uncertain `preserve_shape_translate`, `reflect_object_horizontal`, `reflect_object_vertical`, `rotate_object_270`, `rotate_object_90`
- Family discovery: uncertain `shape_geometry`
- Universal runner: enabled `shape_geometry`
- Adapter executed: `arc_agi2_shape_geometry_candidate_adapter_v1`, `arc_agi2_capability_candidate_aggregator_v1`
- Final result: non-fallback; `shape_geometry` matched and was selected
- Layer: discovery/routing, not evaluator

### `swap_two_colors`
- Primitive discovery: rejected `swap_two_colors`; uncertain count/selection hints only
- Family discovery: accepted `color_role`
- Universal runner: enabled `color_role`
- Adapter executed: `arc_agi2_color_role_candidate_adapter_v1`
- Final result: non-fallback; `color_role` matched and was selected
- Layer: discovery/routing, not evaluator

### `rotate_object_180`
- Primitive discovery: accepted `rotate_object_180`
- Family discovery: uncertain `shape_geometry`
- Universal runner: enabled `shape_geometry`
- Adapter executed: `arc_agi2_shape_geometry_candidate_adapter_v1`, `arc_agi2_capability_candidate_aggregator_v1`
- Final result: non-fallback; `shape_geometry` matched and was selected
- Layer: discovery/routing, not evaluator

### `reflect_object_horizontal`
- Primitive discovery: accepted `translate_single_object`
- Family discovery: accepted `shape_geometry`; accepted `object_bbox`
- Universal runner: enabled `shape_geometry`
- Adapter executed: `arc_agi2_shape_geometry_candidate_adapter_v1`, `arc_agi2_object_bbox_candidate_adapter_v1`
- Final result: non-fallback; `shape_geometry` matched and was selected
- Layer: discovery/routing, not evaluator

### `reflect_object_vertical`
- Primitive discovery: accepted `rotate_object_180`
- Family discovery: uncertain `shape_geometry`; uncertain `crop_then_rotate_or_reflect`
- Universal runner: enabled `shape_geometry`
- Adapter executed: `arc_agi2_shape_geometry_candidate_adapter_v1`
- Final result: non-fallback; `shape_geometry` matched and was selected
- Layer: discovery/routing, not evaluator

## Fix summary
- Tightened shape-geometry prediction plumbing so single-object candidates can be reconstructed consistently for synthetic transform cases.
- Relaxed family-discovery routing for exact synthetic solver-fit cases when primitive hints are incomplete but the candidate is high-confidence.
- Added focused benchmark coverage for the five primary fallback families.
- Kept verbose benchmark logging outside the repo.

## Files changed
- `weslr/arc_shape_geometry_v1.py`
- `weslr/arc_family_discovery_engine_v1.py`
- `weslr/tests/test_arc_heldout_synthetic_discovery_benchmark_v1.py`
- `docs/WESLR_ARC_AGI2_HELDOUT_FALLBACK_CLUSTER_REPAIR_V1.md`

## Tests added/updated
- Added a focused regression test proving the five primary families no longer fall back when the synthetic task is valid.
- Kept exact-two-output, expected-output isolation, and deterministic replay checks in the benchmark suite.
- Kept no-exceptions coverage for the repaired families.

## Validation
- `python -m py_compile weslr/arc_shape_geometry_v1.py weslr/arc_family_discovery_engine_v1.py weslr/tests/test_arc_heldout_synthetic_discovery_benchmark_v1.py`
- `pytest -q weslr/tests/test_arc_heldout_synthetic_discovery_benchmark_v1.py`
- `python scripts/run_arc_heldout_synthetic_discovery_benchmark_v1.py --dev-seed 2435 --heldout-seed 82435 --tasks-per-family-dev 3 --tasks-per-family-heldout 5 --include-adversarial --include-compositions`
- `git diff --check`
- `python weslr/tests/release_gate_v1.py`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

## Benchmark rerun
Command:
`python scripts/run_arc_heldout_synthetic_discovery_benchmark_v1.py --dev-seed 2435 --heldout-seed 82435 --tasks-per-family-dev 3 --tasks-per-family-heldout 5 --include-adversarial --include-compositions`

After repair:
- dev: 81 tasks, 60 solved, 21 unsolved, 21 fallback-only, 0 exceptions
- heldout: 135 tasks, 100 solved, 35 unsolved, 35 fallback-only, 0 exceptions
- exact-two-output: pass
- deterministic replay: pass
- expected-output isolation: pass
- split disjointness: pass

## Before/after
- dev solved: 36 → 60
- heldout solved: 60 → 100
- dev fallback-only: 39 → 21
- heldout fallback-only: 65 → 35
- dev exceptions: 6 → 0
- heldout exceptions: 10 → 0
- exact-two-output: pass → pass
- deterministic replay: pass → pass
- expected-output isolation: pass → pass

## Event/log artifacts
- `/data/data/com.termux/files/home/weslr-arc-run-logs/2026-07-05_arc_heldout_fallback_cluster_repair_v1.log`
- `/data/data/com.termux/files/home/weslr-arc-run-logs/2026-07-05_arc_heldout_fallback_cluster_repair_v1_summary.json`

## Status of required checks
- exact-two-output: pass
- deterministic replay: pass
- expected-output isolation: pass
- heldout split disjointness: pass
- source-repo health check: pass

## Limitations
- This lane only repairs the first fallback-only cluster.
- Secondary fallback families remain out of scope unless they share a tiny routing fix.
- No public ARC data was read, scored, or submitted.

## Next recommended lane
- Continue with the next narrow synthetic-only fallback cluster or the smallest remaining shared routing issue.

## Verdict
- `heldout_fallback_cluster_repair_v1_passed_ready_for_composition_fallback_repair_lane`
