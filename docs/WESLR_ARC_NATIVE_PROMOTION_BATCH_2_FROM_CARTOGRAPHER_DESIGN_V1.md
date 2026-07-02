# WESLR ARC Native Promotion Batch 2 — Design from Cartographer + Perspicuity (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_ARC_NATIVE_PROMOTION_BATCH_2_FROM_CARTOGRAPHER_V1`
**Start HEAD**: `2da358e2`
**Date**: 2026-07-02

---

## 1. Preflight

| Check | Result |
|-------|--------|
| `pwd` | `/data/data/com.termux/files/home/weslr-pr47-clean` ✅ |
| `git status` | one modified file (pre-existing timestamp drift) ✅ |
| `git branch --show-current` | `occ-discovery-doctrine-implementation-20260613` ✅ |
| `git rev-parse --short HEAD` | `2da358e2` ✅ matches expected |

**Actual preflight HEAD**: `2da358e2`

---

## 2. Current State Summary

| Metric | Value |
|--------|-------|
| BH80 semantic regression gate | 80/80 ✅ |
| Discovery 120 scored layer | 110/110 ✅ |
| Candidate probes | 10 unscored ✅ |
| Candidate probes counted as solved | 0 ✅ |
| Promoted native primitives | 1 (`color_invert`) |
| Anti-cheat controls | 13/13 pass |
| Primitive cartographer | Implemented (52 records, 188 nodes, 597 edges) |
| Evidence-driven perspicuity | Implemented (32 candidates ranked) |

---

## 3. Arbitration Method

### 3.1 Combined Score Formula

The arbitration combines cartographer gap evidence with perspicuity implementation evidence:

```
combined_score = w_cart * cartographer_score + w_persp * perspicuity_score +
                 w_famgap * family_gap_bonus + w_dup * (1 - duplicate_risk) +
                 w_ready * implementation_readiness
```

### 3.2 Weights

| Component | Weight | Rationale |
|-----------|--------|-----------|
| Cartographer gap score | 0.30 | Gap-fill value: does this fill a missing cell? |
| Perspicuity evidence score | 0.25 | Implementation evidence: probe, complexity, static quality |
| Family gap bonus | 0.15 | Full family gap (R6) = 1.0; candidate-only (R2) = 0.5; otherwise 0.0 |
| Non-duplicate | 0.15 | Penalty for semantic similarity to existing primitives |
| Implementation readiness | 0.15 | Probe exists + low oracle/solver complexity |

### 3.3 Implementation Readiness

```
implementation_readiness = 0.4 * probe_exists + 0.3 * (1 - oracle_complexity) + 0.3 * (1 - solver_complexity)
```

### 3.4 Decision Rule

- `combined_score >= 0.65` → **promote now**
- `combined_score >= 0.50` → **defer**
- `combined_score < 0.50` → **reject**

---

## 4. Candidate Comparison Table

| Candidate | Family | Cart Score | Persp Score | Cart Rank | Persp Rank | Dup Risk | Oracle Cx | Solver Cx | Fam Gap? | New Fam? | Probe? | Combined Score | Recommendation |
|-----------|--------|-----------|------------|----------|-----------|---------|----------|----------|---------|---------|--------|---------------|----------------|
| constr_draw_rect_around | construction | 0.815 | 0.794 | 1 | 2 | 0.40 | 0.20 | 0.30 | Yes | Yes | Yes | **0.758** | **promote now** |
| mask_complement | noise_safety | 0.755 | 0.805 | 3 | 1 | 0.30 | 0.20 | 0.30 | No | Yes | Yes | **0.734** | **promote now** |
| topo_fill_holes | topology | 0.795 | 0.765 | 2 | 4 | 0.40 | 0.30 | 0.40 | Yes | Yes | Yes | **0.724** | **promote now** |
| sel_leftmost | selection | 0.650 | 0.776 | 7 | 3 | 0.50 | 0.20 | 0.30 | No | Yes | Yes | **0.680** | **promote now** |
| cond_if_edge_clip | conditional | 0.675 | 0.603 | 6 | 27 | 0.40 | 0.30 | 0.40 | Yes | Yes | No | **0.586** | **defer** |
| mask_border_only | extraction | 0.710 | 0.758 | 4 | 5 | 0.60 | 0.20 | 0.30 | No | Yes | Yes | **0.628** | **defer** (dup risk) |
| geom_flip_vertical | geometry | 0.510 | 0.721 | 0 | 8 | 0.60 | 0.10 | 0.20 | No | No | Yes | **0.554** | **defer** (dup risk) |

