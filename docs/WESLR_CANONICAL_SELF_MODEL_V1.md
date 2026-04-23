# WESLR_CANONICAL_SELF_MODEL_V1.md — WESLR Canonical Self-Model

**Status:** CANONICAL — architecture and doctrine document
**Date:** 2026-04-21
**Supersedes:** None (new canonical document)
**Authoritative for:** All future OC Coder sessions, architecture work, self-evaluation system integration

---

> **For future OC Coder sessions:** Read this file first. Then read the relevant canon docs listed in Section 12. Then confirm your branch, allowed scope, forbidden scope, and exact next task before touching any files.

---

## SECTION 1 — FILES CHANGED

| File | Change |
|------|--------|
| `docs/WESLR_CANONICAL_SELF_MODEL_V1.md` | **Created** — this document |

No production code files modified. No schema changes. No behavior changes.

---

## SECTION 2 — COMMANDS RUN

None. This document is documentation-only.

---

## SECTION 3 — DOCUMENT SUMMARY

This document is the authoritative self-model reference for WESLR. It defines what WESLR is, what WESLR is not, the core governing doctrine, the canonical architecture spine (as it actually exists today), the classification of all major lanes, the real role of artifacts, the status of all feature layers (interest/relevance/suggestion/thread), the self-improvement ecosystem, the governance model, the live query surface, environment expectations, sealed canons, known gaps, forbidden drift, and the safe restart ritual for future coder sessions.

This is a repo-truth document. Every classification, every status, and every gap description is grounded in actual code inspection. This is not a marketing document and not a dashboard export.

---

## SECTION 4 — WHAT WESLR IS

WESLR is a **continuity-first governed reasoning system** — an entity intelligence platform that builds structured intelligence over time, with explicit memory, explicit threads, explicit governance, and explicit identity.

Specifically:

- **Continuity-first:** WESLR is designed around persistent memory across sessions. Identity, context, and learning are externalized into explicit records rather than held in a single context window. Temporal continuity is the primary design constraint.
- **Governed reasoning system:** WESLR reasons about its own state, detects inadequacies, synthesizes patterns, and generates proposals — but all consequential actions require operator approval. WESLR observes autonomously. It executes only with permission.
- **Structured intelligence over time:** WESLR does not simply respond to prompts. It maintains an entity graph, a memory system, a thread tracker, an interest registry, and multiple self-evaluation loops that accumulate evidence of WESLR's own quality and bottlenecks.
- **Model-assisted, not model-dependent:** WESLR uses an LLM as a provider, not as its mind. The reasoning structure, the governance rules, the memory systems, and the evaluation loops all exist independently of any single model call. Provider changes are meant to be swappable via `weslr/providers.py`.
- **Research-paper style communication:** WESLR produces structured, human-readable explanations of its own reasoning, weaknesses, and proposals. Deep proposals are communicated as research-paper style documents that operators and other stakeholders can inspect, not as opaque model outputs.

WESLR is **not** a chatbot. It does not treat every response as a standalone turn. It maintains continuity state, tracks threads, evaluates its own adequacy, and surfaces its own weaknesses.

---

## SECTION 5 — WHAT WESLR IS NOT

WESLR is explicitly not each of the following:

- **Not a pure LLM wrapper:** WESLR has structured state, memory systems, governance loops, and self-evaluation infrastructure that exist independently of the LLM provider. The LLM is a component, not the system.
- **Not a hidden self-modifier:** WESLR does not silently modify its own code, configuration, memory, or behavior. All changes go through governed proposal → operator approval → execution → audit. No autonomous patching.
- **Not a black-box reasoning engine:** WESLR produces explainable outputs. Every proposal, every adequacy finding, every synthesis output includes evidence, reasoning traces, and human-readable explanations. Nothing is opaque.
- **Not a single-loop system:** WESLR has multiple parallel self-evaluation and improvement lanes (at least seven, see Section 6). They are not unified into a single loop. They coexist, and their outputs are not yet consolidated into a canonical view.
- **Not a system that depends on maximum context as its mind:** WESLR's memory, identity, and reasoning are externalized into explicit records. The goal is that maximum context becomes increasingly unnecessary for core WESLR functions. Interest tracking, thread continuity, and entity memory are all designed to reduce context dependence.

---

## SECTION 6 — CORE DOCTRINE

The following governing laws are established across WESLR's canonical documents and are binding:

### Continuity Doctrine
**Timeline-first.** The human is a timeline. The role is a timeline. The institution is a timeline. Every persistent identity is a timeline — not a session, not a context window. WESLR wakes fresh each session and reads memory files. That is the correct behavior, not a failure.

### Additive, Reversible Changes Only
All WESLR improvements are additive. No production logic is deleted without operator approval and a rollback path. No self-modification is silent. Changes are governed, reversible, and auditable.

### No Silent Behavior Changes
WESLR does not silently change how it scores, routes, surfaces, or decides. Every behavioral change goes through a proposal → approval → execution path. No hidden routing authority from relevance, suggestions, or thread membership.

### No Hidden Self-Modification
WESLR may propose changes to itself. It may not execute them without operator approval. The execution gate is the boundary.

### Advisory Autonomy, Governed Consequence
WESLR observes autonomously. WESLR suggests autonomously. WESLR executes only with operator approval. This is the core boundary: observation and suggestion are free; execution requires the governance surface.

### Advisory-Only Invariant for Metadata Systems
Interest relevance, thread membership, and suggestion surfacing are **advisory metadata only**. They do not influence routing, wording, ranking, scoring, or decisions. They are information for the operator, not signals for WESLR's reasoning engine.

### Maximum Context Becoming Increasingly Obsolete
The goal of WESLR's memory, interest, and thread systems is that maximum context becomes a fallback, not the primary mechanism. Each system externalizes what would otherwise require context carrying.

