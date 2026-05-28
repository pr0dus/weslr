# WESLR Internal Evaluation Rehearsal Runner v1

## 1. Purpose and Position

WESLR is a continuity-first, governed intelligence system, not a chatbot wrapper.

The rehearsal runner exists to discover missing WESLR capabilities before live response boundary design, public UX, voice, or official-style testing.
It comes after the metadata-only dataset registry and must consume approved registry records without bypassing source classification.

The runner is not an official benchmark runner.
It is not a public scoring system.
It is not a certification system.
It is not a runtime/chat component.
It is not a voice/public UX component.

## 2. Relationship to Completed Internal Evaluation Chain

Recorded status:
- Internal Evaluation Rehearsal Program design complete at `fdb5169`
- Internal Evaluation Rehearsal Program review complete at `2f9dbf9`
- Internal Evaluation Rehearsal Program context alignment complete at workspace commit `a918c03`
- Dataset Registry design complete at `9d2fe42`
- Dataset Registry design review complete at `db28c21`
- Dataset Registry implementation complete at `735557a`
- Dataset Registry implementation review complete at `4d06b04`
- Dataset Registry context alignment complete at workspace commit `d16eaef`

The registry is now the source-governance layer.
The runner must depend on registry validation.
The runner must not load blocked records.
The runner must output internal gap reports, not official claims.

## 3. Runner Scope

### The runner may do
- read approved registry metadata records
- validate records before use
- select test families from approved metadata
- create metadata-only run plans
- execute only future explicitly-approved internal rehearsal tasks
- preserve contamination labels
- record qualitative outcomes
- map failures to capability gaps
- compare predicted vs observed failure labels
- produce internal gap reports
- produce operator review packets

### The runner must not do
- bypass registry approval
- load blocked sources
- download datasets
- inspect hidden/private/semi-private benchmark material
- use blocked answer keys
- store raw benchmark tasks
- store raw private data
- store hidden task contents
- read or write `.weslr`
- call provider/model/search/advisor systems
- wire into runtime/chat
- generate public final answers
- publish scores
- claim official results
- certify intelligence
- claim Turing-test passing
- grant UNKNOWN ENGINE authority

## 4. Runner Input Model

### Allowed future inputs
- validated registry records
- WESLR-created synthetic task descriptors
- metadata-only task family descriptors
- source governance summaries
- contamination labels
- expected output policies
- answer-key policies
- allowed-use labels
- run configuration metadata
- operator-approved run scope

### Blocked inputs
- unvalidated registry records
- blocked registry records
- raw benchmark task contents
- raw private user data
- hidden/private/semi-private task contents
- blocked answer keys
- live user conversations
- `.weslr` private state
- continuity memory contents
- provider/model outputs
- final answer text
- public score claims

## 5. Runner Output Model

### Allowed future outputs
- internal run metadata
- per-task qualitative result labels
- failure labels
- missing capability labels
- contamination-risk summaries
- evidence/currentness-gap labels
- correction-assimilation-gap labels
- abstraction/composition-gap labels
- non-cannedness-gap labels
- UNKNOWN ENGINE predicted-vs-observed comparison labels
- internal gap report
- operator review packet
- recommended next lanes

### Blocked outputs
- official score
- public benchmark result
- verified badge claim
- certified intelligence claim
- Turing-test passing claim
- IQ/intelligence claim
- public readiness claim
- final answer text
- raw private data
- raw hidden/private/semi-private benchmark material
- answer keys from blocked sources
- automatic lesson promotion
- autonomous code-change instruction

## 6. WESLR-Native Test Families

The runner design must support these test families:
- `abstraction_rule_induction`
- `compositional_reasoning`
- `contextual_rule_application`
- `evidence_currentness_reasoning`
- `memory_continuity_boundary`
- `correction_assimilation`
- `non_canned_response_formation`
- `candidate_ranking_rejection`
- `safe_final_response_envelope_behavior`
- `unknown_engine_future_state_projection`
- `turing_style_human_conversation_rehearsal`
- `uncertainty_explanation`
- `human_intent_frustration_urgency_understanding`
- `action_governance_boundary_recognition`

