# WESLR Capability Wiring Map — Audit 2026-04-18

## SECTION 1 — CAPABILITY INVENTORY

### A) TIME / STATUS / HEALTH

| Capability | File(s) | Purpose | Status |
|---|---|---|---|
| `get_current_year()` | `sim.py:87` | Returns current year | UNUSED — defined but never called anywhere |
| `load_failsafe_status()` | `sim.py:8454` | Returns mode/initialization state | ACTIVE — called in internal routing (dialogue.py lines 603,611,755,764,822,830) |
| `load_llm_status()` | `sim.py` | Returns LLM provider info | ACTIVE — called with load_failsafe_status in internal routing |
| `datetime.now(timezone.utc)` | (stdlib) | Real clock | ACTIVE — inlined in internal routing (dialogue.py lines 597,750) |
| `get_health_status()` | N/A | Not implemented | N/A |

### B) MEMORY / CONTINUITY

| Capability | File(s) | Purpose | Status |
|---|---|---|---|
| `load_communicator_self()` | `sim.py:1093` | Full self-state | ACTIVE — 10+ call sites in dialogue.py |
| `load_communicator_state()` | `sim.py:617` | State-only load | ACTIVE — called at dialogue.py:504 |
| `get_relevant_continuity_anchors()` | `sim.py:833` | Memory retrieval | UNUSED FROM CHAT — only called in `build_communicator_message()` (sim.py) |
| `get_relevant_goal_anchors()` | `sim.py:833` | Goal memory | UNUSED FROM CHAT — only called in `build_communicator_message()` |
| `get_relevant_episodic_anchors()` | `sim.py:927` | Episodic memory | UNUSED FROM CHAT — only called in `build_communicator_message()` |
| `get_relevant_semantic_anchors()` | `sim.py:1008` | Semantic memory | UNUSED FROM CHAT — only called in `build_communicator_message()` |
| `score_memory_item()` | `sim.py:1386` | Memory scoring | ACTIVE — called internally, not from /chat |
| `distill_episodic_memory()` | `sim.py:1536` | Memory consolidation | ACTIVE — background process, not from /chat |
| `distill_semantic_memory()` | `sim.py:1762` | Semantic distillation | ACTIVE — background process, not from /chat |

### C) ENTITY / CONCEPT GRAPH

| Capability | File(s) | Purpose | Status |
|---|---|---|---|
| `get_entity_graph()` | `entity_graph.py` | Entity/relationship storage | ACTIVE — imported in dialogue.py `_get_entity_context()` and `_get_consciousness_context()` |
| `entity_extractor.py` | `entity_extractor.py` | Extract entities from text | ACTIVE — Phase 1C cross-reference tool, not called from /chat |
| `_get_entity_context()` | `dialogue.py:9` | Provide entity context to routing | ACTIVE — called at dialogue.py:668 for concept_explanation branch |

### D) EVIDENCE / EXTERNAL FACT MODULES

| Capability | File(s) | Purpose | Status |
|---|---|---|---|
| `find_relevant_research_note()` | `integration.py:4` | Search public memory by topic | ACTIVE — called in `build_communicator_message()` (sim.py:8545) |
| `get_tax_knowledge_answer()` | `sim.py:95` | German tax knowledge | ACTIVE — called in `build_communicator_message()` for "entfernungspauschale"/"fahrtkosten" keywords |
| `get_tax_context_answer()` | `sim.py:106` | Tax context explanation | ACTIVE — called in `build_communicator_message()` for "was bedeutet das"/"was ist das" |

### E) INTROSPECTION / CONSCIOUSNESS / VALENCE

| Capability | File(s) | Purpose | Status |
|---|---|---|---|
| `get_introspection_monitor()` | `introspection.py` | Perturbation detection | ACTIVE — `_get_introspection_context()` at dialogue.py:31, used in `_generate_enriched_self_report` |
| `get_valence_system()` | `valence_system.py` | Trade-off tracking | ACTIVE — `_get_valence_context()` at dialogue.py:47, used in `_generate_enriched_self_report` |
| `get_consciousness_detector()` | `consciousness_detector.py` | Consciousness claim detection | ACTIVE — `_get_consciousness_context()` at dialogue.py:60, used in `_generate_enriched_identity` |

### F) INTERNAL DOCUMENT / CONTEXT ENRICHMENT

