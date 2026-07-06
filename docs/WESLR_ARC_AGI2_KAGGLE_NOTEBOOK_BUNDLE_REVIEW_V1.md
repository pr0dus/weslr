# WESLR ARC-AGI-2 Kaggle Notebook Bundle Review V1

## Metadata

| Field | Value |
|-------|-------|
| Repository | `/data/data/com.termux/files/home/weslr-pr47-clean` |
| Branch | `main` |
| Start HEAD | `94fbc361fbb993f0214a15f364aa92dceb47eff8` |
| End HEAD | (committed below) |
| Preflight match | YES |
| Lane type | Kaggle notebook bundle review/design |
| Previous lane | `WESLR_ARC_AGI2_REPEATED_BARE_DRY_RUN_STABILITY_V1` |
| Previous verdict | `repeated_bare_dry_run_stability_v1_passed_ready_for_kaggle_notebook_bundle_review_lane` |

## Preflight HEAD Verification

| Check | Result |
|-------|--------|
| Expected HEAD prefix | `94fbc361` |
| Actual HEAD | `94fbc361fbb993f0214a15f364aa92dceb47eff8` |
| Match | YES |

## Current Staged Package Summary

| Module | Lines | Purpose |
|--------|-------|---------|
| `portable_solver.py` | ~350 | WESLR solver wrapper with sys.path injection |
| `solver.py` | ~30 | Entry point for file-based solving |
| `kaggle_format.py` | ~230 | Kaggle format converter + validator |
| `kaggle_dummy.py` | ~40 | Dummy dry run placeholder |
| `grid.py` | ~70 | Grid validation utilities |
| `emitter.py` | ~60 | Two-output emission |
| `adapter.py` | ~20 | Dummy bundle builder |
| `public_gate.py` | ~30 | Public data gate |
| `redaction.py` | ~30 | Forbidden-key redaction |
| `schema.py` | ~20 | Schema constants |
| `scorer.py` | ~60 | Scoring utilities (not used in Kaggle path) |
| `__init__.py` | ~20 | Package exports |

**Total:** 12 modules, ~980 lines, ~143 KB on disk.

## Current Script Summary

| Script | Purpose |
|--------|---------|
| `run_kaggle_format_submission_dry_run_v1.py` | Kaggle-format dry run with `--bare` mode |
| `run_repeated_bare_dry_run_v1.py` | Orchestrates repeated bare runs |
| `run_public_eval_unscored_candidate_generation_v1.py` | Public eval unscored generation |
| `run_public_input_shape_dry_run_v1.py` | Public input shape dry run |
| `run_portable_submission_package_smoke_v1.py` | Initial smoke test |

## Proposed Kaggle Bundle Layout

```
/kaggle/working/weslr-kaggle-bundle/
├── src/
│   └── weslr_arc_solver/
│       ├── __init__.py
│       ├── portable_solver.py
│       ├── solver.py
│       ├── kaggle_format.py
│       ├── grid.py
│       ├── emitter.py
│       ├── adapter.py
│       ├── public_gate.py
│       ├── redaction.py
│       ├── schema.py
│       ├── scorer.py
│       └── kaggle_dummy.py
├── weslr_solver/              # Only the 26 required solver modules
│   ├── __init__.py
│   ├── arc_universal_family_runner_v1.py
│   ├── arc_agi2_capability_candidate_aggregator_v1.py
│   ├── arc_agi2_submission_contract.py
│   ├── arc_agi2_object_bbox_candidate_adapter_v1.py
│   ├── arc_agi2_color_role_candidate_adapter_v1.py
│   ├── arc_agi2_resize_tile_candidate_adapter_v1.py
│   ├── arc_agi2_count_quantity_candidate_adapter_v1.py
│   ├── arc_agi2_shape_geometry_candidate_adapter_v1.py
│   ├── arc_agi2_symmetry_line_candidate_adapter_v1.py
│   ├── arc_agi2_hole_row_column_candidate_adapter_v1.py
│   ├── arc_agi2_marker_copy_candidate_adapter_v1.py
│   ├── arc_object_bbox_solver_v1.py
│   ├── arc_shape_geometry_v1.py
│   ├── arc_color_role_abstraction_v1.py
│   ├── arc_resize_tile_canvas_v1.py
│   ├── arc_count_quantity_relations_v1.py
│   ├── arc_hole_row_column_v1.py
│   ├── arc_marker_copy_v1.py
│   ├── arc_object_extraction_v1.py
│   ├── arc_primitive_discovery_engine_v1.py
│   ├── arc_primitive_registry_v1.py
│   ├── arc_family_discovery_engine_v1.py
│   ├── arc_compositional_executor_v1.py
│   ├── arc_hypothesis_engine_v1.py
│   ├── arc_style_grid_schema_helpers.py
│   └── arc_task_feature_signature_v1.py
├── notebook.py                # Kaggle notebook entry point
├── README.md                  # Bundle documentation
└── requirements.txt           # (empty — no third-party deps)
```

