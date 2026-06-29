# WESLR ARC COMPOSED AND MDL ALTERNATIVE ENUMERATION DIAGNOSTIC DESIGN V1

## 1. Executive verdict
`arc_composed_and_mdl_alternative_enumeration_diagnostic_design_complete_with_notes`

## 2. Problem statement
The current non-rival false positives are already split into two families:
- composed-transform false positives
- MDL / simplicity-trap false positives

The attribution work established two important facts:
1. dominant forcedness-laundering patterns are real in both families
2. actual alternative compositions and actual competing grammars were **not** identified in the current artifact chain

That means the next safe step is a diagnostic that can distinguish:
- an alternative / rival that was actually enumerated and rejected by train evidence
from
- a case where no alternative was enumerated and the system only knows proof is missing

Without this diagnostic, a repair risks overstating what was checked and may silently convert missing-proof situations into fake rival-rejection claims.

## 3. Attribution summary
Current upstream findings to preserve:
- composed wrong cases attributed: 4
- MDL wrong cases attributed: 3
- composed dominant direct causes:
  - `composition_not_train_supported_as_unit`
  - `component_level_forcedness_laundered_as_composition_forcedness`
- MDL dominant direct causes:
  - `simplicity_laundered_as_train_forcing`
  - `mdl_primary_evidence_not_detected`
- actual alternative compositions identified: no
- actual competing grammars identified: no
- missing-proof inference used: yes

Design consequence:
- the diagnostic must explicitly model enumeration attempts, not just missing fields
- it must preserve a fail-closed path when no rival/alternative is found
- it must never claim a specific alternative was rejected unless the alternative exists as an explicit diagnostic record

## 4. Composed-transform alternative enumeration design
### 4.1 Target family
Applies to candidates with family `composed_transform` and construction mode `composed_transform_candidate`.

### 4.2 Diagnostic goal
For each composed candidate, enumerate and score structured alternatives before any future discrimination repair is applied.

### 4.3 Inputs the diagnostic should use
Only train-grounded local inputs:
- task id / group id
- train examples
- candidate output descriptor
- candidate construction trace
- candidate component claims if present
- generator-provided sub-operations / object ops / color ops / spatial ops / relation ops
- existing ambiguity / unsupported-assumption / rival flags

Must not use:
- expected answers
- hidden test outputs
- public ARC answers
- runtime wiring

### 4.4 Enumeration model for composed candidates
For each composed candidate, build an `alternative_composition_set` with these buckets:
1. `alternative_component_order`
   - same component set, different order
2. `alternative_component_subset`
   - proper subset of claimed components
3. `partial_transform`
   - only one local subclaim applied to whole candidate
4. `alternative_interaction_assumption`
   - same components, different interaction semantics
5. `alternative_full_composition`
   - different composed explanation that fits at least one train pair
6. `component_only_explanation`
   - evidence supports components individually but not a unitary whole claim

### 4.5 Questions the diagnostic must answer
For each candidate:
- Which components are individually train-supported?
- Is the component order forced by train evidence?
- Does the full ordered composition explain every train pair?
- Are alternative orders viable on train data?
- Are alternative partial transforms viable on train data?
- Are alternative full compositions viable on train data?
- Are those alternatives explicitly rejected by train evidence?
- Is the chosen output forced by the full composition, or only by component-level support?

### 4.6 Per-alternative record fields
Each composed alternative record should include:
- `alternative_id`
- `alternative_kind`
- `components`
- `component_order`
- `interaction_assumption`
- `covers_train_pairs`
- `fails_train_pairs`
- `train_support_scope`
  - `subclaim_only`
  - `partial_train_pairs`
  - `all_train_pairs`
- `produces_candidate_output_descriptor`
- `produces_distinct_output_descriptor`
- `explicit_train_rejection_found`
- `train_rejection_reason`
- `enumeration_status`
  - `identified`
  - `generated_but_not_checkable`
  - `not_generated`

### 4.7 Forcedness decision rules for composed family
The diagnostic should emit:
- `whole_composition_forced = true` only if:
  - ordered component sequence is explicit
  - all train pairs are covered by the same ordered whole claim
  - no enumerated viable alternative remains unrejected
  - component-only support is insufficient by itself
- otherwise emit:
  - `whole_composition_forced = false`
  - `missing_proof_only = true` if no contrary alternative is found but proof is incomplete
  - `direct_counterexample_found = true` if an actual viable alternative remains unrejected

