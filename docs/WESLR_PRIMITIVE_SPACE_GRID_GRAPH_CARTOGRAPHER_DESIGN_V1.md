# WESLR Primitive-Space Grid/Graph Cartographer — Design (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_WESLR_PRIMITIVE_SPACE_GRID_GRAPH_CARTOGRAPHER_V1`
**Start HEAD**: `470f6453`
**Date**: 2026-07-02

---

## 1. Preflight

| Check | Result |
|-------|--------|
| `pwd` | `/data/data/com.termux/files/home/weslr-pr47-clean` ✅ |
| `git status` | one modified file (`weslr/tests/continuity/governance_scorecards.json` — auto-generated timestamp drift, pre-existing) ✅ |
| `git branch --show-current` | `occ-discovery-doctrine-implementation-20260613` ✅ |
| `git rev-parse --short HEAD` | `470f6453` |

**Actual preflight HEAD**: `470f6453`
**Metadata mismatch noted**: yes — expected HEAD `5455610e` is the prior lane's start HEAD, not the current chain HEAD. The perspicuity ranking lane (`cd82b9af` + `470f6453`) committed on top of `5455610e`. Fallback `83e325bc` is also stale. Actual HEAD `470f6453` is the correct current state.

---

## 2. Current State Summary

| Metric | Value |
|--------|-------|
| BH80 semantic regression gate | 80/80 ✅ |
| Discovery 120 scored layer | 110/110 ✅ |
| Candidate probes | 10 unscored ✅ |
| Candidate probes counted as solved | 0 ✅ |
| Promoted native primitives | 1 (`color_invert`) |
| BH80 accepted primitives | 20 |
| Total candidate primitives | 32 (9 families) |
| Anti-cheat controls | 13/13 pass |

---

## 3. Primitive-Space Grid Design

### 3.1 Concept

The primitive-space grid is a multi-dimensional coverage table — analogous to a periodic table or Sudoku grid — where each cell represents a (family × target × role × maturity) intersection. Filled cells show what exists; empty cells show what is missing; candidate-only cells show where promotion is needed.

The grid answers:
- What cells are covered?
- What cells are empty?
- What cells contain only unpromoted candidates?
- What cells have duplicates?
- What cells are high-value but missing?

### 3.2 Grid Axes

#### Axis A: Operation Family (14 categories)

| Code | Family | Description |
|------|--------|-------------|
| SEL | selection | Object selection by property |
| EXT | extraction | Object/region extraction |
| CRP | cropping | Grid cropping to bbox |
| COL | color | Color-space transforms |
| GEO | geometry | Geometric transforms |
| TOP | topology | Topology/connectivity transforms |
| CON | construction | Drawing/building new structures |
| REL | relation | Inter-object relational transforms |
| PAT | pattern | Pattern generation |
| CND | conditional | Conditional/branching transforms |
| CNT | counting | Counting and count-to-pattern |
| NRM | normalization | Position/size normalization |
| PLC | placement | Object placement on canvas |
| NSL | noise/safety | Noise removal, boundary safety |

#### Axis B: Target/Domain (10 categories)

| Code | Target | Description |
|------|--------|-------------|
| CELL | cell | Individual cell value |
| OBJ | object | Single connected component |
| OBJSET | object set | Multiple objects |
| MASK | mask | Binary mask |
| REGION | region | Bounding box / sub-area |
| BBOX | bounding box | Bbox of object/region |
| GRID | whole grid | Entire grid |
| PAT | pattern | Pattern structure |
| REL | relation | Relational structure |
| COUNT | count/output | Integer/count output |

#### Axis C: Transformation Role (9 categories)

| Code | Role | Description |
|------|------|-------------|
| SLR | selector | Selects/identifies target |
| RDC | reducer | Reduces dimensionality (grid → count, grid → mask) |
| EXP | expander | Expands dimensionality (count → pattern, mask → grid) |
| CST | constructor | Builds new structures |
| MOD | modifier | Modifies existing cells |
| CMP | comparator | Compares/detects properties |
| NRM | normalizer | Normalizes position/size |
| CPS | compositor | Composes multiple transforms |
| BRH | brancher | Conditional branching |

#### Axis D: Maturity (9 stages)

