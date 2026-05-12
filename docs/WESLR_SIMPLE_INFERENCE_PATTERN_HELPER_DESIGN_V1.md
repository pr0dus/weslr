# WESLR Simple Inference Pattern Helper Design V1

## Status

- design_only
- simple_inference_pattern_helper
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change

## Purpose

Design safe helper-only detection of simple inference-pattern opportunities over proposition candidates.

This layer is diagnostic and structural only. It identifies where a combined proposition pool may contain enough redacted proposition structure to justify later operator-reviewed helper work. It does not infer truth, generate proof steps, select answers, or connect to runtime scoring.

## Evidence

Redacted combined proposition pool diagnostic evidence:

- total items: 25
- predicate-derived propositions: 61
- binding-derived propositions: 28
- combined propositions: 89
- items with propositions: 21/25
- items with both premise and choice propositions: 4
- premise-choice comparisons: 16
- subject matches: 1
- object matches: 0
- relation matches: 5
- any-term matches: 6
- simple pattern candidates: 6
- items with simple pattern candidate: 3
- unsupported gaps: 0
- duplicate proposition signatures: 28
- anti-gaming safe: yes
- legibility safe: yes
- official score claimed: no

The evidence suggests a small but real opportunity surface for simple pattern detection, while duplicate proposition signatures remain a required blocker for trusted interpretation.

## Non-goals

- no proof-step generation
- no answer selection
- no solver wiring
- no MCQ adapter wiring
- no runtime integration
- no official score claim
- no answer-key use
- no item-ID authority
- no benchmark-specific tuning

## Required precondition

Proposition deduplication / merge handling must happen before inference candidates are trusted.

The combined pool currently includes duplicate proposition signatures. Simple inference-pattern helper output must therefore depend on a prior merge/dedup layer, or clearly mark all candidates as untrusted diagnostics only.

## Dedup/merge design

A future schema should introduce `PropositionMergeCandidate` or an equivalent helper-only record. This record should collapse duplicate proposition signatures without hiding source provenance or unsupported gaps.

Required fields:

- structural signature: role, proposition type, normalized subject, normalized relation, normalized object, polarity, and relevant canonical hints
- source proposition ids: all proposition records included in the merge candidate
- source origins: predicate-derived / binding-derived
- role: premise, choice_claim, background, or unknown
- confidence summary: conservative aggregate such as lowest confidence, confidence histogram, or explicitly mixed confidence
- duplicate count: number of matching proposition signatures beyond the retained representative
- unsupported gaps: union of visible unsupported gaps from all source propositions
- human explanation: redacted explanation of why the propositions are considered duplicate or merge-compatible
- no raw text: no raw questions, choices, answers, or benchmark text stored in the merge candidate

Merge behavior must be conservative:

- never promote low-confidence propositions silently
- never discard source provenance
- never treat duplicate support as proof
- never convert duplicate support into answer selection
- never use answer keys or item IDs as authority
- preserve ambiguity and unsupported gaps for operator review

## Simple pattern candidate types

Design-only candidate families:

### shared-subject

A premise proposition and choice proposition share a normalized subject signature. This is an opportunity marker only, not a claim that the choice is supported.

### shared-object

A premise proposition and choice proposition share a normalized object signature. This is an opportunity marker only, not a claim that the choice is entailed.

### relation-overlap

A premise proposition and choice proposition share a normalized relation signature. This can identify possible connective structure, but relation overlap alone is insufficient for truth or validity.

### contradiction-candidate

Two propositions appear structurally related but differ in polarity or incompatible relation framing. This is only a candidate for later review; it is not a contradiction proof.

### duplicate-support-candidate

Two or more merged propositions share the same structural signature or support the same redacted structural claim. This can identify repeated support, but duplicate support is not proof and cannot select answers.

### transitivity-candidate

Two or more propositions expose a chain-like structure, such as A relation B and B relation C, after deduplication. This is only an opportunity marker for later schema work.

### unsupported/no-pattern

The proposition pool lacks enough trusted, deduplicated, role-aware structure for simple pattern classification. This state must remain visible and must not be treated as failure or evidence for any answer.

## Safety

- pattern candidates are not proof steps
- pattern candidates are not truth claims
- pattern candidates cannot select answers
- ambiguity must remain visible
- low-confidence propositions must not be promoted silently
- duplicate-support candidates are not proof of correctness
- relation-overlap candidates are not entailment claims
- unsupported/no-pattern candidates must remain legible to operators
- no answer-key use
- no item-ID authority
- no benchmark-specific tuning
- no runtime integration
- no official score claim

## Future phases

A. design doc — current

B. proposition dedup/merge schema

C. dedup helper diagnostics

D. simple inference candidate schema

E. simple inference candidate diagnostics

F. only later proof-step generation

G. only much later solver/runtime integration

H. no official score claim

## Operator decision options

- APPROVE_PROPOSITION_MERGE_SCHEMA_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
