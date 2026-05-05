# WESLR_PHASE_8.5 — Structural Classification Doctrine

**Status:** Active | **Applies to:** `unified_matter_generator.py` | **Effective:** 2026-05-05

---

## 1. Principle: Exact-Match Only

Structural type assignment is **conservative and exact**. A known structure type is assigned only when the formula's normalized stoichiometry matches a predefined pattern. All other compositions are marked `unclassified` with `uncertainty: high`.

**Rationale:** Loose heuristics that assign "layered_perovskite" to any AO + ABO₃ combination produce false confidence. CaO₆Sc₂Ti was previously labeled `layered_perovskite` despite not matching any known Ruddlesden–Popper or Aurivillius stoichiometry. This is now corrected.

---

## 2. STOICHIOMETRY_MAP — Canonical Keys

| Normalized Key | Structure Type | Example |
|---|---|---|
| `(1, 1, 3)` | `perovskite` | CaTiO₃ |
| `(2, 1, 4)` | `ruddlesden_popper_n1` | Ca₂TiO₄ |
| `(3, 2, 7)` | `ruddlesden_popper_n2` | (A₃B₂X₇) |
| `(4, 3, 10)` | `ruddlesden_popper_n3` | (A₄B₃X₁₀) |
| `(2, 1, 4)` | `spinel` | MgTi₂O₄ |
| `(1, 2)` | `rutile` | TiO₂ |
| `(1, 1)` | `rocksalt` | MgO |
| `(2, 4)` | `olivine` | Mg₂SiO₄ |
| `(1, 1, 4)` | `wolframite` | (A,B)XO₄ |
| `(1, 1, 6)` | `layered_double_hydroxide` | (approx.) |

**Key format:** `(sorted_cation_counts_desc..., anion_count)` — all integers divided by GCD.

### Ambiguity resolution for `(2, 1, 4)`:

Both `spinel` (AB₂X₄) and `ruddlesden_popper_n1` (A₂BX₄) yield the same normalized key `(2, 1, 4)`. Distinguishing heuristics:

- **Olivine** if any tetravalent p-block cation (Si, Ge, P, B) appears exactly once → `olivine`
- **RP n=1** if the most numerous cation is a large A-site element (Ca, Sr, Ba, La …) → `ruddlesden_popper_n1`
- **Otherwise** → `spinel` (most common AB₂X₄ structure)

---

## 3. `unclassified` Contract

When `_classify_structure()` returns `"unclassified"`:

| Field | Value |
|---|---|
| `geometry_type` | `"unclassified"` |
| `uncertainty` | `"high"` |
| `stability` | multiplied by **0.9** (10% penalty) |
| `device.disclaimer` | Present — warns the proposal is speculative |
| `device.structural_uncertainty` | `"high"` |
| `device.structure_classification` | `"unclassified"` |

No geometry-specific property estimate (e.g., Goldschmidt tolerance factor) is applied to unclassified structures.

---

## 4. `geometry_type` Values Emitted

| `geometry_type` | Meaning |
|---|---|
| `ABX3_cubic` | Exact perovskite match |
| `AB2X4_cubic` | Exact spinel match |
| `AX2_tetragonal` | Exact rutile match |
| `AX_cubic` | Exact rocksalt match |
| `orthorhombic_olivine` | Exact olivine match |
| `monoclinic_wolframite` | Exact wolframite match |
| `layered_perovskite` | RP n=1, n=2, n=3, or Aurivillius — all use this geometry type |
| `layered_double_hydroxide` | Exact LDH match |
| `unclassified` | No known stoichiometry match — high uncertainty |

---

## 5. Testing Requirements

All new structure types added to `STOICHIOMETRY_MAP` must include a corresponding test in `weslr/tests/weslr/test_unified_matter_generator.py`:

```python
def test_<structure>_exact_match():
    r, u = _classify_structure('<example_formula>')
    assert r == '<structure_type>'
    assert u == 'low'

def test_<structure>_uncertainty_flag():
    # unclassified cases
    ...
```

---

## 6. Change Log

| Date | Change |
|---|---|
| 2026-05-05 | Initial doctrine. `_classify_structure()` with exact stoichiometry matching replaces loose `geo_map` fallback. `unclassified` contracts defined. |