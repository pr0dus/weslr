# WESLR Ethics Tradeoff Reasoning Enrichment V1

**Status:** design/doctrine document  
**Date:** 2026-05-10  
**Scope:** General ethics_tradeoff_reasoning enrichment derived from internal public-subset failures  
**Implementation status:** Design and tests only. No runtime behavior changes.

## 1. Purpose

This design defines how WESLR should improve general ethics and tradeoff reasoning from internal public-subset failures without memorizing benchmark items, storing answer keys, or claiming official benchmark performance.

The goal is not to learn the five MMLU business_ethics dev questions. The goal is to treat those failures as evidence that WESLR currently lacks a sufficiently legible, general ethics_tradeoff_reasoning substrate for bounded multiple-choice reasoning.

This design is doctrine-first. It proposes a general, explainable enrichment path only. It does not change runtime behavior yet.

## 2. Gap evidence

Internal public-subset evidence currently shows:

- dataset: MMLU business_ethics dev5
- internal_eval: true
- official_score: false
- no official claim
- accuracy: 0.0
- answered_count: 0
- no_answer_count: 5
- all 5 observed failures were mapped to:
  - missing_skill: ethics_tradeoff_reasoning
  - target_substrate: internal_reasoning_graph_and_governance_surface
  - failure_mode: no_answer_selection

These failures were converted into operator-reviewed enrichment gap records outside the repo. They should be read as evidence of a general missing skill, not as instructions to memorize benchmark items.

## 3. Anti-benchmark-gaming boundary

The following boundary is mandatory:

- do not store answer keys
- do not memorize item text
- do not add item-specific phrase rules
- do not infer official score
- do not infer leaderboard readiness
- use failures only as evidence of a general missing skill
- do not store raw benchmark questions in enrichment records by default
- do not use the five failures to justify benchmark-shaped shortcuts

Internal public-subset failures may guide enrichment design, but they may not become hidden benchmark tuning.

## 4. Explainable tradeoff reasoning rubric

Future ethics_tradeoff_reasoning should use a transparent rubric that can be explained in human terms.

For each question or option set, WESLR should:

1. identify stakeholders
2. identify possible harms
3. identify possible benefits
4. identify duties, rights, and obligations
5. identify evidence boundaries
6. identify authority and governance constraints
7. consider reversibility
8. consider short-term vs long-term effects
9. compare options explicitly
10. choose the best-supported answer
11. state uncertainty when needed

Interpretation guidance:

- **stakeholders** means affected people, groups, institutions, operators, and downstream parties
- **harms** means direct and indirect damage, exploitation, coercion, omission harms, and foreseeable negative externalities
- **benefits** means legitimate gains, protections, welfare improvements, and justified risk reductions
- **duties / rights / obligations** means role duties, fairness constraints, consent boundaries, and protected interests
- **evidence boundaries** means what is supported, what is inferred, and what remains unknown
- **authority / governance** means whether the decision properly belongs to a role, institution, policy, or review gate
- **reversibility** means whether harm can be corrected or whether the decision creates hard-to-undo damage
- **uncertainty** means uncertainty should be stated, not hidden

This rubric is intended to improve general reasoning quality, not just MCQ answer selection.

## 5. MCQ answer-selection method, future implementation only

Future implementation may add a transparent ethics tradeoff scoring method for multiple-choice tasks.

Proposed method:

1. parse question and choices
2. score each choice against the tradeoff rubric
3. prefer options that:
   - acknowledge stakeholders
   - reduce unjustified harm
   - respect duties and rights
   - preserve evidence boundaries
   - avoid absolute or manipulative claims
   - include governance and authority when relevant
4. penalize options that:
   - ignore affected parties
   - justify harm without evidence
   - use absolute language
   - confuse legality with ethics
   - claim certainty without support
   - bypass governance
5. output:
   - `Answer: <label>`
   - `Explanation: <short rubric-based reason>`
   - `Confidence: low/medium/high`

This future method must remain transparent, inspectable, and auditable. It must not become a benchmark-specific phrase matcher.

## 6. Cognitive legibility

Every ethics/tradeoff answer must remain explainable in human terms.

Required boundary:

- no private or internal authority
- no hidden benchmark tuning
- no unteachable scoring logic
- no opaque choice selection mechanism
- reasoning must be teachable
- reasoning must remain operator-inspectable

The Cognitive Legibility Boundary applies fully here. WESLR may enrich internal structure, but the basis for an answer must remain translatable, inspectable, and teachable.

## 7. Target substrate

Primary target substrate:

- internal_reasoning_graph_and_governance_surface

Secondary supporting substrates:

- capability taxonomy
- evidence calibration
- MCQ adapter formatting only after explicit approval

The primary enrichment target is not a new graph. The first move is to enrich the existing internal reasoning graph and governance surface with a clearer ethics tradeoff rubric and related gap/proposal structure.

## 8. Future implementation steps

Staged future implementation:

### A. Add taxonomy and rubric data only

Add explicit ethics_tradeoff_reasoning rubric structure and taxonomy entries without changing runtime behavior.

### B. Add ethics tradeoff scoring helper

Implement a general scoring helper that evaluates options against stakeholders, harms, benefits, duties, rights, evidence boundaries, authority, governance, reversibility, and uncertainty.

### C. Add MCQ formatter integration for ethics_tradeoff_reasoning

Only after approval, connect the scoring helper to MCQ formatting flow in a transparent way.

### D. Run internal public subset again

Re-run the internal business_ethics public subset and compare answered_count, no_answer_selection failures, and explanation quality.

### E. Convert remaining failures to enrichment gaps

Any remaining failures should become additional gap records rather than prompt-specific patches.

### F. Do not claim official score

Even if internal public-subset performance improves, WESLR must not claim official score, leaderboard-level benchmark performance, or benchmark passage.

## 9. Required tests before implementation

Before any runtime implementation, add and pass:

- rubric unit tests
- MCQ choice scoring tests
- anti-memorization tests
- no raw benchmark question storage tests
- no official score claim tests
- before/after internal public-subset result comparison
- failure-to-gap bridge remains intact tests

These tests are required because the enrichment must remain general, auditable, and non-gaming.

## 10. Success criteria

Success does **not** mean official score.

Success means:

- higher answered_count on the internal business_ethics subset
- fewer no_answer_selection failures
- explanations are rubric-based
- no answer-key memorization
- official_score remains false
- failure records remain operator-reviewed
- governance and evidence boundaries stay explicit
- enrichment remains teachable and inspectable

This design makes no benchmark-passage claim. It proposes a general ethics_tradeoff_reasoning enrichment path only.
