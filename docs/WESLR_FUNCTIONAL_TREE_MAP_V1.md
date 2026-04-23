# WESLR FUNCTIONAL TREE MAP V1
**Generated:** 2026-04-22 07:02 GMT+2  
**Purpose:** Canonical working surface inventory for debugging, canonization, and safe future work  
**Mode:** STRICT — inspection only, no code changes, no design proposals

---

## SECTION 1 — PURPOSE

This document maps the complete functional architecture of WESLR as a working system — not a directory listing, but a **living architecture tree**.

It exists so that:
- **Debugging** can locate the correct files without rediscovering the system
- **Canonization** work knows which modules are canonical vs. supporting vs. parallel
- **Future improvement** happens on a known surface, not fragments

**Scope:** Everything in the repo that is actively loaded, referenced, or storing state.  
**Exclusions:** `_out_of_scope/`, `_staging/`, `weslr-tia-openness-bridge/` (separate private repo), `COMMERCIAL-FILES/` (commercial premium), `docs/archive/` (historical).

---

## SECTION 2 — TOP-LEVEL TREE

```
/data/data/com.termux/files/home/.openclaw/workspace/
├── main.py                      [ACTIVE]  7899 lines — CLI entry, 112 command functions, HTTP server on port 8001
├── dialogue.py                  [ACTIVE]  2198 lines — Conversation/dialogue orchestration, artifact reference resolution
├── llm_runtime.py                [ACTIVE]   720 lines — LLM provider abstraction (Ollama/OpenAI compatible)
├── agent_runtime.py              [ACTIVE]     ~600 lines — Multi-agent simulation runtime (agents/ dir)
├── chat_ui.py                   [ACTIVE]     ~560 lines — HTTP chat UI (single-file HTML server)
├── weslr_backend_contract.py    [ACTIVE]     ~960 lines — App shell backend API contract
│
├── weslr/                        [ACTIVE]  Core package — ~450+ Python modules, ~2.5MB
│   ├── chat_responder.py       [CANONICAL]  WESLR-owned conversational surface formatter
│   ├── artifact_store.py       [CANONICAL]  Persistent artifact storage (continuity/artifacts/)
│   ├── suggestion_box.py       [CANONICAL]  Capability request intake layer
│   ├── governance_surface.py   [CANONICAL]  Unified operator governance surface (proposal chain)
│   ├── surface_to_spine_bridge.py [CANONICAL] Artifact weakness → Step 1 inadequacy event bridge
│   ├── cognitive_adequacy.py   [CANONICAL]  CDI detection/threshold engine (proposal-only evaluator)
│   ├── institution.py          [CANONICAL]  Layer 2 role timeline foundation
│   ├── voice_gateway.py        [ACTIVE]     WebSocket voice gateway (Phase 1A, STT shim)
│   ├── thread_tracker.py        [ACTIVE]     Thread surface tracking
│   ├── interest_tracker.py     [ACTIVE]     Interest/relevance tracking (interests.json)
│   ├── relevance_surface.py    [ACTIVE]     Relevance advisory surface
│   ├── relevance_eval_runner.py [ACTIVE]     Relevance evaluation runner
│   ├── internal_reasoning_graph/ [CANONICAL] Reasoning + governance graph (7 modules)
│   ├── concept_graph/           [CANONICAL]  Bridge: entity_graph + evidence + runtime
│   ├── request_intelligence/    [ACTIVE]     Request classification/matching (8 modules)
│   ├── continuity/              [ACTIVE]     Calibration data (SQLite db)
│   ├── evidence_intake/         [CANONICAL]  Evidence → candidate pipeline (4 modules)
│   ├── background_analysis/     [EMPTY]      (no modules present)
│   └── tests/                   [ACTIVE]      Unit tests (per-module test_*.py files)
│
├── commands/                    [ACTIVE]  Modular CLI subcommand framework
│   ├── __init__.py             [CANONICAL]  Dynamic command registry
│   ├── entities.py             [CANONICAL]  entity-list/details/merge/promote/search/stats
│   ├── agents.py                [CANONICAL]  agent-list/details
│   ├── memory.py                [CANONICAL]  memory list/show/prune
│   ├── selfmod.py              [CANONICAL]  selfmod list/apply/rollback/log
│   ├── opportunity.py          [CANONICAL]  opportunity list/transition
│   ├── variation.py             [CANONICAL]  variation generate/list
│   ├── tools.py                 [CANONICAL]  explain/search/lookup
│   ├── interest.py              [CANONICAL]  interest list/track/stop
│   ├── capability.py           [CANONICAL]  capability list/ingest/suggest/show
│   ├── thread.py                [CANONICAL]  thread list/show
│   ├── speak.py                 [CANONICAL]  speak voice/role
│   ├── steuer.py                [ACTIVE]     German tax knowledge commands
│   └── weslr_time.py           [ACTIVE]     Weslr time commands
│
├── continuity/                  [ACTIVE]  Long-term continuity storage
│   ├── history.json            [ACTIVE]      Conversation history
│   ├── latest.json             [ACTIVE]      Latest continuity state
│   ├── metrics.json            [ACTIVE]      Continuity metrics
│   ├── debt.json               [ACTIVE]      Debt tracking
│   ├── task_anchor.json        [ACTIVE]      Task anchor state
│   ├── improvement_engine/     [ACTIVE]      Recommendations + history
│   ├── pilot_signals/          [ACTIVE]      User events + signal tracking
│   ├── snapshots/              [ACTIVE]      Snapshot state
│   ├── suggestion_box/         [ACTIVE]      requests.json + continuity.json
│   └── artifacts/             [ACTIVE]      Stored artifacts + index + eval/
│
├── agents/                      [ACTIVE]  Agent simulation runtime
│   ├── agent-1/, agent-2/, agent-3/, agent-4/
│   │   ├── memory.json
│   │   ├── inbox.json
│   │   ├── opportunity_memory.json
│   │   ├── artifacts/
│   │   └── modules/helper_agent-*.py
│
├── weslr-ui/                    [ACTIVE]  React frontend (vite + TS)
│   ├── App.tsx                 [CANONICAL]  Main React component
│   ├── api.ts                  [CANONICAL]  API client bindings
│   ├── config.ts               [CANONICAL]  Frontend config
│   └── main.tsx                [CANONICAL]  React entry point
│
├── tests/                       [ACTIVE]  Integration test suite
│   ├── test_chat_ui_identity_cache.py
│   ├── test_suggestion_box.py
│   ├── test_suggestion_bridge.py
│   ├── test_suggestion_assessment.py
│   └── test_weslr_operator_views.py
│
├── docs/                        [MIXED]   Documentation + memory logs
│   ├── architecture.md         [ACTIVE]    WESLR architecture reference
│   ├── safety-boundaries.md    [ACTIVE]    Safety contract docs
│   ├── WESLR-HEALTH.md         [ACTIVE]    Health check documentation
│   ├── tia-bridge/             [ACTIVE]    Commercial TIA Portal integration docs
│   ├── steuerwesen/            [ACTIVE]    German tax knowledge documentation
│   ├── memory/                  [ACTIVE]    Session memory logs (YYYY-MM-DD.md)
│   └── *.md                    [ACTIVE]    Phase contracts, roadmaps, standards
│
├── .weslr/timelines/           [ACTIVE]  Timeline storage
│   └── tl_default/events.jsonl
│
├── weslr_main.py               [ACTIVE]  Alternative CLI entry point
├── weslr_cli.py               [ACTIVE]  CLI interface (legacy path, still referenced)
├── config.py                   [CANONICAL]  Configuration loader
├── state_core.json             [ACTIVE]     Core state
├── workspace_state.json        [ACTIVE]     Full workspace state (~54KB)
│
└── [jsonl stores]             [ACTIVE]     Inadequacy/proposal/CDI/governance event logs
```

