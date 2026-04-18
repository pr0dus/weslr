# WESLR — Architecture Gap Plan: Current State vs Real Entity Target
# Date: 2026-04-19 01:05 GMT+2
# Branch: main (clean)
# Server: running, provider_available=true, 219s uptime

---

## SECTION 1 — TARGET_ARCHITECTURE

A real continuity-first entity requires these minimum layers:

```
1. CANONICAL FRONT DOOR
   — single entry point for all interactions (HTTP /chat)
   — all paths converge on one response builder

2. INTENT/SOURCE SELECTION
   — classify what the human actually needs
   — select appropriate capability path (internal vs LLM vs memory vs hybrid)
   — route based on intent, not just keyword pattern matching

3. CONTINUITY/MEMORY RETRIEVAL
   — session continuity (short-term working memory)
   — episodic memory (past sessions, events, decisions)
   — semantic memory (facts, knowledge, learned patterns)
   — identity continuity (who is the entity across sessions)
   — retrieval at query time, not just write time

4. EVIDENCE RETRIEVAL
   — internal evidence (entity graph, capability registry)
   — external evidence (research notes, project context, domain knowledge)
   — retrieval-based facts marked as evidence_fact / memory_fact

5. REASONING/SYNTHESIS
   — LLM for open-ended reasoning (distinct from retrieval)
   — reasoning path marked as model_reasoning (not fact)
   — synthesis uses retrieved context + LLM capability

6. TRUTH/VERIFICATION
   — every response carries metadata about its truth class
   — system_fact: verified (internal capability used)
   — memory_fact: verified (actual retrieval occurred)
   — evidence_fact: verified (actual evidence used)
   — model_reasoning: NOT verified (reasoning ≠ fact)
   — fallback_template: NEVER verified
   — verified flag is a hard constraint, not a hint

7. RESPONSE METADATA / INSPECTABILITY
   — _response_signals: path, evaluation_class, llm_used, internal_capability, confidence
   — _truth_guard: truth_class, verified, can_be_verified, policy
   — source label on every response
   — caller can distinguish fact from reasoning from template programmatically

8. GOVERNED LEARNING/IMPROVEMENT
   — entity observes outcomes (via _response_signals / _truth_guard)
   — proposals for self-improvement go through ExecutionGate (operator reviews)
   — changes are traceable, reversible, and operator-approved
   — no blind self-modification
```

---

## SECTION 2 — CURRENT_TO_TARGET_MAP

### Layer 1: Canonical Front Door
**Status: EXISTS AND WORKS**
- HTTP `/chat` in `main.py:2121` → `_CHAT_EXECUTOR.submit(build_communicator_message_payload, ...)` ✅
- Single entry point, returns structured JSON ✅
- `provider_available` flag working (after import fix) ✅
- Evidence: `main.py` line 2144-2155, server running 219s uptime, health check passing

**Partial:** Voice pipeline (Phase 1+2) uses separate WS connection on port 8778, not yet unified with HTTP `/chat` text path. But front door for each transport is clean.

---

### Layer 2: Intent/Source Selection
**Status: EXISTS BUT PARTIAL**
- `interpret_human_turn()` in `interpretation.py` classifies intent ✅
- `likely_need` mapping: `direct_answer`, `concept_explanation`, `self_report`, `justification`, etc. ✅
- Pattern-based internal routing for time/status/health/capability ✅
- Evidence: `dialogue.py:554` uses `interpret_human_turn`, 20+ routing branches

**Gap:** Classification is phrasing-dependent. "What is X" → `concept_explanation` reaches LLM. "Explain X" → `direct_answer` (statement type) hits template. Same intent, different routing. Intent classification is brittle.

**Also partial:** Taxonomy of `likely_need` covers basic cases but misses some real-world query shapes.

---

### Layer 3: Continuity/Memory Retrieval
**Status: EXISTS BUT SPLIT**
- Memory layers exist: `working`, `episodic`, `semantic`, `archive` in `communicator_self` ✅
- Session count tracked in `continuity.session_count` ✅
- Daily memory files (`memory/YYYY-MM-DD.md`) maintained ✅
- `targeted_anchors` retrieval at response time in `dialogue.py` ✅
- Evidence: `dialogue.py:978-980` — `_get_targeted_anchors()` called at return time

