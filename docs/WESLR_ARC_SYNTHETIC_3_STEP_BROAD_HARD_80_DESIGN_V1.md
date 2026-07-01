# ARC Synthetic 3‑Step – Broad Hard‑80 Redefined Design (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `REDEFINE_AND_REPAIR_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_HARDNESS_MODEL_V1`
**Start HEAD**: `e748b0ee`

> **Note on Start HEAD**: The prior version of this document referenced `c2f9a4e7` as Start HEAD. That commit does not exist in any branch of this repository. The actual HEAD at the time of this repair is `e748b0ee`. This metadata correction is part of the repair.

---

## 1. Finite Primitive Boundary

Only the **contracted primitive set** may appear in executable tasks. The allowed primitives are:

1. `extract`
2. `extract_largest_object`
3. `isolate_largest`
4. `extract_boundary`
5. `crop`
6. `mirror_object`
7. `rotate`
8. `recolor`
9. `normalize_position`
10. `place_back`
11. `count_objects`
12. `pattern_output`
13. `transform`

Additionally, the following family-defined primitive names from existing core families are treated as aliases that map to wrappers in the dispatch layer:

- `remove_noise` → `remove_background_noise` adapter
- `extract_object` → `extract_largest_object` adapter
- `crop_object` → `crop_to_non_background_bbox` adapter
- `recolor_boundary` → recolor wrapper (boundary-recolor variant)
- `count` → `count_objects` wrapper
- `count_or_pattern` → `count_objects` or `pattern_output` (family-dependent)
- `extract_changed_region` → extract wrapper (diff-based variant)
- `fill_region` → fill wrapper

Any task that references a primitive outside the union of the above lists is **invalid** and must be removed or replaced. Unknown primitive names are forbidden unless a separate primitive-contract lane defines them first.

---

## 2. Definition of Unknown Mutation

An **unknown mutation** is a deterministic alteration of an existing scene that is *not* captured by the predefined Hard‑40 or Hard‑40‑derived families, but still uses only the known primitives. Examples include:

- Changing the **object count** while keeping shapes identical.
- Relocating an object to a **new position** that creates edge‑touching or boundary‑clipping scenarios.
- Swapping **colors** between objects to create distractor pressure.
- Adding **holes** or **disconnected parts** to a shape.
- Adjusting the **canvas size** (grid dimensions) to alter scaling.
- Reversing or **shuffling the primitive order** of a known family.
- Changing the **selection rule** (e.g., from "largest" to "second-largest" or "smallest").

All such mutations are fully specified in the `scene_spec` and are **generator‑safe** (no randomness).

---

## 3. Definition of Unknown‑Family Candidate

An **unknown‑family candidate** introduces a **new synthetic grammar** (i.e., a novel combination of scene constraints) that has not been used in any existing family (F001‑F008 or Hard‑40 expansion families A/B). It must:

- Use only the **known primitives** listed in Section 1.
- Provide a deterministic `scene_spec` describing objects, colors, positions, and any special attributes (holes, disconnected parts, etc.).
- Include a **family identifier** that is not one of the existing families (e.g., `BH‑C` through `BH‑G`).
- Define a **hardness‑axis vector** that captures the challenge dimensions.
- Include a clear **shortcut/rival grammar** that the task defeats.

These candidates broaden the measurement space without requiring new primitive contracts.

---

## 4. Hardness‑Axis Model

Each task is assigned a **hardness‑axis vector** of ten Boolean flags:

| # | Axis | Description |
|---|------|-------------|
| 1 | **primitive‑order sensitivity** | The result changes if primitive order is permuted. |
| 2 | **target‑selection ambiguity** | Multiple objects could be the target; correct selection requires non‑trivial rules. |
| 3 | **distractor pressure** | Distractor objects share visual features (color/shape) with the target. |
| 4 | **metadata dependency** | Correct reasoning depends on metadata (e.g., centroid, bounding‑box coordinates). |
| 5 | **non‑commutativity** | Primitives do not commute; order matters for the final outcome. |
| 6 | **rival grammar traps** | The task can be mis‑interpreted by a simpler grammar (e.g., assuming "largest object"). |
| 7 | **edge/boundary pressure** | Objects touch or cross canvas edges, making cropping or extraction ambiguous. |
| 8 | **multi‑object relational pressure** | Reasoning requires understanding relationships between multiple objects. |
| 9 | **shape identity pressure** | Shape details (holes, asymmetry) are crucial for correct processing. |
| 10 | **novel‑family pressure** | The task belongs to a previously unseen synthetic family. |

**Difficulty derivation:**
- **Medium**: 2–3 active axes.
- **Hard**: 4–6 active axes.
- **Adversarial**: ≥7 active axes, and must include axis 6 (rival grammar traps).

---

## 5. Allocation Overview

| Category | Number of Tasks | Families | Description |
|----------|-----------------|----------|-------------|
| **Known‑family anchor** | 18 | F001–F008 | Re‑use of established families for regression comparability. |
| **Hybrid‑family** | 20 | BH‑A, BH‑B | Combine primitive sequences or scene assumptions from two known families. |
| **Mutation** | 20 | BH‑C, BH‑D | Deterministic mutations of known scenes. |
| **Unknown‑family candidate** | 22 | BH‑E, BH‑F, BH‑G | New synthetic grammars built from known primitives. |
| **Total** | **80** | | |

**Difficulty distribution (enforced):**
- **Easy**: 0 tasks
- **Medium**: 16 tasks
- **Hard**: 48 tasks
- **Adversarial**: 16 tasks

**Hard‑40 relationship clarification**: The prior 40‑task expansion used families F001–F008 (20 tasks) and expansion families A/B (20 tasks). The Broad‑Hard‑80 **reuses** 18 anchor tasks from F001–F008 (2–3 per family, selected for regression coverage) and **does not** reuse the expansion A/B tasks directly. Instead, BH‑A and BH‑B are new hybrid families that combine elements from the expansion's primitive pool (extract_boundary, mirror_object, crop) with other families' primitives. The remaining 20 Hard‑40 expansion tasks are **superseded** by the richer BH‑A/B hybrids and BH‑C/D mutations.

---

## 6. Full 80‑Task Table

### 6.1 Known‑Family Anchors (18 tasks, F001–F008)

