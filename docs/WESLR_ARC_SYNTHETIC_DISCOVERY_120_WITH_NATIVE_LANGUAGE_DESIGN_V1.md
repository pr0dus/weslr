# WESLR ARC Synthetic Discovery 120 with Native Language — Design (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_ARC_SYNTHETIC_DISCOVERY_120_WITH_NATIVE_LANGUAGE_V1`
**Start HEAD**: `148d72fd`
**Date**: 2026-07-02

---

## 1. Preflight

| Check | Result |
|-------|--------|
| `pwd` | `/data/data/com.termux/files/home/weslr-pr47-clean` ✅ |
| `git status` | clean ✅ |
| `git branch --show-current` | `occ-discovery-doctrine-implementation-20260613` ✅ |
| `git rev-parse --short HEAD` | `148d72fd` ✅ |

### Metadata mismatch

| Source | HEAD | Match? |
|--------|------|--------|
| Expected from receipt | `148d72fd` | ✅ matches actual |
| Fallback from uploaded promotion pilot report | `cb9a8d0d` | ❌ does not match actual |
| Handoff file (`WESLR_CURRENT_HANDOFF.md`) | `8d38829c` | ❌ stale — superseded by local chain |

**Actual preflight HEAD**: `148d72fd`
**Metadata mismatch noted**: yes — handoff HEAD is stale (`8d38829c`); fallback HEAD (`cb9a8d0d`) does not match actual. Receipt HEAD matches. Working tree clean. Proceeding from `148d72fd`.

---

## 2. BH80 Frozen Base Summary

The BH80 semantic regression gate was frozen at HEAD `dfe65eb7` on 2026-07-01.

| Metric | Value |
|--------|-------|
| semantic_exact | 80/80 (100%) |
| failed | 0 |
| unsupported | 0 |
| structural_pass | 80/80 |
| oracle output diversity | 27 unique outputs |
| solver output diversity | 56 unique outputs |

### Frozen components

| Component | File |
|-----------|------|
| Generator (80 task packets) | `weslr/arc_synthetic_3_step_task_schema.py` |
| Enriched scenes (80 specs) | `weslr/arc_bh80_enriched_scenes.py` |
| Materializer | `weslr/arc_bh80_materializer.py` |
| Oracle | `weslr/arc_bh80_oracle.py` |
| Solver adapter | `weslr/arc_bh80_solver_adapter.py` |
| Semantic scorer | `weslr/arc_bh80_semantic_scorer.py` |
| Solver dispatch | `weslr/arc_synthetic_3_step_real_dispatch.py` |

### BH80 task families

| Family | Count | Primitive sequences |
|--------|-------|-------------------|
| F001 | 2 | extract→rotate→recolor |
| F002 | 2 | remove_noise→extract_object→recolor |
| F003 | 3 | fill_region→count_objects→pattern_output |
| F004 | 2 | crop_object→transform→place_back |
| F005 | 2 | extract_boundary→recolor_boundary→count |
| F006 | 3 | isolate_largest→normalize_position→recolor |
| F007 | 2 | mirror_object→extract_changed_region→recolor |
| F008 | 2 | crop→rotate→count_or_pattern |
| BH-A | 10 | extract_boundary/mirror_object/crop permutations |
| BH-B | 10 | isolate_largest/rotate/normalize_position permutations |
| BH-C | 14 | mixed families (composition variety) |
| BH-D | 6 | novel orderings (normalize/recolor/extract/etc.) |
| BH-E | 7 | extract/count_objects/transform permutations |
| BH-F | 7 | normalize_position/mirror_object/place_back permutations |
| BH-G | 8 | crop/count_objects/recolor permutations |

### Unique BH80 primitives (20)

`count`, `count_objects`, `count_or_pattern`, `crop`, `crop_object`, `extract`, `extract_boundary`, `extract_changed_region`, `extract_object`, `fill_region`, `isolate_largest`, `mirror_object`, `normalize_position`, `pattern_output`, `place_back`, `recolor`, `recolor_boundary`, `remove_noise`, `rotate`, `transform`

### Frozen anti-cheat controls (9)

1. No `[[1]]` scenes
2. Oracle output diversity ≥ 20
3. Solver output diversity ≥ 10
4. No-op shadow control
5. Primitive-order negative control
6. Unsupported primitive sentinel
7. Oracle avoids solver dispatch
8. Semantic scorer uses grid equality
9. structural_pass separate from semantic_exact

**The first 80 tasks of the 120 suite are these exact BH80 tasks, unchanged.**

---

## 3. Native Primitive Status Summary

### Native language schema

Implemented in `weslr/native_arc_language_schema.py`. Defines:
- `PrimitiveContract` dataclass with 15 fields
- `TypeSignature` (input/output/parameters)
- `PromotionStage` enum with 9 stages
- Alien expression format using symbolic tokens (λ, Σ, Ω, κ, γ, τ, Φ, ξ, π, ⇒, ⇢)

### Candidate generator

Implemented in `weslr/native_arc_candidate_generator.py`. Produces 32 candidates across 9 families.

| # | Family | Count | Example expression |
|---|--------|-------|--------------------|
| 1 | object_selector | 5 | `λG.Σ[obj|argmin(col)]⇒extract` |
| 2 | mask_algebra | 4 | `Ω(mask∧border)⇢color(2)` |
| 3 | color_transform | 4 | `κ(invert)⇒recolor` |
| 4 | geometry_transform | 3 | `γ(scale(2.0))⇒resize` |
| 5 | topology_transform | 3 | `τ(fill(holes))⇒solid` |
| 6 | relation_transform | 3 | `Φ(rel(centroid_align),objset)⇒translate` |
| 7 | construction_transform | 4 | `ξ(draw(rect,bbox(obj)))⇒overlay` |
| 8 | pattern_transform | 3 | `π(row_alternate(1,2))⇒pattern` |
| 9 | conditional_transform | 3 | `κ(count(holes)>0)?fill_holes:identity` |
| **Total** | | **32** | |

All 32 candidates are at `PromotionStage.GENERATED`. None can be counted as solved.

### Promoted primitive: `color_invert`

| Field | Value |
|-------|-------|
| primitive_id | `color_invert` |
| Family | color_transform |
| Expression | `κ(invert)⇒recolor` |
| Type | Grid → Grid |
| Semantics | Replace each non-background color `c` with `(10 - c)`. Background (0) unchanged. |
| Oracle | `weslr/native_arc_oracle.py::oracle_color_invert()` |
| Solver | `weslr/native_arc_solver.py::solver_color_invert()` |
| Promotion stage | PROMOTED (all 9 stages completed) |
| `can_be_counted_as_solved()` | True |
| Positive examples | 3 (simple, multi-color, color-9 edge) |
| Negative controls | 2 (no-op differs, unsupported sentinel) |
| Anti-cheat checks | 5/5 pass |
| BH80 regression | 80/80 (no change) |
| Audit artifacts | 12/12 complete |

### Unpromoted candidates (31)

All 31 remaining candidates are at `GENERATED` stage. `can_be_counted_as_solved()` returns `False` for all. They may appear as candidate-probe tasks but cannot be counted in the semantic score.

---

## 4. 120 Composition Plan

