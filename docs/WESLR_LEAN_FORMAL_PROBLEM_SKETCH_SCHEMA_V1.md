# WESLR Lean Formal Problem Sketch Schema V1

## 1. Status

- Lane name: `DESIGN_LEAN_FORMAL_PROBLEM_SKETCH_SCHEMA_V1`
- Lane type: design-only
- Implementation changes: none
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

This document is a metadata schema design only. It creates no helper implementation, no runtime behavior, no theorem prover behavior, no solver behavior, no proof-search behavior, no proof-sketch execution behavior, no compiler feedback capture behavior, and no claim authority.

## 2. Purpose

`LeanFormalProblemSketchV1` is the first metadata-only design after the formal proof-search assimilation boundary. It defines how WESLR may safely represent a future formal math problem intent, a Lean theorem-statement candidate, bounded edit regions, proof-sketch metadata, assumptions, known gaps, misformalization risks, freshness/version labels, source-scope keys, and denied-authority fields.

The schema lets WESLR represent future formal problem sketches without treating them as proof, execution, truth, public authority, product authority, benchmark authority, intelligence authority, Turing authority, certification authority, final-answer authority, or proof-search authority.

## 3. Non-goals

This schema design explicitly blocks:

- implementing schema helpers
- running Lean
- installing theorem provers
- creating proof runners
- creating solver harnesses
- creating proof-search loops
- executing proof sketches
- capturing real compiler feedback
- using real Erdős, Millennium, or other open-problem attempts
- calling providers/models/search/advisors
- reading `.weslr`
- reading private artifacts, uploads, logs, traces, caches, context, transcripts, protected memory, or private source content
- creating final answers, reply text, previews, user-facing output, or runtime responses
- making proof, public, benchmark, prize, intelligence, Turing, certification, official-evaluation, product-readiness, or public-readiness claims

This document does not authorize source ingestion, web/search ingestion, browser access, database access, auth/session changes, filesystem/log/cache/trace ingestion code, runtime/chat/voice/UI behavior, or WESLR helper implementation changes.

## 4. Schema Overview

Future metadata object:

`LeanFormalProblemSketchV1`

The object is:

- JSON-safe
- metadata-only
- source-scoped
- owner/requester/target scoped
- versioned
- freshness-labeled
- authorization-aware
- raw-content-denying
- authority-denying by default

It must not contain raw proof text, raw source content, private context, artifact/upload content, log/trace/cache content, Lean execution output, compiler feedback output, provider/model/search/advisor output, runtime reply text, final-answer text, or public claim text.

## 5. Required Top-Level Fields

`LeanFormalProblemSketchV1` requires these top-level fields:

- `schema_version`: schema label, expected future value `lean_formal_problem_sketch_v1`.
- `sketch_id`: stable metadata identifier; not a proof identifier.
- `created_at_label`: creation label; metadata label only.
- `updated_at_label`: update label; metadata label only.
- `freshness_label`: freshness status label; required before any later review.
- `source_scope`: scoped source metadata key/record.
- `owner_scope`: owner identity/scope metadata.
- `requester_scope`: requester identity/scope metadata.
- `target_scope`: intended target/session/context scope metadata.
- `problem_intent`: problem intent metadata block.
- `source_provenance`: source/provenance metadata block.
- `formalization_candidate`: Lean/formal theorem-statement candidate metadata block.
- `lean_environment_metadata`: Lean/mathlib environment metadata block.
- `protected_statement_metadata`: protected theorem/import/definition/hypothesis metadata block.
- `bounded_edit_region_metadata`: bounded edit-region metadata block or list.
- `proof_sketch_metadata`: proof-sketch metadata block.
- `assumption_metadata`: assumption metadata block or list.
- `known_gap_metadata`: known gap metadata block or list.
- `misformalization_risk_metadata`: misformalization risk labels block.
- `validation_status`: one of the schema validation status labels.
- `blocked_reason_labels`: list of blocked reason labels.
- `next_safe_steps`: list of metadata-only next safe steps.
- `denied_authority`: field-level denied-authority booleans, all false.

## 6. Problem Intent Metadata

`problem_intent` defines:

- `intent_label`
- `domain_label`
- `problem_family_label`
- `difficulty_label`
- `toy_or_real_problem_label`
- `open_problem_risk_label`
- `natural_language_summary_redacted`
- `operator_supplied_context_label`
- `external_source_reference_label`
- `claim_sensitivity_label`

Problem intent metadata is not proof, not source truth, not formalization authority, and not enough to authorize formalization. It is only a scoped, redacted, metadata-only representation of what a future formalization might intend to describe.

## 7. Source / Provenance Metadata

`source_provenance` defines:

- `source_kind`
- `source_reference_label`
- `source_scope_key`
- `source_version_label`
- `source_currentness_label`
- `source_trust_label`
- `source_access_authorization_label`
- `source_content_included: false`

No raw source content may appear in this schema. Source/provenance metadata supports scope, freshness, and authorization review only; it does not make source claims true and does not authorize reads.

## 8. Formalization Candidate Metadata

`formalization_candidate` defines:

- `formalization_id`
- `target_statement_label`
- `lean_theorem_name_label`
- `theorem_statement_hash_label`
- `definition_dependency_labels`
- `hypothesis_labels`
- `conclusion_label`
- `formalization_status`
- `formalization_risk_labels`
- `natural_language_to_formal_mapping_status`

A formalization candidate may be wrong, weakened, shifted, stale, incomplete, underspecified, overconstrained, missing hypotheses, or mapped to the wrong natural-language target. It is not proof authority and not theorem truth.

## 9. Lean Environment Metadata

`lean_environment_metadata` defines:

- `lean_version_label`
- `mathlib_version_label`
- `allowed_import_labels`
- `forbidden_import_labels`
- `environment_fingerprint_label`
- `dependency_version_label`
- `execution_allowed: false`

Environment metadata does not authorize Lean execution. It is only a future compatibility/freshness label set and may be stale or incomplete.

## 10. Protected Statement Metadata

`protected_statement_metadata` defines:

- `protected_theorem_statement_span_label`
- `protected_import_span_labels`
- `protected_definition_span_labels`
- `protected_hypothesis_labels`
- `statement_mutation_allowed: false`
- `definition_mutation_requires_review: true`
- `theorem_drift_check_required: true`

Protected statement metadata exists to prevent theorem drift. It does not create editable source spans, execute checks, or authorize proof attempts.

## 11. Bounded Edit Region Metadata

Each `bounded_edit_region_metadata` entry defines:

- `edit_region_id`
- `edit_region_kind`
- `allowed_mutation_label`
- `forbidden_mutation_labels`
- `requires_review`
- `may_add_helper_lemmas_label`
- `may_change_values_label`
- `may_change_statement_label: false`
- `edit_region_content_included: false`

Bounded edit regions are metadata only. They must not include raw editable content and must not authorize mutation of theorem statements.

## 12. Proof Sketch Metadata

`proof_sketch_metadata` defines:

- `sketch_kind`
- `strategy_summary_label`
- `candidate_lemma_labels`
- `planned_subgoal_labels`
- `tactic_family_labels`
- `uncertainty_labels`
- `known_dependency_labels`
- `proof_text_included: false`
- `contains_sorry_label`
- `contains_admit_label`
- `contains_axiom_label`
- `contains_hallucinated_known_lemma_risk_label`

Proof sketch metadata is not proof authority. It is not a proof, not executable proof text, not compiler feedback, not a formal verifier result, and not final-answer material.

## 13. Assumption Metadata

Each `assumption_metadata` entry defines:

- `assumption_id`
- `assumption_label`
- `assumption_source_label`
- `assumption_status`
- `missing_assumption_risk_label`
- `implicit_assumption_risk_label`
- `assumption_requires_review`

Assumption metadata identifies possible dependencies and risks. It does not establish that assumptions are true, sufficient, current, or authorized.

## 14. Known Gap Metadata

Each `known_gap_metadata` entry defines:

- `gap_id`
- `gap_kind`
- `gap_location_label`
- `gap_severity_label`
- `gap_blocks_claim_authority: true`
- `gap_requires_formal_resolution: true`
- `gap_may_indicate_misformalization`

Known gaps block claim authority. A gap may indicate an incomplete sketch, a wrong theorem, a weakened theorem, a missing assumption, or a misformalization.

