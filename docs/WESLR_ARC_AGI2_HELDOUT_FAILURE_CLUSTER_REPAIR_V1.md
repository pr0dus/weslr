# ARC-AGI2 Held-out Failure Cluster Repair V1

## Repo
- `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`

## Heads
- Actual preflight HEAD: `af5086713ad0abcf5d3296b048c58b5ae21c93e9`
- Start HEAD: `af5086713ad0abcf5d3296b048c58b5ae21c93e9`
- End HEAD: `126e46d53432ae98abb90b0435578c62ee2e2f22`
- Commit status: code/tests committed; report stamped in workspace after final HEAD and not recommitted

## Baseline
Previous benchmark:
- dev: 81 tasks, 36 solved, 45 unsolved, 39 fallback-only, 6 exceptions
- heldout: 135 tasks, 60 solved, 75 unsolved, 65 fallback-only, 10 exceptions
- exact-two-output: pass
- deterministic replay: pass
- expected-output isolation: pass
- split disjointness: pass

## Diagnosis
- `crop_largest_object`: `ValueError: selected_color_not_found`
- `select_largest_object`: `ValueError: selected_color_not_found`
- Category: adapter/capability bug in synthetic solver execution path, not generator or evaluator
- Expected output: correct
- Solver-visible input excludes expected output: yes

## Fix summary
- Hardened `weslr/arc_object_bbox_solver_v1.py` so candidate branches are isolated and cannot abort the solver.
- Hardened `weslr/arc_count_quantity_relations_v1.py` so test-input candidate execution skips exceptions instead of propagating them.
- Added focused repair coverage for `crop_largest_object` and `select_largest_object`.
- Added external run logging outside the repo.

## Files changed
- `weslr/arc_object_bbox_solver_v1.py`
- `weslr/arc_count_quantity_relations_v1.py`
- `weslr/tests/test_arc_heldout_synthetic_discovery_benchmark_v1.py`
- `docs/WESLR_ARC_AGI2_HELDOUT_FAILURE_CLUSTER_REPAIR_V1.md`

## Tests added/updated
- Added a focused benchmark test that exercises `crop_largest_object` and `select_largest_object` without exceptions.
- Existing benchmark suite retained exact-two-output, deterministic replay, and expected-output isolation checks.

## Validation
- `python -m py_compile weslr/arc_object_bbox_solver_v1.py weslr/arc_count_quantity_relations_v1.py weslr/arc_heldout_synthetic_discovery_benchmark_v1.py weslr/tests/test_arc_heldout_synthetic_discovery_benchmark_v1.py scripts/run_arc_heldout_synthetic_discovery_benchmark_v1.py`
- `python -m pytest -q weslr/tests/test_arc_heldout_synthetic_discovery_benchmark_v1.py`
- `python -m pytest -q weslr/tests/test_arc_synthetic_discovery_task_generator_v1.py weslr/tests/test_arc_synthetic_discovery_eval_v1.py`
- `python -m pytest -q weslr/tests/test_arc_universal_family_runner_v1.py weslr/tests/test_arc_compositional_executor_v1.py`
- `git diff --check`
- `python weslr/tests/release_gate_v1.py`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

## Benchmark rerun
Command:
`python scripts/run_arc_heldout_synthetic_discovery_benchmark_v1.py --dev-seed 2435 --heldout-seed 82435 --tasks-per-family-dev 3 --tasks-per-family-heldout 5 --include-adversarial --include-compositions`

After repair:
- dev: 81 tasks, 42 solved, 39 unsolved, 39 fallback-only, 0 exceptions
- heldout: 135 tasks, 70 solved, 65 unsolved, 65 fallback-only, 0 exceptions
- exact-two-output: pass
- deterministic replay: pass
- expected-output isolation: pass
- split disjointness: pass

## Before/after
- dev solved: 36 → 42
- heldout solved: 60 → 70
- exceptions: 6 → 0 on dev; 10 → 0 on heldout
- fallback-only: 39 → 39 on dev; 65 → 65 on heldout
- exact-two-output: pass → pass
- deterministic replay: pass → pass
- expected-output isolation: pass → pass

## Event/log artifacts
- `/data/data/com.termux/files/home/weslr-arc-run-logs/2026-07-05_arc_heldout_failure_cluster_repair_v1.log`
- `/data/data/com.termux/files/home/weslr-arc-run-logs/2026-07-05_arc_heldout_failure_cluster_repair_v1_summary.json`

## Status of required checks
- exact-two-output: pass
- deterministic replay: pass
- expected-output isolation: pass
- heldout split disjointness: pass
- source-repo health check: pass

## Limitations
- This lane only removes the first exception cluster.
- Fallback-only families remain fallback-only and were not broadly expanded.
- No public ARC data was read, scored, or submitted.

## Next recommended lane
- Fallback-cluster repair for the remaining synthetic-only families, starting with the lowest-risk fallback-only branches.

## Verdict
- `heldout_failure_cluster_repair_v1_passed_ready_for_fallback_cluster_repair_lane`
