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