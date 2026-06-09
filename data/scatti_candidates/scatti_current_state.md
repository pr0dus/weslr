# SCATTI Current State — CaSc2TiO6 Pre-DFT

**Date:** 2026-05-08  
**Phase:** 1P (External structure search - Materials Project API)  
**Status:** Unvalidated computational candidate  

## Formula

- **Target:** CaSc2TiO6
- **Stoichiometry:** Ca:Sc:Ti:O = 1:2:1:6

## Generated Candidates

| Phase | Candidates | DFT-ready | Pre-relaxation | Downgraded | Reference |
|-------|-----------|-----------|----------------|------------|-----------|
| 1B (initial) | 13 | 0 | 0 | 13 | 4 |
| 1D (improved validation) | 13 | 0 | 2 | 7 | 4 |
| 1E (manual builders) | 17 | 0 | 2 | 11 | 4 |
| 1J (parent-motif) | 2 | 0 | 0 | 2 | 0 |

**Phase 1J Results:**
- SCATTI-PARENT-001: rejected (fatal Sc-O and O-O contacts)
- SCATTI-PARENT-002: rejected (fatal density and Ti-O/O-O contacts)

**Note:** Phase 1E introduced new manual builders. All exact-formula candidates either:
- Have fatal distance violations (too-short bonds)
- Fail coordination checks (Ti/Sc < 4 O neighbors)
- Both

**Phase 1J Notes:**
Manual parent-motif coordinate construction did not produce a relaxation-ready CaSc2TiO6 structure. This is not evidence that CaSc2TiO6 is impossible; it means hand-built coordinates are insufficient and the next path should be ML/CSP or real external structure sourcing.

## Source Search Status

| Search Type | Status | Notes |
|-------------|--------|-------|
| Exact CaSc2TiO6 | **INCONCLUSIVE** | See detailed source status below |
| Related structures | **INCONCLUSIVE** | See detailed source status below |
| External database | **INCONCLUSIVE** | No confirmed external hits |
| SearxNG web search | **Evidence table created** | See `scatti_searxng_evidence_table.md` |
| Manual parent-motif construction | **FAILED** | See Phase 1J results above |
| CHGNet ML relaxation | **PARTIAL** | `ml_relaxed_but_not_qe_ready` (Phase 1N, forces did not converge) |
| Materials Project API | **CIFs found** | Related parents: Sc2TiO5, Sc2Ti2O7, CaSc2O4 (no exact CaSc2TiO6) |

**Detailed Source Status:**
- **Materials Project:** ✅ Accessible, but **API key missing** (cannot query)
- **COD:** ✅ Accessible, **checked_no_hit** (no results for exact formula)
- **OQMD:** ❌ **Unavailable** (HTTP 502 Bad Gateway)
- **AFLOW:** ✅ Accessible, **checked_no_hit** (no results for exact formula)
- **NOMAD:** ✅ Accessible, **checked_no_hit** (landing page accessible, no direct query)

**SearxNG Evidence Summary:**
- ✅ SearxNG available at `http://127.0.0.1:8888`
- ✅ JSON search works
- ✅ CLI tool available (`searxng-search`)
- **Exact CaSc2TiO6 evidence:** Not found in SearxNG results
- **Related parent evidence:** Found (Ca2ScTiO6, Sc2TiO5, CaSc2O4, Sc-doped CaTiO3)

**Important:** Timeout/API error ≠ zero results. Failed queries must be retried or manually verified.

## DFT Readiness Summary

| Status | Count | Details |
|--------|-------|---------|
| **production_dft_ready** | 0 | None |
| **pre_relaxation_starting_geometry** | 2 | SCATTI-LAYERED-001, SCATTI-RANDOM-02 |
| **ml_relaxed_but_not_qe_ready** | 1 | SCATTI-LAYERED-001 (CHGNet Phase 1N) |
| **downgraded** | 13 | Various distance/coordination violations |
| **reference_phase** | 4 | Not CaSc2TiO6 candidates |

### CHGNet Relaxation Results (Phase 1N)
| Candidate | Input | Output | max_force | Classification |
|-----------|-------|--------|-----------|----------------|
| SCATTI-LAYERED-001 | 540.0 Å³ | 411.1 Å³ | 0.596 eV/Å | `ml_relaxed_but_not_qe_ready` |

**Not QE-ready because:**
- Forces did NOT converge to fmax<0.2 eV/Å (max=0.596 eV/Å after 50 steps)
- Short O-O contact 1.483 Å (< 1.80 Å threshold)
- Sc-O coordination only 2 each (expected ~4 for Sc³⁺)
- Ca-O coordination only 2 (expected ~6-8 for Ca²⁺)
- Volume collapsed by 23.9% (force field bias or over-relaxation)

- **pre_relaxation_starting_geometry:** 2 candidates
  - SCATTI-LAYERED-001 (layered_oxide, density=0.84 g/cm³, min_distance=1.70 Å)
  - SCATTI-RANDOM-02 (random_ordered, density=2.73 g/cm³, min_distance=1.33 Å)
- **downgraded:** 13 candidates (various distance/coordination violations)
- **reference_phase:** 4 (not CaSc2TiO6 candidates)

