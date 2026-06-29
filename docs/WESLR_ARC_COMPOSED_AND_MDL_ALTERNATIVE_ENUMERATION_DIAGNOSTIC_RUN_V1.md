# WESLR ARC COMPOSED AND MDL ALTERNATIVE ENUMERATION DIAGNOSTIC RUN V1

## 1. Executive verdict
`arc_composed_and_mdl_alternative_enumeration_diagnostic_run_needs_more_evidence`

## 2. Run scope
This run applied the reviewed diagnostic module locally to a bounded reconstruction of the 12 target cases from:
- `v4_composed_transform_replay_6` (6 cases)
- `mdl_simplicity_trap_6` (6 cases)

Important run discipline:
- post-ledger labels from prior reports were carried only as reporting metadata
- expected answers were not used in enumeration, comparison, rejection, classification, or deservedness
- no replay rerun was performed
- no generator / assembler / runtime / emitter behavior was changed

## 3. Coverage caveat
This diagnostic fully implements composed-transform and MDL / explicit-grammar only.
It does **not** audit-clean:
- object graph
- invariant / symmetry
- negative evidence as a standalone future family
- helper trap
- relation-first rewrite

Those future families remain fail-closed unsupported paths / labels only.
Any future-family `insufficient_alternative_search` result must **not** be interpreted as proof that the family is safe.

This run is also bounded-local, not globally exhaustive over all ARC hypotheses.

## 4. Composed-transform diagnostic results
Family interpretation:
- composed cases were supported mainly by missing-proof / insufficient-search signals
- this run did **not** find actual alternative composition records
- the prior attribution artifacts still indicate likely component-forcedness laundering, but the current reconstructed trace surface was too thin to materialize explicit component records inside the diagnostic
- this is not strong enough yet for a composed-specific discrimination repair

| task_id | record | family | mode | component list present | alternatives enumerated | alt order count | subset count | partial count | interaction count | alt full count | component-only explanation | whole composition forced | component support only | alternatives identified | alternatives rejected by train evidence | alternatives not rejected count | direct counterexample | missing-proof-only | insufficient search | laundering risk | laundering type | safe failure required | recommended repair family | post-ledger label |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|---|
| v5_replay_v4_composed_transform_replay_6_13 | yes | composed_transform | composed_transform_candidate | no | no | 0 | 0 | 0 | 0 | 0 | no | no | no | no | no | 0 | no | yes | yes | no |  | yes | composed_transform_forcedness_audit | exact |
| v5_replay_v4_composed_transform_replay_6_14 | yes | composed_transform | composed_transform_candidate | no | no | 0 | 0 | 0 | 0 | 0 | no | no | no | no | no | 0 | no | yes | yes | no |  | yes | composed_transform_forcedness_audit | deserved_but_wrong |
| v5_replay_v4_composed_transform_replay_6_15 | yes | composed_transform | composed_transform_candidate | no | no | 0 | 0 | 0 | 0 | 0 | no | no | no | no | no | 0 | no | yes | yes | no |  | yes | composed_transform_forcedness_audit | deserved_but_wrong |
| v5_replay_v4_composed_transform_replay_6_16 | yes | composed_transform | composed_transform_candidate | no | no | 0 | 0 | 0 | 0 | 0 | no | no | no | no | no | 0 | no | yes | yes | no |  | yes | composed_transform_forcedness_audit | deserved_but_wrong |
| v5_replay_v4_composed_transform_replay_6_17 | yes | composed_transform | composed_transform_candidate | no | no | 0 | 0 | 0 | 0 | 0 | no | no | no | no | no | 0 | no | yes | yes | no |  | yes | composed_transform_forcedness_audit | deserved_but_wrong |
| v5_replay_v4_composed_transform_replay_6_18 | yes | composed_transform | composed_transform_candidate | no | no | 0 | 0 | 0 | 0 | 0 | no | no | no | no | no | 0 | no | yes | yes | no |  | yes | composed_transform_forcedness_audit | exact |

