# WESLR ARC Copy-Grid Tie-Break False-Closure Revert V1

- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `2b01a5bf9cfaf04e6da35e181cd362e02c0740f1`
- Requested revert target commits:
  - `2b01a5bf` — invalid integration report / attempted closure
  - `74470826` — tie-break bias that did not improve canonical 120

## Reason for revert
The attempted copy-grid tie-break lane did not change the measured canonical 120 diagnostic outcome versus `9a18710d`.

Measured unchanged metrics at the reverted state were:
- canonical 120: `109 exact / 11 partial / 0 unsupported / 0 failed`
- `copy_grid`: `6 exact / 4 partial`
- `rotate_object_90`: `7 exact / 3 partial`
- `object_count_to_pattern`: `9 exact / 1 partial`
- `reflect_object_horizontal_or_vertical`: `7 exact / 3 partial`

Because the committed code did not improve the canonical 120 and the report was therefore not a valid closure artifact, both commits were reverted with `git revert` to preserve auditability.

## Revert action
Executed:
- `git revert --no-edit 2b01a5bf 74470826`

Created revert commits:
- `b8ac272f` — revert invalid integration report commit
- `fe8fb5ee` — revert ineffective tie-break bias commit

## Expected post-revert state
- The branch returns to the pre-attempt code path for the synthetic solver suite.
- The failed attempted closure remains visible in history via explicit revert commits.
- The unrelated untracked document `docs/WESLR_ARC_SYNTHETIC_80_AFTER_COMPLETE_SYMMETRY_VARIANT_2_FIX_V1.md` is intentionally left untouched.

## Validation
Post-revert validation was requested for:
- focused ARC pytest if relevant
- `python weslr/tests/release_gate_v1.py`
- `git diff --check`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

## Final judgment
This revert restores an auditable, truth-aligned branch state and the failed attempted copy-grid tie-break closure should not be treated as a completed repair lane.

## Recommended next lane
- `DIAGNOSE_ARC_COPY_GRID_ROTATE_AMBIGUITY_WITHOUT_FIX_V1`
