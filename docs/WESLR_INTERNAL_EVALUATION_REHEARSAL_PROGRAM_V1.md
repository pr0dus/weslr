# WESLR Internal Evaluation Rehearsal Program v1

## 1. Purpose and Current Position

WESLR is a continuity-first, governed intelligence system, not a chatbot wrapper.
Its build priority is reasoning, cognition, continuity, evidence handling, correction, abstraction, compositional reasoning, uncertainty handling, candidate selection, and human understanding.

Internal evaluation comes before live response boundary design, public use, voice, or official-style external evaluation.
Voice comes later, after WESLR can reason, understand humans, preserve continuity, and avoid canned or generic responses.

Current chain:
- Level 5 failed-path learning loop: passed, metadata-only.
- Level 6 response candidate ranking: passed, metadata-only.
- Level 7 safe final response assembly: passed, metadata-only.

Level 7 did **not** grant:
- final-answer authority
- user-facing prose authority
- runtime/chat authority
- memory integration authority
- provider/model/search/advisor authority
- public UX authority
- official benchmark/Turing/intelligence/certification claim authority

This program exists to find missing capability before any post-Level-7 live boundary design.

## 2. Safe Naming

Allowed names:
- internal evaluation
- benchmark-style rehearsal
- certification-readiness testing
- Turing-style human evaluation
- intelligence-evaluation rehearsal
- ARC-AGI-style internal rehearsal
- WESLR-created synthetic evaluation

Forbidden names:
- official result
- verified benchmark result
- certified intelligence
- passed official Turing test
- verified badge
- public benchmark claim
- official ARC result unless externally submitted and verified through the official process

## 3. Claim Prohibitions

Forbidden:
- official result claims
- certified intelligence claims
- verified benchmark/badge claims
- hidden/private/semi-private benchmark data use
- answer-key leakage
- raw private user data
- scoring claims that imply external certification
- Turing-test passing claims
- public-readiness claims based only on internal rehearsal
- intelligence/IQ claims
- future-certainty claims
- claims that UNKNOWN ENGINE proves future outcomes
- claims that internal rehearsal equals official validation

## 4. Dataset and Source Classification

Source classes:
- public/open
- synthetic WESLR-created
- semi-private
- private
- hidden/blocked
- unknown-license blocked until reviewed

Rules by class:

### Public/open
- Allowed use: yes, only if license/source review permits.
- Blocked use: no hidden leakage, no answer-key reuse.
- Contamination risk: medium if repeatedly tuned against evals.
- Development use allowed: yes, with license review.
- Sealed internal evaluation allowed: yes.
- Official claims allowed: no, by themselves.

### Synthetic WESLR-created
- Allowed use: yes.
- Blocked use: none by source class, subject to safety rules.
- Contamination risk: low, preferred for repeated loops.
- Development use allowed: yes.
- Sealed internal evaluation allowed: yes.
- Official claims allowed: no.

### Semi-private
- Allowed use: no, unless through official external submission/evaluation process.
- Blocked use: yes by default.
- Contamination risk: high.
- Development use allowed: no.
- Sealed internal evaluation allowed: only through official process.
- Official claims allowed: only through official process and verification.

### Private
- Allowed use: no, unless through official external submission/evaluation process.
- Blocked use: yes by default.
- Contamination risk: high.
- Development use allowed: no.
- Sealed internal evaluation allowed: only through official process.
- Official claims allowed: only through official process and verification.

### Hidden/blocked
- Allowed use: no.
- Blocked use: yes.
- Contamination risk: extreme.
- Development use allowed: no.
- Sealed internal evaluation allowed: no.
- Official claims allowed: no.

### Unknown-license blocked until reviewed
- Allowed use: no until reviewed.
- Blocked use: yes until review completes.
- Contamination risk: unknown/high.
- Development use allowed: no.
- Sealed internal evaluation allowed: no until reviewed.
- Official claims allowed: no.

Raw private user data is always blocked.

## 5. ARC-AGI-Style Internal Plan

- Public training tasks may be used for development if licensing/source rules allow.
- Public eval tasks may be used for sealed internal evaluation.
- Repeated tuning against public eval score is contamination risk and must be treated as such.
- Semi-private/private sets are blocked unless through official external submission.
- WESLR-created ARC-style synthetic tasks should be used for repeated mutation/development.
- Internal results must remain internal rehearsal labels, not official results.
- Internal ARC-style testing is for gap discovery, not public score claims.