### Family-specific runner expectations

- `abstraction_rule_induction`
  - Future test: infer governing rule from examples.
  - Allowed sources: synthetic WESLR-created, public/open only after review.
  - Preferred synthetic strategy: rule-minimal mutation chains.
  - Result labels: `pass_internal_rehearsal`, `partial_internal_rehearsal`, `fail_internal_rehearsal`.
  - Failure labels: `abstraction_failure`, `overconfidence_failure`.
  - Missing capability: `missing_abstraction_helper`.

- `compositional_reasoning`
  - Future test: combine multiple constraints without dropping one.
  - Allowed sources: synthetic WESLR-created, public/open only after review.
  - Preferred synthetic strategy: multi-constraint synthetic prompts.
  - Result labels: `pass_internal_rehearsal`, `partial_internal_rehearsal`, `fail_internal_rehearsal`.
  - Failure labels: `composition_failure`, `unsafe_envelope_failure`.
  - Missing capability: `missing_composition_planner`.

- `contextual_rule_application`
  - Future test: apply a known rule in the correct context.
  - Allowed sources: synthetic WESLR-created, public/open only after review.
  - Preferred synthetic strategy: context-shift variants.
  - Result labels: `pass_internal_rehearsal`, `partial_internal_rehearsal`, `fail_internal_rehearsal`.
  - Failure labels: `contextual_application_failure`, `canned_or_generic_response_failure`.
  - Missing capability: `missing_context_gating`.

- `evidence_currentness_reasoning`
  - Future test: separate current evidence from stale or missing evidence.
  - Allowed sources: synthetic WESLR-created, public/open only after review.
  - Preferred synthetic strategy: time-shifted evidence sets.
  - Result labels: `pass_internal_rehearsal`, `partial_internal_rehearsal`, `fail_internal_rehearsal`.
  - Failure labels: `stale_or_missing_evidence_failure`, `overconfidence_failure`.
  - Missing capability: `missing_evidence_currentness_tracker`.

- `memory_continuity_boundary`
  - Future test: keep continuity without false memory claims.
  - Allowed sources: synthetic WESLR-created, public/open only after review.
  - Preferred synthetic strategy: local-turn continuity sequences.
  - Result labels: `pass_internal_rehearsal`, `partial_internal_rehearsal`, `fail_internal_rehearsal`.
  - Failure labels: `false_memory_or_continuity_failure`, `correction_drop_failure`.
  - Missing capability: `missing_memory_boundary_helper`.

- `correction_assimilation`
  - Future test: absorb user correction and carry it forward.
  - Allowed sources: synthetic WESLR-created, public/open only after review.
  - Preferred synthetic strategy: repeated correction pressure.
  - Result labels: `pass_internal_rehearsal`, `partial_internal_rehearsal`, `fail_internal_rehearsal`.
  - Failure labels: `correction_drop_failure`, `canned_or_generic_response_failure`.
  - Missing capability: `missing_correction_assimilation_helper`.

- `non_canned_response_formation`
  - Future test: produce specific, grounded, non-generic responses.
  - Allowed sources: synthetic WESLR-created, public/open only after review.
  - Preferred synthetic strategy: anti-template prompts.
  - Result labels: `pass_internal_rehearsal`, `partial_internal_rehearsal`, `fail_internal_rehearsal`.
  - Failure labels: `canned_or_generic_response_failure`, `uncertainty_explanation_failure`.
  - Missing capability: `missing_non_canned_response_formation`.

- `candidate_ranking_rejection`
  - Future test: choose a best next answer and reject weaker ones.
  - Allowed sources: synthetic WESLR-created, public/open only after review.
  - Preferred synthetic strategy: multi-candidate ranking pressure.
  - Result labels: `pass_internal_rehearsal`, `partial_internal_rehearsal`, `fail_internal_rehearsal`.
  - Failure labels: `candidate_ranking_failure`, `unsafe_envelope_failure`.
  - Missing capability: `missing_candidate_rejection_helper`.