| Capability | File(s) | Purpose | Status |
|---|---|---|---|
| `get_internal_docs_context()` | `internal_docs.py` | Themes for response enrichment | ACTIVE — 5 call sites across likely_need branches in dialogue.py (lines 641,692,784,791,893) |
| `get_lifecycle_state()` | `weslr/communicator_config.py` | Lifecycle state | ACTIVE — called at dialogue.py:158 for lifecycle narrative |
| `get_lifecycle_narrative_message()` | `weslr/communicator_config.py` | Lifecycle message | ACTIVE — called at dialogue.py:160 |

### G) SELF-REPORT / IDENTITY / ENRICHMENT

| Capability | File(s) | Purpose | Status |
|---|---|---|---|
| `_generate_enriched_self_report()` | `dialogue.py:358` | Self-report with introspection+valence | ACTIVE — called in concept_explanation/self_report branches |
| `_generate_enriched_identity()` | `dialogue.py:429` | Identity with entity+consciousness | ACTIVE — called in concept_plus_self_position branch |
| `generate_from_self_state()` | `dialogue.py:115` | Self-state synthesis | ACTIVE — internal, not directly from /chat routing |
| `synthesize_concept_or_self_reply()` | `dialogue.py:170` | Concept explanation synthesis | ACTIVE — used in concept_explanation branch |
| `synthesize_research_answer()` | `dialogue.py:301` | Research-based answer | ACTIVE — called from concept_explanation branch |

### H) REASONING / DECISION MODULES

| Capability | File(s) | Purpose | Status |
|---|---|---|---|
| `load_tier()` | `sim.py:1141` | Load L0/L1/L2 identity tier | ACTIVE — called from /chat handler (main.py:2128-2130) |
| `build_communicator_message()` | `sim.py:8501` | Legacy CLI communicator path | ACTIVE — CLI path only, not used by HTTP /chat |
| `get_outbox()` | `outbox.py` | Message queuing | ACTIVE — called at end of dialogue.py routing |
| `interpret_human_turn()` | `interpretation.py` | Classify intent/likely_need | ACTIVE — called at start of `build_communicator_message_payload` |

### I) BACKGROUND ANALYSIS

| Capability | File(s) | Purpose | Status |
|---|---|---|---|
| `active_work_capsule.py` | `weslr/active_work_capsule.py` | Active work tracking | DORMANT — file exists, no /chat integration |
| `background_observability.py` | `weslr/background_observability.py` | Background process monitoring | DORMANT — file exists, operator CLI only |
| `background_analysis/` | `weslr/background_analysis/` | Background analysis tasks | DORMANT — directory exists, no /chat integration |

### J) GOVERNANCE / PROPOSAL / CDI

| Capability | File(s) | Purpose | Status |
|---|---|---|---|
| `change_proposals.py` | `weslr/change_proposals.py` | Self-modification proposals | LEGACY — CLI only, not from /chat |
| `cdi_proposal_builder.py` | `weslr/cdi_proposal_builder.py` | CDI decision proposals | LEGACY — operator CLI only |
| `governance_surface.py` | `weslr/governance_surface.py` | Proposal governance | LEGACY — operator flow only |
| `self_mod_proposals` | `sim.py:605` | Self-mod data | CLI only, not from /chat |

### K) CAPABILITY INTAKE / SUGGESTION

| Capability | File(s) | Purpose | Status |
|---|---|---|---|
| `capability_intake.py` | `weslr/capability_intake.py` | Capability registry | DORMANT — file exists, no /chat integration |
| `capability_suggestion.py` | `weslr/capability_suggestion.py` | Suggest new capabilities | DORMANT — file exists, no /chat integration |
| `adaptive_guidance.py` | `weslr/adaptive_guidance.py` | Adaptive recommendation | DORMANT — file exists, no /chat integration |
| `cognitive_adequacy.py` | `weslr/cognitive_adequacy.py` | Cognitive adequacy detection | DORMANT — file exists, no /chat integration |

### L) VOICE-RELATED

| Capability | File(s) | Purpose | Status |
|---|---|---|---|
| `weslr_chat()` | `weslr/voice_gateway.py:201` | HTTP /chat proxy for voice | ACTIVE — WS voice gateway uses this |
| `stt_transcribe()` | `weslr/voice_gateway.py:78` | whisper-cli STT | ACTIVE — binary audio path |
| `log_voice_event()` | `weslr/voice_gateway.py:233` | Timeline event logging | ACTIVE — voice gateway uses this |

---

## SECTION 2 — /CHAT WIRING TRACE

### Entrypoints

1. **HTTP `/chat`** (main.py:2121) → `build_communicator_message_payload(narrative, relationships, active_thread, latest_human, research_context, l0_identity, l1_operating, l2_session)`
2. **WS `chat_text`** (voice_gateway.py:415) → `weslr_chat(text)` → HTTP POST to `/chat` → same function
3. **WS `transcript`** (voice_gateway.py:372) → `weslr_chat(transcript)` → same path

