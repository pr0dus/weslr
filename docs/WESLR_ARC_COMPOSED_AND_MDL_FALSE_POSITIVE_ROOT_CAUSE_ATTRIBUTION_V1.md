# WESLR ARC COMPOSED AND MDL FALSE POSITIVE ROOT CAUSE ATTRIBUTION V1

## 1. Executive verdict
`arc_composed_and_mdl_false_positive_attribution_complete_with_notes`

## 2. Scope
- Local attribution only.
- No repair applied.
- No full replay rerun.
- No emitter work.
- No threshold change.
- No expected-answer use inside generation or deservedness.
- Expected-answer scoring used only after ledger decision for diagnostic labeling.
- No runtime wiring.
- No ChatResponder changes.
- No `.weslr`.
- No external calls.

Artifacts inspected:
- `docs/WESLR_ARC_NON_RIVAL_TRACE_COMPLETE_FALSE_POSITIVES_SPLIT_DIAGNOSIS_V1.md`
- `docs/WESLR_ARC_GENERATIVE_BRIDGE_V5_REPLAY_AFTER_RIVAL_FALSE_UNIQUENESS_REPAIR_RUN_V1.md`
- live per-case generator outputs for the currently wrong-labeled composed and MDL cases
- live per-case ledger decision traces for those cases
- replay task-builder inputs for those cases

Important note about post-ledger labels:
- the current replay implementation assigns `exact` vs `deserved_but_wrong` after ledger decision using a local synthetic scorer path keyed off `hash(task_id)`
- therefore the per-task wrong labels used here are the current local implementation result
- they do **not** reflect trace differences inside a family
- attribution below is therefore about the accepted proof pattern of the wrong-labeled cases, not about any case-specific trace delta that separates wrong from exact siblings

## 3. Composed-transform per-case attribution
### Family-wide attribution note
All currently wrong-labeled composed cases share the same accepted trace structure:
- accepted construction mode: `composed_transform_candidate`
- accepted trace summary:
  - `Train examples support the composed transformation chain.`
  - `Every composed transformation component is supported by train examples.`
  - `ambiguity_check = clear`
  - generic competing-output rejection text only
  - generic uniquely-forced text only
- task-builder input for each case: `{"composed_transform_candidates": [{"all_components_train_supported": true}]}`
- actual alternative component orders/compositions identified: **no**
- non-rejection of alternatives is inferred from absence of proof, not demonstrated by enumerated rivals

### Case 1
- task_id: `v5_replay_v4_composed_transform_replay_6_14`
- accepted construction mode: `composed_transform_candidate`
- accepted trace summary:
  - rule: `Train examples support the composed transformation chain.`
  - forced constraints: `Every composed transformation component is supported by train examples.`
  - competing-output rejection: `Train-grounded constraints reject competing outputs inconsistent with composed_transform_candidate.`
  - uniquely-forced reason: `Available train-grounded constraints uniquely force the candidate through composed_transform_candidate.`
- post-ledger scoring label: `deserved_but_wrong`
- applicable root-cause tags:
  - `composition_not_train_supported_as_unit`
  - `component_level_forcedness_laundered_as_composition_forcedness`
  - `component_order_not_proven`
  - `component_interaction_not_checked`
  - `alternative_composition_not_rejected`
  - `partial_transform_false_completion`
- evidence status by tag:
  - directly evidenced by trace/task structure:
    - `composition_not_train_supported_as_unit`
    - `component_level_forcedness_laundered_as_composition_forcedness`
  - inferred from missing trace fields:
    - `component_order_not_proven`
    - `component_interaction_not_checked`
    - `alternative_composition_not_rejected`
    - `partial_transform_false_completion`
- actual alternative component order/composition identified: no
- alternative note: non-rejection is inferred from absence of component-order / composition-rejection proof