## 15. Misformalization Risk Metadata

`misformalization_risk_metadata` defines these risk labels:

- `wrong_theorem_risk`
- `weakened_statement_risk`
- `missing_hypothesis_risk`
- `definition_drift_risk`
- `natural_language_mismatch_risk`
- `overbroad_helper_lemma_risk`
- `theorem_statement_mutation_risk`
- `source_version_mismatch_risk`

These labels are risk metadata only. They do not diagnose truth and do not authorize proof attempts.

## 16. Validation Status

`validation_status` must be one of:

- `metadata_schema_only`
- `formalization_candidate_unvalidated`
- `formalization_needs_review`
- `blocked_missing_scope`
- `blocked_missing_authorization`
- `blocked_open_problem_attempt`
- `blocked_execution_not_authorized`
- `blocked_claim_authority`
- `ready_for_schema_review`

None of these statuses means proof success, Lean success, formal verification, compiler success, public readiness, benchmark readiness, prize readiness, product readiness, intelligence evidence, Turing evidence, certification evidence, or final-answer readiness.

## 17. Denied Authority Fields

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

If any denied-authority field is missing or true, future validation must fail closed.

## 18. Fail-Closed Rules

Future validation must block if:

- `source_scope` is missing or invalid
- `owner_scope`, `requester_scope`, or `target_scope` is missing
- source authorization is missing
- freshness/version labels are missing
- theorem statement hash is missing
- protected statement metadata is missing
- bounded edit regions are missing
- denied-authority fields are missing or true
- proof text or raw source content is included
- `.weslr`, global, process-default, or `tl_default` markers appear
- an open-problem attempt is implied
- Lean/prover/solver/proof-search execution is implied
- proof/public/intelligence/Turing/certification claim is implied
- final-answer/runtime/chat authority is implied
- non-JSON-safe metadata appears

Fail-closed output must remain metadata-only and must not perform reads, execution, runtime wiring, provider/model/search/advisor calls, or final-answer generation.

## 19. Relationship To Existing WESLR Helpers

- `source_scope` validates scope metadata.
- `read_authorization` should later gate source, context, artifact, upload, cache, log, and trace access.
- The scoped memory/context adapter remains separate.
- The scoped artifact/upload registry remains separate.
- Cache/log/trace scoping remains separate.
- UNKNOWN ENGINE and Cognitive Gym remain metadata-only precedents.
- This schema is not a runner and not proof authority.

This schema may later inform helper design only after review. It does not modify, replace, or invoke existing helpers.

## 20. Future Negative Tests Required

Future synthetic-only tests should cover:

- missing `source_scope`
- invalid `source_scope`
- missing owner/requester/target scope
- missing freshness/version labels
- missing theorem hash
- missing protected statement metadata
- missing edit region metadata
- true denied-authority field
- missing denied-authority field
- raw proof/source content included
- `.weslr` marker
- global/process-default/`tl_default` marker
- open-problem attempt marker
- Lean execution marker
- provider/model/search/advisor marker
- final-answer authority marker
- proof/public/intelligence/Turing/certification claim marker
- non-JSON-safe metadata
- valid metadata-only sketch

These tests must remain synthetic-only unless a later lane explicitly authorizes a broader test posture.

## 21. Relationship To Formal Proof Search Sequence

This is step A after the formal proof-search assimilation boundary:

A. current lane: `DESIGN_LEAN_FORMAL_PROBLEM_SKETCH_SCHEMA_V1`

B. next likely: `REVIEW_LEAN_FORMAL_PROBLEM_SKETCH_SCHEMA_V1`

C. later: proof-sketch population and failed-path registry design

D. later: formal verifier result envelope design

E. later: misformalization detection workflow design

F. later: rater/critic ranking boundary design

G. later: global goal/subgoal cache boundary design

H. much later: synthetic-only local Lean dry-run harness design

No step in this sequence authorizes later steps by implication. Each later lane requires separate operator authorization.

## 22. Decision

`lean_formal_problem_sketch_schema_design_ready_for_review`

## 23. Next Lane

`REVIEW_LEAN_FORMAL_PROBLEM_SKETCH_SCHEMA_V1`
