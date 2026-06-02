# WESLR Unknown Engine Visual Matrix Gap Discovery V1

## 1. Purpose

This design defines an internal synthetic abstract-reasoning rehearsal system.

Visual matrices are one controlled world for reasoning analysis, not an IQ claim, not a certification surface, and not a public benchmark result.

Unknown Engine acts as the challenger: it generates novelty, rule pressure, distractors, ambiguity, and blind-spot probes.

Gap Miner is the missing-capability classifier: it records which reasoning machinery failed, stalled, or overconfidently guessed.

## 2. System components

- Visual Matrix Solver
- Unknown Engine Challenger
- Rule Program Generator
- Future-State Simulator
- Candidate Ranker
- Explanation Validator
- Gap Miner
- IRT-style Calibration Layer
- Capability Maturity Registry bridge

## 3. Matrix world representation

Synthetic matrix items are represented as metadata packets with:

- grid size
- cells
- objects
- attributes
- relations
- transformations
- hidden rule program
- answer candidates
- distractor candidates
- expected explanation
- synthetic provenance
- no official benchmark source

## 4. Rule families

Supported rule families include:

- count
- shape substitution
- fill/color
- size
- rotation
- reflection
- position movement
- symmetry
- sequence
- alternation
- overlay
- subtraction
- XOR
- AND/OR logic
- row arithmetic
- column arithmetic
- analogy
- recursion
- occlusion
- conditional rule
- meta-rule
- rule switching
- multi-rule interaction
- distractor lure

## 5. Unknown Engine challenge modes

- known_rule_confirmation
- known_rule_combination
- distractor_pressure
- ambiguous_rule_pressure
- sparse_evidence_pressure
- noisy_abstraction_pressure
- occluded_object_pressure
- rule_switch_pressure
- meta_rule_pressure
- invented_rule_pressure
- counterfactual_transfer_pressure
- calibration_pressure
- adversarial_false_simplicity_pressure
- unknown_rule_discovery_pressure

## 6. Gap taxonomy

Failures are classified as:

- perception_gap
- representation_gap
- relation_model_gap
- rule_grammar_gap
- hypothesis_generation_gap
- hypothesis_search_gap
- future_state_simulation_gap
- candidate_matching_gap
- distractor_resistance_gap
- explanation_gap
- uncertainty_gap
- calibration_gap
- transfer_gap
- abstraction_compression_gap
- unknown_gap

## 7. Future-state prediction

The solver should:

1. generate competing hypotheses
2. simulate the missing cell for each hypothesis
3. compare each prediction against candidates
4. preserve rejected alternatives
5. record conflicts explicitly
6. never hide ambiguity
7. classify confidence as metadata only

## 8. IRT-style internal calibration

The calibration layer should track:

- synthetic item difficulty
- rule-family difficulty
- discrimination-like metadata
- repeated failure tracking
- adaptive next-item selection
- capability growth curve

It must not produce:

- IQ score
- official benchmark result
- certification claim

## 9. Unknown Engine × IRT loop

Cycle:

1. generate synthetic item
2. solver attempts
3. compare to hidden rule program
4. classify gap
5. update internal capability profile
6. generate next targeted item
7. retest
8. record improvement or stagnation

## 10. Missing capability output

Metadata packet shape:

- challenge_id
- rule_program_ref
- solver_hypothesis_ref
- predicted_candidate
- correct_candidate
- failure_status
- gap_labels
- missing_rule_family
- missing_representation
- distractor_trigger
- calibration_error
- recommended_new_helper
- recommended_training_item
- no_public_score
- no_official_claim
- safe_metadata

## 11. Safety boundaries

Explicitly forbidden:

- official IQ claims
- Raven/WAIS/proprietary test use
- hidden benchmark data
- answer-key leakage
- public intelligence score
- certification claim
- user-private image ingestion
- runtime/image processing
- model/provider calls
- final-answer authority
- autonomous self-modification
- automatic behavior-pack promotion

## 12. Future helper roadmap

Planned lanes:

- Visual Matrix Representation Helper V1
- Matrix Rule Grammar Helper V1
- Future-State Candidate Predictor V1
- Unknown Engine Matrix Challenger V1
- Matrix Gap Miner V1
- Synthetic Matrix Item Bank V1
- IRT Calibration Metadata Helper V1
- Matrix Reasoning Report Helper V1
- Capability Maturity Registry Bridge V1

## 13. Tests to design later

Design later for:

- one-rule synthetic item
- two-rule synthetic item
- XOR/overlay item
- distractor lure item
- ambiguous item
- unknown-rule item
- meta-rule item
- occlusion item
- false-confidence item
- blocked official/proprietary item
- no-score/no-certification item

## 14. Non-goals

This design does not implement image processing, runtime wiring, benchmark scoring, or public evaluation.

It does not claim intelligence, IQ, certification, or readiness.

## 15. Review posture

This is a metadata-first design for synthetic reasoning analysis and gap discovery.

It is ready for later helper decomposition and review.

## 16. Final judgment

`unknown_engine_visual_matrix_gap_discovery_design_ready_for_review`

## 17. Recommended next lane

`REVIEW_WESLR_UNKNOWN_ENGINE_VISUAL_MATRIX_GAP_DISCOVERY_V1`
