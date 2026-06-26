# WESLR MICRO-THEORY SOLVER V1 / TEMPORARY LANGUAGE INVENTOR SOLVER V1

## Status
Design only. No implementation, no solver patching, no runtime wiring, no ChatResponder integration, no provider/model calls, no learned scorer implementation, no public ARC/Kaggle ingestion, no benchmark claim, no `.weslr` writes, and no push.

## 1. One-line definition
A design-only WESLR solver direction where each UNKNOWN ENGINE level is first explained by a disposable private grammar of roles, relations, absences, exceptions, pressures, and transformations, and only then compiled into a grid output if the grammar makes the train examples inevitable.

## 2. Core shift

### Normal solver
`grid → primitive/program search → output`

### Micro-Theory Solver
`grid → strangeness detection → temporary language invention → competing micro-theories → inevitability test → output or safe failure`

The core shift is that the first question is no longer “which primitive sequence fits?” It is “what hidden grammar would make these examples stop being strange?”

## 3. Architecture proposal
The direction is organized as conceptual stages:

1. **scene decomposition**
2. **difference pressure detection**
3. **temporary concept invention**
4. **role induction**
5. **micro-language construction**
6. **competing grammar arena**
7. **inevitability testing**
8. **counterfactual pressure testing**
9. **safe prediction / safe failure**
10. **UNKNOWN ENGINE feedback loop**

The design assumes these stages remain bounded, synthetic-only, and internal. No public benchmark authority is implied.

## 4. Scene decomposition
The solver should read each grid as a scene, not merely as colored cells.

Candidate scene elements:
- colored regions
- objects
- holes
- boundaries
- symmetry structures
- gaps
- singletons
- repeated motifs
- containers
- contained objects
- touching / non-touching relations
- inside / outside relations
- missing counterparts
- changed cells
- unchanged cells
- objects that survive input to output
- objects that disappear
- objects that appear

Important distinction:
- **object** = visible structure
- **role** = function inside the hidden grammar

A red square may matter not because it is red or square, but because it is the only object without a partner, the blocker, the anchor, the witness, the target, the exception, or the thing that defines a missing region.

## 5. Difference pressure detection
Before inventing a rule, the solver should detect pressure: what in the input/output relation demands explanation.

Pressure sources:
- changed cells
- unchanged-but-suspicious cells
- missing expected objects
- objects with no counterpart
- asymmetries
- broken repetitions
- one object behaving differently
- empty spaces that look meaningful
- collisions
- blocked continuations
- colors that swap roles across train pairs
- distractors that look like primitive-bait

Core question:
**What was strange before the output made it less strange?**

UNKNOWN ENGINE levels should be treated as pressure fields. The solver should first identify where explanatory tension is concentrated before guessing a rule.

## 6. Temporary concept invention
The solver should invent temporary concepts that are not pre-listed primitives. A concept earns existence only when it reduces strangeness across train examples.

Example temporary concepts:
- orphan-object
- missing-member-of-set
- witness
- blocker
- anchor
- pressure-source
- forbidden-gap
- exception-object
- repair-target
- legal-completion
- symmetry-repair
- contradiction-resolver
- protected-object
- false-member
- unclaimed-region
- object-lacking-counterpart
- expected-but-absent-marker

Concept invention triggers:
- **A. Repeated contrast**
- **B. Role exchange**
- **C. Absence pressure**
- **D. Exception closure**
- **E. Constraint satisfaction**

The point is not to accumulate a large vocabulary. The point is to invent the smallest temporary language that makes the examples feel lawful.

## 7. Role detection instead of color detection
The solver should detect what an object does, not merely what it looks like.

For each candidate object, WESLR should ask:
- What does this object do?
- What relation does it define?
- What changes because it exists?
- What would break if it were removed?
- What remains constant when its color/shape changes?
- Is this object a source, target, anchor, witness, blocker, exception, protected object, or distractor?

Possible roles:
- anchor
- source
- target
- witness
- container
- contained
- blocker
- mover
- moved
- copied
- deleted
- protected
- exception
- decoy
- boundary
- missing counterpart
- symmetry reference
- completion target

