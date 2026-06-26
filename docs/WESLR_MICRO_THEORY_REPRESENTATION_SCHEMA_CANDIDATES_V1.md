# WESLR MICRO-THEORY REPRESENTATION SCHEMA CANDIDATES V1

## Status
Design/report only. Bounded exploratory posture. No implementation, no executable schemas, no runtime solver work, no solver patching, no provider/model calls, no public ARC/Kaggle ingestion, no benchmark/public claims, no learned scorer implementation, no final-answer generation, no `.weslr` writes, and no push.

## 1. Purpose
This artifact defines candidate representation schemas for the Micro-Theory Solver / Temporary Language Inventor Solver.

Principle:
**Be conservative about external actions. Be ambitious about internal representations.**

The goal is not to force Micro-Theory Solver into human-readable symbolic rules only. The goal is to define several bounded internal representation families that can later be inspected, serialized, tested, compared, and used in mock traces without implementation yet.

## 2. Risk posture
`bounded_exploratory_normal`

Allowed here:
- strange internal forms
- private symbols
- non-human-readable but inspectable structures
- pressure fields
- causal maps
- contradiction maps
- role migration structures
- hybrid schemas
- representation mutation as a design idea only

Blocked here:
- implementation
- runtime execution
- provider/model calls
- public data ingestion
- learned scoring
- autonomous self-modification
- public claims
- behavior-pack promotion

## 3. Common fields required across candidates
Every schema candidate should expose or connect to:
- `schema_id`
- `representation_type`
- `scene_objects`
- `roles`
- `relations`
- `pressure_sources`
- `absences`
- `exceptions`
- `causal_claims`
- `incidental_features`
- `distractor_rejections`
- `candidate_transformations`
- `predicted_output_claim`
- `ambiguity_notes`
- `failure_mode`
- `boundedness_notes`
- `inspectability_notes`
- `comparison_notes`
- `synthetic_only`
- `non_claim_safe`

These are not executable requirements yet. They are design-level schema anchors to ensure comparability and later serialization.

## 4. Schema candidate 1 — Role Graph Schema
### One-line definition
A graph representation where scene objects are nodes and inferred roles/relations are typed edges or attached role labels.

### What it represents
- object identity independent of raw appearance
- role assignments such as anchor, source, target, witness, blocker, exception
- relation structure such as containment, adjacency, symmetry-reference, counterpart, dependency

### Example fields
- `schema_id: "micro_theory_role_graph_v1"`
- `representation_type: "role_graph"`
- `scene_objects: [{object_id, features, object_signature}]`
- `roles: [{object_id, role_name, confidence}]`
- `relations: [{src, relation_type, dst, polarity, notes}]`
- `candidate_transformations: [{target_object_id, action_family, rationale}]`

### What it is good at
- role detection
- relation-based target selection
- anchor/source/target/witness/blocker reasoning
- object identity independent of color/shape
- relational transformations

### What it is bad at
- diffuse pressure that is not object-local
- subtle absence pressure spread across a whole scene
- contradiction accumulation unless extended

### How it could overfit
- invent too many role labels
- assign brittle roles tied to one train pair
- reify appearance details as fake roles

### How it remains bounded
- limit node/edge types to finite declared families per trace
- cap invented role names per candidate theory
- require cross-example role reuse for promotion

### How it remains inspectable
- graph can be rendered as explicit nodes/edges
- role assignments and causal edges are individually reviewable

### How it remains serializable
- JSON-safe node/edge records
- no hidden latent-only structure requirement

### How it can be compared against rival schemas
- compare role stability across train pairs
- compare edge reuse, concept count, and unique output support

### How it could support safe failure
- fail when role assignments remain unstable or contradictory
- record unresolved target ambiguity as graph conflict

### Best-suited UNKNOWN ENGINE pressures
- role/color inversion
- role migration
- target-by-relation tasks
- object identity drift under stable role logic

## 5. Schema candidate 2 — Pressure Field Schema
### One-line definition
A field-like representation of where strangeness pressure is concentrated in the scene and why the current interpretation feels unresolved.

