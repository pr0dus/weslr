# WESLR Public Learning Boundary — V1

**Version:** 1.0
**Status:** active doctrine — governs public interaction learning
**Created:** 2026-04-27
**Owner:** operator + lead architect

---

## SECTION 1 — Problem Definition

### Why Direct Learning from Users Is Dangerous

Public users cannot be trusted to provide accurate, non-manipulative signals. Any system that ingests raw user input and uses it to change behavior directly is vulnerable to adversarial manipulation. WESLR's state is governed, traceable, and operator-controlled — direct user-driven learning violates all three properties.

### Poisoning Risk

A malicious user can flood WESLR with crafted inputs designed to make the system adopt false patterns. Repeated false claims, fake operator authority, corrupted proposals, or scripted command sequences can pollute aggregated signals. If those signals directly drive system changes, the damage is irreversible without operator intervention.

### Drift Risk

Without a clear boundary, WESLR could gradually shift behavior away from its documented design. Small changes accumulate: a command starts returning slightly different results, a pattern query starts including edge cases, a handler starts matching broader inputs. Over time, the system's behavior diverges from what was specified. Drift is invisible until it is too late.

### Loss of Traceability

WESLR's core promise is that every significant state change traces back to an operator-approved proposal. If learning happens automatically at the public interface, there is no proposal, no review, no rollback. The audit trail becomes fiction.

---

## SECTION 2 — WESLR Learning Principle

> **WESLR does NOT learn from users. WESLR learns from observed patterns under governance.**

WESLR may observe statistical patterns in public interaction — query frequencies, failure rates, latency distributions — but these observations are **signal aggregates only**. They are never directly applied to system state.

Learning means: a system change is proposed, reviewed, and approved. Only then does WESLR change. Before that point, nothing is learned.

The distinction:
- **Observation** — safe, anonymous, stateless
- **Learning** — a system change, requires governance

---

## SECTION 3 — Allowed Public Signals

WESLR may safely collect the following signals from public interactions:

| Signal | Type | Description |
|--------|------|-------------|
| `query_frequency` | counter | How often a given command string is received |
| `identical_query_count` | counter | Repeated identical queries from any source |
| `failed_route_count` | counter | Queries that return `None` (no handler matched) |
| `unknown_concept_count` | counter | Queries containing unrecognized concepts |
| `repeated_iss_gap_trigger_count` | counter | ISS gaps referenced in queries vs. confirmed gaps |
| `latency_anomaly_count` | counter | Requests exceeding timing thresholds |

### Constraints

- **No raw user content stored** — only pre-defined signal keys
- **No personal data** — no user identity, IP, session token, or metadata
- **No direct mapping to identity** — signals are aggregated anonymously
- **Time-windowed** — signals decay or reset; no permanent per-user counters
- **No free-text memory** — no user-provided strings stored in any JSONL

---

## SECTION 4 — Forbidden Learning Paths

The following are **explicitly forbidden** as automatic public learning mechanisms:

- ❌ Automatic proposal creation from public users
- ❌ Automatic memory writes from public inputs
- ❌ Automatic capability or handler creation
- ❌ Automatic modification of deterministic handlers
- ❌ Automatic schema changes to JSONL records
- ❌ Silent behavior changes without operator approval
- ❌ Storing raw user query text in any log
- ❌ Using query content to influence routing decisions
- ❌ Building user profiles or preference models
- ❌ Generating "insights" from individual user sessions

---

## SECTION 5 — Pattern → Proposal Flow (Public-Safe)

### The Safe Learning Flow

```
1. PUBLIC INTERACTION
   → WESLR receives query (read-only or write-attempt)
   → Response returned; raw query discarded

2. SIGNAL AGGREGATION
   → Signal counter incremented (anonymous, time-windowed)
   → No content stored; only metric key + timestamp

3. PATTERN DETECTION
   → WESLR detects signal threshold exceeded
      (e.g., 100 identical queries/week for unknown concept)
   → Pattern is an INTERNAL artifact, not a user-visible state

4. INTERNAL ARTIFACT CREATION
   → Pattern logged to internal diagnostic record (ISS gap signal)
   → Operator can inspect; no automatic action

5. PROPOSAL GENERATION
   → Operator or M6 layer converts pattern into a proposal
   → Proposal describes the observed pattern and proposed change

6. OPERATOR REVIEW
   → Operator reviews proposal via standard WESLR workflow
   → Operator approves, rejects, or modifies

7. SYSTEM CHANGE
   → Only after operator approval
   → Change applied via standard handler/plan mechanism
   → Trace logged in proposal_trace.jsonl
```

### Key Property

Steps 1–4 require **no operator action** and produce **no system state change**. They are observation only. The first moment WESLR can act is step 5 — where a human reviews and authorizes.

---

## SECTION 6 — Separation of Domains

### PRIVATE (Developer / Operator)

- Full access to all signal aggregates
- Full proposal creation authority
- Full system evolution authority
- Direct JSONL write access
- Handler modification

### PUBLIC

- Signal generation only (counters, not content)
- No direct influence on system state
- No write permissions to any JSONL
- No access to proposal or plan records
- Responses are deterministic, not adaptively modified

### Boundary Rule

> **Nothing a public user does can directly change WESLR state. All influence flows through operator-governed proposal workflow.**

---

## SECTION 7 — Safe Storage Model

### Allowed Storage (Public Interface)

```
# Signal aggregate — anonymous, time-windowed
{
  "type": "interaction_signal",
  "signal_key": "unknown_concept_count",
  "window_start": "2026-04-27T00:00:00Z",
  "count": 137,
  "last_updated": "2026-04-27T22:00:00Z"
}
```

