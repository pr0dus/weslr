# WESLR ARC Synthetic Task Difficulty Ladder — Design (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_ARC_SYNTHETIC_TASK_DIFFICULTY_LADDER_V1`
**Start HEAD**: `8c9b1e2617da40329352038ec929bed12130fa95`
**Actual preflight HEAD**: `8c9b1e2617da40329352038ec929bed12130fa95`
**End HEAD**: `8c9b1e2617da40329352038ec929bed12130fa95`
**Commit**: no
**Date**: 2026-07-02

## 1) Goal

Design the task-side equivalent of the primitive capability ladder.

Primitive-side discovery asks: *what can a primitive do?*
Task-side difficulty asks: *what kind of reasoning pressure does a task impose?*

The ladder below separates:
- clear primitive regression,
- short composition,
- ambiguity resolution,
- unseen composition,
- primitive insufficiency,
- transfer across surfaces,
- and confidence-aware unresolved tasks.

## 2) Level definitions

### T1 — Primitive-isolation task
**Purpose**
- Test one clear rule.
- Useful for primitive recognition and regression.

**Task signature**
- One latent operation.
- One dominant object/action relation.
- Minimal ambiguity.
- Usually one-step or one primitive-affine chain.

**Required metadata**
- `level_id: T1`
- `rule_type`
- `primary_object_scope`
- `expected_transform`
- `ambiguity_axes: []`
- `confidence_policy: exact`

**Example family**
- Fill hole
- Mirror object
- Select leftmost
- Swap colors

**Expected solver behavior**
- Exact solve from a known primitive or near-direct regression.

**Expected failure mode**
- Overfitting only if the task is not actually isolated.

**Anti-cheat controls**
- No task-id shortcut.
- No primitive-name leakage.
- No sequence leakage.
- No no-op task.
- No single-template repetition.
- No metadata-only solving.

**Promotion criteria**
- Stable across small perturbations and safe as a regression fixture.

---

### T2 — Short-composition task
**Purpose**
- Chain 2–3 known operations.
- Test basic composition and parameter carryover.

**Task signature**
- Two or three known primitives.
- Deterministic order matters.
- Intermediate state must be preserved.

**Required metadata**
- `level_id: T2`
- `primitive_chain_length`
- `ordered_operations`
- `intermediate_state_required: true`
- `confidence_policy: exact`

**Example family**
- Select object → recolor → move
- Extract → invert → place back

**Expected solver behavior**
- Execute a known chain exactly.

**Expected failure mode**
- Order confusion, carryover drift, or chain truncation.

**Anti-cheat controls**
- No sequence leakage.
- No output-template leakage.
- No duplicate surface reuse as a disguised copy task.

**Promotion criteria**
- Becomes scored/regression when the chain is stable and not overly templated.

---

### T3 — Rival-grammar / ambiguous task
**Purpose**
- Distinguish between several plausible rules.
- More important than adding more steps.

**Task signature**
- Multiple grammars fit the visible examples.
- The task must disambiguate via structure, not labels.
- Examples may support largest vs leftmost vs border-touching vs hole-object, etc.

**Required metadata**
- `level_id: T3`
- `rival_grammars`
- `ambiguity_axes`
- `separating_examples`
- `confidence_policy: resolve_or_flag`

**Example family**
- Largest vs leftmost vs border-touching vs hole-object selection.

**Expected solver behavior**
- Resolve confidently if evidence is sufficient.
- Otherwise mark unresolved rather than hallucinate.

**Expected failure mode**
- Shallow heuristic / one-feature heuristic / wrong tie-break rule.

**Anti-cheat controls**
- Require separating examples.
- No tie-breaker leakage.
- No “easy clue” metadata.
- No overfriendly distractors.

**Promotion criteria**
- Moves into hard-mode/scored only when the ambiguity is genuine but resolvable and stable under perturbation.

---

### T4 — Unseen-composition task
**Purpose**
- Use known primitives in a new combination/order/scene type.
- Test generalization of composition rather than memorization.

**Task signature**
- Known primitives.
- Novel order or novel scene form.
- Requires adaptation to a new composition graph.

**Required metadata**
- `level_id: T4`
- `known_primitives`
- `novel_order`
- `novel_scene_form`
- `composition_graph`
- `confidence_policy: exact_if_generalized`

**Example family**
- Select → recolor → move on diagonal-pressure scenes.

**Expected solver behavior**
- Generalize the composition, not just replay a memorized chain.

**Expected failure mode**
- Chain memorization, order fragility, or parameter transfer failure.