| Code | Stage | Description |
|------|-------|-------------|
| ACC | accepted BH80 | Fully accepted, in BH80 suite |
| PRM | promoted native | Fully promoted through 9-stage pipeline |
| GEN | generated candidate | Generated but not yet typed/executable |
| TYP | typed | Type signature validated |
| EXE | executable | Can be executed deterministically |
| ORC | oracle-defined | Independent oracle reference exists |
| SLV | solver-targeted | Solver dispatch target exists |
| TST | tested | Positive/negative tests pass |
| PRP | anti-cheat-promoted | All promotion stages complete |
| MIS | missing | No primitive exists for this cell |

### 3.3 Coverage Grid (Family × Maturity)

| Family | ACC (BH80) | PRM (native) | GEN (candidate) | MIS (missing) |
|--------|------------|-------------|----------------|---------------|
| SEL | 0 | 0 | 5 | 0 |
| EXT | 4 | 0 | 0 | 0 |
| CRP | 2 | 0 | 0 | 0 |
| COL | 1 | 1 | 3 | 0 |
| GEO | 1 | 0 | 3 | 0 |
| TOP | 0 | 0 | 3 | 2 |
| CON | 0 | 0 | 4 | 3 |
| REL | 0 | 0 | 3 | 3 |
| PAT | 1 | 0 | 3 | 0 |
| CND | 0 | 0 | 3 | 3 |
| CNT | 3 | 0 | 0 | 0 |
| NRM | 1 | 0 | 1 | 0 |
| PLC | 1 | 0 | 0 | 0 |
| NSL | 1 | 0 | 0 | 0 |

**Gap summary**: TOP, CON, REL, CND have zero accepted/promoted primitives — these are pure-candidate families. Their cells are candidate-only or missing.

### 3.4 Coverage Grid (Family × Target)

| Family × Target | OBJ | OBJSET | MASK | REGION | GRID | COUNT | CELL | BBOX | PAT | REL |
|-----------------|-----|--------|------|--------|------|-------|------|------|-----|-----|
| SEL | 5c | — | — | — | — | — | — | — | — | — |
| EXT | 2a | — | — | 1a | — | — | — | 1a | — | — |
| CRP | 1a | — | — | — | — | — | — | 1a | — | — |
| COL | — | — | — | — | 1a+1p+3c | — | — | — | — | — |
| GEO | — | — | — | — | 1a+3c | — | — | — | — | — |
| TOP | — | 1c | — | — | 2c | — | — | — | — | — |
| CON | 1c | — | — | 1c | — | — | — | 1c | 1c | — |
| REL | — | 2c | — | — | — | — | — | — | — | 1c |
| PAT | — | — | — | — | 1a+3c | — | — | — | — | — |
| CND | — | — | — | — | 1c | 1c | — | — | — | — |
| CNT | — | 1a | — | — | — | 2a | — | — | — | — |
| NRM | 1a | — | — | — | 1c | — | — | — | — | — |
| PLC | — | — | — | — | 1a | — | — | — | — | — |
| NSL | — | — | — | — | 1a | — | — | — | — | — |

Legend: `a` = accepted BH80, `p` = promoted native, `c` = candidate, number = count

**Key observations**:
- **OBJ (object target)**: SEL has 5 candidates but 0 accepted — large gap
- **OBJSET**: TOP and REL have candidates but 0 accepted — gap
- **MASK**: completely empty — no accepted, promoted, or candidate primitives target masks directly (mask_algebra candidates target GRID, not MASK as output)
- **BBOX**: EXT and CRP cover it; CON has one candidate — partially covered
- **REL (relation target)**: only 1 candidate, 0 accepted — gap
- **CELL**: completely empty — no primitive operates on individual cells (color transforms modify cells but target GRID)

### 3.5 Coverage Grid (Family × Role)

