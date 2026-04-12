# BACKGROUND_ANALYSIS_OBSERVABILITY_SURFACE_v1

## Purpose
Provide operator-visible observability for the active Background Analysis Engine (Phase 5) so analysis loops, budgets, proposals, and control states are transparent, auditable, and role-gated. No autonomous expansion beyond approved visibility + controls.

## First Slice (approved)
- Active loop visibility (ids, status)
- Workspace scope (workspace_id, user_id)
- Budget usage vs caps
- Proposal history (recent)
- Pause/stop status
- Last analysis checkpoint

## Governance / Role Gating
- View: operators/owners
- Pause: operators/owners
- Stop: operators/owners
- Clear history: owners (or delegated operators) only; default read-only for others

## Minimal Schema (first slice)
Fields (per loop):
- loop_id: string
- workspace_id: string
- user_id: string
- status: string (running/paused/stopped)
- budget_used: number
- budget_cap: number
- proposals_recent: array of proposal summaries
- paused: bool
- stopped: bool
- last_checkpoint: string/timestamp
- updated_at: timestamp

## Validation Rules (first slice)
- Per-workspace isolation: data scoped to (workspace_id,user_id); no cross-leak
- Loop state rendered (status/paused/stopped)
- Budget accuracy: budget_used ≤ budget_cap; displayed
- Proposal history visible (recent)
- Role-gated controls enforced for pause/stop/clear history
- Last checkpoint displayed

## Next Steps
Pending implementation with the above schema; keep alignment with runtime snapshot and activation summary.
