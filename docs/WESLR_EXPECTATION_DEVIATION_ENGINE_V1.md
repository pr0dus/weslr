# WESLR Expectation-Deviation Engine V1

## 1. Executive doctrine

**Definition:** WESLR Expectation-Deviation Engine V1.

The Expectation-Deviation Engine is a side-cognition and architecture design boundary for comparing what a system expected to happen with what was actually observed in metadata, reports, or structured outcomes.

It is not runtime cognition authority.
It is not tool execution authority.
It is not proof/correctness authority.
It is not a blocker to Batch B unless later review finds a real dependency.

Core rule: the engine may describe expectations, observations, deviations, and possible structural implications, but it must not execute tools, mutate files, call models/providers, or wire itself into chat/runtime.

## 2. Boundary position

Pipeline:

proposal / design intent / validation result / report / observation
→ expectation model metadata
→ observation model metadata
→ deviation comparison metadata
→ classification metadata
→ review surface later
→ implementation only after explicit approval

This design does not execute any runtime action.

## 3. Why this is needed

- systems often fail by drifting from expected structure rather than by one obvious fault
- expectations and observations need to be compared without turning that comparison into authority
- architecture review benefits from explicit deviation classes
- design-time comparison can reveal missing dependencies, overbroad claims, and boundary drift
- a structured deviation surface can help future review without becoming a hidden runtime judge

## 4. Expectation source classes

- `design_expectation`
- `implementation_expectation`
- `validation_expectation`
- `review_expectation`
- `operator_expectation`
- `owner_expectation`
- `policy_expectation`
- `workflow_expectation`
- `artifact_expectation`
- `unknown_expectation_source`

## 5. Observation source classes

- `metadata_observation`
- `validation_result_observation`
- `report_observation`
- `artifact_observation`
- `workflow_observation`
- `review_observation`
- `operator_report_observation`
- `owner_report_observation`
- `policy_observation`
- `unknown_observation_source`

## 6. Deviation classes

- `no_deviation_detected`
- `missing_expected_field`
- `extra_unexpected_field`
- `status_mismatch`
- `authority_mismatch`
- `scope_mismatch`
- `order_mismatch`
- `dependency_mismatch`
- `claim_mismatch`
- `policy_mismatch`
- `boundary_mismatch`
- `review_mismatch`
- `unknown_deviation`

## 7. Deviation severity levels

- `none`
- `low_metadata_difference`
- `medium_structural_difference`
- `high_boundary_difference`
- `critical_authority_or_claim_difference`
- `blocked_unknown_severity`

## 8. Expectation-deviation statuses

- `not_evaluated`
- `aligned`
- `deviation_detected`
- `needs_clarification`
- `needs_review`
- `blocked_by_policy`
- `blocked_by_unknown_source`
- `blocked_by_claim_risk`
- `blocked_by_authority_risk`
- `unknown_status`

## 9. Expectation-deviation packet shape

Future packet fields:

- `expectation_deviation_packet_id`
- `expectation_source_class`
- `observation_source_class`
- `expectation_summary`
- `observation_summary`
- `expected_fields`
- `observed_fields`
- `missing_fields`
- `extra_fields`
- `deviation_classes`
- `deviation_severity`
- `deviation_status`
- `confidence_status`
- `policy_status`
- `authority_status`
- `claim_status`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `tool_execution_allowed`
- `public_claim_allowed`
- `proof_claim_allowed`
- `learning_claimed`
- `owner_review_required`
- `operator_review_required`
- `recommended_next_check`
- `safe_metadata`

## 10. Engine rules

- compare metadata, not live runtime state
- do not infer authority from expectation alignment
- do not infer correctness from structural similarity
- do not convert deviations into automatic mutation triggers
- do not convert deviations into hidden scoring
- do not call models/providers/search/advisors/tools
- do not write files or `.weslr`
- do not wire into chat/runtime
- do not emit public claims
- do not emit proof/correctness/production readiness claims
- do not treat uncertainty as a pass
- do not treat alignment as approval
- do not treat deviation as execution permission

## 11. Relationship to Batch B boundaries

