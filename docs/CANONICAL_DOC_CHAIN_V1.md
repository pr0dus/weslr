# CANONICAL DOC CHAIN v1

## 1. Purpose
Weslr now sits on a sea of doctrine, continuity notes, milestones, recovery rituals, and surface contracts. This file exists because a single authoritative chain is mandatory: it is the official entry point for repo truth, the spine for every recovery/resume, and the only starting point for future cleanup. No ad-hoc deletions or scattershot merges may happen until this file points them out. Cleanup and growth proceed outward from here, never inward.

## 2. Document classification model
Each referenced file is assigned one of the following classes so builders immediately know operational posture:
- **Canonical Core Doctrine:** Immutable safety, identity, and governance foundations (protected core canonization, identity manifesto, etc.).
- **Canonical Roadmap / Milestone:** Sealed-phase status docs, build roadmaps, and release ledger entries documenting what has been built/closed out.
- **Canonical Product / Surface:** Documents that describe proven product surfaces (front-door contracts, dashboard surfaces, etc.).
- **Canonical Capability / Loop:** Files codifying universal capability shapes, loops, contracts, and cross-domain standards.
- **Canonical Recovery / Workflow:** Rituals, startup checklists, continuity controls needed for restarting/resuming.
- **Reference / Specialized Doctrine:** Detailed sub-docs that explain specialized subsystems but only after canonical reading.
- **Merge-Later Candidate:** Valuable overlap that should be merged into canonical docs before being retired.
- **Archive-Later Candidate:** Historical snapshots to keep in archives but not in active reading paths.
- **Delete-Later Candidate:** Files marked for cautious removal once safe; use only with explicit approval.

## 3. Authoritative reading order
Each layer explains what to read and when; mandatory indicates a restart must include it.

**Layer A — Core Truth** (mandatory):
1. `docs/PROTECTED_CORE_CANONIZATION_V1.md` (Canonical Core Doctrine) — defines what may never change; read first on every restart. Mandatory. 
2. `CORE-IDENTITY.md` (Reference / Specialized Doctrine) — identity framing after protected core. Situational.

**Layer B — Build / Milestone Truth** (mandatory):
1. `docs/CANONICAL_BUILD_ROADMAP_V1.md` (Canonical Roadmap / Milestone) — explains the sealed roadmap. Mandatory on every restart.
2. `docs/PHASE_1_CLOSEOUT_AND_PHASE_2_ENTRY.md` (Canonical Roadmap / Milestone) — documents closure of Phase 1. Mandatory if Phase 2 work continues.
3. `docs/PHASE_2_GOVERNED_LANE_CLOSEOUT.md` (Canonical Roadmap / Milestone) — confirms governed lane status; read if working on governance/execution phases.
4. `docs/RELEASES.md` (Canonical Roadmap / Milestone) — historical release ledger; mandatory when aligning rollback history.

**Layer C — Product / Front Door Truth** (mandatory):
1. `docs/FRONT_DOOR_BRIDGE_CONTRACT_v1.md` (Canonical Product / Surface) — explains how the dashboard is wired. Mandatory when editing front door.
2. `docs/UNIVERSAL_GOVERNED_CYCLE_CONTRACT_V1.md` (Canonical Product / Surface) — proves the loop; mandatory before touching UI surfaces.
3. `docs/WORKFLOW_EXECUTION_CONTRACT_v1.md` (Reference / Specialized Doctrine) — execution-level nuances; read situationally.

**Layer D — Capability / Domain Truth** (mandatory):
1. `docs/CAPABILITY_CONTRACT_LAYER_V1.md` (Canonical Capability / Loop) — lays out capability shape; mandatory before adding new features.
2. `docs/REQUEST_INTELLIGENCE_ARCHITECTURE.md` (Reference / Specialized Doctrine) — capability intake architecture; read situationally for ingestion work.
3. `docs/CAPABILITY_INTAKE_ARCHITECTURE_v1.md` (Merge-Later Candidate) — merge into capability contract before retirement.

**Layer E — Recovery / Workflow Truth** (mandatory for recoveries):
1. `docs/RECOVERY_STARTUP_STATUS_CHECKLIST_v1.md` (Canonical Recovery / Workflow) — reboot ritual. Mandatory when restarting.
2. `docs/SELF_CHANGE_RECOVERY_ORCHESTRATION_v1.md` (Reference / Specialized Doctrine) — self-change protection; read during recovery.
3. `HEARTBEAT.md` (Canonical Recovery / Workflow) — heartbeat rules; situational but mandatory for background monitoring.
4. `docs/CONTINUITY_MEMORY_CONSOLIDATION_v1.md` (Reference / Specialized Doctrine) — consolidating memory; situational for continuity work.

