# CANONICAL_BUILD_ROADMAP_V1

## PURPOSE
This document is the authoritative build roadmap. It defines the canonical build order, protected-core hardening order, governed learning loop order, governance embodiment order, continuity decision order, product wedge timing, packaging timing, and anti-drift workflow laws. All future work must map to these phases without drift.

## CURRENT CANONICAL BASELINE
- Contract 1: Main-door chat contract (chat-only entry, no inner-thought leakage, neutral chat fallback, bounded rescues)
- Contract 2: Provider/runtime contract (generate_chat vs generate_inner_thought; role-scoped normalization; provider routing respects chat_mode)
- Contract 3: Stateless continuity contract (main door is stateless; only request fields + explicit chat_context; hints helper-only)
- Contract 4: Governance lane = CDI-only (adequacy → CDI proposal with lineage/evidence → operator approve/deny/refine; self_mod* legacy)
- Contract 5: Bounded observability contract (operator-safe metadata shape; no chain-of-thought leakage)

Protected core modules: llm_runtime.py; weslr/chat_responder.py; weslr/ingress_adapter.py; weslr/cognitive_dialogue_integration.py; weslr/main_door_test_runner.py (tool). 

Legacy/experimental: self_mod_applier.py; self_modifier.py; continuity.py/sim.py; concept_graph; request_intelligence; world.db continuity usage; transcript artifacts.

## PHASED BUILD ROADMAP

### PHASE 1 — Operational hardening
- Provider-live enforcement
- Main-door actionability strengthening
- Repeated-run validation
- Operator-safe runtime truth strengthening

### PHASE 2 — Governed learning loop wiring v1
- Inadequacy persistence
- Threshold / trigger logic
- CDI proposal wiring
- Lineage enforcement
- Operator decision persistence
- Execution eligibility state
- Audit / history

### PHASE 3 — Governance embodiment
- Operator review flow
- Decision state tracking
- Verification / revert semantics

### PHASE 4 — Continuity decision
- Choose one canonical continuity substrate
- No continuity promotion before governance loop maturity

### PHASE 5 — Minimal operator surface
- Bounded metadata visibility
- Governance state visibility
- Continuity truth visibility

### PHASE 6 — Product wedge execution
- Industrial / engineering wedge
- TIA later

### PHASE 7 — Installer / deployment / packaging
- Only after stable wedge + governance maturity

## CANONICAL RULES
- Every next task must map to exactly one phase; no mixed-phase work.
- Checkpoint after each coherent phase.
- Verify code reality before assuming missing/existing pieces.
- No accidental promotion of experimental code.
- No legacy self_mod path reactivation.
- No continuity promotion before Phase 4.
- No packaging before Phase 7.

## ANTI-DRIFT RULES
- No architecture work outside roadmap phases.
- No casual patching of protected-core contracts.
- No parallel learning lanes; CDI remains the sole sanctioned improvement lane.
- All future major prompts must reference this file.
