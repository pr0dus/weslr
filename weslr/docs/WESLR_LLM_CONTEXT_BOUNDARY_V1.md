# WESLR LLM Context Boundary V1 — Doctrine Addendum

**Version:** 1.0
**Status:** ACTIVE DOCTRINE — governs all LLM integration points
**Created:** 2026-04-28
**Owner:** operator + system architect
**Supersedes:** WESLR_OMNI_EXECUTION_MODEL_V1.md Section 7 (LLM Gate)
**Related:** WESLR_CORE_IDENTITY_V1.md · WESLR_COORDINATION_LAYER_V1.md · WESLR_OMNI_EXECUTION_MODEL_V1.md · WESLR_LAYERED_ARCHITECTURE_V1.md

---

## SECTION 1 — Purpose

This document defines **strict, enforceable boundaries** for how WESLR's language model integrations receive and use context. The LLM context boundary is an explicit architectural rule — not a convention, not a style preference, not a future goal. It is active doctrine that every implementation must satisfy.

The boundary exists to ensure:

- WESLR's structured intelligence remains the authority
- LLM output remains derivative, never authoritative
- Hidden state is never exposed to external model providers
- Every LLM-assisted response traces back to a WESLR-built payload
- System behavior remains fully auditable regardless of LLM provider

---

## SECTION 2 — Core Principle

> **The LLM does not retrieve context.**
> **WESLR constructs context.**
> **The LLM receives only a bounded payload.**

This is a one-directional architectural rule. Context flows from WESLR to LLM. The LLM never reaches back. It never requests additional data, infers missing fields, or pulls from internal registries, files, or state structures. WESLR assembles the payload; the LLM operates only within it.

**Consequence:** If WESLR does not provide context, the LLM behaves as if it does not exist. The LLM never compensates for missing context by guessing, inferring, or reconstructing.

---

## SECTION 3 — Context Boundary Rules

The boundary is enforced at the point where WESLR prepares a payload for LLM consumption.

### B1 — LLM Receives Only Layer 2–Approved Payloads

No LLM call receives anything that has not been assembled, filtered, and approved by Layer 2 (Coordination Layer). Layer 2 is the sole arbiter of what enters an LLM prompt.

**Enforcement:** Context assembly is an explicit Layer 2 operation. There is no direct path from Layer 1, Layer 0, or external input to the LLM that bypasses Layer 2.

### B2 — No Direct Access to Layer 0

LLM may not read directly from:

| Forbidden | Rationale |
|-----------|-----------|
| `proposal_trace.jsonl` | Operator-governed decisions; source of truth |
| `iss_diagnostics.jsonl` | Internal gap signals; operator-only |
| `implementation_plans.json` | Approved plans; not for LLM interpretation |
| `state_checkpoint.json` | Full system state snapshot; internal |
| Any JSONL or checkpoint file | Raw audit data is never exposed |

### B3 — No Direct Access to Internal Registries

LLM may not read from:

| Forbidden | Rationale |
|-----------|-----------|
| Handler registry | Internal mechanism; not user-relevant |
| Write handler registry | Governance structure; operator-only |
| ISS probe registry | Internal diagnostic names and targets |
| Mode configuration | Security-critical; operator-controlled |
| Rate limit state | Internal operational state |

### B4 — No File System Access

LLM may not read files, list directories, or access paths on the host system. The LLM runs outside the WESLR process boundary; it has no file handle into the workspace.

### B5 — No Hidden State Access

LLM may not access:

- Internal session state
- Operator notes or drafts
- Previous LLM call payloads
- The content of other users' queries
- Unstructured logs or raw event streams

### B6 — No Iterative Context Expansion by LLM

The LLM may not:

- Issue a sub-call to retrieve more context
- Request additional fields or records
- Call back into WESLR handlers to fetch more data
- Use tool-use to read files or state

Context is assembled once, passed to the LLM, and the LLM produces its output within that fixed boundary.

### B7 — No Self-Directed Retrieval

The LLM may not decide "I need to know X" and attempt to retrieve X. If WESLR did not provide X in the payload, the LLM must operate without it or return a limitation statement.

---

## SECTION 4 — Allowed LLM Inputs

When WESLR calls the LLM, it may pass:

### C1 — Deterministic Handler Outputs

The structured response from a registered deterministic handler (Layer 1). This is the primary LLM input — a typed, schema-defined answer that WESLR produced from structured state.

