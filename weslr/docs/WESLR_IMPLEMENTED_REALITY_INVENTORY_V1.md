# WESLR Implemented Reality Inventory V1

**Date:** 2026-05-01
**Purpose:** Factual inventory of what is implemented vs spec-only vs not implemented
**Method:** Direct code inspection, not documentation reliance

---

## A) IMPLEMENTED AND TESTED

### /chat Path
- **File:** `main.py` (ThreadingHTTPServer, ChatHandler)
- **Status:** LIVE — endpoint binds and responds with 200
- **Tests:** No dedicated unit test (tested via curl live)
- **Key:** `POST /chat` → `build_communicator_message_payload()` → response

### Interpretation
- **File:** `interpretation.py` (1078+ lines)
- **Status:** LIVE — `interpret_human_turn()` used by `/chat` and detector
- **Functions:** `interpret_human_turn()`, `classify_human_turn()`, `detect_intent()`
- **Tests:** Used by contract observation builder, no standalone test file found

### Public Signal Capture
- **File:** `weslr/website_signal_integration.py` (103 lines)
- **Status:** LIVE — `capture_website_signal()` wired as fire-and-forget in main.py
- **Functions:** `capture_website_signal()`, `build_public_signal_record()`
- **Tests:** `test_website_signal_integration_v1.py` — **15 passed** ✅ (unittest rewrite, no sys.exit)

### Contract Observation
- **File:** `weslr/contract_observation.py` (310 lines)
- **Status:** LIVE — `build_contract_observation()`, `validate_contract_observation()`, `append_contract_observation()`
- **Storage:** `weslr/contract_observations.jsonl` (31 real records)
- **Tests:** `test_contract_observation_v1.py` — **21 passed** ✅

### Contract Insufficiency Detector
- **File:** `weslr/contract_insufficiency_detector.py` (267 lines)
- **Status:** LIVE — `detect_insufficiency()` reads real file, `check_stability()` wired in
- **Functions:** `detect_insufficiency()`, `_append_insufficiency_evidence()`, `check_stability()`, `_get_contract_key()`
- **Tests:** `test_contract_insufficiency_detector_v1.py` — **16 passed** ✅
- **Synthetic tests:** `test_contract_insufficiency_detector_synthetic.py` — **11 passed** ✅
- **Stability:** `proposal_ready=true` at `stable_across_checks=3` confirmed on real data

### Response Contracts
- **File:** `weslr/contract_observation.py` — `response_contract` field in observation records
- **Status:** LIVE — contracts assigned per response path in `build_contract_observation()`
- **Contracts observed in real data:** `conversational_entry`, `guided_help`, `structured_explanation`, `uncertainty_boundary`, `system_answer`

### Proposal Bridge
- **File:** `weslr/contract_improvement_proposal_bridge.py` (266 lines)
- **Status:** LIVE (passive/operator-review only) — reads `contract_insufficiency_log.jsonl`, writes `contract_proposal_review_log.jsonl`
- **Functions:** `generate_proposals()`
- **Filters:** proposal_ready=true, stable_across_checks>=3, PII/rejected-field checking, deduplication
- **Output:** `weslr/contract_proposal_review_log.jsonl` — 1 record generated (CP-20260501-001)
- **Tests:** `test_contract_improvement_proposal_bridge_v1.py` — **15 passed** ✅
- **Note:** Bridge never auto-approves; `automatic_change=false` on all records; no writes to `proposal_trace.jsonl` or `implementation_plans.json`

### Response Expander
- **File:** `weslr/omnichat/response_expander.py` (400+ lines)
- **Status:** LIVE — deterministic expansion layer, no LLM, adds `_omnichat_policy` + `expanded_response`
- **Note:** Deterministic V1 rules; never invents facts; builds L4 guidance from known WESLR commands only

### Bootstrap / OCW Status
- **File:** `weslr/bootstrap.py` (457 lines)
- **Status:** IMPLEMENTED — `new_timeline_id()`, `new_activation_token()`, `verify_secret_words()`, `new_pending_bootstrap()`
- **Purpose:** Timeline creation, bootstrap tokens, secret word verification

---

## B) SPEC ONLY / DOCTRINE ONLY

### Deterministic Anchor + Probabilistic Interpretation Canon
- **Doc:** `weslr/docs/WESLR_DETERMINISTIC_ANCHOR_AND_PROBABILISTIC_INTERPRETATION_CANON_V1.md` (280+ lines)
- **Status:** DOCTRINE ONLY — no runtime implementation
- **Canonical statement:** "Determinism governs authority. Probability assists interpretation."
- **Operator burden boundary:** Probabilistic methods may automate low-risk read-only tasks without operator review loops; high-impact transitions (contract/state/governance/memory/external actions) always require operator authorization
- **Key principle:** "Less operator micromanagement, not more."

