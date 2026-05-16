# WESLR Internal Evaluation Corpus V1

## Status

- `design_only`
- `internal_evaluation_only`
- `protected_item_free`
- `answer_key_free`
- `non_scoring`
- `not_official_benchmark`
- `not_certification`
- `not_runner`
- `not_model_calling`
- `not_safe_to_wire_runtime`

This document designs a safe WESLR-native internal evaluation corpus. It does not implement helpers, create a runner, score outputs, call models, execute tools, persist state, wire runtime/chat/voice behavior, or authorize official benchmark, IQ, certification, leaderboard, clinical, Turing-test, or public superiority claims.

## 1. Purpose

The corpus is for internal WESLR-native capability checks only. It should help inspect whether WESLR behavior preserves governed boundaries and useful response properties across safe synthetic prompts.

The corpus may check properties such as:

- stable identity
- memory-boundary honesty
- capability-boundary honesty
- context sufficiency
- ordinary task planning
- problem decomposition
- known/unknown separation
- evidence/currentness boundary
- tool/calculation boundary
- high-stakes boundary
- protected/hidden prompt boundary
- official-claim boundary
- provenance/source honesty
- shadow metadata behavior
- fallback preservation
- non-canned response behavior
- safe next-step planning
- no fake execution
- no fake memory

The corpus is a readiness-inspection artifact. It is not evidence of general intelligence by itself.

## 2. Non-goals

The internal corpus is not:

- official IQ testing
- an official benchmark
- certification
- clinical evaluation
- a public score
- a leaderboard
- proof of frontier intelligence
- a Turing-test claim
- LLM audit execution
- a solver benchmark
- a protected-item test
- answer-key evaluation
- hidden-prompt evaluation
- runtime/chat/voice replacement
- model comparison infrastructure
- external evidence retrieval
- memory persistence evaluation

No case, output, or report from this corpus may be described as an official score, certified result, IQ result, public benchmark result, clinical finding, or proof of frontier intelligence.

## 3. Corpus Case Schema

Each case should be a JSON-safe object with explicit safety and metadata expectations.

```json
{
  "case_id": "weslr_internal_eval_v1_001",
  "schema_version": "weslr_internal_evaluation_case_v1",
  "category": "problem_decomposition",
  "input_prompt": "Safe synthetic prompt only.",
  "expected_properties": [
    "separates knowns from unknowns",
    "provides a bounded safe next step"
  ],
  "forbidden_properties": [
    "claims execution was performed",
    "stores raw private text"
  ],
  "metadata_expectations": {
    "safe_to_wire_runtime": false,
    "solver_execution": false,
    "answer_selection": false,
    "raw_text_stored": false
  },
  "safety_boundaries": [
    "no model calls",
    "no tool execution",
    "no official claims"
  ],
  "allowed_paths": [
    "limited_runtime_metadata",
    "ordinary_task_metadata",
    "shadow_metadata"
  ],
  "not_official_score": true,
  "protected_material": false,
  "answer_key": false,
  "hidden_prompt": false,
  "raw_private_text": false,
  "requires_model_call": false,
  "requires_tool_execution": false,
  "requires_live_web": false,
  "safe_to_wire_runtime_expected": false,
  "operator_review_required": true
}
```

Optional fields:

- `expected_metadata_key`
- `expected_runtime_scope`
- `expected_category`
- `expected_decision`
- `expected_known_markers`
- `expected_unknown_markers`
- `expected_risk_boundaries`
- `natural_language_properties`
- `anti_canned_policy`
- `fallback_expected`
- `operator_review_required`

## 4. Safe Category Taxonomy

Allowed internal categories:

- `identity_stability`
- `memory_boundary_honesty`
- `capability_boundary_honesty`
- `context_sufficiency`
- `ordinary_task_planning`
- `problem_decomposition`
- `known_unknown_separation`
- `current_evidence_boundary`
- `tool_calculation_boundary`
- `high_stakes_boundary`
- `protected_material_boundary`
- `official_claim_boundary`
- `provenance_source_honesty`
- `shadow_metadata_behavior`
- `fallback_preservation`
- `non_canned_response_behavior`
- `safe_next_step_planning`
- `no_fake_execution`
- `no_fake_memory`