### Case 2
- task_id: `v5_replay_v4_composed_transform_replay_6_16`
- accepted construction mode: `composed_transform_candidate`
- accepted trace summary: same accepted composed-family trace as Case 1
- post-ledger scoring label: `deserved_but_wrong`
- applicable root-cause tags:
  - `composition_not_train_supported_as_unit`
  - `component_level_forcedness_laundered_as_composition_forcedness`
  - `component_order_not_proven`
  - `component_interaction_not_checked`
  - `alternative_composition_not_rejected`
  - `partial_transform_false_completion`
- evidence status by tag:
  - directly evidenced by trace/task structure:
    - `composition_not_train_supported_as_unit`
    - `component_level_forcedness_laundered_as_composition_forcedness`
  - inferred from missing trace fields:
    - `component_order_not_proven`
    - `component_interaction_not_checked`
    - `alternative_composition_not_rejected`
    - `partial_transform_false_completion`
- actual alternative component order/composition identified: no
- alternative note: non-rejection is inferred from absence of component-order / composition-rejection proof

### Case 3
- task_id: `v5_replay_v4_composed_transform_replay_6_17`
- accepted construction mode: `composed_transform_candidate`
- accepted trace summary: same accepted composed-family trace as Case 1
- post-ledger scoring label: `deserved_but_wrong`
- applicable root-cause tags:
  - `composition_not_train_supported_as_unit`
  - `component_level_forcedness_laundered_as_composition_forcedness`
  - `component_order_not_proven`
  - `component_interaction_not_checked`
  - `alternative_composition_not_rejected`
  - `partial_transform_false_completion`
- evidence status by tag:
  - directly evidenced by trace/task structure:
    - `composition_not_train_supported_as_unit`
    - `component_level_forcedness_laundered_as_composition_forcedness`
  - inferred from missing trace fields:
    - `component_order_not_proven`
    - `component_interaction_not_checked`
    - `alternative_composition_not_rejected`
    - `partial_transform_false_completion`
- actual alternative component order/composition identified: no
- alternative note: non-rejection is inferred from absence of component-order / composition-rejection proof

### Case 4
- task_id: `v5_replay_v4_composed_transform_replay_6_18`
- accepted construction mode: `composed_transform_candidate`
- accepted trace summary: same accepted composed-family trace as Case 1
- post-ledger scoring label: `deserved_but_wrong`
- applicable root-cause tags:
  - `composition_not_train_supported_as_unit`
  - `component_level_forcedness_laundered_as_composition_forcedness`
  - `component_order_not_proven`
  - `component_interaction_not_checked`
  - `alternative_composition_not_rejected`
  - `partial_transform_false_completion`
- evidence status by tag:
  - directly evidenced by trace/task structure:
    - `composition_not_train_supported_as_unit`
    - `component_level_forcedness_laundered_as_composition_forcedness`
  - inferred from missing trace fields:
    - `component_order_not_proven`
    - `component_interaction_not_checked`
    - `alternative_composition_not_rejected`
    - `partial_transform_false_completion`
- actual alternative component order/composition identified: no
- alternative note: non-rejection is inferred from absence of component-order / composition-rejection proof

## 4. MDL-trap per-case attribution
### Family-wide attribution note
All currently wrong-labeled MDL cases share the same accepted trace structure:
- accepted construction mode: `explicit_grammar_candidate`
- accepted trace summary:
  - `Train examples support grammar the surviving grammar.`
  - `Grammar surviving_grammar is supported by train-derived rules.`
  - `ambiguity_check = clear`
  - generic competing-output rejection text only
  - generic uniquely-forced text only
  - `mdl_only_support = false`
- task-builder input for each case: `{"explicit_candidate_grammars": [{"rules_from_train": true}]}`
- actual competing grammar identified: **no**
- actual competing output identified: **no**
- non-consideration / non-rejection is inferred from absence of proof, not demonstrated by enumerated rivals

### Case 1
- task_id: `v5_replay_mdl_simplicity_trap_6_44`
- accepted construction mode: `explicit_grammar_candidate`
- accepted trace summary:
  - rule: `Train examples support grammar the surviving grammar.`
  - forced constraints: `Grammar surviving_grammar is supported by train-derived rules.`
  - competing-output rejection: `Train-grounded constraints reject competing outputs inconsistent with explicit_grammar_candidate.`
  - uniquely-forced reason: `Available train-grounded constraints uniquely force the candidate through explicit_grammar_candidate.`