---

## SECTION 3 — FUNCTIONAL SUBTREES

### 3.1 Conversation / Dialogue

| File | Purpose | Key Functions/Classes | Classification |
|------|---------|----------------------|----------------|
| `dialogue.py` | Conversation orchestration, artifact reference resolution | `_is_artifact_reference_phrase()`, `_resolve_active_artifact()`, `classify_human_turn()`, `interpret_human_turn()` | **CANONICAL** |
| `weslr/chat_responder.py` | WESLR-owned conversational response formatter | `Response` dataclass, `format_reasoning_surface()`, `get_explanation_session()`, `_synthesize_active_context()` | **CANONICAL** |
| `chat_ui.py` | HTTP HTML chat UI (simple single-file server) | `WeslrRequestHandler`, `/api/send`, `/api/state` | **CANONICAL** |
| `llm_runtime.py` | LLM provider abstraction layer | `generate_inner_thought()`, `generate_chat()`, `provider_state()` | **CANONICAL** |

**Parallel/Fragmented Areas:**
- `chat_ui.py` (simple HTTP) vs `weslr-ui/` (React SPA) — two different UI entry points
- `chat_responder.py` is WESLR-owned; `weslr_backend_contract.py` has its own chat endpoint

---

### 3.2 Runtime / Communicator

