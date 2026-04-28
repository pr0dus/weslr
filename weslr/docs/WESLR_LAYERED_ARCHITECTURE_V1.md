# WESLR Layered Architecture V1 — Doctrine

**Version:** 1.0
**Status:** ACTIVE DOCTRINE — governs all WESLR architectural development
**Created:** 2026-04-28
**Owner:** operator + system architect

---

## SECTION 1 — Purpose

This document defines the **canonical layered architecture** of WESLR. Every component has a defined role, layer, and boundary. Layers communicate only with adjacent layers. Nothing bypasses governance.

---

## SECTION 2 — Layer Definitions

### Layer 0 — Structured State (Ground Truth)

**What it is:** The persisted state of WESLR — checkpoints, traces, plans, registries, diagnostics.

**Components:**
- `state_checkpoint.json` — versioned system state snapshot
- `proposal_trace.jsonl` — immutable audit trail of proposals, decisions, plans
- `implementation_plans.json` — approved plans linked to proposals
- `iss_diagnostics.jsonl` — ISS gap signals and probe results
- `handler_registry` — registered deterministic handlers

**Rules:**
- Layer 0 is the **only source of truth**
- No other layer can override Layer 0
- All state changes are recorded here first

**Forbidden:**
- ❌ Direct mutation from any layer above
- ❌ Model-generated state without trace

---

### Layer 1 — Deterministic Core (Computation)

**What it is:** Read-only computation over Layer 0. Pure functions. No side effects.

**Components:**
- `deterministic_handlers.py` — registered read-only query handlers
- `dispatch_deterministic_handler()` — priority-sorted trigger matching
- `state_checkpoint` queries — checkpoint state reads
- ISS queries — diagnostic and probe reads
- Proposal/plans queries — trace and plan reads

**Rules:**
- Deterministic handlers **never write** to Layer 0
- Results are **reproducible** — same query, same state → same result
- Handlers are **registered** — no ad-hoc handler creation at runtime

**Forbidden:**
- ❌ Deterministic handlers creating write side effects
- ❌ Runtime handler registration without registry update

---

### Layer 2 — Coordination Layer (Routing and Governance)

**What it is:** Routes requests, enforces mode, manages governance flow, coordinates agents.

**Components:**
- `interpretation.py` — intent classification, mode enforcement, rate limiting
- `write_handlers.py` — write handler dispatch, approval gates
- `governance_surface.py` — proposal intake, operator review routing
- `ISS/` — issue system: gap detection, probe management, intake processing

**Rules:**
- Layer 2 routes requests to the correct layer
- Write operations require approval gates
- Mode (`private_dev`, `local_demo`, `public_demo_readonly`, etc.) is enforced here
- No write bypasses governance

**Forbidden:**
- ❌ Write handler dispatch without mode check
- ❌ Proposal auto-approval without operator review
- ❌ Mode toggling via user input

---

### Layer 3 — OmniChat Interface (Human-Facing Surface)

**What it is:** The conversational layer humans interact with. Formats, explains, and surfaces structured outputs.

**Components:**
- OmniChat response builder
- Verbosity expansion layer (short → detailed → technical → vision)
- Human-safe explanation layer
- Guided handlers (pre-authorized Q&A)

**Rules:**
- Layer 3 always derives from Layers 0–2
- LLM is **downstream only** — used for formatting, explanation, summarization
- LLM never provides truth not present in Layer 0
- Responses never expose internal mechanism names

**Forbidden:**
- ❌ LLM generating answers without structured context
- ❌ Layer 3 directly mutating Layer 0 or Layer 1
- ❌ Raw user input stored or learned from

---

### Layer 4 — External Systems (Outside WESLR)

**What it is:** External tools, models, data sources, and services that integrate with WESLR.

**Components:**
- Optional LLM providers (Ollama, OpenAI, etc.)
- OpenClaw agent infrastructure
- GitHub (source of truth for code)
- weslr.de website / staging server

**Rules:**
- Layer 4 communicates **only through Layer 2** (no direct Layer 0 access)
- External data entering WESLR goes through governance (ISS intake, proposal creation)
- No external system can bypass governance

**Forbidden:**
- ❌ External system writing directly to Layer 0
- ❌ LLM tool access without operator configuration
- ❌ OpenClaw modifying WESLR state without going through proposal trace

---

## SECTION 3 — Layer Communication Rules

| From \ To | Layer 0 | Layer 1 | Layer 2 | Layer 3 | Layer 4 |
|-----------|---------|---------|---------|---------|---------|
| **Layer 0** | — | Read only | Read only | No direct | No direct |
| **Layer 1** | No write | — | No write | No direct | No direct |
| **Layer 2** | Write (gated) | Route to | — | Route to | Route to |
| **Layer 3** | No direct | No direct | Route through | — | Route through |
| **Layer 4** | No direct | No direct | Route through | Route through | — |

**Key rule:** Writes to Layer 0 always originate in Layer 2. Layer 2 is the only layer that can write to Layer 0 — and it only does so through governance gates.

---

## SECTION 4 — Mode Enforcement

Modes filter which layers are active:

| Mode | Layer 2 Writes | Layer 3 LLM | Layer 4 |
|------|---------------|-------------|---------|
| `private_dev` | Full | Enabled | Open |
| `local_demo` | Blocked | Disabled | Local only |
| `public_demo_readonly` | Blocked | Disabled | None |
| `gated_beta` | Proposal sub. only | Context-gated | Restricted |
| `production` | Operator-approved | Cost-guarded | Monitored |

Mode is set at initialization. **Mode cannot be changed via user input.**

---

## SECTION 5 — Future-Proof Constraints

| Constraint | Rationale |
|------------|-----------|
| No new layer may be inserted between Layer 0 and Layer 2 | Would bypass governance |
| No lateral communication跳过 layers | Maintains traceability |
| Layer 4 integrations must define a protocol through Layer 2 | Prevents direct external writes to Layer 0 |
| Any new model integration is Layer 4 only | Models are tools, not intelligence sources |

---

## SECTION 6 — Verdict

**WESLR_LAYERED_ARCHITECTURE_V1_DEFINED**

Canonical layers: Layer 0 (Structured State) → Layer 1 (Deterministic Core) → Layer 2 (Coordination/Governance) → Layer 3 (OmniChat Interface) → Layer 4 (External Systems). Writes always originate in Layer 2. Layer 0 is the only source of truth.
