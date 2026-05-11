# WESLR Logic Teaching Spine V1

## Status
- design_only
- teaching_spine
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change

## Purpose
WESLR is moving from structural recognition toward teachable logic.
The objective is not answer selection. The objective is legible proof, invalidity analysis, counterexample construction, and explanation that a human can inspect and learn from.

## Existing foundation
Current stack:

ReasoningTask
→ LogicalFormParse
→ AtomicTermCandidate
→ RoleAwareTermIndex
→ AlignmentEvidence
→ PredicateCandidate
→ ReasoningTrace
→ ReasoningArbitrator

## Evidence trigger
Redacted diagnostic metrics motivating this design layer:
- 25 items
- 636 atomic term candidates
- 24 relation-hint candidates
- 24 predicate candidates
- 16 items with predicate candidates
- anti-gaming safe
- legibility safe
- official score claimed: no

## Design objective
Next conceptual stack:

PredicateCandidate
→ PropositionCandidate
→ InferencePattern
→ ProofStep
→ CounterexampleCandidate
→ TeachingExplanation

## Proposed structures

### A. PropositionCandidate
**Purpose**
- convert predicate candidates into inspectable logical claims

**Fields to describe**
- proposition id
- source predicate ids
- proposition type
- subject
- relation
- object
- polarity
- quantifier
- modality
- confidence
- human translation
- unsupported gaps

**Role in spine**
A PropositionCandidate is the first unit that can be discussed as a claim rather than only a structural decomposition artifact. It should preserve uncertainty when predicate decomposition is shallow, incomplete, or ambiguous.

### B. InferencePattern
**Purpose**
- identify possible reasoning forms

**Examples**
- modus ponens
- modus tollens
- universal syllogism
- transitive class inclusion
- contradiction
- affirming the consequent
- denying the antecedent
- converse error
- inverse error
- necessary/sufficient confusion
- disjunction elimination
- counterexample-needed

**Role in spine**
An InferencePattern is not an answer selector. It is a typed hypothesis about the reasoning form connecting propositions. It may represent either a valid pattern or a recognizable invalid pattern that should later be explained explicitly.

### C. ProofStep
**Purpose**
- represent one legible reasoning move

**Fields to describe**
- source proposition ids
- target proposition id
- inference pattern id
- warrant
- validity status
- confidence
- human explanation

**Role in spine**
A ProofStep should describe how a target proposition follows, fails to follow, or remains unsupported from one or more source propositions. Validity status should distinguish valid, invalid, ambiguous, and unsupported moves.

### D. CounterexampleCandidate
**Purpose**
- represent why an inference may fail

**Fields to describe**
- challenged proposition/inference
- counterexample type
- possible world sketch
- violated assumption
- human explanation

**Role in spine**
A CounterexampleCandidate makes invalidity teachable. It should expose a possible world or interpretation in which the premises hold but the claimed conclusion or inference does not.

### E. TeachingExplanation
**Purpose**
- explain reasoning in human-teachable form

**Fields to describe**
- conclusion
- why supported
- why unsupported
- why invalid
- common fallacy if any
- step-by-step explanation
- learner-level wording
- uncertainty note

**Role in spine**
A TeachingExplanation is the legible teaching surface. It should translate structural reasoning artifacts into human-readable guidance without hiding uncertainty, unsupported assumptions, or invalid steps.

## Teaching modes
Possible future explanation modes:
- beginner explanation
- academic explanation
- proof-only explanation
- counterexample-first explanation
- Socratic hint mode
- Spock mode: maximally precise, minimal emotion, validity-focused

## Non-goals
- no answer selection in this phase
- no solver wiring
- no MCQ adapter wiring
- no runtime wiring
- no benchmark-specific tuning
- no answer-key use
- no item-id authority
- no official score claim
- no raw benchmark storage by default

## Safety and governance
- all proof/counterexample structures must be legible
- opaque model authority is not enough
- uncertain symbolic translations must remain uncertain
- invalid patterns must be explainable
- teaching explanations must not hide unsupported assumptions
- explanation quality must not depend on answer-key authority
- structural confidence must not be misrepresented as proof certainty

## Future phased plan
A. design doc — current phase
B. schema only
C. proposition helper diagnostics
D. inference-pattern schema
E. proof-step schema
F. counterexample schema
G. teaching explanation schema
H. dry-run diagnostics
I. only later: solver consumption
J. only much later: MCQ adapter opt-in
K. no official score claim

## Success criteria
- WESLR can distinguish valid, invalid, ambiguous, and unsupported reasoning
- WESLR can explain why an inference works
- WESLR can explain why an inference fails
- WESLR can expose common fallacies
- WESLR can generate counterexample structures
- WESLR can teach without answer-key authority

## Operator decision options
- APPROVE_PROPOSITION_SCHEMA_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