| File | Purpose | Key Functions/Classes | Classification |
|------|---------|----------------------|----------------|
| `main.py` | Main CLI + HTTP server (port 8001) | 7899 lines, 112 command functions, `WeslrRequestHandler`, all `/api/*` endpoints | **CANONICAL** |
| `agent_runtime.py` | Multi-agent simulation world | `load_notes()`, `save_inbox()`, `decide_action()`, `choose_target()`, `opportunity_memory_*` | **CANONICAL** |
| `communicator_state.json` | Communicator state snapshot | — | **SUPPORTING** |
| `communicator_self.json` | Self-communicator state | — | **SUPPORTING** |
| `weslr/voice_gateway.py` | WebSocket voice gateway (Phase 1A STT shim) | `VoiceGateway`, `stt_transcribe()`, `set_weslr_http_port()` | **ACTIVE** |

---

### 3.3 Artifacts / Artifact Storage / Artifact Revision

| File | Purpose | Key Functions/Classes | Classification |
|------|---------|----------------------|----------------|
| `weslr/artifact_store.py` | Persistent artifact storage | `save_artifact()`, `get_artifact()`, `list_artifacts()`, `get_active_artifact()`, `set_active_artifact()`, `_generate_artifact_id()` | **CANONICAL** |
| `continuity/artifacts/` | Storage directory for artifacts | `art-*.json` files + `index.json` | **CANONICAL** |
| `continuity/artifacts/eval/` | Evaluation artifact storage | `eval-*.json` files + `index.json` | **CANONICAL** |
| `dialogue.py` | Artifact reference detection | `_is_artifact_reference_phrase()`, `_resolve_active_artifact()` | **CANONICAL** |
| `sim.py` | Artifact proof/explainability infrastructure | `find_meta_file_by_id()`, `build_artifact_explainability()`, `update_artifact_scores()`, `get_artifact_proof()` | **CANONICAL** |

---

### 3.4 Interests / Relevance / Suggestion / Thread

| File | Purpose | Key Functions/Classes | Classification |
|------|---------|----------------------|----------------|
| `weslr/interest_tracker.py` | Interest tracking | Functions for tracking/stopping interests | **ACTIVE** |
| `weslr/interests.json` | Interest store | JSON state | **ACTIVE** |
| `weslr/threads.json` | Thread store | JSON state | **ACTIVE** |
| `weslr/thread_tracker.py` | Thread surface tracking | Thread tracking logic | **ACTIVE** |
| `weslr/relevance_surface.py` | Relevance advisory surface | Relevance evaluation interface | **ACTIVE** |
| `weslr/relevance_eval_runner.py` | Relevance evaluation runner | Runs relevance evaluation | **ACTIVE** |
| `weslr/relevance_eval_analysis.py` | Relevance analysis output | Analysis results | **ACTIVE** |
| `weslr/capability_suggestion.py` | Capability suggestion engine | Suggestion generation | **CANONICAL** |
| `continuity/suggestion_box/requests.json` | Suggestion request storage | JSON store | **CANONICAL** |
| `continuity/suggestion_box/continuity.json` | Suggestion continuity | JSON store | **CANONICAL** |

**Parallel/Fragmented Areas:**
- `interest_tracker.py` + `interests.json` vs `thread_tracker.py` + `threads.json` — two different tracking systems
- `capability_suggestion.py` and `suggestion_box.py` both handle suggestions with different scopes

---

### 3.5 Self-Improvement / Proposals / Governance

| File | Purpose | Key Functions/Classes | Classification |
|------|---------|----------------------|----------------|
| `self_improvement_proposal.py` | Proposal creation/management | `get_proposals()`, `create_proposal()`, `approve_proposal()`, `_is_public_visible()`, `_filter_for_visibility()` | **CANONICAL** |
| `self_improvement_apply.py` | Proposal application | Apply logged proposals to system | **CANONICAL** |
| `self_improvement_chat.py` | Proposal chat interface | Chat-facing proposal interaction | **CANONICAL** |
| `self_improvement_observation.py` | Observation recording | Observation event capture | **CANONICAL** |
| `weslr/governance_surface.py` | Unified operator governance surface | `ProposalGovernanceView`, `GovernanceSession`, `get_proposal_view()` | **CANONICAL** |
| `weslr/change_proposals.py` | Change proposal data model | `ChangeProposal`, `ExecutionGate`, `ProposalState` | **CANONICAL** |
| `weslr/proposal_realization.py` | Realization planning | `RealizationEngine`, `RealizationPlan` | **CANONICAL** |
| `weslr/audit_ledger.py` | Audit trail | Audit logging | **CANONICAL** |
| `self_improvement_proposals.json` | Proposal store | JSON persistence | **SUPPORTING** |
| `self_improvement_approval_log.json` | Approval log | JSON persistence | **SUPPORTING** |