| Component | Count | Scored? | Source |
|-----------|-------|---------|--------|
| Frozen BH80 base | 80 | Yes | Existing 80 tasks (unchanged) |
| Promoted-native tasks (`color_invert`) | 10 | Yes | New tasks using `color_invert` in 3-step chains |
| Old-primitive harder compositions | 10 | Yes | New tasks using BH80 accepted primitives in novel harder chains |
| Candidate-probe tasks | 10 | **No** | New tasks using unpromoted native candidates, explicitly unscored |
| Adversarial/control tasks | 10 | Yes | No-op, order, metadata stripping, output diversity, regression safety |
| **Total** | **120** | **110 scored / 10 candidate-probe** | |

### Task ID range

| Range | Group | Count |
|-------|-------|-------|
| BH80_001 – BH80_080 | Frozen BH80 base | 80 |
| T120_081 – T120_090 | Promoted-native (`color_invert`) | 10 |
| T120_091 – T120_100 | Old-primitive harder compositions | 10 |
| T120_101 – T120_110 | Candidate-probe (unpromoted) | 10 |
| T120_111 – T120_120 | Adversarial/control | 10 |

### Scoring denominator

- Scored total: 110 (BH80 80 + promoted-native 10 + old-primitive 10 + adversarial 10)
- Candidate-probe total: 10 (reported separately, never mixed into scored denominator)
- Overall reported as: `scored_exact / 110` and `candidate_probe_total / 10`

---

## 5. Forty New Task Specifications

### 5.1 Promoted-Native Tasks (T120_081 – T120_090)

These 10 tasks use `color_invert` in 3-step chains. `color_invert` is promoted, so these are scored.

All tasks specify: task_id, primitive sequence (exactly 3 steps), where `color_invert` appears, scene_spec requirements, expected semantic stress, anti-cheat expectation, and why this is not a BH80 duplicate.

#### T120_081

| Field | Value |
|-------|-------|
| task_id | `T120_081` |
| primitive_sequence | `['extract', 'color_invert', 'recolor']` |
| color_invert position | Step 2 (middle) |
| scene_spec | grid_size [8,8], bg=0, 1 rectangle obj color=2 pos=[2,2] size=[3,3], 1 distractor rectangle color=4 pos=[6,6] size=[1,1], noise=0 |
| expected semantic stress | Extract isolates object, color_invert inverts non-bg colors (2→8, 4→6), recolor applies final color mapping. Tests color_invert on extracted sub-grid. |
| anti-cheat expectation | No-op chain produces different output. Order reversal produces different output. No `[[1]]` materialization. |
| not BH80 duplicate | BH80 has no task using `color_invert`. BH80 color tasks use `recolor` only. |

#### T120_082

| Field | Value |
|-------|-------|
| task_id | `T120_082` |
| primitive_sequence | `['color_invert', 'extract', 'rotate']` |
| color_invert position | Step 1 (first) |
| scene_spec | grid_size [10,10], bg=0, 1 rectangle color=1 pos=[1,1] size=[4,4], 1 rectangle color=3 pos=[6,6] size=[2,2], 0 distractors, noise=0 |
| expected semantic stress | color_invert on full grid first (1→9, 3→7), then extract largest, then rotate. Tests color_invert as preprocessing before object selection. |
| anti-cheat expectation | No-op differs. Order reversal (rotate→extract→color_invert) differs. Output diversity from multi-color inversion. |
| not BH80 duplicate | No BH80 task starts with `color_invert`. No BH80 task inverts as preprocessing. |

#### T120_083

| Field | Value |
|-------|-------|
| task_id | `T120_083` |
| primitive_sequence | `['isolate_largest', 'color_invert', 'normalize_position']` |
| color_invert position | Step 2 (middle) |
| scene_spec | grid_size [12,12], bg=0, 2 objects: rect color=5 pos=[1,1] size=[5,5], rect color=2 pos=[8,8] size=[2,2], 1 distractor color=7 pos=[0,11] size=[1,1], noise=0 |
| expected semantic stress | Isolate largest selects 5×5 object, color_invert inverts it (5→5, since 10-5=5 — identity for color 5! Tests edge case where invert is identity), normalize_position centers result. |
| anti-cheat expectation | No-op differs (normalize_position changes layout). Order reversal differs. Edge case: color_invert on color 5 is identity — must still pass semantic_exact because both oracle and solver agree. |
| not BH80 duplicate | BH80 uses isolate_largest→normalize_position→recolor. This uses color_invert instead of recolor, and tests the identity edge case. |

#### T120_084

| Field | Value |
|-------|-------|
| task_id | `T120_084` |
| primitive_sequence | `['crop_object', 'color_invert', 'place_back']` |
| color_invert position | Step 2 (middle) |
| scene_spec | grid_size [10,10], bg=0, 1 rectangle color=3 pos=[2,2] size=[4,3], 1 distractor color=8 pos=[8,0] size=[1,1], noise=0 |
| expected semantic stress | Crop object extracts sub-grid, color_invert inverts within crop (3→7), place_back repositions. Tests color_invert on cropped sub-grid with place_back context. |
| anti-cheat expectation | No-op differs. Order reversal (place_back→color_invert→crop_object) differs. No `[[1]]`. |
| not BH80 duplicate | BH80 uses crop_object→transform→place_back. This replaces transform with color_invert. |

#### T120_085

| Field | Value |
|-------|-------|
| task_id | `T120_085` |
| primitive_sequence | `['color_invert', 'isolate_largest', 'recolor']` |
| color_invert position | Step 1 (first) |
| scene_spec | grid_size [10,10], bg=0, 3 objects: rect color=1 pos=[0,0] size=[2,2], rect color=6 pos=[3,3] size=[4,4], rect color=9 pos=[7,7] size=[2,2], 0 distractors, noise=0 |
| expected semantic stress | color_invert on full grid (1→9, 6→4, 9→1), then isolate_largest selects the now-color-4 4×4 object, recolor applies final mapping. Tests color_invert changing which object is visually distinct before selection. |
| anti-cheat expectation | No-op differs. Order differs. Output diversity from 3-color inversion. |
| not BH80 duplicate | No BH80 task starts with color_invert or uses it before object selection. |

#### T120_086

| Field | Value |
|-------|-------|
| task_id | `T120_086` |
| primitive_sequence | `['extract_boundary', 'color_invert', 'count']` |
| color_invert position | Step 2 (middle) |
| scene_spec | grid_size [8,8], bg=0, 1 rectangle color=2 pos=[1,1] size=[5,5], 0 distractors, noise=0 |
| expected semantic stress | Extract_boundary gets border cells, color_invert inverts boundary colors (2→8), count produces count-based output. Tests color_invert on boundary-only sub-grid. |
| anti-cheat expectation | No-op differs. Order reversal differs. No `[[1]]`. |
| not BH80 duplicate | BH80 uses extract_boundary→recolor_boundary→count. This replaces recolor_boundary with color_invert (global inversion, not targeted boundary recolor). |

#### T120_087

| Field | Value |
|-------|-------|
| task_id | `T120_087` |
| primitive_sequence | `['rotate', 'color_invert', 'crop']` |
| color_invert position | Step 2 (middle) |
| scene_spec | grid_size [10,10], bg=0, 1 rectangle color=4 pos=[2,2] size=[4,4], 1 rectangle color=1 pos=[7,7] size=[2,2], 0 distractors, noise=0 |
| expected semantic stress | Rotate transforms grid, color_invert inverts all colors (4→6, 1→9), crop extracts region. Tests color_invert after geometric transform. |
| anti-cheat expectation | No-op differs. Order reversal differs. Multi-object output diversity. |
| not BH80 duplicate | No BH80 task uses rotate→color_invert→crop. BH80 rotate tasks use recolor or count_or_pattern. |