### 4.8 Fail labels for composed family
- `component_order_unproven`
- `component_interaction_unproven`
- `whole_composition_not_train_forced`
- `component_support_only`
- `alternative_order_viable_unrejected`
- `alternative_subset_viable_unrejected`
- `alternative_full_composition_viable_unrejected`
- `partial_transform_viable_unrejected`
- `insufficient_alternative_search`

## 5. MDL / grammar competing-enumeration design
### 5.1 Target family
Applies to candidates with family `explicit_grammar` / `mdl_trap` and construction mode `explicit_grammar_candidate`.

### 5.2 Diagnostic goal
For each explicit-grammar candidate, enumerate competing grammars and competing outputs so the system can distinguish:
- genuinely train-forced grammar
from
- merely compact / attractive grammar with missing rival proof

### 5.3 Inputs the diagnostic should use
Only local train-grounded inputs:
- task id / group id
- train examples
- candidate construction trace
- candidate grammar id / grammar description if present
- candidate output descriptor
- candidate rival fields if present
- candidate negative-evidence fields if present

Must not use:
- expected answers for generation, comparison, or rejection
- hidden test outputs
- public ARC answers

### 5.4 Enumeration model for MDL / grammar candidates
For each grammar candidate, build a `competing_grammar_set` with these buckets:
1. `simpler_grammar`
   - lower-description grammar compatible with some/all train pairs
2. `more_complex_grammar`
   - higher-description grammar compatible with all train pairs
3. `same_train_different_test_output`
   - grammar compatible with train examples but implying distinct candidate output descriptor
4. `partial_train_fit_grammar`
   - grammar fitting some train pairs only
5. `compact_but_not_forced_grammar`
   - attractive grammar lacking unique train forcing
6. `train_forced_grammar_candidate`
   - explicitly supported grammar with whole-train forcing evidence

### 5.5 Questions the diagnostic must answer
For each candidate:
- Is the accepted grammar merely simple/compact?
- Is simplicity being used as primary evidence?
- Does the grammar explain all train pairs?
- Are competing grammars considered explicitly?
- Are competing grammar outputs considered explicitly?
- Is there negative evidence against wrong-simple rules?
- Is the selected grammar forced by train evidence or only preferred by MDL?

### 5.6 Per-grammar record fields
Each competing grammar record should include:
- `grammar_id`
- `grammar_kind`
- `description_complexity_band`
  - `simpler`
  - `same_band`
  - `more_complex`
- `fits_train_pairs`
- `fails_train_pairs`
- `produces_candidate_output_descriptor`
- `produces_distinct_output_descriptor`
- `negative_evidence_against_grammar`
- `explicit_train_rejection_found`
- `train_rejection_reason`
- `enumeration_status`
  - `identified`
  - `generated_but_not_checkable`
  - `not_generated`

### 5.7 Forcedness decision rules for MDL family
The diagnostic should emit:
- `grammar_forced_by_train = true` only if:
  - accepted grammar explains all train pairs
  - competing grammars are enumerated or search is sufficient
  - distinct competing outputs are either absent or explicitly rejected by train evidence
  - negative evidence exists against attractive wrong-simple rules when such rules are enumerated
- otherwise emit:
  - `grammar_forced_by_train = false`
  - `missing_proof_only = true` if no explicit rival is found but rival search/proof is incomplete
  - `direct_counterexample_found = true` if actual competing grammar/output remains unrejected

### 5.8 Fail labels for MDL family
- `simplicity_as_primary_evidence`
- `grammar_not_proven_on_all_train_pairs`
- `competing_grammar_unenumerated`
- `competing_output_unenumerated`
- `negative_evidence_missing`
- `attractive_wrong_simple_rule_unrejected`
- `insufficient_alternative_search`

## 6. Direct evidence vs missing-proof classification
The diagnostic must classify every family result using explicit output labels.

### 6.1 Required labels
- `alternative_identified`
- `alternative_not_identified`
- `alternative_rejection_proven`
- `alternative_rejection_missing`
- `competing_output_identified`
- `competing_output_rejected`
- `missing_proof_only`
- `direct_counterexample_found`
- `insufficient_alternative_search`

### 6.2 Meaning rules
#### Direct-evidence path
Use when:
- a concrete alternative / rival / competing output record exists
- and the diagnostic can show whether train evidence rejects it

This path may emit:
- `alternative_identified`
- `competing_output_identified`
- `alternative_rejection_proven`
- `competing_output_rejected`
- `direct_counterexample_found`

#### Missing-proof path
Use when:
- no explicit alternative/rival is enumerated
- but the accepted whole claim lacks sufficient proof surface

This path must emit:
- `alternative_not_identified`
- `alternative_rejection_missing`
- `missing_proof_only`

