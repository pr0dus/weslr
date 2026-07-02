# WESLR ARC Synthetic Discovery 140 — Design from 117/117 Clean Base (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_ARC_SYNTHETIC_DISCOVERY_140_FROM_117_CLEAN_BASE_V1`
**Start HEAD**: `56e3849c`
**Date**: 2026-07-02

---

## 1. Preflight

| Check | Result |
|-------|--------|
| `pwd` | `/data/data/com.termux/files/home/weslr-pr47-clean` ✅ |
| `git status` | one modified file (pre-existing timestamp drift) ✅ |
| `git branch --show-current` | `occ-discovery-doctrine-implementation-20260613` ✅ |
| `git rev-parse --short HEAD` | `56e3849c` ✅ matches expected |

---

## 2. Current Trusted State

| Metric | Value |
|--------|-------|
| BH80 semantic regression gate | 80/80 ✅ |
| Discovery 120 scored layer | 117/117 clean ✅ |
| Candidate probe total | 3 (all high-dup-risk 0.60) |
| Candidate probes counted as solved | 0 ✅ |
| Promoted native primitives | 8 |
| Family gaps (R6) | 0 |
| Anti-cheat controls | 13/13 pass |
| Batch 3 review verdict | VALID |

### Promoted native primitives (8)
`color_invert`, `constr_draw_rect_around`, `mask_complement`, `topo_fill_holes`, `sel_leftmost`, `cond_if_holes_fill`, `rel_swap_positions`, `color_swap_1_2`

### Remaining candidate probes (3, all dup ≥ 0.60)
`mask_border_only` (dup 0.60 vs `extract_boundary`), `geom_flip_vertical` (dup 0.60 vs `transform`), `pat_row_alternate` (dup 0.60 vs `pattern_output`)

### Tracked risk
MEDIUM: pre-existing connected-components divergence between oracle CC and phase-2 adapter CC. Does not affect 117/117. Must be tested in expansion.

---

## 3. Expansion over Batch 4 — Justification

Expanding to 140 before promoting more candidates is preferred because:

1. **All 9 families already have promoted primitives** — Batch 4 would only add more primitives to already-covered families, increasing duplicate risk without testing generalization.
2. **The 117/117 base needs stress testing** — promoted primitives have only been tested in 3 scored tasks each (from the 120 suite). More compositions reveal whether they generalize.
3. **CC divergence needs exposure** — the MEDIUM risk should be tested before more promotion, not after.
4. **Low-dup-risk candidates need probe evidence** — 13 candidates with dup < 0.5 have no probe tasks. New probes give them composability evidence before Batch 4 consideration.
5. **Headroom for repair** — if the expansion exposes failures, they can be diagnosed and repaired before further promotion.

---

## 4. 140 Suite Composition

| Component | Count | Scored? | Source |
|-----------|-------|---------|--------|
| Frozen BH80 base (BH80_001–BH80_080) | 80 | Yes | Existing, unchanged |
| Prior promoted-native scored (T120_081–T120_090) | 10 | Yes | Existing, unchanged |
| Prior old-primitive harder (T120_091–T120_100) | 10 | Yes | Existing, unchanged |
| Prior adversarial/control (T120_111–T120_120) | 10 | Yes | Existing, unchanged |
| Prior promoted probe tasks (T120_103, T120_104, T120_105, T120_106, T120_108, T120_109, T120_110) | 7 | Yes | Existing, moved from probe to scored |
| **Prior 117 scored base** | **117** | **Yes (locked)** | **Sub-gate** |
| New scored: multi-native generalization (T140_121–T140_133) | 13 | Yes | New |
| Old remaining probes (T120_101, T120_102, T120_107) | 3 | No | Existing, kept as probe |
| New candidate probes (T140_134–T140_140) | 7 | No | New |
| **Total** | **140** | **130 scored / 10 probe** | |

---

## 5. New Scored Tasks (T140_121–T140_133)

### 5.1 Task Table

