# WESLR Internal Evaluation Dataset Registry v1

## 1. Purpose and Position

WESLR is a continuity-first, governed intelligence system, not a chatbot wrapper.

This dataset registry exists to protect internal evaluation rehearsal from contamination, unsafe sources, hidden benchmark use, public overclaiming, and raw private data use.

Internal evaluation comes before live boundary design, public UX, voice, or official-style claims.
The registry is a prerequisite for future rehearsal runner design.
The registry is not an evaluator, runner, judge, benchmark executor, downloader, or official scoring system.

## 2. Relationship to Internal Evaluation Rehearsal Program

Reference documents:
- `docs/WESLR_INTERNAL_EVALUATION_REHEARSAL_PROGRAM_V1.md`
- `docs/WESLR_INTERNAL_EVALUATION_REHEARSAL_PROGRAM_REVIEW_V1.md`

Recorded status:
- design completed at `fdb5169`
- review completed at `2f9dbf9`
- review judgment: `internal_evaluation_rehearsal_program_design_valid_ready_for_context_alignment`
- context alignment completed at workspace commit `a918c03`
- next substantive lane is this dataset registry design

This registry supports later dataset selection.
It blocks unsafe sources.
It prepares for later implementation.
It must not itself run tests.

## 3. Registry Scope

### May track
- dataset_id
- dataset_name
- source_family
- source_type
- exposure_level
- license_status
- allowed_use
- blocked_use
- contamination_risk
- official_claim_allowed
- development_allowed
- sealed_internal_eval_allowed
- repeated_use_policy
- answer_key_policy
- synthetic_generation_policy
- unknown_engine_allowed_role
- required_review_status
- recommended_next_lane

### Must not track
- raw benchmark task contents
- raw private user data
- hidden/private/semi-private task contents
- answer keys for blocked sources
- provider/model outputs
- live user conversations
- `.weslr` private state
- continuity memory contents
- final answer text

## 4. Source Classification

### `public_open`
- allowed_use: `development_allowed` or `sealed_internal_eval_allowed` only after license/source review
- blocked_use: hidden leakage, answer-key misuse, public overclaiming
- development_allowed: yes after review
- sealed_internal_eval_allowed: yes after review
- repeated_use_allowed: limited, logged
- contamination_risk: low to medium
- license_review_required: yes
- official_claim_allowed: no

### `synthetic_weslr_created`
- allowed_use: development and sealed internal eval
- blocked_use: none by source class, subject to safety rules
- development_allowed: yes
- sealed_internal_eval_allowed: yes
- repeated_use_allowed: yes, preferred for loops
- contamination_risk: low
- license_review_required: no external license, but generation policy review still required
- official_claim_allowed: no

### `semi_private`
- allowed_use: blocked by default
- blocked_use: yes unless through official external submission/evaluation process
- development_allowed: no
- sealed_internal_eval_allowed: only through official process
- repeated_use_allowed: no
- contamination_risk: high
- license_review_required: yes
- official_claim_allowed: only through official process and verification

### `private`
- allowed_use: blocked by default
- blocked_use: yes unless through official external submission/evaluation process
- development_allowed: no
- sealed_internal_eval_allowed: only through official process
- repeated_use_allowed: no
- contamination_risk: high
- license_review_required: yes
- official_claim_allowed: only through official process and verification

### `hidden_blocked`
- allowed_use: blocked
- blocked_use: yes
- development_allowed: no
- sealed_internal_eval_allowed: no
- repeated_use_allowed: no
- contamination_risk: extreme
- license_review_required: yes, but blocked regardless until official process permits
- official_claim_allowed: no

### `unknown_license_blocked_until_reviewed`
- allowed_use: blocked until reviewed
- blocked_use: yes until review completes
- development_allowed: no
- sealed_internal_eval_allowed: no until reviewed
- repeated_use_allowed: no
- contamination_risk: unknown/high
- license_review_required: yes
- official_claim_allowed: no

### `raw_private_user_data_blocked`
- allowed_use: blocked
- blocked_use: yes
- development_allowed: no
- sealed_internal_eval_allowed: no
- repeated_use_allowed: no
- contamination_risk: extreme
- license_review_required: not sufficient; always blocked
- official_claim_allowed: no

### `generated_mutation_from_allowed_source`
- allowed_use: development and sealed internal eval if lineage is preserved
- blocked_use: none if source lineage and policy remain intact
- development_allowed: yes
- sealed_internal_eval_allowed: yes
- repeated_use_allowed: yes with lineage logging
- contamination_risk: low to medium depending on source exposure history
- license_review_required: yes for the base source when applicable
- official_claim_allowed: no

### `generated_mutation_from_blocked_source_blocked`
- allowed_use: blocked
- blocked_use: yes
- development_allowed: no
- sealed_internal_eval_allowed: no
- repeated_use_allowed: no
- contamination_risk: extreme
- license_review_required: no, because the base source remains blocked
- official_claim_allowed: no

## 5. Allowed Use Labels

Allowed use labels:
- `development_allowed`
- `sealed_internal_eval_allowed`
- `synthetic_mutation_allowed`
- `metadata_only_reference_allowed`
- `source_review_only`
- `blocked`

No label grants:
- official result authority
- public score authority
- verified badge authority
- Turing-test authority
- intelligence certification authority
- live runtime authority

## 6. Contamination Risk Model

Contamination risk labels:
- `none`
- `low`
- `medium`
- `high`
- `extreme`
- `unknown`