## 5. MDL / explicit-grammar diagnostic results
Family interpretation:
- MDL cases were also supported mainly by missing-proof / insufficient-search signals
- this run did **not** find actual competing grammar records
- simplicity **was** repeatedly laundered as train forcing in the reconstructed local MDL surface
- despite that signal, the current bounded-local run is still too thin to support a confident MDL-specific discrimination repair, because explicit competing grammars / outputs were not found

| task_id | record | family | mode | accepted grammar info present | competing grammars enumerated | simpler count | more-complex count | same-train-different-test-output count | partial-train-fit count | compact-but-not-forced count | train-forced grammar count | competing outputs identified | competing outputs rejected | negative evidence present | grammar forced by train | simplicity primary evidence | direct counterexample | missing-proof-only | insufficient search | laundering risk | laundering type | safe failure required | recommended repair family | post-ledger label |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|---|
| v5_replay_mdl_simplicity_trap_6_43 | yes | mdl_trap | explicit_grammar_candidate | yes | no | 0 | 0 | 0 | 0 | 0 | 0 | no | no | no | no | yes | no | yes | yes | yes | simplicity_laundered_as_train_forcing | yes | mdl_forcedness_audit | deserved_but_wrong |
| v5_replay_mdl_simplicity_trap_6_44 | yes | mdl_trap | explicit_grammar_candidate | yes | no | 0 | 0 | 0 | 0 | 0 | 0 | no | no | no | no | yes | no | yes | yes | yes | simplicity_laundered_as_train_forcing | yes | mdl_forcedness_audit | deserved_but_wrong |
| v5_replay_mdl_simplicity_trap_6_45 | yes | mdl_trap | explicit_grammar_candidate | yes | no | 0 | 0 | 0 | 0 | 0 | 0 | no | no | no | no | yes | no | yes | yes | yes | simplicity_laundered_as_train_forcing | yes | mdl_forcedness_audit | exact |
| v5_replay_mdl_simplicity_trap_6_46 | yes | mdl_trap | explicit_grammar_candidate | yes | no | 0 | 0 | 0 | 0 | 0 | 0 | no | no | no | no | yes | no | yes | yes | yes | simplicity_laundered_as_train_forcing | yes | mdl_forcedness_audit | exact |
| v5_replay_mdl_simplicity_trap_6_47 | yes | mdl_trap | explicit_grammar_candidate | yes | no | 0 | 0 | 0 | 0 | 0 | 0 | no | no | no | no | yes | no | yes | yes | yes | simplicity_laundered_as_train_forcing | yes | mdl_forcedness_audit | exact |
| v5_replay_mdl_simplicity_trap_6_48 | yes | mdl_trap | explicit_grammar_candidate | yes | no | 0 | 0 | 0 | 0 | 0 | 0 | no | no | no | no | yes | no | yes | yes | yes | simplicity_laundered_as_train_forcing | yes | mdl_forcedness_audit | exact |

## 6. Per-known-bad-case comparison
Stable known-bad cases available from local reports:
- composed: `14`, `15`, `16`, `17`
- MDL: `43`, `44`

MDL discrepancy note:
- the split diagnosis marks `43` and `44` as `deserved_but_wrong`
- the later attribution report marks `44`, `45`, and `46` as wrong
- the prior V5 run report confirms there were 3 MDL deserved-but-wrong cases, but it does not stably resolve the third task id here
- therefore the third MDL false-positive id could **not** be stably identified from current local artifacts alone