### Normal Interaction Channels Are Preferred
Suggestions and relevance observations surface through normal text/voice interaction, not through dashboards. Dashboards are for inspection; interaction channels are for discovery. WESLR should not require a dashboard to participate in its own governance.

### Research-Paper Explanation as Core Communication Mode
For deep proposals, capability evaluations, and self-improvement recommendations, WESLR produces research-paper style structured explanations. These are operator-readable documents, not model output dumps. The format itself is part of the governance contract.

---

## SECTION 7 — CANONICAL ARCHITECTURE SPINE

**Current reality:** WESLR currently has **multiple parallel self-evaluation and improvement systems without a fully unified canonical core**. This is not a design flaw discovered late — it is the accurate current state after multiple chapter completions, each of which was substantively correct within its chapter scope.

**The seven identified lanes:**

| Lane | Name | Trigger | Status |
|------|------|---------|--------|
| A | Inadequacy/CDI Proposal Lane | Runtime failure events | Most complete — full event-to-proposal-to-ExecutionGate path |
| B | Adequacy Hook Lane | Proposal evaluation pass | Complete within itself — not auto-connected to proposal lane |
| C | Self-Directed Growth Loop | Manual (`self grow` CLI) | Complete loop — dead-ends at approval (proposals never reach ExecutionGate) |
| D | Improvement Engine Lane | Manual / periodic | Complete signal aggregation — no formal review/execution path |
| E | Drift Reflection Loop | Continuous (in-process, 48h rolling window) | Complete detection — not connected to proposals |
| F | Self-Architecture A/B Lane | Capability suggestions | Complete comparison engine — not connected to ExecutionGate |
| G | Unifying Self-Model Query | `get_self_summary()` | Read-only composed surface — no write path |

**Canonical spine recommendation:** Lane A (Inadequacy/CDI Proposal Lane) is the strongest candidate for canonical spine status. It has the most complete governance path (event → trigger → handoff → synthesis → proposal → CDI bundle → operator review → ExecutionGate → execution → audit). Its primary gap is that `build_cdi_bundle()` is not auto-triggered from the adequacy pipeline — the auto-path ends at proposal export.

**What "canonical spine" means in this context:** Not that other lanes are deleted, but that Lane A becomes the integration target — where feeds from other lanes are normalized, deduplicated, and routed through the ExecutionGate. Other lanes remain valid but become feeders to the canonical spine rather than independent parallel paths.

**This classification may change as the integration architecture matures.**

---

## SECTION 8 — EXISTING MAJOR LANES AND CLASSIFICATION

### PRIMARY (most complete, governed, production-ready)

**Inadequacy/CDI Proposal Lane (Lane A)**
- Classification: PRIMARY
- Entry: `inadequacy_persistence.record_inadequacy_event()` (runtime failures)
- Flow: event → trigger → handoff → intake → deterministic synthesis → insight proposal payload → CDI bundle → ExecutionGate review → execution
- Files: `inadequacy_persistence.py`, `inadequacy_trigger.py`, `inadequacy_handoff.py`, `inadequacy_intake.py`, `deterministic_synthesis.py`, `insight_proposal_layer.py`, `cognitive_dialogue_integration.py`, `change_proposals.py`
- Governance: Full — ExecutionGate with state transitions, audit trail
- Gap: CDI bundle not auto-triggered; ends at proposal export

**Adequacy Evaluation**
- Classification: PRIMARY (within its scope)
- Entry: `cognitive_adequacy.evaluate()` (threshold-based proposal evaluation)
- Flow: proposal sequence → threshold check (repetition, low confidence, same fix loop, no improvement, evidence-to-action failure) → adequate/inadequate finding
- Files: `cognitive_adequacy.py`, `cognitive_adequacy_hook.py`
- Governance: Findings inform proposal emission; no autonomous execution
- Gap: Not auto-connected to proposal review lane

**Deterministic Synthesis Engine**
- Classification: PRIMARY (analysis tool)
- Entry: `DeterministicSynthesisEngine.synthesize_all()` (reads from existing records only)
- Flow: pattern grouping → approval reason grouping → proposal outcome grouping → confidence trends → bottleneck recurrence
- Files: `deterministic_synthesis.py`, `deterministic_synthesis_formatter.py`
- Governance: Read-only analysis, no mutation, no recommendations
- Status: Clean separation of analysis vs action

**Drift Reflection Loop**
- Classification: PRIMARY (continuous monitoring)
- Entry: `record_drift_signal()` (in-process, 9 concern types)
- Flow: drift signal → 48h rolling window → concern evaluators → pending reflections → operator acknowledgment
- Files: `institution.py` (drift signal store + concern evaluators + Reflection class)
- Governance: Reflections surfaced to operator for acknowledgment or dismissal
- Gap: Not connected to proposals; surfaced concerns not actioned

**Change Proposals / ExecutionGate**
- Classification: PRIMARY (governance infrastructure)
- Entry: `ExecutionGate.create_proposal()`, `transition_state()`, `execute_proposal_if_approved()`
- Flow: proposal → pending → approved/denied → execute (if approved) → audit trail
- Files: `change_proposals.py`
- Governance: Full — state transitions with actor + details, reversible
- Status: The most formally governed execution path

### FEEDER (produces signals/input for primary lanes)

**Adequacy Hook Lane (Lane B)**
- Classification: FEEDER to Lane A
- Produces adequacy findings that inform whether CDI proposals should be generated
- Not auto-connected; manual trigger required to convert finding to proposal

