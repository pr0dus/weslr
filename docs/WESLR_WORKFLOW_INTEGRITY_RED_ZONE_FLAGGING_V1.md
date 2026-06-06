# WESLR Workflow Integrity Red-Zone Flagging V1

## 1. Handshake result
- PASS
- Repo root / branch / expected HEAD matched at design start.

## 2. Start HEAD
- `3f1bd850c622a308e8709732157ad602dbb4e240`

## 3. Files changed
- `docs/WESLR_WORKFLOW_INTEGRITY_RED_ZONE_FLAGGING_V1.md`

## 4. Purpose
This design defines automatic red-zone flagging for WESLR/OCC workflow reports.

Its job is to prevent false readiness, accidental untracked-artifact blindness, stale staged-state confusion, hidden untracked files, and commit/report mismatches.

Core rule: never lie. If repo evidence contradicts the report, classify the lane as red-zone and stop before the next lane.

## 5. Red-zone taxonomy
### `green_zone_ready`
- Repo evidence matches the report.
- No contradiction, no hidden drift, no stale staged-state issue.
- The lane may proceed.

### `yellow_zone_needs_note`
- Evidence is not contradictory, but the report needs a cautionary note.
- Examples: harmless pre-existing untracked files outside scope, known non-blocking ambiguity, or report wording that should mention a caveat.
- The lane may proceed only after the note is added.

### `red_zone_blocked`
- Evidence contradicts the report or hides material repo state.
- The lane must stop.
- Next lane must not be recommended until reconciliation is complete.

### `red_zone_reconciled_ready`
- A prior red zone was detected and explicitly reconciled.
- The report now states the contradiction, the reconciliation, and the final evidence.
- The lane may proceed only after explicit reconciliation is documented.

## 6. Report consistency rules
A workflow report is inconsistent if it claims any of the following while evidence says otherwise:
- created or changed files that are not tracked or not committed as claimed
- final HEAD changed when it did not
- tracked files changed when `git diff --name-only` is empty
- validation passed when a validation command failed
- commit status resolved when `git log --oneline -5` does not show the expected new commit
- readiness when protected-file drift exists

The report must always distinguish between:
- tracked changes
- untracked files
- staged files
- committed files
- validation failures
- reconciliation status

## 7. Commit-status consistency rules
The report must match all of these sources:
- `git status --short`
- `git status --short --untracked-files=all`
- `git status --short --untracked-files=no`
- `git diff --name-only`
- `git diff --stat`
- `git diff --cached --name-only`
- `git log --oneline -5`
- `git ls-files <reported_files>`

Required consistency checks:
1. If the report says a file was created, `git ls-files <reported_file>` must confirm whether it is tracked or not.
2. If the report says a file was committed, `git log --oneline -5` must show the commit.
3. If the report says final HEAD changed, the HEAD value must differ from start HEAD.
4. If the report says tracked changes exist, `git diff --name-only` must show them.
5. If the report says the repo is clean, both tracked and untracked evidence must support that claim for the relevant scope.

## 8. Untracked-file handling
Untracked files must be classified explicitly:
- relevant to current lane
- irrelevant pre-existing workspace drift
- unrelated noise outside the lane

Rules:
- Never call a lane clean if relevant untracked files exist.
- Never imply tracked-state changes from untracked files.
- Never suppress untracked evidence just because tracked diffs are empty.
- If untracked files matter to the report, list them and state their relevance.

## 9. Staged-state handling
Staged files must be treated as active evidence, even if the working tree is otherwise quiet.

Rules:
- `git diff --cached --name-only` must be checked whenever commit status matters.
- A release gate failure with staged files present is a red-zone condition unless the report explicitly documents the stale staged-state problem.
- Do not clear staged state silently in the report narrative.
- If staged state is cleared before a passing gate, the report must say so.

## 10. Release-gate stale-state handling
If the release gate passes only after staged state is cleared, the report must explicitly note:
- what was staged
- why the staged state was stale or misleading
- what changed before the passing validation
- whether the pass reflects the unstaged tree rather than the original staged state

This prevents false confidence from a gate that only passed after the evidence changed.

## 11. Protected-file handling
Protected files are always high-sensitivity drift markers:
- `weslr/chat_responder.py`
- `weslr/main.py`
- `main.py`
- `dialogue.py`
- `chat_ui.py`

Rules:
- Any unexpected change in protected files is red-zone blocked.
- A report may not claim protected-file stability without checking them.
- If protected files changed, the report must stop and report drift.
- Protected-file checks are required even when the lane otherwise looks clean.

## 12. Final-judgment override rules
The final judgment must never override the evidence.

If any red-zone condition is true:
- final judgment cannot say ready
- recommended next lane cannot proceed
- reconciliation is required first

If the report is otherwise good but contains a minor caveat, use `yellow_zone_needs_note` instead of forcing green.

## 13. Red-zone conditions
The design must automatically flag red-zone when any of the following is true:
1. Start HEAD equals final HEAD but files are reported created/changed.
2. A file is present but `git ls-files <file>` returns empty.
3. `git status --short --untracked-files=no` is clean but `git status --short --untracked-files=all` shows relevant untracked files.
4. `git diff --name-only` is empty but a report claims tracked source changes.
5. Validation summary includes any failed command but final judgment says ready.
6. Release gate fails while staged files are present.
7. Release gate passes only after staged state is cleared, without documenting stale staged-state behavior.
8. Report says committed but `git log --oneline -5` does not show a new commit.
9. Protected files changed unexpectedly.
10. Recommended next lane proceeds despite unresolved red-zone condition.

## 14. Required automatic checks
The report generator or verifier must automatically check:
- `git status --short`
- `git status --short --untracked-files=all`
- `git status --short --untracked-files=no`
- `git diff --name-only`
- `git diff --stat`
- `git diff --cached --name-only`
- `git log --oneline -5`
- `git ls-files <reported_files>`
- protected-file drift checks

These checks are mandatory whenever commit/report integrity matters.

## 15. Required reconciliation prompt pattern
When red-zone is detected, the report should use a direct reconciliation prompt pattern:
- state the contradiction
- cite the evidence source(s)
- classify the zone as `red_zone_blocked`
- identify whether the issue is untracked, staged, committed, or protected-file drift
- ask for the smallest next reconciliation step
- do not recommend the next lane yet

Example pattern:
- `RED_ZONE: report claims X, but git evidence shows Y. Reconcile before review.`

## 16. Future helper implementation plan
Future helper work should remain metadata-only and should:
1. collect status/diff/log evidence into a report packet
2. classify evidence into green/yellow/red zones
3. detect contradictions between narrative claims and repo state
4. detect staged-state confusion separately from untracked drift
5. verify protected-file stability
6. emit a reconciliation summary, not an action
7. fail closed when evidence is missing or ambiguous
8. keep runtime, persistence, and mutation authority out of scope

## 17. Safety boundary
This design is metadata-only, non-executing, non-authoritative, and non-public-claiming.

It must not:
- edit runtime files
- edit helper/test files
- read/write `.weslr`
- import `entity_graph.py`
- load `entity_graph.json`
- stage or delete unrelated files
- normalize contradictions away
- claim readiness against contradicted evidence

## 18. Design summary
Workflow integrity flagging is a reconciliation boundary, not a reporting style.
It exists to keep WESLR/OCC lanes honest when repository evidence and written reports diverge.

## 19. Final design judgment
`weslr_workflow_integrity_red_zone_flagging_design_ready_for_review`

## 20. Recommended next lane
`REVIEW_WESLR_WORKFLOW_INTEGRITY_RED_ZONE_FLAGGING_V1`