---

### 3.6 Inadequacy / CDI / Spine

| File | Purpose | Key Functions/Classes | Classification |
|------|---------|----------------------|----------------|
| `weslr/inadequacy_trigger.py` | Trigger detection | `find_candidates()`, `_load_events()` | **CANONICAL** |
| `weslr/inadequacy_intake.py` | Intake processing | Processes handoffs, routes to CDI | **CANONICAL** |
| `weslr/inadequacy_persistence.py` | Event persistence | `record_inadequacy_event()` | **CANONICAL** |
| `weslr/inadequacy_handoff.py` | Handoff routing | `InadequacyHandoff` dataclass | **CANONICAL** |
| `weslr/cognitive_adequacy.py` | CDI threshold engine | `evaluate()` with THRESHOLDS dict | **CANONICAL** |
| `weslr/cdi_proposal_builder.py` | CDI proposal generation | `build_proposals()`, `STORAGE_PROPOSALS/STORAGE_DECISIONS` | **CANONICAL** |
| `weslr/cdi_decision_log.py` | CDI decision logging | Decision record logging | **CANONICAL** |
| `weslr/surface_to_spine_bridge.py` | Artifact → Spine bridge | `BridgePreview`, `ProvenanceRecord`, `record_inadequacy_event()` | **CANONICAL** |

**Data Stores:**
| File | Purpose | Writer | Readers |
|------|---------|--------|---------|
| `weslr_inadequacy_events.jsonl` | Inadequacy events | `inadequacy_persistence.py` | trigger, intake, CDI |
| `weslr_inadequacy_intake.jsonl` | Intake records | `inadequacy_intake.py` | CDI review |
| `weslr_inadequacy_handoffs.jsonl` | Handoff records | `inadequacy_handoff.py` | intake, trigger |
| `weslr_cdi_decisions.jsonl` | CDI decisions | CDI decision layer | proposal builder |
| `weslr_cdi_proposals.jsonl` | CDI proposals | `cdi_proposal_builder.py` | governance |

---

### 3.7 SatUi / Backend / Web Entry Points

| File | Purpose | Entry Points | Classification |
|------|---------|--------------|----------------|
| `chat_ui.py` | Simple HTTP chat UI | `http://localhost:8001` — single-file HTML server | **CANONICAL** |
| `weslr-ui/` | React SPA frontend | `http://localhost:5173` (vite dev server) | **ACTIVE** |
| `weslr_backend_contract.py` | App shell backend contract | `/api/conversations`, `/api/continuity`, `/api/chat`, `/api/upload` | **ACTIVE** |
| `main.py` | Main HTTP API server | All `/api/*` endpoints (8001) | **CANONICAL** |
| `weslr/voice_gateway.py` | WebSocket voice | `ws://localhost:{port}/voice` | **ACTIVE** |

**Fragmented Areas:**
- `chat_ui.py` (simple) and `weslr-ui/` (React) both serve chat but are separate codebases
- `main.py` and `weslr_backend_contract.py` both define API endpoints

---

### 3.8 Continuity / Memory Tiers / Timelines

| File | Purpose | Key Functions/Classes | Classification |
|------|---------|----------------------|----------------|
| `continuity.py` | Continuity orchestration | `ContinuityManager`, `continuity_from_message()` | **CANONICAL** |
| `continuity_prioritizer.py` | Priority calculation | Priority scoring | **CANONICAL** |
| `continuation_notes.py` / `.json` | Session continuation | Continuation notes storage | **SUPPORTING** |
| `session_continuity.py` | Session-level continuity | Session continuity helpers | **CANONICAL** |
| `semantic_memory.py` | Semantic memory layer | Semantic memory interface | **SUPPORTING** |
| `continuity/consolidation.py` | Memory consolidation | `ConsolidationEngine` | **CANONICAL** |
| `continuity/history.json` | Continuity history | JSON store | **SUPPORTING** |
| `continuity/latest.json` | Latest state | JSON store | **SUPPORTING** |
| `continuity/metrics.json` | Continuity metrics | JSON store | **SUPPORTING** |
| `.weslr/timelines/tl_default/events.jsonl` | Timeline event log | Timeline events | **CANONICAL** |