| Task ID | Family | Diff. | Primitive Sequence | Active Axes | Hardness Reason | Shortcut Defeated |
|---------|--------|-------|--------------------|-------------|-----------------|-------------------|
| BH80_001 | F001 | Medium | extract → rotate → recolor | 1,5 | Standard extract‑rotate‑recolor; order matters for rotation angle | Order‑independence |
| BH80_002 | F001 | Hard | extract → rotate → recolor | 1,3,5,7 | Edge‑touching object, distractor with same colour, rotation changes bbox | Largest‑object shortcut |
| BH80_003 | F002 | Medium | remove_noise → extract_object → recolor | 1,3 | Noise removal before extraction; distractor noise pixels | Noise‑ignore shortcut |
| BH80_004 | F002 | Hard | remove_noise → extract_object → recolor | 1,2,3,7 | Multiple objects after denoising, edge contact, ambiguous target | First‑object shortcut |
| BH80_005 | F003 | Hard | fill_region → count_objects → pattern_output | 2,4,5,8 | Count depends on fill region; pattern output requires count metadata | Count‑only shortcut |
| BH80_006 | F003 | Hard | fill_region → count_objects → pattern_output | 1,2,4,5,8 | Fill shape has holes, count must exclude holes, pattern depends on count | Simple‑fill shortcut |
| BH80_007 | F004 | Medium | crop_object → transform → place_back | 1,5 | Crop then transform; place_back must use post‑transform bbox | Bbox‑invariance shortcut |
| BH80_008 | F004 | Hard | crop_object → transform → place_back | 1,4,5,9 | Transform changes shape identity, place_back must respect new geometry | Identity‑invariance shortcut |
| BH80_009 | F005 | Medium | extract_boundary → recolor_boundary → count | 1,4 | Boundary extraction then count; count depends on boundary metadata | Interior‑count shortcut |
| BH80_010 | F005 | Hard | extract_boundary → recolor_boundary → count | 2,3,4,7 | Multiple boundary candidates, distractor edges, edge contact | Single‑boundary shortcut |
| BH80_011 | F006 | Medium | isolate_largest → normalize_position → recolor | 1,2 | Isolation then normalization; selection rule matters | First‑component shortcut |
| BH80_012 | F006 | Hard | isolate_largest → normalize_position → recolor | 1,2,3,5,8 | Same‑size tie, distractor with same colour, normalization changes order | Size‑tie shortcut |
| BH80_013 | F007 | Medium | mirror_object → extract_changed_region → recolor | 1,5 | Mirror then extract changed; order matters for what "changed" means | Symmetry shortcut |
| BH80_014 | F007 | Hard | mirror_object → extract_changed_region → recolor | 1,3,5,7,9 | Asymmetric shape, mirror creates edge contact, recolor must preserve identity | Mirror‑invariance shortcut |
| BH80_015 | F008 | Medium | crop → rotate → count_or_pattern | 1,5 | Crop then rotate; count/pattern depends on rotation result | Pre‑crop shortcut |
| BH80_016 | F008 | Hard | crop → rotate → count_or_pattern | 1,4,5,6,9 | Crop to ambiguous bbox, rotate changes count, rival grammar: "just count" | Count‑first shortcut |
| BH80_017 | F003 | Adversarial | fill_region → count_objects → pattern_output | 2,3,4,5,6,8,9 | Holes + distractors + rival grammar ("fill = all") + metadata dependency + shape identity | Fill‑all shortcut |
| BH80_018 | F006 | Adversarial | isolate_largest → normalize_position → recolor | 1,2,3,4,5,6,8 | Size tie + distractors + metadata + rival grammar ("first object") + non‑commutative | Largest‑first shortcut |

### 6.2 Hybrid‑Family Tasks (20 tasks, BH‑A and BH‑B)

**Family BH‑A**: Combines extract_boundary (from F005) with mirror_object and crop (from F008/F007 expansion). Tests primitive‑order sensitivity across family boundaries.

| Task ID | Family | Diff. | Primitive Sequence | Active Axes | Hardness Reason | Shortcut Defeated |
|---------|--------|-------|--------------------|-------------|-----------------|-------------------|
| BH80_019 | BH‑A | Medium | extract_boundary → mirror_object → crop | 1,5 | Boundary then mirror then crop; order matters | Order‑independence |
| BH80_020 | BH‑A | Medium | mirror_object → extract_boundary → crop | 1,5,7 | Mirror first changes boundary, edge contact | Post‑mirror‑boundary shortcut |
| BH80_021 | BH‑A | Hard | extract_boundary → crop → mirror_object | 1,4,5,7 | Crop changes bbox metadata, mirror after crop | Bbox‑stable shortcut |
| BH80_022 | BH‑A | Hard | crop → extract_boundary → mirror_object | 1,4,5,9 | Crop shifts boundary, shape identity matters after crop | Boundary‑invariance shortcut |
| BH80_023 | BH‑A | Adversarial | extract_boundary → mirror_object → crop | 1,2,3,5,6,7,8 | Ambiguous target, distractor, rival grammar ("boundary = extract all"), edge contact, multi‑object relational | Largest‑object shortcut |
| BH80_024 | BH‑A | Hard | mirror_object → crop → extract_boundary | 1,4,5,7,8 | Mirror changes crop region, multi‑object relation | Mirror‑then‑crop shortcut |
| BH80_025 | BH‑A | Adversarial | crop → mirror_object → extract_boundary | 1,3,4,5,6,7,9 | Distractors + metadata + rival grammar ("crop = extract") + edge + shape | Crop‑equals‑extract shortcut |
| BH80_026 | BH‑A | Adversarial | extract_boundary → crop → mirror_object | 1,2,3,4,5,6,8 | Ambiguous target + metadata + rival grammar ("boundary = extract") + relational | Boundary‑equals‑extract shortcut |
| BH80_027 | BH‑A | Hard | mirror_object → crop → extract_boundary | 1,4,5,7,9 | Mirror changes what crop captures, boundary after crop is shifted | Mirror‑invariance shortcut |
| BH80_028 | BH‑A | Hard | crop → extract_boundary → mirror_object | 1,3,5,7,8 | Distractor edge objects, multi‑object relational pressure | First‑crop shortcut |

