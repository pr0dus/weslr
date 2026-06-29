# WESLR ARC CONTROLLED CANDIDATE TRACE GROUNDING FOR ASSEMBLER REPAIR REVIEW V1

## 1. Executive verdict
`arc_controlled_candidate_trace_grounding_for_assembler_repair_review_valid_with_notes`

## 2. Review scope
- Reviewed the repair report, prior review report, controlled generator module, repaired assembler module, repaired replay module, and the targeted generator/assembler/replay tests.
- Did not rerun the replay lane.
- Did not modify runtime, emitter, protected files, or `.weslr`.

## 3. Candidate trace grounding schema review
- **Valid:** generated candidates now include the requested candidate-level trace-grounding schema:
  - `requires_ledger_review = True`
  - `candidate_treated_as_final_answer = False`
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
- **Valid:** compatibility aliases are also present where needed for the assembler path (`source_train_example_ids`, `forced_constraints_tied_to_train_evidence`, `competing_outputs_rejected_reason`).

## 4. Truthfulness rules review
- **Valid:** the key flags are not constants and do not appear to fake proof.
- Direct spot checks across generated cases show:
  - complete train-forced candidate → `construction_trace_complete = True`, `train_evidence_grounded = True`, `forced_uniqueness_trace_present = True`
  - incomplete train-forced candidate → those flags fall to `False` and `missing_required_trace_fields` records the missing proof
  - resolved explicit-grammar candidate → `rival_elimination_trace_present = True`
  - unresolved explicit-grammar candidate → `rival_elimination_trace_present = False`, `forced_uniqueness_trace_present = False`, unresolved rivals preserved
  - partial candidate → incomplete and not uniquely forced
- **Valid:** missing proof is recorded explicitly through `missing_required_trace_fields` and does not make the candidate appear deserved-ready.

## 5. Rival grammar grounding review
- **Valid:** rival grammar set appears when relevant.
- **Valid:** surviving grammar is emitted only when the candidate path actually has a resolved surviving grammar.
- **Valid:** rival elimination trace is emitted only when supported; unresolved rival cases keep it empty/false.
- **Valid:** surviving-grammar train evidence is present in the resolved explicit-grammar path.
- **Valid:** unresolved rivals are preserved in `unresolved_rivals`, not hidden.
- **Valid:** `surviving_grammar_uniquely_forces_output` is only true in the resolved rival-elimination path with train evidence.

## 6. Construction-mode-specific grounding review
- **Valid:** completeness is mode-specific rather than globally constant.
- Spot review across all 7 construction modes found:
  - `object_correspondence_candidate` can become complete when train-supported
  - `invariant_preserving_candidate` can become complete when train-supported
  - `composed_transform_candidate` can become complete when all components are train-supported
  - `train_forced_transformation_candidate` can become complete when train-grounded constraints are present
  - `explicit_grammar_candidate` can become complete only when rival proof is present where relevant
  - `partial_candidate_descriptor` remains incomplete and not uniquely forced
- **Note:** `relation_first_rewrite_candidate` currently stays fail-closed/incomplete in the reviewed synthetic path unless source-grounding proof is explicitly present. That is safe and truthful, not a false-complete regression.

## 7. Replay integration review
- **Valid:** replay passes candidate descriptors into the assembler without mutating the candidate fields.
- **Valid:** replay does not invent proof or normalize incomplete candidates into complete candidates.
- **Valid:** replay metrics count completeness/grounding from candidate fields.
- **Valid:** generation still occurs before ledger evaluation, and ledger evaluation still occurs before scoring.

## 8. Expected-answer boundary review
- **Valid:** generated candidates do not contain scoring-only or expected-answer fields such as:
  - `synthetic_expected_answer_for_scoring_only`
  - `expected_output`
  - `expected_answer`
  - `deserved_exact_result`
  - `deserved_but_wrong_result`
  - `post_ledger_scoring_result`
- **Valid:** replay keeps expected answers on the outer task object and preserves scoring-after-ledger order.
- **Valid:** assembler still fail-closes if scoring-only keys leak into assembler input.

## 9. Metrics review
- **Valid:** the requested metrics are present and increment from actual candidate fields, not constants:
  - `ledger_review_required_count`
  - `construction_trace_complete_count`
  - `forced_uniqueness_trace_present_count`
  - `rival_elimination_trace_present_count`
  - `train_evidence_grounded_count`
  - `candidate_trace_missing_required_fields_count`
  - `candidate_trace_source_grounded_count`
  - `candidate_trace_incomplete_count`
- Spot checks confirmed complete and incomplete generated candidates produce different metric values as expected.

## 10. Regression risk review
- **Regression risk found: no material new regression in the repaired path.**
- Confirmed during review:
  - assembler safety boundary is not weakened
  - trace flags are not constant yes-values
  - not all candidates appear complete
  - unresolved rivals are not hidden
  - helper output is not treated as evidence
  - rehearsal repeat is not treated as evidence
  - MDL-only support is not treated as proof
  - emitter hard stops remain unchanged in the reviewed replay path
  - protected files remain untouched
  - `.weslr` remains untouched
- **Review note:** the relation-first rewrite path remains conservative/fail-closed unless explicit source-grounding proof exists. That is a coverage note, not a safety regression.

## 11. Validation summary
- Targeted generator, assembler, and replay test suites passed.
- Release gate passed.
- `git diff --check` was clean.
- Release check passed.
- Source-repo health check passed with optional WARNs only.
- Protected files remained unchanged.
- `.weslr` remained untouched.

## 12. Recommended next safe local follow-up
`RUN_ARC_GENERATIVE_BRIDGE_V5_REPLAY_AFTER_TRACE_GROUNDING_REPAIR_V1`