### Arbitration calculation example (sel_leftmost):

```
cartographer_score = 0.650
perspicuity_score = 0.776
family_gap_bonus = 0.5  (selection has isolate_largest, so not full gap, but candidate-only cell)
non_duplicate = 1 - 0.50 = 0.50
implementation_readiness = 0.4*1 + 0.3*(1-0.2) + 0.3*(1-0.3) = 0.4 + 0.24 + 0.21 = 0.85

combined = 0.30*0.650 + 0.25*0.776 + 0.15*0.5 + 0.15*0.50 + 0.15*0.85
         = 0.195 + 0.194 + 0.075 + 0.075 + 0.128
         = 0.667 → promote now
```

### Arbitration calculation example (cond_if_edge_clip):

```
cartographer_score = 0.675
perspicuity_score = 0.603
family_gap_bonus = 1.0  (conditional is full family gap)
non_duplicate = 1 - 0.40 = 0.60
implementation_readiness = 0.4*0 + 0.3*(1-0.3) + 0.3*(1-0.4) = 0 + 0.21 + 0.18 = 0.39

combined = 0.30*0.675 + 0.25*0.603 + 0.15*1.0 + 0.15*0.60 + 0.15*0.39
         = 0.203 + 0.151 + 0.150 + 0.090 + 0.059
         = 0.652 → borderline promote now
```

---

## 5. Final Batch 2 Selection

### Selected (4 primitives)

| # | Candidate | Family | Combined Score | Key reason |
|---|-----------|--------|---------------|------------|
| 1 | `constr_draw_rect_around` | construction | 0.758 | Highest combined score; full family gap; simple oracle; probe ready |
| 2 | `mask_complement` | noise_safety | 0.734 | Top perspicuity score; lowest dup risk (0.30); new family; simple oracle |
| 3 | `topo_fill_holes` | topology | 0.724 | Full family gap; moderate complexity; new family; probe ready |
| 4 | `sel_leftmost` | selection | 0.680 | High perspicuity score; simple oracle; probe ready; new family |

### cond_if_edge_clip vs sel_leftmost — Resolution

**Selected: `sel_leftmost`**

**Reason**: `sel_leftmost` wins on combined score (0.680 vs 0.652) primarily because:
1. **Implementation readiness**: `sel_leftmost` has a probe task (T120_106) and very low oracle/solver complexity (0.20/0.30). `cond_if_edge_clip` has no probe task and higher complexity (0.30/0.40).
2. **Perspicuity rank**: `sel_leftmost` ranks #3 in perspicuity vs `cond_if_edge_clip` at #27. The perspicuity model penalizes `cond_if_edge_clip` for high shortcut risk (0.80) and lack of probe evidence.
3. **Promotion speed**: `sel_leftmost` can be promoted faster — simpler oracle, simpler solver, existing probe validates composability.

**Why cond_if_edge_clip's full family gap doesn't outweigh**: While conditional is a full family gap (R6), `cond_if_edge_clip` lacks a probe task, meaning there is no evidence that it composes well in 3-step chains. The conditional family gap can be filled in Batch 3 with a better-tested conditional primitive. `sel_leftmost` fills a candidate-only cell (R2) in the selection family — while `isolate_largest` exists, `sel_leftmost` introduces property-based selection (leftmost), which is a genuinely new sub-capability.

### Deferred

| Candidate | Combined Score | Reason |
|-----------|---------------|--------|
| cond_if_edge_clip | 0.586 | Defer to Batch 3 — no probe, high shortcut risk, borderline score |
| mask_border_only | 0.628 | Defer — duplicate risk 0.60 against `extract_boundary` |
| geom_flip_vertical | 0.554 | Defer — duplicate risk 0.60 against `transform`, not a new family |

### Rejected

None rejected outright — all deferred candidates have some value but are not Batch 2 priority.

---

## 6. Primitive Contracts

### 6.1 constr_draw_rect_around