**Self-Directed Growth Loop (Lane C)**
- Classification: FEEDER to Lane A (intended)
- Produces self-evaluation + proposals from identity/affect state
- Currently dead-ends at approval step — proposals logged but never routed to ExecutionGate
- Gap: No integration path to Lane A's governance system

**Improvement Engine Lane (Lane D)**
- Classification: FEEDER to Lane A (intended)
- Produces ranked improvement recommendations from multi-source signals
- No formal review/reverse/execute path; outputs to `recommendations.json` for manual operator review
- Gap: No ExecutionGate integration

**Self-Architecture A/B Lane (Lane F)**
- Classification: FEEDER to Lane A (intended)
- Produces `ChangeProposal` objects from capability suggestions via `ProposalEvaluator` and `TradeoffEngine`
- Not connected to ExecutionGate; operates as parallel comparison system
- Gap: No unified execution path

### VALIDATOR

**Cognitive Reflection**
- Classification: VALIDATOR
- Entry: `run_reflection()` (proposal-only consistency pass)
- Flow: proposal + evidence → consistency check → notes/flags attached to adequacy finding
- Files: `cognitive_reflection.py`
- Governance: Bounded reflection for proposal quality; no writes

### ANALYSIS TOOL

**Operator Insight Systems**
- Classification: ANALYSIS TOOL
- Entry: `OperatorInsightComparison`, `OperatorInsightTimeline`, `OperatorInsightHistory`
- Flow: operator insight drift analysis, timeline building, recovery insight tracking
- Files: `operator_insight_comparison.py`, `operator_insight_timeline.py`, `operator_insight_history.py`, `operator_recovery_insight.py`, `operator_insight_consolidation.py`
- Governance: Read-only analysis; no proposal/execution path
- Status: Useful but operates independently of proposal lane

**Unifying Self-Model Query (Lane G)**
- Classification: ANALYSIS TOOL / READ SURFACE
- Entry: `get_self_summary()` (composed 6-layer summary)
- Flow: reads from identity, trust, health, continuity, institutional, active_concerns sources
- Files: `institution.py`
- Governance: Read-only; no write path
- Status: The canonical read surface for WESLR's composed self-model

### PARALLEL (competing / overlapping — creates fragmentation risk)

**Three parallel proposal systems without shared schema:**
1. `InsightProposalPayload` (Lane A output) — JSON with proposal_id, title, type, pattern_summaries, etc.
2. `ChangeProposal` from `change_proposals.py` — full lifecycle with state machine + ExecutionGate
3. `improvement_engine` plain dict proposals — to `recommendations.json`
4. `self_eval` plain dict proposals — from `self_apply_changes()`

Risk: Same underlying issue can generate proposals in multiple systems with no deduplication.

**Two reflection systems:**
1. `institution.Reflection` (in-process, 9 concern types, 48h window)
2. `self_eval.run_self_evaluation()` (on-demand, identity/affect-based gaps)

Risk: Operator cannot see one consolidated concern view.

**Three explanation/report text formats:**
1. `InsightProposalExporter.format_proposal()` — 60-char ASCII border
2. `DeterministicSynthesisFormatter` (6 formatters) — plain text sections
3. `run_self_evaluation()` summary — structured dict with text

### LEGACY / EXPERIMENTAL

**`adequacy_lineage_view.build_proposal_view()`**
- Minimal dict composer with optional lineage/adequacy refs
- Not a full view layer

**`operator_insight_consolidation.py` RecoveryGuidanceSummary**
- Built for specific recovery guidance use case
- Not integrated with main proposal flow

---

## SECTION 9 — ARTIFACT SYSTEM ROLE

The artifact system in WESLR is substantially broader than memo generation. Artifacts serve at least five distinct roles:

### Role 1 — Reasoning Units
An artifact is the primary structured output of WESLR's research and reasoning capability. The canonical artifact schema (`_generate_research_memo` in `main.py`) includes: `hypothesis`, `confidence`, `limitations`, `alternative_interpretations`, `next_experiment`. This is not a memo — it is a structured reasoning record that captures what WESLR concluded, how confident it is, what it considered and rejected, and what should come next.

### Role 2 — Research-Paper Style Explanation
Artifacts are the primary mechanism for producing research-paper style human-readable explanations of WESLR's reasoning. When WESLR evaluates itself or proposes improvements, the output format is designed to be inspectable by operators and other stakeholders — not opaque model output.

### Role 3 — Evaluation Outputs
When WESLR surfaces evaluation findings (e.g., in `build_artifact_explainability()` in `sim.py`, or in `InsightProposalExporter`), the output is a structured evaluation record — not a plain text paragraph. It includes: `internal_strength`, `external_proof`, `risks`, `next_actions`. This is evaluative output, not descriptive commentary.

### Role 4 — Operator-Facing Communication
Artifacts flow into the satellite UI via `build_artifact_detail_views()` → `render_dashboard()` → `dashboard.json`. Artifacts are how WESLR communicates its capability output to the operator in a structured, scannable form.

### Role 5 — Comparison/Evaluation Potential
The artifact system is the intended basis for A/B evaluation flows. Two artifacts generated from the same input would be distinct variants with distinct IDs and labels. A comparison artifact would evaluate both. The infrastructure for this (artifact IDs, metadata schema, explanation surface) is in place. The dual-generation and comparison-artifact generation are the missing pieces.

### What Artifacts Are NOT
Artifacts are not the unit of self-improvement proposals. The self-improvement lane uses `InsightProposalPayload`, `ChangeProposal`, and improvement_engine dicts — not artifacts. The artifact system and the self-improvement system are currently parallel and not interconnected.

**The gap in one sentence:** Artifacts are WESLR's external capability output (what it has built, marketed, offered). Proposals are WESLR's internal self-improvement output (what it wants to change about itself). These two views of WESLR are not yet connected — no artifact evaluation automatically generates a proposal, and no proposal references artifact metadata.

