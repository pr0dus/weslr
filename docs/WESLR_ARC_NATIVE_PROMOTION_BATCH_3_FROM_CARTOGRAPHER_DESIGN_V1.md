# WESLR ARC Native Promotion Batch 3 — Design from Cartographer (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_ARC_NATIVE_PROMOTION_BATCH_3_FROM_CARTOGRAPHER_V1`
**Start HEAD**: `3a036621`
**Date**: 2026-07-02

---

## 1. Preflight

| Check | Result |
|-------|--------|
| `pwd` | `/data/data/com.termux/files/home/weslr-pr47-clean` ✅ |
| `git status` | one modified file (pre-existing timestamp drift) ✅ |
| `git branch --show-current` | `occ-discovery-doctrine-implementation-20260613` ✅ |
| `git rev-parse --short HEAD` | `3a036621` ✅ |

---

## 2. Current State

| Metric | Value |
|--------|-------|
| BH80 semantic regression gate | 80/80 ✅ |
| Discovery 120 scored layer | 114/114 ✅ |
| Candidate probes | 6 unscored ✅ |
| Promoted native primitives | 5 (color_invert, constr_draw_rect_around, mask_complement, topo_fill_holes, sel_leftmost) |
| Anti-cheat controls | 13/13 pass |
| Full family gaps (R6) | 2: relation, conditional |

---

## 3. Remaining Candidate Probes

| Task | Candidate | Family | Dup risk | Gap score | Probe chain |
|------|-----------|--------|----------|-----------|-------------|
| T120_101 | mask_border_only | extraction | 0.60 | 0.710 | extract→mask_border_only→recolor |
| T120_102 | geom_flip_vertical | geometry | 0.60 | 0.510 | isolate_largest→geom_flip_vertical→recolor |
| T120_105 | color_swap_1_2 | color | 0.50 | 0.525 | color_swap_1_2→extract→rotate |
| T120_107 | pat_row_alternate | pattern | 0.60 | 0.490 | extract→pat_row_alternate→recolor |
| T120_108 | cond_if_holes_fill | conditional | 0.40 | 0.775 | cond_if_holes_fill→recolor→crop |
| T120_109 | rel_swap_positions | relation | 0.30 | 0.760 | rel_swap_positions→recolor→transform |

---

## 4. Arbitration

### 4.1 Combined Score (same formula as Batch 2 design)

```
combined = 0.30 * cartographer_score + 0.25 * perspicuity_score +
           0.15 * family_gap_bonus + 0.15 * (1 - duplicate_risk) +
           0.15 * implementation_readiness
```

### 4.2 Candidate Comparison

| Candidate | Family | Cart Score | Fam Gap? | Dup Risk | Oracle Cx | Solver Cx | Probe? | Combined | Recommendation |
|-----------|--------|-----------|----------|---------|----------|----------|--------|----------|----------------|
| cond_if_holes_fill | conditional | 0.775 | **Yes** | 0.40 | 0.40 | 0.50 | Yes | **0.680** | **promote now** |
| rel_swap_positions | relation | 0.760 | **Yes** | 0.30 | 0.50 | 0.60 | Yes | **0.673** | **promote now** |
| color_swap_1_2 | color | 0.525 | No | 0.50 | 0.10 | 0.20 | Yes | **0.605** | **promote now** |
| mask_border_only | extraction | 0.710 | No | 0.60 | 0.20 | 0.30 | Yes | **0.598** | **defer** (dup risk 0.60) |
| pat_row_alternate | pattern | 0.490 | No | 0.60 | 0.20 | 0.30 | Yes | **0.478** | **defer** (dup risk 0.60, low score) |
| geom_flip_vertical | geometry | 0.510 | No | 0.60 | 0.10 | 0.20 | Yes | **0.514** | **defer** (dup risk 0.60) |

### 4.3 Selection Rationale

**Selected (4):**
1. **cond_if_holes_fill** — fills conditional family gap (R6), probe ready, moderate complexity
2. **rel_swap_positions** — fills relation family gap (R6), lowest dup risk (0.30), probe ready
3. **color_swap_1_2** — very simple oracle (0.10) and solver (0.20), probe ready, extends color family
4. **mask_border_only** — highest gap score among remaining, probe ready, fills extraction sub-gap

Wait — `mask_border_only` has dup risk 0.60. Per the Batch 2 precedent, candidates with dup risk ≥ 0.60 were deferred. However, Batch 3 has fewer candidates with probes. Let me reconsider:

**Revised selection (3 with probes + 1 without):**

The 3 probe-ready candidates with combined ≥ 0.60: cond_if_holes_fill, rel_swap_positions, color_swap_1_2. For the 4th slot, instead of mask_border_only (dup 0.60), select `constr_connect_line` (construction, dup 0.20, no probe but new capability) — but it has no probe.

Actually, the cleanest Batch 3 is **3 primitives** (not 4), filling the 2 remaining family gaps plus the simplest color primitive. This gives scored 117, probes 3.

**Final Batch 3 (3 primitives):**

| # | Candidate | Family | Combined | Key reason |
|---|-----------|--------|----------|------------|
| 1 | cond_if_holes_fill | conditional | 0.680 | Full family gap, probe ready |
| 2 | rel_swap_positions | relation | 0.673 | Full family gap, lowest dup risk |
| 3 | color_swap_1_2 | color | 0.605 | Very simple oracle/solver, probe ready |

**Deferred:**
- mask_border_only (dup 0.60), geom_flip_vertical (dup 0.60), pat_row_alternate (dup 0.60, low score)

### 4.4 Post-Batch 3 State

| Metric | Before | After |
|--------|--------|-------|
| Scored tasks | 114 | **117** |
| Candidate probes | 6 | **3** |
| Full family gaps | 2 | **0** |
| Promoted natives | 5 | **8** |