## 6. WESLR-Native Test Families

### Abstraction/rule induction
- Checks: can WESLR infer the governing rule from examples.
- Failure means: shallow pattern matching or overfit behavior.
- May reveal: missing abstraction helper or weak induction.
- Synthetic tasks preferred: yes.

### Compositional reasoning
- Checks: can WESLR combine multiple constraints or subgoals.
- Failure means: loses one constraint while satisfying another.
- May reveal: missing composition planner.
- Synthetic tasks preferred: yes.

### Contextual rule application
- Checks: can WESLR apply a known rule in the right context.
- Failure means: rule is recalled but not applied correctly.
- May reveal: context gating weakness.
- Synthetic tasks preferred: yes.

### Evidence/currentness reasoning
- Checks: can WESLR separate known, current, stale, and missing evidence.
- Failure means: stale or unsupported claims.
- May reveal: currentness tracker or evidence discipline gap.
- Synthetic tasks preferred: yes.

### Memory/continuity boundary
- Checks: can WESLR keep continuity without false memory claims.
- Failure means: invented recall or broken session continuity.
- May reveal: memory boundary helper missing.
- Synthetic tasks preferred: yes.

### Correction assimilation
- Checks: can WESLR absorb user correction and carry it forward.
- Failure means: repeated mistake or correction drop.
- May reveal: correction propagation gap.
- Synthetic tasks preferred: yes.

### Non-canned response formation
- Checks: can WESLR produce specific, grounded, non-generic responses.
- Failure means: checklist-like or template output.
- May reveal: response formation depth gap.
- Synthetic tasks preferred: yes.

### Candidate ranking/rejection
- Checks: can WESLR choose a best next answer and reject weaker ones.
- Failure means: undecided, overinclusive, or wrong-lane selection.
- May reveal: ranking or rejection policy gap.
- Synthetic tasks preferred: yes.

### Safe final response envelope behavior
- Checks: can WESLR assemble a safe response shape without overclaiming.
- Failure means: unsafe authority or final-answer leakage.
- May reveal: envelope logic gap.
- Synthetic tasks preferred: yes.

### UNKNOWN ENGINE future-state projection
- Checks: can WESLR forecast likely failure zones and next gaps.
- Failure means: weak anticipation or unfounded certainty.
- May reveal: projection/compression gap.
- Synthetic tasks preferred: yes.

### Turing-style human conversation rehearsal
- Checks: can WESLR sustain natural, grounded, human-facing dialogue behavior.
- Failure means: cannedness, drift, or weak human modeling.
- May reveal: conversational understanding gap.
- Synthetic tasks preferred: yes.

### Uncertainty explanation
- Checks: can WESLR explain what it knows, does not know, and why.
- Failure means: overconfident or vague uncertainty handling.
- May reveal: uncertainty framing gap.
- Synthetic tasks preferred: yes.

### Human intent/frustration/urgency understanding
- Checks: can WESLR infer what the user likely needs emotionally and operationally.
- Failure means: tone deafness or wrong priority.
- May reveal: human-understanding gap.
- Synthetic tasks preferred: yes.

### Action/governance boundary recognition
- Checks: can WESLR know what it may propose versus what needs approval.
- Failure means: unauthorized action or boundary blur.
- May reveal: governance boundary gap.
- Synthetic tasks preferred: yes.

## 7. UNKNOWN ENGINE Role

UNKNOWN ENGINE is a bounded internal helper concept.

Allowed uses:
- future-state projection
- predicting where WESLR may fail
- generating synthetic task mutations
- comparing predicted vs observed failure
- failure-pattern exploration
- prediction/reveal/correction/compression loops
- compressing repeated failures into capability gaps
- proposing next test families

Forbidden uses:
- no authority
- no future certainty
- no official evaluator status
- no proof-engine status
- no automatic lesson promotion
- no autonomous self-modification
- no runtime/live wiring
- no official benchmark/Turing/intelligence claims
- no public-readiness claims
- no hidden benchmark access
- no claim that projected futures are facts

UNKNOWN ENGINE may help discover gaps, but it must not decide truth, promote lessons automatically, certify WESLR, or authorize code/runtime changes.

## 8. Internal Result Schema

