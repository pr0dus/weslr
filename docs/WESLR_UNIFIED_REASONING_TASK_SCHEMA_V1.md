# WESLR Unified Reasoning Task Schema V1

**Status:** doctrine/design document  
**Date:** 2026-05-11  
**Scope:** unified schema for future benchmark reasoning engine / cognitive orchestration layer  
**Implementation status:** schema doctrine and tests only. No runtime behavior changes.

## 1. Purpose

WESLR is moving from subject-specific scorers toward a general Benchmark Reasoning Engine / Cognitive Orchestration Layer.

This document defines the first unified task schema for that future layer. It is intended to support both formal logic reasoning and ethics/tradeoff reasoning while preserving the Cognitive Legibility Boundary.

This document does not implement runtime behavior, does not wire into MCQ formatting, does not modify scorers, does not change adapter behavior, and does not authorize any official-score claim.

## 2. Why this exists

Recent enrichment work showed several structural lessons:

- the business_ethics scorer helped partially but stayed narrow
- formal_logic keyword scoring failed
- patch-by-subject does not scale
- subject scorers are helpers, not central intelligence
- WESLR needs a common task representation, blackboard state, solver outputs, arbitrator, and legible trace

The first general step is therefore not more subject-specific scorers. The first general step is a unified schema and arbitrator layer that can host multiple solver types without turning benchmark work into scorer sprawl.

## 3. Schema name

Canonical name: `ReasoningTask`

Compatible or older discussion term: `StructuredReasoningRequest`

This doctrine uses `ReasoningTask` as the canonical name because it is shorter, more general, and better aligned with a future blackboard / solver / arbitrator architecture.

## 4. Required top-level fields

A `ReasoningTask` must define these top-level fields:

- `schema_version`
- `task_id`
- `task_family`
- `domain`
- `required_skill`
- `provenance`
- `input`
- `parsed`
- `choice_representations`
- `blackboard`
- `solver_plan`
- `arbitration`
- `legibility`
- `anti_gaming`
- `failure`

Illustrative shape:

```python
ReasoningTask(
    schema_version="1.0",
    task_id="...",
    task_family="multiple_choice_reasoning",
    domain="formal_logic_or_ethics",
    required_skill="ordinary_reasoning",
    provenance={...},
    input={...},
    parsed={...},
    choice_representations=[...],
    blackboard={...},
    solver_plan={...},
    arbitration={...},
    legibility={...},
    anti_gaming={...},
    failure={...},
)
```

## 5. Provenance fields

The `provenance` section should include:

- `source_eval`
- `dataset_name`
- `subset_name`
- `official_score`
- `internal_eval`
- `sample_only`
- `item_fingerprint`
- `adapter_version`
- `prompt_format_version`

Interpretation rules:

- `official_score` must remain explicit and false for internal benchmark-style work unless a real official process says otherwise
- `internal_eval` distinguishes internal measurement from external benchmark submission
- `item_fingerprint` exists so the system can track recurrence without storing raw benchmark content by default

## 6. Input fields

The `input` section should include:

- `question_text` as runtime-only / not stored by default
- `question_fingerprint`
- `choices`

Input rules:

- choice text may be runtime-only / fingerprinted
- no answer key stored in task schema by default
- raw benchmark text should not be stored by default unless an explicit doctrine-safe exception is approved

Illustrative shape:

```python
input = {
    "question_text": "runtime-only / not stored by default",
    "question_fingerprint": "sha256:...",
    "choices": [
        {"label": "A", "text": "runtime-only / fingerprinted"},
        {"label": "B", "text": "runtime-only / fingerprinted"},
    ],
}
```

## 7. Parsed fields

The `parsed` section should include:

- `task_type`
- `question_intent`
- `premises`
- `conclusion_candidates`
- `constraints`
- `assumptions`
- `entities`
- `relations`

This parsed layer is where WESLR converts raw question material into a general reasoning representation rather than directly scoring text snippets.

## 8. Choice representation fields

Each entry in `choice_representations` should include:

- `label`
- `claims`
- `implied_assumptions`
- `supports`
- `violations`
- `uncertainties`

These fields let WESLR compare options as structured reasoning objects instead of opaque answer strings.

## 9. Blackboard fields

The `blackboard` section should include:

- `hypotheses`
- `inferences`
- `conflicts`
- `solver_outputs`

The blackboard is the shared intermediate state where candidate solvers and verifiers deposit structured observations for later arbitration.

## 10. Solver plan fields

The `solver_plan` section should include:

- `candidate_solvers`
- `selected_solvers`
- `blocked_solvers`

This allows task-family-aware orchestration without making any single scorer or model the hidden authority.

## 11. Arbitration fields

The `arbitration` section should include:

- `selected_answer`
- `confidence`
- `uncertainty`
- `conflict_status`
- `why_selected`
- `why_rejected`

The arbitrator is the decision layer. It compares solver outputs, resolves or exposes conflicts, and produces a bounded decision record.

## 12. Legibility fields

The `legibility` section should include:

- `human_explanation`
- `reasoning_trace_summary`
- `symbolic_forms_translated`
- `private_authority_used`

Required boundary:

- `private_authority_used` should be false for acceptable outputs
- symbolic forms may exist internally, but they must be translated into human-understandable terms
- prompt-only reasoning traces are not sufficient authority by themselves

## 13. Anti-gaming fields

The `anti_gaming` section should include:

- `uses_item_id`
- `uses_answer_key`
- `uses_answer_position_bias`
- `stores_raw_question_by_default`
- `official_score_claimed`

These fields exist to make benchmark contamination and heuristic drift visible.

## 14. Failure fields

The `failure` section should include:

- `failure_mode`
- `missing_skill`
- `target_substrate`
- `enrichment_record_allowed`

This connects task-level outcomes to future enrichment work without storing answer keys or collapsing into benchmark-specific patches.

## 15. Formal logic mapping

Formal logic maps naturally into `ReasoningTask`:

- `premises` capture explicit statements and conditional structure
- `conclusion_candidates` capture what might follow
- `constraints` capture quantifiers, negation scope, exclusivity, and valid-form requirements
- valid/invalid inference becomes part of `inferences` and `violations`
- contradiction becomes a `conflicts` record
- consistency becomes a structured check over premises and choice claims
- symbolic translation becomes a legibility artifact under `symbolic_forms_translated`

Example interpretation:

- a syllogism becomes parsed premises plus candidate conclusion relations
- a contradiction check becomes a deterministic verifier result written to the blackboard
- consistency and entailment can be arbitrated without keyword scoring

## 16. Ethics/tradeoff mapping

Ethics/tradeoff reasoning also maps naturally into `ReasoningTask`:

- stakeholders become `entities`
- duties/rights/governance become `constraints`
- values/tradeoffs become `relations`
- option impacts become `choice_representations`
- arbitration compares conflicts across harms, duties, rights, authority, reversibility, and uncertainty

Example interpretation:

- harms and benefits become structured supports or violations
- governance and authority constraints can block otherwise attractive options
- stakeholder conflicts can be surfaced explicitly instead of hidden in a single scorer output

## 17. Blackboard / registry of verifiers

Future architecture rule:

- solvers write to blackboard
- arbitrator checks conflicts
- deterministic verifiers should validate high-risk or symbolic claims
- probabilistic/LLM modules may propose, but not become final authority without legible support

This supports a neuro-symbolic blackboard / registry of verifiers architecture while preserving operator inspectability.

Examples of future verifier roles:

- formal contradiction checker
- consistency checker
- symbolic translation verifier
- governance-constraint verifier
- evidence-boundary verifier

## 18. Existing substrate mapping

`ReasoningTask` should connect to existing WESLR substrates as follows:

- `internal_reasoning_graph` = long-term failure patterns / traces / proposals
- `concept_graph` = domain concepts / axioms / evidence-bearing relations
- `capability_registry` = task and solver taxonomy
- `eval_scorecard` = measurement only
- meaning/response-obligation = nuance and intent layer
- MCQ adapter = input/output shell, not reasoning core

Interpretation rule:

- the unified schema is the reasoning-facing representation
- existing substrates remain the surrounding institutional memory, evidence, routing, and measurement layers
- subject scorers may still exist as narrow helpers, but they are not the central reasoning engine

## 19. Anti-patterns

The following are forbidden:

- subject-specific scorer sprawl
- answer-key memorization
- benchmark-specific phrase rules
- prompt-only reasoning traces
- official-score claims from internal evals
- private symbolic authority
- storing raw benchmark data by default

These anti-patterns are forbidden because they weaken generalization, auditability, and cognitive legibility.

## 20. Future implementation phases

A. schema dataclasses only  
B. ReasoningTrace schema  
C. solver registry  
D. arbitrator/conflict detector  
E. formal logic solver as first real solver  
F. ethics/tradeoff solver migration  
G. MCQ adapter calls reasoning engine  
H. failure bridge records solver-level failures  
I. scorecard compares before/after  
J. no official claim

Phase reading:

- Phase A defines `ReasoningTask` and related schema objects only
- later phases may connect runtime components, but only after doctrine and tests stay legible
- even after implementation, internal evaluations remain separate from any official benchmark process

## Canonical decision

WESLR should standardize on `ReasoningTask` as the first general schema for a future Benchmark Reasoning Engine / Cognitive Orchestration Layer.

The next architectural center should be a unified schema plus arbitrator, not more subject scorers.