### Review Interface
- **Doc:** `weslr/docs/WESLR_REVIEW_INTERFACE_V1.md` (207 lines)
- **File:** `weslr/review_interface.py` — IMPLEMENTED (read-only inspection, no writes)
- **Status:** LIVE — operator may inspect proposal review queue

### Decision Log
- **Doc:** `weslr/docs/WESLR_REVIEW_DECISION_LOG_V1.md` (202 lines)
- **File:** `weslr/review_decision_log.py` — DOES NOT EXIST
- **Status:** SPEC ONLY — persistent record of operator decisions not yet built

### Operator Consistency
- **Doc:** `weslr/docs/WESLR_OPERATOR_CONSISTENCY_LAYER_V1.md` (161 lines)
- **File:** `weslr/operator_consistency.py` — DOES NOT EXIST
- **Status:** SPEC ONLY — marked "diagnostic layer on the human, not the system"

### Controlled Exposure
- **Doc:** `weslr/docs/WESLR_CONTROLLED_OBSERVATION_ENVIRONMENT_V1.md` (343 lines)
- **File:** `weslr/controlled_observation_environment.py` — DOES NOT EXIST
- **Status:** SPEC ONLY

### Public Readiness
- **Doc:** `weslr/docs/WESLR_PUBLIC_READINESS_PLAN_V1.md` — NO DOC FILE
- **File:** `weslr/public_readiness.py` — DOES NOT EXIST
- **Status:** SPEC ONLY — no implementation

### OmniChat Unification
- **Doc:** `weslr/docs/WESLR_OMNICHAT_UNIFICATION_PLAN_V1.md` (420 lines)
- **File:** `weslr/omni_execution_model.py` — DOES NOT EXIST
- **Status:** SPEC ONLY — plan defined but no implementation

### Artificial Analysis Index
- **File:** `weslr/artificial_analysis_index.py` — LIVE, read-only attention filter
- **Tests:** `weslr/tests/test_artificial_analysis_index_v1.py` — **33 passed** ✅
- **Status:** IMPLEMENTED PASS 1 — global attention filter, no state changes
- **Authority:** `attention_only` on every result; `automatic_change: false`
- **Scope:** Pass 1 sources only (`public_signals.jsonl`, `contract_observations.jsonl`, `contract_insufficiency_log.jsonl`, `contract_proposal_review_log.jsonl`)
- **Real-data distribution (2026-05-01):** level 0=31, level 1=240, level 2=1, level 3=1, level 4=0 (273 total)
- **Key functions:** `classify_attention_item()`, `build_attention_summary()`
- **Spec:** `weslr/docs/WESLR_ARTIFICIAL_ANALYSIS_INDEX_CANON_V1.md` (doctrine) + `weslr/docs/WESLR_ARTIFICIAL_ANALYSIS_INDEX_V1_CHECKPOINT.md` (implementation)

### Capability Registry V1
- **File:** `weslr/capability_registry.py` — READ-ONLY registry, no writes, no LLM calls
- **Data:** `weslr/capability_registry.json` — 10 live capability entries
- **Tests:** `weslr/tests/test_capability_registry_v1.py` — **38 passed** ✅
- **Status:** IMPLEMENTED / NOT WIRED TO CHAT — read-only self-map of live capabilities
- **Authority:** `deterministic` / `read_only` on all entries; `automatic_change: false`
- **Key functions:** `load_registry()`, `list_capabilities()`, `get_capability()`, `get_by_slash_command()`, `search_by_trigger()`, `group_capabilities_by_category()`
- **Spec:** `weslr/docs/WESLR_CAPABILITY_INTELLIGENCE_ARCHITECTURE_REVIEW_V1.md`

### Capability Router V1
- **File:** `weslr/capability_router.py` — DETERMINISTIC routing only, no execution, no LLM calls
- **Tests:** `weslr/tests/test_capability_router_v1.py` — **33 passed** ✅
- **Status:** IMPLEMENTED / NOT WIRED TO CHAT — classifies user messages into capability IDs
- **Authority:** `routing_only`; no execution, no JSONL writes, no Ollama, no /chat integration
- **Automatic change:** `false` on all routing results
- **Threshold:** 0.35 confidence minimum for routing decision
- **Key functions:** `route_request()` with slash-match, trigger scoring, and context boosts
- **Spec:** `weslr/docs/WESLR_CAPABILITY_INTELLIGENCE_ARCHITECTURE_REVIEW_V1.md`

