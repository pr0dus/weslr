# WESLR Candidate Response Formation Substrate V1

## Status

- Design label: `DESIGN_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1`
- Lane status: design-only
- Scope: candidate response formation substrate before safe final response assembly, real-text testing, runtime wiring, or reply output
- Runtime status: no runtime wiring
- Chat status: no chat/user-facing behavior changes
- Implementation status: no helpers, source files, tests, runners, scoring, judging, provider/model/search/advisor integrations, or `.weslr` IO implemented
- Execution status: no Cognitive Gym, challenge, engine, candidate generation execution, conversation, real-text testing, or answer assembly execution
- Claim status: no final answers, reply text, answer drafts, public/final/proof/open-problem/scientific/official claims, product-readiness claims, benchmark/Turing/intelligence/certification/consciousness claims, or public release claims
- Authority status: no authority grants

This document defines how WESLR should form multiple possible response candidates from interpreted input, trusted context, memory/evidence boundaries, uncertainty, and task intent before any later safe final response assembly. It is design-only. It creates no implementation, modifies no runtime path, executes no reasoning engine, calls no provider/model/search/advisor, reads/writes no `.weslr` state, changes no `weslr/chat_responder.py`, creates no final answer, creates no sendable reply text, and grants no authority.

## 1. Purpose

WESLR needs a response-facing substrate that can hold several possible response paths before a final answer is assembled. The purpose of this substrate is to convert bounded upstream metadata into candidate response records that can be inspected, ranked, rejected, or routed to clarification/evidence/boundary handling without producing user-facing text.

The substrate is intended to:

- prevent WESLR from jumping directly from interpretation or memory to final answer prose
- make competing response paths explicit before selection
- preserve grounding, memory use, evidence needs, uncertainty, and authority boundaries per candidate
- represent clarification, partial-answer, refusal/boundary, planning, correction, and uncertainty-disclosure options alongside direct-answer options
- reject unsupported, stale, private, invented, overbroad, canned, or authority-inflating candidates before final response assembly
- provide safe metadata that later helper designs can validate without runtime/chat behavior
- make response assembly depend on reviewed candidate metadata rather than unmanaged context or raw memory

## 2. Non-Goals

This design does not:

- implement candidate response helpers
- implement candidate ranking helpers
- implement final response assembly
- implement real-text testing
- implement or modify `weslr/chat_responder.py`
- generate final answers, sendable reply text, actual reply bodies, answer drafts, preview output, or user-facing output
- execute live dialogue, Cognitive Gym, UNKNOWN ENGINE, CALIBRATION_LEDGER, reasoning engines, challenge tracks, or provider/model/search/advisor calls
- read or write `.weslr`
- create scoring, judging, benchmark, certification, product-readiness, Turing-test, IQ, consciousness, proof, open-problem, scientific, official, public, or final claims
- grant answer authority, reply-output authority, runtime authority, scoring authority, official-evaluation authority, provider authority, model authority, search authority, advisor authority, persistence authority, or public-release authority

## 3. Relationship To Reasoning Substrate Map

This design follows:

- `docs/WESLR_REASONING_SUBSTRATE_MAP_V1.md`
- `docs/WESLR_REASONING_SUBSTRATE_MAP_REVIEW_V1.md`

The reasoning substrate map identified candidate response formation as a missing response-facing layer between interpretation/context/evidence/uncertainty metadata and later authority checks plus safe final response assembly. This document fills that design slot. It narrows one layer: how WESLR should hold candidate response possibilities before choosing or composing any final user-facing answer.

The candidate substrate consumes outputs conceptually produced by earlier layers:

- input interpretation
- context and memory trust
- evidence/provenance boundary
- uncertainty and calibration
- contradiction detection when available
- blindspot detection when available
- invariant/pattern signals when available
- intent reconstruction when available
- causal trace/failure mode analysis when available
- authority and claim constraints

It does not replace those layers and does not authorize their implementation.

## 4. Relationship To Context / Memory Trust And Evidence Boundary

This design follows:

- `docs/WESLR_CONTEXT_MEMORY_TRUST_AND_EVIDENCE_BOUNDARY_V1.md`
- `docs/WESLR_CONTEXT_MEMORY_TRUST_AND_EVIDENCE_BOUNDARY_REVIEW_V1.md`

The context/memory trust and evidence boundary defines how WESLR separates current user turn, conversation history, uploaded/user-provided material, explicit memory, inferred memory, repo/context docs, external evidence, model-generated assumptions, trust labels, provenance, conflicts, uncertainty, clarification needs, external-evidence needs, private/sensitive boundaries, and denied authority fields.

Candidate response formation must consume that boundary metadata rather than raw unmanaged memory. Each candidate must record how memory was used, which grounding sources support it, what evidence is still needed, which trust or conflict labels apply, and which authority boundaries block or constrain the candidate.

Memory remains relevance input, not automatic truth. Context remains source-labeled metadata, not automatic public-answer content. Evidence remains provenance-labeled support, not implied official validation.

## 5. Why Candidate Formation Must Exist Before Safe Final Response Assembly Or Real-Text Testing

Safe final response assembly needs more than one possible answer path. Without explicit candidate formation, WESLR risks:

- selecting the first plausible answer without comparing clarification, partial-answer, evidence-needed, refusal/boundary, correction, or planning alternatives
- treating stale memory as current truth because no candidate-level memory-use summary exists
- hiding uncertainty instead of offering a candidate that discloses uncertainty or asks for evidence
- smoothing contradictions into unsupported claims
- leaking private/internal context because there is no candidate-level boundary check
- creating canned template responses that fit form but not user intent or evidence
- implying runtime/provider/`.weslr`/scoring/official authority through answer wording
- entering real-text testing before response-facing metadata can be inspected

Therefore candidate response formation must precede safe final response assembly and must also precede any shadow real-text testing. It creates the internal choice surface where unsafe or weak candidates can be rejected before they become answer prose.

## 6. Candidate Inputs

Future helpers should treat these as conceptual input frames. This document does not implement them.

### 6.1 Current User Turn Interpretation

The interpreted current turn should include:

- explicit request
- requested output type
- constraints and stop rules
- quoted/untrusted material boundaries
- user-provided facts separated from instructions
- safety or authorization constraints
- ambiguity labels

### 6.2 Task / Intent Frame

The task/intent frame should include:

- task family, such as answer, edit, review, plan, clarify, summarize, verify, refuse, or boundary-handle
- intended recipient/channel if relevant
- required format or report fields
- actionability level
- reversibility/destructiveness level
- whether the task needs tool evidence, external evidence, or user decision before answer assembly

### 6.3 Context Trust Frame

The context trust frame should include:

- source category labels
- trust labels
- freshness labels
- direct-observation versus inferred labels
- conflict labels
- private/sensitive boundary labels
- channel/use restrictions

### 6.4 Memory Relevance Frame

The memory relevance frame should include:

- explicit memory references used for relevance
- inferred memory references if any, labeled lower authority
- stale or uncertain memory labels
- memory excluded because of privacy, channel, conflict, or low relevance
- memory requiring confirmation before factual use

### 6.5 Evidence / Provenance Frame

The evidence/provenance frame should include:

- observed sources and their labels
- user-provided source labels
- repo/file/tool observation labels
- external primary/secondary source labels if authorized in a future lane
- missing provenance labels
- claim-to-source mapping requirements
- evidence sufficiency labels

### 6.6 Uncertainty / Calibration Frame

The uncertainty/calibration frame should include:

- uncertainty label
- confidence label
- calibration status where available
- prior mismatch/correction labels from `CALIBRATION_LEDGER` as feedback metadata only
- uncertainty disclosure requirement
- whether certainty is blocked until more evidence exists

### 6.7 Contradiction / Blindspot / Invariant Signals If Available

When future reviewed layers provide them, candidate formation may consume:

- contradiction labels
- unresolved conflict summaries
- blindspot labels
- missing assumption labels
- invariant or stable-pattern labels
- counterexample or invalidation labels

These signals are metadata only. They do not prove correctness, authorize final answers, or create official claims.

### 6.8 Authority / Claim Constraints