| Family × Role | SLR | RDC | EXP | CST | MOD | CMP | NRM | CPS | BRH |
|---------------|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| SEL | 5c | — | — | — | — | — | — | — | — |
| EXT | 4a | — | — | — | — | — | — | — | — |
| CRP | — | 2a | — | — | — | — | — | — | — |
| COL | — | — | — | — | 1a+1p+3c | — | — | — | — |
| GEO | — | — | — | — | 1a+3c | — | — | — | — |
| TOP | — | — | — | 1c | 2c | — | — | — | — |
| CON | — | — | — | 4c | — | — | — | — | — |
| REL | — | — | — | — | 3c | — | — | — | — |
| PAT | — | — | 1a+3c | — | — | — | — | — | — |
| CND | — | — | — | — | — | — | — | — | 3c |
| CNT | — | 3a | — | — | — | — | — | — | — |
| NRM | — | — | — | — | — | — | 1a+1c | — | — |
| PLC | — | — | — | 1a | — | — | — | — | — |
| NSL | — | — | — | — | 1a | — | — | — | — |

**Key observations**:
- **SLR (selector)**: only candidates, 0 accepted — entire role is unpromoted
- **CST (constructor)**: only candidates (CON family) and 1 accepted (PLC/place_back) — large gap
- **BRH (brancher)**: only candidates, 0 accepted — entire role is unpromoted
- **CMP (comparator)**: completely empty — no primitive compares or detects properties
- **RDC (reducer)**: well-covered by CNT family
- **NRM (normalizer)**: only 1 accepted + 1 candidate — thin

---

## 4. Primitive Graph Design

### 4.1 Graph Nodes

| Node type | Description | Examples |
|-----------|-------------|---------|
| `primitive` | An accepted or promoted primitive | `extract`, `color_invert` |
| `candidate` | An unpromoted candidate | `mask_border_only`, `sel_leftmost` |
| `task` | A task in BH80 or 120 suite | `BH80_001`, `T120_084` |
| `family` | A primitive family | `mask_algebra`, `object_selector` |
| `type_sig` | A type signature | `Grid→Grid`, `Grid→Count` |
| `invariant` | A preserved/changed invariant | "grid dimensions preserved" |
| `audit` | An audit artifact | "oracle_defined", "anti_cheat_validated" |
| `stage` | A promotion stage | `GENERATED`, `PROMOTED` |

### 4.2 Graph Edges

| Edge type | From → To | Meaning |
|-----------|-----------|---------|
| `composes_with` | primitive → primitive | These two primitives can appear in the same 3-step chain productively |
| `aliases_or_duplicates` | primitive → primitive/candidate | These primitives produce semantically similar output |
| `depends_on` | primitive → primitive | One primitive's semantics assumes the other was run first |
| `unlocks_task` | primitive → task | Promoting this primitive would make this task scoreable |
| `appears_in_task` | primitive → task | This primitive is used in a task's 3-step chain |
| `has_oracle` | primitive → audit | Oracle reference exists for this primitive |
| `has_solver` | primitive → audit | Solver dispatch target exists |
| `has_failure` | primitive → task | This primitive caused a failure in this task (oracle/solver mismatch) |
| `preserves_invariant` | primitive → invariant | This primitive preserves the given invariant |
| `changes_invariant` | primitive → invariant | This primitive changes the given invariant |
| `promoted_from_candidate` | primitive → candidate | This promoted primitive was originally this candidate |
| `family_member` | primitive → family | This primitive belongs to this family |
| `type_match` | primitive → type_sig | This primitive has this type signature |

### 4.3 Adjacency List (Composition Graph — Known Edges)

Edges derived from BH80 and 120 task chains (which primitives co-occur in 3-step sequences):