**Anti-cheat controls**
- No exact training-chain repetition.
- Variants must change shapes, distractors, or grid geometry.
- No surface copy-paste from prior tasks.

**Promotion criteria**
- Becomes scored when the composition is clearly new but still supported by existing primitives.

---

### T5 — Primitive-insufficiency task
**Purpose**
- Detect when existing primitives or short compositions do not cleanly explain the task.
- Correct response is often: existing primitives insufficient; candidate new primitive needed.

**Task signature**
- No existing primitive chain cleanly covers the rule.
- The nearest known primitives should fail in a separable way.
- Separating examples are mandatory.

**Required metadata**
- `level_id: T5`
- `nearest_primitive_set`
- `separating_examples`
- `candidate_primitive_hint`
- `duplicate_risk`
- `confidence_policy: insufficient_language`

**Example family**
- Construction, merging, edge-clip, gap-split, or other frontier behaviors.

**Expected solver behavior**
- Say “existing primitives insufficient” or similar.
- Do not force a fake exact solve.

**Expected failure mode**
- Overclaiming a solve from the nearest primitive.

**Anti-cheat controls**
- Candidate probes must never count as solved.
- No nearest-neighbor shortcut.
- No primitive-name leakage.
- No claim that an unsupported frontier task is a regression win.

**Promotion criteria**
- Repeated separating evidence + review can create a candidate primitive.

---

### T6 — Transfer-family task
**Purpose**
- Prove the same latent rule transfers across changed surfaces.

**Task signature**
- Same rule across changes in colors, grid size, shape, distractor density, object count, diagonal pressure, or same-color components.
- The family anchor stays the same while surfaces change.

**Required metadata**
- `level_id: T6`
- `family_anchor`
- `variant_axes`
- `invariants`
- `surface_transfer_budget`
- `confidence_policy: exact_across_variants`

**Example family**
- The same selection or topology rule across color-shifted, size-shifted, and distractor-heavy variants.

**Expected solver behavior**
- Transfer robustly across all surfaced variants.

**Expected failure mode**
- Template lock, color overfit, size overfit, or distractor blindness.

**Anti-cheat controls**
- At least 3 distinct surface variants.
- No single-template repetition.
- No “same task, new color only” padding.

**Promotion criteria**
- Becomes regression/scored only after multi-surface proof of the same latent rule.

---

### T7 — Self-calibrating / underdetermined task
**Purpose**
- Force confidence tracking.
- Distinguish confident solve, low-confidence solve, underdetermined, rival grammar unresolved, existing language insufficient, and needs more examples.

**Task signature**
- Evidence may be insufficient by design.
- The task can be legitimately unresolved.
- Confidence is part of the contract.

**Required metadata**
- `level_id: T7`
- `confidence_band`
- `resolution_status`
- `rival_grammar_set`
- `more_examples_needed`
- `abstain_policy`

**Example family**
- Minimal ambiguous scenes with insufficient evidence.

**Expected solver behavior**
- Return unresolved or low-confidence when appropriate.
- Do not force a binary pass/fail guess.

**Expected failure mode**
- Overconfident solve.

**Anti-cheat controls**
- The schema must allow unresolved as a valid output.
- No forced binary labeling.
- No metadata-only solve by inspection.

**Promotion criteria**
- Becomes hard-mode only when unresolved states are first-class and reviewable.

## 3) Current WESLR mapping

### Current known state
- Clean base: `130/130`
- Hard-mode: `19/30 exact, 0 failed, 11 unsupported`
- Current candidate probes: `10`
- Active low-duplicate unsupported frontier candidates: `7` (`T140_134`–`T140_140`)
- High-duplicate sentinels: `3` (`T120_101`, `T120_102`, `T120_107`)

### Ladder mapping

| Current WESLR asset | Ladder level(s) | Notes |
|---|---|---|
| BH80 base + clean 130/130 regression | T1, T2 | Strong regression and short-composition coverage. |
| Hard-mode supported exacts | T2, T3, T4 | Some ambiguity and unseen-composition pressure, but still largely short-chain. |
| Hard-mode unsupported 11 | T5 | Frontier insufficiency signal; these are unsupported, not solved. |
| Current 10 candidate probes | T5 | 7 active low-duplicate frontier candidates + 3 high-duplicate sentinels. |
| 7 active low-duplicate unsupported frontier candidates | T5 | `T140_134`–`T140_140`. |
| 3 high-duplicate sentinels | T5 sentinel-only | `T120_101`, `T120_102`, `T120_107`. |
| Formal transfer families | T6 | Under-covered / not yet a formal lane. |
| Confidence-aware unresolved tasks | T7 | Not yet a formal lane. |

