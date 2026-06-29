# WESLR ARC REPLAY SCORING AND PER-TASK PROVENANCE REPAIR V1

## 1. Executive verdict
`arc_replay_scoring_and_per_task_provenance_repaired_but_needs_review`

## 2. Scoring semantics audit
Observed in the pre-repair replay path:
- every task carried `synthetic_expected_answer_for_scoring_only`
- generator ran before ledger
- ledger decision ran before exact/wrong scoring
- exact/wrong scoring for deserved tasks was assigned by:
  - `random.seed(hash(task_id) % 2**31)`
  - `random.random() < 0.5`
- therefore pre-repair `deserved_exact` and `deserved_but_wrong` were not correctness labels
- they were salted-hash-dependent synthetic stress labels

Post-repair semantics:
- no replay scoring path uses Python salted `hash()`
- no replay scoring path uses RNG/randomness for exact/wrong correctness labels
- no replay scoring path uses RNG/randomness as fallback, tie-breaker, or candidate-selection influence for correctness labels
- exact/wrong now requires deterministic post-ledger candidate-output vs expected-output comparison
- when no comparable candidate output exists, the task is marked `unscorable_due_to_missing_candidate_output`

## 3. Exact/wrong code-path trace
### Pre-repair code paths
1. `candidate_deserved -> expected output present -> RNG branch`
   - result: either `deserved_exact` or `deserved_but_wrong`
   - RNG/hash influence: **fully determines label**
   - real expected-output comparison: **none**

2. `candidate_not_deserved`
   - result: neither `deserved_exact` nor `deserved_but_wrong`
   - `undeserved_exact`: no active path
   - RNG/hash influence: none on the observed branch

3. `task_exact_count`
   - derived only from `deserved_exact`
   - therefore indirectly corrupted by RNG/hash

4. hard stop / threshold paths derived from exact/wrong labels
   - `emitter_hard_stop_reasons += deserved_but_wrong`
   - `threshold_reasons += deserved_exact_below_threshold`
   - `threshold_reasons += deserved_but_wrong_not_zero`
   - `recommended_next_lane` could route to assembler-repair logic from RNG-derived `deserved_but_wrong_count`
   - RNG/hash influence: **indirect through corrupted exact/wrong counts**

### Post-repair code paths
1. `candidate_deserved + candidate output available + expected output available`
   - deterministic equality comparison only
   - exact match => `deserved_exact`
   - non-exact => `deserved_but_wrong`
   - RNG/hash influence: none

2. `candidate_not_deserved + candidate output available + expected output available`
   - deterministic equality comparison only
   - exact match => `undeserved_exact`
   - non-exact => `scored_candidate_not_deserved_non_exact`
   - RNG/hash influence: none

3. `candidate generated but comparable output missing`
   - `post_ledger_scoring_status = unscorable_due_to_missing_candidate_output`
   - not counted as exact or wrong
   - RNG/hash influence: none

4. `candidate not generated`
   - `post_ledger_scoring_status = not_scored_candidate_not_generated`
   - not counted as exact or wrong
   - RNG/hash influence: none