| Source | composes_with | Evidence |
|--------|---------------|---------|
| extract | rotate | BH80_001, BH80_002, T120_082 |
| extract | recolor | BH80_003, T120_081 |
| extract | color_invert | T120_081, T120_086 |
| extract | count_or_pattern | T120_089 |
| isolate_largest | normalize_position | BH80_006 |
| isolate_largest | recolor | BH80_006, T120_085 |
| isolate_largest | color_invert | T120_083 |
| crop_object | transform | BH80_007, BH80_008 |
| crop_object | place_back | BH80_007, T120_084 |
| crop_object | color_invert | T120_084 |
| crop_object | mirror_object | T120_093 |
| extract_boundary | recolor | BH80_005 |
| extract_boundary | count | BH80_005 |
| extract_boundary | color_invert | T120_086 |
| mirror_object | recolor | T120_088 |
| mirror_object | extract_changed_region | T120_088 |
| rotate | color_invert | T120_087 |
| rotate | crop | T120_087 |
| remove_noise | extract_boundary | T120_091 |
| fill_region | color_invert | T120_090 |
| fill_region | transform | T120_090 |
| recolor | count | T120_092 |
| recolor_boundary | count_objects | T120_092 |
| count_objects | pattern_output | T120_094 |
| pattern_output | crop | T120_095 |
| normalize_position | count | T120_096 |
| normalize_position | recolor | T120_097 |
| count | recolor | T120_098 |
| count_objects | place_back | T120_099 |
| place_back | crop | T120_100 |
| place_back | transform | BH80_058 |
| crop_object | recolor_boundary | T120_093 |
| isolate_largest | extract | T120_102 (probe) |
| extract | recolor | T120_101 (probe) |

### 4.4 Hub Analysis

| Primitive | Out-degree (composes_with) | Hub type |
|-----------|---------------------------|----------|
| recolor | 8 | **Major hub** — most composed-with |
| extract | 6 | **Major hub** — second most composed |
| crop_object | 5 | **Moderate hub** |
| color_invert | 5 | **Moderate hub** (promoted native) |
| isolate_largest | 4 | Moderate hub |
| rotate | 3 | Minor hub |
| place_back | 3 | Minor hub |
| extract_boundary | 3 | Minor hub |
| normalize_position | 3 | Minor hub |
| transform | 3 | Minor hub |

**Observation**: `recolor` and `extract` are central hubs. Any new primitive that composes with these hubs has high task-space value. The candidate probes (T120_101–T120_110) all chain with either `extract` or `recolor`, confirming hub connectivity.

### 4.5 Isolated Primitives

| Primitive | Composition edges | Status |
|-----------|-------------------|--------|
| fill_region | 2 (T120_090 only) | Low connectivity |
| remove_noise | 1 (T120_091 only) | Low connectivity |
| count | 2 | Low-moderate |
| pattern_output | 2 | Low-moderate |

These primitives appear in few chains. New primitives that compose with `fill_region`, `remove_noise`, or `pattern_output` could increase graph connectivity.

### 4.6 Near-Duplicate Edges

| Primitive A | Primitive B | Similarity | Edge type |
|------------|------------|-----------|-----------|
| crop | crop_object | 0.9 | aliases_or_duplicates (same semantics after repair) |
| extract | extract_object | 0.9 | aliases_or_duplicates (same semantics) |
| transform | geom_flip_vertical | 0.6 | aliases_or_duplicates (both flip) |
| extract_boundary | mask_border_only | 0.6 | aliases_or_duplicates (border extraction) |
| normalize_position | geom_translate_center | 0.7 | aliases_or_duplicates (centroid centering) |
| recolor | color_swap_1_2 | 0.5 | aliases_or_duplicates (color remap) |
| recolor | color_dominant | 0.5 | aliases_or_duplicates (color remap) |
| pattern_output | pat_row_alternate | 0.6 | aliases_or_duplicates (pattern generation) |

---

## 5. Sudoku-Like Gap Logic

### 5.1 Gap Detection Rules

| Rule | Condition | Action |
|------|-----------|--------|
| R1: Empty high-value cell | Cell exists in (family × target) with no primitive or candidate | Flag as missing |
| R2: Candidate-only cell | Cell has only candidates (no accepted/promoted) | Flag for promotion consideration |
| R3: Overpopulated cell | Cell has 3+ primitives with high mutual similarity (>0.5) | Flag for dedup |
| R4: Missing inverse | A primitive has no inverse/dual in the graph | Flag missing dual |
| R5: Missing composition bridge | Two hub primitives have no connecting primitive between them | Flag bridge gap |
| R6: Family with no promoted primitive | Entire family has 0 accepted/promoted | Flag family gap |
| R7: Family with no scored tasks | Family appears in 0 scored tasks | Flag task gap |
| R8: Isolated primitive | Primitive has < 2 composition edges | Flag for connectivity improvement |
| R9: Missing negative control | A primitive has no negative/no-op control task | Flag anti-cheat gap |

### 5.2 Detected Gaps