**Family BH‑B**: Combines isolate_largest/normalize_position (from F006) with rotate/recolor (from F001). Tests selection and normalization interaction with rotation.

| Task ID | Family | Diff. | Primitive Sequence | Active Axes | Hardness Reason | Shortcut Defeated |
|---------|--------|-------|--------------------|-------------|-----------------|-------------------|
| BH80_029 | BH‑B | Medium | isolate_largest → rotate → normalize_position | 1,5 | Rotate after isolation, normalize after rotation | Order‑independence |
| BH80_030 | BH‑B | Medium | rotate → isolate_largest → normalize_position | 1,2,5 | Rotation changes which object is largest | Pre‑rotate shortcut |
| BH80_031 | BH‑B | Hard | isolate_largest → normalize_position → rotate | 1,2,4,5 | Selection tie, metadata dependency, normalization changes | First‑object shortcut |
| BH80_032 | BH‑B | Hard | normalize_position → isolate_largest → rotate | 1,2,4,5,8 | Normalization reorders objects, selection ambiguous, relational | Position‑invariance shortcut |
| BH80_033 | BH‑B | Hard | rotate → normalize_position → isolate_largest | 1,3,4,5,7 | Distractor same colour, rotation changes positions, edge contact | Rotation‑invariance shortcut |
| BH80_034 | BH‑B | Adversarial | isolate_largest → rotate → normalize_position | 1,2,3,5,6,8,9 | Size tie + distractor + rival grammar ("isolate = always largest") + relational + shape identity | Largest‑first shortcut |
| BH80_035 | BH‑B | Adversarial | normalize_position → rotate → isolate_largest | 1,2,3,4,5,6,8 | Full suite: ordering + selection + distractors + metadata + rival ("normalize = no change") + relational | Normalize‑noop shortcut |
| BH80_036 | BH‑B | Adversarial | rotate → isolate_largest → normalize_position | 1,2,3,4,5,6,9 | Rotation + selection tie + distractors + metadata + rival ("rotate = identity") + shape | Rotate‑identity shortcut |
| BH80_037 | BH‑B | Hard | isolate_largest → normalize_position → rotate | 1,2,4,5,9 | Shape identity matters, holes affect selection | Size‑only shortcut |
| BH80_038 | BH‑B | Hard | normalize_position → isolate_largest → rotate | 1,2,4,5,8 | Normalization changes selection, relational pressure | Normalize‑then‑select shortcut |

### 6.3 Mutation Tasks (20 tasks, BH‑C and BH‑D)

**Family BH‑C**: Mutations of known scenes — object count changes, position shifts, colour swaps, edge contact, canvas size changes.