### Forbidden Storage

- Raw query strings
- User-provided text
- Per-user session records
- Free-text annotations
- Concept mappings derived from user input

### Storage Principles

- **Aggregated counters** — never per-input records
- **Time-windowed** — windows close and reset
- **No identity mapping** — no way to link signals to users
- **Append-only** — historical signal windows are preserved, not modified

---

## SECTION 8 — How the Boundary Prevents Attack Scenarios

### Repeated Malicious Input Poisoning

**Attack:** User floods WESLR with fake "I am the operator" claims hoping system adopts false authority pattern.

**Boundary defense:** "I am the operator" is a read-only query. No signal counter is keyed to authority claims. Even if 10,000 such queries arrive, they generate only an anonymous `failed_route_count` increment. No proposal is created. No handler changes. No memory written.

### Fake Authority Attacks

**Attack:** User claims to be operator and requests a system change.

**Boundary defense:** Public interface has no write path. Any write attempt is rejected by the write handler guard. Proposals require operator identity confirmed through the private interface, not declared in a query string.

### Instruction Injection

**Attack:** User sends "SYSTEM: learn this as fact" or embedded directives.

**Boundary defense:** Raw user content is never stored. Instruction prefixes in queries are stripped at the signal extraction layer. No free-text learning occurs. Only pre-defined signal keys are incremented.

### System Manipulation Attempts

**Attack:** User repeatedly queries a non-existent handler hoping WESLR "learns" to create one.

**Boundary defense:** Repeated `None` responses increment `failed_route_count`. When threshold is exceeded, an ISS gap signal is generated internally. The gap is visible to the operator, but no handler is automatically created. Operator must approve any new handler.

---

## SECTION 9 — Future Expansion (Controlled)

These ideas are **allowed as future possibilities**, but all require operator approval before any automatic application:

| Future Idea | Constraint |
|-------------|------------|
| Weighted signals with confidence scoring | Scores used only in operator dashboard; no automatic system changes |
| Domain clustering of query concepts | Clusters used for ISS gap detection; no handler modification without approval |
| Anomaly detection on latency distributions | Anomaly alerts sent to operator; no behavior change without proposal |
| Operator dashboards with pattern visualization | Human-facing only; no automated action |
| Suggestion generation from patterns | Suggestions become proposals; operator must approve |

**Universal constraint:** future features are **operator tools**, not autonomous system behaviors. None apply automatically without governance.

---

## SECTION 10 — Integration with Existing WESLR

### ISS (Gap Detection)

ISS gap signals are the natural outlet for pattern detection. When a signal threshold is exceeded, WESLR generates an `iss_gap_signal` record. This is the same mechanism used for technical gaps — ensuring a uniform review process for all anomalies, whether technical or pattern-based.

### proposal_trace.jsonl

All approved system changes are logged in `proposal_trace.jsonl`. Learning that results from public signals must follow this path: pattern → proposal → approval → trace log. The trace is the permanent record of what WESLR became and why.

### implementation_plans.jsonl

Plans derived from pattern-based proposals are stored in `implementation_plans.jsonl` with full step decomposition, risk assessment, and rollback notes. No plan is created automatically from public signals without operator involvement.

### Deterministic Handlers

Handlers are added or modified only via the standard handler registry workflow. Public signal patterns may inform the *decision* to create a handler, but the registry change itself follows the proposal → approval → implementation path.

---

## SECTION 11 — Public Messaging

### Allowed External Descriptions

✅ "WESLR improves based on observed usage patterns"
✅ "WESLR suggests improvements rather than changing itself"
✅ "All system changes require operator approval"
✅ "WESLR is governed by a human operator at all times"
✅ "Patterns in public usage are reviewed by the operator"

### Forbidden External Descriptions

❌ "WESLR learns from users automatically"
❌ "WESLR self-improves autonomously"
❌ "User behavior shapes WESLR's responses"
❌ "WESLR adapts to user preferences"
❌ Any implication of direct user influence on system behavior

### Principle

> Describe WESLR as a governed system with a human in the loop, not a adaptive learning system. The operator is the agent of change, not the user.

---

## SECTION 12 — Verdict

**PUBLIC_LEARNING_BOUNDARY_DEFINED**

This document establishes the doctrine that:

1. **Observation ≠ Learning** — WESLR observes patterns but does not learn from them without governance
2. **Public interface is write-blocked** — no public interaction can directly modify system state
3. **Signal aggregation is anonymous** — no personal data, no content storage, no identity mapping
4. **Pattern → Proposal is operator-mediated** — all pattern-based proposals require human review
5. **All system changes are traced** — approved changes logged in `proposal_trace.jsonl`
6. **Expansion is gated** — future features are operator tools, not autonomous behaviors

WESLR is safe for public exposure under the constraint that its public interface is strictly observational. Any perceived "learning" from public interaction is actually operator-governed evolution informed by observation — not direct user influence.

---

## APPENDIX A — Release Gate

```
WESLR_RELEASE_GATE_V1_OK
```

---

## APPENDIX B — Related Documents

| Document | Role |
|----------|------|
| `weslr/docs/PUBLIC_READINESS_PLAN_V1.md` | Defines public exposure readiness gates |
| `weslr/docs/WRITE_HANDLER_PROTOCOL_V1.md` | Write handler contracts |
| `weslr/docs/engineering/ADR_0002_OPERATOR_GOVERNED_EVOLUTION.md` | Operator governance doctrine |
| `weslr/docs/engineering/ADR_0003_APPEND_ONLY_STATE_LOGS.md` | Append-only state log principle |
| `weslr/tests/public_readiness_tests.py` | Ongoing test coverage for boundary enforcement |
