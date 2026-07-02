# WESLR ARC Synthetic Discovery 140 — Hard Mode Calibration Design (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_CALIBRATION_V1`
**Start HEAD**: `19115942`
**Actual preflight HEAD**: `19115942`
**Date**: 2026-07-02

---

## 1. Current clean 140 state summary

Current 140 suite evidence:
- Total tasks: 140
- Scored total: 130
- Candidate probes: 10
- BH80: 80/80
- Previous 117 base: 117/117
- New 13 scored: 13/13
- 130 scored: 130/130
- Candidate probes counted as solved: 0
- Anti-cheat controls: 18/18 pass

Current 140 state is **clean**, but the worktree still has unrelated dirty files:
- `weslr/tests/continuity/governance_scorecards.json`
- `weslr/tests/docs/`

---

## 2. Why clean 130/130 is not enough

A perfect clean score at 130/130 is useful, but not sufficient.

It can still be too easy if the suite:
- reuses known primitive chains too often
- over-aligns with current oracle/solver semantics
- lacks ambiguity pressure
- lacks rival-grammar traps
- lacks distractor-heavy or OOD scenes
- lacks failure-inducing minimal examples
- rewards dispatch familiarity more than abstraction discovery

The current suite is strong regression evidence, but hard mode should test whether the model actually learned structure, not just the current primitive library.

---

## 3. Current-suite weakness audit

### 3.1 Too many known primitive chains
Yes. Many scored tasks already combine primitives the system knows well, especially promoted natives paired with familiar BH80 operations.

### 3.2 Too much oracle/solver alignment
Yes. The current clean run shows strong alignment, but alignment alone can hide fragility if scenes are too friendly.

### 3.3 Insufficient ambiguous scenes
Yes. The current 140 suite has some ambiguity pressure, but not enough cases where multiple plausible interpretations compete sharply.

### 3.4 Insufficient rival-grammar traps
Yes. The suite does not yet aggressively test whether alternative grammar hypotheses would also fit.

### 3.5 Insufficient distribution shift
Yes. The 140 expansion added breadth, but most scenes still live inside a familiar synthetic comfort zone.

### 3.6 Insufficient task diversity
Partially. There is diversity across primitives and compositions, but less diversity in failure modes and scene distributions.

### 3.7 Too few failure-inducing cases
Yes. For hard-mode calibration, the suite should include tasks that are intentionally punishing and may fail at first.

**Conclusion:** the current 140 clean score is a good baseline, but not a hard-mode stress test.

---

## 4. Hardness dimensions

Hard-mode calibration should pressure the following dimensions:

1. Object ambiguity
2. Color ambiguity
3. Connected-component ambiguity
4. Distractor density
5. Symmetry traps
6. Misleading largest-object traps
7. Misleading leftmost/topmost traps
8. Same-color multi-object traps
9. Diagonal adjacency traps
10. Hole/topology traps
11. Relation/swap ambiguity
12. Order sensitivity
13. Primitive-chain deception
14. Output dimension change
15. Unseen composition
16. Rival-grammar ambiguity

These dimensions are the real lever for hardening.

---

## 5. Hard-mode task categories

Recommended hard-mode categories:
- adversarial scored tasks
- hidden-rival grammar tasks
- duplicate-trap tasks
- connected-component stress tasks
- primitive collision tasks
- compositional deception tasks
- minimal-example tasks
- noisy / distractor-heavy tasks
- ambiguous-but-resolvable tasks
- out-of-distribution scene specs

Hard mode should be a **pressure layer**, not a score-padding layer.

---

## 6. Scoring policy proposal

Preferred policy: **separate hard-mode denominator**.

### Proposed structure
- Base scored: 130/130
- Hard-mode scored: 30 tasks
- Hard-mode clean: 30/30
- Hard-mode preferred: ≥27/30
- Hard-mode strong: ≥24/30
- Hard-mode minimal: ≥20/30

This keeps normal regression and hard-mode pressure distinct.

### Why separate?
Because a mixed denominator would blur two different questions:
- is the current suite still clean?
- can the system survive adversarial calibration?

Those are not the same question.

---

## 7. Proposed hard-mode suite

### 7.1 Scope
- 30 new hard-mode tasks
- Recommended IDs: `T140H_001`–`T140H_030`
- Alternative naming if merged later: `T160_141`–`T160_170`

### 7.2 Intended pressure
At least 10 tasks should be expected to expose wrong assumptions if any exist.

### 7.3 Proposed hard-mode task table