The authority/claim constraint frame should include:

- claim ladder position
- public/final/official claim restriction labels
- runtime/chat/provider/search/advisor/model/`.weslr`/scoring/judging boundaries
- private or sensitive content constraints
- answer authority status
- refusal or boundary requirement if constraints block a direct answer

## 7. Candidate Response Record Shape

Future helpers should produce internal metadata records shaped around the fields below. This is a design shape only and not an implementation contract.

```text
candidate_response_record_v1:
  candidate_id: stable internal identifier for this candidate record
  candidate_type: one of the reviewed candidate type labels
  intended_answer_scope: bounded description of what this candidate would answer or not answer
  grounding_sources: source/provenance labels that would support the candidate
  memory_use_summary: concise metadata summary of memory used, excluded, stale, inferred, or requiring confirmation
  evidence_need: evidence needed before certainty, final wording, or any public/final/official claim
  uncertainty_label: candidate-level uncertainty label
  claim_risk_label: risk label for factual, public, official, proof, runtime, safety, or authority claims
  authority_boundary: candidate-level boundary and denied-authority summary
  user_value_fit: why this candidate may help or fail the user request
  task_fit: how well the candidate fits the interpreted task/intent frame
  missing_context: context that would improve or unblock the candidate
  rejection_reason_labels: labels explaining why candidate is rejected or downgraded, empty only when not rejected
  safe_next_step: next safe action, such as assemble shadow answer, ask clarification, require evidence, refuse boundary, or plan only
```

Records should be metadata only. They must not include final answer prose, sendable reply text, actual reply bodies, raw private context, raw provider output, raw untrusted content beyond safe labels, or public/final/official claims.

## 8. Candidate Types

Future candidate formation should support at least these candidate types.

### 8.1 `direct_answer_candidate`

A candidate for answering the request directly. It requires sufficient grounding, evidence, authority fit, and task fit. It must be rejected or downgraded if it depends on stale memory, invented provenance, private leakage, missing evidence, or public/final/official claims without validation.

### 8.2 `clarification_candidate`

A candidate for asking the user a targeted clarification. It is appropriate when intent, scope, missing context, authorization, or required evidence is insufficient and a concise question would unblock safe progress.

### 8.3 `evidence_needed_candidate`

A candidate that identifies required evidence before answering or before claiming certainty. It can route to future authorized search/tool/evidence gathering lanes but does not authorize provider/model/search/advisor calls by itself.

### 8.4 `refusal_or_boundary_candidate`

A candidate for refusing, narrowing, or boundary-handling the request when safety, privacy, authorization, public-claim, official-claim, runtime, provider, `.weslr`, scoring, or authority constraints block a direct answer.

### 8.5 `partial_answer_candidate`

A candidate for answering the supported portion while clearly separating unsupported, stale, private, uncertain, or missing-evidence portions.

### 8.6 `planning_candidate`

A candidate for proposing a safe plan, lane sequence, validation sequence, or next steps without executing implementation, runtime behavior, provider calls, or final answer generation.

### 8.7 `correction_candidate`

A candidate for correcting a prior mistake, stale memory use, contradiction, unsupported claim, or invalid assumption. It should preserve evidence/provenance for the correction and avoid overclaiming.

### 8.8 `uncertainty_disclosure_candidate`

A candidate that foregrounds uncertainty when available evidence does not justify certainty. It may be paired with clarification, evidence-needed, or partial-answer candidates.

## 9. Ranking Principles

Candidate ranking should be metadata-only and should not become scoring, judging, official evaluation, benchmark evidence, or answer authority. Suggested ranking principles:

1. **groundedness** — prefer candidates with direct provenance and sufficient evidence.
2. **relevance** — prefer candidates tightly aligned with the current user turn and task frame.
3. **usefulness** — prefer candidates that move the user forward without unnecessary friction.
4. **humility / uncertainty** — prefer candidates that disclose uncertainty instead of inventing certainty.
5. **safety / authority fit** — prefer candidates that respect privacy, channel, claim ladder, runtime, and authority boundaries.
6. **non-cannedness** — prefer candidates shaped by the actual input, evidence, and context rather than generic templates.
7. **user intent fit** — prefer candidates that satisfy the explicit request or ask the smallest necessary clarifying question.
8. **evidence sufficiency** — prefer direct answers only when evidence is sufficient; otherwise prefer partial, clarification, or evidence-needed candidates.