#### Search-insufficient path
Use when:
- the system cannot even responsibly determine whether alternatives were searched well enough

This path must emit:
- `insufficient_alternative_search`

### 6.3 Guardrail
If `alternative_not_identified = true`, the diagnostic must not claim:
- that a specific alternative order was rejected
- that a specific competing grammar was rejected
- that a specific competing output was rejected

It may only claim:
- proof of rejection is missing
- safe failure would be appropriate pending stronger evidence

## 7. Forcedness-laundering class audit
### 7.1 Purpose
Define one cross-mode audit for the repeated class:
`sub_claim_forcedness_laundered_as_whole_claim_forcedness`

This audit is diagnostic only in this lane.
It does not repair all families now.

### 7.2 Audit modes and checks
#### Composed transform
- subclaim: individual component support
- whole claim: ordered composition forces output
- laundering check:
  - are components supported individually?
  - is order explicitly supported?
  - is whole composition covered across all train pairs?
  - are alternative compositions/orders absent or unrejected?
- failure label:
  - `component_forcedness_laundered_as_composition_forcedness`

#### MDL / grammar
- subclaim: grammar is compact / train-derived in wording
- whole claim: grammar is uniquely train-forced
- laundering check:
  - is simplicity or compactness functioning as primary evidence?
  - are rival grammars absent?
  - are competing outputs absent?
  - is negative evidence missing?
- failure label:
  - `simplicity_laundered_as_train_forcing`

#### Object graph correspondence
- subclaim: local object correspondences exist
- whole claim: whole-grid mapping is forced
- laundering check:
  - do correspondences cover every relevant object and relation?
  - does whole-grid mapping follow uniquely?
  - are unmapped objects or alternative mappings left open?
- failure label:
  - `object_correspondence_laundered_as_whole_grid_mapping`

#### Invariant / symmetry
- subclaim: local invariant holds
- whole claim: global transform is forced
- laundering check:
  - is invariant sufficient to determine full transform?
  - are alternative transforms consistent with same invariant?
- failure label:
  - `local_invariant_laundered_as_global_transformation`

#### Negative evidence
- subclaim: no contradiction seen yet
- whole claim: therefore candidate is positively supported
- laundering check:
  - is absence of contradiction being treated as affirmative proof?
- failure label:
  - `absence_of_contradiction_laundered_as_positive_proof`

#### Helper trap
- subclaim: helper suggested candidate or rationale
- whole claim: train evidence supports candidate
- laundering check:
  - is helper-origin text appearing where train evidence should exist?
- failure label:
  - `helper_suggestion_laundered_as_train_evidence`

#### Relation-first rewrite
- subclaim: local rewrite is supported
- whole claim: whole output rule is forced
- laundering check:
  - does local rewrite determine full output?
  - do unrejected whole-output alternatives remain?
- failure label:
  - `local_relation_rewrite_laundered_as_whole_output_rule`

### 7.3 Shared audit outputs
For all modes, emit:
- `laundering_risk_detected`
- `laundering_type`
- `whole_claim_missing_support`
- `subclaim_support_only`
- `safe_failure_required`

## 8. Diagnostic output schema
A future implementation should emit a diagnostic record per candidate using a schema like:

```json
{
  "task_id": "string",
  "group_id": "string",
  "candidate_id": "string",
  "candidate_mode": "string",
  "candidate_output_descriptor": {},
  "family": "composed_transform | explicit_grammar | object_correspondence | invariant | negative_evidence | helper_trap | relation_first_rewrite | other",
  "subclaims": [],
  "subclaim_support": [
    {
      "subclaim_id": "string",
      "support_scope": "none | partial_train_pairs | all_train_pairs",
      "source_train_ids": [],
      "support_reason": "string"
    }
  ],
  "whole_claim": "string",
  "whole_claim_support": {
    "support_scope": "none | partial_train_pairs | all_train_pairs",
    "order_forced": false,
    "interaction_forced": false,
    "all_train_pairs_explained": false,
    "negative_evidence_present": false,
    "proof_reason": "string"
  },
  "laundering_risk_detected": false,
  "laundering_type": "string | null",
  "alternatives_enumerated": [
    {
      "alternative_id": "string",
      "alternative_kind": "string",
      "description": "string",
      "fits_train_pairs": [],
      "fails_train_pairs": [],
      "produces_candidate_output_descriptor": false,
      "produces_distinct_output_descriptor": false,
      "explicit_train_rejection_found": false,
      "train_rejection_reason": "string"
    }
  ],
  "alternative_outputs": [],
  "alternatives_rejected_by_train_evidence": [],
  "alternatives_not_rejected": [],
  "competing_grammars_enumerated": [
    {
      "grammar_id": "string",
      "grammar_kind": "string",
      "description_complexity_band": "simpler | same_band | more_complex",
      "fits_train_pairs": [],
      "fails_train_pairs": [],
      "produces_candidate_output_descriptor": false,
      "produces_distinct_output_descriptor": false,
      "explicit_train_rejection_found": false,
      "train_rejection_reason": "string"
    }
  ],
  "competing_grammar_outputs": [],
  "competing_grammars_rejected_by_train_evidence": [],
  "missing_proof_fields": [],
  "classification_labels": [],
  "safe_failure_required": false,
  "recommended_repair_family": "composed_transform | explicit_grammar | generic_laundering_audit | none"
}
```

