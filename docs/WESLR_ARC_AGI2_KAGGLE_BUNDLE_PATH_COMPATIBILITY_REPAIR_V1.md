# WESLR ARC-AGI-2 Kaggle Bundle Path Compatibility Repair V1

## Metadata

| Field | Value |
|-------|-------|
| Repository | `/data/data/com.termux/files/home/weslr-pr47-clean` |
| Branch | `main` |
| Start HEAD | `e53544e647a6ebaff7ad4f0300c4699aaf9482b6` |
| End HEAD | (committed below) |
| Preflight match | YES |
| Lane type | Bundle path compatibility repair |
| Previous lane | `WESLR_ARC_AGI2_KAGGLE_NOTEBOOK_BUNDLE_REVIEW_V1` |
| Previous verdict | `kaggle_notebook_bundle_review_v1_passed_ready_for_kaggle_notebook_bundle_dry_run_lane` |

## Preflight HEAD Verification

| Check | Result |
|-------|--------|
| Expected HEAD prefix | `e53544e6` |
| Actual HEAD | `e53544e647a6ebaff7ad4f0300c4699aaf9482b6` |
| Match | YES |

## Files Changed

| File | Change |
|------|--------|
| `src/weslr_arc_solver/portable_solver.py` | Modified — path resolution now supports both `weslr/` and `weslr_solver/` |
| `tests/test_kaggle_bundle_path_compatibility_v1.py` | New — 13 focused tests for path compatibility |

## Old Path Behavior

The `_resolve_weslr_repo_root()` function only checked for a `weslr/` directory:

1. `WESLR_REPO_ROOT` env var → check for `$WESLR_REPO_ROOT/weslr/`
2. Sibling layout → check for `../weslr/`
3. Grandparent layout → check for `../../weslr/`

The `_ensure_weslr_imports()` function added only `$WESLR_REPO_ROOT` and `$WESLR_REPO_ROOT/weslr/` to `sys.path`.

## New Path Behavior

### New helper: `_find_solver_dir(root)`

Checks for any known solver directory name in the given root:

```python
_SOLVER_DIR_NAMES = ("weslr", "weslr_solver")
```

Returns the full path to the first found solver directory, or `None`.

### Updated: `_resolve_weslr_repo_root()`

Uses `_find_solver_dir()` instead of hardcoded `"weslr"`:

1. `WESLR_REPO_ROOT` env var → check for any solver dir in `$WESLR_REPO_ROOT`
2. Sibling layout → check for any solver dir in `../`
3. Grandparent layout → check for any solver dir in `../../`

Error message now lists both supported directory names.

### Updated: `_ensure_weslr_imports()`

- Adds the repo root to `sys.path`
- Adds the solver directory to `sys.path`
- If the solver directory is not named `weslr` (e.g., `weslr_solver/`), creates a `sys.modules["weslr"]` alias so that `from weslr.xxx import ...` works regardless of the actual directory name

## Supported Layouts

| Layout | Directory | Works? | Notes |
|--------|-----------|--------|-------|
| Repo/dev | `weslr/` | ✅ | Existing behavior preserved |
| Kaggle bundle | `weslr_solver/` | ✅ | New — module alias created automatically |
| Both present | `weslr/` preferred | ✅ | `weslr/` checked first in `_SOLVER_DIR_NAMES` |

## Tests Added/Updated

### New test file: `tests/test_kaggle_bundle_path_compatibility_v1.py`

13 tests:

| # | Test | What it verifies |
|---|------|-----------------|
| 1 | `test_resolve_weslr_layout` | `_resolve_weslr_repo_root` finds `weslr/` via env var |
| 2 | `test_resolve_weslr_solver_layout` | `_resolve_weslr_repo_root` finds `weslr_solver/` via env var |
| 3 | `test_resolve_missing_solver_dir` | Error message mentions both dir names |
| 4 | `test_resolve_no_env_var_sibling_weslr` | Sibling detection works for `weslr/` |
| 5 | `test_resolve_no_env_var_sibling_weslr_solver` | Sibling detection works for `weslr_solver/` |
| 6 | `test_find_solver_dir_weslr` | `_find_solver_dir` finds `weslr/` |
| 7 | `test_find_solver_dir_weslr_solver` | `_find_solver_dir` finds `weslr_solver/` |
| 8 | `test_find_solver_dir_prefers_weslr` | `weslr/` preferred when both exist |
| 9 | `test_find_solver_dir_nonexistent` | Returns `None` when no solver dir |
| 10 | `test_no_termux_path_dependency_in_path_resolution` | No hardcoded Termux paths in path resolution |
| 11 | `test_no_public_source_path_dependency_in_path_resolution` | No hardcoded public source paths in path resolution |
| 12 | `test_no_internet_dependency` | No network imports in portable_solver.py |
| 13 | `test_solver_dir_names_constant` | `_SOLVER_DIR_NAMES` contains both names in correct order |

