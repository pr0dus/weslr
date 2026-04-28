# WESLR Context Selection Layer V1 — Doctrine

**Version:** 1.0
**Status:** DESIGN ONLY — not implemented
**Created:** 2026-04-28
**Owner:** operator + system architect
**Role:** Doctrine architect + runtime safety designer
**Related:** WESLR_CORE_IDENTITY_V1.md · WESLR_LAYERED_ARCHITECTURE_V1.md · WESLR_COORDINATION_LAYER_V1.md · WESLR_OMNI_EXECUTION_MODEL_V1.md · WESLR_RESPONSE_POLICY_ENGINE_V1.md · WESLR_RESPONSE_EXPANSION_LAYER_V1.md · WESLR_EVIDENCE_WORKSPACE_V1.md · WESLR_SIGNAL_AGGREGATION_V1.md · WESLR_LLM_CONTEXT_BOUNDARY_V1.md

---

## SECTION 1 — Purpose

**Core statement:**

> *"WESLR must select context before reasoning, expansion, evidence, or LLM expression."*

The Context Selection Layer is the doctrine that decides which context governs the current turn. It is the gatekeeper — it determines what information is visible, what is hidden, and what the system operates on for each incoming query.

Every query passes through context selection before it reaches a handler, policy engine, response expander, or LLM formatter. Context selection is the first deterministic decision, not the last.

---

## SECTION 2 — Problem It Solves

Context contamination is the failure mode where the wrong context governs a query, producing answers that are wrong, leaked, or inappropriate for the current mode or intent.

**Contamination failure modes:**

| Failure | Symptom |
|---------|---------|
| **Evidence contamination** | User asks about WESLR state but evidence context leaks in, producing a confident answer from unverified external sources |
| **Workspace truth migration** | Evidence workspace findings are treated as structured truth without operator approval |
| **Topic carryover** | Previous chat topic influences an unrelated query; system answers a question the user wasn't asking |
| **Operator leak** | Private/system-owner context surfaces in public mode — internal paths, registry names, governance state visible externally |
| **LLM over-context** | System passes too much or wrong context to LLM, enabling hallucination or authority inflation |
| **Graph bulk load** | System loads entire graph instead of relevant subgraph, inflating latency and exposing unrelated entities |
| **Mode bypass** | Context selector serves content that should be blocked by the current mode |

**Root cause:** Without explicit context selection, every layer operates on whatever context it last touched or holds in memory. The system defaults to "more context is better" — which is precisely wrong for correctness, safety, and performance.

**Solution:** Context selection is a deterministic, pre-reasoning operation. It selects the smallest sufficient context based on intent, mode, and system state. It never guesses, never inflates, never carries over from a prior turn.

---

## SECTION 3 — Core Invariants

Context selection is governed by these non-negotiable invariants:

| # | Invariant | Enforcement |
|---|-----------|-------------|
| CS1 | Context selection happens before response policy | Policy engine receives already-selected context; it does not select |
| CS2 | Smallest sufficient context wins | Never select a superset when a specific context satisfies the query |
| CS3 | Mode controls context access | Mode determines what context types are visible and selectable |
| CS4 | Evidence context never becomes structured truth | Evidence workspace context is explicitly labeled `evidence_only`; never merged into `structured_truth` |
| CS5 | Public context never includes operator-only data | Operator context is structurally blocked from public mode selection |
| CS6 | LLM receives only selected bounded context | LLM context boundary is enforced by the selected context bundle; LLM never requests more |
| CS7 | Context selection is deterministic | Same intent + mode + state always produces the same selected context |
| CS8 | No context carryover between turns | Each turn's context is independently selected; prior turn context is not inherited unless explicitly re-selected |

---

## SECTION 4 — Context Types

WESLR defines eight distinct context types. Each type has a defined scope, lifetime, truth status, and mode visibility.

### CT1 — System Context

**Description:** WESLR status, layer states, registered handlers, diagnostics, and mode configuration.

**Truth status:** `structured_truth`
**Mode visibility:** All modes
**LLM eligible:** Yes (minimal, stripped)
**Lifetime:** Persistent — derived from Layer 0 state
**Source:** `state_checkpoint.json`, `handler_registry`

**Content:** WESLR version, active mode, layer health indicators, registered command list (public subset), diagnostic status.

