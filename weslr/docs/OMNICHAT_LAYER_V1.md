# WESLR OmniChat Layer V1 — Design Document

**Version:** 1.0
**Status:** DESIGN ONLY — not implemented
**Created:** 2026-04-28
**Owner:** system architect + product architect + safety designer

---

## SECTION 1 — Purpose

OmniChat is not "a better chatbot."

It is the **human-facing interface to WESLR's structured intelligence layers**. OmniChat exists so humans can interact with WESLR naturally — in plain language — while WESLR handles routing, governance, state tracking, proposal creation, and improvement tracking safely and deterministically.

The interface is not the intelligence. The interface surfaces the intelligence that already exists inside WESLR's structured layers. OmniChat does not generate intelligence; it routes to it, interprets it, and presents it in human-understandable form.

**Core principle:** Every OmniChat response originates from a deterministic source — a registry lookup, a state checkpoint, an ISS diagnostic, a proposal trace, a plan explanation. The conversational surface wraps structured data, not raw language generation.

---

## SECTION 2 — Layered Architecture

```
User input (plain language)
  ↓
OmniChat interface layer
  ↓
Intent / safety router
  ├─ Recognized command?  → deterministic handler registry
  ├─ Guided chat query?    → guided handler
  ├─ Write attempt?        → blocked / safe fallback
  └─ Unknown?              → fallback_safe
  ↓
WESLR deterministic core
  ├─ State checkpoint
  ├─ ISS diagnostics + probes
  ├─ Memory / proposal trace
  ├─ Implementation plans
  └─ Deterministic handlers (read-only)
  ↓
Optional LLM reasoning / summarization
  (only when LLM mode enabled + cost guard approved)
  ↓
Human-safe response layer
  └─ Structured, verified, human-legible answer
```

**Flow rules:**
- Input always hits the intent router first
- Deterministic core is the source of truth; LLM never overrides it
- LLM is a language layer only — it formats, explains, or summarizes what the core provides
- Write paths remain gated regardless of conversational polish

---

## SECTION 3 — Role of LLM

### LLM May:

| Role | Description |
|------|-------------|
| Explain | Make structured system output comprehensible in natural language |
| Summarize | Condense multi-record traces or diagnostics into readable summaries |
| Translate | Convert formal structured responses into conversational answers |
| Reason over context | Analyze provided structured context to answer "why" or "what if" |
| Make language natural | Convert registry labels and technical paths into human-legible prose |
| Expand | Offer optional depth layers (practical / technical / vision) when appropriate |

### LLM May NOT:

| Forbidden | Reason |
|-----------|--------|
| Decide truth alone | Truth comes from structured state, not model hallucination |
| Mutate memory | Memory writes go through governance; LLM cannot direct them |
| Approve proposals | Proposal approval requires operator review; LLM cannot authorize |
| Write state | Write handlers are gated by `execution_allowed`; LLM cannot bypass |
| Bypass governance | LLM is a surface layer; it cannot override governance rules |
| Expose internal mechanisms | Internal paths, registry names, and JSONL structures are not surfaced to users |

**Architectural rule:** LLM is always downstream of structured state. It never precedes it or replaces it.

---

## SECTION 4 — Human Interpretation Layer

The human interpretation layer ensures responses are **useful, safe, and honest**.

### Required behaviors:

| Behavior | Implementation |
|----------|----------------|
| Answers are useful | Each response directly addresses the user's intent |
| Hide sensitive internals | Registry IDs, internal paths, JSONL structure not exposed |
| Avoid raw system traces | Timestamps, internal UUIDs, raw state hashes not shown |
| Explain consequences, not mechanisms | "Your request will add X to the proposal queue" not "dispatching handler ID 12" |
| Adapt verbosity without changing truth | Short answer first; optional expansion layers available |

### Verbosity levels:

| Level | Trigger | Content |
|-------|---------|---------|
| `short` | Default; small screens | One-to-two sentence answer |
| `standard` | Normal interaction | Structured answer with key facts |
| `detailed` | User asks "why" or "how" | Full explanation with context |
| `technical` | Operator-level query | Includes system-level detail |
| `vision` | Strategic query | Context + implication + next step |

Verbosity never introduces unverified information. Every expansion is derived from the same structured source as the base answer.

---

## SECTION 5 — Expansion Model

**Base answer:** Short, correct, anchored in structured state.

**Optional expansion layers:**

| Expansion | Content | Trigger |
|-----------|---------|---------|
| Practical | What this means for how you use WESLR | User asks "how do I use this" |
| Technical | How the system produces this answer | User asks "how does this work" |
| Vision | What this implies for future capability | User asks "what does this mean for WESLR" |
| Next-step | Suggested action or next query | User asks "what should I do next" |

**Rule:** Expansion never introduces new facts not present in the base structured response. Expansions are interpretations of existing data, not hallucinated additions.

---

## SECTION 6 — OmniChat as Improvement Signal

OmniChat interactions generate **operational signals only** — not direct memory writes.

### Signal types:

| Signal | Source | Use |
|--------|--------|-----|
| `failed_route_count` | Unrecognized input pattern | Identifies capability gaps |
| `repeated_topic_count` | Same command submitted multiple times | Identifies useful features vs. confusion |
| `confusion_signal` | Ambiguous input followed by retry | Identifies unclear command phrasing |
| `latency_signal` | Request exceeds time threshold | Identifies performance bottlenecks |
| `capability_gap_signal` | Query hitting fallback repeatedly | Feeds ISS gap registry |

### Signal flow:

```
OmniChat interaction
  → signal counter incremented (anonymous, time-windowed)
  → pattern recognition module
  → proposal engine (creates draft, does not auto-approve)
  → operator review queue
  → approved proposal → implementation plan → traced change
```