| Task ID | Primitive sequence | Category | Promoted native used | Scene stress |
|---------|-------------------|----------|---------------------|-------------|
| T140_121 | `color_invert`→`mask_complement`→`recolor` | multi-native chain | color_invert, mask_complement | 2 objects, multi-color |
| T140_122 | `sel_leftmost`→`constr_draw_rect_around`→`color_invert` | multi-native chain | sel_leftmost, constr_draw_rect_around, color_invert | 3 objects, leftmost selection then draw rect then invert |
| T140_123 | `topo_fill_holes`→`color_swap_1_2`→`extract` | native+BH80 chain | topo_fill_holes, color_swap_1_2 | Hollow rectangle, fill then swap then extract |
| T140_124 | `mask_complement`→`rel_swap_positions`→`rotate` | multi-native chain | mask_complement, rel_swap_positions | 2 objects, complement then swap then rotate |
| T140_125 | `cond_if_holes_fill`→`recolor_boundary`→`count` | native+BH80 chain | cond_if_holes_fill | Largest has hole, fill then boundary recolor then count |
| T140_126 | `constr_draw_rect_around`→`color_swap_1_2`→`crop` | multi-native chain | constr_draw_rect_around, color_swap_1_2 | Draw rect around object, swap 1↔2, crop |
| T140_127 | `color_invert`→`color_swap_1_2`→`mask_complement` | triple-native chain | color_invert, color_swap_1_2, mask_complement | 3-color grid, all 3 color primitives in sequence |
| T140_128 | `sel_leftmost`→`topo_fill_holes`→`normalize_position` | multi-native chain | sel_leftmost, topo_fill_holes | Leftmost has hole, fill then normalize |
| T140_129 | `rel_swap_positions`→`constr_draw_rect_around`→`recolor` | multi-native chain | rel_swap_positions, constr_draw_rect_around | 2 objects, swap then draw rect around new largest then recolor |
| T140_130 | `mask_complement`→`color_invert`→`extract_boundary` | multi-native chain | mask_complement, color_invert | Complement inverts mask, then color_invert, then boundary |
| T140_131 | `topo_fill_holes`→`constr_draw_rect_around`→`color_swap_1_2` | multi-native chain | topo_fill_holes, constr_draw_rect_around, color_swap_1_2 | Fill holes, draw rect, swap colors |
| T140_132 | `extract`→`cond_if_holes_fill`→`mask_complement` | native+BH80 chain | cond_if_holes_fill, mask_complement | Extract largest, conditional fill, complement |
| T140_133 | `color_swap_1_2`→`sel_leftmost`→`transform` | multi-native chain | color_swap_1_2, sel_leftmost | Swap 1↔2 changes which is leftmost, select, flip |

### 5.2 Promoted-Native Coverage Matrix

| Promoted primitive | 120 tasks | 140 new scored | Total scored |
|--------------------|----------|---------------|-------------|
| color_invert | T120_081–090 (10) + T120_114, T120_119 (2) | T140_121, T140_122, T140_127, T140_130 (4) | 16 |
| constr_draw_rect_around | T120_104 (1) | T140_122, T140_126, T140_129, T140_131 (4) | 5 |
| mask_complement | T120_110 (1) | T140_121, T140_124, T140_127, T140_130, T140_132 (5) | 6 |
| topo_fill_holes | T120_103 (1) | T140_123, T140_128, T140_131 (3) | 4 |
| sel_leftmost | T120_106 (1) | T140_122, T140_128, T140_133 (3) | 4 |
| cond_if_holes_fill | T120_108 (1) | T140_125, T140_132 (2) | 3 |
| rel_swap_positions | T120_109 (1) | T140_124, T140_129 (2) | 3 |
| color_swap_1_2 | T120_105 (1) | T140_123, T140_126, T140_127, T140_131, T140_133 (5) | 6 |

**All 8 promoted primitives covered in new scored tasks.** ✅

### 5.3 Composition Categories

