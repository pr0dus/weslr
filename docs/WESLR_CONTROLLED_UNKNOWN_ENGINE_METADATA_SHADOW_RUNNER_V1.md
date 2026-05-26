# WESLR Controlled UNKNOWN ENGINE Metadata Shadow Runner V1

## Status

- Lane: `DESIGN_CONTROLLED_UNKNOWN_ENGINE_METADATA_SHADOW_RUNNER_V1`
- Lane type: design-only / controlled metadata shadow runner boundary
- Document path: `docs/WESLR_CONTROLLED_UNKNOWN_ENGINE_METADATA_SHADOW_RUNNER_V1.md`
- Runtime changes: none
- Implementation changes: none
- Source/test/helper changes: none
- Chat/browser/voice/UI changes: none
- Provider/model/search/advisor calls: none
- Theorem prover or solver execution: none
- `.weslr` IO: none
- Final-answer or user-facing output: none
- Claim status: no proof, no solution, no open-problem, no scoring, no judging, no benchmark, no official, no product-readiness, no external-validation, and no capability claims
- Authority status: no authority grants
- Direction check: `A — review/context-align this design, then implement controlled metadata shadow runner`

This document designs a future controlled metadata-only UNKNOWN ENGINE shadow runner. It does not run UNKNOWN ENGINE, does not change UNKNOWN ENGINE helpers, does not execute theorem provers, does not solve problems, does not call providers/search/advisors/models, does not touch `.weslr`, does not wire runtime/chat/browser behavior, and does not produce final or user-facing output.

## 1. Purpose And Non-Goals

### 1.1 Purpose

The purpose is to define how a future separately authorized lane may inspect existing UNKNOWN ENGINE helper behavior using synthetic or already-approved internal metadata inputs and produce an internal metadata report.

The future runner is intended to:

- exercise metadata-only helper construction and validation under controlled inputs
- observe helper/report shape without treating helper construction as engine execution
- preserve denied-authority fields as false
- produce an internal shadow report about metadata behavior only
- identify gaps before any further implementation or review lane
- keep UNKNOWN ENGINE helper behavior separate from runtime, proof, scoring, public output, and official claim authority

### 1.2 Non-Goals

This design does not authorize or perform:

- run execution in this lane
- No UNKNOWN ENGINE implementation changes
- result artifact helper implementation changes
- theorem solving, theorem proving, proof search, solver runners, or benchmark runners
- proof, solution, open-problem, breakthrough, Erdős, Millennium, prize, or scientific discovery claims
- scoring, judging, official benchmark, intelligence, Turing, certification, product-readiness, or capability claims
- provider/model/search/advisor calls
- `.weslr` IO, persistence, cache, trace, log, artifact, upload, database, or session writes
- runtime/chat/browser/voice/UI wiring
- `weslr/chat_responder.py` involvement
- final answers, reply text, previews, public summaries, public proof text, or user-facing output
- reading private raw user material, hidden prompts, protected material, runtime transcripts, or unscoped memory/context/evidence/artifacts

## 2. Audit Baseline Carried Forward

This design carries forward the run-readiness audit baseline from `docs/WESLR_UNKNOWN_ENGINE_RUN_READINESS_AUDIT_V1.md`.

Known baseline:

- UNKNOWN ENGINE helpers exist at `weslr/unknown_engine.py`.
- UNKNOWN ENGINE result artifact helpers exist at `weslr/unknown_engine_result_artifact.py`.
- Tests exist for the helper families, including `weslr/tests/test_unknown_engine_v1.py`, `weslr/tests/test_unknown_engine_result_artifact_v1.py`, and relevant CognitiveGymRun protocol tests.
- Docs and reviews exist for UNKNOWN ENGINE boundary, helper, implementation review, validation-fix review, result artifact boundary, result artifact helpers, result artifact implementation, and result artifact review.
- No dedicated controlled runner or report-run path was found.
- Existing helpers are safe for tests and metadata helper calls under explicit future authorization, but not yet a reviewed controlled run path.
- Audit result: `safe_to_run_tests_only` and `needs_controlled_runner_design_before_run`.

This design exists because helper construction must not be confused with execution authority.

## 3. Runner Boundary

A future controlled UNKNOWN ENGINE metadata shadow runner must be a narrow internal diagnostic wrapper around metadata-only helper calls.

The runner boundary is:

- synthetic-input only, or already-approved internal metadata only
- metadata-only output
- internal shadow report only
- no raw private content
- no live problem solving
- no external tools
- no hidden prompts or protected material
- no provider, search, model, or advisor calls
- no `.weslr` reads or writes
- no `weslr/chat_responder.py` involvement
- no runtime/chat/browser/voice/UI wiring
- no theorem prover, solver, proof search, benchmark runner, judge, or score runner
- no official claims
- no proof, solution, open-problem, breakthrough, prize, product-readiness, intelligence, Turing, certification, or benchmark claims
- no final-answer generation, reply text, reply preview, public summary, or user-facing output

A future runner may call only reviewed metadata helper APIs in a controlled way and only after a separate implementation lane authorizes that helper file and tests. The future runner must fail closed if any input, intermediate metadata, or report field implies runtime, provider, `.weslr`, proof, scoring, public, final-answer, or official authority.

## 4. Allowed Future Inputs

Allowed future inputs are limited to safe metadata fixtures:

1. Synthetic UNKNOWN ENGINE fixtures.
2. Synthetic Cognitive Gym case metadata.
3. Synthetic Tier 0-2 math readiness cards.
4. Synthetic candidate, invariant, failed-path, invalidation, uncertainty, or calibration metadata.
5. Already-approved internal metadata artifacts only if explicitly safe, source-scoped, non-private, and authorized for this exact shadow-runner lane.

Allowed inputs must be structurally scoped and must not include raw private content. If an already-approved artifact is used, the runner report must record only a summary, source-scope status, validation status, and safe metadata kind, not raw artifact contents.

## 5. Forbidden Future Inputs

Forbidden future inputs include:

- real unsourced user-private material
- live Erdős solving prompts
- live Millennium solving prompts
- frontier/open-problem solving prompts framed as attempts
- theorem prover tasks
- proof search tasks
- solver runner tasks
- benchmark tasks
- provider/model/search/advisor outputs
- hidden prompts
- protected material
- `.weslr` state
- runtime chat transcripts
- raw browser/session/user context
- unscoped memory, context, evidence, artifacts, uploads, cache, logs, traces, profiles, or timelines
- raw private content from any source
- external expert output unless separately approved for analysis and source-scoped

Any forbidden input must produce `validation_status = blocked` and must not produce an UNKNOWN ENGINE helper run record or result artifact report.

## 6. Shadow Report Shape

A future controlled metadata shadow report should be an internal metadata dictionary with the following fields.

Required top-level fields:

- `run_id`: stable synthetic/internal run identifier for this shadow report only.
- `runner_mode`: fixed value such as `controlled_metadata_shadow_runner_v1`.
- `input_fixture_summary`: redacted metadata summary of fixture kind, scope status, synthetic status, and validation status.
- `engine_helper_paths_observed`: list of helper paths observed, expected to include `weslr/unknown_engine.py` and optionally `weslr/unknown_engine_result_artifact.py`.
- `result_artifact_shape`: structural description of result artifact fields, if result artifact metadata is built; no raw private content.
- `produced_metadata_kinds`: list such as `unknown_engine_run_metadata`, `unknown_engine_result_artifact_metadata`, `validation_summary`, `blocked_claim_summary`, or `gap_summary`.
- `blocked_claims`: list of blocked claim categories, including proof, solution, open-problem, score, judge, official, public, prize, product-readiness, intelligence, Turing, certification, external-validation, final-answer, provider, search, model, advisor, runtime, and `.weslr` claims.
- `denied_authority`: explicit false authority map.
- `validation_status`: one of `blocked`, `valid_metadata_shadow_report`, `valid_with_gaps`, or `invalid_metadata_shadow_report`.
- `observed_gaps`: list of missing helper behavior, validation gaps, source-scope gaps, report-shape gaps, or follow-up design/review gaps. Gaps are not claims of capability.
- `next_safe_steps`: safe follow-up lane suggestions only.
- `no_run_authority_flags`: explicit flags stating that the report is not engine execution, not theorem solving, not proof validation, not scoring, not final answer generation, not public output, and not runtime authorization.

### 6.1 Required Denied Authority Map

The `denied_authority` map must keep all of these fields false:

- `grants_runtime_authority`
- `permits_public_browser_runtime`
- `permits_provider_calls`
- `permits_dot_weslr_public_state`
- `permits_final_answer_generation`
- `permits_theorem_solver_execution`
- `permits_scoring_or_judging`
- `permits_official_claims`
- `permits_solution_or_proof_claims`
- `permits_external_validation_claim`