## 4. Family-by-family scoring mechanism table
| group | candidate output actually compared after ledger? | RNG/hash exact-wrong before repair? | RNG/hash fallback? | RNG/hash tie-breaker? | RNG/hash candidate-selection influence? | scoring mechanism differs by group? | concrete candidate output surface suitable now? | expected/scoring output available? | expected output present but unused? | classification now | classification before repair |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `v4_rival_grammar_replay_6` | no | yes (shared global scorer) | no separate fallback; RNG was the scorer | no | no | no | no | yes | yes | `unscorable_due_to_missing_candidate_output` | `synthetic_randomized_stress_label` path if deserved branch reached |
| `v4_beautiful_wrong_rule_replay_6` | no | yes (shared global scorer) | no separate fallback; RNG was the scorer | no | no | no | no | yes | yes | `unscorable_due_to_missing_candidate_output` | `synthetic_randomized_stress_label` path if deserved branch reached |
| `v4_composed_transform_replay_6` | no | yes | no separate fallback; RNG was the scorer | no | no | no | no | yes | yes | `unscorable_due_to_missing_candidate_output` | `synthetic_randomized_stress_label` |
| `v4_negative_evidence_replay_6` | no | yes (shared global scorer) | no separate fallback; RNG was the scorer | no | no | no | no | yes | yes | `unscorable_due_to_missing_candidate_output` | `synthetic_randomized_stress_label` path if deserved branch reached |
| `v4_helper_trap_replay_6` | no | yes (shared global scorer) | no separate fallback; RNG was the scorer | no | no | no | no | yes | yes | `unscorable_due_to_missing_candidate_output` | `synthetic_randomized_stress_label` path if deserved branch reached |
| `object_graph_correspondence_6` | no | yes (shared global scorer) | no separate fallback; RNG was the scorer | no | no | no | no | yes | yes | `unscorable_due_to_missing_candidate_output` | `synthetic_randomized_stress_label` path if deserved branch reached |
| `invariant_symmetry_ambiguity_6` | no | yes (shared global scorer) | no separate fallback; RNG was the scorer | no | no | no | no | yes | yes | `unscorable_due_to_missing_candidate_output` | `synthetic_randomized_stress_label` path if deserved branch reached |
| `mdl_simplicity_trap_6` | no | yes | no separate fallback; RNG was the scorer | no | no | no | no | yes | yes | `unscorable_due_to_missing_candidate_output` | `synthetic_randomized_stress_label` |

Current live replay summary across all 8 groups:
- candidate-generated tasks: 48
- candidate-deserved tasks: 12
- safe-failure tasks: 36
- deserved exact tasks: 0
- deserved but wrong tasks: 0
- undeserved exact tasks: 0
- unscorable tasks: 48
- groups with real expected comparison now: 0
- groups with candidate output missing now: 8

## 5. RNG/hash scoring finding
Finding:
- pre-repair replay correctness labels were corrupted by salted-hash RNG scoring
- this was not a stable correctness oracle
- process-to-process task labels could differ
- any prior `deserved_exact`, `deserved_but_wrong`, `task_exact_rate`, or hard-stop inference built from those labels must be downgraded to stress-signal / hypothesis status unless independently revalidated

Post-repair:
- exact/wrong labels are no longer RNG/hash-derived
- exact/wrong labels are emitted only from deterministic post-ledger comparison
- when comparison cannot be performed, the task is explicitly unscorable

## 6. Fallback/tie-breaker/candidate-selection audit
Observed pre-repair:
- RNG/hash was not a documented fallback after a real comparison failure
- RNG/hash was not a tie-breaker between real labels
- RNG/hash was the primary exact/wrong label assignment whenever the deserved branch reached scoring
- no separate RNG/hash candidate-selection influence was found before ledger

Observed post-repair:
- RNG/hash fallback: none
- RNG/hash tie-breaker: none
- RNG/hash candidate-selection influence: none
- RNG/hash exact/wrong scorer: removed

## 7. Scoring repair
Implemented repair in `weslr/arc_generative_bridge_v5_replay.py`:
- removed salted-hash RNG exact/wrong assignment
- added deterministic `_score_post_ledger(...)`
- added candidate-output extraction rules for explicit override/test surfaces only
- added exact/wrong comparison after ledger only
- added `undeserved_exact` real-comparison path
- added `unscorable_due_to_missing_candidate_output` and `not_scored_candidate_not_generated`
- preserved generator and assembler deservedness logic unchanged

Practical outcome in current live V5 tasks:
- no group currently exposes a comparable candidate output surface
- therefore current replay can no longer pretend it knows exact vs wrong across live V5 tasks
- the honest result is `unscorable_due_to_missing_candidate_output`

## 8. Per-task provenance reporting repair
Added durable per-task outcome records to replay results.
Each record now preserves:
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

This makes replay provenance durable enough for future report artifacts, even when scoring is unscorable.