**Note:** Multiple overlapping continuity systems exist: `continuity.py`, `continuation_notes.py`, `session_continuity.py`, and `continuity/` directory storage are all separate mechanisms.

---

### 3.9 Evaluation / Analysis / Test Harnesses

| File | Purpose | Key Functions/Classes | Classification |
|------|---------|----------------------|----------------|
| `continuity/artifacts/eval/index.json` | Eval artifact index | — | **SUPPORTING** |
| `eval-*.json` files | Individual eval results | — | **SUPPORTING** |
| `tests/test_*.py` | Integration tests | pytest suite | **CANONICAL** |
| `weslr/tests/test_*.py` | Unit tests per module | pytest suite | **CANONICAL** |
| `weslr/test_harness.py` | Test harness framework | `TestHarness` | **CANONICAL** |
| `weslr/test_cognitive_relevance_suite.py` | Cognitive relevance tests | `CognitiveRelevanceSuite` | **CANONICAL** |
| `test_artifact_quality_feedback.py` | Artifact quality tests | Quality feedback tests | **ACTIVE** |
| `test_runtime_relevance_integration.py` | Runtime relevance tests | Integration tests | **ACTIVE** |
| `continuity/artifacts/eval/` | Eval artifacts storage | `eval-*.json` | **SUPPORTING** |

---

### 3.10 Internal Reasoning Graph / Governance Graph

| File | Purpose | Key Functions/Classes | Classification |
|------|---------|----------------------|----------------|
| `weslr/internal_reasoning_graph/__init__.py` | Package init | — | **CANONICAL** |
| `weslr/internal_reasoning_graph/models.py` | Graph data models | `Node`, `NodeFactory`, `ProposalStatus` | **CANONICAL** |
| `weslr/internal_reasoning_graph/governance.py` | Governance engine | `GovernanceAction`, `GovernanceDecision`, `ProposalReviewRecord` | **CANONICAL** |
| `weslr/internal_reasoning_graph/reasoning_engine.py` | Reasoning engine | Reasoning processing | **CANONICAL** |
| `weslr/internal_reasoning_graph/store.py` | Graph storage | Graph persistence | **CANONICAL** |
| `weslr/internal_reasoning_graph/query.py` | Graph queries | Query interface | **CANONICAL** |
| `weslr/internal_reasoning_graph/validation.py` | Graph validation | Validation logic | **CANONICAL** |
| `weslr/internal_reasoning_graph/proposal_workflow.py` | Proposal workflow | Lifecycle management | **CANONICAL** |

**Concept Graph Bridge:**
| File | Purpose | Key Functions/Classes | Classification |
|------|---------|----------------------|----------------|
| `weslr/concept_graph/__init__.py` | Package init | — | **CANONICAL** |
| `weslr/concept_graph/bridge/entity_graph.py` | Entity graph bridge | Entity resolution | **CANONICAL** |
| `weslr/concept_graph/bridge/evidence.py` | Evidence bridge | Evidence integration | **CANONICAL** |
| `weslr/concept_graph/bridge/runtime.py` | Runtime bridge | Runtime integration | **CANONICAL** |

---

## SECTION 4 — ENTRY POINTS

### 4.1 Chat Entry Points

| File/Function | Calls Next | Canonical? |
|--------------|-----------|------------|
| `chat_ui.py` → `WeslrRequestHandler.do_POST(/api/send)` | `dialogue.py` handle functions | **YES** |
| `weslr-ui/App.tsx` → `sendMessage()` | `weslr_backend_contract.py` `/api/chat` | **YES** |
| `main.py` → `/api/chat` endpoint | `llm_runtime.generate_chat()` | **YES** |

### 4.2 Backend Contract Entry Points

| File/Function | Calls Next | Canonical? |
|--------------|-----------|------------|
| `weslr_backend_contract.py` → `get_conversation_list()` | `entity_graph.py` | **YES** |
| `weslr_backend_contract.py` → `get_continuity_status()` | `continuity/latest.json` | **YES** |
| `weslr_backend_contract.py` → `upload_file()` | `file_router.py` | **YES** |
| `weslr_backend_contract.py` → `/api/chat` | `dialogue.py` | **YES** |

