# WESLR Rater Critic Ranking Boundary V1

## 1. Status

- Lane name: `DESIGN_RATER_CRITIC_RANKING_BOUNDARY_V1`
- Lane type: design-only
- Implementation changes: none
- Rater execution: none
- Critic execution: none
- Elo/ranking implementation: none
- Lean execution: none
- Theorem prover / solver runner: none
- Proof search: none
- Proof-sketch execution: none
- Compiler feedback capture: none
- Provider/model/search/advisor calls: none
- Runtime/chat/browser wiring: none
- Final-answer generation: none
- Public/proof/intelligence/Turing/certification claims: none
- Authority grant: none

This document is a metadata boundary design only. It creates no helper implementation, no rater behavior, no critic behavior, no Elo/ranking implementation, no runtime behavior, no theorem prover behavior, no solver behavior, no proof-search behavior, no proof-sketch execution behavior, no compiler feedback capture behavior, no provider/model/search/advisor behavior, and no claim authority.

## 2. Purpose

`RaterCriticRankingBoundaryV1` is the metadata-only boundary for future rater, critic, and ranking metadata in WESLR formal proof-search work.

The boundary defines how WESLR may later represent prioritization signals, critic notes, ranking labels, candidate comparison metadata, score labels, and Elo-like bookkeeping without treating ranking as proof authority, benchmark evidence, intelligence evidence, Turing evidence, certification evidence, product-readiness evidence, public-claim authority, or final-answer authority.

Ranking metadata may support future triage only. It must never decide theorem truth, validate proof success, validate natural-language intent, override misformalization blocks, select final answers, authorize execution, or authorize public claims.

## 3. Non-goals

This design explicitly blocks:

- implementing rater/critic helpers
- running raters or critics
- creating Elo/ranking execution
- scoring candidates as benchmark/intelligence evidence
- selecting final answers
- running Lean
- installing theorem provers
- creating proof attempts
- creating solver/prover runners
- creating proof-search loops
- executing proof sketches
- capturing real compiler feedback
- calling providers/models/search/advisors
- reading `.weslr`
- reading private artifacts/uploads/logs/traces/caches/context
- creating final answers, reply text, previews, user-facing output, or runtime responses
- making proof, public, benchmark, prize, intelligence, Turing, certification, official-evaluation, product-readiness, or public-readiness claims

This document does not authorize source ingestion, web/search ingestion, browser access, database access, auth/session changes, filesystem/log/cache/trace ingestion code, runtime/chat/voice/UI behavior, WESLR helper implementation changes, rater/critic implementation changes, ranking execution, or final-answer generation.

## 4. Boundary Overview

Future metadata object:

`RaterCriticRankingBoundaryV1`

The object is:

- metadata-only
- JSON-safe
- source-scoped
- owner/requester/target scoped
- versioned
- freshness-labeled
- optionally linked to a valid `LeanFormalProblemSketchV1`
- optionally linked to a valid `ProofSketchPopulationAndFailedPathRegistryV1`
- optionally linked to a valid `FormalVerifierResultEnvelopeV1`
- optionally linked to a valid `MisformalizationDetectionAndAdjudicationWorkflowV1`
- fail-closed
- raw-content-denying
- authority-denying by default

It must not contain raw proof text, raw theorem source content, raw candidate content, raw critic content, raw comparison content, raw score rationale content, raw verifier output, raw compiler traces, raw goal states, raw errors, private context, artifact/upload content, log/trace/cache content, provider/model/search/advisor output, runtime reply text, final-answer text, public claim text, benchmark evidence, intelligence evidence, Turing evidence, certification evidence, or product-readiness evidence.

## 5. Required Top-Level Fields

`RaterCriticRankingBoundaryV1` requires these top-level fields:

- `schema_version`: schema label, expected future value `rater_critic_ranking_boundary_v1`.
- `ranking_boundary_id`: stable metadata identifier; not a proof identifier and not a benchmark identifier.
- `created_at_label`: creation label; metadata label only.
- `updated_at_label`: update label; metadata label only.
- `freshness_label`: freshness status label.
- `source_scope`: scoped source metadata key/record.
- `owner_scope`: owner identity/scope metadata.
- `requester_scope`: requester identity/scope metadata.
- `target_scope`: intended target/session/context scope metadata.
- `linked_lean_formal_problem_sketch_id`: optional link to a valid sketch metadata object; not proof authority.
- `linked_population_registry_id`: optional link to a valid population/failed-path registry; not proof authority.
- `linked_verifier_result_envelope_id`: optional link to a valid verifier result envelope; not proof authority and not intent-validation authority.
- `linked_misformalization_workflow_id`: optional link to a valid misformalization workflow; not authority to override blocks.
- `ranking_purpose_metadata`: triage purpose metadata block.
- `candidate_reference_metadata`: candidate reference metadata block or list.
- `critic_signal_metadata`: critic signal metadata block or list.
- `comparison_metadata`: candidate comparison metadata block or list.
- `priority_metadata`: priority metadata block.
- `score_metadata`: score/Elo-like bookkeeping metadata block or list.
- `adjudication_dependency_metadata`: dependency metadata for required adjudication and external review.
- `risk_metadata`: risk label block.
- `validation_status`: one of the boundary validation status labels.
- `blocked_reason_labels`: list of blocked reason labels.
- `next_safe_steps`: list of metadata-only next safe steps.
- `denied_authority`: field-level denied-authority booleans, all false.

## 6. Ranking Purpose Metadata

`ranking_purpose_metadata` defines:

- `ranking_purpose_id`
- `ranking_purpose_label`
- `ranking_scope_label`
- `ranking_for_triage_only: true`
- `ranking_content_included: false`
- `ranking_grants_proof_authority: false`
- `ranking_grants_benchmark_authority: false`
- `ranking_grants_intelligence_authority: false`
- `ranking_grants_final_answer_authority: false`

Ranking purpose metadata describes why future candidate prioritization metadata exists. It is not proof authority, benchmark authority, intelligence evidence, Turing evidence, certification evidence, product-readiness evidence, public-claim authority, or final-answer authority.

## 7. Candidate Reference Metadata

Each `candidate_reference_metadata` entry defines:

- `candidate_reference_id`
- `linked_candidate_id`
- `candidate_status_label`
- `candidate_source_scope_key`
- `candidate_freshness_label`
- `candidate_content_included: false`
- `candidate_as_truth_allowed: false`

Candidate references do not make candidates true, proved, verified, executable, selected, public, or final-answer material. They are scoped pointers to candidate metadata only. A referenced candidate may be wrong, stale, incomplete, misformalized, weakened, overconstrained, dependent on forbidden assumptions, or blocked by later adjudication.

## 8. Critic Signal Metadata

Each `critic_signal_metadata` entry defines:

- `critic_signal_id`
- `critic_kind_label`
- `critic_summary_label`
- `critic_confidence_label`
- `critic_scope_label`
- `critic_content_included: false`
- `critic_execution_observed: false`
- `critic_grants_authority: false`

Critic signals are triage labels only. They cannot override misformalization blocks, verifier caveats, source-scope requirements, read-authorization requirements, denied-authority fields, operator review requirements, external expert review requirements, or adjudication blocks.

## 9. Comparison Metadata

Each `comparison_metadata` entry defines:

- `comparison_id`
- `candidate_a_id`
- `candidate_b_id`
- `comparison_basis_label`
- `comparison_result_label`
- `comparison_confidence_label`
- `comparison_content_included: false`
- `comparison_grants_authority: false`

Comparison metadata may later describe bounded candidate-to-candidate triage labels only. It is not proof, not theorem intent validation, not verifier output, not a benchmark result, not intelligence evidence, not public claim material, and not final-answer material.

## 10. Priority Metadata

`priority_metadata` defines:

- `priority_id`
- `selected_candidate_id`
- `priority_reason_label`
- `priority_confidence_label`
- `priority_status_label`
- `priority_grants_execution_authority: false`
- `priority_grants_claim_authority: false`

Priority metadata may later identify a candidate as worth further metadata-only review. It does not authorize execution, proof search, verifier capture, Lean/prover/solver access, provider/model/search/advisor calls, public claims, final-answer generation, or claim authority.

## 11. Score Metadata

Each `score_metadata` entry defines:

- `score_id`
- `score_kind_label`
- `score_value_label`
- `score_range_label`
- `score_interpretation_label`
- `score_content_included: false`
- `score_is_benchmark: false`
- `score_is_intelligence_evidence: false`
- `score_is_turing_evidence: false`
- `score_grants_claim_authority: false`