### Capability Welcome Surface V1
- **File:** `weslr/capability_welcome_surface.py` — Registry-generated welcome/help surface
- **Tests:** `weslr/tests/test_capability_welcome_surface_v1.py` — **23 passed** ✅
- **Status:** IMPLEMENTED / NOT WIRED TO CHAT — read-only welcome and help formatter
- **Authority:** `registry_generated`; no execution, no JSONL writes, no Ollama, no /chat integration
- **Key functions:** `build_welcome_overview()`, `build_category_help()`, `build_capability_suggestions()`
- **Uses:** Capability Registry V1 and Capability Router V1 (read-only)
- **Spec:** `weslr/docs/WESLR_CAPABILITY_REGISTRY_ROUTER_V1_CHECKPOINT.md`

### Capability Welcome Chat Bridge V1
- **File:** `weslr/capability_welcome_chat_bridge.py` — Staging-only bridge wiring welcome surface into /chat
- **Tests:** `test_capability_welcome_chat_bridge_v1.py` — **20 passed** ✅
- **Runtime integration:** `deploy/staging/weslr_demo_server.py` — wired before evidence bridge in do_POST
- **Status:** IMPLEMENTED GUARDED / STAGING RUNTIME WIRED
- **Authority:** `registry_generated`; no execution, no JSONL writes, no Ollama, no evidence search
- **Handles only:** help/welcome/capability overview queries (what can you do, /help, etc.)
- **Does NOT handle:** /evidence, /system, /governance, /attention, /sources (future work)
- **Order:** capability welcome bridge → evidence bridge → signal capture
- **Spec:** `weslr/docs/WESLR_CAPABILITY_REGISTRY_ROUTER_V1_CHECKPOINT.md`

### Frontend / UI
- **Doc:** `weslr/docs/WESLR_FRONTDOOR_UI_SPEC_V1.md` (244 lines)
- **File:** `weslr/frontdoor_ui_spec.py` — DOES NOT EXIST
- **Status:** SPEC ONLY — UI spec defined but no implementation

---

## Summary Table

| Component | Status | File |
|-----------|--------|------|
| /chat path | ✅ LIVE | main.py |
| Interpretation | ✅ LIVE | interpretation.py |
| Response contracts | ✅ LIVE | contract_observation.py |
| Public signal capture | ✅ LIVE | website_signal_integration.py |
| Contract observation | ✅ LIVE | contract_observation.py |
| Contract insufficiency detector | ✅ LIVE | contract_insufficiency_detector.py |
| Response expander | ✅ LIVE | weslr/omnichat/response_expander.py |
| Proposal bridge | ✅ LIVE (review only) | contract_improvement_proposal_bridge.py |
| Review interface | ✅ LIVE (read-only) | weslr/review_interface.py |
| Capability Registry V1 | ✅ IMPLEMENTED (read-only, not wired to /chat) | capability_registry.py / capability_registry.json |
| Capability Router V1 | ✅ IMPLEMENTED (deterministic, not wired to /chat) | capability_router.py |
| Capability Welcome Surface V1 | ✅ IMPLEMENTED (read-only, not wired to /chat) | capability_welcome_surface.py |
| Capability Welcome Chat Bridge V1 | ✅ IMPLEMENTED (staging, wired before evidence bridge) | capability_welcome_chat_bridge.py |
| Decision log | ❌ SPEC ONLY | no .py file |
| Operator consistency | ❌ SPEC ONLY | no .py file |
| Controlled exposure | ❌ SPEC ONLY | no .py file |
| Public readiness | ❌ SPEC ONLY | no .py file |
| OmniChat unification | ❌ SPEC ONLY | no .py file |
| Frontend/UI | ❌ SPEC ONLY | no .py file |
| Deployment/OCW status | ✅ IMPLEMENTED | bootstrap.py |
| contract_observations.jsonl | ✅ LIVE (31 records) | weslr/ |
| Observation loop canon | ✅ LIVE (doctrine) | weslr/docs/WESLR_OBSERVATION_LOOP_PHASE_1_CANNON.md |

---

## Test Results