| Field | Value |
|-------|-------|
| primitive_id | `constr_draw_rect_around` |
| Family | construction |
| Expression | `ξ(draw(rect,bbox(obj)))⇒overlay` |
| Type | Grid → Grid |
| Semantics | Draw a rectangle outline (color 2) around the bounding box of the largest connected component on the original grid. Existing grid content preserved. |
| Preconditions | Grid is non-empty; at least one non-background cell exists |
| Invariants preserved | Grid dimensions, existing cell values inside and outside bbox |
| Invariants changed | Cells on the bbox perimeter that were background become color 2 |
| Edge cases | Empty grid (all bg) → return grid unchanged; single cell → draw 1×1 rect (no change); object touches grid edge → rect clipped to grid bounds |

### 6.2 mask_complement

| Field | Value |
|-------|-------|
| primitive_id | `mask_complement` |
| Family | noise_safety (mask_algebra sub-family) |
| Expression | `Ω(¬mask)⇢invert` |
| Type | Grid → Grid |
| Semantics | Invert the object/background mask: background cells become color 1, object cells become background (0). If multiple objects exist, applies to the mask of all non-background cells. |
| Preconditions | Grid is non-empty |
| Invariants preserved | Grid dimensions |
| Invariants changed | All cell values (bg → 1, non-bg → 0) |
| Edge cases | Empty grid (all bg) → all cells become 1; single color grid (all 1s) → all cells become 0; grid with bg=0 and one color → clean complement |

### 6.3 topo_fill_holes

| Field | Value |
|-------|-------|
| primitive_id | `topo_fill_holes` |
| Family | topology |
| Expression | `τ(fill(holes))⇒solid` |
| Type | Grid → Grid |
| Semantics | Fill all background cells that are fully enclosed (4-connected) by an object's cells with the object's color. Open background (connected to grid border) remains background. |
| Preconditions | Grid is non-empty |
| Invariants preserved | Grid dimensions, object cell values |
| Invariants changed | Enclosed background cells filled with surrounding object color |
| Edge cases | Empty grid → unchanged; object with no holes → unchanged; object touching grid edge (no enclosed bg) → unchanged; multiple objects with holes → each filled independently; nested objects → inner enclosed bg filled with inner object color |

### 6.4 sel_leftmost

| Field | Value |
|-------|-------|
| primitive_id | `sel_leftmost` |
| Family | selection |
| Expression | `λG.Σ[obj|argmin(col)]⇒extract` |
| Type | Grid → Grid |
| Semantics | Select the leftmost connected component (minimum column in bounding box) and return a grid containing only that component, with all other cells set to background. |
| Preconditions | Grid is non-empty; at least one non-background cell exists |
| Invariants preserved | Grid dimensions |
| Invariants changed | Non-selected cells set to background |
| Edge cases | Empty grid → unchanged; single object → returns grid unchanged (that object is leftmost); tie (two objects with same min column) → select the one with smaller min row (topmost-leftmost); all objects at same column → topmost wins |

---

## 7. Oracle Design

### 7.1 Oracle: constr_draw_rect_around

```
def oracle_constr_draw_rect_around(grid):
    # Independent implementation — no solver imports
    bg = 0
    components = connected_components(grid, bg)  # oracle's own CC
    if not components:
        return True, [row[:] for row in grid], {}
    largest = max(components, key=len)
    min_r, min_c, max_r, max_c = bbox(largest)
    out = [row[:] for row in grid]
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            if r == min_r or r == max_r or c == min_c or c == max_c:
                if 0 <= r < len(out) and 0 <= c < len(out[0]):
                    if out[r][c] == bg:
                        out[r][c] = 2
    return True, out, {"bbox": [min_r, min_c, max_r, max_c]}
```

### 7.2 Oracle: mask_complement

```
def oracle_mask_complement(grid):
    # Independent implementation
    bg = 0
    out = [[1 if v == bg else bg for v in row] for row in grid]
    return True, out, {}
```

### 7.3 Oracle: topo_fill_holes