**Gap (CRITICAL):** HTTP `/chat` path does NOT load memory anchors into context. `build_communicator_message_payload` receives `narrative` + `relationships` from `load_communicator_self()` but does NOT populate working/episodic/semantic memory layers into the prompt context. The continuity data exists but is not retrieved at query time for the HTTP path.

**Evidence:** sim.py `build_communicator_message()` (CLI path) loads `active_thread=pick_relevant_active_thread()` and `find_relevant_research_note()` — richer context. HTTP path only has `latest_human`, `research_context=None`, and tier data (L0/L1/L2). No memory anchor loading.

**SPLIT:** CLI path (sim.py) has richer continuity. HTTP path (main.py) has shallower continuity. Same function (`build_communicator_message_payload`) called with different context richness.

---

### Layer 4: Evidence Retrieval
**Status: EXISTS BUT PARTIAL (HTTP path)**
- `find_relevant_research_note()` in `integration.py` — wired to HTTP `/chat` via `main.py` research_context enrichment ✅ (after `f545a02` commit)
- Bounded: 350-char cap on `summary`, 80-char cap on `title` ✅
- `entity_graph` context available in `dialogue.py:9-19` via `_get_entity_context()` ✅
- `_get_internal_docs_context()` called at 5 call sites in `dialogue.py` ✅

**Gap:** `entity_graph` is loaded and `_get_entity_context()` is called, but the entity context is not actually used in the response generation. The context is retrieved but not woven into the prompt/synthesis path.

**Also partial:** Tax knowledge (`get_tax_knowledge_answer()`, `get_tax_context_answer()`) is CLI-only. Not reachable from HTTP `/chat`. Documented in `docs/TWO_PATH_GAP_ANALYSIS.md`.

---

### Layer 5: Reasoning/Synthesis
**Status: EXISTS BUT PARTIAL (gating issue)**
- `synthesize_concept_or_self_reply()` in `dialogue.py:170` calls LLM via `get_provider().generate()` ✅
- `synthesis` variable is set when LLM fires ✅
- LLM provider (Ollama) connected and working ✅

**Gap (CRITICAL):** LLM synthesis path is reached inconsistently. `"what is quantum entanglement"` reaches synthesis. `"explain photosynthesis"` hits `simple_response()` template. `"what is a quark"` hits `simple_response()` template. Root cause: `interpret_human_turn` classifies "explain X" as `direct_answer` (turn_type='statement'), not `concept_explanation` (turn_type='question'). The `direct_answer` branch has a simple-word gate that catches most non-question inputs before reaching synthesis.

**Evidence:** `"what is quantum entanglement"` → `turn_type='question'`, `need='concept_explanation'`, reaches synthesis. `"explain photosynthesis"` → `turn_type='statement'`, `need='direct_answer'`, hits template at `dialogue.py:792`.

**Result:** LLM fires but only for a narrow subset of queries. Most general questions hit templates or fallbacks.

---

### Layer 6: Truth/Verification
**Status: EXISTS AND WORKS**
- `_response_signals` added to all `/chat` responses (commit `bf0a14c`) ✅
- `_truth_guard` added to all `/chat` responses (commit `6ed93ab`) ✅
- Truth classes: `system_fact`, `model_reasoning`, `fallback_template`, `uncertain` ✅
- `verified` flag: `system_fact + internal_cap=True` → `True`; `model_reasoning` → `False`; `fallback_template` → `False`; all else → `False` ✅
- Hallucination guard active on all responses ✅
- Evidence:
  - `"what time is it"` → `verified=True, truth_class=system_fact` ✅
  - `"are you healthy"` → `verified=True, truth_class=system_fact` ✅
  - `"what is a quark"` → `verified=False, truth_class=uncertain` ✅
  - `"hello"` → `verified=False, truth_class=uncertain` ✅

**Partial:** `model_reasoning` is never actually reached because LLM synthesis is not reached for most queries. So `truth_class=model_reasoning` is defined but effectively dormant. Would activate if Layer 5 routing were fixed.

---

