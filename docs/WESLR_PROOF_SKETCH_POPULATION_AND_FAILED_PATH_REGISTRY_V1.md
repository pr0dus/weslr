# WESLR Proof Sketch Population And Failed Path Registry V1

## 1. Status

- Lane name: `DESIGN_PROOF_SKETCH_POPULATION_AND_FAILED_PATH_REGISTRY_V1`
- Lane type: design-only
- Implementation changes: none
- Lean execution: none
- Theorem prover / solver runner: none
- Proof search: none
- Proof-sketch execution: none
- Compiler feedback capture: none
- Rater/critic execution: none
- Elo/ranking implementation: none
- Provider/model/search/advisor calls: none
- Runtime/chat/browser wiring: none
- Final-answer generation: none
- Public/proof/intelligence/Turing/certification claims: none
- Authority grant: none

This document is a metadata boundary design only. It creates no helper implementation, no runtime behavior, no theorem prover behavior, no solver behavior, no proof-search behavior, no proof-sketch execution behavior, no compiler feedback capture behavior, no rater/critic behavior, no ranking implementation, and no claim authority.

## 2. Purpose

`ProofSketchPopulationAndFailedPathRegistryV1` is the metadata-only design for future proof-sketch populations and failed-path registries.

It extends the reviewed `LeanFormalProblemSketchV1` posture by defining how WESLR may later represent proof-sketch candidate families, candidate lineage, rejected paths, failed approaches, mutation metadata, gap labels, blocked reasons, and triage selection metadata without treating any candidate, ranking, or failure record as proof, truth, execution, ranking authority, final-answer authority, or public claim authority.

This registry is for future internal metadata organization only. It does not generate candidates, execute candidates, validate candidates, rank candidates as benchmark evidence, or prove or disprove any theorem.

## 3. Non-goals

This design explicitly blocks:

- implementing helpers
- running Lean
- installing theorem provers
- creating proof attempts
- creating solver/prover runners
- creating proof-search loops
- executing proof sketches
- capturing real compiler feedback
- executing rater/critic ranking
- creating Elo scores as benchmark or intelligence evidence
- using real Erdős, Millennium, or other open-problem attempts
- calling providers/models/search/advisors
- reading `.weslr`
- reading private artifacts, uploads, logs, traces, caches, context, transcripts, protected memory, or private source content
- creating final answers, reply text, previews, user-facing output, or runtime responses
- making proof, public, benchmark, prize, intelligence, Turing, certification, official-evaluation, product-readiness, or public-readiness claims

This document does not authorize source ingestion, web/search ingestion, browser access, database access, auth/session changes, filesystem/log/cache/trace ingestion code, runtime/chat/voice/UI behavior, or WESLR helper implementation changes.

## 4. Registry Overview

Future metadata object:

`ProofSketchPopulationAndFailedPathRegistryV1`

The object is:

- JSON-safe
- metadata-only
- source-scoped
- owner/requester/target scoped
- versioned
- freshness-labeled
- linked to a valid `LeanFormalProblemSketchV1`
- fail-closed
- raw-content-denying
- authority-denying by default

It must not contain raw proof text, raw source content, raw candidate content, raw failure content, private context, artifact/upload content, log/trace/cache content, Lean execution output, compiler feedback output, provider/model/search/advisor output, rater/critic output, Elo benchmark evidence, runtime reply text, final-answer text, or public claim text.

## 5. Required Top-Level Fields

`ProofSketchPopulationAndFailedPathRegistryV1` requires these top-level fields:

- `schema_version`: schema label, expected future value `proof_sketch_population_failed_path_registry_v1`.
- `registry_id`: stable metadata identifier; not a proof identifier.
- `created_at_label`: creation label; metadata label only.
- `updated_at_label`: update label; metadata label only.
- `freshness_label`: freshness status label; required before any later review.
- `source_scope`: scoped source metadata key/record.
- `owner_scope`: owner identity/scope metadata.
- `requester_scope`: requester identity/scope metadata.
- `target_scope`: intended target/session/context scope metadata.
- `linked_lean_formal_problem_sketch_id`: link to the future sketch metadata object; not proof authority.
- `linked_sketch_schema_version`: expected compatible sketch schema version.
- `population_metadata`: metadata describing the bounded candidate population.
- `candidate_records`: list of candidate metadata records.
- `lineage_metadata`: metadata describing candidate ancestry and derivation labels.
- `failed_path_records`: list of failed or rejected path metadata records.
- `mutation_metadata`: metadata describing allowed candidate metadata mutations.
- `selection_metadata`: triage/selection metadata without proof or benchmark authority.
- `risk_metadata`: risk labels associated with candidates, lineage, failed paths, mutation, and selection.
- `validation_status`: one of the registry validation status labels.
- `blocked_reason_labels`: list of blocked reason labels.
- `next_safe_steps`: list of metadata-only next safe steps.
- `denied_authority`: field-level denied-authority booleans, all false.