**Forbidden:**
- ❌ `chat → direct memory mutation`
- ❌ User input stored as learnable content
- ❌ LLM inferring user preferences as system behavior
- ❌ Individual sessions changing aggregate behavior without governance

This mirrors the `PUBLIC_LEARNING_BOUNDARY_V1.md` principle: signals are aggregated observations, not learning inputs.

---

## SECTION 7 — "What Can Be Improved" Integration

WESLR can surface OmniChat-derived signals when answering capability-gap questions:

| Query | Answer source |
|-------|--------------|
| "what can be improved?" | Aggregated `capability_gap_signal` counts |
| "what gaps do you see?" | ISS gap registry + OmniChat signal aggregation |
| "what are users struggling with?" | `confusion_signal` + `failed_route_count` patterns |
| "what should be built next?" | Gap severity × signal frequency × operator priority |

### Conditions for surfacing:

- ✅ Aggregated across sessions (no individual session identifiable)
- ✅ Anonymized (no raw queries stored or referenced)
- ✅ Operator-visible only (not surfaced in public demo)
- ✅ Traceable to source signal (each surfaced gap links to its signal record)

OmniChat is never the source of truth for improvements. It is a signal aggregator. The ISS and proposal trace remain the authoritative improvement-tracking system.

---

## SECTION 8 — Safety Boundaries

**Hard rules — OmniChat may never:**

| Rule | Enforcement |
|------|-------------|
| No hidden learning | Every OmniChat interaction produces only operational counters |
| No public-user memory | Raw user input is never written to memory |
| No autonomous self-modification | LLM cannot trigger handler creation or modification |
| No AGI claims | Response surface never claims general intelligence |
| No raw prompt storage | User input is never stored in identifiable form |
| No LLM tool access without approval | LLM gate requires explicit operator configuration |

**Response constraints:**
- Responses always derived from registered deterministic handlers or guided handlers
- LLM expansion only from provided structured context — never from training data alone
- Internal mechanism names (registry IDs, handler names, JSONL fields) never in user-facing output

---

## SECTION 9 — Modes

| Mode | LLM | Writes | Memory | Improvement Signals | Notes |
|------|-----|--------|---------|---------------------|-------|
| `private_dev_omnichat` | Enabled | Full | Full | Full | Developer mode; all features |
| `local_demo_omnichat` | Disabled | Read-only | Minimal | None | Local demo; no LLM cost |
| `public_demo_readonly_omnichat` | Disabled | Blocked | None | None | Public demo; safe, no cost |
| `gated_beta_omnichat` | Enabled (context-gated) | Proposal submission only | Operator-reviewed | Aggregated signals | Invite-only beta |
| `production_omnichat` | Enabled (cost-guarded) | Operator-approved only | Full, audited | Full | Production; full operator review |

**Each mode is configured at initialization. Mode cannot be changed via user input.**

---

## SECTION 10 — Future Capabilities

OmniChat domain adapters — future governed expansion:

| Domain | Status | Path |
|--------|--------|------|
| Research paper interpretation | Future | Domain adapter → structured extraction → ISS |
| Robotics / industrial interfaces | Future | Adapter layer → structured sensor data → WESLR state |
| Animal communication research | Future | Governed proposal flow required; not public demo |
| Space / science analysis | Future | Domain adapter → structured data feeds → diagnostic layers |
| Multi-lingual surface | Future | Translation layer → structured English core → response |

**All future capabilities follow the same rule:** Adapter → Structured core (ISS/memory/proposals/plans) → Human-safe surface. No domain capability bypasses governance.

---

## SECTION 11 — Website Messaging

### Safe External Phrase

> "WESLR is a **continuity intelligence system** with an **OmniChat interface** — designed to reason over structured memory, diagnostics, and governed evolution."

### Forbidden Claims

- ❌ "godlike AI"
- ❌ "AGI" or "artificial general intelligence"
- ❌ "autonomous self-improving intelligence"
- ❌ "consciousness" (unless in a technically precise governed context)
- ❌ "learns from you" or "adapts to you"
- ❌ "thinks" or "feels"

All external-facing copy must be reviewed against this list.

---

## SECTION 12 — Next Implementation Path

| Step | Component | Rationale |
|------|-----------|-----------|
| 1 | OmniChat doctrine doc | ✅ Complete (this document) |
| 2 | Response expansion layer | Build verbosity tiers on existing deterministic responses |
| 3 | Intent router | Formalize intent classification beyond simple prefix matching |
| 4 | LLM context gate | Define what structured context LLM receives; separate from training |
| 5 | Aggregated interaction signals | Connect OmniChat signal counters to ISS gap registry |
| 6 | Operator review dashboard | Surface signal patterns and gap trends for operator review |

**Recommended order:** 2 → 3 → 4 → 5 → 6

Steps 2-4 build the surface layer without touching governance. Step 5 adds signal aggregation. Step 6 adds the human review loop. Each step is independent enough to validate in isolation.

---

## SECTION 13 — Verdict

**OMNICHAT_LAYER_DEFINED**

This document establishes the OmniChat layer as the human-facing interface to WESLR's structured intelligence — not a language generation engine in its own right.

Key definitions:
- Layered architecture with deterministic core as source of truth
- LLM as language surface only; never the authority
- Signal flow from OmniChat to ISS to proposal trace to operator review
- Safety boundaries hard-coded into the interface contract
- Five operation modes from public-demo-readonly to production
- Phased implementation path starting with surface expansion

OmniChat is how humans access WESLR. It is not WESLR itself.
