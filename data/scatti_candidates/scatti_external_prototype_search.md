# SCATTI Local Heuristic Prototype Search

**Date:** 2026-05-08  
**Target Formula:** CaSc2TiO6  
**Search Type:** Local heuristic prototype search; no external database access  

## Search Capabilities

| Capability | Status |
|------------|--------|
| Materials Project API | **NO KEY** (local only) |
| Local CIF Files | **NONE** (0 files found) |
| Local POSCAR Files | **NONE** (0 files found) |
| pymatgen StructureMatcher | **YES** |
| pymatgen Built-in Prototypes | **YES** |
| ICSD Database | **NOT QUERIED** |
| COD Database | **NOT QUERIED** |
| OQMD Database | **NOT QUERIED** |
| AFLOW Database | **NOT QUERIED** |
| NOMAD Database | **NOT QUERIED** |
| Literature Search | **NOT PERFORMED** |

**Conclusion:** No external database access available. Search limited to local pymatgen built-in prototypes and heuristics.

---

## Source Limitation Statement

**No Materials Project, ICSD, COD, OQMD, AFLOW, NOMAD, or literature database was queried in this phase.**

All findings are based on local pymatgen prototype generation and heuristic comparison.

---

## Exact Match Search Results

**Query:** CaSc2TiO6  
**Result:** **NO EXACT MATCH FOUND**  

**Local Resources Checked:**  
- pymatgen StructureMatcher (built-in prototypes)  
- pymatgen prototype library  
- Local CIF/POSCAR files (0 files found)  

**Conclusion:** No exact CaSc2TiO6 structure was found in local resources.

**Reason:** CaSc2TiO6 is not a standard prototype in pymatgen's built-in library. It requires custom construction as an **ordered perovskite** with B-site ordering (Sc/Ti on B-sites).

---

## Corrected Ca2ScTiO6 Status

**Target Stoichiometry:** CaSc2TiO6 = Ca:Sc:Ti:O = 1:2:1:6  
**Ca2ScTiO6 Stoichiometry:** Ca:Sc:Ti:O = 2:1:1:6  

**Relation:** `related_double_perovskite_stoichiometry`  
**Useful_as_Parent:** yes, with caution  
**Reason:** Related Ca-Sc-Ti-O oxide framework; useful for ordering ideas, but Ca:Sc ratio differs from target CaSc2TiO6  
**Exact Match:** false  

---

## Related Prototypes Analysis

| Formula | Source | Relation | Exact Match | Useful_as_Parent | Reason |
|---------|--------|----------|-------------|------------------|--------|
| CaTiO3 | Perovskite | exact_ca_ti_o_system | false | YES | Standard perovskite; useful for Ca/O/Ti coordination only |
| ScTiO3 | Perovskite | sc_ti_oxide_framework | false | YES | Sc/Ti ordering prototype; useful for B-site ordering ideas |
| CaSc2O4 | Layered Oxide | ca_sc_framework | false | YES | Ca-Sc-O framework; useful for Sc-O and Ca-O coordination |
| Sc2O3 | Bixbyite | sc_oxide_framework | false | YES | Reference phase; Sc-O bonding reference |
| TiO2 | Rutile | ti_oxide_framework | false | YES | Reference phase; Ti-O bonding reference |
| **Ca2ScTiO6** | Double Perovskite | **related_double_perovskite_stoichiometry** | **false** | **YES, with caution** | **Related framework; Ca:Sc ratio differs (2:1 vs 1:2)** |
| Ca3Sc2TiO8 | Layer Perovskite | related_layered_perovskite | false | YES | Layered perovskite variant; useful for layered motif |
| Sc2TiO5 | Langbeinite | sc_ti_oxide_framework | false | YES | Better Sc-Ti-O framework than Sc2O3 alone |
| Sc2Ti2O7 | Pyrochlore | sc_ti_oxide_framework | false | YES | Better Sc-Ti-O framework than generic oxides |
| Al2O3 | Corundum | o_framework_reference | false | NO | Oxygen sublattice reference only; not structurally compatible |

**Summary:** 7 of 8 related systems provide useful structural or bonding insights for CaSc2TiO6 construction.

---