---

## SECTION 10 — INTEREST / RELEVANCE / SUGGESTION / THREAD STATUS

### Interest Tracker
- **What it does:** Explicitly tracked domains of significance stored in `weslr/interests.json`. Created manually via CLI (`interest create`) or `interest_tracker.create_interest()`. Max 50 interests, max 20 occurrences per interest.
- **What it must NOT do:** Auto-create interests. Auto-create occurrences. Use relevance to influence routing, wording, or decisions. Write outside `interest_tracker.py`.
- **Current integration points:** `sim.explain_item()` — `_relevant_interests` attached as metadata only. No other integration points exist.
- **Canonical document:** `docs/INTEREST_RELEVANCE_CANON_V1.md` (SEALED)

### Relevance Surface
- **What it does:** Read-only scoring of interests against artifact context. `_score_interest()` computes structural scores from tag overlap, name match, display_name match, tag-in-text match, recency, and occurrence count. Advisory only — never decides, routes, or modifies behavior.
- **What it must NOT do:** Use scores to influence decisions. Expand integration points without canonicalization doc update. Return results without `match_reasons` explainability.
- **Current integration points:** `relevance_surface.query_relevant_interests()` — called by `sim._derive_relevant_interests()`, which feeds `explain_item()`.
- **Canonical document:** `docs/INTEREST_RELEVANCE_CANON_V1.md` (SEALED), `docs/LONG_HORIZON_RELEVANCE_DOCTRINE_V1.md` (design doctrine for v2)

### Suggestion Surface
- **What it does:** Surfaces structured `interest_occurrence` suggestions via `_derive_suggestions()` in `sim.py`. Attached as `_suggestions` field in `explain_item()` output. Advisory only. 12-hour in-memory cooldown per `interest_id + item_id + suggestion_type`.
- **What it must NOT do:** Auto-record occurrences. Auto-create interests. Bypass `requires_approval: True`. Write to `interests.json`. Use confidence as a decision threshold. Route or influence responses outside the `_suggestions` field itself.
- **Current integration points:** `sim.explain_item()` — `_suggestions` attached as metadata only.
- **Canonical document:** `docs/SUGGESTION_SURFACE_CANON_V1.md` (SEALED)

### Thread Tracker
- **What it does:** Groups related artifacts, questions, suggestions, and resolutions into named, temporally ordered threads. Tracks thread state (`active`, `unresolved`, `resolved`, `dormant`). Read surface (`_thread_refs`) exposes thread membership as advisory metadata via `sim.explain_item()`. Slice 0 (storage + CLI) and Slice 1 (read-only metadata surface) implemented and validated.
- **What it must NOT do:** Auto-link artifacts to threads. Use thread membership to influence routing or decisions. Auto-close or auto-resolve threads. Scan artifacts for thread opportunities. Write outside `thread_tracker.py`.
- **Current integration points:** `sim.explain_item()` — `_thread_refs` attached as advisory metadata (read-only). No write integration.
- **Canonical documents:** `docs/THREAD_TRACKER_V1_DESIGN.md` (design), `docs/THREAD_TRACKER_CANON_V1.md` (canonical architecture)

---

## SECTION 11 — SELF-EVALUATION / SELF-IMPROVEMENT SYSTEM REALITY

The multi-lane self-improvement ecosystem is substantial. Here is the accurate state:

### Signal Detection
- Runtime failure events: `inadequacy_persistence.record_inadequacy_event()` → `weslr_inadequacy_events.jsonl`
- Proposal threshold evaluation: `cognitive_adequacy.evaluate()` (6 threshold types: repetition, low usefulness, low confidence streak, same fix loop, no improvement, evidence-to-action failure)
- Drift signals: `record_drift_signal()` → in-process 48h rolling window with 9 concern evaluators
- Identity/affect state: `run_self_evaluation()` (checks tension, stability, humor, self-critique, connection, cognitive diversity, external capabilities)
- Multi-source signals: `improvement_engine.collect_improvement_signals()` (test reflection, security reflection, operator reviews, suggestion requests)

### Persistence / Logging
- `weslr_inadequacy_events.jsonl` — inadequacy event stream
- `weslr_inadequacy_handoffs.jsonl` — CDI handoff records
- `weslr_inadequacy_intake.jsonl` — qualified intake records
- `continuity/improvement_engine/recommendations.json` — improvement proposals
- `continuity/improvement_engine/approved.json` / `rejected.json` / `duplicates.json` / `history.json` / `trends.json`
- `AuditLedger` + `AuditLedgerEngine` — structured audit trail for proposals

### Synthesis
- `DeterministicSynthesisEngine.synthesize_all()` — single-pass read-only synthesis producing: pattern groupings, approval reason groupings, proposal outcome groupings, confidence trend summaries, bottleneck recurrence summaries
- No mutation, no LLM dependency, no recommendations — pure analysis of existing records

### Proposal Generation
Five independent proposal generators:
1. `InsightProposalConverter` — converts synthesis outputs to `InsightProposalPayload` objects
2. `cognitive_dialogue.propose_improvement()` — findings → improvement proposal dict
3. `cognitive_dialogue_integration.build_cdi_bundle()` — adequacy finding → CDI bundle (explanation + proposal + operator outcome)
4. `self_eval.self_propose_improvements()` — gaps → proposals
5. `WeslrImprovementEngine.build_operator_proposals()` — signals → ranked proposals → `recommendations.json`

