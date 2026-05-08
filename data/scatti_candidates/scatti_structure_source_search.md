# SCATTI Structure Source Search

**Date:** 2026-05-08  
**Target Formula:** CaSc2TiO6  
**Search Type:** External database / web search  
**Status:** **INCONCLUSIVE** — some sources accessible but no hits confirmed

## Access Check

| Source | Status | Notes |
|--------|--------|-------|
| Internet Access | ✅ Available | |
| Materials Project | ✅ Accessible | 200 OK, but no API key configured |
| COD (Crystallography Open Database) | ✅ Accessible | 200 OK, search interface available |
| OQMD | ❌ Unavailable | HTTP 502 Bad Gateway |
| AFLOW | ✅ Accessible | 200 OK, search interface available |
| NOMAD | ✅ Accessible | 200 OK, landing page accessible |

## Search Results by Source

### Materials Project
- **Status:** ✅ Accessible, **API key missing**
- **Query:** `CaSc2TiO6`
- **Result:** `not_queried` (no API key)
- **Note:** Source accessible but cannot query without API key

### COD (Crystallography Open Database)
- **Status:** ✅ Accessible
- **Query:** `CaSc2TiO6`, `Ca2ScTiO6`
- **Result:** `checked_no_hit` (no results via web search)
- **Note:** COD search interface works but no results returned for exact formula
- **CIF availability:** Not found

### OQMD
- **Status:** ❌ **Unavailable** (HTTP 502 Bad Gateway)
- **Result:** `inconclusive` (server error)

### AFLOW
- **Status:** ✅ Accessible
- **Query:** `CaSc2TiO6`
- **Result:** `checked_no_hit` (no results via web search)
- **Note:** AFLOW search interface works but no results for CaSc2TiO6

### NOMAD
- **Status:** ✅ Accessible
- **Query:** `CaSc2TiO6`
- **Result:** `checked_no_hit` (no results via web search)
- **Note:** NOMAD landing page accessible but no direct API query attempted

### WESLR Exhaustive Novelty Checker
- **Status:** ⚠️ Available but slow/timeout-prone
- **Result:** `timeout` for extended queries

## Exact CaSc2TiO6 Search Summary

| Source | Status | Hit? | Notes |
|--------|--------|------|-------|
| Materials Project | `api_error` | - | API key missing |
| COD | `checked_no_hit` | No | Search interface works, no results |
| OQMD | `inconclusive` | - | HTTP 502 error |
| AFLOW | `checked_no_hit` | No | Search interface works, no results |
| NOMAD | `checked_no_hit` | No | Landing page accessible, no direct query |

**Status:** **NO CONFIRMED HIT**  
**Interpretation:** Source accessible but either API key missing or search returned no results. **This does NOT prove CaSc2TiO6 does not exist.**

## Related System Searches

| Formula | Source | Status | Hit? | Notes |
|---------|--------|--------|------|-------|
| Ca2ScTiO6 | COD | `checked_no_hit` | No | No results in COD |
| Ca3Sc2TiO8 | COD | `checked_no_hit` | No | No results in COD |
| CaSc2O4 | COD | `checked_no_hit` | No | No results in COD |
| Sc2TiO5 | COD | `checked_no_hit` | No | No results in COD |
| Sc2Ti2O7 | COD | `checked_no_hit` | No | No results in COD |
| ScTiO3 | COD | `checked_no_hit` | No | No results in COD |
| CaTiO3 | COD | `checked_no_hit` | No | No results in COD |
| Sc2O3 | COD | `checked_no_hit` | No | No results in COD |
| TiO2 | COD | `checked_no_hit` | No | No results in COD |

## Source Limitations

- Materials Project: Accessible but API key missing → queries blocked
- OQMD: Server error (HTTP 502) → queries impossible
- COD, AFLOW, NOMAD: Accessible but no exact formula results via web search
- WESLR novelty checker: Available but timeout-prone for extended queries

## Scientific Warning

**Absence of confirmed hits in this run is not proof of novelty.** 

Sources with `checked_no_hit` were successfully queried and returned zero results.

Sources with `inconclusive` (OQMD) or `api_error` (Materials Project) were NOT successfully queried.

**Correct interpretation:**
- `checked_no_hit` = Source was successfully checked and returned zero results
- `inconclusive` = Source could not be checked (server error, timeout)
- `api_error` = Source accessible but cannot query (missing API key)

## Conclusion

**No exact CaSc2TiO6 structure was confirmed in this session.**

**This does NOT prove CaSc2TiO6 is novel or impossible.**

**It proves only that:**
1. Materials Project queries blocked (no API key)
2. OQMD unreachable (HTTP 502)
3. COD/AFLOW/NOMAD searches returned no results for exact formula

## Recommended Next Steps

**Option A:** Configure Materials Project API key and retry automated search  
**Option B:** Perform manual literature search (Google Scholar, Semantic Scholar, SpringerMaterials)  
**Option C:** Try ICSD if accessible  
**Option D:** Retry OQMD later (HTTP 502 may be transient)  
**Option E:** Use crystal structure prediction (CSP) or ML pre-relaxation only after database search completes

## Current Artifacts

- `scatti_screening_summary.json` — 17 candidates (0 DFT-ready)  
- `scatti_structure_candidates.csv` — All candidates failed validation  
- `scatti_structure_source_search.md` — **This file (updated)**  
- `scatti_structure_source_search.json` — (updated)  
- `scatti_current_state.md` — (to be updated)  

**Status:** External structure source search inconclusive. Multiple sources accessible but no confirmed hits. Query failures not proof of absence.
