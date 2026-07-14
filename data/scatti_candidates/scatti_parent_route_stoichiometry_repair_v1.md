# SCATTI Parent Route Stoichiometry Repair V1

**Date:** 2026-07-14
**Target:** CaSc2TiO6
**Parent:** Sc4Ti2O10 (Sc2TiO5 × 2)
**Generated from HEAD:** `62e9ba794c780bb37d5472d79ca8c9d91230892d`

## Purpose

Audit the previous MP-parent experiment conclusion that the Sc2TiO5 parent could not scale honestly to CaSc2TiO6. Determine whether the failure was caused by a formula-unit scaling bug.

## Previous Conclusion

The MP-parent experiment concluded that the Sc2TiO5 parent could not scale honestly to CaSc2TiO6 because its CIF cell was Sc4Ti2O10. The observed wrong output was CaSc4Ti2O11.

## Stoichiometric Analysis

### Formula Unit Decomposition

| Formula | Reduced Formula | Z (units) | Full Cell Composition |
|---------|----------------|-----------|----------------------|
| Sc4Ti2O10 | Sc2TiO5 | 2.0 | Sc=4, Ti=2, O=10 |
| CaSc2TiO6 | CaSc2TiO6 | 1.0 | Ca=1, Sc=2, Ti=1, O=6 |
| Ca2Sc4Ti2O12 | CaSc2TiO6 | 2.0 | Ca=2, Sc=4, Ti=2, O=12 |
| CaSc4Ti2O11 | CaSc4Ti2O11 | 1.0 | Ca=1, Sc=4, Ti=2, O=11 |

### The Bug

The parent CIF cell (Sc4Ti2O10) contains **2 reduced formula units** (Z=2). The previous experiment added only **1 Ca + 1 O** to this cell, producing:

```
Sc4Ti2O10 + CaO -> CaSc4Ti2O11
```

This is **not** a multiple of CaSc2TiO6 because:
- CaSc4Ti2O11 has Sc=4, Ti=2, O=11
- 2 × CaSc2TiO6 has Ca=2, Sc=4, Ti=2, O=12
- Missing: 1 Ca, 1 O

### Correct Operation

The correct stoichiometric transformation requires adding **2 Ca + 2 O** to the Sc4Ti2O10 cell:

```
Sc4Ti2O10 + 2 CaO -> Ca2Sc4Ti2O12 = 2 × CaSc2TiO6
```

This is an **exact balanced route** with target coefficient 2.

## Exact Balanced Routes

| Route | Balanced | Route Class | Geometry Established |
|-------|----------|-------------|---------------------|
| Sc2TiO5 + CaO -> CaSc2TiO6 | ✅ | exact_combination_route | ❌ |
| Sc4Ti2O10 + 2 CaO -> 2 CaSc2TiO6 | ✅ | exact_combination_route | ❌ |
| CaSc2O4 + TiO2 -> CaSc2TiO6 | ✅ | exact_combination_route | ❌ |
| CaTiO3 + Sc2O3 -> CaSc2TiO6 | ✅ | exact_combination_route | ❌ |

All four routes are mathematically exact. None establish a valid geometry or stability.

## Verdict

**Classification:** `previous_negative_result_invalid_due_to_scaling_bug`

The previous failure was caused by a formula-unit scaling bug. The code added 1 CaO to a cell containing 2 reduced formula units. The correct operation requires 2 CaO to reach 2 × CaSc2TiO6.

## Superseded Statements

1. "The Sc2TiO5 parent could not scale honestly to CaSc2TiO6" — **superseded**. The scaling is mathematically exact when the formula-unit factor Z is correctly accounted for.
2. "Sc4Ti2O10 + CaO -> CaSc4Ti2O11 is the only possible outcome" — **superseded**. The correct outcome with 2 CaO is 2 × CaSc2TiO6.
3. "Parent-derived construction is mathematically impossible" — **superseded**. Four exact balanced routes are available.

## What This Does NOT Establish

- ❌ Does not establish a valid geometry
- ❌ Does not establish stability
- ❌ Does not prove CaSc2TiO6 exists
- ❌ Does not replace the need for database search, CSP, or DFT

## What This DOES Establish

- ✅ Parent-derived construction is stoichiometrically valid
- ✅ The previous failure was caused by a formula-unit scaling bug
- ✅ Four exact balanced routes are mathematically available
- ✅ Parent-derived construction should be revisited with corrected atom counts

## Next Recommended Phase

**Corrected parent-derived geometric construction** — revisit parent-derived construction using the corrected stoichiometry (2 CaO per Sc4Ti2O10 cell, or 1 CaO per Sc2TiO5 cell).