#### T120_088

| Field | Value |
|-------|-------|
| task_id | `T120_088` |
| primitive_sequence | `['mirror_object', 'color_invert', 'extract_changed_region']` |
| color_invert position | Step 2 (middle) |
| scene_spec | grid_size [10,10], bg=0, 1 rectangle color=3 pos=[1,1] size=[4,3], 1 distractor color=7 pos=[8,8] size=[1,1], noise=0 |
| expected semantic stress | Mirror reflects object, color_invert inverts (3→7, 7→3 — swaps distractor and object colors!), extract_changed_region detects inverted+mirrored region. Tests color_invert interacting with mirror to create color convergence. |
| anti-cheat expectation | No-op differs. Order reversal differs. Color convergence edge case must still produce deterministic output. |
| not BH80 duplicate | BH80 uses mirror_object→extract_changed_region→recolor. This inserts color_invert between mirror and extract_changed_region. |

#### T120_089

| Field | Value |
|-------|-------|
| task_id | `T120_089` |
| primitive_sequence | `['color_invert', 'crop', 'count_or_pattern']` |
| color_invert position | Step 1 (first) |
| scene_spec | grid_size [8,8], bg=0, 1 rectangle color=1 pos=[1,1] size=[3,3], 1 rectangle color=8 pos=[5,5] size=[2,2], 0 distractors, noise=2 |
| expected semantic stress | color_invert on full grid (1→9, 8→2), crop extracts region, count_or_pattern produces count/pattern output. Tests color_invert as preprocessing with noise present. |
| anti-cheat expectation | No-op differs. Order differs. Noise pixels deterministic. No `[[1]]`. |
| not BH80 duplicate | No BH80 task starts with color_invert. BH80 noise tasks use remove_noise first. |

#### T120_090

| Field | Value |
|-------|-------|
| task_id | `T120_090` |
| primitive_sequence | `['fill_region', 'color_invert', 'transform']` |
| color_invert position | Step 2 (middle) |
| scene_spec | grid_size [10,10], bg=0, 1 cross color=2 pos=[3,3] size=[3,3], 1 distractor color=6 pos=[0,0] size=[1,1], noise=0 |
| expected semantic stress | Fill_region fills enclosed areas, color_invert inverts all colors (2→8, 6→4), transform applies geometric transform. Tests color_invert after fill, before transform. |
| anti-cheat expectation | No-op differs. Order differs. Cross shape with fill creates non-trivial inversion target. |
| not BH80 duplicate | BH80 uses fill_region→count_objects→pattern_output. This replaces steps 2-3 with color_invert→transform. |

### 5.2 Old-Primitive Harder Compositions (T120_091 – T120_100)

These 10 tasks use only accepted BH80 primitives in novel, harder 3-step chains not present in BH80. These are scored.

#### T120_091

| Field | Value |
|-------|-------|
| task_id | `T120_091` |
| primitive_sequence | `['remove_noise', 'rotate', 'extract_boundary']` |
| scene_spec | grid_size [12,12], bg=0, 1 rectangle color=1 pos=[2,2] size=[5,5], 2 distractors (color=1 pos=[10,10] size=[1,1], color=1 pos=[0,11] size=[1,1]), noise=3 |
| expected semantic stress | Noise removal, then rotation, then boundary extraction on rotated grid. Tests compound transform+boundary with noise. |
| not BH80 duplicate | No BH80 task uses this exact sequence. BH80 noise tasks pair with extract_object, not rotate+extract_boundary. |

#### T120_092

| Field | Value |
|-------|-------|
| task_id | `T120_092` |
| primitive_sequence | `['extract', 'normalize_position', 'count_objects']` |
| scene_spec | grid_size [10,10], bg=0, 3 objects: rect color=2 pos=[0,0] size=[2,2], rect color=2 pos=[5,5] size=[2,2], rect color=3 pos=[8,0] size=[1,1], 0 distractors, noise=0 |
| expected semantic stress | Extract isolates sub-grid, normalize_position centers, count_objects produces count. Tests extract→normalize→count chain with 3 objects. |
| not BH80 duplicate | BH80 uses isolate_largest→normalize_position→recolor. This uses extract→normalize_position→count_objects — different primitives at steps 1 and 3. |

#### T120_093

| Field | Value |
|-------|-------|
| task_id | `T120_093` |
| primitive_sequence | `['crop_object', 'mirror_object', 'recolor_boundary']` |
| scene_spec | grid_size [10,10], bg=0, 1 rectangle color=4 pos=[2,2] size=[4,4], 1 distractor color=4 pos=[8,8] size=[1,1], noise=0 |
| expected semantic stress | Crop sub-grid, mirror object within crop, recolor boundary of mirrored result. Tests crop→mirror→recolor_boundary chain. |
| not BH80 duplicate | No BH80 task uses crop_object→mirror_object→recolor_boundary. BH-A uses extract_boundary/mirror/crop; BH-D uses recolor/extract/rotate. |

#### T120_094

| Field | Value |
|-------|-------|
| task_id | `T120_094` |
| primitive_sequence | `['isolate_largest', 'extract_changed_region', 'pattern_output']` |
| scene_spec | grid_size [12,12], bg=0, 2 objects: rect color=1 pos=[1,1] size=[6,6], rect color=2 pos=[9,9] size=[2,2], 1 distractor color=1 pos=[0,11] size=[1,1], noise=0 |
| expected semantic stress | Isolate largest, extract changed region (isolation changes grid), pattern output from changed region. Tests isolate→extract_changed→pattern chain. |
| not BH80 duplicate | BH80 uses isolate_largest→normalize_position→recolor. This uses extract_changed_region and pattern_output instead. |

#### T120_095

| Field | Value |
|-------|-------|
| task_id | `T120_095` |
| primitive_sequence | `['count_objects', 'crop', 'transform']` |
| scene_spec | grid_size [10,10], bg=0, 3 objects: rect color=2 pos=[1,1] size=[2,2], rect color=3 pos=[5,5] size=[2,2], rect color=4 pos=[8,8] size=[1,1], 0 distractors, noise=0 |
| expected semantic stress | Count objects first (changes grid to count representation), crop extracts region, transform applies geometry. Tests count→crop→transform ordering. |
| not BH80 duplicate | BH80 has count_objects→pattern_output→fill_region and crop→count_objects→recolor. This is a novel ordering. |

#### T120_096

| Field | Value |
|-------|-------|
| task_id | `T120_096` |
| primitive_sequence | `['place_back', 'extract_boundary', 'rotate']` |
| scene_spec | grid_size [10,10], bg=0, 1 rectangle color=5 pos=[2,2] size=[3,3], 1 distractor color=5 pos=[7,0] size=[1,1], noise=0 |
| expected semantic stress | Place_back repositions object, extract_boundary gets border, rotate transforms boundary. Tests place_back before boundary extraction. |
| not BH80 duplicate | BH-F uses normalize_position→mirror_object→place_back. This uses place_back first, then extract_boundary→rotate. |

#### T120_097

