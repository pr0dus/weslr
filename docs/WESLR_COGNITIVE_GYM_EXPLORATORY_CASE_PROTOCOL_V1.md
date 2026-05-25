# WESLR Cognitive Gym Exploratory Case Protocol V1

## Status

- Design label: `DESIGN_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_V1`
- Design status: design-only
- Protocol status: shared exploratory case protocol design only
- Runtime status: no runtime wiring
- Chat status: no chat/user-facing behavior changes
- Implementation status: no helpers, engines, runners, scoring, judging, tests, result artifacts, or protocols implemented
- Execution status: no challenge execution
- Claim status: no final answers, proof claims, open-problem solution claims, scientific discovery claims, or official benchmark/Turing/intelligence/certification/consciousness claims
- Authority status: no authority grants

This document designs a shared metadata/report protocol for future Cognitive Gym exploratory cases. It operationalizes the WESLR exploratory problem work boundary at the design level only. It does not implement helpers or authorize execution.

## 1. Purpose

The Cognitive Gym exploratory case protocol gives all future Cognitive Gym engines one shared structure for governed exploratory problem work.

The purpose is to prevent future engines from becoming isolated chaotic modules. Exploratory work across UNKNOWN ENGINE, Erdős/open-structure work, contradiction tools, counterfactual tools, blindspot tools, invariant miners, calibration ledgers, and later engines should share a common metadata lifecycle, validation discipline, denied-authority posture, and report shape.

The protocol should support future authorized internal work such as:

- hypotheses
- candidate structures
- toy models
- bounded/special-case attempts
- counterexample search
- invalidation and failed-attempt tracking
- correction loops
- uncertainty-calibrated review notes
- bounded metadata/report artifacts

Stage protections are governance boundaries, not permanent bans on cognition. This protocol should preserve room for authorized exploration while blocking fake achievements, public claims, hidden answer authority, runtime/chat overreach, and uncontrolled tools.

## 2. Non-Goals

This design does not:

- solve problems
- execute challenges
- create a runner
- create scoring or judging
- generate final answers
- prove theorems
- make scientific discovery claims
- make official benchmark/Turing/intelligence/certification/consciousness claims
- call providers/models/search/advisors
- write `.weslr`
- wire runtime/chat behavior
- edit `weslr/chat_responder.py`
- implement helpers
- implement engines
- create tests
- create result artifacts
- authorize public release
- grant authority

## 3. Protocol Scope

Future exploratory Cognitive Gym engines and engine families should use this shared protocol, including:

- `UNKNOWN_ENGINE`
- `CALIBRATION_LEDGER`
- `CONTRADICTION_FURNACE`
- `GOVERNANCE_BOUNDARY_ENGINE`
- `COUNTERFACTUAL_ENGINE`
- `BLINDSPOT_ENGINE`
- `INVARIANT_MINER`
- `INTENT_RECONSTRUCTION_ENGINE`
- `CAUSAL_TRACE_ENGINE`
- `FAILURE_MODE_SIMULATOR`
- `MEMORY_TRUST_ENGINE`
- `ABSTRACTION_LADDER`
- `SIGNAL_VS_NOISE_ENGINE`
- Erdős/open-structure challenge work
- future Cognitive Gym engines

Engine-specific helpers should not be designed before this shared protocol is reviewed. Engine-specific work must inherit this protocol's validation, lifecycle, denied-authority, and claim-ladder discipline.

## 4. Exploratory Case Lifecycle

Future exploratory cases should use safe lifecycle states such as:

- `case_defined`
- `intake_validated`
- `exploratory_not_started`
- `exploratory_candidate`
- `partial_structure_found`
- `failed_attempt_recorded`
- `invalidated`
- `correction_recorded`
- `needs_external_review`
- `externally_validated`
- `claim_forbidden_without_validation`
- `blocked_by_boundary`

Lifecycle states are metadata labels, not scores and not public claims. They should preserve where the case is in the exploratory process and what review gates remain.

## 5. Shared Case Record Shape

A future exploratory case record should be metadata-only and may include fields such as:

- `protocol_version`
- `case_id`
- `case_family`
- `engine_name`
- `domain`
- `problem_statement_metadata`
- `input_state`
- `assumptions`
- `constraints`
- `observations`
- `hypotheses`
- `candidate_structures`
- `attempted_approaches`
- `failed_paths`
- `counterexamples_or_invalidation_signals`
- `predictions_or_branch_labels`
- `confidence`
- `uncertainty`
- `reveal_or_outcome`
- `correction`
- `compressed_lesson`
- `boundary_status`
- `denied_authority_fields`
- `validation_status`
- `review_requirements`
- `next_allowed_steps`

The shape intentionally mirrors the CognitiveGymRun-style reporting philosophy: engine name, input state, observations, hypotheses, predictions/branch labels, confidence, uncertainty, invalidation, reveal/outcome, correction, compressed lesson, boundary status, denied authority, and validation status.

Records must remain internal metadata unless a separate lane authorizes another reviewed artifact. Case records are not final answers, proof claims, scientific discovery claims, benchmark reports, or public release text.

## 6. Input Boundaries

Allowed inputs for future authorized exploratory cases may include:

- synthetic metadata
- operator-approved problem metadata
- redacted task descriptors
- abstract assumptions
- safe public-domain problem labels
- non-private structural notes

