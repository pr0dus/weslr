# WESLR Adaptive Synthetic Learning Boundary V1

## 1. Learning definition

This design defines learning as bounded metadata accumulation from synthetic reasoning work, not uncontrolled self-improvement.

Learning levels:

- solve attempt — a synthetic task is attempted
- failure record — the attempt outcome is recorded as metadata
- gap classification — the failure is labeled with a gap type
- curriculum adaptation — next synthetic item selection changes based on the gap
- capability profile update — internal maturity metadata is adjusted
- helper proposal — repeated gaps can suggest a new helper boundary
- owner-reviewed promotion — only owner review may approve any promotion step

Learning here never means automatic runtime learning, self-modification, or model training.

## 2. Synthetic learning source policy

Allowed sources:

- synthetic WESLR-generated tasks
- provenance-known internal items
- non-private examples
- non-proprietary examples
- no official benchmark source

Forbidden sources:

- official IQ tests
- Raven / WAIS / proprietary items
- hidden answer keys
- private user images
- poisoned external images
- unverified benchmark datasets
- social-media poison sources
- runtime self-training from arbitrary input

## 3. Gap-to-learning loop

The bounded loop is:

1. generate a synthetic task
2. solver attempts the task
3. compare against the hidden rule program
4. classify the gap
5. update the capability profile
6. generate a targeted next task
7. detect improvement or plateau
8. compress the lesson into metadata
9. propose a new helper if the same gap repeats

The hidden rule program stays hidden from the solver path. Only metadata may flow forward.

## 4. Gap types

Supported gap types:

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
- overfit_risk
- poison_risk
- unknown_gap

## 5. Learning blockers

Hard blockers:

- untrusted source
- private/proprietary source
- official test source
- poison risk
- missing provenance
- repeated failure with no improvement
- overfitting detected
- confidence inflation
- hidden benchmark leakage
- raw-data retention risk
- owner approval missing
- automatic self-modification attempted
- automatic behavior-pack promotion attempted
- model fine-tuning attempted without explicit owner approval

Any hard blocker stops adaptive learning and forces review.

## 6. Capability profile

Capability profiles are metadata-only records.

Shape:

- capability_id
- rule_family
- current_maturity
- evidence_count
- success_rate_band
- failure_pattern
- calibration_error
- transfer_status
- overfit_risk
- recommended_next_training
- recommended_new_helper
- promotion_status
- owner_review_required
- safe_metadata

## 7. Curriculum adaptation

Curriculum adapts by pressure and spacing, not by uncontrolled optimization.

Modes:

- easy → medium → hard → adversarial
- targeted repetition after failure
- spaced retest
- distractor pressure
- ambiguity pressure
- meta-rule pressure

Stop conditions:

- plateau detected
- poison/provenance risk
- overfit detected
- repeated failure count exceeded

## 8. Anti-infinite-learning controls

Controls:

- max iterations per session
- max repeated failures before review
- plateau detection
- lesson compression
- raw item retention limits
- no automatic source ingestion
- no model update
- no code update
- no behavior-pack promotion
- owner/operator review gates

These controls prevent infinite loops and keep learning bounded.

## 9. Promotion policy

Promotion is proposal-only.

Requirements:

- candidate helper proposal only
- review required
- tests required
- provenance required
- maturity registry update required
- no automatic runtime wiring
- no broad authority
- no public claim

Promotion does not occur inside the learning loop itself.

## 10. Relation to Visual Matrix / Unknown Engine lane

This boundary is designed for the Visual Matrix / Unknown Engine side branch.

Recorded relationship:

- visual matrix lane is a synthetic side branch
- Unknown Engine acts as challenger, novelty generator, and blind-spot detector
- Gap Miner converts failures into capability gaps
- IRT-style calibration tracks internal capability only
- no official IQ, Raven, WAIS, benchmark, certification, or public intelligence claim

The lane is a controlled abstract-reasoning laboratory, not an authority surface.

## 11. Safety boundaries

Explicitly forbidden:

- self-modification
- autonomous fine-tuning
- official intelligence score
- public IQ claim
- benchmark certification
- proprietary test training
- hidden answer-key learning
- private-image ingestion
- arbitrary runtime learning from user uploads
- model/provider calls
- runtime write authority
- automatic behavior-pack promotion

## 12. Future helper roadmap

Planned future lanes:

- Adaptive Synthetic Learning Packet Helper V1
- Visual Matrix Capability Profile Helper V1
- Gap-to-Curriculum Selector V1
- Plateau and Overfit Detector V1
- Helper Proposal Generator V1
- Capability Maturity Registry Bridge V1
- Learning Safety Review Helper V1

## 13. Closing posture

This design is metadata-first, bounded, and review-gated.

It supports learning from synthetic failures only when the source is known, the provenance is safe, and the outcome stays inside helper metadata.

It does not create runtime authority, model-training authority, public-scoring authority, or automatic promotion authority.

## 14. Final judgment

`adaptive_synthetic_learning_boundary_design_ready_for_review`

## 15. Recommended next lane

`REVIEW_WESLR_ADAPTIVE_SYNTHETIC_LEARNING_BOUNDARY_V1`