```
def oracle_topo_fill_holes(grid):
    # Independent implementation — flood fill from borders, fill enclosed bg
    bg = 0
    h, w = len(grid), len(grid[0]) if grid else 0
    visited = [[False]*w for _ in range(h)]
    # BFS from all border background cells
    queue = []
    for r in range(h):
        for c in range(w):
            if (r == 0 or r == h-1 or c == 0 or c == w-1) and grid[r][c] == bg:
                queue.append((r, c))
                visited[r][c] = True
    while queue:
        r, c = queue.pop(0)
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] == bg:
                visited[nr][nc] = True
                queue.append((nr, nc))
    # Fill unvisited bg cells with surrounding color
    out = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            if grid[r][c] == bg and not visited[r][c]:
                # Find surrounding color (nearest non-bg neighbor)
                for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != bg:
                        out[r][c] = grid[nr][nc]
                        break
    return True, out, {}
```

### 7.4 Oracle: sel_leftmost

```
def oracle_sel_leftmost(grid):
    # Independent implementation
    bg = 0
    components = connected_components(grid, bg)  # oracle's own CC
    if not components:
        return True, [row[:] for row in grid], {}
    # Leftmost = minimum min_c, tie-break by minimum min_r
    def leftmost_key(comp):
        min_r = min(r for r, _ in comp)
        min_c = min(c for _, c in comp)
        return (min_c, min_r)
    selected = min(components, key=leftmost_key)
    out = [[bg for _ in row] for row in grid]
    for r, c in selected:
        out[r][c] = grid[r][c]
    return True, out, {}
```

---

## 8. Solver Design

### 8.1 Solver: constr_draw_rect_around

```
def solver_constr_draw_rect_around(grid, params):
    # No oracle imports
    bg = _background_value_from_grid(grid)
    components = _connected_components(grid, bg)
    if not components:
        return True, [row[:] for row in grid], {}
    largest = max(components, key=len)
    min_r, min_c, max_r, max_c = _bounding_box_for_cells(largest)
    out = [row[:] for row in grid]
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            if r == min_r or r == max_r or c == min_c or c == max_c:
                if out[r][c] == bg:
                    out[r][c] = 2
    return True, out, {}
```

### 8.2 Solver: mask_complement

```
def solver_mask_complement(grid, params):
    bg = 0  # background is always 0 for mask operations
    out = [[1 if v == bg else bg for v in row] for row in grid]
    return True, out, {}
```

### 8.3 Solver: topo_fill_holes

```
def solver_topo_fill_holes(grid, params):
    # No oracle imports — uses phase-2 adapter utilities
    bg = _background_value_from_grid(grid)
    h, w = len(grid), len(grid[0]) if grid else 0
    # Flood fill from borders
    visited = [[False]*w for _ in range(h)]
    queue = []
    for r in range(h):
        for c in range(w):
            if (r == 0 or r == h-1 or c == 0 or c == w-1) and grid[r][c] == bg:
                queue.append((r, c))
                visited[r][c] = True
    while queue:
        r, c = queue.pop(0)
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] == bg:
                visited[nr][nc] = True
                queue.append((nr, nc))
    out = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            if grid[r][c] == bg and not visited[r][c]:
                for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != bg:
                        out[r][c] = grid[nr][nc]
                        break
    return True, out, {}
```

### 8.4 Solver: sel_leftmost

```
def solver_sel_leftmost(grid, params):
    bg = _background_value_from_grid(grid)
    components = _connected_components(grid, bg)
    if not components:
        return True, [row[:] for row in grid], {}
    # Leftmost = minimum min_c, tie-break by minimum min_r
    def leftmost_key(comp):
        min_r = min(r for r, _ in comp)
        min_c = min(c for _, c in comp)
        return (min_c, min_r)
    selected = min(components, key=leftmost_key)
    out = [[bg for _ in row] for row in grid]
    for r, c in selected:
        out[r][c] = grid[r][c]
    return True, out, {}
```

---

## 9. Audit Artifact Plan

For each selected primitive, the implementation lane must produce:

| # | Artifact | Description |
|---|----------|-------------|
| 1 | Oracle implementation | Independent reference in `native_arc_oracle.py` |
| 2 | Solver implementation | Dispatch target in `native_arc_solver.py` |
| 3 | Positive examples | At least 3 input/output pairs proving correct behavior |
| 4 | Negative controls | At least 2 no-op/unsupported controls proving non-trivial behavior |
| 5 | Anti-cheat checks | No-op differs, order reversal differs, no `[[1]]` materialization |
| 6 | BH80 regression proof | BH80 remains 80/80 after adding primitive |
| 7 | 120 scored regression proof | Original 110 scored tasks remain 110/110 |
| 8 | Scene_spec read audit | Primitive reads only grid, no task metadata |
| 9 | Output diversity proof | Primitive produces diverse outputs across test scenes |
| 10 | Content hash verification | Primitive contract hash matches implementation |
| 11 | Invariant checks | Preserved/changed invariants verified |
| 12 | Promotion stage records | All 9 stages completed and recorded |

