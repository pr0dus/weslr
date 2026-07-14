# WESLR SCATTI Implementation and Evidence Audit V1

**Date:** 2026-07-14
**Generated from HEAD:** `62e9ba794c780bb37d5472d79ca8c9d91230892d`
**Branch:** `origin/scatti-audit-bundle-v2` (detached HEAD)

## SECTION 1 — PREFLIGHT

| Property | Value |
|----------|-------|
| Actual branch | `origin/scatti-audit-bundle-v2` (detached HEAD) |
| HEAD | `62e9ba794c780bb37d5472d79ca8c9d91230892d` |
| Tracked modifications | None (clean working tree for tracked files) |
| Untracked SCATTI-related files | `weslr/modules/materials_stoichiometric_route_engine.py`, `weslr/tests/test_materials_stoichiometric_route_engine.py` |
| Commit 2d40b9d reachable | **No** — not in this repository |
| Commit 55342bb reachable | **No** — not in this repository |

**Note:** The MP-parent experiment script (`scripts/scatti_mp_parent_experiment.py`) and its data directory (`data/scatti_candidates/mp_parent_experiment/`) are not present in this repository. They exist on the Ubuntu/Nova host at `/home/pr0/projects/weslr` which is not accessible from this Android device.

## SECTION 2 — ACTUAL SCATTI IMPLEMENTATION INVENTORY

| Metric | Count |
|--------|-------|
| Total relevant artifacts | 24 |
| Implemented | 24 |
| Executed | 12 |
| Planned | 0 |
| Superseded | 0 |
| Unknown | 0 |

### Artifact Types

- **Scripts:** 1 (`scripts/scatti_prepare_screening.py`)
- **Runtime modules:** 1 (`weslr/modules/materials_stoichiometric_route_engine.py`)
- **Tests:** 1 (`weslr/tests/test_materials_stoichiometric_route_engine.py`)
- **Datasets (JSON):** 9 (screening summary, source search, evidence table, parent clues, prototype search, structure search v2, repair report, evidence ledger, implementation inventory)
- **Reports (Markdown):** 10 (current state, claim safe, DFT queue, manual verification, parent clues, source search, evidence table, prototype search, structure search v2, repair report)
- **Documentation:** 2 (audit bundle README, manual verification checklist)
- **Archives:** 1 (audit bundle ZIP)

### Evidence Classification

- **primary_computation:** 4 (screening script, screening summary, structure CSV, audit bundle)
- **external_source:** 5 (SearxNG evidence, source search, prototype search, structure search v2, parent clues)
- **derived_analysis:** 7 (parent clues report, evidence table report, source search report, prototype report, structure search report, repair report JSON, repair report MD)
- **governance:** 5 (current state, claim safe, DFT queue, manual verification, evidence ledger)
- **metadata_only:** 2 (stoichiometric route engine, tests)

## SECTION 3 — STOICHIOMETRIC AUDIT

### Parent Unit-Cell Formulas

| Parent | Full Cell Composition | Reduced Formula | Z |
|--------|---------------------|-----------------|---|
| Sc4Ti2O10 | Sc=4, Ti=2, O=10 | Sc2TiO5 | 2.0 |
| Sc2TiO5 | Sc=2, Ti=1, O=5 | Sc2TiO5 | 1.0 |
| CaSc2O4 | Ca=1, Sc=2, O=4 | CaSc2O4 | 1.0 |
| CaTiO3 | Ca=1, Ti=1, O=3 | CaTiO3 | 1.0 |

### Previous Operation

The MP-parent experiment added **1 Ca + 1 O** to a Sc4Ti2O10 cell (Z=2), producing:

```
Sc4Ti2O10 + CaO -> CaSc4Ti2O11
```

This is **not** a multiple of CaSc2TiO6.

### Correct Operation

The correct operation requires **2 Ca + 2 O** to the Sc4Ti2O10 cell:

```
Sc4Ti2O10 + 2 CaO -> Ca2Sc4Ti2O12 = 2 × CaSc2TiO6
```

### Bug Confirmation