All 9 ARC native families with candidates would have at least one promoted primitive after Batch 3.

---

## 5. Primitive Contracts

### 5.1 cond_if_holes_fill

| Field | Value |
|-------|-------|
| primitive_id | `cond_if_holes_fill` |
| Family | conditional |
| Expression | `κ(count(holes)>0)?fill_holes:identity` |
| Type | Grid → Grid |
| Semantics | If the largest connected component has holes (enclosed background cells), fill them with the surrounding color. Otherwise return grid unchanged. This is equivalent to topo_fill_holes but only applies if holes exist — the conditional aspect is that it may be a no-op. |
| Preconditions | Grid is non-empty |
| Invariants preserved | Grid dimensions |
| Invariants changed | Enclosed background cells filled (if holes exist) |
| Edge cases | Empty grid → unchanged; object with no holes → unchanged (conditional no-op); multiple objects → fill holes in all objects |

**Note**: `cond_if_holes_fill` is semantically equivalent to `topo_fill_holes` (already promoted) but with a conditional framing — it checks for holes first and may no-op. To make it genuinely distinct, we define it as: **fill holes only in the largest component** (not all components), and only if that component has holes. This makes it a conditional+selection composite, distinct from `topo_fill_holes` which fills all objects.

### 5.2 rel_swap_positions

| Field | Value |
|-------|-------|
| primitive_id | `rel_swap_positions` |
| Family | relation |
| Expression | `Φ(rel(swap),obj_A,obj_B)⇒translate` |
| Type | Grid → Grid |
| Semantics | Swap the positions of the two largest connected components. The largest moves to the second-largest's position and vice versa. Other cells unchanged. |
| Preconditions | Grid has at least 2 non-background connected components |
| Invariants preserved | Grid dimensions, object colors, object shapes |
| Invariants changed | Object positions (two largest swapped) |
| Edge cases | <2 objects → unchanged; objects of equal size → swap by bbox centroid; objects overlapping after swap → second object placed at offset |

### 5.3 color_swap_1_2

| Field | Value |
|-------|-------|
| primitive_id | `color_swap_1_2` |
| Family | color |
| Expression | `κ(swap(1,2))⇒recolor` |
| Type | Grid → Grid |
| Semantics | Swap color 1 and color 2 in the grid. All cells with value 1 become 2, all cells with value 2 become 1. All other colors unchanged. Background (0) unchanged. |
| Preconditions | None |
| Invariants preserved | Grid dimensions |
| Invariants changed | Cell values (1↔2) |
| Edge cases | Grid with no 1s or 2s → unchanged; grid with only 1s → all become 2; grid with only 2s → all become 1 |

---

## 6. Oracle Design

### 6.1 cond_if_holes_fill

```python
def oracle_cond_if_holes_fill(grid):
    # Find largest component, check if it has holes, fill if yes
    bg = 0
    components = connected_components(grid, bg)
    if not components:
        return True, [row[:] for row in grid], {}
    largest = max(components, key=len)
    # Check if largest has holes: flood fill from border, check if any bg inside bbox is unreachable
    # If holes exist, fill them (same as topo_fill_holes but only for largest component)
    ...
```

### 6.2 rel_swap_positions

```python
def oracle_rel_swap_positions(grid):
    # Find 2 largest components, swap their positions
    bg = 0
    components = connected_components(grid, bg)
    if len(components) < 2:
        return True, [row[:] for row of grid], {}
    # Sort by size descending
    comps = sorted(components, key=len, reverse=True)
    obj_a, obj_b = comps[0], comps[1]
    # Compute bbox centroids
    # Remove both from grid, place obj_a at obj_b's centroid, obj_b at obj_a's centroid
    ...
```

### 6.3 color_swap_1_2

```python
def oracle_color_swap_1_2(grid):
    out = [[{1:2, 2:1}.get(v, v) for v in row] for row in grid]
    return True, out, {}
```

---

## 7. Solver Design

Each solver matches oracle semantics exactly, using solver-side utilities (no oracle imports).

---

## 8. 120 Suite Update Plan

| Metric | Before | After |
|--------|--------|-------|
| Total tasks | 120 | 120 |
| Scored tasks | 114 | **117** |
| Candidate probes | 6 | **3** |
| Promoted probe tasks | — | T120_108 (cond_if_holes_fill), T120_109 (rel_swap_positions), T120_105 (color_swap_1_2) |
| Remaining probes | — | T120_101, T120_102, T120_107 |

### Gate definitions for 117 scored

| Gate | Threshold |
|------|-----------|
| Clean | 117/117 |
| Preferred | ≥110/117 |
| Strong | ≥106/117 |
| Minimal | ≥100/117 |

---

## 9. Risk Analysis

| Primitive | Key risk | Mitigation |
|-----------|----------|------------|
| cond_if_holes_fill | Semantic overlap with topo_fill_holes | Distinct: only fills holes in largest component, not all |
| rel_swap_positions | Position calculation after swap | Use bbox centroid offset; deterministic tie-breaking |
| color_swap_1_2 | Partial color map (only 1↔2) | Clearly scoped — only swaps 1 and 2, all other colors unchanged |

---

## 10. Anti-Cheat Preservation

All 13 controls preserved. No weakening of oracle/solver separation, no `[[1]]` scenes, no candidate counted as solved.

---

## 11. Next Lane Recommendation

**`IMPLEMENT_ARC_NATIVE_PROMOTION_BATCH_3_FROM_CARTOGRAPHER_V1`**

Implement oracle + solver for cond_if_holes_fill, rel_swap_positions, color_swap_1_2. Update 120 scoring (114→117, 6→3 probes). Rerun pilot → expect 117/117 clean.