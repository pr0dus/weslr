# WESLR — FULL SYSTEM TRUTH AUDIT
# Date: 2026-04-19 00:35 GMT+2
# Branch: main (clean + provider_config.json staged)
# Server: 820s uptime, provider_available=true

---

SECTION 1 — WORKING_DEFINITION

WESLR is "working" when ALL of the following are true:

1. **Runtime** — Server starts, holds ports, responds to HTTP + WebSocket
2. **Canonical /chat** — Accepts JSON, routes to `build_communicator_message_payload`, returns non-empty responses
3. **LLM path** — Non-trivial queries actually hit the LLM (not just templates/fallbacks)
4. **Internal capability routing** — Time/status/health answered from WESLR's own modules, not LLM
5. **No silent fallbacks** — Every fallback is intentional, not masking a broken path
6. **Voice pipeline** — Phase 1A-F complete, WS demux working, real STT validated
7. **Answer trustworthiness** — Response source is identifiable and correct
8. **Architectural coherence** — HTTP + CLI paths converge, no split-brain

---

SECTION 2 — LAYER_STATE

### A) Runtime / Serving
**Status: WORKING**
- Server starts and holds ports 8001 + 8778 ✅
- `provider_available: true` after fix ✅
- HTTP + WebSocket both serve ✅
- Proof: `curl localhost:8001/api/health` → `{"healthy":true,"provider_available":true,"uptime_s":820}`
- Limitation: Server requires env vars at startup (`WESLR_LLM_PROVIDER=ollama WESLR_LLM_MODEL=qwen2.5:0.5b-instruct`) — not self-configuring

### B) Canonical /chat
**Status: WORKING (narrow)**
- `/chat` endpoint accepts POST, calls `build_communicator_message_payload`, returns JSON ✅
- Time/status/health routed correctly via explicit pattern matching ✅
- Proof: `"what time is it"` → `"It is 00:33 local time (Europe/Berlin). UTC is 22:33."` ✅
- Limitation: Routing is narrow — only questions starting with specific patterns (time/status/health/capability) are routed explicitly. Everything else falls through to templates or `simple_response()`.

### C) LLM reasoning path
**Status: PARTIAL**
- Ollama connected, `provider_available: true` ✅
- LLM fires for some queries (e.g. "what is quantum entanglement" → synthesis response) ⚠️
- LLM does NOT fire for many queries that should reach it (e.g. "explain photosynthesis") ❌
- Root cause: `concept_explanation` branch has complex internal routing; many inputs fall through to `simple_response()` before reaching LLM call
- Proof: `"explain photosynthesis"` → `simple_response()` (template) instead of LLM synthesis. Yet `"what is quantum entanglement"` DOES get synthesis. The difference: `interpret_human_turn` classifies "explain photosynthesis" as `need='direct_answer'` (turn_type='statement') while "what is quantum entanglement" gets `need='concept_explanation'` (turn_type='question'). The direct_answer branch is more template-heavy.
- Limitation: Classification determines fate. Same query shape (factual question) gets different treatment based on framing ("what is X" vs "explain X").

### D) Internal capability routing
**Status: WORKING**
- Time, status, health, capability patterns explicitly routed before LLM call ✅
- Proof: 9/9 regression tests pass ✅
- Limitation: Routing is string-pattern-based, not semantic. New patterns must be added manually. No self-discovery.

### E) Voice pipeline
**Status: WORKING (Phase 2 partial)**
- Phase 1A-F complete: WS voice gateway, STT shim, real microphone, whisper-cli, demux ✅
- Phase 2 WS text-chat: `chat_text`/`chat_text_response` JSON frames added on port 8778 ✅
- Proof: Phase 2.1 demux test — binary WAV + JSON text on one shared WS connection ✅
- Satellite UI wired: textarea/Send button reuse, `chat_text_response` in `ws.onmessage` ✅
- Limitation: Voice pipeline and text-chat use separate WS connections (voice on 8778, text on 8001 upgrade path). UI copy updated but no unified text+voice experience yet.
- `shim_mode=True` propagation confirmed in `ws.onmessage` → `stt_provider` reflects fallback state ✅

### F) WS shared transport
**Status: WORKING**
- Port 8778 serves both binary WAV (voice) and JSON text-chat frames ✅
- Demux: 4-byte header distinguishes frame types ✅
- Proof: `f64f792` — "demux: validate binary WAV + JSON text frames on one WS connection"
- Limitation: Only validated locally; browser integration not live-tested in this session

