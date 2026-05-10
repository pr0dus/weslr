# WESLR Formal Logic Reasoning Enrichment V1

**Status:** design only  
**Date:** 2026-05-10  
**Scope:** general formal_logic / ordinary_reasoning enrichment derived from internal public-subset failures  
**Implementation status:** documentation and test only. No runtime behavior changes.

## 1. Purpose

Design a general formal-logic / ordinary-reasoning enrichment from internal public-subset failures without memorizing benchmark items.

This design is for explainable reasoning improvement only. It does not implement runtime behavior, does not tune MCQ heuristics, and does not authorize any official benchmark claim.

## 2. Gap evidence

Observed internal public-subset evidence:

- dataset: MMLU formal_logic dev5
- official_score: false
- internal_eval: true
- accuracy: 0.0
- answered_count: 0
- no_answer_count: 5
- failure_mode: no_answer_selection across all 5 failures
- missing_skill: ordinary_reasoning across all 5 failures
- target_substrate: internal_reasoning_graph_and_eval_scorecard across all 5 failures
- enrichment gap records were written outside the repo for operator-reviewed follow-up

Interpretation boundary:

- these failures are evidence of a general missing reasoning skill only
- they are not evidence for answer-key recovery
- they are not evidence for item-specific rules
- they do not support any official benchmark claim

## 3. Anti-benchmark-gaming boundary

The following boundaries are mandatory:

- no answer-key storage
- no item-text memorization
- no item-specific phrase rules
- no official-score inference
- no official claim
- no hidden benchmark tuning
- failures are evidence of general missing reasoning skill only

This design must never turn internal public-subset failures into benchmark theater. The purpose is general reasoning enrichment, not benchmark gaming.

## 4. Explainable formal-logic reasoning rubric

Future reasoning behavior should be grounded in a transparent rubric with these dimensions:

- premise detection
- conclusion detection
- conditional reasoning
- necessary vs sufficient conditions
- negation
- quantifiers
- contradiction detection
- consistency checking
- valid vs invalid inference
- counterexample search
- answer-choice elimination
- uncertainty when symbolic form is unclear

Rubric intent:

- identify what the problem is asserting
- identify what must follow and what does not follow
- distinguish valid inference from invalid inference
- detect when contradiction, consistency, or quantifier structure changes the answer space
- prefer explainable elimination over opaque pattern matching
- surface uncertainty when the logical form is unclear instead of fabricating confidence

## 5. Future MCQ method

A future transparent method should:

1. parse question and choices
2. identify logical form
3. identify premises and conclusion
4. test each option against the premises
5. eliminate contradictions
6. prefer valid entailment or consistency
7. reject unsupported conclusions
8. state uncertainty if symbolic structure is unclear

This method should remain general. It should not encode benchmark-item shortcuts, answer-position bias, or phrase-trigger rules tied to a specific benchmark item.

## 6. Cognitive legibility

Every answer must be explainable in human terms.

Rules:

- no private or internal symbols as final authority
- any symbolic shorthand must be translatable
- reasoning categories must remain teachable, inspectable, and auditable
- the Cognitive Legibility Boundary remains the upper rule over any future formal-logic helper

## 7. Target substrate

Primary target substrate:

- internal_reasoning_graph_and_eval_scorecard

Secondary targets for later approved work:

- capability taxonomy
- formal reasoning scorer/helper later
- MCQ adapter formatting only after approval

The design choice follows the existing doctrine: extend current substrates first instead of inventing a benchmark-specific graph.

## 8. Future implementation steps

A. add formal-logic concept/rubric data  
B. add formal-logic scorer helper  
C. integrate into MCQ formatting only for formal_logic / ordinary_reasoning  
D. rerun internal subset  
E. convert remaining failures to enrichment gaps  
F. do not claim official score

These are staged implementation steps only. They require later approval before any runtime behavior change.

## 9. Required tests before implementation

Required tests:

- rubric/concept tests
- symbolic pattern tests
- conditional reasoning tests
- negation/quantifier tests
- contradiction tests
- no memorization tests
- no official-score claim tests
- before/after internal subset result
- failure-to-gap bridge remains intact

The test surface must prove that any future change improves general formal reasoning while preserving provenance, legibility, and anti-gaming boundaries.

## 10. Success criteria

Success is not official score.

Success means:

- higher answered_count on internal formal_logic subset
- fewer no_answer_selection failures
- explanations are logic-rubric-based
- no answer-key memorization
- official_score remains false
- failure records remain operator-reviewed

Non-success conditions include:

- any drift toward benchmark-specific memorization
- any attempt to infer an official score
- any design that cannot be translated into human-understandable reasoning
- any implementation that bypasses operator review for failure-derived enrichment