## Files Created

| File | Size | Purpose |
|------|------|---------|
| scatti_screening_summary.json | 27 KB | All candidate details |
| scatti_structure_candidates.csv | 18 KB | Candidate table |
| scatti_dft_queue.md | 233 B | Empty (no DFT-ready) |
| scatti_claim_safe_report.md | 920 B | Validation summary |
| scatti_external_prototype_search.* | 13 KB | Prototype search results |
| scatti_structure_source_search.* | 5.1 KB | Updated source search results |
| scatti_manual_verification_checklist.md | 2.9 KB | Manual verification guide |
| scatti_current_state.md | This file | Current status summary |
| scatti_external_structure_search_v2.* | 180 KB | Phase 1P search results |
| scatti_ml_csp_assessment.md | 4.2 KB | ML/CSP assessment |
| **materials_project_search_results.*** | **4.4 KB** | **Materials Project search** |
| **materials_project/cifs/*.cif** | **12 KB** | **4 related parent CIFs exported** |

## Git Status

```
data/scatti_candidates/  (SCATTI artifacts committed)
scripts/scatti_prepare_screening.py  (script version committed)
```

All SCATTI artifacts committed at commits:
- `d29b5be` — external structure search v2
- `62e9ba7` — update current state after ML audit

## Materials Project API Search (Phase 1P)

| Formula | Result | Material ID | e_above_hull | CIF |
|---------|--------|-------------|--------------|-----|
| **CaSc2TiO6** | **no_hit** | — | — | — |
| **Ca2ScTiO6** | **no_hit** | — | — | — |
| **Sc2TiO5** | **found** | mp-753401 | 0.000 eV/atom | ✅ exported |
| **Sc2Ti2O7** | **found** | mp-753802 | 0.000 eV/atom | ✅ exported |
| **CaSc2O4** | **found** | mp-4056 | 0.000 eV/atom | ✅ exported |
| **CaTiO3** | **found** | mp-3442 | 0.017 eV/atom | no |
| **Sc2O3** | **found** | mp-558748 | 0.066 eV/atom | no |
| **TiO2** | **found** | mp-2657 | 0.044 eV/atom | no |
| **CaO** | **found** | mp-2605 | 0.000 eV/atom | no |

**CIFs exported to:**
- `data/scatti_candidates/materials_project/cifs/mp-753401_Sc2TiO5.cif`
- `data/scatti_candidates/materials_project/cifs/mp-753802_Sc2Ti2O7.cif`
- `data/scatti_candidates/materials_project/cifs/mp-4056_CaSc2O4.cif`

**Notes:**
- Exact CaSc2TiO6 and Ca2ScTiO6 not found in Materials Project database
- CaTiO3 query now working with updated field names
- All entries are theoretical (no experimental entries found)
- CaTiO3 has 6 entries (various polymorphs)
- mp-4056 (CaSc2O4) marked as experimental=false (theoretical)

**Claim boundary:**
Materials Project data is computational/database evidence, not experimental proof unless explicitly marked experimental.  
Related parent structures found but require manual construction for exact CaSc2TiO6.

## Recommended Next Decision

**Option A:** Use MP CIFs (Sc2TiO5, Sc2Ti2O7, CaSc2O4) to build better exact CaSc2TiO6 candidates
**Option B:** Perform manual literature search (Google Scholar, Semantic Scholar, SpringerMaterials)
**Option C:** Use SearxNG findings (Ca2ScTiO6, Sc2TiO5, CaSc2O4, Sc-doped CaTiO3) as parent inspiration
**Option D:** Retry OQMD later (HTTP 502 may be transient)
**Option E:** Use crystal structure prediction (CSP) or ML pre-relaxation only after database search completes

**Option F:** Assess ML/CSP tool availability and installability (CHGNet, MatGL, ASE relaxers) before committing to long calculations

## Scientific Status

- **CaSc2TiO6 remains an unvalidated computational candidate.**
- **0 production DFT-ready structures** (all candidates fail validation)
- **2 pre-relaxation starting geometries** (require ML/force-field cleanup)
- **External source search inconclusive** (no exact CaSc2TiO6 in MP, SearxNG, COD)
- **Materials Project API search completed** (related parents found, no exact CaSc2TiO6)
- **CHGNet ML relaxation performed** (SCATTI-LAYERED-001, classified `ml_relaxed_but_not_qe_ready`)
- **MP parent CIF experiment attempted** (Phase 1Q, isolated script)
  - Parent CIFs used: Sc2TiO5, Sc2Ti2O7, CaSc2O4
  - Exact CaSc2TiO6 construction failed
  - Wrong stoichiometry observed: CaSc4Ti2O11
  - Result: metadata_only (no honest transformation possible)
- **Multilingual literature search completed** (Phase 1R)
  - Languages searched: English, German, Russian, Chinese, Japanese, Korean, French, Spanish, Italian
  - Exact CaSc2TiO6 found: No
  - Related Sc-doped CaTiO3 found: Yes (English, high usefulness)
  - Phase diagram studies found: Yes (German/English)
- **No Quantum ESPRESSO installed**
- **No DFT run performed**

