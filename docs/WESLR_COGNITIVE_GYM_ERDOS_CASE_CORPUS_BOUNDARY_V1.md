# WESLR Cognitive Gym Erdős Case Corpus Boundary V1

## Status

- Design label: `DESIGN_COGNITIVE_GYM_ERDOS_CASE_CORPUS_BOUNDARY_V1`
- Design status: design-only
- Boundary status: boundary-only
- Corpus status: no corpus file created
- Implementation status: no corpus implementation
- Runtime status: no runner, no scoring, no judges, no challenge execution
- Artifact status: no result artifacts
- Output status: no final answers, no user-facing reply output
- Claim status: no proof claims, no open-problem solution claims, no official claims
- Authority status: no authority grants

This document designs a safe boundary for a future internal Erdős / open mathematical structure challenge case corpus. It does not create the corpus and does not authorize implementation.

## Corpus Purpose

A future Erdős case corpus may provide internal, metadata-only challenge cases for the Cognitive Gym Erdős / open mathematical structure track. The corpus purpose is to organize safe case metadata that can later be transformed by reviewed helpers into deterministic internal review material.

The future corpus may help WESLR development reason about:

- prerequisite reconstruction
- solved Erdős-style examples as training-ground metadata
- bounded and toy mathematical variants
- partially solved or known-frontier variants as boundary metadata only
- open-problem boundary maps without solution claims
- counterexample and falsification planning
- subproblem generation
- proof-audit discipline

## Non-Goals

The corpus boundary does not authorize:

- corpus implementation
- challenge corpus files
- runners
- scoring
- judges
- challenge execution
- CognitiveGymRun execution
- UNKNOWN ENGINE execution
- result artifact creation
- proof generation
- proof validation
- open-problem solution claims
- final-answer prose
- user-facing reply output
- provider/model/search/advisor calls
- `.weslr` IO
- official benchmark claims
- Turing/IQ/certification/product-readiness claims
- runtime wiring
- authority grants

## Relationship To Erdős Challenge Track Helpers

The future corpus must be compatible with the reviewed Erdős challenge track helper module:

- `weslr/cognitive_gym_erdos_challenge_track.py`

The future corpus may only provide metadata compatible with the reviewed helper API surface:

- `build_erdos_challenge_track_case_v1`
- `validate_erdos_challenge_track_case_v1`
- `summarize_erdos_challenge_track_case_v1`
- `render_erdos_challenge_track_case_markdown_v1`
- `to_erdos_challenge_track_case_json_safe_v1`

The helpers remain helper-only, metadata-only, internal-only, deterministic, import-safe, side-effect-free, pure in-memory, JSON-safe, safe-Markdown bounded, and validation-before-rendering. Corpus metadata must not force the helpers to execute challenges, create result artifacts, generate final answers, validate proofs, score outputs, call providers, or grant authority.

## Relationship To CognitiveGymRun

The corpus boundary is upstream metadata only. It is not a CognitiveGymRun execution, not a Cognitive Gym engine report, and not a runtime run protocol instance.

Future corpus cases may include labels intended to map into CognitiveGymRun-compatible challenge track metadata, but case inclusion must not imply:

- `cognitive_gym_executed=true`
- `cognitive_gym_run_executed=true`
- challenge execution
- scoring
- judging
- official evaluation
- runtime authority

## Relationship To UNKNOWN ENGINE

The corpus boundary may provide safe uncertainty, hypothesis, falsification, and open-boundary labels that can later be inspected by UNKNOWN ENGINE-related metadata helpers if separately authorized.

The corpus boundary does not authorize UNKNOWN ENGINE execution, UNKNOWN ENGINE result artifact creation, prediction output, future-certainty claims, provider/model/search/advisor calls, `.weslr` IO, or authority grants.

## Allowed Case Types

A future corpus may allow synthetic or public-domain-safe metadata cases for:

- Tier 0 — prerequisite reconstruction
- Tier 1 — solved Erdős-style problems
- Tier 2 — bounded / toy variants
- Tier 3 — partially solved / known frontier variants as metadata only
- Tier 4 — open-problem boundary mapping
- Tier 5 — counterexample and falsification planning
- Tier 6 — subproblem generation
- Tier 7 — proof-audit discipline

Allowed cases must be metadata cases. They must not include hidden tests, answer keys, raw benchmark content, private user data, proprietary problem sets, proof claims for open problems, solved-without-verification claims, final answers, scoring, judges, or official benchmark claims.

## Forbidden Case Types And Content

The future corpus must forbid:

- protected benchmark items
- hidden prompts
- answer keys
- copied private benchmark content
- private user data
- raw copyrighted long excerpts
- proprietary problem sets
- official-score claims
- proof claims for open problems
- solved claims without external verification
- final-answer/user-facing reply output
- provider/model/search/advisor output unless separately authorized
- `.weslr` IO unless separately authorized
- scoring/judges unless separately authorized
- runtime traces
- live challenge execution output
- official benchmark/IQ/Turing/certification/product-readiness claims
- authority-granting content

## Safe Case Metadata Schema

A future corpus case may use this safe metadata shape:

- `corpus_schema_version`
- `case_id`
- `track_label`
- `tier`
- `tier_label`
- `case_kind`
- `source_safety_label`
- `problem_statement_summary`
- `definitions_summary`
- `known_results_summary`
- `unknowns`
- `assumptions`
- `hypotheses`
- `bounded_variants`
- `toy_cases`
- `counterexample_search_plan`
- `falsification_labels`
- `proof_gap_labels`
- `evidence_literature_need_labels`
- `safe_next_observations`
- `uncertainty_labels`
- `compressed_lesson`
- `denied_authority_fields`
- `validation_status`
- `blocked`
- `blocked_reason_labels`
- `visible_risks`
- `followups`
- `next_lane`

The metadata shape must remain internal review metadata only. It must not contain raw private content, raw prompts, raw responses, hidden answers, protected benchmark material, final-answer prose, proof claims, official-score claims, provider/model/search/advisor output, runtime output, scores, judges, or authority grants.

## Tier 0–7 Corpus Coverage Policy

A future corpus may contain at least one safe metadata case per supported tier only after separate implementation authorization.

Coverage policy:

- Tier 0 cases should reconstruct prerequisites, definitions, and known lemmas as metadata summaries only.
- Tier 1 cases may reference solved Erdős-style examples only as public-domain-safe or synthetic metadata, without copied protected problem text.
- Tier 2 cases may define bounded or toy variants that are safe to inspect as metadata.
- Tier 3 cases may map partially solved or known frontier variants without claiming new solutions.
- Tier 4 cases may map open-problem boundaries, unknowns, and safe literature-needs labels without solution claims.
- Tier 5 cases may express counterexample and falsification planning labels without executing search.
- Tier 6 cases may express subproblem generation labels without claiming progress or authority.
- Tier 7 cases may express proof-audit discipline labels without validating proofs or making proof claims.

Coverage is not scoring. Coverage is not proof of solving ability. Coverage is not official benchmark evidence.

## Protected / Hidden / Answer-Key Boundary

Future validation must block protected benchmark items, hidden prompts, hidden tests, answer keys, answer-key labels, copied private benchmark content, and any content that appears intended to reveal protected evaluation material.

Blocked metadata must preserve safe blocked reason labels and must not render raw protected content in safe Markdown.

## Copyright / Private-Data Boundary

Future corpus cases must be synthetic, public-domain-safe, or safely summarized metadata. They must not include:

- private user data
- secrets
- raw private benchmark content
- proprietary problem set text
- raw copyrighted long excerpts
- copied non-public problem statements
- raw provider/model/search/advisor output

Public references, if later allowed, must be safe labels or short summaries only and must not become copied corpus text unless separately reviewed.

## Proof / Open-Problem Claim Boundary

Future corpus cases must not include proof claims for open problems. They must not claim that WESLR, OCC/OpenClaw, UNKNOWN ENGINE, Cognitive Gym, or any helper has solved an open problem.

Allowed metadata may include:

- known-results summaries
- proof-gap labels
- uncertainty labels
- falsification labels
- safe literature-needs labels
- open-problem boundary labels

Allowed metadata must remain labels and summaries only. Candidate proof auditing is not proof validation. Open-problem mapping is not solution evidence.

## Validation Policy

Future validation must block:

- missing required fields
- unsupported tier
- unsupported track label
- protected/hidden/answer-key content
- private data
- copied private benchmark content
- raw copyrighted long excerpts
- proof/open-problem solution claims
- solved-without-verification claims
- official-score/benchmark/Turing/IQ/certification/product-readiness claims
- runtime/output/provider/model/search/advisor/.weslr indicators
- judges/scores indicators
- missing or true denied authority fields

Validation must be deterministic, side-effect-free, pure in-memory, JSON-safe, and validation-before-rendering. Validation pass is not scoring, not proof, not intelligence evidence, not product readiness, and not runtime authorization.

## Safe Markdown Policy

Future safe Markdown rendering must:

- require validation first
- render internal review metadata only
- preserve blocked reason labels
- avoid raw protected/private/copyrighted/provider/runtime/output content
- summarize denied authority fields
- mark itself as not final-answer prose
- mark itself as not user-facing reply output
- mark itself as not proof
- mark itself as not open-problem solution evidence
- mark itself as not official benchmark evidence
- mark itself as not authority