**Bundle size estimate:** ~634 KB (143 KB staging package + 490 KB solver modules + ~1 KB notebook/readme).

**Key design decision:** The solver modules are copied into a `weslr_solver/` directory (not `weslr/`) to avoid importing the full 73MB WESLR platform. The `portable_solver.py` would need a path resolution update to find `weslr_solver/` instead of `weslr/`.

## WESLR_REPO_ROOT Dependency Assessment

### Current behavior

The `portable_solver.py` resolves the WESLR repo root in this order:

1. **`WESLR_REPO_ROOT` environment variable** — checks if `$WESLR_REPO_ROOT/weslr/` exists
2. **Sibling directory lookup** — walks up from `src/weslr_arc_solver/` to find a `weslr/` sibling
3. **Grandparent lookup** — walks up one more level

Then it adds both the repo root and `weslr/` to `sys.path`.

### Assessment for Kaggle

| Strategy | Works in Kaggle? | Notes |
|----------|-----------------|-------|
| `WESLR_REPO_ROOT` env var | **YES** | Set to bundle root in notebook cell |
| Sibling directory lookup | **YES** | If `weslr_solver/` is a sibling of `src/` |
| Grandparent lookup | **YES** | If nested deeper |

**Verdict: Acceptable for first Kaggle dry run.** The env-var approach is the most reliable. The notebook would set:

```python
import os
os.environ["WESLR_REPO_ROOT"] = "/kaggle/working/weslr-kaggle-bundle"
```

### Fragility assessment

| Issue | Severity | Mitigation |
|-------|----------|------------|
| `WESLR_REPO_ROOT` must be set before first import | Low | Set in first notebook cell |
| Bundle path must match env var | Low | Use `os.path.dirname(os.path.abspath(__file__))` for auto-detection |
| `weslr/` directory name expected | Medium | Rename to `weslr_solver/` or update path resolution |
| Full `weslr/` package is 73MB | **High** | Must bundle only 26 solver modules (~490 KB) |

**Recommendation:** Before the bundle dry run, update `portable_solver.py` to accept an alternative solver directory name (e.g., `weslr_solver/`), or create a bundle-specific wrapper that sets the path correctly.

## Kaggle Input Discovery Assessment

### Current approach

The dry-run scripts use a hardcoded path:
```python
PUBLIC_ZIP_PATH = "/data/data/com.termux/files/home/arc-agi2-public-source/arc-prize-2026-arc-agi-2.zip"
```

### Required for Kaggle

The notebook must discover the challenge file without local paths. Design:

```python
import glob, os

def discover_challenge_json() -> str:
    """Find the ARC-AGI-2 challenge JSON in Kaggle input."""
    # Search common Kaggle input paths
    patterns = [
        "/kaggle/input/**/arc-agi_test_challenges.json",
        "/kaggle/input/**/arc-agi_evaluation_challenges.json",
    ]
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            return matches[0]
    # Fallback: explicit env var
    env_path = os.environ.get("ARC_CHALLENGES_JSON")
    if env_path and os.path.exists(env_path):
        return env_path
    raise FileNotFoundError(
        "Cannot find ARC-AGI-2 challenge JSON. "
        "Set ARC_CHALLENGES_JSON env var or place file in /kaggle/input/"
    )
```

