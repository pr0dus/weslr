# WESLR ARC NON-RIVAL TRACE-COMPLETE FALSE POSITIVES SPLIT DIAGNOSIS V1

## 1. Executive verdict
`arc_non_rival_trace_complete_false_positives_split_diagnosis_complete_with_notes`

## 2. Scope
- Local diagnosis only.
- No full replay rerun.
- No repair applied.
- No emitter work.
- No expected-answer use inside generation or deservedness.
- Expected-answer scoring used only after ledger decision for local diagnostic labeling of the already-deserved 12 cases.
- No runtime wiring.
- No ChatResponder changes.
- No `.weslr`.
- No external calls.
- Protected files remained outside diagnostic scope.

Evidence inspected:
- `docs/WESLR_ARC_GENERATIVE_BRIDGE_V5_REPLAY_AFTER_RIVAL_FALSE_UNIQUENESS_REPAIR_RUN_V1.md`
- live generator behavior for the 12 current deserved cases
- live ledger decision traces for the 12 current deserved cases
- synthetic replay task builder for `v4_composed_transform_replay_6` and `mdl_simplicity_trap_6`
- live rival-group spot-check to confirm the prior repair still closes the known bypass

## 3. Rival repair success confirmation
Confirmed closed as a local issue for this branch state:
- `v4_rival_grammar_replay_6` no longer produces unsafe deservedness.
- The known train-forced rival bypass is blocked.
- Current result is `0 deserved`, `6 safe failures`, `0 deserved-but-wrong` for the rival group.
- `rival_context_detected_count = 6`.
- `rival_context_safe_failure_count = 6`.
- `train_forced_rival_bypass_blocked_count = 6`.
- The intended conservative outcome is now active: safe failure until rival-proof fields exist.
- No regression was found that would justify including rival-grammar in the next repair lane.

Why this is considered closed for the next lane:
- rival candidates are no longer allowed to cross the ledger on trace-complete wording alone
- unresolved rival context now collapses forced uniqueness instead of laundering it
- the remaining hard stop comes entirely from non-rival trace-complete cases

## 4. Twelve deserved cases inspected
### Summary note
All 12 current deserved cases were inspected live.

Important structural finding:
- within `v4_composed_transform_replay_6`, all 6 deserved cases share the same candidate/ledger trace pattern except for `task_id` and post-ledger scoring label
- within `mdl_simplicity_trap_6`, all 6 deserved cases share the same candidate/ledger trace pattern except for `task_id` and post-ledger scoring label
- therefore the exact vs deserved-but-wrong split is **not** explained by different trace evidence inside a family; the ledger is accepting the same family-level proof template across all 6 cases in each family

### 4.1 Composed-transform deserved cases inspected
For every composed case below:
- construction mode: `composed_transform_candidate`
- candidate descriptor core: `source_constraints=["composed_transform"]`, `construction_trace_complete=true`, `forced_uniqueness_trace_present=true`, `train_evidence_grounded=true`, `mdl_only_support=false`, `rival_context_detected=false`
- train-grounded transformation rule: `Train examples support the composed transformation chain.`
- train-grounded forced constraints: `Every composed transformation component is supported by train examples.`
- forced-uniqueness trace: `Available train-grounded constraints uniquely force the candidate through composed_transform_candidate.`
- competing-output rejection reason: `Train-grounded constraints reject competing outputs inconsistent with composed_transform_candidate.`
- ambiguity check: `clear`
- ledger decision trace: single generic trace only — `candidate_deserved / candidate_level_trace_grounding / explicit`

| task_id | group_id | post-ledger scoring label |
|---|---|---|
| `v5_replay_v4_composed_transform_replay_6_13` | `v4_composed_transform_replay_6` | `exact` |
| `v5_replay_v4_composed_transform_replay_6_14` | `v4_composed_transform_replay_6` | `deserved_but_wrong` |
| `v5_replay_v4_composed_transform_replay_6_15` | `v4_composed_transform_replay_6` | `deserved_but_wrong` |
| `v5_replay_v4_composed_transform_replay_6_16` | `v4_composed_transform_replay_6` | `deserved_but_wrong` |
| `v5_replay_v4_composed_transform_replay_6_17` | `v4_composed_transform_replay_6` | `deserved_but_wrong` |
| `v5_replay_v4_composed_transform_replay_6_18` | `v4_composed_transform_replay_6` | `exact` |

Representative construction trace actually accepted in all 6 composed cases:
```json
[
  {
    "step_id": 0,
    "source_helper": "local_generator",
    "source_constraint": "composed_transform",
    "operation": "transform",
    "train_support": true,
    "assumption_status": "forced",
    "rival_impact": "none",
    "ledger_relevance": "required",
    "evidence_status": "train_explicit",
    "source_train_ids": ["train_1"],
    "train_grounded_transformation_rule": "Train examples support the composed transformation chain.",
    "train_grounded_forced_constraints": [
      "Every composed transformation component is supported by train examples."
    ],
    "ambiguity_check": "clear",
    "competing_output_rejection_reason": "Train-grounded constraints reject competing outputs inconsistent with composed_transform_candidate.",
    "uniquely_forced_reason": "Available train-grounded constraints uniquely force the candidate through composed_transform_candidate."
  }
]
```