### Layer 7: Response Metadata / Inspectability
**Status: EXISTS AND WORKS**
- `_response_signals` on every response: `path`, `evaluation_class`, `llm_used`, `internal_capability`, `confidence` ✅
- `_truth_guard` on every response: `truth_class`, `verified`, `can_be_verified`, `policy` ✅
- `source` label on every response (e.g. `conversation-aware-communicator:question:answer_directly`) ✅
- `targeted_anchors` on every response (memory retrieval metadata) ✅
- Evidence: all 5 test queries return both `_response_signals` and `_truth_guard` correctly

**This layer is the strongest implemented layer in the current system.**

---

### Layer 8: Governed Learning/Improvement
**Status: EXISTS BUT PARTIAL**
- `self_improvement_apply.py` / `self_improvement_observation.py` — ExecutionGate architecture exists ✅
- Proposals require operator review before application ✅
- `adaptive_guidance.py` marked EXPERIMENTAL, has test file + integration hook ✅
- Evidence: `docs/CAPABILITY_WIRING_MAP_v1.md` — `adaptive_guidance.py` classified EXPERIMENTAL, not dead code

**Gap:** No actual self-improvement loop is active in canonical `/chat`. No outcome observation → proposal generation → operator approval → application cycle. The infrastructure exists but is dormant.

**Also:** Governance surface (`governance_surface.py`) exists but is not connected to the `/chat` response evaluation loop. `_response_signals` and `_truth_guard` could feed into governance, but currently don't.

---

## SECTION 3 — GAP_TABLE

| Target Layer | Current Implementation | Status | Main Gap | Risk if Ignored | Suggested Fix |
|---|---|---|---|---|---|
| **1. Front door** | HTTP `/chat` + voice WS (separate) | WORKS | Two transports, not yet unified | Not critical — separate but functional | Phase 2 text-chat integration, separate from Phase 1 voice |
| **2. Intent selection** | `interpret_human_turn()` with 20+ branches | PARTIAL | Phrasing-dependent, brittle | "Explain X" vs "What is X" gets different treatment | Make classification intent-based, not phrasing-based |
| **3. Continuity** | Memory layers exist; HTTP path shallow | SPLIT | HTTP path does not load memory anchors at query time | Each HTTP session starts from scratch; continuity thin | Wire memory anchor loading into `build_communicator_message_payload` context |
| **4. Evidence retrieval** | research_context wired; entity_graph loaded but unused | PARTIAL | Entity context retrieved but not woven into synthesis | Missed opportunity for grounded responses | Use `_get_entity_context()` output in synthesis prompt |
| **5. Reasoning/Synthesis** | LLM fires for "what is X" only; template for rest | PARTIAL | Synthesis path gated by turn_type classification | Most general questions get template, not reasoning | Fix `direct_answer` branch to reach synthesis for non-trivial queries |
| **6. Truth/Verification** | `_response_signals` + `_truth_guard` fully implemented | WORKS | `model_reasoning` never reached (upstream gating) | Defined but dormant; would activate when Layer 5 fixed | Fix Layer 5 → Layer 6 auto-improves |
| **7. Inspectability** | Full metadata on every response | WORKS | None critical | None | Keep as-is; foundation is solid |
| **8. Governed improvement** | Infrastructure exists; not connected to /chat | PARTIAL | No outcome observation → proposal loop active | Entity cannot learn from its own responses | Connect `_response_signals` evaluation to governance surface |

---

## SECTION 4 — FOUNDATIONAL_PARTS_TO_KEEP

These parts of current WESLR are strong enough to remain as-is and should NOT be redesigned:

1. **Response metadata infrastructure (`_response_signals` + `_truth_guard`)** — This is solid. Every response carries inspectable metadata. The truth policy is well-designed. This is now a genuine differentiator and should be preserved exactly as-is.

2. **Internal capability routing (time/status/health)** — Deterministic, testable, works at 9/9 regression. Should be preserved as the gold standard for what "verified" means.

3. **The tier architecture (L0/L1/L2)** — Clean separation of identity core (L0), operating facts (L1), session state (L2). Already being used correctly by `/chat`.

4. **Regression test suite** — `weslr/test_chat_internal_routing.py` with 9 tests covering critical paths. Should be expanded, not replaced.