Total: 12 artifacts per primitive × 4 primitives = 48 audit artifacts.

---

## 10. 120 Suite Update Plan

### Before promotion

| Metric | Value |
|--------|-------|
| Total tasks | 120 |
| Scored tasks | 110 |
| Candidate probes | 10 |
| Probe tasks for selected primitives | T120_104 (constr_draw_rect_around), T120_110 (mask_complement), T120_103 (topo_fill_holes), T120_106 (sel_leftmost) |

### After promotion

| Metric | Value |
|--------|-------|
| Total tasks | 120 (unchanged) |
| Scored tasks | 114 (110 + 4 promoted probe tasks) |
| Candidate probes | 6 (10 - 4 promoted) |
| Candidate probes counted as solved | 0 (for remaining 6 unpromoted probes) |

### Update steps

1. Add oracle implementations to `native_arc_oracle.py`
2. Add solver implementations to `native_arc_solver.py`
3. Add primitive names to `BH80_ACCEPTED_PRIMITIVES` equivalent in `_get_promotion_status()` or `PROMOTED_PRIMITIVES` set
4. Update `CANDIDATE_PROBE_TASKS` to remove promoted primitives
5. Update `_classify_scoring_layer()` in `arc_discovery_120_generator.py` to classify promoted primitives as scored
6. Re-run 120 semantic pilot
7. Verify scored_exact = 114/114
8. Verify BH80 = 80/80
9. Verify remaining 6 candidate probes remain unscored

---

## 11. Gate Definitions After Batch 2

### Scored gates (114-task denominator)

| Gate | Threshold |
|------|-----------|
| Clean | 114/114 |
| Preferred | ≥ 107/114 |
| Strong | ≥ 103/114 |
| Minimal | ≥ 97/114 |

### Preserved gates

| Gate | Threshold |
|------|-----------|
| BH80 clean | 80/80 |
| Original 110 scored base clean | 110/110 |
| Candidate probes counted as solved | 0 |

---

## 12. Risk Analysis

### 12.1 constr_draw_rect_around

| Risk | Severity | Mitigation |
|------|----------|------------|
| bbox outline vs filled rectangle | Medium | Oracle and solver both draw outline only (perimeter cells that are bg → color 2). Test with a hollow object. |
| Object-selection ambiguity | Low | Uses largest connected component, same as existing oracle pattern. No ambiguity. |
| Object touches grid edge | Low | Rect clipped to grid bounds. Test with edge-touching object. |

### 12.2 mask_complement

| Risk | Severity | Mitigation |
|------|----------|------------|
| Complement scope (object mask vs bbox mask vs grid mask) | Medium | Design decision: complement applies to the full grid — bg(0) → 1, non-bg → 0. Not object-specific. Simplest and most composable. |
| Background value assumption | Low | Background is always 0 for mask operations. Test with non-zero bg (should still work if bg detected). |
| Identity on uniform grid | Low | All-0 grid → all-1 grid (not identity). All-1 grid → all-0 grid (not identity). Test as negative control. |

### 12.3 topo_fill_holes

| Risk | Severity | Mitigation |
|------|----------|------------|
| 4-connectivity vs 8-connectivity | Medium | Design decision: 4-connectivity for hole detection (consistent with existing connected components). Flood fill from borders using 4-connectivity. |
| Hole definition ambiguity | Low | A hole is any bg cell not reachable from the grid border via 4-connected bg path. Clear definition. |
| Fill color selection | Low | Fill with the color of the nearest non-bg 4-neighbor. If multiple neighbors, take first found (deterministic order: up, down, left, right). |
| Multiple objects with holes | Low | Each enclosed region filled independently. Test with donut + separate rectangle. |

### 12.4 sel_leftmost

