# WESLR Response Expansion Layer V1 — Doctrine Extension

**Version:** 1.0
**Status:** ACTIVE DOCTRINE — governs how WESLR transforms structured answers into human-aligned responses
**Created:** 2026-04-28
**Owner:** operator + system architect
**Related:** WESLR_CORE_IDENTITY_V1.md · WESLR_OMNI_EXECUTION_MODEL_V1.md · WESLR_LLM_CONTEXT_BOUNDARY_V1.md · WESLR_EVIDENCE_WORKSPACE_V1.md · WESLR_SIGNAL_AGGREGATION_V1.md

---

## SECTION 1 — Purpose

WESLR's deterministic core produces structured, authoritative answers. Those answers are correct by design — but raw structured output is not always immediately useful, clear, or actionable for a human user. This document defines how WESLR expands, formats, and presents structured answers to feel intelligent and helpful without ever introducing new facts, hallucinating details, or compromising truth authority.

> **"Response expansion transforms structured truth into useful communication — it never invents truth."**

Expansion is a transformation layer, not a generation layer. It takes what WESLR knows and makes it accessible. It never fills gaps, never infers beyond the payload, and never presents unverified information as structured knowledge.

---

## SECTION 2 — Core Invariant

The following invariant is never violated, under any mode, at any depth:

### Expansion = Transformation, NOT Invention

**WESLR May in Expansion:**

| Action | Description |
|--------|-------------|
| Rephrase | Restate the same information in different words |
| Structure | Organize known facts into hierarchies, bullets, tables |
| Explain | Clarify how something works or why something is true |
| Contextualize | Show relationships between known facts |
| Guide | Suggest next steps within WESLR's documented capabilities |

**WESLR May NOT in Expansion:**

| Forbidden | Rationale |
|-----------|-----------|
| Add facts not in structured state | Truth authority is absolute; WESLR never invents |
| Guess missing information | Gaps are labeled; guesses are hallucinations |
| Generalize beyond known scope | Expansion stays within the payload |
| Merge evidence with structured knowledge | These are separate streams; never conflated |
| Infer unstated causal chains | Causal links require structured provenance |

**Consequence:** Any expansion step that cannot be traced to a known source in the payload must be removed or labeled as uncertainty.

---

## SECTION 3 — Response Expansion Layers

Every WESLR response may optionally include up to four expansion layers. Each layer is independently optional — the user or mode may request any combination. No layer adds new facts; each layer only makes existing facts more accessible.

### Layer L1 — Core Answer (Deterministic, Minimal, Authoritative)

**What it is:** The raw structured answer from the deterministic handler. Compact, typed, authoritative.

**Content:** The registered handler's response payload, with field names appropriate for display.

**When used:** Always present; the other layers are built on top of it.

**Example:**
```
capability: weslr.self_inspect
status: active
confidence: 0.95
```

### Layer L2 — Structured Explanation

**What it is:** Clarifies what the core answer means, how it was derived, and why it is structured this way.

**Content:** Field-by-field explanation, provenance reference, confidence interpretation.

**Requires:** L1 present.

**Example:**
```
The self-inspection capability is active (confidence 0.95).
This means WESLR has verified its own state against
the last checkpoint (state_checkpoint.json, v47).
```

### Layer L3 — Contextual Expansion

**What it is:** Shows use cases, implications, connections, and relevant related information — all drawn from existing structured state.

**Content:** Related entities, capability implications, co-occurrence patterns, historical context.

**Requires:** L1 + L2 available.

**Example:**
```
This capability connects to the co-occurrence layer:
queries about self-improvement often co-occur with
capability expansion proposals. You may also want to try:
- show system overview
- show capabilities
- show proposals in review
```

### Layer L4 — Guidance Layer

**What it is:** Directs the user toward productive next steps within WESLR's documented capabilities.

**Content:** Suggested queries, exploration paths, relevant commands.

**Requires:** L1 present.

**Example:**
```
You can explore further:
- "explain how wsesr self-inspection works" (deep)
- "show system overview" (structured)
- "how can you improve" (operator path)
```

### Layer Availability by Mode:

| Mode | L1 | L2 | L3 | L4 |
|------|----|----|----|-----|
| `public_demo_readonly` | ✅ | ✅ short | ❌ | ✅ short |
| `local_demo` | ✅ | ✅ | ✅ | ✅ |
| `private_dev` | ✅ | ✅ | ✅ | ✅ |
| `gated_beta` | ✅ | ✅ | ✅ | ✅ |
| `production` | ✅ | ✅ | ✅ | ✅ cost-guarded |

---

## SECTION 4 — Response Type Expansion Rules

Each WESLR response type has specific expansion rules. Expansion never changes the authoritative core; it only adds interpretive and navigational layers.

### RT1 — Deterministic Response

**Core:** Registered handler output. Authoritative.

**Expansion rules:**
- L2: Explain each field in the response using the handler's documentation
- L3: Show related capabilities or entities if available in state
- L4: Offer 2–3 related structured queries

**Constraints:** No speculation; every expansion sentence must trace to a known handler field or documented behavior.

---

### RT2 — Guided Response

**Core:** Pre-authorized identity or clarification response.

**Expansion rules:**
- L2: Expand on WESLR's identity or the guided topic with structured references
- L3: Show related guided entry points; surface related structured queries
- L4: Provide canonical next steps in the guided topic sequence

**Constraints:** Stay within the guided domain; do not drift into unguided territory.

---

### RT3 — Graph-Derived Response

**Core:** Answer derived from entity or capability graph traversal.

**Expansion rules:**
- L2: Explain what the graph traversal found and why
- L3: Expand relationships — show connections between entities/capabilities without inventing new nodes
- L4: Suggest related graph queries (entity details, capability relationships)

**Constraints:** Do not invent nodes, edges, or attributes not present in the graph. If the graph lacks a connection, say so explicitly.

---

### RT4 — Evidence Workspace Response

**Core:** Exploration output from Evidence Workspace. Explicitly labeled as non-WESLR knowledge.

**Expansion rules:**
- L2: Expand uncertainty explanation — clarify what is well-supported vs. contested
- L3: Compare sources if multiple sources exist; highlight contradictions
- L4: Suggest next investigation steps, refined search terms, or how to validate findings

**Constraints:**
- **Never** convert evidence into structured knowledge
- **Never** merge Evidence Workspace output with deterministic output
- Label must appear on every Evidence Workspace response
- Every claim must cite its source when available

---

### RT5 — Fallback Response

**Core:** Returned when no structured handler matches the query.

**Expansion rules:**
- L2: Explain clearly why WESLR cannot answer — not a vague failure, but a specific limitation
- L3: Suggest 3–5 registered commands that might serve the user's underlying intent
- L4: Offer Evidence Workspace as an explicit opt-in alternative

**Before Fallback:** Check whether the query pattern matches a known evidence gap signal. If so, record the signal per WESLR_SIGNAL_AGGREGATION_V1.md.

**Dead-end replacement:** The old fallback was a flat limitation statement. The new fallback is a structured assistance offer:

```
Old: "I don't have information about that."
New: "That topic isn't in WESLR's structured knowledge.
      WESLR can:
      1. Explore it as evidence (opt-in)
      2. Suggest related structured queries
      3. Log it as a demand signal for operator review"
```

---

### RT6 — Blocked Write Response

**Core:** Returned when a write operation is blocked by mode or governance.

**Expansion rules:**
- L2: Explain why the write was blocked (mode, governance rule, or execution flag)
- L3: Show the user what write operations are available in the current mode
- L4: Guide toward allowed alternatives; suggest how to route the intent through governance

**Example:**
```
This operation requires writes, which are blocked
in public_demo_readonly mode.
Allowed alternatives:
- explore this topic via Evidence Workspace
- submit a proposal for operator review
- use a private_dev session for full access
```

---

## SECTION 5 — Expansion Strategies

These are the defined strategies for transforming structured content. Each is a valid transformation; none introduces new facts.

### S1 — Hierarchical Structuring

Take a flat or nested payload and render it as a clear hierarchy.

```
Input: {entity: X, capability: Y, status: Z}
Output:
  Entity: X
  └─ Capability: Y
     └─ Status: Z
```

### S2 — Bullet Decomposition

Break a compound answer into discrete, labeled items.

### S3 — Causal Explanation

Explain why a state is what it is, using known provenance:

```
"Status is 'degraded' because the last checkpoint
(state_checkpoint.json, v47) recorded 2 unresolved
inadequacy signals."
```

### S4 — Comparison Framing