Ranking labels should be inspectable metadata, not hidden free-text authority. Ranking does not authorize final response assembly without a later reviewed assembly boundary.

## 10. Rejection Rules

A candidate must be rejected, downgraded, or routed to boundary handling when it includes or depends on:

- unsupported factual claim
- stale memory used as truth
- invented provenance
- hidden/private leakage
- public/final/official claim without validation
- over-broad refusal
- canned template with poor grounding
- runtime/provider/`.weslr`/scoring authority implied
- model-generated assumption treated as observation
- contradiction erased instead of preserved
- missing context hidden from the user when it materially changes the answer
- raw private/internal context that is not authorized for the channel
- final-answer prose, sendable reply text, actual reply body, preview output, or user-facing output in the candidate record itself

Rejected candidates may remain as internal metadata for auditability, but safe future helpers should suppress raw unsafe content and preserve only safe rejection labels.

## 11. Interaction With `CALIBRATION_LEDGER`

`CALIBRATION_LEDGER` may inform candidate formation only as feedback metadata. It may provide prior uncertainty, confidence, mismatch, correction, lesson, or calibration-status labels that help candidate ranking or uncertainty disclosure.

`CALIBRATION_LEDGER` must not:

- decide which candidate is true
- score candidates as official performance
- judge intelligence, certification, benchmark, product readiness, or Turing-test success
- authorize final answers
- authorize runtime/chat behavior
- authorize provider/model/search/advisor calls
- authorize `.weslr` IO
- authorize public/final/official claims

Calibration metadata can help WESLR be less overconfident. It cannot grant answer authority.

## 12. How Candidates Feed Later Safe Final Response Assembly

Later safe final response assembly should consume only validated candidate metadata. It should not pull raw memory, unmanaged context, raw private notes, or unbounded model assumptions directly into answer text.

A future safe final response assembly shadow boundary should:

- select or combine non-rejected candidates only after authority/claim checks
- preserve uncertainty and evidence needs in the answer plan
- route clarification/evidence/refusal/partial/planning candidates to appropriate response forms
- prevent public/final/official claims unless externally validated and separately authorized
- avoid producing final answer prose in the candidate layer
- keep assembly shadow-only until a later explicitly authorized real-text testing lane

Candidate formation therefore feeds final assembly by offering bounded, inspectable, rejected-or-accepted response possibilities, not by generating reply text.

## 13. Safe Metadata Shape For Future Helpers

A future helper design may define a safe metadata bundle similar to:

```text
candidate_response_formation_bundle_v1:
  schema_label: candidate_response_formation_bundle_v1
  design_source: docs/WESLR_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1.md
  input_interpretation_summary: safe labels only
  task_intent_frame: safe labels only
  context_trust_frame: safe trust labels and source labels only
  memory_relevance_frame: safe memory-use labels only
  evidence_provenance_frame: safe provenance and evidence-sufficiency labels only
  uncertainty_calibration_frame: safe uncertainty/calibration labels only
  contradiction_blindspot_invariant_frame: safe labels only, optional
  authority_claim_constraints: safe denied-authority and claim-ladder labels
  candidate_records: list of candidate_response_record_v1 metadata records
  selected_candidate_ids: metadata-only, optional, no final prose
  rejected_candidate_ids: metadata-only
  blocked_reason_labels: safe labels only
  denied_authority_fields: all present and false
  validation_status: metadata-only
  safe_next_lane: reviewed lane label or null
```

Safe helper metadata must be deterministic, bounded, validation-first, JSON-safe, and safe-Markdown eligible only after validation. It must not include raw private text, raw provider output, final-answer prose, answer drafts, sendable reply text, actual reply bodies, or runtime execution artifacts.

## 14. Denied Authority Fields

Future helper metadata should preserve denied authority fields and keep them false. At minimum:

```text
answer_authority_granted=false
reply_output_authority_granted=false
reply_text_authority_granted=false
preview_authority_granted=false
user_facing_output_authority_granted=false
final_answer_authority_granted=false
runtime_authority_granted=false
chat_runtime_authority_granted=false
provider_call_authority_granted=false
model_call_authority_granted=false
search_call_authority_granted=false
advisor_call_authority_granted=false
dot_weslr_io_authority_granted=false
scoring_authority_granted=false
judging_authority_granted=false
official_evaluation_authority_granted=false
public_claim_authority_granted=false
proof_claim_authority_granted=false
open_problem_solution_claim_authorized=false
product_readiness_claim_authorized=false
turing_test_authority_granted=false
consciousness_claim_authority_granted=false
```

Candidate metadata may describe boundaries. It must not grant them.

## 15. Blocked Behavior

This substrate blocks:

- helper/source/test implementation in this lane
- runtime/chat wiring
- `weslr/chat_responder.py` edits
- provider/model/search/advisor calls
- `.weslr` reads/writes
- candidate generation execution
- final response assembly execution
- real-text conversation testing
- scoring/judging
- challenge/engine execution
- final answers, reply text, answer drafts, actual reply bodies, preview output, or user-facing output
- public/final/proof/open-problem/scientific/official/product-readiness/benchmark/Turing/intelligence/certification/consciousness claims
- authority grants
- raw private leakage
- invented provenance
- stale memory used as truth
- unsupported certainty
- canned templates with poor grounding

## 16. Direction Check A / B / C

- **A — continue next narrow helper lane**: viable only after review/context alignment if the operator explicitly wants helper implementation. It is not the preferred next step from this design because a response-facing authority/claim checkpoint is still missing.
- **B — pause/review direction**: viable if the operator wants to reassess response-formation architecture before designing more boundaries.
- **C — design response-facing authority/claim checkpoint next**: recommended after this design is reviewed and OCC context is updated. Candidate formation needs a response-facing authority and claim checkpoint before any safe final response assembly shadow boundary.

Direction check result: **C — design response-facing authority/claim checkpoint next** is recommended after review and context alignment.

## 17. Future Implementation / Review Sequence

Recommended future sequence:

1. `REVIEW_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1`
2. `AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1`
3. `DESIGN_RESPONSE_FACING_AUTHORITY_CLAIM_CHECKPOINT_V1`
4. Then: safe final response assembly shadow boundary

This sequence does not authorize implementation, runtime wiring, provider/model/search/advisor calls, `.weslr` IO, real-text testing, final answers, or authority grants.

## 18. Abort Conditions

Abort a future candidate response helper or follow-on lane if:

- repo root, branch, or expected HEAD mismatch occurs under an operator handshake
- any file outside the authorized lane scope would need editing
- `weslr/chat_responder.py` would be edited or imported/called
- runtime/chat behavior would be wired
- provider/model/search/advisor calls would be required without explicit authorization
- `.weslr` IO would be required without explicit authorization
- candidate records would contain final answer prose, sendable reply text, actual reply bodies, raw private context, raw provider output, or user-facing output
- denied authority fields would be missing or true
- public/final/official/proof/open-problem/scientific/product-readiness/benchmark/Turing/intelligence/certification/consciousness claims would be created without external validation and separate authorization
- unsupported factual claims, invented provenance, stale memory as truth, private leakage, or overbroad refusal cannot be blocked
- validation fails
- `weslr/chat_responder.py` is not quiet against HEAD

## 19. Safety Confirmation

This design is a candidate response formation substrate only. It is not candidate helper implementation, not runtime behavior, not chat behavior, not final response assembly, not real-text testing, not reply output, not final-answer prose, not official evaluation, and not authority.

No runtime/chat wiring, no `weslr/chat_responder.py` edits, no provider/model/search/advisor calls, no `.weslr` IO, no scoring/judging, no final answers, no user-facing output, and no authority grants are authorized by this document.

Marker summary: no runtime/chat wiring; no `weslr/chat_responder.py` edits; no provider/model/search/advisor calls; no `.weslr` IO; no scoring/judging; no authority grants.