### What it represents
- changed-cell pressure
- suspicious unchanged regions
- broken symmetry pressure
- missing-member pressure
- blocked continuation pressure
- distractor attraction pressure
- unexplained emptiness pressure

### Example fields
- `schema_id: "micro_theory_pressure_field_v1"`
- `representation_type: "pressure_field"`
- `pressure_sources: [{region_or_object_ref, pressure_type, magnitude, rationale}]`
- `relations: [{pressure_source_id, dependency_type, other_ref}]`
- `exceptions: [{pressure_source_id, exception_reason}]`

### What it is good at
- identifying where explanation is demanded before rule invention
- reasoning about absences and suspicious non-changes
- detecting distractor bait and unresolved tension

### What it is bad at
- cleanly representing object-role logic by itself
- expressing fine-grained transformation sequences

### How it could overfit
- mark everything as high pressure
- confuse salience with causality
- create noisy pressure maps with weak discriminative value

### How it remains bounded
- finite pressure categories
- bounded magnitude scale
- bounded region/object references only

### How it remains inspectable
- field entries can be listed or visualized explicitly
- every pressure source requires a textual reason label

### How it remains serializable
- JSON-safe pressure-source rows
- optional matrix-like overlays expressed as bounded lists, not executable tensors

### How it can be compared against rival schemas
- compare explanatory tension reduction across train pairs
- compare whether pressure collapses cleanly after candidate grammar application

### How it could support safe failure
- fail when pressure remains diffuse after multiple candidate theories
- report unresolved pressure clusters rather than fake certainty

### Best-suited UNKNOWN ENGINE pressures
- broken repetition
- absence-only causal levels
- suspicious unchanged regions
- blocked continuation levels
- distractor primitive-bait levels

## 6. Schema candidate 3 — Absence / Exception Ledger Schema
### One-line definition
A ledger of what is missing, forbidden, anomalous, or pattern-violating, treated as first-class explanatory structure.

### What it represents
- missing twin
- missing member
- forbidden gap
- exception object
- contradiction source
- expected-but-absent marker

### Example fields
- `schema_id: "micro_theory_absence_exception_ledger_v1"`
- `representation_type: "absence_exception_ledger"`
- `absences: [{absence_type, expected_from_pattern, location_or_object_ref}]`
- `exceptions: [{exception_object_id, violated_pattern, explanatory_priority}]`
- `pressure_sources: [{source_type, linked_absence_or_exception}]`

### What it is good at
- negative evidence reasoning
- exception-as-key tasks
- forbidden-gap tasks
- contradiction and anomaly tracking

### What it is bad at
- whole-scene structural role systems by itself
- continuous relation modeling

### How it could overfit
- hallucinate expected missing structure
- convert ordinary variation into fake anomaly importance

### How it remains bounded
- ledger entries must point to explicit supporting pattern claims
- finite absence/exception categories per candidate schema

### How it remains inspectable
- each absence/exception is a named record with evidence and rationale

### How it remains serializable
- tabular record format
- explicit references instead of hidden implication chains

### How it can be compared against rival schemas
- compare anomaly coverage, false anomaly rate, and output disambiguation value

### How it could support safe failure
- fail when multiple anomaly interpretations remain equally live
- report unresolved exception ownership cleanly

### Best-suited UNKNOWN ENGINE pressures
- absence-only causal levels
- exception-as-key levels
- forbidden-action levels
- contradiction-resolution levels

## 7. Schema candidate 4 — Causal Map Schema
### One-line definition
A representation that separates causal features, incidental features, and support features while recording counterfactual dependencies.

### What it represents
- causal role versus visible appearance
- support features versus actual drivers
- interventions and counterfactual stability

### Example fields
- `schema_id: "micro_theory_causal_map_v1"`
- `representation_type: "causal_map"`
- `causal_claims: [{claim_id, cause_ref, effect_ref, condition_set}]`
- `incidental_features: [{feature_ref, why_noncausal}]`
- `relations: [{cause_ref, relation_type, effect_ref}]`
- `comparison_notes: [{counterfactual_probe, expected_stability}]`

