# WESLR Logic Teaching Spine Connectivity Contract V1

## Status
- design_only
- connectivity_contract
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change

## Purpose
Document that the teaching spine connects as a strict upward projection, not a side channel.

## Canonical flow
PredicateCandidate
→ PropositionCandidate
→ InferencePattern
→ ProofStep
→ CounterexampleCandidate
→ TeachingExplanation

## Connectivity rules

### A. PredicateCandidate → PropositionCandidate
- This is the only direct bridge from existing predicate layer into the teaching spine.
- PropositionCandidate.source_predicate_ids points back to source predicates.
- Propositions are claim-level normalization of predicate structure.

### B. PropositionCandidate + proposition groups → InferencePattern
- InferencePattern is a reusable typed reasoning template.
- It should not bind to one item/problem by itself.
- It declares expected proposition roles/types.

### C. PropositionCandidate + InferencePattern → ProofStep
- ProofStep is the first item-specific reasoning object.
- Core join:
  - ProofStep.source_proposition_ids
  - ProofStep.target_proposition_id
  - ProofStep.inference_pattern_id

### D. ProofStep / PropositionCandidate → CounterexampleCandidate
- Counterexamples challenge either:
  - a proposition, or
  - a proof step.
- Existing fields:
  - challenged_proposition_id
  - challenged_proof_step_id

### E. PropositionCandidate + ProofStep + CounterexampleCandidate → TeachingExplanation
- TeachingExplanation is a view layer over prior artifacts.
- It is not a reasoning primitive.
- It uses:
  - source_proposition_ids
  - source_proof_step_ids
  - source_counterexample_ids

## Design doctrine
- Predicates are structural atoms for claims.
- Propositions are claim units.
- Inference patterns are reusable reasoning forms.
- Proof steps are concrete reasoning applications.
- Counterexamples are concrete failure witnesses.
- Teaching explanations are human-facing summaries.

## Boundary rule
- PredicateCandidate feeds only PropositionCandidate directly.
- Higher layers must not reach back to PredicateCandidate except for traceability/provenance.
- Higher layers must not read raw parser text.
- Higher layers must not use answer keys.
- Higher layers must not use item IDs as authority.

## Non-goals
- no behavior implementation
- no parser changes
- no solver changes
- no MCQ adapter changes
- no runtime changes
- no answer selection
- no official score claim
- no benchmark-specific tuning

## Future first behavior phase
Recommend:
PredicateCandidate → PropositionCandidate helper diagnostics only

Explicitly:
- no inference application yet
- no proof-step generation yet
- no teaching explanation generation yet
- no solver consumption yet

## Operator decision options
- APPROVE_PROPOSITION_HELPERS_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