## 6. Population Metadata

`population_metadata` defines:

- `population_id`
- `population_kind`
- `population_purpose_label`
- `candidate_count_label`
- `candidate_limit_label`
- `generation_mode_label`
- `synthetic_only_label`
- `real_problem_attempt_allowed: false`
- `population_content_included: false`

Population metadata is not proof authority. It does not authorize candidate generation, proof generation, proof execution, theorem proving, proof search, compiler feedback capture, rater/critic execution, ranking execution, provider/model/search/advisor calls, final-answer generation, or public claims.

A population record may only describe future candidate-family metadata after a separately authorized helper implementation and review. Candidate counts and limits are bookkeeping labels, not evidence of capability, intelligence, progress, or proof validity.

## 7. Candidate Record Metadata

Each `candidate_records` entry defines:

- `candidate_id`
- `candidate_kind`
- `parent_candidate_id`
- `candidate_status`
- `strategy_summary_label`
- `candidate_lemma_labels`
- `planned_subgoal_labels`
- `known_gap_labels`
- `uncertainty_labels`
- `misformalization_risk_labels`
- `claim_authority_label`
- `proof_text_included: false`
- `candidate_content_included: false`

Candidate records are not truth, not proof, not formal verification, not compiler feedback, not final-answer material, and not public claim material. A candidate can be wrong, stale, incomplete, underspecified, overconstrained, weakened, shifted, missing assumptions, dependent on hallucinated lemmas, or mapped to the wrong formal target.

`claim_authority_label` must remain a denial or blocked-state label unless a later separately reviewed authority workflow changes that posture. This registry itself never grants claim authority.

## 8. Lineage Metadata

`lineage_metadata` defines:

- `lineage_id`
- `root_candidate_id`
- `ancestor_candidate_labels`
- `mutation_reason_labels`
- `derived_from_failed_path_label`
- `lineage_status`
- `lineage_content_included: false`

Lineage metadata is explanation metadata only. It can describe candidate ancestry, derivation labels, and relationships to failed paths, but it is not scoring, proof, verifier output, ranking authority, final-answer authority, or public authority.

Lineage must remain scoped to the registry owner/requester/target. Cross-user or cross-tenant lineage reuse must fail closed unless a later reviewed design explicitly authorizes scoped sharing.

## 9. Failed Path Records

Each `failed_path_records` entry defines:

- `failed_path_id`
- `associated_candidate_id`
- `failure_kind`
- `failure_location_label`
- `failure_summary_label`
- `gap_labels`
- `blocked_reason_labels`
- `retry_recommendation_label`
- `failure_severity_label`
- `may_retry_label`
- `failed_path_content_included: false`

Allowed `failure_kind` labels include:

- `formalization_gap`
- `missing_assumption`
- `suspected_wrong_theorem`
- `suspected_weakened_statement`
- `overbroad_helper_lemma`
- `hallucinated_known_lemma`
- `sorry_or_admit_risk`
- `axiom_or_soundness_risk`
- `dependency_or_import_risk`
- `strategy_dead_end`
- `claim_authority_blocked`
- `execution_not_authorized`

Failed-path records are negative or blocked-path metadata only. They do not prove impossibility, disprove a theorem, validate a theorem, establish compiler feedback, or authorize retry execution. They may inform future triage only after a separately authorized helper implementation and review.

## 10. Mutation Metadata

Each `mutation_metadata` entry defines:

- `mutation_id`
- `source_candidate_id`
- `target_candidate_id`
- `mutation_kind`
- `mutation_reason_label`
- `allowed_mutation_label`
- `forbidden_mutation_labels`
- `protected_statement_unchanged_label`
- `bounded_edit_region_respected_label`
- `mutation_content_included: false`

Allowed `mutation_kind` labels may include:

- `strategy_rewrite_metadata`
- `lemma_plan_adjustment_metadata`
- `subgoal_order_change_metadata`
- `assumption_review_metadata`
- `risk_label_update_metadata`
- `failed_path_response_metadata`

Theorem statement mutation is not allowed by this registry. Any mutation metadata implying theorem-statement mutation, protected-definition drift, unreviewed import change, raw content inclusion, or bounded-edit-region violation must fail closed.

Mutation metadata does not authorize edits, execution, candidate generation, proof search, theorem proving, compiler feedback capture, or final-answer generation.

## 11. Selection Metadata

`selection_metadata` defines:

- `selection_id`
- `selected_candidate_id`
- `selection_reason_label`
- `selection_confidence_label`
- `selection_method_label`
- `ranking_content_included: false`
- `ranking_grants_proof_authority: false`
- `ranking_grants_benchmark_authority: false`
- `ranking_grants_intelligence_authority: false`

Selection and ranking metadata is triage metadata only. It may label why a candidate is a future candidate for review, but it does not establish proof validity, theorem truth, compiler success, benchmark performance, intelligence evidence, Turing evidence, certification evidence, product readiness, public readiness, or final-answer readiness.

This registry does not implement ranking, Elo scoring, rater/critic execution, pairwise comparison, or benchmark evaluation.

## 12. Risk Metadata

`risk_metadata` defines these risk labels:

- `candidate_as_truth_risk`
- `false_proof_authority_risk`
- `misformalization_risk`
- `stale_candidate_risk`
- `raw_content_leakage_risk`
- `cross_user_lineage_risk`
- `unscoped_cache_risk`
- `overbroad_helper_lemma_risk`
- `sorry_laundering_risk`
- `hallucinated_lemma_risk`
- `benchmark_overclaim_risk`

Risk metadata must be treated as warning metadata only. It does not authorize reads, execution, ranking, proof search, proof claims, public claims, or runtime behavior.

## 13. Validation Status

`validation_status` is constrained to:

- `metadata_schema_only`
- `linked_sketch_missing`
- `linked_sketch_unvalidated`
- `population_candidate_unvalidated`
- `blocked_missing_scope`
- `blocked_missing_authorization`
- `blocked_raw_content`
- `blocked_open_problem_attempt`
- `blocked_execution_not_authorized`
- `blocked_claim_authority`
- `ready_for_schema_review`

None of these statuses means proof success, Lean success, theorem-prover success, formal verification, compiler success, ranking success, benchmark readiness, prize readiness, product readiness, intelligence evidence, Turing evidence, certification evidence, public readiness, final-answer readiness, or claim authority.

## 14. Denied Authority Fields

`denied_authority` requires these field-level booleans, all false:

- `permits_lean_execution: false`
- `permits_theorem_prover_execution: false`
- `permits_solver_runner: false`
- `permits_proof_search: false`
- `permits_proof_sketch_execution: false`
- `permits_compiler_feedback_capture: false`
- `permits_provider_calls: false`
- `permits_model_calls: false`
- `permits_search_calls: false`
- `permits_advisor_calls: false`
- `permits_rater_execution: false`
- `permits_critic_execution: false`
- `permits_elo_scoring: false`
- `permits_dot_weslr_reads: false`
- `permits_private_context_reads: false`
- `permits_artifact_content_reads: false`
- `permits_log_trace_cache_reads: false`
- `permits_runtime_chat_wiring: false`
- `permits_final_answer_generation: false`
- `permits_proof_claims: false`
- `permits_public_claims: false`
- `permits_benchmark_claims: false`
- `permits_intelligence_claims: false`
- `permits_turing_claims: false`
- `permits_certification_claims: false`
- `permits_product_readiness_claims: false`

Future validation must fail closed if any denied-authority field is missing, non-boolean, or true.

## 15. Fail-Closed Rules

Future validation must block if:

- `source_scope` is missing or invalid
- `owner_scope`, `requester_scope`, or `target_scope` is missing
- linked Lean formal problem sketch ID is missing
- linked sketch schema version is missing
- source authorization is missing
- freshness/version labels are missing
- candidate records are missing required metadata
- failed-path records are missing required metadata
- mutation metadata implies theorem statement mutation
- selection metadata implies proof authority
- denied-authority fields are missing or true
- proof text or raw source/candidate/failure content is included
- `.weslr`, global, process-default, or `tl_default` markers appear
- a real open-problem attempt is implied
- Lean/prover/solver/proof-search execution is implied
- rater/critic execution or Elo benchmark scoring is implied
- proof/public/intelligence/Turing/certification claim is implied
- final-answer/runtime/chat authority is implied
- non-JSON-safe metadata appears

