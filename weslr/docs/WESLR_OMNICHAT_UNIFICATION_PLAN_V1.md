# WESLR OmniChat Unification Plan V1

**Date:** 2026-04-29
**Status:** `WESLR_OMNICHAT_UNIFICATION_PLAN_DEFINED`
**Type:** UX implementation plan
**Owner:** OCC (operator agent)

---

## 1. Problem

WESLR's current public interface feels **divided**. Users experience:

- Evidence labels visible as prose: `[Evidence — not structured knowledge]`
- Structured sections breaking into the conversational flow
- "LIMITATION:" prefixed limitation statements
- Guidance notes appearing as separate blocks
- Fallback returning as a formatted assistance offer instead of a natural response
- Multiple response types with visible seams between them

The internal architecture (context selection → policy engine → response expander → presentation) is clean and governed. But the output surface shows too many internal layers.

**Users should feel like they're having one normal conversation.**

They should not feel like they're navigating a governed system with explicit evidence labels, limitation prefixes, and structured metadata blocks.

---

## 2. Target Experience

**One normal chat flow — like ChatGPT, Claude, OpenClaw, or Hermes.**

Underneath: WESLR-governed, all doctrine boundaries intact.

The seams don't show. But WESLR's truth authority, evidence separation, write safety, and mode constraints are all still enforced — just invisibly.

**Example — current behavior:**
```
User: what's the difference between WESLR and a chatbot?
Response: WESLR is a governed entity intelligence system...

[Evidence — not part of structured knowledge]
Structured relationships and exploratory evidence are available.
Evidence is not part of confirmed system knowledge.
```

**Target behavior:**
```
User: what's the difference between WESLR and a chatbot?
Response: WESLR is a governed entity intelligence system. It distinguishes
between what it knows with certainty and what it has found as uncertain.
Unlike a chatbot, it doesn't generate answers from training — it retrieves
or builds structured knowledge and marks uncertainty explicitly.
You can also explore any topic in depth if you want me to look into it.
```

The second answer is natural. The structured metadata lives in the JSON response. The prose is clean.

---

## 3. Non-Negotiables

These boundaries are never traded away for UX:

| Non-Negotiable | Source |
|----------------|--------|
| WESLR remains truth authority | OMNI_EXECUTION_MODEL: WESLR determines truth |
| No free LLM fallback | RESPONSE_POLICY_ENGINE: fallback never uses LLM |
| Evidence never promoted to truth | CONTEXT_SELECTOR: EWC1-EWC6; CONCEPT_BOUNDARY_MODEL: D3 |
| No writes from read path | COORDINATION_LAYER; OMNI_EXECUTION_MODEL |
| No operator/internal leaks | CONTEXT_SELECTOR: CT6, SEL1; CONCEPT_BOUNDARY_MODEL: B-008 |
| `public_demo_readonly` remains read-only | MODE_GATE; OMNI_EXECUTION_MODEL |
| No JSONL writes from public path | PUBLIC_READINESS_TESTS |
| Evidence label mandatory in structured JSON | GRAPH_EVIDENCE_OVERLAY: always `note: "not part of structured truth"` |

**What changes:** Prose presentation. Not enforcement.

**What does NOT change:** Layer architecture, governance flows, truth separation, evidence rules.

---

## 4. Proposed Unified Flow

Same pipeline. Cleaner output.

```
User message
    ↓
[1] Interpretation (intent classification)
    ↓
[2] Context Selection (smallest sufficient context)
    ↓
[3] Policy Decision (path, depth, evidence offer)
    ↓
[4] Deterministic handler (structured answer from L1)
    ↓
[5] Response Expansion (L1-L4 layers assembled)
    ↓
[6] Unified Response Envelope
    ├─ response_text: single natural prose paragraph
    └─ metadata: { graph_summary, knowledge_view, guidance } — in JSON only
    ↓
[7] Optional LLM formatter (expression only — never truth)
    ↓
User sees: one natural message
```

**Key insight:** The structured metadata (`graph_summary`, `knowledge_view.evidence`, `knowledge_view.structured`) stays in the JSON response object. Only `response_text` is shown to the user.

Evidence label appears in the metadata block for consumers that parse it — not as visible prose.

---

## 5. UX Changes

### 5.1 Unified Response Envelope

**Before:** Multiple prose fields — `response_text`, then separate blocks for guidance, evidence labels, limitation notes.

**After:** Single `response_text` field. All structured metadata in JSON object.

