# WESLR Cognitive Gym Exploratory Case Helpers V1

## Status

- Design label: `DESIGN_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_V1`
- Design status: design-only
- Helper status: shared exploratory case helper design only
- Runtime status: no runtime wiring
- Chat status: no chat/user-facing behavior changes
- Implementation status: no helpers implemented in this lane
- Engine status: no engines implemented and no engine-specific helpers designed
- Execution status: no challenge execution
- Scoring/judging status: no scoring, judging, benchmarks, or official evaluation
- Persistence status: no `.weslr` reads/writes
- Provider/search/advisor status: no provider/model/search/advisor calls
- Claim status: no final answers, proof claims, open-problem solution claims, scientific discovery claims, or official benchmark/Turing/intelligence/certification/consciousness claims
- Authority status: no authority grants

This document designs future shared metadata/validation helpers for Cognitive Gym exploratory case records. It does not implement helpers, create tests, create result artifacts, execute challenges, wire runtime/chat behavior, call providers/models/search/advisors, read/write `.weslr`, or authorize engine-specific helpers.

## 1. Purpose

The shared Cognitive Gym exploratory case helpers should provide one reviewed helper discipline for all future exploratory Cognitive Gym engines before any engine-specific helpers are designed.

The helpers should make the reviewed exploratory case protocol usable in future implementation lanes by defining a deterministic, side-effect-free, in-memory way to:

- build metadata-only exploratory case records
- validate boundary and authority constraints before rendering
- summarize valid or blocked case metadata
- render safe internal Markdown only after validation
- convert case metadata to JSON-safe internal structures
- preserve lifecycle labels without turning them into scores or public claims
- preserve the WESLR claim ladder
- return blocked metadata instead of unsafe output

The purpose is to keep future Cognitive Gym engines aligned to a common CognitiveGymRun-style reporting discipline and prevent disconnected chaotic modules.

## 2. Non-Goals

This design does not:

- implement `weslr/cognitive_gym_exploratory_case.py`
- implement tests
- implement engines
- design engine-specific helpers
- execute challenges
- create runners
- create scoring or judging
- generate final answers
- prove theorems
- make open-problem solution claims
- make scientific discovery claims
- make official benchmark/Turing/intelligence/certification/consciousness claims
- call providers/models/search/advisors
- read or write `.weslr`
- wire runtime/chat behavior
- edit `weslr/chat_responder.py`
- create result artifacts
- authorize public release
- grant authority

## 3. Relationship To Reviewed Protocol

This helper design is downstream of:

- `docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_V1.md`
- `docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_REVIEW_V1.md`
- `docs/WESLR_EXPLORATORY_PROBLEM_WORK_BOUNDARY_V1.md`
- `docs/WESLR_EXPLORATORY_PROBLEM_WORK_BOUNDARY_REVIEW_V1.md`

The reviewed protocol judgment was:

`cognitive_gym_exploratory_case_protocol_design_valid_ready_for_context_alignment`

Future helpers must implement the protocol's shared lifecycle, metadata-only record shape, input/output boundaries, denied-authority posture, validation-before-rendering philosophy, claim-ladder discipline, external validation requirements, and no-runtime/no-chat/no-provider/no-scoring/no-execution authority boundaries.

Helpers must remain shared protocol helpers. They must not become UNKNOWN ENGINE helpers, Erdős helpers, contradiction helpers, counterfactual helpers, or any other engine-specific helper set.

## 4. Future Target Path

Future implementation target, if separately authorized:

- `weslr/cognitive_gym_exploratory_case.py`

Future test target, if separately authorized:

- `weslr/tests/test_cognitive_gym_exploratory_case_v1.py`

These paths are design targets only in this lane. They are not created here.

## 5. Future Public APIs

Future implementation should expose only shared exploratory case helper APIs such as:

- `build_cognitive_gym_exploratory_case_v1(...)`
- `validate_cognitive_gym_exploratory_case_v1(...)`
- `summarize_cognitive_gym_exploratory_case_v1(...)`
- `render_cognitive_gym_exploratory_case_markdown_v1(...)`
- `to_cognitive_gym_exploratory_case_json_safe_v1(...)`

These names are design targets only. No helper API is implemented in this lane.

## 6. Shared Case Shape

A future exploratory case record should remain metadata-only and include fields aligned with the reviewed protocol:

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
- `blocked_reason_labels`

Records are not final answers, proof claims, scientific discovery claims, benchmark reports, public release text, runtime activation payloads, or chat outputs.

## 7. Lifecycle Labels

Future helpers should accept only safe lifecycle labels such as:

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

Lifecycle labels are metadata states only. They are not scores, judge decisions, benchmark states, official readiness claims, public proof states, or public claims.

## 8. Input Boundary Rules

Allowed future inputs should be safe metadata only:

- synthetic metadata
- operator-approved problem metadata
- redacted task descriptors
- abstract assumptions
- safe public-domain problem labels
- non-private structural notes
- bounded internal review notes

Forbidden inputs must include:

- raw private user content unless separately approved
- hidden prompts
- answer keys
- protected benchmark items
- provider/model raw outputs
- secrets/tokens
- personal sensitive data
- copyrighted long-form source dumps
- executable instructions for unsafe actions
- runtime/chat activation instructions
- public-claim text intended for release

Input validation should preserve safe summaries and labels while rejecting raw unsafe content and boundary violations.

## 9. Output Boundary Rules

