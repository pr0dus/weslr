# WESLR 50-User Working Version Roadmap V1

## Executive summary

WESLR is **not yet a broad public product**. The goal of this roadmap is a **controlled 50-user working version**: invite-only or manually approved, bounded, observable, and reliable enough to support repeated real use without pretending to be finished intelligence.

This roadmap prioritizes:
- reliability before richer cognition
- state before personality
- checked execution before improvisation
- memory honesty before memory breadth
- operator visibility before autonomy
- narrow tools before many tools
- governed drift before self-modification
- exact review lanes before runtime integration

## 1) Current architecture baseline

From the discovery docs, WESLR already has:
- a live shell
- a strong boundary/governance layer
- memory/provenance scaffolding
- helper-level cognition primitives
- release discipline

But it still lacks:
- one unified runtime intelligence loop
- one coherent 50-user product experience
- a simple, stable state model that feels continuous across sessions
- a clean bridge from helper metadata to user-visible reliability

So the roadmap treats WESLR as a **governed state platform first**, and only later as a richer adaptive system.

## 2) 50-user definition

A 50-user working version means:
- invite-only or manually approved users
- bounded accounts
- controlled onboarding
- clear operator visibility
- basic continuity across sessions
- limited but reliable tool lanes
- safe memory behavior
- incident/error handling
- no public self-registration unless separately approved
- no public paid product claim unless separately approved

## 3) Roadmap principles

- reliability before richer cognition
- state before personality
- checked execution before improvisation
- memory honesty before memory breadth
- operator visibility before autonomy
- narrow tools before many tools
- governed drift before self-modification
- exact review lanes before runtime integration

## 4) Roadmap phases

### Phase 0 — Roadmap closure / review
**Purpose:** decide whether this roadmap is the right next path and what must be clarified before execution.

**Concrete deliverables:**
- reviewed roadmap
- success criteria
- go/no-go decision on whether to continue release-gate hardening review first or move into 50-user product work

**Prerequisite lanes:** none

**Likely files/modules/docs involved:**
- this roadmap doc
- review lane doc
- release-gate documentation

**Risk level:** low

**Validation required:** review approval

**What must not be done:**
- no implementation
- no runtime changes
- no public claims

**Recommended next lane after completion:** `REVIEW_WESLR_50_USER_WORKING_VERSION_ROADMAP_V1`

---

### Phase 1 — Product shell minimum
**Purpose:** define the smallest visible product shell that feels coherent to a user.

**Concrete deliverables:**
- account / invite / manual approval model
- conversation/workspace shell
- project/session structure
- basic UX identity
- user-visible “what WESLR can do now” surface
- visible non-goals and limitations for operators/testers

**Prerequisite lanes:** roadmap review

**Likely files/modules/docs involved:**
- `weslr/README.md`
- `weslr/PILOT_*`
- `weslr/PUBLIC_TEST_DEPLOYMENT.md`
- product shell / onboarding docs
- UI/runtime surface docs, not runtime edits yet

**Risk level:** medium

**Validation required:** UX/spec review, operator clarity review

**What must not be done:**
- no public self-registration
- no broad product claims
- no hidden autonomy

**Recommended next lane after completion:** `DESIGN_WESLR_PRODUCT_SHELL_MINIMUM_V1`

---

### Phase 2 — State and continuity MVP
**Purpose:** make WESLR feel continuous, honest, and source-scoped across sessions.

**Concrete deliverables:**
- session state
- project state
- user-approved persistent context
- memory honesty rules
- scoped source references
- correction/update flow
- no silent fake memory

**Prerequisite lanes:** Phase 1 shell definition

**Likely files/modules/docs involved:**
- `weslr/continuity.py`
- `weslr/context.py`
- `weslr/context_continuity.py`
- `weslr/entity_memory.py`
- `weslr/entity_timeline_memory.py`
- `weslr/memory_capture.py`
- `weslr/rag_query_routing_boundary.py`
- memory boundary docs

**Risk level:** high

**Validation required:** memory-boundary tests, source-scope tests, correction-path checks

**What must not be done:**
- no fake persistence
- no memory-as-authority
- no cross-user leakage

**Recommended next lane after completion:** `DESIGN_WESLR_STATE_AND_CONTINUITY_MVP_V1`

---

### Phase 3 — Tool-governed execution lanes
**Purpose:** create a small set of reliable, checked tool paths that users can trust.

**Concrete deliverables:**
- choose 3–5 reliable first tool lanes
- proposal-before-action
- validation-before-execution
- operator approval where needed
- clear user-facing tool status
- failure handling