- `safe_final_response_envelope_behavior`
  - Future test: assemble a safe response shape without overclaiming.
  - Allowed sources: synthetic WESLR-created, public/open only after review.
  - Preferred synthetic strategy: safe-envelope shadow scenarios.
  - Result labels: `pass_internal_rehearsal`, `partial_internal_rehearsal`, `fail_internal_rehearsal`.
  - Failure labels: `unsafe_envelope_failure`, `overconfidence_failure`.
  - Missing capability: `missing_safe_envelope_checker`.

- `unknown_engine_future_state_projection`
  - Future test: forecast likely failure zones and next gaps.
  - Allowed sources: synthetic WESLR-created only for repeated loops.
  - Preferred synthetic strategy: predicted-vs-observed mutation loops.
  - Result labels: `pass_internal_rehearsal`, `partial_internal_rehearsal`, `fail_internal_rehearsal`.
  - Failure labels: `unknown_engine_projection_mismatch`, `overconfidence_failure`.
  - Missing capability: `missing_unknown_engine_projection_comparison`.

- `turing_style_human_conversation_rehearsal`
  - Future test: sustain natural, grounded, human-facing dialogue behavior.
  - Allowed sources: synthetic WESLR-created, public/open only after review.
  - Preferred synthetic strategy: short multi-turn dialogue sequences.
  - Result labels: `pass_internal_rehearsal`, `partial_internal_rehearsal`, `fail_internal_rehearsal`.
  - Failure labels: `canned_or_generic_response_failure`, `human_intent_modeling_failure`.
  - Missing capability: `missing_human_intent_modeling`.

- `uncertainty_explanation`
  - Future test: explain what is known, unknown, and why.
  - Allowed sources: synthetic WESLR-created, public/open only after review.
  - Preferred synthetic strategy: uncertainty contrast prompts.
  - Result labels: `pass_internal_rehearsal`, `partial_internal_rehearsal`, `fail_internal_rehearsal`.
  - Failure labels: `uncertainty_explanation_failure`, `overconfidence_failure`.
  - Missing capability: `missing_uncertainty_framing`.

- `human_intent_frustration_urgency_understanding`
  - Future test: infer likely need emotionally and operationally.
  - Allowed sources: synthetic WESLR-created, public/open only after review.
  - Preferred synthetic strategy: intent/frustration/urgency variants.
  - Result labels: `pass_internal_rehearsal`, `partial_internal_rehearsal`, `fail_internal_rehearsal`.
  - Failure labels: `human_intent_modeling_failure`, `action_governance_failure`.
  - Missing capability: `missing_human_intent_modeling`.

- `action_governance_boundary_recognition`
  - Future test: know what may be proposed versus what needs approval.
  - Allowed sources: synthetic WESLR-created, public/open only after review.
  - Preferred synthetic strategy: authority-boundary prompts.
  - Result labels: `pass_internal_rehearsal`, `partial_internal_rehearsal`, `fail_internal_rehearsal`.
  - Failure labels: `action_governance_failure`, `unsafe_envelope_failure`.
  - Missing capability: `missing_action_governance_boundary`.

## 7. Run Phases

### Phase 0 — Preflight
- verify repo/root/session if implemented
- verify registry records
- verify no blocked source
- verify no direct live/runtime/public/voice lane
- verify `official_claim_allowed=false`
- verify `public_claim_allowed=false`
- verify UNKNOWN ENGINE has no authority

### Phase 1 — Run Plan Construction
- build metadata-only run plan
- select approved records
- select test families
- preserve contamination labels
- define expected output policy
- define allowed qualitative labels

### Phase 2 — Controlled Internal Execution
- future execution only after separate implementation/review approval
- no benchmark downloading
- no blocked sources
- no runtime/chat/public UX
- no provider/model/search/advisor calls unless separately designed and approved
- no official scoring

### Phase 3 — Outcome Normalization
- normalize outcomes into qualitative labels
- preserve uncertainty
- separate incorrect, unsupported, unsafe, overconfident, generic, and incomplete failures
- avoid official score language

### Phase 4 — Gap Mapping
- map failures to capability gaps
- aggregate repeated failures
- identify missing helper categories
- identify reasoning/cognition gaps
- identify evidence/currentness gaps
- identify continuity/correction gaps
- identify non-canned response gaps