5. **`main.py` `/chat` handler structure** — The executor pattern with bounded semaphore and timeout is correct. The research_context enrichment is correct.

6. **The `_set_signal` / `_response_signals` instrumentation pattern** — Adding metadata to responses without changing behavior is the right approach. Should be extended, not removed.

---

## SECTION 5 — MINIMUM_REMAINING_WORK

Before WESLR can honestly be called a **coherent continuity-capable entity**:

### MUST FIX (blocking)

1. **Fix LLM synthesis path gating** — Non-trivial queries like "explain photosynthesis", "what is a quark" return template instead of LLM reasoning. Classification must be intent-based, not phrasing-based. This is the single highest-leverage fix.

2. **Wire memory anchors into HTTP `/chat` context** — Continuity is thin on the HTTP path. Session starts from scratch on each connection. Must load working/episodic/semantic memory at query time, not just at write time.

### MUST ADD (missing capability)

3. **Connect truth evaluation to governance** — `_response_signals` and `_truth_guard` should feed into `governance_surface`. Currently evaluation exists but no loop closes. At minimum: when `evaluation_class=fallback_template` repeatedly for the same query, surface a proposal.

### MUST CLEAN (technical debt)

4. **Unify HTTP + CLI paths** — Two entry points with different context enrichment produce different responses for identical inputs. At minimum: document the split as intentional, or unify the pre-enrichment logic.

5. **Remove dead code** — `get_current_year()` (sim.py:87, zero call sites), dormant `capability_intake.py`, unused `background_analysis/`. Keeps system comprehensible.

### CAN WAIT (nice to have)

6. **Voice + text unified on single transport** — Already designed in Phase 2; not blocking coherence.
7. **Browser integration validation** — Locally validated but not in real browser; can wait.

---

## SECTION 6 — BUILD_ORDER

Ordered from smallest to biggest, with prefer: **unify before expand, truth before fluency, continuity before self-improvement, evaluation before autonomy**.

**Step 1:** Fix LLM synthesis path gating in `direct_answer` branch — widen so non-trivial queries reach `synthesize_concept_or_self_reply()` instead of `simple_response()`. This is the single biggest coherence improvement.

**Step 2:** Add instrumented `_set_signal` for `synthesis` in `concept_explanation` branch (confirm `synthesis` variable is being tagged when LLM fires). Validate with `"what is quantum entanglement"` → `evaluation_class=model_reasoning, llm_used=True`.

**Step 3:** Wire memory anchor loading into `build_communicator_message_payload` context — load `working`, `episodic`, `semantic` into the prompt context for HTTP `/chat`. Make continuity real on the canonical path.

**Step 4:** Connect evaluation to governance — at minimum, when `fallback_template` fires 3+ times in a row for similar queries, emit a governance event. No automatic action; operator reviews.

**Step 5:** Unify HTTP + CLI pre-enrichment OR document the split as intentional. At minimum: document which capabilities are HTTP-only vs CLI-only vs shared.

**Step 6:** Remove dead code (`get_current_year()`, dormant modules). Keep system comprehensible.

**Step 7:** Expand regression suite to cover truth_guard behavior. Add tests: `test_system_fact_verified`, `test_fallback_not_verified`, `test_model_reasoning_not_verified`.

---

## SECTION 7 — EXACT_NEXT_STEP

**Fix LLM synthesis path gating in the `direct_answer` branch.**

Bounded action: In `dialogue.py`, in the `elif likely_need == "direct_answer"` block, after the internal routing patterns (time/status/health/capability), modify the else clause so that non-simple-word, non-identity queries reach `synthesize_concept_or_self_reply()` instead of `simple_response()`.

Specifically: queries that are not in the simple-word set AND not identity questions AND not internal-routed should attempt synthesis before falling back to `simple_response()`.

Validate: `"explain photosynthesis"` should return a synthesis response (not `simple_response()` template) with `_response_signals` showing `path=synthesis, evaluation_class=model_reasoning, llm_used=True, confidence=medium`. Run regression suite to confirm no regression on time/status/health internal routing.

This is the smallest, highest-leverage change that most directly addresses the main coherence gap.