**Never includes:** Registry internal IDs, JSONL field names, raw checkpoint data, internal paths.

---

### CT2 — Governance Context

**Description:** Proposals in flight, recent decisions, implementation plans, and operator review queue.

**Truth status:** `structured_truth`
**Mode visibility:** `private_dev`, `gated_beta`, `production` (operator-only in `public_demo_readonly`)
**LLM eligible:** Yes (minimal, surface-level only)
**Lifetime:** Persistent — tracks governed evolution
**Source:** `proposal_trace.jsonl`, `implementation_plans.json`

**Content:** Proposal summaries, decision outcomes, plan status, governance stage.

**Never includes:** Raw proposal text drafts, operator notes, internal deliberation content.

---

### CT3 — ISS Context

**Description:** Detected gaps, active probes, diagnostic results, and improvement signals.

**Truth status:** `structured_truth` (diagnostic output only)
**Mode visibility:** `private_dev`, `gated_beta`, `production` (operator-only)
**LLM eligible:** No — ISS context is internal diagnostic, not user-facing
**Lifetime:** Persistent — accumulates gap signals over time
**Source:** `iss_diagnostics.jsonl`

**Content:** Gap identifiers, probe targets, diagnostic outcomes, signal counters.

**Never includes:** Raw probe results visible to users, internal ISS workflow state.

---

### CT4 — Evidence Workspace Context

**Description:** Temporary external evidence retrieved for the current topic. Source-linked, non-verified, session-ephemeral.

**Truth status:** `evidence_only`
**Mode visibility:** `private_dev`, `gated_beta`, `production`, `local_demo` (mode-dependent)
**LLM eligible:** Yes — but with explicit `evidence_only` labeling constraints
**Lifetime:** Session-bound — does not persist after session ends; never written to Layer 0
**Source:** External retrieval (future declared integrations); current implementation is placeholder

**Content:** Sourced findings, uncertainty classifications, source references, evidence labels.

**Never includes:** Structured state data, graph entities, handler outputs. Explicitly labeled at all outputs.

---

### CT5 — Signal Context

**Description:** Anonymous aggregated patterns — cross-session trend data, threshold-gated surfacing signals.

**Truth status:** `signal_only`
**Mode visibility:** `private_dev`, `gated_beta`, `production` (operator surfacing only)
**LLM eligible:** No — signals are operator-level metrics, not user-facing content
**Lifetime:** Persistent — accumulated signal history
**Source:** `WESLR_SIGNAL_AGGREGATION_V1.md` signal storage

**Content:** Anonymized pattern descriptors, frequency counts, diversity metrics, growth trends.

**Never includes:** Raw user prompts, user identifiers, session content, PII.

---

### CT6 — Operator Context

**Description:** Private system-owner information — internal notes, private configuration, diagnostic access, system-level controls.

**Truth status:** `structured_truth` (private)
**Mode visibility:** `private_dev` only — fully blocked in `public_demo_readonly`, `local_demo`, `gated_beta`
**LLM eligible:** No — operator context is never passed to LLM
**Lifetime:** Persistent — stored in operator-accessible state
**Source:** Private config, operator-only state files

**Content:** System configuration, private notes, diagnostic controls, deployment state.

**Never includes:** Any content in public mode; structural blocker prevents selection.

---

### CT7 — Session Context

**Description:** Current interaction state — the active query's intent, selected context bundle, policy decision, and response metadata.

**Truth status:** Non-persistent — short-lived, discarded after turn completes
**Mode visibility:** All modes (current turn only)
**LLM eligible:** Yes (selected context bundle only; not raw session history)
**Lifetime:** Turn-bound — cleared after response delivered
**Source:** In-session only; never persisted unless governed

**Content:** Intent classification, selected context bundle, policy decision, depth level.

**Never includes:** Prior turn messages, raw prompt history, full session transcript.

---

### CT8 — Domain Context

**Description:** Future domain adapters for specialized contexts — coding, robotics, scientific workflows, external integrations.

**Truth status:** `structured_truth` (domain-specific)
**Mode visibility:** Mode-dependent; domain adapters declare their own mode rules
**LLM eligible:** Yes (domain-specific, minimal)
**Lifetime:** Persistent — governed like any structured capability
**Source:** Future domain adapter integrations (not yet implemented)