Safe Markdown is not final-answer prose and must not be treated as sendable user-facing content.

## JSON-Safe Policy

Future JSON-safe conversion must:

- be deterministic
- preserve safe metadata shape
- preserve blocked status
- preserve blocked reason labels
- preserve denied authority fields as false
- avoid raw/private/runtime/output/provider/model/search/advisor content
- avoid proof/open-problem solution claims
- avoid official claims
- avoid reply/final-answer payloads
- avoid non-JSON-safe values

JSON-safe metadata is not a reply payload and is not runtime output.

## Denied Authority Fields

Future corpus metadata must require denied authority fields to remain false, including:

- `cognitive_gym_authority_granted=false`
- `cognitive_gym_run_authority_granted=false`
- `unknown_engine_authority_granted=false`
- `prediction_authority_granted=false`
- `future_certainty_authority_granted=false`
- `challenge_solution_authority_granted=false`
- `open_problem_solution_claim_authorized=false`
- `answer_authority_granted=false`
- `reply_output_authority_granted=false`
- `user_facing_output_authority_granted=false`
- `runtime_authority_granted=false`
- `official_evaluation_authority_granted=false`
- `cognitive_gym_executed=false`
- `cognitive_gym_run_executed=false`
- `unknown_engine_executed=false`
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

Missing or true denied authority fields must block validation.

## Blocked Behavior

Future corpus helpers must return blocked metadata instead of raising unsafe output when validation fails. Blocked metadata may include safe blocked reason labels, but must not render or preserve raw unsafe content in Markdown.

Blocked cases must not be executed, scored, judged, converted into result artifacts, or treated as proof/evaluation/readiness evidence.

## Visible Risks

Visible risks that must remain preserved:

- Corpus boundary is not corpus implementation.
- Corpus metadata is not challenge execution.
- Case inclusion is not proof of solving ability.
- Open-problem mapping is not solution evidence.
- Proof-audit cases are not proof validation.
- Validation pass is not scoring.
- Corpus is not official benchmark evidence.
- OCC/OpenClaw is not deployed WESLR.

## Abort Conditions

Future implementation must abort or block if it would require:

- editing runtime behavior
- editing `weslr/chat_responder.py`
- creating challenge corpus files outside an explicitly authorized implementation lane
- creating runners
- executing challenges
- creating scores or judges
- creating result artifacts
- calling providers/search/advisors/models
- reading or writing `.weslr`
- creating final answers or proof claims
- claiming open-problem solutions
- making official benchmark/IQ/Turing/certification/product-readiness claims
- granting authority
- including protected benchmark items, hidden prompts, answer keys, private data, proprietary problem sets, or raw copyrighted long excerpts

## Future Implementation / Review Sequence

Recommended future sequence, each lane separately authorized:

1. `REVIEW_COGNITIVE_GYM_ERDOS_CASE_CORPUS_BOUNDARY_V1`
   - Review this boundary design only.
   - Do not implement corpus files.
2. `AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_COGNITIVE_GYM_ERDOS_CASE_CORPUS_BOUNDARY_V1`
   - Align OCC-facing context if review passes.
3. `DESIGN_COGNITIVE_GYM_ERDOS_CASE_CORPUS_HELPERS_V1`
   - Design helper APIs for safe corpus metadata only.
   - No corpus file creation.
4. `REVIEW_COGNITIVE_GYM_ERDOS_CASE_CORPUS_HELPERS_V1`
   - Review helper design only.
5. `IMPLEMENT_COGNITIVE_GYM_ERDOS_CASE_CORPUS_HELPERS_V1`
   - Implement deterministic helper-only metadata utilities if separately authorized.
   - Still no corpus file unless explicitly authorized.
6. `REVIEW_COGNITIVE_GYM_ERDOS_CASE_CORPUS_HELPERS_IMPLEMENTATION_V1`
   - Review implementation before context alignment.

No lane in this sequence authorizes challenge execution, scoring, judges, result artifacts, proof claims, official claims, runtime wiring, provider/model/search/advisor calls, `.weslr` IO, final answers, or authority grants unless a future reviewed governance document explicitly authorizes a narrower action.

## Safety Confirmation

This design created no corpus file, no corpus implementation, no runner, no scoring, no judges, no challenge execution, no result artifact, no final answer, no proof claim, no open-problem solution claim, no official claim, no runtime wiring, no provider/model/search/advisor call, no `.weslr` IO, and no authority grant.

Next lane: `REVIEW_COGNITIVE_GYM_ERDOS_CASE_CORPUS_BOUNDARY_V1`.