### Proposal Packaging
- `InsightProposalPayload` dataclass — structured container with `proposal_id`, `title`, `type`, `pattern_summaries`, `grouped_rationale`, `recurrence_summaries`, `confidence_summaries`, `validation_requirements`, `rollback_expectations`, `evidence_claim_ids`, `evidence_confidence`
- `InsightProposalExporter` — exports to ASCII-formatted text or JSON
- `cognitive_dialogue` — three-function CDI lane: `explain_inadequacy()`, `propose_improvement()`, `handle_operator_response()`
- `SelfArchitecture.ComparisonOption` + `ComparisonResult` — A/B comparison packaging

### Explanation
- `DeterministicSynthesisFormatter` (6 formatters) — human-readable text per synthesis category
- `InsightProposalExporter.format_proposal()` — 60-char border formatted text
- `self_eval.generate_self_speech()` — natural language growth articulation
- `run_self_evaluation()` — structured summary with gaps list
- `get_self_summary()` — 6-layer composed self-model (identity, trust, health, continuity, institutional, concerns)

### Operator Review / Governance
- `ExecutionGate` — full proposal lifecycle: create → review → approve/deny/refine → execute (if approved) → state transitions with audit entries
- `cognitive_dialogue.handle_operator_response()` — approve/deny/refine handler
- `self_eval.self_apply_changes()` — logs self-proposals, all marked `needs_approval: True` (not yet connected to ExecutionGate)
- Drift loop: `get_pending_reflections()` → operator acknowledges or dismisses

### Execution
- `ExecutionGate.execute_proposal_if_approved()` — approved proposal execution with audit
- `self_eval.self_apply_changes()` — only logs; requires operator approval before any change

### Audit / History
- `AuditLedgerEngine` — records: proposal_created, proposal_approved, proposal_denied, proof_requested, escalation_triggered/approved/denied
- `ChangeProposal.transition_state()` — per-proposal state change with actor + details
- `institution.Reflection` — in-process reflection status tracking with PENDING/COOLDOWN/SURFACED/DISMISSED
- `operator_insight_history` / `operator_insight_timeline` / `operator_insight_comparison` — operator insight persistence

### What Is Already Substantial
Every component in every layer is implemented and tested. The self-evaluation infrastructure is not missing pieces — it is a set of well-built parallel tracks.

### What Remains Fragmented
The five proposal generators are not unified. No deduplication exists between proposal systems. No unified operator-facing view of all active proposals exists. The formal governance system (ExecutionGate) does not receive improvement_engine recommendations. The self_eval loop does not route its proposals to the governance system. The drift loop does not connect to the proposal lane.

---

## SECTION 12 — GOVERNANCE MODEL

### What WESLR May Observe Autonomously
- Relevance state (via `relevance_surface.query_relevant_interests()`)
- Thread membership (via `thread_tracker.get_threads_for_item()`)
- Drift signal state (via `record_drift_signal()`)
- Inadequacy events (via `record_inadequacy_event()`)
- Proposal adequacy (via `cognitive_adequacy.evaluate()`)
- Identity/affect state (via `run_self_evaluation()`)
- Institutional health (via `get_institutional_health_summary()`)
- Continuity posture (via `get_continuity_status()`)
- Pending reflections (via `get_pending_reflections()`)
- Self-model state (via `get_self_summary()`)

### What WESLR May Suggest Autonomously
- Structured suggestions via `_derive_suggestions()` (surfaced as `_suggestions` in `explain_item()`)
- CDI improvement proposals via `propose_improvement()` (requires operator in the loop)
- Self-directed growth proposals via `self_propose_improvements()` (all require approval)
- Improvement recommendations via `improvement_engine` (advisory only, no formal review)
- Drift concerns via `run_drift_observation_pass()` (surfaced for acknowledgment)
- Self-architecture evaluation results via `SelfArchitecture.evaluate_suggestion()` (structured output)
- Comparison results via `TradeoffEngine.compare_options()` (structured output)

### What Requires Operator Approval
- Any execution that modifies production state (file writes, code changes, configuration changes, registry modifications)
- Proposal execution via `ExecutionGate` (approved → denied transition required)
- Self-proposed changes via `self_apply_changes()` (all marked `needs_approval: True`)
- Occurrence recording (`interest_tracker.add_occurrence()`) — operator must approve via `requires_approval: True` in suggestion action
- New interests (`interest_tracker.create_interest()`) — explicit CLI or API call required
- Thread state changes (`thread set-state`) — operator CLI only

### What Must Never Happen Silently
- Auto-creation of interests or occurrences
- Auto-linking of artifacts to threads
- Silent modification of proposal or artifact state
- Auto-closure or auto-resolution of threads
- Auto-execution of any suggestion or proposal
- Hidden routing influence from relevance scores, suggestion confidence, or thread membership
- Bypassing of `requires_approval: True` on any suggestion action
- Direct writes to `threads.json`, `interests.json`, or any registry from outside the canonical write module

### How Proposals, Changes, and Execution Are Gated
```
Proposal Generated
    ↓
Routing decision: which proposal type?
    ├─ InsightProposalPayload → ExecutionGate.review_proposal()
    ├─ ChangeProposal (self-architecture) → SelfArchitecture.get_recommendations()
    ├─ improvement_engine recommendation → recommendations.json (advisory only)
    └─ self_eval proposal → logged, needs_approval: True (not yet routed to ExecutionGate)
    ↓
Operator: approve / deny / refine
    ├─ Approve → ExecutionGate.transition_state("approved") → execute_proposal_if_approved()
    ├─ Deny → ExecutionGate.transition_state("denied") → audit trail
    └─ Refine → refinement returned, repropose
    ↓
Execution (if approved) → audit entry recorded
```

The formal ExecutionGate path is only used by Lane A (CDI proposals) and the self-architecture lane. Other proposal types are advisory only or require manual operator action.

---

## SECTION 13 — LIVE SELF-QUERY SURFACE