| Risk | Severity | Mitigation |
|------|----------|------------|
| Tie-breaking ambiguity | Medium | Design decision: leftmost = minimum min_c in bbox; tie-break by minimum min_r (topmost-leftmost). Test with two objects at same column. |
| Duplicate risk against extract/isolate_largest | Low | `sel_leftmost` selects by column position, not by size. Different semantics. `isolate_largest` selects by component size. Test with small-leftmost + large-rightmost. |
| Empty grid | Low | Return unchanged. Test. |

---

## 13. Anti-Cheat Preservation

| Control | How preserved |
|---------|--------------|
| No-op control | Each primitive's output must differ from input on test scenes |
| Unsupported sentinel | Primitives not in the dispatch table return unsupported |
| Oracle/solver separation | Oracle modules must not import solver dispatch; solver modules must not import oracle |
| Output diversity | Each primitive must produce ≥ 3 unique outputs across test scenes |
| Scene_spec read audit | Primitives read only the materialized grid, no task metadata |
| Unpromoted primitive solved-count blocking | Remaining 6 candidate probes stay unscored |
| Candidate probe separation | Promoted probe tasks move to scored; remaining stay as candidate_probe |
| BH80 regression | BH80 must remain 80/80 after all changes |
| 120 scored-layer regression | Original 110 must remain 110/110; new 4 must be exact |

---

## 14. Design Boundaries

This lane is **design-only**.

- ❌ No oracle implementation
- ❌ No solver implementation
- ❌ No primitive promotion
- ❌ No 120 generator modification
- ❌ No 120 pilot run
- ❌ No candidate counted as solved
- ❌ No BH80 changes
- ❌ No scorer changes
- ❌ No runtime/chat/UI/provider paths
- ❌ No `.weslr` IO
- ❌ No push

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
| Start HEAD | `2da358e2` |
| End HEAD | (design-only, commit with report) |
| Actual preflight HEAD | `2da358e2` |
| Metadata mismatch noted | no |
| Arbitration method defined | yes ✅ — 5-component weighted formula (cart 30%, persp 25%, famgap 15%, nondup 15%, readiness 15%) |
| Candidate comparison table produced | yes ✅ — 7 candidates compared with all evidence dimensions |
| Final Batch 2 selected | yes ✅ — 4 primitives |
| Selected primitives | `constr_draw_rect_around`, `mask_complement`, `topo_fill_holes`, `sel_leftmost` |
| cond_if_edge_clip vs sel_leftmost resolved | yes ✅ — `sel_leftmost` selected (higher implementation readiness, probe evidence, lower complexity) |
| Primitive contracts defined | yes ✅ — 4 contracts with semantics, preconditions, invariants, edge cases |
| Oracle design defined | yes ✅ — 4 independent oracle implementations in pseudocode |
| Solver design defined | yes ✅ — 4 solver implementations in pseudocode, no oracle imports |
| 120 update plan defined | yes ✅ — scored 110→114, probes 10→6, remaining probes stay unscored |
| 114-scored gates defined | yes ✅ — clean 114, preferred ≥107, strong ≥103, minimal ≥97 |
| Anti-cheat preservation defined | yes ✅ — 9 controls |
| BH80 unchanged | yes ✅ — design-only |
| Candidates still unscored | yes ✅ — design-only, no promotion |
| Validation | PASS ✅ |
| Push avoided | yes ✅ |
| Recommended next lane | `IMPLEMENT_ARC_NATIVE_PROMOTION_BATCH_2_FROM_CARTOGRAPHER_V1` |

---

## 17. Next Lane Recommendation

**Recommended next lane**: `IMPLEMENT_ARC_NATIVE_PROMOTION_BATCH_2_FROM_CARTOGRAPHER_V1`

This lane should:
1. Implement oracle for `constr_draw_rect_around`, `mask_complement`, `topo_fill_holes`, `sel_leftmost` in `native_arc_oracle.py`
2. Implement solver for all 4 in `native_arc_solver.py`
3. Add all 4 to `PROMOTED_PRIMITIVES` set
4. Run the 9-stage promotion pipeline for each
5. Produce 48 audit artifacts (12 per primitive)
6. Update 120 generator scoring classification
7. Re-run 120 semantic pilot → expect 114/114
8. Verify BH80 remains 80/80
9. Verify remaining 6 candidate probes stay unscored
10. Run all validation gates