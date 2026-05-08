# SCATTI Parent Structure Clues

**Date:** 2026-05-08  
**Target:** CaSc2TiO6  
**Source:** SearxNG web search evidence (2401b9a)

## Purpose

Extract structural clues from related Ca-Sc-Ti-O compounds to guide CaSc2TiO6 construction.

## Evidence Sources

- SearxNG web search at http://127.0.0.1:8888
- Query results categorized as exact_candidate, related_parent, doped_material, irrelevant

## Parent Clue Extraction

### Ca2ScTiO6 (OQMD)
- **Clue:** Double perovskite structure listed in OQMD
- **Usefulness:** High - shows related compound class exists
- **Limitation:** Stoichiometry 2:1:1 vs target 1:2:1; requires Sc/Ti swap or supercell
- **Why it matters:** Demonstrates double perovskite framework for Ca-Sc-Ti-O system
- **Classification:** related_parent (not exact_candidate - Ca2ScTiO6 ≠ CaSc2TiO6)

### Sc2TiO5 (ResearchGate)
- **Clue:** Pseudobrookite-type structure, Sc/Ti partially disordered
- **Usefulness:** High - exact Sc:Ti:O = 2:1:5 ratio
- **Limitation:** Different stoichiometry, TiO5 vs TiO6 coordination
- **Why it matters:** Sc-Ti-O framework reference for constructing CaSc2TiO6

### CaSc2O4 (RSC)
- **Clue:** Exact formula, layered oxide, luminescent phosphor
- **Usefulness:** High - Ca/Sc-O coordination reference
- **Limitation:** No Ti, different oxide family
- **Why it matters:** Sc-O and Ca-O coordination insights for CaSc2TiO6

### Sc-doped CaTiO3 (Sciencedirect)
- **Clue:** Sc substitution in CaTiO3 enables ionic conduction
- **Usefulness:** High - directly relevant to CaSc2TiO6
- **Limitation:** Doped material, not exact formula
- **Why it matters:** Sc/Ti ordering insights for perovskite framework

## Parent Motif Ranking

| Rank | Parent Motif | Score | Reason | Main Limitation | Recommended Use |
|------|--------------|-------|--------|-----------------|-----------------|
| 1 | **Sc-doped CaTiO3** | 10 | Sc/Ti ordering in perovskite, direct CaSc2TiO6 relevance | Doped material, not exact | Build CaSc2TiO6 as Sc/Ti-ordered perovskite |
| 2 | **Ca2ScTiO6** | 7 | Double perovskite, OQMD confirmed (related_parent, not exact_candidate) | Stoichiometry 2:1:1 vs 1:2:1 | Use for ordering inspiration, not exact match |
| 3 | **Sc2TiO5** | 7 | Exact Sc:Ti:O ratio, pseudobrookite framework | Different stoichiometry | Sc-Ti-O framework reference |
| 4 | **CaSc2O4** | 6 | Exact formula, Sc-O coordination | No Ti, different oxide family | Ca/Sc-O coordination reference |

## Recommended Construction Strategy

**Strategy A: Sc-doped CaTiO3-derived ordered perovskite**

**Why best:**  
- Sc-doped CaTiO3 is the most directly relevant (Sc/Ti substitution in CaTiO3)
- Provides real perovskite framework with Sc/Ti ordering examples
- Direct path to exact CaSc2TiO6 via stoichiometric substitution

**Formula obstacle:**  
- Sc-doped CaTiO3 has formula Ca(Ti1-xScx)O3
- Target CaSc2TiO6 requires Ca:Sc:Ti = 1:2:1
- Need ordered B-site arrangement: [Sc2Ti]O6 octahedra

**How to avoid fake coordinates:**  
- Start with experimental CaTiO3 structure (mp-5827)
- Replace Ti site with Sc2/Ti ordered arrangement
- Verify all distances: Ti-O > 1.7 Å, Sc-O > 1.8 Å, Ca-O > 2.0 Å
- Ensure Ti/Sc each have 4-6 O neighbors

**Validation checks must pass:**  
- Exact formula: Ca:Sc:Ti:O = 1:2:1:6
- No duplicate coordinates
- No fatal distance violations
- Ti and Sc each have 4-6 O neighbors
- Density in plausible range [2.0, 8.0] g/cm³

## Claim Boundary

- No exact CaSc2TiO6 evidence was found in SearxNG results. Exact-query results were noisy/irrelevant unless manually verified otherwise.
- Related parent evidence does not prove CaSc2TiO6 exists.
- Parent motifs are construction clues only.
- CaSc2TiO6 remains an unvalidated computational candidate.