### 4.2 MDL-simplicity-trap deserved cases inspected
For every MDL case below:
- construction mode: `explicit_grammar_candidate`
- candidate descriptor core: `source_constraints=["explicit_grammar"]`, `construction_trace_complete=true`, `forced_uniqueness_trace_present=true`, `train_evidence_grounded=true`, `mdl_only_support=false`, `rival_context_detected=false`
- train-grounded transformation rule: `Train examples support grammar the surviving grammar.`
- train-grounded forced constraints: `Grammar surviving_grammar is supported by train-derived rules.`
- forced-uniqueness trace: `Available train-grounded constraints uniquely force the candidate through explicit_grammar_candidate.`
- competing-output rejection reason: `Train-grounded constraints reject competing outputs inconsistent with explicit_grammar_candidate.`
- ambiguity check: `clear`
- ledger decision trace: single generic trace only — `candidate_deserved / candidate_level_trace_grounding / explicit`

| task_id | group_id | post-ledger scoring label |
|---|---|---|
| `v5_replay_mdl_simplicity_trap_6_43` | `mdl_simplicity_trap_6` | `deserved_but_wrong` |
| `v5_replay_mdl_simplicity_trap_6_44` | `mdl_simplicity_trap_6` | `deserved_but_wrong` |
| `v5_replay_mdl_simplicity_trap_6_45` | `mdl_simplicity_trap_6` | `exact` |
| `v5_replay_mdl_simplicity_trap_6_46` | `mdl_simplicity_trap_6` | `exact` |
| `v5_replay_mdl_simplicity_trap_6_47` | `mdl_simplicity_trap_6` | `exact` |
| `v5_replay_mdl_simplicity_trap_6_48` | `mdl_simplicity_trap_6` | `exact` |

Representative construction trace actually accepted in all 6 MDL cases:
```json
[
  {
    "step_id": 0,
    "source_helper": "local_generator",
    "source_constraint": "explicit_grammar",
    "operation": "transform",
    "train_support": true,
    "assumption_status": "forced",
    "rival_impact": "none",
    "ledger_relevance": "required",
    "evidence_status": "train_explicit",
    "source_train_ids": ["train_1"],
    "train_grounded_transformation_rule": "Train examples support grammar the surviving grammar.",
    "train_grounded_forced_constraints": [
      "Grammar surviving_grammar is supported by train-derived rules."
    ],
    "ambiguity_check": "clear",
    "competing_output_rejection_reason": "Train-grounded constraints reject competing outputs inconsistent with explicit_grammar_candidate.",
    "uniquely_forced_reason": "Available train-grounded constraints uniquely force the candidate through explicit_grammar_candidate."
  }
]
```

## 5. Composed-transform diagnosis
### Direct answer
Yes. In the composed family, the current system is effectively treating:
- `each component looks forced`
as if it were:
- `the full composition is forced`

### Evidence from inspected traces
The only composed-family proof actually present is:
- `Train examples support the composed transformation chain.`
- `Every composed transformation component is supported by train examples.`
- generic forced-uniqueness and generic competing-output rejection text

What is **not** present in the accepted trace:
- no component list
- no component order proof
- no component interaction proof
- no whole-composition proof packet
- no statement that all train pairs require the same ordered composition as a unit
- no alternative component order rejection
- no alternative composition rejection
- no explicit proof that a partial transform was excluded

### Requested checks
Wrong composed cases lack proof of:
- component order — **yes, missing**
- component interaction — **yes, missing**
- whole-composition support — **yes, missing as a unit**
- all components explaining all train pairs — **yes, missing**
- alternative component orders being rejected — **yes, missing**
- alternative compositions being rejected — **yes, missing**
- partial transform masquerading as full transform — **not ruled out by the accepted trace**
- train evidence forcing the composition as a unit — **yes, missing**

### Composed root-cause classification
- `component_order_not_proven`
- `component_interaction_not_checked`
- `composition_not_train_supported_as_unit`
- `alternative_composition_not_rejected`
- `partial_transform_false_completion`
- `component_level_forcedness_laundered_as_composition_forcedness`

## 6. MDL-simplicity-trap diagnosis
### Direct answer
Yes. In the MDL family, the current system is effectively treating:
- `compact grammar with train-derived wording`
as if it were:
- `train-forced unique grammar`

### Evidence from inspected traces
The only MDL-family proof actually present is:
- `Train examples support grammar the surviving grammar.`
- `Grammar surviving_grammar is supported by train-derived rules.`
- generic forced-uniqueness and generic competing-output rejection text
- `mdl_only_support=false`