### 4.3 HTTP Server Entry Points

| File/Function | Port | Canonical? |
|--------------|------|------------|
| `main.py` → `ThreadingHTTPServer` | 8001 | **YES** |
| `chat_ui.py` → `ThreadingHTTPServer` | 8001 | **YES** (simple UI) |

### 4.4 CLI Command Entry Points

| File | Commands | Canonical? |
|------|---------|------------|
| `main.py` | 112 command functions (`handle_*`) | **YES** |
| `weslr_main.py` | Subcommand routing via `commands/` | **YES** |
| `weslr_cli.py` | Legacy CLI (still referenced) | **LEGACY** |

### 4.5 Automated/Background Flows

| Flow | Trigger | Files in Chain |
|------|---------|---------------|
| Inadequacy → CDI | `inadequacy_trigger.find_candidates()` → write to `weslr_cdi_decisions.jsonl` | `inadequacy_trigger.py` → `inadequacy_intake.py` → `cdi_proposal_builder.py` |
| Artifact weakness → Spine | `surface_to_spine_bridge` preview/confirm mode | `surface_to_spine_bridge.py` → `inadequacy_persistence.py` |
| Proposal governance | `governance_surface.py` operator review | `governance_surface.py` → `change_proposals.py` → `proposal_realization.py` |
| Self-improvement cycle | `self_improvement_proposal.py` → operator approval | `proposal.py` → `governance_surface.py` → `self_improvement_apply.py` |

---

## SECTION 5 — MAJOR DATA STORES

| File/Path | Purpose | Writer Authority | Reader Surfaces |
|-----------|---------|-----------------|-----------------|
| `continuity/artifacts/index.json` | Artifact registry | `artifact_store.py` | dialogue, chat_responder, sim |
| `continuity/artifacts/art-*.json` | Individual artifacts | `artifact_store.save_artifact()` | dialogue, surface_to_spine_bridge |
| `continuity/artifacts/eval/index.json` | Eval artifact registry | test/eval runners | analysis, test_harness |
| `continuity/artifacts/eval/eval-*.json` | Eval results | test runners | `test_artifact_quality_feedback.py` |
| `weslr/interests.json` | Interest tracking state | `interest_tracker.py` | relevance_surface, chat_responder |
| `weslr/threads.json` | Thread tracking state | `thread_tracker.py` | thread commands, relevance |
| `continuity/suggestion_box/requests.json` | Capability requests | `suggestion_box.py` | governance, capability_suggestion |
| `continuity/suggestion_box/continuity.json` | Suggestion continuity | `suggestion_box.py` | continuity consolidation |
| `self_improvement_proposals.json` | Proposal store | `self_improvement_proposal.py` | governance_surface, chat |
| `self_improvement_approval_log.json` | Approval log | `self_improvement_proposal.py` | governance audit |
| `weslr_inadequacy_events.jsonl` | Inadequacy event log | `inadequacy_persistence.py` | trigger, intake, CDI |
| `weslr_inadequacy_intake.jsonl` | Intake records | `inadequacy_intake.py` | CDI pipeline |
| `weslr_inadequacy_handoffs.jsonl` | Handoff records | `inadequacy_handoff.py` | intake, trigger |
| `weslr_cdi_decisions.jsonl` | CDI decisions | CDI decision layer | proposal builder |
| `weslr_cdi_proposals.jsonl` | CDI proposals | `cdi_proposal_builder.py` | governance |
| `weslr_governance_reviews.jsonl` | Governance review events | `governance_surface.py` | audit, recovery |
| `weslr_apply_eligibility.jsonl` | Apply eligibility events | `apply_eligibility_gate.py` | recovery, benchmark |
| `weslr_apply_staging.jsonl` | Apply staging events | staging layer | execution, recovery |
| `continuity/history.json` | Conversation history | continuity system | dialogue, chat |
| `continuity/latest.json` | Latest continuity state | continuity system | all continuity consumers |
| `.weslr/timelines/tl_default/events.jsonl` | Timeline events | voice_gateway, runtime | recovery, insight |
| `workspace_state.json` | Full workspace state (~54KB) | main.py state management | operator views, diagnostics |

---

## SECTION 6 — DEPENDENCY / FLOW MAP

### Chat Input → Dialogue → Response
```
chat_ui.py (HTTP) 
  → main.py WeslrRequestHandler.do_POST(/api/send)
  → dialogue.py classify_human_turn() + interpret_human_turn()
  → llm_runtime.generate_chat()
  → weslr/chat_responder.py format_reasoning_surface()
  → response back to client
```

