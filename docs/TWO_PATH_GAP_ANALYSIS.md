# Two-Path Capability Gap Analysis — 2026-04-18

## SECTION 1 — PATHS INSPECTED

### Path A: Canonical HTTP /chat
- **Entrypoint:** `main.py:2121` — `_CHAT_EXECUTOR.submit(build_communicator_message_payload, ...)`
- **Handler:** `dialogue.py:503` — `build_communicator_message_payload()`
- **Classification:** `interpretation.py:interpret_human_turn()` → `likely_need` routing
- **Context sources:** `_get_introspection_context()`, `_get_valence_context()`, `_get_entity_context()`, `_get_consciousness_context()`, `get_internal_docs_context()`, `get_lifecycle_narrative_message()`
- **Internal routing:** direct_answer / concept_explanation / self_report / etc. (12+ branches)
- **Fallback:** `_get_language_module().simple_response()`

### Path B: sim.py build_communicator_message (CLI/legacy)
- **Entrypoint:** `sim.py:8501` — `build_communicator_message()` (called by main.py:cmd_communicator_message)
- **Pre-enrichment:** tax_knowledge → tax_context → find_relevant_research_note → then calls Path A's payload
- **Context sources:** `get_tax_knowledge_answer()`, `get_tax_context_answer()`, `find_relevant_research_note()`
- **Then delegates to:** `build_communicator_message_payload()` (same function as Path A!)
- **Key difference:** active_thread = `pick_relevant_active_thread()` (thread object) vs Path A's `"human_message"` string

---

## SECTION 2 — PATH TRACE

### Path A: Canonical HTTP /chat

```
HTTP POST /chat
  → main.py:2121 _CHAT_EXECUTOR.submit(
        build_communicator_message_payload,
        narrative=load_communicator_self().get("narrative_state", {}),
        relationships=load_relationships(),
        active_thread="human_message",         ← STRING, not thread
        latest_human={"message": message},      ← minimal, no topics
        research_context=None,                 ← ALWAYS None!
        l0_identity=load_tier("l0"),
        l1_operating=load_tier("l1"),
        l2_session=load_tier("l2"),
      )
  → dialogue.py:503 build_communicator_message_payload(
        narrative={...},
        relationships={...},
        active_thread="human_message",         ← no thread object
        latest_human={"message": msg},
        research_context=None,                ← NEVER populated from HTTP
      )
  → interpretation.interpret_human_turn(msg) → likely_need
  → routing branches (direct_answer, concept_explanation, etc.)
  → internal capability helpers (time, status, health, introspection, valence, etc.)
  → _get_language_module().simple_response() [fallback]
```

### Path B: sim.py build_communicator_message (wraps A)

```
main.py cmd_communicator_message → cmd_communicator_message()
  → sim.py:8501 build_communicator_message()
  → pre-enrichment (tax + research note):
      if "entfernungspauschale" in msg → return get_tax_knowledge_answer()
      if "was bedeutet das" in msg → return get_tax_context_answer()
      latest_topic → find_relevant_research_note(load_public_memory(), topic)
  → build_communicator_message_payload(
        narrative=load_communicator_self()['narrative_state'],
        relationships=load_communicator_self()['relationships'],
        active_thread=pick_relevant_active_thread(...), ← actual thread object
        latest_human=recent_messages[-1],              ← full message with topics
        research_context={...},                         ← populated from research!
      )
  → dialogue.py:503 (same payload function, richer inputs)
```

---

## SECTION 3 — CAPABILITY DELTA TABLE