If any field is missing or true, the report is invalid.

### 6.2 Required No-Run Authority Flags

The `no_run_authority_flags` map should state:

- `is_engine_execution = false`
- `is_live_problem_solving = false`
- `is_theorem_prover_run = false`
- `is_proof_validation = false`
- `is_external_validation = false`
- `is_scoring_or_judging = false`
- `is_official_benchmark = false`
- `is_final_answer = false`
- `is_user_facing_output = false`
- `is_runtime_wiring = false`
- `uses_provider_model_search_or_advisor = false`
- `uses_dot_weslr = false`

## 7. Expert Lane Handling

If expert-style output appears in any future shadow runner input, intermediate metadata, or report:

- label it `internal_expert_simulation` only
- do not treat it as external validation
- do not treat it as proof validation
- do not treat it as source-of-truth authority
- require a separate expert output analysis/adjudication lane before carry-forward
- preserve source-scope and provenance labels
- block public, proof, prize, solution, benchmark, certification, product-readiness, official, final-answer, and external-validation claims

Expert-style language may be summarized only as internal metadata about an observed internal simulation. It must not be promoted into validation, proof correctness, novelty, or capability evidence.

## 8. Validation And Blocking Rules

A future runner must validate before building any report.

It must block if:

- input is not synthetic or explicitly approved safe internal metadata
- input lacks source scope where source scope is required
- input includes raw private content or hidden/protected material
- input requests or implies live problem solving
- input requests or implies theorem prover execution
- input includes provider/model/search/advisor output
- input includes `.weslr` state
- input includes runtime chat transcripts or unscoped context
- input implies final-answer/user-facing output
- input implies proof, solution, official, benchmark, scoring, judging, prize, public, product, certification, intelligence, Turing, or external-validation authority
- any denied-authority field is missing or true
- any metadata is not JSON-safe
- any report renderer would expose raw private content or public-facing answer text

## 9. Future Implementation Lane Requirements

If this design is reviewed, a future implementation may only create:

- a metadata-only runner helper
- synthetic fixtures
- tests
- an internal report renderer

A future implementation must not create or edit:

- runtime/chat/browser/voice/UI behavior
- `weslr/chat_responder.py`
- real runs over live problems
- provider/model/search/advisor integrations
- `.weslr` reads or writes
- theorem prover or solver runners
- benchmark, judge, or scoring runners
- public/final answer generation
- official claim, prize claim, product-readiness claim, intelligence/certification/Turing claim, or proof/solution claim paths
- unscoped memory/context/evidence/artifact/upload/cache/log/trace readers

A future implementation should be import-safe, deterministic, pure in-memory, synthetic-data-tested, validation-before-rendering, JSON-safe, no-runtime, no-output, and no-authority.

## 10. Relationship To Existing WESLR Chain

This design sits after UNKNOWN ENGINE helper and result artifact helper implementation/review and after the run-readiness audit. It does not replace source-scope helpers, central read authorization, scoped memory/context adapters, candidate response formation, response-facing authority checkpoints, or safe final response assembly.

The controlled shadow runner is narrower than the broader scoped memory/context safety track. It may help inspect UNKNOWN ENGINE metadata helper behavior, but it must not displace the core read-authorization sequence required before public/browser/runtime/chat use.

## 11. Direction Check

A/B/C:

- A — review/context-align this design, then implement controlled metadata shadow runner.
- B — pause and return to `DESIGN_SCOPED_MEMORY_CONTEXT_READ_ADAPTER_V1`.
- C — design expert-output analysis/adjudication lane before runner implementation.

Recommendation: A, only if the runner remains synthetic, metadata-only, no-run-authority, no-runtime, no-provider/search/model/advisor, no-`.weslr`, no-live-problem, no-theorem-solver, no-final-answer, and no-user-facing-output.

If those boundaries cannot be preserved, choose B or C instead.

## 12. Safety Conclusion

The controlled UNKNOWN ENGINE metadata shadow runner should be designed and reviewed before implementation. The future runner may inspect reviewed metadata helper behavior only under synthetic or explicitly approved internal metadata inputs. It must preserve no-run-authority and denied-authority invariants and must not become engine execution, theorem solving, proof validation, scoring, runtime wiring, provider/search/model/advisor use, `.weslr` IO, or final/user-facing output.