| Field | Value |
|-------|-------|
| task_id | `T120_097` |
| primitive_sequence | `['transform', 'remove_noise', 'extract']` |
| scene_spec | grid_size [12,12], bg=0, 1 rectangle color=1 pos=[3,3] size=[4,4], 2 distractors (color=1 pos=[10,0] size=[1,1], color=1 pos=[0,10] size=[1,1]), noise=4 |
| expected semantic stress | Transform first (geometric), then remove noise, then extract. Tests transform before noise removal — noise patterns may shift. |
| not BH80 duplicate | BH80 noise tasks always start with remove_noise. This reverses: transform first, then noise removal. |

#### T120_098

| Field | Value |
|-------|-------|
| task_id | `T120_098` |
| primitive_sequence | `['recolor', 'place_back', 'count']` |
| scene_spec | grid_size [10,10], bg=0, 2 objects: rect color=1 pos=[1,1] size=[3,3], rect color=2 pos=[6,6] size=[2,2], 1 distractor color=1 pos=[0,9] size=[1,1], noise=0 |
| expected semantic stress | Recolor changes colors, place_back repositions, count produces count-based output. Tests recolor→place_back→count chain. |
| not BH80 duplicate | BH-D uses recolor→extract→rotate and recolor→isolate_largest→normalize_position. This uses place_back and count. |

#### T120_099

| Field | Value |
|-------|-------|
| task_id | `T120_099` |
| primitive_sequence | `['extract_object', 'count_objects', 'normalize_position']` |
| scene_spec | grid_size [10,10], bg=0, 3 objects: rect color=3 pos=[0,0] size=[2,2], rect color=3 pos=[4,4] size=[3,3], rect color=4 pos=[8,8] size=[1,1], 0 distractors, noise=0 |
| expected semantic stress | Extract object, count objects, normalize position. Tests extract_object before counting, then normalization. |
| not BH80 duplicate | BH80 uses remove_noise→extract_object→recolor. This uses extract_object→count_objects→normalize_position. |

#### T120_100

| Field | Value |
|-------|-------|
| task_id | `T120_100` |
| primitive_sequence | `['normalize_position', 'recolor_boundary', 'mirror_object']` |
| scene_spec | grid_size [10,10], bg=0, 2 objects: rect color=2 pos=[1,1] size=[4,4], rect color=2 pos=[7,7] size=[2,2], 0 distractors, noise=0 |
| expected semantic stress | Normalize positions, recolor boundaries, mirror objects. Tests normalize→recolor_boundary→mirror chain with multi-object. |
| not BH80 duplicate | No BH80 task uses normalize_position→recolor_boundary→mirror_object. BH-B uses isolate/rotate/normalize; BH-F uses normalize/mirror/place_back. |

### 5.3 Candidate-Probe Tasks (T120_101 – T120_110)

These 10 tasks use unpromoted native candidates. They are **not scored**. Each is explicitly marked `candidate_probe` and `can_be_counted_as_solved()` must return `False`.

#### T120_101

| Field | Value |
|-------|-------|
| task_id | `T120_101` |
| primitive_sequence | `['extract', 'mask_border_only', 'recolor']` |
| candidate_primitive | `mask_border_only` (family: mask_algebra, expression: `Ω(mask∧border)⇢color(2)`) |
| unpromoted_status | `PromotionStage.GENERATED` — `can_be_counted_as_solved()` = False |
| not counted in score | Yes — candidate probe |
| scene_spec | grid_size [10,10], bg=0, 1 rectangle color=3 pos=[2,2] size=[5,5], 0 distractors, noise=0 |
| diagnostic value | Tests whether mask_border_only produces meaningful border-highlight output when composed with extract and recolor. |
| promotion evidence it may help generate | If oracle/solver agreement + no-op control + output diversity pass, this probe contributes evidence for `mask_border_only` promotion batch 2. |
| counted as semantic solved | No — must report `candidate_probe` / `unpromoted` |

#### T120_102

| Field | Value |
|-------|-------|
| task_id | `T120_102` |
| primitive_sequence | `['isolate_largest', 'geom_flip_vertical', 'recolor']` |
| candidate_primitive | `geom_flip_vertical` (family: geometry_transform, expression: `γ(flip(axis=row))⇒reflect`) |
| unpromoted_status | `PromotionStage.GENERATED` — `can_be_counted_as_solved()` = False |
| not counted in score | Yes — candidate probe |
| scene_spec | grid_size [10,10], bg=0, 1 rectangle color=1 pos=[1,1] size=[4,4], 1 distractor color=1 pos=[8,8] size=[1,1], noise=0 |
| diagnostic value | Tests geom_flip_vertical on isolated largest object. Shows whether vertical flip is distinguishable from existing mirror_object. |
| promotion evidence | If flip output differs from mirror_object output and passes anti-cheat, supports geom_flip_vertical promotion. |
| counted as semantic solved | No |

#### T120_103

| Field | Value |
|-------|-------|
| task_id | `T120_103` |
| primitive_sequence | `['topo_fill_holes', 'extract', 'recolor']` |
| candidate_primitive | `topo_fill_holes` (family: topology_transform, expression: `τ(fill(holes))⇒solid`) |
| unpromoted_status | `PromotionStage.GENERATED` — `can_be_counted_as_solved()` = False |
| not counted in score | Yes — candidate probe |
| scene_spec | grid_size [10,10], bg=0, 1 hollow rectangle (border only) color=2 pos=[2,2] size=[5,5] (interior is bg=0, creating holes), 0 distractors, noise=0 |
| diagnostic value | Tests whether topo_fill_holes correctly fills interior holes, and whether subsequent extract/recolor produce distinguishable output. |
| promotion evidence | If fill behavior is deterministic, oracle/solver agree, and no-op differs, supports topo_fill_holes promotion batch 2. |
| counted as semantic solved | No |

#### T120_104

| Field | Value |
|-------|-------|
| task_id | `T120_104` |
| primitive_sequence | `['constr_draw_rect_around', 'recolor', 'crop']` |
| candidate_primitive | `constr_draw_rect_around` (family: construction_transform, expression: `ξ(draw(rect,bbox(obj)))⇒overlay`) |
| unpromoted_status | `PromotionStage.GENERATED` — `can_be_counted_as_solved()` = False |
| not counted in score | Yes — candidate probe |
| scene_spec | grid_size [12,12], bg=0, 1 rectangle color=4 pos=[3,3] size=[3,3], 0 distractors, noise=0 |
| diagnostic value | Tests construction primitive drawing a rectangle around an object. Shows whether construction creates novel grid state. |
| promotion evidence | If drawn rectangle is deterministic, oracle/solver agree, and output differs from no-op, supports constr_draw_rect_around promotion. |
| counted as semantic solved | No |

#### T120_105

| Field | Value |
|-------|-------|
| task_id | `T120_105` |
| primitive_sequence | `['color_swap_1_2', 'extract', 'rotate']` |
| candidate_primitive | `color_swap_1_2` (family: color_transform, expression: `κ(swap(1,2))⇒recolor`) |
| unpromoted_status | `PromotionStage.GENERATED` — `can_be_counted_as_solved()` = False |
| not counted in score | Yes — candidate probe |
| scene_spec | grid_size [10,10], bg=0, 2 objects: rect color=1 pos=[1,1] size=[3,3], rect color=2 pos=[6,6] size=[3,3], 0 distractors, noise=0 |
| diagnostic value | Tests color swap (1↔2) before extraction. Shows whether swap creates visually distinguishable output vs. no-op. |
| promotion evidence | If swap is deterministic, differs from identity, and oracle/solver agree, supports color_swap_1_2 promotion. |
| counted as semantic solved | No |