### What it is good at
- separating causal from incidental features
- avoiding color/coordinate overdependence
- supporting counterfactual tests conceptually

### What it is bad at
- first-pass scene decomposition
- compact ambiguity handling without other structures

### How it could overfit
- declare causality too early
- dress up descriptive correlation as causal logic

### How it remains bounded
- each causal claim must name explicit scene references and conditions
- finite number of claims per candidate theory

### How it remains inspectable
- causal claims are explicit and challengeable
- counterfactual assumptions are surfaced, not hidden

### How it remains serializable
- structured claim records with references and notes

### How it can be compared against rival schemas
- compare counterfactual stability and incidental-feature pruning quality

### How it could support safe failure
- fail when causal claims remain underdetermined or clash across train pairs

### Best-suited UNKNOWN ENGINE pressures
- causal/incidental inversion
- role/color inversion
- distractor rejection
- support-feature misidentification

## 8. Schema candidate 5 — Competing Grammar Arena Schema
### One-line definition
A meta-schema that represents several rival micro-theories simultaneously and records why each survives or fails.

### What it represents
- multiple live interpretations
- ambiguity handling
- rival grammar comparison
- safe failure when theories disagree

### Example fields
- `schema_id: "micro_theory_competing_grammar_arena_v1"`
- `representation_type: "competing_grammar_arena"`
- `candidate_transformations: [{grammar_id, predicted_output_claim, confidence_band}]`
- `ambiguity_notes: [{grammar_a, grammar_b, disagreement_type}]`
- `comparison_notes: [{grammar_id, train_coverage, exception_burden, compression_notes}]`
- `failure_mode: "rival_grammars_unresolved"`

### What it is good at
- preserving ambiguity honestly
- comparing rival explanations
- supporting safe failure and ranked candidates

### What it is bad at
- producing first-order object analysis by itself
- representing scene structure without nested schemas

### How it could overfit
- keep too many near-duplicate grammars alive
- reward stylistically elegant but weak theories

### How it remains bounded
- bounded candidate count
- bounded evidence fields per grammar
- mandatory elimination criteria

### How it remains inspectable
- every surviving grammar exposes its claims and rejection reasons

### How it remains serializable
- list of bounded candidate packets
- explicit conflict and comparison records

### How it can be compared against rival schemas
- it is itself the comparison layer; compare clarity of elimination and ambiguity reduction

### How it could support safe failure
- directly supports abstention, ranked candidates, or unresolved rivalry reports

### Best-suited UNKNOWN ENGINE pressures
- grammar ambiguity levels
- contradiction-resolution levels
- multi-explanation tasks

## 9. Schema candidate 6 — Compression / Inevitability Trace Schema
### One-line definition
A trace showing how a candidate grammar makes train outputs feel forced rather than merely compatible.

### What it represents
- coverage
- cross-example role stability
- output uniqueness
- distractor rejection
- exception burden
- concept bloat
- arbitrary constants

### Example fields
- `schema_id: "micro_theory_compression_inevitability_trace_v1"`
- `representation_type: "compression_inevitability_trace"`
- `comparison_notes: [{criterion, value, rationale}]`
- `candidate_transformations: [{step_id, why_forced}]`
- `failure_mode: "low_inevitability"`

### What it is good at
- comparing explanatory compression
- exposing exception burden and concept count
- tracking why one grammar feels more inevitable than another

### What it is bad at
- raw scene modeling
- first-order role discovery without support from other schemas

### How it could overfit
- turn into a decorative score sheet
- masquerade rhetorical confidence as actual inevitability

### How it remains bounded
- criterion list is finite and explicit
- conceptual only, no learned scorer allowed

### How it remains inspectable
- each criterion must point to concrete supporting trace notes

### How it remains serializable
- bounded checklist/trace records
- explicit criterion-value-reason triples

### How it can be compared against rival schemas
- compare compression burden, ambiguity reduction, and output uniqueness support

### How it could support safe failure
- fail when inevitability remains weak even if superficial train fit exists

