# WESLR Working Root Guard

This file is a permanent, visible guard to prevent accidental work
in the wrong repository.

## Correct WESLR Repository

**This is the real WESLR working repository.**

- **Correct repo path:** `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Correct branch for current work:** `master`
- **Latest recorded design checkpoint:** `20ee91d` — *WESLR: design next controlled safe non-model observation lane*

## Current Context Alignment

- **Latest context checkpoint:** `20ee91d` — *WESLR: design next controlled safe non-model observation lane*
- **Alignment layer:** `OCC_CONTEXT_ALIGNMENT` records this orientation; the design itself is `WESLR_CANON_ALIGNMENT` design only.
- **Live/user-facing WESLR behavior changed:** no.
- **Implementation performed:** no.
- **Matrix V1 status:** `matrix_clean_but_limited`.
- **Clean observations:** `ordinary_task_behavior_003`, `non_canned_cognition_002`, `conduct_alignment_001`, `conduct_alignment_002`.
- **Allowed low-risk families covered:** `ordinary_task_behavior`, `non_canned_cognition`, `conduct_alignment`.
- **Recommended next structured lane:** `DESIGN_CONTROLLED_SAFE_NON_MODEL_OBSERVATION_LANE_V2`.
- **Recommended V2 shape:** one deterministic-safe prompt, one mock-required low-risk prompt, one blocked-family negative control.
- **Negative controls:** preflight-only; no callable construction, no safe callable build, no mocked retry, no `ChatResponder`/`respond_chat()`/`generate_chat()`, and no prompt execution.
- **V2 success criteria:** routing-validator-first, deterministic-safe prompts allowed without mock, mock-required prompts blocked without mock and allowed only with mock, blocked-family controls blocked before callable construction, no raw retention, no `.weslr` writes, no live model/search/advisor calls, no official claims, metadata-only reporting, selected prompt IDs only.
- **V2 abort criteria:** gate-order drift, blocked family reaches callable construction, mock-required prompt proceeds without mock, live `generate_chat`/model/search/advisor path, raw prompt/response in report, `.weslr` change, scope expansion, default feature flag, or blocker contract failure.
- **Design readiness label:** `lane_design_ready`.
- **Cleanup debt:** previous stale literal `Current HEAD` marker was replaced with stable checkpoint wording during this context alignment; continue to verify the actual repo HEAD with `scripts/weslr_assert_correct_repo.sh`.
- **Recommended sequence:** context alignment → design V2 lane before any more observations.

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
