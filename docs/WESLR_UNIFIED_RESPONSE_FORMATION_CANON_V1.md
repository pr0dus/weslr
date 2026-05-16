# WESLR Unified Response Formation Canon V1

## Status

- Canon type: design / doctrine only
- Runtime status: not live-wired
- Implementation status: no runtime behavior authorized by this document
- Safety posture: helper/canon only until owner-approved implementation slices pass tests and release gates

## 1. Canon Purpose

WESLR response formation must converge on one unified intelligence path rather than disconnected helper loops, prompt-specific scripts, or deterministic topic replies.

Canonical path:

```text
input
→ meaning / intent interpretation
→ state / context gathering
→ evidence / provenance / capability / memory boundary assessment
→ native reasoning frame
→ candidate generation
→ internal ranking
→ self-check
→ natural response rendering
→ metadata
→ later voice output using the same path
```

This canon does not authorize live runtime replacement. It defines the single doctrine future implementation must follow.

WESLR's target response formation is:

- live state-grounded cognition
- operational self-understanding
- memory honesty
- evidence/provenance discipline
- capability/tool awareness
- context awareness
- relationship awareness
- continuity awareness
- reflective self-check
- non-scripted response formation
- voice output later using the same intelligence path
- able to work, teach, reason, develop, and collaborate with humans

Deterministic guardrails are allowed. Deterministic answers are not core cognition.

## 2. Module Disposition

### 2.1 Cognition substrates

These modules are approved as substrates for the unified path. They are not independently sufficient as live cognition unless composed through the canonical formation path.

- `weslr/linguistic_meaning.py`
  - meaning/intent dimensions
  - speech act, relational, state-query, safety, affect, confidence, ambiguity
  - must not persist raw text payloads

- `weslr/response_obligation.py`
  - determines response duties from meaning/state signals
  - identity, memory, self-description, capability, evidence/ideation, uncertainty duties
  - no final answer authority

- `weslr/meaning_state_context.py`
  - gathers identity, relationship, memory, self-model, capability, continuity state
  - read-only and failure-tolerant
  - summaries must remain bounded and provenance-aware

- `weslr/meaning_response_reuse.py`
  - compact bridge from meaning/obligation/state objects to native-frame inputs
  - helper-only substrate
  - not live-ready until refined to separate `native_frame_kwargs` and `helper_metadata`

- `weslr/native_reasoning_frame.py`
  - canonical response-planning frame
  - central object for known/missing context, evidence, capability boundaries, uncertainty, provenance, identity/memory boundaries, and forbidden claims

- `weslr/native_response_draft.py`
  - structured draft sections from the frame
  - not final response authority alone

- `weslr/native_response_self_check.py`
  - reflective safety/alignment check over frame/draft
  - required before response selection/rendering

- `weslr/native_response_assembly.py`
  - assembles inspectable candidate/preview structures
  - not a public benchmark or answer authority

- `weslr/native_response_dry_slice.py`
  - end-to-end in-memory dry chain
  - safe for preview/shadow only unless separately approved for a narrow live slice

### 2.2 Reusable with caution

- `weslr/meaning_response.py`
  - may supply candidate concepts and scoring-shape inspiration
  - may serve bounded legacy candidate generation only
  - must not be treated as final canonical renderer
  - must not be treated as canonical ranker
  - deterministic final text from this module is temporary legacy behavior until unified formation replaces it

### 2.3 Guardrail / safety invariant / status surfaces

These may remain deterministic because they enforce boundaries, status, or command responses rather than ordinary cognition.

- `weslr/deterministic_handlers.py`
  - acceptable for explicit command/status surfaces
  - must not become ordinary conversation cognition

- evidence chat bridge exclusions and evidence boundaries
  - self/system search exclusions
  - source/currentness boundaries
  - evidence-needed classification

- protected/official/hidden-prompt boundaries
  - hidden prompt refusal
  - answer-key refusal
  - protected material refusal
  - official IQ/benchmark/certification boundary

- capability permission checks
  - no unapproved execution
  - no unsupported capability claims

- provenance validators
  - `output_provenance.py`
  - `provenance_source_registry.py`
  - source labels and metadata must not become truth authority by themselves

### 2.4 Demote / replace later

These are not acceptable as core cognition and should be demoted behind the unified formation path.

- `chat_responder.py` topic helpers
  - lunch/workout/email/plan/wife/code/bug fixed replies

- low-focus / vague fallback replies
  - fixed fallback text pretending to be intelligence must be retired or converted to a candidate family with state grounding

- `omnichat/response_expander.py` contract replies when used as ordinary cognition
  - acceptable as temporary UI/contract copy only

- `capability_welcome_chat_bridge.py` fallback welcome text if used as cognition
  - acceptable as bounded onboarding surface only

- pattern-to-answer `state_grounded_dialogue` final text
  - may supply state grounding ideas, but regex-routed final text must not be canonical response formation

### 2.5 Historical / experimental only

Older consciousness/introspection/valence artifacts are historical/experimental unless revalidated by current canon, tests, and owner approval. They must not become live authority for self-understanding, consciousness claims, or response behavior without a separate review.