#### Rule R2: Candidate-only families

| Family | Candidates | Accepted | Promoted | Gap |
|--------|-----------|----------|----------|-----|
| SEL (selection) | 5 | 0 | 0 | **Full family gap** — no promoted selection primitive |
| TOP (topology) | 3 | 0 | 0 | **Full family gap** — no promoted topology primitive |
| CON (construction) | 4 | 0 | 0 | **Full family gap** — no promoted construction primitive |
| REL (relation) | 3 | 0 | 0 | **Full family gap** — no promoted relation primitive |
| CND (conditional) | 3 | 0 | 0 | **Full family gap** — no promoted conditional primitive |

#### Rule R1: Empty high-value cells

| Cell (family × target) | Status | Value |
|------------------------|--------|------|
| CON × BBOX | 1 candidate (`constr_draw_rect_around`) | High — drawing on bbox is common in ARC |
| TOP × OBJSET | 1 candidate (`topo_merge_objects`) | Medium — merging is useful but less common |
| REL × OBJSET | 2 candidates (`rel_align_centroids`, `rel_order_by_size`) | High — multi-object relations are common |
| CND × COUNT | 1 candidate (`cond_if_multi_count`) | Medium — conditional counting |
| SEL × OBJSET | 0 (no candidate even exists) | **Missing** — selecting from object sets |
| CMP × GRID | 0 (no candidate) | **Missing** — comparator/detector role entirely empty |
| MASK × (any) | 0 (mask as target, not just mask as tool) | **Missing** — no primitive outputs a mask |

#### Rule R4: Missing inverses

| Primitive | Inverse expected | Exists? |
|-----------|-----------------|---------|
| rotate (90° CW) | rotate (90° CCW) or rotate 3× | No — only CW rotation exists |
| mirror_object (horizontal flip) | mirror_object (vertical flip) | No — only horizontal exists |
| crop_object | expand/place_back | place_back is partial inverse |
| recolor (to color 2) | recolor (from 2 to original) | No — one-directional |
| color_invert (c → 10-c) | color_invert (10-c → c) | Yes — self-inverse ✅ |
| normalize_position | denormalize | No — no restore-original-position |
| fill_region (fill with 1) | clear_region | No — no inverse fill |

#### Rule R6: Family gap summary

| Family | Accepted | Promoted | Scored tasks using family | Gap severity |
|--------|----------|----------|--------------------------|-------------|
| SEL | 0 | 0 | 1 probe (T120_106) | **High** — 5 candidates ready, 0 promoted |
| TOP | 0 | 0 | 1 probe (T120_103) | **High** — 3 candidates ready, 0 promoted |
| CON | 0 | 0 | 1 probe (T120_104) | **High** — 4 candidates ready, 0 promoted |
| REL | 0 | 0 | 1 probe (T120_109) | **High** — 3 candidates ready, 0 promoted |
| CND | 0 | 0 | 1 probe (T120_108) | **High** — 3 candidates ready, 0 promoted |

---

## 6. Gap Scoring Model

### 6.1 Deterministic Gap Score Formula

Each gap cell receives a score:

```
gap_score = w1 * cell_empty + w2 * task_space_value + w3 * family_novelty +
            w4 * oracle_implementability + w5 * solver_implementability +
            w6 * (1 - duplicate_risk) + w7 * (1 - regression_risk) +
            w8 * anti_cheat_value + w9 * tasks_unlocked + w10 * probe_exists
```

### 6.2 Weights

| Weight | Component | Value | Rationale |
|--------|-----------|-------|-----------|
| w1 | cell empty (1=empty, 0.5=candidate-only, 0=filled) | 0.15 | Empty cells are highest priority |
| w2 | task-space expansion value | 0.15 | How much new task variety |
| w3 | family novelty (1=new family, 0=existing) | 0.10 | New families unlock more |
| w4 | oracle implementability (1-easy, 0=hard) | 0.10 | Easy oracle = fast promotion |
| w5 | solver implementability (1-easy, 0=hard) | 0.10 | Easy solver = fast promotion |
| w6 | non-duplicate (1-no dup, 0=full dup) | 0.10 | Avoid wasting promotion on duplicates |
| w7 | non-regression (1=safe, 0=risky) | 0.10 | Avoid breaking BH80/120 |
| w8 | anti-cheat value (1=adds control, 0=no new control) | 0.05 | Strengthens anti-cheat |
| w9 | tasks unlocked (normalized 0-1) | 0.10 | More unlocked = higher value |
| w10 | probe exists (1=yes, 0=no) | 0.05 | Probe proves composability |

