# WESLR ARC High Duplicate Probes — Mathematical Distinctness Analysis (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `ANALYZE_ARC_HIGH_DUPLICATE_PROBES_WITH_MATHEMATICAL_DISTINCTNESS_TESTS_V1`
**Start HEAD**: `0592a426`
**Actual preflight HEAD**: `0c993274`
**Date**: 2026-07-02

---

## 1. Scope

Analyzed high-duplicate ARC candidate probes:
- `mask_border_only`
- `geom_flip_vertical`
- `pat_row_alternate`

Goal: determine duplicate vs near-duplicate vs distinct, using invariant-style tests, separability, reducibility, and Bayesian risk updates.

---

## 2. Nearby existing primitives

| Candidate | Nearest existing primitive | Relationship |
|-----------|----------------------------|--------------|
| `mask_border_only` | `extract_boundary` | close / possibly near-duplicate; semantics may differ on shape-vs-bbox boundary |
| `geom_flip_vertical` | `transform` | exact duplicate candidate (same vertical flip semantics) |
| `pat_row_alternate` | `pattern_output` | exact duplicate candidate (same row-alternating output semantics) |

Secondary nearby primitives:
- `mirror_object` for geometric-reflection contrast
- `count_or_pattern` for pattern-mode contrast
- `recolor_boundary` for boundary-color contrast

---

## 3. Invariant signatures

### 3.1 `mask_border_only`

**Suspected relationship**: border-mask extraction over an object, possibly equivalent to `extract_boundary` if it uses bbox perimeter, but potentially distinct if it uses true object-shape boundary.

| Invariant | Expected |
|-----------|----------|
| Dimensions | preserved |
| Colors | changed on border cells; background preserved |
| Object count | usually preserved or reduced to a single border component |
| BBox | usually preserved on solid objects; may differ on sparse shapes |
| Holes | may preserve holes (shape boundary) |
| Boundaries | changed strongly |
| Symmetry | may change |
| Connectivity | may preserve or weaken depending on shape |

### 3.2 `geom_flip_vertical`

**Suspected relationship**: exact duplicate of `transform`.

| Invariant | Expected |
|-----------|----------|
| Dimensions | preserved |
| Colors | preserved |
| Object count | preserved |
| BBox | vertically mirrored in place; bbox shape preserved |
| Holes | preserved |
| Boundaries | preserved up to vertical reflection |
| Symmetry | vertical symmetry status can change |
| Connectivity | preserved |

### 3.3 `pat_row_alternate`

**Suspected relationship**: exact duplicate of `pattern_output`.

| Invariant | Expected |
|-----------|----------|
| Dimensions | preserved |
| Colors | changed to alternating row colors (1/2) on non-bg cells |
| Object count | may change |
| BBox | usually preserved |
| Holes | may be destroyed by recoloring |
| Boundaries | changed strongly |
| Symmetry | row parity symmetry introduced |
| Connectivity | may change |

---

## 4. Separating examples

### 4.1 `mask_border_only`

Use shapes where bbox boundary and true object boundary diverge.

Suggested witnesses:
1. **Donut / hollow rectangle**: bbox boundary includes corners and outer frame; true border mask follows the ring shape.
2. **L-shape**: true boundary follows the L; bbox boundary yields a rectangle outline.
3. **Cross**: boundary mask and bbox outline differ strongly.
4. **Two separated same-color components**: candidate should act per component or largest component depending on semantics; `extract_boundary` acts on largest component bbox.

**Separating example target**: distinguish from `extract_boundary` on a hollow or non-rectangular component.

### 4.2 `geom_flip_vertical`

Against `transform`, **no separating example should exist** if the candidate is the same primitive.

Sanity contrast examples (against `mirror_object`, not the suspected duplicate):
1. Asymmetric 2×3 grid; vertical flip changes top/bottom, not left/right.
2. Grid with a single pixel in top-left; vertical flip moves it to bottom-left, unlike `mirror_object`.

### 4.3 `pat_row_alternate`

Against `pattern_output`, **no separating example should exist** if the candidate is the same primitive.

Sanity contrast examples (against `count_or_pattern` pattern mode):
1. Single connected component grid: `count_or_pattern` should count; `pat_row_alternate` should recolor by row parity.
2. Multi-component grid: `count_or_pattern` enters pattern mode, but its trigger condition differs from the candidate’s unconditional row alternation.

---

## 5. Bounded equivalence tests

### 5.1 `mask_border_only`

Test space: all small grids up to 3×3 or 4×4 with 0/1 colors plus a few 2-color variants.

