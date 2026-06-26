# WESLR MICRO-THEORY MOCK TRACE FORMAT V1

## Status
Design/report only. Bounded exploratory posture. No implementation, no executable schemas, no runtime solver work, no solver patching, no provider/model calls, no public ARC/Kaggle ingestion, no benchmark/public claims, no learned scorer implementation, no final-answer generation, no `.weslr` writes, and no push.

## 1. One-line definition
A design-only record format for showing how a Micro-Theory Solver interprets a synthetic UNKNOWN ENGINE level through pressure detection, temporary representation construction, competing micro-theories, inevitability checks, and safe prediction or safe failure.

## 2. Trace purpose
This trace format is not a solver and not a proof of performance.

It is a bounded design artifact for making interpretation attempts visible and comparable before implementation. Its purpose is to show whether a temporary language actually reduces strangeness across train examples, or merely produces a plausible narrative.

The trace should make a synthetic interpretation attempt:
- inspectable
- serializable
- comparable
- bounded
- testable
- compatible with a future shared Cognitive Gym-style protocol direction

## 3. Trace lifecycle
A mock trace should move through these stages:
1. trace metadata
2. level reference
3. scene decomposition
4. initial strangeness / pressure map
5. candidate representation selection
6. temporary vocabulary / structure creation
7. competing micro-theory construction
8. train-pair interpretation
9. cross-example compression
10. counterfactual / intervention notes
11. inevitability assessment
12. ambiguity / rival grammar comparison
13. predicted-output claim or safe-failure claim
14. anti-overfit notes
15. boundary flags

This lifecycle mirrors the intended Micro-Theory transition:
`strange scene → pressure detection → temporary representation → competing micro-theories → inevitability test → predicted output or safe failure`

## 4. Required trace fields
The trace format should include fields such as:
- `trace_id`
- `trace_version`
- `synthetic_level_id`
- `source_protocol`
- `cognitive_gym_compatible`
- `synthetic_only`
- `non_claim_safe`
- `representation_forms_used`
- `scene_decomposition`
- `pressure_sources`
- `absences_detected`
- `exceptions_detected`
- `candidate_roles`
- `candidate_relations`
- `causal_claims`
- `incidental_features`
- `distractor_rejections`
- `temporary_vocabulary`
- `micro_theory_candidates`
- `grammar_arena`
- `train_pair_explanations`
- `cross_example_invariants`
- `counterfactual_checks`
- `inevitability_assessment`
- `ambiguity_notes`
- `safe_failure_mode`
- `predicted_output_claim`
- `anti_overfit_notes`
- `comparison_summary`
- `boundedness_notes`
- `inspectability_notes`

These are design-level fields. They are not an implementation commitment yet.

## 5. Representation form compatibility
The trace format should be able to hold or reference these representation families:
- Role Graph
- Pressure Field
- Absence / Exception Ledger
- Causal Map
- Competing Grammar Arena
- Compression / Inevitability Trace
- Hybrid Micro-Theory Packet

The trace should not force all tasks into one representation. It should allow multiple representation forms to coexist in one trace when the level demands mixed reasoning.

Suggested compatibility record:
- `representation_forms_used: [{schema_id, representation_type, why_selected, boundedness_notes}]`

This allows a trace to say, for example, that a role graph handled object targeting while an absence ledger handled a missing-member anomaly and a causal map handled counterfactual pruning.

## 6. Grammar arena format
Rival micro-theories should be represented explicitly.

Each candidate should include:
- `candidate_id`
- `temporary_language_summary`
- `representation_forms`
- `role_assignments`
- `causal_claims`
- `transformation_claims`
- `absences_explained`
- `exceptions_explained`
- `distractors_rejected`
- `train_coverage`
- `cross_example_role_stability`
- `output_uniqueness`
- `exception_burden`
- `concept_count`
- `compression_notes`
- `counterfactual_stability`
- `predicted_output_claim`
- `ambiguity_notes`
- `failure_notes`

The grammar arena should remain inspectable. Every surviving candidate must reveal why it still survives and every rejected candidate should carry a small rejection reason trail.

## 7. Inevitability assessment format
This remains conceptual-only. It must not become a learned scorer in this artifact.

Suggested fields:
- `coverage_assessment`
- `role_stability_assessment`
- `compression_assessment`
- `output_uniqueness_assessment`
- `negative_evidence_assessment`
- `distractor_rejection_assessment`
- `exception_burden_assessment`
- `arbitrary_constant_penalty`
- `concept_bloat_penalty`
- `coordinate_color_overdependence_penalty`
- `unresolved_rival_grammar_penalty`
- `overall_inevitability_label`

Allowed labels:
- `high`
- `medium`
- `low`
- `unresolved`
- `unsafe_to_predict`

This section is meant to record why a theory felt forced or unforced, not to assign a learned truth score.

## 8. Safe failure taxonomy
Traceable failure modes should include:
- `representation_unresolved`
- `rival_grammars_disagree`
- `test_scene_parse_unstable`
- `insufficient_train_disambiguation`
- `concept_bloat_detected`
- `false_inevitability_risk`
- `unbounded_representation`
- `uninspectable_representation`
- `no_unique_output`
- `unsafe_prediction`

A strong trace format should let the system fail diagnostically rather than pretending the problem was merely search depth.