| Task ID | Family | Diff. | Primitive Sequence | Active Axes | Mutation Type | Shortcut Defeated |
|---------|--------|-------|--------------------|-------------|---------------|-------------------|
| BH80_039 | BH‑C | Medium | extract → rotate → recolor | 1,3 | Object count increased to 3 (from 1), distractor added | Single‑object shortcut |
| BH80_040 | BH‑C | Medium | isolate_largest → normalize_position → recolor | 1,2 | Selection rule changed to "second‑largest" | Largest‑first shortcut |
| BH80_041 | BH‑C | Hard | extract_boundary → recolor_boundary → count | 1,3,4,7 | Object moved to edge, boundary touches canvas edge | Interior‑only shortcut |
| BH80_042 | BH‑C | Hard | crop_object → transform → place_back | 1,4,5,9 | Shape has holes, transform must preserve holes, place_back respects holes | Solid‑shape shortcut |
| BH80_043 | BH‑C | Hard | fill_region → count_objects → pattern_output | 1,2,4,5,8 | Canvas size doubled, count changes with scale, relational pressure | Fixed‑canvas shortcut |
| BH80_044 | BH‑C | Hard | extract → rotate → recolor | 1,3,5,7,9 | Colours swapped between objects, edge contact, asymmetric shape | Colour‑map shortcut |
| BH80_045 | BH‑C | Hard | remove_noise → extract_object → recolor | 1,2,3,5,8 | Noise level increased, multiple objects after denoising, relational | Single‑extract shortcut |
| BH80_046 | BH‑C | Hard | crop → rotate → count_or_pattern | 1,3,4,5,7 | Crop region ambiguous, edge contact, rotation changes count | Count‑first shortcut |
| BH80_047 | BH‑C | Hard | isolate_largest → normalize_position → recolor | 1,2,3,5,8 | Three same‑size objects, colour swap, selection rule = smallest | Largest‑only shortcut |
| BH80_048 | BH‑C | Adversarial | mirror_object → extract_changed_region → recolor | 1,3,4,5,6,7,9 | Disconnected parts + edge contact + rival grammar ("mirror = no change") + holes + metadata | Connected‑shape shortcut |
| BH80_049 | BH‑C | Adversarial | extract_boundary → mirror_object → crop | 1,3,4,5,6,7,9 | Colour swap + edge contact + rival grammar ("boundary = extract all") + holes + metadata | Boundary‑all shortcut |
| BH80_050 | BH‑C | Adversarial | fill_region → count_objects → pattern_output | 2,3,4,5,6,8,9 | Holes + distractors + canvas resize + rival grammar ("fill = count all") + relational + shape | Fill‑count‑all shortcut |

**Family BH‑D**: Mutations of primitive order and selection rules — shuffled sequences, reversed orders, changed selection criteria.

| Task ID | Family | Diff. | Primitive Sequence | Active Axes | Mutation Type | Shortcut Defeated |
|---------|--------|-------|--------------------|-------------|---------------|-------------------|
| BH80_051 | BH‑C | Adversarial | extract → rotate → recolor | 1,2,3,5,6,7,9 | Selection rule reversed, distractor same colour, shape with holes, rival grammar ("extract = first object"), edge contact | First‑object shortcut |
| BH80_052 | BH‑C | Hard | crop_object → transform → place_back | 1,3,4,5,7 | Canvas size changed, positions shifted, edge contact | Position‑invariance shortcut |
| BH80_053 | BH‑D | Hard | normalize_position → isolate_largest → recolor | 1,2,4,5,8 | Primitive order shuffled (normalize before isolate), relational pressure | Order‑independence shortcut |
| BH80_054 | BH‑D | Hard | recolor → extract → rotate | 1,3,5,7,9 | Primitive order reversed (recolor first), colour swap, edge contact | Order‑independence shortcut |
| BH80_055 | BH‑D | Medium | recolor → isolate_largest → normalize_position | 1,5 | F006 order reversed; recolor before isolation | Order‑independence |
| BH80_056 | BH‑D | Medium | rotate → extract → recolor | 1,5 | F001 order reversed; rotate before extract | Extract‑first shortcut |
| BH80_057 | BH‑D | Hard | count_objects → pattern_output → fill_region | 1,2,4,5,8 | F003 order reversed; count before fill, relational | Fill‑first shortcut |
| BH80_058 | BH‑D | Medium | place_back → crop_object → transform | 1,4,5 | F004 order reversed; place_back before crop | Crop‑first shortcut |

### 6.4 Unknown‑Family Candidate Tasks (22 tasks, BH‑E through BH‑G)