#### T120_106

| Field | Value |
|-------|-------|
| task_id | `T120_106` |
| primitive_sequence | `['sel_leftmost', 'recolor', 'rotate']` |
| candidate_primitive | `sel_leftmost` (family: object_selector, expression: `λG.Σ[obj|argmin(col)]⇒extract`) |
| unpromoted_status | `PromotionStage.GENERATED` — `can_be_counted_as_solved()` = False |
| not counted in score | Yes — candidate probe |
| scene_spec | grid_size [10,10], bg=0, 3 objects: rect color=3 pos=[5,1] size=[2,2], rect color=4 pos=[5,5] size=[2,2], rect color=5 pos=[5,8] size=[2,2], 0 distractors, noise=0 |
| diagnostic value | Tests leftmost object selection. Shows whether sel_leftmost is distinguishable from isolate_largest and extract. |
| promotion evidence | If leftmost selection is deterministic and differs from other selectors, supports sel_leftmost promotion batch 2. |
| counted as semantic solved | No |

#### T120_107

| Field | Value |
|-------|-------|
| task_id | `T120_107` |
| primitive_sequence | `['extract', 'pat_row_alternate', 'recolor']` |
| candidate_primitive | `pat_row_alternate` (family: pattern_transform, expression: `π(row_alternate(1,2))⇒pattern`) |
| unpromoted_status | `PromotionStage.GENERATED` — `can_be_counted_as_solved()` = False |
| not counted in score | Yes — candidate probe |
| scene_spec | grid_size [8,8], bg=0, 1 rectangle color=1 pos=[1,1] size=[6,2], 0 distractors, noise=0 |
| diagnostic value | Tests row-alternating pattern generation on extracted sub-grid. Shows whether pattern transform creates novel output. |
| promotion evidence | If pattern is deterministic, differs from no-op, and oracle/solver agree, supports pat_row_alternate promotion. |
| counted as semantic solved | No |

#### T120_108

| Field | Value |
|-------|-------|
| task_id | `T120_108` |
| primitive_sequence | `['cond_if_holes_fill', 'recolor', 'crop']` |
| candidate_primitive | `cond_if_holes_fill` (family: conditional_transform, expression: `κ(count(holes)>0)?fill_holes:identity`) |
| unpromoted_status | `PromotionStage.GENERATED` — `can_be_counted_as_solved()` = False |
| not counted in score | Yes — candidate probe |
| scene_spec | grid_size [10,10], bg=0, 1 hollow rectangle (border only) color=2 pos=[2,2] size=[5,5], 1 distractor color=2 pos=[8,0] size=[1,1], noise=0 |
| diagnostic value | Tests conditional hole-filling. Shows whether conditional transform produces correct branch output. |
| promotion evidence | If conditional branching is deterministic, oracle/solver agree, and both branches differ, supports cond_if_holes_fill promotion. |
| counted as semantic solved | No |

#### T120_109

| Field | Value |
|-------|-------|
| task_id | `T120_109` |
| primitive_sequence | `['rel_swap_positions', 'recolor', 'transform']` |
| candidate_primitive | `rel_swap_positions` (family: relation_transform, expression: `Φ(rel(swap),obj_A,obj_B)⇒translate`) |
| unpromoted_status | `PromotionStage.GENERATED` — `can_be_counted_as_solved()` = False |
| not counted in score | Yes — candidate probe |
| scene_spec | grid_size [12,12], bg=0, 2 objects: rect color=1 pos=[1,1] size=[3,3], rect color=2 pos=[8,8] size=[3,3], 0 distractors, noise=0 |
| diagnostic value | Tests relational position swap between two objects. Shows whether relation transform creates novel, correct output. |
| promotion evidence | If swap is deterministic, oracle/solver agree, and output differs from no-op, supports rel_swap_positions promotion batch 3. |
| counted as semantic solved | No |

#### T120_110

| Field | Value |
|-------|-------|
| task_id | `T120_110` |
| primitive_sequence | `['mask_complement', 'extract_boundary', 'recolor']` |
| candidate_primitive | `mask_complement` (family: mask_algebra, expression: `Ω(¬mask)⇢invert`) |
| unpromoted_status | `PromotionStage.GENERATED` — `can_be_counted_as_solved()` = False |
| not counted in score | Yes — candidate probe |
| scene_spec | grid_size [10,10], bg=0, 1 rectangle color=3 pos=[2,2] size=[5,5], 1 distractor color=3 pos=[8,8] size=[1,1], noise=0 |
| diagnostic value | Tests mask complement (inverting mask selection). Shows whether complement produces distinguishable output from direct mask. |
| promotion evidence | If complement is deterministic, oracle/solver agree, and differs from direct mask, supports mask_complement promotion. |
| counted as semantic solved | No |

### 5.4 Adversarial/Control Tasks (T120_111 – T120_120)

These 10 tasks test no-op, order, metadata stripping, output diversity, and regression safety. They use only accepted BH80 primitives and/or `color_invert`. These are scored.

#### T120_111

| Field | Value |
|-------|-------|
| task_id | `T120_111` |
| primitive_sequence | `['pattern_output', 'pattern_output', 'pattern_output']` |
| scene_spec | grid_size [6,6], bg=0, 1 rectangle color=1 pos=[1,1] size=[3,3], 0 distractors, noise=0 |
| expected semantic stress | Triple no-op-ish chain (pattern_output is near-identity). Tests that repeated pattern_output does not produce `[[1]]` and is deterministic. |
| anti-cheat expectation | Output must not be `[[1]]`. Must be deterministic. No-op control must differ from a real transform chain. |
| scored | Yes |
| purpose | Regression safety: near-identity chain must still produce valid, measurable output. |

#### T120_112

| Field | Value |
|-------|-------|
| task_id | `T120_112` |
| primitive_sequence | `['extract', 'rotate', 'extract']` |
| scene_spec | grid_size [10,10], bg=0, 1 rectangle color=2 pos=[2,2] size=[4,4], 1 distractor color=2 pos=[8,0] size=[1,1], noise=0 |
| expected semantic stress | Extract→rotate→extract: second extract after rotate may extract rotated region. Tests primitive-order sensitivity with repeated extract. |
| anti-cheat expectation | Order reversal (extract→rotate→extract vs extract→rotate→extract) is the same — but differs from rotate→extract→rotate. No `[[1]]`. |
| scored | Yes |
| purpose | Primitive-order control with repeated primitives. |

#### T120_113

| Field | Value |
|-------|-------|
| task_id | `T120_113` |
| primitive_sequence | `['count', 'count', 'count']` |
| scene_spec | grid_size [8,8], bg=0, 3 objects: rect color=1 pos=[0,0] size=[2,2], rect color=2 pos=[4,4] size=[1,1], rect color=3 pos=[6,6] size=[1,1], 0 distractors, noise=0 |
| expected semantic stress | Triple count chain. Tests that count produces deterministic, non-trivial output even when repeated. |
| anti-cheat expectation | No `[[1]]`. Output diversity: must differ from single-count. Metadata stripping: count must not leak task_id. |
| scored | Yes |
| purpose | Output diversity and metadata stripping control. |