- post-ledger scoring label: `deserved_but_wrong`
- applicable root-cause tags:
  - `simplicity_laundered_as_train_forcing`
  - `mdl_primary_evidence_not_detected`
  - `negative_evidence_missing`
  - `competing_grammar_not_considered`
  - `competing_outputs_not_rejected`
- evidence status by tag:
  - directly evidenced by trace/task structure:
    - `simplicity_laundered_as_train_forcing`
    - `mdl_primary_evidence_not_detected`
  - inferred from missing trace fields:
    - `negative_evidence_missing`
    - `competing_grammar_not_considered`
    - `competing_outputs_not_rejected`
- actual competing grammar identified: no
- actual competing output identified: no
- competing note: non-consideration / non-rejection is inferred from absence of competing-grammar proof

### Case 2
- task_id: `v5_replay_mdl_simplicity_trap_6_45`
- accepted construction mode: `explicit_grammar_candidate`
- accepted trace summary: same accepted MDL-family trace as Case 1
- post-ledger scoring label: `deserved_but_wrong`
- applicable root-cause tags:
  - `simplicity_laundered_as_train_forcing`
  - `mdl_primary_evidence_not_detected`
  - `negative_evidence_missing`
  - `competing_grammar_not_considered`
  - `competing_outputs_not_rejected`
- evidence status by tag:
  - directly evidenced by trace/task structure:
    - `simplicity_laundered_as_train_forcing`
    - `mdl_primary_evidence_not_detected`
  - inferred from missing trace fields:
    - `negative_evidence_missing`
    - `competing_grammar_not_considered`
    - `competing_outputs_not_rejected`
- actual competing grammar identified: no
- actual competing output identified: no
- competing note: non-consideration / non-rejection is inferred from absence of competing-grammar proof

### Case 3
- task_id: `v5_replay_mdl_simplicity_trap_6_46`
- accepted construction mode: `explicit_grammar_candidate`
- accepted trace summary: same accepted MDL-family trace as Case 1
- post-ledger scoring label: `deserved_but_wrong`
- applicable root-cause tags:
  - `simplicity_laundered_as_train_forcing`
  - `mdl_primary_evidence_not_detected`
  - `negative_evidence_missing`
  - `competing_grammar_not_considered`
  - `competing_outputs_not_rejected`
- evidence status by tag:
  - directly evidenced by trace/task structure:
    - `simplicity_laundered_as_train_forcing`
    - `mdl_primary_evidence_not_detected`
  - inferred from missing trace fields:
    - `negative_evidence_missing`
    - `competing_grammar_not_considered`
    - `competing_outputs_not_rejected`
- actual competing grammar identified: no
- actual competing output identified: no
- competing note: non-consideration / non-rejection is inferred from absence of competing-grammar proof

## 5. Cause concentration vs spread
### Composed-transform
- The 4 wrong composed cases are caused by **two dominant direct causes** plus a repeated cluster of secondary missing-proof inferences.
- Dominant direct causes:
  - `composition_not_train_supported_as_unit`
  - `component_level_forcedness_laundered_as_composition_forcedness`
- Secondary inferred causes:
  - `component_order_not_proven`
  - `component_interaction_not_checked`
  - `alternative_composition_not_rejected`
  - `partial_transform_false_completion`
- Minimum safe repair shape:
  - **not** several unrelated sub-fixes
  - one narrow family fix that fail-closes composition-level deservedness unless composition-as-a-unit proof exists
  - additional order / interaction / rejection detail can be required under that same family gate

### MDL-trap
- The 3 wrong MDL cases are caused by **two dominant direct causes** plus a repeated cluster of secondary missing-proof inferences.
- Dominant direct causes:
  - `simplicity_laundered_as_train_forcing`
  - `mdl_primary_evidence_not_detected`
- Secondary inferred causes:
  - `negative_evidence_missing`
  - `competing_grammar_not_considered`
  - `competing_outputs_not_rejected`
