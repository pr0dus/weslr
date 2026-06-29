# WESLR ARC REPLAY SCORING AND PER-TASK PROVENANCE REPAIR REVIEW V1

## 1. Executive verdict
`arc_replay_scoring_and_per_task_provenance_repair_review_valid_with_notes`

## 2. Review scope
- Local review only.
- Reviewed repair artifact: `docs/WESLR_ARC_REPLAY_SCORING_AND_PER_TASK_PROVENANCE_REPAIR_V1.md`
- Reviewed implementation: `weslr/arc_generative_bridge_v5_replay.py`
- Reviewed relevant unchanged dependencies: `weslr/arc_controlled_answer_candidate_generator.py`, `weslr/arc_ledger_deservedness_assembler.py`
- Reviewed replay tests plus generator/assembler suites.
- No repair edits outside replay/report/release-gate scope.

## 3. Scoring semantics finding review
Review result: valid.

Confirmed from code/history described in the repair artifact:
- pre-repair exact/wrong scoring for deserved tasks was assigned by a salted-hash RNG branch, not by real candidate-output vs expected-output comparison
- all 8 V5 groups shared that replay scorer path because scoring was implemented centrally in `_process_task(...)`, not family-by-family
- no pre-repair family-specific real expected-output comparison path was found in replay
- therefore pre-repair `deserved_exact` / `deserved_but_wrong` were synthetic stress labels, not verified correctness evidence
- hard-stop and threshold conclusions derived from those labels must be downgraded
- ledger/safety conclusions remain separately usable because generator and assembler decisions are upstream of post-ledger scoring

## 4. RNG/hash removal review
Review result: valid.

Confirmed in current replay module:
- no replay scoring path uses Python salted `hash()` for exact/wrong labels
- no replay scoring path uses `random.seed`, `random.random`, or other RNG for exact/wrong labels
- no RNG/random fallback path exists for exact/wrong labels
- no RNG/random tie-breaker path exists for exact/wrong labels
- no RNG/random candidate-selection influence exists for correctness labels in replay
- deterministic randomized stress labels are not being emitted as `deserved_exact` / `deserved_but_wrong`
- current `synthetic_randomized_stress_label_task_ids` list remains present as provenance surface but is empty under the repaired implementation

## 5. Real scoring / unscorable behavior review
Review result: valid.

Confirmed behavior:
- exact/wrong labels are emitted only from deterministic post-ledger comparison in `_score_post_ledger(...)`
- expected/scoring output is used only after ledger decision
- expected/scoring output does not enter generation
- expected/scoring output does not enter deservedness
- when candidate output is unavailable or ambiguous, the task becomes `unscorable_due_to_missing_candidate_output`
- unscorable tasks are not counted as `deserved_exact` or `deserved_but_wrong`
- the repaired path also correctly supports `undeserved_exact` if a non-deserved candidate nevertheless matches the expected/scoring output

Note:
- current live V5 tasks do not expose candidate outputs, so the repaired scorer is honest but mostly unscorable in production replay usage today

## 6. All-8-groups scoring classification review
Review result: valid.

Confirmed every V5 group has explicit scoring classification:
- `v4_rival_grammar_replay_6`
- `v4_beautiful_wrong_rule_replay_6`
- `v4_composed_transform_replay_6`
- `v4_negative_evidence_replay_6`
- `v4_helper_trap_replay_6`
- `object_graph_correspondence_6`
- `invariant_symmetry_ambiguity_6`
- `mdl_simplicity_trap_6`

Confirmed current live classification:
- all 8 groups are `unscorable_due_to_missing_candidate_output`
- expected/scoring output exists for all 8 groups
- candidate output surface is missing for all 8 groups
- candidate-output surface design is the next blocker if this repair is accepted

## 7. Per-task provenance review
Review result: valid.

Confirmed per-task outcome records are emitted and include:
- `task_id`
- `group_id`
- `candidate_generated`
- `candidate_blocked`
- `ledger_decision`
- `candidate_deserved`
- `candidate_not_deserved`
- `safe_failure`
- `post_ledger_scoring_status`
- `deserved_exact`
- `deserved_but_wrong`
- `undeserved_exact`
- `hard_stop_triggered`
- `hard_stop_reason_list`
- `post_ledger_scoring_mechanism`
- `post_ledger_scoring_seed_or_determinism_note`
- `rng_or_hash_influenced_scoring`
- `rng_or_hash_influence_type`
- `candidate_output_available`
- `expected_output_available`
- `candidate_trace_provenance`
- `scoring_mechanism_classification`

