# SCATTI Current State — CaSc2TiO6 Pre-DFT

**Date:** 2026-05-08  
**Phase:** 1H (SearxNG evidence added)  
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

**Note:** Phase 1E introduced new manual builders. All exact-formula candidates either:
- Have fatal distance violations (too-short bonds)
- Fail coordination checks (Ti/Sc < 4 O neighbors)
- Both

## Source Search Status

| Search Type | Status | Notes |
|-------------|--------|-------|
| Exact CaSc2TiO6 | **INCONCLUSIVE** | See detailed source status below |
| Related structures | **INCONCLUSIVE** | See detailed source status below |
| External database | **INCONCLUSIVE** | No confirmed external hits |
| SearxNG web search | **Evidence table created** | See `scatti_searxng_evidence_table.md` |

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

- **production_dft_ready:** 0 candidates
- **pre_relaxation_starting_geometry:** 2 candidates
  - SCATTI-LAYERED-001 (layered_oxide, density=0.84 g/cm³, min_distance=1.70 Å)
  - SCATTI-RANDOM-02 (random_ordered, density=2.73 g/cm³, min_distance=1.33 Å)
- **downgraded:** 11 candidates (various distance/coordination violations)
- **reference_phase:** 4 (not CaSc2TiO6 candidates)

## Files Created

| File | Size | Purpose |
|------|------|---------|
| scatti_screening_summary.json | 27 KB | All candidate details |
| scatti_structure_candidates.csv | 18 KB | Candidate table |
| scatti_dft_queue.md | 233 B | Empty (no DFT-ready) |
| scatti_claim_safe_report.md | 880 B | Validation summary |
| scatti_external_prototype_search.* | 13 KB | Prototype search results |
| scatti_structure_source_search.* | 5.1 KB | Updated source search results |
| scatti_manual_verification_checklist.md | 2.9 KB | Manual verification guide |
| scatti_current_state.md | This file | Current status summary |
| **scatti_searxng_evidence_table.md** | **5.0 KB** | **SearxNG evidence table** |
| **scatti_searxng_evidence_table.json** | **3.7 KB** | **SearxNG evidence JSON** |

## Git Status

```
?? data/scatti_candidates/  (SCATTI artifacts committed)
?? scripts/scatti_prepare_screening.py  (script version committed)
```

All SCATTI artifacts committed at commit `3a36be6`.

## Recommended Next Decision

**Option A:** Configure Materials Project API key and retry automated search  
**Option B:** Perform manual literature search (Google Scholar, Semantic Scholar, SpringerMaterials)  
**Option C:** Use SearxNG findings (Ca2ScTiO6, Sc2TiO5, CaSc2O4, Sc-doped CaTiO3) as parent inspiration  
**Option D:** Retry OQMD later (HTTP 502 may be transient)  
**Option E:** Use crystal structure prediction (CSP) or ML pre-relaxation only after database search completes

## Scientific Status

- **CaSc2TiO6 remains an unvalidated computational candidate.**
- **0 production DFT-ready structures** (all candidates fail validation)
- **2 pre-relaxation starting geometries** (require ML/force-field cleanup)
- **External source search inconclusive** (multiple sources accessible but no confirmed hits)
- **SearxNG web search available** (created evidence table with related parent structures)
- **No Quantum ESPRESSO installed**
- **No DFT run performed**
