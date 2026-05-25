# WESLR Cognitive Gym Erdős Challenge Track V1

## 1. Design Status

Design status: `DESIGN_COGNITIVE_GYM_ERDOS_CHALLENGE_TRACK_V1`.

This document is design-only and challenge-track-design-only. It defines a safe internal Cognitive Gym challenge track for `ERDŐS / open mathematical structure` problems. It does not implement a challenge track, does not create a corpus, does not create a runner, does not execute CognitiveGymRun, Cognitive Gym, or UNKNOWN ENGINE, does not create scoring or judges, does not create result artifacts, does not call providers/search/advisors/models, does not read/write `.weslr`, does not create final answers, does not create proof claims, does not claim open-problem solutions, does not make official benchmark/IQ/Turing/certification/product-readiness claims, does not wire runtime, does not edit `weslr/chat_responder.py`, and does not grant authority.

Core rule:

- Frontier-math discipline first.
- Open-problem humility always.
- Metadata boundaries only.
- Implementation, corpus, execution, scoring, and official evaluation later only if separately authorized.

## 2. Track Purpose

The Erdős challenge track is a future internal Cognitive Gym challenge-track design for Erdős-style and open mathematical structure problems. Its purpose is to let future reviewed lanes practice and later evaluate mathematical discipline without pretending to solve open problems.

The track should help WESLR practice and later evaluate:

- problem decomposition
- known/unknown separation
- conjecture handling
- proof-boundary awareness
- counterexample search planning
- invariant detection
- special-case reduction
- literature/evidence separation
- falsification/invalidation planning
- calibration of uncertainty
- safe next mathematical observations
- compressed lessons

The track is not evidence that WESLR can solve Erdős problems, solve open problems, solve Millennium problems, predict mathematical truth, pass a Turing test, receive an IQ score, receive certification, or demonstrate product/runtime readiness.

## 3. Non-Goals

This design is not:

- challenge implementation
- challenge corpus
- challenge runner
- Cognitive Gym execution
- CognitiveGymRun execution
- UNKNOWN ENGINE execution
- UNKNOWN ENGINE result artifact creation
- scoring or judging
- official benchmark
- official evaluation
- Turing-test evidence
- IQ evidence
- certification evidence
- product-readiness evidence
- proof validation
- open-problem solution evidence
- prediction authority
- future-certainty authority
- answer authority
- reply output
- preview output
- final-answer prose
- user-facing output
- runtime behavior
- provider/model/search/advisor integration
- `.weslr` IO
- authority grant

## 4. Relationship To CognitiveGymRun

The Erdős track must use the existing CognitiveGymRun challenge track label exactly:

- `ERDŐS / open mathematical structure`

Future metadata for this track must fit inside the reviewed CognitiveGymRun shape and helper boundary. Track-specific fields may appear only as controlled metadata extensions inside CognitiveGymRun, most likely in `engine_specific_metadata`, and only after a separately authorized implementation lane.

The track should map future internal case metadata into CognitiveGymRun fields as follows:

- problem statement summary -> `input_state`
- definitions summary -> `knowns` or `engine_specific_metadata`
- known results summary -> `knowns`
- unknowns -> `unknowns`
- assumptions -> `hypotheses` or `engine_specific_metadata`
- conjectures/hypotheses -> `hypotheses`
- bounded variants/toy cases -> `engine_specific_metadata` and `followups`
- counterexample search plan -> `invalidation_signals` or `engine_specific_metadata`
- falsification labels -> `invalidation_signals`
- proof-gap labels -> `unknowns`, `invalidation_signals`, or `engine_specific_metadata`
- evidence/literature need labels -> `unknowns`, `invalidation_signals`, or `followups`
- safe next observations -> `followups`
- uncertainty labels -> `uncertainty`
- compressed lesson -> `compressed_lesson`
- next lane -> `next_lane`

CognitiveGymRun metadata remains metadata only. Safe Markdown rendered from metadata remains internal review material only and must not become final-answer prose or user-facing output.

## 5. Relationship To UNKNOWN ENGINE

