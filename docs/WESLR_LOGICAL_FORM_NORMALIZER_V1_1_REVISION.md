# WESLR LogicalFormNormalizer V1.1 Revision

## Status
- revision_design
- request_revision
- evidence_driven
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change

## Trigger
V1 helper diagnostic showed:
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

## Diagnosis
- whole-statement surface normalization is too weak
- zero alignments across 123 normalized terms shows structural inadequacy
- the next step is not parser wiring, solver wiring, threshold tuning, or benchmark-specific patching
- the missing layer is atomic logical-form normalization

## V1.1 Design Objective
Design a normalizer that transforms parsed statements into atomic, inspectable units:

`ParsedStatement -> atomic term candidates -> predicate candidates -> role-aware premise/candidate structures -> term alignment records -> normalized logical form`

## Proposed V1.1 Architecture
`LogicalFormParse -> AtomicExtractionPass -> PredicateDecompositionPass -> RoleAwareAlignmentPass -> NormalizedLogicalForm -> dry-run diagnostics only`

## Atomic Term Extraction Responsibilities
- split statement-level surfaces into candidate terms
- preserve only fingerprints and canonical forms
- distinguish premise terms from candidate terms
- avoid raw text persistence
- avoid answer-label authority
- mark unsupported extraction gaps visibly

## Predicate Decomposition Responsibilities
- represent subject / relation / object where safely identifiable
- preserve polarity
- preserve quantifier
- preserve modality
- support relation-shape normalization
- produce human-readable warrants
- avoid hidden symbolic authority

## Role-Aware Alignment Responsibilities
- align premise-side terms to candidate-side terms only through visible normalized evidence
- distinguish exact canonical match from weak candidate match
- never select answers
- never use answer keys
- never use item ids as authority
- emit alignment confidence and explanation
- expose unaligned premise/candidate terms

## New Proposed Schema Additions or Extensions
Design only. Do not implement.

- `AtomicTermCandidate` — atomic term candidate record with role, canonical form, fingerprint list, confidence, and visible warrant summary
- `PredicateCandidate` — predicate candidate record with subject/object references, relation shape, polarity, quantifier, modality, and diagnostic confidence
- `RoleAwareTermIndex` — per-item role-aware index of premise-side and candidate-side terms with safe references only
- `AlignmentEvidenceRecord` — visible evidence container for exact-match or weak-match alignment support without raw text persistence
- `NormalizerDiagnosticSummary` — redacted aggregate diagnostic record for atomic extraction coverage, alignment density, unsupported gaps, anti-gaming, and legibility status

## Diagnostic-First Implementation Plan
A. V1.1 revision doc — current phase  
B. schema extension only  
C. atomic extraction helpers only  
D. redacted diagnostic over 25-item aggregate  
E. predicate decomposition helpers only  
F. redacted diagnostic over 25-item aggregate  
G. role-aware alignment helpers only  
H. redacted diagnostic over 25-item aggregate  
I. only after evidence: dry-run solver consumption  
J. only later: opt-in MCQ adapter path behind explicit flag  
K. no official claim

## Success Criteria Before Solver Consumption
- normalized terms are atomic, not whole statements
- alignments are greater than zero on aggregate
- alignments are explainable
- anti-gaming remains safe
- legibility remains safe
- raw text is not stored by default
- no answer selection occurs
- no benchmark-specific rules are introduced

## Stop Criteria
- zero alignments remain after atomic extraction
- alignments depend on benchmark-specific patterns
- alignments require raw text persistence
- alignments depend on answer labels or answer keys
- diagnostics remain too sparse or noisy

## Safety Boundaries
- no raw benchmark storage by default
- no answer-key use
- no item-id authority
- no official-score claim
- no benchmark-specific tuning
- no answer selection
- no autonomous self-modification
- no runtime wiring now

## Operator Decision Options
- `APPROVE_V1_1_SCHEMA_EXTENSION_ONLY`
- `REQUEST_MORE_DIAGNOSTICS`
- `REJECT_OR_DEFER`

## Explicit Forbidden Actions Now
- no changes to `logical_form_normalizer.py`
- no parser changes
- no solver changes
- no MCQ adapter changes
- no threshold changes
- no benchmark-specific fixes
- no runtime wiring

This revision doc includes no raw benchmark question text, no answer choices, and no correct answers.