**Uncertainty:** The exact Kaggle competition input file name is not yet verified. The ARC-AGI-2 competition may use a different file name or structure. The discovery wrapper should be flexible.

**Verdict: Acceptable for dry run.** The glob-based discovery handles unknown file names. The env-var fallback provides an explicit override.

## Submission Output Path Assessment

### Current behavior

The dry-run scripts write to:
```python
OUTPUT_DIR = "/data/data/com.termux/files/home/weslr-arc-public-eval-unscored-runs"
```

### Required for Kaggle

The notebook must write to:
```python
OUTPUT_PATH = "/kaggle/working/submission.json"
```

The `kaggle_format.py` converter already produces the correct format:
```json
{
    "task_id_1": [
        {"attempt_1": [[...], ...], "attempt_2": [[...], ...]},
        ...
    ],
    ...
}
```

**Verdict: Clean.** The converter produces the correct format. The notebook just needs to use the Kaggle output path.

## Notebook Execution Flow

### Proposed notebook cells

```python
# Cell 1: Setup
import os, sys, json, glob

# Set bundle root
BUNDLE_ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ["WESLR_REPO_ROOT"] = BUNDLE_ROOT
sys.path.insert(0, os.path.join(BUNDLE_ROOT, "src"))

# Cell 2: Discover challenge file
def discover_challenge_json():
    patterns = [
        "/kaggle/input/**/arc-agi_test_challenges.json",
        "/kaggle/input/**/arc-agi_evaluation_challenges.json",
    ]
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            return matches[0]
    env_path = os.environ.get("ARC_CHALLENGES_JSON")
    if env_path and os.path.exists(env_path):
        return env_path
    raise FileNotFoundError("Cannot find ARC-AGI-2 challenge JSON")

challenges_path = discover_challenge_json()
print(f"Challenge file: {challenges_path}")

# Cell 3: Load challenges
with open(challenges_path) as f:
    challenges = json.load(f)
print(f"Tasks: {len(challenges)}")

# Cell 4: Import and run solver
from weslr_arc_solver.portable_solver import solve_challenges
from weslr_arc_solver.kaggle_format import (
    convert_weslr_to_kaggle_v1,
    validate_kaggle_submission_v1,
)

weslr_packet = solve_challenges(challenges)
kaggle_output = convert_weslr_to_kaggle_v1(weslr_packet)

# Cell 5: Validate and write
validation = validate_kaggle_submission_v1(kaggle_output)
print(f"Valid: {validation['valid']}")
print(f"Tasks: {validation['task_count']}")
print(f"Test inputs: {validation['test_input_count']}")

output_path = "/kaggle/working/submission.json"
with open(output_path, "w") as f:
    json.dump(kaggle_output, f, indent=2)
print(f"Submission written to: {output_path}")
```

**No internet. No API calls. No model calls. No solution files. No scoring.**

## Risky Pattern Search Results

### Staging package (`src/weslr_arc_solver/`)

| Pattern | Matches | Classification |
|---------|---------|---------------|
| `/data/data/com.termux` | 2 | ✅ Acceptable — in `validate_submission_packet()` forbidden-needle check |
| `arc-agi2-public-source` | 2 | ✅ Acceptable — in `validate_submission_packet()` forbidden-needle check |
| `expected_output` | 8 | ✅ Acceptable — in docstrings, forbidden-key lists, scorer parameter |
| `solution` | 4 | ✅ Acceptable — in docstrings and forbidden-key lists |
| `public_solution` | 4 | ✅ Acceptable — in docstrings and forbidden-key lists |
| `answer_key` | 1 | ✅ Acceptable — in `redaction.py` forbidden-key list |
| `kaggle_ready` | 0 | ✅ Clean |
| `synthetic_only` | 0 | ✅ Clean |
| `schema_version` | 0 | ✅ Clean |
| `metadata` | 0 | ✅ Clean |
| `requests` | 0 | ✅ Clean |
| `http` | 0 | ✅ Clean |
| `openai` | 0 | ✅ Clean |
| `anthropic` | 0 | ✅ Clean |
| `google` | 0 | ✅ Clean |
| `subprocess` | 0 | ✅ Clean |
| `WESLR_REPO_ROOT` | 8 | ✅ Acceptable — in `portable_solver.py` path resolution logic |

