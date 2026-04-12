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

## Checkpoint Traceability
- Each major checkpoint commit/doc should reference this snapshot (CURRENT_RUNTIME_STATE_SNAPSHOT_v1.md) as the authoritative state.
- Snapshot should list/latest stable checkpoints so recovery and audits can trace back.
- Add/update links in checkpoint docs to this snapshot where appropriate.

## Canonical Startup + Status Reference
- Core/worktree: weslr/canonical-clean-signals at /data/data/com.termux/files/home/.openclaw/workspace_clean_signals
- Canonical path: route_request → DecisionLayer → anchor (LLM_ANCHOR=local) via thin client/service (browser deferred)
- Startup: `WESLR_CORE_PATH=/data/data/com.termux/files/home/.openclaw/workspace_clean_signals LLM_ANCHOR=local ./scripts/weslr_thin_client.py`
- Status/checkpoints: see PHASES_1_TO_5_ACTIVATION_SUMMARY_v1.md and CURRENT_RUNTIME_STATE_SNAPSHOT_v1.md
- Deferred surfaces: browser UI deferred; legacy/CLI speak prohibited (non-default)

## Deferred Browser Return Conditions
- Canonical backend path (route_request/DecisionLayer) remains stable across checkpoints.
- Thin-client route_request path stays authoritative (no routing regressions).
- Browser send/receive must pass end-to-end test before reactivation.
- Legacy UI paths remain prohibited; only the canonical path may be exposed.
- Checkpoint + snapshot traceability updated when reactivated.

## Browser Reactivation Harness Trigger
- Triggered before any browser reactivation.
- Uses canonical backend (route_request/DecisionLayer) as truth source.
- Validates end-to-end send/receive from browser client to route_request and back.
- Ensures no legacy routing (CLI speak/legacy UI) is involved.
- Confirms response is visible in the browser UI.
- Pass/fail must be recorded in the runtime snapshot before enabling browser surface.

## Browser Reactivation PASS Checklist
Must pass before browser UI reactivation:
- Canonical backend path stable (route_request/DecisionLayer/anchor).
- route_request verified via test message (browser → backend → reply).
- Browser send button functional; response visible in UI.
- No legacy UI path reachable; no CLI speak path reachable.
- Runtime snapshot updated with pass result.
- Checkpoint + traceability updated.

## Browser Reactivation Rollback Criteria
Rollback (disable browser) if any occur:
- Send button failure or no response visibility in UI.
- Routing mismatch (route_request not reached) or legacy/CLI path reappears.
- Repeated E2E harness failures.
- Checkpoint mismatch or snapshot inconsistency after activation.

## Browser Reactivation Go / No-Go Gate
- GO when: PASS checklist completed; no rollback triggers active; E2E harness passing; route_request canonical path stable; no legacy/CLI path reachable; snapshot + checkpoint traceability aligned.
- NO-GO when: any rollback trigger active; harness fail; send/receive fail; snapshot inconsistency; backend instability; legacy route reachable.

## Browser Reactivation Freeze
- Freeze all browser UI work (reactivation, endpoints, send-button, harness, UI routing changes) until an explicit UI return phase is strategically approved.

## Next Queued Follow-Ups
- Refresh snapshot after major checkpoints (activation hygiene)
- Design observability surface (pending approval)
