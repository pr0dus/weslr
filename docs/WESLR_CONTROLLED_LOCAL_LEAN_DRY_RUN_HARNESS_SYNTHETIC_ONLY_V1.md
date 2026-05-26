# WESLR Controlled Local Lean Dry Run Harness Synthetic Only V1

## 1. Status

- Lane name: `DESIGN_CONTROLLED_LOCAL_LEAN_DRY_RUN_HARNESS_SYNTHETIC_ONLY_V1`
- Lane type: design-only
- Implementation changes: none
- Lean install: none
- Lean execution: none
- Theorem prover / solver runner: none
- Proof search: none
- Proof-sketch execution: none
- Compiler feedback capture: none
- Real verifier result capture: none
- Cache creation/read/write: none
- `.weslr` read/write: none
- Rater/critic/Elo execution: none
- Provider/model/search/advisor calls: none
- Runtime/chat/browser wiring: none
- Final-answer generation: none
- Public/proof/intelligence/Turing/certification claims: none
- Authority grant: none

This document is a boundary design only. It creates no harness implementation, no Lean installation, no Lean execution, no theorem prover behavior, no solver behavior, no proof-search behavior, no proof-sketch execution behavior, no compiler feedback capture behavior, no real verifier result capture behavior, no cache behavior, no `.weslr` behavior, no rater/critic/Elo behavior, no provider/model/search/advisor behavior, no runtime/chat/browser behavior, no final-answer behavior, and no claim authority.

## 2. Purpose

`ControlledLocalLeanDryRunHarnessSyntheticOnlyV1` is the boundary design for a future controlled local Lean dry-run harness using only synthetic toy fixtures.

The purpose is to identify what must be true before a later separately authorized implementation can run Lean in a sandboxed, non-public, non-proof-authority, non-runtime path. The future harness, if ever implemented after separate design/review/authorization, would be limited to local synthetic toy fixtures and bounded metadata/result-envelope handling. It would not open proof-search execution, real theorem attempts, open-problem attempts, raw trace retention, provider/model/search/advisor calls, runtime/chat wiring, final-answer generation, or proof/public/intelligence/Turing/certification/product-readiness claims.

## 3. Non-goals

This design explicitly blocks:

- implementing the harness
- installing Lean
- running Lean
- invoking theorem provers or solvers
- creating proof-search loops
- executing proof sketches
- using real Erdős, Millennium, or other open-problem attempts
- using user private theorem content
- capturing real compiler feedback
- creating cache/log/trace files
- reading or writing `.weslr`
- calling providers/models/search/advisors
- ranking/scoring as benchmark or intelligence evidence
- creating final answers
- making proof, public, benchmark, prize, intelligence, Turing, certification, or product-readiness claims

This document does not authorize source ingestion, web/search ingestion, browser access, database access, auth/session changes, filesystem/log/cache/trace ingestion code, runtime/chat/voice/UI behavior, WESLR helper implementation changes, Lean runner changes, solver/prover implementation changes, cache/log/trace implementation changes, or final-answer generation.

## 4. Harness Boundary Overview

Future concept:

`ControlledLocalLeanDryRunHarnessSyntheticOnlyV1`

The future boundary is:

- design-only in this lane
- local-only
- synthetic-only
- toy-fixture-only
- sandbox-scoped
- no-network
- no-provider
- no-runtime
- no-final-answer
- raw-output-limited
- source-scoped
- freshness-labeled
- fail-closed
- authority-denying by default

It must not contain raw compiler output, raw verifier output, raw goal state, raw error text, raw traces, raw proof text, raw theorem source content, private user theorem content, private context, artifact/upload content, cache/log/trace content, provider/model/search/advisor output, rater/critic output, runtime reply text, final-answer text, public claim text, benchmark evidence, intelligence evidence, Turing evidence, certification evidence, or product-readiness evidence.

## 5. Required Top-Level Fields

`ControlledLocalLeanDryRunHarnessSyntheticOnlyV1` requires these top-level fields:

- `schema_version`: schema label, expected future value `controlled_local_lean_dry_run_harness_synthetic_only_v1`.
- `harness_boundary_id`: stable metadata identifier; not an execution identifier and not proof authority.
- `created_at_label`: creation label; metadata label only.
- `updated_at_label`: update label; metadata label only.
- `freshness_label`: freshness status label.
- `source_scope`: scoped source metadata key/record.
- `owner_scope`: owner identity/scope metadata.
- `requester_scope`: requester identity/scope metadata.
- `target_scope`: intended target/session/context scope metadata.
- `sandbox_scope`: local sandbox scope metadata.
- `fixture_scope`: synthetic fixture scope metadata.
- `execution_scope`: future execution scope metadata; not authorization in this lane.
- `linked_lean_formal_problem_sketch_id`: optional link to a synthetic sketch metadata object; not proof authority.
- `linked_verifier_result_envelope_id`: optional link to a verifier result envelope design record; not real verifier output.
- `linked_misformalization_workflow_id`: optional link to a misformalization workflow; not authority to bypass review.
- `linked_cache_boundary_id`: optional link to the global goal/subgoal cache boundary; not cache access.
- `fixture_policy_metadata`: synthetic fixture policy block.
- `sandbox_policy_metadata`: local sandbox policy block.
- `execution_policy_metadata`: future execution gating policy block.
- `output_capture_policy_metadata`: output-capture restriction block.
- `network_policy_metadata`: no-network/no-provider policy block.
- `filesystem_policy_metadata`: temporary filesystem scope policy block.
- `claim_policy_metadata`: authority/claim denial policy block.
- `abort_policy_metadata`: abort conditions block.
- `risk_metadata`: risk label block.
- `validation_status`: one of the boundary validation status labels.
- `blocked_reason_labels`: list of blocked reason labels.
- `next_safe_steps`: list of metadata-only next safe steps.
- `denied_authority`: field-level denied-authority booleans, all false.

## 6. Fixture Policy Metadata

`fixture_policy_metadata` defines:

- `fixture_policy_id`
- `fixture_kind_label`
- `synthetic_only: true`
- `toy_problem_only: true`
- `real_open_problem_allowed: false`
- `private_user_content_allowed: false`
- `fixture_source_scope_key`
- `fixture_content_included: false`
- `fixture_requires_review: true`

Fixture policy metadata restricts any future dry-run harness to reviewed synthetic toy fixtures only. It excludes real open problems, private user theorem content, raw fixture content in reports, and unreviewed fixture use.

## 7. Sandbox Policy Metadata

`sandbox_policy_metadata` defines:

- `sandbox_policy_id`
- `local_only: true`
- `network_access_allowed: false`
- `provider_access_allowed: false`
- `external_tool_download_allowed: false`
- `filesystem_scope_label`
- `allowed_work_dir_label`
- `forbidden_paths_label`
- `dot_weslr_access_allowed: false`

Sandbox policy metadata confines future execution to a local, no-network, no-provider, no-download sandbox. It forbids `.weslr` access and requires explicit filesystem labels before any later implementation.

## 8. Execution Policy Metadata

`execution_policy_metadata` defines:

- `execution_policy_id`
- `execution_authorized_by_this_design: false`
- `future_execution_requires_separate_approval: true`
- `lean_execution_allowed_in_this_lane: false`
- `proof_search_allowed: false`
- `solver_runner_allowed: false`
- `timeout_required: true`
- `resource_limit_required: true`
- `single_fixture_only_by_default: true`
- `batch_execution_allowed: false`

Execution policy metadata is descriptive and restrictive. It does not authorize execution in this lane. Any future execution requires separate approval, timeout controls, resource limits, and single-fixture default handling.

## 9. Output Capture Policy Metadata

`output_capture_policy_metadata` defines:

- `output_capture_policy_id`
- `raw_output_capture_allowed: false`
- `raw_trace_capture_allowed: false`
- `raw_goal_state_capture_allowed: false`
- `raw_error_text_capture_allowed: false`
- `bounded_summary_allowed_only_after_future_review: true`
- `result_envelope_required: true`
- `formal_verifier_result_envelope_required: true`

Output capture policy metadata blocks raw compiler/verifier output, raw traces, raw goal states, and raw error text. Any future bounded summary requires future review and must use result-envelope handling.

## 10. Network Policy Metadata

`network_policy_metadata` defines:

- `network_disabled_required: true`
- `provider_calls_allowed: false`
- `model_calls_allowed: false`
- `search_calls_allowed: false`
- `advisor_calls_allowed: false`
- `package_download_allowed: false`

Network policy metadata requires no network and no external calls. It blocks package downloads, providers, models, search, and advisors.

## 11. Filesystem Policy Metadata

`filesystem_policy_metadata` defines:

- `filesystem_policy_id`
- `read_scope_label`
- `write_scope_label`
- `workspace_temp_only: true`
- `persistent_write_allowed: false`
- `dot_weslr_read_allowed: false`
- `dot_weslr_write_allowed: false`
- `source_tree_write_allowed: false`
- `cache_write_allowed: false`
- `log_trace_write_allowed: false`

Filesystem policy metadata confines any future implementation to temporary workspace-only behavior. It forbids persistent writes, `.weslr` IO, source-tree writes, cache writes, and log/trace writes.

## 12. Claim Policy Metadata

`claim_policy_metadata` defines:

- `claim_policy_id`
- `dry_run_grants_proof_authority: false`
- `dry_run_grants_public_authority: false`
- `dry_run_grants_benchmark_authority: false`
- `dry_run_grants_intelligence_authority: false`
- `dry_run_grants_turing_authority: false`
- `dry_run_grants_certification_authority: false`
- `dry_run_grants_product_readiness_authority: false`
- `dry_run_grants_final_answer_authority: false`

Claim policy metadata ensures that even a future successful synthetic dry run cannot become proof authority, public authority, benchmark evidence, intelligence evidence, Turing evidence, certification evidence, product-readiness evidence, or final-answer authority.

## 13. Abort Policy Metadata

`abort_policy_metadata` must define abort conditions for:

- non-synthetic fixture detected
- real open problem detected
- private user content detected
- network access required
- provider/model/search/advisor call required
- `.weslr` access required
- source tree write required
- persistent cache/log/trace write required
- raw compiler/goal/error/trace capture required
- proof/public/intelligence/final-answer claim implied
- timeout/resource limit missing
- denied-authority violation detected

Abort handling must fail closed before execution, before output capture, before filesystem writes, before cache/log/trace writes, before provider calls, and before any final-answer path.

## 14. Risk Metadata

`risk_metadata` defines labels for:

- `synthetic_boundary_escape_risk`
- `real_problem_attempt_risk`
- `private_content_leakage_risk`
- `raw_trace_leakage_risk`
- `dot_weslr_access_risk`
- `network_escape_risk`
- `provider_call_risk`
- `proof_search_expansion_risk`
- `dry_run_as_proof_risk`
- `benchmark_overclaim_risk`
- `final_answer_overclaim_risk`
- `runtime_wiring_risk`

Risk metadata is non-authoritative. It records visible risk labels so future validation can block unsafe metadata, but it does not certify safety or authorize execution.

## 15. Validation Status

`validation_status` must use one of these labels:

- `design_only`
- `not_implemented`
- `execution_not_authorized`
- `synthetic_fixture_required`
- `blocked_non_synthetic_fixture`
- `blocked_open_problem_attempt`
- `blocked_private_content`
- `blocked_network_required`
- `blocked_provider_required`
- `blocked_dot_weslr_access`
- `blocked_raw_output_capture`
- `blocked_persistent_write`
- `blocked_claim_authority`
- `ready_for_boundary_review`

None of these labels means proof success, theorem intent validation, public proof authority, benchmark readiness, intelligence evidence, Turing evidence, certification evidence, product readiness, final-answer readiness, runtime readiness, or claim authority.

## 16. Denied Authority Fields

`denied_authority` requires all fields below to be present and false:

- `permits_lean_install: false`
- `permits_lean_execution: false`
- `permits_theorem_prover_execution: false`
- `permits_solver_runner: false`
- `permits_proof_search: false`
- `permits_proof_sketch_execution: false`
- `permits_compiler_feedback_capture: false`
- `permits_real_verifier_result_capture: false`
- `permits_cache_creation: false`
- `permits_cache_reads: false`
- `permits_cache_writes: false`
- `permits_dot_weslr_reads: false`
- `permits_dot_weslr_writes: false`
- `permits_log_trace_cache_reads: false`
- `permits_log_trace_cache_writes: false`
- `permits_private_context_reads: false`
- `permits_artifact_content_reads: false`
- `permits_cross_user_reuse: false`
- `permits_provider_calls: false`
- `permits_model_calls: false`
- `permits_search_calls: false`
- `permits_advisor_calls: false`
- `permits_rater_execution: false`
- `permits_critic_execution: false`
- `permits_elo_scoring: false`
- `permits_runtime_chat_wiring: false`
- `permits_final_answer_generation: false`
- `permits_theorem_intent_validation_claim: false`
- `permits_proof_claims: false`
- `permits_public_claims: false`
- `permits_benchmark_claims: false`
- `permits_intelligence_claims: false`
- `permits_turing_claims: false`
- `permits_certification_claims: false`
- `permits_product_readiness_claims: false`

