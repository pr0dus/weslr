# WESLR Report / Receipt / Commit Provenance Protocol (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_WESLR_REPORT_RECEIPT_COMMIT_PROVENANCE_PROTOCOL_V1`
**Start HEAD**: `d2ba47ea815f2e6b20b70826c9a2db37354da267`
**actual preflight HEAD**: `d2ba47ea815f2e6b20b70826c9a2db37354da267`

## Problem statement

Repeated report/receipt mismatches happened because a report file was being expected to know its own final commit hash before the commit existed. That is impossible and caused stale or pending commit metadata to appear like an error.

## Why self-commit hashes are impossible inside the same report

A report is written before the final commit exists.
So the report cannot truthfully know:

- its own final commit hash,
- whether it has already been committed,
- the final `End HEAD` produced by the commit.

Those facts belong in the post-commit receipt, not in the pre-commit report body.

## 1) Report-field policy

### Safe in a pre-commit report

A report may truthfully include:

- lane
- repo
- branch
- start HEAD
- actual preflight HEAD
- files changed
- validation results
- boundaries respected
- recommended next lane
- commit status as `pending` / `prepared before commit`

### Not required inside the report body

These are not required in the committed report body:

- final End HEAD
- final commit hash
- whether the report itself was committed
- exact files committed
- final git status
- push avoided yes/no

## 2) Receipt-field policy

The receipt is the authoritative post-commit record. It must include:

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

A report is valid if it truthfully records the pre-commit facts and clearly separates them from post-commit receipt facts.

## 4) Allowed report footer format

Recommended footer text:

`Commit note: this report was prepared before final commit. Final commit hash is recorded in the post-commit receipt.`

Optional status line:

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

Optional additions:

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

- `git status --short` shows an unrelated dirty tracked file and several untracked report files.
- `git rev-parse --short HEAD` is `d2ba47ea`.
- `git log --oneline -8` shows the recent ARC boundary and toy-adapter commits.
- `git ls-files docs/WESLR_ARC_OFFICIAL_FORMAT_TOY_FIXTURE_ADAPTER_BEHAVIOR_REVIEW_V1.md` returned no tracked entry.

Conclusion:

- `docs/WESLR_ARC_OFFICIAL_FORMAT_TOY_FIXTURE_ADAPTER_BEHAVIOR_REVIEW_V1.md` is currently **untracked**.
- That is normal and not a provenance failure.
- If needed, it can be committed later in a separate cleanup lane.

## 8) Recommended next lane

- **Separate cleanup lane for any untracked review report commit**

## Standard report footer

Commit note: this report was prepared before final commit. Final commit hash is recorded in the post-commit receipt.
