# WESLR ARC CANDIDATE OUTPUT AND TRACE SURFACE FOR REAL SCORING DESIGN V1

## 1. Executive verdict
`arc_candidate_output_and_trace_surface_for_real_scoring_design_complete_with_notes`

## 2. Problem statement
Current replay state:
- RNG/hash scoring is removed
- ledger/gating independence from exact/wrong scoring is confirmed
- all 8 V5 groups are currently `unscorable_due_to_missing_candidate_output`
- expected/scoring outputs exist
- live candidate output surface is missing
- composed-transform trace surface is too thin for later alternative-enumeration diagnosis

The design goal is to add the minimum local candidate-output and trace surface needed so replay can perform **real post-ledger deterministic scoring** without leaking expected answers upstream.

Key design constraint:
- candidate output must be generated from candidate construction only
- expected/scoring output must be loaded only after ledger decision
- no generator or assembler deservedness logic may depend on scoring

## 3. Candidate output surface schema
### A. Proposed schema object
Add a replay-safe candidate-output packet on each candidate descriptor:

`candidate_output_surface`
- `present: bool`
- `output_type: str`
- `normalized_output: object | null`
- `raw_output_reference: object | null`
- `output_provenance: str`
- `serialization_status: str`
- `comparable_to_expected: bool`
- `incomparable_reason_code: str`
- `schema_version: str`

### B. Field meanings
- `present`
  - whether the candidate actually proposes an output surface
- `output_type`
  - one of:
    - `grid_int_matrix`
    - `grid_symbolic_matrix`
    - `object_graph_projection`
    - `descriptor_only`
    - `grammar_emitted_grid`
    - `intermediate_only`
    - `missing`
- `normalized_output`
  - canonical deterministic structure used for exact comparison
  - for first implementation lane, target only `grid_int_matrix`
- `raw_output_reference`
  - local candidate-side raw structure before normalization
  - must not contain expected-answer data
- `output_provenance`
  - one of:
    - `generator_emitted_final_output`
    - `generator_emitted_projection`
    - `candidate_override`
    - `replay_preserved_candidate_output`
    - `missing`
- `serialization_status`
  - `json_safe`
  - `non_json_safe_rejected`
  - `missing`
- `comparable_to_expected`
  - true only when the scorer can structurally compare `normalized_output` to `synthetic_expected_answer_for_scoring_only`
- `incomparable_reason_code`
  - one of:
    - `none`
    - `candidate_output_missing`
    - `expected_output_missing`
    - `output_type_not_comparable`
    - `ambiguous_output_surface`
    - `non_json_safe_output`
    - `normalization_failed`
- `schema_version`
  - e.g. `arc_candidate_output_surface_v1`

### C. Minimal first-implementation normalization rule
For initial scoring lane, support only:
- rectangular nested integer lists
- exact row/column/value equality
- no fuzzy matching
- no descriptor-only scoring

### D. Scoring-safe serialization rule
Candidate output surface must be:
- JSON-safe
- detached from expected output
- reproducible from candidate state only
- serializable in replay per-task records

## 4. Trace surface schema
### A. Core trace packet
Add a replay-preserved `candidate_trace_surface` packet per candidate:
- `construction_mode: str`
- `construction_trace_complete: bool`
- `forced_uniqueness_trace_present: bool`
- `train_evidence_grounded: bool`
- `missing_required_trace_fields: list[str]`
- `unresolved_rivals: list[str]`
- `candidate_trace_provenance: str`
- `trace_schema_version: str`
- `candidate_output_surface_present: bool`
- `candidate_output_surface_type: str`

### B. Trace preservation rule
Replay must preserve the trace packet:
- from generator output to candidate descriptor
- from candidate descriptor to replay per-task record
- without inserting expected/scoring fields into the packet

### C. Diagnostic-compatibility rule
Trace must preserve enough family-specific detail for:
- replay scoring provenance
- composed alternative enumeration
- MDL/grammar diagnosis
- missing-proof classification

## 5. Composed-transform trace requirements
For `composed_transform_candidate`, add a structured composed trace surface:

`composed_trace_surface`
- `ordered_component_list: list[str]`
- `component_execution_order: list[str]`
- `component_records: list[object]`
- `intermediate_outputs_after_each_component: list[object]`
- `component_support_map: dict[str, bool]`
- `component_only_support: bool`
- `whole_composition_support: bool`
- `interaction_assumptions: list[str]`
- `alternative_order_surfaces: list[object]`
- `alternative_subset_surfaces: list[object]`
- `partial_transform_surfaces: list[object]`
- `full_composition_alternatives: list[object]`
- `sufficient_for_alternative_enumeration: bool`

### Required semantics
- `ordered_component_list`
  - named intended transform chain in order
- `component_execution_order`
  - actual order used to produce candidate output
- `component_records`
  - per-component operation name, input shape, output shape, support status