| Category | Count | Description |
|----------|-------|-------------|
| Multi-native chain (2+ natives) | 9 | Tests native-to-native composition |
| Native + BH80 chain | 2 | Tests native-to-BH80 composition |
| Triple-native chain | 1 | Tests 3 natives in sequence |
| Order-sensitive | 13 | All designed to be order-dependent |

### 5.4 Adversarial/Control Features

| Feature | Tasks |
|---------|-------|
| No-op trap (output must differ from input) | All 13 |
| Order reversal trap | T140_127 (color chain: invert→swap→complement vs reverse differs) |
| Multi-object selection | T140_122, T140_128, T140_129, T140_133 |
| Hollow object | T140_123, T140_128, T140_131 |
| Color transformation cascade | T140_127, T140_130 |

---

## 6. Connected-Components Risk Tests

### 6.1 CC Divergence Sentinel Tasks

| Task ID | Primitive sequence | CC stress | Expected behavior |
|---------|-------------------|------------|------------------|
| T140_121 | color_invert→mask_complement→recolor | Diagonal adjacency after invert creates new adjacencies | May expose CC divergence if downstream uses CC |
| T140_124 | mask_complement→rel_swap_positions→rotate | Complement changes connectivity, then swap uses CC | Direct CC test — swap requires CC identification |
| T140_129 | rel_swap_positions→constr_draw_rect_around→recolor | Swap changes which object is largest, then draw rect uses CC | CC + selection interaction |
| T140_133 | color_swap_1_2→sel_leftmost→transform | Color swap changes which object is leftmost (if colors differ) | Selection + CC interaction |

### 6.2 CC Divergence Diagnostic Tasks (Candidate Probes)

| Task ID | Candidate | CC stress | Purpose |
|---------|-----------|-----------|---------|
| T140_137 | `geom_scale_2x` | Scale changes grid dimensions, may create new adjacencies | Dimension change CC stress |
| T140_138 | `topo_merge_objects` | Merge requires CC identification | Direct CC test — merge depends on CC |
| T140_139 | `constr_connect_line` | Drawing line between objects creates new connectivity | Connectivity creation CC stress |
| T140_140 | `topo_split_at_gap` | Split requires identifying narrowest gap in CC | Gap identification CC stress |

### 6.3 Scene Design for CC Stress

The implementation should include scene_specs with:
- **Diagonal adjacency**: objects placed at (r,c) and (r+1,c+1) — 4-connected = separate, 8-connected = same
- **Same-color touching**: two objects of same color separated by 1 bg cell — near-touching
- **Multiple components same color**: 3+ objects of same color at different positions
- **Large object + distractor**: well-separated, tests largest selection with distractors

---

## 7. New Candidate Probes (T140_134–T140_140)

### 7.1 Selection Strategy

Select 7 candidates from the low-dup-risk pool (dup < 0.5), prioritizing:
1. New families not yet probed (topology split, construction line, construction copy, pattern cycle, conditional edge)
2. Candidates that could fill cartographer R5 bridge gaps
3. Candidates that test CC divergence

### 7.2 Probe Task Table

| Task ID | Candidate | Family | Dup risk | Chain | Rationale |
|---------|-----------|--------|----------|-------|-----------|
| T140_134 | `geom_scale_2x` | geometry | 0.20 | geom_scale_2x→recolor→crop | Lowest dup risk, dimension change stress |
| T140_135 | `topo_merge_objects` | topology | 0.30 | topo_merge_objects→extract→recolor | New topology sub-capability, CC-dependent |
| T140_136 | `constr_connect_line` | construction | 0.20 | extract→constr_connect_line→recolor | Lowest dup risk, new construction sub-capability |
| T140_137 | `constr_copy_to_pos` | construction | 0.40 | constr_copy_to_pos→color_invert→crop | Construction + color chain, multi-object |
| T140_138 | `pat_color_cycle` | pattern | 0.40 | extract→pat_color_cycle→recolor | New pattern sub-capability, low dup |
| T140_139 | `cond_if_edge_clip` | conditional | 0.40 | cond_if_edge_clip→recolor→rotate | Conditional family extension, probe evidence |
| T140_140 | `topo_split_at_gap` | topology | 0.20 | topo_split_at_gap→recolor→count | Lowest dup risk, hardest topology, CC stress |