Allowed helper outputs should be bounded internal metadata:

- validation metadata
- blocked metadata
- metadata summaries
- hypotheses
- uncertainty notes
- invalidation notes
- failed-attempt records
- correction notes
- compressed lessons
- bounded internal review notes
- next safe lane recommendations
- safe internal Markdown summaries after validation
- JSON-safe internal structures

Forbidden helper outputs must include:

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
- chat/user-facing answer text
- authority grants

## 10. Denied Authority Fields

Every future case record must require these fields to be present and false:

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

False denied-authority fields are not placeholders for implicit permission. A future lane must explicitly authorize and review any authority change.

## 11. Validation Rules

`validate_cognitive_gym_exploratory_case_v1` should reject or block:

- missing denied authority fields
- any true denied authority field
- missing `boundary_status`
- missing `validation_status`
- missing uncertainty for exploratory records
- invalid lifecycle labels
- final/proof/solved claims
- official benchmark/Turing/intelligence/certification/consciousness claims
- scoring/judging claims
- runtime/chat activation claims
- provider/model/search/advisor call claims
- persistence/`.weslr` claims
- raw private content indicators
- hidden prompts
- answer keys
- protected benchmark material
- public claim states without external review status
- claim-ladder inconsistency
- speculative hypotheses presented as facts
- automatic runtime promotion or public release pathways

Validation should return structured blocked metadata rather than unsafe output.

Validation pass is not scoring, proof, product readiness, official evaluation, public claim permission, runtime authorization, chat authority, provider-call authority, persistence authority, or engine execution.

## 12. Blocked Metadata Behavior

When validation blocks a case, future helpers should return metadata shaped like:

- `valid: false`
- `blocked: true`
- `blocked_reason_labels: [...]`
- `boundary_status: blocked_by_boundary`
- `validation_status: blocked`
- `safe_summary: <bounded internal explanation>`
- denied authority fields preserved false
- no unsafe content echoed back

Blocked metadata may be summarized internally. It must not become a user answer, final answer, proof, public claim, runtime instruction, benchmark score, or authority grant.

## 13. Safe Markdown Rules

`render_cognitive_gym_exploratory_case_markdown_v1` should:

- require validation first
- render only bounded internal metadata
- include lifecycle, boundary status, validation status, uncertainty, and next safe lane notes
- omit raw private content, hidden prompts, answer keys, protected benchmark material, secrets, provider/model raw outputs, and long copyrighted dumps
- label hypotheses and candidate structures as internal exploratory metadata
- label blocked cases as blocked metadata
- preserve denied authority fields as false
- avoid final-answer prose and public-release language

Safe Markdown is not user-facing answer text and is not a reply payload.

## 14. JSON-Safe Rules

`to_cognitive_gym_exploratory_case_json_safe_v1` should:

- return only JSON-compatible primitives, lists, and dictionaries
- preserve blocked status and denied authority fields
- strip or replace unsupported object types
- avoid raw private content and unsafe source dumps
- preserve uncertainty and validation metadata
- avoid runtime handles, provider handles, file handles, or executable callables

JSON-safe metadata is not a reply payload, runtime payload, public artifact, or authority grant.

## 15. Claim Ladder Preservation

Future helpers must preserve the non-skippable WESLR claim ladder:

1. `internal_observation`
2. `internal_hypothesis`
3. `candidate_structure`
4. `reviewed_candidate`
5. `externally_checked_candidate`
6. `validated_result`
7. `public_claim`

WESLR may not skip levels. Internal observations, hypotheses, and candidate structures are not public claims. Externally checked candidates are not automatically public claims. Public/final/official claims require external validation and separate authorization.

## 16. External Validation Requirement

Future helpers may record `needs_external_review` or `externally_validated` as metadata, but they do not perform external validation and do not authorize public claims.

Any public/final/official claim must require:

- external validation status
- separate authorization
- a reviewed claim-promotion lane
- no claim-ladder skip
- explicit denial of automatic public release

## 17. Import-Safety And Side-Effect Expectations

Future implementation should be:

- deterministic
- import-safe
- side-effect-free
- pure in-memory
- file-system silent unless a future lane explicitly authorizes artifact writing
- no provider/model/search/advisor calls
- no `.weslr` reads/writes
- no runtime/chat wiring
- no `weslr/chat_responder.py` imports or calls
- no feature flags
- no runner/scoring/judging creation

## 18. Future Implementation / Review Sequence

Recommended sequence, each lane separately authorized:

1. `REVIEW_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_V1`
   - Review this helper design only.
2. `AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_V1`
   - Align OCC-facing context if review passes.
3. `IMPLEMENT_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_V1`
   - Implement only shared metadata/validation helpers if separately approved.
4. `REVIEW_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_IMPLEMENTATION_V1`
   - Review helper implementation before use.
5. Design engine-specific helpers only after shared helper implementation is reviewed.

Engine-specific helper design must not precede shared protocol and shared helper discipline.

## 19. Abort Conditions

Future work must abort or block if it:

- implements helpers in this design lane
- designs engine-specific helpers before shared helper review
- creates runtime/chat behavior
- imports or calls `weslr/chat_responder.py`
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

A shared Cognitive Gym exploratory case helper layer should exist before future engine-specific helpers. It should be metadata-only, deterministic, side-effect-free, validation-first, safe-Markdown bounded, JSON-safe, authority-denying, and claim-ladder preserving.

This lane creates only the design document. No helpers are implemented in this lane.
