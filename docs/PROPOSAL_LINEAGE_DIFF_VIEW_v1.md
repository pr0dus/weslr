# PROPOSAL_LINEAGE_DIFF_VIEW_v1

**Scope:** Define the Proposal Lineage Diff View for operators to compare proposal state across review stages and surfaces. Doctrine-first; minimal runtime slice included.

## Goals
- Allow operators to compare two proposal lineage snapshots (e.g., before/after review) side-by-side.
- Highlight differences in status history, audit trail, confidence, checkpoints, and adequacy findings if present.
- Remain read-only, proposal-only; no execution effects.

## Inputs
- Two lineage records (A, B) with:
  - proposal_id, source_loop_id, workspace_id, user_id
  - trigger_reason, originating_evidence_signal
  - timestamp, confidence
  - linked_checkpoint
  - current_status
  - status_history[]
  - audit_log[]
  - optional adequacy reference

## Output
- Diff structure with:
  - summary: proposal_id, same/different workspace/user
  - field_diffs: confidence change, status change, checkpoint change, adequacy change
  - status_history_diff: added/removed/changed transitions
  - audit_diff: added/removed audit entries
  - flags: regression (confidence drop), advancement (status progression), checkpoint drift

## Constraints
- Read-only; no mutation of lineage.
- Role/permission checks must be enforced at call sites.
- No UI defined; this view is data-only, suitable for observability/operator surfaces.

## Next Step
- Implement diff helper and tests; integrate with observability as a read helper (optional).
