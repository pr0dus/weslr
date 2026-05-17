# WESLR Working Root Guard

This file is a permanent, visible guard to prevent accidental work
in the wrong repository.

## Correct WESLR Repository

**This is the real WESLR working repository.**

- **Correct repo path:** `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Correct branch for current work:** `master`
- **Current HEAD:** `801a634` — *WESLR: add safe non-model ChatResponder harness*

## NOT the WESLR Repo

The OpenClaw workspace is **NOT** the WESLR project repo:

- **Wrong path:** `/data/data/com.termux/files/home/.openclaw/workspace`
- This is the OpenClaw agent runtime workspace.
- It contains personal memory files, session logs, and agent tooling.
- WESLR source code must **never** be committed there.

## Why This Guard Exists

A previous WESLR work packet was accidentally committed in
`.openclaw/workspace` instead of this repository.  The commit
`bd7a54f` exists only in the wrong repo.  This guard prevents
that from happening again.

## Rule for Every WESLR/OCC Packet

Every WESLR work packet must start with:

```bash
cd /data/data/com.termux/files/home/weslr-pr47-clean || exit 1
scripts/weslr_assert_correct_repo.sh
```

## Branch Rule

- Work must abort if `git rev-parse --show-toplevel` does not match
  `/data/data/com.termux/files/home/weslr-pr47-clean`.
- Work must abort if the branch is not `master`, unless the operator
  explicitly approves a branch-specific task.

## File Boundaries

- Files in `.openclaw/workspace` must **not** be moved, copied, or
  deleted into this repo without explicit owner approval.
- The accidental `bd7a54f` commit in `.openclaw/workspace` is
  outside WESLR canon and must not be cherry-picked or referenced
  as authoritative.