- `intermediate_outputs_after_each_component`
  - local-only intermediate candidate-side outputs; no expected-answer data
- `component_support_map`
  - whether each component is train-supported as a unit
- `component_only_support`
  - true when only individual components are supported
- `whole_composition_support`
  - true only when the composition-as-a-unit is proven, not merely componentwise
- `interaction_assumptions`
  - assumptions about component interaction/order dependence
- `alternative_*_surfaces`
  - locally derivable rival order/subset/partial-transform packets for diagnostic use
- `sufficient_for_alternative_enumeration`
  - true only when enough structure exists for later composed enumeration logic to work without report reconstruction guesswork

### Design note
First implementation does not need full alternative enumeration.
It does need enough structured component/output state so enumeration and scoring stop depending on generic chain wording.

## 6. MDL / explicit-grammar trace requirements
For `explicit_grammar_candidate`, add a structured grammar trace surface:

`mdl_trace_surface`
- `accepted_grammar_id: str`
- `accepted_grammar_record: object`
- `grammar_output_surface: object | null`
- `grammar_train_support_evidence: list[str]`
- `simplicity_primary_evidence: bool`
- `negative_evidence_present: bool`
- `competing_grammar_records: list[object]`
- `train_forced_grammar: bool`
- `compact_but_not_forced: bool`
- `sufficient_for_competing_grammar_diagnosis: bool`

### Required semantics
- `accepted_grammar_record`
  - grammar rule identity plus locally generated output summary
- `grammar_output_surface`
  - candidate-side output proposed by accepted grammar
- `grammar_train_support_evidence`
  - train-derived reasons only
- `simplicity_primary_evidence`
  - true when compactness/MDL is the main support signal
- `negative_evidence_present`
  - whether explicit rival-blocking/negative evidence exists
- `competing_grammar_records`
  - locally derivable rival grammar packets when available
- `train_forced_grammar`
  - true only when train evidence uniquely forces the grammar
- `compact_but_not_forced`
  - true when grammar is concise but not uniquely supported
- `sufficient_for_competing_grammar_diagnosis`
  - whether the trace is rich enough for later MDL false-positive diagnosis

## 7. Post-ledger scorer design
### A. Invocation boundary
Scorer runs only after replay sets `ledger_decision`.
Scorer inputs:
- candidate descriptor(s) with `candidate_output_surface`
- replay task `synthetic_expected_answer_for_scoring_only`
- no generator-only internals beyond preserved candidate output/trace packet

### B. Scorer comparison contract
- exact deterministic structural equality only
- no fuzzy matching
- no heuristic equivalence
- no RNG fallback
- no RNG tie-breaker
- no candidate-selection influence from scoring

### C. Scoring outcome statuses
Allowed statuses:
- `deserved_exact`
- `deserved_but_wrong`
- `undeserved_exact`
- `scored_candidate_not_deserved_non_exact`
- `unscorable_due_to_missing_candidate_output`
- `unscorable_due_to_missing_expected_output`
- `unscorable_due_to_incomparable_output_type`
- `unscorable_due_to_ambiguous_output_surface`
- `not_scored_candidate_not_generated`

### D. First-implementation comparison rule
If:
- `candidate_output_surface.present == true`
- `output_type == grid_int_matrix`
- `comparable_to_expected == true`
- expected output exists
then:
- normalize both to canonical nested integer lists
- compare exact equality

Else:
- emit explicit unscorable reason code
- do not convert missing/incomparable output into wrongness

### E. Multi-candidate replay rule
Replay scoring must not perform candidate selection.
Scoring evaluates only the candidate already accepted by ledger context.
If replay task preserves multiple candidates and no accepted-output identity exists, emit:
- `unscorable_due_to_ambiguous_output_surface`

## 8. Boundary and leakage prevention
### A. Data-flow boundary
Strict pipeline:
1. generator builds candidate + trace + candidate output surface
2. assembler evaluates deservedness without expected/scoring fields
3. replay records ledger decision
4. scorer loads expected/scoring output after ledger decision only
5. scorer compares preserved normalized candidate output vs expected output

### B. Forbidden upstream field names
Generator and assembler must reject or ignore any upstream payload containing:
- `synthetic_expected_answer_for_scoring_only`
- `expected_output`
- `expected_answer`
- `post_ledger_scoring_status`
- `post_ledger_scoring_result`
- `deserved_exact_result`
- `deserved_but_wrong_result`
- `scoring_result`
- `scoring_label`

### C. Provenance boundary record
Per-task scoring provenance should add:
- `expected_output_load_stage: post_ledger_only`
- `expected_output_loaded_after_ledger_decision: true|false`
- `candidate_output_surface_source: ...`

