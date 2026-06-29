# WESLR ARC COMPOSED AND MDL ALTERNATIVE ENUMERATION DIAGNOSTIC IMPLEMENTATION V1

## 1. Executive verdict
`arc_composed_and_mdl_alternative_enumeration_diagnostic_implemented_but_needs_review`

## 2. Design implemented
Implemented the diagnostic-only lane in:
- `weslr/arc_composed_mdl_alternative_enumeration_diagnostic.py`
- `weslr/tests/test_arc_composed_mdl_alternative_enumeration_diagnostic_v1.py`

This lane remains diagnostic-only.
It does **not** mutate generator deservedness, assembler deservedness, replay decisions, emitter behavior, runtime behavior, or final-answer behavior.

## 3. Shared diagnostic schema
The implementation emits one structured record per candidate with the required schema fields:
- `task_id`
- `group_id`
- `candidate_id`
- `candidate_mode`
- `candidate_output_descriptor`
- `family`
- `subclaims`
- `subclaim_support`
- `whole_claim`
- `whole_claim_support`
- `laundering_risk_detected`
- `laundering_type`
- `alternatives_enumerated`
- `alternative_outputs`
- `alternatives_rejected_by_train_evidence`
- `alternatives_not_rejected`
- `competing_grammars_enumerated`
- `competing_grammar_outputs`
- `competing_grammars_rejected_by_train_evidence`
- `missing_proof_fields`
- `classification_labels`
- `safe_failure_required`
- `recommended_repair_family`

Implementation style is plain/local: dataclass + pure helper functions.

## 4. Composed-transform enumeration
Full implementation in this lane covers composed-transform candidates only for:
- family `composed_transform`
- mode `composed_transform_candidate`

Bounded-local enumeration is implemented over these buckets:
- `alternative_component_order`
- `alternative_component_subset`
- `partial_transform`
- `alternative_interaction_assumption`
- `alternative_full_composition`
- `component_only_explanation`

Scope clarification:
- enumeration is **not** limited only to alternatives already emitted by the generator
- enumeration derives bounded local alternatives from component claims and local trace surface
- enumeration is **not** globally exhaustive over all ARC hypotheses
- if the structure is too thin, the diagnostic emits `missing_proof_only` and/or `insufficient_alternative_search`

Implemented composed outputs include:
- component-level support vs whole-composition support separation
- explicit direct-counterexample vs missing-proof classification
- explicit unrejected-alternative labels
- composed-family forcedness laundering audit

## 5. MDL / grammar enumeration
Full implementation in this lane covers MDL / explicit-grammar candidates only for:
- family `explicit_grammar`
- family `mdl_trap`
- mode `explicit_grammar_candidate`

Bounded-local competing-enumeration is implemented over these buckets:
- `simpler_grammar`
- `more_complex_grammar`
- `same_train_different_test_output`
- `partial_train_fit_grammar`
- `compact_but_not_forced_grammar`
- `train_forced_grammar_candidate`

Scope clarification:
- enumeration is **not** limited only to already-generated candidates
- it derives bounded local competitor records from explicit rival fields and local grammar-trace surfaces
- it is **not** globally exhaustive over all ARC grammar hypotheses
- when the rival surface is too thin, the diagnostic emits `missing_proof_only` and/or `insufficient_alternative_search`

Implemented MDL outputs include:
- simplicity-primary-evidence detection
- grammar-all-train support checks
- explicit competing-grammar / competing-output distinction
- negative-evidence presence checks
- MDL-family forcedness laundering audit

## 6. Direct evidence vs missing-proof classification
Implemented explicit classification labels for:
- `alternative_identified`
- `alternative_not_identified`
- `alternative_rejection_proven`
- `alternative_rejection_missing`
- `competing_output_identified`
- `competing_output_rejected`
- `missing_proof_only`
- `direct_counterexample_found`
- `insufficient_alternative_search`

Meaning preserved:
- direct-evidence labels are only emitted when a concrete alternative / rival record exists
- missing-proof labels are used when proof is incomplete without an explicit rival record
- search-insufficient labels are used when local structure is too thin to responsibly claim sufficiency

## 7. Forcedness-laundering audit helpers
Implemented now for:
- composed-transform forcedness laundering
- MDL / simplicity laundering

Future-family unsupported fail-closed paths are exposed only as labels / repair-family routing hints for:
- `object_correspondence_laundered_as_whole_grid_mapping`
- `local_invariant_laundered_as_global_transformation`
- `absence_of_contradiction_laundered_as_positive_proof`
- `helper_suggestion_laundered_as_train_evidence`
- `local_relation_rewrite_laundered_as_whole_output_rule`

Those future families are **not** fully implemented in this lane. They fail closed with `insufficient_alternative_search` instead of false precision.

## 8. Safety and expected-answer boundary
Maintained:
- local only
- no full V5 replay run
- no push
- no public ARC/Kaggle data
- no hidden test output use
- no expected-answer use in enumeration / comparison / rejection
- no runtime solver wiring
- no ChatResponder changes
- no final-answer emission
- no emitter implementation
- no learned scorer implementation
- no `.weslr`
- no external calls

The diagnostic rejects forbidden scoring-only fields when passed via the safe entrypoint.
It does not mutate the input candidate.

## 9. Tests added
Focused coverage now includes:
- expected-answer field rejection
- no final-answer emission / no input mutation
- composed order enumeration
- composed thin-structure fail-closed behavior
- composed component-support-only vs whole-composition support
- composed direct-counterexample detection
- composed missing-proof-only path
- composed laundering type
- MDL train-forced vs merely-rules-from-train distinction
- MDL simplicity-primary-evidence detection
- MDL competing-grammar category enumeration
- MDL unrejected rival-output detection
- MDL missing-proof-only path
- MDL laundering type
- unsupported future-family fail-closed behavior

## 10. Safety boundaries
Protected files were left outside this lane.
No `.weslr` touch is required or implemented.
No runtime or public-claim behavior is added.

## 11. Recommended next safe local follow-up
`REVIEW_ARC_COMPOSED_AND_MDL_ALTERNATIVE_ENUMERATION_DIAGNOSTIC_IMPLEMENTATION_V1`
