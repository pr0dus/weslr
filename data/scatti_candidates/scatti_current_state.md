# SCATTI Current State — CaSc2TiO6 Pre-DFT

**Date:** 2026-05-08  
**Phase:** 1G (Artifacts preserved)  
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
| Exact CaSc2TiO6 | **inconclusive** | All database queries timed out or failed |
| Related structures | **inconclusive** | All queries timed out |
| External database | **inconclusive** | No confirmed external hits in this session |

**Important:** Timeout/API error ≠ zero results. Failed queries must be retried or manually verified.

## DFT Readiness Summary

- **production_dft_ready:** 0 candidates
- **pre_relaxation_starting_geometry:** 2 candidates
  - SCATTI-LAYERED-001 (layered_oxide, density=0.84 g/cm³)
  - SCATTI-RANDOM-02 (random_ordered, density=2.73 g/cm³)
- **downgraded:** 11 candidates (various violations)
- **reference_phase:** 4 (not CaSc2TiO6 candidates)

## Recommended Next Decision

**Option A:** Configure Materials Project API key and retry automated search  
**Option B:** Perform manual literature search for CaSc2TiO6  
**Option C:** Retry database queries with longer timeout settings  
**Option D:** Use crystal structure prediction (CSP) or ML pre-relaxation  
**Option E:** Submit computational candidates for experimental validation

## Files Created

| File | Size | Purpose |
|------|------|---------|
| scatti_screening_summary.json | 27 KB | All candidate details |
| scatti_structure_candidates.csv | 18 KB | Candidate table |
| scatti_dft_queue.md | 233 B | Empty (no DFT-ready) |
| scatti_claim_safe_report.md | 880 B | Validation summary |
| scatti_external_prototype_search.* | 13 KB | Prototype search results |
| scatti_structure_source_search.* | 5.8 KB | Source search results |
| scatti_manual_verification_checklist.md | 2.9 KB | Manual verification guide |
| scatti_current_state.md | This file | Current status summary |

## Git Status

```
?? data/scatti_candidates/  (new artifacts)
?? scripts/scatti_prepare_screening.py  (script versions)
```

All artifacts are untracked (not committed). Ready for review.