```
Example payload:
{
  "structured_answer": {
    "intent": "capability_query",
    "capabilities": [...],
    "source": "deterministic_handler:list_capabilities"
  },
  "query_type": "explanation",
  "verbosity_level": "standard",
  "constraints": { "may_not": ["decide_truth", "fill_gaps", "override"] }
}
```

### C2 — Structured Graph Subviews

A minimal, purpose-filtered subgraph derived from the Entity or Capability graph. The subview is assembled by Layer 2 and contains only nodes and edges relevant to the specific query.

**Requirements for graph subviews:**
- Assembled by Layer 2 (not raw graph dump)
- Minimal: only nodes/edges needed for this query
- Stripped: no registry IDs, internal paths, provenance metadata
- Mode-safe: no operator-only fields in public modes

### C3 — Summarized State Slices

A concise, WESLR-produced summary of system state or checkpoint data — not the raw state. The summary is derived, formatted, and validated by a deterministic handler before it enters the LLM payload.

**Requirements:**
- Produced by a registered handler
- Not raw JSON/state dumps
- Explicitly labeled with source and reliability

### C4 — Pre-Filtered Context Bundles

Bundles assembled by Layer 2 from multiple sources, with irrelevant or restricted fields removed. A context bundle is a curated payload — not a concatenation of raw data.

**Requirements:**
- Assembled by Layer 2 only
- Each field verified as appropriate for this LLM call
- No internal mechanism names or IDs exposed

### All LLM Inputs Must Be:

| Property | Requirement |
|----------|-------------|
| **Minimal** | Only fields needed for this specific query |
| **Relevant** | Directly addresses the query intent |
| **Source-controlled** | Traces to a registered handler or deterministic read |
| **Mode-safe** | No operator-only or restricted fields in public modes |
| **Stripped** | No internal paths, registry IDs, JSONL field names |
| **Bounded** | Fixed schema; no open-ended field injection |

---

## SECTION 5 — Forbidden LLM Behaviors

These behaviors are architecturally impossible when the context boundary is enforced correctly. They are documented here as doctrine rules in case of implementation gaps.

### D1 — LLM May Not Request Additional Context

The LLM must not ask for more data. If the payload is insufficient, WESLR returns a limitation statement. The LLM does not decide to fetch more.

### D2 — LLM May Not Infer Missing Data Beyond Provided Payload

The LLM must not fabricate facts. If a field is absent from the payload, the LLM must say it does not know — not infer, guess, or extrapolate.

### D3 — LLM May Not Reconstruct Hidden System State

The LLM must not attempt to reverse-engineer WESLR's internal structures from partial information. It may not infer the existence of handlers, registries, modes, or governance mechanisms from the payload.

### D4 — LLM May Not Merge Unrelated Context

The LLM must not combine the current payload with information from previous LLM calls, external knowledge, or training data to produce a compound answer that neither source alone would support.

### D5 — LLM May Not Read Raw User Input History

The LLM does not receive full conversation history. It receives a structured, Layer 2–assembled payload for the current turn only. The raw input history (messages, queries) is never passed to the LLM.

### D6 — LLM May Not Access Memory or Logs Directly

No WESLR memory structure, log file, or session state is accessible to the LLM. Memory is a derived view of tracked state — the LLM accesses it only through WESLR-built payloads assembled by Layer 2.

### D7 — LLM May Not Bypass the Coordination Layer

The LLM cannot route around Layer 2. It cannot call write handlers, trigger proposals, access the ISS, or modify state. It can only produce the output for the current response — it cannot initiate further WESLR operations.

---

## SECTION 6 — Context Assembly Responsibility

Context assembly is an explicit Layer 2 operation. It belongs exclusively to the Coordination Layer. No other layer may assemble context destined for the LLM.

### Responsibilities:

| Who | What |
|-----|------|
| **Layer 2 (Coordination Layer)** | Assembles the LLM payload. Selects fields. Filters restricted data. Enforces mode. Calls LLM. |
| **Layer 1 (Deterministic Core)** | Produces structured answers. Does not call LLM directly. |
| **Layer 3 (OmniChat Interface)** | Receives WESLR-built payload. Formats for display. May not assemble LLM payload. |
| **LLM (Layer 4, External)** | Receives bounded payload. Produces surface expression. Cannot request more context. |

### Rules:

**R1:** OmniChat may request context from Layer 2, but may not construct it.
**R2:** The LLM never participates in context selection or data retrieval.
**R3:** Layer 2 enforces mode safety before constructing any LLM payload.
**R4:** Layer 2 is the only layer that calls the LLM.
**R5:** Layer 2 is the only layer that reads from deterministic handlers for LLM preparation.

---

## SECTION 7 — Failure Behavior