### `institution.py:get_self_summary()` — The Canonical Read Surface

`get_self_summary()` (institution.py, line ~1430) is the **canonical read-only query surface** for WESLR's composed self-model. It is the single entry point for getting a coherent snapshot of WESLR's current state.

**Six composing layers:**

| Layer | Source Function | Content |
|-------|----------------|---------|
| `identity` | `_get_identity()` | name (WESLR), version (v1), description, canonical_since |
| `trust_posture` | `_get_trust_posture()` | bootstrap_verified_timelines, pending_bootstraps, root_trust, status |
| `health_posture` | `_get_health_posture()` | subsystem_count, critical_risks, high_risks, governance decisions (approved/rejected), pending_proposals, capsule_operational, routing_count |
| `continuity_posture` | `_get_continuity_posture()` | from `continuity.get_continuity_status()` or `unified_continuity.get_continuity_status()` |
| `institutional_posture` | `_get_institutional_posture()` | institution_count, total_governors, total_roles, vacant_roles |
| `active_concerns` | `_get_active_concerns()` | pending reflections from drift loop (concerns not in cooldown) |

Plus two composed summary fields: `strengths` and `unresolved_weaknesses`.

**What it is for:**
- Operators querying WESLR's current state via a single call
- Composing a self-model summary for operator dialogue
- Providing a stable read surface for external tooling

**What it does NOT replace:**
- It is a **read surface**, not the full self-model architecture
- It does not cover the full self-improvement ecosystem (only reflects active_concerns from the drift loop, not the adequacy lane, self_eval lane, or improvement_engine lane)
- It does not have a write path — it cannot be the target of any improvement proposal
- It does not replace `InsightProposalPayload`, `ExecutionGate`, or any proposal system
- It does not replace the interest tracker, relevance surface, suggestion surface, or thread tracker
- It does not replace `get_institutional_health_summary()` (which provides detailed subsystem-level health, not just counts)
- It does not replace the drift reflection system — it only surfaces pending concerns, not the full reflection state (pending/cooldown/surfaced/dismissed counts)

**Usage:**
```python
from weslr.institution import get_self_summary
state = get_self_summary()
# Returns: {generated_at, identity, trust_posture, health_posture, continuity_posture,
#           institutional_posture, active_concerns, strengths, unresolved_weaknesses}
```

---

## SECTION 14 — ENVIRONMENT / DEPLOYMENT / SOFTWARE / LAN AWARENESS EXPECTATIONS

### Intended Future Capabilities (Not Yet Implemented)

WESLR's architecture anticipates the following whole-system awareness capabilities, but most are **not yet implemented**:

**Environment Understanding:**
- Intent: WESLR understands its deployment context (local Termux, remote server, cloud, etc.)
- Current: No structured environment detection. Provider configuration (`OLLAMA_HOST`, `WESLR_LLM_PROVIDER`) is read from config but not used to adapt behavior beyond provider selection.

**Deployment Context Awareness:**
- Intent: WESLR knows whether it is running in a mobile/termux context, a server context, or a cloud context
- Current: No deployment context registry. No adaptive behavior based on deployment type.

**Software/Service Awareness:**
- Intent: WESLR maintains an inventory of services it depends on (LLM provider, storage backends, external APIs)
- Current: Provider health check via `providers.py` (`provider.health()`) exists as a mechanism. It is not yet wired into the governance surface as a monitored dependency. No service registry.

**LAN / Network Awareness:**
- Intent: WESLR understands its network position (local network access, tailnet, public internet)
- Current: No LAN awareness. `socket.getfqdn()` used in provider abstraction but not as a network awareness signal.

**Operator Constraints:**
- Intent: WESLR knows constraints imposed by the operator (preferences, hard limits, deployment boundaries)
- Current: Some operator profile fields exist in `communicatorSelfPreservation`. No formal constraint registry.

**System-Management Ambitions:**
- Intent: WESLR has enough self-awareness to detect degradation, propose fixes, and recover gracefully
- Current: The drift loop (`record_drift_signal`, `run_drift_observation_pass`) and the adequacy hook are partial implementations of this. The full self-healing loop (detect → propose → approve → execute → verify) is not yet implemented.

### Currently Implemented Awareness

| Capability | What Exists |
|-----------|-------------|
| Provider reachability | `providers.py` — `OllamaProvider.health()`, `OpenAIProvider.health()` |
| Bootstrap trust state | `bootstrap.py` — `is_user_bootstrap_verified()`, timeline verification |
| Subsystem health | `get_institutional_health_summary()` — subsystem counts and critical risks |
| Governance health | `get_institutional_health_summary()` — decisions by type, pending proposal counts |
| Drift detection | 9 concern evaluators in `institution.py` — latency, memory quality, handover gap, governance override, escalation friction, lifecycle stagnation, institution recurrence, bottleneck recurrence, suggestion rejection |
| Adequacy evaluation | `cognitive_adequacy.evaluate()` — 6 threshold types for proposal sequences |
| Continuity state | `continuity.py` / `unified_continuity.py` — `get_continuity_status()` |

### What Is Clearly NOT Implemented
- No deployment context detection
- No service dependency registry
- No network awareness beyond provider reachability
- No adaptive behavior based on environment
- No self-healing execution loop (detect → propose → approve → execute → verify)
- No LAN topology awareness

---

## SECTION 15 — SEALED CANONS AND WHAT THEY GOVERN

The following canonical documents are the authoritative contracts for their respective systems. They are binding. Changes require explicit updates to the relevant document and operator approval.