### 7.3 Probe Coverage

| Family | Existing probes | New probes | Total |
|--------|----------------|-----------|-------|
| Geometry | geom_flip_vertical (dup 0.60) | geom_scale_2x (dup 0.20) | 2 |
| Topology | — | topo_merge_objects (0.30), topo_split_at_gap (0.20) | 2 |
| Construction | — | constr_connect_line (0.20), constr_copy_to_pos (0.40) | 2 |
| Pattern | pat_row_alternate (dup 0.60) | pat_color_cycle (0.40) | 2 |
| Conditional | — | cond_if_edge_clip (0.40) | 1 |
| Extraction | mask_border_only (0.60) | — | 1 |

**All new probes have dup risk < 0.50.** The 3 old high-dup-risk probes remain as duplicate-risk controls.

---

## 8. Old Remaining Probe Handling

| Probe | Status | Classification |
|-------|--------|---------------|
| T120_101 (mask_border_only) | Kept as probe | Duplicate-risk control (dup 0.60 vs extract_boundary) |
| T120_102 (geom_flip_vertical) | Kept as probe | Duplicate-risk control (dup 0.60 vs transform) |
| T120_107 (pat_row_alternate) | Kept as probe | Duplicate-risk control (dup 0.60 vs pattern_output) |

These 3 probes:
- Remain unscored ✅
- Not counted as solved ✅
- Serve as duplicate-risk controls — if they accidentally pass, it would indicate semantic overlap with existing primitives
- Not eligible for promotion until duplicate risk is resolved or semantics are proven distinct

---

## 9. Gate Definitions

### 9.1 Scored Gates (130-task denominator)

| Gate | Threshold |
|------|-----------|
| Clean | 130/130 |
| Preferred | ≥ 122/130 |
| Strong | ≥ 117/130 |
| Minimal | ≥ 111/130 |

### 9.2 Mandatory Sub-Gates

| Sub-gate | Threshold | Description |
|----------|-----------|-------------|
| BH80 clean | 80/80 | Frozen BH80 base |
| Previous 117 scored base clean | 117/117 | All prior scored tasks remain exact |
| New 13 scored expansion clean target | 13/13 | All new scored tasks pass |
| Candidate probes counted as solved | 0 | Across all 10 probes |

### 9.3 Future All-140 Gate

| Gate | Threshold |
|------|-----------|
| Clean | 140/140 |
| Preferred | ≥ 131/140 |
| Strong | ≥ 126/140 |
| Minimal | ≥ 119/140 |

---

## 10. Anti-Cheat Expansion Controls

### Existing 13 controls (preserved)

All 13 existing controls remain: no `[[1]]`, output diversity, no-op shadow, primitive-order, unsupported sentinel, oracle avoids solver, grid equality, structural_pass separate, unpromoted blocked, candidate probe separation, scene_spec audit, output diversity audit, candidate probe counted-as-solved = 0.

### New expansion controls (5)

| # | Control | Description |
|---|---------|-------------|
| 14 | Duplicate-risk probe separation | Old 3 high-dup-risk probes separated from new 7 low-dup-risk probes in metadata |
| 15 | Promoted-native generalization coverage | Every promoted native must appear in at least 2 new scored tasks |
| 16 | CC divergence sentinel | At least 1 scored task must use CC-dependent primitive on a stress scene; if oracle/solver disagree, task fails (not silently passes) |
| 17 | Native-chain order sensitivity | At least 3 new scored tasks must produce different output when primitive order is reversed |
| 18 | Candidate-probe non-counting proof | All 10 probes (3 old + 7 new) must return result != semantic_exact or be unsupported |

---

## 11. Implementation Artifact Plan