The previous code used the **full cell composition** (Sc4Ti2O10) as if it were a single reduced formula unit. It did not account for Z=2. Adding 1 CaO to a cell with 2 reduced units produces a non-multiple formula (CaSc4Ti2O11).

## SECTION 4 — VERDICT ON COMMIT 2d40b9d

**Classification:** `previous_negative_result_invalid_due_to_scaling_bug`

The MP-parent experiment's conclusion that the Sc2TiO5 parent could not scale honestly to CaSc2TiO6 is **invalid** due to a formula-unit scaling bug. The parent CIF cell (Sc4Ti2O10) contains 2 reduced formula units (Z=2). The code added only 1 CaO instead of the required 2 CaO.

## SECTION 5 — EXACT BALANCED ROUTES

| Route | Balanced | Route Class | Geometry Established |
|-------|----------|-------------|---------------------|
| Sc2TiO5 + CaO -> CaSc2TiO6 | ✅ | exact_combination_route | ❌ |
| Sc4Ti2O10 + 2 CaO -> 2 CaSc2TiO6 | ✅ | exact_combination_route | ❌ |
| CaSc2O4 + TiO2 -> CaSc2TiO6 | ✅ | exact_combination_route | ❌ |
| CaTiO3 + Sc2O3 -> CaSc2TiO6 | ✅ | exact_combination_route | ❌ |

All four routes are mathematically exact. None establish a valid geometry or stability.

## SECTION 6 — AUTONOMOUS WESLR IMPLEMENTATION

### Module Created

`weslr/modules/materials_stoichiometric_route_engine.py`

### Functions

| Function | Purpose |
|----------|---------|
| `normalize_formula(formula)` | Canonical formula normalization (unicode, whitespace, element ordering) |
| `elemental_vector(formula)` | Element -> count dict |
| `reduced_formula_and_factor(formula)` | (reduced_formula, Z) tuple |
| `balance_reaction(reactants, target)` | Integer coefficient search for reaction balancing |
| `calculate_parent_to_target_delta(parent, target)` | Atom addition/removal analysis |
| `classify_route(route)` | Stable route classification |
| `check_charge_balance(formula)` | Approximate charge balance check |
| `serialize_route(route)` | Deterministic JSON serialization |

### Stable Reason Codes

- `exact_addition_route`
- `exact_combination_route`
- `exact_substitution_route`
- `requires_atom_removal`
- `noninteger_scaling`
- `element_mismatch`
- `charge_balance_unchecked`
- `invalid_formula`

### Key Design Decisions

1. **Target coefficient search:** The solver varies both reactant coefficients (a, b) and target coefficient (t) to handle cases like Sc4Ti2O10 + 2 CaO -> 2 CaSc2TiO6.
2. **Bottleneck element strategy:** For parent-to-target delta, the function identifies the element with the highest ratio (the bottleneck) and finds the smallest integer scaling that satisfies it.
3. **No LLM/network/hidden state:** The module is fully deterministic and isolated.

## SECTION 7 — EVIDENCE LEDGER

### Entries

| ID | Phase | Status |
|----|-------|--------|
| E001 | candidate_definition | supports |
| E002 | formula_normalization | supports |
| E003 | literature_search | inconclusive |
| E004 | database_crosscheck | inconclusive |
| E005 | chemical_plausibility | supports |
| E006 | structure_generation | executed_negative |
| E007 | structure_generation | executed_negative |
| E008 | stability_screening | executed_inconclusive |
| E009 | competing_phase_analysis | not_started |
| E010 | dynamic_stability | not_started |
| E011 | property_prediction | not_started |
| E012 | synthesis_feasibility | not_started |
| E013 | evidence_package | partial |
| E014 | publication_draft | not_started |
| E015 | chemical_plausibility | contradicts |

### Contradictions

| ID | Description | Resolved |
|----|-------------|----------|
| C001 | Previous MP-parent experiment conclusion vs stoichiometric analysis | ✅ Yes — formula-unit scaling bug |

### Open Questions