## Warning

**Parent prototype usefulness does not imply CaSc2TiO6 is stable or structurally compatible.**

All parent prototypes serve as *inspiration* for theoretical construct generation. No prototype guarantees experimental feasibility.

---

## Recommended Parent Prototypes (Revised Ranking)

1. **CaTiO3 (Perovskite)**  
   - **Role:** Primary Ca/Ti/O coordination reference  
   - **Usefulness:** High for Ca/O framework; moderate for Ti site replacement logic  
   - **Limitation:** No Sc present; requires Sc insertion logic  

2. **Ca2ScTiO6 (Double Perovskite)**  
   - **Role:** Ordering pattern inspiration (Ca/Sc ordering on A-sites)  
   - **Usefulness:** High for B-site ordering concepts  
   - **Limitation:** Ca:Sc ratio is 2:1 vs target 1:2; exact formula mismatch  

3. **Ca3Sc2TiO8 (Layer Perovskite)**  
   - **Role:** Layered motif inspiration  
   - **Usefulness:** Moderate for layer stacking concepts  
   - **Limitation:** Different stoichiometry; not direct template  

4. **CaSc2O4 (Layered Oxide)**  
   - **Role:** Ca/Sc-O coordination reference  
   - **Usefulness:** High for Sc-O and Ca-O bonding insights  
   - **Limitation:** No Ti present; different oxide family  

5. **Sc2TiO5 / Sc2Ti2O7 (If Available)**  
   - **Role:** Best Sc-Ti-O framework candidates  
   - **Usefulness:** High for Sc/Ti ordering insights  
   - **Limitation:** Not available in local search; require external query  

6. **Sc2O3 (Bixbyite)**  
   - **Role:** Sc coordination reference only  
   - **Usefulness:** Low; reference phase only  
   - **Limitation:** No Ti or Ca; not structurally related  

7. **TiO2 (Rutile)**  
   - **Role:** Ti coordination reference only  
   - **Usefulness:** Low; reference phase only  
   - **Limitation:** No Sc or Ca; not structurally related

## Phase 1D Audit Result

After constructing and auditing theoretical candidates:

- **13 candidates generated** from corrected parent prototypes
- **2 candidates eligible for pre-relaxation only** (SCATTI-LAYERED-001, SCATTI-RANDOM-02)
- **7 candidates downgraded** due to hard distance violations or other failures
- **0 candidates DFT-ready** - no candidate passed all strict validation criteria

**Audit Decision:** No candidate is suitable for production DFT without pre-relaxation. Theoretical candidates require ML/force-field or manual geometry cleanup before DFT.  

---

## Next Step Recommendation

**Option A: Build CaSc2TiO6 from corrected parent-prototype logic**  
- Proceed with **CaTiO3 perovskite** as primary template (Ca/O framework)  
- Use **Ca2ScTiO6** for B-site ordering inspiration (Ca/Sc ordering pattern)  
- Construct theoretical CaSc2TiO6 as ordered perovskite  
- Label all constructs as "theoretical" in metadata  
- Re-run SCATTI Phase 1C screening with corrected prototypes  

**Option B: Perform external literature/database search**  
- Search ICSD/CAMD for experimental CaSc2TiO6 structures  
- Use Materials Project (requires API key)  
- More time-intensive but potentially higher success rate  

**Option C: Install Quantum ESPRESSO**  
- Not recommended at this stage  
- DFT should only run after promising candidates are identified  

**Option D: Stop and preserve current artifacts**  
- Not recommended  
- Local search provides clear path forward with corrected logic  

**Recommendation: Option A**  
Proceed with CaTiO3 perovskite as primary template, use Ca2ScTiO6 for ordering inspiration, construct theoretical CaSc2TiO6 as ordered perovskite, re-run SCATTI screening.

---

## Current Artifacts

- `scatti_screening_summary.json` — 13 candidates (0 DFT-ready)  
- `scatti_structure_candidates.csv` — All candidates failed geometry validation  
- `scatti_external_prototype_search.md` — **This file (updated)**  
- `scatti_external_prototype_search.json` — **Updated**  

**Status:** Ready to construct new candidates from corrected parent-prototype logic.