### Artifact Generation → Artifact Store → Reference Resolution
```
dialogue.py (user asks for analysis/improvement)
  → llm_runtime generates content
  → weslr/artifact_store.save_artifact()
  → continuity/artifacts/art-*.json + index.json update
  → set_active_artifact() marks session artifact

User later says "improve this" → dialogue._is_artifact_reference_phrase()
  → _resolve_active_artifact() → artifact_store.get_artifact()
  → research_context populated → response generation
```

### Suggestion → Bridge → Proposal Review
```
suggestion_box.py (submit capability request)
  → requests.json written
  → governance_surface.OperatorProposalReview triggered
  → change_proposals.ChangeProposal created
  → operator approval required
  → self_improvement_apply.py on approval
```

### Inadequacy → Trigger → Handoff → CDI
```
inadequacy_trigger.find_candidates() 
  → reads weslr_inadequacy_events.jsonl
  → detects recurring pattern (WINDOW_MINUTES=60, MIN_RECURRENCE=2)
  → inadequacy_handoff.py creates handoff record
  → writes weslr_inadequacy_handoffs.jsonl

inadequacy_intake.py processes handoffs
  → writes weslr_inadequacy_intake.jsonl
  → qualifies → "cdi_review" status

cdi_proposal_builder.build_proposals()
  → reads weslr_cdi_decisions.jsonl
  → writes weslr_cdi_proposals.jsonl
  → governance_surface.py operator review
```

### Artifact Weakness → Spine (Surface-to-Spine Bridge)
```
surface_to_spine_bridge.py (preview mode)
  → sim.find_meta_file_by_id() loads artifact
  → BridgePreview object built
  → validate_bridge() checks structure

surface_to_spine_bridge.py (confirm mode)
  → inadequacy_persistence.record_inadequacy_event()
  → writes weslr_inadequacy_events.jsonl
  → enters inadequacy trigger cycle
```

### Relevance → Runtime Advisory Metadata
```
interest_tracker.py tracks user interests
  → writes weslr/interests.json
  → relevance_surface.py reads interests
  → relevance_eval_runner.py evaluates
  → chat_responder._synthesize_active_context() uses for response shaping
```

### Eval Runner → Eval Artifact → Analysis
```
test_artifact_quality_feedback.py (or similar test harness)
  → generates eval result
  → writes continuity/artifacts/eval/eval-*.json
  → eval index updated
  → test_surface reads for assertions
```

### Governance Proposal Flow
```
self_improvement_proposal.py create_proposal()
  → writes self_improvement_proposals.json
  → governance_surface.get_proposal_view() packages for operator
  → operator reviews via governance surface
  → approve_proposal() or reject_proposal()
  → on approval: self_improvement_apply.apply()
```

---

## SECTION 7 — KNOWN PARALLEL / FRAGMENTED AREAS

### 7.1 Suggestion / Proposal Flows
- `suggestion_box.py` — external capability requests (institutions, individuals)
- `capability_suggestion.py` — internal suggestion generation
- `self_improvement_proposal.py` — system self-improvement proposals
- `cdi_proposal_builder.py` — CDI-triggered proposals
- `insight_proposal_layer.py` — insight-based proposals
**Issue:** 5 overlapping proposal paths with different triggers and storage

### 7.2 SatUi / Backend / Chat Surfaces
- `chat_ui.py` — simple single-file HTTP server on port 8001
- `weslr-ui/` — React SPA (separate vite server)
- `weslr_backend_contract.py` — backend API (referenced by weslr-ui)
- `main.py` — full HTTP API server (port 8001)
- `voice_gateway.py` — WebSocket voice (Phase 1A)
**Issue:** Chat UI is fragmented; 3+ different chat entry points

### 7.3 Artifact Revision vs Proposal Systems
- `artifact_store.py` — stores artifacts with revisions
- `sim.py` — artifact explainability and proof
- `surface_to_spine_bridge.py` — artifact weakness → inadequacy
- `change_proposals.py` — proposal data model
- `proposal_realization.py` — realization planning
**Issue:** Artifact revision and proposal systems run in parallel with different triggers

### 7.4 Governance vs Advisory Systems
- `governance_surface.py` — operator-facing governance (proposals)
- `relevance_surface.py` — relevance advisory (no governance)
- `suggestion_bridge.py` — suggestion assessment bridge
- `cognitive_adequacy_hook.py` — CDI hook (governance-adjacent)
- `internal_reasoning_graph/governance.py` — graph governance engine
**Issue:** Governance is split across surface + graph + CDI with unclear boundaries

