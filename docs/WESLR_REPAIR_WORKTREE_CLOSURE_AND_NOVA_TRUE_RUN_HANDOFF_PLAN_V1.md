# WESLR Repair Worktree Closure And Nova True-Run Handoff Plan V1

## 1. Purpose
Provide a closure plan for the repair worktree and a controlled handoff path to a Nova/Ubuntu true-run lane now that the canonical chain validates.

## 2. Canonical final state check
- Repo root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`
- HEAD at plan start: `b7bb4def`
- Dirty files: unrelated untracked docs/helper/test drift only; no tracked dirty files
- Recent log:
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
- Canonical validates the candidate-preparation chain: yes
- Protected runtime file status: clean for `weslr/chat_responder.py`, `weslr/main.py`, `main.py`, `dialogue.py`, `chat_ui.py`

## 3. Repair worktree closure inventory
- Repair repo root: `/data/data/com.termux/files/home/weslr-repair-worktrees/cross-domain-open-problem-discovery-scout-clean-impl`
- Repair branch: `implement-cross-domain-open-problem-discovery-scout-clean-20260613`
- Repair HEAD: `bb2e8bc5`
- Dirty files: none in the repair worktree at the time of review
- All repair work is now represented in canonical history or canonical docs
- The repair worktree can be kept temporarily as a read-only backup
- Before deletion, the owner should approve closure and final archival/deletion
- Do not delete without owner approval

## 4. Active copy policy
- Canonical repo is the active WESLR repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Repair worktree becomes inactive/read-only backup until owner approves deletion
- No new worktrees or branches unless explicitly approved
- Every future OCC/Nova dispatch must state:
  1. repo root
  2. branch
  3. HEAD
  4. dirty files
  before doing work

## 5. Nova/Ubuntu true-run readiness
- This is no longer another metadata-only helper lane.
- The next step should be a controlled live/local service true-run on Nova/Ubuntu.
- The likely boundary is a live metadata locator or source locator path feeding MLCF candidate preparation.
- Required boundary controls:
  - no source ingestion
  - no raw content retention
  - no evidence acceptance
  - no public claims
  - no proposal action
  - no runtime wiring
  - no `.weslr` IO
  - no autonomous loop
- Output should remain metadata-only locator/source-summary/intake-preparation unless later explicitly authorized otherwise.

## 6. Handoff target recommendation
**Recommended next lane:** `RUN_WESLR_CONTROLLED_NOVA_TRUE_RUN_METADATA_SOURCE_LOCATOR_TO_MLCF_CANDIDATE_PREPARATION_V1`

Handoff guidance:
- Canonical repo to use: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Current canonical HEAD: `b7bb4def`
- Expect a local SearXNG or equivalent live metadata/source locator boundary only if the Nova/Ubuntu environment provides it
- Allowed true-run boundary: live metadata lookup / locator only
- Source-access limits: bounded metadata lookup only; no raw content capture
- What not to ingest: full pages, HTML dumps, snippets as retained source content, papers, datasets, or raw pages
- Report to produce: a metadata-only locator/source-summary/intake-preparation report with operator-review posture preserved
- Validation required: confirm no source ingestion, no raw retention, no evidence acceptance, no proposal action, no `.weslr`, no runtime wiring, no public claim
- Stop when any boundary is exceeded or if the live service is unavailable

## 7. Boundary recap
- Canonical remains metadata-only and reviewable
- The repair worktree chain is complete and validated in canonical
- The next work should move from synthetic helper validation to controlled true-run metadata locator behavior

## 8. Why this reduces copy confusion
- Canonical is now the authoritative active repo
- The repair worktree is explicitly a backup, not the live source of truth
- The handoff lane is named and bounded
- Future dispatches must restate repo root / branch / HEAD / dirty files before work begins

## 9. Why this is not a runtime/public/claim step
- It is a closure and handoff plan only
- No evidence creation, accepted candidate creation, proposal action, runtime wiring, or public claims are introduced
- It does not modify `.weslr` or protected runtime surfaces

## 10. Protected-file assessment
- No diffs in:
  - `weslr/chat_responder.py`
  - `weslr/main.py`
  - `main.py`
  - `dialogue.py`
  - `chat_ui.py`

## 11. Validation plan
- `git diff --check`
- `python3 weslr/tests/release_gate_v1.py`
- `bash scripts/weslr_release_check.sh`
- `python3 -m pytest weslr/tests/test_cross_domain_scout_to_mlcf_candidate_preparation_v1.py`
- `python3 -m pytest weslr/tests/test_cross_domain_scout_to_mlcf_integration_v1.py`
- `python3 -m pytest weslr/tests/test_cross_domain_open_problem_discovery_scout_v1.py`

## 12. Cleanup plan after closure
- Keep the repair worktree until the owner approves closure
- Keep it read-only backup until then
- Do not delete or repurpose it in this lane

## 13. Branches / worktrees to keep temporarily
- Keep canonical `master`
- Keep the repair worktree as read-only backup
- Keep unrelated worktrees untouched until their owners approve changes

## 14. Branches / worktrees that can be deleted later only after owner approval
- The repair worktree may be deleted later only after owner approval
- No deletion now

## 15. Final judgment
`repair_worktree_closure_and_nova_true_run_handoff_plan_valid_ready_for_owner_go_to_nova`
