# CURRENT_RUNTIME_STATE_SNAPSHOT_v1

## Active Phases (1–5)
- Phase 1: Governance gate/autonomy boundaries — ACTIVE (checkpoint: 35f3018)
- Phase 2: Identity continuity partition/cache — ACTIVE (checkpoint: b9c246e3ef0c27114a7073c5b8b265ec833f7f00)
- Phase 3: Decision Layer with rollback toggle — ACTIVE (checkpoint: 98417f6; rollback test: 7bb80ad)
- Phase 4: Evidence sufficiency + acquisition proposals only — ACTIVE (checkpoint: 888f292; harness: test_phase4_evidence_acquisition_dryrun.py)
- Phase 5: Background analysis engine internal-only/proposal-only — ACTIVE (checkpoint: 0349d6b; summary: PHASE5_BACKGROUND_ANALYSIS_CHECKPOINT.md)

## Latest Canonical Path
- Conversational path: route_request → DecisionLayer → anchor (LLM_ANCHOR=local) via thin client/service (browser deferred; CLI speak non-default)
- Identity continuity: partitioned by (workspace_id, user_id); stateless when unresolved
- Governance gate: ON; approvals/overrides per policy

## Safety Toggles / Rollback Flags
- Decision Layer rollback toggle available (DECISION_LAYER_PHASE3_ACTIVE)
- Evidence acquisition: proposals-only; can disable proposals → assessment-only
- Background analysis: internal-only; pause/stop/rollback paths available
- Governance/autonomy boundaries: owner/operator override to tighten/rollback

## Deferred Surfaces
- Browser UI deferred until core path remains stable
- Legacy/CLI speak: non-default (debug only)

## Checkpoints (recent)
- Phases 1–5 activation checkpoints: see PHASES_1_TO_5_ACTIVATION_SUMMARY_v1.md
- Latest HEAD: see git log (branch weslr/canonical-clean-signals)

## Open Items / Queued Follow-Ups
- Existing follow-up (auto-sequenced): keep snapshot/recovery checklist references current after checkpoints
- New gap/idea: Background Analysis Observability Surface (doctrine-first, approval required)

## Snapshot Refresh Discipline
Refresh the snapshot when any of the following occur:
- Phase go-live checkpoint (activation/rollback)
- Rollback checkpoint applied
- New governance layer activation
- Canonical path changes
- Major runtime documentation changes (activation summary, recovery checklist)
- Recovery checklist changes

Refresh rules:
- Responsibility: system-autonomous (auto-sequenced) to keep snapshot authoritative.
- Update: active phases, checkpoints, canonical path, toggles, deferred surfaces, open items, queued follow-ups, escalated net-new items.
- Carry-forward: queued follow-ups and net-new escalations are retained/updated in the snapshot.

## Next Queued Follow-Ups
- Refresh snapshot after major checkpoints (activation hygiene)
- Design observability surface (pending approval)