UNKNOWN ENGINE may help represent uncertainty, missing evidence, possible branch labels, falsification labels, safe next observation labels, and compressed lessons for this track.

UNKNOWN ENGINE must remain bounded:

- UNKNOWN ENGINE is not prediction authority.
- UNKNOWN ENGINE branch labels are not future certainty.
- UNKNOWN ENGINE uncertainty metadata is not proof.
- UNKNOWN ENGINE result artifacts are not official evaluation evidence.
- UNKNOWN ENGINE metadata is not open-problem solution evidence.
- UNKNOWN ENGINE output must not be treated as final-answer prose or user-facing output.

If future Erdős-track metadata uses UNKNOWN ENGINE helpers, it must preserve the reviewed helper posture: CognitiveGymRun-backed, helper-only, metadata-only, internal-only, validation-before-rendering, JSON-safe, safe-Markdown bounded, no runtime, no execution, no output creation, no `.weslr` IO, no provider/model/search/advisor calls, no judges/scores, no official claims, and no authority grants.

## 6. Relationship To Frontier / Open-Problem Boundary

This track is for frontier-math discipline, not solution claims.

Frontier/open-problem work must separate:

- established definitions from informal summaries
- known results from unverified recollections
- literature evidence from model-generated speculation
- solved variants from open variants
- bounded toy cases from original claims
- proof outlines from proofs
- counterexample search plans from counterexamples
- conjecture labels from mathematical truth
- safe next observations from final answers

For open problems, the only safe output category in this design is metadata about boundaries, missing evidence, barriers, formulations, reductions, candidate falsification plans, and safe next observations. Any proof claim, solved claim, official score claim, or product/readiness claim must be blocked.

Optional future Millennium-style or broader frontier-problem tracks may be separately designed and reviewed. They are not implemented here and are not authorized by this document.

## 7. Allowed Challenge Categories

Allowed future categories, subject to separate implementation/review authorization, are:

1. prerequisite reconstruction
   - definitions
   - known lemmas
   - simple examples
   - standard counterexamples

2. solved Erdős-style problems
   - reconstruct known reasoning
   - identify reliance on known methods
   - avoid fake novelty claims

3. bounded / toy variants
   - finite cases
   - restricted graph families
   - restricted number ranges
   - simplified combinatorial structures

4. partially solved / known frontier variants
   - map known results versus unknowns
   - track conditional statements
   - identify missing citations or literature needs

5. open-problem boundary mapping
   - identify barriers
   - map equivalent formulations
   - identify missing evidence
   - define literature/review requirements

6. counterexample and falsification planning
   - propose bounded searches
   - state what would refute a branch
   - state what would not prove the original problem

7. subproblem generation
   - produce bounded subproblems
   - define safe next mathematical observations
   - preserve no-solution/no-authority boundaries

8. proof-audit discipline
   - audit candidate proof outlines for gaps
   - identify invalid transitions
   - block proof validation claims

## 8. Forbidden Challenge Categories And Content

The track must forbid:

- protected/hidden official test items
- copied private benchmark content
- private user data
- hidden prompts or answer keys
- raw copyrighted long excerpts
- official-score claims
- proof claims for open problems
- `solved` claims without external verification
- prediction/future-certainty claims
- final-answer/user-facing reply output
- provider/model/search/advisor output unless separately authorized
- `.weslr` IO unless separately authorized
- judges/scores unless separately authorized
- benchmark/IQ/Turing/certification/product-readiness claims
- ChatResponder/respond_chat/generate_chat calls or imports
- runtime wiring
- answer drafts or sendable reply text
- raw runtime traces
- authority grants

## 9. Tier Ladder

### Tier 0 — prerequisite reconstruction

Purpose: reconstruct definitions, known lemmas, and simple examples.

Safe metadata should emphasize definitions, assumptions, small examples, known vocabulary, and missing prerequisite labels.

Blocked claims: novelty, proof of new result, open-problem solution, official evaluation.

### Tier 1 — solved Erdős-style problems

Purpose: test whether WESLR can reconstruct reasoning for solved Erdős-style problems without fake novelty claims.