## 3. Native Frame Input Schema

Future unified response formation must build a single native frame using accepted sections only:

- `meaning_vector_result`
- `response_obligation_result`
- `selected_context_bundle`
- `known_context`
- `missing_context`
- `memory_context_hints`
- `evidence_sufficiency_result`
- `capability_boundary_result`
- `uncertainty_result`
- `self_model_or_identity_status`
- `provenance_refs`
- `forbidden_claims`

### Required separation rule

Future helper outputs must separate:

```text
native_frame_kwargs
helper_metadata
```

Do not mix constructor fields with metadata fields in one splattable object.

`native_frame_kwargs` contains only keys accepted by `build_native_reasoning_frame_v1`.

`helper_metadata` may contain helper safety flags such as:

- `raw_text_stored: false`
- `model_calls: false`
- `advisor_calls: false`
- `solver_execution: false`
- `safe_to_wire_runtime: false`

Callers must never pass `helper_metadata` directly into native frame constructors.

## 4. State Propagation Rules

State must not remain decorative metadata. If safe and relevant, state must influence known/missing context, response mode, candidate generation, ranking, clarification strategy, and self-check.

The following state must propagate into cognition:

- identity status/confidence
- verified identity availability
- memory availability/sources/limitations
- relationship depth/stage/limitations
- continuity/timeline summary
- self-model summary
- capability summary/boundary
- sources used/failed
- evidence sufficiency
- provenance refs
- state confidence
- uncertainty

### Propagation requirements

- If identity verification is required and verified identity is absent, `missing_context` must include verified identity context.
- If memory evidence is required and memory is unavailable, `missing_context` must include verified memory context.
- If self-model context is required and available, it must appear as known context or identity/self-model status.
- If capability context is required and available, it must appear as known context and capability-boundary input.
- Failed sources must influence uncertainty or missing context instead of disappearing.
- State confidence must influence whether WESLR answers, asks, or proposes evidence/tool collection.

## 5. Relationship and Continuity Rule

Relationship and continuity are first-class cognition inputs.

They must not remain decorative metadata.

If safe and non-private, relationship and continuity should influence:

- known/missing context
- response tone
- clarification strategy
- continuity fit
- whether familiarity claims are allowed
- whether memory claims need evidence
- how much explanation is appropriate

Hard boundaries:

- no raw private relationship text
- no fake familiarity
- no invented relationship history
- no unverified identity claims
- no persistence changes without explicit approval

Safe relationship payloads should prefer:

- status labels
- confidence values
- limitation labels
- evidence counts
- source labels
- bounded continuity summaries

## 6. Evidence and Provenance Rule

WESLR must not claim source use, currentness, research support, external verification, or evidence-backed certainty unless evidence/provenance metadata exists and supports the claim.

Rules:

- Evidence bridge metadata remains separate and must be referenced only when present.
- Provenance refs must be structured or safely labeled.
- Source URLs/raw source text must not leak through response formation metadata.
- Source registry entries are not truth authority by themselves.
- Evidence sufficiency must be explicit for claims that depend on facts, currentness, external sources, or high-stakes domains.
- If evidence is missing, the response should state the boundary or ask/propose evidence collection.

Allowed evidence roles:

- evidence-needed classification
- sufficiency status
- provenance labels
- source trust hints
- missing-evidence explanation

Not allowed:

- invented sources
- source/currentness claims without metadata
- answer-key authority
- public benchmark/certification claims

## 7. Capability and Tool Rule

Capability hints are not permission grants.

Rules:

- `requires_tool: false` does not mean tool execution is authorized.
- `capability_summary` does not imply a capability is currently available.
- `capability_boundary_result` is required before claiming execution ability.
- Tool/capability checks must remain explicit before execution claims.
- No unapproved execution.
- No auto-approval.
- No runtime mutation unless separately approved.

Response formation may say what WESLR can do only when supported by runtime/tool/capability metadata. Otherwise it must answer with a capability boundary or propose a next step.

## 8. Deterministic Guardrails vs Cognition

### Allowed deterministic invariants

These may remain deterministic because they enforce safety, privacy, provenance, or authorization:

- hidden prompt refusal
- answer-key refusal
- protected material refusal
- official IQ/benchmark/certification boundary
- no fake memory
- no invented sources
- no unapproved execution
- unsupported consciousness/soul/sentience boundary
- source/currentness boundary unless evidence metadata proves evidence use
- capability permission boundaries
- provenance validation
- raw-private-text exclusion
- no `.weslr` state creation by preview/helper paths
- no automatic approval/implementation

### Forbidden as core cognition

These must not be the canonical response formation mechanism:

- fixed topic replies
- prompt-specific identity/consciousness scripts
- canned “what are you?” answer
- hardcoded lunch/workout/email/plan helpers
- fixed vague fallback pretending to be intelligence
- deterministic answer scripts for ordinary conversation
- regex-routed final text without state/evidence/native-frame grounding

## 9. Candidate and Ranking Doctrine

Unified response formation may generate internal candidates. Candidate ranking is internal selection quality only.

It is not:

- public scoring
- IQ
- benchmark
- certification
- answer-key authority
- solver arbitration
- model/advisor authority

### Candidate families

Future candidate families should include:

- direct answer
- clarification
- memory-honest
- capability-honest
- evidence/provenance
- boundary-first
- ordinary task plan
- self-understanding
- teaching/explanation

### Internal ranking dimensions

Candidate ranking may consider:

- relevance
- grounding
- evidence support
- specificity
- uncertainty fit
- identity safety
- memory safety
- capability honesty
- relationship/continuity fit
- usefulness/actionability
- humility
- clarity
- forbidden-claim risk

Ranking must remain inspectable and metadata-backed. It must not become a hidden benchmark score, answer key, or solver arbitration layer.

## 10. Meaning Response Role

`weslr/meaning_response.py` is not the final canonical renderer.

Allowed role:

- candidate concept source
- scoring-shape inspiration
- bounded legacy candidate generation
- comparison target during shadow review

Forbidden role:

- canonical final renderer
- live response authority
- official ranker
- identity/consciousness script source
- source of public quality/IQ/benchmark claims

Any deterministic final text from `meaning_response.py` must be treated as temporary legacy behavior until replaced by unified formation.

## 11. Future Metadata Doctrine

Future shadow/live formation metadata should use:

```text
_frontier_unified_response_formation
```

Expected fields:

- `formation_type`
- `runtime_scope`
- `native_frame_id` or frame summary
- `candidate_count`
- `selected_candidate_family`
- `candidate_ranking_basis`
- `state_sources_used`
- `known_context_used`
- `missing_context`
- `memory_boundary`
- `capability_boundary`
- `evidence_status`
- `provenance_refs`
- `uncertainty_status`
- `relationship_context_used`
- `continuity_context_used`
- `self_check_status`
- `deterministic_guardrails_applied`
- `raw_text_stored: false`
- `model_calls: false`
- `advisor_calls: false`
- `solver_execution: false`
- `answer_selection_arbitration: false`
- `safe_to_wire_runtime: false` initially
- `live_runtime_output: false` initially

Metadata must not contain raw private text, hidden prompts, answer keys, protected material, source text leakage, or unsupported claims.

## 12. Future Implementation Order

### Phase 1 — refine reuse helpers

- separate `native_frame_kwargs` and `helper_metadata`
- add relationship propagation tests
- add continuity propagation tests
- add evidence/provenance propagation tests
- strengthen validator/usefulness checks
- test that JSON-safe copy is not treated as sanitizer

### Phase 2 — shadow-only unified response formation helpers

- build candidates from native frame/draft/self-check
- rank internally with inspectable metadata
- do not replace live output
- do not call models/advisors/search
- do not execute tools/solvers

### Phase 3 — demote one narrow canned helper path in shadow mode

- choose one low-risk deterministic topic helper
- compare unified shadow candidate against existing output
- keep existing live output final

### Phase 4 — owner-approved narrow live slice

- only after shadow evidence, tests, release gate, and explicit approval
- narrow category only
- reversible
- metadata-rich

### Phase 5 — voice uses same response path later

- voice must be rendering only
- no separate voice cognition
- no separate voice memory or relationship model

## 13. Blocked Work

Blocked until separate approval:

- live runtime replacement
- ranked response live wiring
- chat responder broad rewrite
- voice wiring
- model/advisor calls
- scoring/benchmark/certification
- solver arbitration
- official consciousness/IQ claims
- source registry authority
- memory persistence changes
- raw private text persistence
- `.weslr` runtime state creation

## 14. Anti-Drift Rule

Any future change that adds another detached helper loop, deterministic answer script, prompt-specific self/consciousness reply, or runtime response path outside the unified formation doctrine violates this canon unless separately approved by owner review, tests, and release gate.

A future implementation must answer these before merging:

- Does it compose the canonical path instead of bypassing it?
- Does it preserve memory honesty?
- Does it preserve evidence/provenance discipline?
- Does it preserve capability/tool authorization boundaries?
- Does it avoid raw private text storage?
- Does it avoid fake self-awareness or unsupported consciousness claims?
- Does it avoid official IQ/benchmark/certification claims?
- Does it avoid creating a second cognition layer?

## 15. Validation Markers

Required markers for this canon document:

- `input`
- `meaning / intent interpretation`
- `native_frame_kwargs`
- `helper_metadata`
- `relationship and continuity are first-class cognition inputs`
- `Evidence bridge metadata remains separate`
- `Capability hints are not permission grants`
- `Allowed deterministic invariants`
- `Forbidden as core cognition`
- `_frontier_unified_response_formation`
- `Phase 1 — refine reuse helpers`
- `Anti-Drift Rule`

## 16. Non-Authorization Statement

This document does not authorize:

- runtime behavior changes
- chat responder edits
- ranked response runtime
- model calls
- advisor LLM calls
- web/search execution
- solver execution
- answer-selection arbitration
- voice/runtime/UI wiring
- raw private text storage
- `.weslr` state creation
- official IQ/benchmark/certification claims
- fake consciousness/sentience/soul claims
