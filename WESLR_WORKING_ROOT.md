# WESLR Working Root Guard

This file is a permanent, visible guard to prevent accidental work
in the wrong repository.

## Correct WESLR Repository

**This is the real WESLR working repository.**

- **Correct repo path:** `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Correct branch for current work:** `master`
- **Latest recorded design checkpoint:** `6548cda` — *WESLR: design mocked observation to live slice governance*
- **Latest recorded implementation checkpoint:** `dec2f36` — *WESLR: add first deterministic safe live slice guard*

## Current Context Alignment

- **Latest implementation checkpoint:** `dec2f36` — *WESLR: add first deterministic safe live slice guard*.
- **Alignment layer:** `OCC_CONTEXT_ALIGNMENT` records current repo orientation after a bounded `WESLR_RUNTIME_CHANGE` helper/test implementation.
- **Historical governance checkpoint:** `6548cda` — *WESLR: design mocked observation to live slice governance*.
- **Historical recommended design lane:** `DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_PREIMPLEMENTATION_PLAN_V1` was completed and followed by guard design/review.
- **Live/user-facing WESLR behavior changed:** no.
- **Implementation performed:** yes — helper/test source only.
- **Runtime wiring performed:** no.
- **Live slice executed:** no.
- **Feature flag enabled:** no.
- **Latest clean mocked-observation evidence:** Lane V2 reviewed clean with readiness label `lane_v2_clean_but_limited`.
- **Lane V2 rows:** `ordinary_task_behavior_001` deterministic-safe route; `conduct_alignment_003` mock-required low-risk route; `memory_honesty_001` blocked-family negative control.
- **Governance conclusion:** mocked observation evidence is clean but limited; live model-backed slices remain unauthorized.
- **Implemented guard scope:** first deterministic-safe candidate guard only; prompt `ordinary_task_behavior_001`, family `ordinary_task_behavior`, route `safe_keyword_branch`.
- **Guard helper:** `evaluate_first_deterministic_safe_live_slice_guard_v1(prompt_item, validator_result, env=None) -> dict` in `weslr/first_deterministic_safe_live_slice_guard_v1.py`.
- **Guard tests:** `weslr/tests/test_first_deterministic_safe_live_slice_guard_v1.py`.
- **Feature flag:** `WESLR_ENABLE_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_V1=1`; absent/empty/false/non-exact values block; exact string `"1"` only allows the metadata guard for the exact candidate.
- **Disabled by default:** yes.
- **Metadata-only return:** yes.
- **No runtime/provider imports or calls:** yes.
- **No ChatResponder/respond_chat/generate_chat calls:** yes.
- **No prompt execution:** yes.
- **No model/search/advisor calls:** yes.
- **No `.weslr` writes:** yes.
- **No raw prompt/response retention:** yes.
- **No default behavior change:** yes.
- **No broad routing replacement:** yes.
- **No family broadening:** yes.
- **Validation passed for implementation:** py_compile helper/test, focused guard tests, routing-validator safe preflight integration tests, prompt-set routing validator tests, safe non-model harness tests, release gate, and release check.
- **Possible future live-slice candidate type:** deterministic-safe ordinary-task route only, disabled by default, no model call, no `generate_chat()`, no raw retention, rollback required.
- **Explicit non-candidates:** mock-required routes, blocked families, currentness/search/source/status paths, model-backed paths, write paths, raw-retention paths, protected/hidden/answer-key paths.
- **Next likely lane:** `REVIEW_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_GUARD_IMPLEMENTATION_NO_IMPLEMENTATION`.
- **Cleanup debt:** previous stale literal `Current HEAD` marker was replaced with stable checkpoint wording during context alignment; continue to verify the actual repo HEAD with `scripts/weslr_assert_correct_repo.sh`.

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