The fail-closed output must remain metadata-only and must not perform reads, source ingestion, execution, runtime wiring, provider/model/search/advisor calls, rater/critic calls, Elo scoring, cache/log/trace access, `.weslr` access, or final-answer generation.

## 16. Relationship To Lean Formal Problem Sketch Schema

- This registry must link to a valid `LeanFormalProblemSketchV1`.
- It does not replace formalization metadata.
- It does not create compiler feedback metadata.
- It does not validate theorem statements.
- It does not prove or disprove candidates.
- It may only represent candidate and failed-path metadata after future helper implementation and review.

`LeanFormalProblemSketchV1` remains the source of formal problem intent, formalization candidate metadata, Lean environment metadata, protected statement metadata, bounded edit-region metadata, proof-sketch metadata, assumptions, known gaps, misformalization risks, validation state, blocked reasons, and denied authority. This registry only adds population/lineage/failed-path/mutation/selection metadata around that sketch.

## 17. Relationship To Existing WESLR Helpers

- `source_scope` validates scope metadata.
- `read_authorization` should later gate source, context, artifact, upload, cache, log, and trace access.
- The scoped memory/context adapter remains separate.
- The scoped artifact/upload registry remains separate.
- Cache/log/trace scoping remains separate.
- UNKNOWN ENGINE and Cognitive Gym remain metadata-only precedents.
- This registry is not a runner, not a rater, not a proof engine, and not proof authority.

The registry does not modify, replace, or invoke existing helpers. It may only inform future helper design after separate authorization and review.

## 18. Future Negative Tests Required

Future helper implementation should include synthetic-only tests for:

- missing `source_scope`
- invalid `source_scope`
- missing owner/requester/target scope
- missing linked sketch ID
- missing linked schema version
- missing freshness/version labels
- missing candidate metadata
- missing failed-path metadata
- mutation implies theorem statement change
- selection implies proof authority
- true denied-authority field
- missing denied-authority field
- raw proof/source/candidate/failure content included
- `.weslr` marker
- global/process-default/`tl_default` marker
- open-problem attempt marker
- Lean execution marker
- rater/critic execution marker
- Elo benchmark/intelligence marker
- provider/model/search/advisor marker
- final-answer authority marker
- proof/public/intelligence/Turing/certification claim marker
- non-JSON-safe metadata
- valid metadata-only registry

These tests must remain synthetic-only unless a later lane explicitly authorizes a broader test posture. They must not run Lean, call providers, read private context, read `.weslr`, ingest logs/traces/caches, execute proof search, or generate final answers.

## 19. Relationship To Formal Proof Search Sequence

This design is step B after the Lean formal problem sketch schema:

A. completed/reviewed: `DESIGN_LEAN_FORMAL_PROBLEM_SKETCH_SCHEMA_V1`

B. current lane: `DESIGN_PROOF_SKETCH_POPULATION_AND_FAILED_PATH_REGISTRY_V1`

C. next likely: `REVIEW_PROOF_SKETCH_POPULATION_AND_FAILED_PATH_REGISTRY_V1`

D. later: formal verifier result envelope design

E. later: misformalization detection workflow design

F. later: rater/critic ranking boundary design

G. later: global goal/subgoal cache boundary design

H. much later: synthetic-only local Lean dry-run harness design

No step authorizes later steps by implication. Each later lane requires separate operator authorization, separate design/review, and explicit validation.

## 20. Decision

`proof_sketch_population_failed_path_registry_design_ready_for_review`

Rationale: this design defines a JSON-safe, metadata-only, source-scoped, freshness-labeled, linked, fail-closed, authority-denying registry for future proof-sketch populations and failed-path metadata. It blocks implementation, Lean execution, theorem proving, solver runners, proof search, proof-sketch execution, compiler feedback capture, rater/critic execution, Elo/ranking implementation, provider/model/search/advisor calls, runtime/chat/browser wiring, final-answer generation, and proof/public/intelligence/Turing/certification/product-readiness claims.

## 21. Next Lane

`REVIEW_PROOF_SKETCH_POPULATION_AND_FAILED_PATH_REGISTRY_V1`
