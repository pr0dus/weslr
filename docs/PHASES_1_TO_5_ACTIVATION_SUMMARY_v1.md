# PHASES 1–5 ACTIVATION SUMMARY (Canonical)

## Active Phases
- **Phase 1 — Capability Governance Runtime / Autonomy Boundaries**
  - Status: ACTIVE
  - Purpose: enforce capability/autonomy bounds; approvals/overrides gated
  - Safety: governance gate on; owner/operator override required for boundary changes
  - Rollback: toggle/override to revert to prior boundary set
  - Checkpoint: 35f3018c4bca0c276aa0f0a628bff5b6fc2a4073 (phase go-live)

- **Phase 2 — Identity Continuity Boundary / Front-Door Continuity Cache**
  - Status: ACTIVE
  - Purpose: partition continuity by (workspace_id, user_id); stateless when unresolved
  - Safety: isolation; owner/operator flush/disable
  - Rollback: disable/flush cache
  - Checkpoint: b9c246e3ef0c27114a7073c5b8b265ec833f7f00

- **Phase 3 — Decision Layer**
  - Status: ACTIVE
  - Purpose: operator-facing decision synthesis; governance-gated; rollback toggle available
  - Safety: approvals enforced; rollback toggle to baseline
  - Rollback: DECISION_LAYER_PHASE3_ACTIVE toggle
  - Checkpoint: 98417f6 (decision layer), 7bb80ad (rollback test), 35f3018 (phase 1) context

- **Phase 4 — Evidence Sufficiency + Proactive Acquisition (Proposal-Only)**
  - Status: ACTIVE (proposal-only)
  - Purpose: assess evidence sufficiency; propose acquisitions; no outbound without approval
  - Safety: proposals only; high-risk blocked; rollback to assessment-only
  - Rollback: disable proposals → assessment-only
  - Checkpoint: 888f292, harness: test_phase4_evidence_acquisition_dryrun.py

- **Phase 5 — Background Analysis Engine (Internal-Only, Proposal-Only)**
  - Status: ACTIVE
  - Purpose: bounded internal background analysis loops; proposals only; no external reach
  - Safety: budget/time caps; workspace isolation; pause/stop/rollback paths
  - Rollback: pause/disable loop; discard interim artifacts
  - Checkpoint: 0349d6b

## Runtime Shape (after Phase 5)
- Governance gate active (Phase 1)
- Identity continuity partitioned (Phase 2)
- Decision Layer active with rollback toggle (Phase 3)
- Evidence sufficiency + acquisition proposals only (Phase 4)
- Background analysis engine internal-only/proposal-only (Phase 5)
- Canonical conversational path: route_request → DecisionLayer → (anchor/local) with thin client; browser UI deferred; CLI speak path non-default

## Recovery / Resume
- Use the canonical recovery checklist after interruptions/resets: see docs/RECOVERY_STARTUP_STATUS_CHECKLIST_v1.md
- Snapshot: current runtime state reference at docs/CURRENT_RUNTIME_STATE_SNAPSHOT_v1.md (active phases, checkpoints, canonical path, toggles, open items).
- Why: ensures correct branch/worktree, active phases, canonical path, checkpoints, and safety toggles before resuming work.

## Open / Deferred Items
- Background Analysis Observability Surface (new, doctrine-first)
- Browser front door deferred until core path remains stable

## Next Step
Pending approval: add recovery-oriented startup/status checklist and design observability surface (doctrine-first) for background analysis.
