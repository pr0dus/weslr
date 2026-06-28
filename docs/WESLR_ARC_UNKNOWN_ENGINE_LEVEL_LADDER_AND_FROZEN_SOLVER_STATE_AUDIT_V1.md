# WESLR ARC UNKNOWN ENGINE LEVEL LADDER AND FROZEN SOLVER STATE AUDIT V1

## Recovery status
This document is a **recovered / reconstructed current-branch artifact** created on branch `occ-discovery-doctrine-implementation-20260613`.

- Recovered on current branch: **yes**
- Original cited commit `98eed788b2a76ba2b41276ea41fc45c5694fa456` present locally: **no**
- Historical provenance for an original prior artifact can be proven: **no**
- Recovery basis: current local code inspection, current local synthetic smoke output, existing committed smoke-metrics repair/review docs, and owner-provided receipt values where explicitly marked

This artifact does **not** claim to be the original missing historical doc. It records the current valid branch state only.

## Boundary statement
- Internal synthetic-only ARC-style work: **yes**
- Public ARC data used: **no**
- Kaggle data used: **no**
- Official scoring claimed: **no**
- ARC-AGI-1 performance claimed: **no**
- ARC-AGI-2 performance claimed: **no**

## Current branch audit
### Generator found from current branch
**Yes**

Observed current-branch generator surface:
- `weslr/arc_style_synthetic_task_generators.py`
- imported by `weslr/arc_style_synthetic_solver_suite.py`
- current suite family summary exposes 12 synthetic families / ladder levels:
  - `border_frame`
  - `complete_symmetry`
  - `copy_grid`
  - `extract_largest_object`
  - `fill_region`
  - `line_completion`
  - `move_single_object`
  - `object_count_to_pattern`
  - `recolor_symbol`
  - `reflect_object_horizontal_or_vertical`
  - `remove_background_noise`
  - `rotate_object_90`

### Solver / runner found from current branch
**Yes**

Observed current-branch runner surface:
- `weslr/arc_style_grid_solver_dry_run.py`
- `weslr/arc_style_synthetic_solver_suite.py`
- bounded dry-run path invoked through `run_arc_style_synthetic_solver_suite_v1()`

### Synthetic smoke possible from current branch
**Yes**

Known safe runner command:
```bash
python -c "import sys; sys.path.append('/data/data/com.termux/files/home/weslr-pr47-clean'); from weslr.arc_style_synthetic_solver_suite import run_arc_style_synthetic_solver_suite_v1; print(run_arc_style_synthetic_solver_suite_v1())"
```

Equivalent validated local command form used during recovery:
```bash
python3 - <<'PY'
import sys
sys.path.append('/data/data/com.termux/files/home/weslr-pr47-clean')
from weslr.arc_style_synthetic_solver_suite import run_arc_style_synthetic_solver_suite_v1
print(run_arc_style_synthetic_solver_suite_v1())
PY
```

## Current recovered smoke signal
Recovered from current branch live output:
- Generated ladder levels / synthetic families: **12**
- Generated tasks: **36**
- Attempted tasks: **36**
- Top-2 packets evaluated: **48**
- Task exact count: **31**
- Task exact rate: **31 / 36 = 0.8611111111111112**
- Packet exact count: **41**
- Packet exact rate: **41 / 48 = 0.8541666666666666**
- Packet partial count: **3**
- Packet unsupported count: **4**
- Failed count: **0**
- Threshold basis: **`task_exact_rate`**
- Internal pass 85: **true**
- Level hardening allowed flag in current code: **true**

## Provenance limitation note
- The earlier cited `98eed...` commit is not present locally.
- The original referenced audit/smoke artifacts were missing from this branch and unreachable in local history.
- Therefore this audit is recorded as a **current-branch recovery artifact**, not as proven historical recovery from the missing commit.
- The current branch state is strong enough to describe the live generator/runner surface, but not strong enough to assert exact historical wording or original receipt ancestry.

## Recommended next lane after recovery
`ADD_ARC_UNKNOWN_ENGINE_SMOKE_METRICS_COVERAGE_TESTS_V1`

Reason:
- branch documentation can now be reconstructed on the current valid branch
- metric policy coverage is still too thin for Smoke V2 / hardening decisions
- task-level threshold protection should be hardened with stronger negative-case tests before another smoke promotion step