### Phase 5 — Review Packet and Next-Lane Recommendation
- produce internal review packet
- recommend gap-closure lanes
- block public/live/voice/official-claim jumps
- require operator review before any implementation expansion

## 8. Qualitative Result Labels

Allowed result labels:
- `pass_internal_rehearsal`
- `partial_internal_rehearsal`
- `fail_internal_rehearsal`
- `blocked_by_registry`
- `blocked_by_source_governance`
- `blocked_by_contamination`
- `blocked_by_answer_key_policy`
- `blocked_by_private_data`
- `blocked_by_hidden_material`
- `blocked_by_runtime_boundary`
- `blocked_by_official_claim_boundary`
- `needs_operator_review`
- `inconclusive_internal_rehearsal`

These are internal labels only.
They must not be presented as official scores, benchmark results, intelligence scores, certifications, or public-readiness claims.

## 9. Failure and Gap Labels

Failure labels:
- `abstraction_failure`
- `composition_failure`
- `contextual_application_failure`
- `stale_or_missing_evidence_failure`
- `false_memory_or_continuity_failure`
- `correction_drop_failure`
- `canned_or_generic_response_failure`
- `candidate_ranking_failure`
- `unsafe_envelope_failure`
- `overconfidence_failure`
- `uncertainty_explanation_failure`
- `human_intent_modeling_failure`
- `action_governance_failure`
- `unknown_engine_projection_mismatch`
- `contamination_boundary_failure`
- `answer_key_policy_failure`
- `source_governance_failure`

Missing capability labels:
- `missing_abstraction_helper`
- `missing_composition_planner`
- `missing_context_gating`
- `missing_evidence_currentness_tracker`
- `missing_memory_boundary_helper`
- `missing_correction_assimilation_helper`
- `missing_non_canned_response_formation`
- `missing_candidate_rejection_helper`
- `missing_safe_envelope_checker`
- `missing_uncertainty_framing`
- `missing_human_intent_modeling`
- `missing_action_governance_boundary`
- `missing_unknown_engine_projection_comparison`
- `missing_gap_compression_helper`

## 10. UNKNOWN ENGINE Runner Role

UNKNOWN ENGINE is a bounded internal helper only.

### Allowed runner-related roles
- predict likely failure zones before a run
- propose synthetic mutation categories
- suggest qualitative failure labels
- compare predicted vs observed failure labels
- compress repeated failure patterns into candidate gaps
- suggest next test families

### Forbidden roles
- no authority
- no source approval authority
- no license approval authority
- no truth-certification authority
- no official evaluator role
- no benchmark score authority
- no future-certainty claims
- no automatic lesson promotion
- no autonomous self-modification
- no runtime/live authority
- no permission to use blocked sources
- no permission to reconstruct hidden benchmark tasks
- no permission to promote lessons without review
- no public-readiness authority

## 11. Contamination and Source Governance

The runner must consume registry contamination labels.
It must preserve source lineage.
It must separate development tasks from sealed internal evaluation.
It must block repeated public eval tuning from being treated as clean evaluation.
It must prefer synthetic WESLR-created tasks for repeated loops.
It must block semi-private/private/hidden sources.
It must block unknown-license sources until reviewed.
It must block generated mutations from blocked sources.
It must block raw private user data.

## 12. Answer-Key and Expected Output Governance

The runner must consume answer-key policy from the registry.
It must not store blocked answer keys.
It must not expose sealed expected outputs to development loops.
It must not leak expected outputs into future training/development.
Synthetic expected outputs may be used only under WESLR-created task definitions.
Result artifacts must track policy labels, not raw blocked answer-key content.

## 13. Internal Run Record Schema

Future run record fields:
- `runner_version`
- `run_id`
- `run_purpose`
- `run_scope`
- `registry_record_ids`
- `source_type_summary`
- `contamination_summary`
- `task_family_summary`
- `operator_approval_required`
- `official_claim_allowed=false`
- `public_claim_allowed=false`
- `runtime_authority_allowed=false`
- `voice_authority_allowed=false`
- `unknown_engine_authority_allowed=false`
- `result_labels`
- `failure_labels`
- `missing_capability_labels`
- `predicted_failure_labels`
- `observed_failure_labels`
- `gap_discovery_labels`
- `recommended_next_lanes`
- `blocked_next_lanes`
- `notes_redacted`