When WESLR cannot assemble sufficient context for a query, behavior is governed by this section — not by LLM judgment.

### When Context Is Insufficient:

**LLM must NOT:**
- Fill gaps with fabricated information
- Guess at missing facts
- Combine unrelated partial contexts
- Use training data to substitute for structured state
- Produce a structured answer WESLR did not provide

**WESLR must return:**
- An explicit **limitation statement**: *"I don't have structured information about that"*
- Or a **safe fallback response** with supported alternatives
- Optionally: list 3–5 relevant registered commands the user can try

**LLM may only:**
- Explain the limitation in natural language
- Suggest how to rephrase the query for supported intents
- Surface the limitation using the verbosity level provided in the payload

### Gap Signal:

Insufficient context is a gap signal. It routes through the standard improvement flow:

```
Insufficient context
    ↓
Anonymous failed-route signal (operator-visible only)
    ↓
ISS gap candidate (if threshold exceeded)
    ↓
Operator decides whether to create a proposal
```

The LLM does not self-improve around the gap. The operator does.

---

## SECTION 8 — Mode Interaction

The mode determines whether the LLM is available at all, and what constraints apply.

### Mode → LLM Availability:

| Mode | LLM Allowed | Constraints |
|------|-------------|-------------|
| `public_demo_readonly` | **Disabled** | LLM call returns limitation statement |
| `local_demo` | **Disabled** | LLM call returns limitation statement |
| `private_dev` | Enabled | Full context gate; no restrictions beyond B1–B7 |
| `gated_beta` | Context-gated | LLM receives only pre-approved payload types |
| `production` | Cost-guarded | LLM usage tracked; budget enforced per session |

### Mode Always Determines LLM Availability:

- Mode is set at WESLR initialization; it is **never mutable via user input**
- Mode is visible in all responses as `_weslr_mode`
- The LLM never decides whether it is available — WESLR enforces this
- User requests cannot bypass mode restrictions

### Context Boundary in Each Mode:

```
public_demo_readonly:
  → LLM disabled entirely
  → No LLM call is made
  → Structured limitation returned directly

local_demo:
  → LLM disabled
  → Same as public_demo_readonly

private_dev:
  → LLM enabled
  → Full context assembly available
  → All B1–B7 rules apply

gated_beta:
  → LLM enabled for approved payload types only
  → Non-approved payloads return limitation
  → Layer 2 enforces approval list

production:
  → LLM enabled
  → Cost guard enforced before LLM call
  → All B1–B7 rules apply
```

---

## SECTION 9 — Security Rationale

The LLM context boundary is a security boundary. It exists to prevent:

### H1 — Hallucination Becoming System Truth

Without the boundary, an LLM could produce a confident, plausible-sounding answer that is not grounded in WESLR's actual state. If that answer is accepted as structured truth, the system becomes non-deterministic and unauditable. The boundary ensures WESLR determines truth — the LLM only formats it.

### H2 — Hidden State Exposure

WESLR's internal registries, governance structures, diagnostics, and operator-only data are not intended for public or LLM consumption. The boundary ensures these are never in an LLM payload — no matter what query is made.

### H3 — Model-Driven Reasoning Drift

LLMs change behavior over time (training updates, fine-tuning, provider changes). If WESLR relies on LLM reasoning to fill gaps, system behavior drifts with model behavior. The boundary keeps WESLR deterministic regardless of which LLM provider or model version is in use.

### H4 — Full Auditability of Outputs

Every WESLR response traces back to a deterministic handler, a structured payload, and Layer 2 assembly. When the LLM boundary is respected, auditability is preserved: the operator can always identify what WESLR provided and what the LLM did with it.

### H5 — WESLR Deterministic Core Integrity

WESLR's core is deterministic. The same query, from the same state, always returns the same structured answer. This property is only preserved if the LLM cannot alter that answer or inject non-WESLR content into the structured response. The boundary enforces this.

---

## SECTION 10 — Cross-Doctrine Alignment

The LLM context boundary is not standalone. It is enforced by and reinforces every other WESLR doctrine document.

### WESLR_CORE_IDENTITY_V1.md:

> *"LLM is optional and restricted — Language models format, explain, or summarize what the structured core provides. They never replace it."*

The context boundary is the **enforcement mechanism** for this identity rule. Without the boundary, the CORE_IDENTITY principle has no architectural anchor.

**Link:** `WESLR_CORE_IDENTITY_V1.md` Section 3, Rule R6 — *"Never allow LLM to override structured state or bypass governance"*

### WESLR_COORDINATION_LAYER_V1.md:

Layer 2 is defined as the only layer that writes to Layer 0 and the only layer that coordinates agents and LLM calls. The context boundary is the **LLM-specific expression** of Layer 2's coordination authority.

**Link:** `WESLR_COORDINATION_LAYER_V1.md` Section 2 — *Interpretation Engine* and *Write Handler Dispatch* both enforce boundaries; the LLM context boundary extends this to LLM payloads.

### WESLR_OMNI_EXECUTION_MODEL_V1.md:

The Omni Execution Model defines the LLM Gate (Section 7) as the point where WESLR decides whether to call the LLM and what to pass. The context boundary is the **content rule** for what that gate passes.

**Link:** `WESLR_OMNI_EXECUTION_MODEL_V1.md` Section 7 — *LLM Input Contract* specifies the payload structure; this document governs its contents.

### WESLR_LAYERED_ARCHITECTURE_V1.md:

The layered architecture defines LLM as Layer 4 (external system), downstream of Layer 2 (Coordination) and Layer 3 (Interface). The context boundary is the **enforcement** of that layer ordering: Layer 4 never bypasses Layer 2 to access Layer 0 or Layer 1 directly.

**Link:** `WESLR_LAYERED_ARCHITECTURE_V1.md` Section 2, Layer 4 rules — *Layer 4 communicates only through Layer 2; no direct Layer 0 access*

### Coherence Check:

| Doctrine Rule | Enforced By | This Document |
|---------------|-------------|---------------|
| LLM is downstream, not authoritative | LLM Context Boundary (B1–B7) | ✅ |
| WESLR determines truth | Failure Behavior (Section 7) | ✅ |
| No LLM authority over structured state | Forbidden Behaviors (Section 5) | ✅ |
| Mode controls LLM availability | Mode Interaction (Section 8) | ✅ |
| Layer 2 assembles all LLM payloads | Context Assembly (Section 6) | ✅ |
| Context never includes raw JSONL or registries | Boundary Rules (Section 3, B2–B3) | ✅ |
| LLM cannot self-retrieve | Boundary Rules (Section 3, B6–B7) | ✅ |

---

## SECTION 11 — Future-Proof Constraints

These constraints ensure the boundary holds regardless of how WESLR or its integrations evolve.

### F1 — LLM Providers May Change; Boundary Remains Constant

New LLM providers, model versions, or API changes do not modify the boundary rules. The boundary is enforced by WESLR's Layer 2 assembly — not by the LLM's behavior or capabilities.

### F2 — Context Payload Format May Evolve; Boundary Remains Enforced

Future payload formats (new fields, new schemas, new LLM-compatible representations) must still satisfy B1–B7. A new format does not grant access to previously forbidden data sources.

### F3 — Multi-Model Setups Must All Obey Same Boundary

If WESLR uses multiple LLM providers or models simultaneously, each call is subject to the same boundary rules. No model receives context another model was denied.

### F4 — No Future Feature May Grant LLM Autonomous Retrieval

New features, handlers, or capabilities may not introduce a path for the LLM to retrieve context without Layer 2 assembly. This is a hard architectural constraint, not a guideline.

### F5 — Context Boundary Survives Architecture Refactors

Even if Layer 2 is decomposed, renamed, or restructured, the context boundary must remain enforced by whatever component assumes Layer 2's coordination responsibilities.

---

## SECTION 12 — Verification

Compliance with this document is verified by:

| Check | Method |
|-------|--------|
| LLM never receives raw JSONL | Code audit: no direct JSONL→LLM path |
| LLM never reads files directly | Code audit: no file-read LLM call |
| Context assembled only in Layer 2 | Code audit: Layer 2 boundary enforced |
| Mode enforcement before LLM call | Unit test: mock mode; verify LLM call blocked |
| Failure behavior returns limitation | Unit test: insufficient context → limitation statement |
| Boundary preserved in multi-model setup | Integration test: verify all models receive identical payload |
| No autonomous retrieval by LLM | Code audit: no tool-use, no sub-call, no back-channel |

---

## SECTION 13 — Verdict

**WESLR_LLM_CONTEXT_BOUNDARY_DEFINED**

This document establishes the LLM context boundary as an enforceable architectural rule. The boundary is enforced by Layer 2, respected by all LLM integrations, and maintained regardless of provider, model, or format changes.

The boundary is not aspirational. It is not a style guide. It is the consequence of WESLR's core identity: **WESLR determines truth; LLM expresses truth.**

Every future implementation must satisfy this boundary. Every deviation requires a doctrine amendment, not a code merge.