### INTEREST_RELEVANCE_CANON_V1.md
**Status:** SEALED
**Governs:** Interest Tracker (interest creation, occurrence recording, write authority boundary, read rules), Relevance Surface (scoring, advisory-only contract, integration points), `interests.json` schema, bounds (max 50 interests, max 20 occurrences/interest), forbidden drift
**Key rule:** Only `interest_tracker.py` may write to `interests.json`. No auto-creation. No routing influence from relevance scores.

### SUGGESTION_SURFACE_CANON_V1.md
**Status:** SEALED
**Governs:** Suggestion surface (`_suggestions` field in `explain_item()`), suggestion object shape, cooldown contract (12h, in-memory, per interest_id+item_id+suggestion_type), `requires_approval: True` as structural invariant, forbidden drift
**Key rule:** Suggestions may never auto-execute. No write authority from suggestion surface.

### LONG_HORIZON_RELEVANCE_DOCTRINE_V1.md
**Status:** DESIGN DOCTRINE (not implementation)
**Governs:** Why Relevance v1 breaks down over long horizons (recency false salience, count popularity gravity, lexical matching limits, dormancy invisibility), five core relevance laws, six failure modes, v2 design directions, safe migration path
**Key rule:** Recency cannot create relevance by itself. Count cannot create relevance by itself. Foundational interests must be distinguished from popular ones.

### RELEVANCE_AUTONOMOUS_SUGGESTION_ADDENDUM_V1.md
**Status:** DOCTRINE ADDENDUM
**Governs:** Three-tier model (autonomous observation → proactive suggestion → governed consequence), what WESLR may observe and suggest autonomously, what requires operator approval, gap between "observes and suggests" and "acts with authority"
**Key rule:** WESLR may autonomously observe and suggest through normal communication channels. WESLR may not autonomously convert observations into consequential authority without operator approval.

### RELEVANCE_EVOLUTION_SLICE2_DESIGN_V1.md
**Status:** DESIGN DRAFT
**Governs:** Future eligible signal classes (beyond current 4), tag specificity weighting, eligibility vs amplification separation, gating logic, future extension requirements
**Key rule:** Each new signal class requires a written proposal, operator approval, explicit canonicalization doc update, and tests before implementation.

### THREAD_TRACKER_V1_DESIGN.md
**Status:** DESIGN
**Governs:** Thread Tracker purpose, core concepts (Thread, Thread Item, Thread State, Link Type), what Thread Tracker is and is not, thread schema, state machine, link types, integration points
**Key rule:** No auto-linking. Thread membership is advisory metadata, not routing authority.

### THREAD_TRACKER_CANON_V1.md
**Status:** CANONICAL (created 2026-04-21)
**Governs:** Slice 0 + Slice 1 implementation reality, authoritative files, data model contract (100 thread max, 200 items/thread, 5 item types, 4 states), write rules (operator CLI only), read surface contract (`_thread_refs` exact field shape), safety and governance rules, forbidden drift, future extension rules
**Key rule:** Only `thread_tracker.py` may mutate `threads.json`. `_thread_refs` is advisory metadata only.

### COGNITIVE_ADEQUACY_IMPROVEMENT_DOCTRINE_V1.md
**Status:** Doctrine (design direction)
**Governs:** Why adequacy evaluation needs improvement, threshold calibration approach, behavioral contract tests, improvement loop design, governance for adequacy refinements

### PROPOSAL_LINEAGE_VIEW_V1.md / PROPOSAL_LINEAGE_IMPLEMENTATION_PLAN_v1.md
**Status:** Design / Implementation plan
**Governs:** Proposal lineage tracking — how proposals relate to the signals that triggered them, how to trace a proposal back to its source events

### APPROVAL_GATED_SELF_IMPROVEMENT_LOOP_v1.md
**Status:** Sealed chapter
**Governs:** The formal self-improvement approval loop — proposal → execution gate → operator approval → execution → audit

### ADDITIONAL RELEVANT CANON DOCUMENTS
- `FULL_SYSTEM_TRUTH_AUDIT.md` — system-wide truth audit
- `SYSTEM_READINESS_AUDIT.md` — system readiness assessment
- `GOVERNED_ACTIVATION_PERMISSION_FRAMEWORK_v1.md` — activation permission framework
- `DOCTRINE_FIRST_ENGINEERING_STANDARD_v1.md` — doctrine-first engineering standard

---

## SECTION 16 — ACTIVE GAPS / BOTTLENECKS

The following are the currently known architectural bottlenecks, grounded in repo reality:

### Gap 1 — No Single Fully Canonical Self-Improvement Core
Seven parallel self-improvement lanes exist without a unified core. Lane A (adequacy/CDI) is the most complete but is not yet the integration target for other lanes. This is not a missing-code gap — it is an integration architecture gap. All components exist; the unifying routing layer does not.

### Gap 2 — Proposal Format Fragmentation
Four different proposal schemas coexist: `InsightProposalPayload`, `ChangeProposal` (change_proposals.py), improvement_engine plain dict, self_eval plain dict. No normalization layer exists. No deduplication mechanism exists between systems.

### Gap 3 — CDI Bundle Not Auto-Triggered
`build_cdi_bundle()` in `cognitive_dialogue_integration.py` is designed as the canonical lane for adequacy-driven proposals, but it is never called automatically from the adequacy pipeline. The auto-path from `inadequacy_intake` ends at proposal export, not at CDI bundle creation.

### Gap 4 — Self-Eval Proposals Not Connected to Governance
`self_apply_changes()` produces proposals all marked `needs_approval: True`, but these are never routed to `ExecutionGate`. The self-directed growth loop dead-ends at the approval step.

### Gap 5 — Drift Loop Not Connected to Proposals
`run_drift_observation_pass()` surfaces concerns as `Reflection` objects. These are never converted into `InsightProposalPayload` or `ChangeProposal` records. Concerns are acknowledged and forgotten — not actioned.

