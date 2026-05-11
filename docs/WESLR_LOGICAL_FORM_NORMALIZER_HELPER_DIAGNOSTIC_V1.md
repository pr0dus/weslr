# WESLR LogicalFormNormalizer Helper Diagnostic V1

## Status
- diagnostic_checkpoint
- evidence_only
- no_behavior_change
- operator_review_required
- execution_allowed = false
- official_score_claimed = false

## Purpose
This diagnostic measured whether the newly added helper-only LogicalFormNormalizer functions improved term-alignment visibility before any parser, solver, or runtime wiring.

## Evidence Summary
- suite_count: 5
- total_item_count: 25
- total_premises: 23
- total_candidates: 100
- total_normalized_terms: 123
- total_alignments: 0
- items_with_alignment: 0
- items_with_no_premises: 10
- anti-gaming safe: yes
- legibility safe: yes
- official score claimed: no

## Per-Suite Redacted Summary
- mmlu_formal_logic_dev5_v1
  - premises: 6
  - candidates: 20
  - normalized terms: 26
  - alignments: 0
  - items with no premises: 2
- mmlu_logical_fallacies_dev5_v1
  - premises: 1
  - candidates: 20
  - normalized terms: 21
  - alignments: 0
  - items with no premises: 4
- mmlu_philosophy_dev5_v1
  - premises: 3
  - candidates: 20
  - normalized terms: 23
  - alignments: 0
  - items with no premises: 2
- mmlu_abstract_algebra_dev5_v1
  - premises: 7
  - candidates: 20
  - normalized terms: 27
  - alignments: 0
  - items with no premises: 1
- mmlu_high_school_mathematics_dev5_v1
  - premises: 6
  - candidates: 20
  - normalized terms: 26
  - alignments: 0
  - items with no premises: 1

## Interpretation
- Helpers are safe and redacted.
- Helpers preserve anti-gaming and legibility.
- Helpers are useful as negative evidence.
- Current helper layer is too weak to support solver improvement.
- Whole-statement surface normalization does not create useful term alignments.
- Zero alignments across 123 normalized terms indicates a structural gap.

## Diagnosis
The next design revision should focus on:
- atomic term extraction
- predicate decomposition
- premise/candidate role-aware term extraction
- relation-shape normalization
- quantifier-aware predicate representation
- disjunction/case representation
- unsupported-gap tracking

## Explicit Non-Conclusion
- This does not justify parser wiring.
- This does not justify solver wiring.
- This does not justify MCQ adapter wiring.
- This does not justify threshold changes.
- This does not justify benchmark-specific fixes.

## Recommended Next Operator Decision
`REQUEST_REVISION`

Reason: The helper layer is safe but insufficient. Revise the normalizer design before implementation.

## Future Proposed Revision
**LogicalFormNormalizer V1.1**

Focus:

`ParsedStatement -> atomic terms -> predicates -> premise/candidate alignment -> normalized logical form`

## Safety Boundaries
- no raw benchmark storage by default
- no answer-key use
- no item-id authority
- no official-score claim
- no benchmark-specific tuning
- no answer selection
- no autonomous self-modification
- no MCQ adapter wiring now
- no solver wiring now
- no threshold changes

No raw benchmark text, no raw choices, and no correct answers are included in this diagnostic checkpoint.
