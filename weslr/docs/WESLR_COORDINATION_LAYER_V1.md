# WESLR Coordination Layer V1 — Doctrine

**Version:** 1.0
**Status:** ACTIVE DOCTRINE — governs WESLR routing, governance, and coordination
**Created:** 2026-04-28
**Owner:** operator + system architect

---

## SECTION 1 — Purpose

The **Coordination Layer** is Layer 2 of WESLR's architecture. It routes requests, enforces mode, manages governance flow, and coordinates agents. It is the only layer that can write to Layer 0 — and it only does so through approval gates.

The Coordination Layer is the **gateway between intent and action**. Every user request passes through it. Every write operation originates from it. It is where governance is enforced.

---

## SECTION 2 — Components

### Interpretation Engine
**Role:** Classify intent, enforce mode, route to correct handler.

**What it does:**
- Matches input against deterministic handler triggers
- Enforces `public_demo_readonly` mode (blocks writes)
- Enforces rate limits
- Returns structured responses

**What it may NOT do:**
- Dispatch writes in read-only mode
- Bypass mode checks
- Store raw user input

---

### Write Handler Dispatch
**Role:** Route write operations through governance gates.

**What it does:**
- Matches write attempts against `WRITE_HANDLER_REGISTRY`
- Checks `execution_allowed` flag
- Requires operator confirmation for high-side-effect writes
- Routes proposal-creating writes through ISS intake

**What it may NOT do:**
- Auto-approve writes without confirmation
- Execute writes in `public_demo_readonly` mode
- Dispatch writes when `execution_allowed=False`

---

### Governance Surface
**Role:** Route proposals through operator review.

**What it does:**
- Receives proposals from ISS intake or operator input
- Presents proposals for operator review
- Records decisions in `proposal_trace.jsonl`
- Triggers plan creation on approval

**What it may NOT do:**
- Auto-approve proposals
- Bypass operator review for high-impact changes
- Modify proposal content without governance

---

### ISS (Issue System)
**Role:** Detect and track gaps, run probes, manage intake.

**What it does:**
- Records gap signals from deterministic runs
- Runs probe diagnostics against registered targets
- Processes ISS intake (converted suggestions → proposals)
- Maintains `iss_diagnostics.jsonl`

**What it may NOT do:**
- Auto-create proposals without intake processing
- Run probes without registered entries
- Expose internal probe results publicly

---

### Agent Coordination
**Role:** Coordinate multi-agent OCC ↔ OCW handoffs.

**What it does:**
- Enforce GitHub as the single source of truth for code handoffs
- Track commit hashes through handoff protocol
- Validate OCW deployments against known-good commits
- Report deployment state to operator

**What it may NOT do:**
- Allow OCC → OCW direct file transfer (GitHub only)
- Authorize OCW to modify WESLR core
- Bypass the handoff protocol for production deployments

---

## SECTION 3 — Governance Flow

Every significant state change follows this path:

```
Intent
  ↓
Interpretation (classify + mode enforce)
  ↓
[Read operation?]  →  Deterministic handler  →  Structured response
  ↓
[Write operation?]
  ↓
[execution_allowed=False?]  →  Blocked (public_demo_readonly)
  ↓
[high side effect?]  →  Requires confirmation  →  Wait for operator
  ↓
[proposal-creating?]  →  ISS intake  →  Governance surface  →  Operator review
  ↓
[approved?]  →  proposal_trace.jsonl  →  Plan creation  →  Implementation
  ↓
Traced change recorded
```

**Rule:** No state change bypasses this flow. No exceptions.

---

## SECTION 4 — Mode Enforcement Rules

| Mode | Writes | LLM | Rate Limits | Agent Coordination |
|------|--------|-----|------------|-------------------|
| `private_dev` | Full | Enabled | None | Full |
| `local_demo` | Blocked | Disabled | Soft | Local only |
| `public_demo_readonly` | Blocked | Disabled | Hard (10/min/IP) | None |
| `gated_beta` | Proposal only | Context-gated | Hard | Restricted |
| `production` | Operator-approved | Cost-guarded | Monitored | Full + audit |

**Mode rules:**
- Mode set at initialization; **never changeable via user input**
- Mode change requires operator action + restart
- Mode is always visible in responses (`_weslr_mode` field)

---

## SECTION 5 — Write Handler Rules

| Rule | Description |
|------|-------------|
| All writes gated by `execution_allowed` | No writes when `False` |
| High-side-effect writes require confirmation | `requires_confirmation=True` handlers wait for operator |
| Proposal-creating writes route through ISS intake | Creates draft; does not auto-approve |
| Public mode blocks ALL writes | `public_demo_readonly` → all writes return `fallback_safe` |
| No write handler may self-authorize | Every write has an explicit `write_guard` function |
| No raw user input in write payloads | Sanitize before dispatch |

---

## SECTION 6 — Agent Coordination Rules

| Rule | Description |
|------|-------------|
| OCC is canonical source agent | OCC designs; OCW deploys |
| GitHub is the single handoff mechanism | OCC commits; OCW pulls; no direct file transfer |
| OCW may not modify WESLR core | OCW deploys; OCC designs |
| OCW may not touch e-qubs.de | Completely forbidden |
| All OCW deployments validated by tests | `release_gate_v1.py` passes before deployment |
| Commit hash tracked through every handoff | Before + after recorded per OCW_HANDOFF_V1.md |

---

## SECTION 7 — Forbidden Coordination Behaviors

| Forbidden | Reason |
|-----------|--------|
| Direct OCC → OCW file transfer | Undermines governance; no audit trail |
| Write dispatch without `execution_allowed` check | Would bypass safety |
| Proposal auto-approval without operator review | Violates governance principle |
| Mode toggling via user input | Safety boundary; operator controls mode |
| OCW editing WESLR core logic | Architecture boundary |
| OCW deploying without running tests | Would deploy untested code |
| Write operations in `public_demo_readonly` mode | Public demo safety requirement |

---

## SECTION 8 — Future-Proof Constraints

| Constraint | Rationale |
|------------|-----------|
| New coordination components must route through Layer 2 | Maintains single write origin point |
| New agent types must comply with handoff protocol | Maintains audit trail across agents |
| New modes must define write/LLM/signal boundaries | Modes exist to enforce safety per context |
| Governance flow changes require operator proposal | Governance is itself governed |
| ISS intake changes require registry update + test | Keeps probe/gap system auditable |

---

## SECTION 9 — Verdict

**WESLR_COORDINATION_LAYER_V1_DEFINED**

The Coordination Layer (Layer 2) is WESLR's gateway: routing requests, enforcing modes, managing writes, running governance, and coordinating agents. It is the only layer that writes to Layer 0 — and every write is traceable to a governance decision. No exceptions.