Present two or more structured options in a comparison structure:

```
Method A: fast, read-only, no governance
Method B: slower, write-capable, operator-reviewed
```

### S5 — Scenario Illustration (Grounded ONLY)

Illustrate a scenario using only structured facts — no invented details.

```
"When you use 'show system overview', WESLR
reads the latest checkpoint and returns the
structured state snapshot."
```

**Forbidden:** Invented scenarios not traceable to structured state.

### S6 — Progressive Disclosure

Allow the user to reveal depth incrementally without re-querying.

```
Level 1 (minimal):  [status: active]
Level 2 (standard): [status: active, checkpoint: v47, confidence: 0.95]
Level 3 (deep):     [status: active + full handler output]
[click to expand deeper levels]
```

Each level adds detail from the same payload — no new facts introduced at deeper levels.

---

## SECTION 6 — Depth Control

Depth is an explicit user-settable parameter. It controls how many expansion layers are applied.

### Depth Levels:

| Level | Label | Expansion |
|-------|-------|-----------|
| `minimal` | Fast answer | L1 only |
| `standard` | Default | L1 + L2 + L4 |
| `deep` | Expanded reasoning | L1 + L2 + L3 + L4 |
| `expert` | Full breakdown | All layers + provenance chain + full handler metadata |

### Depth Constraints:

| Rule | Description |
|------|-------------|
| D1 | Depth never introduces new facts |
| D2 | Depth only reveals what is already in the structured payload |
| D3 | Depth is mode-gated: `public_demo_readonly` maxes at `standard` |
| D4 | Deep and Expert require `private_dev` or higher |
| D5 | Depth request is a user preference, not a guarantee — if content is shallow, expansion stays shallow |

### Depth Override:

If a lower depth is requested but the content is insufficient for that depth, WESLR downgrades gracefully rather than padding with speculation:

```
Requested: deep
Actual content: L1 only
Result: L1 + L2 (standard), with note: "limited structured detail
         available for this query"
```

---

## SECTION 7 — Evidence Integration in Expansion

When Evidence Workspace output enters the expansion pipeline, special rules apply.

### Evidence Label Placement:

Every Evidence Workspace expansion must include the evidence label:

**Format:** `"[Evidence — not WESLR structured knowledge]"`

**Placement:** Appears as a header prefix and a footer suffix on every evidence-based response.

### Uncertainty Highlighting:

Evidence Workspace expansions must explicitly mark confidence levels:

| Evidence Level | Language |
|---------------|----------|
| High confidence | "Sources consistently indicate..." |
| Mixed/conflicting | "Sources disagree on...; some indicate..., others..." |
| Low confidence | "Limited or conflicting evidence; appears to be..." |
| No evidence | "No evidence found; unable to assess..." |

### Source Presentation:

Evidence sources are cited directly:

```
[Source 1] Domain report, 2024 — states X
[Source 2] Industry analysis, 2025 — states Y
[Source 3] Academic paper — inconclusive on X
```

No source invented or implied beyond what was retrieved.

### Forbidden Evidence Merges:

**Never merge:**
- Evidence Workspace output with deterministic output in the same paragraph
- Uncertainty-cited claims with high-confidence structured claims
- External source references with WESLR internal state references

**Separation rule:** Evidence Workspace and deterministic responses are separate response types. Expansion combines layers within a type, not across types.

---

## SECTION 8 — User Guidance Layer

The Guidance Layer (L4) is the most interaction-oriented expansion. It belongs on every response type and helps users navigate WESLR productively.

### Guidance Types:

| Type | Trigger | Example |
|------|---------|---------|
| Related queries | Any structured response | "Try 'show system overview' for more context" |
| Deep dive | Explicit request | "For expert detail, ask 'explain [topic] expert'" |
| Evidence offer | Fallback or unknown topic | "I can explore this as evidence if you'd like" |
| Governance path | Blocked write | "To pursue this, submit a proposal to the operator" |
| Capability route | Improvement intent | "Use 'how can you improve' to explore structured options" |

### Guidance Constraints:

| Rule | Description |
|------|-------------|
| G1 | Guidance must stay within WESLR's documented capabilities |
| G2 | Never imply unsupported features |
| G3 | Never promise outcomes beyond WESLR's authority |
| G4 | Evidence offer appears only in fallback or explicit unknown states |