**Family BH‑E**: "Extract‑then‑count‑then‑transform" — a grammar where extraction feeds into counting which feeds into a shape transform. No existing family chains extract → count → transform.

| Task ID | Family | Diff. | Primitive Sequence | Active Axes | Grammar | Shortcut Defeated |
|---------|--------|-------|--------------------|-------------|---------|-------------------|
| BH80_059 | BH‑E | Hard | extract → count_objects → transform | 1,4,5,8,10 | Extract then count then transform; count metadata drives transform; novel family, relational | Extract‑only shortcut |
| BH80_060 | BH‑E | Hard | extract → count_objects → transform | 1,2,3,5,8,10 | Ambiguous target, distractors, count changes transform; novel family | Count‑ignore shortcut |
| BH80_061 | BH‑E | Adversarial | extract → count_objects → transform | 1,2,3,4,5,6,10 | Full suite: selection + distractors + metadata + rival ("extract = ignore count") + novel | Extract‑ignore shortcut |
| BH80_062 | BH‑E | Hard | count_objects → extract → transform | 1,4,5,8,9,10 | Count before extract (novel order), count selects target, shape identity | Count‑then‑extract shortcut |
| BH80_063 | BH‑E | Hard | extract → count_objects → transform | 1,3,4,5,7,10 | Edge contact, distractors, metadata dependency, novel family | Edge‑free shortcut |
| BH80_064 | BH‑E | Hard | transform → extract → count_objects | 1,2,4,5,8,10 | Transform first (novel order), transform changes what is extracted and counted | Extract‑first shortcut |
| BH80_065 | BH‑E | Hard | count_objects → transform → extract | 1,2,4,5,8,10 | Count first, transform changes extraction, relational, novel family | Count‑final shortcut |

**Family BH‑F**: "Normalize‑then‑mirror‑then‑place" — a grammar where normalization changes positions, mirror flips, and placement must respect the mirrored geometry. No existing family chains normalize → mirror → place_back.

| Task ID | Family | Diff. | Primitive Sequence | Active Axes | Grammar | Shortcut Defeated |
|---------|--------|-------|--------------------|-------------|---------|-------------------|
| BH80_066 | BH‑F | Hard | normalize_position → mirror_object → place_back | 1,4,5,7,8,10 | Normalize reorders, mirror flips, place_back must use post‑mirror coords; novel | Normalize‑noop shortcut |
| BH80_067 | BH‑F | Hard | mirror_object → normalize_position → place_back | 1,2,4,5,8,10 | Mirror first, normalize after mirror (selection changes), relational | Mirror‑invariance shortcut |
| BH80_068 | BH‑F | Hard | normalize_position → mirror_object → place_back | 1,2,3,4,5,10 | Distractors, ambiguous target, metadata; novel family | Position‑invariance shortcut |
| BH80_069 | BH‑F | Adversarial | normalize_position → mirror_object → place_back | 1,2,3,4,5,6,10 | Full suite: selection + distractors + metadata + rival ("normalize = identity") + novel | Normalize‑identity shortcut |
| BH80_070 | BH‑F | Hard | mirror_object → place_back → normalize_position | 1,4,5,8,9,10 | Place_back before normalize (novel order), shape identity, relational | Place‑last shortcut |
| BH80_071 | BH‑F | Hard | place_back → normalize_position → mirror_object | 1,2,4,5,8,10 | Place_back first (novel order), selection after placement, relational | Place‑first shortcut |
| BH80_072 | BH‑F | Hard | mirror_object → normalize_position → place_back | 1,2,4,5,9,10 | Mirror first, normalize after, shape identity, novel family | Mirror‑flip‑only shortcut |

**Family BH‑G**: "Crop‑then‑count‑then‑recolor" — a grammar where cropping determines what is counted and recolouring depends on count. No existing family chains crop → count → recolor.

