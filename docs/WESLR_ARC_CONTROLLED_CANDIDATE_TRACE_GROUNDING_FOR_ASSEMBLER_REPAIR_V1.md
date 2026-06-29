# WESLR ARC CONTROLLED CANDIDATE TRACE GROUNDING FOR ASSEMBLER REPAIR V1

## 1. Executive verdict
`arc_controlled_candidate_trace_grounding_for_assembler_repaired_but_needs_review`

## 2. Review finding addressed
- The prior review found the repaired ledger deservedness assembler was correctly fail-closed but the live controlled candidate generator still emitted only minimal construction traces.
- This repair adds candidate-level trace-grounding fields to generator output so the generator → assembler interface carries explicit completeness, source-grounding, train-grounding, forced-uniqueness, and rival-grammar evidence when that evidence is actually present.
- The assembler boundary was preserved and not weakened.

## 3. Candidate trace grounding schema
Generated candidate descriptors now include candidate-level fields for:
- `requires_ledger_review`
- `candidate_treated_as_final_answer`
- `construction_trace`
- `construction_trace_complete`
- `construction_trace_source_grounded`
- `train_evidence_grounded`
- `forced_uniqueness_trace_present`
- `source_train_ids`
- `synthetic_local_train_ids`
- `train_grounded_transformation_rule`
- `train_grounded_forced_constraints`
- `ambiguity_check`
- `competing_output_rejection_reason`
- `uniquely_forced_reason`
- `unsupported_assumptions`
- `unresolved_rivals`
- `helper_output_as_evidence = False`
- `rehearsal_repeat_as_evidence = False`
- `mdl_only_support = False`

Compatibility aliases are also emitted for the repaired assembler path where needed:
- `source_train_example_ids`
- `forced_constraints_tied_to_train_evidence`
- `competing_outputs_rejected_reason`

## 4. Truthfulness rules
- `construction_trace_complete = True` only when the candidate has the full required proof bundle for its construction mode.
- `construction_trace_source_grounded = True` only when the candidate carries `source_train_ids` or `synthetic_local_train_ids`.
- `train_evidence_grounded = True` only when the candidate has train-backed source ids, a train-grounded transformation rule, train-grounded forced constraints, and mode-appropriate train support.
- `forced_uniqueness_trace_present = True` only when the candidate has train grounding, clear ambiguity state, no unresolved rivals, no unsupported assumptions, and non-empty competing-output rejection plus uniquely-forced reasons.
- Missing proof remains explicit via `missing_required_trace_fields`; missing proof is not converted into deservedness.

## 5. Rival grammar candidate grounding
- Explicit grammar candidates now carry rival-grammar fields when present:
  - `rival_grammars`
  - `surviving_grammar`
  - `rival_elimination_trace`
  - `surviving_grammar_train_evidence`
  - `rival_outputs_considered`
  - `rejected_rival_reasons`
  - `surviving_grammar_uniquely_forces_output`
- Unresolved rivals remain preserved in `unresolved_rivals`.
- Rival uniqueness is not asserted unless rival elimination and surviving-grammar train evidence are actually present.

## 6. Construction-mode-specific grounding
Completeness is now evaluated per construction mode:
- `relation_first_rewrite_candidate` — requires grounded rewrite trace, train ids, rule, constraints, ambiguity check, and uniqueness reasons.
- `object_correspondence_candidate` — requires grounded correspondence trace plus the same candidate-level evidence bundle.
- `invariant_preserving_candidate` — requires train-backed invariant grounding plus the same candidate-level evidence bundle.
- `composed_transform_candidate` — requires all-components-train-supported grounding plus the same candidate-level evidence bundle.
- `train_forced_transformation_candidate` — requires train-supported transformation grounding plus the same candidate-level evidence bundle.
- `explicit_grammar_candidate` — requires the same common evidence bundle and, when rival grammars are present, rival elimination and surviving-grammar train evidence.
- `partial_candidate_descriptor` — remains intentionally incomplete, not uniquely forced, and non-deserved.

## 7. Replay integration
- Replay integration was updated only to propagate the new generator-produced trace metrics and pass candidate descriptors through unchanged.
- No replay-local normalization layer was added.
- Replay does not invent missing proof and does not mark incomplete candidates complete.

## 8. Metrics
Generator and replay propagation now cover:
- `ledger_review_required_count`
- `construction_trace_complete_count`
- `forced_uniqueness_trace_present_count`
- `rival_elimination_trace_present_count`
- `train_evidence_grounded_count`
- `candidate_trace_missing_required_fields_count`
- `candidate_trace_source_grounded_count`
- `candidate_trace_incomplete_count`

## 9. Expected-answer boundary preservation
- Candidate generation does not read or emit `synthetic_expected_answer_for_scoring_only`.
- Expected/scoring answer fields remain outside candidate generation and outside deservedness proof.
- The assembler still fail-closes on scoring-answer leakage inside assembler input.
- Replay still keeps expected answer usage downstream of ledger decision.

## 10. Tests added/updated
Updated tests cover:
- generator candidate schema and truthfulness flags
- complete vs incomplete candidate grounding
- rival grammar grounding and unresolved rival preservation
- partial candidate behavior
- absence of expected-answer leakage in generated candidates
- helper/rehearsal/MDL anti-laundering boundaries
- generator-produced complete candidate passing assembler
- generator-produced incomplete candidate safe-failing through assembler
- replay propagation and trace metric counting
- expected-answer scoring boundary and emitter hard-stop preservation
- no runtime wiring

## 11. Safety boundaries
- local only
- no push
- no replay run
- no expected-answer use in generation or deservedness
- no emitter implementation
- no runtime solver wiring
- no ChatResponder change
- no `.weslr`
- no protected-file edits
- no public ARC/Kaggle data or external calls

## 12. Recommended next safe local follow-up
`REVIEW_ARC_CONTROLLED_CANDIDATE_TRACE_GROUNDING_FOR_ASSEMBLER_REPAIR_V1`