### 7.5 Continuity / Memory Systems
- `continuity.py` + `continuity/*.json` — primary continuity
- `continuation_notes.py` + `continuation_notes.json` — session notes
- `session_continuity.py` — session-level helpers
- `semantic_memory.py` — semantic layer (stub)
- `.weslr/timelines/` — timeline event log
- `memory/` directory — daily session logs (docs/memory/)
**Issue:** 6+ overlapping continuity/memory mechanisms with unclear scope boundaries

### 7.6 Interest / Thread Tracking
- `interest_tracker.py` + `interests.json` — interest tracking
- `thread_tracker.py` + `threads.json` — thread tracking
- `relevance_surface.py` — relevance evaluation
- `relevance_eval_runner.py` — relevance evaluation runner
**Issue:** Interest and thread are separate systems; unclear if redundant or intentionally separate

---

## SECTION 8 — DEBUGGING INDEX

### Greeting/Routing Bug
**Inspect first:** `dialogue.py` → `classify_human_turn()`, `interpret_human_turn()`

### Artifact Reference Bug
**Inspect first:** `dialogue.py` → `_is_artifact_reference_phrase()`, `_resolve_active_artifact()`, `weslr/artifact_store.py` → `get_active_artifact()`

### Relevance Missing
**Inspect first:** `weslr/interest_tracker.py`, `weslr/interests.json`, `weslr/relevance_surface.py`, `weslr/relevance_eval_runner.py`

### Proposal Review Issue
**Inspect first:** `self_improvement_proposal.py`, `weslr/governance_surface.py`, `self_improvement_proposals.json`, `governance_reviews.jsonl`

### Artifact Persistence Issue
**Inspect first:** `weslr/artifact_store.py`, `continuity/artifacts/index.json`, `continuity/artifacts/` directory

### Inadequacy → CDI Pipeline Issue
**Inspect first:** `weslr/inadequacy_trigger.py` (find_candidates), `weslr/inadequacy_intake.py`, `weslr/cdi_proposal_builder.py`, `weslr/cognitive_adequacy.py` (THRESHOLDS)

### Surface-to-Spine Bridge Issue
**Inspect first:** `weslr/surface_to_spine_bridge.py` (BridgePreview class), `sim.py` (find_meta_file_by_id, get_artifact_proof), `weslr/inadequacy_persistence.py` (record_inadequacy_event)

### SatUi / Backend Issue
**Inspect first:** `main.py` (WeslrRequestHandler), `weslr_backend_contract.py`, `chat_ui.py` — determine which UI is being used

### Continuity/Timeline Issue
**Inspect first:** `continuity.py`, `continuity/latest.json`, `continuity/history.json`, `.weslr/timelines/tl_default/events.jsonl`

### Voice Gateway Issue
**Inspect first:** `weslr/voice_gateway.py` (VoiceGateway class, stt_transcribe shim), `set_weslr_http_port()`

### Governance Scorecard / Benchmark Issue
**Inspect first:** `weslr/governance_scorecard.py` (if available), `weslr/governance_surface.py` → `GovernanceBenchmarkEngine`, `test_governance_benchmark_integration.py`

### Self-Improvement Application Issue
**Inspect first:** `self_improvement_apply.py`, `self_mod_applier.py`, `self_mod_log.json`

### Test Failure
**Inspect first:** `tests/test_*.py` or `weslr/tests/test_*.py` — per-module test files, `test_harness.py`

### Chat Responder Formatting Issue
**Inspect first:** `weslr/chat_responder.py` → `format_reasoning_surface()`, `get_explanation_session()`, `_synthesize_active_context()`

### Thread/Interest Tracking Issue
**Inspect first:** `weslr/thread_tracker.py`, `weslr/interest_tracker.py`, `weslr/threads.json`, `weslr/interests.json`

---

## SECTION 9 — STOP LINE

**DOCUMENTATION ONLY — NO CODE CHANGES**

This document was generated by inspection of the WESLR working surface. It reflects the state of the repository as of **2026-04-22 07:02 GMT+2**.

No code was read, no commands were executed that modify system state, no designs were proposed, no implementations were suggested.

If something is incorrect, incomplete, or misclassified: this is an inspection finding. Correct the documentation, not the code.

---
*WESLR FUNCTIONAL TREE MAP V1 — Canonization Artifact*