| Capability / Context Source | Path A (HTTP) | Path B (sim.py) | Location | What it contributes | Stronger Path |
|---|---|---|---|---|---|
| **Tax knowledge (entfernungspauschale)** | ❌ No | ✅ Yes | sim.py:8517-8518 | Returns structured tax answer, short-circuits before calling payload | Path B |
| **Tax context (was bedeutet das)** | ❌ No | ✅ Yes | sim.py:8532-8533 | Returns explanation of previous tax concept, short-circuits | Path B |
| **Research note search (find_relevant_research_note)** | ❌ No | ✅ Yes | sim.py:8545, integration.py:4 | Populates research_context from public_memory by topic | Path B |
| **research_context to payload** | ❌ Always None | ✅ Populated | sim.py:8547-8552 | Enables `synthesize_research_answer()` in concept_explanation | Path B |
| **Introspection context** | ✅ Yes | Via A (same payload) | dialogue.py:31,618 | Perturbation detection → enriched self-report | TIE (both reach it via same payload) |
| **Valence context** | ✅ Yes | Via A | dialogue.py:47,618 | Trade-off tracking → enriched self-report | TIE |
| **Entity graph context** | ✅ Yes | Via A | dialogue.py:12,668 | Entity/relationship context for concept_explanation | TIE |
| **Consciousness context** | ✅ Yes | Via A | dialogue.py:60,429 | Consciousness detector → enriched identity | TIE |
| **Internal docs themes** | ✅ Yes | Via A | dialogue.py:641,692,784,791,893 | Per-branch thematic enrichment | TIE |
| **Lifecycle narrative** | ✅ Yes | Via A | dialogue.py:157-160 | Lifecycle state message generation | TIE |
| **Time (clock) routing** | ✅ Yes | Via A | dialogue.py:597,750 | Internal datetime routing | TIE |
| **Status routing** | ✅ Yes | Via A | dialogue.py:603-606,822-825 | load_failsafe_status + load_llm_status | TIE |
| **Health routing** | ✅ Yes | Via A | dialogue.py:611-613,830-832 | load_failsafe_status only | TIE |
| **Self-report generation** | ✅ Yes | Via A | dialogue.py:358-424 | Enriched self-report with introspection/valence | TIE |
| **Identity generation** | ✅ Yes | Via A | dialogue.py:429-498 | Enriched identity with entity/consciousness | TIE |
| **Concept synthesis** | ✅ Yes | Via A | dialogue.py:170-300 | synthesize_concept_or_self_reply + synthesize_research_answer | TIE |
| **L0/L1/L2 identity tiers** | ✅ Yes | ❌ No | main.py:2128-2130, sim.py:1141 | Loaded from JSON files, available in Path A | Path A |
| **active_thread as thread object** | ❌ String "human_message" | ✅ pick_relevant_active_thread() | sim.py:8510 | Enables topic/thread context in routing | Path B |
| **latest_human with topics** | ❌ Just {"message": msg} | ✅ recent_messages[-1] with topics | sim.py:8505-8506 | Richer routing context | Path B |
| **Memory layers (L0/L1/L2)** | ✅ Yes (injected) | ❌ No | main.py:2128-2130 | Tiers passed to payload, enable richer responses | Path A |
| **simple_response fallback** | ✅ Yes | Via A | dialogue.py:simple_response() | Generic fallback when no internal routing matches | TIE |
| **greeting_response** | ✅ Yes | Via A | dialogue.py:greeting_response() | Greeting branch | TIE |
| **direct_answer_response** | ✅ Yes | Via A | dialogue.py:direct_answer_response() | Lead topic direct answer | TIE |
| **concept_explanation branch** | ✅ Yes | Via A | dialogue.py:804-896 | Concept synthesis with research_context | TIE |
| **self_report branch** | ✅ Yes | Via A | dialogue.py:583-643 | Enriched self-report + introspection/valence | TIE |
| **get_current_year()** | ❌ No | ❌ No | sim.py:87 (unused) | Unused function, zero call sites | Neither |

---

## SECTION 4 — TOP PROMOTION CANDIDATES

Ranked by: user value + implementation risk + architectural cleanliness + real usefulness

### TOP CANDIDATES (safe, high-value)

**#1 — `research_context` population (HTTP /chat)**
- **What:** HTTP /chat always passes `research_context=None`. sim.py path populates it via `find_relevant_research_note()`.
- **Value:** Would enable `synthesize_research_answer()` in canonical /chat for questions about known research topics.
- **Risk:** Low — additive only, doesn't break existing routing.
- **Architectural cleanliness:** Medium — needs `find_relevant_research_note()` to be callable from dialogue.py context, or HTTP /chat handler needs to pre-populate like sim.py does.
- **Chat usefulness:** High for research-aware topics.
- **Recommendation:** PROMOTE. Add `find_relevant_research_note()` call to HTTP /chat handler OR pre-populate in main.py before calling payload.
- **Score:** ★★★★★

**#2 — `latest_human` with topics (HTTP /chat)**
- **What:** HTTP /chat sends `{"message": msg}` only. sim.py path sends `recent_messages[-1]` which includes topics.
- **Value:** `interpret_human_turn()` in Path A works without topics. Having them would make routing more precise.
- **Risk:** Very low — topics are already handled by `interpret_human_turn()`.
- **Architectural cleanliness:** High — just enrich the dict before calling payload.
- **Chat usefulness:** Medium-High.
- **Recommendation:** PROMOTE. HTTP /chat handler should call `interpret_human_turn()` and pass topics like sim.py does.
- **Score:** ★★★★☆

**#3 — `active_thread` as thread object (HTTP /chat)**
- **What:** HTTP /chat sends `"human_message"` string. sim.py sends `pick_relevant_active_thread()` result.
- **Value:** Currently `elif active_thread:` branch at dialogue.py:963 short-circuits on string (ValueError), so it's never reached. Proper thread object would enable that branch.
- **Risk:** Low — thread object branch already exists in dialogue.py, just never reached.
- **Architectural cleanliness:** High — the branch is already written, just needs proper input.
- **Chat usefulness:** Medium.
- **Recommendation:** PROMOTE. Pre-compute `pick_relevant_active_thread()` in HTTP /chat handler like sim.py does.
- **Score:** ★★★★☆