#### T120_114

| Field | Value |
|-------|-------|
| task_id | `T120_114` |
| primitive_sequence | `['color_invert', 'color_invert', 'color_invert']` |
| scene_spec | grid_size [10,10], bg=0, 2 objects: rect color=1 pos=[1,1] size=[3,3], rect color=8 pos=[6,6] size=[2,2], 0 distractors, noise=0 |
| expected semantic stress | Triple color_invert. First invert: 1→9, 8→2. Second invert: 9→1, 2→8 (back to original). Third invert: 1→9, 8→2. Tests that odd-count inversion is non-identity and even-count is identity. |
| anti-cheat expectation | Output must differ from no-op (triple invert = single invert). Must differ from double invert (identity). No `[[1]]`. |
| scored | Yes |
| purpose | Tests color_invert self-composition and parity semantics. |

#### T120_115

| Field | Value |
|-------|-------|
| task_id | `T120_115` |
| primitive_sequence | `['crop', 'crop', 'crop']` |
| scene_spec | grid_size [12,12], bg=0, 1 rectangle color=4 pos=[3,3] size=[6,6], 0 distractors, noise=0 |
| expected semantic stress | Triple crop. Sequential cropping of already-cropped grid. Tests that repeated crop converges deterministically and does not produce `[[1]]`. |
| anti-cheat expectation | No `[[1]]`. Deterministic. Output must be measurable. |
| scored | Yes |
| purpose | Regression safety: repeated same-primitive chain must not collapse to default. |

#### T120_116

| Field | Value |
|-------|-------|
| task_id | `T120_116` |
| primitive_sequence | `['rotate', 'recolor', 'rotate']` |
| scene_spec | grid_size [10,10], bg=0, 1 rectangle color=1 pos=[2,2] size=[4,4], 1 distractor color=3 pos=[8,8] size=[1,1], noise=0 |
| expected semantic stress | Rotate→recolor→rotate: sandwich pattern. Tests that recolor between rotates is order-sensitive — reversing to recolor→rotate→recolor should differ. |
| anti-cheat expectation | Order reversal differs. No `[[1]]`. Output diversity. |
| scored | Yes |
| purpose | Primitive-order negative control with sandwich pattern. |

#### T120_117

| Field | Value |
|-------|-------|
| task_id | `T120_117` |
| primitive_sequence | `['extract_boundary', 'count', 'recolor']` |
| scene_spec | grid_size [8,8], bg=0, 1 rectangle color=2 pos=[1,1] size=[5,5], 2 distractors (color=2 pos=[0,7] size=[1,1], color=2 pos=[7,0] size=[1,1]), noise=0 |
| expected semantic stress | Extract boundary, count, recolor. Tests boundary+count+recolor with distractors present. |
| anti-cheat expectation | Distractors must not be ignored or leaked. No `[[1]]`. Output diversity from distractor pressure. |
| scored | Yes |
| purpose | Distractor pressure and output diversity audit. |

#### T120_118

| Field | Value |
|-------|-------|
| task_id | `T120_118` |
| primitive_sequence | `['remove_noise', 'normalize_position', 'count_objects']` |
| scene_spec | grid_size [12,12], bg=0, 2 objects: rect color=1 pos=[1,1] size=[3,3], rect color=1 pos=[8,8] size=[2,2], 2 distractors (color=1 pos=[0,11] size=[1,1], color=1 pos=[11,0] size=[1,1]), noise=5 |
| expected semantic stress | Noise removal, normalize position, count objects. Tests full pipeline with high noise + distractors. |
| anti-cheat expectation | No `[[1]]`. Noise must be deterministic. Count must not leak task metadata. |
| scored | Yes |
| purpose | High-noise regression safety and metadata stripping. |

#### T120_119

| Field | Value |
|-------|-------|
| task_id | `T120_119` |
| primitive_sequence | `['isolate_largest', 'color_invert', 'count']` |
| scene_spec | grid_size [10,10], bg=0, 3 objects: rect color=1 pos=[0,0] size=[2,2], rect color=3 pos=[3,3] size=[5,5], rect color=9 pos=[8,8] size=[1,1], 0 distractors, noise=0 |
| expected semantic stress | Isolate largest (5×5), color_invert (3→7, 9→1 on isolated grid), count. Tests promoted primitive + count composition. |
| anti-cheat expectation | No `[[1]]`. No-op differs. Order differs. color_invert must not leak metadata. |
| scored | Yes |
| purpose | Promoted primitive in adversarial position (before count — tests count-reads-inverted-grid). |

#### T120_120

| Field | Value |
|-------|-------|
| task_id | `T120_120` |
| primitive_sequence | `['transform', 'extract_object', 'pattern_output']` |
| scene_spec | grid_size [10,10], bg=0, 1 rectangle color=5 pos=[2,2] size=[4,4], 2 distractors (color=5 pos=[8,8] size=[1,1], color=5 pos=[0,9] size=[1,1]), noise=2 |
| expected semantic stress | Transform, extract object, pattern output. Tests full pipeline with noise + distractors + pattern generation. |
| anti-cheat expectation | No `[[1]]`. Noise deterministic. Distractors must not collapse output. Output diversity from multi-distractor + noise. |
| scored | Yes |
| purpose | Scene_spec read audit and output diversity with noise + distractors + pattern.

---

## 6. Scored vs Candidate-Probe Scoring Policy

### 6.1 Two Score Layers

**Layer A: Scored Semantic Layer**

| Property | Rule |
|----------|------|
| Includes | BH80 base (80) + promoted-native tasks (10) + old-primitive harder (10) + adversarial/control (10) |
| Scored total | 110 |
| semantic_exact | Grid equality: solver grid equals oracle grid (element-wise, dimension-wise) |
| structural_pass | Separate boolean, never reported as semantic_exact |
| `color_invert` | May be counted because it is promoted (`can_be_counted_as_solved()` = True) |
| Unpromoted primitives | Blocked from scored layer |

**Layer B: Candidate Probe Layer**

| Property | Rule |
|----------|------|
| Includes | 10 candidate-probe tasks (T120_101 – T120_110) |
| May be executed | Yes — for diagnostics |
| Can be counted as solved | No — `can_be_counted_as_solved()` must be False for all unpromoted candidates |
| Status reporting | Must report `candidate_probe`, `unpromoted`, or equivalent status |
| Score mixing | Never mixed into `semantic_exact` denominator |

### 6.2 Reporting Format

```
scored_exact: <N>/110
scored_total: 110
candidate_probe_total: 10
candidate_probe_solved: <M> (reported for diagnostics only, not counted)
overall_tasks: 120
```

If all 120 were scored (future, after candidate promotion):
```
semantic_exact: <N>/120
```

### 6.3 Unpromoted Primitive Blocking

For every task, the scorer must check:
1. Every primitive in the sequence has `can_be_counted_as_solved()` = True
2. If any primitive returns False, the task is classified as `candidate_probe`
3. `candidate_probe` tasks are excluded from `scored_exact` and `scored_total`
4. No exception for "almost promoted" or "oracle-only verified" primitives

---

## 7. `color_invert` Task Usage Summary