### G) Satellite UI
**Status: WORKING**
- HTML UI at workspace root served as static file ✅
- Textarea + Send button + status div updated with Phase 2 labels ✅
- Proof: `cce703d`, `d6b72ac` commits — UI polish and `chat_text_response` handler
- Limitation: No browser validation in this session (termux environment)

### H) Continuity / memory usage
**Status: PARTIAL**
- Daily `memory/YYYY-MM-DD.md` files written and read ✅
- Memory anchors (continuity/goals/episodic/semantic) exist but are CLI-only, NOT wired to `/chat` ❌
- `find_relevant_research_note()` wired to HTTP `/chat` via research_context enrichment ✅
- `interpret_human_turn()` uses historical message context ✅
- Limitation: Memory anchors used by sim.py path, not HTTP path. Continuity signals (session_count, variant_index) visible but shallow.

### I) Capability integration (wiring completeness)
**Status: PARTIAL**
- **13 confirmed /chat-wired**: time, status, introspection, valence, entity graph, consciousness, internal docs (5 call sites), lifecycle, L0/L1/L2 tiers, voice gateway, STT ✅
- **4+ active elsewhere, NOT /chat-wired**: `get_tax_knowledge_answer()`, `get_tax_context_answer()`, memory anchors, `find_relevant_research_note()` (CLI only) ❌
- research_context enrichment added to HTTP `/chat` (350-char cap on summary) ✅
- Tax knowledge + context: in sim.py path only (keyword pre-check), not in HTTP path ❌
- `get_current_year()` in `sim.py:87` with zero call sites — dead code ❌
- Limitation: HTTP `/chat` path is richer than before but still missing some capabilities that sim.py path has

### J) Architectural coherence
**Status: PARTIAL**
- Two distinct paths confirmed: HTTP `/chat` (main.py) vs CLI (sim.py) ✅
- Both converge on `build_communicator_message_payload` ✅
- sim.py pre-enriches with tax knowledge + research notes; HTTP path now has bounded research_context ✅
- Not merged — remain separate entry points with different enrichments ❌
- Proof: `docs/TWO_PATH_GAP_ANALYSIS.md` — full gap map documented
- Limitation: Two paths = two behaviors for similar inputs. No unified capability surface.

### K) Answer trustworthiness
**Status: PARTIAL**
- Source label present on every response (e.g. `conversation-aware-communicator:question:answer_directly`) ✅
- Internal routing (time/status/health) has high trust: deterministic, no LLM involved ✅
- LLM responses: source is `conversation-aware-communicator:*` but content varies wildly (template vs synthesis vs simple_response) ❌
- No answer quality scoring or confidence indicator ❌
- Limitation: Cannot distinguish LLM synthesis from template fallback from user-facing output

---

SECTION 3 — REAL_VS_ILLUSION

### A) REAL (proven with evidence)
- Server holds ports and responds to health checks ✅
- `provider_available=true` after import fix ✅
- Time routing: exact clock value, correct timezone ✅
- Status routing: correct failsafe state + provider name ✅
- Health routing: GUIDED mode response ✅
- WS demux: binary + JSON confirmed on same port 8778 ✅
- Phase 2 text-chat frames on WS transport (code path only) ✅
- 9/9 regression tests pass ✅
- `provider_config.json` model set to correct Ollama name ✅
- `main.py` import bug fixed (`weslr.providers.get_provider`) ✅

### B) PARTIAL (works in limited conditions)
- LLM fires for "what is X" questions but NOT "explain X" style inputs
- Ollama works when started with correct env vars; wrong without them
- `concept_explanation` branch fires for questions starting with "what is/are", misses others
- `direct_answer` branch fires for greeting + simple words, misses most other inputs
- Research context enrichment: only when message starts with what/how/why/explain/tell/define/about AND topic matches a research note
- Voice pipeline: validated locally, not in real browser

### C) ILLUSION (appears to work but is fallback/template)
- `"explain photosynthesis"` returns `simple_response()` template — appears to work, is actually a template fallback
- `"define algorithm"` → `simple_response()` template
- `"tell me about gravity"` → `simple_response()` template
- These all LOOK like real responses but are NOT using LLM or any reasoning path
- The `direct_answer_response()` branch (line 921) is the last fallback before `simple_response()` — many queries never reach it
- `"what can you do"` → capability list (real, but hardcoded template, not LLM-generated)

### D) DEAD / UNUSED
- `get_current_year()` in `sim.py:87` — zero call sites, never called
- `get_tax_knowledge_answer()` — CLI path only, not reachable from HTTP `/chat`
- `get_tax_context_answer()` — CLI path only, not reachable from HTTP `/chat`
- `adaptive_guidance.py` — marked EXPERIMENTAL, has test file + hook, but no active integration
- `capability_intake.py` — dormant
- `background_analysis/` — dormant
- Memory anchors: `continuity`, `goals`, `episodic`, `semantic` — CLI path only