### Under-covered levels
- Most under-covered: `T6`, `T7`
- Also under-covered: formal `T3` ambiguity tasks and formal `T4` unseen-composition tasks
- Well covered already: `T1`, `T2`
- Frontier-covered but not yet formalized: `T5`

## 4) Coverage metrics

### Current task-side coverage snapshot

| Level | Current tasks known | Scored | Hard-mode | Probes / sentinels | Coverage note |
|---|---:|---:|---:|---:|---|
| T1 | High volume in clean regression base | 130-base dominates | 0 formal hard-mode | 0 | Well covered |
| T2 | Many clean short compositions | 130-base dominates | 19 exact hard-mode supported-chain tasks partly overlap | 0 | Well covered |
| T3 | Few explicit formal tasks | some implicit in hard-mode | some supported hard-mode pressure | 0 | Under-covered |
| T4 | Few explicit formal tasks | some implicit in hard-mode | some supported hard-mode pressure | 0 | Under-covered |
| T5 | Frontier-only | 0 | 11 unsupported hard-mode + 10 candidate probes | 10 total probes | Covered at frontier, not yet formalized |
| T6 | 0 formal tasks | 0 | 0 | 0 | Under-covered |
| T7 | 0 formal tasks | 0 | 0 | 0 | Most under-covered |

### Scoring split
- Scored: strong on T1/T2
- Hard-mode: pressure-bearing T3/T4 and T5 frontier
- Probes/sentinels: explicit T5 boundary controls
- Unsupported frontier: 11 tasks, preserved as unsupported

## 5) Advancement rules

### When a T1 task becomes regression
- The rule is isolated.
- No ambiguity remains.
- The task is stable under small scene perturbations.

### When a T2 task becomes hard-mode
- The chain is known but the scene now introduces enough distractor/symmetry/topology pressure that a direct replay is no longer enough.

### When a T3 ambiguity task becomes scored
- The task has a real ambiguity axis.
- Separating examples exist.
- The solver can resolve or safely flag unresolved.

### When a T5 insufficiency task creates a primitive candidate
- Nearest existing primitives fail repeatedly in a separable way.
- A candidate primitive explains the pattern better than any short existing chain.
- Duplicate-risk review is passed.

### When a T6 transfer family proves generalization
- The same latent rule succeeds across multiple surface variants.
- The task remains the same rule under color/shape/grid/distractor changes.

### When a T7 task should be marked unresolved
- If the visible evidence is genuinely insufficient.
- If multiple grammars remain plausible.
- If confidence is low and no separating example resolves it.
- Unresolved is not a failure; it is the correct outcome.

## 6) Task-level anti-cheat controls

Global controls for all levels:
- No task-id shortcut.
- No primitive-name leakage.
- No sequence leakage.
- No no-op task.
- No single-template repetition.
- No metadata-only solving.
- Candidate probes never count as solved.
- No overfriendly examples.

Level-specific controls:
- **T1/T2**: keep examples minimal but not trivialized by metadata hints.
- **T3**: require separating examples and explicit ambiguity axes.
- **T4**: force novel order/surface changes.
- **T5**: keep `can_be_counted_as_solved: false` and require candidate-review metadata.
- **T6**: vary at least 3 surface axes.
- **T7**: require a valid unresolved output state.

## 7) Recommended next lane

Recommended next lane:
- `IMPLEMENT_ARC_SYNTHETIC_TASK_DIFFICULTY_LADDER_SCHEMA_V1`

Why:
- The ladder is now defined.
- The next useful step is to encode it as schema before building a cartographer or hard-mode v2.
- TaskContract can follow the ladder schema.

## 8) Receipt

- Start HEAD: `8c9b1e2617da40329352038ec929bed12130fa95`
- End HEAD: `8c9b1e2617da40329352038ec929bed12130fa95`
- Commit: no
- actual preflight HEAD: `8c9b1e2617da40329352038ec929bed12130fa95`
- T1–T7 levels defined: yes
- task signatures defined: yes
- expected solver behavior defined: yes
- failure modes defined: yes
- anti-cheat controls defined: yes
- current WESLR state mapped onto ladder: yes
- under-covered levels identified: yes
- next lane recommended: `IMPLEMENT_ARC_SYNTHETIC_TASK_DIFFICULTY_LADDER_SCHEMA_V1`
- validation: PASS
- push avoided: yes