| Test Suite | Result |
|------------|--------|
| `test_contract_observation_v1.py` | ✅ 21 passed |
| `test_contract_insufficiency_detector_v1.py` | ✅ 16 passed |
| `test_contract_insufficiency_detector_synthetic.py` | ✅ 11 passed |
| `test_contract_improvement_proposal_bridge_v1.py` | ✅ 15 passed |
| `test_website_signal_integration_v1.py` | ✅ 15 passed |
| `test_capability_registry_v1.py` | ✅ 38 passed |
| `test_capability_router_v1.py` | ✅ 33 passed |
| `test_capability_welcome_surface_v1.py` | ✅ 23 passed |
| `self_test.py` | ✅ exit code 0 |

---

## Current Blocker List

1. **Decision log not implemented** — no `review_decision_log.py`; no persistent record of operator decisions
2. **Review interface now implemented** — `weslr/review_interface.py` live, read-only inspection operational

---

## Checkpoints and Canon

| Document | Verdict |
|----------|---------|
| `WESLR_DETERMINISTIC_ANCHOR_AND_PROBABILISTIC_INTERPRETATION_CANON_V1.md` | WESLR_DETERMINISTIC_ANCHOR_AND_PROBABILISTIC_INTERPRETATION_CANON_V1_DEFINED |
| `WESLR_OBSERVATION_LOOP_PHASE_1_CANNON.md` | WESLR_OBSERVATION_LOOP_PHASE_1_CANNON_DEFINED |
| `OCC_WESLR_STAGING_TEST_LOOP_V1.md` | OCC_WESLR_STAGING_TEST_LOOP_V1_DEFINED |

---

## C) OPERATIONAL DOCTRINE / DOCUMENTED

Operational docs that define workflows but have no runtime implementation.

### OCC → WESLR Staging Test Loop

- **File:** `OCC_WESLR_STAGING_TEST_LOOP_V1.md`
- **Status:** OPERATIONAL DOCTRINE / DOCUMENTED
- **Summary:** Defines safe loop: OCC phone tests staging, OCW repairs only on explicit operator instruction. No automatic wiring. No autonomous repair. Governance boundary preserved.

---

### Composite Analysis Stack V1

- **File:** `weslr/composite_analysis_stack.py`
- **Tests:** `test_composite_analysis_stack_v1.py` — 34 passed
- **Status:** IMPLEMENTED READ-ONLY / PASS 1
- **Authority:** `analysis_only`
- **Functions:** `classify_structure`, `compute_similarity_score`, `estimate_confidence`, `governance_boundary`, `analyze_item`, `build_composite_summary`
- **AAI integration:** Reads AAI attention classification if available; graceful fallback if unavailable
- **No /chat integration:** Does not route through or modify response contracts
- **No Ollama:** No LLM calls, no formatter integration
- **No JSONL writes:** Read-only from Pass 1 sources

### Composite Analysis Stack Canon V1

- **File:** `weslr/docs/WESLR_COMPOSITE_ANALYSIS_STACK_CANON_V1.md`
- **Status:** ACTIVE DOCTRINE — defines purpose, layers, authority boundary, AAI relationship, experiment rules, V1 scope

### State Grounded Dialogue Canon V1

- **File:** `weslr/docs/WESLR_STATE_GROUNDED_DIALOGUE_CANON_V1.md`
- **Status:** DEFINED — doctrine for read-only architecture/system question answering

### State Grounded Dialogue V1

- **File:** `weslr/state_grounded_dialogue.py`
- **Tests:** `test_state_grounded_dialogue_v1.py` — 32 passed
- **Status:** IMPLEMENTED READ-ONLY / NOT WIRED TO CHAT
- **Authority:** `read_only`
- **Functions:** `classify_state_question`, `load_state_sources`, `answer_state_question`
- **Question types:** implemented_reality, attention_summary, composite_summary, architecture_boundary, pending_reviews
- **Sources:** AAI summary, composite summary, implemented reality inventory doc
- **No /chat integration:** Does not route through or modify response contracts
- **No Ollama:** No LLM calls, no formatter integration
- **No JSONL writes:** Read-only from doc files and analysis modules

### Evidence Needed Detector V1

- **File:** `weslr/evidence_needed_detector.py`
- **Tests:** `test_evidence_needed_detector_v1.py` — 27 passed
- **Status:** IMPLEMENTED READ-ONLY / NOT WIRED TO CHAT
- **Authority:** `classification_only`
- **Functions:** `classify_evidence_need`, `build_evidence_needed_response`
- **Need types:** definition_request, open_knowledge, source_request, lookup_request, latest_information
- **No search adapter yet:** Detects evidence need but does not perform web search
- **No /chat integration:** Standalone classifier, not yet routed from /chat
- **No Ollama:** No LLM calls
- **No JSONL writes:** Read-only classification only