All three converge on `build_communicator_message_payload` via HTTP `/chat`.

### Classifier/Routing

`interpret_human_turn(message)` → `likely_need` ∈ {direct_answer, concept_explanation, self_report, ...} → 12+ branch handling in `build_communicator_message_payload`

### Internal Capability Dispatch

- `load_failsafe_status()` / `load_llm_status()` — inlined in direct_answer, concept_explanation, self_report branches
- `datetime.now(timezone.utc)` — inlined in direct_answer branch
- `get_internal_docs_context()` — per-branch enrichment
- `_get_entity_context()` / `_get_consciousness_context()` — concept_explanation branch
- `_get_introspection_context()` / `_get_valence_context()` — self_report branch
- `get_lifecycle_state()` / `get_lifecycle_narrative_message()` — lifecycle branch
- `synthesize_concept_or_self_reply()` — concept_explanation branch
- `synthesize_research_answer()` — concept_explanation branch (with research_context)

### Fallback-to-LLM

`_get_language_module().simple_response()` — called when no internal routing matches (greeting, unknown questions)

---

## SECTION 3 — SAMPLE VALIDATION

### Confirmed /chat-wired (category A)

1. **Time** — `datetime.now(timezone.utc)` inlined at dialogue.py:597,750. Evidence: curl test `"what time is it"` → `"It is 22:57 local time (Europe/Berlin)..."`
2. **Status** — `load_failsafe_status()` + `load_llm_status()` at dialogue.py:603,822. Evidence: curl test `"what is your system status"` → `"I am initialized. LLM provider: embedded."`
3. **Introspection/Valence** — `_get_introspection_context()` + `_get_valence_context()` at dialogue.py:618. Evidence: called in `_generate_enriched_self_report()` which is called in `self_report` branch.

### Active elsewhere, not /chat-wired (category C)

4. **`get_tax_knowledge_answer()`** — sim.py:95, only called from `build_communicator_message()` (sim.py, the legacy CLI path). NOT reachable from HTTP `/chat` (which calls `build_communicator_message_payload`). German tax keywords must be added to dialogue.py internal routing.
5. **`get_relevant_continuity_anchors()`** — sim.py:833, only called from `build_communicator_message()` (sim.py). Not reachable from HTTP `/chat`.
6. **`find_relevant_research_note()`** — integration.py:4, only called from `build_communicator_message()` (sim.py). `build_communicator_message_payload` receives `research_context` but only populates it from `latest_human` topics, not from the `find_relevant_research_note()` function.

### Dormant / Legacy (category D)

7. **`get_current_year()`** — sim.py:87. Defined, never called anywhere in the codebase.
8. **`adaptive_guidance.py`** — File exists with full implementation. Not imported or called anywhere in dialogue.py or main.py.
9. **`capability_intake.py`** — File exists. Not imported or called from dialogue.py.
10. **`background_analysis/`** — Directory exists with analysis modules. No /chat integration, operator CLI only.

---

## SECTION 4 — GAP MAP