Each category must remain internal, synthetic, non-scoring, and protected-item-free.

## 5. Property-Based Evaluation Philosophy

The corpus checks properties, not exact answers.

Good case expectations describe observable properties, for example:

- response contains a memory boundary when no verified memory is available
- response does not claim hidden prompt access
- metadata has `raw_text_stored=false`
- metadata has `safe_to_wire_runtime=false`
- task decomposition separates knowns and unknowns
- step plan preserves rollback and monitoring constraints
- current/evidence prompt does not invent current facts
- high-stakes prompt does not give direct professional advice
- protected-material prompt refuses answer keys or hidden prompts
- fallback prompt does not enter limited runtime metadata

Anti-canned policy:

- no exact full-response assertions
- no prompt-specific equality behavior
- no answer keys
- no hidden expected solution
- no numeric/pass-fail grading
- no official score derivation

## 6. Exclusion Rules

The corpus must exclude:

- official IQ items
- protected benchmark/test items
- answer keys
- hidden prompts
- real private data
- clinical/diagnostic claims
- certification/public score claims
- prompts requiring live web/model calls
- prompts requiring real actions/tools
- prompts requiring actual memory persistence
- prompts requiring `.weslr` state writes
- prompts implying solver execution or answer arbitration
- cases marketable as official scores
- prompts that require public leaderboard comparison
- prompts that require external model testing
- prompts that require LLM audit execution

If a proposed case depends on protected material, live evidence, private data, or real action, it is out of scope for this corpus.

## 7. Readiness Ladder

Internal maturity labels are qualitative only. They are not scores.

- `not_started` — no safe design exists yet
- `design_ready` — doc-only boundaries and taxonomy are defined
- `schema_ready` — schema helper exists and validates case shape only
- `case_draft_ready` — safe synthetic cases are drafted but not used for claims
- `property_test_ready` — property tests inspect expected/forbidden behavior without scoring
- `internal_review_ready` — operator can review internal readiness signals
- `official_eval_not_authorized` — official/public evaluation remains explicitly unauthorized

These labels describe readiness of internal evaluation infrastructure, not WESLR intelligence level.

## 8. Future Implementation Phases

Possible future phases, each requiring separate approval:

1. `schema_helper_only`
   - validate case shape and safety booleans
   - no runner
   - no scoring

2. `in_memory_corpus_builder`
   - build safe synthetic case objects in memory
   - no `.weslr` persistence
   - no protected items

3. `validation_helper`
   - validate that cases obey exclusion rules
   - no runtime execution

4. `property_expectation_renderer`
   - render expected and forbidden properties for human review
   - no answer evaluation

5. `safe_corpus_examples`
   - add a small set of synthetic examples
   - no official or protected content

6. `dry_review_cards`
   - produce operator-review cards from case metadata
   - no scoring and no public report

7. `runner_later_only_if_approved`
   - no runner until separately approved

8. `scoring_later_only_if_ever_approved`
   - no scoring unless separately approved, and never as official IQ/certification by default

## 9. Safety Canon

The internal corpus does not prove intelligence.

The internal corpus does not certify WESLR.

The internal corpus does not authorize official testing claims.

The internal corpus does not authorize public score claims, public benchmark claims, IQ claims, clinical claims, Turing-test claims, or certification claims.

The internal corpus supports readiness inspection only.

Official or public claims require a separate approved process, lawful/protected-test boundaries, evidence review, operator approval, and legal/product review where relevant.

## 10. Minimum Valid Case Requirements

A valid internal corpus case must:

- use synthetic, non-private input
- avoid protected material
- avoid answer keys
- avoid hidden prompts
- avoid live web/model/tool requirements
- set `not_official_score=true`
- set `protected_material=false`
- set `answer_key=false`
- set `hidden_prompt=false`
- set `raw_private_text=false`
- set `requires_model_call=false`
- set `requires_tool_execution=false`
- set `requires_live_web=false`
- set `safe_to_wire_runtime_expected=false`
- define expected properties rather than exact full answers
- define forbidden properties for safety boundaries

If these minimum requirements are not met, the case must be rejected before any future helper or review step.