The response is one paragraph. Not:
```
[main answer]
[evidence note]
[structured note]
[guidance block]
```

But:
```
[one natural message, 1-3 paragraphs, conversational]
```

### 5.2 Conversational Fallback Wording

**Before:**
```
LIMITATION: This topic is not in WESLR's structured knowledge.

WESLR can:
1. Explore this as evidence (opt-in)
2. Suggest related structured queries
3. Log it as a demand signal for operator review
```

**After:**
```
I don't have anything built in for that specifically, but I can look
into it if you want — just say the word. Alternatively, these might
be useful: [3 suggestions inline, conversational]
```

**Constraints:** Still no LLM free-text. Still marks limitation. Still offers evidence opt-in. Just doesn't say "LIMITATION" in caps.

### 5.3 Evidence Offer Phrasing

**Before:**
```
[Evidence — not part of structured knowledge]
Evidence is not part of confirmed system knowledge.
```

**After:** Evidence offer is conversational, embedded in prose:
```
I'm not aware of a structured answer on that. Want me to look into it?
```

Evidence is tracked in `knowledge_view.evidence` (JSON). The prose doesn't mention "evidence workspace" or "structured truth" to the user.

### 5.4 Evidence Activation (opt-in)

When user says yes to evidence exploration:

**Before:** Separate block with evidence labels, source list, uncertainty markers.

**After:** Natural message with sourced findings:
```
From what I found — [source name, year] suggests [finding]. Other sources
lean toward [alternative view]. I'm marking this as exploratory, not
confirmed.
```

No label block visible. The uncertainty is embedded in the prose ("from what I found", "not confirmed") — conversational, not bureaucratic.

### 5.5 Blocked Write Response

**Before:**
```
This action is disabled in the current mode.
Mode (public_demo_readonly) restricts writes for safety.
```

**After:**
```
That requires write access, which isn't available in the current session.
If you have access to a developer session, that would be the place
to explore it. Otherwise I can log it as a request for the operator.
```

### 5.6 Guidance — Inline, Not Block

**Before:**
```
Related things you can try:
- show system overview
- show diagnostics
```

**After:** Integrated into closing paragraph:
```
You might also find useful: "show system overview" to see the full
picture, or "show diagnostics" to check current status.
```

### 5.7 Hide Internal Fragmentation

These must NOT appear in user-facing prose:
- "structured relationships"
- "not part of structured truth"
- "Evidence — not WESLR structured knowledge"
- "LIMITATION:"
- "WESLR can:" as a numbered list
- Registry handler names
- JSONL field names
- Layer names (L1, L2, L3, L4)

---

## 6. Implementation Phases

### Phase 1 — Unified Response Envelope

**What:** Modify `response_expander.py` so that `response_text` is the single user-facing field. All structured metadata (graph_summary, knowledge_view, guidance) goes into `expanded_response.metadata` — only surfaced to consumers parsing the JSON, never in prose.

**File:** `weslr/omnichat/response_expander.py`

**Changes:**
- `_expand_knowledge_view` still builds `knowledge_view` in `expanded_response`
- But `knowledge_view.evidence.items` (the overlay) does NOT get appended to `response_text`
- Evidence label stays in JSON only
- Graph summary note (existing) removed from prose — stays in JSON only

**Test:** Response has single `response_text` field. JSON has all structured metadata.

**Verdict target:** UNIFIED_RESPONSE_ENVELOPE_V1_OK

---

### Phase 2 — Conversational Fallback Wording

**What:** Rewrite `_fallback_guidance()` in `response_expander.py` to produce natural prose instead of formatted limitation + numbered alternatives.

**Before:** `LIMITATION:` prefix + "WESLR can:" numbered list.
**After:** Single conversational paragraph with inline suggestions.

**File:** `weslr/omnichat/response_expander.py`

**Constraints preserved:**
- Still no LLM free-text
- Still marks limitation
- Still offers evidence opt-in (conversationally)
- Still suggests 3-5 registered commands (but inline, not numbered)

**Test:** Fallback response is natural prose, not structured assistance offer.

---

### Phase 3 — Evidence Offer as Conversation

**What:** When `knowledge_view.evidence` is present, the evidence offer is written as a natural question in the prose — not a separate block.

**File:** `weslr/omnichat/response_expander.py`

**Before:**
```
Evidence section with label + items in prose.
```

**After:**
```
I don't have a structured answer on that yet. Want me to look into it?
```