## 9. Named task-id lists
Added durable named lists derived from per-task records:
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

Current live V5 replay counts:
- `candidate_generated_task_ids`: 48
- `candidate_deserved_task_ids`: 12
- `candidate_not_deserved_task_ids`: 36
- `safe_failure_task_ids`: 36
- `deserved_exact_task_ids`: 0
- `deserved_but_wrong_task_ids`: 0
- `undeserved_exact_task_ids`: 0
- `unscorable_task_ids`: 48
- `synthetic_randomized_stress_label_task_ids`: 0
- `rng_influenced_scoring_task_ids`: 0
- `hard_stop_task_ids`: 0

## 10. Candidate trace provenance surface
Replay now records whether task-level scoring provenance came from:
- `candidate_descriptors_override`
- `generated_from_candidate_generation_inputs`

Current limitation:
- provenance now says where the candidate trace came from
- but the standard live generator path still does not emit comparable candidate output surfaces for current V5 tasks
- therefore provenance is repaired, but real scoring still needs candidate-output surface design/plumbing

## 11. Prior conclusion downgrade / preservation analysis
### Conclusions that remain valid
These are still grounded in ledger/safety behavior, not RNG scoring:
- candidate generated
- candidate deserved
- candidate not deserved
- safe failure
- rival-context safe failure
- protected-boundary checks
- generator/assembler gating and safety metrics
- group-level candidate-deserved vs safe-failure distribution

### Conclusions that must be downgraded
These were previously contaminated by RNG/hash scoring and must no longer be treated as verified correctness evidence:
- `deserved_exact`
- `deserved_but_wrong`
- `task_exact_count`
- `task_exact_rate`
- hard-stop conclusions based on `deserved_but_wrong`
- threshold conclusions based on exact/wrong counts
- downstream claims about specific wrong-ID sets when sourced only from pre-repair replay scoring

Required interpretation reset:
- until a real candidate-output surface exists, prior replay `deserved_but_wrong` numbers are stress-signal hypotheses, not verified correctness findings
- the historical ledger/safety conclusions remain usable
- the historical exact/wrong split does not remain authoritative

## 12. Tests added/updated
Updated `weslr/tests/test_arc_generative_bridge_v5_replay_v1.py` to confirm:
- no replay scoring path uses Python salted `hash()` for exact/wrong correctness labels
- no replay scoring path uses RNG/randomness as fallback for exact/wrong correctness labels
- no replay scoring path uses RNG/randomness as tie-breaker for exact/wrong correctness labels
- no replay scoring path uses RNG/randomness to influence candidate selection for exact/wrong correctness labels
- expected/scoring answer comparison happens only after ledger decision
- expected/scoring answers do not enter generation or deservedness
- if candidate output and expected output are available, exact/wrong uses real comparison
- if candidate output is unavailable, task becomes `unscorable_due_to_missing_candidate_output`
- per-task records are emitted for all attempted tasks
- named task-id lists match per-task records
- hard-stop task IDs are preserved
- scoring mechanism is durable across separate Python processes
- candidate trace provenance is recorded
- aggregate metrics remain consistent with per-task records
- all 8 groups have explicit scoring mechanism classification

## 13. Safety and expected-answer boundary
Confirmed:
- expected/scoring answers remain outside generation and deservedness
- scoring executes only after ledger decision
- no generator deservedness repair was made
- no assembler deservedness repair was made
- no enumeration expansion was done
- no emitter implementation was added
- no runtime solver wiring was added
- no ChatResponder changes
- no final-answer emission
- no learned scorer implementation
- no `.weslr`
- no external calls

## 14. Recommended next safe local follow-up
`DESIGN_ARC_CANDIDATE_OUTPUT_SURFACE_FOR_REAL_SCORING_V1`

Why:
- replay scoring semantics and per-task provenance are now honest and durable
- but all 8 current V5 groups are unscorable because the live candidate surface lacks comparable candidate outputs
- the next blocker is not RNG semantics anymore
- the next blocker is missing candidate-output surface for real post-ledger correctness comparison