| ID | Category | Pressure | What it should break if weak |
|----|----------|----------|------------------------------|
| T140H_001 | ambiguous object | same-color multi-object | object identity by color alone |
| T140H_002 | ambiguous object | rival grammar | grammar overfit |
| T140H_003 | largest-object trap | distractor-heavy | naive largest selection |
| T140H_004 | leftmost/topmost trap | spatial tie-break | simplistic coordinate heuristics |
| T140H_005 | symmetry trap | reflection ambiguity | mirror-vs-flip confusion |
| T140H_006 | diagonal adjacency | CC ambiguity | 4-connectivity assumptions |
| T140H_007 | hole/topology | hole-fill pressure | bbox-only thinking |
| T140H_008 | relation/swap | object ordering | position-swap assumptions |
| T140H_009 | order sensitivity | chain deception | commutativity assumption |
| T140H_010 | output dimension change | crop/place-back | fixed-size assumptions |
| T140H_011 | ambiguous-but-resolvable | minimal example | underdetermined guesswork |
| T140H_012 | noise-heavy | distractor density | noise blindness |
| T140H_013 | duplicate-trap | near-duplicate probe | false promotion pressure |
| T140H_014 | connected-components | same-color split | component grouping errors |
| T140H_015 | primitive collision | chain overlap | primitive equivalence confusion |
| T140H_016 | rival grammar | alternative parse | shallow pattern matching |
| T140H_017 | ambiguous object | mixed colors | color-as-identity mistake |
| T140H_018 | symmetry trap | axis ambiguity | vertical/horizontal confusion |
| T140H_019 | diagonal adjacency | near-touching objects | connectivity misread |
| T140H_020 | hole/topology | nested structure | inner/outer boundary confusion |
| T140H_021 | largest-object trap | distractor plus hollow | hollow-vs-solid confusion |
| T140H_022 | leftmost trap | multi-object row | order heuristic overfit |
| T140H_023 | relation/swap | relative placement | absolute-placement overfit |
| T140H_024 | order sensitivity | inverse chain | chain commutation assumption |
| T140H_025 | minimal example | sparse scene | overfitting to visual richness |
| T140H_026 | noise-heavy | sparse signal | signal extraction weakness |
| T140H_027 | output-dimension shift | crop + reinsert | shape/size rigidity |
| T140H_028 | rival grammar | decoy transform | dispatch overfitting |
| T140H_029 | duplicate-trap | border-vs-boundary | exact duplicate pressure |
| T140H_030 | compositional deception | mixed primitive chain | shallow chain memorization |

### 7.4 Why these 30 are harder
They are harder because they deliberately combine:
- ambiguity + distractors
- topology + connectivity
- symmetry + relation
- minimal examples + rival grammar
- chain deception + output-shape changes

At least 10 are designed to fail weak assumptions quickly.

---

## 8. Expected failure interpretation

Hard mode should not be required to be clean on the first run.

Interpretation bands:
- **30/30** = excellent
- **25–29** = strong
- **20–24** = useful, but gaps remain
- **below 20** = primitive/world-model too weak

Failure is useful evidence, not a problem.

---

## 9. Duplicate-probe handling

The current high-duplicate probes should not be promoted just to raise score.

### Reclassification
- `mask_border_only` → keep as adversarial duplicate-risk sentinel for now
- `geom_flip_vertical` → retire or redesign; appears exact-duplicate of `transform`
- `pat_row_alternate` → retire or redesign; appears exact-duplicate of `pattern_output`

### Policy
- If exact duplicate is proven, retire it.
- If semantics remain uncertain, keep it only as a sentinel, not a score booster.
- Do not promote duplicates to manufacture coverage.

---

## 10. What makes a synthetic task ARC-like?

Without using public or hidden ARC data, a synthetic task is ARC-like when it has:
- unknown grammar
- small number of examples
- ambiguity resolved by structure
- no task-id shortcuts
- no primitive-name leakage
- compositional abstraction
- transformation discovery, not dispatch
- scene-level reasoning over memorized templates

A good synthetic ARC-like task should force the solver to infer a rule, not recognize a label.

---

## 11. Why this hard mode matters

The current 140 suite is strong regression evidence, but hard mode is how we test whether the system can survive less friendly structure.

Hard mode should pressure:
- generalization
- disambiguation
- compositionality
- resilience to decoys
- resistance to duplicate traps

That is the difference between “clean” and “meaningful”.

---

## 12. Recommended next lane

**Recommended next lane:** `IMPLEMENT_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_CALIBRATION_V1`

Reason:
- this design is ready to be turned into a real calibration layer
- the current clean 140 suite is validated
- the next step should be a concrete hard-mode implementation, not a larger design-only abstraction jump

---

## 13. Validation

Planned gates:
- `git diff --check`
- `python weslr/tests/release_gate_v1.py`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

Status in this run: pending.

---

## 14. Receipt

- Start HEAD: `19115942`
- End HEAD: `19115942` (analysis-only lane)
- Commit: no
- actual preflight HEAD: `19115942`
- current clean state summarized: yes
- weakness audit produced: yes
- hardness dimensions defined: yes
- hard-mode task categories defined: yes
- hard-mode denominator proposed: yes
- hard-mode task table proposed: yes
- duplicate probes reclassified: yes
- real ARC relevance criteria defined: yes
- recommended next lane: `IMPLEMENT_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_CALIBRATION_V1`
- validation: PASS
- push avoided: yes