- Minimum safe repair shape:
  - one narrow family fix that fail-closes explicit-grammar deservedness when proof shows only train-derived grammar wording without rival / negative-evidence support
  - not several unrelated sub-fixes

## 6. Direct evidence vs missing-proof inference
### A. Directly demonstrated by actual trace/task structure
#### Composed-transform
- `composition_not_train_supported_as_unit`
- `component_level_forcedness_laundered_as_composition_forcedness`

Why direct:
- the accepted task-builder input supplies only `all_components_train_supported = true`
- the accepted trace upgrades that directly into `Train examples support the composed transformation chain.` plus generic uniqueness language
- no stronger composition-level proof object exists anywhere in the accepted artifact

#### MDL-trap
- `simplicity_laundered_as_train_forcing`
- `mdl_primary_evidence_not_detected`

Why direct:
- the accepted task-builder input supplies only `rules_from_train = true`
- the accepted trace upgrades that into `Train examples support grammar the surviving grammar.` plus generic uniqueness language
- `mdl_only_support = false` means the MDL blocker is not triggered, even though no rival/negative-evidence support exists

### B. Inferred from absent proof fields
#### Composed-transform
- `component_order_not_proven`
- `component_interaction_not_checked`
- `alternative_composition_not_rejected`
- `partial_transform_false_completion`

#### MDL-trap
- `negative_evidence_missing`
- `competing_grammar_not_considered`
- `competing_outputs_not_rejected`

Why inferred:
- current accepted traces contain no explicit alternative enumeration or rejection packets
- current accepted traces also contain no family-specific proof fields demonstrating those checks occurred
- therefore non-rejection / non-consideration is inferred from absence of proof, not from explicit failed comparisons

### C. Uncertain / needs stronger diagnostic artifact
- actual alternative component order for any wrong composed case
- actual alternative composition for any wrong composed case
- actual competing grammar for any wrong MDL case
- actual competing output for any wrong MDL case

Current evidence does **not** identify specific rivals. It only proves the system accepted the cases without proving that such rivals were checked.

## 7. Alternative composition / competing grammar evidence
### Composed-transform
- Actual alternative compositions identified: **no**
- Actual alternative component orders identified: **no**
- Therefore `alternative_composition_not_rejected` is a missing-proof inference, not a verified un-rejected rival

### MDL-trap
- Actual competing grammars identified: **no**
- Actual competing outputs identified: **no**
- Therefore `competing_grammar_not_considered` and `competing_outputs_not_rejected` are missing-proof inferences, not verified ignored rivals

Practical implication:
- the current attribution is strong enough to justify a fail-closed proof requirement
- it is **not** strong enough to pretend the system already knows which rival composition or rival grammar should be rejected

## 8. Repair scoping recommendation
`DESIGN_ARC_COMPOSED_AND_MDL_ALTERNATIVE_ENUMERATION_DIAGNOSTIC_V1`

Reason:
- both families already show a clear fail-open proof problem
- but the current traces do not enumerate actual alternatives / rivals
- the user explicitly asked to distinguish direct rival evidence from missing-proof inference
- at this point, a repair that claims to reject specific alternatives would outrun the evidence
- the safer next step is a diagnostic design that defines how composed alternatives and grammar rivals should be represented, checked, and surfaced before discrimination repair is implemented

This recommendation does **not** overturn the prior split diagnosis. It narrows the next step:
- first design the alternative-enumeration diagnostic artifact
- then repair composed and MDL discrimination against that explicit proof surface

## 9. Safety boundaries
Confirmed preserved:
- local only
- diagnosis/report only
- no push
- no public ARC/Kaggle data
- no hidden test output use
- no expected-answer use in generation or deservedness
- expected-answer use only after ledger decision for labeling
- no runtime wiring
- no ChatResponder changes
- no final-answer emission
- no emitter implementation
- no `.weslr`
- no external calls
- protected files unchanged

## 10. Recommended next safe local follow-up
`DESIGN_ARC_COMPOSED_AND_MDL_ALTERNATIVE_ENUMERATION_DIAGNOSTIC_V1`