Elo-like or score-like metadata is bookkeeping only. It may later help order internal review queues but must not become benchmark evidence, intelligence evidence, Turing evidence, certification evidence, product-readiness evidence, proof authority, public authority, final-answer authority, or model/capability claims.

## 12. Adjudication Dependency Metadata

`adjudication_dependency_metadata` defines:

- `misformalization_workflow_required: true`
- `misformalization_blocks_override_ranking: true`
- `external_review_required_for_claims: true`
- `verifier_success_required_but_not_sufficient: true`
- `ranking_cannot_override_denied_authority: true`

Ranking cannot replace or bypass source scoping, read authorization, formalization review, verifier envelope review, misformalization adjudication, operator review, external expert review, or final-response authority checkpoints. A ranked candidate remains blocked if any required upstream or downstream authority gate is blocked.

## 13. Risk Metadata

`risk_metadata` defines:

- `ranking_as_truth_risk`
- `critic_overclaim_risk`
- `elo_as_intelligence_risk`
- `benchmark_overclaim_risk`
- `candidate_selection_as_proof_risk`
- `misformalization_override_risk`
- `final_answer_overclaim_risk`
- `cross_user_ranking_leakage_risk`
- `stale_score_risk`
- `provider_bias_risk`

Risk metadata is caution metadata only. It does not prove the risk is resolved and does not grant authority to continue when a risk remains unresolved.

## 14. Validation Status

Allowed `validation_status` labels include:

- `metadata_schema_only`
- `not_ranked`
- `ranking_not_authorized`
- `linked_population_registry_missing`
- `linked_misformalization_workflow_missing`
- `blocked_missing_scope`
- `blocked_missing_authorization`
- `blocked_raw_content`
- `blocked_misformalization_unresolved`
- `blocked_verifier_not_sufficient`
- `blocked_external_review_required`
- `blocked_claim_authority`
- `ready_for_boundary_review`

None of these labels means proof success, theorem intent validation, public proof authority, benchmark readiness, intelligence evidence, Turing evidence, certification evidence, product readiness, final-answer readiness, or claim authority. `ready_for_boundary_review` means only that the boundary metadata can be reviewed.

## 15. Denied Authority Fields

`denied_authority` requires all of these field-level booleans to be present and false:

- `permits_lean_execution: false`
- `permits_theorem_prover_execution: false`
- `permits_solver_runner: false`
- `permits_proof_search: false`
- `permits_proof_sketch_execution: false`
- `permits_compiler_feedback_capture: false`
- `permits_real_verifier_result_capture: false`
- `permits_provider_calls: false`
- `permits_model_calls: false`
- `permits_search_calls: false`
- `permits_advisor_calls: false`
- `permits_rater_execution: false`
- `permits_critic_execution: false`
- `permits_elo_scoring: false`
- `permits_benchmark_scoring: false`
- `permits_dot_weslr_reads: false`
- `permits_private_context_reads: false`
- `permits_artifact_content_reads: false`
- `permits_log_trace_cache_reads: false`
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

Future validation must fail closed if any denied-authority field is missing, true, non-boolean, implied true by another field, or overridden by another section.

## 16. Fail-Closed Rules

Future validation must block if:

- `source_scope` is missing or invalid
- owner/requester/target scope is missing
- freshness/version labels are missing
- source authorization is missing
- ranking purpose metadata is missing
- candidate reference metadata is missing
- critic metadata implies authority
- comparison metadata implies authority
- priority metadata implies execution or claim authority
- score metadata implies authority
- raw candidate, critic, comparison, or score content is included
- rater/critic/Elo execution is implied
- score is treated as benchmark/intelligence/Turing/certification evidence
- ranking overrides a misformalization block
- ranking overrides a verifier caveat
- ranking overrides denied authority
- external review is required but not observed
- denied-authority fields are missing or true
- `.weslr`, global, process-default, or `tl_default` markers appear
- Lean/prover/solver/proof-search execution is implied
- provider/model/search/advisor call is implied
- proof/public/intelligence/Turing/certification claim is implied
- final-answer/runtime/chat authority is implied
- non-JSON-safe metadata appears

Fail-closed handling must prefer blocked metadata-only status over repair, inference, fallback execution, hidden reads, context expansion, ranking execution, runtime wiring, claim escalation, benchmark/capability interpretation, or final-answer generation.

## 17. Relationship To Previous Formal Proof Search Components