### Existing tests still pass

| Suite | Tests | Result |
|-------|-------|--------|
| `test_portable_solver_v1.py` | 25 | ✅ All pass |
| `test_kaggle_format_v1.py` | 15 | ✅ All pass |
| `test_kaggle_bundle_path_compatibility_v1.py` | 13 | ✅ All pass |
| **Total** | **53** | **✅ All pass** |

## Smoke Test Result

Ran `scripts/run_kaggle_format_submission_dry_run_v1.py --bare`:

| Check | Result |
|-------|--------|
| Exit code | 0 ✅ |
| Tasks | 120 ✅ |
| Test inputs | 172 ✅ |
| Valid | True ✅ |
| Metadata clean | True ✅ |
| Forbidden clean | True ✅ |
| No solution read | True ✅ |
| No scoring | True ✅ |
| No Kaggle submission | True ✅ |

## Canonical Hash Check

| Check | Result |
|-------|--------|
| Expected hash | `78f295d33a665325393ee03bd40cf0816beccbd32787d321522f180a2a3eb7c9` |
| Actual hash | `78f295d33a665325393ee03bd40cf0816beccbd32787d321522f180a2a3eb7c9` |
| Match | **YES** ✅ |

The canonical output hash is preserved. The path compatibility repair did not change solver behavior.

## Public-Data Boundary Status

| Check | Status |
|-------|--------|
| Public challenge JSON parsed | YES (in dry run) |
| Solution files opened | **NO** |
| Scoring occurred | **NO** |
| Kaggle submission occurred | **NO** |
| Public data copied into repo | NO |
| Generated outputs committed | NO |

## No-Solution-Read Statement

**No solution files were opened during this repair lane.**

## No-Scoring Statement

**No scoring occurred during this repair lane.**

## No-Kaggle-Submission Statement

**No Kaggle submission occurred during this repair lane.**

## Remaining Risks

1. **Module alias approach**: The `sys.modules["weslr"]` alias for `weslr_solver/` is a runtime workaround. It works for the current import chain but may not handle all edge cases (e.g., subpackage imports within the solver modules). The bundle dry run should verify this.

2. **Solver module count**: The 26 required solver modules were identified by static analysis. If the solver chain imports additional modules at runtime (e.g., conditional imports), the bundle may be incomplete. The bundle dry run should catch this.

3. **Kaggle environment**: The module alias approach has not been tested in a real Kaggle environment. The bundle dry run should simulate this.

## Next Recommended Lane

`WESLR_ARC_AGI2_KAGGLE_NOTEBOOK_BUNDLE_DRY_RUN_V1`

This lane should:
- Build a temporary Kaggle-like directory layout outside repo
- Copy the 12 staging modules + 26 solver modules into `weslr_solver/`
- Create a notebook entry point
- Set Kaggle-like env vars
- Run the notebook-equivalent script from outside repo
- Use public eval challenge JSON
- Write `submission.json`
- Validate canonical output hash: `78f295d33a665325393ee03bd40cf0816beccbd32787d321522f180a2a3eb7c9`
- No solution reads
- No scoring
- No Kaggle submission

## Readiness Verdict

```
kaggle_bundle_path_compatibility_repair_v1_passed_ready_for_kaggle_notebook_bundle_dry_run_lane
```

### Criteria met:
- ✅ Both `weslr/` and `weslr_solver/` layouts work
- ✅ Existing staging/package smoke tests pass (25 tests)
- ✅ Kaggle-format tests pass (15 tests)
- ✅ New path compatibility tests pass (13 tests)
- ✅ Canonical output hash preserved (`78f295d3...`)
- ✅ No public solution files are opened
- ✅ No scoring occurs
- ✅ No Kaggle submission occurs
- ✅ Source-repo health check passes (6/6 mandatory)
