# WESLR Report / Receipt / Commit Provenance Protocol (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_WESLR_REPORT_RECEIPT_COMMIT_PROVENANCE_PROTOCOL_V1`
**Start HEAD**: `d2ba47ea815f2e6b20b70826c9a2db37354da267`
**actual preflight HEAD**: `d2ba47ea815f2e6b20b70826c9a2db37354da267`

## Problem statement

Several reports have repeated the same mismatch pattern:

- the report file is written before the final commit exists,
- the report cannot truthfully know its own final commit hash at write time,
- yet the report is later read as if it were a post-commit receipt.

That creates false expectations around `End HEAD`, `Commit`, and final commit hash fields.

## Why self-commit hashes are impossible inside the same report

A report file is written before the commit that would record it exists. Therefore:

- the report cannot know its own final commit hash before the commit is made,
- the report cannot truthfully assert `End HEAD` if that means the final commit hash,
- the report cannot truthfully mark itself as already committed while still uncommitted.

The correct pattern is:

- the report states the pre-commit facts it can know,
- the post-commit receipt states the final commit facts it can know.

## 1) Report-field policy

### Safe and truthful inside a report file before commit

These fields are safe in a pre-commit report:

- lane
- repo
- branch
- start HEAD
- actual preflight HEAD
- files changed
- validation results
- boundaries respected
- recommended next lane
- commit status as `pending` or `prepared before commit`

### Not required inside the report file

These should not be required in the committed report body:

- final `End HEAD`
- final commit hash
- whether the report itself was committed
- exact files committed
- final `git status`
- `push avoided yes/no`

## 2) Receipt-field policy

The post-commit receipt is the authoritative place for final commit facts. It must include:

- Start HEAD
- actual preflight HEAD
- End HEAD
- Commit yes/no
- commit hash if yes
- files committed
- files intentionally left uncommitted
- validation PASS/FAIL
- push avoided yes/no
- recommended next lane

## 3) Official rule

A report file must **not** be considered invalid merely because it cannot contain its own final commit hash.

A report is valid if it truthfully states:

- what it knew before commit,
- what it validated,
- what remains pending until the receipt is written.

## 4) Allowed report footer format

Recommended footer text:

`Commit note: this report was prepared before final commit. Final commit hash is recorded in the post-commit receipt.`

If a lane must be committed later, the report may also say:

`Commit status: pending`

## 5) Receipt format

Standard receipt template:

- Start HEAD / End HEAD / Commit
- actual preflight HEAD
- files committed
- files intentionally left uncommitted
- validation PASS/FAIL
- push avoided yes/no
- recommended next lane

When useful, include:

- report committed yes/no
- exact commit hash
- report status checked yes/no

## 6) When a second provenance review is needed

Require a second provenance review only if:

- the report path is untracked,
- the report does not match the tracked code,
- the commit range is unclear,
- `Start HEAD` differs without explanation,
- files changed are not listed,
- an official-data boundary could be affected.

## 7) Current repo/report status check

Observed at write time:

- `git status --short` shows unrelated dirty files and untracked report files.
- `git rev-parse --short HEAD` is `d2ba47ea`.
- `git log --oneline -8` shows the toy adapter and contamination-boundary commits already in history.
- `git ls-files docs/WESLR_ARC_OFFICIAL_FORMAT_TOY_FIXTURE_ADAPTER_BEHAVIOR_REVIEW_V1.md` returned no tracked entry.

Conclusion:

- `docs/WESLR_ARC_OFFICIAL_FORMAT_TOY_FIXTURE_ADAPTER_BEHAVIOR_REVIEW_V1.md` is currently **untracked**.
- It is not a provenance failure; it is a normal pre-commit state.
- If desired, commit it later in a separate cleanup lane.

## 8) Recommended next lane

- **Separate cleanup lane for any untracked review report commit**

That should be done only if the owner explicitly wants the untracked review report committed.

## Standard report footer

Commit note: this report was prepared before final commit. Final commit hash is recorded in the post-commit receipt.