**#4 — `get_tax_knowledge_answer()` routing**
- **What:** German tax keyword routing in sim.py not in dialogue.py.
- **Value:** Useful for German-speaking users asking about tax topics.
- **Risk:** Low — just a keyword match + function call.
- **Architectural cleanliness:** Medium — duplicating sim.py logic in dialogue.py.
- **Chat usefulness:** High for tax topics, but narrow audience.
- **Recommendation:** PROMOTE with keyword pattern in direct_answer branch, same pattern as time/health.
- **Score:** ★★★☆☆

**#5 — `get_tax_context_answer()` routing**
- **What:** Follow-up tax explanation ("was bedeutet das") in sim.py not in dialogue.py.
- **Value:** Enables follow-up tax questions.
- **Risk:** Low — keyword match.
- **Architectural cleanliness:** Medium.
- **Chat usefulness:** Medium (follow-up only).
- **Recommendation:** PROMOTE alongside #4 (same tax domain).
- **Score:** ★★★☆☆

### DEFER (medium risk / lower value)

**#6 — `entity graph` pre-enrichment**
- **What:** `_get_entity_context()` already wired in dialogue.py, but not pre-populated from sim.py's richer context.
- **Value:** Medium — already active in concept_explanation.
- **Risk:** Low but architectural change needed.
- **Recommendation:** DEFER — already functional via `_get_entity_context()` within the function.

**#7 — Memory anchors (continuity/goals/episodic/semantic)**
- **What:** `get_relevant_continuity_anchors()`, etc. only in sim.py, not reachable from HTTP /chat.
- **Value:** Unclear — these enrich context but in ways that may not help short /chat responses.
- **Risk:** High — large architectural change.
- **Recommendation:** DEFER — no evidence current /chat responses are missing these.

### KEEP OUT OF /CHAT

**#8 — `get_current_year()`**
- **What:** Defined at sim.py:87, zero call sites, completely unused.
- **Decision:** MARK LEGACY. Remove from sim.py in a future cleanup pass. Not worth wiring to /chat.
- **Recommendation:** Remove.

**#9 — Governance / proposal / CDI modules**
- **What:** `change_proposals.py`, `cdi_proposal_builder.py`, `governance_surface.py` — operator-only.
- **Decision:** Keep out of /chat. These are operator-facing, not user-facing.
- **Recommendation:** Operator-only.

**#10 — Background analysis modules**
- **What:** `background_analysis/`, `active_work_capsule.py` — background tasks.
- **Decision:** Keep out of /chat. These run asynchronously, not as chat responses.
- **Recommendation:** Leave as background.

---

## SECTION 5 — BOUNDED MIGRATION ORDER

### Step 1 (Smallest, safest)
Add `find_relevant_research_note()` pre-population to HTTP /chat handler (or call it before calling payload). Add one keyword pattern `"what is the current year?"` → `get_current_year()` in direct_answer branch.

### Step 2
Enrich `latest_human` dict in HTTP /chat handler with `interpret_human_turn()` output (topics, likely_need, turn_type, reply_shape).

### Step 3
Pre-compute `pick_relevant_active_thread()` in HTTP /chat handler and pass as thread object instead of string.

### Step 4
Add tax knowledge keyword patterns to direct_answer branch (`entfernungspauschale`, `fahrtkosten`) → `get_tax_knowledge_answer()`.

### Items to defer
- Memory anchor enrichment (continuity/episodic/semantic) — architectural change, no clear /chat benefit
- Entity graph pre-enrichment — already functional via `_get_entity_context()`
- Governance/proposal modules — operator-only, not /chat appropriate

### Items to keep out
- Background analysis
- CDI proposal builder
- Governance surface
- `get_current_year()` — mark legacy, remove from sim.py

---

## KEY FINDING: The Two Paths Are Convergent But Asymmetric

Both paths end up calling `build_communicator_message_payload()` (dialogue.py). The gap is NOT about different routing logic — it's about:

1. **HTTP /chat always passes `research_context=None`** — loses the research synthesis path
2. **HTTP /chat passes minimal `latest_human`** — no topics, no rich context
3. **HTTP /chat passes `active_thread="human_message"` string** — cannot trigger the thread-object branch in dialogue.py:963
4. **HTTP /chat has L0/L1/L2 tiers** that sim.py path does not have
5. **sim.py has tax knowledge + research note pre-enrichment** that HTTP /chat does not have

The simplest migration is to enrich the HTTP /chat handler's call to `build_communicator_message_payload` with the same pre-enrichments that sim.py does — without changing the payload function itself.