| task_id | family | previous label | record | explicit alternative/rival identified | explicit competing output identified | direct counterexample | missing-proof-only | insufficient search | laundering risk | laundering type | safe failure required | repair implication |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| v5_replay_v4_composed_transform_replay_6_14 | composed_transform | deserved_but_wrong | yes | no | no | no | yes | yes | no |  | yes | cannot claim specific rival rejection; proof-requirement / diagnostic-expansion path only |
| v5_replay_v4_composed_transform_replay_6_15 | composed_transform | deserved_but_wrong | yes | no | no | no | yes | yes | no |  | yes | cannot claim specific rival rejection; proof-requirement / diagnostic-expansion path only |
| v5_replay_v4_composed_transform_replay_6_16 | composed_transform | deserved_but_wrong | yes | no | no | no | yes | yes | no |  | yes | cannot claim specific rival rejection; proof-requirement / diagnostic-expansion path only |
| v5_replay_v4_composed_transform_replay_6_17 | composed_transform | deserved_but_wrong | yes | no | no | no | yes | yes | no |  | yes | cannot claim specific rival rejection; proof-requirement / diagnostic-expansion path only |
| v5_replay_mdl_simplicity_trap_6_43 | mdl_trap | deserved_but_wrong | yes | no | no | no | yes | yes | yes | simplicity_laundered_as_train_forcing | yes | explicit simplicity trap signal exists, but rival search remains too thin for discrimination repair |
| v5_replay_mdl_simplicity_trap_6_44 | mdl_trap | deserved_but_wrong | yes | no | no | no | yes | yes | yes | simplicity_laundered_as_train_forcing | yes | explicit simplicity trap signal exists, but rival search remains too thin for discrimination repair |

Interpretation of insufficient search:
- `insufficient_alternative_search` on these known false positives means the current bounded-local diagnostic is too thin for the case
- it does **not** mean the candidate is safe
- it does **not** mean no rival exists
- it means a repair must not claim specific alternative/rival rejection for the case

## 7. Direct evidence vs missing-proof summary
- total diagnostic records: 12
- composed diagnostic records: 6
- MDL diagnostic records: 6
- actual alternative compositions identified count: 0
- actual competing grammars identified count: 0
- direct counterexample found count: 0
- missing-proof-only count: 12
- insufficient alternative search count: 12
- alternative rejection proven count: 0
- alternative rejection missing count: 12
- competing output identified count: 0
- competing output rejected count: 0

## 8. Known-bad directness aggregate
Using the 6 stable known-bad ids above:
- known-bad cases inspected count: 6
- known-bad cases with explicit alternatives/rivals count: 0
- known-bad cases with direct counterexamples count: 0
- known-bad cases missing-proof-only count: 6
- known-bad cases insufficient-search count: 6
- composed known-bad direct-evidence count: 0
- composed known-bad missing-proof-only count: 4
- composed known-bad insufficient-search count: 4
- MDL known-bad direct-evidence count: 0
- MDL known-bad missing-proof-only count: 2
- MDL known-bad insufficient-search count: 2

## 9. Forcedness-laundering summary
- component forcedness laundered as composition forcedness count: 0 in the bounded reconstructed run
- simplicity laundered as train forcing count: 6
- unsupported future-family fail-closed count: 0 in this run
- all-family audit overclaim appeared: no

Important note:
- prior attribution artifacts still point to likely component-forcedness laundering in the wrong composed family
- the current bounded-local run did not emit that label because the reconstructed local traces lacked explicit component lists / unit-level composition fields

## 10. Expected-answer boundary confirmation
Confirmed:
- expected/scoring-only fields were not used in enumeration, comparison, rejection, classification, or deservedness
- post-ledger exact/wrong labels were carried as reporting metadata only

## 11. Diagnostic-only boundary confirmation
Confirmed:
- local-only run
- no replay rerun
- no generator repair
- no assembler repair
- no replay-decision mutation
- no emitter implementation
- no runtime solver wiring
- no ChatResponder changes
- no final-answer emission
- no learned scorer implementation
- no `.weslr`
- no external calls
- protected files unchanged

## 12. Repair readiness decision
`DESIGN_ARC_ALTERNATIVE_ENUMERATION_DIAGNOSTIC_EXPANSION_V1`

Why:
- most stable known-bad cases are still `missing_proof_only`
- all stable known-bad cases are still `insufficient_alternative_search`
- no explicit alternative compositions were found
- no explicit competing grammars were found
- no direct counterexamples were found
- the current bounded-local diagnostic is informative, but still too thin to safely ground a discrimination repair claim around explicit rejected/unrejected rivals

## 13. Recommended next safe local follow-up
`DESIGN_ARC_ALTERNATIVE_ENUMERATION_DIAGNOSTIC_EXPANSION_V1`