## 9. Anti-overfit trace checks
The trace should explicitly record whether the micro-theory:
- reused concepts across train examples
- avoided object naming when role definition was possible
- avoided arbitrary coordinates
- avoided color fixation unless color earned causality
- explained non-changes
- explained ignored distractors
- produced a unique output claim or safe failure
- stayed bounded
- stayed inspectable

Suggested record block:
- `anti_overfit_notes: [{check_name, status, evidence_note}]`

## 10. Cognitive Gym compatibility
This trace format should remain compatible with a future shared Cognitive Gym-style protocol.

It should:
- avoid private mythology
- keep protocol-like fields
- remain serializable
- support synthetic-only level references
- separate solver-visible and evaluator-only information
- preserve boundary flags
- make traces comparable across future agents or solvers
- avoid benchmark/public-performance claims

Suggested compatibility anchors:
- `source_protocol`
- `cognitive_gym_compatible`
- `synthetic_level_id`
- `observations`
- `trace_id`
- `comparison_summary`

UNKNOWN ENGINE-specific metadata is allowed, but the format should stay migratable rather than becoming a disconnected private philosophy.

## 11. Example trace skeleton
Placeholder-only illustrative skeleton:

```json
{
  "trace_id": "micro_trace_mock_0001",
  "trace_version": "MicroTheoryMockTraceV1",
  "synthetic_level_id": "ue_mock_level_001",
  "source_protocol": "cognitive_gym_style_mock_v1",
  "cognitive_gym_compatible": true,
  "synthetic_only": true,
  "non_claim_safe": true,
  "representation_forms_used": [
    {
      "schema_id": "micro_theory_role_graph_v1",
      "representation_type": "role_graph",
      "why_selected": "object targeting appears relational",
      "boundedness_notes": "finite role set"
    },
    {
      "schema_id": "micro_theory_absence_exception_ledger_v1",
      "representation_type": "absence_exception_ledger",
      "why_selected": "missing member pressure detected",
      "boundedness_notes": "finite absence categories"
    }
  ],
  "scene_decomposition": {
    "scene_objects": ["obj_a", "obj_b", "obj_c"],
    "candidate_regions": ["region_1"],
    "notes": "placeholder synthetic scene only"
  },
  "pressure_sources": [
    {"pressure_type": "missing_member", "ref": "region_1", "magnitude": "medium"}
  ],
  "absences_detected": [
    {"absence_type": "missing_counterpart", "ref": "obj_c"}
  ],
  "exceptions_detected": [],
  "candidate_roles": [
    {"object_id": "obj_a", "role": "anchor"},
    {"object_id": "obj_c", "role": "missing_counterpart"}
  ],
  "candidate_relations": [
    {"src": "obj_a", "relation": "selects", "dst": "obj_b"}
  ],
  "temporary_vocabulary": ["anchor", "missing_counterpart", "repair_target"],
  "grammar_arena": [
    {
      "candidate_id": "grammar_a",
      "temporary_language_summary": "repair the missing counterpart selected by anchor relation",
      "train_coverage": "high",
      "output_uniqueness": "medium",
      "predicted_output_claim": "placeholder_claim_a"
    },
    {
      "candidate_id": "grammar_b",
      "temporary_language_summary": "recolor salient object only",
      "train_coverage": "medium",
      "output_uniqueness": "low",
      "predicted_output_claim": "placeholder_claim_b"
    }
  ],
  "inevitability_assessment": {
    "coverage_assessment": "high",
    "role_stability_assessment": "medium",
    "overall_inevitability_label": "medium"
  },
  "safe_failure_mode": null,
  "predicted_output_claim": "placeholder_claim_a",
  "anti_overfit_notes": [
    {"check_name": "reused_concepts", "status": "pass", "evidence_note": "anchor and repair_target recur"}
  ],
  "boundedness_notes": "mock trace only; no executable content",
  "inspectability_notes": "all claims exposed as explicit records"
}
```

This skeleton uses placeholder synthetic IDs only. It is not a benchmark example and contains no public ARC/Kaggle content.

## 12. What is explicitly not implemented
This artifact does not implement:
- runtime solver
- executable schema
- learned scorer
- final-answer generator
- ChatResponder integration
- provider/model calls
- public ARC/Kaggle evaluation
- benchmark claim
- public claim
- behavior-pack promotion

## 13. Compatibility with representation schema candidates
The mock trace format is designed to sit above the schema candidates artifact.

It should:
- reference one or more schema families
- record why they were selected
- expose how they cooperated or conflicted
- preserve boundedness/inspectability notes per form
- allow later manual synthetic mock traces without implementation

## 14. What makes a good mock trace
A good mock trace:
- shows real representational tension, not just polished language
- exposes rival interpretations explicitly
- records why one theory became more inevitable than another
- supports safe failure instead of hiding ambiguity
- remains comparable across different UNKNOWN ENGINE levels
- can be inspected by a human without reverse engineering hidden state

## 15. Recommended next safe follow-up
Recommended next safe follow-up:
`RUN_MICRO_THEORY_SYNTHETIC_LEVEL_TRACE_MOCKS_V1`

Reason:
The mock trace format is now concrete enough to manually instantiate against synthetic UNKNOWN ENGINE levels without implementing runtime solver behavior. That makes manual bounded trace-mock creation the best next exploratory artifact.

## 16. Final note
The correct next step is not implementation. It is to test whether the trace format can capture genuinely different micro-theory attempts on synthetic levels without collapsing into decorative explanation or unbounded private mythology.