Prefer:
`target(x) := unique object inside container`
over:
`target(x) := red object`
unless color truly earns causality.

## 8. Causal vs incidental features
The solver should separate causal features from incidental features through internal counterfactual pressure tests.

Internal intervention questions:
- If color changes but role stays the same, does the rule still work?
- If position shifts but relation stays the same, does the rule still work?
- If object size changes but containment relation stays the same, does the rule still work?
- If a raw visual feature is removed, does the predicted transformation still follow?

Feature buckets:
- causal features
- incidental features
- support features

Penalize grammars that:
- use absolute coordinates unnecessarily
- depend on exact color when relational role explains better
- require one-off constants
- need different logic per train pair
- cannot explain unchanged regions
- cannot explain why distractors were ignored

## 9. Absence, exception, contradiction, and negative evidence
Absence should be treated as first-class, not as nothing.

Absence concepts:
- missing twin
- missing corner
- unfilled slot
- forbidden gap
- empty center
- broken symmetry
- unclaimed region
- expected-but-absent marker
- negative boundary

Negative evidence doctrine:
The solver expected X because pattern P exists. X is absent. The output repairs, marks, mirrors, avoids, or exploits that absence. Therefore absence may be causal.

Exception reasoning:
There is a general pattern. One object violates it. The output acts on the violator. Therefore the exception is not noise; it is the key.

Contradiction reasoning:
Two plausible rules explain different parts. The output resolves the contradiction. Therefore the hidden grammar may be about conflict resolution.

## 10. Detecting wrong representation
A representation is suspicious when:
- it requires many exceptions
- it explains one train pair beautifully but another badly
- it uses raw colors while roles shift across examples
- it cannot explain unchanged objects
- it ignores a visible contradiction
- it cannot explain why distractors are not transformed
- it creates multiple possible outputs with no tie-breaker
- it depends on absolute coordinates without reason
- it needs per-example invented concepts instead of shared concepts
- it compresses poorly

The design should include a **representation pressure** or **representation shame** concept:
- a grammar should feel bad when it explains each example with separate ad hoc reasons
- a grammar should feel good when one compact role-language explains all train pairs

Wrong representation is a primary failure type, not a minor inconvenience.

## 11. Competing interpretations
The solver should maintain a competing grammar arena.

Each candidate micro-theory should include:
- private vocabulary
- object-role assignments
- causal claims
- transformation claims
- absences explained
- exceptions explained
- distractors rejected
- predicted outputs
- confidence / ambiguity
- failure notes

Example rival grammars:
- Grammar A: task is about color replacement
- Grammar B: task is about completing symmetry
- Grammar C: task is about identifying the exception object
- Grammar D: task is about filling the missing member of a relational set

Elimination tests:
- Does it cover all train pairs?
- Does it use the same concepts across examples?
- Does it explain why some objects change and others do not?
- Does it avoid arbitrary constants?
- Does it produce one output, not many?
- Does it survive leave-one-train-pair-out testing?
- Does it explain negative evidence?
- Does it explain ignored distractors?
- Does it compress better than rivals?

## 12. Avoiding overfitting
Anti-overfit laws:
- a micro-language is suspicious if it invents a concept used only once
- suspicious if it names an object instead of defining a role
- suspicious if it memorizes coordinates
- suspicious if it requires more concepts than the level has meaningful structure
- suspicious if it cannot predict what should stay unchanged
- suspicious if it cannot reject distractors
- suspicious if it cannot produce a unique output on test

Good temporary concepts should be:
- reused across train examples
- relationally defined
- small
- predictive
- able to explain non-changes
- able to explain ignored objects
- able to produce deterministic or bounded output

## 13. Compression into inevitability
The scoring idea is not raw fit alone. It is inevitability.

The solver should ask:
**Did the grammar make the train outputs feel forced?**

A grammar has high inevitability when:
- it identifies the same kind of role in every train pair
- it explains changed cells
- it explains unchanged cells
- it explains distractors
- it explains absences
- it has low exception count
- it produces a unique output
- it needs few concepts
- it survives small counterfactual changes