---

SECTION 4 — CRITICAL_GAPS

### 1. LLM path is inconsistently reached
**What:** Many queries that should get LLM synthesis instead hit `simple_response()` template.
**Why:** `interpret_human_turn()` classifies by phrasing, not intent. "Explain X" vs "What is X" get different routing. The direct_answer branch has a simple-word gate that catches many inputs.
**Impact:** System appears responsive but is actually using templates for most inputs. User gets inconsistent quality.
**Evidence:** `"explain photosynthesis"` → template. `"what is quantum entanglement"` → synthesis.

### 2. No answer quality signal
**What:** Every response has a source label but no confidence/quality indicator.
**Why:** `build_communicator_message_payload` returns message text with no metadata about whether LLM was used, how confident the routing is, or if a fallback was triggered.
**Impact:** Cannot distinguish template response from LLM response programmatically.
**Evidence:** Both template and LLM responses return identical JSON shape.

### 3. Tax knowledge unreachable from HTTP /chat
**What:** `get_tax_knowledge_answer()` and `get_tax_context_answer()` are CLI-only.
**Why:** sim.py pre-enrichment path (build_communicator_message) has keyword checks for tax; HTTP path (main.py) does not.
**Impact:** Tax-related queries via HTTP get generic responses, not domain knowledge.
**Evidence:** TWO_PATH_GAP_ANALYSIS.md documents full gap.

### 4. Continuity is shallow
**What:** Session count and variant index are incremented but memory anchors (goals, episodic, semantic) are not loaded into HTTP `/chat` context.
**Why:** `build_communicator_message_payload` receives `narrative` + `relationships` from `load_communicator_self()` but does not load memory anchor files.
**Impact:** Each session starts from scratch on the HTTP path; CLI path has richer continuity.
**Evidence:** Memory anchors exist in persistence but not in HTTP path context building.

### 5. Server startup coupling to env vars
**What:** Server must be started with explicit env vars (`WESLR_LLM_PROVIDER=ollama WESLR_LLM_MODEL=qwen2.5:0.5b-instruct`) or wrong provider/model is used.
**Why:** `config.py` defaults override `provider_config.json`; env var wins only if set.
**Impact:** Provider configuration is fragile; easy to start server with wrong settings.
**Evidence:** `provider_config.json` has correct values but was ignored until env vars set.

### 6. No browser integration validation
**What:** Voice pipeline and Satellite UI have been validated locally but not in a real browser session.
**Why:** Termux environment has no graphical browser.
**Impact:** Phase 2 text-chat and demux may work in code but could fail in browser due to WebSocket framing, audio format, or UI JavaScript issues.

---

SECTION 5 — VERDICT

**Does WESLR currently work?** PARTIAL

**In what sense it works:**
- Server is stable and serving HTTP + WebSocket for 820+ seconds
- Internal capability routing (time/status/health) works correctly and deterministically
- Ollama LLM is connected and fires for some query types
- Voice pipeline Phase 1 + Phase 2 text-chat demux code is complete and locally validated
- Regression tests pass (9/9)
- No silent crashes; every endpoint returns structured JSON

**In what sense it fails:**
- LLM path is inconsistently reached — most non-system queries hit templates
- Classification is phrasing-dependent — same semantic query gets different treatment
- Two architectural paths (HTTP vs CLI) produce different responses for identical inputs
- No answer quality signal makes it impossible to trust responses programmatically
- Continuity is session-deep on CLI path but shallow on HTTP path

**Maturity classification:** FUNCTIONAL PROTOTYPE

A functional prototype is a system where individual pieces work correctly but the whole is not yet coherent. WESLR matches this:
- Internal routing: works ✅
- LLM integration: partial ⚠️
- Voice pipeline: complete but not browser-validated ⚠️
- Continuity: present but shallow ⚠️
- No unified experience — separate HTTP/CLI/WS paths with different behaviors

Not yet an "early system" (requires coherent response quality and unified path).
Not a prototype anymore (too much code, too many integrated pieces).
Too broken to be "functional system" (LLM path unreliable).
So: **Functional prototype** — pieces work, whole is not yet coherent.

---

SECTION 6 — READINESS_SCORE