### SearXNG Search Adapter V1

- **File:** `weslr/searxng_search_adapter.py`
- **Tests:** `test_searxng_search_adapter_v1.py` — 26 passed
- **Status:** IMPLEMENTED DISABLED-BY-DEFAULT / NOT WIRED TO CHAT
- **Authority:** `external_evidence_unverified`
- **Functions:** `is_searxng_enabled`, `get_searxng_base_url`, `build_search_url`, `normalize_searxng_result`, `search_searxng`
- **Enable with:** `WESLR_SEARXNG_ENABLED=true`
- **Default URL:** `http://localhost:8888` (override with `WESLR_SEARXNG_URL`)
- **No truth writes:** Results are evidence only, never written to state
- **No /chat integration:** Standalone adapter, not yet routed from /chat
- **No Ollama:** No LLM calls
- **No JSONL writes:** Read-only adapter, no file writes

### Evidence Packet Builder V1

- **File:** `weslr/evidence_packet_builder.py`
- **Tests:** `test_evidence_packet_builder_v1.py` — 20 passed
- **Status:** IMPLEMENTED READ-ONLY / NOT WIRED TO CHAT
- **Authority:** `external_evidence_unverified`
- **Truth status:** `unverified`
- **Functions:** `build_evidence_packet()`, `summarize_evidence_packet()`
- **Input:** `searxng_search_response_v1` (ok=true, at least one result)
- **Output:** `external_evidence_packet_v1` with results truncated and unsafe fields stripped
- **Max content length:** 2000 chars per result
- **Safe fields only:** title, url, content, source, authority
- **No truth writes:** `automatic_truth_write=false` on all packets
- **No /chat integration:** Standalone builder, not yet routed from /chat
- **No Ollama:** No LLM calls
- **No JSONL writes:** Read-only builder, no file writes
### Evidence Answer Builder V1

- **File:** 
- **Tests:**  — 23 passed
- **Status:** IMPLEMENTED READ-ONLY / NOT WIRED TO CHAT
- **Authority:** 
- **Truth status:** 
- **Functions:** , 
- **Input:**  (safe_for_answer_builder=true, at least one result)
- **Output:**  with cautious user-facing answer draft
- **Depths:** brief (2-3 sentences), normal (concise paragraph + sources), deep (multi-part)
- **Boundary wording:** Always includes "Based on external search results — not stored WESLR truth"
- **No truth writes:**  on all answers
- **No /chat integration:** Standalone builder, not yet routed from /chat
- **No Ollama:** No LLM calls
- **No JSONL writes:** Read-only builder, no file writes

### User Timeline Memory V1
- **File:** `weslr/user_timeline_memory.py` (195 lines)
- **Test:** `weslr/tests/test_user_timeline_memory_v1.py` — **31 passed** ✅
- **Status:** IMPLEMENTED EXPERIMENTAL / NOT WIRED TO CHAT
- **Authority:** `user_timeline_memory`
- **Functions:** `normalize_user_id()`, `get_user_timeline_path()`, `build_session_summary_event()`, `append_session_summary()`, `load_recent_session_summaries()`, `build_continuity_note()`
- **Path:** `.weslr/timelines/user_<normalized_user_id>/events.jsonl`
- **Rules enforced:** `raw_prompt_stored=false`, `hidden_learning=false`, `automatic_action=false` on every event
- **No Ollama:** No LLM calls, no HTTP requests
- **No /chat wiring:** Explicit write only — no automatic runtime call, no chat injection
- **Future roadmap:** entity timelines, chat injection (opt-in), voice summary, proactive suggestions

### Continuity Note Chat Bridge V1
- **File:** `weslr/continuity_note_chat_bridge.py`
- **Test:** `test_continuity_note_chat_bridge_v1.py` — **21 passed** ✅
- **Runtime integration:** `deploy/staging/weslr_demo_server.py` — FIRST bridge in `do_POST`
- **Integration order:** continuity → capability welcome → evidence → signal capture
- **Status:** IMPLEMENTED GUARDED / STAGING RUNTIME WIRED
- **Authority:** `user_timeline_memory`
- **Functions:** `is_continuity_query()`, `maybe_answer_with_continuity_note()`
- **Continuity patterns:** "what did we work on last time?", "do you remember...", "continue from last time", etc.
- **Reads:** `.weslr/timelines/user_<user_id>/events.jsonl` via `build_continuity_note()`
- **No Ollama:** No LLM calls, no evidence search
- **No raw prompt storage, no hidden learning, no action execution**
- **Bridging:** reads `build_continuity_note()`, returns `path=continuity_note`, `response_contract=system_answer`
- **Safe failure:** try/except — bridge failure never crashes the request