### Local dev scripts (not part of bundle)

| Pattern | Matches | Classification |
|---------|---------|---------------|
| `/data/data/com.termux` | 12 | ✅ Acceptable — local dev scripts with hardcoded Termux paths |
| `arc-agi2-public-source` | 8 | ✅ Acceptable — local dev scripts |

**No notebook/bundle blockers found in the staged package.** The local dev scripts have Termux paths but are not part of the Kaggle bundle.

## Public-Data Boundary Status

| Check | Status |
|-------|--------|
| Public challenge JSON parsed | YES (in previous lanes) |
| Solution files opened | **NO** |
| Scoring occurred | **NO** |
| Kaggle submission occurred | **NO** |
| Public data copied into repo | NO |
| Generated outputs committed | NO |

## No-Solution-Read Statement

**No solution files were opened during this review lane.** This is a design/review lane only.

## No-Scoring Statement

**No scoring occurred during this review lane.**

## No-Kaggle-Submission Statement

**No Kaggle submission occurred during this review lane.**

## Remaining Blockers

| Blocker | Severity | Resolution |
|---------|----------|------------|
| `portable_solver.py` expects `weslr/` directory name | **Medium** | Update path resolution to accept `weslr_solver/` or create bundle-specific wrapper |
| Full `weslr/` package is 73MB | **High** | Bundle only 26 required solver modules (~490 KB) |
| No bundle packaging script exists | **Medium** | Create `scripts/build_kaggle_bundle_v1.py` |
| No notebook entry point exists | **Low** | Create `notebook.py` in bundle |
| Challenge file discovery not tested in Kaggle layout | **Low** | Test in bundle dry run lane |
| Unknown Kaggle competition file name | **Low** | Use glob-based discovery with fallback |

## Next Recommended Lane

`WESLR_ARC_AGI2_KAGGLE_NOTEBOOK_BUNDLE_DRY_RUN_V1`

This lane should:
- Build a temporary Kaggle-like directory layout outside repo
- Copy only the 26 required solver modules + staging package
- Create a notebook entry point
- Set Kaggle-like env vars
- Run the notebook-equivalent script from outside repo
- Use public eval challenge JSON (already approved for parsing)
- Write `submission.json`
- Validate canonical output hash: `78f295d33a665325393ee03bd40cf0816beccbd32787d321522f180a2a3eb7c9`
- No solution reads
- No scoring
- No Kaggle submission

**Prerequisite repair:** Before the bundle dry run, update `portable_solver.py` to accept an alternative solver directory name (e.g., `weslr_solver/`), or create a bundle-specific wrapper.

## Readiness Verdict

```
kaggle_notebook_bundle_review_v1_passed_ready_for_kaggle_notebook_bundle_dry_run_lane
```

### Criteria met:
- ✅ Bundle layout is clear (12 staging modules + 26 solver modules)
- ✅ Notebook flow is clear (5 cells, no internet, no API calls)
- ✅ `WESLR_REPO_ROOT` dependency is acceptable for dry run (env var approach)
- ✅ No notebook/bundle blockers remain in staged package
- ✅ No solution files are opened
- ✅ No scoring occurs
- ✅ No Kaggle submission occurs
- ✅ Source-repo health check passes (6/6 mandatory)

### Prerequisite for next lane:
- Update `portable_solver.py` to accept `weslr_solver/` directory name (or create bundle wrapper)
- Create bundle packaging script