### D. Required tests
Add tests that fail if:
- expected/scoring fields appear in generator input and influence candidate generation
- expected/scoring fields appear in assembler input and influence deservedness
- scorer runs before ledger decision
- candidate output normalization reads expected output
- composed/MDL trace surfaces are replaced by generic-only wording when structured fields are expected

### E. Minimal-fit principle
No broad module split required.
This design can fit current files by extending:
- generator candidate descriptor payloads
- replay per-task preservation
- scorer normalization helper(s)

## 9. All-8-groups output/trace coverage table
| group | current output surface available | minimum needed output surface | minimum needed trace surface | expected scoring comparison type | likely implementation target | expected-answer leakage risk | first implementation lane scorable? |
|---|---|---|---|---|---|---|---|
| `v4_rival_grammar_replay_6` | no | accepted candidate final grid output | existing train/rival trace + output provenance | exact grid equality | generator + replay preservation | low | yes |
| `v4_beautiful_wrong_rule_replay_6` | no | final grid output for accepted transform candidate | existing transform trace + output provenance | exact grid equality | generator + replay preservation | low | yes |
| `v4_composed_transform_replay_6` | no | final composed output grid | structured composed trace surface with components/intermediates/support | exact grid equality | generator + replay + composed trace packet | medium | yes, if component/output emission is implemented together |
| `v4_negative_evidence_replay_6` | no | final candidate grid output | negative-evidence-related trace flags + output provenance | exact grid equality | generator + replay preservation | low | yes |
| `v4_helper_trap_replay_6` | no | final candidate grid output | helper-trap-safe trace + output provenance | exact grid equality | generator + replay preservation | low | yes |
| `object_graph_correspondence_6` | no | projected final grid derived from correspondence candidate | object correspondence trace + projection provenance | exact grid equality | generator emits projection output | medium | yes, if projection is made explicit |
| `invariant_symmetry_ambiguity_6` | no | final invariant-preserving candidate grid or explicit ambiguous-output packet | invariant/symmetry trace + ambiguity packet | exact grid equality or ambiguous-output unscorable | generator + replay preservation | medium | likely yes for clear cases; ambiguous cases may remain unscorable by design |
| `mdl_simplicity_trap_6` | no | grammar-emitted final grid output | MDL grammar trace surface with accepted grammar and rival metadata | exact grid equality | generator + replay + grammar output packet | medium | yes |

## 10. Implementation sequencing
### Stage 1 — schema/helpers only
Recommended lane:
`IMPLEMENT_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_SCHEMA_HELPERS_V1`

Scope:
- define candidate output surface helper schema
- define core trace surface helper schema
- define composed trace surface helper schema
- define MDL trace surface helper schema
- add JSON-safe normalization helpers only

Why first:
- smallest safe step
- lets tests lock the boundary before behavior wiring

### Stage 2 — generator emits candidate output descriptors
- add `candidate_output_surface` for groups that can emit deterministic final grids
- add `candidate_trace_surface` base packet
- no expected-output comparison yet

### Stage 3 — replay preserves candidate output/trace records
- preserve per-task candidate output surface
- preserve structured trace packets in replay records
- preserve provenance fields

### Stage 4 — scorer compares normalized candidate output vs expected output post-ledger
- enable real exact/wrong scoring for scorable groups only
- leave others explicitly unscorable with precise reason codes

### Stage 5 — composed trace surface preservation
- add structured composed component/intermediate/output surface
- enable later composed enumeration diagnosis without report reconstruction

### Stage 6 — MDL grammar output surface preservation
- add accepted grammar output packet and rival grammar trace packet
- enable real MDL scoring and later diagnosis from preserved artifacts

### Stage 7 — focused replay scoring run over 8 groups
- rerun only after schema, preservation, and scorer are in place
- then exact/wrong conclusions become newly trustworthy

## 11. Prior conclusion handling
- old exact/wrong conclusions remain downgraded
- new exact/wrong conclusions can be trusted only after real candidate-output scoring exists and is actually run
- old ledger/safety conclusions remain usable because ledger/gating independence was confirmed
- composed and MDL diagnosis should continue to treat pre-output-surface exact/wrong labels as historical stress signals, not correctness proof

## 12. Safety boundaries
Confirmed design boundaries:
- local only
- design/report only
- no push
- no public ARC/Kaggle data
- no hidden test output use
- no expected-answer use during generation or deservedness
- no generator deservedness repair
- no assembler deservedness repair
- no emitter implementation
- no runtime solver wiring
- no ChatResponder changes
- no final-answer emission
- no learned scorer implementation
- no `.weslr`
- no external calls
- protected files unchanged

## 13. Recommended next safe local follow-up
`IMPLEMENT_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_SCHEMA_HELPERS_V1`

Why:
- schema/helper work should happen first
- it reduces leakage risk before implementation wiring
- it creates a stable contract for generator emission, replay preservation, scorer comparison, composed trace preservation, and MDL grammar output preservation