Rules:
- repeated public eval exposure increases contamination risk
- public training/task examples used for development must not be treated as sealed evaluation
- synthetic tasks can lower repeated-loop contamination but must preserve generation lineage
- hidden/private/semi-private exposure is high or extreme and blocked
- unknown-license or unclear provenance is unknown/high and blocked until reviewed
- any answer-key leakage is high/extreme and must block use

## 7. Answer Key and Expected Output Policy

Define:
- `expected_output_available`
- `expected_output_allowed_for_development`
- `expected_output_allowed_for_sealed_eval`
- `expected_output_blocked`
- `answer_key_leakage_risk`

Rules:
- answer keys from blocked sources must not be stored or used
- public/open expected outputs may be used only if license/source review permits
- sealed evaluation expected outputs must be protected from development loops
- synthetic expected outputs may be used if generated by WESLR-created task definitions
- registry tracks policy, not raw answer-key content

## 8. Dataset Review Status

Review statuses:
- `unreviewed`
- `source_review_passed`
- `license_review_passed`
- `blocked_by_license`
- `blocked_by_exposure`
- `blocked_by_private_data`
- `blocked_by_hidden_material`
- `blocked_by_contamination`
- `approved_for_development`
- `approved_for_sealed_internal_eval`
- `approved_for_synthetic_mutation_only`

Each status must specify:
- who or what may approve in future
- what evidence is required
- what remains blocked
- whether use is reversible

## 9. WESLR-Native Test Family Mapping

The registry must support mapping datasets/tasks to these WESLR-native test families:
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

For each family:
- public/open sources may be used only if license/source review permits
- synthetic sources are preferred for repeated development
- sealed evaluation is appropriate only when source rules allow
- UNKNOWN ENGINE mutation may be used only as a bounded internal helper for synthetic mutation planning
- contamination risks must be recorded explicitly

## 10. UNKNOWN ENGINE Registry Role

UNKNOWN ENGINE is a bounded internal helper only.

Allowed registry-related roles:
- propose synthetic task families
- propose mutation categories
- predict likely failure zones
- compare predicted vs observed failure labels in later runs
- suggest gap categories
- compress repeated failure patterns into candidate capability gaps

Forbidden roles:
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

## 11. Internal Registry Record Schema

Future registry record schema:
- `registry_version`
- `dataset_id`
- `dataset_name`
- `dataset_description_redacted`
- `source_family`
- `source_type`
- `exposure_level`
- `license_status`
- `source_review_status`
- `allowed_use_labels`
- `blocked_use_labels`
- `development_allowed`
- `sealed_internal_eval_allowed`
- `synthetic_mutation_allowed`
- `repeated_use_policy`
- `contamination_risk`
- `answer_key_policy`
- `expected_output_policy`
- `official_claim_allowed=false`
- `public_claim_allowed=false`
- `hidden_material_allowed=false`
- `raw_private_data_allowed=false`
- `unknown_engine_role`
- `mapped_test_families`
- `required_pre_run_checks`
- `recommended_next_lane`
- `notes_redacted`

Requirements:
- metadata-only record
- JSON-safe future implementation
- no raw private data
- no raw benchmark task content
- no hidden task content
- no answer-key content for blocked sources
- `official_claim_allowed` must always be false for internal rehearsal records

## 12. Registry Validation Rules

Validation rules:
- fail closed if `source_type` is unknown
- fail closed if `license_status` is unknown
- fail closed if `exposure_level` is semi_private/private/hidden
- fail closed if `raw_private_data_allowed` is true
- fail closed if `hidden_material_allowed` is true
- fail closed if `official_claim_allowed` is true
- fail closed if `public_claim_allowed` is true
- fail closed if `answer_key_policy` allows blocked answer keys
- fail closed if UNKNOWN ENGINE is assigned authority
- fail closed if `recommended_next_lane` jumps directly to live/runtime/public/voice work

## 13. Relationship to Future Runner

- dataset registry implementation must happen before rehearsal runner design
- rehearsal runner must consume only approved metadata records
- rehearsal runner must not bypass source classification
- rehearsal runner must not load blocked sources
- rehearsal runner must preserve contamination labels
- rehearsal runner must output gap reports, not official claims

## 14. Blocked Behaviors in This Lane

- no implementation
- no dataset downloads
- no benchmark execution
- no runner
- no baseline run
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

## 15. Required Future Lanes

1. `REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_V1`
2. `IMPLEMENT_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_V1`
3. `REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_V1`
4. `DESIGN_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1`
5. `IMPLEMENT_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1`
6. `REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1`
7. `RUN_WESLR_INTERNAL_EVALUATION_BASELINE_V1`
8. `REVIEW_WESLR_INTERNAL_EVALUATION_BASELINE_RESULT_V1`
9. `DESIGN_WESLR_CAPABILITY_GAP_CLOSURE_PLAN_V1`
10. `IMPLEMENT_SELECTED_MISSING_HELPERS_OR_REASONING_EXPANSIONS_V1`
11. `RERUN_WESLR_INTERNAL_EVALUATION_REHEARSAL_V1`
12. Only then return to `DESIGN_POST_LEVEL_7_SAFE_LIVE_RESPONSE_BOUNDARY_V1`

## 16. Validation Plan

Validation for this design lane:
- repo root/branch/HEAD handshake
- release gate
- release check
- confirm protected files untouched
- confirm only allowed files changed
- confirm no implementation files added
- confirm no dataset downloads
- confirm no benchmark data files added
- confirm no `.weslr` access
- confirm no runtime/chat wiring
- confirm no provider/model/search/advisor calls