### 6.3 Top-10 Gap Scores (Design Estimate)

| Rank | Cell | Gap type | Gap score | Rationale |
|------|------|----------|-----------|-----------|
| 1 | SEL × OBJ × SLR | Candidate-only family | 0.85 | 5 candidates, new family, simple oracle, probe exists |
| 2 | CON × BBOX × CST | Candidate-only | 0.82 | 1 candidate, new family, simple oracle, probe exists |
| 3 | TOP × OBJ × MOD | Candidate-only family | 0.78 | 3 candidates, new family, moderate oracle, probe exists |
| 4 | MASK × GRID × MOD | Candidate-only | 0.75 | mask_complement candidate, new family, simple oracle |
| 5 | COL × GRID × MOD | Candidate | 0.72 | color_swap_1_2, simple oracle, but existing recolor overlap |
| 6 | REL × OBJSET × MOD | Candidate-only family | 0.70 | 3 candidates, new family, harder oracle |
| 7 | PAT × GRID × EXP | Candidate | 0.68 | pat_row_alternate, existing pattern_output overlap |
| 8 | GEO × GRID × MOD | Candidate | 0.65 | geom_flip_vertical, existing transform overlap |
| 9 | CND × GRID × BRH | Candidate-only family | 0.62 | 3 candidates, new family, but high shortcut risk |
| 10 | CMP × GRID × CMP | Missing (no candidate) | 0.55 | Entirely missing role, but no candidate exists yet |

---

## 7. Integration with Perspicuity

### 7.1 Cartography Evidence for Perspicuity

The perspicuity ranking (`native_arc_perspicuity.py`) should incorporate cartography evidence:

| Evidence feature | From cartography | How used |
|-----------------|-----------------|----------|
| Fills missing cell | Gap detection (R1, R2) | Bonus to task_space_value |
| Reduces duplication | Near-duplicate edges | Penalty to duplicate_risk |
| Connects graph components | Hub/isolated analysis | Bonus to task_space_value |
| Unlocks new scored tasks | `unlocks_task` edges | Directly feeds expected_denominator_gain |
| Strengthens anti-cheat | R9 gap detection | Bonus to anti_cheat_value |
| Family gap fill | R6 family gap | Major bonus to task_space_value |
| Composition bridge | R5 bridge gap | Bonus for connecting hubs |

### 7.2 Updated Perspicuity Formula (Design)

```
evidence_score = static_perspicuity * 0.20 +
                 probe_availability * 0.10 +
                 promotion_ease * 0.15 +
                 task_space_value * 0.20 +
                 cartography_gap_fill * 0.10 +    # NEW
                 graph_connectivity * 0.05 +       # NEW
                 non_duplicate * 0.08 +
                 non_regression * 0.07 +
                 non_shortcut * 0.05
```

The cartography components add 15% total weight, redistributed from existing components. This means:
- Static perspicuity: 25% → 20%
- Promotion ease: 20% → 15%
- Non-duplicate: 10% → 8%
- Non-regression: 10% → 7%
- New: cartography_gap_fill (10%) + graph_connectivity (5%)

### 7.3 Gap-Fill Bonus Calculation

For each candidate, `cartography_gap_fill` = max of:
- 1.0 if candidate's family has 0 accepted/promoted (full family gap fill)
- 0.8 if candidate fills an empty high-value cell (R1)
- 0.6 if candidate fills a candidate-only cell (R2)
- 0.3 if candidate's cell is already partially covered
- 0.0 if candidate is in an overpopulated cell (R3)

### 7.4 Graph Connectivity Bonus

`graph_connectivity` = measure of how many new composition edges the primitive would create:
- 1.0 if primitive composes with 2+ major hubs that currently lack a bridge
- 0.5 if primitive composes with 1 major hub
- 0.0 if primitive only composes with non-hub primitives