**Prerequisite lanes:** Phase 2 continuity MVP

**Likely files/modules/docs involved:**
- `weslr/controlled_*`
- `weslr/*_boundary.py`
- `weslr/autonomous_debugging_dry_run_boundary.py`
- `weslr/tests/release_gate_v1.py`
- tool-use and execution boundary docs

**Risk level:** high

**Validation required:** dry-run validation, tool-status tests, approval boundary tests

**What must not be done:**
- no many-tool sprawl
- no unreviewed execution authority
- no user confusion about what was actually done

**Recommended next lane after completion:** `DESIGN_WESLR_TOOL_GOVERNED_EXECUTION_LANES_V1`

---

### Phase 4 — Observability and operator control
**Purpose:** make the system legible to the operator at 50-user scale.

**Concrete deliverables:**
- operator dashboard or operator-readable logs
- per-user state summary
- memory/change visibility
- incidents and blocked actions
- deletion/export/revocation status
- support workflow for 50 users

**Prerequisite lanes:** Phase 3 tool lanes

**Likely files/modules/docs involved:**
- governance surfaces
- audit/report helpers
- pilot/test logging docs
- release-gate and review docs

**Risk level:** medium-high

**Validation required:** operator-readability review, audit trail checks, incident visibility checks

**What must not be done:**
- no hidden behavior
- no opaque state changes
- no operator-unreadable drift

**Recommended next lane after completion:** `DESIGN_WESLR_OPERATOR_OBSERVABILITY_AND_CONTROL_V1`

---

### Phase 5 — Safety/governance closure
**Purpose:** lock the safety, privacy, and boundary story before scale.

**Concrete deliverables:**
- privacy/terms alignment
- deletion/export boundaries
- operator authority
- public/pilot claim boundaries
- release-gate status
- audit/readiness checks
- no hidden autonomy surprises

**Prerequisite lanes:** Phases 1–4

**Likely files/modules/docs involved:**
- privacy/deployment docs
- release gate docs
- governance docs
- pilot/runbook docs

**Risk level:** medium

**Validation required:** policy review, release-gate review, boundary review

**What must not be done:**
- no public launch claims
- no stealth autonomy
- no boundary weakening

**Recommended next lane after completion:** `DESIGN_WESLR_SAFETY_GOVERNANCE_CLOSURE_V1`

---

### Phase 6 — Latency and responsiveness
**Purpose:** make the system feel responsive and trustworthy under repeated use.

**Concrete deliverables:**
- immediate acknowledgement
- progressive response
- background task state
- reaction-time budget
- graceful slow-path handling
- user trust under repeated use

**Prerequisite lanes:** Phases 1–5

**Likely files/modules/docs involved:**
- latency helper docs
- timing/budget helpers
- product shell UX docs
- operator logs

**Risk level:** medium

**Validation required:** timing checks, slow-path checks, repeated-use UX checks

**What must not be done:**
- no fake speed
- no hidden long-running actions without status
- no performance claims without evidence

**Recommended next lane after completion:** `DESIGN_WESLR_LATENCY_AND_RESPONSIVENESS_V1`

---

### Phase 7 — Bounded adaptive identity
**Purpose:** let the system remain stable and recognizable while still adapting under governance.

**Concrete deliverables:**
- stable tone/personality boundaries
- cross-session continuity
- adaptive behavior only from approved state
- no claims of being alive
- no uncontrolled self-modification
- slow governed drift

**Prerequisite lanes:** Phases 2, 5, 6

**Likely files/modules/docs involved:**
- identity/canon/context docs
- continuity and memory docs
- governance and answer-boundary docs

**Risk level:** high

**Validation required:** identity-boundary review, drift review, memory-authority review

**What must not be done:**
- no autonomy theater
- no identity inflation
- no unreviewed self-change

**Recommended next lane after completion:** `DESIGN_WESLR_BOUNDED_ADAPTIVE_IDENTITY_V1`

---

### Phase 8 — Proto-cognitive/regulatory extensions later
**Purpose:** only after the 50-user base is stable, add richer regulation and self-state layers.

**Concrete deliverables:**
- homeostasis metrics
- state tracking
- failure recovery
- internal regulation loops
- memory influence on behavior
- only after base 50-user reliability exists

**Prerequisite lanes:** Phases 1–7

**Likely files/modules/docs involved:**
- advanced state/regulation docs
- future helper boundaries
- internal evaluation and rehearsal docs