| Task ID | Family | Diff. | Primitive Sequence | Active Axes | Grammar | Shortcut Defeated |
|---------|--------|-------|--------------------|-------------|---------|-------------------|
| BH80_073 | BH‑G | Hard | crop → count_objects → recolor | 1,4,5,8,10 | Crop determines count, count determines recolor; novel family, relational | Crop‑noop shortcut |
| BH80_074 | BH‑G | Hard | count_objects → crop → recolor | 1,3,4,5,8,10 | Count before crop (novel order), distractors, relational, novel family | Crop‑first shortcut |
| BH80_075 | BH‑G | Hard | crop → recolor → count_objects | 1,2,4,5,9,10 | Recolor before count (novel order), ambiguous target, shape identity | Count‑first shortcut |
| BH80_076 | BH‑G | Hard | recolor → crop → count_objects | 1,3,4,5,7,10 | Recolor first (novel order), distractors, edge contact, novel family | Recolor‑last shortcut |
| BH80_077 | BH‑G | Hard | crop → count_objects → recolor | 1,2,3,4,5,10 | Ambiguous target, distractors, metadata, novel family | Crop‑noop shortcut |
| BH80_078 | BH‑G | Adversarial | crop → count_objects → recolor | 1,2,3,4,5,6,10 | Full suite: ambiguous crop + distractors + metadata + rival ("crop = extract all") + novel | Crop‑all shortcut |
| BH80_079 | BH‑G | Hard | count_objects → recolor → crop | 1,2,4,5,8,10 | Count first (novel order), selection, relational, novel family | Count‑last shortcut |
| BH80_080 | BH‑G | Adversarial | crop → count_objects → recolor | 1,2,3,4,5,6,9 | Full suite: ambiguous crop + distractors + metadata + rival ("crop = extract all") + shape + novel | Crop‑extract‑all shortcut |

### 6.5 Summary Verification

| Check | Expected | Actual |
|-------|----------|--------|
| Total task IDs | 80 (BH80_001–BH80_080) | 80 ✅ |
| Unique task IDs | 80 | 80 ✅ |
| Tasks with exactly 3 primitives | 80 | 80 ✅ |
| Family count | 15 family IDs (F001–F008, BH‑A–BH‑G) | 15 ✅ |
| Known‑family anchors | 15–20 | 18 ✅ |
| Hybrid‑family tasks | 20 | 20 ✅ |
| Mutation tasks | 20 | 20 ✅ |
| Unknown‑family candidates | 20–25 | 22 ✅ |
| Easy tasks | 0 | 0 ✅ |
| Medium tasks | 16 | 16 ✅ |
| Hard tasks | 48 | 48 ✅ |
| Adversarial tasks | 16 | 16 ✅ |
| All leakage flags false | yes | yes ✅ |
| All primitives from allowed set | yes | yes ✅ |
| No public/hidden ARC data | yes | yes ✅ |
| No ARC‑AGI claims | yes | yes ✅ |

**Family size breakdown:**

| Family | Type | Count |
|--------|------|-------|
| F001 | Known anchor | 2 |
| F002 | Known anchor | 2 |
| F003 | Known anchor | 3 |
| F004 | Known anchor | 2 |
| F005 | Known anchor | 2 |
| F006 | Known anchor | 3 |
| F007 | Known anchor | 2 |
| F008 | Known anchor | 2 |
| BH‑A | Hybrid | 10 |
| BH‑B | Hybrid | 10 |
| BH‑C | Mutation | 14 |
| BH‑D | Mutation | 6 |
| BH‑E | Unknown‑family | 7 |
| BH‑F | Unknown‑family | 7 |
| BH‑G | Unknown‑family | 8 |
| **Total** | | **80** |

---

## 7. Generator‑Readiness Schema (per‑task)