### 8.1 Family-specific required fields
#### Composed family adds
- `component_list`
- `component_orders_tested`
- `component_subsets_tested`
- `interaction_assumptions_tested`
- `whole_composition_forced`

#### MDL family adds
- `accepted_grammar_complexity_band`
- `simplicity_primary_evidence_detected`
- `negative_evidence_against_wrong_simple_rules`
- `grammar_forced_by_train`

## 9. Safety and expected-answer boundary
The diagnostic must not:
- use expected answers to generate alternatives
- use expected answers to reject alternatives
- use expected answers to decide deservedness
- emit final answers
- make public claims
- wire into runtime
- mutate solver behavior

Allowed expected-answer usage:
- only after ledger decision
- only for diagnostic labeling / retrospective analysis in already-reported local runs
- never as evidence for a candidate, alternative, grammar, or rejection claim

Required implementation guardrails:
- no `expected_answer` or scoring-only fields may enter enumeration logic
- any future test fixture using expected labels must isolate them from generator / assembler / diagnostic reasoning inputs
- if no explicit alternative/rival is found, the diagnostic must prefer `missing_proof_only` over any fake rejection claim

## 10. Implementation plan
### Phase 1: shared diagnostic skeleton
- add a new diagnostic-only module for alternative enumeration records
- accept candidate trace + train examples + local task metadata only
- emit schema-compliant diagnostic packets
- no mutation of generator or assembler behavior

### Phase 2: composed enumeration
- derive component set from candidate sub-operations / trace fields
- enumerate order permutations within bounded local limits
- enumerate subsets / partial transforms / interaction variants
- score train-pair coverage and explicit rejection status
- emit composed-family labels and laundering flags

### Phase 3: MDL / grammar enumeration
- derive accepted grammar description from candidate fields
- enumerate rival grammar placeholders/categories within bounded local limits
- compare train-pair fit and competing output implications
- emit grammar-family labels and laundering flags

### Phase 4: class-audit integration
- generalize shared laundering checks into reusable helpers
- expose family-specific adapters for other modes later
- keep current lane limited to composed + MDL implementation first

### Phase 5: reporting and fixture wiring
- create small focused local fixtures for composed and MDL families
- ensure output records preserve direct-evidence vs missing-proof separation
- keep diagnostic output doc/report-only until separately approved for broader use

## 11. Tests required for future implementation
### Shared safety tests
- diagnostic does not ingest expected-answer fields into enumeration logic
- diagnostic never emits final answers
- diagnostic never changes deservedness decisions by itself
- no public-claim / runtime / `.weslr` side effects

### Composed-family tests
- enumerates alternative orders when component set exists
- marks `alternative_not_identified` when component structure is too thin
- distinguishes `component_support_only` from `whole_composition_forced`
- emits `direct_counterexample_found` when a viable alternative remains unrejected
- emits `missing_proof_only` when no alternative is found but proof is insufficient

### MDL-family tests
- distinguishes `rules_from_train` from actual train-forced uniqueness
- emits `simplicity_as_primary_evidence` when compactness dominates support
- enumerates competing grammar categories without expected-answer leakage
- distinguishes unrejected rival output from mere absence of rival enumeration
- emits `missing_proof_only` when no explicit grammar rival is identified

### Forcedness-laundering audit tests
- each supported family can emit a laundering type
- no family may escalate subclaim support into whole-claim forcedness without family-specific proof
- unsupported families may emit `insufficient_alternative_search` rather than false precision

## 12. Recommended next safe local follow-up
`IMPLEMENT_ARC_COMPOSED_AND_MDL_ALTERNATIVE_ENUMERATION_DIAGNOSTIC_V1`

Reason:
- the design is complete enough to implement as a diagnostic-only artifact
- the current evidence is strong enough to justify explicit enumeration tooling
- the current evidence is still not strong enough to skip that diagnostic and jump straight to final discrimination repair with specific rival claims