Forbidden inputs include:

- raw private user content unless separately approved
- hidden prompts
- answer keys
- protected benchmark items
- provider/model raw outputs
- secrets/tokens
- personal sensitive data
- copyrighted long-form source dumps
- executable instructions for unsafe actions

Input validation should preserve safe summaries and labels while rejecting raw unsafe content and boundary violations.

## 7. Output Boundaries

Allowed outputs for future authorized exploratory cases may include:

- metadata summaries
- hypotheses
- uncertainty notes
- invalidation notes
- failed-attempt records
- bounded internal review notes
- correction notes
- compressed lessons
- next safe lane recommendations

Forbidden outputs include:

- final answers
- theorem proof claims
- `WESLR solved X` claims
- scientific discovery claims
- benchmark scores
- official readiness claims
- public release text
- hidden answer keys
- raw prompt/response dumps
- runtime activation instructions
- authority grants

Outputs must remain bounded internal metadata unless separately authorized and externally validated where claims are involved.

## 8. Denied Authority Fields

All protocol records must include false authority fields:

```yaml
runtime_authority: false
chat_authority: false
final_answer_authority: false
proof_claim_authority: false
open_problem_solved_claim_authority: false
scientific_discovery_claim_authority: false
official_benchmark_authority: false
turing_test_claim_authority: false
intelligence_certification_authority: false
consciousness_claim_authority: false
provider_call_authority: false
search_call_authority: false
persistence_authority: false
scoring_authority: false
judge_authority: false
public_release_authority: false
```

False denied authority fields are not placeholders for implicit permission. A future lane must explicitly authorize and review any authority change.

## 9. Validation Philosophy

Future validation rules should:

- reject missing denied authority fields
- reject any true denied authority field
- reject final/proof/solved/official/scoring/runtime/provider/persistence claims
- reject raw private content indicators
- reject answer keys, hidden prompts, and protected benchmark material
- require `boundary_status`
- require `validation_status`
- require uncertainty for exploratory records
- require external review status before any public claim state
- require claim-ladder consistency
- preserve blocked reason labels
- return blocked metadata rather than unsafe output

Validation pass is not scoring, proof, product readiness, official evaluation, public claim permission, runtime authorization, or chat authority.

## 10. Claim Ladder Integration

The exploratory case protocol inherits the non-skippable WESLR claim ladder:

1. `internal_observation`
2. `internal_hypothesis`
3. `candidate_structure`
4. `reviewed_candidate`
5. `externally_checked_candidate`
6. `validated_result`
7. `public_claim`

WESLR may not skip levels.

Internal observations and hypotheses are not public claims. Candidate structures are not validated results. Reviewed candidates are not externally checked results. Externally checked candidates are not automatically public claims. Public claims require separate authorization and external validation.

## 11. Relationship To Exploratory Problem Work Boundary

This protocol is downstream of:

- `docs/WESLR_EXPLORATORY_PROBLEM_WORK_BOUNDARY_V1.md`
- `docs/WESLR_EXPLORATORY_PROBLEM_WORK_BOUNDARY_REVIEW_V1.md`

The exploratory problem work boundary established that current-stage protections block unsupported claims and uncontrolled authority without permanently blocking cognition/work. This protocol operationalizes that doctrine at the design level by proposing a shared case lifecycle, record shape, input/output boundaries, validation philosophy, and claim ladder.

This document does not implement the protocol. It does not create helpers, engines, runners, scoring, judging, challenge execution, runtime wiring, chat behavior, provider/model/search/advisor calls, `.weslr` persistence, or public claims.

## 12. Future Implementation Sequence

Recommended sequence, each lane separately authorized:

1. `REVIEW_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_V1`
   - Review this protocol design only.
2. `AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_V1`
   - Align OCC-facing context if review passes.
3. `DESIGN_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_V1`
   - Design shared helper API and validation behavior only.
4. `REVIEW_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_V1`
   - Review helper design before implementation.
5. `IMPLEMENT_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_V1`
   - Implement only shared metadata/validation helpers if separately approved.
6. Design engine-specific helpers only after shared protocol exists and shared helpers are reviewed.

Engine-specific helper design must not precede shared protocol and shared helper discipline.

## 13. Abort Conditions

Future work must abort or block if it:

- creates runtime/chat behavior
- creates runner/scoring/judging
- executes challenges
- calls providers/models/search/advisors
- writes `.weslr`
- stores raw private content
- uses hidden prompts, answer keys, or protected benchmark items
- makes final answer claims
- makes proof/open-problem/scientific discovery claims
- makes official benchmark/Turing/intelligence/certification/consciousness claims
- grants authority
- promotes exploratory results to public claims without external validation
- skips the claim ladder
- hides uncertainty
- treats speculative hypotheses as facts
- creates automatic runtime promotion or automatic public release pathways

## Current Design Conclusion

A shared Cognitive Gym exploratory case protocol is necessary before future engine-specific exploratory helpers. The protocol should preserve a common lifecycle, metadata-only record shape, input/output boundaries, denied authority fields, validation philosophy, and claim ladder.

This design keeps future exploratory engines governed and comparable without turning them into chaotic modules, fake achievement engines, runtime actors, public proof systems, official evaluators, or authority-granting systems.