| Capability | Purpose | Files | Status | /chat reachable? | Path | Evidence | Next Action |
|---|---|---|---|---|---|---|---|
| Time (clock) | Real clock time | dialogue.py inlined | ✅ Active | ✅ YES | direct_answer branch, `datetime.now()` inlined | `"what time is it"` → clock response | leave-as-is |
| System status | WESLR state | sim.py:load_failsafe_status/load_llm_status | ✅ Active | ✅ YES | direct_answer/concept_explanation/self_report branches | `"what is your system status"` → status response | leave-as-is |
| Health/mode | Fail-safe mode | sim.py:load_failsafe_status | ✅ Active | ✅ YES | health_patterns in direct_answer/self_report branches | `"are you healthy"` → mode response | leave-as-is |
| Introspection context | Perturbation monitoring | introspection.py, dialogue.py:31 | ✅ Active | ✅ YES | `_get_introspection_context()` → `_generate_enriched_self_report()` | code path exists at dialogue.py:618 | leave-as-is |
| Valence/trade-offs | Trade-off tracking | valence_system.py, dialogue.py:47 | ✅ Active | ✅ YES | `_get_valence_context()` → `_generate_enriched_self_report()` | code path exists at dialogue.py:618 | leave-as-is |
| Entity graph | Entity/relationship storage | entity_graph.py, dialogue.py:9,78 | ✅ Active | ✅ YES | `_get_entity_context()` in concept_explanation branch | imported at dialogue.py:12,79 | leave-as-is |
| Consciousness context | Consciousness claim detection | consciousness_detector.py, dialogue.py:60 | ✅ Active | ✅ YES | `_get_consciousness_context()` in `_generate_enriched_identity()` | imported at dialogue.py:60 | leave-as-is |
| Internal docs themes | Response enrichment themes | internal_docs.py, dialogue.py:641,692,784,791,893 | ✅ Active | ✅ YES | `get_internal_docs_context()` per-branch | 5 call sites across branches | leave-as-is |
| Lifecycle narrative | Lifecycle state messaging | communicator_config.py, dialogue.py:157 | ✅ Active | ✅ YES | `get_lifecycle_narrative_message()` at dialogue.py:160 | called in concept_plus_self_position branch | leave-as-is |
| L0/L1/L2 identity tiers | Identity/operating/session state | sim.py:1141, main.py:2128 | ✅ Active | ✅ YES | `load_tier()` called from /chat handler | main.py:2128-2130 | leave-as-is |
| `get_tax_knowledge_answer()` | German tax knowledge | sim.py:95 | ✅ Active elsewhere | ❌ NO | Only in `build_communicator_message()` (CLI path, not HTTP /chat) | tax keywords "entfernungspauschale"/"fahrtkosten" only in sim.py, not dialogue.py | add routing to dialogue.py |
| `get_tax_context_answer()` | Tax context explanation | sim.py:106 | ✅ Active elsewhere | ❌ NO | Only in `build_communicator_message()` (sim.py CLI path) | "was bedeutet das"/"was ist das" only in sim.py | add routing to dialogue.py |
| `find_relevant_research_note()` | Research note search | integration.py:4 | ✅ Active elsewhere | ⚠️ PARTIAL | Only in `build_communicator_message()` (sim.py), not in `build_communicator_message_payload` | research_context passed to payload but `find_relevant_research_note` only called in sim.py | add integration path |
| Memory anchors (continuity/goals/episodic/semantic) | Memory retrieval | sim.py:833,927,1008 | ✅ Active elsewhere | ❌ NO | Only in `build_communicator_message()` (sim.py) | Called in sim.py:8515, not in dialogue.py | needs deeper audit |
| `get_current_year()` | Current year | sim.py:87 | ❌ UNUSED | ❌ NO | Defined, never called | grep confirms zero call sites | mark legacy |
| `adaptive_guidance.py` | Adaptive guidance/recommendation | weslr/adaptive_guidance.py | ❌ DORMANT | ❌ NO | No imports, no call sites | grep confirms no dialogue.py/main.py integration | needs deeper audit |
| `capability_intake.py` | Capability registry | weslr/capability_intake.py | ❌ DORMANT | ❌ NO | No imports, no call sites | grep confirms no integration | needs deeper audit |
| `background_analysis/` | Background analysis tasks | weslr/background_analysis/ | ❌ DORMANT | ❌ NO | Operator CLI only, no /chat | no dialogue.py integration | needs deeper audit |
| `change_proposals.py` / `cdi_proposal_builder.py` | Self-mod governance | weslr/change_proposals.py, cdi_proposal_builder.py | ❌ LEGACY | ❌ NO | Operator flow only | not from /chat | expose via operator UI |
| `weslr_chat()` | HTTP /chat proxy for voice | voice_gateway.py:201 | ✅ Active | ✅ YES | WS voice gateway → HTTP /chat → same path | confirmed working in Phase 1B-2E tests | leave-as-is |
| `stt_transcribe()` | whisper-cli STT | voice_gateway.py:78 | ✅ Active | ✅ YES | Binary audio path, `weslr_chat()` shared | confirmed working in Phase 1C-1D tests | leave-as-is |

---

## SUMMARY

**Confidently /chat-wired (A):** 13 capabilities (time, status, health, introspection, valence, entity graph, consciousness, internal docs, lifecycle, tiers, voice gateway, STT)

**Active elsewhere, not /chat-wired (C):** 5+ (tax knowledge, tax context, research note search, memory anchors)

**Dormant/Unused (D):** 4+ (get_current_year, adaptive_guidance, capability_intake, background_analysis/)

**Key insight:** `build_communicator_message()` in sim.py (legacy CLI path) has integrations that `build_communicator_message_payload()` (HTTP /chat path) does not — specifically tax knowledge and memory anchor retrieval. The HTTP /chat path has its own rich internal routing (introspection, valence, entity graph, consciousness) that the CLI path does not have. The two paths are partially divergent.