| Task | Sequence | color_invert position | Scene highlights | Why not BH80 duplicate |
|------|----------|----------------------|------------------|----------------------|
| T120_081 | extract→**color_invert**→recolor | Step 2 | 8×8, 2 colors + distractor | No BH80 task uses color_invert |
| T120_082 | **color_invert**→extract→rotate | Step 1 | 10×10, 2 objects | No BH80 task starts with color_invert |
| T120_083 | isolate_largest→**color_invert**→normalize_position | Step 2 | 12×12, edge case (color 5 = identity under invert) | Tests invert identity edge case |
| T120_084 | crop_object→**color_invert**→place_back | Step 2 | 10×10, crop context | Replaces transform with color_invert in crop chain |
| T120_085 | **color_invert**→isolate_largest→recolor | Step 1 | 10×10, 3 objects | Invert changes visual distinctiveness before selection |
| T120_086 | extract_boundary→**color_invert**→count | Step 2 | 8×8, boundary context | Replaces recolor_boundary with global invert |
| T120_087 | rotate→**color_invert**→crop | Step 2 | 10×10, 2 objects | Invert after geometric transform |
| T120_088 | mirror_object→**color_invert**→extract_changed_region | Step 2 | 10×10, color convergence | Invert creates color convergence with mirror |
| T120_089 | **color_invert**→crop→count_or_pattern | Step 1 | 8×8, noise=2 | Invert as preprocessing with noise |
| T120_090 | fill_region→**color_invert**→transform | Step 2 | 10×10, cross shape | Invert after fill, before transform |
| T120_114 | **color_invert**→**color_invert**→**color_invert** | All 3 | 10×10, parity test | Triple invert parity semantics |
| T120_119 | isolate_largest→**color_invert**→count | Step 2 | 10×10, 3 objects | Promoted primitive before count |

All `color_invert` usage is scored because `color_invert` is promoted.

---

## 8. Candidate Probe Policy

### 8.1 Candidate Probe Tasks Summary

| Task | Candidate primitive | Family | Expression | Diagnostic value |
|------|-------------------|--------|------------|------------------|
| T120_101 | `mask_border_only` | mask_algebra | `Ω(mask∧border)⇢color(2)` | Border-highlight on composed chain |
| T120_102 | `geom_flip_vertical` | geometry_transform | `γ(flip(axis=row))⇒reflect` | Vertical flip vs. mirror_object distinction |
| T120_103 | `topo_fill_holes` | topology_transform | `τ(fill(holes))⇒solid` | Hole-filling on hollow objects |
| T120_104 | `constr_draw_rect_around` | construction_transform | `ξ(draw(rect,bbox(obj)))⇒overlay` | Construction drawing around objects |
| T120_105 | `color_swap_1_2` | color_transform | `κ(swap(1,2))⇒recolor` | Color swap vs. no-op distinction |
| T120_106 | `sel_leftmost` | object_selector | `λG.Σ[obj|argmin(col)]⇒extract` | Leftmost selection vs. other selectors |
| T120_107 | `pat_row_alternate` | pattern_transform | `π(row_alternate(1,2))⇒pattern` | Row-alternating pattern generation |
| T120_108 | `cond_if_holes_fill` | conditional_transform | `κ(count(holes)>0)?fill_holes:identity` | Conditional branching correctness |
| T120_109 | `rel_swap_positions` | relation_transform | `Φ(rel(swap),obj_A,obj_B)⇒translate` | Relational position swap |
| T120_110 | `mask_complement` | mask_algebra | `Ω(¬mask)⇢invert` | Mask complement vs. direct mask |

### 8.2 Rules

1. No candidate probe is reported as `semantic_solved`
2. No candidate probe contributes to `scored_exact` or `scored_total`
3. Each candidate probe must report `candidate_probe: true` and `unpromoted: true` in its result metadata
4. `can_be_counted_as_solved()` must return `False` for every candidate primitive used
5. Candidate probes may provide diagnostic value: oracle output, solver output, grid comparison (for promotion evidence gathering)
6. Candidate probes may not: modify BH80 tasks, affect BH80 score, or be promoted without separate promotion pipeline

---

## 9. Scene Spec Requirements

All 40 new scene specs must be semantic-ready. Requirements:

| Requirement | Rule |
|-------------|------|
| No default `[[1]]` | No task materializes to `[[1]]` grid |
| Varied grid sizes | Range from 6×6 to 12×12 (not all 10×10) |
| Varied shapes | Rectangles, crosses, hollow rectangles (for topology/probe tasks) |
| Distractors where relevant | 13 of 40 new tasks have distractors |
| Edges/boundaries where relevant | Objects touching edges in T120_083, T120_097, T120_118 |
| Multi-object cases where relevant | 15 of 40 new tasks have 2+ objects |
| Color diversity | Especially for `color_invert` tasks: colors 1, 2, 3, 4, 5, 8, 9 used across tasks |
| Deterministic noise only where intended | T120_089 (noise=2), T120_091 (noise=3), T120_097 (noise=4), T120_118 (noise=5), T120_120 (noise=2) |

### Grid size distribution

| Size | Count |
|------|-------|
| 6×6 | 1 (T120_111) |
| 8×8 | 5 (T120_081, T120_086, T120_089, T120_107, T120_113) |
| 10×10 | 25 |
| 12×12 | 9 (T120_083, T120_091, T120_094, T120_097, T120_104, T120_109, T120_115, T120_118, T120_119 partial) |

### Color diversity for color_invert tasks

| Color | Appears in | Inversion result |
|-------|-----------|-----------------|
| 1 | T120_082, T120_085, T120_089, T120_114, T120_119 | 1→9 |
| 2 | T120_081, T120_086, T120_089 | 2→8 |
| 3 | T120_081, T120_084, T120_088, T120_119 | 3→7 |
| 4 | T120_081(distractor), T120_084, T120_087 | 4→6 |
| 5 | T120_083 (identity edge case), T120_120 | 5→5 (identity!) |
| 8 | T120_085, T120_089, T120_114 | 8→2 |
| 9 | T120_085, T120_089, T120_119 | 9→1 |

---

## 10. Anti-Cheat Preservation

### 10.1 Frozen BH80 Controls (preserved unchanged)

| # | Control | Preservation |
|---|---------|-------------|
| 1 | No `[[1]]` scenes | All 40 new scene specs avoid `[[1]]` materialization. Explicitly tested in T120_111 (near-identity) and T120_115 (repeated crop). |
| 2 | Oracle output diversity ≥ 20 | 40 new tasks add diverse outputs. Overall diversity must remain ≥ 20 across 120. |
| 3 | Solver output diversity ≥ 10 | 40 new tasks add diverse outputs. Overall diversity must remain ≥ 10 across 120. |
| 4 | No-op shadow control | Replacing any task's primitives with no-op chain must produce different oracle output. Tested in T120_111, T120_113, T120_114. |
| 5 | Primitive-order negative control | Reversing primitive order must produce different output. Tested in T120_112, T120_116. |
| 6 | Unsupported primitive sentinel | `fake_primitive` returns `unsupported` from both solver and oracle. Candidate probes must also handle unsupported gracefully. |
| 7 | Oracle avoids solver dispatch | Oracle module does not import or call solver dispatch. Native oracle (`native_arc_oracle.py`) also does not import solver. |
| 8 | Semantic scorer uses grid equality | `semantic_exact` = solver grid equals oracle grid. No change. |
| 9 | structural_pass separate | `structural_pass` is a separate boolean. No change. |

