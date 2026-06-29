# WESLR ARC REPLAY SCORING REPAIR REVIEW SUPPLEMENT LEDGER INDEPENDENCE V1

## 1. Executive verdict
`arc_replay_scoring_repair_review_supplement_valid_with_notes`

## 2. Scope
This is a narrow supplement to:
- `docs/WESLR_ARC_REPLAY_SCORING_AND_PER_TASK_PROVENANCE_REPAIR_REVIEW_V1.md`
- `docs/WESLR_ARC_REPLAY_SCORING_AND_PER_TASK_PROVENANCE_REPAIR_V1.md`

Supplement-only focus:
- ledger/gating independence from exact/wrong scoring
- test contamination scan
- reachable RNG/hash audit
- unscorable reason completeness

No replay repair redesign was done here.

## 3. Ledger/gating independence audit
Review result: valid.

Code-level findings:
- `weslr/arc_controlled_answer_candidate_generator.py` does not read or branch on:
  - `deserved_exact`
  - `deserved_but_wrong`
  - `undeserved_exact`
  - `task_exact`
  - `post_ledger_scoring_status`
  - `synthetic_randomized_stress_label`
  - any exact/wrong scoring result
- `weslr/arc_ledger_deservedness_assembler.py` does not use exact/wrong scoring outputs in deservedness decisions
- the assembler explicitly fail-closes on scoring-answer leakage via `_FORBIDDEN_SCORING_KEYS`, including:
  - `synthetic_expected_answer_for_scoring_only`
  - `expected_output`
  - `expected_answer`
  - `post_ledger_scoring_result`
  - `deserved_exact_result`
  - `deserved_but_wrong_result`
  - `scoring_result`
- in `weslr/arc_generative_bridge_v5_replay.py`, ledger decision is set before `_score_post_ledger(...)` runs
- `candidate_deserved`, `candidate_not_deserved`, and `safe_failure` are computed upstream of scoring
- scoring does not feed back into candidate construction
- scoring does not feed back into assembler deservedness
- rival-context safe-failure behavior remains driven by generator/assembler trace conditions, not by exact/wrong labels

Important note:
- replay emitter-threshold/hard-stop summaries still consume post-ledger scoring counts after the ledger decision is made
- this does not contaminate preserved ledger/safety conclusions, but it does mean downstream replay-gate interpretation still depends on whether scoring is real or unscorable
- that dependence was already correctly downgraded in the main review/repair reports

## 4. Test contamination scan
Review result: no contamination found.

Confirmed from test scan:
- replay tests no longer assert fake exact/wrong outcomes as correctness for live V5 tasks
- exact/wrong assertions exist only in controlled override tests where a real synthetic candidate-output surface is explicitly supplied
- replay tests explicitly assert `unscorable_due_to_missing_candidate_output` when candidate output is missing
- candidate-deserved / safe-failure assertions remain in place and are safe because ledger independence is confirmed in code
- no test asserts pre-repair random exact-rate behavior
- no test asserts old MDL/composed wrong-ID sets as correctness evidence
- no test asserts pre-repair hard-stop behavior caused by RNG-derived wrong labels, except where a real override-based wrong output intentionally triggers the hard stop under the repaired deterministic scorer

Note on generator tests:
- generator tests still mention `deserved_exact_result` / `deserved_but_wrong_result` only as forbidden scoring-leakage field names in boundary checks, not as valid correctness outputs
- that is appropriate and non-contaminating

## 5. Reachable RNG/hash audit
Review result: no reachable RNG/hash scoring path found.

Confirmed in reachable code paths:
- no `hash()`-based exact/wrong scoring path exists in replay/generator/assembler modules
- no `random.seed`
- no `random.random`
- no RNG fallback path for correctness labels
- no RNG tie-breaker path for correctness labels
- no RNG candidate-selection influence for correctness labels

This audit is about reachable code, not stale docs/comments.
Current reachable implementation is clean.

## 6. Unscorable reason completeness
Review result: valid with a note.

Confirmed every current V5 unscorable record has machine-readable fields sufficient to explain why it is unscorable:
- `post_ledger_scoring_status`
- `candidate_output_available`
- `expected_output_available`
- `post_ledger_scoring_mechanism`
- `post_ledger_scoring_seed_or_determinism_note`
- `rng_or_hash_influenced_scoring`
- `rng_or_hash_influence_type`
- `candidate_trace_provenance`
- `scoring_mechanism_classification`

Current live V5 interpretation is machine-readable and sufficient:
- expected output exists
- candidate output is unavailable
- scoring mechanism is `candidate_output_unavailable`
- classification is `unscorable_due_to_missing_candidate_output`
- trace provenance indicates whether the candidate came from override or generated inputs

Note:
- the current reason code is coarse but adequate for this stage
- no additional provenance-reason-code repair is required before candidate-output/trace-surface design

## 7. Impact on existing review verdict
Result:
- the existing review verdict remains valid
- this supplement strengthens it by confirming ledger/safety conclusions are code-level independent from the old fake exact/wrong scoring path
- no narrow contamination repair lane is required from this supplement

## 8. Recommended next safe local follow-up
`DESIGN_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_FOR_REAL_SCORING_V1`

Why:
- ledger/gating independence is confirmed
- test contamination was not found
- reachable RNG/hash scoring paths are gone
- unscorable reasons are machine-readable enough for the next design step
- the next blocker is providing candidate-output and supporting trace surface so replay can perform real post-ledger correctness comparison on live V5 tasks