What is **not** present in the accepted trace:
- no named rival grammar set
- no explicit more-complex rival considered
- no negative-evidence packet against the wrong-simple rule
- no proof that the grammar was forced by train evidence rather than merely compact
- no explicit rejection of competing grammar outputs
- no family-specific MDL trap detector triggered

Why `mdl_only_rejected_count = 0` despite this family:
- the generator marks MDL-only only when `operations.get("mdl_only")` is true **and** `rules_from_train` is false
- the replay builder for this family only supplies `{"rules_from_train": true}`
- therefore these candidates bypass the MDL-only rejection path entirely and are accepted as train-grounded explicit grammars

### Requested checks
Wrong MDL cases show:
- MDL/elegance as primary evidence — **not explicitly tagged, but the accepted proof is too generic to distinguish compactness from train forcing**
- compact grammar treated as proof — **yes**
- no negative evidence against wrong-simple rule — **yes**
- no explicit more-complex rival considered — **yes**
- grammar does not explain all train pairs — **not proven by the accepted trace; the trace is too generic to establish all-pair coverage**
- competing grammar outputs not rejected — **yes, only generic rejection wording is present**
- forced uniqueness is compression-grounded rather than train-grounded — **the trace does not prove train-forced uniqueness beyond generic wording, so this risk remains live**

### MDL root-cause classification
- `mdl_primary_evidence_not_detected`
- `simplicity_laundered_as_train_forcing`
- `negative_evidence_missing`
- `competing_grammar_not_considered`
- `competing_outputs_not_rejected`

## 7. One-bug-vs-two-bugs decision
Decision: `D. mixed generator + assembler flaws`

Why this is the best-supported answer from the inspected traces:
1. **Generator weakness exists**
   - both families are emitted with trace-complete / forced-unique packets from very small family-level flags
   - composed family gets forced uniqueness from `all_components_train_supported=true`
   - MDL family gets train-grounded grammar status from `rules_from_train=true`
   - neither family emits the family-specific proof needed to justify forced uniqueness

2. **Assembler weakness exists**
   - the ledger accepts both families through the same generic `candidate_level_trace_grounding` path
   - it does not require family-specific proof once generic completeness fields are present
   - it therefore treats generic trace-complete wording as sufficient deservedness

3. **The two families are not identical in missing proof**
   - composed failure is about composition-level proof missing from component-level support
   - MDL failure is about grammar/rival/negative-evidence proof missing from compact grammar support

So the remaining hard stop is **not** one generic rival-style bug, and **not** one pure generator-only bug. It is a mixed generator+assembler problem with two distinct non-rival family manifestations.

## 8. Shared ledger weakness, if any
Shared ledger weakness: **yes**.

Observed shared weakness:
- once candidate fields satisfy generic completeness checks
- and no rival / ambiguity / explicit MDL-only flag blocks them
- the assembler emits `candidate_deserved` using a single generic trace:
  `candidate_level_trace_grounding`

That means the ledger currently lacks family-specific deservedness gates for at least:
- composition-as-a-unit proof
- explicit grammar rivalry / negative-evidence proof

In short:
- the ledger is over-trusting generic trace completeness
- it is not discriminating between `trace present` and `trace proves the right thing for this family`

## 9. Generator trace-grounding weakness, if any
Generator trace-grounding weakness: **yes**.

Observed generator weakness:
- composed family auto-derives strong proof wording from only `all_components_train_supported=true`
- MDL family auto-derives strong proof wording from only `rules_from_train=true`
- forced uniqueness then becomes mechanically available from those generic fields plus `ambiguity_check=clear`
- family-specific missing proof is never surfaced as missing

This is a truthfulness weakness, not a rival-boundary weakness:
- the generator is not hallucinating hidden test answers
- but it is overstating what the train evidence actually establishes for these two families

## 10. Risk to prior repairs
Potential regression risk exists if the next repair is done as a broad generic tightening without preserving the proven rival boundary behavior.

Must preserve explicitly:
- rival-context repair — preserve current unresolved-rival collapse to safe failure
- train-forced rival bypass blocking — preserve `train_forced_rival_bypass_blocked_count`
- safe-failure routing — do not convert current conservative safe failures into accidental hard accepts
- trace-grounding truthfulness — do not patch by inventing stronger trace text without real supporting structure
- expected-answer boundary — keep expected-answer use strictly post-ledger diagnostic only

Safe repair direction characteristics:
- add family-specific discrimination for composed and MDL cases
- keep rival-context checks earlier and unchanged
- do not weaken existing unresolved-rival gating
- do not backfill fake rival-elimination or fake uniqueness proof text

## 11. Recommended next repair lane
`REPAIR_ARC_COMPOSED_AND_MDL_DISCRIMINATION_SEPARATELY_V1`

Why this lane is recommended instead of a single generic assembler patch:
- composed and MDL families fail for different evidentiary reasons
- both share a ledger over-acceptance pattern, but the missing proof is not the same
- a single broad “trace-complete false positive gate” risks over-tightening unrelated families or regressing the rival repair
- separate family discrimination is more surgical and more aligned with the inspected traces