| Dimension | Score | Notes |
|---|---|---|
| **runtime stability** | 80/100 | Server holds 820s, no crashes, provider_available=true. -20: requires correct env vars at startup |
| **interaction quality** | 45/100 | Time/status/health responses are high quality. Most other queries → templates. Source labels present but no confidence signal. |
| **reasoning capability** | 35/100 | LLM fires for some queries only. "What is X" works; "Explain X" fails. No semantic classification. |
| **capability integration** | 55/100 | 13 capabilities wired, 5+ unreachable. research_context now wired. Tax knowledge CLI-only. |
| **continuity** | 40/100 | Memory files maintained. Session count incremented. But HTTP path doesn't load memory anchors. Shallow on HTTP. |
| **trustworthiness** | 50/100 | Internal routing is deterministic and trustworthy. LLM responses are identifiable but quality variable. No quality signal. |
| **architectural coherence** | 45/100 | Two paths converge on same function but with different enrichments. Not merged. Split-brain for similar inputs. |
| **TOTAL** | **47/100** | Functional prototype — core pieces work, overall coherence lacking |

**Sub-score rationale:**
- Runtime: stable when correctly configured
- Reasoning: severely gated by classification/phrasing sensitivity
- Continuity: files exist but context is thin in HTTP path
- Trust: deterministic responses are trustworthy; LLM responses are a lottery

---

SECTION 7 — WHAT_REMAINS

### MUST FIX (blocking issues)

1. **Fix LLM path inconsistency** — `interpret_human_turn` + `direct_answer` branch gate is too aggressive. "Explain photosynthesis" should reach LLM, not template. Classification should be intent-based, not phrasing-based. Either widen the synthesis path or remove the simple-word gate from direct_answer.

2. **Add answer quality metadata** — Every response should include `confidence: high|medium|low` and `path: internal|llm|template` so callers can distinguish template from synthesis. Without this, WESLR cannot be trusted for non-trivial queries.

3. **Make server startup self-configuring** — Remove the env-var coupling. If `provider_config.json` has `provider=ollama`, the server should use it without requiring env vars. Current behavior: env var always wins, making persisted config fragile.

### MUST ADD (missing critical capability)

4. **Wire tax knowledge to HTTP /chat** — `get_tax_knowledge_answer()` and `get_tax_context_answer()` are unreachable from `/chat`. Either add keyword patterns to HTTP path or accept that tax queries get generic responses.

5. **Add response quality gate** — Before returning, check: was LLM actually called? Was synthesis reached? If neither, at minimum surface that the response is templated. Currently no such gate exists.

### MUST CLEAN (technical debt)

6. **Remove dead code** — `get_current_year()` in sim.py:87 (zero call sites), `adaptive_guidance.py` (EXPERIMENTAL but no active hook), `capability_intake.py` (dormant). Either integrate or remove.

7. **Unify HTTP + CLI paths** — Two entry points with different enrichments produce different responses. Either merge (HTTP path gets tax knowledge + memory anchors) or document the split as intentional.

---

SECTION 8 — MAIN_BOTTLENECK

**LLM path gating by classification — inconsistent response quality**

The single most important bottleneck is that `interpret_human_turn()` + the direct_answer gate determine whether LLM is used, and they do this based on phrasing rather than intent. This means:
- "what is X" → LLM synthesis ✅
- "explain X" → template ❌
- "define X" → template ❌
- "tell me about X" → template ❌

Every query that should reach the LLM either hits the simple-word gate or the `simple_response()` fallback, and the user cannot tell which path was taken. The system's perceived intelligence is capped by its most restrictive classifier, not by the LLM's capability.

Fixing this (making classification intent-based and widening the synthesis path) would unlock the majority of the remaining capability gap. It is the single change that most increases system coherence.

---

SECTION 9 — EXACT_NEXT_STEP

**Trace `build_communicator_message_payload` for `"explain photosynthesis"` with runtime logging to confirm exactly where the LLM call is bypassed, then widen the synthesis path in the `direct_answer` branch to reach LLM for non-trivial queries.**

Bounded action:
1. Add temporary debug logging to `dialogue.py` at the `direct_answer` branch entry point to capture `likely_need`, `lead_topic`, and whether `simple_response()` or `_generate_enriched_self_report()` was called
2. Confirm: does `"explain photosynthesis"` reach `direct_answer` branch and hit `simple_response()` at line 921?
3. If yes: modify the `direct_answer` branch to route non-simple-word, non-identity queries toward LLM synthesis instead of `simple_response()`
4. Validate: `"explain photosynthesis"` should return a synthesis-style response, not `simple_response()`
5. Run regression suite to confirm no regression on internal routing (time/status/health)

This is the one step that most directly addresses the main bottleneck with minimal scope and no new complexity.