Require:
- metadata-only
- JSON-safe
- no raw private data
- no raw benchmark task content
- no hidden/private/semi-private task content
- no blocked answer-key content
- no final answer text

## 14. Gap Report Schema

Future gap report fields:
- `report_version`
- `run_id`
- `summary_status`
- `total_records_considered`
- `total_records_blocked`
- `total_tasks_planned`
- `total_tasks_completed`
- `result_label_counts`
- `failure_label_counts`
- `missing_capability_counts`
- `contamination_risk_summary`
- `source_governance_summary`
- `answer_key_policy_summary`
- `unknown_engine_projection_summary`
- `repeated_failure_patterns`
- `recommended_gap_closure_lanes`
- `blocked_public_claims`
- `blocked_live_or_voice_lanes`
- `operator_review_required`
- `notes_redacted`

Require:
- internal-only
- qualitative
- non-official
- no public score
- no certified intelligence claim
- no Turing-test passing claim
- no raw private/hidden/blocked content

## 15. Runner Validation Rules

Future runner implementation must fail closed if:
- registry record validation fails
- registry record is blocked
- source_type is unknown
- license_status is unknown
- exposure_level is semi_private/private/hidden
- contamination risk is high/extreme without explicit review handling
- answer_key_policy blocks use
- raw_private_data_allowed is true
- hidden_material_allowed is true
- official_claim_allowed is true
- public_claim_allowed is true
- runtime_authority_allowed is true
- voice_authority_allowed is true
- UNKNOWN ENGINE is assigned authority
- recommended next lane jumps directly to live/runtime/public/voice work
- recommended next lane jumps directly to official benchmark/Turing/intelligence/certification claims
- generated mutation comes from blocked source
- unknown-license source is marked allowed before review
- mapped test family is unknown

## 16. Relationship to Future Implementation

This design must be reviewed before implementation.
Implementation must be pure Python.
Implementation must be deterministic.
Implementation must be metadata-only.
Implementation must use dataset registry validation.
Implementation must include tests for all blocked paths.
Implementation must not perform network/file benchmark downloads.
Implementation must not execute external providers/models/search/advisors.
Implementation must not read/write `.weslr`.
Implementation must not integrate with `chat_responder.py` or `main.py`.
Implementation review must happen before any baseline run.

## 17. Blocked Behaviors in This Lane

- no implementation
- no runner code
- no baseline run
- no dataset downloads
- no benchmark execution
- no raw task storage
- no hidden/private/semi-private benchmark use
- no answer-key leakage
- no raw private user data
- no `.weslr` IO
- no provider/model/search/advisor calls
- no runtime/chat wiring
- no final-answer generation
- no public UX
- no voice work
- no official benchmark/Turing/intelligence/certification claims
- no UNKNOWN ENGINE authority
- no automatic lesson promotion
- no autonomous self-modification
- no post-Level-7 live boundary design yet

## 18. Required Future Lanes

1. `REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1`
2. `IMPLEMENT_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1`
3. `REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1`
4. `RUN_WESLR_INTERNAL_EVALUATION_BASELINE_V1`
5. `REVIEW_WESLR_INTERNAL_EVALUATION_BASELINE_RESULT_V1`
6. `DESIGN_WESLR_CAPABILITY_GAP_CLOSURE_PLAN_V1`
7. `IMPLEMENT_SELECTED_MISSING_HELPERS_OR_REASONING_EXPANSIONS_V1`
8. `RERUN_WESLR_INTERNAL_EVALUATION_REHEARSAL_V1`
9. Only then return to `DESIGN_POST_LEVEL_7_SAFE_LIVE_RESPONSE_BOUNDARY_V1`

## 19. Validation Plan

For this design lane:
- repo root/branch/HEAD handshake
- release gate
- release check
- confirm protected files untouched
- confirm only allowed files changed
- confirm no runner code, no baseline, no dataset download, no benchmark execution, no runtime/chat/public/voice behavior, and no official claims