This boundary depends on, but cannot override, previous formal proof-search metadata components:

- `LeanFormalProblemSketchV1` remains the formalization metadata source.
- `ProofSketchPopulationAndFailedPathRegistryV1` remains the candidate and failed-path metadata source.
- `FormalVerifierResultEnvelopeV1` remains the verifier and integrity metadata source.
- `MisformalizationDetectionAndAdjudicationWorkflowV1` blocks or adjudicates natural-language intent alignment and formalization mismatch risk.
- Ranking cannot override any of these components.
- Ranking is triage metadata only.

A high ranking, favorable critic label, selected priority label, or score label cannot establish proof success, theorem intent validation, soundness, source alignment, public authority, benchmark authority, intelligence evidence, Turing evidence, certification evidence, product readiness, final-answer readiness, or claim authority.

## 18. Relationship To Existing WESLR Helpers

Existing WESLR helper boundaries remain separate:

- `source_scope` validates scope metadata.
- `read_authorization` should later gate source, context, artifact, log, trace, cache, and ranking access.
- The scoped memory/context adapter remains separate.
- The scoped artifact/upload registry remains separate.
- Cache/log/trace scoping remains separate.
- UNKNOWN ENGINE and Cognitive Gym remain metadata-only precedents.
- This boundary is not a runner, not a rater, not a critic, not a proof engine, not a theorem prover, not a solver, not a ranking implementation, and not proof authority.

This boundary must not bypass source scoping, read authorization, scoped adapters, artifact/upload boundaries, cache/log/trace boundaries, misformalization blocks, verifier caveats, authority checkpoints, or final-response assembly boundaries.

## 19. Future Negative Tests Required

Future helper implementation, if separately authorized, must include synthetic-only tests for:

- missing source_scope
- invalid source_scope
- missing owner/requester/target scope
- missing freshness/version labels
- missing ranking purpose metadata
- missing candidate reference metadata
- critic signal implies proof authority
- comparison implies proof authority
- priority implies execution authority
- score treated as benchmark/intelligence evidence
- ranking overrides misformalization block
- ranking overrides verifier caveat
- ranking overrides denied authority
- external review required but not observed
- true denied-authority field
- missing denied-authority field
- raw candidate/critic/comparison/score content included
- `.weslr` marker
- global/process-default/`tl_default` marker
- Lean execution marker
- rater/critic execution marker
- Elo scoring marker
- provider/model/search/advisor marker
- final-answer authority marker
- proof/public/intelligence/Turing/certification claim marker
- non-JSON-safe metadata
- valid metadata-only ranking boundary

All tests must remain synthetic-only. They must not run Lean, install theorem provers, execute raters/critics, compute real Elo scores, capture real compiler feedback, capture real verifier results, read `.weslr`, read private artifacts/uploads/logs/traces/caches/context, call providers/models/search/advisors, generate final answers, validate theorem intent, or make claims.

## 20. Relationship To Formal Proof Search Sequence

This is step E in the formal proof-search design sequence:

A. completed/reviewed: `DESIGN_LEAN_FORMAL_PROBLEM_SKETCH_SCHEMA_V1`

B. completed/reviewed: `DESIGN_PROOF_SKETCH_POPULATION_AND_FAILED_PATH_REGISTRY_V1`

C. completed/reviewed: `DESIGN_FORMAL_VERIFIER_RESULT_ENVELOPE_V1`

D. completed/reviewed: `DESIGN_MISFORMALIZATION_DETECTION_AND_ADJUDICATION_WORKFLOW_V1`

E. current lane: `DESIGN_RATER_CRITIC_RANKING_BOUNDARY_V1`

F. next likely: `REVIEW_RATER_CRITIC_RANKING_BOUNDARY_V1`

G. later: global goal/subgoal cache boundary design

H. much later: synthetic-only local Lean dry-run harness design

This sequence remains design-first and review-first. No ranking helper, rater, critic, Elo implementation, proof-search runner, Lean dry-run, provider call, open-problem attempt, runtime wiring, final answer, theorem-intent-validation claim, benchmark claim, intelligence claim, Turing claim, certification claim, product-readiness claim, public claim, or proof claim may be introduced by this design.

## 21. Decision

`rater_critic_ranking_boundary_design_ready_for_review`

## 22. Next Lane

`REVIEW_RATER_CRITIC_RANKING_BOUNDARY_V1`