### Source Trust Ranking V1

- **File:** `weslr/source_trust_ranking.py`
- **Tests:** `test_source_trust_ranking_v1.py` — 29 passed
- **Status:** LIVE ON STAGING / DETERMINISTIC RANKING / USED BY EVIDENCE PACKET BUILDER
- **Live entropy ordering confirmed:** wikipedia.org → quantamagazine.org → (britannica.com) → reddit.com → youtube.com
- **Authority:** `ranking_only` (does not verify truth)
- **Functions:** `classify_source()`, `score_source()`, `rank_search_results()`
- **High trust:** Wikipedia, Britannica, Merriam-Webster, Quanta Magazine, .edu, government/official domains
- **Medium trust:** Science news, established journalism, organization sites (.org)
- **Low trust:** Reddit, YouTube, forums, social media, SEO commercial pages
- **Behavior:** Orders sources by trust score — does NOT drop sources
- **No truth writes:** Truth status remains `unverified` regardless of source tier
- **No memory writes:** No JSONL, no artifact storage
- **No Ollama:** No LLM calls

### External Evidence Pipeline V1

- **File:** `weslr/evidence_pipeline.py`
- **Tests:** `test_evidence_pipeline_v1.py` — 14 passed
- **Status:** IMPLEMENTED READ-ONLY / NOT WIRED TO CHAT
- **Authority:** `external_evidence_unverified`
- **Truth status:** `unverified`
- **Functions:** `run_evidence_pipeline()`
- **Pipeline:** Evidence Needed Detector → SearXNG Search Adapter → Evidence Packet Builder → Evidence Answer Builder
- **Search disabled by default:** `WESLR_SEARXNG_ENABLED=true` required to activate
- **No truth writes:** `automatic_truth_write=false` on all pipeline outputs
- **No /chat integration:** Standalone orchestrator, not yet routed from /chat
- **No Ollama:** No LLM calls
- **No JSONL writes:** Read-only pipeline, no file writes

### Evidence Chat Bridge V1

- **File:** `weslr/evidence_chat_bridge.py`
- **Tests:** `test_evidence_chat_bridge_v1.py` — 23 passed
- **Status:** LIVE ON STAGING / GUARDED / ENV-GATED
- **Runtime:** `deploy/staging/weslr_demo_server.py` (not main.py)
- **Integration point:** Injected in staging `do_POST` handler after `response = weslr_chat(message)`, before `_capture_signal()`, using `response["reply"]` field
- **Activation conditions:** search enabled (WESLR_SEARXNG_ENABLED=true), evidence_needed=true, message not self/system, current response is fallback template or generic depth prompt
- **Fallback signals:** `my current best answer is that`, `i don't have a confirmed answer`, `i can explain that clearly`, `tell me how deep you want to go`
- **Authority:** `external_evidence_unverified`
- **Truth status:** `unverified`
- **Functions:** `maybe_answer_with_evidence(message, current_message)`
- **No /chat integration wiring:** Only activated on fallback-template responses — never overrides genuine synthesis
- **Self/system guard:** Questions like "what are you?", "how do you work?" do not trigger search
- **No truth writes:** `automatic_truth_write=false` on all outputs
- **No memory writes:** No JSONL writes, no artifact storage
- **No Ollama:** No LLM calls in bridge
- **No JSONL writes:** Read-only bridge, no file writes
- **Live-tested:** OCW confirmed 20:39 CEST — "What is entropy?" → `evidence_grounded_answer`, `source_count=5`, `authority=external_evidence_unverified`, `automatic_truth_write=false`


### External Evidence Pipeline V1

- **File:** 
- **Tests:**  — 14 passed
- **Status:** IMPLEMENTED READ-ONLY / NOT WIRED TO CHAT
- **Authority:** 
- **Truth status:** 
- **Functions:** 
- **Pipeline:** Evidence Needed Detector → SearXNG Search Adapter → Evidence Packet Builder → Evidence Answer Builder
- **Search disabled by default:**  required to activate
- **No truth writes:**  on all pipeline outputs
- **No /chat integration:** Standalone orchestrator, not yet routed from /chat
- **No Ollama:** No LLM calls
- **No JSONL writes:** Read-only pipeline, no file writes