Missing denied-authority fields or any true value must fail closed.

## 17. Fail-Closed Rules

Future validation must block if:

- `source_scope` is missing or invalid
- owner/requester/target/sandbox/fixture/execution scope is missing
- fixture policy is missing
- sandbox policy is missing
- execution policy is missing
- output capture policy is missing
- network policy is missing
- filesystem policy is missing
- claim policy is missing
- non-synthetic fixture is implied
- real open-problem attempt is implied
- private content is implied
- network/provider/model/search/advisor call is implied
- `.weslr` access is implied
- source tree write is implied
- persistent cache/log/trace write is implied
- raw compiler, goal, error, or trace capture is implied
- Lean execution is implied in this lane
- proof search or solver runner is implied
- runtime/chat/final-answer authority is implied
- proof/public/intelligence/Turing/certification claim is implied
- denied-authority fields are missing or true
- non-JSON-safe metadata appears

Fail-closed behavior must return metadata-only blocked status and must not install Lean, run Lean, create proof attempts, call providers, access `.weslr`, write persistent files, capture raw output, or generate final answers.

## 18. Relationship To Previous Formal Proof Search Components

- Lean formal problem sketch schema remains the formalization metadata source.
- Proof sketch population and failed-path registry remains the candidate/failed-path metadata source.
- Formal verifier result envelope remains the verifier/integrity metadata source.
- Misformalization detection and adjudication workflow blocks or adjudicates intent alignment.
- Rater/critic ranking boundary remains triage-only.
- Global goal/subgoal cache boundary remains metadata-only.
- This harness boundary cannot override any of them.
- A future dry run, even if successful, is not proof, public, or final-answer authority.

Any future dry-run harness must be downstream of these metadata boundaries and cannot relax their blocked states, denied authority, or review requirements.

## 19. Relationship To Existing WESLR Helpers

- `source_scope` validates scope metadata.
- `read_authorization` would gate any future reads.
- Scoped memory/context adapter remains separate.
- Scoped artifact/upload registry remains separate.
- Cache/log/trace scoping remains separate.
- UNKNOWN ENGINE and Cognitive Gym remain metadata-only precedents.
- This design is not an implementation, not a runner, not a proof engine, and not proof authority.

Existing helpers do not become Lean harness helpers by this document. Any future helper or runner must be separately designed, reviewed, implemented, and reviewed again before use.

## 20. Future Negative Tests Required

Future synthetic-only tests must cover:

- missing source_scope
- missing sandbox/fixture/execution scope
- missing fixture policy
- non-synthetic fixture marker
- real open-problem marker
- private content marker
- network access marker
- provider/model/search/advisor marker
- `.weslr` access marker
- source tree write marker
- persistent cache/log/trace write marker
- raw compiler output marker
- raw goal state marker
- raw error text marker
- Lean execution marker in design lane
- proof search marker
- solver runner marker
- runtime/chat marker
- final-answer authority marker
- proof/public/intelligence/Turing/certification claim marker
- true denied-authority field
- missing denied-authority field
- non-JSON-safe metadata
- valid metadata-only harness boundary

All tests must be synthetic-only. They must not install Lean, run Lean, read `.weslr`, read logs/traces/caches, call providers/models/search/advisors, create final answers, or make proof/public/intelligence/Turing/certification claims.

## 21. Relationship To Formal Proof Search Sequence

This lane is the step G/H transition:

- A. completed/reviewed: Lean formal problem sketch schema
- B. completed/reviewed: proof sketch population/failed-path registry
- C. completed/reviewed: formal verifier result envelope
- D. completed/reviewed: misformalization workflow
- E. completed/reviewed: rater/critic ranking boundary
- F. completed/reviewed: global goal/subgoal cache boundary
- G. current lane: controlled local Lean dry-run harness synthetic-only design
- H. next likely: review controlled local Lean dry-run harness synthetic-only design
- I. later only after separate authorization: implementation helpers for synthetic-only dry-run harness
- J. much later: real theorem/proof attempt lanes, if ever separately authorized

This sequence remains design/review/context-driven. This lane does not authorize implementation, execution, or real theorem/proof attempts.

## 22. Decision

`controlled_local_lean_dry_run_harness_synthetic_only_design_ready_for_review`

## 23. Next Lane

`REVIEW_CONTROLLED_LOCAL_LEAN_DRY_RUN_HARNESS_SYNTHETIC_ONLY_V1`