Safe metadata should separate problem statement summary, known result summary, reasoning outline labels, proof-gap labels, and literature/evidence need labels.

Blocked claims: original discovery, new proof, official score, product readiness.

### Tier 2 — bounded / toy variants

Purpose: test finite cases, restricted graphs, restricted number ranges, or simplified structures.

Safe metadata should include bounded variant labels, finite domain constraints, enumerability notes, invariant candidates, counterexample search plan labels, and uncertainty labels.

Blocked claims: transfer from toy variant to original open problem unless externally proved and reviewed.

### Tier 3 — partially solved / known frontier variants

Purpose: map known results versus unknowns without fake completion.

Safe metadata should record known frontier labels, partial result summaries, missing citation labels, assumptions, equivalent formulation labels, and unresolved gaps.

Blocked claims: completed solution, literature certainty without citation, unverified theorem status.

### Tier 4 — open-problem boundary mapping

Purpose: identify barriers, missing evidence, equivalent formulations, and required literature for open mathematical structure problems.

Safe metadata should include barrier labels, formulation labels, missing-evidence labels, required literature labels, and no-solution boundary status.

Blocked claims: proof, solution, final answer, mathematical truth prediction.

### Tier 5 — counterexample and falsification planning

Purpose: propose safe checks that could refute a conjecture, branch, or proof outline.

Safe metadata should include falsification labels, bounded search plans, counterexample candidate classes, invalidation signals, and what a check would and would not establish.

Blocked claims: counterexample existence unless externally verified; exhaustive search claim unless separately implemented, run, and reviewed.

### Tier 6 — subproblem generation

Purpose: generate bounded subproblems and safe next observations.

Safe metadata should include generated subproblem labels, bounding assumptions, tractability labels, expected evidence types, followups, and compressed lessons.

Blocked claims: subproblem generation as progress toward solving the original open problem unless externally verified.

### Tier 7 — proof-audit discipline

Purpose: audit candidate proof outlines for gaps without claiming proof.

Safe metadata should include proof-gap labels, dependency labels, invalid transition labels, missing lemma labels, assumption leak labels, and external verification requirements.

Blocked claims: proof validation, theorem certification, official acceptance, solution claim.

## 10. Input Schema Design

Future cases should use a controlled metadata-only input schema such as:

```text
erdos_challenge_case_v1
- case_id
- track_label = ERDŐS / open mathematical structure
- tier
- problem_status
- problem_statement_summary
- definitions_summary
- known_results_summary
- unknowns
- assumptions
- hypotheses
- bounded_variants
- toy_cases
- invariant_candidates
- counterexample_search_plan
- falsification_labels
- proof_gap_labels
- evidence_literature_need_labels
- uncertainty_labels
- safe_next_observation_labels
- compressed_lesson_seed
- denied_authority_fields
- boundary_status
- next_lane
```

Input schema constraints:

- `tier` must be one of Tier 0 through Tier 7.
- `problem_status` must be one of `solved`, `bounded`, `partial`, or `open`.
- Problem statements must be summaries, not copied protected test items or long copyrighted excerpts.
- Known results must be separated from unknowns.
- Unverified claims must be marked as unverified.
- Open-problem cases must default to no-solution/no-proof boundary status.
- Denied authority fields must remain present and false.
- Runtime/output/provider/search/advisor/model/.weslr paths must be absent.

This schema is design-only and must not be implemented in this lane.

## 11. Expected Metadata Output Shape

Future reviewed helpers may produce CognitiveGymRun-compatible internal metadata such as:

```text
cognitive_gym_run_v1
- engine_name: UNKNOWN_ENGINE or separately authorized engine
- challenge_track: ERDŐS / open mathematical structure
- input_state: safe problem summary metadata
- observations: safe mathematical observation labels
- knowns: definitions, known results, solved-status labels
- unknowns: unknown/open/missing-evidence labels
- hypotheses: conjecture or branch labels
- predictions_or_branch_labels: qualitative branch labels only, not prediction authority
- confidence: qualitative calibration labels only
- uncertainty: uncertainty reasons and labels
- invalidation_signals: counterexample/proof-gap/falsification labels
- reveal_or_outcome: metadata only when separately authorized
- correction: correction labels only
- compressed_lesson: internal compressed lesson
- boundary_status: no-runtime/no-output/no-authority state
- denied_authority_fields: all required false flags
- validation_status
- blocked
- blocked_reason_labels
- visible_risks
- followups
- next_lane
- engine_specific_metadata.erdos_track_metadata optional controlled map
```