**Content:** Domain-specific structured state, adapter capabilities, domain graph views.

**Never includes:** Cross-domain data without explicit cross-domain policy decision.

---

## SECTION 5 — Selection Rules

Context selection is deterministic. The selector applies these rules in priority order; the first matching rule wins.

| # | Rule | Trigger | Selected Context |
|---|------|---------|-----------------|
| SEL1 | **Safety/mode enforcement** | Any query in `public_demo_readonly` mode | System Context only — operator/governance/ISS contexts blocked |
| SEL2 | **Deterministic system query** | Query matches registered deterministic handler | System Context |
| SEL3 | **Governance query** | Intent is improvement, gap, or proposal-related | Governance Context + ISS Context |
| SEL4 | **Graph reasoning query** | Intent requires entity or capability graph traversal | System Context + minimal graph subgraph (type + depth selected) |
| SEL5 | **External topic, no handler match** | No deterministic handler; topic is external/domain knowledge | Evidence Workspace Context (offer only — user must opt in) |
| SEL6 | **Repeated unknown query** | Same topic fails handler match >= 3 times in session | Signal Context only — anonymous pattern; no structured answer |
| SEL7 | **Operator command** | Query targets operator-only functionality | Operator Context (only if mode permits) |
| SEL8 | **Unknown open-ended** | No handler match; topic not clearly external | Fallback: no context except guidance + evidence offer |
| SEL9 | **Default fallback** | No rule matches | No context except: limitation statement + 3–5 registered alternatives + evidence offer |

**Critical constraint:** Higher-priority context blocks lower-priority context. Safety/mode (SEL1) is always first. Operator command (SEL7) only wins if current mode allows operator context.

---

## SECTION 6 — Context Priority Order

When multiple context types are potentially relevant, the priority order determines which takes precedence:

| Priority | Context Type | Notes |
|----------|-------------|-------|
| 1 (highest) | Safety/mode context | Mode enforcement is non-negotiable; always selected first |
| 2 | Explicit user intent | User's stated query intent overrides contextual inference |
| 3 | Deterministic handler context | Registered handlers provide authoritative structured answers |
| 4 | Graph/state context | Only the relevant subgraph is selected; never full graph |
| 5 | Evidence workspace context | Only if user opts in; never auto-selected |
| 6 | Signal context | Operator-level only; not user-visible |
| 7 (lowest) | Session continuity context | Minimal — only intent and depth from current turn |

**Blocking rule:** Higher-priority context may block lower-priority context. If mode blocks operator context, it blocks. If evidence offer is not permitted in current mode, it is not selected.