### 10.2 New Controls for 120

| # | Control | Requirement |
|---|---------|-------------|
| 10 | Unpromoted primitive counted-as-solved blocking | Any task containing an unpromoted primitive must be classified as `candidate_probe` and excluded from `scored_exact` |
| 11 | Candidate probe separation | `candidate_probe_total` reported separately from `scored_total` |
| 12 | Scene_spec read audit | All 120 tasks must actually read their scene_spec (no hardcoded grids) |
| 13 | Output diversity audit | Across all 120 tasks, oracle output diversity ≥ 30 and solver output diversity ≥ 20 |

---

## 11. 120 Gate Definitions

### 11.1 Scored Gates (110-task denominator)

| Level | Threshold | Rate | Action |
|-------|-----------|------|--------|
| Clean | 110/110 | 100% | No regression — proceed |
| Strong | ≥ 99/110 | 90% | Minimum for promotion and expansion |
| Preferred | ≥ 103/110 | 93.6% | May proceed to further expansion |
| Minimal | ≥ 94/110 | 85% | Absolute floor |
| Below minimal | < 94/110 | < 85% | Critical regression — block, investigate |

### 11.2 BH80 Sub-Gate (80-task subset)

| Level | Threshold | Action |
|-------|-----------|--------|
| Clean | 80/80 | No BH80 regression |
| Preferred | ≥ 75/80 | BH80 preferred gate intact |
| Strong | ≥ 72/80 | BH80 strong gate intact |
| Minimal | ≥ 68/80 | BH80 absolute floor |
| Below minimal | < 68/80 | Critical — rollback required |

### 11.3 Candidate Probe Reporting

| Metric | Reporting |
|--------|-----------|
| candidate_probe_total | 10 |
| candidate_probe_executed | ≤ 10 (may be unsupported) |
| candidate_probe_oracle_solver_agree | <N> (diagnostic only) |
| candidate_promoted_as_solved | Must be 0 |

### 11.4 All-120 Gates (future, after candidate promotion)

If all candidates are eventually promoted and all 120 are scored:

| Level | Threshold | Rate |
|-------|-----------|------|
| Clean | 120/120 | 100% |
| Strong | 108/120 | 90% |
| Preferred | 112/120 | 93.3% |
| Minimal | 102/120 | 85% |

---

## 12. Relationship to Future Promotion

### 12.1 Candidate Probe → Promotion Path

Candidate probes serve as **promotion evidence generators**. Each probe task provides:

1. **Oracle output**: If an oracle implementation exists for the candidate, the probe produces reference output
2. **Solver output**: If a solver wrapper exists, the probe produces solver output
3. **Grid comparison**: If both exist, grid equality can be checked (diagnostic only, not scored)
4. **Anti-cheat signals**: No-op control, order reversal, unsupported sentinel behavior on candidate primitives

### 12.2 Promotion from Probe to Scored

For a candidate probe to become a scored task:

1. **Oracle definition**: Implement independent oracle reference for the candidate primitive
2. **Solver targeting**: Implement solver dispatch wrapper for the candidate primitive
3. **Testing**: Verify oracle/solver agreement on positive examples
4. **Anti-cheat validation**: No-op, order, sentinel controls pass
5. **Regression safety**: BH80 remains ≥ 72/80 and scored-110 remains ≥ 99/110
6. **Audit artifacts**: All 12 mandatory artifacts produced
7. **Stage advancement**: Candidate advances through all 9 promotion stages to `PROMOTED`
8. **120 rerun**: Once promoted, the task moves from `candidate_probe` to `scored` and the 120 suite is rerun with updated scoring

### 12.3 Next Promotion Batch Candidates

Based on candidate probe diagnostic value:

| Batch | Candidates | Priority |
|-------|-----------|----------|
| 2 | `mask_border_only`, `geom_flip_vertical`, `topo_fill_holes`, `constr_draw_rect_around` | High — simple Grid→Grid, oracle < 50 lines |
| 3 | `color_swap_1_2`, `sel_leftmost`, `pat_row_alternate`, `cond_if_holes_fill` | Medium — more complex semantics |
| 4 | `rel_swap_positions`, `mask_complement` | Lower — multi-object or abstract |

### 12.4 9-Stage Promotion Pipeline (unchanged)

```
generated → typed → executable → oracle_defined → solver_targeted →
tested → anti_cheat_validated → regression_safe → promoted
```

No stage may be skipped. No candidate may be counted as solved until `PROMOTED`.

---

## 13. Next Lane Recommendation

**Expected next lane**: `IMPLEMENT_ARC_SYNTHETIC_DISCOVERY_120_WITH_NATIVE_LANGUAGE_GENERATOR_V1`

This lane should:
- Implement the 120-task generator (80 BH80 + 40 new)
- Implement scored vs candidate-probe scoring separation
- Implement unpromoted primitive blocking in scorer
- Implement candidate probe status reporting
- Implement 120-task gate checks
- Implement new anti-cheat controls (10–13)
- Not change any BH80 frozen component
- Not promote any new primitives
- Not run the 120 suite (implementation only)
- Validate with release gate, release check, health check

---

## 14. Forbidden Actions (This Lane)

- ❌ Implement generator code
- ❌ Create task files
- ❌ Run 120 suite
- ❌ Promote more primitives
- ❌ Count unpromoted candidates as solved
- ❌ Change BH80
- ❌ Weaken semantic scorer
- ❌ Weaken oracle separation
- ❌ Use public ARC data
- ❌ Use hidden/private ARC data
- ❌ Make ARC-AGI claims
- ❌ Touch runtime/chat/UI/provider paths
- ❌ Touch `.weslr`
- ❌ Push

---

## 15. Validation

| Check | Result |
|-------|--------|
| `git diff --check` | clean ✅ |
| `python weslr/tests/release_gate_v1.py` | `WESLR_RELEASE_GATE_V1_OK` ✅ |
| `./scripts/weslr_release_check.sh` | `WESLR_RELEASE_CHECK_OK` ✅ |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | PASS=6 FAIL=0 WARN=3 ✅ |

---

## 16. Receipt

| Field | Value |
|-------|-------|
| Start HEAD | `148d72fd` |
| End HEAD | `8e7baa71` |
| Commit | yes (`8e7baa71`) |
| Actual preflight HEAD | `148d72fd` |
| Metadata mismatch noted | yes — handoff HEAD stale (`8d38829c`); fallback HEAD (`cb9a8d0d`) does not match actual; receipt HEAD matches |
| BH80 frozen base preserved | yes ✅ |
| 40 new tasks specified | yes (T120_081–T120_120) ✅ |
| color_invert counted only as promoted | yes ✅ |
| Candidate probes marked unscored | yes (T120_101–T120_110) ✅ |
| Unpromoted primitives blocked from solved count | yes ✅ |
| Scored/probe scoring layers defined | yes (110 scored / 10 probe) ✅ |
| Scene_spec requirements semantic-ready | yes ✅ |
| Anti-cheat controls preserved | yes (9 frozen + 4 new) ✅ |
| 120 gates defined | yes (110-scored, 80-sub-gate, 120-future) ✅ |
| Validation | PASS ✅ |
| Push avoided | yes ✅ |
| Recommended next lane | `IMPLEMENT_ARC_SYNTHETIC_DISCOVERY_120_WITH_NATIVE_LANGUAGE_GENERATOR_V1` |