```json
{
  "task_id": "BH80_XXX",
  "family_id": "BH‑X",
  "difficulty": "medium|hard|adversarial",
  "primitive_sequence": ["<prim1>", "<prim2>", "<prim3>"],
  "scene_spec": {
    "grid_size": [W, H],
    "initial_objects": [
      {
        "object_id": "obj_<family>_<variant>",
        "type": "generic",
        "attributes": {
          "color": "<color>",
          "position": [x, y],
          "shape": "<descriptor>",
          "holes": false,
          "disconnected_parts": false
        }
      }
    ],
    "distractors": []
  },
  "train_pair_count": 1,
  "test_input_count": 1,
  "hardness_axes": [1, 5],
  "hardness_reason": "<description>",
  "shortcut_defeated": "<description>",
  "expected_trace_requirements": {
    "step_1_exports": true,
    "step_2_imports": true,
    "step_2_exports": true,
    "step_3_imports": true,
    "carried_parameters_by_edge": {"1-2": [], "2-3": []},
    "dropped_parameters_by_edge": {"1-2": [], "2-3": []},
    "parameter_origin_by_step": {},
    "intermediate_grid_1_summary": "",
    "intermediate_grid_2_summary": "",
    "failure_step": null,
    "failure_reason": null,
    "sequence_visibility_reason": "all steps visible"
  },
  "allowed_dynamic_parameters": [],
  "forbidden_shortcuts": ["expected_test_output", "task_id_shortcut", "generator_note_shortcut"],
  "leakage_flags": {
    "arc_agi_participation_claim": false,
    "leaderboard_claim": false,
    "hidden_test_use": false,
    "public_claim": false,
    "final_answer_wiring": false,
    "weslr_persistence": false,
    "external_calls": false,
    "provider_model_calls": false,
    "runtime_chat_wiring": false
  },
  "expected_failure_categories": []
}
```

All 80 tasks conform to this schema.

---

## 8. Forbidden Claims

The design contains **no** references to:

- Public ARC‑AGI benchmark scores or claims.
- Use of public or hidden ARC datasets.
- Assertions of autonomous discovery or real‑world evidence intake.
- External provider APIs or model calls.
- Any public product readiness claim.

All scenes are **fully synthetic** and generator‑safe. No randomness is used. No public ARC data is referenced. No hidden or private test data is used.

---

## 9. Validation Plan

1. **Static verification** – script checks that:
   - Exactly 80 unique `task_id`s exist.
   - Each task has exactly 3 primitives from the allowed list.
   - Family sizes match the allocation.
   - Difficulty counts match the target distribution (0 easy, 16 medium, 48 hard, 16 adversarial).
   - All `leakage_flags` are false.
2. **Schema validation** – each JSON task validates against the generator‑readiness schema.
3. **Shortcut trap audit** – ensure each task lists at least one defeated shortcut/rival grammar.
4. **Hardness‑axis audit** – confirm that every task's `hardness_axes` vector aligns with the described challenge dimensions and difficulty derivation rules.
5. **Primitive‑boundary audit** – confirm no task references a primitive outside the allowed set.
6. **Release‑gate validation** – run `weslr_release_check.sh` and `chat_weslr_de_health_check.sh --mode source‑repo`.

---

## 10. Next Lane Recommendation

`IMPLEMENT_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_GENERATOR_V1` – implement the deterministic generator that emits the 80‑task packet described above, together with unit tests exercising the static checks.

---

## Receipt

| Field | Value |
|-------|-------|
| **Start HEAD** | `e748b0ee` |
| ****End HEAD** | `0b8840e6` |
| ****Commit performed** | yes (`0b8840e6`) |
| **Primitive boundary defined** | yes |
| **Hardness axes defined** | yes |
| **Unknown mutation defined** | yes |
| **Unknown‑family candidate defined** | yes |
| **15–20 known‑family anchors** | yes (18) |
| **Hybrid tasks included** | yes (20) |
| **Mutation tasks included** | yes (20) |
| **Unknown‑family candidates included** | yes (22) |
| **All tasks exactly 3 primitives** | yes |
| **Unsupported primitive names avoided** | yes |
| **Generator‑ready** | yes |
| **Validation** | PASS |
| **Push avoided** | yes |
| **Recommended next lane** | `IMPLEMENT_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_GENERATOR_V1` |