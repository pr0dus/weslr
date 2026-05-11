# WESLR Formal Logic Normalization Governed Proposal V1

## Status
- proposal_only
- design_first
- DESIGN_FIRST
- operator_review_required
- execution_allowed = false
- official_score_claimed = false

## Scope Boundary
This document is a governed design proposal only. It does not implement parser changes, solver changes, scoring changes, MCQ adapter wiring, runtime behavior changes, or autonomous self-modification.

## Evidence Summary
Redacted aggregate evidence from internal evaluation only:
- sample size: 25
- distinct subsets: 5
- repeated failure count: 20
- aggregate solver status:
  - parsed_no_supported_inference: 24
  - parsed_ambiguous_candidates: 1
- aggregate bottlenecks:
  - no_term_overlap: 20
  - no_premises: 10
  - quantifier_present: 8
  - unsupported_fragments_present: 6
  - disjunction_present: 5
  - term_alignment_possible: 2
  - conditional_present: 1
  - same_relation_shape_seen: 1
- support metrics:
  - total premises: 23
  - total candidates: 100
  - total unsupported fragments: 9
  - potential term-alignment pairs: 6
  - same-shape pairs: 1
  - proposed answers: 0
- aggregate gate decision: DESIGN_FIRST
- operator_review_required: true
- execution_allowed: false
- official_score_claimed: false

No raw questions, raw choices, correct answers, benchmark item text, or benchmark-derived answer claims are included here.

## Problem Statement
WESLR can route MCQ items into ReasoningTask, parse them, create traces, and run FormalLogicSolver, but across 25 internal-eval items it still produces no proposed answers because parser/normalizer alignment is insufficient.

## Core Diagnosis
- The problem is not thresholding.
- The problem is not one dev5 slice.
- The pattern repeats across 5 subsets.
- The dominant issue is logical form / term alignment.
- Secondary issues are premise extraction gaps, quantifier handling, disjunction/case handling, and unsupported fragments.
- The next move should not patch item wording.
- The evidence points to an architectural gap between parse output and solver-consumable normalized form.

## Proposed Architecture
**LogicalFormNormalizer V1**

Proposed flow:

`LogicalFormParse -> LogicalFormNormalizer -> NormalizedLogicalForm -> FormalLogicSolver -> ReasoningTrace -> ReasoningArbitrator`

This component should sit between FormalLogicParser and FormalLogicSolver and operate in a design-governed, dry-run-first path only.

## Proposed Responsibilities
LogicalFormNormalizer V1 should:
- normalize terms without raw-text persistence
- align premise terms and candidate terms
- preserve visible candidate identity only
- detect relation shapes
- normalize singular/plural where safe
- normalize simple predicates
- normalize negation forms
- expose unsupported normalization gaps
- create trace warrants
- never select answers directly

## Non-Responsibilities
LogicalFormNormalizer V1 must not:
- perform answer selection
- make score claims
- use answer-key data
- use item-id authority
- add benchmark-specific phrase rules
- add hidden tuning
- perform runtime wiring in V1

## Proposed Data Structures
- `NormalizedLogicalForm`
- `NormalizedTerm`
- `NormalizedPredicate`
- `TermAlignmentRecord`
- `NormalizationWarning`
- `NormalizationLegibilityRecord`
- `NormalizationAntiGamingRecord`

### Structure Intent
- `NormalizedLogicalForm`: normalized container for premises, candidate-linked statements, relation summaries, and warnings
- `NormalizedTerm`: canonical term identity with safe morphological normalization metadata
- `NormalizedPredicate`: normalized predicate/operator representation with polarity and shape metadata
- `TermAlignmentRecord`: explicit record of why two terms were considered aligned or not aligned
- `NormalizationWarning`: redacted explanation for unsupported normalization gaps or ambiguity
- `NormalizationLegibilityRecord`: human-readable justification trail for normalization decisions
- `NormalizationAntiGamingRecord`: boundary record showing no answer-key use, no item-id use, and no benchmark-specific tuning

## Proposed Safety Constraints
- no raw benchmark storage by default
- no answer-key use
- no item-id use
- no item-id authority
- no official-score claim
- no benchmark-specific tuning
- no private symbolic authority
- human-readable normalization warrants required
- candidate identity must remain visible and auditable
- unsupported normalization gaps must remain explicit rather than silently coerced

## Proposed Tests Before Implementation
- dataclass/schema tests
- anti-gaming tests
- raw-text non-storage tests
- term normalization tests
- relation-shape tests
- negation normalization tests
- singular/plural normalization tests
- candidate identity preservation tests
- no answer-selection tests
- trace-warrant tests
- aggregate evidence regression tests
- release gate

## Proposed Implementation Phases
A. design proposal only — current phase  
B. normalizer schema only  
C. normalizer helper functions  
D. redacted diagnostics over existing 25-item aggregate  
E. solver consumes normalized form in dry-run only  
F. arbitrator dry-run comparison  
G. only later: opt-in MCQ adapter path behind explicit flag  
H. no official claim

## Operator Decision Required
This proposal requires operator review before any implementation work.

Possible operator decisions:
- `APPROVE_SCHEMA_ONLY`
- `REQUEST_REVISION`
- `REJECT_OR_DEFER`

## Explicit Forbidden Implementation Now
- no parser code changes
- no solver code changes
- no MCQ adapter changes
- no threshold changes
- no benchmark-specific fixes
- no runtime wiring now
- no autonomous self-modification

## Governed Next Step Recommendation
If the operator approves, the safe next step is schema-first only: define the NormalizedLogicalForm family and tests before any parser or solver integration.