| Artifact | Description |
|----------|-------------|
| 140 generator (`arc_discovery_140_generator.py`) | Generates 140 tasks: imports 117 existing + 3 old probes + 20 new |
| 140 semantic pilot extension | Update `arc_discovery_120_semantic_pilot.py` or create `arc_discovery_140_semantic_pilot.py` |
| Task composition report | Per-task: ID, group, scoring layer, primitive sequence, scene_spec |
| Scored/probe classification report | 130 scored / 10 probe breakdown |
| Sub-gate report | BH80 80/80, 117-base 117/117, new-13 13/13 |
| CC divergence sentinel report | Oracle vs solver CC comparison on stress scenes |
| Anti-cheat expansion report | All 18 controls verified |

---

## 12. Risk Analysis

| Risk | Severity | Mitigation |
|------|----------|------------|
| Overfitting to promoted primitives | MEDIUM | 13 new tasks cover diverse compositions, not just easy ones |
| Scoring too many easy compositions | LOW | Multi-native chains with 2-3 natives increase difficulty |
| Hiding CC divergence | MEDIUM | CC sentinel tasks + diagnostic probes explicitly test CC |
| Counting probes accidentally | LOW | Control #18 explicitly checks all 10 probes return non-exact |
| Duplicate-risk probes masquerading as progress | LOW | Old 3 probes remain unscored, classified as duplicate-risk controls |
| Weakening 117 base | LOW | 117 base is locked sub-gate; must remain 117/117 |
| Adding too much before CC repair | MEDIUM | 140 is measured expansion (only 20 new); CC repair can follow |
| New probe candidates failing unexpectedly | LOW | Probes are unscored — failures don't affect scored denominator |

---

## 13. Design Boundaries

This lane is **design-only**.

- ❌ No code implementation
- ❌ No task generation
- ❌ No primitive promotion
- ❌ No scoring changes
- ❌ No BH80 changes
- ❌ No oracle/solver behavior changes
- ❌ No CC divergence repair
- ❌ No candidate counted as solved
- ❌ No runtime/chat/UI/provider paths
- ❌ No `.weslr` IO
- ❌ No push

---

## 14. Validation

| Check | Result |
|-------|--------|
| `git diff --check` | clean ✅ |
| `python weslr/tests/release_gate_v1.py` | `WESLR_RELEASE_GATE_V1_OK` ✅ |
| `./scripts/weslr_release_check.sh` | `WESLR_RELEASE_CHECK_OK` ✅ |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | PASS=6 FAIL=0 WARN=3 ✅ |

---

## 15. Receipt

| Field | Value |
|-------|-------|
| Start HEAD | `56e3849c` |
| End HEAD | (design-only, commit with report) |
| Actual preflight HEAD | `56e3849c` |
| Metadata mismatch noted | no |
| Current trusted state summarized | yes ✅ |
| Expansion over Batch 4 justified | yes ✅ (5 reasons: families covered, generalization testing needed, CC divergence exposure, low-dup probes needed, headroom for repair) |
| 140 suite composition defined | yes ✅ (140 total, 130 scored, 10 probe) |
| Proposed total tasks | 140 |
| Proposed scored_total | 130 |
| Proposed candidate_probe_total | 10 |
| T140_121–T140_140 task table defined | yes ✅ (13 scored + 7 probe) |
| Promoted-native coverage defined | yes ✅ (all 8 primitives covered, minimum 2 new tasks each) |
| Connected-components risk tests defined | yes ✅ (4 sentinel scored + 4 diagnostic probes) |
| Old 3 probes remain unscored | yes ✅ |
| Candidate probes counted as solved 0 preserved | yes ✅ |
| 130-scored gates defined | yes ✅ (clean 130, preferred ≥122, strong ≥117, minimal ≥111) |
| BH80 sub-gate preserved | yes ✅ (80/80) |
| 117-base sub-gate preserved | yes ✅ (117/117) |
| Anti-cheat expansion controls defined | yes ✅ (5 new controls, total 18) |
| Validation | PASS ✅ |
| Push avoided | yes ✅ |
| Recommended next lane | `IMPLEMENT_ARC_SYNTHETIC_DISCOVERY_140_GENERATOR_V1` |