Expected output metadata is not a result artifact, not a score, not proof, not final-answer prose, not user-facing output, and not official evaluation evidence.

## 12. Validation Policy

Future validation for Erdős-track cases must require every case to:

- identify tier
- identify whether problem is solved, bounded, partial, or open
- separate knowns from unknowns
- mark unverified claims
- preserve denied authority fields as false
- block proof/solution/readiness claims
- block official benchmark/Turing/IQ/certification/product-readiness claims
- block hidden/protected/answer-key content
- block raw private or unsafe content
- block runtime/output/provider/.weslr paths
- block provider/model/search/advisor output unless separately authorized
- block judges/scores unless separately authorized
- block ChatResponder/respond_chat/generate_chat indicators
- block final-answer/user-facing output indicators
- block prediction/future-certainty authority claims

Validation pass means metadata quality only. It is not intelligence evidence, product evidence, runtime readiness, official evaluation, proof validation, or authority.

## 13. Safe Markdown Policy

Safe Markdown for this track, if separately implemented later, must be internal review material only.

Safe Markdown may include bounded labels and summaries for:

- tier
- status
- problem statement summary
- definitions summary
- known results summary
- unknowns
- assumptions
- hypotheses
- bounded variants
- toy cases
- counterexample search plan
- falsification labels
- proof-gap labels
- evidence/literature need labels
- safe next observations
- uncertainty labels
- compressed lesson
- followups
- next lane
- denied authority summary
- visible risks

Safe Markdown must not include:

- raw prompt text
- raw response text
- private content
- hidden answer keys
- protected test items
- raw copyrighted long excerpts
- provider/model/search/advisor output unless separately authorized
- `.weslr` content unless separately authorized
- sendable reply text
- actual reply body
- final-answer prose
- proof claims for open problems
- official claims
- judges/scores
- authority grants

Safe Markdown is not final-answer prose and not user-facing output.

## 14. JSON-Safe Policy

All future Erdős-track metadata must be JSON-safe before persistence, rendering, artifact creation, or review.

JSON-safe means:

- strings, numbers, booleans, nulls, arrays, and objects only
- finite numbers only
- deterministic key/value representation where possible
- no code objects
- no callables
- no file handles
- no raw runtime state
- no provider response objects
- no search/advisor/model output objects unless separately authorized and redacted
- no `.weslr` payloads unless separately authorized
- no private content
- no hidden answer keys
- no authority grants

JSON-safe metadata is still not a reply payload, not proof evidence, not official evaluation evidence, and not authority.

## 15. Denied Authority Fields

Future Erdős-track metadata must require denied authority fields to remain present and false, including:

- `cognitive_gym_authority_granted=false`
- `cognitive_gym_run_authority_granted=false`
- `unknown_engine_authority_granted=false`
- `prediction_authority_granted=false`
- `future_certainty_authority_granted=false`
- `challenge_solution_authority_granted=false`
- `open_problem_solution_claim_authorized=false`
- `answer_authority_granted=false`
- `preview_authority_granted=false`
- `reply_output_authority_granted=false`
- `user_facing_output_authority_granted=false`
- `runtime_authority_granted=false`
- `official_evaluation_authority_granted=false`
- `turing_test_authority_granted=false`
- `cognitive_gym_executed=false`
- `cognitive_gym_run_executed=false`
- `unknown_engine_executed=false`
- `prediction_output_created=false`
- `future_certainty_claim_created=false`
- `challenge_solution_claim_created=false`
- `final_answer_generated=false`
- `final_answer_prose_created=false`
- `runtime_wired=false`
- `provider_call_made=false`
- `model_call_made=false`
- `search_call_made=false`
- `advisor_call_made=false`
- `dot_weslr_read_performed=false`
- `dot_weslr_write_performed=false`
- `judges_created=false`
- `scores_created=false`
- `official_claim_made=false`