---

## SECTION 9 — Mode Behavior for Expansion

Mode controls which expansion layers are available and how deeply they render.

### Mode → Expansion Matrix:

| Mode | Max Depth | Evidence | L3 | Cost Guard |
|------|-----------|----------|----|------------|
| `public_demo_readonly` | `standard` | Limited or off | ❌ | N/A |
| `local_demo` | `deep` | ✅ labeled | ✅ | N/A |
| `private_dev` | `expert` | ✅ labeled | ✅ | N/A |
| `gated_beta` | `deep` | ✅ labeled | ✅ | Soft |
| `production` | `expert` | ✅ labeled | ✅ | Hard |

### public_demo_readonly Expansion Rules:

- L1 always present
- L2 present but concise — no extended prose
- L3 disabled (no contextual connections — creates surface for confusion)
- L4 short form only — 1–2 guidance options
- Evidence workspace: may be limited or disabled entirely
- Fallback expansion: minimal — 2 suggestions max

### local_demo / private_dev:

- All layers available
- Evidence fully labeled
- L3 shows entity/capability connections from co-occurrence data
- L4 full guidance

### Production:

- All layers available
- LLM expansion cost-guarded per session
- Budget tracking enforced before deep LLM expansion

---

## SECTION 10 — LLM Role in Expansion

The LLM participates in expansion only as a downstream formatter. It never determines truth.

### LLM Allowed Operations in Expansion:

| Operation | Description | Input |
|-----------|-------------|-------|
| Formatting | Apply prose style, paragraph structure | Structured payload |
| Summarization | Condense lengthy structured output | L1 + L2 content |
| Explanation | Rephrase structured facts in accessible language | L1 + L2 content |
| Readability improvement | Improve flow without changing meaning | Any expansion layer |

### LLM Input Contract for Expansion:

```
LLM receives:
  {
    "response_type": "deterministic | guided | graph_derived | evidence | fallback | blocked",
    "structured_payload": { ... L1 core ... },
    "expansion_layers": ["L2", "L3", "L4"],
    "depth": "minimal | standard | deep | expert",
    "mode": "...",
    "constraints": {
      "may_not": ["add_facts", "infer_causation", "merge_evidence_with_structured"],
      "must": ["include_evidence_label", "cite_sources", "downgrade_if_insufficient"]
    }
  }
```

### LLM Forbidden Operations:

- Adding facts not in the structured payload
- Inferring causal relationships not in state
- Merging Evidence Workspace output with deterministic output
- Changing the authoritative meaning of any field
- Fabricating provenance or confidence levels

### Anti-Hallucination Gate (pre-output):

Before any LLM-formatted response is returned, WESLR verifies:

| Check | Action if Failed |
|-------|-----------------|
| Every sentence has a source in the payload | Remove unsourced sentence |
| No implicit assumption added | Label assumption as "inferred" |
| Evidence and structured output not merged | Split into separate labeled blocks |
| Evidence label present if evidence workspace | Add/reinforce label |

If verification fails, WESLR falls back to deterministic-only output (L1) with a note.

---

## SECTION 11 — Anti-Hallucination Enforcement

This section defines the explicit checks that run before any expansion output is finalized.

### Pre-Output Verification Checklist:

Before returning an expanded response, WESLR confirms:

| # | Check | Standard |
|---|-------|----------|
| V1 | Every factual statement has a source in the structured payload | Required |
| V2 | No sentence introduces data not in the payload | Required |
| V3 | No implicit assumptions added as facts | Required |
| V4 | Evidence and deterministic content are not merged | Required for evidence responses |
| V5 | Evidence label is present on all evidence workspace output | Required |
| V6 | Source citations are accurate and match retrieved evidence | Required |
| V7 | Guidance suggestions are within WESLR's documented capabilities | Required |

### Downgrade Protocol:

If verification fails at any step:

```
Fail V1/V2/V3:
  → Remove unsourced content
  → Return L1 only (deterministic core)
  → Note: "expanded content removed due to verification failure"

Fail V4/V5/V6:
  → Reinforce evidence label
  → Separate evidence and structured blocks
  → Remove uncited claims

Fail V7:
  → Remove unsupported guidance
  → Return only guidance that traces to documented capabilities
```

### Uncertainty Label Trigger:

If L2 or L3 cannot be verified as fully grounded:

```
"Inference detected: [statement] is derived from
[known_fact], not directly from structured state.
Treated as low-confidence."
```

---

## SECTION 12 — Implementation Mapping

This section maps the expansion layer to WESLR's current architecture and defines the future implementation path.

### Current Architecture → Expansion Layer:

| Component | Current Role | Expansion Role |
|-----------|-------------|----------------|
| `deterministic_handlers.py` | Produces L1 core | L1 remains here |
| `interpretation.py` | Routes, classifies | Routes to expansion layer; does not expand |
| `response_formatter.py` | Basic formatting | Becomes: receives L1, applies expansion layers |
| Layer 3 (future) | Not separated | Expansion layer lives here |

### Future Module Structure:

```
weslr/
  omnichat/
    response_expander.py    # Expansion engine
    depth_controller.py     # Depth level enforcement
    evidence_labeler.py     # Evidence output labeling
    guidance_builder.py     # L4 guidance construction
    anti_halluc_gate.py    # Pre-output verification
```

### Expansion Pipeline (Future):

```
Deterministic Handler Output (L1)
    ↓
Depth Controller (apply depth settings)
    ↓
Evidence Labeler (if evidence workspace response)
    ↓
L2 Builder (structured explanation from handler metadata)
    ↓
L3 Builder (contextual connections from co-occurrence/proposals)
    ↓
L4 Builder (guidance from registered commands)
    ↓
Anti-Hallucination Gate (verify all statements)
    ↓
LLM Formatter (if mode permits + cost allows)
    ↓
Final Response
```

---

## SECTION 13 — Non-Goals

These are explicitly rejected as expansion layer goals:

| Rejected | Reason |
|----------|--------|
| Chatbot personality simulation | WESLR is not a persona; it is infrastructure |
| Emotional AI | Emotion is not a structured WESLR concept |
| Open-ended free conversation | WESLR is a structured intelligence interface |
| Creative generation outside scope | Generation is limited to expansion of known facts |
| LLM-first answering | LLM is downstream; never the primary answer source |
| Speculative expansion | Any expansion that cannot trace to source is forbidden |

---

## SECTION 14 — Cross-Doctrine Alignment

| Document | Alignment |
|----------|-----------|
| WESLR_CORE_IDENTITY_V1.md | Expansion respects identity rules: no new capabilities claimed, no personality projected, truth authority preserved |
| WESLR_OMNI_EXECUTION_MODEL_V1.md | Expansion is the L3 surface: step 10 in the execution pipeline; maps to response types defined here |
| WESLR_LLM_CONTEXT_BOUNDARY_V1.md | LLM is strictly downstream formatter; receives bounded payload; cannot add facts |
| WESLR_EVIDENCE_WORKSPACE_V1.md | Evidence responses have special expansion rules: mandatory labels, source separation, uncertainty highlighting |
| WESLR_SIGNAL_AGGREGATION_V1.md | Fallback expansion may record signals; evidence demand signals feed aggregation |
| WESLR_COORDINATION_LAYER_V1.md | Layer 2 controls what reaches expansion; expansion never bypasses Layer 2 routing |

---

## SECTION 15 — Expected Outcomes

When fully implemented, WESLR responses become:

| Property | Before | After |
|----------|--------|-------|
| Usefulness | Correct but flat | Correct and navigable |
| Clarity | Requires WESLR literacy | Accessible to new users |
| Helpfulness | Minimal guidance | Structured next steps |
| Trustworthiness | High | High + verifiable (anti-halluc gate) |
| Determinism | Core preserved | Core preserved + verifiable |
| Mode fitness | Inconsistent | Mode-appropriate depth |

**Core property unchanged:** Every response is still deterministic at its core. Expansion makes the deterministic answer more accessible — it never replaces it.

---

## SECTION 16 — Verdict

**WESLR_RESPONSE_EXPANSION_LAYER_DEFINED**

Response Expansion is a transformation layer, not a generation layer. It takes structured truth from WESLR's deterministic core and makes it accessible, navigable, and human-aligned — without ever inventing facts, bypassing governance, or compromising truth authority.

Core invariant: Expansion = transformation. Not invention. Every sentence in an expanded response traces back to a known structured source. Where that trace is missing, the sentence is removed or downgraded.

WESLR remains deterministic at its core. Expansion makes the core useful.