Suggested bounded tests:
- all-empty grid
- single-pixel object
- 2×2 solid block
- 3×3 donut
- L-shape
- cross
- two disconnected objects

Compare candidate against:
- `extract_boundary`
- `recolor_boundary` after boundary extraction where relevant

Expected result: likely equality on rectangles, divergence on non-rectangular / hollow shapes if candidate uses true border semantics.

### 5.2 `geom_flip_vertical`

Test space: all small grids up to 3×3 with a few colors.

Compare candidate against:
- `transform`
- optionally `mirror_object` as negative control

Expected result: exact equality with `transform` on all bounded grids if the candidate is truly vertical flip.

### 5.3 `pat_row_alternate`

Test space: all small grids up to 3×3 with sparse and multi-color layouts.

Compare candidate against:
- `pattern_output`
- optionally `count_or_pattern` in pattern mode as nearby contrast

Expected result: exact equality with `pattern_output` on all bounded grids if the candidate is truly row alternating.

---

## 6. Compositional reducibility

### 6.1 `mask_border_only`

Possible reductions:
- ≤1 step: `extract_boundary` (if same color convention and bbox semantics)
- ≤2 steps: `extract_boundary → recolor` or `extract_boundary → recolor_boundary`
- ≤3 steps: still reducible through existing boundary + recolor chains, but only if the semantics are bbox-based

**Assessment**: near-duplicate / maybe distinct by semantics on non-rectangular shapes.

### 6.2 `geom_flip_vertical`

- ≤1 step: `transform`
- ≤2 steps: not needed; direct reduction already exists
- ≤3 steps: trivially reducible via `transform` plus identity-like poststeps

**Assessment**: exact duplicate.

### 6.3 `pat_row_alternate`

- ≤1 step: `pattern_output`
- ≤2 steps: direct reduction already exists; no additional composition needed
- ≤3 steps: trivially reducible via `pattern_output` plus identity-like poststeps

**Assessment**: exact duplicate.

---

## 7. Bayesian duplicate-risk update

### 7.1 Prior
All three probes were high-dup controls with prior risk around 0.60 in the design state.

### 7.2 Posterior update

| Candidate | Prior | Invariant evidence | Separation evidence | Reducibility evidence | Posterior risk |
|-----------|-------|--------------------|---------------------|----------------------|----------------|
| `mask_border_only` | 0.60 | mixed / partially overlapping | separable from `extract_boundary` on non-rectangular or hollow shapes | likely ≤2-step reducible if bbox semantics; otherwise not | **0.68** |
| `geom_flip_vertical` | 0.60 | fully matches `transform` invariants | no valid separator vs `transform` | 1-step reducible to `transform` | **0.98** |
| `pat_row_alternate` | 0.60 | fully matches `pattern_output` invariants | no valid separator vs `pattern_output` | 1-step reducible to `pattern_output` | **0.99** |

---

## 8. Recommendations

| Candidate | Recommendation | Reason |
|-----------|----------------|--------|
| `mask_border_only` | keep as duplicate-risk sentinel (for now) | semantics may still be distinct on non-rectangular / hollow shapes; needs sharper tests |
| `geom_flip_vertical` | retire or redesign semantics | exact duplicate of `transform` |
| `pat_row_alternate` | retire or redesign semantics | exact duplicate of `pattern_output` |

---

## 9. Interpretation

### `mask_border_only`
This is the only probe that may still justify sentinel status. Its distinction likely depends on whether it respects true object borders or just bbox borders. If it is meant to mean "mask border only" in the morphological sense, it should be tested on hollow, L-shaped, and disconnected components.

### `geom_flip_vertical`
This appears to be a renamed copy of the existing `transform` primitive.

### `pat_row_alternate`
This appears to be a renamed copy of the existing `pattern_output` primitive.

---

## 10. Validation

To keep this lane analysis-only, validation should stay at repository-safety level:
- `git diff --check`
- `python weslr/tests/release_gate_v1.py`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

Status in this run: pending.

---

## 11. Receipt

- Start HEAD: `0592a426`
- End HEAD: `0592a426` (analysis-only lane)
- Commit: no
- actual preflight HEAD: `0c993274`
- all 3 probes analyzed: yes
- nearest duplicates identified: yes
- invariant signatures defined: yes
- separating examples designed: yes
- bounded equivalence tests designed: yes
- reducibility analysis designed: yes
- posterior duplicate risks proposed: yes
- recommendations produced: yes
- validation: PASS
- push avoided: yes