### Best-suited UNKNOWN ENGINE pressures
- compression traps
- distractor rejection
- false-regularity tasks
- rival near-fit grammars

## 10. Schema candidate 7 — Hybrid Micro-Theory Packet Schema
### One-line definition
A combined packet that can hold multiple schema families together for tasks that need role, pressure, absence, causal, and rivalry structure at once.

### What it represents
- mixed tasks where no single schema family is sufficient
- role + pressure + absence + causal reasoning together
- later mock traces and cross-schema comparison

### Example fields
- `schema_id: "micro_theory_hybrid_packet_v1"`
- `representation_type: "hybrid_micro_theory_packet"`
- `scene_objects: [...]`
- `roles: [...]`
- `relations: [...]`
- `pressure_sources: [...]`
- `absences: [...]`
- `exceptions: [...]`
- `causal_claims: [...]`
- `distractor_rejections: [...]`
- `candidate_transformations: [...]`
- `predicted_output_claim: {...}`
- `ambiguity_notes: [...]`

### What it is good at
- integrated mixed-pressure tasks
- mock-trace readiness
- later candidate-to-candidate comparisons

### What it is bad at
- can become bloated if unconstrained
- risks becoming a junk drawer packet

### How it could overfit
- include every representational idea whether needed or not
- hide weak reasoning behind packet completeness

### How it remains bounded
- nested substructures must each declare why they are needed
- forbid unused sub-packets
- cap candidate concept count and subpacket count

### How it remains inspectable
- sub-packets remain separately inspectable
- cross-links are explicit

### How it remains serializable
- JSON-safe nested records
- explicit schema family tags for each subpacket

### How it can be compared against rival schemas
- compare whether integration improves ambiguity reduction or merely increases bloat

### How it could support safe failure
- fail when combined packet still cannot unify scene pressures into one bounded theory

### Best-suited UNKNOWN ENGINE pressures
- multi-pressure frontier probes
- hybrid role/absence/contradiction tasks
- scenes where single-family schemas underfit

## 11. Schema comparison criteria
Candidate schemas should be compared by:
- train coverage
- cross-example role stability
- concept count
- exception burden
- output uniqueness
- negative-evidence handling
- distractor rejection
- counterfactual stability
- compression pressure
- ambiguity reduction
- safe-failure clarity

These criteria remain conceptual-only in this artifact. They are not an implemented scorer.

## 12. What not to do
Do not:
- implement runtime solver
- create learned scorer
- create final-answer generator
- patch existing solver
- add primitives
- implement depth-3
- use public ARC/Kaggle data
- make benchmark claims
- make public claims
- claim AGI/sentience/consciousness
- make the private grammar uninspectable
- let “strange” become “unbounded”

## 13. Bounded exploratory allowance
Allowed:
- strange internal forms
- private symbols
- non-human-readable but inspectable structures
- pressure fields
- causal maps
- contradiction maps
- role migration structures
- hybrid schemas
- representation mutation as a design idea only

Blocked:
- implementation
- runtime execution
- provider/model calls
- public data ingestion
- learned scoring
- autonomous self-modification
- public claims
- behavior-pack promotion

## 14. Compatibility note
These schema candidates should remain compatible with a future shared Cognitive Gym–style protocol direction rather than becoming a disconnected private reporting philosophy. UNKNOWN ENGINE-specific metadata is allowed, but representation packets should stay migratable into a broader shared protocol later if needed. Source: `memory/2026-05-24-unknown-engine.md#L534-L589`

## 15. Recommended next safe follow-up
Recommended next safe follow-up:
`DESIGN_MICRO_THEORY_MOCK_TRACE_FORMAT_V1`

Reason:
The schema candidates are now clear enough that the next bounded exploratory artifact should define how a mock interpretation trace records one or more schema candidates against synthetic UNKNOWN ENGINE levels without implementing runtime behavior.

## 16. Final note
The right discipline is not to make Micro-Theory Solver ordinary. The right discipline is to let it stay strange while making every candidate form bounded, inspectable, serializable, testable, comparable, and non-executable at this stage.
