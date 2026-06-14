# WESLR Termux Canonical Origin Divergence Diagnosis And Reconciliation Plan V1

## 1. Repo root
- `/data/data/com.termux/files/home/weslr-pr47-clean`

## 2. Branch
- `master`

## 3. Start HEAD
- `b628ae64`

## 4. End HEAD / diagnosis-plan commit hash
- pending commit of this diagnosis plan

## 5. origin/master HEAD
- `3342beec285cc30992e205e0fd04b122c9a6f8cf`
- short form: `3342beec`

## 6. Merge-base
- `f7acdb15f27bde4e84b778c803a10ec859073032`
- short form: `f7acdb15`

## 7. Local-only commit summary
Local side contains the older consolidation chain ending at `b628ae64`:
- `b628ae64` `WESLR: plan repair worktree closure and Nova true-run handoff v1`
- `b7bb4def` `WESLR: review revised repair worktree consolidation to canonical repo v1`
- `79e4c9f9` `WESLR: implement cross-domain scout to MLCF integration helper v1`
- `19a37bb5` `WESLR: revise consolidation plan after candidate preparation conflict v1`
- `5da24459` `WESLR: prepare repair worktree chain consolidation plan v1`
- `b2d68798` `WESLR: review first cross-domain scout to MLCF candidate preparation sample v1`
- `687fe8ae` `WESLR: repair candidate preparation missing-evidence carry-forward v1`
- `ceada0ba` `WESLR: review cross-domain scout to MLCF candidate preparation helper v1`
- `5f8fac27` `WESLR: repair cross-domain scout to MLCF candidate preparation helper v1`
- `b2895619` `WESLR: implement cross-domain scout to MLCF candidate preparation helper v1`
- `9b47c42b` `WESLR: implement cross-domain open problem discovery scout helper v1`

Local-only changed files are the candidate-preparation / consolidation set:
- `weslr/cross_domain_open_problem_discovery_scout.py`
- `weslr/cross_domain_scout_to_mlcf_candidate_preparation.py`
- `weslr/cross_domain_scout_to_mlcf_integration.py`
- `weslr/tests/test_cross_domain_open_problem_discovery_scout_v1.py`
- `weslr/tests/test_cross_domain_scout_to_mlcf_candidate_preparation_v1.py`
- `weslr/tests/test_cross_domain_scout_to_mlcf_integration_v1.py`
- `docs/WESLR_REPAIR_WORKTREE_CHAIN_CONSOLIDATION_TO_CANONICAL_REPO_PLAN_V1.md`
- `docs/WESLR_REPAIR_WORKTREE_CHAIN_CONSOLIDATION_TO_CANONICAL_REPO_REVISED_PLAN_AFTER_CONFLICT_V1.md`
- `docs/WESLR_REPAIR_WORKTREE_CLOSURE_AND_NOVA_TRUE_RUN_HANDOFF_PLAN_V1.md`
- `docs/WESLR_REVISED_REPAIR_WORKTREE_CHAIN_CONSOLIDATION_TO_CANONICAL_REPO_REVIEW_V1.md`
- plus the earlier candidate-preparation docs kept on the local side

## 8. Remote-only commit summary
Remote/master contains the newer live SearXNG metadata-only chain:
- `3342beec` `WESLR: review MLCF routing helper from live SearXNG metadata result`
- `4267ff26` `WESLR: implement MLCF routing helper from live SearXNG metadata result`
- `6999205f` `WESLR: review MLCF routing helper from live SearXNG metadata result`
- `bc5346d7` `WESLR: design MLCF routing helper from live SearXNG metadata result`
- `dbd14b4b` `WESLR: review MLCF routing for first live SearXNG metadata result`
- `af717568` `WESLR: design MLCF routing for first live SearXNG metadata result`
- `00ff3b7b` `WESLR: rerun first controlled live SearXNG metadata-only sample`
- `5ea6eb29` `WESLR: review live SearXNG timestamp repair`
- `9c6556fa` `WESLR: repair live SearXNG timestamp handling`
- `23f5cd65` `WESLR: design first controlled live SearXNG metadata-only sample`
- `9c202286` `WESLR: review controlled live SearXNG query encoding repair`
- `6c6f7128` `WESLR: repair controlled live SearXNG query encoding`
- `24f20ada` `WESLR: review controlled live SearXNG metadata-only boundary implementation`
- `8fccf95b` `WESLR: implement controlled live SearXNG metadata-only boundary`
- `7a66613a` `WESLR: allow controlled live SearXNG design doc in release gate`
- `620838ad` `WESLR: design controlled live SearXNG metadata-only boundary`