**Risk level:** very high

**Validation required:** strict review, staged rollout plan, rollback plan

**What must not be done:**
- no early overbuild
- no pretending this is the first priority
- no self-evolving autonomy

**Recommended next lane after completion:** `DESIGN_WESLR_PROTO_COGNITIVE_REGULATORY_EXTENSIONS_V1`

## 5) Pressure-tier mapping

### Tier 1
- stable product shell
- safety/governance
- controlled memory/continuity
- reliable tool lanes
- observability/operator control

### Tier 2
- latency/responsiveness
- bounded identity/adaptive behavior

### Tier 3
- richer proto-cognitive/regulatory layers
- advanced self-state systems
- advanced adaptive cognition

## 6) Screenshot-derived architecture implications

### Implication A — architecture matters more than prompt style
Pure prompting is not enough. The roadmap must prioritize state, tools, and execution discipline over chat-surface cleverness.

### Implication B — checked execution beats improvisation
Grounded feedback loops matter more than fluent guessing. The roadmap should favor proposal, validation, and operator-visible execution status.

### Implication C — memory must be episodic and governed
Memory should improve future behavior, but only through scoped, reviewable, source-aware channels.

### Implication D — regulation/homeostasis matters
The system should track its own state and recover gracefully. Stability is part of the product.

### Implication E — persistent identity must be bounded
Cross-session identity can help continuity, but it must never become authority drift or “alive” theater.

### Implication F — security against manipulation is core
The roadmap must preserve the poison-shield / authority-firewall model and keep external content out of command authority.

### Implication G — slow governed drift is the right growth model
WESLR should evolve by reviewed change, not random leaps.

## 7) 50-user readiness checklist

### Product shell
- [ ] invite-only or manual approval exists
- [ ] users can understand what WESLR is for
- [ ] limitations are visible
- [ ] session/project structure is coherent

### Onboarding / access
- [ ] onboarding path is bounded
- [ ] account approval is controlled
- [ ] no public self-registration by default
- [ ] access revocation is possible

### Memory / continuity
- [ ] memory is scoped
- [ ] corrections persist safely
- [ ] no fake memory claims
- [ ] source scope is visible

### Tool lanes
- [ ] 3–5 reliable lanes selected
- [ ] proposal-before-action exists
- [ ] validation-before-execution exists
- [ ] failure handling is clear

### Safety / governance
- [ ] operator authority remains explicit
- [ ] privacy/deletion/export boundaries exist
- [ ] public/pilot claims are bounded
- [ ] release-gate status is clear

### Observability / operator
- [ ] operator-readable state exists
- [ ] incidents are visible
- [ ] blocked actions are visible
- [ ] per-user summaries are possible

### Latency / responsiveness
- [ ] immediate acknowledgement exists
- [ ] progressive response exists
- [ ] slow-path status is visible
- [ ] repeated use feels stable

### Support / incident handling
- [ ] support workflow exists
- [ ] error escalation path exists
- [ ] blocked actions are explainable
- [ ] operator intervention is visible

### Legal / privacy / pilot boundaries
- [ ] deletion/export boundary is defined
- [ ] pilot claim boundary is defined
- [ ] no public readiness claim is implied
- [ ] no certification claim is implied

### Launch / no-launch criteria
- [ ] launch only if shell, continuity, tools, observability, and safety are coherent
- [ ] no launch if state is still fake or opaque
- [ ] no launch if operator control is unclear
- [ ] no launch if public self-registration is premature

## 8) What not to do yet

- do not chase superintelligence claims
- do not overbuild proto-cognitive layers first
- do not add many unstable tools
- do not expose public self-registration prematurely
- do not create public benchmark/certification claims
- do not make WESLR look alive
- do not use memory as authority
- do not bypass operator control
- do not store OCC workflow context inside WESLR master

## 9) Recommended immediate next lanes

1. `REVIEW_WESLR_50_USER_WORKING_VERSION_ROADMAP_V1`
2. `DESIGN_WESLR_PRODUCT_SHELL_MINIMUM_V1`
3. `DESIGN_WESLR_STATE_AND_CONTINUITY_MVP_V1`
4. `DESIGN_WESLR_OPERATOR_OBSERVABILITY_AND_CONTROL_V1`
5. `REVIEW_RELEASE_GATE_BROAD_ALLOWLIST_DETECTOR_V1` (pending; schedule before deeper release-gate hardening)

## Final judgment

`weslr_50_user_working_version_roadmap_ready_for_review`