## 4. Current canonical set
All canonical files to preserve: `docs/PROTECTED_CORE_CANONIZATION_V1.md`, `docs/CANONICAL_BUILD_ROADMAP_V1.md`, `docs/PHASE_1_CLOSEOUT_AND_PHASE_2_ENTRY.md`, `docs/PHASE_2_GOVERNED_LANE_CLOSEOUT.md`, `docs/FRONT_DOOR_BRIDGE_CONTRACT_v1.md`, `docs/UNIVERSAL_GOVERNED_CYCLE_CONTRACT_V1.md`, `docs/CAPABILITY_CONTRACT_LAYER_V1.md`, `docs/REQUEST_INTELLIGENCE_ARCHITECTURE.md`, `docs/WORKFLOW_EXECUTION_CONTRACT_v1.md`, `docs/ROADMAP.md`, `docs/RELEASES.md`, `docs/RECOVERY_STARTUP_STATUS_CHECKLIST_v1.md`, `HEARTBEAT.md`, `docs/SELF_CHANGE_RECOVERY_ORCHESTRATION_v1.md`, plus any `docs/PHASE*_CHECKPOINT` files referenced above.
Archived artifacts now live in `docs/archive/` (e.g., `docs/archive/HISTORICAL_LAYER_RECONCILIATION_AUDIT_v1.md`, `docs/archive/POST_STEP_SUGGESTION_STANDARD_v1.md`, `docs/archive/ARCHITECTURE_WAVE_ROADMAP_v1.md`) so the canonical chain references their archive paths rather than older directories.

## 5. Recovery order (ritual)
1. `verify_branch`: `git branch --show-current` (confirm you are on `weslr/canonical-clean-signals`).
2. `verify_head`: `git rev-parse HEAD` (confirm last sealed commit). 
3. `inspect_worktree`: `git status --short` (note dirt in runtime files but avoid touching until last sealed doc read).
4. `read_doc_chain`: `cat docs/CANONICAL_DOC_CHAIN_V1.md` (the canonical chain; do this before editing). 
5. `read_core`: follow Layer A & B in order (protected core -> roadmap -> milestone docs). 
6. `confirm_sealed_milestone`: check `docs/PHASE_2_GOVERNED_LANE_CLOSEOUT.md` or other milestone with current sealed commit. 
7. `state_next_step`: review `CURRENT NEXT STEP` inside this doc before editing or branching off.
Continuity memory guidance (interaction, working, consolidated layers plus partitioning and promotion rules) is now embedded here and in the recovery checklist so builders retain conversation-state context without leaking sensitive detail.
Never skip this ritual; treat it as the operational continuity bridge.

## 6. Cleanup governance map
A. **Merge-Later Candidates:**
   - `docs/CONTINUITY_MEMORY_CONSOLIDATION_v1.md` (merge key continuity notes into new canonical doc).
   - `docs/PHASE3_DECISION_LAYER_CHECKPOINT.md` & `PHASE4_EVIDENCE_ACQUISITION_CHECKPOINT.md` (merge summaries into `PHASE_*` master docs before retirement).
   - `docs/CAPABILITY_INTAKE_ARCHITECTURE_v1.md` (incorporate into capability contract). 
   - Before merging: ensure canonical doc mentions the merged concepts and update this chain to reference the merged file.
B. **Archive-Later Candidates:**
   - `docs/HISTORICAL_LAYER_RECONCILIATION_AUDIT_v1.md` (retain for forensic history).
   - `docs/POST_STEP_SUGGESTION_STANDARD_v1.md` (archive after verifying no live links). 
   - `docs/ARCHITECTURE_WAVE_ROADMAP_v1.md` once `CANONICAL_BUILD_ROADMAP_V1.md` fully replaces it. 
   - Before archiving: record location in `docs/CONTINUITY_MEMORY_CONSOLIDATION_v1.md`.
C. **Delete-Later Candidates:**
   - Only consider deleting obsolete phase checkpoint drafts (e.g., `PHASE5_BACKGROUND_ANALYSIS_CHECKPOINT.md`) if their key points appear in canonical docs and approval occurs; mark clearly before deletion.

## 7. Current project state snapshot
- Protected core canonized via `docs/PROTECTED_CORE_CANONIZATION_V1.md`.
- Universal governed cycle formalized in `docs/UNIVERSAL_GOVERNED_CYCLE_CONTRACT_V1.md`.
- Capability contract formalized via `docs/CAPABILITY_CONTRACT_LAYER_V1.md`.
- Front door born and polished (dashboard + suggestion loop) per `docs/FRONT_DOOR_BRIDGE_CONTRACT_v1.md` and `dashboard/index.html` updates.
- First domain loop (observability/governance) closed; second science domain loop now closed via the planetary signal artifact.
- Cross-domain governed proof complete and codified; second-domain loop is live.
- Current next architectural priority: controlled cleanup & doc audit based on this canonical chain before any new capability expansions.

## 8. Current next step
1. Read this canonical doc chain fully. 
2. Then perform the cleanup governance plan (merge/ archive candidates) before touching other directories. 
3. Nothing else is the next step (no immediate feature work or refactors). 

## 9. Quickstart for new windows
```bash
pwd && git branch --show-current && git rev-parse HEAD && \
cat docs/CANONICAL_DOC_CHAIN_V1.md && \
cat docs/PROTECTED_CORE_CANONIZATION_V1.md && \
cat docs/CANONICAL_BUILD_ROADMAP_V1.md && \
cat docs/UNIVERSAL_GOVERNED_CYCLE_CONTRACT_V1.md && \
cat docs/CAPABILITY_CONTRACT_LAYER_V1.md
```
Use this block in every new session to instantly align with repo truth and the sanctioned reading order.

## 10. Result
- this chain is the governance spine; follow it before any recovery, cleanup, or future development.