Remote-only changed files are the live-SearXNG metadata boundary chain:
- `weslr/controlled_live_searxng_metadata_only_boundary.py`
- `weslr/mlcf_routing_from_live_searxng_metadata_result.py`
- `weslr/tests/test_controlled_live_searxng_metadata_only_boundary_v1.py`
- `weslr/tests/test_mlcf_routing_from_live_searxng_metadata_result_v1.py`
- `docs/WESLR_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_BOUNDARY_V1.md`
- `docs/WESLR_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_BOUNDARY_IMPLEMENTATION_REVIEW_V1.md`
- `docs/WESLR_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_BOUNDARY_QUERY_ENCODING_REPAIR_REVIEW_V1.md`
- `docs/WESLR_CONTROLLED_LIVE_SEARXNG_BOUNDARY_REAL_TIMESTAMP_REPAIR_REVIEW_V1.md`
- `docs/WESLR_FIRST_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_SAMPLE_V1.md`
- `docs/WESLR_FIRST_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_SAMPLE_RESULT_V1.md`
- `docs/WESLR_MLCF_ROUTING_FROM_LIVE_SEARXNG_METADATA_RESULT_HELPER_V1.md`
- `docs/WESLR_MLCF_ROUTING_FROM_LIVE_SEARXNG_METADATA_RESULT_HELPER_REVIEW_V1.md`
- `docs/WESLR_MLCF_ROUTING_FROM_LIVE_SEARXNG_METADATA_RESULT_HELPER_IMPLEMENTATION_REVIEW_V1.md`
- `docs/WESLR_MLCF_ROUTING_FOR_FIRST_LIVE_SEARXNG_METADATA_ONLY_RESULT_V1.md`
- `docs/WESLR_MLCF_ROUTING_FOR_FIRST_LIVE_SEARXNG_METADATA_ONLY_RESULT_REVIEW_V1.md`

## 9. Overlap-risk assessment
- Exact-path overlap exists in `weslr/tests/release_gate_v1.py` on both sides.
- No protected runtime files were touched on either side.
- The remaining divergence is mostly disjoint and content-compatible.
- Risk level: moderate, not catastrophic.
- The overlap is small enough to reconcile safely by preserving both histories and resolving the gate file carefully if/when reconciliation is executed.

## 10. Protected-file status
- Local working tree diffs in protected runtime files: none
- Confirmed clean for:
  - `weslr/chat_responder.py`
  - `weslr/main.py`
  - `main.py`
  - `dialogue.py`
  - `chat_ui.py`

## 11. Compatibility assessment
- Divergence is content-compatible overall: yes
- `origin/master` likely contains useful newer chain that must be preserved: yes
- Local `b628ae64` contains canonical consolidation work that must be preserved: yes
- The two histories are complementary, with only a small overlap on release-gate logic

## 12. Safest reconciliation method
**Recommended method: C**
- Create a temporary reconciliation branch from `origin/master`
- Cherry-pick the local-only commits onto it
- Validate
- Fast-forward/switch `master` only after the reconciliation branch is proven

Why this is safest:
- preserves both histories
- avoids destructive operations
- keeps the newer remote live-SearXNG chain intact
- keeps the local candidate-preparation/consolidation chain intact
- isolates the only meaningful overlap (`release_gate_v1.py`) to a controlled reconciliation point

## 13. What not to do
- Do not merge blindly
- Do not rebase blindly
- Do not reset
- Do not stash
- Do not overwrite either chain

## 14. Validation performed for this diagnosis
- `git rev-parse --show-toplevel`
- `git branch --show-current`
- `git rev-parse --short=8 HEAD`
- `git status --short`
- `git remote -v`
- `git fetch origin master`
- `git rev-parse --short=8 origin/master`
- `git merge-base HEAD origin/master`
- `git log --oneline --left-right --cherry-pick HEAD...origin/master`
- `git log --oneline origin/master..HEAD`
- `git log --oneline HEAD..origin/master`
- `git diff --name-status origin/master..HEAD`
- `git diff --name-status HEAD..origin/master`
- protected-file diff check

## 15. Final judgment
`canonical_origin_divergence_plan_valid_ready_for_owner_approved_reconciliation`
