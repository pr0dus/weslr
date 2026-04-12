# ARCHITECTURE_WAVE_ROADMAP_v1

**Scope:** Roadmap addendum capturing active layers, partial layers, implied missing layers, dependencies, and coding waves. Roadmap freeze only; no coding changes.

## SECTION 1 — ACTIVE LAYERS
- Governance/autonomy boundaries (Phase 1)
- Identity continuity partition/cache (Phase 2)
- Decision Layer with rollback toggle (Phase 3)
- Evidence sufficiency + acquisition (proposal-only) (Phase 4)
- Background analysis engine (internal, proposal-only) (Phase 5)
- Proposal lineage first slice (storage, permissions, observability link, governed reads)
- Cognitive adequacy evaluator + post-proposal hook (proposal-only; reflection toggle off by default; guards fixed)

## SECTION 2 — PARTIAL LAYERS
- Background Analysis Observability Surface: doc/schema present; runtime surface not fully wired.
- Cognitive adequacy reflection: optional toggle, not enabled by default; no wider wiring.
- Observability lineage integration: documented; limited runtime consumption.
- Self-improvement loop: approval-gated doctrine defined; no active self-change beyond reflection toggle.

## SECTION 3 — IMPLIED MISSING LAYERS
- Cognitive Dialogue Interface
- Proposal Lineage Diff View
- Reasoning Strategy Comparison Sandbox
- Adequacy→Lineage/Observability view (surface adequacy findings via lineage/observability)
- Recovery/roll-forward orchestration for approval-gated self-changes

## SECTION 4 — GAP CLASSIFICATION
- Cognitive Dialogue Interface: strategic net-new layer.
- Proposal Lineage Diff View: missing companion layer.
- Reasoning Strategy Comparison Sandbox: strategic net-new layer.
- Adequacy→Lineage/Observability view: existing-layer completion.
- Recovery/roll-forward orchestration for self-changes: existing-layer completion.
- Background Analysis Observability Surface runtime wiring: existing-layer completion.

## SECTION 5 — DEPENDENCY MAP
- Cognitive Dialogue Interface depends on adequacy findings + lineage surfaces.
- Proposal Lineage Diff View depends on lineage storage/observability linking.
- Reasoning Strategy Comparison Sandbox depends on adequacy harness + proposal lineage to compare outcomes.
- Adequacy→Lineage/Observability view depends on adequacy findings + observability surface.
- Recovery/roll-forward orchestration depends on approval-gated self-improvement loop + checkpoints.

## SECTION 6 — CODING WAVES
- Wave 1 (completion): wire Background Analysis Observability Surface + adequacy→lineage/observability view; add guard-regression tests.
- Wave 2 (companion tooling): Proposal Lineage Diff View; recovery/roll-forward orchestration for self-changes.
- Wave 3 (net-new): Cognitive Dialogue Interface; Reasoning Strategy Comparison Sandbox.

## SECTION 7 — NEXT STEP
- Begin Wave 1 execution from this locked roadmap (with approvals as needed for integration work).