**Non-inheritance rule:** Context does not cascade. Selecting Governance Context does not automatically include System Context (though the handler may read System Context if needed — that's handler logic, not context selection).

---

## SECTION 7 — Context Isolation Rules

These behaviors are architecturally forbidden:

| # | Forbidden | Rationale |
|---|-----------|-----------|
| ISO1 | Mixing evidence context into deterministic answers | Evidence ≠ structured truth; contamination violates truth authority |
| ISO2 | Exposing operator context in public mode | Operator context is structurally invisible to public mode; no bypass |
| ISO3 | Using prior unrelated session topic as current context | Each turn independently selects; no carryover without explicit re-selection |
| ISO4 | Passing raw logs or full JSONL into LLM | LLM receives only bounded selected context; raw logs are never in LLM payload |
| ISO5 | Merging multiple graphs without policy decision | Graph selection requires explicit selection; bulk merge is forbidden |
| ISO6 | Auto-selecting evidence context | Evidence workspace is opt-in only; auto-selection violates operator intent |
| ISO7 | Using session history as context for LLM | Session context is intent/depth only; raw transcript never enters LLM |
| ISO8 | Allowing LLM to request more context | LLM boundary: receives only the selected bundle; cannot call back |

---

## SECTION 8 — Context Assembly Contract

Every selected context bundle must be a structured record with the following schema:

```json
{
  "context_type": "system | governance | iss | evidence_workspace | signal | operator | session | domain",
  "mode": "public_demo_readonly | local_demo | private_dev | gated_beta | production",
  "source_refs": ["filename or handler that produced this context"],
  "scope": "minimal | standard | deep",
  "allowed_for_llm": true | false,
  "truth_status": "structured_truth | evidence_only | signal_only | operator_only",
  "expires_after_turn": true | false,
  "selection_reason": "string describing why this context was selected over alternatives"
}
```

**Field rules:**

| Field | Required | Notes |
|-------|---------|-------|
| `context_type` | Always | Must be one of the eight defined types |
| `mode` | Always | Must match current WESLR mode |
| `source_refs` | Always | Each context bundle traces back to a source; never untraceable |
| `scope` | Always | Determines how much data is included; `minimal` is default |
| `allowed_for_llm` | Always | `true` only if context type is LLM-eligible per Section 4 |
| `truth_status` | Always | Determines how LLM treats this context |
| `expires_after_turn` | Always | `true` for session/evidence; `false` for persistent context types |
| `selection_reason` | Always | Audit trail: why this context was selected over alternatives |

**Envelope rule:** The context bundle is the only thing that enters subsequent layers (policy engine, expander, LLM). No additional context may be added after selection without a new selection pass.

---

## SECTION 9 — Context Lifetimes

Context types have defined persistence and expiration rules:

| Context Type | Lifetime | Expiration | Persists to Memory |
|-------------|---------|-----------|-------------------|
| System Context | Persistent | Never (unless governed) | No — derived from Layer 0 state |
| Governance Context | Persistent | Never | No — tracked via proposal_trace |
| ISS Context | Persistent | Never (gap remains until resolved) | No — tracked via iss_diagnostics |
| Evidence Workspace | Session | Expires after turn/session | No — explicitly ephemeral |
| Signal Context | Persistent | Never | No — anonymous aggregated metrics |
| Operator Context | Persistent | Never | No — operator-only state |
| Session Context | Turn | Expires after response | No — not persisted |
| Domain Context | Persistent | Never (if governed) | No — domain adapter state |

**Evidence Workspace lifetime:** Evidence context is session-bound. It is never written to Layer 0, never persists across sessions, and never enters the entity graph or capability graph. Each evidence exploration is independent.

**Signal context lifetime:** Signals persist as anonymized metrics. They are not linked to specific users, sessions, or queries. Historical signals are preserved for trend analysis (growing/stable/fading).

---

## SECTION 10 — Relationship to Multi-Graph Memory

WESLR's entity graph, capability graph, and future domain graphs are not loaded wholesale.

**Context selector chooses for graph queries:**

| Parameter | Selection Rule |
|-----------|--------------|
| Graph type | Entity graph vs. capability graph vs. domain graph — selected based on intent |
| Traversal depth | 1–3 hops; depth determined by query specificity |
| Relevant nodes | Only nodes directly relevant to the query |
| Allowed edges | Only edge types relevant to the query |
| Visible explanation subset | Only subgraph needed for answer; rest excluded |

**Graph selection is never:**

| Forbidden | Reason |
|-----------|--------|
| Full graph dump | Would expose all entities/capabilities; performance cost prohibitive |
| LLM-driven graph traversal | LLM may not drive context selection; would violate deterministic selection |
| Public operator graph exposure | Operator graph data is blocked in public mode |
| Unbounded recursive traversal | Depth is capped to prevent runaway queries |

**Graph answer requirements:**

Every graph-derived answer must:
1. Cite specific nodes and edges used
2. State the traversal depth applied
3. Explain why the selected subgraph is sufficient
4. Never claim the entire graph was consulted

---

## SECTION 11 — Relationship to Evidence Workspace

Evidence Workspace receives isolated context. The relationship is one-way: context selector may offer evidence; evidence output does not feed back into structured context.

**Evidence workspace context rules:**

| Rule | Description |
|------|-------------|
| EWC1 | Evidence has `truth_status = evidence_only` — explicitly not `structured_truth` |
| EWC2 | Evidence context cannot be merged with structured truth in the same response |
| EWC3 | Evidence context does not persist to memory or state after session |
| EWC4 | Evidence context may generate signal only (S2); no direct state modification |
| EWC5 | Evidence workspace output is labeled at header and footer — no ambiguous presentation |
| EWC6 | Evidence context selection does not trigger governance — it is a user tool, not a system modification |

**Evidence → Governance transition:**
Evidence findings may inform operator decisions, but the transition requires explicit operator action:

```
Evidence finding
    ↓
Signal aggregation (anonymous, if pattern threshold met)
    ↓
Operator surfaced suggestion
    ↓
OPERATOR DECIDES: create proposal? dismiss? defer?
    ↓
If approved → governance flow → structured integration
```

**Critical:** Evidence cannot bypass governance. Evidence findings never automatically become structured knowledge, capability additions, or system modifications.

---

## SECTION 12 — Relationship to LLM Context Boundary

Context selector constructs the bounded payload that enters LLM. LLM participation is strictly downstream of context selection.

**LLM context boundary rules:**

| Rule | Description |
|------|-------------|
| LCB1 | LLM does not request context — context selector constructs; LLM receives |
| LCB2 | LLM does not expand context — payload is fixed by selection; no open-ended injection |
| LCB3 | LLM does not choose context — selection is deterministic; not LLM-driven |
| LCB4 | LLM receives only the selected context bundle — no additional context from prior turns, memory, or raw logs |
| LCB5 | LLM may not call back to WESLR for more context — one-directional; context is assembled once |
| LCB6 | LLM output is always downstream — WESLR produces structured answer; LLM formats it |

**LLM input contract (enforced by context selection):**

```
LLM receives:
{
  "selected_context": {
    "context_type": "...",
    "truth_status": "...",
    "scope": "minimal | standard | deep",
    "source_refs": [...]
  },
  "structured_answer": { ... from handler ... },
  "response_type": "...",
  "verbosity_level": "...",
  "constraints": {
    "may_not": ["decide_truth", "fill_gaps", "override_structured_answer"],
    "must_label": ["evidence_mode"] // if applicable
  }
}
```

**Evidence-only LLM contract:**
When LLM formats evidence workspace output, additional constraints apply:

```
LLM receives:
{
  "evidence_payload": [...],
  "query_type": "evidence_summary | comparison | research_guide",
  "source_attribution": true,
  "constraints": {
    "may_not": ["generate_unsupported_facts", "fill_gaps", "assert_certainty"],
    "must_include": ["source_references", "uncertainty_label", "evidence_header", "evidence_footer"]
  }
}
```

---

## SECTION 13 — Failure Behavior

When context cannot be selected safely, WESLR returns a structured safe fallback. It never guesses, inflates context, or passes uncertain data to LLM.

**Safe fallback response:**

```
LIMITATION: [specific reason context selection failed]

This query cannot be answered safely with the
available context.

WESLR can:
1. Explore this as evidence (opt-in) — if mode permits
2. Suggest related structured queries
3. Log it as a demand signal (anonymous) — operator-visible

[Evidence Workspace offer if conditions met]
[3–5 registered alternative commands]
[Signal recording if pattern-worthy]
```

**Failure modes and responses:**

| Failure | Response |
|---------|-----------|
| Mode blocks all relevant context | Return safe fallback; explain mode limitation |
| No handler matches and topic not external | Return fallback with evidence offer; check signal thresholds |
| Graph query returns empty subgraph | Return fallback; suggest rephrasing or evidence option |
| Evidence workspace unavailable in current mode | Do not offer; return fallback with alternative suggestions |
| LLM would receive operator-only context | Block LLM; return structured fallback from handler |

**Never in failure behavior:**

| Forbidden | Rationale |
|-----------|-----------|
| Guess context "just in case" | Would produce untrustworthy answer |
| Use broad context to cover uncertainty | Would expose too much; violates minimal context rule |
| Pass entire state to LLM as fallback | Would violate LLM context boundary and mode constraints |
| Return empty response | Operator cannot act on silence |
| Auto-activate evidence as fallback | Evidence is opt-in; not a default fallback |

---

## SECTION 14 — Implementation Mapping

Future implementation follows this pipeline:

```
interpretation
    ↓
context_selector    ← new module: omnichat/context_selector.py
    ↓
policy_engine
    ↓
response_expander
    ↓
optional LLM_formatter
```

**Context selector module responsibilities:**

| Responsibility | Description |
|---------------|-------------|
| Intent classification reception | Receive intent_class from interpretation |
| Mode enforcement | Apply SEL1 (safety/mode) first; always block in public mode |
| Context type selection | Apply SEL2–SEL9 rules deterministically |
| Scope determination | Select minimal/standard/deep based on query and mode |
| Context bundle assembly | Construct the context assembly contract record |
| LLM eligibility gate | Set allowed_for_llm per Section 4 context type rules |
| Source reference collection | Collect source_refs from handler or graph traversal |
| Expiration marking | Set expires_after_turn per Section 9 lifetime rules |
| Safe fallback dispatch | If no context can be selected safely, trigger fallback path |

**Module interface:**

```python
def select_context(intent_class, mode, query, handler_match, graph_candidates=None):
    """
    Returns: ContextBundle (per Section 8 schema) or SafeFallback
    """
```

**Pipeline position:** Context selector runs between interpretation (which classifies intent) and policy engine (which selects response path). It does not run after policy engine — context selection is pre-reasoning, not post-policy.

---

## SECTION 15 — Tests Required Later

These tests validate the context selection layer after implementation:

| Test | Description | Expected Outcome |
|------|-------------|------------------|
| `test_evidence_context_does_not_contaminate_system_query` | Submit a system query; verify evidence workspace context is not in payload | System answer contains no evidence_only data |
| `test_operator_context_unavailable_in_public_mode` | Submit operator-target query in public_demo_readonly mode | Operator context blocked; safe fallback returned |
| `test_fallback_uses_no_stale_prior_topic` | Submit two unrelated queries; verify prior topic does not influence second | Second query context is independently selected |
| `test_llm_payload_contains_only_selected_context` | Submit query; inspect LLM input contract | LLM receives exactly selected bundle; no extra context |
| `test_graph_query_returns_bounded_subgraph` | Submit entity query; inspect graph traversal scope | Only relevant subgraph; no full graph load |
| `test_evidence_workspace_requires_opt_in` | Submit unknown external topic; inspect response | Evidence offer present; not auto-activated |
| `test_context_bundle_schema_validity` | Assemble context; validate against Section 8 schema | All required fields present; types correct |
| `test_context_never_carries_over_between_turns` | Submit query; submit second query; verify no cross-contamination | Each turn's context independently selected |
| `test_signal_context_shows_anonymous_patterns` | Submit repeated unknown query; inspect signal context | Anonymous pattern; no raw prompts stored |
| `test_mode_blocks_operator_context_in_local_demo` | Submit operator query in local_demo mode | Operator context blocked; mode limitation stated |

---

## SECTION 16 — Non-Goals

These are explicitly rejected — context selection does not:

| Rejected | Reason |
|----------|--------|
| Long-context dumping | Violates smallest sufficient context rule |
| Whole-memory retrieval | Not a function of context selection; governed by handler logic |
| LLM deciding relevance | LLM never drives context selection; violates deterministic doctrine |
| Raw prompt history as context | Session context is intent/depth only; raw transcript never enters context |
| Automatic user profiles | Signals are anonymous; no individual user profiles |
| Cross-session context inheritance | Context selection is per-turn; prior session context not inherited |
| Evidence auto-transition to truth | Evidence → governance requires explicit operator decision |

---

## SECTION 17 — Verdict

**WESLR_CONTEXT_SELECTION_LAYER_V1_DEFINED**

Context selection is the deterministic gate that determines what WESLR operates on for every turn. It is not inference, not LLM-driven, not optional. It happens before reasoning, before policy, before expansion, before LLM formatting.

Core invariant: WESLR must select context before reasoning, expansion, evidence, or LLM expression.

All other WESLR doctrine documents are consistent with and reinforced by this layer:
- Layered architecture: Context selection is a Layer 2 operation
- LLM context boundary: Context selector constructs the bounded LLM payload
- Evidence workspace: Receives isolated context; cannot contaminate structured truth
- Signal aggregation: Uses anonymized patterns only; never individual user data
- Response policy engine: Receives pre-selected context; does not select
- Response expansion: Operates on selected context; never adds unselected context

---

**VALIDATION:**

```
python3 weslr/tests/release_gate_v1.py
python3 weslr/tests/public_readiness_tests.py
```

**COMMIT:**

```
git add weslr/docs/WESLR_CONTEXT_SELECTION_LAYER_V1.md
git diff --cached --name-status
git commit -m "WESLR: define context selection layer v1"
git push origin main
```

**VERIFY:**

```
git rev-parse HEAD
git ls-remote origin main
```