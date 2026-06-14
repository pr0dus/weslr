# WESLR Repair Worktree Consolidation After Cherry-Pick Conflict Revised Plan V1

## 1. Purpose
Revise the consolidation plan after the first exact cherry-pick sequence failed on a missing-file conflict in canonical `master`.

## 2. Failed consolidation attempt summary
- Attempted exact cherry-pick sequence: `91c01a3e`, `45f52b72`, `d61fba09`, `bcdb3519`, `48d46d34`
- Failure point: first commit `91c01a3e`
- Result: cherry-pick stopped immediately and was aborted cleanly
- No consolidation landed

## 3. Conflict path and conflict type
- Conflict path: `weslr/cross_domain_scout_to_mlcf_candidate_preparation.py`
- Conflict type: `modify/delete`
- Canonical HEAD `9b47c42b` did not have the file in place; the repair commit attempted to modify a path that canonical deleted/missing at that base

## 4. Why the first plan failed
The prior plan started at a repair commit instead of including the dependency commit that first created the candidate-preparation helper file. The file must exist in canonical history before later repair/review/sample commits can apply cleanly.

## 5. Missing dependency analysis
The repair history shows the candidate-preparation file is introduced earlier than the failed cherry-pick start point.

Observed file history for `weslr/cross_domain_scout_to_mlcf_candidate_preparation.py`:
- `73308956` — first creation/implementation of the helper file
- `91c01a3e` — repair of the helper file
- `d61fba09` — later repair that carries missing-evidence forward and updates sample/test/report artifacts

Therefore, the previous plan omitted the file-creation dependency commit.

## 6. Full file-history inventory for `weslr/cross_domain_scout_to_mlcf_candidate_preparation.py`
- `73308956` `WESLR: implement cross-domain scout to MLCF candidate preparation helper v1`
  - Role: file creation / first helper implementation
  - Type: source/helper
  - Release gate touched: no
  - Protected files touched: no
- `91c01a3e` `WESLR: repair cross-domain scout to MLCF candidate preparation helper v1`
  - Role: helper repair
  - Type: source/helper
  - Release gate touched: no
  - Protected files touched: no
- `d61fba09` `WESLR: repair candidate preparation missing-evidence carry-forward v1`
  - Role: helper repair + sample/test/report update
  - Type: source/helper/test/report/sample
  - Release gate touched: no
  - Protected files touched: no

## 7. Commit dependency inventory
Safe-to-consolidate dependency chain for the candidate-preparation line:
1. `73308956` — create the helper file in canonical history first
2. `91c01a3e` — helper repair on top of the created file
3. `45f52b72` — helper review artifact
4. `d61fba09` — missing-evidence carry-forward repair
5. `bcdb3519` — sample review artifact
6. `48d46d34` — consolidation plan artifact

## 8. Which commits are safe to consolidate
- Safe: all six commits above, if applied in the corrected order
- Safe because they remain metadata-only, review-oriented, and do not touch protected runtime files

## 9. Which commits should be skipped, if any
- None identified as unnecessary for a faithful consolidation of the current repair-worktree chain
- The only skip would be a conservative operator decision to leave review/plan docs out of canonical if the owner wants code-only consolidation, but that is not recommended here because the chain explicitly includes review artifacts and a plan record

## 10. Recommended consolidation method
**Recommended method:** full dependency cherry-pick sequence into canonical `master`

Why:
- The failure showed the dependency gap precisely
- The helper file must be introduced before repairs that modify it
- Cherry-pick remains the safest exact method because it preserves commit boundaries and keeps the chain replayable

## 11. Exact revised commit sequence or patch-state strategy
Start repo:
- `/data/data/com.termux/files/home/weslr-repair-worktrees/cross-domain-open-problem-discovery-scout-clean-impl`

Target repo:
- `/data/data/com.termux/files/home/weslr-pr47-clean`

Target branch:
- `master`

Revised exact sequence:
1. `73308956`
2. `91c01a3e`
3. `45f52b72`
4. `d61fba09`
5. `bcdb3519`
6. `48d46d34`

Patch-state strategy is not recommended here because the commit graph is still cleanly replayable once the missing creation commit is included.

## 12. Validation plan
After each cherry-pick phase in canonical `master`:
1. Confirm the cherry-pick applied cleanly.
2. Run `git diff --check`.
3. Run the focused helper/test validation appropriate to the touched layer.
4. Confirm protected runtime files remain unchanged.
5. Confirm no `.weslr` access, source access, runtime wiring, provider/model/web/GitHub calls, or public-claim artifacts appear.

## 13. Abort conditions
Abort if any of the following occur:
- any cherry-pick conflict that reaches beyond the expected helper/doc/test paths
- any protected runtime file diff
- any `.weslr` touch
- any source access / ingestion / provider / model / web / GitHub call
- any unexpected canonical tracked contamination appears on the target paths
- any release gate or diff-check failure appears

## 14. Protected-file checks
Canonical protected files must remain clean throughout:
- `weslr/chat_responder.py`
- `weslr/main.py`
- `main.py`
- `dialogue.py`
- `chat_ui.py`

## 15. Canonical untracked-drift handling
- Canonical `master` currently has unrelated untracked docs/helper/test drift
- Do not delete or rewrite those files in this lane
- If any target path collides with an untracked file, stop and report before applying anything

## 16. Why this remains metadata-only
- The chain contains helper, test, sample, report, and review artifacts only
- No evidence creation, no accepted candidate membership, no proposal payloads, no runtime wiring, and no external actions are introduced

## 17. Why this avoids source access, ingestion, claims, accepted candidates, and proposal action
- The chain is bounded to metadata-only sample and review content
- It preserves denied-authority posture
- It does not fetch sources, ingest content, or assert proof/discovery/public-science claims
- It does not create accepted candidates or proposal actions

## 18. Next recommended lane
- `EXECUTE_WESLR_REVISED_REPAIR_WORKTREE_CHAIN_CONSOLIDATION_TO_CANONICAL_REPO_V1`

## 19. Final judgment
`revised_consolidation_plan_valid_ready_for_owner_approved_execution`