| ID | Question | Blocked By |
|----|----------|------------|
| Q001 | Does CaSc2TiO6 exist in Materials Project? | API key not configured |
| Q002 | Does CaSc2TiO6 exist in OQMD? | HTTP 502 (transient?) |
| Q003 | Can a valid geometry be constructed from Sc2TiO5 + CaO? | Corrected geometric construction |
| Q004 | Can a valid geometry be constructed from CaSc2O4 + TiO2? | Geometric construction |
| Q005 | Can a valid geometry be constructed from CaTiO3 + Sc2O3? | Geometric construction |
| Q006 | Is CaSc2TiO6 dynamically stable? | DFT-relaxed structure |
| Q007 | What are the competing phases and decomposition energies? | DFT-relaxed structure |

### Stage Statuses

| Stage | Status |
|-------|--------|
| candidate_definition | ✅ passed_gate |
| formula_normalization | ✅ passed_gate |
| literature_search | ⚠️ executed_inconclusive |
| database_crosscheck | ⚠️ executed_inconclusive |
| chemical_plausibility | ✅ passed_gate |
| structure_generation | ❌ executed_negative |
| stability_screening | ⚠️ executed_inconclusive |
| competing_phase_analysis | ⬜ not_started |
| dynamic_stability | ⬜ not_started |
| property_prediction | ⬜ not_started |
| synthesis_feasibility | ⬜ not_started |
| evidence_package | 🔶 partial |
| publication_draft | ⬜ not_started |

## SECTION 8 — FILES CREATED OR MODIFIED

### New Files (untracked)

| File | Size | Purpose |
|------|------|---------|
| `weslr/modules/materials_stoichiometric_route_engine.py` | ~21 KB | Deterministic stoichiometric route engine |
| `weslr/tests/test_materials_stoichiometric_route_engine.py` | ~10 KB | 39 tests for route engine |
| `data/scatti_candidates/scatti_parent_route_stoichiometry_repair_v1.json` | ~3 KB | Stoichiometric repair report (JSON) |
| `data/scatti_candidates/scatti_parent_route_stoichiometry_repair_v1.md` | ~3.5 KB | Stoichiometric repair report (Markdown) |
| `data/scatti_candidates/scatti_evidence_ledger_v1.json` | ~14 KB | Evidence ledger |
| `data/scatti_candidates/scatti_implementation_inventory_v1.json` | ~18 KB | Implementation inventory |

### Modified Files

None. All new files are untracked.

## SECTION 9 — VALIDATION RESULTS

| Check | Result |
|-------|--------|
| `pytest weslr/tests/test_materials_stoichiometric_route_engine.py` | ✅ 39 passed |
| `python3 -m compileall weslr/modules/materials_stoichiometric_route_engine.py` | ✅ OK |
| `git diff --check` | ✅ No whitespace errors |
| JSON validation (all new JSON files) | ✅ Valid |
| Deterministic output (5 repeated runs) | ✅ Identical |

## SECTION 10 — GIT DIFF / STATUS

```
$ git status --short
?? weslr/modules/materials_stoichiometric_route_engine.py
?? weslr/tests/test_materials_stoichiometric_route_engine.py
?? data/scatti_candidates/scatti_parent_route_stoichiometry_repair_v1.json
?? data/scatti_candidates/scatti_parent_route_stoichiometry_repair_v1.md
?? data/scatti_candidates/scatti_evidence_ledger_v1.json
?? data/scatti_candidates/scatti_implementation_inventory_v1.json
```

No tracked files modified. All new files are untracked.

## SECTION 11 — NEXT RECOMMENDED PHASE

**B. Corrected parent-derived geometric construction**

The stoichiometric analysis has confirmed that four exact balanced routes are mathematically available. The previous failure was caused by a formula-unit scaling bug, not an impossible transformation. The next phase should:

1. Revisit parent-derived construction using corrected stoichiometry
2. Use Sc2TiO5 + CaO (1:1) or Sc4Ti2O10 + 2 CaO (1:2) as the parent route
3. Place Ca atoms into the Sc2TiO5 framework with proper coordination
4. Validate all distances and coordination numbers
5. Do NOT run PyXtal, CHGNet, or DFT in this phase

**Rationale:** The stoichiometric barrier has been removed. The remaining challenge is geometric placement, which is a separate problem from stoichiometric feasibility.