A grammar has low inevitability when:
- many outputs would also fit
- the rule is mostly descriptive
- the transformation is arbitrary
- exceptions do the real work
- the language is larger than the explanation

Conceptual score:

`Inevitability Score = coverage + cross-example role stability + compression + uniqueness of output + negative-evidence explanation + distractor rejection - exception burden - arbitrary constants - concept bloat - coordinate/color overdependence - unresolved rival grammars`

This is a design scoring idea only, not a learned scorer implementation.

## 14. Safe failure
Safe failure modes:

1. **One clear grammar**
   - produce output normally.
2. **Two close grammars, same test output**
   - produce output, but mark internal ambiguity.
3. **Two close grammars, different test outputs**
   - produce ranked candidates or abstain internally.
4. **No compact grammar**
   - fail as `representation_unresolved`, not `search_depth_insufficient`.
5. **Grammar explains train but test parse is unstable**
   - fail as `test_scene_does_not_instantiate_learned_language_cleanly`.

Failure should be diagnostic, for example:
“Solver found multiple possible hidden grammars. Train examples do not disambiguate whether the causal role is containment, symmetry repair, or orphan completion. Prediction unsafe.”

## 15. UNKNOWN ENGINE feedback loop
UNKNOWN ENGINE can force this solver to improve by generating level families that attack representational weakness rather than primitive weakness.

Target families:
- role/color inversion levels
- absence-only causal levels
- exception-as-key levels
- distractor primitive-bait levels
- grammar ambiguity levels
- negative evidence levels
- compression trap levels
- role migration levels
- contradiction-resolution levels
- forbidden-action levels

The point of the loop is not to add more fixed solver tricks. It is to pressure-test whether the temporary language can become compact, stable, and non-ad hoc under stranger conditions.

## 16. Relationship to current WESLR doctrine
This is not a normal program-search solver direction.

Doctrine:
**Understanding begins when the system invents the smallest language in which the unknown case becomes non-strange.**

This aligns with WESLR’s UNKNOWN ENGINE and discovery-preservation doctrine:
- broad search/discovery direction remains allowed
- weird internal representation design is allowed
- no public claims
- no runtime behavior change
- no external benchmark claim
- no ingestion of public ARC/Kaggle data

## 17. Risks and hazards
Key risks:
- micro-language bloat
- false inevitability
- hidden overfitting
- concept invention that becomes arbitrary
- private grammar becoming uninspectable
- apparent intelligence without measurable improvement
- pressure scoring becoming a learned scorer too early
- unsafe public overclaim

The design should stay inspectable, bounded, and reviewable before any implementation attempt.

## 18. What is explicitly not implemented
This document does **not** implement:
- runtime solver
- solver patch
- ChatResponder integration
- provider/model call
- learned scorer
- final-answer generation
- behavior-pack promotion
- public ARC/Kaggle evaluation
- public claim

## 19. Recommended next safe follow-up
Do not implement immediately.

Recommended next artifact:
- `WESLR_MICRO_THEORY_SOLVER_REVIEW_V1.md`

Only later, and only if approved:
- schema candidates for representing temporary micro-languages
- mock train/example traces using synthetic UNKNOWN ENGINE levels only
- no runtime solver patch yet

## 20. Temporary language form flexibility
The temporary language does not need to be a normal human-readable symbolic language. It may take any bounded internal form that makes the level less strange:
- role graph
- constraint system
- private symbols
- compressed trace
- causal map
- counterfactual map
- relation lattice
- pressure field
- object-role assignment table
- executable sketch
- transformation grammar
- absence/exception ledger
- contradiction-resolution structure

The winning representation should be judged by explanatory compactness, cross-example stability, and inevitability, not by how human-readable it looks.

## 21. Summary judgment
This direction is intentionally stranger than ordinary solver extension. It does not ask WESLR to search deeper in the same language. It asks WESLR to invent a smaller temporary language in which the level becomes lawful before any output is trusted.
