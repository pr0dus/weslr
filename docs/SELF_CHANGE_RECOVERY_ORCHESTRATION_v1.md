# SELF_CHANGE_RECOVERY_ORCHESTRATION_v1

**Scope:** Recovery/roll-forward orchestration for approval-gated self-changes. Doctrine + minimal runtime helper. No autonomous activation.

## Purpose
- Ensure every approved self-change (e.g., reflection enablement, future self-improvement steps) has checkpoint, rollback, validation, and lineage recorded.
- Provide a deterministic flow for apply → validate → rollback/commit.

## Flow
1) Plan: define change, checkpoints, rollback trigger, validation plan.
2) Apply (guarded): perform change behind a toggle.
3) Validate: run harness/tests/observability checks; evaluate noise/regressions.
4) Decide: if pass → commit; if fail/noisy → rollback.
5) Record: write lineage entry (what/why/evidence/approval/rollback ref).

## Inputs
- change_id, description, approval_ref
- checkpoint_ref (pre-change)
- rollback_ref (target commit/toggle state)
- validation_plan (tests, observability checks)
- execution_result (pass/fail/noise)

## Outputs
- state: pending/validated/rolled_back/committed
- applied_at/rolled_back_at/committed_at
- validation_outcome
- lineage_ref

## Constraints
- Read/write only to orchestration state; no direct routing/execution changes.
- Requires explicit approval_ref to apply; no auto-apply.
- Rollback must be callable if validation fails.

## Next Step
- Implement helper + tests to enforce this flow for future self-changes.