The Expectation-Deviation Engine is a side surface that can help later review of Batch B metadata helpers, but it is not part of the Batch B execution path.

If later review finds a real dependency, it should be handled as a separate review item.

It does not override:
- Code Validation Runner
- Patch Feedback Loop
- Tool-Use Executor Boundary
- Autonomous Debugging Dry-Run Boundary
- Document-to-Action Boundary
- Action Authority Boundary
- Rollback and Reversal Boundary
- Owner Operator Workflow Engine
- Artifact Exporter Boundary

## 12. Relationship to design review

Expectation/deviation review may highlight:
- missing expected fields
- overly broad authority language
- claim drift
- order mismatches between boundaries
- dependency gaps
- review routing issues
- status drift between design and implementation

These findings are review inputs only.

## 13. Relationship to implementation

Future implementation should remain metadata-only and pure.

Potential future helper path:
`weslr/expectation_deviation_engine.py`

But no helper is authorized by this design alone.

## 14. Initial examples

1. Expected boundary status matches observed metadata and yields no deviation.
2. A missing expected field is recorded as a structural deviation only.
3. An unexpected authority field is recorded as an authority mismatch.
4. A claim drift between design and report is recorded as a claim mismatch.
5. A dependency order mismatch is recorded without changing execution order.
6. A policy mismatch is surfaced for review, not automatic repair.
7. An unknown source is blocked, not promoted.
8. Status alignment does not imply correctness.
9. Deviation detection does not imply runtime authority.
10. Side-cognition review remains separate from Batch B implementation.

## 15. Future helper design

Recommended future helper:
`weslr/expectation_deviation_engine.py`

Future APIs:
- `build_expectation_deviation_packet_v1(...)`
- `classify_expectation_source_v1(...)`
- `classify_observation_source_v1(...)`
- `compare_expectations_to_observations_v1(packet)`
- `classify_deviation_v1(packet)`
- `select_expectation_deviation_status_v1(packet)`
- `validate_expectation_deviation_packet_v1(packet)`
- `summarize_expectation_deviation_packet_v1(packet)`
- `to_expectation_deviation_json_safe_v1(value)`
- `build_initial_expectation_deviation_examples_v1()`

## 16. Future implementation strategy

Recommended phases:

1. metadata-only packet builder
2. synthetic examples
3. validation helper
4. expectation source classifier
5. observation source classifier
6. deviation comparator
7. status selector
8. summary helper
9. side-cognition review surface
10. metadata-helper implementation only

## 17. Validation and failure policy

Future validator should fail if:
- runtime_authority is true
- writes_state is true
- model_provider_used is true
- tool_execution_allowed is true
- public_claim_allowed is true
- proof_claim_allowed is true
- learning_claimed is true
- hidden prompt / raw private / secret fields appear
- unknown expectation source is promoted as authoritative
- unknown observation source is promoted as authoritative
- unknown deviation is promoted as alignment
- authority mismatch is ignored
- claim mismatch is ignored
- policy mismatch is ignored
- deviation is used to authorize runtime behavior
- deviation is used to prove correctness
- deviation is used to prove public readiness
- deviation is used to create public claims

## 18. Boundaries and non-claims

This design does not implement cognition.
It does not execute tools.
It does not call models/providers.
It does not write files.
It does not mutate state.
It does not wire into chat/runtime.
It does not write `.weslr`.
It does not authorize any runtime behavior.
It does not claim implementation readiness, proof, correctness, legal compliance, security certification, production readiness, public readiness, AGI, consciousness, sentience, or Turing success.

## 19. Recommended next lane

Recommend:
`REVIEW_WESLR_EXPECTATION_DEVIATION_ENGINE_V1`

After review, return to:
`IMPLEMENT_WESLR_PATCH_FEEDBACK_LOOP_BOUNDARY_V1`

## 20. Final judgment

Use one:
- `expectation_deviation_engine_design_ready_for_review`
- `expectation_deviation_engine_design_needs_review`
- `expectation_deviation_engine_design_blocked`

Recommended judgment:
`expectation_deviation_engine_design_ready_for_review`