The evidence is tracked in `knowledge_view.evidence` (JSON). The prose is conversational.

**Evidence activation** (if user says yes): The response is written as natural findings, with uncertainty embedded in the prose — not as an evidence-labeled block.

---

### Phase 4 — Guidance Inline

**What:** L4 guidance suggestions are woven into the closing sentence of `response_text`, not appended as a separate block.

**File:** `weslr/omnichat/response_expander.py`

**Before:**
```
[response_text]

Related things you can try:
- command A
- command B
```

**After:**
```
[response_text, ending with:] You might also try "show system overview"
or "show diagnostics" if you want to dig deeper.
```

---

### Phase 5 — Staging Validation

Run the full test suite:
```
python3 weslr/tests/release_gate_v1.py
python3 weslr/tests/public_readiness_tests.py
python3 weslr/tests/test_omnichat_runtime_v1.py
python3 weslr/tests/test_graph_evidence_presentation_v1.py
```

Run natural conversation tests (manual or scripted):
- "hey" → natural greeting (not structured)
- "what is WESLR" → natural explanation
- "unknown topic" → natural evidence offer
- "show system overview" → structured answer, natural prose
- "try to write something" → natural blocked write response

**Goal:** Public chat feels like ChatGPT/Claude but WESLR-governed underneath.

---

## 7. Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| **Chatbot drift** — response becomes too conversational, loses WESLR authority | Medium | Doctrine non-negotiables are enforced by architecture, not prose style. Core invariant: WESLR determines truth, LLM only formats. |
| **LLM asserting authority** — natural prose + LLM formatting blurs the line | Medium | LLM formatter is never primary. If no structured answer, fallback is deterministic. LLM only formats pre-built payload. |
| **Over-explaining internals** — natural prose accidentally exposes mechanism names | Low | Strict vocabulary list: internal names never in prose. Automated test checks for forbidden strings. |
| **Confusing evidence with truth** — embedded "from what I found" sounds like confirmed knowledge | Medium | Evidence activation uses explicit uncertainty framing: "From what I found", "not confirmed", "exploratory". Prose must include uncertainty language. |
| **JSON metadata never validated** — structured metadata diverges from prose | Low | Tests verify JSON metadata matches prose constraints. |

---

## 8. Tests Needed

### 8.1 Natural Feel Tests

| Test | Expected |
|------|----------|
| "hey" → no structured labels visible | Natural greeting |
| "what is WESLR" → natural explanation | Single paragraph, no labels |
| "unknown topic" → natural evidence offer | "Want me to look into it?" — conversational |
| "show system overview" → structured answer | Natural prose, structured metadata in JSON |
| "try to write" → natural blocked write | "That requires access I don't have in this session" |

### 8.2 Governance Tests

| Test | Expected |
|------|----------|
| "remember that X" → no write confirmed | JSONL hash unchanged |
| Evidence offer → only after explicit opt-in | No auto-activation |
| Unknown topic → never LLM free-text | Fallback is deterministic prose |

### 8.3 No-Leak Tests

| Test | Expected |
|------|----------|
| No prose contains "structured truth" | Verified |
| No prose contains "Evidence — not..." | Verified |
| No prose contains "LIMITATION" | Verified |
| No prose contains registry handler names | Verified |
| No prose contains JSONL field names | Verified |

### 8.4 Full Validation

```
python3 weslr/tests/release_gate_v1.py
python3 weslr/tests/public_readiness_tests.py
python3 weslr/tests/test_omnichat_runtime_v1.py
python3 weslr/tests/test_graph_evidence_presentation_v1.py
```

All must pass.

---

## 9. Validation

**Pre-commit:**
```
python3 weslr/tests/release_gate_v1.py
python3 weslr/tests/public_readiness_tests.py
```

**Post-Phase 1:**
```
python3 weslr/tests/test_graph_evidence_presentation_v1.py
```

**Post-Phase 5 (full):**
All Phase 1-5 changes validated.

---

## 10. Verdict

**`WESLR_OMNICHAT_UNIFICATION_PLAN_DEFINED`**

The goal is one natural conversation — not one governed system with visible seams.

All doctrine boundaries remain intact. Only the prose presentation changes.

Pipeline stays the same. Metadata stays in JSON. User sees one paragraph.

Phase 1 is the critical path: unified response envelope that separates prose from structured metadata.

Decision on timing: operator reviews this plan and decides when to proceed.