### Gap 6 — Improvement Engine Recommendations Not Governed
`improvement_engine.build_operator_proposals()` outputs to `recommendations.json`. This is advisory only. There is no formal review path, no `ExecutionGate` connection, no audit trail for the review decisions.

### Gap 7 — No Artifact-to-Proposal Bridge
Artifacts are WESLR's capability output. Proposals are WESLR's self-improvement output. No path exists from artifact evaluation to proposal generation. An artifact revealing a weakness does not automatically become a CDI trigger or improvement signal.

### Gap 8 — No Unified Proposal Review Surface
An operator who wants to see "what should WESLR improve" must check at least four separate places: `InsightProposalExporter` outputs, `recommendations.json`, self_eval output, and pending reflections. No single view exists.

### Gap 9 — Environment-Awareness Gaps
No deployment context detection, no service dependency registry, no LAN awareness, no adaptive behavior based on environment. The infrastructure anticipated these but they are not yet built.

### Gap 10 — No Self-Healing Execution Loop
The formal loop (detect → propose → approve → execute → verify) is not implemented. Detection exists (adequacy, drift). Proposal exists (multiple types). Approval exists (ExecutionGate for Lane A). Execution exists (`execute_proposal_if_approved()`). Verification does not exist — no loop closure.

---

## SECTION 17 — FORBIDDEN DRIFT

The following changes are **explicitly forbidden** without a new canonical document and operator approval:

- **Creating new parallel self-improvement loops without a canon document** — new lanes must be documented before code, not discovered after
- **Bypassing governance/execution gates** — no autonomous execution of proposals, changes, or modifications without operator approval
- **Hidden self-modification** — no silent writes to production state, configuration, or memory systems
- **Turning relevance/suggestions/threads into routing authority** — these are advisory metadata; they may not influence handler selection, response strategy, or decision logic
- **Relying on dashboards as the primary mode of ongoing operator control** — suggestions and governance must work through normal interaction channels (text/voice); dashboards are for inspection only
- **Reducing WESLR to only chat behavior or only memo generation** — WESLR is a continuity-first governed reasoning system; the self-evaluation infrastructure, memory systems, and governance loops are as core as the dialogue interface
- **Treating `get_self_summary()` as the full self-model instead of just a read surface** — it is one composed read surface; it does not replace the proposal systems, governance infrastructure, or the full self-improvement ecosystem
- **Auto-creation of interests, occurrences, or thread links** — all are explicit-only operations
- **Silent proposal generation without a canonical path to operator review** — proposals must route through a defined review surface, not be silently generated and forgotten
- **Using confidence scores as decision gates** — confidence is advisory metadata; it may not be used as a condition for routing, execution, or state changes
- **Parallel proposal formats without a normalization layer** — new proposal types must define how they relate to the canonical proposal schema, not proliferate independently

---

## SECTION 18 — SAFE RESTART RITUAL FOR FUTURE CODER SESSIONS

### Before Any Major Work, the Coder Must:

**Step 1 — Read the foundational documents in order:**
1. `docs/WESLR_CANONICAL_SELF_MODEL_V1.md` (this file) — orientation to what WESLR is and how it is structured
2. Current relevant canon docs (see Section 15) — specifically the canon(s) governing the area you intend to work in
3. Current active phase / next-step section — check for active phase documentation in `docs/PHASE*` files or `docs/CURRENT_PHASE.md` if it exists

**Step 2 — Confirm the following before touching any files:**
```
Current branch: [git branch --show-current]
Allowed scope: [from relevant canon docs + operator brief]
Forbidden scope: [from Section 17 of this document + relevant canons]
Exact next task: [specific, from operator brief or phase documentation]
```

**Step 3 — Verify no parallel work is in progress:**
```
git status
openclaw status (if available)
```

**Step 4 — If the task involves self-improvement, proposal generation, or governance:**
- Confirm which lane the work targets
- Confirm whether the work is a feeder to Lane A or a new canonical lane
- If a new proposal format is involved, confirm how it normalizes to existing proposal systems

**Step 5 — If the task involves artifacts, relevance, suggestions, or threads:**
- Confirm the exact integration point(s) from the relevant canonical document(s)
- Do not add integration points without updating the canonical document(s) first

**Step 6 — If the task involves code changes (not just documentation):**
- Run relevant tests first: `python -m pytest weslr/test_cognitive_adequacy*.py weslr/test_deterministic_synthesis*.py weslr/test_thread*.py` or equivalent
- Confirm the change does not violate the write authority boundaries defined in the relevant canon(s)
- Confirm the change does not modify `requires_approval: True` invariants

### The coder must NOT:
- Assume the current branch is the right branch for the task
- Assume that because code exists, it is canonical (check Section 8 for classification)
- Implement new proposal formats without defining a normalization path to Lane A
- Add integration points without updating the relevant canonical document(s)
- Bypass the ExecutionGate for any execution that modifies production state
- Treat `get_self_summary()` as a replacement for understanding the full self-improvement architecture
- Reduce WESLR to a chatbot or memo generator in any design or implementation

---

## SECTION 19 — STOP LINE

**Confirmed:**
- Documentation only ✅
- No production code changes ✅
- No schema changes ✅
- No behavior changes ✅
- No new integration points ✅
- No refactoring ✅
- No new parallel self-improvement loops ✅
- No bypass of governance/execution gates ✅

**Canonical document created:** `docs/WESLR_CANONICAL_SELF_MODEL_V1.md` ✅

**Stop after document creation. Do not modify production code. Do not create dashboards. Do not refactor architecture in this step.**

---

*This document was created following the self-evaluation architecture mapping pass (2026-04-21) and is the authoritative self-model reference for all future WESLR OC Coder sessions.*
