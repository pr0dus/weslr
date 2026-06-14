# WESLR Repair Worktree Chain Consolidation To Canonical Repo Plan V1

## 1. Purpose
Prepare a safe, exact consolidation path for moving the clean repair-worktree chain back into the canonical WESLR repo without merging, cherry-picking, or mutating anything yet.

## 2. Repair worktree state
- Repo root: `/data/data/com.termux/files/home/weslr-repair-worktrees/cross-domain-open-problem-discovery-scout-clean-impl`
- Branch: `implement-cross-domain-open-problem-discovery-scout-clean-20260613`
- HEAD: `bcdb3519`
- Dirty files at inspection start: none
- Recent log:
  - `bcdb3519` `WESLR: review first cross-domain scout to MLCF candidate preparation sample v1`
  - `d61fba09` `WESLR: repair candidate preparation missing-evidence carry-forward v1`
  - `45f52b72` `WESLR: review cross-domain scout to MLCF candidate preparation helper v1`
  - `91c01a3e` `WESLR: repair cross-domain scout to MLCF candidate preparation helper v1`
- Shared-base note: the repair chain is the linear sequence beginning at `91c01a3e` and ending at `bcdb3519`; the canonical repo is on a different branch state (`master`) and should be treated as the consolidation target.

## 3. Canonical repo state
- Repo root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`
- HEAD: `9b47c42b`
- Dirty files at inspection start: many untracked docs and one untracked helper/test set; no tracked diffs were reported in protected runtime files.
- Recent log:
  - `9b47c42b` `WESLR: implement cross-domain open problem discovery scout helper v1`
  - `f7acdb15` `WESLR: review MLCF metadata to evidence vertical slice`
  - `90706cdb` `WESLR: run first MLCF normalized evidence packet from intake preparation sample`
  - `2f0b7ee0` `WESLR: review MLCF normalized evidence packet from intake preparation helper`
- Protected-file check in canonical repo:
  - `weslr/chat_responder.py` — clean
  - `weslr/main.py` — clean
  - `main.py` — clean
  - `dialogue.py` — clean
  - `chat_ui.py` — clean

## 4. Commit inventory
Chronological repair-chain commits to consider for consolidation:

| Commit | Message | Files changed | Role | Type | Release gate touched | Protected files touched |
|---|---|---|---|---|---|---|
| `91c01a3e` | `WESLR: repair cross-domain scout to MLCF candidate preparation helper v1` | `weslr/cross_domain_scout_to_mlcf_candidate_preparation.py` | fixes helper behavior and carry-forward foundations | source/helper | no | no |
| `45f52b72` | `WESLR: review cross-domain scout to MLCF candidate preparation helper v1` | `docs/WESLR_CROSS_DOMAIN_SCOUT_TO_MLCF_CANDIDATE_PREPARATION_HELPER_REVIEW_V1.md` | review artifact for helper | report/review | no | no |
| `d61fba09` | `WESLR: repair candidate preparation missing-evidence carry-forward v1` | `weslr/cross_domain_scout_to_mlcf_candidate_preparation.py`, `weslr/tests/test_cross_domain_scout_to_mlcf_candidate_preparation_v1.py`, `docs/WESLR_FIRST_CROSS_DOMAIN_SCOUT_TO_MLCF_CANDIDATE_PREPARATION_SAMPLE_V1.md` | fixes missing-evidence carry-forward and updates sample/report | source/helper/test/report/sample | no | no |
| `bcdb3519` | `WESLR: review first cross-domain scout to MLCF candidate preparation sample v1` | `docs/WESLR_FIRST_CROSS_DOMAIN_SCOUT_TO_MLCF_CANDIDATE_PREPARATION_SAMPLE_REVIEW_V1.md` | review artifact for repaired sample | report/review | no | no |

## 5. Changed-file inventory
Across the repair chain, the changed files are:
- `weslr/cross_domain_scout_to_mlcf_candidate_preparation.py`
- `weslr/tests/test_cross_domain_scout_to_mlcf_candidate_preparation_v1.py`
- `docs/WESLR_CROSS_DOMAIN_SCOUT_TO_MLCF_CANDIDATE_PREPARATION_HELPER_REVIEW_V1.md`
- `docs/WESLR_FIRST_CROSS_DOMAIN_SCOUT_TO_MLCF_CANDIDATE_PREPARATION_SAMPLE_V1.md`
- `docs/WESLR_FIRST_CROSS_DOMAIN_SCOUT_TO_MLCF_CANDIDATE_PREPARATION_SAMPLE_REVIEW_V1.md`

## 6. Contamination-risk assessment
Observed risks:
- Canonical repo is dirty with many unrelated untracked docs and a few untracked helper/test files.
- This is a workspace contamination risk, not a protected-runtime change.
- No accidental `.weslr` access was observed.
- No live source access, source ingestion, GitHub, provider, or model calls were observed in this lane.
- No hidden branch/worktree creation or deletion occurred in this lane.
- No accidental placeholder path writes were observed in the consolidated repair chain.
- No public-claim artifacts were created beyond metadata-only docs.

Risk rating: moderate environmental contamination, low content-risk for the repair chain itself.

## 7. Protected-file assessment
- Repair worktree: no diffs in `weslr/chat_responder.py`, `weslr/main.py`, `main.py`, `dialogue.py`, `chat_ui.py`.
- Canonical repo: those files are clean.
- No protected runtime file touched by the repair chain.

## 8. Release-gate assessment
- Repair worktree validations passed:
  - `python3 -m py_compile ...` — pass
  - focused candidate-preparation tests — pass
  - integration tests — pass
  - scout tests — pass
  - science-direction candidate tests — pass
  - source-selection evidence-plan tests — pass
  - `git diff --check` — pass
  - `python3 weslr/tests/release_gate_v1.py` — pass
  - `bash scripts/weslr_release_check.sh` — pass
- No release-gate weakening was required.
- No exact-file allowance for `weslr/tests/release_gate_v1.py` was needed for this plan artifact.

## 9. Proposed consolidation method
**Recommended method:** exact cherry-pick sequence into canonical `master`.

Why this method:
- It preserves the linear, review-gated repair chain.
- It avoids merge noise and reduces accidental replay of unrelated canonical changes.
- It is the safest exact method for a contamination-sensitive chain.

## 10. Exact commit sequence to consolidate
Start repo:
- `/data/data/com.termux/files/home/weslr-repair-worktrees/cross-domain-open-problem-discovery-scout-clean-impl`

Target repo:
- `/data/data/com.termux/files/home/weslr-pr47-clean`

Target branch:
- `master`

Exact sequence to consolidate:
1. `91c01a3e` — helper repair foundation
2. `45f52b72` — helper review artifact
3. `d61fba09` — missing-evidence carry-forward repair
4. `bcdb3519` — repaired sample review artifact

## 11. Validation plan
After each phase in canonical `master`:
1. Verify the cherry-pick applied cleanly.
2. Run `git diff --check`.
3. Run the relevant focused tests for the touched layer:
   - after helper commits: candidate-preparation suite and dependent integration/scout suites
   - after sample/report commits: quick release gate and release check
4. Confirm protected files remain unchanged.
5. Confirm no `.weslr` writes and no source-access behavior appeared.

## 12. Abort conditions
Abort consolidation immediately if any of the following occur:
- cherry-pick conflict affecting anything outside the intended files
- unexpected diff in any protected runtime file
- any `.weslr` path is touched
- any source-access / ingestion / provider / model / GitHub / web call appears
- unrelated tracked-file drift appears in canonical `master`
- any release-gate or diff-check failure appears
- any commit order dependency is violated

## 13. Cleanup plan after consolidation
- Keep the repair worktree until the canonical repo has been validated against the consolidated chain.
- Keep canonical `master` as the authoritative target.
- After owner approval and post-consolidation verification, the temporary repair worktree may be archived or deleted.
- Do not delete anything yet.

## 14. Branches / worktrees to keep temporarily
- Keep: `/data/data/com.termux/files/home/weslr-repair-worktrees/cross-domain-open-problem-discovery-scout-clean-impl`
- Keep: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Keep any unrelated existing worktrees untouched until their owners approve cleanup.

## 15. Branches / worktrees that can be deleted later only after owner approval
- The repair worktree above can be deleted later only after owner-approved consolidation verification.
- No deletion is authorized in this lane.

## 16. Why this reduces WESLR copy confusion
- It records the exact chain boundary from `91c01a3e` through `bcdb3519`.
- It separates helper, test, sample, and review artifacts.
- It distinguishes repair-worktree state from canonical repo state.
- It keeps the consolidation path exact rather than vague.

## 17. Why this is not a runtime / public / claim step
- The chain is metadata-only, review-oriented, and plan-oriented.
- It does not create evidence, accepted candidates, proposals, runtime wiring, or public claims.
- It does not access sources or mutate `.weslr`.

## 18. Next recommended lane
- `EXECUTE_WESLR_REPAIR_WORKTREE_CHAIN_CONSOLIDATION_TO_CANONICAL_REPO_V1`

## 19. Final judgment
`repair_worktree_chain_consolidation_plan_valid_ready_for_owner_approved_execution`