Internal result schema fields:
- task_id
- task_family
- source_type
- source_license_status
- exposure_level
- expected_output_available
- correctness_label
- confidence_label
- missing_capability
- failure_mode
- contamination_risk
- official_claim_allowed=false
- unknown_engine_projection_used
- unknown_engine_projection_label
- predicted_failure_label
- observed_failure_label
- gap_discovery_label
- recommended_next_lane

Rules:
- qualitative labels preferred at design stage
- no public score claims
- no external certification implication
- official_claim_allowed must always be false for internal rehearsal artifacts

## 9. Gap Report Output

Gap report fields:
- capability gaps
- repeated failure modes
- unsafe overclaim patterns
- missing tools/adapters
- missing reasoning helpers
- missing evidence/currentness mechanisms
- missing continuity/correction mechanisms
- missing abstraction/composition mechanisms
- contamination risks
- recommended next lanes
- blocked public/live claims

## 10. Baseline and Rerun Strategy

Future sequence:
1. DESIGN_WESLR_INTERNAL_EVALUATION_REHEARSAL_PROGRAM_V1
2. REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_PROGRAM_V1
3. AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_INTERNAL_EVALUATION_REHEARSAL_PROGRAM_REVIEW_V1
4. DESIGN_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_V1
5. IMPLEMENT_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_V1
6. REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_V1
7. DESIGN_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1
8. IMPLEMENT_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1
9. REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1
10. RUN_WESLR_INTERNAL_EVALUATION_BASELINE_V1
11. REVIEW_WESLR_INTERNAL_EVALUATION_BASELINE_RESULT_V1
12. DESIGN_WESLR_CAPABILITY_GAP_CLOSURE_PLAN_V1
13. IMPLEMENT_SELECTED_MISSING_HELPERS_OR_REASONING_EXPANSIONS_V1
14. RERUN_WESLR_INTERNAL_EVALUATION_REHEARSAL_V1
15. Only then return to DESIGN_POST_LEVEL_7_SAFE_LIVE_RESPONSE_BOUNDARY_V1

The goal is to prevent WESLR from being blindsided by future official-style testing.

## 11. Contamination Controls

- separate development tasks from sealed evaluation tasks
- mark repeated eval exposure as contamination risk
- prefer synthetic mutations for repeated training/development
- keep public eval use limited and logged
- block hidden/private/semi-private materials
- block unknown-license datasets
- block answer-key leakage
- block raw private user data
- block hidden benchmark reconstruction
- block benchmark memorization loops

## 12. Blocked Behaviors

- no implementation in this lane
- no test execution
- no benchmark downloading
- no runtime/chat wiring
- no provider/model/search/advisor calls
- no .weslr reads/writes
- no public claims
- no raw private data
- no final answer generation
- no live response boundary design yet
- no voice work
- no public UX
- no official benchmark/Turing/intelligence/certification claims
- no UNKNOWN ENGINE authority
- no automatic lesson promotion
- no autonomous self-modification

## 13. Validation Plan

Validation for this design lane:
- repo root/branch/HEAD handshake
- release gate
- release check
- confirm protected files untouched
- confirm only allowed files changed
- confirm no implementation files added
- confirm no dataset downloads
- confirm no .weslr access
- confirm no runtime/chat wiring
- confirm no provider/model/search/advisor calls

## 14. Recommended Next Lanes

1. REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_PROGRAM_V1
2. AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_INTERNAL_EVALUATION_REHEARSAL_PROGRAM_REVIEW_V1
3. DESIGN_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_V1
4. IMPLEMENT_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_V1
5. REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_V1
6. DESIGN_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1
7. IMPLEMENT_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1
8. REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1
9. RUN_WESLR_INTERNAL_EVALUATION_BASELINE_V1
10. REVIEW_WESLR_INTERNAL_EVALUATION_BASELINE_RESULT_V1
11. DESIGN_WESLR_CAPABILITY_GAP_CLOSURE_PLAN_V1
12. IMPLEMENT_SELECTED_MISSING_HELPERS_OR_REASONING_EXPANSIONS_V1
13. RERUN_WESLR_INTERNAL_EVALUATION_REHEARSAL_V1
14. Return later to DESIGN_POST_LEVEL_7_SAFE_LIVE_RESPONSE_BOUNDARY_V1