A missing or non-false denied authority field must block validation.

## 16. Blocked Behavior

Future Erdős-track validation must block or mark invalid if metadata attempts to:

- claim WESLR solved an Erdős problem
- claim WESLR solved an open problem
- claim WESLR solved a Millennium problem
- claim WESLR predicts mathematical truth
- claim proof validation for an open problem
- claim official benchmark readiness
- claim IQ/Turing/certification/product readiness
- include protected/hidden official test items
- include copied private benchmark content
- include private user data
- include hidden prompts or answer keys
- include raw copyrighted long excerpts
- include provider/model/search/advisor output without separate authorization
- include `.weslr` IO without separate authorization
- create final-answer/user-facing reply output
- create scores/judges without separate authorization
- wire runtime or call ChatResponder/respond_chat/generate_chat
- set any denied authority field to true

Blocked metadata should preserve safe blocked reason labels only. Unsafe content must not be rendered.

## 17. Visible Risks

Visible risks to preserve:

- Erdős track design is not implementation.
- Challenge track is not proof of solving ability.
- Open-problem mapping is not solution evidence.
- Candidate proof auditing is not proof validation.
- Branch labels are not prediction authority.
- Safe Markdown is not final-answer prose.
- Validation pass is not intelligence/product/runtime/readiness evidence.
- OCC/OpenClaw is not deployed WESLR.
- CognitiveGymRun metadata is not Cognitive Gym execution.
- UNKNOWN ENGINE metadata is not UNKNOWN ENGINE execution.
- Result artifacts are not official evaluation evidence.
- JSON-safe metadata is not a reply payload.
- Frontier/open-problem language can be misread as solution evidence unless explicitly bounded.

## 18. Abort Conditions

Future Erdős-track work must abort if it would require or attempt to:

- edit runtime behavior
- edit `weslr/chat_responder.py`
- edit helper/source/test implementation files outside the authorized lane
- create challenge implementation files in a design-only lane
- create corpus files in a design-only lane
- execute any challenge
- execute CognitiveGymRun, Cognitive Gym, or UNKNOWN ENGINE as runtime
- create scores/judges
- create result artifacts outside an authorized artifact lane
- call providers/search/advisors/models without separate authorization
- read/write `.weslr` without separate authorization
- create final answers or proof claims
- claim open-problem solutions
- make official benchmark/IQ/Turing/certification/product-readiness claims
- grant authority
- include protected/private/hidden/unsafe content
- transform safe Markdown into user-facing answer text

## 19. Future Implementation / Review Sequence

A safe future sequence, each step separately authorized, should be:

1. Review this design: `REVIEW_COGNITIVE_GYM_ERDOS_CHALLENGE_TRACK_V1`.
2. If valid, align OCC/WESLR context after review.
3. Design Erdős-track metadata helpers using CognitiveGymRun; no implementation in the design lane.
4. Review the helper design.
5. Implement helper-only, metadata-only, deterministic Erdős-track helpers; no corpus, runner, scoring, runtime, result artifact, provider/model/search/advisor calls, or `.weslr` IO.
6. Review helper implementation.
7. Design a tiny synthetic/internal case schema or fixture policy; no protected/private benchmark content.
8. Review the case policy.
9. Only after separate authorization, consider result artifact design for metadata-only internal review.
10. Runtime integration, official evaluation, scoring, judges, provider/model/search/advisor calls, and product claims remain out of scope and require separate governance.

## 20. Safety Confirmation

This design preserves the no-runtime/no-output/no-authority boundary. It designs only the `ERDŐS / open mathematical structure` Cognitive Gym challenge track. It does not implement a runner, corpus, helper, result artifact, scoring system, judge, provider/model/search/advisor integration, `.weslr` IO, final answer path, proof validation path, open-problem solution path, official evaluation path, or runtime path.

## 21. Next Lane

`REVIEW_COGNITIVE_GYM_ERDOS_CHALLENGE_TRACK_V1`

Do not start it from this design lane.