Durability judgment:
- this is sufficient to preserve replay scoring provenance for future reports
- this is a meaningful repair over prior aggregate-only ambiguity

## 8. Named task-id lists review
Review result: valid.

Confirmed named task-id lists are derived from per-task records:
- `candidate_generated_task_ids`
- `candidate_deserved_task_ids`
- `candidate_not_deserved_task_ids`
- `safe_failure_task_ids`
- `deserved_exact_task_ids`
- `deserved_but_wrong_task_ids`
- `undeserved_exact_task_ids`
- `unscorable_task_ids`
- `synthetic_randomized_stress_label_task_ids`
- `rng_influenced_scoring_task_ids`
- `hard_stop_task_ids`

Confirmed aggregate consistency against live replay output:
- attempted: 48
- candidate generated: 48
- candidate deserved: 12
- candidate not deserved: 36
- safe failure: 36
- deserved exact: 0
- deserved but wrong: 0
- undeserved exact: 0
- unscorable: 48
- RNG-influenced scoring: 0

## 9. Prior conclusion downgrade review
Review result: valid.

Correctly preserved as still usable:
- candidate generated
- candidate deserved
- candidate not deserved
- safe failure
- rival-context safe failure
- protected-boundary checks
- generator/assembler gating and safety metrics
- group-level candidate-deserved vs safe-failure distribution

Correctly downgraded:
- `deserved_exact`
- `deserved_but_wrong`
- `task_exact_count`
- `task_exact_rate`
- hard-stop conclusions based on `deserved_but_wrong`
- threshold conclusions based on exact/wrong counts
- downstream claims about specific wrong-ID sets sourced from pre-repair scoring

Review note:
- this downgrade is necessary and appropriately narrow; it does not erase the ledger/safety chain wholesale

## 10. Regression review
Review result: no material regression found within the declared lane.

Confirmed:
- generator deservedness logic unchanged
- assembler deservedness logic unchanged
- rival repair behavior not silently changed
- protected files unchanged
- no runtime wiring
- no emitter implementation
- no final-answer behavior
- no `.weslr`
- no external calls

Files changed in the repair lane are limited to:
- `weslr/arc_generative_bridge_v5_replay.py`
- `weslr/tests/test_arc_generative_bridge_v5_replay_v1.py`
- `weslr/tests/release_gate_v1.py`
- `docs/WESLR_ARC_REPLAY_SCORING_AND_PER_TASK_PROVENANCE_REPAIR_V1.md`

## 11. Test adequacy review
Review result: valid with one note.

Confirmed test coverage includes:
- all exact/wrong replay paths
- all 8 groups explicit scoring classification
- no Python salted hash in correctness scoring
- no RNG fallback/tie-breaker/candidate-selection influence
- post-ledger-only expected-output comparison
- unscorable handling
- per-task records
- named task-id lists
- candidate trace provenance
- aggregate consistency
- cross-process durability check

Note:
- the tests are strong for the semantic repair itself
- they do not prove real scoring on live V5 tasks yet, because the current live tasks remain unscorable by design after the repair
- that is acceptable for this lane because candidate-output surface design was explicitly deferred
- no extra narrow test-repair lane is required before moving to candidate-output surface design

## 12. Safety and expected-answer boundary
Review result: preserved.

Confirmed:
- expected/scoring answers remain outside generation and deservedness
- scoring happens only after ledger decision
- no generator/assembler deservedness repair was introduced in this lane
- no runtime/emitter/final-answer wiring was added
- protected boundaries remain intact

## 13. Recommended next safe local follow-up
`DESIGN_ARC_CANDIDATE_OUTPUT_SURFACE_FOR_REAL_SCORING_V1`

Why:
- replay scoring semantics are now honest
- per-task provenance is durable
- the remaining blocker is missing candidate-output surface for real post-ledger correctness comparison across live V5 groups
